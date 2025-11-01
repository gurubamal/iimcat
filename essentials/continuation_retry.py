#!/usr/bin/env python3
"""
Retry price/volume continuation metrics for the latest AI Top 10.

Steps:
 1) Read latest outputs/ai_adjusted_top*.csv
 2) Take top 10 tickers
 3) Attempt OHLCV fetch via yfinance with backoff (up to ~12 minutes)
 4) Print ranked continuation table by price-change% * log1p(vol_ratio_20D)
"""

from __future__ import annotations

import glob
import os
import time
from typing import List, Dict


def latest_ai_csv() -> str | None:
    cand = sorted(glob.glob(os.path.join('outputs', 'ai_adjusted_top*_.csv')))  # unlikely pattern
    # Fallback robust listing
    cand = sorted(glob.glob(os.path.join('outputs', 'ai_adjusted_top*.csv')))
    return cand[-1] if cand else None


def read_top10(path: str) -> List[str]:
    import csv
    out: List[str] = []
    with open(path, 'r', encoding='utf-8') as f:
        rdr = csv.DictReader(f)
        for row in rdr:
            t = (row.get('ticker') or '').strip().upper()
            if t:
                out.append(t)
            if len(out) >= 10:
                break
    return out


def fetch_continuation(tickers: List[str]) -> List[Dict[str, object]]:
    import yfinance as yf
    import pandas as pd  # noqa: F401
    import math
    syms = [t if t.endswith('.NS') else f"{t}.NS" for t in tickers]
    data = yf.download(syms, period='2mo', interval='1d', progress=False, auto_adjust=False, group_by='ticker', threads=False)
    results: List[Dict[str, object]] = []
    for yf_sym, t in zip(syms, tickers):
        try:
            if yf_sym not in data or data[yf_sym] is None or data[yf_sym].empty or len(data[yf_sym]) < 2:
                results.append({'ticker': t, 'error': 'no_data'})
                continue
            df = data[yf_sym].dropna()
            last = df.iloc[-1]; prev = df.iloc[-2]
            if float(prev['Close']) == 0:
                pct = float('nan')
            else:
                pct = (float(last['Close']) - float(prev['Close'])) / float(prev['Close']) * 100.0
            vol20 = float(df['Volume'].iloc[:-1].tail(20).mean() or 0.0)
            vratio = (float(last['Volume']) / vol20) if vol20 > 0 else float('nan')
            green = bool(float(last['Close']) > float(last['Open']))
            score = (max(0.0, pct) * math.log1p(max(0.0, vratio))) if (pct == pct and vratio == vratio) else -1.0
            results.append({'ticker': t, 'pct': round(pct, 2) if pct == pct else None, 'vratio': round(vratio, 2) if vratio == vratio else None, 'green': green, 'score': round(score, 3) if score == score else -1.0})
        except Exception as e:
            results.append({'ticker': t, 'error': str(e)})
    return results


def main() -> None:
    path = latest_ai_csv()
    if not path:
        print('ERROR: No ai_adjusted_top*.csv found under outputs/. Run ranking first.')
        return
    top = read_top10(path)
    if not top:
        print('ERROR: No tickers found in ranking CSV.')
        return
    deadline = time.time() + 12 * 60  # ~12 minutes
    attempt = 0
    results: List[Dict[str, object]] = []
    while time.time() < deadline:
        attempt += 1
        try:
            results = fetch_continuation(top)
        except Exception as e:
            results = [{'ticker': t, 'error': str(e)} for t in top]
        ok = [r for r in results if r.get('score', -1) >= 0]
        if len(ok) >= max(3, len(top)//2):
            break
        # backoff: 60s, 90s, then 120s steps
        sleep_for = 60 + (attempt - 1) * 30
        print(f"[retry] insufficient data ({len(ok)}/{len(top)} ok). Sleeping {sleep_for}s...")
        time.sleep(sleep_for)

    ok = [r for r in results if r.get('score', -1) >= 0]
    ok.sort(key=lambda x: x['score'], reverse=True)
    print('TICKER,CHANGE%,VOL_RATIO20D,GREEN,SCORE')
    for r in ok:
        print(f"{r['ticker']},{r.get('pct')},{r.get('vratio')},{r.get('green')},{r.get('score')}")
    missing = [r for r in results if r.get('score', -1) < 0]
    if missing:
        print('\nMISSING_OR_ERROR:')
        for m in missing:
            print(f"{m['ticker']}: {m.get('error','no_score')}")


if __name__ == '__main__':
    main()

