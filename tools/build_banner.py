"""Build assets/banner.svg: the profile banner, an animated SVG in the style of amirradjou.com.

A small peer-to-peer network where some peers are projects. Every 9 seconds a message floods from
go-orbitdb: each peer passes it to its neighbours one hop later, and the links it travels light up.
GitHub shows README images without scripts or web fonts, so the animation is CSS inside the SVG and
the name and tagline are outlines (Archivo, OFL, in tools/fonts). Project labels use the viewer's
system font. With reduced motion, the whole flood is drawn still.

    uv run --with fonttools --with brotli --with uharfbuzz python tools/build_banner.py
"""

from __future__ import annotations

import math
import random
from io import BytesIO
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
FONT = ROOT / "tools" / "fonts" / "Archivo-latin-wdth.woff2"
W, H = 1600, 560
CYCLE = 9.0  # seconds per flood, rest included
HOP = 0.42  # seconds per hop
PLATE, DEEP, PAPER, SAFFRON = "#17407f", "#0e2b5a", "#f4f7fb", "#f5b731"

# Text block (bottom left), kept clear of peers and links.
TEXT = (64, 170, 800, 530)

# Projects as labelled peers, placed by hand so labels stay readable at about 850 px wide.
PROJECTS = {
    "go-orbitdb": (930, 92),
    "CNSim": (1190, 70),
    "leash": (1440, 118),
    "pennywatch": (1010, 250),
    "llm-honeypot": (1300, 232),
    "exitcheck": (905, 418),
    "poker-table": (1120, 452),
    "overhead": (1452, 348),
    "chess-coach": (1300, 520),
}
ORIGIN = "go-orbitdb"


def outline(text: str, size: float, x: float, y: float, wdth: float, wght: float) -> str:
    """The text as one SVG path, shaped with HarfBuzz (kerning included)."""
    data = FONT.read_bytes()
    tt = TTFont(BytesIO(data))
    static = instancer.instantiateVariableFont(tt, {"wdth": wdth, "wght": wght})
    buf = BytesIO()
    static.flavor = None
    static.save(buf)
    blob = hb.Blob(buf.getvalue())
    face = hb.Face(blob)
    font = hb.Font(face)
    upem = face.upem
    hbbuf = hb.Buffer()
    hbbuf.add_str(text)
    hbbuf.guess_segment_properties()
    hb.shape(font, hbbuf, {"kern": True, "liga": True})
    glyphs = static.getGlyphSet()
    order = static.getGlyphOrder()
    pen = SVGPathPen(glyphs)
    scale = size / upem
    cursor = 0.0
    for info, pos in zip(hbbuf.glyph_infos, hbbuf.glyph_positions):
        name = order[info.codepoint]
        tx = x + (cursor + pos.x_offset) * scale
        ty = y - pos.y_offset * scale
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, tx, ty)))
        cursor += pos.x_advance
    return pen.getCommands()


def crosses_text(a, b) -> bool:
    """Liang-Barsky: does segment a-b enter the text block?"""
    (x1, y1), (x2, y2) = a, b
    t0, t1 = 0.0, 1.0
    dx, dy = x2 - x1, y2 - y1
    left, top, right, bottom = TEXT
    for p, q in ((-dx, x1 - left), (dx, right - x1), (-dy, y1 - top), (dy, bottom - y1)):
        if p == 0:
            if q < 0:
                return False
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return False
    return True


def label_box(name: str, x: float, y: float) -> tuple[float, float, float, float]:
    """Roughly where a project's label sits (left, top, right, bottom), at 27 px system sans."""
    width = 15.5 * len(name)
    if x < W - 230:
        return (x - 12, y - 24, x + 22 + width, y + 22)
    return (x - 22 - width, y - 24, x + 12, y + 22)


def build() -> str:
    rng = random.Random(3)
    peers: list[tuple[tuple[float, float], str | None]] = [
        ((float(x), float(y)), name) for name, (x, y) in PROJECTS.items()
    ]
    labels = [label_box(name, x, y) for name, (x, y) in PROJECTS.items()]
    # Unlabelled peers around them, and a few across the top of the text block.
    tries = 0
    while len(peers) < 34 and tries < 5000:
        tries += 1
        x, y = rng.uniform(40, W - 40), rng.uniform(34, H - 34)
        if TEXT[0] - 10 < x < TEXT[2] + 10 and TEXT[1] - 10 < y < TEXT[3]:
            continue
        if any(l - 14 < x < r + 14 and t - 14 < y < b + 14 for l, t, r, b in labels):
            continue
        if all(math.dist((x, y), p) > 105 for p, _ in peers):
            peers.append(((x, y), None))
    pts = [p for p, _ in peers]

    edges: set[tuple[int, int]] = set()
    for i, a in enumerate(pts):
        near = sorted((j for j in range(len(pts)) if j != i), key=lambda j: math.dist(a, pts[j]))
        added = 0
        for j in near:
            if added == 3:
                break
            if crosses_text(a, pts[j]):
                continue
            edges.add((min(i, j), max(i, j)))
            added += 1

    # Connect components by their closest pair that avoids the text.
    def components():
        adj = {i: set() for i in range(len(pts))}
        for a, b in edges:
            adj[a].add(b)
            adj[b].add(a)
        seen, comps = set(), []
        for s in range(len(pts)):
            if s in seen:
                continue
            stack, comp = [s], []
            seen.add(s)
            while stack:
                n = stack.pop()
                comp.append(n)
                for m in adj[n]:
                    if m not in seen:
                        seen.add(m)
                        stack.append(m)
            comps.append(comp)
        return comps, adj

    while True:
        comps, adj = components()
        if len(comps) == 1:
            break
        best = min(
            ((a, b) for a in comps[0] for c in comps[1:] for b in c),
            key=lambda e: math.dist(pts[e[0]], pts[e[1]]) * (50 if crosses_text(pts[e[0]], pts[e[1]]) else 1),
        )
        edges.add((min(best), max(best)))

    # Flood by hops from the origin.
    origin = next(i for i, (_, n) in enumerate(peers) if n == ORIGIN)
    hops = {origin: 0}
    parent: dict[int, int] = {}
    queue = [origin]
    while queue:
        n = queue.pop(0)
        for m in sorted(adj[n], key=lambda m: math.dist(pts[n], pts[m])):
            if m not in hops:
                hops[m] = hops[n] + 1
                parent[m] = n
                queue.append(m)

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'role="img" aria-labelledby="t d">'
    )
    out.append('<title id="t">Amirreza Radjou: distributed systems, built and measured.</title>')
    out.append(
        '<desc id="d">A peer-to-peer network whose peers include the projects go-orbitdb, CNSim, leash, '
        "pennywatch, llm-honeypot, exitcheck, poker-table, overhead and chess-coach. A message floods "
        "from go-orbitdb to every peer.</desc>"
    )
    out.append(
        f"""<defs>
<radialGradient id="shade" cx="85%" cy="0%" r="110%"><stop offset="40%" stop-color="{DEEP}" stop-opacity="0"/><stop offset="100%" stop-color="{DEEP}" stop-opacity="0.7"/></radialGradient>
<style>
.link {{ stroke: {PAPER}; stroke-opacity: .22; stroke-width: 2; }}
.hot {{ stroke: {SAFFRON}; stroke-width: 3.5; fill: none; stroke-dasharray: 1; stroke-dashoffset: 1; opacity: 0;
  animation: wire {CYCLE}s linear infinite; }}
.peer {{ fill: {PAPER}; animation: lit {CYCLE}s linear infinite; }}
.ring {{ fill: none; stroke: {SAFFRON}; stroke-width: 2; opacity: 0; transform-box: fill-box; transform-origin: center;
  animation: ring {CYCLE}s ease-out infinite; }}
.label {{ font: 600 27px -apple-system, "Segoe UI", Helvetica, Arial, sans-serif; fill: {PAPER};
  paint-order: stroke; stroke: {PLATE}; stroke-width: 8px; stroke-linejoin: round; animation: label {CYCLE}s linear infinite; }}
@keyframes wire {{ 0% {{ stroke-dashoffset: 1; opacity: 1; }} 4.5% {{ stroke-dashoffset: 0; opacity: 1; }}
  38% {{ opacity: 1; }} 52% {{ opacity: 0; }} 100% {{ stroke-dashoffset: 0; opacity: 0; }} }}
@keyframes lit {{ 0% {{ fill: {SAFFRON}; }} 40% {{ fill: {SAFFRON}; }} 55% {{ fill: {PAPER}; }} 100% {{ fill: {PAPER}; }} }}
@keyframes label {{ 0% {{ fill: {SAFFRON}; }} 40% {{ fill: {SAFFRON}; }} 55% {{ fill: {PAPER}; }} 100% {{ fill: {PAPER}; }} }}
@keyframes ring {{ 0% {{ opacity: 1; transform: scale(1); }} 9% {{ opacity: 0; transform: scale(4.2); }} 100% {{ opacity: 0; transform: scale(4.2); }} }}
@media (prefers-reduced-motion: reduce) {{
  .hot {{ animation: none; opacity: .9; stroke-dashoffset: 0; }}
  .peer, .label {{ animation: none; fill: {SAFFRON}; }}
  .ring {{ display: none; }}
}}
</style>
</defs>"""
    )
    out.append(f'<rect width="{W}" height="{H}" fill="{PLATE}"/><rect width="{W}" height="{H}" fill="url(#shade)"/>')

    for a, b in sorted(edges):
        (x1, y1), (x2, y2) = pts[a], pts[b]
        out.append(f'<line class="link" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}"/>')
    for child, par in sorted(parent.items(), key=lambda kv: hops[kv[0]]):
        (x1, y1), (x2, y2) = pts[par], pts[child]
        delay = hops[par] * HOP
        out.append(
            f'<path class="hot" pathLength="1" style="animation-delay:{delay:.2f}s" '
            f'd="M{x1:.0f} {y1:.0f}L{x2:.0f} {y2:.0f}"/>'
        )
    for i, ((x, y), name) in enumerate(peers):
        delay = hops[i] * HOP + (0 if i == origin else HOP * 0.9)
        r = 9 if name else 5
        out.append(f'<circle class="ring" style="animation-delay:{delay:.2f}s" cx="{x:.0f}" cy="{y:.0f}" r="{r}"/>')
        out.append(f'<circle class="peer" style="animation-delay:{delay:.2f}s" cx="{x:.0f}" cy="{y:.0f}" r="{r}"/>')
        if name:
            right = x < W - 230
            lx = x + 18 if right else x - 18
            anchor = "start" if right else "end"
            out.append(
                f'<text class="label" style="animation-delay:{delay:.2f}s" x="{lx:.0f}" y="{y + 9:.0f}" '
                f'text-anchor="{anchor}">{name}</text>'
            )

    out.append(f'<path fill="{PAPER}" d="{outline("Amirreza", 132, 82, 318, 125, 780)}"/>')
    out.append(f'<path fill="{PAPER}" d="{outline("Radjou", 132, 82, 438, 125, 780)}"/>')
    out.append(f'<path fill="{PAPER}" d="{outline("Distributed systems, built and measured.", 44, 84, 505, 88, 500)}"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    target = ROOT / "assets" / "banner.svg"
    target.write_text(build())
    print(f"wrote {target.relative_to(ROOT)} ({target.stat().st_size} bytes)")
