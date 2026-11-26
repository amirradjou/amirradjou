"""Builds assets/status.svg: a daily network-monitor strip of the projects, with real numbers.

For each project in tools/profile.json: the last commit on its default branch, how many commits it had in
the last 90 days, the latest CI run there and the latest release, from the GitHub API. For each live page: the HTTP status and response time
of a GET from the machine running this (on GitHub, one of its runners), the fastest of three tries.

    GITHUB_TOKEN=... python tools/status.py        # needs no packages beyond the standard library
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / "tools" / "profile.json").read_text())
TOKEN = os.environ.get("GITHUB_TOKEN", "")
NOW = datetime.now(timezone.utc)

PLATE, DEEPER, PAPER, SOFT, SAFFRON, ALERT = "#17407f", "#0b2350", "#f4f7fb", "#b9c9e4", "#f5b731", "#ff8f7a"
MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace'


def api(path: str):
    req = urllib.request.Request(f"https://api.github.com/{path}", headers={"Accept": "application/vnd.github+json"})
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    try:
        with urllib.request.urlopen(req, timeout=20) as res:
            return json.load(res)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        raise


def ago(iso: str) -> str:
    days = (NOW - datetime.fromisoformat(iso.replace("Z", "+00:00"))).days
    return "today" if days == 0 else "1 day ago" if days == 1 else f"{days} days ago"


def repo_row(project: dict) -> dict:
    repo = project["repo"]
    meta = api(f"repos/{repo}") or {}
    branch = meta.get("default_branch", "main")
    commits = api(f"repos/{repo}/commits?sha={branch}&per_page=1") or []
    runs = (api(f"repos/{repo}/actions/runs?branch={branch}&per_page=1") or {}).get("workflow_runs", [])
    release = api(f"repos/{repo}/releases/latest")
    ci = "none"
    if runs:
        run = runs[0]
        ci = run.get("conclusion") or run.get("status") or "none"
    return {
        "name": project["id"],
        "commit": ago(commits[0]["commit"]["committer"]["date"]) if commits else "—",
        "ci": ci,
        "recent": recent_commits(repo, branch),
        "release": release["tag_name"] if release else "—",
        "live": project.get("live"),
    }


def recent_commits(repo: str, branch: str) -> int:
    """Commits on the default branch in the last 90 days."""
    since = datetime.fromtimestamp(NOW.timestamp() - 90 * 86400, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    total, page = 0, 1
    while True:
        batch = api(f"repos/{repo}/commits?sha={branch}&since={since}&per_page=100&page={page}") or []
        total += len(batch)
        if len(batch) < 100:
            return total
        page += 1


def probe(url: str) -> str:
    """'200 in 84 ms' (fastest of three), or what went wrong."""
    best, last = None, "no answer"
    for _ in range(3):
        start = time.perf_counter()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "amirradjou-profile-status"})
            with urllib.request.urlopen(req, timeout=15) as res:
                res.read(2048)
                ms = (time.perf_counter() - start) * 1000
                if best is None or ms < best[1]:
                    best = (res.status, ms)
        except urllib.error.HTTPError as err:
            last = f"HTTP {err.code}"
        except Exception:  # noqa: BLE001 - any failure is reported as "no answer"
            last = "no answer"
        time.sleep(1)
    return f"{best[0]} in {best[1]:.0f} ms" if best else last


def render(rows: list[dict], sites: list[tuple[str, str]]) -> str:
    w, row_h, top = 1600, 50, 132
    h = top + row_h * (len(rows) + len(sites)) + 40
    cols = [("PEER", 40), ("LAST COMMIT", 330), ("CI", 580), ("COMMITS 90D", 720), ("RELEASE", 940), ("LIVE PAGE", 1130)]
    stamp = NOW.strftime("%Y-%m-%d %H:%M UTC")
    where = "a GitHub runner" if os.environ.get("GITHUB_ACTIONS") == "true" else "a local machine"
    o = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-labelledby="t">',
        f"<title id=\"t\">Project status measured {stamp}: "
        + escape("; ".join(f"{r['name']}: last commit {r['commit']}, CI {r['ci']}" for r in rows))
        + "</title>",
        f"""<style>
text {{ font-family: {MONO}; font-size: 25px; fill: {PAPER}; }}
.head {{ fill: {SOFT}; font-size: 20px; letter-spacing: .08em; }}
.soft {{ fill: {SOFT}; }}
.ok {{ fill: #8be0a4; }}
.bad {{ fill: {ALERT}; }}
.live {{ fill: {SAFFRON}; }}
.title {{ font-size: 27px; font-weight: 700; }}
.pulse {{ animation: pulse 2s ease-in-out infinite; }}
@keyframes pulse {{ 50% {{ opacity: .25; }} }}
@media (prefers-reduced-motion: reduce) {{ .pulse {{ animation: none; }} }}
</style>""",
        f'<rect width="{w}" height="{h}" rx="22" fill="{DEEPER}"/>',
        f'<circle class="pulse" cx="52" cy="52" r="9" fill="{SAFFRON}"/>',
        f'<text class="title" x="76" y="61">$ watch amirradjou</text>',
        f'<text class="soft" x="{w - 40}" y="61" text-anchor="end">measured {stamp} from {where}</text>',
    ]
    for label, x in cols:
        o.append(f'<text class="head" x="{x}" y="{top - 22}">{label}</text>')
    o.append(f'<line x1="40" y1="{top - 8}" x2="{w - 40}" y2="{top - 8}" stroke="{SOFT}" stroke-opacity=".3"/>')
    y = top + 30
    for r in rows:
        ci_class = "ok" if r["ci"] == "success" else "bad" if r["ci"] in ("failure", "timed_out", "startup_failure") else "soft"
        ci_text = {"success": "passing", "failure": "failing"}.get(r["ci"], r["ci"])
        live = r.get("probe", "—")
        live_class = "live" if live.startswith("200") else "soft" if live == "—" else "bad"
        o += [
            f'<text x="40" y="{y}">{escape(r["name"])}</text>',
            f'<text class="soft" x="330" y="{y}">{escape(r["commit"])}</text>',
            f'<text class="{ci_class}" x="580" y="{y}">{escape(ci_text)}</text>',
            f'<text class="soft" x="720" y="{y}">{r["recent"]}</text>',
            f'<text class="soft" x="940" y="{y}">{escape(r["release"])}</text>',
            f'<text class="{live_class}" x="1130" y="{y}">{escape(live)}</text>',
        ]
        y += row_h
    for name, result in sites:
        o += [
            f'<text x="40" y="{y}">{escape(name)}</text>',
            f'<text class="soft" x="330" y="{y}">website</text>',
            f'<text class="{"live" if result.startswith("200") else "bad"}" x="1130" y="{y}">{escape(result)}</text>',
        ]
        y += row_h
    o.append("</svg>")
    return "\n".join(o) + "\n"


def main() -> None:
    rows = [repo_row(p) for p in DATA["projects"]]
    for r in rows:
        if r["live"]:
            r["probe"] = probe(r["live"])
    sites = [(s["name"], probe(s["url"])) for s in DATA["sites"]]
    (ROOT / "assets" / "status.svg").write_text(render(rows, sites))
    print("status:", ", ".join(f"{r['name']} {r['ci']}" for r in rows))


if __name__ == "__main__":
    main()
