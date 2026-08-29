---
name: trip-master-plan
description: Plan a trip end-to-end and deliver a rich, living MASTER itinerary document. Use when the user asks to plan a trip, roadtrip, vacation, výlet, itinerář, cestovní plán, "naplánuj mi cestu/výlet", "trip plan", "master plán", or invokes /trip-master-plan. Interviews the user, researches and date-verifies attractions and local events, then compiles a versioned HTML artifact with route alternatives, real-geography maps, day cards with drive times, photos, weather, official links and research prompts.
---

# Trip MASTER Plan

Produce a single, continuously versioned HTML artifact ("MASTER plán") that the user and their travel companions revisit before and during the trip. Never deliver a plain chat answer for a trip-planning request — the artifact is the deliverable. Work in the user's language throughout (document included).

## Phase 0 — Assessment (AskUserQuestion)

Ask only what the request does not already answer. Two rounds maximum, ≤4 questions each:

Round 1 (trip shape): destination/region + exact dates (check for public holidays at destination — they change opening hours and create festivals); party size and vehicle; interests as multiSelect (offer: příroda, technické památky, umění/architektura, historie, festivaly/trhy/poutě, vinařství/gastro, koupání/pláže, farmy/exkurze — plus anything the request hints at); pace constraint (max driving per segment — default ~2 h with a stop between segments; one base vs. moving camp).

Round 2 (logistics): lodging style (hotel/Airbnb/kemp/mix) and budget per night; whether they want route ALTERNATIVES or one committed route; extras opt-in: photos in the document, auto-refreshing weather, copy-to-clipboard research prompts ("Perplexity buttons"), a concierge system prompt for their research assistant.

If the session appears unattended, use sensible defaults, state them at the top of the document, and proceed.

## Phase 1 — Research first, format later

Do all research BEFORE building the document. For every anchor attraction and every event: verify with WebSearch/WebFetch that it is open/running on the user's exact dates (holiday schedules!). Actively hunt for local, non-touristy happenings in the date window: county fairs, farm events, harvest festivals, museum specials, free city festivals, factory tours. Flag tourist traps to avoid, by name, with an honest alternative.

Label every fact in the document with its verification state (see structure reference): `✓ ověřeno` (confirmed for the exact dates, with source), `ověřit` (plausible, unconfirmed), and a source chip when an idea came from another assistant or the user.

## Phase 2 — Compile the document

Read `references/document-structure.md` and follow it exactly — it carries the CSS design system, the section skeleton, and canonical HTML fragments (comparison table with anchor links, route sections with badge/pitch/stats, day cards with drive bars, tags, verified/check/src chips, copy-prompt buttons, weather chips). Build:

1. Header with title, **version chip** (`VERZE n · vyrobeno <date, time, user's timezone>`) and a legend of markers.
2. Comparison table of route alternatives (3–6), each row anchor-linking to its section; ratings per interest dimension; character summary; a one-line recommendation below.
3. Per route: badge + name, route-sub (stop sequence + why this weekend), **route-stats** (total km, total net driving time, Google Maps deep link `https://www.google.com/maps/dir/?api=1&origin=…&destination=…&waypoints=a%7Cb…`, ≤9 waypoints), and a **pitch paragraph** that sells the route in the subject's own imagery.
4. Day cards: `day-head` (date chip + day title + weather chip), drive bars carrying ONLY logistics (from → to · time · road), every stop as a full bullet with 1–3 sentences of substance, official link on the bold name, verification chips, `Nocleh:` line. On desktop the card is a two-column grid: text left, that day's map right.
5. Practical section (booking urgency, timezones, tolls/park fees, safety), open-questions section, footer with version history and credits.

Publish with the Artifact tool; every later change republishes THE SAME file path/URL, bumps the version chip, and appends one history line to the footer. Before each publish: check tag balance programmatically and screenshot-verify layout with Playwright (light + dark theme; the CSS is token-based for both).

## Phase 3 — Maps from real geography

Never hand-draw schematic maps. Follow `references/maps.md`: download Natural Earth 10m GeoJSON layers (script `scripts/fetch_geo.sh`), write a mapspec JSON (documented schema), and run `scripts/genmaps.py` to render theme-aware SVG maps whose routes follow real roads (Dijkstra over the NE roads layer with gap-bridging). Produce: one overview map per route (numbered stops, state/water labels, figcaption with totals) and one **per-day detail map** (auto bbox, day km + drive time + per-day Google Maps link in the caption). Compute km from the road graph but sanity-check against real-world driving distances; state the longest segment and admit any that exceed the user's limit.

## Phase 4 — Photos

Follow `references/photos.md`. One significant photo per attraction, Wikimedia Commons only (free licenses). If the environment can reach Commons, fetch via its API; if egress is blocked, generate the photo ORDER file (template in the reference) for the user to run in a network-enabled Claude Code and embed the returned zip. Always: resize ~560 px, JPEG q≈72, embed as data URIs in per-day photo strips, link each thumb to its Commons file page, and add a credits line (author + license) to the footer. Never embed images with unknown licensing; report honestly what could not be sourced.

## Phase 5 — Weather

Follow `references/weather.md`. The published artifact sandbox blocks all runtime calls to third-party servers (fetch, scripts AND iframes) — never promise a live external widget. Instead: fetch NWS point forecasts via WebFetch (`forecast.weather.gov/MapClick.php` works even behind egress filters; for non-US destinations find an equivalent fetchable source), build the in-document **weather map widget** (own SVG map + day tabs + embedded JSON `#wx-data`; generator `scripts/wxmap.py`, wiring in the reference), add per-day weather chips fed from the same JSON, and stamp `#wx-stamp`. Then OFFER (AskUserQuestion — creating standing automation requires explicit consent) scheduled refresh tasks via create_trigger: daily before the trip, 2× daily during it, self-deleting after; prompt templates are in the reference.

## Phase 6 — Research prompts & concierge

If opted in: inject the copy-to-clipboard prompt buttons (JS in the structure reference) on every itinerary item — each click copies a complete research prompt (who the travelers are, exact date and day context, 8 standard questions, "verify on official sources, answer in <language>"). On request, generate the travel-concierge system prompt from the template in `references/prompts.md`, filled with this trip's facts.

## Phase 7 — Adversarial audit

Before declaring the document final (and after any large content merge), run a fact-check audit: spawn 3–5 parallel subagents using the `trip-fact-checker` agent definition, one per route/section, instructing each to verify every date, superlative, measurement, price and historical claim via web search and report only errors with corrections and sources. Apply fixes, log the audit in the version history. Treat user-supplied plans from other assistants as leads to verify, never as facts — deduplicate them into the master, tag their origin, and verify the load-bearing claims yourself.

## Iteration etiquette

The user will keep sending additions (other assistants' answers, photos, new wishes). Each iteration: integrate, bump version + timestamp, append history, republish same URL, and answer in chat with only what changed. Keep a "Co zbývá doverifikovat" section honest — when only phone-calls and live booking systems remain, say so and list phone numbers. When the user needs data you cannot reach (blocked hosts, live prices), produce a precise, copy-pastable order/prompt for a tool that can, and integrate the result when it comes back.
