# Vancouver Crime Analysis

Static Leaflet choropleth of VPD crime data (2003–present), with a GitHub
Actions cron that re-downloads the VPD feed weekly and commits a fresh data
file. No server, no infra cost.

```
vancrime/
├── index.html                     # the dashboard (static, CDN deps)
├── data/
│   ├── crime_cube.json            # generated count-cube (committed, full 2003–now history)
│   └── local-areas.geojson        # neighbourhood polygons (City of Vancouver Open Data)
├── scripts/aggregate.py           # downloads + aggregates -> crime_cube.json
└── .github/workflows/refresh-data.yml   # weekly cron
```

## How it works

The dashboard never loads raw incidents. `aggregate.py` collapses ~916k
incidents (2003–now) into a **count-cube**: counts grouped by
`month × crime-type × neighbourhood`. The whole history is only ~0.18 MB of
JSON, so the page loads instantly and all date-range / type / neighbourhood
filtering is a cheap client-side sum. (Tradeoff: no point-map. The
individual-incident view needs raw X/Y rows — a separate, much heavier data
path the choropleth doesn't need.)

## Where the data comes from

**Vancouver Police Department GeoDASH open data** — <https://geodash.vpd.ca/opendata/>.

The portal looks form-gated (you tick a disclaimer checkbox before the download
button activates), but that gate is purely client-side. The page's
`submitLink()` just builds a static URL and `window.open()`s it — the zip itself
is a plain public GET, no login, cookie, or token. The full history is one file:

```
https://geodash.vpd.ca/opendata/crimedata_download/AllNeighbourhoods_AllYears/crimedata_csv_AllNeighbourhoods_AllYears.zip
```

`aggregate.py` downloads that zip, extracts the CSV
(`TYPE,YEAR,MONTH,DAY,HOUR,MINUTE,HUNDRED_BLOCK,NEIGHBOURHOOD,X,Y`), and builds
the cube. Each row carries its own year/month, so the single multi-year file
aggregates correctly.

> If VPD ever restructures the portal and `--download` fails, re-derive the URL:
> open <https://geodash.vpd.ca/opendata/>, View Source, and read the
> `submitLink()` function — it shows exactly how the download URL is assembled.

## Build the cube

Requires **Python 3.9+** (stdlib only — no dependencies).

```bash
# fetch the full history from VPD and rebuild the cube (this is what CI runs)
python scripts/aggregate.py --download

# or build from files already on disk (.csv or .zip)
python scripts/aggregate.py --from-dir /path/to/folder
```

## Neighbourhood polygons

The choropleth uses `data/local-areas.geojson` — Vancouver's **"Local Area
Boundary"** dataset, fetched from the City of Vancouver Open Data portal:

```bash
curl -sL "https://opendata.vancouver.ca/api/explore/v2.1/catalog/datasets/local-area-boundary/exports/geojson" \
  -o data/local-areas.geojson
```

The frontend auto-detects the name field and reconciles label differences via
`NAME_FIX` in `index.html` (e.g. the boundary file's *Downtown* → the data's
*Central Business District*). If a polygon doesn't match a cube neighbourhood,
an orange bar lists it — add it to `NAME_FIX` and reload.

**Known gap:** this boundary file has 22 areas; the crime data has 24. *Musqueam*
and *Stanley Park* have no polygon in the city file, so they never colour on the
map (they still appear in the sidebar counts). A boundary file that includes them
would close the gap.

## Run it

```bash
python -m http.server 8000   # then open http://localhost:8000
```

## Deploy (free, autonomous)

1. Push to a GitHub repo.
2. Settings → Pages → deploy from `main` / root. (Or import to Vercel.)
3. The cron in `refresh-data.yml` runs every Monday, rebuilds the cube, and
   commits only if the data changed. Trigger it manually anytime via
   Actions → "Refresh crime data" → Run workflow.

   Note: the workflow refreshes `crime_cube.json` only. `local-areas.geojson`
   is a stable boundary file committed once, not part of the weekly refresh.
