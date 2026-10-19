# Copied from knodemd/brand (Source/engine.py): the grid outline with every corner rounded by half a cell.
"""Grid → outline with every corner (convex or concave) turned into a quarter arc of radius r (in cells)."""
import math
def contours(rows):
    H, W = len(rows), max(len(r) for r in rows)
    f = lambda x, y: 0 <= y < H and 0 <= x < len(rows[y]) and rows[y][x] == "#"
    out = {}
    for y in range(H):
        for x in range(W):
            if not f(x, y): continue
            if not f(x, y - 1): out.setdefault((x, y), []).append((x + 1, y))
            if not f(x + 1, y): out.setdefault((x + 1, y), []).append((x + 1, y + 1))
            if not f(x, y + 1): out.setdefault((x + 1, y + 1), []).append((x, y + 1))
            if not f(x - 1, y): out.setdefault((x, y + 1), []).append((x, y))
    loops = []
    while out:
        start = next(iter(out)); prev = None; cur = start; loop = []
        while True:
            nxts = out.get(cur)
            if not nxts: break
            if len(nxts) > 1 and prev:   # diagonal touch: turn right so cells stay separate
                dx, dy = cur[0] - prev[0], cur[1] - prev[1]
                nxt = next((n for n in nxts if (n[0] - cur[0], n[1] - cur[1]) == (-dy, dx)), nxts[0])
            else: nxt = nxts[0]
            nxts.remove(nxt)
            if not nxts: del out[cur]
            loop.append(cur); prev, cur = cur, nxt
            if cur == start and (start not in out): break
        pts = [p for i, p in enumerate(loop)
               if (loop[i - 1][0] - p[0]) * (loop[(i + 1) % len(loop)][1] - p[1]) - (loop[i - 1][1] - p[1]) * (loop[(i + 1) % len(loop)][0] - p[0]) != 0]
        if len(pts) >= 4: loops.append(pts)
    return loops
def corners(pts, r):
    n = len(pts); res = []
    for i in range(n):
        p, v, q = pts[i - 1], pts[i], pts[(i + 1) % n]
        d1 = ((v[0] - p[0]) / (abs(v[0] - p[0]) + abs(v[1] - p[1])), (v[1] - p[1]) / (abs(v[0] - p[0]) + abs(v[1] - p[1])))
        d2 = ((q[0] - v[0]) / (abs(q[0] - v[0]) + abs(q[1] - v[1])), (q[1] - v[1]) / (abs(q[0] - v[0]) + abs(q[1] - v[1])))
        cw = d1[0] * d2[1] - d1[1] * d2[0] > 0
        l1 = abs(v[0] - p[0]) + abs(v[1] - p[1]); l2 = abs(q[0] - v[0]) + abs(q[1] - v[1])
        rc = min(r, l1 / 2, l2 / 2)   # never let two arcs on one edge overlap
        res.append(((v[0] - d1[0] * rc, v[1] - d1[1] * rc), (v[0] + d2[0] * rc, v[1] + d2[1] * rc), cw, v, rc))
    return res
def path_d(rows, r=0.5, ox=0, oy=0):
    out = []
    f = lambda v: f"{v:.3f}".rstrip("0").rstrip(".")
    for pts in contours(rows):
        cs = corners(pts, r)
        a, b, cw, v, rc = cs[0]
        out.append(f"M{f(b[0]+ox)} {f(b[1]+oy)}")
        for a, b, cw, v, rc in cs[1:] + cs[:1]:
            out.append(f"L{f(a[0]+ox)} {f(a[1]+oy)}A{f(rc)} {f(rc)} 0 0 {1 if cw else 0} {f(b[0]+ox)} {f(b[1]+oy)}")
        out.append("Z")
    return "".join(out)
def polyline(rows, r=0.5, seg=10):
    """Contours as point lists (arcs sampled) — for TTF."""
    res = []
    for pts in contours(rows):
        ring = []
        for a, b, cw, v, rc in corners(pts, r):
            cx, cy = a[0] + b[0] - v[0], a[1] + b[1] - v[1]
            a0, a1 = math.atan2(a[1] - cy, a[0] - cx), math.atan2(b[1] - cy, b[0] - cx)
            da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
            for k in range(seg + 1):
                t = a0 + da * k / seg; ring.append((cx + rc * math.cos(t), cy + rc * math.sin(t)))
        res.append(ring)
    return res
