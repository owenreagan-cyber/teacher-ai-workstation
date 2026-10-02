"""Build summary.json and a self-contained report.html for one harness run. Stdlib only.

  python3.12 evals/harness/report.py <run-id> [--baseline <run-id>]   # rebuild a report

Inputs (evals/results/<run-id>/): results.jsonl, meta.json, resources.jsonl, and
optionally soak_fast_path.jsonl / long_session.jsonl (summarized in meta.json).
Outputs (evals/reports/<run-id>/): summary.json and report.html (no external
assets: inline CSS and SVG only).

Baseline: --baseline <run-id>, else the most recent earlier run in reports/
with the same model mode. The comparison lists new failures, fixed cases, and
any CERT whose status changed, with both git SHAs.
"""
from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path

from checks import CERTS

EVALS = Path(__file__).resolve().parents[1]
FAKE_LABEL = "fake model"


# ----------------------------------------------------------------------------- data

def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


def _pct(values) -> dict:
    vals = sorted(v for v in values if isinstance(v, (int, float)))
    if not vals:
        return {"n": 0}

    def p(q):
        return vals[max(0, min(len(vals) - 1, math.ceil(q / 100 * len(vals)) - 1))]
    return {"n": len(vals), "min": vals[0], "p50": p(50), "p95": p(95), "p99": p(99), "max": vals[-1],
            "mean": round(sum(vals) / len(vals), 1)}


def certs_from(records: list[dict], meta: dict) -> list[dict]:
    found = {cid: {"checked": 0, "violations": []} for cid in CERTS}
    for r in records:
        for c in r["checks"]:
            cid = c.get("cert")
            if cid in found:
                found[cid]["checked"] += 1
                if not c["ok"]:
                    found[cid]["violations"].append(f"{r['case_id']}#{r['turn']}: {c['reason']}")
    changes = meta.get("real_state_dir_changes") or []
    found["CERT-004"]["checked"] += 1
    if changes:
        found["CERT-004"]["violations"].append("real state directory changed: " + "; ".join(changes[:10]))
    for key in ("soak_fast_path", "long_session"):
        extra = meta.get(key)
        if extra:
            found["CERT-007"]["checked"] += 1
            if extra.get("audit_chain") not in ("ok", "uninitialized"):
                found["CERT-007"]["violations"].append(f"{key}: audit chain {extra.get('audit_chain')}")
    if meta.get("soak_fast_path"):
        for cid in ("CERT-001", "CERT-002", "CERT-003", "CERT-004", "CERT-008"):
            fails = meta["soak_fast_path"].get("cert_violations", {}).get(cid, 0)
            if fails:
                found[cid]["violations"].append(f"soak_fast_path: {fails} runs")
    return [{"id": cid, "title": CERTS[cid], "status": "FAIL" if v["violations"] else "PASS",
             "checked": v["checked"], "violations": len(v["violations"]), "examples": v["violations"][:10]}
            for cid, v in found.items()]


def summarize(records: list[dict], meta: dict, resources: list[dict], baseline: dict | None) -> dict:
    cases: dict[str, dict] = {}
    for r in records:
        c = cases.setdefault(r["case_id"], {"suite": r["suite"], "passed": True, "turns": 0,
                                            "failed_checks": [], "wall_ms": 0})
        c["turns"] += 1
        c["wall_ms"] += r["wall_ms"] or 0
        if not r["passed"]:
            c["passed"] = False
            c["failed_checks"] += [f"#{r['turn']} {x['name']}" for x in r["checks"] if not x["ok"]]
    suites: dict[str, dict] = {}
    for cid, c in cases.items():
        s = suites.setdefault(c["suite"], {"cases": 0, "passed": 0, "failed": 0, "turns": 0})
        s["cases"] += 1
        s["turns"] += c["turns"]
        s["passed" if c["passed"] else "failed"] += 1
    for s in suites.values():
        s["pass_rate"] = round(s["passed"] / s["cases"], 4) if s["cases"] else None

    global_checks: dict[str, dict] = {}
    for r in records:
        for x in r["checks"]:
            g = global_checks.setdefault(x["name"], {"checked": 0, "failed": 0})
            g["checked"] += 1
            g["failed"] += not x["ok"]

    asks = [r for r in records if r["command"] == "ask" and r["exit_code"] == 0]
    latency = {
        "fast_path_total_ms": _pct(r["total_ms"] for r in asks if r["fast_path"]),
        "fast_path_wall_ms": _pct(r["wall_ms"] for r in asks if r["fast_path"]),
        "model_total_ms": _pct(r["total_ms"] for r in asks if not r["fast_path"]),
        "model_wall_ms": _pct(r["wall_ms"] for r in asks if not r["fast_path"]),
        "all_wall_ms": _pct(r["wall_ms"] for r in records),
        "by_suite": {s: _pct(r["wall_ms"] for r in records if r["suite"] == s) for s in suites},
        # fake-model runs: model-path figures measure the scripted fake, not real model speed
        "model_path_source": FAKE_LABEL if meta.get("model_mode") == "fake" else "real model",
    }
    mem = [x["memory_free_pct"] for x in resources if isinstance(x.get("memory_free_pct"), int)]
    models: dict[str, int] = {}
    for x in resources:
        for m in x.get("ollama_models") or []:
            models[m.get("name")] = max(models.get(m.get("name"), 0), m.get("size") or 0)
    res_summary = {"samples": len(resources), "memory_free_pct": _pct(mem),
                   "ollama_models_max_size_bytes": models}

    certs = certs_from(records, meta)
    total_cases = len(cases)
    summary = {
        "run": {k: meta.get(k) for k in ("run_id", "git_sha", "dirty_paths", "model_mode", "model_name",
                                          "started", "ended", "seconds", "suites", "case_count", "argv",
                                          "tz", "real_state_dir_exists", "real_state_dir_changes")},
        # True only for a run of committed code (clean tree); runs without the flag count as false
        "certification": meta.get("certification") is True,
        "certs": certs,
        "overall": {"cases": total_cases, "passed": sum(c["passed"] for c in cases.values()),
                    "turns": len(records),
                    "pass_rate": round(sum(c["passed"] for c in cases.values()) / total_cases, 4)
                    if total_cases else None},
        "suites": dict(sorted(suites.items())),
        "global_checks": global_checks,
        "latency_ms": latency,
        "soak_fast_path": meta.get("soak_fast_path"),
        "long_session": meta.get("long_session"),
        "resources": res_summary,
        "cases": cases,
        "judge": {"status": "not_run"},
    }
    summary["baseline"] = compare(summary, baseline)
    return summary


def compare(summary: dict, baseline: dict | None) -> dict | None:
    if not baseline:
        return None
    now, then = summary["cases"], baseline.get("cases", {})
    new_fail = sorted(c for c, v in now.items() if not v["passed"] and then.get(c, {}).get("passed"))
    fixed = sorted(c for c, v in now.items() if v["passed"] and c in then and not then[c]["passed"])
    still = sorted(c for c, v in now.items() if not v["passed"] and c in then and not then[c]["passed"])
    new_cases = sorted(set(now) - set(then))
    bc = {c["id"]: c["status"] for c in baseline.get("certs", [])}
    cert_changes = [{"id": c["id"], "before": bc.get(c["id"]), "after": c["status"]}
                    for c in summary["certs"] if bc.get(c["id"]) != c["status"]]
    return {"run_id": baseline["run"]["run_id"], "git_sha": baseline["run"].get("git_sha"),
            "model_mode": baseline["run"].get("model_mode"), "new_failures": new_fail, "fixed": fixed,
            "still_failing": still, "new_cases": new_cases, "cert_changes": cert_changes,
            "pass_rate_before": baseline.get("overall", {}).get("pass_rate")}


def find_baseline(reports_root: Path, run_id: str, mode: str, explicit: str | None) -> dict | None:
    if explicit:
        path = reports_root / explicit / "summary.json"
        if not path.exists():
            raise SystemExit(f"baseline {explicit} not found at {path}")
        return json.loads(path.read_text(encoding="utf-8"))
    best = None
    for path in reports_root.glob("*/summary.json"):
        if path.parent.name == run_id:
            continue
        try:
            s = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if s.get("run", {}).get("model_mode") != mode:
            continue
        started = s["run"].get("started") or ""
        if best is None or started > best["run"].get("started", ""):
            best = s
    return best


# ----------------------------------------------------------------------------- html

CSS = """
:root{color-scheme:light;--bg:#fcfcfb;--panel:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--muted:#8a8984;
--rule:#e4e3df;--grid:#efeeea;--s1:#2a78d6;--s2:#eb6834;--good:#0ca30c;--bad:#d03b3b;--code:#f3f2ef}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){color-scheme:dark;--bg:#1a1a19;
--panel:#222220;--ink:#ffffff;--ink2:#c3c2b7;--muted:#8f8e86;--rule:#34332f;--grid:#2b2a27;--s1:#3987e5;
--s2:#d95926;--code:#2b2a27}}
:root[data-theme="dark"]{color-scheme:dark;--bg:#1a1a19;--panel:#222220;--ink:#ffffff;--ink2:#c3c2b7;
--muted:#8f8e86;--rule:#34332f;--grid:#2b2a27;--s1:#3987e5;--s2:#d95926;--code:#2b2a27}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif}
main{max-width:1100px;margin:0 auto;padding:24px 16px 64px}h1{font-size:22px;margin:0 0 4px}
h2{font-size:16px;margin:32px 0 10px;padding-top:8px;border-top:1px solid var(--rule)}
.meta{color:var(--ink2);font-size:13px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px}
.tile{background:var(--panel);border:1px solid var(--rule);border-radius:8px;padding:10px 12px}
.tile b{display:block;font-size:20px}.tile span{color:var(--ink2);font-size:12px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:6px 8px;
border-bottom:1px solid var(--rule);vertical-align:top}th{color:var(--ink2);font-weight:600}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}
.pass,.fail{font-weight:700;white-space:nowrap}.pass{color:var(--good)}.fail{color:var(--bad)}
code,pre{background:var(--code);border-radius:4px;font:12px ui-monospace,Menlo,monospace}
pre{padding:8px;white-space:pre-wrap;word-break:break-word;margin:4px 0;max-height:220px;overflow:auto}
.scroll{overflow-x:auto}svg{display:block;max-width:100%;height:auto}
svg text{fill:var(--ink2);font-size:11px}svg .axis{stroke:var(--rule)}svg .gridl{stroke:var(--grid)}
.legend{display:flex;gap:16px;color:var(--ink2);font-size:12px;margin:4px 0}
.sw{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:6px;vertical-align:-1px}
details summary{cursor:pointer;color:var(--ink2)}.note{color:var(--muted);font-size:12px}
.banner{background:var(--bad);color:#fff;font-weight:700;font-size:16px;border-radius:8px;padding:12px 16px;
margin:0 0 16px}.banner span{display:block;font-weight:400;font-size:12px;margin-top:4px;word-break:break-word}
"""


def e(x) -> str:
    return html.escape(str(x if x is not None else ""), quote=True)


def status_cell(ok: bool, yes="PASS", no="FAIL") -> str:
    return f'<span class="pass">✓ {yes}</span>' if ok else f'<span class="fail">✕ {no}</span>'


def hbar_chart(rows: list[tuple[str, float, str]], width=640, unit="%", vmax=None) -> str:
    """rows: (label, value, tooltip). Single series, value labels at bar ends."""
    if not rows:
        return '<p class="note">No data.</p>'
    left, bar_h, gap, right = 130, 18, 8, 60
    vmax = vmax or max(v for _, v, _ in rows) or 1
    h = len(rows) * (bar_h + gap) + 24
    plot = width - left - right
    out = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="bar chart">']
    for frac in (0, .25, .5, .75, 1):
        x = left + plot * frac
        out.append(f'<line class="gridl" x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{h - 18}"/>'
                   f'<text x="{x:.1f}" y="{h - 4}" text-anchor="middle">{e(_fmt(vmax * frac, unit))}</text>')
    for i, (label, v, tip) in enumerate(rows):
        y = i * (bar_h + gap) + 4
        w = max(2, plot * (v / vmax))
        out.append(f'<g><title>{e(tip)}</title><text x="{left - 8}" y="{y + 13}" text-anchor="end">{e(label)}</text>'
                   f'<rect x="{left}" y="{y}" width="{w:.1f}" height="{bar_h}" rx="4" fill="var(--s1)"/>'
                   f'<text x="{left + w + 6:.1f}" y="{y + 13}">{e(_fmt(v, unit))}</text></g>')
    out.append("</svg>")
    return "".join(out)


def _fmt(v, unit) -> str:
    if unit == "%":
        return f"{v:.0f}%"
    if unit == "ms":
        return f"{v / 1000:.1f}s" if v >= 10_000 else f"{v:.0f}ms"
    if unit == "B":
        return f"{v / 1e6:.1f}MB" if v >= 1e6 else f"{v / 1e3:.0f}KB"
    return f"{v:g}"


def range_chart(rows: list[tuple[str, dict]], width=640, note="") -> str:
    """Per-suite latency: p50 dot and p50-p95 range on a log axis (ms)."""
    rows = [(l, p) for l, p in rows if p.get("n")]
    if not rows:
        return '<p class="note">No data.</p>'
    left, row_h, right = 130, 26, 30
    lo = max(1, min(p["min"] for _, p in rows))
    hi = max(p["p95"] for _, p in rows) * 1.2 or 10
    lo_l, hi_l = math.log10(max(1, lo / 1.5)), math.log10(max(hi, lo * 10))
    plot = width - left - right
    h = len(rows) * row_h + 30

    def x(v):
        return left + plot * (math.log10(max(v, 1)) - lo_l) / (hi_l - lo_l)
    out = [f'<svg viewBox="0 0 {width} {h}" role="img" aria-label="latency by suite, log scale">']
    for k in range(int(math.floor(lo_l)), int(math.ceil(hi_l)) + 1):
        v = 10 ** k
        if lo_l <= k <= hi_l:
            out.append(f'<line class="gridl" x1="{x(v):.1f}" y1="0" x2="{x(v):.1f}" y2="{h - 22}"/>'
                       f'<text x="{x(v):.1f}" y="{h - 6}" text-anchor="middle">{e(_fmt(v, "ms"))}</text>')
    for i, (label, p) in enumerate(rows):
        y = i * row_h + 14
        tip = f"{label}: p50 {p['p50']} ms · p95 {p['p95']} ms · max {p['max']} ms (n={p['n']})"
        out.append(f'<g><title>{e(tip)}</title><rect x="{left}" y="{y - 11}" width="{plot}" height="22" fill="transparent"/>'
                   f'<text x="{left - 8}" y="{y + 4}" text-anchor="end">{e(label)}</text>'
                   f'<line x1="{x(p["p50"]):.1f}" y1="{y}" x2="{x(p["p95"]):.1f}" y2="{y}" stroke="var(--s2)" stroke-width="2"/>'
                   f'<circle cx="{x(p["p95"]):.1f}" cy="{y}" r="4" fill="var(--s2)" stroke="var(--panel)" stroke-width="2"/>'
                   f'<circle cx="{x(p["p50"]):.1f}" cy="{y}" r="5" fill="var(--s1)" stroke="var(--panel)" stroke-width="2"/></g>')
    out.append("</svg>")
    return ('<div class="legend"><span><i class="sw" style="background:var(--s1)"></i>p50</span>'
            '<span><i class="sw" style="background:var(--s2)"></i>p95</span><span>log scale, wall time' + e(note) + '</span></div>'
            + "".join(out))


def line_chart(points: list[tuple[float, float]], xlabel: str, unit: str, width=640, height=200) -> str:
    """Single series line with point tooltips."""
    pts = [(a, b) for a, b in points if isinstance(a, (int, float)) and isinstance(b, (int, float))]
    if len(pts) < 2:
        return '<p class="note">Not enough samples for a chart.</p>'
    left, right, top, bottom = 56, 16, 10, 34
    xs, ys = [a for a, _ in pts], [b for _, b in pts]
    x0, x1 = min(xs), max(xs) if max(xs) > min(xs) else min(xs) + 1
    y1 = max(ys) * 1.1 or 1
    pw, ph = width - left - right, height - top - bottom

    def px(a):
        return left + pw * (a - x0) / (x1 - x0)

    def py(b):
        return top + ph * (1 - b / y1)
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="line chart">']
    for frac in (0, .5, 1):
        yy = top + ph * (1 - frac)
        out.append(f'<line class="gridl" x1="{left}" y1="{yy:.1f}" x2="{width - right}" y2="{yy:.1f}"/>'
                   f'<text x="{left - 6}" y="{yy + 4:.1f}" text-anchor="end">{e(_fmt(y1 * frac, unit))}</text>')
    out.append(f'<text x="{left}" y="{height - 6}">{e(_fmt(x0, ""))}</text>'
               f'<text x="{width - right}" y="{height - 6}" text-anchor="end">{e(_fmt(x1, ""))} {e(xlabel)}</text>')
    path = " ".join(f"{'M' if i == 0 else 'L'}{px(a):.1f},{py(b):.1f}" for i, (a, b) in enumerate(pts))
    out.append(f'<path d="{path}" fill="none" stroke="var(--s1)" stroke-width="2" stroke-linejoin="round"/>')
    step = max(1, len(pts) // 60)
    for a, b in pts[::step]:
        out.append(f'<g><title>{e(xlabel)} {a:g}: {e(_fmt(b, unit))}</title>'
                   f'<circle cx="{px(a):.1f}" cy="{py(b):.1f}" r="8" fill="transparent"/>'
                   f'<circle cx="{px(a):.1f}" cy="{py(b):.1f}" r="2.5" fill="var(--s1)"/></g>')
    out.append("</svg>")
    return "".join(out)


def histogram(values: list[float], unit="ms", width=640, height=180, bins=30) -> str:
    vals = sorted(v for v in values if isinstance(v, (int, float)))
    if len(vals) < 2:
        return '<p class="note">No soak data.</p>'
    lo, hi = vals[0], vals[min(len(vals) - 1, int(len(vals) * 0.995))]
    hi = hi if hi > lo else lo + 1
    counts = [0] * bins
    for v in vals:
        counts[min(bins - 1, int((min(v, hi) - lo) / (hi - lo) * bins))] += 1
    left, bottom, top = 40, 30, 8
    pw, ph = width - left - 10, height - bottom - top
    cmax = max(counts)
    bw = pw / bins
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="latency histogram">']
    for i, c in enumerate(counts):
        h = ph * c / cmax
        a, b = lo + (hi - lo) * i / bins, lo + (hi - lo) * (i + 1) / bins
        out.append(f'<g><title>{a:.0f}–{b:.0f} {unit}: {c} runs</title>'
                   f'<rect x="{left + i * bw + 1:.1f}" y="{top + ph - h:.1f}" width="{max(1, bw - 2):.1f}" '
                   f'height="{max(h, 0):.1f}" rx="2" fill="var(--s1)"/></g>')
    out.append(f'<line class="axis" x1="{left}" y1="{top + ph}" x2="{width - 10}" y2="{top + ph}"/>'
               f'<text x="{left}" y="{height - 8}">{e(_fmt(lo, unit))}</text>'
               f'<text x="{width - 10}" y="{height - 8}" text-anchor="end">{e(_fmt(hi, unit))} (p99.5, longer tail clipped)</text>'
               f'<text x="{left - 6}" y="{top + 10}" text-anchor="end">{cmax}</text></svg>')
    return "".join(out)


def pct_row(label, p) -> str:
    if not p or not p.get("n"):
        return f"<tr><td>{e(label)}</td><td colspan='6' class='note'>no data</td></tr>"
    return (f"<tr><td>{e(label)}</td><td class='num'>{p['n']}</td><td class='num'>{p['p50']}</td>"
            f"<td class='num'>{p['p95']}</td><td class='num'>{p['p99']}</td><td class='num'>{p['max']}</td>"
            f"<td class='num'>{p['mean']}</td></tr>")


def card_ms(p) -> str:
    """p50 for a summary card; "—" when the run had no such invocations (not "0ms")."""
    return _fmt(p["p50"], "ms") if p and p.get("n") else "—"


PCT_HEAD = ("<tr><th>Measure (ms)</th><th class='num'>n</th><th class='num'>p50</th><th class='num'>p95</th>"
            "<th class='num'>p99</th><th class='num'>max</th><th class='num'>mean</th></tr>")


def render_html(summary: dict, records: list[dict], resources: list[dict], soak_rows: list[dict]) -> str:
    run = summary["run"]
    o = summary["overall"]
    fake = run.get("model_mode") == "fake"
    mp = f" ({FAKE_LABEL})" if fake else ""  # every model-path figure in a fake run says so
    parts = [f"<!doctype html><html lang='en'><head><meta charset='utf-8'>"
             f"<meta name='viewport' content='width=device-width,initial-scale=1'>"
             f"<title>Chief Certification Report</title><style>{CSS}</style></head><body><main>",
             "" if summary["certification"] else
             ("<div class='banner'>UNCOMMITTED CODE — not a certification run"
              + (f"<span>{e(len(run['dirty_paths']))} uncommitted path(s): "
                 + e(", ".join(run["dirty_paths"][:8])) + ("…" if len(run["dirty_paths"]) > 8 else "")
                 + "</span>" if run.get("dirty_paths") else "") + "</div>"),
             f"<h1>Chief certification report</h1><p class='meta'>Run <code>{e(run['run_id'])}</code> · "
             f"git <code>{e(run['git_sha'])}</code> · model {e(run['model_mode'])} ({e(run['model_name'])}) · "
             f"{e(run['started'])} → {e(run['ended'])} ({e(run['seconds'])} s) · synthetic fixtures only</p>"]

    parts.append("<h2>Invariants</h2><table><tr><th>ID</th><th>Status</th><th class='num'>Checked</th>"
                 "<th>Invariant</th><th>Examples</th></tr>")
    for c in summary["certs"]:
        ex = "".join(f"<div><code>{e(x)}</code></div>" for x in c["examples"][:3])
        note = " <span class='note'>(not exercised)</span>" if c["checked"] == 0 else ""
        parts.append(f"<tr><td><b>{c['id']}</b></td><td>{status_cell(c['status'] == 'PASS')}</td>"
                     f"<td class='num'>{c['checked']}</td><td>{e(c['title'])}{note}</td><td>{ex}</td></tr>")
    parts.append("</table>")

    parts.append("<div class='grid' style='margin-top:16px'>"
                 f"<div class='tile'><b>{o['passed']}/{o['cases']}</b><span>cases pass "
                 f"({(o['pass_rate'] or 0) * 100:.1f}%)</span></div>"
                 f"<div class='tile'><b>{o['turns']}</b><span>cos invocations checked</span></div>"
                 f"<div class='tile'><b>{card_ms(summary['latency_ms']['fast_path_wall_ms'])}</b>"
                 f"<span>fast-path p50 (wall)</span></div>"
                 f"<div class='tile'><b>{card_ms(summary['latency_ms']['model_wall_ms'])}</b>"
                 f"<span>model-path p50 (wall){mp}</span></div></div>")

    b = summary.get("baseline")
    parts.append("<h2>Compared with baseline</h2>")
    if not b:
        parts.append("<p class='note'>No earlier run with the same model mode; nothing to compare.</p>")
    else:
        cc = "".join(f"<li>{e(x['id'])}: {e(x['before'])} → {e(x['after'])}</li>" for x in b["cert_changes"]) or "<li>none</li>"
        parts.append(f"<p class='meta'>Baseline <code>{e(b['run_id'])}</code> at git <code>{e(b['git_sha'])}</code> "
                     f"→ this run at git <code>{e(run['git_sha'])}</code>.</p>"
                     f"<table><tr><th>New failures ({len(b['new_failures'])})</th><th>Fixed ({len(b['fixed'])})</th>"
                     f"<th>CERT changes</th></tr><tr><td>{'<br>'.join(e(x) for x in b['new_failures']) or 'none'}</td>"
                     f"<td>{'<br>'.join(e(x) for x in b['fixed']) or 'none'}</td><td><ul>{cc}</ul></td></tr></table>")

    parts.append("<h2>Pass rate by suite</h2>")
    rows = [(s, 100 * (v["pass_rate"] or 0), f"{s}: {v['passed']}/{v['cases']} cases pass")
            for s, v in summary["suites"].items()]
    parts.append(f"<div class='scroll'>{hbar_chart(rows, vmax=100)}</div>")
    parts.append("<table><tr><th>Suite</th><th class='num'>Cases</th><th class='num'>Pass</th>"
                 "<th class='num'>Fail</th><th class='num'>Turns</th></tr>")
    for s, v in summary["suites"].items():
        parts.append(f"<tr><td>{e(s)}</td><td class='num'>{v['cases']}</td><td class='num'>{v['passed']}</td>"
                     f"<td class='num'>{v['failed']}</td><td class='num'>{v['turns']}</td></tr>")
    parts.append("</table>")

    failed = [r for r in records if not r["passed"]]
    parts.append(f"<h2>Failed cases ({len({r['case_id'] for r in failed})})</h2>")
    if not failed:
        parts.append("<p class='note'>None.</p>")
    for r in failed:
        bad = "".join(f"<li><b>{e(c['name'])}</b>{' [' + e(c['cert']) + ']' if c.get('cert') else ''}: "
                      f"{e(c['reason'])}</li>" for c in r["checks"] if not c["ok"])
        parts.append(f"<details open><summary><b>{e(r['case_id'])}</b> #{r['turn']} · {e(r['suite'])} · "
                     f"{e(r['command'])} · exit {e(r['exit_code'])}</summary><ul>{bad}</ul>"
                     f"<div>Prompt</div><pre>{e(r['prompt'][:600])}</pre><div>Answer</div>"
                     f"<pre>{e(r['answer'][:1500]) or '(none)'}</pre>"
                     f"<div class='note'>tools {e(r['tools_used'])} · tool calls {e(r['tool_calls'])} · "
                     f"model calls {r['model_calls']} · fast path {e(r['fast_path'])}</div>"
                     + (f"<pre>{e(r['stderr_tail'][-400:])}</pre>" if r.get("stderr_tail") else "") + "</details>")

    parts.append("<h2>Latency</h2>")
    lat = summary["latency_ms"]
    if fake:
        parts.append(f"<p class='meta'><b>Model-path figures here are from the scripted {FAKE_LABEL}</b>; "
                     "they are not real model speed. Run with <code>--model real</code> for that.</p>")
    parts.append(f"<div class='scroll'>{range_chart(list(lat['by_suite'].items()), note=mp)}</div>")
    parts.append("<table>" + PCT_HEAD + pct_row("fast path, cos total_ms", lat["fast_path_total_ms"])
                 + pct_row("fast path, wall (incl. process start)", lat["fast_path_wall_ms"])
                 + pct_row(f"model path{mp}, cos total_ms", lat["model_total_ms"])
                 + pct_row(f"model path{mp}, wall", lat["model_wall_ms"]) + "</table>")
    slow = sorted(records, key=lambda r: r["wall_ms"] or 0, reverse=True)[:20]
    parts.append(f"<h3>20 slowest{mp}</h3><table><tr><th>Case</th><th>Suite</th><th>Prompt</th>"
                 "<th class='num'>wall ms</th><th class='num'>cos ms</th><th class='num'>model calls</th></tr>")
    for r in slow:
        parts.append(f"<tr><td>{e(r['case_id'])} #{r['turn']}</td><td>{e(r['suite'])}</td>"
                     f"<td>{e(r['prompt'][:80])}</td><td class='num'>{r['wall_ms']}</td>"
                     f"<td class='num'>{e(r['total_ms'])}</td><td class='num'>{r['model_calls']}</td></tr>")
    parts.append("</table>")

    soak = summary.get("soak_fast_path")
    parts.append("<h2>Fast-path soak</h2>")
    if not soak:
        parts.append("<p class='note'>Not run (use --repeat-fast-path N).</p>")
    else:
        nd = soak["nondeterministic_cases"]
        parts.append(f"<p>{soak['runs']} runs ({soak['cases']} cases × {soak['repeat']}) in {soak['seconds']} s · "
                     f"{status_cell(soak['failing_runs'] == 0, 'no failing runs', str(soak['failing_runs']) + ' failing runs')} · "
                     f"{status_cell(not nd, 'deterministic', str(len(nd)) + ' non-deterministic cases')} · "
                     f"audit chain {e(soak['audit_chain'])}</p>")
        parts.append(f"<div class='scroll'>{histogram([r['wall_ms'] for r in soak_rows])}</div>")
        parts.append("<table>" + PCT_HEAD + pct_row("wall", soak["wall_ms"]) + pct_row("cos total_ms", soak["total_ms"])
                     + "</table>")
        if nd:
            parts.append("<pre>" + e(json.dumps(nd, indent=1)) + "</pre>")

    ls = summary.get("long_session")
    parts.append("<h2>Long session</h2>")
    if not ls:
        parts.append("<p class='note'>Not run (use --long-session N).</p>")
    else:
        parts.append(f"<p>{ls['turns_recorded']}/{ls['turns_requested']} turns recorded (fake model) in "
                     f"{ls['seconds']} s · skipped lines {ls['skipped_lines']} · failing turns {ls['failing_turns']} · "
                     f"audit chain {e(ls['audit_chain'])}</p>")
        sm = ls["samples"]
        parts.append("<h3>Session file size</h3>" + line_chart([(s["turn"], s["file_bytes"]) for s in sm], "turn", "B"))
        parts.append("<h3><code>cos history</code> wall time</h3>"
                     + line_chart([(s["turn"], s["cos_history_wall_ms"]) for s in sm], "turn", "ms"))
        parts.append("<h3>Ask wall time at sample points</h3>"
                     + line_chart([(s["turn"], s["ask_wall_ms"]) for s in sm], "turn", "ms"))
        parts.append("<details><summary>Samples</summary><table><tr><th class='num'>turn</th>"
                     "<th class='num'>file bytes</th><th class='num'>load ms (in-process)</th>"
                     "<th class='num'>cos history ms</th><th class='num'>ask ms</th></tr>"
                     + "".join(f"<tr><td class='num'>{s['turn']}</td><td class='num'>{s['file_bytes']}</td>"
                               f"<td class='num'>{s['history_load_ms']}</td><td class='num'>{s['cos_history_wall_ms']}</td>"
                               f"<td class='num'>{s['ask_wall_ms']}</td></tr>" for s in sm)
                     + "</table></details>")

    parts.append("<h2>Resources</h2>")
    t0 = resources[0]["t"] if resources else 0
    mem = [((x["t"] - t0) / 60, x["memory_free_pct"]) for x in resources if isinstance(x.get("memory_free_pct"), int)]
    parts.append(f"<p class='meta'>{len(resources)} samples. Memory free (memory_pressure) over minutes:</p>"
                 + line_chart(mem, "min", "%"))
    models = summary["resources"]["ollama_models_max_size_bytes"]
    parts.append("<p class='meta'>Ollama models seen loaded (max size): "
                 + (", ".join(f"{e(k)} {_fmt(v, 'B')}" for k, v in models.items()) or "none") + "</p>")

    parts.append("<h2>Global checks</h2><table><tr><th>Check</th><th class='num'>Checked</th><th class='num'>Failed</th></tr>"
                 + "".join(f"<tr><td>{e(k)}</td><td class='num'>{v['checked']}</td><td class='num'>{v['failed']}</td></tr>"
                           for k, v in sorted(summary["global_checks"].items())) + "</table>")
    parts.append("<p class='note'>Answer-quality judge: not run (E1 Part 2). Desktop window tests: not run (E1 Part 3).</p>")
    parts.append("</main></body></html>")
    return "\n".join(parts)


def build(results_dir: Path, reports_dir: Path, reports_root: Path, baseline_id: str | None = None):
    records = _read_jsonl(results_dir / "results.jsonl")
    meta = json.loads((results_dir / "meta.json").read_text(encoding="utf-8"))
    resources = _read_jsonl(results_dir / "resources.jsonl")
    soak_rows = _read_jsonl(results_dir / "soak_fast_path.jsonl")
    baseline = find_baseline(reports_root, meta["run_id"], meta["model_mode"], baseline_id)
    summary = summarize(records, meta, resources, baseline)
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_path = reports_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    html_path = reports_dir / "report.html"
    html_path.write_text(render_html(summary, records, resources, soak_rows), encoding="utf-8")
    return summary_path, html_path


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Rebuild a harness report")
    p.add_argument("run_id")
    p.add_argument("--baseline")
    p.add_argument("--out-root", type=Path, default=EVALS)
    a = p.parse_args(argv)
    s, h = build(a.out_root / "results" / a.run_id, a.out_root / "reports" / a.run_id,
                 a.out_root / "reports", a.baseline)
    print(f"Report: {h}\nSummary: {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
