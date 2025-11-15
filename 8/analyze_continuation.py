#!/usr/bin/env python3
"""
Compute today's price change and volume surge for a set of NSE tickers,
and rank likely continuation candidates for tomorrow.

Usage:
  python analyze_continuation.py TICKER [TICKER...]

Notes:
  - Tickers should be NSE symbols without suffix (e.g., RELIANCE, ITC).
  - Uses yfinance daily data (last 2 months) to compute:
      * pct_change = (Close_today - Close_prev) / Close_prev
      * vol_ratio = Volume_today / 20-day average volume (excluding today)
      * score = max(0, pct_change%) * log1p(max(0, vol_ratio))
"""

from __future__ import annotations

import sys
import math
from typing import List, Dict

def main(args: List[str]) -> None:
    try:
        import yfinance as yf
        import pandas as pd  # noqa
    except Exception as e:
        print(f"ERROR: yfinance not available: {e}")
        sys.exit(1)

    if not args:
        args = [
            'ADANIENT','HCLTECH','MARUTI','SPICEJET','RECLTD','NTPC','SUZLON',
        ]

    # Build NSE-suffixed list and batch download to reduce rate hits
    syms = []
    norm_map: Dict[str, str] = {}
    for sym0 in args:
        sym = (sym0 or '').strip().upper()
        yf_sym = sym if sym.endswith('.NS') else f"{sym}.NS"
        syms.append(yf_sym)
        norm_map[yf_sym] = sym

    results: List[Dict[str, object]] = []
    try:
        data = yf.download(syms, period='2mo', interval='1d', progress=False, auto_adjust=False, group_by='ticker', threads=False)
    except Exception as e:
        # Fallback: mark all as missing
        for yf_sym in syms:
            results.append({'ticker': norm_map[yf_sym], 'error': str(e)})
        data = None

    for yf_sym in syms:
        sym = norm_map[yf_sym]
        try:
            if data is None or yf_sym not in data or data[yf_sym] is None or data[yf_sym].empty or len(data[yf_sym]) < 2:
                results.append({'ticker': sym, 'error': 'no_data'})
                continue
            df = data[yf_sym].dropna()
            last = df.iloc[-1]
            prev = df.iloc[-2]
            if float(prev['Close']) == 0:
                pct = float('nan')
            else:
                pct = (float(last['Close']) - float(prev['Close'])) / float(prev['Close']) * 100.0
            vol20 = float(df['Volume'].iloc[:-1].tail(20).mean() or 0.0)
            vratio = (float(last['Volume']) / vol20) if vol20 > 0 else float('nan')
            green = bool(float(last['Close']) > float(last['Open']))
            score = (max(0.0, pct) * math.log1p(max(0.0, vratio))) if (not math.isnan(pct) and not math.isnan(vratio)) else -1.0
            results.append({
                'ticker': sym,
                'pct': round(pct, 2) if pct == pct else None,
                'vratio': round(vratio, 2) if vratio == vratio else None,
                'green': green,
                'close': round(float(last['Close']), 2),
                'vol': int(last['Volume']),
                'score': round(score, 3) if score == score else -1.0,
            })
        except Exception as e:
            results.append({'ticker': sym, 'error': str(e)})

    ranked = [r for r in results if r.get('score', -1) >= 0]
    ranked.sort(key=lambda x: x['score'], reverse=True)

    print('TICKER,CHANGE%,VOL_RATIO20D,GREEN,CLOSE,VOLUME,SCORE')
    for r in ranked:
        print(f"{r['ticker']},{r.get('pct')},{r.get('vratio')},{r.get('green')},{r.get('close')},{r.get('vol')},{r.get('score')}")

    missing = [r for r in results if r.get('score', -1) < 0]
    if missing:
        print('\nMISSING_OR_ERROR:')
        for m in missing:
            print(f"{m['ticker']}: {m.get('error','no_score')}")

if __name__ == '__main__':
    main(sys.argv[1:])
