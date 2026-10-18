"""mac.status: battery, memory, disk, uptime, and loaded Ollama models.

Fixed argv only. Process listings are never needed or printed.
"""
from __future__ import annotations

import re

from cos.registry import Tool

KEYWORDS = ("mac", "macbook", "battery", "memory", "ram", "disk", "storage", "space",
            "computer", "laptop", "uptime", "ollama", "model", "models", "charging", "power")


def parse_battery(text: str) -> dict:
    m = re.search(r"(\d+)%;\s*([^;]+);", text)
    if not m:
        return {"battery": "unknown"} if "InternalBattery" not in text else {"battery": "unparsed"}
    source = "AC power" if "AC Power" in text else "battery power"
    return {"battery_pct": int(m.group(1)), "battery_state": m.group(2).strip(), "power_source": source}


def parse_memory(text: str) -> dict:
    m = re.search(r"free percentage:\s*(\d+)%", text)
    return {"memory_free_pct": int(m.group(1))} if m else {"memory_free_pct": None}


def parse_df(text: str) -> dict:
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        return {"disk_free_gb": None}
    cols = lines[1].split()
    try:
        total_kb, avail_kb = int(cols[1]), int(cols[3])
    except (IndexError, ValueError):
        return {"disk_free_gb": None}
    return {"disk_free_gb": round(avail_kb / 1024 / 1024), "disk_total_gb": round(total_kb / 1024 / 1024)}


def parse_boottime(text: str, now_ts: float) -> dict:
    m = re.search(r"sec\s*=\s*(\d+)", text)
    if not m:
        return {"uptime": None}
    secs = max(0, int(now_ts - int(m.group(1))))
    days, rem = divmod(secs, 86400)
    hours, rem = divmod(rem, 3600)
    return {"uptime": f"{days}d {hours}h" if days else f"{hours}h {rem // 60}m"}


def status(ctx, args: dict) -> dict:
    out: dict = {}
    probes = (
        (["/usr/bin/pmset", "-g", "batt"], parse_battery),
        (["/usr/bin/memory_pressure"], parse_memory),
        (["/bin/df", "-k", "/"], parse_df),
    )
    for argv, parser in probes:
        try:
            res = ctx.run(argv, timeout=5)
            out.update(parser(res.stdout))
        except Exception as e:  # noqa: BLE001 - one failed probe must not hide the rest
            out[f"{argv[0].rsplit('/', 1)[-1]}_error"] = type(e).__name__
    try:
        res = ctx.run(["/usr/sbin/sysctl", "-n", "kern.boottime"], timeout=5)
        out.update(parse_boottime(res.stdout, ctx.clock().timestamp()))
    except Exception as e:  # noqa: BLE001
        out["uptime_error"] = type(e).__name__
    if ctx.loaded_models is not None:
        try:
            out["ollama_loaded"] = ctx.loaded_models()
        except Exception as e:  # noqa: BLE001
            out["ollama_loaded"] = f"unavailable ({type(e).__name__})"
    return out


def one_line(s: dict) -> str:
    parts = []
    if "battery_pct" in s:
        parts.append(f"battery {s['battery_pct']}% ({s['battery_state']})")
    if s.get("memory_free_pct") is not None:
        parts.append(f"memory {s['memory_free_pct']}% free")
    if s.get("disk_free_gb") is not None:
        parts.append(f"disk {s['disk_free_gb']} GB free")
    if s.get("uptime"):
        parts.append(f"up {s['uptime']}")
    loaded = s.get("ollama_loaded")
    if isinstance(loaded, list):
        parts.append("Ollama: " + (", ".join(loaded) if loaded else "no model loaded"))
    elif loaded:
        parts.append(f"Ollama: {loaded}")
    return " · ".join(parts) if parts else "unavailable"


def tools(ctx):
    return [Tool(
        name="mac.status",
        description="Mac status: battery, memory free, disk free, uptime, and loaded local Ollama models.",
        parameters={"type": "object", "properties": {}, "additionalProperties": False},
        side_effect="none", data_class="P1", timeout_s=15,
        func=lambda args: status(ctx, args), keywords=KEYWORDS,
    )]
