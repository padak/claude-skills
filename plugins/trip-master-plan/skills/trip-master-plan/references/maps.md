# Maps from real geography

All maps are hand-authored SVG rendered by `scripts/genmaps.py` from Natural Earth 10m data — never schematic hand-drawn sketches, never external tile services (the artifact sandbox blocks them, and inline SVG is sharper and theme-aware anyway).

## Setup

```bash
sh scripts/fetch_geo.sh        # downloads geo/*.geojson (~85 MB) from GitHub
python3 scripts/genmaps.py mapspecs.json maps_out.json      # route maps
python3 scripts/genmaps.py dayspecs.json daymaps_out.json   # per-day maps
```

Outputs are JSON dicts `{spec_id: "<svg …>"}` — splice each SVG into its `<figure class="map">` / `<figure class="dmap">`.

## Mapspec schema (one object per map)

```json
{
  "id": "A", "color": "--lake", "size": [640, 420],
  "bbox": [-90.7, 41.5, -86.6, 43.85],
  "river_rank": 6,
  "aria": "Accessible description of the map",
  "stops": {
    "ohare": {"name": "Chicago O'Hare", "ll": [-87.905, 41.977], "num": 1,
               "anchor": "end", "dx": -12, "dy": 4},
    "wilmette": {"name": "Wilmette", "ll": [-87.685, 42.075], "major": false, "dx": 9, "dy": -4}
  },
  "order": ["ohare", "wilmette"],
  "legs": [["ohare", "wilmette"]],
  "statelabels": [["WISCONSIN", [-88.25, 43.55]]],
  "waterlabels": [["LAKE MICHIGAN", [-86.98, 42.75], -73]]
}
```

Notes: `ll` is `[lon, lat]`. `major: false` renders a small ring without a number. `color` must be one of the route accent CSS variables. Legs are routed along the Natural Earth roads layer via Dijkstra (nodes merged at ~1 km, gaps ≤3.5 km bridged); a leg falls back to a straight line only when the graph fails — the script prints fallback counts, investigate any nonzero on a road trip.

## Per-day maps

Derive from the route spec: subset of stops in visiting order, consecutive legs, auto bbox = min/max of stop coordinates padded ~40 % horizontally / 30 % vertically (minimum span 0.45°×0.32°), size ≈360×300, numbering restarted 1..n. Skip days without driving. In the figcaption: `≈ {km} km · ~{čas} jízdy · čísla = pořadí zastávek · <a …>Google Maps ↗</a>`.

## Distances and times

Sum leg lengths from the road graph, then sanity-check against known real-world driving distances — the NE road graph overestimates up to ~15 % (bridging penalty); prefer curated realistic values when they disagree. State per-route totals in `.route-stats`, per-day totals in the day-map figcaption, and flag any segment above the user's driving limit honestly (in the drive bar, the comparison table and the lede).

## Google Maps deep links

```
https://www.google.com/maps/dir/?api=1&travelmode=driving
  &origin=<urlencoded>&destination=<urlencoded>
  &waypoints=<wp1>%7C<wp2>…            (≤9 waypoints)
```

One per route (all anchor stops) and one per day (that day's stops). Use recognizable place names ("Illinois Railway Museum Union IL"), not bare coordinates.

## Label hygiene

After generating, render the page with Playwright and LOOK at every map (screenshot per figure). Fix collisions by adjusting per-stop `anchor/dx/dy` in the spec and regenerating. Text labels get a paint-order halo from the stylesheet, but overlapping the route line or clipping at the bbox edge must be fixed in the spec (widen bbox padding or move the label side).
