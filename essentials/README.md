# Fetch Full Articles — Quickstart

This script fetches full‑text news articles for Indian equities (and any tickers you pass), filtering by recent publication time and favoring reputable finance publishers. It saves a single aggregated file and optional per‑ticker files for review and downstream screening.

## Requirements
- Python 3.11
- Install dependencies (readability is required; others are optional but improve extraction):
  - requests, beautifulsoup4, readability-lxml
  - Optional: yfinance, newspaper3k, trafilatura

Example install:
```
pip install requests beautifulsoup4 readability-lxml yfinance newspaper3k trafilatura
```

## Basic Usage
Run from repo root (recommended):
```
python intelligent_scripts/fetch_full_articles.py --tickers-file intelligent_scripts/valid_nse_tickers.txt --limit 0
```
Or from this folder:
```
python fetch_full_articles.py --tickers-file ../intelligent_scripts/valid_nse_tickers.txt --limit 0
```

## Common Flags
- --tickers: space‑separated tickers (e.g., `--tickers RELIANCE TCS`)
- --tickers-file: path to a text file with one ticker per line
- --limit: limit number of tickers from file (0 = all)
- --hours-back: 8|16|24|48 — only include recent news (default 24)
- --sources: preferred domains to prioritize (defaults included)
- --publishers-only: only first‑party publisher RSS (skip Google News)
- --max-articles: max full articles saved per ticker (default 2)
- --all-news: include non‑finance pages (finance‑only filter is default)
- --output-file: aggregated output path (timestamp auto‑appended unless `--no-timestamp-output`)
- --per-ticker-dir: directory for per‑ticker files; use `--no-per-ticker` to disable
- --concurrency: global worker threads (default 8)
- --per-host / --per-host-interval: polite rate‑limit controls per domain
- --no-cleanup / --keep-files: keep N recent aggregated/per‑ticker runs (default 2)

## Outputs
- Aggregated: `aggregated_full_articles_<hours>h_<timestamp>.txt` in current directory
- Per‑ticker: `full_articles_run_<timestamp>/TICKER_<timestamp>.txt` (unless `--no-per-ticker`)

## Examples
- Explicit tickers, 2 articles each:
```
python intelligent_scripts/fetch_full_articles.py --tickers RELIANCE TCS --max-articles 2
```
- Publishers‑only from specific sources:
```
python intelligent_scripts/fetch_full_articles.py --tickers HDFCBANK --publishers-only --sources reuters.com livemint.com
```
- From file, last 16 hours, 1 article each, narrowed sources:
```
python intelligent_scripts/fetch_full_articles.py \
  --tickers-file intelligent_scripts/valid_nse_tickers.txt \
  --limit 10 --max-articles 1 --hours-back 16 \
  --publishers-only --sources reuters.com economictimes.indiatimes.com business-standard.com moneycontrol.com
```

## Tips & Troubleshooting
- Rate limits: Script spaces requests per‑host and retries. Financial metrics (Net Profit/Net Worth) may be skipped when rate‑limited; the aggregated file will note this.
- Dependencies: Ensure `readability-lxml` and `beautifulsoup4` are installed; optional `trafilatura`/`newspaper3k` improve extraction on some sites.
- Network: Corporate proxies or blocked sites can reduce coverage; try `--publishers-only` with local publishers.
- Paths: When running outside repo root, adjust paths to `valid_nse_tickers.txt` accordingly.

## Next Steps
After fetching, use:
- Screening: `python intelligent_scripts/screen_full_articles.py --top 20 [--with-tech]`
- Blend with technicals: `python intelligent_scripts/news_technical_screen.py --top 20 --export out.csv`
