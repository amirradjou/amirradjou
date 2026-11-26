"""Builds the README's images from tools/profile.json and peers.json:

  assets/banner.svg   a peer-to-peer network of the projects, with slots for visitors who pinged.
                      A message floods from the newest visitor (or go-orbitdb) every 9 seconds.
  assets/ping.svg     the "ping" button
  assets/cards/*.svg  one card per project: its own picture, embedded, and its line and result

Everything is CSS-animated SVG with outlined text (see textpath.py): READMEs run no scripts and
load no fonts. The layout is deterministic, so a new visitor never reshuffles the network.

    uv run --with-requirements tools/requirements.txt python tools/build_assets.py
"""

from __future__ import annotations

import base64
import json
import math
import random
from html import escape
from pathlib import Path

from textpath import measure, outline, wrap

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "tools" / "profile.json").read_text())
PEERS = ROOT / "peers.json"

PLATE, DEEP, DEEPER = "#17407f", "#0e2b5a", "#0b2350"
PAPER, SOFT, SAFFRON = "#f4f7fb", "#b9c9e4", "#f5b731"
SANS = '-apple-system, "Segoe UI", Helvetica, Arial, sans-serif'

# ---------------------------------------------------------------- the network

W, H = 1600, 600
CYCLE = 9.0  # seconds per flood, rest included
HOP = 0.42  # seconds per hop
TEXT = (64, 236, 820, 572)  # name and tagline, kept clear of peers and links
PROJECTS = {
    "go-orbitdb": (960, 120),
    "CNSim": (1210, 92),
    "leash": (1452, 150),
    "pennywatch": (1030, 282),
    "llm-honeypot": (1310, 262),
    "exitcheck": (920, 452),
    "poker-table": (1130, 488),
    "overhead": (1462, 384),
    "chess-coach": (1300, 556),
}
# Where visitors appear, newest first. Upper slots label above, lower slots below.
SLOTS = [(150.0, 112.0), (286.0, 172.0), (422.0, 108.0), (558.0, 168.0), (694.0, 106.0), (830.0, 166.0)]
DEFAULT_ORIGIN = "go-orbitdb"


def label_box(text: str, x: float, y: float, size: float = 27) -> tuple[float, float, float, float]:
    width = 0.58 * size * len(text)
    if x < W - 230:
        return (x - 12, y - 24, x + 22 + width, y + 22)
    return (x - 22 - width, y - 24, x + 12, y + 22)


def crosses(a, b, box) -> bool:
    """Liang-Barsky: does segment a-b enter the box (left, top, right, bottom)?"""
    (x1, y1), (x2, y2) = a, b
    t0, t1 = 0.0, 1.0
    dx, dy = x2 - x1, y2 - y1
    left, top, right, bottom = box
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


def load_peers() -> list[dict]:
    """Visitors, newest first."""
    if not PEERS.exists():
        return []
    return sorted(json.loads(PEERS.read_text())["peers"], key=lambda p: p["joined"], reverse=True)


def network(visitors: list[dict]):
    """Points, names, edges. Base peers never depend on visitors, so joins don't reshuffle anything."""
    rng = random.Random(3)
    pts: list[tuple[float, float]] = []
    names: list[str | None] = []
    for name, (x, y) in PROJECTS.items():
        pts.append((float(x), float(y)))
        names.append(name)
    labels = [label_box(n, x, y) for n, (x, y) in PROJECTS.items()]
    tries = 0
    while len(pts) < 32 and tries < 6000:
        tries += 1
        x, y = rng.uniform(40, W - 40), rng.uniform(34, H - 34)
        if TEXT[0] - 10 < x < TEXT[2] + 10 and TEXT[1] - 10 < y < TEXT[3]:
            continue
        if any(l - 14 < x < r + 14 and t - 14 < y < b + 14 for l, t, r, b in labels):
            continue
        if any(math.dist((x, y), s) < 90 for s in SLOTS):
            continue
        if all(math.dist((x, y), p) > 105 for p in pts):
            pts.append((x, y))
            names.append(None)
    base = len(pts)

    def link(i: int, candidates: range, k: int, edges: set):
        near = sorted((j for j in candidates if j != i), key=lambda j: math.dist(pts[i], pts[j]))
        added = 0
        for j in near:
            if added == k:
                break
            if crosses(pts[i], pts[j], TEXT):
                continue
            edges.add((min(i, j), max(i, j)))
            added += 1

    edges: set[tuple[int, int]] = set()
    for i in range(base):
        link(i, range(base), 3, edges)
    connect(pts, edges, base)

    # Visitors plug in at their slot, to their two nearest base peers.
    for slot, visitor in zip(SLOTS, visitors):
        pts.append(slot)
        names.append("@" + visitor["login"])
        link(len(pts) - 1, range(base), 2, edges)
    return pts, names, edges, base


def connect(pts, edges, count):
    while True:
        adj = adjacency(count, edges)
        seen, comps = set(), []
        for s in range(count):
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
        if len(comps) == 1:
            return
        a, b = min(
            ((a, b) for a in comps[0] for c in comps[1:] for b in c),
            key=lambda e: math.dist(pts[e[0]], pts[e[1]]) * (50 if crosses(pts[e[0]], pts[e[1]], TEXT) else 1),
        )
        edges.add((min(a, b), max(a, b)))


def adjacency(count, edges):
    adj = {i: set() for i in range(count)}
    for a, b in edges:
        if a < count and b < count:
            adj[a].add(b)
            adj[b].add(a)
    return adj


def flood(pts, edges, origin: int):
    """Hops from origin, and the parent each peer first heard the message from."""
    adj = adjacency(len(pts), edges)
    hops, parent, queue = {origin: 0}, {}, [origin]
    while queue:
        n = queue.pop(0)
        for m in sorted(adj[n], key=lambda m: math.dist(pts[n], pts[m])):
            if m not in hops:
                hops[m] = hops[n] + 1
                parent[m] = n
                queue.append(m)
    return hops, parent


def short(login: str) -> str:
    return login if len(login) <= 15 else login[:14] + "…"


def banner(visitors: list[dict]) -> str:
    pts, names, edges, base = network(visitors)
    origin = names.index("@" + visitors[0]["login"]) if visitors else names.index(DEFAULT_ORIGIN)
    hops, parent = flood(pts, edges, origin)
    count = len(visitors)
    if count == 0:
        caption = "Nobody has joined yet. Ping to be the first peer."
    else:
        people = "1 person has" if count == 1 else f"{count} people have"
        caption = f"{people} joined this network. Newest: @{short(visitors[0]['login'])}"

    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-labelledby="t d">',
        '<title id="t">Amirreza Radjou: distributed systems, built and measured.</title>',
        f'<desc id="d">A peer-to-peer network of my projects. {escape(caption)} A message floods through every peer.</desc>',
        f"""<defs>
<radialGradient id="shade" cx="85%" cy="0%" r="110%"><stop offset="40%" stop-color="{DEEP}" stop-opacity="0"/><stop offset="100%" stop-color="{DEEP}" stop-opacity=".7"/></radialGradient>
<style>
.link {{ stroke: {PAPER}; stroke-opacity: .22; stroke-width: 2; }}
.hot {{ stroke: {SAFFRON}; stroke-width: 3.5; fill: none; stroke-dasharray: 1; stroke-dashoffset: 1; opacity: 0; animation: wire {CYCLE}s linear infinite; }}
.peer {{ fill: {PAPER}; animation: lit {CYCLE}s linear infinite; }}
.ring {{ fill: none; stroke: {SAFFRON}; stroke-width: 2; opacity: 0; transform-box: fill-box; transform-origin: center; animation: ring {CYCLE}s ease-out infinite; }}
.label {{ font: 600 27px {SANS}; fill: {PAPER}; paint-order: stroke; stroke: {PLATE}; stroke-width: 8px; stroke-linejoin: round; animation: label {CYCLE}s linear infinite; }}
.visitor {{ font-size: 24px; }}
.slot {{ fill: none; stroke: {PAPER}; stroke-opacity: .75; stroke-width: 2; stroke-dasharray: 5 5; }}
.slot-label {{ font: 600 24px {SANS}; fill: {SOFT}; opacity: .8; }}
.caption {{ font: 500 22px {SANS}; fill: {SOFT}; }}
.blink {{ animation: blink 1.6s steps(1) infinite; }}
@keyframes wire {{ 0% {{ stroke-dashoffset: 1; opacity: 1; }} 4.5% {{ stroke-dashoffset: 0; opacity: 1; }} 38% {{ opacity: 1; }} 52% {{ opacity: 0; }} 100% {{ stroke-dashoffset: 0; opacity: 0; }} }}
@keyframes lit {{ 0% {{ fill: {SAFFRON}; }} 40% {{ fill: {SAFFRON}; }} 55% {{ fill: {PAPER}; }} 100% {{ fill: {PAPER}; }} }}
@keyframes label {{ 0% {{ fill: {SAFFRON}; }} 40% {{ fill: {SAFFRON}; }} 55% {{ fill: {PAPER}; }} 100% {{ fill: {PAPER}; }} }}
@keyframes ring {{ 0% {{ opacity: 1; transform: scale(1); }} 9% {{ opacity: 0; transform: scale(4.2); }} 100% {{ opacity: 0; transform: scale(4.2); }} }}
@keyframes blink {{ 0% {{ opacity: 1; }} 50% {{ opacity: .15; }} }}
@media (prefers-reduced-motion: reduce) {{
  .hot {{ animation: none; opacity: .9; stroke-dashoffset: 0; }}
  .peer, .label {{ animation: none; fill: {SAFFRON}; }}
  .ring {{ display: none; }}
  .blink {{ animation: none; }}
}}
</style>
</defs>""",
        f'<rect width="{W}" height="{H}" fill="{PLATE}"/><rect width="{W}" height="{H}" fill="url(#shade)"/>',
    ]
    for a, b in sorted(edges):
        (x1, y1), (x2, y2) = pts[a], pts[b]
        o.append(f'<line class="link" x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}"/>')
    for child, par in sorted(parent.items(), key=lambda kv: hops[kv[0]]):
        (x1, y1), (x2, y2) = pts[par], pts[child]
        o.append(
            f'<path class="hot" pathLength="1" style="animation-delay:{hops[par] * HOP:.2f}s" d="M{x1:.0f} {y1:.0f}L{x2:.0f} {y2:.0f}"/>'
        )
    # Empty slots: open sockets, dashed and already wired to their two nearest peers.
    for i, (x, y) in enumerate(SLOTS[count:], start=count):
        for j in sorted(range(base), key=lambda j: math.dist((x, y), pts[j]))[:2]:
            o.append(
                f'<line class="slot" x1="{x:.0f}" y1="{y:.0f}" x2="{pts[j][0]:.0f}" y2="{pts[j][1]:.0f}" stroke-opacity=".3"/>'
            )
        o.append(f'<circle class="slot" cx="{x:.0f}" cy="{y:.0f}" r="13" fill="{PLATE}"/>')
        if i == count:
            above = i % 2 == 0
            o.append(f'<text class="slot-label blink" x="{x}" y="{y - 26 if above else y + 44}" text-anchor="middle">you?</text>')
    for i, ((x, y), name) in enumerate(zip(pts, names)):
        delay = hops[i] * HOP + (0 if i == origin else HOP * 0.9)
        r = 9 if name else 5
        o.append(f'<circle class="ring" style="animation-delay:{delay:.2f}s" cx="{x:.0f}" cy="{y:.0f}" r="{r}"/>')
        o.append(f'<circle class="peer" style="animation-delay:{delay:.2f}s" cx="{x:.0f}" cy="{y:.0f}" r="{r}"/>')
        if name and name.startswith("@"):
            slot = SLOTS.index((x, y))
            above = slot % 2 == 0
            o.append(
                f'<text class="label visitor" style="animation-delay:{delay:.2f}s" x="{x:.0f}" '
                f'y="{y - 24 if above else y + 42:.0f}" text-anchor="middle">{escape("@" + short(name[1:]))}</text>'
            )
        elif name:
            right = x < W - 230
            o.append(
                f'<text class="label" style="animation-delay:{delay:.2f}s" x="{x + 18 if right else x - 18:.0f}" '
                f'y="{y + 9:.0f}" text-anchor="{"start" if right else "end"}">{escape(name)}</text>'
            )
    o.append(f'<text class="caption" x="70" y="44">{escape(caption)}</text>')
    o.append(f'<path fill="{PAPER}" d="{outline("Amirreza", 132, 82, 366, 125, 780)}"/>')
    o.append(f'<path fill="{PAPER}" d="{outline("Radjou", 132, 82, 486, 125, 780)}"/>')
    o.append(f'<path fill="{PAPER}" d="{outline("Distributed systems, built and measured.", 44, 84, 553, 88, 500)}"/>')
    o.append("</svg>")
    return "\n".join(o) + "\n"


# ---------------------------------------------------------------- the ping button

def ping_button() -> str:
    text = "ping amirradjou"
    size = 40
    tw = measure(text, size, 112, 650)
    pw = measure("$ ", size, 112, 650)
    w = int(56 + pw + tw + 34 + 48)
    h = 96
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="ping amirradjou: open an issue titled ping to join the network">
<style>.cursor {{ animation: blink 1.1s steps(1) infinite; }} @keyframes blink {{ 50% {{ opacity: 0; }} }} @media (prefers-reduced-motion: reduce) {{ .cursor {{ animation: none; }} }}</style>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="14" fill="{DEEPER}" stroke="{SAFFRON}" stroke-width="2"/>
<path fill="{SAFFRON}" d="{outline("$ ", size, 30, 62, 112, 650)}"/>
<path fill="{PAPER}" d="{outline(text, size, 30 + pw, 62, 112, 650)}"/>
<rect class="cursor" x="{30 + pw + tw + 10:.0f}" y="30" width="20" height="38" fill="{SAFFRON}"/>
</svg>
"""


# ---------------------------------------------------------------- project cards

CW, CH = 900, 820
PAD = 30
PIC_H = 470


def card(project: dict, index: int) -> str:
    left = index % 2 == 0
    pic = ""
    if "picture" in project:
        path = ROOT / "assets" / "projects" / project["picture"]
        data = base64.b64encode(path.read_bytes()).decode()
        # Screenshots fill the frame; charts ("fit": "meet") sit whole on a white mat.
        fit = project.get("fit", "slice")
        mat = f'<rect x="{PAD}" y="{PAD}" width="{CW - 2 * PAD}" height="{PIC_H}" rx="12" fill="#fff"/>' if fit == "meet" else ""
        pic = mat + (
            f'<image href="data:image/webp;base64,{data}" x="{PAD + (14 if fit == "meet" else 0)}" y="{PAD + (14 if fit == "meet" else 0)}" '
            f'width="{CW - 2 * PAD - (28 if fit == "meet" else 0)}" height="{PIC_H - (28 if fit == "meet" else 0)}" '
            f'preserveAspectRatio="xMidYMid {fit}" clip-path="url(#pic)"/>'
        )
    else:
        lines = wrap(project["panel"], 62, CW - 2 * PAD - 80, 125, 760)
        y0 = PAD + PIC_H - 40 - (len(lines) - 1) * 64
        pic = f'<rect x="{PAD}" y="{PAD}" width="{CW - 2 * PAD}" height="{PIC_H}" rx="12" fill="{DEEP}"/>' + "".join(
            f'<path fill="{PAPER}" d="{outline(line, 62, PAD + 40, y0 + i * 64, 125, 760)}"/>' for i, line in enumerate(lines)
        )

    y = PAD + PIC_H + 70
    parts = [f'<path fill="{PAPER}" d="{outline(project["id"], 48, PAD + 4, y, 118, 700)}"/>']
    parts.append(f'<path fill="{SOFT}" d="{outline(project["kind"], 25, PAD + 6, y + 40, 100, 450)}"/>')
    y += 92
    for line in wrap(project["line"], 26, CW - 2 * PAD - 12, 100, 420)[:3]:
        parts.append(f'<path fill="{PAPER}" d="{outline(line, 26, PAD + 6, y, 100, 420)}"/>')
        y += 36
    if project.get("fact"):
        y += 10
        fact_lines = wrap(project["fact"], 26, CW - 2 * PAD - 40, 100, 600)[:2]
        parts.append(f'<rect x="{PAD + 6}" y="{y - 26}" width="4" height="{len(fact_lines) * 36 - 4}" fill="{SAFFRON}"/>')
        for line in fact_lines:
            parts.append(f'<path fill="{PAPER}" d="{outline(line, 26, PAD + 26, y, 100, 600)}"/>')
            y += 36

    # The port and a stub of its branch, on the edge facing the other column.
    px = CW - 6 if left else 6
    port = f'<line x1="{px}" y1="{PAD + 40}" x2="{CW if left else 0}" y2="{PAD + 40}" stroke="{SAFFRON}" stroke-width="3"/><circle cx="{px}" cy="{PAD + 40}" r="8" fill="{SAFFRON}"/>'
    alt = project["line"] + (" " + project["fact"] if project.get("fact") else "")
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}" role="img" aria-label="{escape(project['id'])}: {escape(alt)}">
<defs><clipPath id="pic"><rect x="{PAD}" y="{PAD}" width="{CW - 2 * PAD}" height="{PIC_H}" rx="12"/></clipPath></defs>
<rect x="6" y="1" width="{CW - 12}" height="{CH - 2}" rx="22" fill="{PLATE}"/>
{pic}
{''.join(parts)}
{port}
</svg>
"""


def main() -> None:
    visitors = load_peers()
    (ROOT / "assets" / "banner.svg").write_text(banner(visitors))
    (ROOT / "assets" / "ping.svg").write_text(ping_button())
    cards = ROOT / "assets" / "cards"
    cards.mkdir(exist_ok=True)
    for i, project in enumerate(DATA["projects"]):
        (cards / f"{project['id'].lower()}.svg").write_text(card(project, i))
    print(f"banner ({len(visitors)} visitors), ping button, {len(DATA['projects'])} cards")


if __name__ == "__main__":
    main()
