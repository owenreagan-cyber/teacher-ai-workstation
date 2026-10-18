#!/usr/bin/env python3
"""Generate the Canvas Planner macOS app icon (pure stdlib, no Pillow).

Draws a 1024x1024 rounded-square icon:
  - deep navy -> brighter blue vertical gradient background
  - subtle laptop/keyboard-deck silhouette (workstation reference)
  - centered white weekly-planner card (navy header + 5-column grid)
  - green circular checkmark badge (success/readiness cue)

Transparent outside the rounded-square boundary. Outputs PNG at 16..1024 px
using a minimal stdlib PNG encoder (zlib + struct). No external dependencies.

Usage:
    python3 generate_icon.py <output_dir>
"""
from __future__ import annotations

import struct
import sys
import zlib
from pathlib import Path

SIZE = 1024
SIZES = (16, 32, 64, 128, 256, 512, 1024)

# Palette.
NAVY_TOP = (24, 52, 86)        # deep navy (top of background)
BLUE_BOTTOM = (62, 130, 202)   # brighter blue (bottom of background)
LAPTOP_DARK = (13, 33, 57)     # subtle workstation silhouette
CARD_HEADER = (30, 58, 95)     # navy card header
GRID_LINE = (30, 58, 95)
TODAY_FILL = (219, 234, 254)   # light blue "today" cell
GREEN = (34, 197, 94)          # #22C55E success badge
WHITE = (255, 255, 255)


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return lo if v < lo else (hi if v > hi else v)


def _mix(c1: tuple[int, int, int], c2: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = _clamp(t)
    return tuple(int(round(c1[i] + (c2[i] - c1[i]) * t)) for i in range(3))


def _in_rounded_rect(x: float, y: float, cx: float, cy: float, hw: float, hh: float, r: float) -> bool:
    if abs(x - cx) > hw or abs(y - cy) > hh:
        return False
    dx = abs(x - cx) - (hw - r)
    dy = abs(y - cy) - (hh - r)
    if dx <= 0 or dy <= 0:
        return True
    return dx * dx + dy * dy <= r * r


def _in_rect(x: float, y: float, x0: float, y0: float, x1: float, y1: float) -> bool:
    return x0 <= x <= x1 and y0 <= y <= y1


def _in_circle(x: float, y: float, cx: float, cy: float, r: float) -> bool:
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def _seg_dist(x: float, y: float, ax: float, ay: float, bx: float, by: float) -> float:
    px, py = bx - ax, by - ay
    l2 = px * px + py * py
    t = 0.0 if l2 == 0 else ((x - ax) * px + (y - ay) * py) / l2
    t = _clamp(t)
    cx, cy = ax + t * px, ay + t * py
    return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5


def _in_check(x: float, y: float, cx: float, cy: float, half: float = 26.0) -> bool:
    """Thick two-stroke checkmark centered at (cx, cy), scaled for a ~140px badge."""
    d1 = _seg_dist(x, y, cx - 92, cy - 6, cx - 16, cy + 68)
    d2 = _seg_dist(x, y, cx - 16, cy + 68, cx + 116, cy - 78)
    return min(d1, d2) <= half


def _color_at(x: float, y: float) -> tuple[int, int, int, int]:
    """Return straight (unpremultiplied) RGBA for pixel at design-space (x, y)."""
    # 1. Background rounded square (navy -> brighter blue vertical gradient).
    if not _in_rounded_rect(x, y, SIZE / 2, SIZE / 2, SIZE / 2, SIZE / 2, 210):
        return (0, 0, 0, 0)
    t = _clamp(y / SIZE)
    color = _mix(NAVY_TOP, BLUE_BOTTOM, t)

    # 2. Subtle laptop silhouette (screen + keyboard deck), darker navy.
    #    Screen: tall rounded panel; deck: a rounded bar at the bottom.
    if _in_rounded_rect(x, y, SIZE / 2, 470.0, 330.0, 340.0, 30.0):
        color = _mix(color, LAPTOP_DARK, 0.85)
    if _in_rounded_rect(x, y, SIZE / 2, 830.0, 316.0, 92.0, 30.0):
        color = _mix(color, LAPTOP_DARK, 0.92)
        # Trackpad notch in the deck center.
        if _in_rounded_rect(x, y, SIZE / 2, 830.0, 88.0, 26.0, 13.0):
            color = _mix(color, LAPTOP_DARK, 0.95)

    # 3. White weekly-planner card (navy header + 5-column grid).
    card_x0, card_x1 = 250.0, 774.0
    card_y0, card_y1 = 180.0, 720.0
    card_r = 50.0
    if _in_rounded_rect(x, y, (card_x0 + card_x1) / 2, (card_y0 + card_y1) / 2,
                        (card_x1 - card_x0) / 2, (card_y1 - card_y0) / 2, card_r):
        header_bottom = card_y0 + 118.0
        if _in_rect(x, y, card_x0, card_y0, card_x1, header_bottom):
            color = CARD_HEADER
            # Five weekday dots in the header.
            col_w = (card_x1 - card_x0) / 5.0
            for i in range(5):
                dot_x = card_x0 + (i + 0.5) * col_w
                if _in_circle(x, y, dot_x, card_y0 + 59.0, 11.0):
                    color = WHITE
        else:
            color = WHITE
            col_w = (card_x1 - card_x0) / 5.0
            row_h = (card_y1 - header_bottom) / 2.0
            # "Today" highlight (row 2, column 3).
            if _in_rect(x, y, card_x0 + 2 * col_w, header_bottom + row_h, card_x0 + 3 * col_w, card_y1):
                color = TODAY_FILL
                # A small green dot marks the readiness cue inside "today".
                dot_x = card_x0 + 2.5 * col_w
                if _in_circle(x, y, dot_x, card_y1 - row_h * 0.5, 20.0):
                    color = GREEN
            # Grid lines (columns + row separator).
            for i in range(1, 5):
                gx = card_x0 + i * col_w
                if abs(x - gx) < 2.5 and header_bottom <= y <= card_y1:
                    color = GRID_LINE
            if abs(y - (header_bottom + row_h)) < 2.5 and card_x0 <= x <= card_x1:
                color = GRID_LINE

    # 4. Green checkmark badge (success/readiness cue), bottom-right overlap.
    badge = (750.0, 750.0, 142.0)
    if _in_circle(x, y, badge[0], badge[1], badge[2]):
        # White ring separating the badge from the card/background.
        if _in_circle(x, y, badge[0], badge[1], badge[2]) and not _in_circle(x, y, badge[0], badge[1], badge[2] - 12.0):
            color = WHITE
        else:
            color = GREEN
            if _in_check(x, y, badge[0], badge[1]):
                color = WHITE

    return (color[0], color[1], color[2], 255)


def render(size: int) -> bytes:
    """Render one size (pixels), supersampling from the 1024 design."""
    scale = size / SIZE
    raw = bytearray()
    for py in range(size):
        raw.append(0)  # filter type 0
        for px in range(size):
            r = g = b = a = 0
            for sy in (0.0, 0.5):
                for sx in (0.0, 0.5):
                    dx = (px + sx) / scale
                    dy = (py + sy) / scale
                    cr, cg, cb, ca = _color_at(dx, dy)
                    r += cr
                    g += cg
                    b += cb
                    a += ca
            n = 4.0
            raw.extend((int(round(r / n)), int(round(g / n)), int(round(b / n)), int(round(a / n))))
    return _encode_png(size, size, bytes(raw))


def _encode_png(width: int, height: int, raw_rgba: bytes) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw_rgba, 9)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", idat)
            + chunk(b"IEND", b""))


def main() -> int:
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out_dir.mkdir(parents=True, exist_ok=True)
    for size in SIZES:
        data = render(size)
        (out_dir / f"icon_{size}x{size}.png").write_bytes(data)
    print(f"Wrote {len(SIZES)} PNGs to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
