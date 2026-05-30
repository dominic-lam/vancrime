# Vancouver Crime Analysis — TODO

## NEXT SESSION
- Enable GitHub Pages: `gh api -X POST repos/dominic-lam/vancrime/pages -f 'source[branch]=main' -f 'source[path]=/'` (publishes the site publicly)
- Fix weekly no-op commits: skip the CI commit when only `generated_utc` changed (compare count + months, not the full file)
- Consider per-capita crime rate toggle (needs neighbourhood population from City of Vancouver census data)

## Active Sprint
- [x] Bootstrap static dashboard (`index.html`, `data/`, `scripts/`, GitHub Actions)
- [x] Fix data pipeline — real VPD download URL (AllYears zip, plain GET)
- [x] Build full-history cube: 915k incidents, 2003-01 → 2026-05, 0.18 MB
- [x] Fix Leaflet SRI hash (broken from the start; map never loaded)
- [x] Add neighbourhood GeoJSON (`data/local-areas.geojson`)
- [x] Sidebar panels: monthly-trend sparkline, crime-type mix (top 3 + expand), top neighbourhoods
- [x] Active-filter chips with per-chip clear
- [x] Click-to-filter on map polygons, ranked rows
- [x] Per-area modal (crime-type breakdown, date-aware, Filter button)
- [x] Reorder sidebar: readout → trend → top hoods → filters → type-mix → reset
- [x] Header info popup (data sources)
- [x] GitHub link button in sidebar
- [x] Reset filters button (disabled at default state)
- [x] Initial commit + push to GitHub

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
- Weekly CI commits even when no new incidents (only `generated_utc` changed) — add a content hash check
- `data/local-areas.geojson` is not refreshed by the CI workflow (stable, but should be noted)
- `img/` folder (reference screenshot) is untracked — either commit or `.gitignore`
