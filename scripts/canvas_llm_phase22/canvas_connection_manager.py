#!/usr/bin/env python3
"""Phase 22 live Canvas API transport — Q1W2 allowlisted POST endpoints only."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.canvas_llm_phase22 import canvas_connection as connection  # noqa: E402
from scripts.canvas_llm_phase22 import phase22_workstation as p22  # noqa: E402

HOMEROOM_COURSE_ID = connection.HOMEROOM_COURSE_ID
MATH_COURSE_ID = connection.MATH_COURSE_ID
READING_COURSE_ID = connection.READING_COURSE_ID
ELA_COURSE_ID = connection.ELA_COURSE_ID
HISTORY_COURSE_ID = connection.HISTORY_COURSE_ID
SCIENCE_COURSE_ID = connection.SCIENCE_COURSE_ID

ALLOWED_LIVE_COURSE_IDS = {
    HOMEROOM_COURSE_ID,
    MATH_COURSE_ID,
    READING_COURSE_ID,
    ELA_COURSE_ID,
    HISTORY_COURSE_ID,
    SCIENCE_COURSE_ID,
}
ALLOWED_POST_PATH_RES = (
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/pages$'),
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/assignments$'),
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/discussion_topics$'),
)
ALLOWED_PUT_PATH_RES = (
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/assignments/\d+$'),
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/discussion_topics/\d+$'),
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/pages/[^/]+$'),
)
ALLOWED_DELETE_PATH_RES = (
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/assignments/\d+$'),
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/discussion_topics/\d+$'),
)
ALLOWED_GET_PATH_RES = (
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)$'),
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/pages/[^/]+$'),
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/assignments/\d+$'),
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/assignment_groups$'),
    re.compile(r'^/api/v1/courses/(?P<course_id>\d+)/discussion_topics/\d+$'),
)
BLOCKED_PATH_MARKERS = {
    'grades',
    'gradebook',
    'submissions',
    'analytics',
    'student',
    'users',
    'people',
    'enrollments',
    'settings',
    'rubrics',
    'outcomes',
    'quizzes',
    'modules',
    'files',
    'folders',
}
MOCK_LIVE_STORE: dict[str, dict[str, Any]] = {'pages': {}, 'assignments': {}, 'announcements': {}}


def compact(value: Any) -> str:
    return p22.compact(value)


def deployment_mode() -> str:
    return compact(os.environ.get('CANVAS_LLM_DEPLOYMENT_MODE') or 'controlled').lower()


def is_live_deployment_mode() -> bool:
    return deployment_mode() == 'live'


def is_live_transport_test_mode() -> bool:
    return compact(os.environ.get('CANVAS_LLM_LIVE_TRANSPORT_TEST') or '').lower() in {'1', 'true', 'yes'}


def use_live_transport(*, test_mode: bool = False) -> bool:
    return is_live_deployment_mode() or is_live_transport_test_mode() or test_mode


def _token_configured() -> bool:
    return bool(compact(os.environ.get('CANVAS_TOKEN') or os.environ.get('CANVAS_API_TOKEN') or ''))


def _base_url_configured() -> bool:
    return bool(compact(os.environ.get('CANVAS_BASE_URL') or ''))


def _live_approved() -> bool:
    return compact(os.environ.get('CANVAS_LLM_LIVE_Q1W2_APPROVED') or '').lower() in {'1', 'true', 'yes'}


def require_live_prerequisites(*, test_mode: bool = False) -> None:
    if test_mode or is_live_transport_test_mode():
        return
    if not is_live_deployment_mode():
        raise RuntimeError('BLOCKED: CANVAS_LLM_DEPLOYMENT_MODE=live required for real Canvas transport')
    if not _live_approved():
        raise RuntimeError('BLOCKED: CANVAS_LLM_LIVE_Q1W2_APPROVED=1 required for live deployment')
    if not _token_configured():
        raise RuntimeError('BLOCKED: CANVAS_TOKEN required for live deployment')
    if not _base_url_configured():
        raise RuntimeError('BLOCKED: CANVAS_BASE_URL required for live deployment')


def _validate_course(course_id: int) -> None:
    if int(course_id) not in ALLOWED_LIVE_COURSE_IDS:
        raise PermissionError(f'BLOCKED: course {course_id} is not allowlisted for Q1W2 live writes')


def _is_allowed_get_path(path: str) -> bool:
    return any(pattern.match(path) for pattern in ALLOWED_GET_PATH_RES)


def _course_id_from_path(path: str, regexes) -> int | None:
    for pattern in regexes:
        match = pattern.match(path)
        if match:
            return int(match.group('course_id'))
    return None


def validate_live_transport_path(method: str, path: str) -> None:
    """Validate a live transport request path against the allowlist."""
    _validate_path(method, path)


def _validate_path(method: str, path: str) -> None:
    lowered = path.lower()
    if any(marker in lowered for marker in BLOCKED_PATH_MARKERS):
        raise PermissionError(f'BLOCKED: endpoint touches a blocked Canvas area: {path}')
    upper = method.upper()
    if upper == 'POST':
        if not any(pattern.match(path) for pattern in ALLOWED_POST_PATH_RES):
            raise PermissionError(f'BLOCKED: POST not allowlisted for live transport: {path}')
        course_id = _course_id_from_path(path, ALLOWED_POST_PATH_RES)
        _validate_course(course_id)
    elif upper == 'GET':
        if not _is_allowed_get_path(path):
            raise PermissionError(f'BLOCKED: GET not allowlisted for live transport verification: {path}')
        course_id = _course_id_from_path(path, ALLOWED_GET_PATH_RES)
        if course_id is not None:
            _validate_course(course_id)
    elif upper == 'PUT':
        if not any(pattern.match(path) for pattern in ALLOWED_PUT_PATH_RES):
            raise PermissionError(f'BLOCKED: PUT not allowlisted for live transport: {path}')
        course_id = _course_id_from_path(path, ALLOWED_PUT_PATH_RES)
        _validate_course(course_id)
    elif upper == 'DELETE':
        if not any(pattern.match(path) for pattern in ALLOWED_DELETE_PATH_RES):
            raise PermissionError(f'BLOCKED: DELETE not allowlisted for live transport: {path}')
        course_id = _course_id_from_path(path, ALLOWED_DELETE_PATH_RES)
        _validate_course(course_id)
    else:
        raise PermissionError(f'BLOCKED: {upper} not allowlisted for live transport: {path}')


@dataclass
class LiveTransportStatus:
    api_client: str
    authentication: str
    course_mapping: str
    write_transport: str
    write_gate: str
    environment: str
    blockers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_live_transport_status(*, test_mode: bool = False) -> LiveTransportStatus:
    blockers: list[str] = []
    conn = connection.build_connection_status(test_mode=test_mode)

    if is_live_deployment_mode() and not _live_approved() and not test_mode:
        blockers.append('live_deployment_not_approved')
    if is_live_deployment_mode() and not test_mode and not is_live_transport_test_mode():
        if not _token_configured():
            blockers.append('missing_canvas_token')
        if not _base_url_configured():
            blockers.append('missing_canvas_base_url')

    authentication = conn.authentication
    if is_live_deployment_mode() and blockers:
        authentication = 'FAIL'

    mapping = conn.course_mapping
    transport_enabled = (
        authentication == 'PASS'
        and mapping == 'PASS'
        and (test_mode or is_live_transport_test_mode() or (is_live_deployment_mode() and _live_approved()))
    )
    environment = 'LIVE' if is_live_deployment_mode() or test_mode or is_live_transport_test_mode() else 'CONTROLLED'

    return LiveTransportStatus(
        api_client='READY' if transport_enabled or test_mode else 'BLOCKED',
        authentication=authentication,
        course_mapping=mapping,
        write_transport='ENABLED' if transport_enabled else 'BLOCKED',
        write_gate='CONTROLLED',
        environment=environment,
        blockers=blockers,
    )


class MockPhase22CanvasClient:
    """In-memory Canvas API transport for tests — no network, no fake-mode downgrade."""

    transport = 'mock'

    def create_page(
        self,
        course_id: int,
        *,
        title: str,
        body: str,
        published: bool = True,
        front_page: bool = False,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        page_id = p22.stable_id('canvas-page', course_id, title)
        url = compact(title).lower().replace(' ', '-').replace(':', '')
        payload = {
            'id': page_id,
            'url': url,
            'course_id': course_id,
            'title': title,
            'body': body,
            'published': published,
            'front_page': front_page,
        }
        MOCK_LIVE_STORE['pages'][url] = payload
        return payload

    def create_assignment(
        self,
        course_id: int,
        *,
        title: str,
        description: str,
        assignment_group: str,
        points: int = 100,
        grading_type: str = 'percent',
        submission_type: str = 'on_paper',
        due_at: str = '',
        counts_toward_final_grade: bool = True,
        published: bool = True,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        assignment_id = p22.stable_id('canvas-assignment', course_id, title)
        payload = {
            'id': assignment_id,
            'course_id': course_id,
            'name': title,
            'title': title,
            'description': description,
            'assignment_group': assignment_group,
            'points_possible': points,
            'grading_type': grading_type,
            'submission_types': [submission_type],
            'due_at': due_at,
            'omit_from_final_grade': not counts_toward_final_grade,
            'counts_toward_final_grade': counts_toward_final_grade,
            'published': published,
        }
        MOCK_LIVE_STORE['assignments'][assignment_id] = payload
        return payload

    def get_page(self, course_id: int, page_ref: str) -> dict[str, Any]:
        _validate_course(course_id)
        for page in MOCK_LIVE_STORE['pages'].values():
            if int(page['course_id']) == int(course_id) and page.get('url') == page_ref:
                return page
            if compact(page.get('id')) == compact(page_ref):
                return page
        raise KeyError(f'page not found: {page_ref}')

    def get_assignment(self, course_id: int, assignment_id: str) -> dict[str, Any]:
        _validate_course(course_id)
        stored = MOCK_LIVE_STORE['assignments'].get(compact(assignment_id))
        if not stored or int(stored['course_id']) != int(course_id):
            raise KeyError(f'assignment not found: {assignment_id}')
        return stored

    def get_announcement(self, course_id: int, topic_id: str) -> dict[str, Any]:
        _validate_course(course_id)
        stored = MOCK_LIVE_STORE['announcements'].get(compact(topic_id))
        if not stored or int(stored['course_id']) != int(course_id):
            raise KeyError(f'announcement not found: {topic_id}')
        return stored

    def create_announcement(
        self,
        course_id: int,
        *,
        title: str,
        message: str = '',
        published: bool = True,
        delayed_post_at: str | None = None,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        topic_id = p22.stable_id('canvas-announcement', course_id, title)
        payload = {
            'id': topic_id,
            'course_id': course_id,
            'title': title,
            'message': message,
            'published': published,
            'delayed_post_at': delayed_post_at,
        }
        MOCK_LIVE_STORE['announcements'][topic_id] = payload
        return payload

    def update_assignment(
        self,
        course_id: int,
        assignment_id: str,
        *,
        title: str | None = None,
        due_at: str | None = None,
        omit_from_final_grade: bool | None = None,
        published: bool | None = None,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        stored = self.get_assignment(course_id, assignment_id)
        if title is not None:
            stored['name'] = title
            stored['title'] = title
        if due_at is not None:
            stored['due_at'] = due_at
        if omit_from_final_grade is not None:
            stored['omit_from_final_grade'] = omit_from_final_grade
            stored['counts_toward_final_grade'] = not omit_from_final_grade
        if published is not None:
            stored['published'] = published
        return stored

    def delete_assignment(self, course_id: int, assignment_id: str) -> dict[str, Any]:
        _validate_course(course_id)
        stored = MOCK_LIVE_STORE['assignments'].pop(compact(assignment_id), None)
        if not stored or int(stored['course_id']) != int(course_id):
            raise KeyError(f'assignment not found: {assignment_id}')
        return stored

    def update_announcement(
        self,
        course_id: int,
        topic_id: str,
        *,
        title: str | None = None,
        message: str | None = None,
        published: bool | None = None,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        stored = self.get_announcement(course_id, topic_id)
        if title is not None:
            stored['title'] = title
        if message is not None:
            stored['message'] = message
        if published is not None:
            stored['published'] = published
        return stored

    def delete_announcement(self, course_id: int, topic_id: str) -> dict[str, Any]:
        _validate_course(course_id)
        stored = MOCK_LIVE_STORE['announcements'].pop(compact(topic_id), None)
        if not stored or int(stored['course_id']) != int(course_id):
            raise KeyError(f'announcement not found: {topic_id}')
        return stored

    def update_page(
        self,
        course_id: int,
        page_ref: str,
        *,
        title: str | None = None,
        body: str | None = None,
        published: bool | None = None,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        stored = self.get_page(course_id, page_ref)
        if title is not None:
            stored['title'] = title
        if body is not None:
            stored['body'] = body
        if published is not None:
            stored['published'] = published
        return stored

    def request(self, method: str, path: str, data: dict[str, Any] | None = None) -> Any:
        _validate_path(method, path)
        raise RuntimeError('MockPhase22CanvasClient.request is not used directly')


class CanvasTransportError(RuntimeError):
    """A clean, token-free transport failure (HTTP status or network error).

    Raised by Phase22LiveCanvasClient.request so callers can convert a failed
    Canvas write into a BLOCKED result instead of an uncaught traceback.
    """

    def __init__(self, method: str, path: str, status: int | None, detail: str) -> None:
        self.method = method
        self.path = path
        self.status = status
        self.detail = detail
        code = f'{status}' if status is not None else 'network'
        super().__init__(f'Canvas HTTP {code} on {method} {path}: {detail}')


class Phase22LiveCanvasClient:
    """Real Canvas API transport with Q1W2 endpoint allowlist."""

    transport = 'live'

    def __init__(self, base_url: str, token: str, *, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> Phase22LiveCanvasClient:
        base_url = compact(os.environ.get('CANVAS_BASE_URL') or '')
        token = compact(os.environ.get('CANVAS_TOKEN') or os.environ.get('CANVAS_API_TOKEN') or '')
        if not base_url or not token:
            raise RuntimeError('BLOCKED: CANVAS_BASE_URL and CANVAS_TOKEN are required for live transport')
        return cls(base_url=base_url, token=token)

    def request(
        self,
        method: str,
        path: str,
        data: dict[str, Any] | None = None,
    ) -> Any:
        _validate_path(method, path)
        url = f'{self.base_url}{path}'
        body = None
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
        }
        if data is not None:
            body = urllib.parse.urlencode(data, doseq=True).encode('utf-8')
            headers['Content-Type'] = 'application/x-www-form-urlencoded'
        req = urllib.request.Request(url, data=body, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                text = response.read().decode('utf-8')
                if not text:
                    return {}
                return json.loads(text)
        except urllib.error.HTTPError as exc:
            detail = ''
            try:
                detail = (exc.read() or b'').decode('utf-8', 'replace')[:400]
            except Exception:  # noqa: BLE001 - best-effort body capture only
                detail = ''
            raise CanvasTransportError(method.upper(), path, exc.code, detail or exc.reason) from exc
        except urllib.error.URLError as exc:
            raise CanvasTransportError(method.upper(), path, None, str(exc.reason)) from exc

    def create_page(
        self,
        course_id: int,
        *,
        title: str,
        body: str,
        published: bool = True,
        front_page: bool = False,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        data = {
            'wiki_page[title]': title,
            'wiki_page[body]': body,
            'wiki_page[published]': 'true' if published else 'false',
            'wiki_page[front_page]': 'true' if front_page else 'false',
        }
        return self.request('POST', f'/api/v1/courses/{course_id}/pages', data=data)

    def create_assignment(
        self,
        course_id: int,
        *,
        title: str,
        description: str,
        assignment_group: str,
        points: int = 100,
        grading_type: str = 'percent',
        submission_type: str = 'on_paper',
        due_at: str = '',
        counts_toward_final_grade: bool = True,
        published: bool = True,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        group_id = self._resolve_assignment_group_id(course_id, assignment_group)
        data: dict[str, Any] = {
            'assignment[name]': title,
            'assignment[description]': description,
            'assignment[assignment_group_id]': group_id,
            'assignment[points_possible]': points,
            'assignment[grading_type]': grading_type,
            'assignment[submission_types][]': submission_type,
            'assignment[published]': 'true' if published else 'false',
            'assignment[omit_from_final_grade]': 'false' if counts_toward_final_grade else 'true',
        }
        if due_at:
            data['assignment[due_at]'] = due_at
        return self.request('POST', f'/api/v1/courses/{course_id}/assignments', data=data)

    def _resolve_assignment_group_id(self, course_id: int, group_name: str) -> str:
        groups = self.request('GET', f'/api/v1/courses/{course_id}/assignment_groups')
        if not isinstance(groups, list):
            raise RuntimeError(f'assignment group lookup failed for course {course_id}')
        for group in groups:
            if compact(group.get('name')) == compact(group_name):
                return compact(group.get('id'))
        raise RuntimeError(f'assignment group not found: {group_name}')

    def get_course(self, course_id: int) -> dict[str, Any]:
        return self.request('GET', f'/api/v1/courses/{course_id}')

    def get_page(self, course_id: int, page_url: str) -> dict[str, Any]:
        return self.request('GET', f'/api/v1/courses/{course_id}/pages/{page_url}')

    def get_assignment(self, course_id: int, assignment_id: str) -> dict[str, Any]:
        return self.request('GET', f'/api/v1/courses/{course_id}/assignments/{assignment_id}')

    def get_announcement(self, course_id: int, topic_id: str) -> dict[str, Any]:
        return self.request('GET', f'/api/v1/courses/{course_id}/discussion_topics/{topic_id}')

    def create_announcement(
        self,
        course_id: int,
        *,
        title: str,
        message: str = '',
        published: bool = True,
        delayed_post_at: str | None = None,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        data = {
            'title': title,
            'message': message,
            'is_announcement': 'true',
            'published': 'true' if published else 'false',
        }
        if delayed_post_at:
            data['delayed_post_at'] = delayed_post_at
        return self.request('POST', f'/api/v1/courses/{course_id}/discussion_topics', data=data)

    def update_assignment(
        self,
        course_id: int,
        assignment_id: str,
        *,
        title: str | None = None,
        due_at: str | None = None,
        omit_from_final_grade: bool | None = None,
        published: bool | None = None,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        data: dict[str, Any] = {}
        if title is not None:
            data['assignment[name]'] = title
        if due_at is not None:
            data['assignment[due_at]'] = due_at
        if omit_from_final_grade is not None:
            data['assignment[omit_from_final_grade]'] = 'true' if omit_from_final_grade else 'false'
        if published is not None:
            data['assignment[published]'] = 'true' if published else 'false'
        return self.request('PUT', f'/api/v1/courses/{course_id}/assignments/{assignment_id}', data=data)

    def delete_assignment(self, course_id: int, assignment_id: str) -> dict[str, Any]:
        _validate_course(course_id)
        return self.request('DELETE', f'/api/v1/courses/{course_id}/assignments/{assignment_id}')

    def update_announcement(
        self,
        course_id: int,
        topic_id: str,
        *,
        title: str | None = None,
        message: str | None = None,
        published: bool | None = None,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        data: dict[str, Any] = {}
        if title is not None:
            data['title'] = title
        if message is not None:
            data['message'] = message
        if published is not None:
            data['published'] = 'true' if published else 'false'
        return self.request('PUT', f'/api/v1/courses/{course_id}/discussion_topics/{topic_id}', data=data)

    def delete_announcement(self, course_id: int, topic_id: str) -> dict[str, Any]:
        _validate_course(course_id)
        return self.request('DELETE', f'/api/v1/courses/{course_id}/discussion_topics/{topic_id}')

    def update_page(
        self,
        course_id: int,
        page_ref: str,
        *,
        title: str | None = None,
        body: str | None = None,
        published: bool | None = None,
    ) -> dict[str, Any]:
        _validate_course(course_id)
        data: dict[str, Any] = {}
        if title is not None:
            data['wiki_page[title]'] = title
        if body is not None:
            data['wiki_page[body]'] = body
        if published is not None:
            data['wiki_page[published]'] = 'true' if published else 'false'
        return self.request('PUT', f'/api/v1/courses/{course_id}/pages/{page_ref}', data=data)


def get_transport_client(*, test_mode: bool = False) -> MockPhase22CanvasClient | Phase22LiveCanvasClient:
    if test_mode or is_live_transport_test_mode():
        return MockPhase22CanvasClient()
    require_live_prerequisites(test_mode=False)
    return Phase22LiveCanvasClient.from_env()


def transport_inventory_objects() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for page in MOCK_LIVE_STORE['pages'].values():
        items.append({'object_type': 'page', **page})
    for assignment in MOCK_LIVE_STORE['assignments'].values():
        items.append({'object_type': 'assignment', **assignment})
    for announcement in MOCK_LIVE_STORE['announcements'].values():
        items.append({'object_type': 'announcement', **announcement})
    return items


def live_mode_blocks_without_approval() -> bool:
    if not is_live_deployment_mode():
        return True
    if _live_approved():
        return False
    status = build_live_transport_status()
    return status.write_transport == 'BLOCKED'


def transport_has_no_fake_fallback() -> bool:
    source = Path(__file__).read_text().lower()
    marker = 'def transport_has_no_fake_fallback'
    idx = source.find(marker)
    scan_source = source[:idx] if idx >= 0 else source
    forbidden = ('fallback to fake', 'downgrade to fake', 'fake_mode_fallback', 'use_fake_mode')
    return not any(token in scan_source for token in forbidden)


def print_live_transport_status_report(*, test_mode: bool = False) -> None:
    status = build_live_transport_status(test_mode=test_mode)
    print('Canvas Live Transport')
    print()
    print('API Client:')
    print(status.api_client)
    print()
    print('Authentication:')
    print(status.authentication)
    print()
    print('Course Mapping:')
    print(status.course_mapping)
    print()
    print('Write Transport:')
    print(status.write_transport)
    print()
    print('Write Gate:')
    print(status.write_gate)
    print()
    print('Environment:')
    print(status.environment)


def command_status_report(_args: argparse.Namespace) -> int:
    test_mode = compact(os.environ.get('CANVAS_LLM_LIVE_TRANSPORT_TEST') or '').lower() in {'1', 'true', 'yes'}
    test_mode = test_mode or compact(os.environ.get('CANVAS_LLM_CONNECTION_TEST_MODE') or '').lower() in {'1', 'true', 'yes'}
    print_live_transport_status_report(test_mode=test_mode)
    status = build_live_transport_status(test_mode=test_mode)
    return 0 if status.write_transport == 'ENABLED' or test_mode else 1


def command_self_test() -> int:
    MOCK_LIVE_STORE['pages'].clear()
    MOCK_LIVE_STORE['assignments'].clear()
    MOCK_LIVE_STORE['announcements'].clear()

    status = build_live_transport_status(test_mode=True)
    assert status.api_client == 'READY'
    assert status.authentication == 'PASS'
    assert status.course_mapping == 'PASS'
    assert status.write_transport == 'ENABLED'
    assert status.write_gate == 'CONTROLLED'
    assert status.environment == 'LIVE'

    client = get_transport_client(test_mode=True)
    assert isinstance(client, MockPhase22CanvasClient)

    page = client.create_page(
        HOMEROOM_COURSE_ID,
        title='Q1W2 Weekly Agenda',
        body='<p>Test agenda</p>',
        published=True,
        front_page=True,
    )
    assert page['front_page'] is True
    verified = client.get_page(HOMEROOM_COURSE_ID, compact(page['url']))
    assert verified['title'] == 'Q1W2 Weekly Agenda'

    assignment = client.create_assignment(
        MATH_COURSE_ID,
        title='SM5: Lesson 2',
        description='Complete problems.',
        assignment_group='Homework/Class Work',
        counts_toward_final_grade=True,
    )
    got = client.get_assignment(MATH_COURSE_ID, compact(assignment['id']))
    assert got['counts_toward_final_grade'] is True

    try:
        client.create_page(99999, title='Blocked', body='x')
        raise AssertionError('unexpected course should be blocked')
    except PermissionError:
        pass

    validate_live_transport_path('GET', f'/api/v1/courses/{HOMEROOM_COURSE_ID}')
    validate_live_transport_path('GET', f'/api/v1/courses/{HOMEROOM_COURSE_ID}/pages/q1w2-weekly-agenda')
    validate_live_transport_path('GET', f'/api/v1/courses/{MATH_COURSE_ID}/assignments/12345')
    validate_live_transport_path('GET', f'/api/v1/courses/{READING_COURSE_ID}/assignment_groups')

    for blocked_path in (
        f'/api/v1/courses/{HOMEROOM_COURSE_ID}/students',
        f'/api/v1/courses/{HOMEROOM_COURSE_ID}/submissions',
        f'/api/v1/courses/{HOMEROOM_COURSE_ID}/grades',
        f'/api/v1/courses/{HOMEROOM_COURSE_ID}/enrollments',
        f'/api/v1/courses/{HOMEROOM_COURSE_ID}/modules',
        f'/api/v1/courses/{HOMEROOM_COURSE_ID}/files',
        f'/api/v1/courses/{HOMEROOM_COURSE_ID}/pages',
        f'/api/v1/courses/{HOMEROOM_COURSE_ID}/assignments',
    ):
        try:
            validate_live_transport_path('GET', blocked_path)
            raise AssertionError(f'expected blocked path: {blocked_path}')
        except PermissionError:
            pass

    # Update/remove operations are now allowlisted for the approved manifest.
    validate_live_transport_path('PUT', f'/api/v1/courses/{MATH_COURSE_ID}/assignments/12345')
    validate_live_transport_path('DELETE', f'/api/v1/courses/{MATH_COURSE_ID}/assignments/12345')
    validate_live_transport_path('PUT', f'/api/v1/courses/{HOMEROOM_COURSE_ID}/pages/agenda')
    validate_live_transport_path('PUT', f'/api/v1/courses/{HOMEROOM_COURSE_ID}/discussion_topics/987')
    validate_live_transport_path('DELETE', f'/api/v1/courses/{HOMEROOM_COURSE_ID}/discussion_topics/987')
    validate_live_transport_path('POST', f'/api/v1/courses/{HOMEROOM_COURSE_ID}/discussion_topics')

    # Still-blocked methods and non-allowlisted targets.
    for blocked_method, blocked_path in (
        ('PATCH', f'/api/v1/courses/{HOMEROOM_COURSE_ID}/assignments/12345'),
        ('DELETE', f'/api/v1/courses/{HOMEROOM_COURSE_ID}/pages/agenda'),
        ('PUT', f'/api/v1/courses/{HOMEROOM_COURSE_ID}/modules/5'),
        ('POST', f'/api/v1/courses/{HOMEROOM_COURSE_ID}/files'),
    ):
        try:
            validate_live_transport_path(blocked_method, blocked_path)
            raise AssertionError(f'expected blocked method: {blocked_method} {blocked_path}')
        except PermissionError:
            pass

    assert transport_has_no_fake_fallback()
    assert live_mode_blocks_without_approval() or _live_approved()
    print('PASS canvas connection manager self-test')
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Canvas live transport manager')
    sub = parser.add_subparsers(dest='cmd', required=True)
    sub.add_parser('status-report').set_defaults(func=command_status_report)
    sub.add_parser('self-test').set_defaults(func=lambda _args: command_self_test())
    args = parser.parse_args()
    raise SystemExit(args.func(args))
