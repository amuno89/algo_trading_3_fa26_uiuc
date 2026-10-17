# Research data

This directory contains the reproducible data pipeline for the pairs-trading paper in the repository.

## Important scope note

The paper uses CRSP and Compustat data. `yfinance` is useful for an open-data approximation, but it does **not** provide:

- a survivorship-bias-free CRSP universe from 1980–2020;
- historical delisted securities and CRSP delisting returns;
- point-in-time Compustat accounting data;
- the paper's exact 78 Green et al. firm characteristics;
- historical exchange/share codes for filtering NYSE, AMEX, and Nasdaq.

The scripts below therefore produce a clearly labeled `yfinance` approximation. Results should not be described as an exact replication unless the CRSP/Compustat inputs are substituted.

## Layout

```text
data/
  raw/yfinance/       downloaded daily OHLCV, dividends, and splits
  raw/yfinance_fundamentals/  statements, shares, metadata, and actions
  raw/benchmarks/      S&P 500/index proxies
  processed/          monthly panel and 48 momentum features
  factors/            Fama–French and q-factor files, when downloaded
  universe/           ticker input files
scripts/
  download_yfinance.py
  download_yfinance_fundamentals.py
  download_benchmarks.py
  build_monthly_features.py
  download_factor_data.py
```

## Quick start

```bash
python -m pip install -r requirements.txt
cp data/universe/tickers.example.txt data/universe/tickers.txt
python scripts/download_yfinance.py \
  --tickers-file data/universe/tickers.txt \
  --start 1979-12-01 --end 2021-01-01
python scripts/build_monthly_features.py
python scripts/download_yfinance_fundamentals.py \
  --tickers-file data/universe/tickers.txt \
  --start 1979-12-01 --end 2021-01-01
python scripts/download_benchmarks.py
```

The downloader writes one file per ticker, which makes retries and partial downloads safe. Files include adjusted and unadjusted prices, volume, dividends, and split information. The feature builder creates monthly prices/returns and `mom_1` through `mom_48`; `mom_1` is the prior month's return and `mom_i` is the compounded return over months `t-i` through `t-2`, matching the paper's timing convention.

The fundamentals downloader stores Yahoo Finance annual income statements, balance sheets, cash flows, shares, dividends, corporate actions, and current metadata. Yahoo's fundamentals are not historical point-in-time observations, so they must not be used to claim a bias-free replication of the paper.

For factor regressions, run:

```bash
python scripts/download_factor_data.py
```

Factor files are downloaded from the official Kenneth French Data Library and the Global-Q website when their URLs are reachable. They are not sourced from `yfinance`.
