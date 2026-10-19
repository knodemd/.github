"""Draw the map of knodemd's repositories, in the Knode brand.

Reads map/repos.yml, asks GitHub which repositories exist, and writes profile/map.svg.
Fails when a repository of the organisation is not declared in repos.yml, so the map never falls behind.

    python3 map/render.py            # needs PyYAML; set GITHUB_TOKEN to avoid rate limits
"""

import base64
import json
import os
import sys
import urllib.request
from html import escape
from pathlib import Path

import yaml

ORG = "knodemd"
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "profile" / "map.svg"

INK, PAPER, INDIGO, MUTED, LINE, PANEL = "#0B0B14", "#F3F2EE", "#818CF8", "#A3A2BA", "#2A2A44", "#11111C"
W, H, GAP_X, GAP_Y, PAD, TOP = 230, 66, 28, 64, 48, 112


def org_repos():
    """The public, non-archived repositories of the organisation."""
    req = urllib.request.Request(f"https://api.github.com/orgs/{ORG}/repos?per_page=100&type=public")
    if os.environ.get("GITHUB_TOKEN"):
        req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with urllib.request.urlopen(req) as res:
        return {r["name"] for r in json.load(res) if not r["archived"]}


def font(name):
    data = base64.b64encode((ROOT / "fonts" / f"{name}.woff2").read_bytes()).decode()
    return f'@font-face{{font-family:"{name}";src:url(data:font/woff2;base64,{data}) format("woff2")}}'


def main():
    repos = yaml.safe_load((ROOT / "repos.yml").read_text())["repos"]
    declared = {r["name"] for r in repos}
    existing = org_repos()

    missing = sorted(existing - declared)
    if missing:
        sys.exit(f"Not in map/repos.yml: {', '.join(missing)}. Declare every repository before drawing the map.")
    for r in repos:
        for dep in r.get("uses", []):
            if dep not in declared:
                sys.exit(f"{r['name']} uses {dep}, which is not in map/repos.yml.")
        if r["name"] not in existing and not r.get("planned"):
            sys.exit(f"{r['name']} does not exist on GitHub; mark it planned or remove it.")

    # columns by dependency depth: a repository sits right of everything it uses;
    # repositories nothing uses and that use nothing sit in a row of their own at the bottom
    by = {r["name"]: r for r in repos}
    used = {d for r in repos for d in r.get("uses", [])}
    linked = [r for r in repos if r.get("uses") or r["name"] in used]
    alone = [r for r in repos if r not in linked]
    depth = {}

    def level(n):
        if n not in depth:
            depth[n] = 1 + max((level(d) for d in by[n].get("uses", [])), default=-1)
        return depth[n]

    for r in linked:
        level(r["name"])
    cols = {}
    for r in linked:
        cols.setdefault(depth[r["name"]], []).append(r)
    pos, rows = {}, []
    tallest = max(len(c) for c in cols.values())
    for c, members in sorted(cols.items()):
        top = TOP + (tallest - len(members)) * (H + GAP_Y / 2) / 2
        for i, r in enumerate(members):
            pos[r["name"]] = (PAD + c * (W + 90), top + i * (H + GAP_Y / 2))
    width = PAD * 2 + len(cols) * W + (len(cols) - 1) * 90
    y = TOP + tallest * (H + GAP_Y / 2) + 40
    rows.append(("PROJECT", y))
    for i, r in enumerate(alone):
        pos[r["name"]] = (PAD + i * (W + GAP_X), y)
    width = max(width, PAD * 2 + len(alone) * W + (len(alone) - 1) * GAP_X)
    height = y + H + PAD
    rows.insert(0, ("REPOSITORIES BY WHAT THEY USE", TOP))

    edges = []
    for r in repos:
        for dep in r.get("uses", []):
            (ax, ay), (bx, by_) = pos[dep], pos[r["name"]]
            x1, y1, x2, y2 = ax + W, ay + H / 2, bx, by_ + H / 2
            mx = (x1 + x2) / 2
            d = f"M{x1} {y1}C{mx} {y1} {mx} {y2} {x2} {y2}"
            planned = r.get("planned") or by[dep].get("planned")
            dash = ' stroke-dasharray="6 6"' if planned else ""
            edges.append(f'<path d="{d}" fill="none" stroke="{MUTED}" stroke-width="1.6"{dash} marker-end="url(#a)"/>')

    boxes = []
    for r in repos:
        x, y = pos[r["name"]]
        planned = r.get("planned")
        stroke = INDIGO if r.get("group") == "product" else LINE
        dash = ' stroke-dasharray="7 6"' if planned else ""
        tag = f' <tspan fill="{INDIGO}">{escape(planned)}</tspan>' if planned else ""
        boxes.append(
            f'<a href="https://github.com/{ORG}/{escape(r["name"])}"><g>'
            f'<rect x="{x}" y="{y}" width="{W}" height="{H}" rx="14" fill="{INK}" stroke="{stroke}" stroke-width="1.6"{dash}/>'
            f'<text x="{x + 18}" y="{y + 28}" class="n">{escape(r["name"].upper())}</text>'
            f'<text x="{x + 18}" y="{y + 48}" class="d">{escape(r["what"])}{tag}</text></g></a>'
        )

    labels = "".join(f'<text x="{PAD}" y="{y - 14}" class="g">{label}</text>' for label, y in rows)
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="The repositories of Knode and how they depend on each other">
<style>{font("KnodeLine")}{font("KnodeBlock")}
.t{{font:24px "KnodeBlock",monospace;fill:{PAPER}}}.g{{font:13px "KnodeLine",monospace;fill:{MUTED};letter-spacing:.06em}}
.n{{font:15px "KnodeLine",monospace;fill:{PAPER}}}.d{{font:13px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;fill:{MUTED}}}</style>
<defs><marker id="a" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L8 4L0 8z" fill="{MUTED}"/></marker></defs>
<rect width="100%" height="100%" rx="20" fill="{PANEL}"/>
<text x="{PAD}" y="62" class="t">KNODE REPOSITORIES</text>
{labels}{"".join(edges)}{"".join(boxes)}</svg>
'''
    OUT.write_text(svg)
    print(f"wrote {OUT.relative_to(ROOT.parent)}: {len(repos)} repositories")


if __name__ == "__main__":
    main()
