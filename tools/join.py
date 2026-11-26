"""Handles one issue opened on this repo (run by .github/workflows/ping.yml).

  title "ping"    adds the author as a peer in peers.json (once), rebuilds the banner, and writes a pong
                  with the route their message took through the banner's network
  title "unping"  removes them again
  anything else   is ignored, as are bots and logins in tools/blocklist.txt

Reads the event from $GITHUB_EVENT_PATH, writes `action=...` to $GITHUB_OUTPUT and the reply to
$COMMENT_FILE. Only a login that passes GitHub's own format check ever reaches a file or a reply.

Local test:  GITHUB_EVENT_PATH=event.json COMMENT_FILE=/tmp/c.md python tools/join.py
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import build_assets as assets

ROOT = Path(__file__).resolve().parent.parent
LOGIN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
PROFILE = "https://github.com/amirradjou"


def output(action: str) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a") as f:
            f.write(f"action={action}\n")
    print(f"action={action}")


def blocked(login: str) -> bool:
    path = ROOT / "tools" / "blocklist.txt"
    names = {line.strip().lower() for line in path.read_text().splitlines() if line.strip() and not line.startswith("#")}
    return login.lower() in names


def save(peers: list[dict]) -> None:
    data = json.loads(assets.PEERS.read_text())
    data["peers"] = sorted(peers, key=lambda p: p["joined"])
    assets.PEERS.write_text(json.dumps(data, indent=2) + "\n")


def route(login: str) -> tuple[str, int, int]:
    """Which projects the visitor's message reached at each hop, on the banner's own network."""
    visitors = assets.load_peers()
    pts, names, edges, _ = assets.network(visitors)
    me = names.index("@" + login) if ("@" + login) in names else None
    if me is None:  # beyond the banner's slots: route from the newest slot instead
        me = names.index("@" + visitors[0]["login"])
    hops, _ = assets.flood(pts, edges, me)
    by_hop: dict[int, list[str]] = {}
    for i, name in enumerate(names):
        if name and not name.startswith("@"):
            by_hop.setdefault(hops[i], []).append(name)
    lines = [f"traceroute to amirradjou, from @{login}"]
    lines += [f" hop {h:>2}  {', '.join(sorted(by_hop[h]))}" for h in sorted(by_hop)]
    farthest = max(by_hop)
    reached = sum(len(v) for v in by_hop.values())
    return "\n".join(lines), reached, farthest


def main() -> None:
    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    issue = event["issue"]
    title = (issue.get("title") or "").strip().lower()
    user = issue.get("user") or {}
    login = user.get("login") or ""
    comment = Path(os.environ.get("COMMENT_FILE", "comment.md"))

    if title not in ("ping", "unping") or user.get("type") != "User" or not LOGIN.match(login) or blocked(login):
        output("ignore")
        return

    peers = json.loads(assets.PEERS.read_text())["peers"]
    present = any(p["login"].lower() == login.lower() for p in peers)

    if title == "unping":
        if not present:
            output("ignore")
            return
        save([p for p in peers if p["login"].lower() != login.lower()])
        assets.main()
        comment.write_text(f"Done, @{login}: you are no longer a peer in the network on [my profile]({PROFILE}).\n")
        output("leave")
        return

    if not present:
        peers.append({"login": login, "joined": issue["created_at"], "issue": issue["number"]})
        save(peers)
        assets.main()
    text, reached, farthest = route(login)
    first = "You are now a peer" if not present else "You were already a peer"
    comment.write_text(
        f"**pong**, @{login}. {first} in the network on [my profile]({PROFILE}); the banner can take a minute to update.\n\n"
        f"Your message flooded the network and reached all {reached} projects, the farthest {farthest} hops away:\n\n"
        f"```\n{text}\n```\n\n"
        "The hops are counted on the banner's own network; it is a drawing, not real latency. "
        "To leave, open an issue titled `unping`.\n\n"
        "<sub>Automated reply from a GitHub Action in this repository.</sub>\n"
    )
    output("join" if not present else "already")


if __name__ == "__main__":
    main()
