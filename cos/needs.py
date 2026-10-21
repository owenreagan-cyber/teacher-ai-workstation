"""cos needs: what needs Owen, gathered from registered providers (never from the model).

An item is {"id", "kind", "title", "reason", "source", "created_at", "action"}:
  kind     "decision" (Needs your decision), "suggestion" (Suggested next steps), or "info"
  action   null, or one of
           {"type": "open_link", "label", "link_id"}  an https link; the URL goes in "resources"
                                                      (the window opens it by id, like sources)
           {"type": "page", "label", "page"}          a page of the Chief window (PAGES)
           {"type": "command", "label", "command"}    a command Owen can copy; nothing runs it

Providers, in order:
  config      Chief's own setup problems: no weather places, the home place unnamed, the web
              search key missing, auto web search off.
  owner_list  needs.json in the state folder, a file Owen (or a build report) writes:
                {"items": [{"id": "pick-sm5-title", "kind": "decision",
                            "title": "Pick the SM5 homework title",
                            "reason": "Canvas titles must match before Friday.",
                            "created_at": "2026-10-20T09:00:00-04:00",
                            "action": {"type": "page", "label": "Open Settings", "page": "settings"},
                            "resolved": false}]}
              "action" and "resolved" are optional. A resolved item disappears, and so does any
              item with the same id from another provider (a way to dismiss one). Chief never
              writes this file.
  canvas      bin/canvas-weekly-status --json, if it exists: its "action_items" ({kind, title,
              reason, deep_link}). Missing: one info item, "Canvas planner status isn't connected
              yet."
  harness     the latest real-model eval report (evals/reports/*/summary.json): a decision when
              it failed certification for a reason other than an uncommitted tree.

Items are deduplicated by id (the first provider wins). The model never creates, edits, or
ranks them: the order is provider order, then each provider's own order.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from cos.blocks import https_url, link_id
from cos.config import LEGACY_HOME_NAME, weather_places
from cos.tools import web_search

KINDS = ("decision", "suggestion", "info")
PAGES = ("today", "chat", "agents", "mac", "settings")
ID_RE = re.compile(r"[a-z0-9_.:-]{1,80}")
OWNER_FILE = "needs.json"
OWNER_FIELDS = {"id", "kind", "title", "reason", "created_at", "action", "resolved", "source"}
MAX_ITEMS = 50
CANVAS_COMMAND = "bin/canvas-weekly-status"
CANVAS_TIMEOUT_S = 20
UNCOMMITTED = "UNCOMMITTED CODE — not a certification run"
SEARCH_KEY_COMMAND = 'security add-generic-password -a "$USER" -s chief-search-brave -w'


class NeedError(Exception):
    pass


def _clean(value, cap: int, where: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NeedError(f"{where} must be text")
    return re.sub(r"\s+", " ", value).strip()[:cap]


def make_action(raw) -> tuple[dict | None, list[dict]]:
    """(action, resources) from a provider's action; an unusable one becomes no action."""
    if not isinstance(raw, dict):
        return None, []
    label = raw.get("label") if isinstance(raw.get("label"), str) and raw["label"].strip() else "Open"
    label = label.strip()[:40]
    kind = raw.get("type")
    if kind in ("open_link", "deep_link"):
        target = raw.get("url") if kind == "open_link" else raw.get("target")
        if isinstance(target, str) and target.startswith("chief://"):
            page = target.removeprefix("chief://").strip("/")
            return ({"type": "page", "label": label, "page": page}, []) if page in PAGES else (None, [])
        url = https_url(target)
        if url is None:
            return None, []
        lid = link_id(url)
        return {"type": "open_link", "label": label, "link_id": lid}, [{"id": lid, "url": url}]
    if kind == "page" and raw.get("page") in PAGES:
        return {"type": "page", "label": label, "page": raw["page"]}, []
    if kind == "command" and isinstance(raw.get("command"), str) and raw["command"].strip():
        return {"type": "command", "label": label, "command": raw["command"].strip()[:200]}, []
    return None, []


def item(id_: str, kind: str, title: str, reason: str, source: str, created_at: str,
         action=None) -> tuple[dict, list[dict]]:
    if not ID_RE.fullmatch(id_):
        raise NeedError(f"id {id_!r} must be 1-80 of a-z 0-9 _ . : -")
    if kind not in KINDS:
        raise NeedError(f"kind must be one of {', '.join(KINDS)}")
    act, resources = make_action(action)
    return ({"id": id_, "kind": kind, "title": _clean(title, 120, "title"),
             "reason": _clean(reason, 300, "reason"), "source": source,
             "created_at": str(created_at)[:40], "action": act}, resources)


# ----------------------------------------------------------------------------- providers

def config_provider(config, ctx, now: str) -> list[tuple[dict, list]]:
    out = []
    places = weather_places(config)
    if not places:
        out.append(item("config:places-missing", "suggestion", "Add your weather places",
                         "Chief has no places for the weather. Add home and work in Settings.",
                         "config", now, {"type": "page", "label": "Open Settings", "page": "settings"}))
    elif "home" in places and places["home"].name == LEGACY_HOME_NAME:
        out.append(item("config:home-unnamed", "suggestion", "Name your home place",
                        "Weather says \"Home\" because the home place has no name yet.",
                        "config", now, {"type": "page", "label": "Open Settings", "page": "settings"}))
    if not search_key_present(config, ctx):
        out.append(item("config:search-key", "suggestion", "Store the web search key",
                        "Web search needs its Brave API key in the Keychain. The command prompts for "
                        "it and never echoes it.", "config", now,
                        {"type": "command", "label": "Copy command", "command": SEARCH_KEY_COMMAND}))
    if not config.auto_search:
        out.append(item("config:auto-search-off", "info", "Auto web search is off",
                        "Chief searches only when you type \"search …\".", "config", now,
                        {"type": "page", "label": "Open Settings", "page": "settings"}))
    return out


def search_key_present(config, ctx) -> bool:
    """Whether the Keychain holds the search key, without reading the secret (no -w)."""
    if config.fixture_dir:
        return (config.fixture_dir / "search.json").exists()
    try:
        res = ctx.run([web_search.SECURITY, "find-generic-password", "-s", web_search.KEYCHAIN_SERVICE],
                      timeout=5)
    except Exception:  # noqa: BLE001 - unknown means "not set up"
        return False
    return res.returncode == 0


def owner_provider(state_dir: Path) -> tuple[list[tuple[dict, list]], set[str]]:
    """(items, resolved ids) from needs.json. A damaged file is one info item, never a crash."""
    path = state_dir / OWNER_FILE
    if not path.exists():
        return [], set()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        entries = data.get("items") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            raise NeedError('needs.json must be {"items": [...]}')
        out, resolved = [], set()
        for i, e in enumerate(entries[:MAX_ITEMS]):
            if not isinstance(e, dict):
                raise NeedError(f"items[{i}] must be an object")
            unknown = set(e) - OWNER_FIELDS
            if unknown:
                raise NeedError(f"items[{i}] has unknown keys {sorted(unknown)}")
            if e.get("resolved") is True:
                if isinstance(e.get("id"), str):
                    resolved.add(e["id"])
                continue
            out.append(item(str(e.get("id")), e.get("kind"), e.get("title"), e.get("reason"),
                            "owner_list", e.get("created_at") or "", e.get("action")))
        return out, resolved
    except (OSError, ValueError, NeedError) as e:
        reason = str(e) if isinstance(e, NeedError) else f"it isn't valid JSON ({type(e).__name__})"
        return [item("owner:unreadable", "info", "needs.json couldn't be read", reason[:300],
                     "owner_list", datetime.now().astimezone().isoformat(timespec="seconds"))], set()


def _canvas_id(entry: dict) -> str:
    raw = entry.get("id")
    if isinstance(raw, str):
        slug = re.sub(r"[^a-z0-9_.:-]+", "-", raw.lower()).strip("-")[:70]
        if slug:
            return f"canvas:{slug}"
    digest = hashlib.sha256(f"{entry.get('kind')}\x1f{entry.get('title')}".encode()).hexdigest()[:12]
    return f"canvas:{digest}"


def canvas_items(data, now: str) -> list[tuple[dict, list]]:
    entries = data.get("action_items") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise NeedError("no action_items list")
    out = []
    for e in entries[:MAX_ITEMS]:
        if not isinstance(e, dict):
            continue
        kind = e.get("kind") if e.get("kind") in KINDS else "info"
        deep = e.get("deep_link")
        action = {"type": "deep_link", "label": "Open in planner", "target": deep} if deep else None
        try:
            out.append(item(_canvas_id(e), kind, e.get("title"), e.get("reason") or "From the Canvas planner.",
                            "canvas", e.get("created_at") or now, action))
        except NeedError:
            continue  # one bad action item never hides the rest
    return out


def canvas_provider(config, ctx, now: str) -> list[tuple[dict, list]]:
    not_connected = [item("canvas:not-connected", "info", "Canvas planner status isn't connected yet.",
                          f"{CANVAS_COMMAND} is not in the repo yet.", "canvas", now)]
    if config.fixture_dir:
        path = config.fixture_dir / "canvas-weekly-status.json"
        if not path.exists():
            return not_connected
        return canvas_items(json.loads(path.read_text(encoding="utf-8")), now)
    command = Path(config.repo_root) / CANVAS_COMMAND
    if not command.is_file():
        return not_connected
    try:
        res = ctx.run([str(command), "--json"], timeout=CANVAS_TIMEOUT_S, cwd=Path(config.repo_root))
        if res.returncode != 0:
            raise NeedError(f"it exited with {res.returncode}")
        return canvas_items(json.loads(res.stdout), now)
    except Exception as e:  # noqa: BLE001 - a broken planner is one info item
        reason = str(e) if isinstance(e, NeedError) else type(e).__name__
        return [item("canvas:unreadable", "info", "Canvas planner status couldn't be read",
                     f"{CANVAS_COMMAND} --json: {reason}"[:300], "canvas", now)]


def latest_real_report(reports_root: Path) -> dict | None:
    best = None
    for path in reports_root.glob("*/summary.json"):
        try:
            s = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        run = s.get("run") if isinstance(s, dict) else None
        if not isinstance(run, dict) or run.get("model_mode") != "real":
            continue
        if best is None or str(run.get("started") or "") > str(best["run"].get("started") or ""):
            best = s
    return best


def harness_provider(config, now: str) -> list[tuple[dict, list]]:
    if config.fixture_dir:
        path = config.fixture_dir / "harness-summary.json"
        summary = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    else:
        summary = latest_real_report(Path(config.repo_root) / "evals/reports")
    if not summary or summary.get("certification") is not False:
        return []
    reasons = [str(r) for r in summary.get("certification_reasons") or [] if r != UNCOMMITTED]
    if not reasons:
        return []  # only an uncommitted tree: a development run, not a failed certification
    run = summary.get("run") or {}
    run_id = re.sub(r"[^a-z0-9_.-]+", "-", str(run.get("run_id") or "latest").lower())[:50]
    return [item(f"harness:certification:{run_id}", "decision", "Latest real-model eval didn't certify",
                 "; ".join(reasons)[:300], "harness", run.get("ended") or run.get("started") or now,
                 {"type": "command", "label": "Copy command",
                  "command": "python3.12 evals/harness/run.py --model real"})]


# ----------------------------------------------------------------------------- gather

def gather(config, ctx, now: datetime) -> dict:
    """{"items", "resources", "providers"}: deduplicated by id, resolved ids removed."""
    stamp = now.isoformat(timespec="seconds")
    collected: list[tuple[str, list[tuple[dict, list]]]] = []
    providers: dict[str, dict] = {}
    resolved: set[str] = set()

    def run(name, fn):
        try:
            got = fn()
            providers[name] = {"ok": True, "count": len(got)}
            collected.append((name, got))
        except Exception as e:  # noqa: BLE001 - one failing provider never hides the others
            providers[name] = {"ok": False, "count": 0, "reason": f"{type(e).__name__}"}

    run("config", lambda: config_provider(config, ctx, stamp))

    def owner():
        got, done = owner_provider(Path(config.state_dir))
        resolved.update(done)
        return got
    run("owner_list", owner)
    run("canvas", lambda: canvas_provider(config, ctx, stamp))
    run("harness", lambda: harness_provider(config, stamp))

    items, resources, seen = [], {}, set()
    for _name, got in collected:
        for it, res in got:
            if it["id"] in seen or it["id"] in resolved:
                continue
            seen.add(it["id"])
            items.append(it)
            for r in res:
                resources[r["id"]] = r
    items = items[:MAX_ITEMS]
    used = {it["action"]["link_id"] for it in items if it["action"] and it["action"]["type"] == "open_link"}
    return {"items": items, "resources": [r for k, r in resources.items() if k in used], "providers": providers}
