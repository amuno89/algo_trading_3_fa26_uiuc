#!/usr/bin/env python3
"""Download reproducible Yahoo Finance inputs for the paper approximation."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf


def read_tickers(path: Path) -> list[str]:
    tickers = []
    for line in path.read_text().splitlines():
        value = line.split("#", 1)[0].strip().upper()
        if value:
            tickers.append(value)
    return list(dict.fromkeys(tickers))


def download_one(ticker: str, args: argparse.Namespace, output_dir: Path) -> dict:
    destination = output_dir / f"{ticker.replace('/', '-')}.parquet"
    try:
        frame = yf.download(
            ticker,
            start=args.start,
            end=args.end,
            interval=args.interval,
            auto_adjust=False,
            actions=True,
            progress=False,
            group_by="column",
            threads=False,
        )
        if frame.empty:
            return {"ticker": ticker, "status": "empty", "rows": 0}
        if isinstance(frame.columns, pd.MultiIndex):
            frame.columns = [column[0] for column in frame.columns]
        frame = frame.reset_index()
        frame.insert(0, "ticker", ticker)
        frame.to_parquet(destination, index=False)
        return {"ticker": ticker, "status": "downloaded", "rows": len(frame), "file": str(destination)}
    except Exception as exc:  # keep the batch going and report failed symbols
        return {"ticker": ticker, "status": "error", "error": repr(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers-file", type=Path, required=True)
    parser.add_argument("--start", default="1979-12-01")
    parser.add_argument("--end", default="2021-01-01")
    parser.add_argument("--interval", default="1d", choices=["1d", "1wk", "1mo"])
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/yfinance"))
    args = parser.parse_args()

    if not args.tickers_file.exists():
        parser.error(f"ticker file does not exist: {args.tickers_file}")
    tickers = read_tickers(args.tickers_file)
    if not tickers:
        parser.error("ticker file contains no symbols")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    results = [download_one(ticker, args, args.output_dir) for ticker in tickers]
    manifest = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance via yfinance",
        "start": args.start,
        "end_exclusive": args.end,
        "interval": args.interval,
        "tickers_file": str(args.tickers_file),
        "results": results,
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    failed = [item for item in results if item["status"] == "error"]
    empty = [item for item in results if item["status"] == "empty"]
    print(f"Downloaded {len(results) - len(failed) - len(empty)}/{len(results)} tickers")
    if empty:
        print(f"Empty: {', '.join(item['ticker'] for item in empty)}", file=sys.stderr)
    if failed:
        print(f"Failed: {', '.join(item['ticker'] for item in failed)}", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
