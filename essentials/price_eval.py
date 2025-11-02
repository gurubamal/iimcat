#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Tuple


def _parse_aggregated_published(agg_path: str) -> Dict[str, str]:
    """Return map title -> published ISO string (best-effort)."""
    out: Dict[str, str] = {}
    try:
        with open(agg_path, "r", encoding="utf-8", errors="replace") as f:
            cur_title = None
            for raw in f:
                ln = raw.strip()
                if ln.startswith("Title"):
                    cur_title = ln.split(":", 1)[1].strip()
                elif ln.startswith("Published") and cur_title:
                    ts = ln.split(":", 1)[1].strip()
                    out[cur_title] = ts
                elif not ln:
                    cur_title = None
    except Exception:
        pass
    return out


def _parse_run_ts(agg_path: str) -> datetime | None:
    try:
        with open(agg_path, "r", encoding="utf-8", errors="replace") as f:
            for i in range(10):
                ln = f.readline()
                if not ln:
                    break
                if ln.startswith("Run UTC:"):
                    ts = ln.split(":", 1)[1].strip()
                    return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None
    return None


def ensure_ns(t: str) -> str:
    t = (t or "").strip().upper()
    return t if "." in t else f"{t}.NS"


def evaluate_reactions(top_rows: List[Dict[str, str]], agg_path: str) -> List[Dict[str, object]]:
    """Compute 1d/3d/5d returns after news for each top row.
    Requires network for yfinance; gracefully degrades if unavailable.
    """
    try:
        import yfinance as yf
    except Exception:
        # No evaluation possible
        return []

    published_map = _parse_aggregated_published(agg_path)
    run_ts = _parse_run_ts(agg_path) or datetime.now(timezone.utc)

    evals: List[Dict[str, object]] = []
    for row in top_rows:
        tkr = (row.get("ticker") or "").strip().upper()
        title = (row.get("top_title") or "").strip()
        source = (row.get("top_source") or "").strip()
        ev = (row.get("event_type") or "").strip()

        sym = ensure_ns(tkr)
        # Event time
        pts = published_map.get(title)
        try:
            event_ts = datetime.fromisoformat(pts.replace("Z", "+00:00")) if pts else run_ts
        except Exception:
            event_ts = run_ts

        # Fetch prices
        try:
            hist = yf.Ticker(sym).history(period="6mo", interval="1d")
            if hist is None or hist.empty:
                continue
            # Find t0: first bar with index >= event date
            # Use date-only compare in UTC
            event_date = event_ts.date()
            idx = [d.date() for d in hist.index]
            if event_date not in idx:
                # pick next trading date after event
                t0i = None
                for i, d in enumerate(idx):
                    if d >= event_date:
                        t0i = i
                        break
            else:
                t0i = idx.index(event_date)
            if t0i is None:
                continue
            def ret(days: int) -> float:
                j = t0i + days
                if j >= len(hist):
                    return 0.0
                c0 = float(hist["Close"].iloc[t0i])
                c1 = float(hist["Close"].iloc[j])
                if c0 <= 0:
                    return 0.0
                return (c1 - c0) / c0 * 100.0
            r1 = ret(1)
            r3 = ret(3)
            r5 = ret(5)
            consistent = 1 if (r3 >= 2.0 and r5 >= 2.0) else 0
            fake = 1 if (r1 >= 2.0 and r5 <= 0.5) else 0
            evals.append({
                "ticker": tkr,
                "symbol": sym,
                "event_type": ev,
                "title": title,
                "source": source,
                "event_ts": event_ts.isoformat(),
                "ret_1d": r1,
                "ret_3d": r3,
                "ret_5d": r5,
                "consistent": consistent,
                "fake": fake,
            })
        except Exception:
            continue

    return evals


def evaluate_live(top_rows: List[Dict[str, str]]) -> List[Dict[str, object]]:
    """Best-effort present-day feedback using recent OHLC data.
    Returns per-ticker: symbol, asof (iso date), price (last close or intraday),
    prev_close, live_ret (pct vs prev close).
    Uses batch daily download for robustness; falls back to per-symbol queries.
    """
    try:
        import yfinance as yf  # type: ignore
    except Exception:
        return []

    # Prepare symbols
    tickers: List[str] = []
    for row in top_rows:
        t = (row.get("ticker") or "").strip().upper()
        if t:
            tickers.append(t)
    # Deduplicate while preserving order
    seen = set()
    uniq: List[str] = []
    for t in tickers:
        if t not in seen:
            seen.add(t)
            uniq.append(t)

    sym_map = {t: (t if "." in t else f"{t}.NS") for t in uniq}

    results: List[Dict[str, object]] = []

    # Batch daily download to compute change vs previous close
    try:
        data = yf.download(list(sym_map.values()), period="5d", interval="1d", progress=False, auto_adjust=False, group_by="ticker", threads=False)
    except Exception:
        data = None

    def _append_from_series(t: str, ser_close) -> None:
        try:
            if ser_close is None or ser_close.empty:
                return
            if len(ser_close) < 2:
                return
            last_date = ser_close.index[-1]
            last_close = float(ser_close.iloc[-1])
            prev_close = float(ser_close.iloc[-2])
            if prev_close <= 0:
                return
            ret = (last_close - prev_close) / prev_close * 100.0
            results.append({
                "ticker": t,
                "symbol": sym_map[t],
                "asof": last_date.isoformat() if hasattr(last_date, "isoformat") else str(last_date),
                "price": last_close,
                "prev_close": prev_close,
                "live_ret": ret,
            })
        except Exception:
            return

    if data is not None:
        # data can be Panel-like with columns per symbol
        for t, sym in sym_map.items():
            try:
                if sym in data and hasattr(data[sym], "__getitem__"):
                    ser = data[sym]["Close"] if "Close" in data[sym] else None
                    _append_from_series(t, ser)
                else:
                    # Single-symbol frame path
                    if "Close" in data:
                        _append_from_series(t, data["Close"])
            except Exception:
                continue

    # Fallback for any missing tickers: try per-symbol daily
    have = {r["ticker"] for r in results}
    missing = [t for t in uniq if t not in have]
    for t in missing:
        sym = sym_map[t]
        try:
            h = yf.download(sym, period="5d", interval="1d", progress=False, auto_adjust=False, group_by="ticker", threads=False)
            ser = h["Close"] if (h is not None and not h.empty and "Close" in h) else None
            _append_from_series(t, ser)
        except Exception:
            continue

    # Final fallback: fast_info per ticker (instant price vs previous_close)
    have = {r["ticker"] for r in results}
    import datetime as _dt
    for t in [x for x in uniq if x not in have]:
        sym = sym_map[t]
        try:
            ti = yf.Ticker(sym)
            fi = getattr(ti, "fast_info", None)
            if not fi:
                continue
            last_price = float(getattr(fi, "last_price", None) or fi.get("last_price") or 0.0) if isinstance(fi, dict) or hasattr(fi, "get") else 0.0
            prev_close = float(getattr(fi, "previous_close", None) or (fi.get("previous_close") if isinstance(fi, dict) else 0.0) or 0.0)
            if prev_close > 0 and last_price > 0:
                ret = (last_price - prev_close) / prev_close * 100.0
                results.append({
                    "ticker": t,
                    "symbol": sym,
                    "asof": _dt.datetime.now().isoformat(timespec="seconds"),
                    "price": last_price,
                    "prev_close": prev_close,
                    "live_ret": ret,
                })
        except Exception:
            pass

    return results
