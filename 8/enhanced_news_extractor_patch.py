#!/usr/bin/env python3
"""
Enhanced news extractor fallback used by fetch_full_articles.save_articles().

Design goals:
- No hard dependencies beyond requests, bs4, readability-lxml (all already in repo).
- Be resilient: try multiple strategies and return the longest plausible body.
- Keep it self-contained to avoid circular imports.

Usage:
    from enhanced_news_extractor_patch import enhanced_fetch_article_content
    text = enhanced_fetch_article_content(url)

Returns empty string on failure.
"""
from __future__ import annotations

import re
import json
import time
import random
import urllib.parse
from typing import Optional

import requests
from bs4 import BeautifulSoup
from readability import Document

# Optional extras (used if available; safe to miss)
try:
    import trafilatura  # type: ignore
    HAS_TRAFILATURA = True
except Exception:
    HAS_TRAFILATURA = False

try:
    from pdfminer.high_level import extract_text as pdf_extract_text  # type: ignore
    HAS_PDFMINER = True
except Exception:
    HAS_PDFMINER = False

# Conservative headers
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/123.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'no-cache',
}

_SESS = None

def _session() -> requests.Session:
    global _SESS
    if _SESS is None:
        s = requests.Session()
        s.headers.update(HEADERS)
        _SESS = s
    return _SESS


def _is_pdf_url(url: str) -> bool:
    p = urllib.parse.urlparse(url)
    return (p.path or '').lower().endswith('.pdf')


def _get(url: str, timeout: float = 15.0) -> Optional[requests.Response]:
    try:
        s = _session()
        r = s.get(url, timeout=timeout, allow_redirects=True)
        return r
    except Exception:
        return None


def _text_from_node(node) -> str:
    for el in node.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
        el.decompose()
    return node.get_text(separator=' ', strip=True)


SITE_SELECTORS = [
    'article',
    '[role="main"] article',
    'div[itemprop="articleBody"]',
    'section[itemprop="articleBody"]',
    'div[class*="article"]',
    'div[class*="content"]',
    'section[class*="content"]',
]


def _extract_ld_json_article_body(soup: BeautifulSoup) -> str:
    bodies = []
    for tag in soup.find_all('script', type=lambda v: v and 'ld+json' in v):
        try:
            data = json.loads(tag.string or tag.text or '{}')
        except Exception:
            continue
        # Some pages include a list of JSON-LD objects
        if isinstance(data, list):
            for obj in data:
                if not isinstance(obj, dict):
                    continue
                body = (obj.get('articleBody') or obj.get('description') or '')
                if body and len(body) > 200:
                    bodies.append(body)
        elif isinstance(data, dict):
            body = (data.get('articleBody') or data.get('description') or '')
            if body and len(body) > 200:
                bodies.append(body)
    return max(bodies, key=len) if bodies else ''


def _amp_href(soup: BeautifulSoup, base_url: str) -> Optional[str]:
    link = soup.find('link', rel=lambda v: v and 'amphtml' in v.lower())
    if link and link.get('href'):
        return urllib.parse.urljoin(base_url, link['href'])
    return None


def _try_trafilatura(url: str) -> str:
    if not HAS_TRAFILATURA:
        return ''
    try:
        downloaded = trafilatura.fetch_url(url, no_ssl=True)
        if not downloaded:
            return ''
        text = trafilatura.extract(downloaded, include_comments=False, include_tables=False, favor_recall=True, output_format='txt')
        return (text or '').strip()
    except Exception:
        return ''


def _try_pdf(url: str) -> str:
    if not HAS_PDFMINER:
        return ''
    try:
        r = _get(url, timeout=20)
        if not r or r.status_code != 200:
            return ''
        # Quick check on content-type if present
        ctype = (r.headers.get('content-type') or '').lower()
        if 'pdf' not in ctype and not _is_pdf_url(url):
            return ''
        # Write to temp bytes and let pdfminer parse from bytes via file-like object
        import io
        bio = io.BytesIO(r.content)
        text = pdf_extract_text(bio) or ''
        return text.strip()
    except Exception:
        return ''


def enhanced_fetch_article_content(url: str, max_retries: int = 2) -> str:
    """Robust extractor. Returns full text or empty string.

    Strategy order:
    1) PDF extraction (if URL/content-type indicates PDF)
    2) Trafilatura (if installed)
    3) Site selectors on main page
    4) AMP page selectors
    5) Readability (main then AMP)
    6) JSON-LD articleBody
    """
    if not url:
        return ''

    # 1) PDFs
    if _is_pdf_url(url):
        txt = _try_pdf(url)
        if len(txt) >= 200:
            return txt[:20000]

    # 2) Trafilatura first (fast + good)
    txt = _try_trafilatura(url)
    if len(txt) >= 600:
        return txt[:20000]

    # 3) Fetch base page
    r = _get(url, timeout=15)
    if not r or r.status_code != 200 or not r.text:
        return ''
    base_url = r.url or url
    soup = BeautifulSoup(r.text, 'html.parser')

    # 3a) Try explicit site selectors
    candidates = []
    for sel in SITE_SELECTORS:
        for node in soup.select(sel):
            t = _text_from_node(node)
            if len(t) > 400:
                candidates.append(t)
    if candidates:
        best = max(candidates, key=len)
        if len(best) >= 200:
            return best[:20000]

    # 4) AMP fallback
    amp = _amp_href(soup, base_url)
    if amp:
        r2 = _get(amp, timeout=12)
        if r2 and r2.status_code == 200 and r2.text:
            soup2 = BeautifulSoup(r2.text, 'html.parser')
            cand2 = []
            for sel in SITE_SELECTORS:
                for node in soup2.select(sel):
                    t = _text_from_node(node)
                    if len(t) > 300:
                        cand2.append(t)
            if cand2:
                best2 = max(cand2, key=len)
                if len(best2) >= 200:
                    return best2[:20000]

    # 5) Readability main page
    try:
        doc = Document(r.text)
        soup_r = BeautifulSoup(doc.summary(), 'html.parser')
        t = _text_from_node(soup_r)
        if len(t) >= 200:
            return t[:20000]
    except Exception:
        pass

    # 5b) Readability on AMP if available
    if amp:
        try:
            if not ('r2' in locals() and r2 is not None and r2.status_code == 200):
                r2 = _get(amp, timeout=12)
            if r2 and r2.status_code == 200 and r2.text:
                doc2 = Document(r2.text)
                soup2r = BeautifulSoup(doc2.summary(), 'html.parser')
                t2 = _text_from_node(soup2r)
                if len(t2) >= 200:
                    return t2[:20000]
        except Exception:
            pass

    # 6) JSON-LD articleBody as last resort
    try:
        ld = _extract_ld_json_article_body(soup)
        if len(ld) >= 200:
            return ld[:20000]
    except Exception:
        pass

    # Optional retry once with small delay (pages sometimes render slower)
    if max_retries > 0:
        time.sleep(0.8 + random.uniform(0.0, 0.4))
        return enhanced_fetch_article_content(url, max_retries=max_retries - 1)

    return ''


if __name__ == '__main__':
    # Lightweight self-test on static HTML (no internet required)
    SAMPLE_HTML = '''
    <html><head><title>Test</title></head>
    <body>
      <header>nav</header>
      <article>
        <h1>Title</h1>
        <p>Para 1.</p>
        <p>''' + ('This is content. ' * 50) + '''</p>
      </article>
    </body></html>
    '''
    soup = BeautifulSoup(SAMPLE_HTML, 'html.parser')
    # Simulate selector extraction
    nodes = [n for sel in SITE_SELECTORS for n in soup.select(sel)]
    assert nodes, 'Selector failed to find article'
    text = _text_from_node(nodes[0])
    assert len(text) > 200, 'Extracted text too short in self-test'
    print('Self-test OK (selector path)')
