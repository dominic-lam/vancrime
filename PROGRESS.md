# Progress Log

## 2026-05-29 (Session 1 — Full dashboard build)
**Completed:** Built the entire Vancouver Crime Analysis dashboard from scratch — fixed the broken VPD data pipeline (wrong URL; now downloads the AllYears zip), built a 915k-incident full-history count-cube (2003-present, 0.18 MB), and shipped the full dashboard UI: choropleth map, sidebar with trend sparkline / type-mix / top-hoods panels, active-filter chips, per-area modal, info popup, and GitHub link. Fixed a critical Leaflet SRI hash that blocked the map from ever loading. Initial commit pushed to GitHub.
**In progress:** GitHub Pages not yet enabled; weekly CI commits even when data hasn't changed (generated_utc always changes).
**Next session should:** Enable GitHub Pages (`gh api -X POST repos/dominic-lam/vancrime/pages ...`) and fix the no-op weekly commit issue.

## 2026-05-29 (Session 2 — Mobile layout & CI fix)
**Completed:** Added mobile-responsive layout (single scrolling column below 760px), reference screenshot, and fixed the CI no-op weekly commit (skips commit when only `generated_utc` changed).
**In progress:** GitHub Pages not yet enabled; mobile section navigation still a single scrolling list on small screens.
**Next session should:** Enable GitHub Pages and add a section tab-bar to improve mobile navigation.

## 2026-05-30 (Session 3 — GitHub Pages live & mobile tabs)
**Completed:** Enabled GitHub Pages — site is now live at https://dominic-lam.github.io/vancrime/; merged PR #1 adding a sticky section tab-bar (Areas / Filters / Types) on narrow screens using `display:contents` on desktop so it's fully inert outside mobile.
**In progress:** Nothing.
**Next session should:** Add shareable URL state (`#from=&to=&hood=&type=`) so users can link to a specific filter view on the live site.
