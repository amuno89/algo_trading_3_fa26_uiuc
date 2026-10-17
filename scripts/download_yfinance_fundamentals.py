#!/usr/bin/env python3
"""Download Yahoo Finance fundamentals and corporate-action history.

These are point-in-time-uncontrolled observations. They are useful proxies for
research prototyping, but should not be treated as historical Compustat data.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf


def read_tickers(path: Path) -> list[str]:
    values = []
    for line in path.read_text().splitlines():
        ticker = line.split("#", 1)[0].strip().upper()
        if ticker:
            values.append(ticker)
    return list(dict.fromkeys(values))


def write_frame(frame: pd.DataFrame, path: Path) -> int:
    if frame is None or frame.empty:
        return 0
    frame = frame.copy()
    if isinstance(frame.index, pd.MultiIndex):
        frame = frame.reset_index()
    else:
        frame = frame.reset_index(names="period")
    frame.to_parquet(path, index=False)
    return len(frame)


def download_one(ticker: str, args: argparse.Namespace, root: Path) -> dict:
    target = root / ticker.replace("/", "-")
    target.mkdir(parents=True, exist_ok=True)
    item = {"ticker": ticker, "status": "downloaded", "files": {}}
    try:
        security = yf.Ticker(ticker)
        statements = {
            "income_statement": security.get_income_stmt(freq="yearly"),
            "balance_sheet": security.get_balance_sheet(freq="yearly"),
            "cash_flow": security.get_cash_flow(freq="yearly"),
        }
        for name, frame in statements.items():
            item["files"][name] = write_frame(frame, target / f"{name}.parquet")

        shares = security.get_shares_full(start=args.start, end=args.end)
        if shares is not None and not shares.empty:
            shares.rename("shares").rename_axis("Date").to_frame().to_parquet(
                target / "shares.parquet", index=True
            )
            item["files"]["shares"] = len(shares)
        else:
            item["files"]["shares"] = 0

        for name, frame in {
            "dividends": security.dividends,
            "actions": security.actions,
        }.items():
            if frame is not None and not frame.empty:
                if isinstance(frame, pd.Series):
                    frame = frame.rename_axis("Date").rename(name).to_frame()
                frame.to_parquet(target / f"{name}.parquet", index=True)
                item["files"][name] = len(frame)
            else:
                item["files"][name] = 0

        info = {}
        try:
            info = security.get_info()
        except Exception as exc:
            item["info_error"] = repr(exc)
        (target / "info.json").write_text(json.dumps(info, indent=2, default=str) + "\n")
        time.sleep(args.pause)
    except Exception as exc:
        item["status"] = "error"
        item["error"] = repr(exc)
    return item


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers-file", type=Path, required=True)
    parser.add_argument("--start", default="1979-12-01")
    parser.add_argument("--end", default="2021-01-01")
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw/yfinance_fundamentals"))
    parser.add_argument("--pause", type=float, default=0.25)
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
        "warning": "Fundamentals are not point-in-time and are not CRSP/Compustat equivalents.",
        "results": results,
    }
    (args.output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    failed = [r for r in results if r["status"] == "error"]
    print(f"Processed {len(results) - len(failed)}/{len(results)} tickers")
    if failed:
        print("Failed: " + ", ".join(r["ticker"] for r in failed), file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
