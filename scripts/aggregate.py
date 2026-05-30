#!/usr/bin/env python3
"""
Build a compact crime count-cube for the Vancouver Crime dashboard.

Two modes:
  1. DOWNLOAD (CI):  python aggregate.py --download
       Fetches the full-history zip from VPD GeoDASH and builds the cube.
  2. LOCAL (dev):    python aggregate.py --from-dir /path/with/files
       Reads any crimedata_csv_*.csv or crimedata_csv_*.zip already on disk.

Output: data/crime_cube.json
  {
    "meta": { "neighbourhoods": [...], "types": [...], "months": ["2003-01", ...],
              "generated_utc": "...", "years_loaded": [...], "total_incidents": N },
    "data": { "YYYY-MM": { "<typeIdx>": [c0, c1, ... per neighbourhood idx] } }
  }

The cube is COUNTS ONLY (no raw incident rows, no X/Y). That collapses ~1.4M
incidents across 23 years into a few MB. A choropleth only needs counts per
(neighbourhood x month x type); arbitrary date-range + type filtering is then a
cheap client-side sum. If you ever want the GeoDASH-style point map, that needs
raw X/Y rows and is a separate, much heavier data path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import io
import json
import os
import sys
import urllib.request
import zipfile
import csv
from collections import defaultdict

# ---------------------------------------------------------------------------
# VPD GeoDASH publishes the entire history (every year, every neighbourhood) as
# one public zip. No login or token: the portal's "accept disclaimer" checkbox
# only enables the download button client-side — the file itself is a plain GET.
# (Confirmed against https://geodash.vpd.ca/opendata/ — the page's submitLink()
# builds exactly this URL.)
DOWNLOAD_URL = ("https://geodash.vpd.ca/opendata/crimedata_download/"
                "AllNeighbourhoods_AllYears/crimedata_csv_AllNeighbourhoods_AllYears.zip")
# ---------------------------------------------------------------------------

EXPECTED_HEADER = ["TYPE", "YEAR", "MONTH", "DAY", "HOUR", "MINUTE",
                   "HUNDRED_BLOCK", "NEIGHBOURHOOD", "X", "Y"]

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "..", "data", "crime_cube.json")


def csv_from_zip_bytes(raw: bytes) -> str:
    """Extract the single crime CSV from a VPD zip and return its text."""
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise ValueError("zip contained no .csv member")
        with zf.open(names[0]) as f:
            return f.read().decode("utf-8-sig", errors="replace")


def fetch_all() -> str:
    """Download the full-history VPD zip and return its CSV text."""
    req = urllib.request.Request(DOWNLOAD_URL,
                                 headers={"User-Agent": "vancrime-bot/1.0"})
    print(f"Downloading full history:\n  {DOWNLOAD_URL}", file=sys.stderr)
    with urllib.request.urlopen(req, timeout=180) as resp:
        raw = resp.read()
    print(f"  got {len(raw):,} bytes (zip)", file=sys.stderr)
    return csv_from_zip_bytes(raw)


def iter_rows(csv_text: str):
    reader = csv.reader(io.StringIO(csv_text))
    header = next(reader, None)
    if header is None:
        return
    if [h.strip().upper() for h in header] != EXPECTED_HEADER:
        print(f"  WARNING: unexpected header: {header}", file=sys.stderr)
    for row in reader:
        if len(row) < 8:
            continue
        yield row


def build_cube(sources: dict[str, str]) -> dict:
    """sources: {label: csv_text}. Returns the cube dict.

    Each row carries its own YEAR/MONTH, so a single multi-year CSV aggregates
    correctly regardless of how many source files there are.
    """
    neigh_set, type_set, month_set = set(), set(), set()
    # counts[(month, type, neigh)] = n
    counts: dict[tuple[str, str, str], int] = defaultdict(int)
    total = 0
    dropped_no_neigh = 0

    for label, text in sorted(sources.items()):
        n_before = total
        for row in iter_rows(text):
            ctype = row[0].strip()
            yr = row[1].strip()
            mo = row[2].strip()
            neigh = row[7].strip()
            if not ctype or not yr or not mo:
                continue
            if not neigh or neigh.lower() == "null":
                dropped_no_neigh += 1
                continue
            try:
                month_key = f"{int(yr):04d}-{int(mo):02d}"
            except ValueError:
                continue
            neigh_set.add(neigh)
            type_set.add(ctype)
            month_set.add(month_key)
            counts[(month_key, ctype, neigh)] += 1
            total += 1
        print(f"  [{label}] {total - n_before:>8,} incidents", file=sys.stderr)

    # years actually present in the data (correct even for one AllYears file)
    years_loaded = sorted({int(mk[:4]) for mk in month_set})

    neighbourhoods = sorted(neigh_set)
    types = sorted(type_set)
    months = sorted(month_set)
    n_idx = {n: i for i, n in enumerate(neighbourhoods)}
    t_idx = {t: i for i, t in enumerate(types)}

    data: dict[str, dict[str, list[int]]] = {}
    for (month_key, ctype, neigh), c in counts.items():
        ti = str(t_idx[ctype])
        bucket = data.setdefault(month_key, {})
        arr = bucket.get(ti)
        if arr is None:
            arr = [0] * len(neighbourhoods)
            bucket[ti] = arr
        arr[n_idx[neigh]] += c

    if dropped_no_neigh:
        print(f"  note: dropped {dropped_no_neigh:,} rows with no neighbourhood "
              f"(can't place on a choropleth)", file=sys.stderr)

    return {
        "meta": {
            "neighbourhoods": neighbourhoods,
            "types": types,
            "months": months,
            "generated_utc": dt.datetime.now(dt.timezone.utc)
                               .isoformat(timespec="seconds"),
            "years_loaded": years_loaded,
            "total_incidents": total,
            "dropped_no_neighbourhood": dropped_no_neigh,
        },
        "data": data,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true",
                    help="Fetch the full-history zip from VPD GeoDASH.")
    ap.add_argument("--from-dir",
                    help="Read crimedata_csv_*.csv / *.zip files already on disk.")
    ap.add_argument("--out", default=OUT_PATH)
    args = ap.parse_args()

    sources: dict[str, str] = {}

    if args.from_dir:
        paths = sorted(glob.glob(os.path.join(args.from_dir, "crimedata_csv_*.csv")) +
                       glob.glob(os.path.join(args.from_dir, "crimedata_csv_*.zip")))
        if not paths:
            sys.exit(f"No crimedata_csv_*.csv or *.zip files in {args.from_dir}")
        for p in paths:
            if p.lower().endswith(".zip"):
                with open(p, "rb") as f:
                    text = csv_from_zip_bytes(f.read())
            else:
                with open(p, "r", encoding="utf-8-sig", errors="replace") as f:
                    text = f.read()
            sources[os.path.basename(p)] = text
            print(f"  loaded {os.path.basename(p)}", file=sys.stderr)
    elif args.download:
        try:
            sources["AllNeighbourhoods_AllYears"] = fetch_all()
        except Exception as e:  # noqa: BLE001
            sys.exit(f"Download failed: {e}\n"
                     "VPD may have changed the portal — re-check the URL built by "
                     "submitLink() at https://geodash.vpd.ca/opendata/")
    else:
        ap.error("Pass --download (CI) or --from-dir PATH (local).")

    cube = build_cube(sources)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(cube, f, separators=(",", ":"))

    size_mb = os.path.getsize(args.out) / 1e6
    m = cube["meta"]
    print(f"\nWrote {args.out}  ({size_mb:.2f} MB)", file=sys.stderr)
    print(f"  {m['total_incidents']:,} incidents | "
          f"{len(m['neighbourhoods'])} neighbourhoods | "
          f"{len(m['types'])} types | "
          f"{len(m['months'])} months "
          f"({m['months'][0]}..{m['months'][-1]})", file=sys.stderr)


if __name__ == "__main__":
    main()
