#!/usr/bin/env python3
"""Generate the Canvas Planner macOS app icon (pure stdlib, no Pillow).

Draws a 1024x1024 rounded-square icon (calm teacher-professional blue), a white
weekly-grid calendar, and a green checkmark badge. Outputs PNG at the requested
sizes using a minimal PNG encoder (zlib + struct). No external deps.

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


def _in_check(x: float, y: float, half: float = 30.0) -> bool:
    """Green checkmark badge centered at (cx, cy)."""
    cx, cy = 720.0, 720.0
    # Two thick strokes forming a check (stroke half-width ~30px).
    d1 = _seg_dist(x, y, cx - 105, cy - 8, cx - 20, cy + 78)
    d2 = _seg_dist(x, y, cx - 20, cy + 78, cx + 130, cy - 88)
    return min(d1, d2) <= half


def _color_at(x: float, y: float) -> tuple[int, int, int, int]:
    """Return RGBA (0-255) for pixel at fractional (x, y)."""
    # Background rounded square.
    top = (59, 130, 200)      # #3B82C4
    bottom = (37, 99, 160)    # #2563A0
    # Vertical gradient over the 1024 canvas.
    t = y / SIZE
    bg = _mix(top, bottom, t)

    if not _in_rounded_rect(x, y, SIZE / 2, SIZE / 2, SIZE / 2, SIZE / 2, 180):
        return (0, 0, 0, 0)

    color = bg
    alpha = 255

    # Weekly calendar card (white rounded rect).
    card = (200.0, 250.0, 824.0, 830.0)  # x0,y0,x1,y1
    card_r = 70.0
    if _in_rounded_rect(x, y, (card[0] + card[2]) / 2, (card[1] + card[3]) / 2,
                        (card[2] - card[0]) / 2, (card[3] - card[1]) / 2, card_r):
        # Header band.
        if _in_rect(x, y, card[0], card[1], card[2], card[1] + 130):
            color = (30, 58, 95)  # dark navy header
        else:
            color = (255, 255, 255)
            # Grid lines + weekday header cells.
            col_w = (card[2] - card[0]) / 5.0
            row_h = (card[3] - (card[1] + 130)) / 2.0
            # Column separators.
            for i in range(1, 5):
                gx = card[0] + i * col_w
                if abs(x - gx) < 3.0 and card[1] + 130 <= y <= card[3]:
                    color = (30, 58, 95)
            # Row separator.
            if abs(y - (card[1] + 130 + row_h)) < 3.0 and card[0] <= x <= card[2]:
                color = (30, 58, 95)
            # A highlighted "today" cell (col 3, row 2) accent.
            if _in_rect(x, y, card[0] + 2 * col_w, card[1] + 130 + row_h, card[0] + 3 * col_w, card[3]):
                color = (219, 234, 254)  # light blue accent

    # Green checkmark badge.
    if _in_circle(x, y, 720, 720, 170):
        color = (34, 197, 94)  # #22C55E
        if _in_check(x, y):
            color = (255, 255, 255)

    return (color[0], color[1], color[2], alpha)


def render(size: int) -> bytes:
    """Render one size (pixels), supersampling from the 1024 design."""
    scale = size / SIZE
    rows: list[bytes] = []
    raw = bytearray()
    for py in range(size):
        raw.append(0)  # filter type 0
        for px in range(size):
            # 2x2 supersampling in design space; straight (unpremultiplied) RGBA.
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
    # Also write the 1024 master as icon_1024.png.
    print(f"Wrote {len(SIZES)} PNGs to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
