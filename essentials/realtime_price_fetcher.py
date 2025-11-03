#!/usr/bin/env python3
"""
REAL-TIME PRICE FETCHER
======================
Fetches current prices from yfinance to ensure AI doesn't rely on training data.

This module ensures that:
1. AI receives ONLY real-time data from yfinance
2. No reliance on training data for current prices
3. Entry/exit prices are calculated based on real-time data
4. All price-related outputs are grounded in fetched data

Usage:
    from realtime_price_fetcher import fetch_current_price, calculate_entry_exit_prices

    price_data = fetch_current_price('RELIANCE')
    # Returns: {
    #   'current_price': 2450.50,
    #   'timestamp': '2025-11-03 10:30:00',
    #   'symbol': 'RELIANCE.NS',
    #   'entry_zone_low': 2400.00,
    #   'entry_zone_high': 2430.00,
    #   'target_conservative': 2550.00,
    #   'target_aggressive': 2650.00,
    #   'stop_loss': 2380.00
    # }
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Optional, Tuple

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  WARNING: yfinance not installed. Run: pip3 install yfinance", file=sys.stderr)

try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

PRICE_CACHE_FILE = 'offline_price_cache.json'
_PRICE_CACHE: Optional[Dict[str, Dict]] = None
ALLOW_OFFLINE_PRICE_CACHE = os.getenv('ALLOW_OFFLINE_PRICE_CACHE', '0').strip() == '1'


def _normalize_cache_ticker(ticker: str) -> str:
    """Normalize ticker for cache lookup (strip exchange suffixes)."""
    ticker = (ticker or '').upper().strip()
    for suffix in ('.NS', '.BO', '.BSE', '.NSE'):
        if ticker.endswith(suffix):
            ticker = ticker[:-len(suffix)]
    return ticker


def _load_price_cache() -> Dict[str, Dict]:
    """Load cached price data from disk once per process."""
    if not ALLOW_OFFLINE_PRICE_CACHE:
        return {}
    global _PRICE_CACHE
    if _PRICE_CACHE is not None:
        return _PRICE_CACHE

    if not os.path.exists(PRICE_CACHE_FILE):
        _PRICE_CACHE = {}
        return _PRICE_CACHE

    try:
        with open(PRICE_CACHE_FILE, 'r', encoding='utf-8') as f:
            _PRICE_CACHE = json.load(f)
            if not isinstance(_PRICE_CACHE, dict):
                _PRICE_CACHE = {}
    except Exception as exc:
        print(f"⚠️  WARNING: Failed to load offline price cache ({exc})", file=sys.stderr)
        _PRICE_CACHE = {}
    return _PRICE_CACHE


def _save_price_cache(cache: Dict[str, Dict]) -> None:
    """Persist cache back to disk (best effort)."""
    if not ALLOW_OFFLINE_PRICE_CACHE:
        return
    global _PRICE_CACHE
    _PRICE_CACHE = cache
    try:
        with open(PRICE_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cache, f, indent=2)
    except Exception as exc:
        print(f"⚠️  WARNING: Could not save offline price cache ({exc})", file=sys.stderr)


def _update_price_cache(ticker: str, price_info: Dict) -> None:
    """Store latest price snapshot for offline fallback."""
    if not ALLOW_OFFLINE_PRICE_CACHE:
        return
    if not price_info or price_info.get('current_price') is None:
        return
    cache = _load_price_cache()
    cache_key = _normalize_cache_ticker(ticker)
    if not cache_key:
        return
    entry = {
        'current_price': float(price_info.get('current_price')),
        'timestamp': price_info.get('timestamp', datetime.now().isoformat()),
        'symbol': price_info.get('symbol', ticker),
        'source': price_info.get('source', 'yfinance'),
        'cached_at': datetime.now().isoformat()
    }
    cache[cache_key] = entry
    _save_price_cache(cache)


def _get_cached_price(ticker: str) -> Optional[Dict]:
    """Return cached price if live fetch fails."""
    if not ALLOW_OFFLINE_PRICE_CACHE:
        return None
    cache = _load_price_cache()
    cache_key = _normalize_cache_ticker(ticker)
    entry = cache.get(cache_key)
    if not entry or entry.get('current_price') is None:
        return None
    cached_at = entry.get('cached_at')
    age_hours = None
    if cached_at:
        try:
            age_hours = (datetime.now() - datetime.fromisoformat(cached_at)).total_seconds() / 3600.0
        except Exception:
            age_hours = None
    return {
        'current_price': float(entry.get('current_price')),
        'timestamp': entry.get('timestamp', datetime.now().isoformat()),
        'symbol': entry.get('symbol', ticker),
        'data_available': True,
        'source': 'offline_cache',
        'cache_metadata': {
            'original_source': entry.get('source', 'unknown'),
            'cached_at': cached_at,
            'age_hours': age_hours
        }
    }


def fetch_current_price(ticker: str,
                        exchange_suffix: str = '.NS',
                        fallback_suffix: str = '.BO') -> Optional[Dict]:
    """
    Fetch current price from yfinance with fallback to BSE.

    Returns:
        dict with keys: current_price, timestamp, symbol, data_available
        or None if fetch fails
    """
    if not YFINANCE_AVAILABLE:
        return {
            'current_price': None,
            'timestamp': datetime.now().isoformat(),
            'symbol': ticker,
            'data_available': False,
            'error': 'yfinance not installed'
        }

    # Try NSE first, then BSE
    symbols_to_try = []
    if '.' in ticker:
        symbols_to_try = [ticker]
    else:
        symbols_to_try = [f"{ticker}{exchange_suffix}", f"{ticker}{fallback_suffix}"]

    for symbol in symbols_to_try:
        try:
            stock = yf.Ticker(symbol)

            # Try to get current price from fast_info (real-time)
            try:
                current_price = stock.fast_info['lastPrice']
                if current_price and current_price > 0:
                    price_snapshot = {
                        'current_price': float(current_price),
                        'timestamp': datetime.now().isoformat(),
                        'symbol': symbol,
                        'data_available': True,
                        'source': 'yfinance.fast_info'
                    }
                    _update_price_cache(ticker, price_snapshot)
                    return price_snapshot
            except (KeyError, AttributeError, TypeError):
                pass

            # Fallback to history (last close)
            hist = stock.history(period='5d')
            if hist is not None and not hist.empty and len(hist) > 0:
                current_price = hist['Close'].iloc[-1]
                if current_price and current_price > 0:
                    price_snapshot = {
                        'current_price': float(current_price),
                        'timestamp': hist.index[-1].strftime('%Y-%m-%d %H:%M:%S'),
                        'symbol': symbol,
                        'data_available': True,
                        'source': 'yfinance.history'
                    }
                    _update_price_cache(ticker, price_snapshot)
                    return price_snapshot
        except Exception as e:
            print(f"⚠️  Error fetching {symbol}: {str(e)[:100]}", file=sys.stderr)
            continue

    if ALLOW_OFFLINE_PRICE_CACHE:
        cached = _get_cached_price(ticker)
        if cached:
            return cached

    # All attempts failed
    return {
        'current_price': None,
        'timestamp': datetime.now().isoformat(),
        'symbol': ticker,
        'data_available': False,
        'error': f'No data for {ticker} (tried: {", ".join(symbols_to_try)})'
    }


def calculate_entry_exit_prices(current_price: Optional[float],
                                 sentiment: str = 'bullish',
                                 expected_move_pct: float = 0.0,
                                 volatility_factor: float = 1.0) -> Dict:
    """
    Calculate entry zone and exit targets based on current price.

    Args:
        current_price: Real-time price from yfinance
        sentiment: bullish/bearish/neutral
        expected_move_pct: Expected price move percentage from AI
        volatility_factor: Multiplier for wider/narrower ranges (1.0 = default)

    Returns:
        dict with entry_zone, targets, and stop_loss
    """
    if current_price is None or current_price <= 0:
        return {
            'entry_zone_low': None,
            'entry_zone_high': None,
            'target_conservative': None,
            'target_aggressive': None,
            'stop_loss': None,
            'calculated': False
        }

    # Entry zone calculation (for bullish sentiment)
    # Conservative: Buy on slight dip (-1% to -3% from current)
    # Aggressive: Buy near current price (-0.5% to +0.5%)

    if sentiment == 'bullish':
        # Entry zone: -1% to current price
        entry_low_pct = -1.0 * volatility_factor
        entry_high_pct = 0.0

        # Targets based on expected move
        if expected_move_pct > 0:
            # Conservative: 50% of expected move
            target_conservative_pct = max(3.0, expected_move_pct * 0.5)
            # Aggressive: 100% of expected move
            target_aggressive_pct = max(5.0, expected_move_pct)
        else:
            # Default targets if no expected move
            target_conservative_pct = 4.0
            target_aggressive_pct = 8.0

        # Stop loss: -3% to -5% below current
        stop_loss_pct = -4.0 * volatility_factor

    elif sentiment == 'bearish':
        # For bearish, these are SHORT entry/exit levels
        # Entry: near current or slight rally
        entry_low_pct = 0.0
        entry_high_pct = 1.0 * volatility_factor

        # Targets (downside)
        if expected_move_pct < 0:
            target_conservative_pct = max(-5.0, expected_move_pct * 0.5)
            target_aggressive_pct = min(-10.0, expected_move_pct)
        else:
            target_conservative_pct = -3.0
            target_aggressive_pct = -6.0

        # Stop loss (upside risk for short)
        stop_loss_pct = 3.0 * volatility_factor

    else:  # neutral
        # Neutral: tight ranges
        entry_low_pct = -1.5 * volatility_factor
        entry_high_pct = 0.5
        target_conservative_pct = 2.5
        target_aggressive_pct = 5.0
        stop_loss_pct = -2.5 * volatility_factor

    # Calculate absolute prices
    entry_zone_low = current_price * (1 + entry_low_pct / 100)
    entry_zone_high = current_price * (1 + entry_high_pct / 100)
    target_conservative = current_price * (1 + target_conservative_pct / 100)
    target_aggressive = current_price * (1 + target_aggressive_pct / 100)
    stop_loss = current_price * (1 + stop_loss_pct / 100)

    return {
        'entry_zone_low': round(entry_zone_low, 2),
        'entry_zone_high': round(entry_zone_high, 2),
        'target_conservative': round(target_conservative, 2),
        'target_aggressive': round(target_aggressive, 2),
        'stop_loss': round(stop_loss, 2),
        'calculated': True,
        'calculation_basis': {
            'current_price': current_price,
            'sentiment': sentiment,
            'expected_move_pct': expected_move_pct,
            'volatility_factor': volatility_factor
        }
    }


def get_comprehensive_price_data(ticker: str,
                                 sentiment: str = 'bullish',
                                 expected_move_pct: float = 0.0) -> Dict:
    """
    Get complete price package: current price + entry/exit calculations.

    This is the main function to use - it combines fetching and calculations.

    Args:
        ticker: Stock ticker (e.g., 'RELIANCE')
        sentiment: Expected sentiment from news/AI
        expected_move_pct: Expected percentage move

    Returns:
        Complete dict with all price data needed for AI and output
    """
    # Fetch current price
    price_info = fetch_current_price(ticker)

    if not price_info or not price_info.get('data_available'):
        return {
            'ticker': ticker,
            'current_price': None,
            'price_timestamp': datetime.now().isoformat(),
            'entry_zone_low': None,
            'entry_zone_high': None,
            'target_conservative': None,
            'target_aggressive': None,
            'stop_loss': None,
            'price_data_available': False,
            'error': price_info.get('error', 'Unknown error') if price_info else 'Fetch failed',
            'cache_metadata': price_info.get('cache_metadata') if price_info else None
        }

    current_price = price_info['current_price']

    # Calculate entry/exit levels
    levels = calculate_entry_exit_prices(
        current_price=current_price,
        sentiment=sentiment,
        expected_move_pct=expected_move_pct
    )

    # Combine into single dict
    return {
        'ticker': ticker,
        'current_price': current_price,
        'price_timestamp': price_info['timestamp'],
        'price_symbol': price_info['symbol'],
        'entry_zone_low': levels['entry_zone_low'],
        'entry_zone_high': levels['entry_zone_high'],
        'target_conservative': levels['target_conservative'],
        'target_aggressive': levels['target_aggressive'],
        'stop_loss': levels['stop_loss'],
        'price_data_available': True,
        'source': price_info.get('source', 'yfinance'),
        'cache_metadata': price_info.get('cache_metadata')
    }


def format_price_context_for_ai(price_data: Dict) -> str:
    """
    Format price data into clear text for AI prompt.

    This ensures AI sees explicit price data and doesn't use training data.
    """
    if not price_data.get('price_data_available'):
        return f"""
🚫 CRITICAL: NO REAL-TIME PRICE DATA AVAILABLE FOR {price_data.get('ticker', 'UNKNOWN')}
- Error: {price_data.get('error', 'Unknown')}
- You MUST NOT use training data or memorized prices
- If analysis requires price, state "INSUFFICIENT DATA" and return neutral scores
"""

    ticker = price_data['ticker']
    cp = price_data['current_price']
    ts = price_data['price_timestamp']
    source = price_data.get('source', 'yfinance')
    cache_note = ""
    if source == 'offline_cache':
        meta = price_data.get('cache_metadata') or {}
        cached_at = meta.get('cached_at', 'unknown time')
        age = meta.get('age_hours')
        if isinstance(age, (int, float)):
            age_str = f"{age:.1f}h old"
        else:
            age_str = "freshness unknown"
        origin = meta.get('original_source', 'unknown source')
        cache_note = (
            "\n⚠️  NOTE: Using cached price snapshot "
            f"(seeded from {origin} at {cached_at}; {age_str}). "
            "Verify with live market data before trading."
        )

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 REAL-TIME PRICE DATA (FETCHED FROM YFINANCE NOW)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ticker: {ticker}
Current Price: ₹{cp:.2f}
Fetched At: {ts}
Source: {source}
Symbol: {price_data.get('price_symbol', ticker)}
{cache_note}

SUGGESTED TRADING LEVELS (based on current price):
├─ Entry Zone: ₹{price_data['entry_zone_low']:.2f} - ₹{price_data['entry_zone_high']:.2f}
├─ Target 1 (Conservative): ₹{price_data['target_conservative']:.2f}
├─ Target 2 (Aggressive): ₹{price_data['target_aggressive']:.2f}
└─ Stop Loss: ₹{price_data['stop_loss']:.2f}

⚠️  CRITICAL INSTRUCTIONS FOR AI:
1. Use ONLY the above current price (₹{cp:.2f}) fetched just now
2. DO NOT use any memorized/training data prices for {ticker}
3. Base ALL calculations on the real-time price above
4. If you need historical context, request it explicitly
5. Your analysis must be grounded in THIS price data ONLY

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""


# CLI test interface
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 realtime_price_fetcher.py <TICKER> [sentiment] [expected_move_pct]")
        print("Example: python3 realtime_price_fetcher.py RELIANCE bullish 5.0")
        sys.exit(1)

    ticker = sys.argv[1]
    sentiment = sys.argv[2] if len(sys.argv) > 2 else 'bullish'
    expected_move = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0

    print(f"\n🔍 Fetching real-time price data for {ticker}...")
    print("=" * 80)

    data = get_comprehensive_price_data(ticker, sentiment, expected_move)

    if data['price_data_available']:
        print(f"\n✅ SUCCESS! Current price: ₹{data['current_price']:.2f}")
        print(f"   Fetched at: {data['price_timestamp']}")
        print(f"   Symbol: {data['price_symbol']}")
        print(f"\n📊 Trading Levels:")
        print(f"   Entry Zone: ₹{data['entry_zone_low']:.2f} - ₹{data['entry_zone_high']:.2f}")
        print(f"   Target 1: ₹{data['target_conservative']:.2f}")
        print(f"   Target 2: ₹{data['target_aggressive']:.2f}")
        print(f"   Stop Loss: ₹{data['stop_loss']:.2f}")
        print("\n" + "=" * 80)
        print("\n📝 AI Prompt Context:\n")
        print(format_price_context_for_ai(data))
    else:
        print(f"\n❌ FAILED: {data.get('error', 'Unknown error')}")
        print("\n📝 AI Prompt Context:\n")
        print(format_price_context_for_ai(data))

    print("\n" + "=" * 80)
