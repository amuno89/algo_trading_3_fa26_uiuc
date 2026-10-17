#!/usr/bin/env python3
"""Build the monthly return panel and paper-style 48 momentum features."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def build_one(path: Path) -> pd.DataFrame:
    daily = pd.read_parquet(path)
    daily["Date"] = pd.to_datetime(daily["Date"], utc=True).dt.tz_localize(None)
    daily = daily.sort_values("Date").set_index("Date")
    # Adjusted close incorporates splits/dividends and is the appropriate price
    # series for total-return features when CRSP is unavailable.
    monthly = daily["Adj Close"].resample("ME").last().rename("adj_close").to_frame()
    monthly["return"] = monthly["adj_close"].pct_change()
    monthly["ticker"] = daily["ticker"].iloc[0]
    for i in range(1, 49):
        if i == 1:
            monthly[f"mom_{i}"] = monthly["return"].shift(1)
        else:
            # At formation month t, use returns t-i ... t-2 only.
            monthly[f"mom_{i}"] = (1 + monthly["return"].shift(2)).rolling(i - 1).apply(
                lambda values: values.prod(), raw=True
            ) - 1
    return monthly.reset_index()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, default=Path("data/raw/yfinance"))
    parser.add_argument("--output", type=Path, default=Path("data/processed/monthly_features.parquet"))
    args = parser.parse_args()
    files = sorted(path for path in args.input_dir.glob("*.parquet") if path.name != "monthly_features.parquet")
    if not files:
        parser.error(f"no parquet files found in {args.input_dir}")
    output = pd.concat((build_one(path) for path in files), ignore_index=True)
    output = output.sort_values(["Date", "ticker"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(args.output, index=False)
    print(f"Wrote {len(output):,} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
