#!/usr/bin/env python3
"""
Magnitude × Intensity × Timing (MIT) ranking for latest AI news screen.

Inputs (preferred):
  - outputs/ai_adjusted_top*.csv (latest)
Fallback:
  - outputs/all_news_screen.csv (if present)

Outputs:
  - outputs/mit_rank_top25_YYYYMMDD_HHMMSS.csv
  - Prints Top 10 with breakdown: M, I, T, total score, and reason

Notes:
  - Attempts yfinance OHLCV batch fetch for Timing; falls back to heuristic when rate-limited.
  - Uses orchestrator/config.py for event/source weighting learned from context.
"""

from __future__ import annotations

import csv
import glob
import math
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any


# ---------- Utilities ----------

def latest_ai_csv() -> str | None:
    # Look in both base dir and outputs/, pick the most recently modified
    cands = []
    cands.extend(glob.glob('ai_adjusted_top*.csv'))
    cands.extend(glob.glob(os.path.join('outputs', 'ai_adjusted_top*.csv')))
    if not cands:
        return None
    try:
        cands.sort(key=lambda p: os.path.getmtime(p))
    except Exception:
        cands.sort()
    return cands[-1]


def load_rows(csv_path: str) -> List[Dict[str, str]]:
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        rdr = csv.DictReader(f)
        return [r for r in rdr]


def domain_of(src: str) -> str:
    s = (src or '').lower().strip()
    return s


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def normalize_amt_cr(amt_cr: float) -> float:
    # Normalize 0..1 using log scaling up to ~5000 Cr
    if amt_cr <= 0:
        return 0.0
    return clamp(math.log10(1.0 + amt_cr) / math.log10(1.0 + 5000.0), 0.0, 1.0)


def normalize_vs_mcap_cr(amt_cr: float, mcap_cr: float) -> float:
    """Normalize news magnitude relative to company size.
    Uses percent-of-market-cap with log scaling to 0..1.
    E.g., if news is ~1% of mcap -> small, 10% -> high.
    """
    if amt_cr <= 0 or mcap_cr <= 0:
        return 0.0
    perc = 100.0 * (amt_cr / max(1.0, mcap_cr))
    # Map 0..100% -> 0..1 with log scaling
    return clamp(math.log10(1.0 + perc) / math.log10(1.0 + 100.0), 0.0, 1.0)


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
    return 0.35  # General


def listicle_penalty(title: str) -> float:
    t = (title or '').lower()
    if re.search(r'(stocks? to watch|in focus|live updates)', t):
        return 0.8
    return 1.0


def try_batch_yf(tickers: List[str]) -> Dict[str, Tuple[float | None, float | None]]:
    """Return {ticker: (pct_change_today, vol_ratio_20d)} or empty on failure.
    Tickers should be symbols without suffix.
    """
    try:
        import yfinance as yf
        import pandas as pd  # noqa: F401
    except Exception:
        return {}
    # Map to .NS
    sym_map = {t: (t if t.endswith('.NS') else f'{t}.NS') for t in tickers}
    try:
        data = yf.download(list(sym_map.values()), period='2mo', interval='1d', progress=False, auto_adjust=False, group_by='ticker', threads=False)
    except Exception:
        return {}
    out: Dict[str, Tuple[float | None, float | None]] = {}
    for t, yfs in sym_map.items():
        try:
            if yfs not in data or data[yfs] is None or data[yfs].empty or len(data[yfs]) < 2:
                out[t] = (None, None); continue
            df = data[yfs].dropna()
            last = df.iloc[-1]; prev = df.iloc[-2]
            if float(prev['Close']) == 0:
                pct = None
            else:
                pct = (float(last['Close']) - float(prev['Close'])) / float(prev['Close']) * 100.0
            vol20 = float(df['Volume'].iloc[:-1].tail(20).mean() or 0.0)
            vratio = (float(last['Volume']) / vol20) if vol20 > 0 else None
            out[t] = (pct, vratio)
        except Exception:
            out[t] = (None, None)
    return out


def timing_score(ev: str, has_price: float | None, vol_ratio: float | None) -> float:
    # Price/volume present: combine
    if has_price is not None and vol_ratio is not None:
        # positive change emphasized, volume up emphasized
        p = clamp(max(0.0, has_price) / 5.0, 0.0, 1.0)  # 0..1 around +5%
        v = clamp((min(vol_ratio, 3.0) - 1.0) / 2.0, 0.0, 1.0)  # 1x->0, 3x->1
        return clamp(0.5 * p + 0.5 * v, 0.0, 1.0)
    # Heuristic fallback: immediacy by event type
    e = event_baseline(ev)
    # Map baseline [0.35..0.8] -> timing [0.4..0.9]
    return clamp(0.2 + e * 0.85, 0.4, 0.9)


def main() -> None:
    # Load context-driven config for event/source weights
    try:
        from orchestrator.config import load_config
        cfg = load_config()
    except Exception:
        cfg = {}
    src_bonus: Dict[str, float] = cfg.get('source_bonus', {}) or {}
    ev_bonus: Dict[str, float] = cfg.get('event_bonus', {}) or {}

    csv_path = latest_ai_csv()
    if not csv_path:
        fallback = os.path.join('outputs', 'all_news_screen.csv')
        if os.path.exists(fallback):
            csv_path = fallback
        else:
            print('ERROR: No ai_adjusted_top*.csv or all_news_screen.csv found. Run ranking first.')
            return

    rows = load_rows(csv_path)
    # Take a reasonable working set (top 200)
    rows = rows[:200]

    # Optional: load market cap map if available (sec_list.csv)
    mcap_map: Dict[str, float] = {}
    try:
        # If sec_list.csv has MarketCapCr column, load it
        with open('sec_list.csv', 'r', encoding='utf-8', errors='ignore') as f:
            import csv as _csv
            rdr = _csv.DictReader(f)
            for rr in rdr:
                t = (rr.get('Symbol') or '').strip().upper()
                mc = rr.get('MarketCapCr') or rr.get('MktCapCr') or rr.get('MarketCap')
                if not t or mc is None:
                    continue
                try:
                    mcap_val = float(str(mc).replace(',', '').strip())
                except Exception:
                    continue
                if mcap_val > 0:
                    mcap_map[t] = mcap_val
    except Exception:
        mcap_map = {}

    # Prepare batch yfinance timing for top 50 tickers (if available)
    tickers = [ (r.get('ticker') or '').strip().upper() for r in rows[:50] if (r.get('ticker') or '').strip() ]
    yf_map = try_batch_yf(tickers)

    # Fill missing market caps via yfinance fast_info (best-effort)
    try:
        import yfinance as yf  # type: ignore
        need_caps = [ (r.get('ticker') or '').strip().upper() for r in rows if (r.get('ticker') or '').strip() and (r.get('ticker') or '').strip().upper() not in mcap_map ]
        # Deduplicate preserving order and cap to 80 to avoid rate limits
        seen_caps = set()
        qcaps: list[str] = []
        for t in need_caps:
            if t not in seen_caps:
                seen_caps.add(t)
                qcaps.append(t)
            if len(qcaps) >= 80:
                break
        for t in qcaps:
            sym = t if '.' in t else f"{t}.NS"
            try:
                ti = yf.Ticker(sym)
                fi = getattr(ti, 'fast_info', None)
                mc = None
                if fi:
                    if hasattr(fi, 'market_cap'):
                        mc = getattr(fi, 'market_cap')
                    elif isinstance(fi, dict):
                        mc = fi.get('market_cap') or fi.get('marketCap')
                if mc is None:
                    info = getattr(ti, 'info', {}) or {}
                    mc = info.get('marketCap')
                if mc and float(mc) > 0:
                    mcap_map[t] = float(mc) / 1e7  # INR to Cr (approx)
            except Exception:
                continue
    except Exception:
        pass

    scored: List[Tuple[float, Dict[str, Any]]] = []
    for r in rows:
        tkr = (r.get('ticker') or '').strip().upper()
        title = (r.get('top_title') or '').strip()
        ev = (r.get('event_type') or '').strip()
        src = domain_of(r.get('top_source') or '')
        has_word = str(r.get('has_word') or '').strip().lower() in ('1', 'true', 'yes')
        try:
            dups = int(r.get('dups') or '1')
        except Exception:
            dups = 1
        try:
            amt_cr = float(r.get('amt_cr') or 0.0)
        except Exception:
            amt_cr = 0.0

        # Magnitude: combine absolute and relative-to-mcap when mcap is known
        m_norm_abs = normalize_amt_cr(amt_cr)
        m_norm_rel = normalize_vs_mcap_cr(amt_cr, float(mcap_map.get(tkr, 0.0))) if tkr in mcap_map else 0.0
        base_ev_mag = event_baseline(ev)
        if m_norm_rel > 0:
            # emphasize relative size for small/mid caps
            magnitude = clamp(0.5 * m_norm_abs + 0.5 * m_norm_rel + 0.2 * base_ev_mag, 0.0, 1.0)
        else:
            magnitude = clamp(0.6 * m_norm_abs + 0.4 * base_ev_mag, 0.0, 1.0)

        # Intensity
        # Event bonus from context (scaled)
        e_bonus = 0.0
        try:
            e_bonus = float(ev_bonus.get(ev, 0.0))
        except Exception:
            e_bonus = 0.0
        e_factor = 1.0 + clamp(e_bonus, 0.0, 0.1)
        # Source reliability
        s_boost = 0.0
        for dom, b in src_bonus.items():
            if dom.lower() in src:
                try:
                    s_boost = max(s_boost, float(b))
                except Exception:
                    pass
        s_factor = 1.0 + clamp(s_boost, 0.0, 0.1)
        # Name precision and duplication
        name_factor = 1.0 if has_word else 0.85
        dedup_factor = (1.0 / float(max(1, dups))) ** 0.5
        # Listicle/live penalty
        list_pen = listicle_penalty(title)
        intensity = clamp(base_ev_mag * e_factor * s_factor * name_factor * dedup_factor * list_pen, 0.0, 1.2)

        # Timing
        pct, vr = (None, None)
        if tkr in yf_map:
            pct, vr = yf_map.get(tkr) or (None, None)
        timing = timing_score(ev, pct, vr)

        total = magnitude * intensity * timing
        out = dict(r)
        out['mit_magnitude'] = f"{magnitude:.3f}"
        out['mit_intensity'] = f"{intensity:.3f}"
        out['mit_timing'] = f"{timing:.3f}"
        out['mit_score'] = f"{total:.6f}"
        scored.append((total, out))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [row for _, row in scored[:25]]

    # Write output CSV
    os.makedirs('outputs', exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_csv = os.path.join('outputs', f'mit_rank_top25_{ts}.csv')
    fieldnames = [
        'ticker','company_name','event_type','top_title','top_source','amt_cr','dups','has_word',
        'mit_magnitude','mit_intensity','mit_timing','mit_score'
    ]
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in top:
            w.writerow({k: r.get(k, '') for k in fieldnames})

    # Print Top 10 summary
    print('Top 10 by MIT score:')
    for r in top[:10]:
        print(f"- {r.get('ticker')} | M={r['mit_magnitude']} I={r['mit_intensity']} T={r['mit_timing']} -> {r['mit_score']}\n  {r.get('event_type')}: {r.get('top_title')} ({r.get('top_source')})")
    print(f"\nSaved: {out_csv}")


if __name__ == '__main__':
    main()

