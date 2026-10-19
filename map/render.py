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

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grid import path_d

ORG = "knodemd"
ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / "profile"
README = OUT / "README.md"

THEMES = {
    # name: (box fill, text, muted text, box line, product line, arrows)
    "dark": ("#0B0B14", "#F3F2EE", "#A3A2BA", "#2A2A44", "#818CF8", "#A3A2BA"),
    "light": ("#FFFFFF", "#0B0B14", "#5E5D73", "#DAD8E2", "#0B0B14", "#5E5D73"),
}
INDIGO = "#818CF8"
W, H, GAP_X, GAP_Y, PAD, TOP = 290, 66, 28, 64, 48, 112
# no side margin, so the map lines up with the repository cards below it
PAD_X = 2


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
            pos[r["name"]] = (PAD_X + c * (W + 90), top + i * (H + GAP_Y / 2))
    width = PAD_X * 2 + len(cols) * W + (len(cols) - 1) * 90
    y = TOP + tallest * (H + GAP_Y / 2) + 40
    rows.append(("PROJECT", y))
    # the project row stretches to the same width as the columns above
    span = width - PAD_X * 2
    aw = (span - (len(alone) - 1) * GAP_X) / len(alone) if alone else W
    widths = {}
    for i, r in enumerate(alone):
        pos[r["name"]] = (PAD_X + i * (aw + GAP_X), y)
        widths[r["name"]] = aw
    height = y + H + PAD + 44
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
            edges.append(f'<path d="{d}" fill="none" stroke="MUTED_STROKE" stroke-width="1.6"{dash} marker-end="url(#a)"/>')

    icons = json.loads((ROOT / "icons.json").read_text())["icons"]
    by_kebab = {k.lower().replace(" ", "-"): v for k, v in icons.items()}
    for theme, (fill, text, muted, line, product, arrow) in THEMES.items():
        boxes = []
        for r in repos:
            x, y = pos[r["name"]]
            bw = widths.get(r["name"], W)
            planned = r.get("planned")
            stroke = product if r.get("group") == "product" else line
            dash = ' stroke-dasharray="7 6"' if planned else ""
            tag = f' <tspan fill="{INDIGO}">{escape(planned)}</tspan>' if planned else ""
            glyph = path_d(by_kebab.get(r.get("icon", "node"), by_kebab["node"]), .5)
            boxes.append(
                f'<rect x="{x}" y="{y}" width="{bw}" height="{H}" rx="14" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{dash}/>'
                f'<g transform="translate({x + 16} {y + 19}) scale({28 / 7})"><path d="{glyph}" fill="{INDIGO if r.get("group") == "product" else text}" fill-rule="evenodd"/></g>'
                f'<text x="{x + 56}" y="{y + 28}" class="n">{escape(r["name"].upper())}</text>'
                f'<text x="{x + 56}" y="{y + 48}" class="d">{escape(r["what"])}{tag}</text>'
            )
        labels = "".join(f'<text x="{PAD_X}" y="{y - 14}" class="g">{label}</text>' for label, y in rows)
        ly = height - 30
        labels += (f'<g class="d">'
                   f'<rect x="{PAD_X}" y="{ly - 12}" width="26" height="16" rx="5" fill="none" stroke="{product}" stroke-width="1.6"/><text x="{PAD_X + 36}" y="{ly + 1}">Product</text>'
                   f'<rect x="{PAD_X + 120}" y="{ly - 12}" width="26" height="16" rx="5" fill="none" stroke="{muted}" stroke-width="1.6"/><text x="{PAD_X + 156}" y="{ly + 1}">Exists</text>'
                   f'<rect x="{PAD_X + 232}" y="{ly - 12}" width="26" height="16" rx="5" fill="none" stroke="{muted}" stroke-width="1.6" stroke-dasharray="5 4"/><text x="{PAD_X + 268}" y="{ly + 1}">Planned, with its version</text>'
                   f'<path d="M{PAD_X + 470} {ly - 4}L{PAD_X + 506} {ly - 4}" stroke="{arrow}" stroke-width="1.6" marker-end="url(#a)"/><text x="{PAD_X + 518}" y="{ly + 1}">Uses</text></g>')
        lines = "".join(e.replace("MUTED_STROKE", arrow) for e in edges)
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-label="The repositories of Knode and how they depend on each other">
<style>{font("KnodeLine")}{font("KnodeBlock")}
.t{{font:24px "KnodeBlock",monospace;fill:{text}}}.g{{font:13px "KnodeLine",monospace;fill:{muted};letter-spacing:.06em}}
.n{{font:15px "KnodeLine",monospace;fill:{text}}}.d{{font:13px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;fill:{muted}}}</style>
<defs><marker id="a" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L8 4L0 8z" fill="{arrow}"/></marker></defs>
<text x="{PAD_X}" y="62" class="t">KNODE REPOSITORIES</text>
{labels}{lines}{"".join(boxes)}</svg>
'''
        (OUT / f"map-{theme}.svg").write_text(svg)
    # one clickable card per repository, since links inside an image are not allowed on GitHub
    (OUT / "repos").mkdir(exist_ok=True)
    for old in (OUT / "repos").glob("*.svg"):
        old.unlink()
    CW, CH = 420, 64
    cells = []
    for r in repos:
        slug = r["name"].lstrip(".") or r["name"]
        rows = by_kebab.get(r.get("icon", "node"), by_kebab["node"])
        glyph = path_d(rows, .5)
        for theme, (fill, text, muted, line, product, arrow) in THEMES.items():
            planned = r.get("planned")
            stroke = product if r.get("group") == "product" else line
            dash = ' stroke-dasharray="7 6"' if planned else ""
            tag = f' <tspan fill="{INDIGO}">{escape(planned)}</tspan>' if planned else ""
            card = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CW} {CH}" width="{CW}" height="{CH}" role="img" aria-label="{escape(r["name"])}">'
                    f'<style>{font("KnodeLine")}.n{{font:15px "KnodeLine",monospace;fill:{text}}}.d{{font:13px -apple-system,"Segoe UI",Helvetica,Arial,sans-serif;fill:{muted}}}</style>'
                    f'<rect x="1" y="1" width="{CW - 2}" height="{CH - 2}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash}/>'
                    f'<g transform="translate(18 18) scale({28 / 7})"><path d="{glyph}" fill="{INDIGO if r.get("group") == "product" else text}" fill-rule="evenodd"/></g>'
                    f'<text x="62" y="29" class="n">{escape(r["name"].upper())}</text>'
                    f'<text x="62" y="47" class="d">{escape(r["what"])}{tag}</text>'
                    f'<path d="M{CW - 30} 27L{CW - 24} 32L{CW - 30} 37" fill="none" stroke="{muted}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>\n')
            (OUT / "repos" / f"{slug}-{theme}.svg").write_text(card)
        link = f"https://github.com/{ORG}/{r['name']}" if r["name"] in existing else f"https://github.com/{ORG}"
        cells.append(f'<a href="{link}"><picture><source media="(prefers-color-scheme: dark)" srcset="repos/{slug}-dark.svg">'
                     f'<img src="repos/{slug}-light.svg" alt="{escape(r["name"])}: {escape(r["what"])}" width="49%"></picture></a>')
    order = {"product": 0, "alongside": 1, "design": 2, "project": 3}
    titles = {"product": "Product", "alongside": "Alongside", "design": "Design", "project": "Project"}
    groups = {}
    for r, cell in zip(repos, cells):
        groups.setdefault(r.get("group", "project"), []).append(cell)
    rows_html = "\n\n".join(f"#### {titles[g]}\n\n<p>\n" + "\n".join(groups[g]) + "\n</p>" for g in sorted(groups, key=lambda g: order.get(g, 9)))
    readme = README.read_text()
    start, end = "<!-- repos:start -->", "<!-- repos:end -->"
    if start in readme and end in readme:
        before, rest = readme.split(start, 1)
        README.write_text(before + start + "\n" + rows_html + "\n" + end + rest.split(end, 1)[1])
    print(f"wrote the map, {len(repos)} repository cards and the profile list")


if __name__ == "__main__":
    main()
