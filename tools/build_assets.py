#!/usr/bin/env python3
"""Render the profile README's header banner and project cards as SVGs.

Every image comes in a dark and a light variant; README.md picks one with
<picture> so it follows the viewer's GitHub theme. Edit PROJECTS below and run:

    python3 tools/build_assets.py
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "dark": {
        "bg": "#0d1117",
        "card": "#161b22",
        "border": "#30363d",
        "text": "#e6edf3",
        "muted": "#8b949e",
        "link": "#58a6ff",
        "pill": "#21262d",
        "pill_text": "#c9d1d9",
        "edge": "#30363d",
        "node": "#a5b4fc",
        "glow": 0.35,
    },
    "light": {
        "bg": "#ffffff",
        "card": "#ffffff",
        "border": "#d0d7de",
        "text": "#1f2328",
        "muted": "#59636e",
        "link": "#0969da",
        "pill": "#eff2f5",
        "pill_text": "#424a53",
        "edge": "#d0d7de",
        "node": "#6366f1",
        "glow": 0.18,
    },
}
ACCENT = ("#8b5cf6", "#06b6d4")  # violet -> cyan

LANG_COLOURS = {
    "Go": "#00ADD8",
    "TypeScript": "#3178c6",
    "Python": "#3572A5",
    "Java": "#b07219",
}

PROJECTS = [
    {
        "slug": "llm-honeypot",
        "tag": "security",
        "desc": "SSH honeypot that hands attackers a convincing fake Linux box and records everything they try.",
        "lang": "Go",
        "tech": "SSH · LLM",
    },
    {
        "slug": "esm-famil",
        "tag": "multiplayer",
        "desc": "Real-time version of the Persian word game Esm-o-Famil, with rooms, invite codes and server-side answer checking.",
        "lang": "TypeScript",
        "tech": "Fastify · socket.io · React",
    },
    {
        "slug": "poker-table",
        "tag": "llm agents",
        "desc": "No-limit hold'em table where LLM agents with different personalities play each other, and you can sit down.",
        "lang": "Python",
        "tech": "LLM agents · CLI",
    },
    {
        "slug": "go-orbitdb",
        "tag": "open source",
        "desc": "Go port of OrbitDB, the peer-to-peer database on IPFS. Author of 194 of its 201 commits.",
        "lang": "Go",
        "tech": "IPFS · libp2p",
    },
    {
        "slug": "cnsim",
        "tag": "research",
        "desc": "Bitcoin transaction-finality experiments on the CNSim consensus simulator, from my MSc thesis.",
        "lang": "Java",
        "tech": "Python · simulation",
    },
    {
        "slug": "terminal-portfolio",
        "tag": "live",
        "desc": "Terminal-style portfolio you can type into, live at terminal.amirradjou.com.",
        "lang": "TypeScript",
        "tech": "React · Vite · PWA",
    },
]

# octicon "repo" (16px)
REPO_ICON = (
    "M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 "
    "0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 "
    "1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8ZM5 12.25a.25.25 0 0 1 .25-.25h3.5a.25.25 0 0 1 "
    ".25.25v3.25a.25.25 0 0 1-.4.2l-1.45-1.087a.249.249 0 0 0-.3 0L5.4 15.7a.25.25 0 0 1-.4-.2Z"
)


def gradient(id_: str, x2: str = "100%", y2: str = "0%") -> str:
    return (
        f'<linearGradient id="{id_}" x1="0%" y1="0%" x2="{x2}" y2="{y2}">'
        f'<stop offset="0%" stop-color="{ACCENT[0]}"/><stop offset="100%" stop-color="{ACCENT[1]}"/>'
        "</linearGradient>"
    )


def header(t: dict) -> str:
    w, h = 1200, 300
    nodes = [(820, 70), (930, 140), (1060, 80), (1120, 190), (990, 240), (860, 210), (760, 150)]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 0), (1, 4), (1, 5), (2, 4)]
    lines = "".join(
        f'<line x1="{nodes[a][0]}" y1="{nodes[a][1]}" x2="{nodes[b][0]}" y2="{nodes[b][1]}"/>'
        for a, b in edges
    )
    circles = "".join(
        f'<circle class="n" style="animation-delay:{i * 0.45:.2f}s" cx="{x}" cy="{y}" r="7"/>'
        for i, (x, y) in enumerate(nodes)
    )
    # messages travelling between peers
    packets = ""
    for i, (a, b) in enumerate([(6, 1), (1, 2), (5, 4), (2, 3)]):
        (x1, y1), (x2, y2) = nodes[a], nodes[b]
        packets += (
            f'<circle r="3.5" fill="url(#accent)">'
            f'<animateMotion dur="{2.6 + i * 0.4:.1f}s" begin="{i * 0.7:.1f}s" repeatCount="indefinite" '
            f'path="M{x1},{y1} L{x2},{y2}"/></circle>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">
<title id="t">Amirreza Radjou: backend and distributed-systems engineer, Toronto</title>
<defs>
{gradient("accent")}
<radialGradient id="g1" cx="0.15" cy="0.1" r="0.7"><stop offset="0%" stop-color="{ACCENT[0]}" stop-opacity="{t["glow"]}"/><stop offset="100%" stop-color="{ACCENT[0]}" stop-opacity="0"/></radialGradient>
<radialGradient id="g2" cx="0.85" cy="0.9" r="0.6"><stop offset="0%" stop-color="{ACCENT[1]}" stop-opacity="{t["glow"]}"/><stop offset="100%" stop-color="{ACCENT[1]}" stop-opacity="0"/></radialGradient>
<clipPath id="c"><rect width="{w}" height="{h}" rx="20"/></clipPath>
</defs>
<style>
.n {{ fill: {t["node"]}; animation: pulse 3.2s ease-in-out infinite; }}
@keyframes pulse {{ 0%, 100% {{ opacity: .35; }} 50% {{ opacity: 1; }} }}
@media (prefers-reduced-motion: reduce) {{ .n {{ animation: none; opacity: .8; }} }}
</style>
<g clip-path="url(#c)">
<rect width="{w}" height="{h}" fill="{t["bg"]}"/>
<rect width="{w}" height="{h}" fill="url(#g1)"/>
<rect width="{w}" height="{h}" fill="url(#g2)"/>
<g stroke="{t["edge"]}" stroke-width="2">{lines}</g>
{circles}
{packets}
</g>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="19" fill="none" stroke="{t["border"]}" stroke-width="2"/>
<text x="72" y="132" font-family="{FONT}" font-size="64" font-weight="700" fill="url(#accent)">Amirreza Radjou</text>
<text x="74" y="184" font-family="{FONT}" font-size="26" fill="{t["text"]}">Backend &amp; distributed-systems engineer · Toronto</text>
<text x="74" y="228" font-family="{MONO}" font-size="19" fill="{t["muted"]}">peer-to-peer systems · simulators · LLM-powered tools</text>
</svg>
"""


def card(p: dict, t: dict) -> str:
    w, h, pad = 420, 164, 22
    name = escape(p["slug"])
    tag = escape(p["tag"])
    tag_w = 7.2 * len(p["tag"]) + 20
    desc = textwrap.wrap(p["desc"], 50, break_on_hyphens=False)
    if len(desc) > 3:
        raise SystemExit(f"{p['slug']}: description wraps to {len(desc)} lines; keep it to 3")
    desc_svg = "".join(
        f'<text x="{pad}" y="{76 + i * 21}" font-family="{FONT}" font-size="14" fill="{t["muted"]}">{escape(line)}</text>'
        for i, line in enumerate(desc)
    )
    lang = escape(p["lang"])
    footer_x = pad + 16 + 7.6 * len(p["lang"]) + 12
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">
<title id="t">{name}: {escape(p["desc"])}</title>
<defs>{gradient("accent")}<clipPath id="c"><rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12"/></clipPath></defs>
<g clip-path="url(#c)">
<rect width="{w}" height="{h}" fill="{t["card"]}"/>
<rect width="{w}" height="4" fill="url(#accent)"/>
</g>
<rect x="1" y="1" width="{w - 2}" height="{h - 2}" rx="12" fill="none" stroke="{t["border"]}" stroke-width="1.5"/>
<path transform="translate({pad},28)" fill="{t["muted"]}" d="{REPO_ICON}"/>
<text x="{pad + 24}" y="42" font-family="{FONT}" font-size="18" font-weight="600" fill="{t["link"]}">{name}</text>
<rect x="{w - pad - tag_w:.1f}" y="25" width="{tag_w:.1f}" height="22" rx="11" fill="{t["pill"]}" stroke="{t["border"]}"/>
<text x="{w - pad - tag_w / 2:.1f}" y="40" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{t["pill_text"]}">{tag}</text>
{desc_svg}
<circle cx="{pad + 6}" cy="{h - 25}" r="6" fill="{LANG_COLOURS[p["lang"]]}"/>
<text x="{pad + 18}" y="{h - 20}" font-family="{FONT}" font-size="13" fill="{t["text"]}">{lang}</text>
<text x="{footer_x:.1f}" y="{h - 20}" font-family="{FONT}" font-size="13" fill="{t["muted"]}">{escape(p["tech"])}</text>
</svg>
"""


def main() -> None:
    (ASSETS / "cards").mkdir(parents=True, exist_ok=True)
    for theme, t in THEMES.items():
        (ASSETS / f"header-{theme}.svg").write_text(header(t), encoding="utf-8")
        for p in PROJECTS:
            (ASSETS / "cards" / f"{p['slug']}-{theme}.svg").write_text(card(p, t), encoding="utf-8")
    print(f"wrote header + {len(PROJECTS)} cards x {len(THEMES)} themes to {ASSETS}")


if __name__ == "__main__":
    main()
