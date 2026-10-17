#!/usr/bin/env python3
"""Download factor files referenced by the paper (not Yahoo Finance data)."""

from __future__ import annotations

import argparse
from pathlib import Path

import requests


FACTOR_URLS = {
    "ff3_monthly.zip": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip",
    "ff5_monthly.zip": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_5_Factors_2x3_CSV.zip",
    "momentum_monthly.zip": "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Momentum_Factor_CSV.zip",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("data/factors"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for filename, url in FACTOR_URLS.items():
        destination = args.output_dir / filename
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        destination.write_bytes(response.content)
        print(f"Wrote {destination}")
    print("q-factor data is intentionally not guessed here; obtain the matching vintage from the Global-Q data source and place it in data/factors/.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
