"""Text as SVG outlines, in Archivo (OFL, tools/fonts), shaped with HarfBuzz.

GitHub shows README images without web fonts, so every word in the generated SVGs is drawn as a path.
`measure` gives the advance width, so callers can wrap lines to a width.
"""

from __future__ import annotations

from functools import lru_cache
from io import BytesIO
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONT = Path(__file__).resolve().parent / "fonts" / "Archivo-latin-wdth.woff2"


@lru_cache(maxsize=None)
def _instance(wdth: float, wght: float):
    tt = TTFont(BytesIO(FONT.read_bytes()))
    static = instancer.instantiateVariableFont(tt, {"wdth": wdth, "wght": wght})
    static.flavor = None
    buf = BytesIO()
    static.save(buf)
    face = hb.Face(hb.Blob(buf.getvalue()))
    return static, hb.Font(face), face.upem


def _shape(text: str, wdth: float, wght: float):
    static, font, upem = _instance(wdth, wght)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True})
    return static, upem, buf.glyph_infos, buf.glyph_positions


def measure(text: str, size: float, wdth: float = 100, wght: float = 400) -> float:
    _, upem, _, positions = _shape(text, wdth, wght)
    return sum(p.x_advance for p in positions) * size / upem


def outline(text: str, size: float, x: float, y: float, wdth: float = 100, wght: float = 400) -> str:
    """Path data for `text` with its baseline starting at (x, y)."""
    static, upem, infos, positions = _shape(text, wdth, wght)
    glyphs = static.getGlyphSet()
    order = static.getGlyphOrder()
    pen = SVGPathPen(glyphs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip("."))
    scale = size / upem
    cursor = 0.0
    for info, pos in zip(infos, positions):
        tx = x + (cursor + pos.x_offset) * scale
        ty = y - pos.y_offset * scale
        glyphs[order[info.codepoint]].draw(TransformPen(pen, (scale, 0, 0, -scale, tx, ty)))
        cursor += pos.x_advance
    return pen.getCommands()


def wrap(text: str, size: float, width: float, wdth: float = 100, wght: float = 400) -> list[str]:
    """Greedy word wrap to `width`, measured with the real font."""
    lines: list[str] = []
    line = ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and measure(candidate, size, wdth, wght) > width:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines
