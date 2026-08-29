#!/bin/sh
# Download Natural Earth 10m GeoJSON layers into ./geo/ (≈85 MB total).
# Source: nvkelso/natural-earth-vector on GitHub (public domain data).
set -e
mkdir -p geo && cd geo
base="https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson"
for f in ne_10m_lakes.geojson ne_10m_admin_1_states_provinces_lines.geojson ne_10m_rivers_lake_centerlines.geojson ne_10m_roads.geojson; do
  [ -f "$f" ] || curl -sfO --max-time 180 "$base/$f"
done
ls -la
