"""Build three complete M-Lab months for Canadian city/ASN cohorts with >=100 tests."""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
import re
import shutil
import tempfile
from pathlib import Path
from urllib.request import urlopen

import pyarrow.parquet as parquet

MANIFEST = "https://storage.googleapis.com/mlab-sandbox-iqb-us-central1/manifest/v0/manifest.json"
OUTPUT = Path(__file__).resolve().parents[1] / "web/data"
PERCENTILES = [1, 5, 10, 25, 50, 75, 90, 95, 99]
MIN_COUNT = 100
FILE = re.compile(r"^cache/v1/(\d{6})01T000000Z/\d{8}T000000Z/(download|upload)s_by_country_city_asn/data.parquet$")


def get_parquet(entry, cache):
    expected = entry["sha256"]
    cached = cache / expected
    if not cached.exists():
        with urlopen(entry["url"], timeout=180) as response, cached.with_suffix(".tmp").open("wb") as out:
            shutil.copyfileobj(response, out)
        cached.with_suffix(".tmp").replace(cached)
    with cached.open("rb") as f:
        actual = hashlib.file_digest(f, "sha256").hexdigest()
    if actual != expected:
        raise ValueError(f'Unexpected file checksum for {entry["url"]}')
    return cached


def compact(path, direction):
    pct_cols = [f"{direction}_p{q}" for q in PERCENTILES]
    table = parquet.read_table(path, columns=["subdivision1_iso_code", "city", "asn", "as_name", "sample_count", *pct_cols],
                               filters=[("country_code", "=", "CA"), ("sample_count", ">=", MIN_COUNT)])
    rows = []
    seen = set()
    for row in table.to_pylist():
        key = (row["subdivision1_iso_code"], row["city"], row["asn"])
        if not all(key):
            continue
        if key in seen:
            raise ValueError(f"Duplicate city/network {key}")
        seen.add(key)
        values = [row[col] for col in pct_cols]
        if any(v is None or not math.isfinite(v) or v < 0 for v in values) or values != sorted(values):
            raise ValueError(f"Invalid speed boundaries for {key}")
        rows.append([*key, row["as_name"] or f'AS{key[-1]}', row["sample_count"], *values])
    if not rows:
        raise ValueError(f"No Canadian {direction} cohorts in {path}")
    return sorted(rows)


def write(path, obj):
    path.write_text(json.dumps(obj, separators=(",", ":"), ensure_ascii=False, allow_nan=False) + "\n")


def refresh(cache):
    with urlopen(MANIFEST, timeout=120) as r:
        entries = json.load(r)["files"]
    groups = {}
    for key, entry in entries.items():
        m = FILE.match(key)
        if m:
            groups.setdefault(m[1], {})[m[2]] = entry
    months = sorted((month for month, files in groups.items() if len(files) == 2), reverse=True)[:3]
    if len(months) != 3:
        raise ValueError("Expected at least three complete months in the manifest")
    cache.mkdir(exist_ok=True, parents=True)
    OUTPUT.mkdir(exist_ok=True, parents=True)
    with tempfile.TemporaryDirectory(dir=OUTPUT.parent) as temp:
        staged = Path(temp)
        summary = {"retrieved": dt.datetime.now(dt.timezone.utc).date().isoformat(), "percentiles": PERCENTILES,
                   "min_count": MIN_COUNT, "months": [], "cohorts": 0}
        for stamp in months:
            month = f"{stamp[:4]}-{stamp[4:]}"
            record = {"month": month, "sources": {}, "counts": {}}
            for direction in ("download", "upload"):
                entry = groups[stamp][direction]
                print(month, direction, flush=True)
                rows = compact(get_parquet(entry, cache), direction)
                write(staged / f"{month}-{direction}.json", rows)
                record["sources"][direction] = entry
                record["counts"][direction] = len(rows)
                summary["cohorts"] += len(rows)
            summary["months"].append(record)
        summary["start"] = summary["months"][-1]["month"]
        summary["end"] = summary["months"][0]["month"]
        write(staged / "status.json", summary)
        for new in staged.glob("*.json"):
            os.replace(new, OUTPUT / new.name)
        for old in OUTPUT.glob("????-??-*.json"):
            if old.name[:7] not in {m["month"] for m in summary["months"]}:
                old.unlink()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, help="Reusable directory for SHA-256 verified Parquet downloads")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as default:
        refresh(args.cache or Path(default))
