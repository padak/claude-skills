# Weather

## Hard constraint (explain it to the user before they ask for widgets)

The published artifact runs in a sandbox that blocks every runtime request to third-party servers: fetch/XHR, external scripts, external stylesheets/images AND iframes (verified empirically — an embedded windy.com iframe renders as a grey blocked-frame box). No Windy/Open-Meteo/any live widget can run inside the page, with or without API keys. Never accept an API key for this purpose into the document; if the user pasted one in chat, advise rotating it.

The working pattern instead: **snapshot data embedded in the page + scheduled tasks that refresh the snapshot by republishing**. With 1–2 refreshes a day this behaves like a live widget for trip-planning purposes.

## Getting forecast data

`api.weather.gov` and `api.open-meteo.com` are typically blocked by egress AND robots-disallowed for WebFetch. What works: WebFetch on the NWS human pages:

```
https://forecast.weather.gov/MapClick.php?lat=<LAT>&lon=<LON>&unit=0&lg=english&FcstType=text
```

Prompt WebFetch to return, per trip day: daily high °F, precip chance %, short condition. NWS covers ~7 days — days beyond the horizon are honest "—". Convert °F→°C (round). Icon map: ☀ sunny/clear · ⛅ partly · ☁ cloudy · 🌧 rain/showers · ⛈ thunderstorms · 🌫 fog. Non-US trips: find an equivalent robots-friendly national-service page and adapt.

## In-document widget

1. Pick ~8–12 weather localities (route bases + overnight stops), each mapped to the itinerary days that happen there.
2. Generate the region weather map: write `wxspec.json` (bbox, locs with label anchors — schema in `scripts/wxmap.py` docstring), run `python3 scripts/wxmap.py wxspec.json > wxmap.svg`.
3. Assemble the section (canonical wiring in document-structure.md): day-tab buttons (`.wx-tab`, one per trip day), the SVG in a card, a note with `<span id="wx-stamp">` timestamp, `<script id="wx-data" type="application/json">` holding `{"loc":{"day":{"t":27,"p":20,"i":"⛅"},…},…}` (day keys are short slugs like pa/so/ne/po; omit `p` when 0/unknown; omit a day with no forecast), and the runner script (MUST be wrapped in `DOMContentLoaded` — it also fills the per-day chips that appear later in the document).
4. Per-day chips in day-heads: `<span class="wx"><span class="wxv" data-wx="loc:day">static fallback</span> · <a href=windy point link>Windy ↗</a></span>` — JS overwrites from the JSON; static text remains if JS fails.
5. Add a row of Windy point links (`https://www.windy.com/<lat>/<lon>?temp,<lat>,<lon>,9`) per route base + waves/marine link where relevant — those open the LIVE forecast outside the sandbox.

## Scheduled auto-refresh (ask consent first — it is standing automation)

Offer via AskUserQuestion: daily / 2× daily during the trip / manual. Create with `create_trigger` (cron in UTC — convert from the user's timezone). Two tasks work well: a daily morning task (runs every day, contains the SELF-CLEANUP clause: if today in the destination timezone is past the trip end, list_triggers → delete BOTH tasks by name and stop) and a trip-days-only afternoon task (cron day-of-month range, with a year-guard cleanup clause so it cannot fire next year).

The refresh prompt must be fully standalone (fresh session, no context): artifact URL; the 11 localities with coordinates and the MapClick URL pattern; °F→°C + icon rules; instructions to Artifact-read the URL, modify ONLY `#wx-data` JSON (preserving already-past days) and `#wx-stamp` (user-timezone timestamp), keep valid JSON, republish with `url` param and a `wx-refresh-<date>` label, retry once on version conflict, keep old data for failed localities, and report briefly.
