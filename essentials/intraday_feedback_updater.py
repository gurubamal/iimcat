#!/usr/bin/env python3
"""
Intraday feedback updater for EXIT AI.

Purpose
- Pull 1m/5m intraday prices for top-3 tickers (from latest realtime CSV
  or provided file), compare expected direction vs actual move, and apply
  a small configuration nudge via update_exit_ai_config.py.

Network usage
- Uses yfinance (Yahoo) in a polite, low-rate, sequential way (3 symbols)
  to avoid rate limits or IP blocking.

Usage examples
  python3 intraday_feedback_updater.py --csv realtime_exit_ai_results_2025-11-02_09-01-39_codex.csv --interval 1m --window 120
  python3 intraday_feedback_updater.py --tickers SAGILITY WORTH BHEL --interval 5m --window 240
  python3 intraday_feedback_updater.py --tickers-file exit.check.txt --interval 1m --window 90

Output
- ai_feedback_simulation.json (consumed by update_exit_ai_config.py)
"""

from __future__ import annotations
import argparse
import csv
import glob
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


AI_FEEDBACK_FILE = Path('ai_feedback_simulation.json')


@dataclass
class TopRec:
    ticker: str
    action: str   # IMMEDIATE_EXIT | MONITOR | HOLD (exit system)


def _infer_latest_csv() -> Optional[str]:
    files = sorted(glob.glob('realtime_exit_ai_results_*_*.csv'))
    return files[-1] if files else None


def _read_top3_from_csv(path: str) -> List[TopRec]:
    rows = []
    with open(path, 'r', newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            rows.append(row)
    # Already sorted by exit_urgency_score in generator; if not, sort
    try:
        rows.sort(key=lambda x: float(x.get('exit_urgency_score', 0.0)), reverse=True)
    except Exception:
        pass
    out = []
    for row in rows[:3]:
        t = (row.get('ticker') or '').strip().upper()
        a = (row.get('exit_recommendation') or '').strip().upper() or 'MONITOR'
        if t:
            out.append(TopRec(ticker=t, action=a))
    return out


def _read_first3_from_file(path: str) -> List[TopRec]:
    out = []
    with open(path, 'r') as f:
        for line in f:
            s = line.strip().upper()
            if s and not s.startswith('#'):
                out.append(TopRec(ticker=s, action='MONITOR'))
            if len(out) >= 3:
                break
    return out


def _yf_symbol(sym: str) -> List[str]:
    # Try NSE then BSE if no suffix
    if '.' in sym:
        return [sym]
    return [f"{sym}.NS", f"{sym}.BO"]


def _get_intraday_change_pct(ticker: str, interval: str, window: int) -> Optional[float]:
    try:
        import yfinance as yf  # network needed
    except Exception as e:
        print(f"❌ yfinance not available: {e}", file=sys.stderr)
        return None

    # Use 1d period with minute bars; compute change vs today's first bar
    for s in _yf_symbol(ticker):
        try:
            df = yf.download(s, period='1d', interval=interval, progress=False, auto_adjust=False, prepost=False, threads=False)
            if df is None or df.empty:
                continue
            # If window is specified, trim to last N minutes/bars
            if window and len(df) > window:
                df = df.tail(window)
            opens = df['Open']
            closes = df['Close']
            if opens.empty or closes.empty:
                continue
            first = float(opens.iloc[0])
            last = float(closes.iloc[-1])
            if first <= 0:
                continue
            pct = (last - first) / first * 100.0
            return pct
        except Exception as e:
            # Try next suffix
            continue
    return None


def _map_exit_action_to_expectation(action: str) -> str:
    # For exit system, IMMEDIATE_EXIT expects negative move; HOLD expects flat/pos
    a = (action or '').upper()
    if a == 'IMMEDIATE_EXIT':
        return 'SELL'
    if a == 'MONITOR':
        return 'HOLD'
    if a == 'HOLD':
        return 'HOLD'
    return 'HOLD'


def main() -> int:
    p = argparse.ArgumentParser(description='Intraday feedback updater for EXIT AI')
    p.add_argument('--csv', help='CSV produced by realtime_exit_ai_analyzer')
    p.add_argument('--tickers', nargs='*', help='Explicit tickers (use top-3 order)')
    p.add_argument('--tickers-file', help='File with tickers; uses first 3')
    p.add_argument('--interval', default='5m', choices=['1m','2m','5m','15m'])
    p.add_argument('--window', type=int, default=240, help='Number of recent bars to consider')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    top: List[TopRec] = []
    if args.csv:
        top = _read_top3_from_csv(args.csv)
    elif args.tickers:
        top = [TopRec(t, 'MONITOR') for t in args.tickers[:3]]
    elif args.tickers_file:
        top = _read_first3_from_file(args.tickers_file)
    else:
        latest = _infer_latest_csv()
        if latest:
            top = _read_top3_from_csv(latest)

    if not top:
        print('❌ No tickers found for intraday feedback', file=sys.stderr)
        return 1

    entries = []
    for rec in top[:3]:
        pct = _get_intraday_change_pct(rec.ticker, args.interval, args.window)
        if pct is None:
            print(f"⚠️  Could not fetch intraday for {rec.ticker}", file=sys.stderr)
            continue
        expected = _map_exit_action_to_expectation(rec.action)
        entries.append({
            'ticker': rec.ticker,
            'initial_action': expected,  # SELL/HOLD
            'change_pct': round(pct, 3)
        })
        print(f"• {rec.ticker}: {pct:+.2f}% vs action={rec.action} -> expected={expected}")

    if not entries:
        print('❌ No intraday data fetched; aborting feedback.', file=sys.stderr)
        return 2

    payload = {
        'asof': datetime.now(timezone.utc).isoformat(),
        'entries': entries,
    }
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return 0

    AI_FEEDBACK_FILE.write_text(json.dumps(payload, indent=2))
    print(f"✅ Wrote {AI_FEEDBACK_FILE}")

    # Apply config update
    try:
        import subprocess
        subprocess.run(['python3', 'update_exit_ai_config.py'], check=False)
    except Exception:
        pass
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
