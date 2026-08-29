#!/usr/bin/env python3
"""Generate theme-aware SVG itinerary maps from Natural Earth 10m data."""
import json, math, heapq, sys
from collections import defaultdict

GEO = "geo/"

def load(name):
    return json.load(open(GEO + name))["features"]

lakes = load("ne_10m_lakes.geojson")
borders = load("ne_10m_admin_1_states_provinces_lines.geojson")
rivers = load("ne_10m_rivers_lake_centerlines.geojson")
roads = load("ne_10m_roads.geojson")

def hav(a, b):
    lon1, lat1, lon2, lat2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    d = 2 * math.asin(math.sqrt(math.sin((lat2 - lat1) / 2) ** 2 +
        math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2))
    return 6371.0 * d

def geoms(feat):
    g = feat["geometry"]
    if g is None: return
    t, c = g["type"], g["coordinates"]
    if t == "LineString": yield c
    elif t == "MultiLineString": yield from c
    elif t == "Polygon": yield from c
    elif t == "MultiPolygon":
        for poly in c: yield from poly

def in_bbox(coords, bb, pad=0.5):
    x0, y0, x1, y1 = bb[0]-pad, bb[1]-pad, bb[2]+pad, bb[3]+pad
    return any(x0 <= p[0] <= x1 and y0 <= p[1] <= y1 for p in coords[::max(1, len(coords)//20)])

# ---------- road graph ----------
class Graph:
    def __init__(self, bb):
        self.adj = defaultdict(list)
        self.nodes = {}
        for f in roads:
            for line in geoms(f):
                if not in_bbox(line, bb): continue
                prev = None
                for p in line:
                    key = (round(p[0], 2), round(p[1], 2))  # ~1km merge
                    self.nodes[key] = (p[0], p[1])
                    if prev is not None and prev != key:
                        w = hav(self.nodes[prev], self.nodes[key])
                        self.adj[prev].append((key, w))
                        self.adj[key].append((prev, w))
                    prev = key
        # bridge small data gaps: connect nodes within ~3.5 km
        grid = defaultdict(list)
        for k, v in self.nodes.items():
            grid[(int(v[0] / 0.05), int(v[1] / 0.05))].append(k)
        for k, v in self.nodes.items():
            gx, gy = int(v[0] / 0.05), int(v[1] / 0.05)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for k2 in grid[(gx + dx, gy + dy)]:
                        if k2 <= k: continue
                        d = hav(v, self.nodes[k2])
                        if d < 3.5 and all(n != k2 for n, _ in self.adj[k]):
                            self.adj[k].append((k2, d * 1.5))
                            self.adj[k2].append((k, d * 1.5))
    def nearest(self, pt):
        best, bd = None, 1e9
        for k, v in self.nodes.items():
            d = hav(pt, v)
            if d < bd: bd, best = d, k
        return best, bd
    def route(self, a, b):
        sa, da = self.nearest(a); sb, db = self.nearest(b)
        dist = {sa: 0.0}; prev = {}; pq = [(0.0, sa)]
        target = sb
        while pq:
            d, u = heapq.heappop(pq)
            if u == target: break
            if d > dist.get(u, 1e18): continue
            for v, w in self.adj[u]:
                nd = d + w
                if nd < dist.get(v, 1e18):
                    dist[v] = nd; prev[v] = u
                    heapq.heappush(pq, (nd, v))
        if target not in prev and target != sa:
            return None, None
        path = [target]
        while path[-1] != sa:
            path.append(prev[path[-1]])
        path.reverse()
        coords = [self.nodes[k] for k in path]
        length = dist[target] + da + db
        geo = hav(a, b)
        if geo > 5 and length > 3.0 * geo:  # absurd detour => data gap
            return None, None
        return [list(a)] + coords + [list(b)], length

# ---------- map spec ----------
def project(bb, W, H, pad):
    lon0, lat0, lon1, lat1 = bb
    k = math.cos(math.radians((lat0 + lat1) / 2))
    w_geo = (lon1 - lon0) * k; h_geo = (lat1 - lat0)
    s = min((W - 2 * pad) / w_geo, (H - 2 * pad) / h_geo)
    ox = (W - w_geo * s) / 2; oy = (H - h_geo * s) / 2
    def P(p):
        x = ox + (p[0] - lon0) * k * s
        y = H - oy - (p[1] - lat0) * s
        return x, y
    return P

def path_d(line, P, close=False, prec=1):
    pts = [P(p) for p in line]
    # light simplification: drop points closer than 1.2px
    out = [pts[0]]
    for p in pts[1:]:
        if (p[0]-out[-1][0])**2 + (p[1]-out[-1][1])**2 > 1.4:
            out.append(p)
    if len(out) < 2: out = pts[:2] if len(pts) > 1 else pts
    d = "M" + " L".join(f"{x:.{prec}f},{y:.{prec}f}" for x, y in out)
    if close: d += " Z"
    return d

def render(spec):
    bb = spec["bbox"]; W, H = spec["size"]; P = project(bb, W, H, 8)
    g = Graph(bb)
    parts = []
    cid = spec["id"]
    parts.append(f'<clipPath id="clip{cid}"><rect x="0" y="0" width="{W}" height="{H}" rx="8"/></clipPath>')
    parts.append(f'<g clip-path="url(#clip{cid})">')
    parts.append(f'<rect x="0" y="0" width="{W}" height="{H}" class="gm-land"/>')
    # lakes
    lk = []
    for f in lakes:
        for ring in geoms(f):
            if in_bbox(ring, bb):
                lk.append(path_d(ring, P, close=True))
    parts.append('<path class="gm-water" d="' + " ".join(lk) + '"/>')
    # rivers (major only)
    rv = []
    for f in rivers:
        pr = f.get("properties") or {}
        if (pr.get("scalerank") or 9) > spec.get("river_rank", 5): continue
        for line in geoms(f):
            if in_bbox(line, bb):
                rv.append(path_d(line, P))
    parts.append('<path class="gm-river" fill="none" d="' + " ".join(rv) + '"/>')
    # state borders
    bd = []
    for f in borders:
        pr = f.get("properties") or {}
        if pr.get("ADM0_A3") not in (None, "USA"): continue
        for line in geoms(f):
            if in_bbox(line, bb):
                bd.append(path_d(line, P))
    parts.append('<path class="gm-border" fill="none" d="' + " ".join(bd) + '"/>')
    # interstates faint context
    if spec.get("roads", True):
        rd = []
        for f in roads:
            pr = f.get("properties") or {}
            if pr.get("class") != "Interstate": continue
            for line in geoms(f):
                if in_bbox(line, bb, pad=0.2):
                    rd.append(path_d(line, P))
        parts.append('<path class="gm-road" fill="none" d="' + " ".join(rd) + '"/>')
    # route legs
    color = spec["color"]
    route_paths = []
    fallbacks = 0
    for leg in spec["legs"]:
        a = spec["stops"][leg[0]]["ll"]; b = spec["stops"][leg[1]]["ll"]
        line, length = g.route(a, b)
        if line is None:
            fallbacks += 1
            line = [a, b]
        route_paths.append(path_d(line, P))
    dash = ' stroke-dasharray="6 5"' if False else ""
    parts.append(f'<path fill="none" stroke="var({color})" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" opacity="0.9" d="' + " ".join(route_paths) + '"/>')
    # state labels
    for lab in spec.get("statelabels", []):
        x, y = P(lab[1])
        parts.append(f'<text x="{x:.0f}" y="{y:.0f}" class="gm-state" text-anchor="middle">{lab[0]}</text>')
    for lab in spec.get("waterlabels", []):
        x, y = P(lab[1])
        rot = lab[2] if len(lab) > 2 else 0
        tr = f' transform="rotate({rot} {x:.0f} {y:.0f})"' if rot else ""
        parts.append(f'<text x="{x:.0f}" y="{y:.0f}" class="gm-sea" text-anchor="middle"{tr}>{lab[0]}</text>')
    # stops
    order = spec.get("order") or list(spec["stops"].keys())
    for i, key in enumerate(order, 1):
        st = spec["stops"][key]
        x, y = P(st["ll"])
        big = st.get("major", True)
        r = 7.5 if big else 4
        if big:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="var({color})" stroke="var(--card)" stroke-width="1.6"/>')
            parts.append(f'<text x="{x:.1f}" y="{y + 3.2:.1f}" class="gm-num" text-anchor="middle">{st.get("num", i)}</text>')
        else:
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="var(--card)" stroke="var({color})" stroke-width="2"/>')
        lx, ly = st.get("dx", 10), st.get("dy", 4)
        anchor = st.get("anchor", "start")
        parts.append(f'<text x="{x + lx:.1f}" y="{y + ly:.1f}" class="gm-stop" text-anchor="{anchor}">{st["name"]}</text>')
    parts.append('</g>')
    parts.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="8" fill="none" stroke="var(--line)"/>')
    svg = (f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{spec["aria"]}">' + "".join(parts) + "</svg>")
    sys.stderr.write(f'map {cid}: {fallbacks} fallback legs, {len(svg)//1024} KB\n')
    return svg

import sys as _sys
_in = _sys.argv[1] if len(_sys.argv)>1 else "mapspecs.json"
_out = _sys.argv[2] if len(_sys.argv)>2 else "maps_out.json"
SPECS = json.load(open(_in))
out = {}
for s in SPECS:
    out[s["id"]] = render(s)
json.dump(out, open(_out, "w"))
print("done", {k: len(v) for k, v in out.items()})
