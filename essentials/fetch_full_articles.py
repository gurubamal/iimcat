#!/usr/bin/env python3
"""
Fetch full news articles for given tickers (last 24h) and save to txt files.

Minimal, dependency-light test that:
- Queries Google News RSS per ticker
- Filters items published within 24 hours
- Follows redirects to resolve original article URL
- Extracts full text content using readability-lxml
- Saves results to timestamped .txt files (one per ticker)

Usage examples:
  # Explicit tickers
  python intelligent_scripts/fetch_full_articles.py --tickers RELIANCE TCS --max-articles 2
  python intelligent_scripts/fetch_full_articles.py --tickers HDFCBANK --sources reuters.com livemint.com

  # From file (one ticker per line), last 16 hours only
  python intelligent_scripts/fetch_full_articles.py --tickers-file intelligent_scripts/valid_nse_tickers.txt --limit 10 --max-articles 1 --hours-back 16 --publishers-only --sources reuters.com economictimes.indiatimes.com business-standard.com moneycontrol.com
"""

import argparse
import datetime as dt
import html
import sys
import time
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Tuple
import os
import json
import glob
import shutil
import signal
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from bs4 import BeautifulSoup
import re
import re
import threading
import random
import functools
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv

# ---------------------------------------------------------------
# Networking: pooled session, retries, throttling, and helpers
# ---------------------------------------------------------------

_SESSION_LOCK = threading.Lock()
_SESSION = None

# Per-host throttle: limit request rate and concurrency per domain
_HOST_LOCKS = {}
_HOST_LAST_TS = {}
_HOST_SEMAPHORES = {}

# Defaults (can be tuned via CLI)
_GLOBAL_MAX_WORKERS = 8
_PER_HOST_MAX_CONCURRENCY = 2
_PER_HOST_MIN_INTERVAL_SEC = 0.6  # polite spacing between requests per host


def _get_session() -> requests.Session:
    global _SESSION
    if _SESSION is not None:
        return _SESSION
    with _SESSION_LOCK:
        if _SESSION is not None:
            return _SESSION
        s = requests.Session()
        retries = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.6,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(["GET"]),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(pool_connections=64, pool_maxsize=64, max_retries=retries)
        s.mount("http://", adapter)
        s.mount("https://", adapter)
        _SESSION = s
        return _SESSION


def _get_host_gate(host: str):
    host = host or ""
    if host not in _HOST_LOCKS:
        _HOST_LOCKS[host] = threading.Lock()
        _HOST_LAST_TS[host] = 0.0
        _HOST_SEMAPHORES[host] = threading.Semaphore(_PER_HOST_MAX_CONCURRENCY)
    return _HOST_LOCKS[host], _HOST_SEMAPHORES[host]


def http_get(url: str, *, timeout: float = 12.0, allow_redirects: bool = True, headers: dict | None = None) -> requests.Response:
    """Centralized GET with session pooling, retries, backoff, and per-host throttling.

    Adds small jitter to spacing; politely limits concurrency per host; retries on 429/5xx via adapter.
    """
    sess = _get_session()
    h = headers or HEADERS
    parsed = urllib.parse.urlparse(url)
    host = (parsed.netloc or "").lower()
    lock, gate = _get_host_gate(host)

    # Rate spacing per host
    with lock:
        now = time.time()
        wait_for = _PER_HOST_MIN_INTERVAL_SEC - (now - _HOST_LAST_TS[host])
        if wait_for > 0:
            # add small jitter to avoid regular cadence
            time.sleep(wait_for + random.uniform(0.0, 0.25))
        _HOST_LAST_TS[host] = time.time()

    # Concurrency limit per host
    with gate:
        resp = sess.get(url, headers=h, timeout=timeout, allow_redirects=allow_redirects)
        # Friendly manual backoff on 429
        if resp is not None and resp.status_code == 429:
            for i in range(2):
                delay = (i + 1) * 1.5 + random.uniform(0.0, 0.5)
                time.sleep(delay)
                resp = sess.get(url, headers=h, timeout=timeout, allow_redirects=allow_redirects)
                if resp.status_code != 429:
                    break
        return resp
from readability import Document

# Prefer centralized output dirs if available
try:
    from orchestrator.config import AGGREGATES_DIR as _AGGREGATES_DIR, NEWS_RUNS_DIR as _NEWS_RUNS_DIR
except Exception:
    # Fallback to local outputs structure
    _BASE = Path(__file__).resolve().parent
    _AGGREGATES_DIR = str(_BASE / 'outputs' / 'aggregates')
    _NEWS_RUNS_DIR = str(_BASE / 'outputs' / 'news_runs')
    try:
        os.makedirs(_AGGREGATES_DIR, exist_ok=True)
        os.makedirs(_NEWS_RUNS_DIR, exist_ok=True)
    except Exception:
        pass

# Optional extractors (installed at runtime if available)
try:
    import trafilatura  # type: ignore
    HAS_TRAFILATURA = True
except Exception:
    HAS_TRAFILATURA = False

try:
    from newspaper import Article  # type: ignore
    HAS_NEWSPAPER = True
except Exception:
    HAS_NEWSPAPER = False


# Preferred news domains for direct URLs
DEFAULT_SOURCES = [
    # Core international/business
    'reuters.com', 'bloomberg.com', 'bqprime.com',
    # India finance publishers
    'economictimes.indiatimes.com', 'livemint.com', 'moneycontrol.com',
    'business-standard.com', 'thehindubusinessline.com', 'financialexpress.com',
    'cnbctv18.com', 'businesstoday.in', 'zeebiz.com',
]

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/123.0.0.0 Safari/537.36'
    ),
    'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
}


FINANCE_PATH_CUES = [
    'business', 'market', 'markets', 'companies', 'company', 'finance', 'financial', 'economy', 'economic', 'industry'
]

DOMAIN_FINANCE_HINTS = {
    'reuters.com': ['/business/', '/markets/'],
    'livemint.com': ['/market', '/companies', '/money/', '/Money/'],
    'economictimes.indiatimes.com': ['/markets', '/industry', '/news/'],
    'moneycontrol.com': ['/news', '/markets'],
    'business-standard.com': ['/markets', '/companies'],
    'thehindubusinessline.com': ['/portfolio/', '/markets/'],
    'financialexpress.com': ['/market/', '/industry/'],
    'cnbctv18.com': ['/market/', '/economy/'],
    'zeebiz.com': ['/markets/', '/companies/'],
}

# Known financial domains that should always be considered financial
TRUSTED_FINANCE_DOMAINS = {
    'livemint.com', 'economictimes.indiatimes.com', 'moneycontrol.com',
    'business-standard.com', 'thehindubusinessline.com', 'financialexpress.com',
    'cnbctv18.com', 'zeebiz.com', 'reuters.com', 'mint.com', 'mint',
    'et manufacturing', 'et retail', 'eteducation.com'
}

_RESOLVE_CACHE: dict[str, str] = {}
_CONTENT_CACHE: dict[str, str] = {}
_MARKET_CAP_CACHE: dict[str, tuple[int | None, str | None]] = {}
_MCAP_REQUEST_LOG: list[float] = []
_NET_PROFIT_CACHE: dict[str, tuple[int | None, str | None]] = {}
_NET_PROFIT_REQ_LOG: list[float] = []
_NET_WORTH_CACHE: dict[str, tuple[int | None, str | None]] = {}
_NET_WORTH_REQ_LOG: list[float] = []

def is_financial_url(url: str) -> bool:
    try:
        u = urllib.parse.urlparse(url)
        host = (u.netloc or '').lower()
        path = (u.path or '').lower()
        
        # First check if it's a trusted financial domain - if so, be more lenient
        for trusted_domain in TRUSTED_FINANCE_DOMAINS:
            if trusted_domain in host:
                return True
                
        # Domain-specific strong cues for other domains
        for dom, cues in DOMAIN_FINANCE_HINTS.items():
            if dom in host:
                return any(c in path for c in cues)
                
        # Generic path cues for unknown domains
        return any(c in path for c in FINANCE_PATH_CUES)
    except Exception:
        return False

def build_gnews_rss_url(query: str, sources: List[str]) -> str:
    # Restrict to preferred sources via ORed site: clauses
    site_clause = ' OR '.join(f"site:{s}" for s in sources) if sources else ''
    full_query = f"{query} {site_clause}".strip()
    q = urllib.parse.quote_plus(full_query)
    # English India localization to improve coverage for NSE names
    return f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"


def parse_pubdate(pubdate_text: str) -> dt.datetime:
    # Example: Sat, 30 Aug 2025 08:10:00 GMT
    try:
        return dt.datetime.strptime(pubdate_text, "%a, %d %b %Y %H:%M:%S %Z")
    except Exception:
        # Fallback: try without TZ, treat as UTC
        try:
            return dt.datetime.strptime(pubdate_text, "%a, %d %b %Y %H:%M:%S")
        except Exception:
            try:
                # Last resort: dateparser (handles many formats)
                import dateparser  # type: ignore
                d = dateparser.parse(pubdate_text, settings={"TO_TIMEZONE": "UTC", "RETURN_AS_TIMEZONE_AWARE": False})
                return d
            except Exception:
                return None


def fetch_rss_items(ticker: str, sources: List[str], publishers_only: bool = False) -> List[Tuple[str, str, str, dt.datetime]]:
    """Return list of (title, link, source, published_dt) for a ticker.

    Strategy:
    1) Attempt Google News RSS for breadth.
    2) Also query a set of first-party publisher feeds and filter by ticker keyword in title.
    """
    items: List[Tuple[str, str, str, dt.datetime]] = []

    # 1) First-party publisher RSS (filter by ticker keyword) — prefer direct sources first
    publisher_feeds = [
        # India business/markets
        'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms',
        'https://www.business-standard.com/rss/markets-106.rss',
        'https://www.moneycontrol.com/rss/MCtopnews.xml',
        'https://www.livemint.com/rss/companies',
        'https://www.livemint.com/rss/market',
        'https://www.cnbctv18.com/rss/latest.xml',
        'https://www.financialexpress.com/market/feed/',
        'https://www.thehindubusinessline.com/feeder/default.rss',
        'https://www.businesstoday.in/rssfeeds/?id=0',
        'https://www.bqprime.com/feed',
        'https://www.indianewsnetwork.com/rss.en.business.xml',
        'https://zeebiz.com/rss/latestnews.xml',
        'https://www.forbesindia.com/rss/latest.xml',
        'https://trak.in/feed/',
    ]
    kw = ticker.upper()
    relaxed_kw = ticker.capitalize()
    def _fetch_feed(feed_url: str):
        try:
            r = http_get(feed_url, timeout=12)
            if r is None or r.status_code >= 400:
                return []
            root = ET.fromstring(r.content)
            ch = root.find('channel')
            if ch is None:
                return []
            out = []
            for it in ch.findall('item'):
                title = it.findtext('title') or ''
                if not title:
                    continue
                if not title_matches_ticker(ticker, title):
                    continue
                link = it.findtext('link') or ''
                pubdate = parse_pubdate(it.findtext('pubDate') or '')
                src_el = it.find('{*}source')
                src = (src_el.text or '').strip() if src_el is not None else urllib.parse.urlparse(link).netloc
                out.append((html.unescape(title), link, src, pubdate))
            return out
        except Exception:
            return []

    # Parallelize publisher feed fetching (polite per-host gates still apply)
    with ThreadPoolExecutor(max_workers=min(len(publisher_feeds), _GLOBAL_MAX_WORKERS)) as ex:
        futs = [ex.submit(_fetch_feed, feed) for feed in publisher_feeds]
        for f in as_completed(futs):
            try:
                items.extend(f.result())
            except Exception:
                pass

    # 2) Google News RSS (breadth) unless restricted to publishers only
    if not publishers_only:
        try:
            url = build_gnews_rss_url(ticker, sources)
            resp = http_get(url, timeout=12)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            channel = root.find('channel')
            if channel is not None:
                for it in channel.findall('item'):
                    title = it.findtext('title') or ''
                    link = it.findtext('link') or ''
                    pubdate = parse_pubdate(it.findtext('pubDate') or '')
                    source_el = it.find('{*}source')
                    source = (source_el.text or '').strip() if source_el is not None else ''
                    # Try description anchor for publisher URL
                    desc_html = it.findtext('description') or ''
                    orig_link = ''
                    if desc_html:
                        try:
                            dh = BeautifulSoup(desc_html, 'html.parser')
                            a = dh.find('a', href=True)
                            if a and a['href']:
                                orig_link = a['href']
                        except Exception:
                            pass
                    best_link = orig_link or link
                    # Apply ticker-aware title filter for GNews too
                    if title and best_link and title_matches_ticker(ticker, title):
                        items.append((html.unescape(title), best_link, source, pubdate))
        except Exception:
            pass

    return items


# --------- Ticker title matching using symbol lists + synonyms ---------
_TICKER_SYNONYMS = None  # Dict[str, set[str]] of base symbol -> name aliases
_VALID_TICKERS = None    # Set[str] of valid symbols (both base and base.NS)


def _load_valid_ticker_set() -> set[str]:
    """Load a set of valid common-equity symbols from local sources (cached).

    Filters out obvious non-equity instruments (ETF, FUND, INDEX, etc.).
    """
    global _VALID_TICKERS
    if _VALID_TICKERS is not None:
        return _VALID_TICKERS
    s: set[str] = set()
    # valid_nse_tickers.txt
    try:
        with open('valid_nse_tickers.txt', 'r', encoding='utf-8', errors='ignore') as vf:
            for line in vf:
                sym = (line.strip() or '').upper()
                if not sym:
                    continue
                base = sym.replace('.NS', '')
                s.add(base)
                s.add(base + '.NS')
    except Exception:
        pass
    # sec_list.csv (Symbol column)
    try:
        with open('sec_list.csv', 'r', encoding='utf-8', errors='ignore') as cf:
            reader = csv.DictReader(cf)
            for row in reader:
                sym = (row.get('Symbol') or '').strip().upper()
                name = (row.get('Security Name') or '').strip()
                if not sym:
                    continue
                nm_up = name.upper()
                if any(k in nm_up for k in (
                    'ETF', 'FUND', 'INDEX', 'NIFTY', 'SENSEX', 'TRUST', 'GOLD', 'SILVER', 'SOVEREIGN', 'BOND', 'DEBT'
                )):
                    continue
                base = sym.replace('.NS', '')
                s.add(base)
                s.add(base + '.NS')
    except Exception:
        pass
    _VALID_TICKERS = s
    return _VALID_TICKERS


def _load_ticker_synonyms():
    global _TICKER_SYNONYMS
    if _TICKER_SYNONYMS is not None:
        return _TICKER_SYNONYMS
    syn: dict[str, set[str]] = {}
    # Optional: tickers.py mapping
    try:
        import os, sys
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
        if root_dir not in sys.path:
            sys.path.append(root_dir)
        import tickers as tickers_mod  # type: ignore
        mapping = getattr(tickers_mod, '_TICKERS', {})
        for k, aliases in mapping.items():
            base = k.replace('.NS', '').upper()
            names = set()
            for a in aliases or []:
                if not a:
                    continue
                names.add(str(a).strip().lower())
                names.add(str(a).strip().title())
            if names:
                syn[base] = names
    except Exception:
        pass
    # Add minimal built-ins if still empty (top India names)
    if not syn:
        fallback = {
            'RELIANCE': {'reliance', 'reliance industries', 'ril'},
            'TCS': {'tcs', 'tata consultancy services'},
            'TATAMOTORS': {'tata motors', 'tatamotors'},
            'TATASTEEL': {'tata steel', 'tatasteel'},
            'ADANIENT': {'adani enterprises', 'adani ent'},
            'ADANIPORTS': {'adani ports', 'adani ports and special economic zone', 'apsez'},
            'ADANIGREEN': {'adani green', 'adani green energy'},
            'ADANIPOWER': {'adani power'},
            'ADANITRANS': {'adani energy solutions', 'adani transmission'},
        }
        for base, aliases in fallback.items():
            syn[base] = set(a for a in aliases)
    # Augment with sec_list.csv Security Name for broad coverage
    try:
        with open('sec_list.csv', 'r', encoding='utf-8', errors='ignore') as cf:
            reader = csv.DictReader(cf)
            for row in reader:
                sym = (row.get('Symbol') or '').strip().upper()
                name = (row.get('Security Name') or '').strip()
                if not sym or not name:
                    continue
                base = sym.replace('.NS', '')
                variants = set()
                nm = name
                variants.add(nm.lower())
                variants.add(nm.title())
                # Basic LTD/LIMITED normalization
                nm2 = re.sub(r"\blimited\b", "ltd", nm, flags=re.I).strip()
                variants.add(nm2.lower())
                variants.add(nm2.title())
                # Remove punctuation variants
                nm3 = re.sub(r"[^A-Za-z0-9\s]", "", nm)
                variants.add(nm3.lower())
                variants.add(nm3.title())
                if base not in syn:
                    syn[base] = set()
                syn[base].update(variants)
    except Exception:
        pass
    _TICKER_SYNONYMS = syn
    return syn


_EXPERT_PLAYBOOK = None  # cached config


def _load_expert_playbook() -> dict:
    global _EXPERT_PLAYBOOK
    if _EXPERT_PLAYBOOK is not None:
        return _EXPERT_PLAYBOOK
    try:
        import json, os
        path = os.getenv('EXPERT_PLAYBOOK_PATH', 'expert_playbook.json')
        if path and os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                _EXPERT_PLAYBOOK = json.load(f)
                return _EXPERT_PLAYBOOK
    except Exception:
        pass
    _EXPERT_PLAYBOOK = {}
    return _EXPERT_PLAYBOOK


def title_matches_ticker(ticker: str, title: str) -> bool:
    """Strict title-to-ticker match with real symbol validation.

    - Requires the provided ticker to be a known listed symbol (via local lists)
    - Matches exact ticker with word boundaries (avoids ACC ⊂ accuracy)
    - Also matches common company name variants (from sec_list.csv/tickers.py)
    """
    if not ticker or not title:
        return False
    valid = _load_valid_ticker_set()
    t_up = (ticker or '').strip().upper()
    base = t_up.replace('.NS', '')
    # Reject non-listed tokens early (e.g., BFSI/CONS/TECH) using local symbol lists
    if base not in valid and (base + '.NS') not in valid:
        return False

    title_up = title.upper()
    # Ambiguous symbols require company-name match (avoid plain-word collisions like GLOBAL)
    ambiguous = set((_load_expert_playbook().get('heuristic') or {}).get('ambiguous_symbols', []))
    is_ambiguous = base in ambiguous

    # Exact ticker with word boundaries (optionally with .NS). Skip for ambiguous symbols.
    if not is_ambiguous:
        try:
            if re.search(rf"\b{re.escape(base)}(?:\.NS)?\b", title_up):
                return True
        except re.error:
            if f" {base} " in f" {title_up} ":
                return True

    # Company name/synonyms check
    syn = _load_ticker_synonyms()
    names = syn.get(base, set()) or set()
    title_low = title.lower()
    for n in names:
        s = (n or '').strip()
        if not s:
            continue
        if s.lower() in title_low:
            return True
    return False


def resolve_final_url(url: str) -> str:
    """Follow redirects to original article and return the final URL.

    Handles Google News/aggregator links that embed the publisher link in a url=
    param or inside intermediate HTML pages.
    """
    try:
        # Cache check
        if url in _RESOLVE_CACHE:
            return _RESOLVE_CACHE[url]
        r = http_get(url, timeout=12, allow_redirects=True)
        if 200 <= r.status_code < 400 and r.url:
            final = r.url
            # If we still land on Google News/URL wrapper, try to extract publisher URL
            parsed_final = urllib.parse.urlparse(final)
            host = parsed_final.netloc.lower()
            if 'news.google.' in host or host.startswith('www.google.'):
                # Try url= from query
                try:
                    q = urllib.parse.parse_qs(parsed_final.query)
                    if 'url' in q and q['url']:
                        return q['url'][0]
                except Exception:
                    pass
                # If it's an RSS article path, try the non-RSS article page which often exposes the publisher link
                try:
                    if parsed_final.path.startswith('/rss/articles/'):
                        article_path = parsed_final.path.replace('/rss/articles/', '/articles/')
                        gn_url = urllib.parse.urlunparse((parsed_final.scheme, parsed_final.netloc, article_path, '', parsed_final.query, ''))
                        r_gn = http_get(gn_url, timeout=12)
                        if r_gn.status_code == 200:
                            soup_gn = BeautifulSoup(r_gn.text, 'html.parser')
                            # look for outbound publisher links
                            for a in soup_gn.find_all('a', href=True):
                                href = a['href']
                                if not href.startswith('http'):
                                    continue
                                h = urllib.parse.urlparse(href).netloc.lower()
                                if 'google' not in h:
                                    _RESOLVE_CACHE[url] = href
                                    return href
                except Exception:
                    pass
                # Parse HTML for meta refresh or anchor to publisher
                try:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    # canonical or og:url first
                    can = soup.find('link', rel=lambda v: v and 'canonical' in v.lower())
                    if can and can.get('href'):
                        ch = urllib.parse.urlparse(can['href']).netloc.lower()
                        if ch and 'google' not in ch:
                            _RESOLVE_CACHE[url] = urllib.parse.urljoin(final, can['href'])
                            return _RESOLVE_CACHE[url]
                    og = soup.find('meta', attrs={'property': 'og:url'})
                    if og and og.get('content'):
                        oh = urllib.parse.urlparse(og['content']).netloc.lower()
                        if oh and 'google' not in oh:
                            _RESOLVE_CACHE[url] = og['content']
                            return _RESOLVE_CACHE[url]
                    # meta refresh
                    meta = soup.find('meta', attrs={'http-equiv': lambda v: v and v.lower() == 'refresh'})
                    if meta and meta.get('content'):
                        # content like: '0;url=https://publisher/article'
                        parts = meta['content'].split('url=')
                        if len(parts) > 1:
                            return parts[1].strip()
                    # fall back: any anchor pointing outside Google
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if not href:
                            continue
                        u = urllib.parse.urlparse(href)
                        if not u.netloc:
                            continue
                        if 'google' in u.netloc.lower():
                            # try url= param
                            q2 = urllib.parse.parse_qs(u.query)
                            if 'url' in q2 and q2['url']:
                                _RESOLVE_CACHE[url] = q2['url'][0]
                                return _RESOLVE_CACHE[url]
                            continue
                        _RESOLVE_CACHE[url] = href
                        return _RESOLVE_CACHE[url]
                except Exception:
                    pass
                # As a last resort, attempt the improved resolver (may be noisy)
                try:
                    from improved_url_resolver import get_actual_article_url_improved  # type: ignore
                    improved = get_actual_article_url_improved(final)
                    if improved and 'news.google.' not in improved:
                        _RESOLVE_CACHE[url] = improved
                        return _RESOLVE_CACHE[url]
                except Exception:
                    pass
            _RESOLVE_CACHE[url] = final
            return final
    except Exception:
        pass
    # Fallback: Some aggregator links include a url= param directly
    try:
        parsed = urllib.parse.urlparse(url)
        q = urllib.parse.parse_qs(parsed.query)
        if 'url' in q and q['url']:
            _RESOLVE_CACHE[url] = q['url'][0]
            return _RESOLVE_CACHE[url]
    except Exception:
        pass
    return url


def _text_from_soup(soup: BeautifulSoup) -> str:
    for el in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
        el.decompose()
    return soup.get_text(separator=' ', strip=True)


def _extract_site_specific(url: str, soup: BeautifulSoup) -> str:
    host = urllib.parse.urlparse(url).netloc.lower()
    candidates = []
    # Generic strong candidates
    for sel in [
        'article',
        '[role="main"] article',
        'div[itemprop="articleBody"]',
        'section[itemprop="articleBody"]',
        'div[class*="article"]',
        'div[class*="content"]',
        'section[class*="content"]',
    ]:
        for node in soup.select(sel):
            text = _text_from_soup(node)
            if len(text) > 500:
                candidates.append(text)

    # Site-specific boosters (best-effort)
    if 'moneycontrol.com' in host:
        for sel in ['article', 'div.clearfix', 'div#article_main', 'div#article-main', 'div.normal']:
            for node in soup.select(sel):
                text = _text_from_soup(node)
                if len(text) > 400:
                    candidates.append(text)
    if 'livemint.com' in host:
        for sel in ['article', 'div.storyParagraph', 'section.page-content', 'div.text']:
            for node in soup.select(sel):
                text = _text_from_soup(node)
                if len(text) > 400:
                    candidates.append(text)
    if 'indiatimes.com' in host:
        for sel in ['div#articleText', 'div.artText', 'div.content', 'article']:
            for node in soup.select(sel):
                text = _text_from_soup(node)
                if len(text) > 400:
                    candidates.append(text)
    if 'business-standard.com' in host:
        for sel in ['div.p-content', 'div.story-content', 'article']:
            for node in soup.select(sel):
                text = _text_from_soup(node)
                if len(text) > 400:
                    candidates.append(text)
    if 'reuters.com' in host:
        for sel in ['div[data-testid="article-body"]', 'div.article-body__content', 'article']:
            for node in soup.select(sel):
                text = _text_from_soup(node)
                if len(text) > 400:
                    candidates.append(text)

    # Pick the longest as proxy for full body
    if candidates:
        return max(candidates, key=len)
    return ''


def extract_full_text(url: str) -> str:
    try:
        if url in _CONTENT_CACHE:
            return _CONTENT_CACHE[url]
        # 0) Trafilatura (fast and robust on many news sites)
        if HAS_TRAFILATURA:
            try:
                downloaded = trafilatura.fetch_url(url, no_ssl=True)
                if downloaded:
                    text = trafilatura.extract(
                        downloaded,
                        include_comments=False,
                        include_tables=False,
                        favor_recall=True,
                        output_format='txt'
                    )
                    if text and len(text) > 600:
                        text = text[:20000]
                        _CONTENT_CACHE[url] = text
                        return text
            except Exception:
                pass

        # 0b) Newspaper3k fallback
        if HAS_NEWSPAPER:
            try:
                art = Article(url)
                art.download()
                art.parse()
                text = (art.text or '').strip()
                if len(text) > 600:
                    text = text[:20000]
                    _CONTENT_CACHE[url] = text
                    return text
            except Exception:
                pass

        r = http_get(url, timeout=15)
        if r.status_code != 200 or not r.text:
            return ''

        base_soup = BeautifulSoup(r.text, 'html.parser')
        # Try site-specific content first (often more complete than readability)
        site_text = _extract_site_specific(r.url, base_soup)
        if len(site_text) > 400:
            text = site_text[:20000]
            if len(text) >= 200:
                _CONTENT_CACHE[url] = text
            return text

        # If page is a shell, try AMP version
        # Prefer AMP when available (often cleaner content)
        amp_link = base_soup.find('link', rel=lambda v: v and 'amphtml' in v.lower())
        if amp_link and amp_link.get('href'):
            try:
                amp_url = urllib.parse.urljoin(r.url, amp_link['href'])
                r2 = http_get(amp_url, timeout=12)
                if r2.status_code == 200 and r2.text:
                    soup2 = BeautifulSoup(r2.text, 'html.parser')
                    # AMP often has <article> or [itemprop=articleBody]
                    amp_text = _extract_site_specific(amp_url, soup2)
                    if len(amp_text) > 300:
                        text = amp_text[:20000]
                        if len(text) >= 200:
                            _CONTENT_CACHE[url] = text
                        return text
                    # Fallback: readability on AMP
                    doc2 = Document(r2.text)
                    soup2r = BeautifulSoup(doc2.summary(), 'html.parser')
                    text2r = _text_from_soup(soup2r)
                    if len(text2r) > 300:
                        text = text2r[:20000]
                        if len(text) >= 200:
                            _CONTENT_CACHE[url] = text
                        return text
            except Exception:
                pass

        # Fallback to readability on the original page
        doc = Document(r.text)
        soup = BeautifulSoup(doc.summary(), 'html.parser')
        text = _text_from_soup(soup)
        text = text[:20000]
        if len(text) >= 200:
            _CONTENT_CACHE[url] = text
        return text
    except Exception:
        return ''


# --------- Market Cap Lookup (Resilient: yfinance + Yahoo APIs + Google) ---------
def _enforce_mcap_rate_limits(max_per_minute: int = 15):
    now = time.time()
    global _MCAP_REQUEST_LOG
    _MCAP_REQUEST_LOG = [t for t in _MCAP_REQUEST_LOG if now - t < 60]
    if len(_MCAP_REQUEST_LOG) >= max_per_minute:
        sleep_time = 61 - (now - _MCAP_REQUEST_LOG[0])
        if sleep_time > 0:
            time.sleep(sleep_time)
            now = time.time()
            _MCAP_REQUEST_LOG = [t for t in _MCAP_REQUEST_LOG if now - t < 60]
    _MCAP_REQUEST_LOG.append(time.time())


def _yahoo_quote_v7(symbol: str) -> tuple[int | None, str | None]:
    try:
        url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={urllib.parse.quote(symbol)}"
        r = http_get(url, timeout=8)
        if not r or r.status_code >= 400:
            return None, None
        data = r.json()
        res = (data or {}).get('quoteResponse', {}).get('result', [])
        if not res:
            return None, None
        entry = res[0]
        mcap = entry.get('marketCap')
        cur = entry.get('currency') or ''
        if isinstance(mcap, float):
            mcap = int(mcap)
        return (mcap if isinstance(mcap, int) else None), cur
    except Exception:
        return None, None


def _yahoo_quote_v10(symbol: str) -> tuple[int | None, str | None]:
    try:
        url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{urllib.parse.quote(symbol)}?modules=summaryDetail,price"
        r = http_get(url, timeout=8)
        if not r or r.status_code >= 400:
            return None, None
        data = r.json()
        res = (data or {}).get('quoteSummary', {}).get('result', [])
        if not res:
            return None, None
        node = res[0]
        sd = (node or {}).get('summaryDetail', {})
        cap = (sd or {}).get('marketCap', {})
        raw = cap.get('raw') if isinstance(cap, dict) else None
        cur = (node.get('price', {}) or {}).get('currency')
        if isinstance(raw, float):
            raw = int(raw)
        return (raw if isinstance(raw, int) else None), (cur or '')
    except Exception:
        return None, None


def _google_finance_cap(symbol_base: str, exchange: str = 'NSE') -> tuple[int | None, str | None]:
    try:
        url = f"https://www.google.com/finance/quote/{urllib.parse.quote(symbol_base)}:{exchange}?hl=en"
        r = http_get(url, timeout=10)
        if not r or r.status_code >= 400 or not r.text:
            return None, None
        m = re.search(r"Market\s*cap.*?([0-9,.]+)\s*([KMBT])", r.text, re.I | re.S)
        if not m:
            return None, None
        num = float(m.group(1).replace(',', ''))
        mult = {'K':1e3, 'M':1e6, 'B':1e9, 'T':1e12}.get(m.group(2).upper(), 1.0)
        val = int(num * mult)
        cur = ''
        return val, cur
    except Exception:
        return None, None


def get_market_cap_for_ticker(ticker: str) -> tuple[int | None, str | None]:
    key = ticker.upper()
    if key in _MARKET_CAP_CACHE:
        return _MARKET_CAP_CACHE[key]

    # Throttle to avoid Yahoo rate limits
    _enforce_mcap_rate_limits()

    # Prefer using shared helper implemented in get_market_caps.py (validated)
    try:
        from get_market_caps import fetch_mcap as _fetch_caps  # type: ignore
        rows = _fetch_caps([key], use_ns=True, debug=False)
        if rows:
            _base, _sym, _mcap, _cur = rows[0]
            if isinstance(_mcap, int) and _mcap >= 1_000_000_000:
                _MARKET_CAP_CACHE[key] = (_mcap, _cur)
                return _MARKET_CAP_CACHE[key]
    except Exception:
        pass

    # Fallback internal method: Prefer NSE symbol first
    sym_ns = f"{key}.NS"
    mcap = None
    cur = ''

    # Try yfinance if available
    try:
        import yfinance as yf  # type: ignore
        from yfinance import shared as yshared  # type: ignore
        sess = _get_session()
        try:
            yshared._session = sess  # reuse pooled session
        except Exception:
            pass
        try:
            info = yf.Ticker(sym_ns, session=sess).info
        except Exception:
            info = {}
        mcap = info.get('marketCap') if isinstance(info, dict) else None
        cur = (info.get('currency') if isinstance(info, dict) else '') or ''
        if isinstance(mcap, float):
            mcap = int(mcap)
        if not mcap:
            try:
                info2 = yf.Ticker(key, session=sess).info
            except Exception:
                info2 = {}
            mcap = info2.get('marketCap') if isinstance(info2, dict) else None
            if not cur:
                cur = (info2.get('currency') if isinstance(info2, dict) else '') or ''
            if isinstance(mcap, float):
                mcap = int(mcap)
    except Exception:
        pass

    # Yahoo API fallbacks
    if not mcap:
        mcap, cur2 = _yahoo_quote_v7(sym_ns)
        if cur2 and not cur:
            cur = cur2
    if not mcap:
        mcap, cur2 = _yahoo_quote_v7(key)
        if cur2 and not cur:
            cur = cur2
    if not mcap:
        mcap, cur2 = _yahoo_quote_v10(sym_ns)
        if cur2 and not cur:
            cur = cur2
    if not mcap:
        mcap, cur2 = _yahoo_quote_v10(key)
        if cur2 and not cur:
            cur = cur2

    # Google Finance fallback (NSE page)
    # Optional Google Finance fallback (guard with sanity threshold to avoid bogus matches)
    if not mcap:
        gmcap, gcur = _google_finance_cap(key, exchange='NSE')
        # Accept only clearly non-trivial values (>= 1e9) to avoid accidental small matches like "6.00K"
        if isinstance(gmcap, int) and gmcap >= 1_000_000_000:
            mcap = gmcap
            if gcur and not cur:
                cur = gcur

    # Do not force default currency; keep as-is if unknown
    _MARKET_CAP_CACHE[key] = (mcap if isinstance(mcap, int) else None, cur)
    return _MARKET_CAP_CACHE[key]


# --------- Yahoo v10 helpers for Net Profit and Net Worth ---------
def _yahoo_v10_income_ttm(symbol: str) -> tuple[int | None, str | None] | None:
    try:
        url = (
            f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{urllib.parse.quote(symbol)}"
            f"?modules=incomeStatementHistoryQuarterly,incomeStatementHistory,financialData,price"
        )
        r = http_get(url, timeout=10)
        if not r or r.status_code >= 400:
            return None
        data = r.json()
        res = (data or {}).get('quoteSummary', {}).get('result', [])
        if not res:
            return None
        node = res[0]
        # Currency from price or financialData
        cur = (node.get('price', {}) or {}).get('currency') or (node.get('financialData', {}) or {}).get('financialCurrency')
        # Sum last 4 quarterly netIncome.raw if available
        qhist = (((node.get('incomeStatementHistoryQuarterly') or {}).get('incomeStatementHistory')) or [])
        ttm = 0
        count = 0
        for q in qhist[:4]:
            ni = (q.get('netIncome') or {}).get('raw')
            if isinstance(ni, (int, float)):
                ttm += int(ni)
                count += 1
        if count >= 2:  # accept if at least 2 quarters available
            return int(ttm), cur
        # Fallback to latest annual
        ahist = (((node.get('incomeStatementHistory') or {}).get('incomeStatementHistory')) or [])
        if ahist:
            ni = (ahist[0].get('netIncome') or {}).get('raw')
            if isinstance(ni, (int, float)):
                return int(ni), cur
    except Exception:
        return None
    return None


def _yahoo_v10_equity_latest(symbol: str) -> tuple[int | None, str | None] | None:
    try:
        url = (
            f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{urllib.parse.quote(symbol)}"
            f"?modules=balanceSheetHistoryQuarterly,balanceSheetHistory,price"
        )
        r = http_get(url, timeout=10)
        if not r or r.status_code >= 400:
            return None
        data = r.json()
        res = (data or {}).get('quoteSummary', {}).get('result', [])
        if not res:
            return None
        node = res[0]
        cur = (node.get('price', {}) or {}).get('currency')
        # Prefer quarterly
        qhist = (((node.get('balanceSheetHistoryQuarterly') or {}).get('balanceSheetStatements')) or [])
        if qhist:
            eq = (qhist[0].get('totalStockholderEquity') or {}).get('raw')
            if isinstance(eq, (int, float)):
                return int(eq), cur
        ahist = (((node.get('balanceSheetHistory') or {}).get('balanceSheetStatements')) or [])
        if ahist:
            eq2 = (ahist[0].get('totalStockholderEquity') or {}).get('raw')
            if isinstance(eq2, (int, float)):
                return int(eq2), cur
    except Exception:
        return None
    return None


def _format_market_cap(val: int | None, currency: str | None) -> str:
    if not val:
        return "Unknown"
    units = ["", "K", "M", "B", "T"]
    v = float(val)
    idx = 0
    while v >= 1000.0 and idx < len(units) - 1:
        v /= 1000.0
        idx += 1
    cur = currency or ""
    return f"{v:.2f}{units[idx]} {cur}".strip()


# --------- Net Profit (TTM/latest) via yfinance with fallbacks ---------
def _enforce_np_rate_limits(max_per_minute: int = 15):
    now = time.time()
    global _NET_PROFIT_REQ_LOG
    _NET_PROFIT_REQ_LOG = [t for t in _NET_PROFIT_REQ_LOG if now - t < 60]
    if len(_NET_PROFIT_REQ_LOG) >= max_per_minute:
        sleep_time = 61 - (now - _NET_PROFIT_REQ_LOG[0])
        if sleep_time > 0:
            time.sleep(sleep_time)
            now = time.time()
            _NET_PROFIT_REQ_LOG = [t for t in _NET_PROFIT_REQ_LOG if now - t < 60]
    _NET_PROFIT_REQ_LOG.append(time.time())


def _latest_from_df(df, labels: list[str]) -> int | None:
    try:
        if df is None or getattr(df, 'empty', True):
            return None
        # Try exact label match first
        for label in labels:
            if label in df.index:
                try:
                    ser = df.loc[label].dropna()
                    if not ser.empty:
                        return int(float(ser.iloc[0]))
                except Exception:
                    pass
        # Case-insensitive fallback
        idx = [str(i).strip().lower() for i in list(df.index)]
        for label in labels:
            lab = label.strip().lower()
            if lab in idx:
                try:
                    row = df.loc[df.index[idx.index(lab)]]
                    ser = row.dropna()
                    if not ser.empty:
                        return int(float(ser.iloc[0]))
                except Exception:
                    continue
        # heuristic: any row containing net/profit keywords
        for i, name in enumerate(list(df.index)):
            nlow = str(name).lower()
            if ('net' in nlow and 'income' in nlow) or ('net' in nlow and 'profit' in nlow):
                try:
                    row = df.loc[name]
                    ser = row.dropna()
                    if len(ser) > 0:
                        return int(float(ser.iloc[0]))
                except Exception:
                    continue
    except Exception:
        return None
    return None


def _retry_yahoo(callable_fn, *args, **kwargs):
    try:
        res = callable_fn(*args, **kwargs)
        if res and res[0]:
            return res
    except Exception:
        pass
    try:
        time.sleep(0.8)
        res = callable_fn(*args, **kwargs)
        if res and res[0]:
            return res
    except Exception:
        return None
    return None


def _sum_last_n_from_df(df, labels: list[str], n: int = 4) -> int | None:
    try:
        if df is None or getattr(df, 'empty', True):
            return None
        # Try exact labels first
        for label in labels:
            if label in df.index:
                try:
                    ser = df.loc[label].dropna()
                    if not ser.empty:
                        vals = [float(v) for v in list(ser)[:n] if v == v]
                        if vals:
                            return int(sum(vals))
                except Exception:
                    pass
        # Case-insensitive fallback
        idx = [str(i).strip().lower() for i in list(df.index)]
        for label in labels:
            lab = label.strip().lower()
            if lab in idx:
                try:
                    row = df.loc[df.index[idx.index(lab)]]
                    ser = row.dropna()
                    if not ser.empty:
                        vals = [float(v) for v in list(ser)[:n] if v == v]
                        if vals:
                            return int(sum(vals))
                except Exception:
                    continue
    except Exception:
        return None
    return None


def _yf_symbol(ticker: str) -> str:
    t = (ticker or '').strip().upper()
    if t.endswith('.NS'):
        base = t[:-3]
        clean = re.sub(r'[^\w]', '', base)
        return clean + '.NS'
    clean_t = re.sub(r'[^\w]', '', t)
    return clean_t + '.NS'


def _first(values: list) -> int | None:
    for v in values:
        if v is None:
            continue
        try:
            if isinstance(v, bool):
                continue
            iv = int(float(v))
            return iv
        except Exception:
            continue
    return None


def get_net_profit_for_ticker(ticker: str) -> tuple[int | None, str | None]:
    key = ticker.upper()
    if key in _NET_PROFIT_CACHE:
        return _NET_PROFIT_CACHE[key]
    _enforce_np_rate_limits()
    sym_ns = _yf_symbol(key)
    val: int | None = None
    cur: str | None = None
    # 0) Yahoo v10 API (TTM from last 4 quarters; fallback to latest annual) with one retry
    y = _retry_yahoo(_yahoo_v10_income_ttm, sym_ns)
    if y and y[0]:
        _NET_PROFIT_CACHE[key] = (int(y[0]), y[1])
        return _NET_PROFIT_CACHE[key]

    try:
        import yfinance as yf  # type: ignore
        from yfinance import shared as yshared  # type: ignore
        sess = _get_session()
        try:
            yshared._session = sess
        except Exception:
            pass
        tk = yf.Ticker(sym_ns, session=sess)
        fi = getattr(tk, 'fast_info', {}) or {}
        info = tk.info or {}
        # Access DFs; try both attribute spellings used in your screener
        # Income statement candidates (quarterly then annual)
        qis = (
            getattr(tk, 'quarterly_income_stmt', None)
            or getattr(tk, 'quarterly_income_statement', None)
            or getattr(tk, 'quarterly_financials', None)
        )
        ais = (
            getattr(tk, 'income_stmt', None)
            or getattr(tk, 'income_statement', None)
            or getattr(tk, 'financials', None)
        )
        # Prefer explicit TTM sum from quarterly; then other fallbacks
        val = _first([
            _sum_last_n_from_df(qis, ['Net Income','Net Profit','Profit After Tax'], n=4),
            _latest_from_df(ais, ['Net Income','Net Profit','Profit After Tax']),
            fi.get('ttm_net_income'),
            info.get('netIncome') or info.get('netIncomeToCommon')
        ])
        cur = info.get('financialCurrency') or info.get('currency') or cur
    except Exception:
        pass

    # 2b) Approximation using Market Cap and P/E if available
    if not val:
        try:
            mcap, mcur = get_market_cap_for_ticker(key)
            import yfinance as yf  # type: ignore
            sess = _get_session()
            pe = None
            try:
                info3 = yf.Ticker(sym_ns, session=sess).info
                pe = info3.get('trailingPE') or info3.get('forwardPE')
            except Exception:
                pe = None
            if mcap and pe and pe > 0:
                approx = int(mcap / float(pe))
                _NET_PROFIT_CACHE[key] = (approx, mcur)
                return _NET_PROFIT_CACHE[key]
        except Exception:
            pass

    # 3) Screener's get_fin as last resort (may be heavy)
    try:
        import importlib
        mod = importlib.import_module('swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods')
        gf = getattr(mod, 'get_fin', None)
        if callable(gf):
            fin = gf(key, require_positive=False, skip=False, hist_df=None)
            if fin:
                v = getattr(fin, 'inc', None)
                if v is not None:
                    _NET_PROFIT_CACHE[key] = (int(float(v)), None)
                    return _NET_PROFIT_CACHE[key]
    except Exception:
        pass

    _NET_PROFIT_CACHE[key] = (val if isinstance(val, int) else None, cur)
    return _NET_PROFIT_CACHE[key]


def _latest_equity_from_bs(df) -> int | None:
    """Try common equity row names; else compute Assets - Liab for latest column."""
    if df is None or getattr(df, 'empty', True):
        return None
    labels = [
        'Total Stockholder Equity',
        "Total Stockholders' Equity",
        'Total Shareholder Equity',
        'Shareholders Equity',
        'Shareholder Equity',
        'Total Equity',
        'Total Equity Gross Minority Interest',
        'Net Assets',
    ]
    # Direct match
    for lab in labels:
        try:
            if lab in df.index:
                row = df.loc[lab]
            else:
                # case-insensitive match
                for idx in list(df.index):
                    if str(idx).strip().lower() == lab.lower():
                        row = df.loc[idx]
                        break
                else:
                    continue
            ser = row.dropna()
            if len(ser) > 0:
                try:
                    return int(float(ser.iloc[0]))
                except Exception:
                    pass
        except Exception:
            continue
    # Compute Assets - Liabilities
    try:
        assets_row = None
        liab_row = None
        for idx in list(df.index):
            low = str(idx).lower()
            if assets_row is None and ('total assets' in low):
                assets_row = df.loc[idx]
            if liab_row is None and ('total liab' in low or 'total liabilities' in low):
                liab_row = df.loc[idx]
        if assets_row is not None and liab_row is not None:
            # Align columns and pick first non-null of (assets - liab)
            common_cols = [c for c in assets_row.index if c in liab_row.index]
            for c in common_cols:
                try:
                    a = float(assets_row[c])
                    l = float(liab_row[c])
                    v = a - l
                    if v == v:  # not NaN
                        return int(v)
                except Exception:
                    continue
    except Exception:
        pass
    return None


def _enforce_nw_rate_limits(max_per_minute: int = 15):
    now = time.time()
    global _NET_WORTH_REQ_LOG
    _NET_WORTH_REQ_LOG = [t for t in _NET_WORTH_REQ_LOG if now - t < 60]
    if len(_NET_WORTH_REQ_LOG) >= max_per_minute:
        sleep_time = 61 - (now - _NET_WORTH_REQ_LOG[0])
        if sleep_time > 0:
            time.sleep(sleep_time)
            now = time.time()
            _NET_WORTH_REQ_LOG = [t for t in _NET_WORTH_REQ_LOG if now - t < 60]
    _NET_WORTH_REQ_LOG.append(time.time())


def get_net_worth_for_ticker(ticker: str) -> tuple[int | None, str | None]:
    key = ticker.upper()
    if key in _NET_WORTH_CACHE:
        return _NET_WORTH_CACHE[key]
    _enforce_nw_rate_limits()
    sym_ns = _yf_symbol(key)
    val: int | None = None
    cur: str | None = None
    # 0) Screener's get_fin first (matches production logic you trust)
    try:
        import importlib
        mod = importlib.import_module('swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods')
        gf = getattr(mod, 'get_fin', None)
        if callable(gf):
            fin = gf(key, require_positive=False, skip=False, hist_df=None)
            if fin:
                v = getattr(fin, 'net', None)
                if v is not None:
                    _NET_WORTH_CACHE[key] = (int(float(v)), None)
                    return _NET_WORTH_CACHE[key]
    except Exception:
        pass

    # 1) Yahoo v10 API (latest equity) with one retry
    y = _retry_yahoo(_yahoo_v10_equity_latest, sym_ns)
    if y and y[0]:
        _NET_WORTH_CACHE[key] = (int(y[0]), y[1])
        return _NET_WORTH_CACHE[key]
    try:
        import yfinance as yf  # type: ignore
        from yfinance import shared as yshared  # type: ignore
        sess = _get_session()
        try:
            yshared._session = sess
        except Exception:
            pass
        tk = yf.Ticker(sym_ns, session=sess)
        fi = getattr(tk, 'fast_info', {}) or {}
        info = tk.info or {}
        qbs = (
            getattr(tk, 'quarterly_balance_sheet', None)
            or getattr(tk, 'quarterly_balancesheet', None)
        )
        abs_ = (
            getattr(tk, 'balance_sheet', None)
            or getattr(tk, 'balancesheet', None)
        )
        val = _first([
            _latest_equity_from_bs(qbs),
            _latest_equity_from_bs(abs_),
            (fi.get('book_value') and (fi.get('book_value') * (fi.get('shares_outstanding') or info.get('sharesOutstanding')))),
            info.get('totalStockholderEquity') or info.get('netAssets')
        ])
        cur = info.get('financialCurrency') or info.get('currency') or cur
    except Exception:
        pass

    # 2b) Approximation using Market Cap and P/B if available
    if not val:
        try:
            mcap, mcur = get_market_cap_for_ticker(key)
            import yfinance as yf  # type: ignore
            sess = _get_session()
            pb = None
            try:
                info3 = yf.Ticker(sym_ns, session=sess).info
                pb = info3.get('priceToBook')
            except Exception:
                pb = None
            if mcap and pb and pb > 0:
                approx = int(mcap / float(pb))
                _NET_WORTH_CACHE[key] = (approx, mcur)
                return _NET_WORTH_CACHE[key]
        except Exception:
            pass

    # Fallback: use screener's get_fin if available
    if val is None:
        try:
            import importlib
            mod = importlib.import_module('swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods')
            gf = getattr(mod, 'get_fin', None)
            if callable(gf):
                fin = gf(key, require_positive=False, skip=False, hist_df=None)
                if fin:
                    # fin.inc is Net Profit; currency not exposed here
                    v = getattr(fin, 'inc', None)
                    if v is not None:
                        val = int(float(v))
        except Exception:
            pass

    _NET_WORTH_CACHE[key] = (val if isinstance(val, int) else None, cur)
    return _NET_WORTH_CACHE[key]


def cleanup_old_files(current_aggregated_file: str, max_keep: int = 2):
    """
    Clean up old news files by moving them to old_news_files directory.
    Keeps only the most recent files based on max_keep parameter.
    """
    try:
        # Determine the aggregates root folder from the current file if provided,
        # else use the centralized aggregates dir.
        script_dir = os.path.dirname(os.path.abspath(__file__))
        aggregates_root = os.path.dirname(current_aggregated_file) if current_aggregated_file else _AGGREGATES_DIR
        if not aggregates_root:
            aggregates_root = _AGGREGATES_DIR
        if not os.path.isdir(aggregates_root):
            aggregates_root = script_dir

        old_dir = os.path.join(aggregates_root, "old_news_files")
        
        # Create old_news_files directory if it doesn't exist
        os.makedirs(old_dir, exist_ok=True)
        
        # Find all aggregated files (with or without .txt)
        all_aggregated = []
        patterns = [
            os.path.join(aggregates_root, "aggregated_full_articles_*.txt"),
            os.path.join(aggregates_root, "aggregated_full_articles_*")
        ]
        for pat in patterns:
            all_aggregated.extend([p for p in glob.glob(pat) if os.path.isfile(p)])
        # Dedup in case of overlap
        all_aggregated = sorted(set(all_aggregated))
        
        # Sort by modification time (newest first)
        all_aggregated.sort(key=os.path.getmtime, reverse=True)
        
        # Keep only the most recent files (including current one)
        files_to_move = all_aggregated[max_keep:]
        
        moved_files = 0
        for old_file in files_to_move:
            if old_file != current_aggregated_file:  # Don't move the current file
                try:
                    filename = os.path.basename(old_file)
                    dest_path = os.path.join(old_dir, filename)
                    # If destination exists, add timestamp to make unique
                    if os.path.exists(dest_path):
                        name, ext = os.path.splitext(filename)
                        timestamp = str(int(time.time()))
                        dest_path = os.path.join(old_dir, f"{name}_{timestamp}{ext}")
                    shutil.move(old_file, dest_path)
                    moved_files += 1
                except Exception as e:
                    print(f"[WARN] Could not move {old_file}: {e}")
        
        # Clean up old full_articles_run_* directories in the news runs root
        runs_root = _NEWS_RUNS_DIR if os.path.isdir(_NEWS_RUNS_DIR) else script_dir
        pattern = os.path.join(runs_root, "full_articles_run_*")
        all_run_dirs = [p for p in glob.glob(pattern) if os.path.isdir(p)]
        
        # Sort by modification time (newest first)
        all_run_dirs.sort(key=os.path.getmtime, reverse=True)
        
        # Keep only the most recent run directories
        dirs_to_move = all_run_dirs[max_keep:]
        
        moved_dirs = 0
        for old_dir_path in dirs_to_move:
            try:
                dirname = os.path.basename(old_dir_path)
                dest_path = os.path.join(old_dir, dirname)
                # If destination exists, add timestamp to make unique
                if os.path.exists(dest_path):
                    timestamp = str(int(time.time()))
                    dest_path = os.path.join(old_dir, f"{dirname}_{timestamp}")
                shutil.move(old_dir_path, dest_path)
                moved_dirs += 1
            except Exception as e:
                print(f"[WARN] Could not move directory {old_dir_path}: {e}")
        
        if moved_files > 0 or moved_dirs > 0:
            print(f"[CLEANUP] Moved {moved_files} old files and {moved_dirs} old directories to {old_dir}/")
            
    except Exception as e:
        print(f"[WARN] Cleanup failed: {e}")


def save_articles(ticker: str, articles: List[Tuple[str, str, str, dt.datetime]], max_articles: int, allowed_sources: List[str], output_file: str = None, mirror_dir: str | None = None, run_timestamp: str | None = None) -> str:
    ts = run_timestamp or dt.datetime.now().strftime('%Y%m%d_%H%M%S')
    agg_path = output_file or f"full_articles_test_{ticker}_{ts}.txt"
    per_ticker_path = None
    if mirror_dir:
        try:
            os.makedirs(mirror_dir, exist_ok=True)
            per_ticker_path = os.path.join(mirror_dir, f"full_articles_test_{ticker}_{ts}.txt")
        except Exception:
            per_ticker_path = None
    mode = 'a' if output_file else 'w'
    agg_fh = open(agg_path, mode, encoding='utf-8') if agg_path else None
    per_fh = open(per_ticker_path, 'w', encoding='utf-8') if per_ticker_path else None

    def write_line(s: str):
        for fh in [h for h in (agg_fh, per_fh) if h]:
            fh.write(s)

    # headers
    for fh in [h for h in (agg_fh, per_fh) if h]:
        fh.write(f"Full Article Fetch Test - {ticker}\n")
        fh.write("=" * 80 + "\n\n")

    # Worker that resolves, filters by allowed sources, extracts content
    def process_item(item: Tuple[str, str, str, dt.datetime]):
        title, link, source, pubdt = item
        try:
            raw_host = urllib.parse.urlparse(link).netloc.lower()
            # Early allow check to avoid heavy resolve if already allowed
            final_url = link
            if allowed_sources and any(dom.lower() in raw_host for dom in allowed_sources):
                final_url = link
            else:
                final_url = resolve_final_url(link)

            if allowed_sources:
                host = urllib.parse.urlparse(final_url).netloc.lower()
                if not any(dom.lower() in host for dom in allowed_sources):
                    return {
                        'status': 'skip',
                        'reason': 'outside allowed sources',
                        'title': title,
                        'url': final_url,
                    }

            text = extract_full_text(final_url)
            if len(text or '') < 200:
                try:
                    from enhanced_news_extractor_patch import enhanced_fetch_article_content  # type: ignore
                    alt = enhanced_fetch_article_content(final_url, max_retries=2)
                    if alt and len(alt.strip()) >= 200:
                        text = alt
                except Exception:
                    pass
            if len(text or '') < 200:
                return {
                    'status': 'skip',
                    'reason': 'short content',
                    'title': title,
                    'url': final_url,
                }
            return {
                'status': 'ok',
                'title': title,
                'url': final_url,
                'source': source,
                'pubdt': pubdt,
                'text': text,
            }
        except Exception:
            return {
                'status': 'skip',
                'reason': 'error',
                'title': item[0],
                'url': item[1],
            }

    saved = 0
    results = []
    # Submit all items; per-host gates and retries keep it polite
    with ThreadPoolExecutor(max_workers=_GLOBAL_MAX_WORKERS) as ex:
        futs = [ex.submit(process_item, it) for it in articles]
        for f in as_completed(futs):
            try:
                results.append(f.result())
            except Exception:
                results.append({'status': 'skip', 'reason': 'error', 'title': '', 'url': ''})

    # Write results: preserve acceptance limit; still log skips
    # Prepare Net Worth and Net Profit lines; print only when first full article is saved
    nw_line = None
    np_line = None
    nw_written = False
    np_written = False
    today = dt.datetime.utcnow().strftime('%Y-%m-%d')
    try:
        # Quick test for rate limiting - if basic yfinance fails, skip the heavy functions
        skip_financial_data = False
        try:
            import yfinance as yf
            test_ticker = yf.Ticker(f'{ticker}.NS')
            test_info = test_ticker.info
            # If we get here without error, proceed with full financial data fetch
        except Exception as e:
            # If basic test fails (likely rate limited), skip the heavy functions
            error_msg = str(e).lower()
            if 'rate limit' in error_msg or 'too many requests' in error_msg or 'forbidden' in error_msg:
                skip_financial_data = True
        
        if skip_financial_data:
            # Skip financial data fetching and show fallback message
            np_line = f"Financial metrics temporarily unavailable (rate limited) - {today}\n\n"
            nw_val, np_val = None, None
        else:
            # Try to fetch financial data normally
            try:
                nw_val, nw_cur = get_net_worth_for_ticker(ticker)
            except Exception:
                nw_val, nw_cur = None, None
                
            try:
                np_val, np_cur = get_net_profit_for_ticker(ticker)
            except Exception:
                np_val, np_cur = None, None
            
            # Process the results
            if nw_val is None and np_val is None:
                np_line = f"Financial metrics temporarily unavailable (rate limited) - {today}\n\n"
            else:
                # Net Worth check - only show if value > 0
                if isinstance(nw_val, int) and nw_val > 0:
                    nw_line = f"Net Worth ({today}): {_format_market_cap(nw_val, nw_cur)}\n"
                
                # Net Profit check - show if non-zero value
                if isinstance(np_val, int) and np_val:
                    np_line = f"Net Profit (TTM/latest) ({today}): {_format_market_cap(np_val, np_cur)}\n\n"
            
    except Exception:
        # If any error, use fallback message
        np_line = f"Financial metrics temporarily unavailable - {today}\n\n"
        nw_line = None
    for res in results:
        if res.get('status') != 'ok':
            # Write skip note for visibility
            write_line(f"(skipped: {res.get('reason')}) Title: {res.get('title')}\n")
            write_line(f"URL     : {res.get('url')}\n\n")
            continue
        if saved >= max_articles:
            continue
        fetched_utc = dt.datetime.utcnow().isoformat()
        if not nw_written and nw_line:
            write_line(nw_line)
            nw_written = True
        if not np_written and np_line:
            write_line(np_line)
            np_written = True
        write_line(f"Title   : {res['title']}\n")
        write_line(f"Source  : {res.get('source','')}\n")
        write_line(f"Published: {res.get('pubdt').isoformat() if res.get('pubdt') else 'Unknown'}\n")
        write_line(f"Fetched : {fetched_utc}\n")
        write_line(f"URL     : {res['url']}\n")
        write_line("-" * 80 + "\n")
        write_line(res['text'] + "\n\n")
        saved += 1

    if saved == 0:
        write_line("No full-length articles saved (all items too short or blocked).\n")

    if agg_fh:
        agg_fh.close()
    if per_fh:
        per_fh.close()
    return agg_path


def main():
    ap = argparse.ArgumentParser(description='Fetch full news articles for tickers (last 24h).')
    # Tune networking knobs from CLI (declare globals early to avoid scope issues)
    global _GLOBAL_MAX_WORKERS, _PER_HOST_MAX_CONCURRENCY, _PER_HOST_MIN_INTERVAL_SEC
    ap.add_argument('--tickers', nargs='+', default=None, help='List of tickers to test')
    ap.add_argument('--tickers-file', type=str, help='Path to file with tickers (one per line)')
    ap.add_argument('--sources', nargs='*', default=DEFAULT_SOURCES, help='Preferred news domains')
    ap.add_argument('--max-articles', type=int, default=2, help='Max articles per ticker to save')
    ap.add_argument('--publishers-only', action='store_true', help='Use first-party publisher RSS only (skip Google News)')
    ap.add_argument('--limit', type=int, default=0, help='Limit number of tickers from file (0=all)')
    ap.add_argument('--hours-back', type=int, default=24, choices=[8, 16, 24, 48], help='Only include news published within the last N hours')
    ap.add_argument('--output-file', type=str, help='Write all results into a single aggregated output file (default: auto-named with timestamp)')
    ap.add_argument('--timestamp-output', action='store_true', help='[Deprecated] Timestamp aggregated output (now default)')
    ap.add_argument('--no-timestamp-output', action='store_true', help='Do not append timestamp to --output-file')
    ap.add_argument('--all-news', action='store_true', help='Disable finance-only filtering (finance-only is default)')
    ap.add_argument('--per-ticker-dir', type=str, help='Directory to store per-ticker files (default: auto timestamped in CWD)')
    ap.add_argument('--no-per-ticker', action='store_true', help='Do not write per-ticker files')
    ap.add_argument('--concurrency', type=int, default=8, help='Global max worker threads for fetching')
    ap.add_argument('--per-host', type=int, default=2, help='Max concurrent requests per host')
    ap.add_argument('--per-host-interval', type=float, default=0.6, help='Minimum seconds between requests to same host')
    ap.add_argument('--no-cleanup', action='store_true', help='Skip cleanup of old files')
    ap.add_argument('--keep-files', type=int, default=2, help='Number of recent files to keep (default: 2)')
    args = ap.parse_args()

    now = dt.datetime.utcnow()
    cutoff = now - dt.timedelta(hours=int(args.hours_back))
    print(f"Filtering articles within the last {int(args.hours_back)} hours (UTC)")

    # Apply networking knobs from CLI
    _GLOBAL_MAX_WORKERS = max(1, int(args.concurrency))
    _PER_HOST_MAX_CONCURRENCY = max(1, int(args.per_host))
    _PER_HOST_MIN_INTERVAL_SEC = max(0.0, float(args.per_host_interval))

    # Resolve tickers input (CLI list or file)
    input_tickers = []
    if args.tickers:
        input_tickers = args.tickers
    elif args.tickers_file:
        try:
            with open(args.tickers_file, 'r', encoding='utf-8') as fh:
                lines = [ln.strip() for ln in fh.readlines()]
                # basic cleanup: ignore empty lines and comments
                input_tickers = [ln for ln in lines if ln and not ln.startswith('#')]
        except Exception as e:
            print(f"Error reading tickers file: {e}")
            sys.exit(1)
    else:
        # Default to local valid_nse_tickers.txt if available
        script_dir = os.path.dirname(os.path.abspath(__file__))
        default_file = os.path.join(script_dir, 'valid_nse_tickers.txt')
        if os.path.exists(default_file):
            try:
                with open(default_file, 'r', encoding='utf-8') as fh:
                    lines = [ln.strip() for ln in fh.readlines()]
                    input_tickers = [ln for ln in lines if ln and not ln.startswith('#')]
                print(f"Using default tickers file: {default_file} ({len(input_tickers)} entries)")
            except Exception as e:
                print(f"Error reading default tickers file: {e}")
                input_tickers = ['RELIANCE', 'TCS']
        else:
            # sensible fallback if no file exists
            input_tickers = ['RELIANCE', 'TCS']

    if args.limit and args.limit > 0:
        input_tickers = input_tickers[: args.limit]

    # Setup per-run timestamp and outputs
    run_stamp = now.strftime('%Y%m%d_%H%M%S')
    # Aggregated output default: write into centralized aggregates dir
    aggregate_path = args.output_file
    # Decide target directory for aggregate file
    if aggregate_path:
        provided_dir = os.path.dirname(aggregate_path)
        base, ext = os.path.splitext(os.path.basename(aggregate_path))
        if not ext:
            ext = ".txt"
        out_dir = provided_dir or _AGGREGATES_DIR
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            pass
        append_stamp = not getattr(args, 'no_timestamp_output', False)
        if getattr(args, 'timestamp_output', False):
            append_stamp = True
        fname = f"{base}_{run_stamp}{ext}" if append_stamp else f"{base}{ext}"
        aggregate_path = os.path.join(out_dir, fname)
    else:
        out_dir = _AGGREGATES_DIR
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception:
            pass
        aggregate_path = os.path.join(out_dir, f"aggregated_full_articles_{int(args.hours_back)}h_{run_stamp}.txt")
    # Create aggregated file header
    try:
        with open(aggregate_path, 'w', encoding='utf-8') as agg:
            agg.write("Full Article Fetch - Aggregated Run\n")
            agg.write("=" * 100 + "\n")
            agg.write(f"Run UTC: {now.isoformat()}\n")
            agg.write(f"Hours back: {int(args.hours_back)}\n")
            agg.write(f"Publishers-only: {bool(args.publishers_only)}\n")
            agg.write(f"Sources: {', '.join(args.sources or [])}\n")
            agg.write(f"Tickers planned: {len(input_tickers)}\n")
            agg.write("=" * 100 + "\n\n")
    except Exception as e:
        print(f"Error creating aggregate file: {e}")
        aggregate_path = None

    # Setup per-ticker directory unless disabled
    mirror_dir = None
    if not args.no_per_ticker:
        if args.per_ticker_dir:
            # If a directory path is provided, respect absolute paths; otherwise place under NEWS_RUNS_DIR
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

    for ticker in input_tickers:
        try:
            items = fetch_rss_items(ticker, args.sources, publishers_only=bool(args.publishers_only))
            # Keep within timeframe and from preferred sources if specified
            fresh = []
            for title, link, source, pubdt in items:
                if pubdt is None:
                    continue
                # Treat pubDate as UTC (Google News)
                if pubdt < cutoff:
                    continue
                # If publishers-only, ensure link already matches preferred domains
                if args.publishers_only and args.sources:
                    host = urllib.parse.urlparse(link).netloc.lower()
                    if not any(dom.lower() in host for dom in args.sources):
                        continue
                # Finance-only filtering (default). Check both URL and source
                if not args.all_news:
                    is_financial = is_financial_url(link)
                    # Also check if source is from a trusted financial domain
                    if not is_financial and source:
                        source_lower = source.lower()
                        is_financial = any(domain in source_lower for domain in TRUSTED_FINANCE_DOMAINS)
                    if not is_financial:
                        continue
                fresh.append((title, link, source, pubdt))

            if not fresh:
                print(f"[{ticker}] No fresh items in last {int(args.hours_back)}h")
                if aggregate_path:
                    with open(aggregate_path, 'a', encoding='utf-8') as agg:
                        agg.write(f"Full Article Fetch Test - {ticker}\n")
                        agg.write("=" * 80 + "\n\n")
                        agg.write(f"(no fresh items in last {int(args.hours_back)}h)\n\n")
                continue

            outfile = save_articles(ticker, fresh, args.max_articles, [], output_file=aggregate_path, mirror_dir=mirror_dir, run_timestamp=run_stamp)
            if aggregate_path:
                print(f"[{ticker}] Appended to: {aggregate_path}")
            else:
                print(f"[{ticker}] Saved full articles to: {outfile}")
            # brief pause to be polite
            time.sleep(0.8)
        except Exception as e:
            print(f"[{ticker}] Error: {e}")

    # Clean up old files at the end
    if not args.no_cleanup:
        try:
            cleanup_old_files(aggregate_path, max_keep=args.keep_files)
        except Exception as e:
            print(f"[WARN] Cleanup failed: {e}")


if __name__ == '__main__':
    main()
