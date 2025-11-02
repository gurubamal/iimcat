#!/usr/bin/env python3
"""
Enhanced India-focused finance news and filings collector.

This script wraps the existing fetch_full_articles.py collector without modifying it.
It adds:
 - Exchange/regulator lanes (NSE/BSE/SEBI) via RSS/HTML where possible.
 - Wider, allowlisted publisher sources for India finance desks.
 - Optional NewsAPI lane restricted by domains (allowlist only).
 - Domain finance hints for exchanges and common IR patterns.

Usage examples:
  # Broader, India-focused harvest for last 48h from trusted domains
  python enhanced_india_finance_collector.py \
    --tickers-file sec_tickers.txt \
    --hours-back 48 \
    --max-articles 3 \
    --sources reuters.com livemint.com economictimes.indiatimes.com business-standard.com \
             moneycontrol.com thehindubusinessline.com financialexpress.com cnbctv18.com zeebiz.com

  # Include exchange/regulator lanes (default on) and allow additional RSS endpoints
  python enhanced_india_finance_collector.py \
    --tickers RELIANCE TCS \
    --extra-rss https://www.bqprime.com/feed https://www.businesstoday.in/rssfeeds/?id=0

  # Optional NewsAPI lane restricted to allowlist domains
  NEWSAPI_KEY=... python enhanced_india_finance_collector.py \
    --tickers HDFCBANK \
    --newsapi --sources reuters.com livemint.com moneycontrol.com

Notes:
 - This script NEVER edits existing modules; it only imports and extends at runtime.
 - All network access, retries, and extraction re-use the base collector's helpers.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Tuple, Iterable

import json

# Import the existing collector as base (same directory)
import fetch_full_articles as base
from pathlib import Path

# Centralize default output locations
try:
    from orchestrator.config import AGGREGATES_DIR as _AGGREGATES_DIR, NEWS_RUNS_DIR as _NEWS_RUNS_DIR
except Exception:
    _BASE = Path(__file__).resolve().parent
    _AGGREGATES_DIR = str(_BASE / 'outputs' / 'aggregates')
    _NEWS_RUNS_DIR = str(_BASE / 'outputs' / 'news_runs')
    try:
        os.makedirs(_AGGREGATES_DIR, exist_ok=True)
        os.makedirs(_NEWS_RUNS_DIR, exist_ok=True)
    except Exception:
        pass
from bs4 import BeautifulSoup  # already a dependency of base


# --------- Constants: default allowlist and domain hints extensions ---------

DEFAULT_ALLOWLIST = [
    # Wires / international
    'reuters.com',
    # India finance desks
    'livemint.com',
    'economictimes.indiatimes.com',
    'business-standard.com',
    'moneycontrol.com',
    'thehindubusinessline.com',
    'financialexpress.com',
    'cnbctv18.com',
    'zeebiz.com',
    # Regulatory sources
    'sebi.gov.in',
    'nseindia.com',
    'bseindia.com',
]

# Extend base DOMAIN_FINANCE_HINTS without modifying its source
_DOMAIN_HINT_UPDATES = {
    'nseindia.com': [
        '/companies-listing', '/corporate-filings', '/companies', '/corporate', '/announcements', '/listing'
    ],
    'bseindia.com': ['/corporates/'],
    'sebi.gov.in': ['/press', '/media', '/circulars', '/orders', '/adjudication', '/reports', '/notices'],
    # Example IR newsroom path (add more via --ir-domains)
    'tatamotors.com': ['/newsroom', '/press-releases'],
}


# --------- Helpers: RSS parsing and safe HTTP via base ---------

def _http_get(url: str, timeout: float = 12.0):
    return base.http_get(url, timeout=timeout)


def _parse_rss_items(feed_url: str) -> list[tuple[str, str, str, dt.datetime | None]]:
    """Parse a standard RSS/Atom feed to (title, link, source, pubdate).
    Fail-safe: returns [] on any error.
    """
    try:
        r = _http_get(feed_url, timeout=15)
        if r is None or r.status_code >= 400 or not r.content:
            return []
        root = ET.fromstring(r.content)
        channel = root.find('channel')
        out = []
        if channel is not None:
            for it in channel.findall('item'):
                title = (it.findtext('title') or '').strip()
                link = (it.findtext('link') or '').strip()
                pubdate = base.parse_pubdate(it.findtext('pubDate') or '')
                src_el = it.find('{*}source')
                source = (src_el.text or '').strip() if src_el is not None else urllib.parse.urlparse(link).netloc
                if title and link:
                    out.append((title, link, source, pubdate))
        else:
            # Atom minimal fallback
            for entry in root.findall('{*}entry'):
                title = (entry.findtext('{*}title') or '').strip()
                link_el = entry.find('{*}link')
                href = link_el.get('href') if link_el is not None else ''
                updated = entry.findtext('{*}updated') or ''
                pubdate = base.parse_pubdate(updated) if updated else None
                source = urllib.parse.urlparse(href).netloc
                if title and href:
                    out.append((title, href, source, pubdate))
        return out
    except Exception:
        return []


# --------- Lanes: Exchanges and Regulator (best-effort, fail-safe) ---------

def _filter_items_for_ticker(ticker: str, items: Iterable[tuple[str, str, str, dt.datetime | None]]):
    for title, link, src, pubdt in items:
        if not title:
            continue
        if base.title_matches_ticker(ticker, title):
            yield (title, link, src, pubdt)


def fetch_sebi_press_releases(ticker: str) -> list[tuple[str, str, str, dt.datetime | None]]:
    """Scrape SEBI press releases listing page for links.
    Endpoint (UI list): https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=6&smid=0&ssid=23
    This is a best-effort HTML parse and may miss JS-rendered content.
    """
    url = (
        'https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=6&smid=0&ssid=23'
    )
    try:
        resp = _http_get(url, timeout=15)
        if resp is None or resp.status_code >= 400:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        out: list[tuple[str, str, str, dt.datetime | None]] = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = (a.get_text() or '').strip()
            if not text or not href:
                continue
            if '/press' in href or '/media' in href or 'press' in text.lower():
                full = urllib.parse.urljoin(url, href)
                out.append((text, full, 'SEBI', None))
        return list(_filter_items_for_ticker(ticker, out))
    except Exception:
        return []


def fetch_bse_corporate_announcements(ticker: str) -> list[tuple[str, str, str, dt.datetime | None]]:
    """Best-effort scrape of BSE Corporate Announcements landing page.
    UI: https://www.bseindia.com/corporates/ann.html
    The page may use dynamic APIs; this function defensively parses anchors.
    """
    base_url = 'https://www.bseindia.com/corporates/ann.html'
    try:
        r = _http_get(base_url, timeout=15)
        if r is None or r.status_code >= 400:
            return []
        soup = BeautifulSoup(r.text, 'html.parser')
        items = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            txt = (a.get_text() or '').strip()
            if not href or not txt:
                continue
            if 'corporates' in href.lower() or 'ann' in href.lower() or 'notice' in href.lower():
                full = urllib.parse.urljoin(base_url, href)
                items.append((txt, full, 'BSE', None))
        return list(_filter_items_for_ticker(ticker, items))
    except Exception:
        return []


def fetch_nse_rss_candidates() -> list[str]:
    """Return a list of NSE RSS endpoints when known.
    This list is intentionally conservative; supply more via --extra-rss.
    """
    return [
        # If NSE exposes general RSS (categories may vary over time)
        'https://www.nseindia.com/rss-feed',
    ]


def fetch_nse_announcements(ticker: str) -> list[tuple[str, str, str, dt.datetime | None]]:
    out: list[tuple[str, str, str, dt.datetime | None]] = []
    for feed in fetch_nse_rss_candidates():
        out.extend(_parse_rss_items(feed))
    return list(_filter_items_for_ticker(ticker, out))


# --------- Optional NewsAPI lane (domains-restricted) ---------

def _newsapi_everything(ticker: str, domains: list[str], api_key: str, page_size: int = 50) -> list[tuple[str, str, str, dt.datetime | None]]:
    try:
        sess = base._get_session()
        q = ticker
        url = (
            'https://newsapi.org/v2/everything?'
            + urllib.parse.urlencode({
                'q': q,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': str(page_size),
                'domains': ','.join(domains),
            })
        )
        headers = {'X-Api-Key': api_key, **base.HEADERS}
        r = sess.get(url, headers=headers, timeout=15)
        if r.status_code >= 400:
            return []
        data = r.json()
        arts = data.get('articles', []) or []
        out = []
        for a in arts:
            title = (a.get('title') or '').strip()
            link = (a.get('url') or '').strip()
            src = ((a.get('source') or {}).get('name') or '').strip()
            pub = a.get('publishedAt') or ''
            pubdt = None
            try:
                pubdt = dt.datetime.strptime(pub.replace('Z', ''), '%Y-%m-%dT%H:%M:%S') if pub else None
            except Exception:
                pubdt = None
            if title and link:
                out.append((title, link, src, pubdt))
        return list(_filter_items_for_ticker(ticker, out))
    except Exception:
        return []


# --------- Main orchestration ---------

def _dedup_by_url(items: list[tuple[str, str, str, dt.datetime | None]]) -> list[tuple[str, str, str, dt.datetime | None]]:
    seen = set()
    out = []
    for t, link, s, d in items:
        key = link.strip()
        if key in seen:
            continue
        seen.add(key)
        out.append((t, link, s, d))
    return out


def main():
    ap = argparse.ArgumentParser(description='Enhanced India-focused finance news and filings collector (wrapper).')
    ap.add_argument('--tickers', nargs='*', help='Tickers to search (e.g., RELIANCE TCS)')
    ap.add_argument('--tickers-file', type=str, help='File with one ticker per line')
    ap.add_argument('--limit', type=int, default=0, help='Limit number of tickers (0=all)')
    ap.add_argument('--hours-back', type=int, default=48, help='Freshness window in hours (default: 48)')
    ap.add_argument('--max-articles', type=int, default=5, help='Max articles per ticker to save (default: 5)')
    ap.add_argument('--sources', nargs='*', default=DEFAULT_ALLOWLIST, help='Allowlisted news domains')
    ap.add_argument('--include-exchanges', action='store_true', default=True, help='Include NSE/BSE/SEBI lanes (default: on)')
    ap.add_argument('--no-exchanges', action='store_true', help='Disable exchange/regulator lanes')
    ap.add_argument('--extra-rss', nargs='*', default=[], help='Additional RSS feed URLs to pull (company IR, etc.)')
    ap.add_argument('--ir-domains', nargs='*', default=[], help='Additional IR domains to whitelist and hint as finance (paths will be inferred)')
    ap.add_argument('--newsapi', action='store_true', help='Enable optional NewsAPI /everything lane restricted to allowlist domains')
    ap.add_argument('--newsapi-key', type=str, default=os.environ.get('NEWSAPI_KEY', ''), help='NewsAPI key (or set NEWSAPI_KEY env var)')
    ap.add_argument('--output-file', type=str, default='', help='Aggregated output file path (timestamp added)')
    ap.add_argument('--no-per-ticker', action='store_true', help='Do not write per-ticker files')
    ap.add_argument('--per-ticker-dir', type=str, default='', help='Directory for per-ticker files (default: auto in CWD)')
    ap.add_argument('--all-news', action='store_true', help='Disable finance-path filtering for broader intake (useful for exchanges)')
    ap.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging with sample URLs and rejection reasons')
    ap.add_argument('--show-samples', type=int, default=3, help='Number of sample URLs to show in verbose mode (default: 3)')

    args = ap.parse_args()

    # Respect disable flag for exchange lanes
    include_exchanges = args.include_exchanges and not args.no_exchanges

    # Extend base domain finance hints in-memory (no file changes)
    for k, v in _DOMAIN_HINT_UPDATES.items():
        try:
            base.DOMAIN_FINANCE_HINTS.setdefault(k, [])
            for cue in v:
                if cue not in base.DOMAIN_FINANCE_HINTS[k]:
                    base.DOMAIN_FINANCE_HINTS[k].append(cue)
        except Exception:
            pass
    # Add any user-supplied IR domains with generic newsroom/press paths
    for dom in args.ir_domains:
        dom = dom.strip().lower()
        if not dom:
            continue
        base.DOMAIN_FINANCE_HINTS.setdefault(dom, [])
        for cue in ['/news', '/newsroom', '/press', '/press-releases']:
            if cue not in base.DOMAIN_FINANCE_HINTS[dom]:
                base.DOMAIN_FINANCE_HINTS[dom].append(cue)

    # Resolve tickers
    tickers: list[str] = []
    if args.tickers:
        tickers = [t.strip() for t in args.tickers if t.strip()]
    elif args.tickers_file:
        try:
            with open(args.tickers_file, 'r', encoding='utf-8') as fh:
                lines = [ln.strip() for ln in fh.readlines()]
                tickers = [ln for ln in lines if ln and not ln.startswith('#')]
        except Exception as e:
            print(f"Error reading tickers file: {e}")
            sys.exit(1)
    else:
        # Fallback to a small sample
        tickers = ['RELIANCE', 'TCS']
    if args.limit and args.limit > 0:
        tickers = tickers[: args.limit]

    # Setup output timestamp and header (reuse base formatting)
    now = dt.datetime.utcnow()
    run_stamp = now.strftime('%Y%m%d_%H%M%S')
    # Determine output dir and filename
    if args.output_file:
        provided_dir = os.path.dirname(args.output_file)
        base_name, ext = os.path.splitext(os.path.basename(args.output_file))
        if not ext:
            ext = '.txt'
        out_dir = provided_dir or _AGGREGATES_DIR
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            pass
        aggregate_path = os.path.join(out_dir, f"{base_name}_{run_stamp}{ext}")
    else:
        try:
            os.makedirs(_AGGREGATES_DIR, exist_ok=True)
        except Exception:
            pass
        aggregate_path = os.path.join(_AGGREGATES_DIR, f"aggregated_full_articles_{int(args.hours_back)}h_{run_stamp}.txt")

    try:
        with open(aggregate_path, 'w', encoding='utf-8') as agg:
            agg.write("Full Article Fetch - Aggregated Run\n")
            agg.write("=" * 100 + "\n")
            agg.write(f"Run UTC: {now.isoformat()}\n")
            agg.write(f"Hours back: {int(args.hours_back)}\n")
            agg.write(f"Sources: {', '.join(args.sources or [])}\n")
            agg.write(f"Tickers planned: {len(tickers)}\n")
            agg.write("=" * 100 + "\n\n")
    except Exception as e:
        print(f"Error creating aggregate file: {e}")
        aggregate_path = None

    mirror_dir = None
    if not args.no_per_ticker:
        if args.per_ticker_dir:
            if os.path.isabs(args.per_ticker_dir) or os.path.dirname(args.per_ticker_dir):
                mirror_dir = args.per_ticker_dir
            else:
                mirror_dir = os.path.join(_NEWS_RUNS_DIR, args.per_ticker_dir)
        else:
            mirror_dir = os.path.join(_NEWS_RUNS_DIR, f"full_articles_run_{run_stamp}")
        try:
            os.makedirs(mirror_dir, exist_ok=True)
        except Exception as e:
            print(f"[warn] Could not create per-ticker directory '{mirror_dir}': {e}")
            mirror_dir = None

    cutoff = now - dt.timedelta(hours=max(1, int(args.hours_back)))

    # Statistics tracking
    total_tickers = len(tickers)
    stats = {
        'processed': 0,
        'with_news': 0,
        'no_news': 0,
        'total_articles': 0,
        'filtered_old': 0,
        'filtered_non_financial': 0,
        'errors': 0
    }

    print(f"\n{'='*80}")
    print(f"🔍 ENHANCED NEWS COLLECTION STARTED")
    print(f"{'='*80}")
    print(f"📅 Time window: Last {int(args.hours_back)} hours (cutoff: {cutoff.strftime('%Y-%m-%d %H:%M:%S')} UTC)")
    print(f"🎯 Tickers to scan: {total_tickers}")
    print(f"📰 News sources: {len(args.sources)}")
    print(f"{'='*80}\n")

    # Iterate per ticker
    for idx, tk in enumerate(tickers, 1):
        gathered: list[tuple[str, str, str, dt.datetime | None]] = []
        stats['processed'] += 1
        
        # Progress indicator
        progress_pct = (idx / total_tickers) * 100
        print(f"[{idx}/{total_tickers} ({progress_pct:.1f}%)] Processing {tk}...", end='', flush=True)
        
        ticker_stats = {
            'base_fetched': 0,
            'base_filtered_old': 0,
            'base_filtered_non_fin': 0,
            'exchange_items': 0,
            'newsapi_items': 0,
            'extra_rss_items': 0,
            'rejected_urls_old': [],
            'rejected_urls_non_fin': []
        }

        # 1) Base collector: publisher feeds + Google News (breadth)
        try:
            items = base.fetch_rss_items(tk, args.sources, publishers_only=False)
            ticker_stats['base_fetched'] = len(items)
            
            for title, link, source, pubdt in items:
                if pubdt is None or pubdt < cutoff:
                    ticker_stats['base_filtered_old'] += 1
                    stats['filtered_old'] += 1
                    if args.verbose and len(ticker_stats['rejected_urls_old']) < args.show_samples:
                        age = "unknown"
                        if pubdt:
                            age_delta = now - pubdt
                            hours_ago = age_delta.total_seconds() / 3600
                            age = f"{hours_ago:.1f}h ago"
                        ticker_stats['rejected_urls_old'].append((title[:60], link, age))
                    continue
                # Finance-only filter unless user explicitly requests all-news
                if not args.all_news and not base.is_financial_url(link):
                    ticker_stats['base_filtered_non_fin'] += 1
                    stats['filtered_non_financial'] += 1
                    if args.verbose and len(ticker_stats['rejected_urls_non_fin']) < args.show_samples:
                        ticker_stats['rejected_urls_non_fin'].append((title[:60], link))
                    continue
                # If sources provided, ensure item link aligns after basic host check
                if args.sources:
                    host = urllib.parse.urlparse(link).netloc.lower()
                    if not any(dom.lower() in host for dom in args.sources):
                        # allow through; base will try to resolve later in save_articles
                        pass
                gathered.append((title, link, source, pubdt))
        except Exception as e:
            print(f" ❌ base collector error: {e}")
            stats['errors'] += 1

        # 2) Extra RSS endpoints (company IR, newsroom feeds)
        for feed in args.extra_rss or []:
            for item in _filter_items_for_ticker(tk, _parse_rss_items(feed)):
                title, link, src, pubdt = item
                if pubdt is not None and pubdt < cutoff:
                    stats['filtered_old'] += 1
                    continue
                gathered.append(item)
                ticker_stats['extra_rss_items'] += 1

        # 3) Exchanges/regulator lanes (optional)
        if include_exchanges:
            try:
                exchange_before = len(gathered)
                for item in fetch_nse_announcements(tk):
                    title, link, src, pubdt = item
                    if pubdt is not None and pubdt < cutoff:
                        stats['filtered_old'] += 1
                        continue
                    gathered.append(item)
                    ticker_stats['exchange_items'] += 1
            except Exception:
                pass
            try:
                for item in fetch_bse_corporate_announcements(tk):
                    title, link, src, pubdt = item
                    if pubdt is not None and pubdt < cutoff:
                        stats['filtered_old'] += 1
                        continue
                    gathered.append(item)
                    ticker_stats['exchange_items'] += 1
            except Exception:
                pass
            try:
                for item in fetch_sebi_press_releases(tk):
                    title, link, src, pubdt = item
                    if pubdt is not None and pubdt < cutoff:
                        stats['filtered_old'] += 1
                        continue
                    gathered.append(item)
                    ticker_stats['exchange_items'] += 1
            except Exception:
                pass

        # 4) Optional NewsAPI lane (domains restricted)
        if args.newsapi and args.newsapi_key:
            try:
                na_items = _newsapi_everything(tk, args.sources, args.newsapi_key)
                for title, link, src, pubdt in na_items:
                    if pubdt is not None and pubdt < cutoff:
                        stats['filtered_old'] += 1
                        continue
                    gathered.append((title, link, src or 'NewsAPI', pubdt))
                    ticker_stats['newsapi_items'] += 1
            except Exception as e:
                print(f" ⚠️ NewsAPI error: {e}")
                stats['errors'] += 1

        # De-dup and save using base.save_articles
        gathered = _dedup_by_url(gathered)
        
        # Enhanced logging with diagnostics
        if not gathered:
            stats['no_news'] += 1
            print(f" ⚫ NO NEWS")
            print(f"    └─ Fetched: {ticker_stats['base_fetched']} items")
            print(f"    └─ Filtered (old): {ticker_stats['base_filtered_old']}, (non-financial): {ticker_stats['base_filtered_non_fin']}")
            if ticker_stats['exchange_items'] > 0 or ticker_stats['newsapi_items'] > 0 or ticker_stats['extra_rss_items'] > 0:
                print(f"    └─ Exchange: {ticker_stats['exchange_items']}, NewsAPI: {ticker_stats['newsapi_items']}, Extra RSS: {ticker_stats['extra_rss_items']}")
            
            # Verbose mode: show sample rejected URLs
            if args.verbose:
                if ticker_stats['rejected_urls_old']:
                    print(f"    └─ Sample OLD articles rejected:")
                    for title, url, age in ticker_stats['rejected_urls_old']:
                        domain = urllib.parse.urlparse(url).netloc
                        print(f"       • [{age}] {title}... ({domain})")
                
                if ticker_stats['rejected_urls_non_fin']:
                    print(f"    └─ Sample NON-FINANCIAL URLs rejected:")
                    for title, url in ticker_stats['rejected_urls_non_fin']:
                        domain = urllib.parse.urlparse(url).netloc
                        path = urllib.parse.urlparse(url).path[:40]
                        print(f"       • {title}... ({domain}{path})")
            
            if aggregate_path:
                try:
                    with open(aggregate_path, 'a', encoding='utf-8') as agg:
                        agg.write(f"Full Article Fetch Test - {tk}\n")
                        agg.write("=" * 80 + "\n\n")
                        agg.write(f"(no fresh items in last {int(args.hours_back)}h)\n\n")
                except Exception:
                    pass
            continue

        # We have news!
        stats['with_news'] += 1
        stats['total_articles'] += len(gathered)
        
        print(f" ✅ FOUND {len(gathered)} articles")
        print(f"    ├─ Fetched: {ticker_stats['base_fetched']} items from base sources")
        if ticker_stats['base_filtered_old'] > 0:
            print(f"    ├─ Filtered out: {ticker_stats['base_filtered_old']} (too old), {ticker_stats['base_filtered_non_fin']} (non-financial)")
        if ticker_stats['exchange_items'] > 0:
            print(f"    ├─ Exchange announcements: {ticker_stats['exchange_items']}")
        if ticker_stats['newsapi_items'] > 0:
            print(f"    ├─ NewsAPI: {ticker_stats['newsapi_items']}")
        if ticker_stats['extra_rss_items'] > 0:
            print(f"    ├─ Extra RSS: {ticker_stats['extra_rss_items']}")
        
        # Show sample headlines
        if gathered:
            print(f"    └─ Latest headlines:")
            for i, (title, link, source, pubdt) in enumerate(gathered[:3], 1):
                age = "unknown"
                if pubdt:
                    age_delta = now - pubdt
                    hours_ago = age_delta.total_seconds() / 3600
                    if hours_ago < 1:
                        age = f"{int(age_delta.total_seconds()/60)}m ago"
                    elif hours_ago < 24:
                        age = f"{int(hours_ago)}h ago"
                    else:
                        age = f"{int(hours_ago/24)}d ago"
                title_preview = title[:70] + "..." if len(title) > 70 else title
                print(f"       {i}. [{age}] {title_preview}")

        try:
            outfile = base.save_articles(
                tk,
                gathered,
                max_articles=int(args.max_articles),
                allowed_sources=args.sources,
                output_file=aggregate_path,
                mirror_dir=mirror_dir,
                run_timestamp=run_stamp,
            )
            if aggregate_path:
                print(f"    └─ 💾 Saved to: {aggregate_path}")
            else:
                print(f"    └─ 💾 Saved to: {outfile}")
        except Exception as e:
            print(f"    └─ ❌ Save error: {e}")
            stats['errors'] += 1

    # Optional cleanup of old runs (reuse base)
    try:
        base.cleanup_old_files(aggregate_path, max_keep=2)
    except Exception:
        pass

    # Print comprehensive summary
    print(f"\n{'='*80}")
    print(f"📊 COLLECTION SUMMARY")
    print(f"{'='*80}")
    print(f"✅ Successfully processed: {stats['processed']}/{total_tickers} tickers")
    print(f"📰 Tickers with news: {stats['with_news']} ({(stats['with_news']/total_tickers*100):.1f}%)")
    print(f"⚫ Tickers with no news: {stats['no_news']} ({(stats['no_news']/total_tickers*100):.1f}%)")
    print(f"📄 Total articles saved: {stats['total_articles']}")
    
    if stats['filtered_old'] > 0 or stats['filtered_non_financial'] > 0:
        print(f"\n🔍 Filtering statistics:")
        print(f"   ├─ Filtered (too old): {stats['filtered_old']}")
        print(f"   └─ Filtered (non-financial): {stats['filtered_non_financial']}")
    
    if stats['errors'] > 0:
        print(f"\n⚠️  Errors encountered: {stats['errors']}")
    
    if stats['with_news'] > 0:
        hit_rate = (stats['with_news'] / total_tickers) * 100
        print(f"\n🎯 Hit Rate: {hit_rate:.2f}%")
        if hit_rate >= 2.0:
            print(f"   ✅ EXCELLENT - Above 2% target!")
        elif hit_rate >= 1.0:
            print(f"   ⚠️  GOOD - Above 1% baseline")
        else:
            print(f"   ⚠️  LOW - Below 1% baseline (adjust time window or sources)")
    
    if aggregate_path:
        print(f"\n📁 Output file: {aggregate_path}")
    if mirror_dir:
        print(f"📁 Per-ticker files: {mirror_dir}/")
    
    print(f"{'='*80}")
    print(f"⏱️  Scan completed at: {dt.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
