#!/usr/bin/env python3
"""Weather base-map generator: region map with location markers whose values
are filled at runtime from the #wx-data JSON (see references/weather.md).

Usage: python3 wxmap.py wxspec.json > wxmap.svg
wxspec.json: {"bbox":[lon0,lat0,lon1,lat1], "size":[960,400],
  "sealabel": ["LAKE MICHIGAN", [lon,lat], rotationDeg],
  "locs": {"key": {"name":"Milwaukee","lat":43.04,"lon":-87.91,"anchor":"end","dx":-9}, ...}}
Requires ./geo/ layers (run fetch_geo.sh first).
"""
import json, math, sys
gj=lambda n: json.load(open("geo/"+n))["features"]
lakes=gj("ne_10m_lakes.geojson"); borders=gj("ne_10m_admin_1_states_provinces_lines.geojson"); rivers=gj("ne_10m_rivers_lake_centerlines.geojson")
def geoms(f):
    g=f["geometry"]
    if not g: return
    t,c=g["type"],g["coordinates"]
    if t=="LineString": yield c
    elif t=="MultiLineString": yield from c
    elif t=="Polygon": yield from c
    elif t=="MultiPolygon":
        for poly in c: yield from poly
spec=json.load(open(sys.argv[1]))
bb=tuple(spec["bbox"]); W,H=spec.get("size",[960,400])
def inb(cs,pad=0.5):
    return any(bb[0]-pad<=p[0]<=bb[2]+pad and bb[1]-pad<=p[1]<=bb[3]+pad for p in cs[::max(1,len(cs)//20)])
k=math.cos(math.radians((bb[1]+bb[3])/2))
s=min((W-16)/((bb[2]-bb[0])*k),(H-16)/(bb[3]-bb[1]))
ox=(W-(bb[2]-bb[0])*k*s)/2; oy=(H-(bb[3]-bb[1])*s)/2
def P(p): return (ox+(p[0]-bb[0])*k*s, H-oy-(p[1]-bb[1])*s)
def pd(line,close=False):
    pts=[P(p) for p in line]; out=[pts[0]]
    for p in pts[1:]:
        if (p[0]-out[-1][0])**2+(p[1]-out[-1][1])**2>1.4: out.append(p)
    d="M"+" L".join(f"{x:.1f},{y:.1f}" for x,y in out)
    return d+(" Z" if close else "")
parts=[f'<clipPath id="clipWX"><rect width="{W}" height="{H}" rx="8"/></clipPath><g clip-path="url(#clipWX)">',
       f'<rect width="{W}" height="{H}" class="gm-land"/>']
parts.append('<path class="gm-water" d="'+" ".join(pd(r,True) for f in lakes for r in geoms(f) if inb(r))+'"/>')
parts.append('<path class="gm-river" fill="none" d="'+" ".join(pd(l) for f in rivers if ((f.get("properties") or {}).get("scalerank") or 9)<=6 for l in geoms(f) if inb(l))+'"/>')
parts.append('<path class="gm-border" fill="none" d="'+" ".join(pd(l) for f in borders if (f.get("properties") or {}).get("ADM0_A3") in (None,"USA") for l in geoms(f) if inb(l))+'"/>')
if spec.get("sealabel"):
    t,ll,rot=spec["sealabel"]; x,y=P(ll)
    parts.append(f'<text x="{x:.0f}" y="{y:.0f}" class="gm-sea" text-anchor="middle" transform="rotate({rot} {x:.0f} {y:.0f})">{t}</text>')
for key,L in spec["locs"].items():
    x,y=P((L["lon"],L["lat"])); anc=L.get("anchor","middle"); dx=L.get("dx",0)
    parts.append(f'<g><circle cx="{x:.0f}" cy="{y:.0f}" r="3.5" class="wx-dot"/>'
                 f'<text x="{x+dx:.0f}" y="{y-8:.0f}" class="wx-val" data-loc="{key}" text-anchor="{anc}">—</text>'
                 f'<text x="{x+dx:.0f}" y="{y+16:.0f}" class="wx-name" text-anchor="{anc}">{L["name"]}</text></g>')
parts.append(f'</g><rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="8" fill="none" stroke="var(--line)"/>')
print(f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="Mapa regionu s předpovědí počasí" style="display:block;max-width:100%;height:auto">'+"".join(parts)+'</svg>')
