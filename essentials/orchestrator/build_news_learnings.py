#!/usr/bin/env python3
"""
Build Top-100 learnings from all available aggregated news, factoring:
- News age (recency)
- Impact (event type + ₹ amount cue)
- Price as of today (live return vs prev close)

Outputs:
- outputs/news_learnings_top100_YYYYMMDD_HHMMSS.csv
- learning/learnings_top100_YYYYMMDD.md (summary)

This script reuses the aggregated parser and news scoring from top10_ranker,
adds impact heuristics and present-day price feedback, and produces a
ranked Top-100 list.
"""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Any

from orchestrator.config import OUTPUTS_DIR, LEARNING_DIR, load_config, BASE_DIR
from orchestrator.top10_ranker import (
    parse_aggregated_file,
    find_aggregated,
    compute_article_score,
    hours_ago,
)
from orchestrator.ranking import parse_amount_crore as parse_amt_cr
from price_eval import evaluate_live


def event_baseline(ev: str) -> float:
    evl = (ev or '').lower()
    if evl.startswith('ipo') or 'listing' in evl:
        return 0.65
    if 'm&a' in evl or 'jv' in evl:
        return 0.7
    if 'order' in evl or 'contract' in evl or 'tender' in evl or 'project' in evl or 'deal' in evl:
        return 0.8
    if 'regulatory' in evl or 'approval' in evl:
        return 0.75
    if 'results' in evl or 'metrics' in evl:
        return 0.55
    if 'block deal' in evl:
        return 0.45
    if 'management' in evl:
        return 0.4
    return 0.35


def classify_event(title: str) -> str:
    t = (title or '').lower()
    if re.search(r"\bipo\b|listing|fpo|qip|rights issue", t):
        return "IPO/listing"
    if re.search(r"acquisit|merger|buyout|joint venture|\bjv\b|stake (?:buy|sale)", t):
        return "M&A/JV"
    if re.search(r"order\b|contract\b|tender|project|deal", t):
        return "Order/contract"
    if re.search(r"approval|usfda|sebi|nod|clearance|regulator", t):
        return "Regulatory"
    if re.search(r"block deal", t):
        return "Block deal"
    if re.search(r"dividend|buyback|payout", t):
        return "Dividend/return"
    if re.search(r"result|profit|ebitda|margin|q[1-4]|quarter|yoy|growth", t):
        return "Results/metrics"
    if re.search(r"appoints|resigns|ceo|cfo", t):
        return "Management"
    return "General"


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def normalize_amt_cr(amt_cr: float) -> float:
    import math
    if amt_cr <= 0:
        return 0.0
    return clamp(math.log10(1.0 + amt_cr) / math.log10(1.0 + 5000.0), 0.0, 1.0)


def load_reliability(db_path: str, tickers: List[str]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    if not os.path.exists(db_path) or not tickers:
        return out
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        q = ",".join(["?"] * len(tickers))
        cur.execute(f"SELECT ticker, reliability_score FROM ticker_stats WHERE ticker IN ({q})", [t.upper() for t in tickers])
        for t, rel in cur.fetchall():
            out[(t or '').upper()] = float(rel or 0.0)
        con.close()
    except Exception:
        return {}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Build Top-100 learnings from news age, impact, and today price")
    ap.add_argument("--days", type=int, default=7, help="Look-back window in days for aggregated files (default: 7)")
    ap.add_argument("--hours", type=int, default=None, help="Filter to articles within last N hours (optional)")
    ap.add_argument("--top", type=int, default=100, help="Top N tickers to include (default: 100)")
    ap.add_argument("--half-life", type=float, default=48.0, help="News half-life in hours for recency decay (default: 48)")
    ap.add_argument("--best-buy-top", type=int, default=25, help="Max Best-Buy-Today candidates to export (default: 25)")
    args = ap.parse_args()

    cfg = load_config()
    src_bonus: Dict[str, float] = cfg.get("source_bonus", {}) or {}

    files = find_aggregated(args.days)
    if not files:
        print("[ERROR] No aggregated_full_articles_* files found. Fetch news first.")
        return
    print(f"Using {len(files)} aggregated file(s) in last {args.days} days.")

    # Parse all articles
    articles: List[Dict[str, Any]] = []
    for p in files:
        try:
            arts = parse_aggregated_file(p)
            if args.hours is not None:
                arts = [a for a in arts if (a.get('published') and hours_ago(a.get('published')) <= float(args.hours))]
            articles.extend(arts)
        except Exception:
            continue
    if not articles:
        print("[INFO] No articles found in window; exiting.")
        return

    # Compute duplicate counts by title for certainty penalty
    dup: Dict[str, int] = {}
    for it in articles:
        t = (it.get('title') or '').strip()
        if t:
            dup[t] = dup.get(t, 0) + 1

    # Group per ticker
    per: Dict[str, List[Tuple[float, Dict[str, Any]]]] = {}
    # Load valid NSE tickers to avoid noise symbols
    valid: set[str] = set()
    try:
        with open(os.path.join(BASE_DIR, 'valid_nse_tickers.txt'), 'r', encoding='utf-8') as vf:
            for line in vf:
                t = line.strip().upper()
                if t:
                    valid.add(t)
    except Exception:
        valid = set()

    for it in articles:
        tk = (it.get('ticker') or '').split('.')[0].upper()
        if valid and tk not in valid:
            continue
        title = it.get('title') or ''
        src = it.get('source') or ''
        published = it.get('published') or ''
        body = it.get('body') or ''
        sc = compute_article_score(title, body, src, published, half_life=args.half_life)
        per.setdefault(tk, []).append((sc, it))

    # Rank per ticker by sum of top-10 article scores
    ranking: List[Tuple[float, str, Dict[str, Any]]] = []
    for tk, lst in per.items():
        lst2 = sorted(lst, key=lambda x: x[0], reverse=True)
        top10 = lst2[:10]
        total = sum(s for s, _ in top10)
        best = top10[0][1] if top10 else {'title': '', 'source': '', 'published': ''}
        ranking.append((total, tk, best))
    ranking.sort(reverse=True, key=lambda x: x[0])

    # Take top N
    ranking = ranking[: args.top]
    tickers = [tk for _, tk, _ in ranking]

    # Live price feedback (best-effort)
    live = evaluate_live([{'ticker': t} for t in tickers])
    lmap: Dict[str, Dict[str, Any]] = { (r.get('ticker') or '').upper(): r for r in live }

    # Reliability (optional)
    db_path = os.path.join(LEARNING_DIR, 'learning.db')
    rel_map = load_reliability(db_path, tickers)

    # Build rows
    rows: List[Dict[str, Any]] = []
    # Heuristics for listicle/live headlines
    LISTICLE_RE = re.compile(r"(stocks? to watch|in focus|live updates|share price live)", re.I)

    best_buy_rows: List[Dict[str, Any]] = []

    for total, tk, best in ranking:
        title = (best.get('title') or '').strip()
        src = (best.get('source') or '').strip()
        pub = best.get('published') or ''
        ev = classify_event(title)
        amt = float(parse_amt_cr(title) or 0.0)
        m_norm = normalize_amt_cr(amt)
        ev_base = event_baseline(ev)
        impact = clamp(0.6 * m_norm + 0.4 * ev_base, 0.0, 1.0)
        age_h = hours_ago(pub) if pub else 9999.0
        has_word = bool(tk and title and re.search(rf"\b{re.escape(tk)}\b", title, re.I))
        # certainty
        name_factor = 1.0 if has_word else 0.85
        dups = dup.get(title, 1)
        dups_factor = (1.0 / float(max(1, dups))) ** 0.5
        s_boost = 0.0
        src_l = src.lower()
        for dom, b in src_bonus.items():
            if dom.lower() in src_l:
                try:
                    s_boost = max(s_boost, float(b))
                except Exception:
                    pass
        src_factor = 1.0 + clamp(s_boost, 0.0, 0.1)
        news_certainty = clamp(ev_base * name_factor * dups_factor * src_factor, 0.0, 1.2)
        rel = float(rel_map.get(tk, 0.0))
        rel_scaled = clamp((rel + 1.0) / 2.0, 0.0, 1.0)
        trust = clamp(0.7 * news_certainty + 0.3 * rel_scaled, 0.0, 1.0)
        lr = lmap.get(tk, {})
        row = {
            'ticker': tk,
            'news_count': len(per.get(tk) or []),
            'total_news_score': f"{total:.3f}",
            'best_title': title,
            'best_source': src,
            'news_age_hours': f"{age_h:.1f}",
            'event_type': ev,
            'amt_cr': f"{amt:.1f}",
            'impact_score': f"{impact:.3f}",
            'news_certainty': f"{news_certainty:.3f}",
            'trust_score': f"{trust:.3f}",
            'live_ret': (f"{float(lr.get('live_ret')):.3f}" if lr.get('live_ret') is not None else ''),
            'asof': lr.get('asof') or '',
        }
        rows.append(row)

        # Best-Buy-Today gating (bullet-proofing)
        reasons: List[str] = []
        eligible = True
        # Recency
        if age_h > 48.0:
            eligible = False; reasons.append('old>48h')
        # Event quality
        if ev not in {"Order/contract", "IPO/listing", "Regulatory"}:
            reasons.append('weak-event')
            # Allow but at higher threshold
        # Headline listicle/live penalty
        if LISTICLE_RE.search(title):
            eligible = False; reasons.append('listicle')
        # Certainty/trust thresholds
        if news_certainty < 0.50:
            eligible = False; reasons.append('low-certainty')
        if trust < 0.45:
            eligible = False; reasons.append('low-trust')
        # Impact threshold
        if impact < 0.25:
            reasons.append('low-impact')
        # Price guardrail (if available): avoid if sharply negative
        try:
            lret = float(lr.get('live_ret')) if lr.get('live_ret') is not None else None
        except Exception:
            lret = None
        if lret is not None and lret < -0.5:
            eligible = False; reasons.append('price-down')

        if eligible:
            bb = dict(row)
            bb['bb_reasons'] = ';'.join(reasons) if reasons else 'meets-thresholds'
            best_buy_rows.append(bb)

    # Export CSV
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_csv = os.path.join(OUTPUTS_DIR, f"news_learnings_top100_{ts}.csv")
    import csv
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=[
            'ticker','news_count','total_news_score','best_title','best_source','news_age_hours',
            'event_type','amt_cr','impact_score','news_certainty','trust_score','live_ret','asof'
        ])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Saved CSV: {out_csv}")

    # Summary MD (top 20)
    os.makedirs(LEARNING_DIR, exist_ok=True)
    out_md = os.path.join(LEARNING_DIR, f"learnings_top100_{ts}.md")
    with open(out_md, 'w', encoding='utf-8') as f:
        f.write(f"# Top-100 News Learnings — {ts}\n\n")
        f.write("Ranked by decayed news score, with impact and live return.\n\n")
        for i, r in enumerate(rows[:20], 1):
            f.write(f"{i:2d}. {r['ticker']:<10} score={r['total_news_score']} age={r['news_age_hours']}h impact={r['impact_score']} live={r['live_ret']}%\n")
            f.write(f"    {r['event_type']}: {r['best_title']} ({r['best_source']})\n")
    print(f"Saved MD: {out_md}")

    # Export Best-Buy-Today candidates (capped)
    if best_buy_rows:
        out_bb = os.path.join(OUTPUTS_DIR, f"best_buy_today_{ts}.csv")
        import csv as _csv
        with open(out_bb, 'w', newline='', encoding='utf-8') as f:
            w = _csv.DictWriter(f, fieldnames=[
                'ticker','news_count','total_news_score','best_title','best_source','news_age_hours',
                'event_type','amt_cr','impact_score','news_certainty','trust_score','live_ret','asof','bb_reasons'
            ])
            w.writeheader()
            for r in best_buy_rows[: args.best_buy_top]:
                w.writerow(r)
        print(f"Saved Best-Buy-Today: {out_bb} ({min(len(best_buy_rows), args.best_buy_top)} items)")


if __name__ == '__main__':
    # Ensure UTF-8 output on Windows consoles
    try:
        import sys
        sys.stdout.reconfigure(encoding='utf-8')  # type: ignore[attr-defined]
    except Exception:
        pass
    main()
