# Photos

Goal: one significant, freely licensed photo per attraction, embedded as a data URI (the artifact sandbox blocks external images), attributed properly.

## Source policy

Wikimedia Commons only (CC BY / CC BY-SA / CC0 / public domain). Official sites only when they explicitly allow reuse. Never embed a photo with unknown licensing, never pass off an unrelated image; if nothing exists (it happens — small wineries, local carousels), skip and say so. A "visually representative but geographically wrong" photo may be used only with an honest caption ("ilustrační").

## Pipeline A — direct (network allows commons.wikimedia.org)

1. Search: `https://commons.wikimedia.org/w/api.php?action=query&format=json&list=search&srnamespace=6&srsearch=<query>` — craft queries per attraction (landmark + city; prefer the iconic subject: the building, the signature exhibit, the shoreline).
2. Fetch thumbnail (`…/thumb/...800px-…`) + `extmetadata` (Artist, LicenseShortName) via `imageinfo`.
3. Review candidates VISUALLY on a contact sheet (Playwright/PIL) — reject winter shots, watermarks, portraits of people; prefer landscape orientation.
4. `python3 scripts/embed_photos.py <dir>` → 560 px q72 data URIs.

## Pipeline B — order file (egress blocked)

Test reachability first (`curl -sI` to upload.wikimedia.org). If blocked, generate a photo ORDER markdown the user runs in a network-enabled Claude Code, then embed the returned zip. Order file must specify exactly:

- task: find one freely licensed photo per manifest entry (Commons first; skip rather than substitute; report skips with reasons)
- output: `photos/<slug>.jpg` (800 px wide, q≈78, EXIF stripped), `credits.json` = `{slug: {title, source_url (file page), author, license}}`, `report.md`, zipped
- selection criteria: most characteristic subject, landscape, no watermark, no winter
- manifest: JSON array of `{slug, hledat: "search phrase"}` for every attraction

## Embedding

Per-day photo strip before the tags row (fragment in document-structure.md): `div.phs > a.ph[href=commons file page][title="Author · License"] > img[src=dataURI] + span caption`. Reuse of a photo across routes duplicates the data URI — acceptable, but keep total page ≤ ~5 MB (recompress harder if needed; artifact hard limit 16 MB).

## Credits (required by CC licenses)

Footer block: `<b>Fotografie</b> — Wikimedia Commons, užito v souladu s licencemi:` followed by `<a href=file-page>Caption</a> © Author (License)` for every distinct photo. The thumb's link + title attribute complement this but do not replace it.
