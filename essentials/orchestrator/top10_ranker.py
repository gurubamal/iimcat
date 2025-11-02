#!/usr/bin/env python3
from __future__ import annotations

import argparse
import math
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple

from orchestrator.config import BASE_DIR, OUTPUTS_DIR, AGGREGATES_DIR, load_config, load_entities


AGG_HEADER_RE = re.compile(r"^Full Article Fetch Test -\s*(?P<ticker>[A-Za-z0-9_.\-]+)\s*$")
TITLE_RE = re.compile(r"^Title\s*:\s*(?P<val>.+?)\s*$")
SOURCE_RE = re.compile(r"^Source\s*:\s*(?P<val>.+?)\s*$")
PUBLISHED_RE = re.compile(r"^Published:\s*(?P<val>.+?)\s*$")
URL_RE = re.compile(r"^URL\s*:\s*(?P<val>.+?)\s*$")
SEP_RE = re.compile(r"^-{5,}\s*$")

POSITIVE_CUES = [
    r"\bloa\b", r"letter of award", r"order\b", r"contract\b", r"mou\b", r"pact\b",
    r"acquisition|merger|buyout|stake (?:buy|sale)|joint venture|\bjv\b",
    r"ipo\b|listing|fpo|qip|fundraise|funding|rights issue",
    r"approval|nod|clearance|sebi|cabinet|regulator|usfda",
    r"commission|commissioning|commissions|inaugurat|launch|unveil",
    r"capacity|\bmw\b|\bgw\b|plant|greenfield|brownfield|expansion|de-bottleneck",
    r"profit|ebitda|margin|guidance|upgrade|outlook|beat|surpass",
    r"invest|capex|crore|cr\b|bn\b|billion|lakh|million|restructur",
]

NEGATIVE_CUES = [
    r"downgrade|cut (?:rating|target)|miss(?:ed)?|below estimates|profit warning",
    r"loss\b|losses|penalty|fine|raid|probe|ban|halt|fraud|scam",
    r"strike|shutdown|outage|fire|accident|blast|fatal|death|layoff",
    r"delay|postpone|postponement|defer|deferred",
]


def parse_aggregated_file(path: str) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    cur_ticker = None
    cur_title = None
    cur_source = None
    cur_published = None
    cur_url = None
    body_lines: List[str] = []
    in_body = False

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.rstrip("\n")

            mhead = AGG_HEADER_RE.match(line)
            if mhead:
                # flush previous article if any
                if cur_ticker and cur_title and body_lines:
                    items.append({
                        'ticker': cur_ticker,
                        'title': cur_title,
                        'source': cur_source or '',
                        'published': cur_published or '',
                        'url': cur_url or '',
                        'body': '\n'.join(body_lines).strip(),
                    })
                cur_ticker = (mhead.group('ticker') or '').strip()
                cur_title = None; cur_source = None; cur_published = None; cur_url = None
                body_lines = []
                in_body = False
                continue

            mt = TITLE_RE.match(line)
            if mt:
                # flush previous
                if cur_ticker and cur_title and body_lines:
                    items.append({
                        'ticker': cur_ticker,
                        'title': cur_title,
                        'source': cur_source or '',
                        'published': cur_published or '',
                        'url': cur_url or '',
                        'body': '\n'.join(body_lines).strip(),
                    })
                cur_title = mt.group('val').strip()
                cur_source = None; cur_published = None; cur_url = None
                body_lines = []
                in_body = False
                continue

            ms = SOURCE_RE.match(line)
            if ms:
                cur_source = ms.group('val').strip()
                continue

            mp = PUBLISHED_RE.match(line)
            if mp:
                cur_published = mp.group('val').strip()
                continue

            mu = URL_RE.match(line)
            if mu:
                cur_url = mu.group('val').strip()
                continue

            if SEP_RE.match(line):
                in_body = True
                body_lines = []
                continue

            if in_body:
                body_lines.append(line)

    # flush last article
    if cur_ticker and cur_title and body_lines:
        items.append({
            'ticker': cur_ticker,
            'title': cur_title,
            'source': cur_source or '',
            'published': cur_published or '',
            'url': cur_url or '',
            'body': '\n'.join(body_lines).strip(),
        })
    return items


def hours_ago(iso_like: str) -> float:
    try:
        dt = datetime.fromisoformat(iso_like.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return max(0.0, (now - dt).total_seconds() / 3600.0)
    except Exception:
        return 9999.0


def recency_decay(hours_back: float, half_life: float) -> float:
    if half_life <= 0:
        return 1.0
    return math.exp(-math.log(2) * (hours_back / half_life))


def domain_weight(src: str) -> float:
    if not src:
        return 1.0
    src_l = src.lower()
    weights = {
        'reuters.com': 1.5,
        'bloomberg.com': 1.6,
        'economictimes.indiatimes.com': 1.4,
        'livemint.com': 1.4,
        'moneycontrol.com': 1.3,
        'business-standard.com': 1.4,
        'thehindubusinessline.com': 1.3,
        'financialexpress.com': 1.2,
        'cnbctv18.com': 1.2,
        'businesstoday.in': 1.1,
    }
    for dom, w in weights.items():
        if dom in src_l:
            return w
    return 1.0


INST_CUES_RE = re.compile(r"\b(FII|FPI|DII|mutual fund|institutional|QIB|anchor investor|AIF|block deal|bulk deal)s?\b", re.I)
CIRCUIT_LOWER_RE = re.compile(r"\blower circuit(s)?\b", re.I)
CIRCUIT_UPPER_RE = re.compile(r"\bupper circuit(s)?\b", re.I)
LIVE_UPDATES_RE = re.compile(r"(live updates|share price live)", re.I)

_STOPWORDS = {
    'limited','ltd','inc','co','company','industries','industry','india','the','and','&','private','pvt','corp','corporation','plc','group','science','sciences','pharma','pharmaceuticals','bank','financial','finance','services','technology','technologies','global','intl','international'
}

def _tokenize(text: str) -> List[str]:
    s = re.sub(r"[^a-z0-9\s]"," ", (text or '').lower())
    toks = [t for t in s.split() if t and t not in _STOPWORDS and len(t) > 1]
    return toks


def compute_article_score(title: str, body: str, source: str, published: str, half_life: float = 72.0) -> float:
    text = f"{title}\n{body}".lower()
    score = 0.0
    pos_hits = 0
    for pat in POSITIVE_CUES:
        if re.search(pat, text):
            score += 2.0
            pos_hits += 1
    for pat in NEGATIVE_CUES:
        if re.search(pat, text):
            score -= 2.5
    # magnitude cues
    if re.search(r"\b\d+\s*(mw|gw)\b", text):
        score += 1.5
    if re.search(r"(₹|rs\.?|crore|cr\b|billion|bn\b|lakh)", text):
        score += 1.0
    if re.search(r"\b\d+%\b", text):
        score += 0.5
    # length hint
    if len(body.split()) > 300:
        score += 0.5
    # If no positive financial cues, treat as non-financial news -> discard
    if pos_hits == 0:
        return 0.0

    # Context penalty: fund/PE references without listed entity hints
    if re.search(r"\bfund(s)?\b", text) and not re.search(r"tyre|tyres|hospital|hospitals|ltd|limited|industr|company|bank", text):
        score *= 0.7

    # Institutional cues and circuits (small boosts)
    cfg = load_config()
    fw = cfg.get("feature_weights", {}) or {}
    if INST_CUES_RE.search(text):
        score *= (1.0 + float(fw.get("inst_cues", 0.0)))
    # circuits
    circ = 0.0
    if CIRCUIT_LOWER_RE.search(text):
        circ += float(fw.get("circuit_lower", 0.0))
    if CIRCUIT_UPPER_RE.search(text):
        circ += float(fw.get("circuit_upper", 0.0))
    score *= (1.0 + max(-0.02, min(0.02, circ)))

    # live updates penalty (hard -30%)
    if LIVE_UPDATES_RE.search(title):
        score *= 0.7

    # Source & recency
    w = domain_weight(source)
    decay = recency_decay(hours_ago(published) if published else 9999.0, half_life)
    return score * w * decay


def find_aggregated(days: int) -> List[str]:
    cut = datetime.now().timestamp() - (days * 86400)
    out: List[Tuple[float, str]] = []
    for root in (BASE_DIR, AGGREGATES_DIR):
        try:
            for name in os.listdir(root):
                if name.startswith("aggregated_full_articles_") and name.endswith(".txt"):
                    p = os.path.join(root, name)
                    try:
                        mt = os.path.getmtime(p)
                        if mt >= cut:
                            out.append((mt, p))
                    except Exception:
                        continue
        except Exception:
            pass
    out.sort(reverse=True)
    return [p for _, p in out]


def main() -> None:
    ap = argparse.ArgumentParser(description="Rank stocks by top-10 financial news over last N days/hours")
    ap.add_argument("--days", type=int, default=30, help="Look back window in days (default: 30). Ignored if --hours is set.")
    ap.add_argument("--hours", type=int, default=None, help="Limit to articles within last N hours (filters inside aggregated files)")
    ap.add_argument("--top", type=int, default=50, help="Top N tickers to show (default: 50)")
    ap.add_argument("--export", action="store_true", help="Export CSV to outputs/")
    args = ap.parse_args()

    files = find_aggregated(args.days)
    if not files:
        print("[ERROR] No aggregated_full_articles_* files found in window. Fetch news first (collector).")
        return
    print(f"Using {len(files)} aggregated file(s) in last {args.days} days:")
    for p in files[:5]:
        print(f" - {os.path.basename(p)}")

    articles: List[Dict[str, Any]] = []
    for p in files:
        try:
            arts = parse_aggregated_file(p)
            if args.hours is not None:
                arts = [a for a in arts if (a.get('published') and hours_ago(a.get('published')) <= float(args.hours))]
            articles.extend(arts)
        except Exception as e:
            print(f"[warn] parse failed for {os.path.basename(p)}: {e}")

    if args.hours is not None and not articles:
        print(f"[info] No articles found within last {args.hours} hours. Widening to 24 hours for this run.")
        for p in files:
            try:
                arts = parse_aggregated_file(p)
                arts = [a for a in arts if (a.get('published') and hours_ago(a.get('published')) <= 24.0)]
                articles.extend(arts)
            except Exception:
                continue
    if args.hours is not None and not articles:
        print("[info] Still empty at 24h. Widening to 48 hours.")
        for p in files:
            try:
                arts = parse_aggregated_file(p)
                arts = [a for a in arts if (a.get('published') and hours_ago(a.get('published')) <= 48.0)]
                articles.extend(arts)
            except Exception:
                continue

    # Load valid NSE tickers (restrict ranking to known symbols)
    valid: set[str] = set()
    try:
        with open(os.path.join(BASE_DIR, 'valid_nse_tickers.txt'), 'r', encoding='utf-8') as vf:
            for line in vf:
                t = line.strip().upper()
                if t:
                    valid.add(t)
    except Exception:
        valid = set()

    # Score articles and group per ticker
    per_ticker: Dict[str, List[Tuple[float, Dict[str, Any]]]] = {}
    entities = load_entities()
    for it in articles:
        t = (it.get('ticker') or '').split('.')[0].upper()
        if valid and t not in valid:
            continue
        s = compute_article_score(it.get('title') or '', it.get('body') or '', it.get('source') or '', it.get('published') or '')
        per_ticker.setdefault(t, []).append((s, it))

    ranking: List[Tuple[float, str, int, Dict[str, Any]]] = []
    for t, lst in per_ticker.items():
        # Filter non-financial (score<=0) and deduplicate identical titles
        seen_titles: set[str] = set()
        filtered: List[Tuple[float, Dict[str, Any]]] = []
        for s, it in sorted(lst, key=lambda x: x[0], reverse=True):
            if s <= 0:
                continue
            title_key = (it.get('title') or '').strip().lower()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            # Entity disambiguation penalties
            ent = entities.get(t, {}) if isinstance(entities, dict) else {}
            if ent:
                tx = f"{(it.get('title') or '')} \n {(it.get('body') or '')}".lower()
                excl = ent.get('exclude_phrases', []) or []
                if any(ex.lower() in tx for ex in excl):
                    s *= 0.5
                req = ent.get('require_any', []) or []
                if req and not any(kw.lower() in tx for kw in req):
                    s *= 0.6
            # Dynamic precision based on company tokens if available via title tokens overlap
            title_toks = set(_tokenize(it.get('title') or ''))
            # If no overlap with ticker tokens and generic fund context, penalize
            if title_toks and (t.lower() not in title_toks) and re.search(r"\b(fund|funds|global management|private equity|pe firm)\b", (it.get('title') or '').lower()):
                s *= 0.7
            filtered.append((s, it))
        lst = filtered
        top10 = lst[:10]
        tot = sum(s for s, _ in top10)
        best_it = top10[0][1] if top10 else {'title': '', 'source': ''}
        ranking.append((tot, t, len(top10), best_it))

    ranking.sort(reverse=True, key=lambda x: x[0])

    # Print
    print("\nTop picks by top-10 financial news (sum of scores):")
    for i, (tot, t, n, best) in enumerate(ranking[:args.top], 1):
        title = (best.get('title') or '')[:100]
        src = best.get('source') or 'n/a'
        print(f"{i:2d}. {t:<12} total={tot:6.2f} news={n:2d} - {title} ({src})")

    # Export
    if args.export:
        try:
            os.makedirs(OUTPUTS_DIR, exist_ok=True)
            out = os.path.join(OUTPUTS_DIR, f"top10_news_rank_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            import csv
            with open(out, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(["rank", "ticker", "total_score", "news_count", "best_title", "best_source"])
                for i, (tot, t, n, best) in enumerate(ranking[:args.top], 1):
                    w.writerow([i, t, f"{tot:.3f}", n, best.get('title') or '', best.get('source') or ''])
            print(f"\nSaved CSV: {out}")
        except Exception as e:
            print(f"[warn] export failed: {e}")


if __name__ == "__main__":
    main()
