#!/usr/bin/env python3
"""Download benchmark/index proxies used in the paper's comparisons."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import yfinance as yf


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="1979-12-01")
    parser.add_argument("--end", default="2021-01-01")
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/benchmarks"))
    parser.add_argument("--tickers", nargs="+", default=["^GSPC", "SPY"])
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for ticker in args.tickers:
        frame = yf.download(
            ticker, start=args.start, end=args.end, interval="1d", auto_adjust=False,
            actions=True, progress=False, threads=False,
        )
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = [column[0] for column in frame.columns]
        frame.reset_index().to_parquet(args.output_dir / f"{ticker.replace('/', '-')}.parquet", index=False)
        print(f"Wrote {ticker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
