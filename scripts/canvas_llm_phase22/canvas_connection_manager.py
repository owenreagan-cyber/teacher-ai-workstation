#!/usr/bin/env python3
"""Phase 22 live Canvas API transport — Q1W2 allowlisted POST endpoints only."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
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

ALLOWED_LIVE_COURSE_IDS = {HOMEROOM_COURSE_ID, MATH_COURSE_ID, READING_COURSE_ID}
ALLOWED_POST_PATH_RE = re.compile(
    r'^/api/v1/courses/(?P<course_id>\d+)/(pages|assignments)$'
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
    'discussion_topics',
    'announcements',
}
MOCK_LIVE_STORE: dict[str, dict[str, Any]] = {'pages': {}, 'assignments': {}}


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


def _validate_path(method: str, path: str) -> None:
    lowered = path.lower()
    if any(marker in lowered for marker in BLOCKED_PATH_MARKERS):
        raise PermissionError(f'BLOCKED: endpoint touches a blocked Canvas area: {path}')
    upper = method.upper()
    if upper == 'POST':
        if not ALLOWED_POST_PATH_RE.match(path):
            raise PermissionError(f'BLOCKED: POST not allowlisted for live transport: {path}')
        course_id = int(ALLOWED_POST_PATH_RE.match(path).group('course_id'))  # type: ignore[union-attr]
        _validate_course(course_id)
    elif upper == 'GET':
        if not re.match(r'^/api/v1/courses/\d+/(pages/[^/]+|assignments/\d+|assignment_groups)$', path):
            raise PermissionError(f'BLOCKED: GET not allowlisted for live transport verification: {path}')


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

    def request(self, method: str, path: str, data: dict[str, Any] | None = None) -> Any:
        _validate_path(method, path)
        raise RuntimeError('MockPhase22CanvasClient.request is not used directly')


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
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            text = response.read().decode('utf-8')
            if not text:
                return {}
            return json.loads(text)

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

    def get_page(self, course_id: int, page_url: str) -> dict[str, Any]:
        return self.request('GET', f'/api/v1/courses/{course_id}/pages/{page_url}')

    def get_assignment(self, course_id: int, assignment_id: str) -> dict[str, Any]:
        return self.request('GET', f'/api/v1/courses/{course_id}/assignments/{assignment_id}')


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
