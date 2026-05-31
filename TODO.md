# Vancouver Crime Analysis — TODO

## NEXT SESSION
- Add shareable URL state (`#from=&to=&hood=&type=`) — site is now live; linking to specific filter views is high-value
- Add per-capita crime rate toggle (needs population CSV from City of Vancouver census; changes the whole choropleth story)
- Commit or gitignore `img/` screenshot folder — currently untracked, makes `git status` noisy

## Active Sprint
_(All sprint items shipped — see PROGRESS.md for full history)_

## Backlog
- Per-capita crime rate toggle (needs population CSV; changes the whole map story)
- Shareable URL state (`#from=&to=&hood=&type=`)
- Export current selection as CSV / JSON
- Time-lapse playback (▶ animates choropleth 2003 → now)
- "Top movers" view — compare two periods, show biggest ∆ by hood/type
- Seasonality panel — month-of-year patterns
- Monthly-trend sparkline inside the per-area modal + citywide comparison line
- Deep-link directly to a neighbourhood modal
- Add Musqueam + Stanley Park polygons (they exist in crime data but not the city boundary file)

## Tech Debt
- `data/local-areas.geojson` is not refreshed by the CI workflow (stable, but should be noted)
- `img/` folder (reference screenshot) is untracked — either commit or `.gitignore`
