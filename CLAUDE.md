# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static Leaflet choropleth of Vancouver Police Department (VPD) open crime data.
No server, no backend, no build step — just `index.html` (CDN deps) reading a
pre-aggregated JSON file, plus a GitHub Actions cron that rebuilds that file
weekly. Deploys for free on GitHub Pages / Vercel from `main` root.

## Commands

```bash
# Serve the dashboard locally (then open http://localhost:8000)
python -m http.server 8000

# Rebuild the cube from a folder of CSVs you already have on disk
python scripts/aggregate.py --from-dir /path/to/csvs

# Rebuild by downloading every year FIRST_YEAR..current from VPD (this is what CI runs)
python scripts/aggregate.py --download
```

There are no tests, linters, or package manifests. `aggregate.py` is pure stdlib
(Python 3.12, no dependencies). The frontend has no toolchain.

## The central design decision: the count-cube

The dashboard **never loads raw incidents**. `scripts/aggregate.py` collapses
~1.4M incidents (2003–now) into `data/crime_cube.json`, a count-cube grouped by
`month × crime-type × neighbourhood`. This keeps the payload a few MB and makes
every filter a cheap client-side sum.

Cube shape (note the index encoding — this is the contract between the two files):

```json
{
  "meta": {
    "neighbourhoods": ["Arbutus Ridge", ...],   // sorted; index = position
    "types": ["Break and Enter ...", ...],       // sorted; index = position
    "months": ["2003-01", ...],                  // sorted "YYYY-MM" strings
    "generated_utc": "...", "years_loaded": [...],
    "total_incidents": N, "dropped_no_neighbourhood": N
  },
  "data": { "YYYY-MM": { "<typeIdx>": [count_per_neighbourhood_idx, ...] } }
}
```

`typeIdx` and the array position both reference the **sorted** `meta.types` /
`meta.neighbourhoods` arrays. The frontend (`recompute()`) sums the per-hood
arrays across the selected month range and selected type(s). Months compare as
plain strings because `"YYYY-MM"` sorts lexically.

**Tradeoff:** counts only, no X/Y coordinates — so there is no point map. A
GeoDASH-style individual-incident view would need raw rows and a separate, much
heavier data path.

## Data source (confirmed)

- **Crime data:** VPD GeoDASH — the full 2003–now history is one public zip
  (`.../crimedata_download/AllNeighbourhoods_AllYears/...zip`). The portal's
  disclaimer checkbox is client-side only; the zip is a plain GET (no token).
  `aggregate.py --download` fetches and unzips it. If VPD restructures the
  portal, re-read `submitLink()` in the page source to rebuild the URL.
- **Polygons:** `data/local-areas.geojson` is committed — Vancouver "Local Area
  Boundary" from `opendata.vancouver.ca` (v2.1 geojson export). It has **22**
  areas; the crime data has **24**, so **Musqueam** and **Stanley Park** have no
  polygon and never colour (they still appear in sidebar counts).
- `aggregate.py` is stdlib-only and runs on **Python 3.9+** (a
  `from __future__ import annotations` defers the `X | None` typing); CI uses 3.12.

## Name reconciliation (frontend)

VPD neighbourhood names and the geojson's polygon labels don't always match.
`index.html` auto-detects the geojson name field (`GEO_NAME_KEYS`) and maps
labels via the `NAME_FIX` dict. Any polygon whose (fixed) name isn't in the cube
shows up in an **orange warning bar** — resolve by adding it to `NAME_FIX` and
reloading. Watch for "Musqueam" and "Stanley Park" (often missing/renamed) and
note "Downtown" ↔ "Central Business District".

## CI

`.github/workflows/refresh-data.yml` runs Mondays 16:00 UTC: `aggregate.py
--download`, then commits `data/crime_cube.json` only if it changed. Manually
triggerable via Actions → "Refresh crime data" → Run workflow. Needs
`contents: write` (already set).

## Conventions / gotchas

- All API calls and aggregation logic live in `scripts/aggregate.py`; the
  frontend only consumes the finished JSON.
- `aggregate.py` is intentionally fault-tolerant on download: a failed/HTML/404
  year is skipped, not fatal, so partial-year backfills still produce a cube.
- Rows with no neighbourhood (`null`/blank) are dropped — they can't be placed
  on a choropleth — and counted in `meta.dropped_no_neighbourhood`.
```