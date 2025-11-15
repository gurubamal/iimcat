#!/usr/bin/env python3
"""
EXIT INTELLIGENCE ANALYZER - COMPREHENSIVE SELL/EXIT ASSESSMENT SYSTEM
========================================================================
Multi-Factor Exit Decision Engine that assesses stocks IRRESPECTIVE of NEWS.

KEY FEATURES:
✅ Comprehensive multi-factor analysis (not just news-based)
✅ Technical breakdown detection (support breaks, bearish patterns)
✅ Fundamental deterioration assessment
✅ Volume and momentum analysis
✅ Risk factor evaluation
✅ AI-powered intelligent assessment (Claude/Codex)
✅ Categorizes into: immediate_exit and non_exit lists

ASSESSMENT FACTORS (works WITHOUT news):
1. Technical Analysis:
   - Support/resistance breaks
   - Bearish patterns (head & shoulders, double top)
   - Moving average crosses (death cross)
   - RSI oversold/overbought conditions
   - Volume deterioration

2. Fundamental Analysis:
   - Recent earnings misses
   - Debt level concerns
   - Margin compression
   - Cash flow issues
   - Valuation overextension

3. News Sentiment Analysis (if available):
   - Negative news (regulatory, legal, downgrades)
   - Profit warnings
   - Management issues
   - Sector headwinds

4. Risk Factors:
   - Competitive threats
   - Regulatory risks
   - Market sentiment shift
   - Macro headwinds

Usage:
  python3 exit_intelligence_analyzer.py --tickers-file exit.check.txt --ai-provider claude

  # With custom configuration
  python3 exit_intelligence_analyzer.py --tickers-file exit.check.txt --ai-provider codex --hours-back 72

Output:
  - exit_assessment_immediate.txt: Stocks requiring immediate exit
  - exit_assessment_hold.txt: Stocks that can be held
  - exit_assessment_detailed.csv: Full analysis with scores and reasoning
"""

import sys
import os
import json
import argparse
import math
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import csv

# Ensure recommendations output directory is available early
try:
    # Prefer central config if available
    from orchestrator.config import RECOMMENDATIONS_DIR as _RECOMMENDATIONS_DIR  # type: ignore
except Exception:
    # Fallback to local outputs/recommendations under current module directory
    _BASE = Path(__file__).resolve().parent
    _RECOMMENDATIONS_DIR = str(_BASE / 'outputs' / 'recommendations')
    try:
        os.makedirs(_RECOMMENDATIONS_DIR, exist_ok=True)
    except Exception:
        pass

# Try to import yfinance for real-time data
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not available, technical analysis will be limited", file=sys.stderr)

# Try to import technical indicators
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    print("⚠️  pandas/numpy not available, technical analysis will be limited", file=sys.stderr)


# ============================================================================
# CONFIGURATION
# ============================================================================

EXIT_THRESHOLDS = {
    'technical_breakdown_score': 65,  # Score > 65 = technical breakdown
    'fundamental_risk_score': 70,     # Score > 70 = fundamental red flag
    'negative_sentiment_score': 75,   # Score > 75 = strong negative sentiment
    'combined_exit_score': 70,        # Combined score > 70 = immediate exit
    'rsi_oversold': 30,
    'rsi_overbought': 70,
}

EXIT_RISK_WEIGHTS = {
    # Legacy weights (kept for reference); new framework overrides below
    'technical': 0.35,
    'fundamental': 0.30,
    'sentiment': 0.25,
    'volume_momentum': 0.10,
}

# New scoring framework (configurable via CLI flags later)
NEW_WEIGHTS = {
    'tech': 0.45,
    'news': 0.25,
    'fund': 0.20,
    'liquidity': 0.10,
}

DECISION_BANDS = {
    'STRONG_EXIT': 90,
    'EXIT': 70,
    'MONITOR': 50,
    'HOLD': 30,
    # < 30 => STRONG_HOLD
}

def _load_exit_ai_config() -> None:
    """Optionally override weights/bands from exit_ai_config.json.

    This enables light feedback calibration via update_exit_ai_config.py
    without changing code.
    """
    import json
    try:
        path = os.getenv('EXIT_AI_CONFIG', 'exit_ai_config.json')
        if not path or not os.path.exists(path):
            return
        with open(path, 'r') as f:
            cfg = json.load(f)
        w = (cfg.get('weights') or {})
        b = (cfg.get('bands') or {})
        # Normalize and clamp weights
        def _norm(ws):
            ws2 = {k: float(max(0.05, min(0.8, ws.get(k, NEW_WEIGHTS.get(k, 0.1))))) for k in ('tech','news','fund','liquidity')}
            s = sum(ws2.values()) or 1.0
            return {k: v/s for k, v in ws2.items()}
        nw = _norm(w) if w else None
        if nw:
            NEW_WEIGHTS.update(nw)
        # Bands (keep sensible ordering)
        sb = int(b.get('STRONG_EXIT', DECISION_BANDS['STRONG_EXIT'])) if b else DECISION_BANDS['STRONG_EXIT']
        ex = int(b.get('EXIT', DECISION_BANDS['EXIT'])) if b else DECISION_BANDS['EXIT']
        mo = int(b.get('MONITOR', DECISION_BANDS['MONITOR'])) if b else DECISION_BANDS['MONITOR']
        ho = int(b.get('HOLD', DECISION_BANDS['HOLD'])) if b else DECISION_BANDS['HOLD']
        # Ensure ordering: STRONG_EXIT >= EXIT > MONITOR > HOLD
        sb = max(sb, ex)
        ex = max(ex, mo+1)
        mo = max(mo, ho+1)
        DECISION_BANDS.update({'STRONG_EXIT': sb, 'EXIT': ex, 'MONITOR': mo, 'HOLD': ho})
    except Exception:
        # Silent: config is optional
        pass

# ----------------------------
# Catalyst/Risk Type Heuristics
# ----------------------------
_FUND_CUE = (
    'order', 'contract', 'order book', 'ordr book', 'ob expansion', 'earnings', 'guidance', 'profit', 'revenue',
    'margin', 'cash flow', 'cashflow', 'fcf', 'debt', 'leverage', 'dividend', 'buyback', 'regulatory', 'approval',
    'customer', 'plant', 'capacity', 'capex', 'opex', 'tariff', 'pricing', 'market share', 'rm cost', 'input cost',
    'fta', 'fta duty', 'tax', 'gst', 'audit', 'fraud', 'liquidity', 'credit', 'rating', 'downgrade', 'upgrade',
)
_TECH_CUE = (
    'breakout', 'break down', 'breakdown', 'support', 'resistance', 'rsi', 'bollinger', 'dma', 'sma', 'ema', 'atr',
    'momentum', 'volume', 'volatility', '52-week', 'swing', 'overbought', 'oversold', 'gap', 'pattern', 'trend',
)

def _classify(items):
    fund = 0
    tech = 0
    out = []
    for it in items or []:
        s = str(it or '').strip()
        sl = s.lower()
        is_f = any(k in sl for k in _FUND_CUE)
        is_t = any(k in sl for k in _TECH_CUE)
        if is_f and not is_t:
            fund += 1
            out.append(('fundamental', s))
        elif is_t and not is_f:
            tech += 1
            out.append(('technical', s))
        elif is_f and is_t:
            # Mixed → consider fundamental to be conservative for exits
            fund += 1
            out.append(('fundamental', s))
        else:
            out.append(('other', s))
    return fund, tech, out


# ============================================================================
# TECHNICAL ANALYSIS MODULE
# ============================================================================

def get_stock_data(ticker: str, period: str = "6mo") -> Optional[pd.DataFrame]:
    """Fetch stock data using yfinance."""
    if not YFINANCE_AVAILABLE or not PANDAS_AVAILABLE:
        return None

    try:
        # Add .NS suffix for NSE stocks if not present; try .BO fallback
        tried = []
        symbols = [ticker] if '.' in ticker else [f"{ticker}.NS", f"{ticker}.BO"]
        for symbol in symbols:
            tried.append(symbol)
            try:
                stock = yf.Ticker(symbol)
                df = stock.history(period=period)
                if df is not None and not df.empty:
                    return df
            except Exception:
                continue
        print(f"⚠️  No data found for {ticker} (tried: {', '.join(tried)})", file=sys.stderr)
        return None
    except Exception as e:
        print(f"⚠️  Error fetching data for {ticker}: {e}", file=sys.stderr)
        return None


def calculate_technical_indicators(df: pd.DataFrame) -> Dict:
    """Calculate technical indicators for exit assessment."""
    if df is None or df.empty:
        return {}

    try:
        indicators = {}

        # Current price
        current_price = df['Close'].iloc[-1]
        indicators['current_price'] = current_price

        # Moving averages
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()

        indicators['sma_20'] = df['SMA_20'].iloc[-1] if len(df) >= 20 else None
        indicators['sma_50'] = df['SMA_50'].iloc[-1] if len(df) >= 50 else None

        # Price vs MA (breakdown detection)
        if indicators['sma_20']:
            indicators['price_vs_sma20_pct'] = ((current_price - indicators['sma_20']) / indicators['sma_20']) * 100
        if indicators['sma_50']:
            indicators['price_vs_sma50_pct'] = ((current_price - indicators['sma_50']) / indicators['sma_50']) * 100

        # RSI calculation
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        indicators['rsi'] = df['RSI'].iloc[-1] if len(df) >= 14 else None

        # Volume analysis
        avg_volume_20 = df['Volume'].rolling(window=20).mean().iloc[-1]
        current_volume = df['Volume'].iloc[-1]
        indicators['volume_ratio'] = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0
        indicators['avg_volume_20'] = float(avg_volume_20) if avg_volume_20 == avg_volume_20 else None  # NaN check
        indicators['current_volume'] = float(current_volume) if current_volume == current_volume else None

        # Price momentum (10-day return)
        if len(df) >= 10:
            indicators['momentum_10d_pct'] = ((df['Close'].iloc[-1] - df['Close'].iloc[-10]) / df['Close'].iloc[-10]) * 100

        # Recent price action (5-day trend)
        if len(df) >= 5:
            recent_prices = df['Close'].iloc[-5:].values
            indicators['recent_trend'] = 'down' if recent_prices[-1] < recent_prices[0] else 'up'

        # Support break detection (52-week low proximity)
        if len(df) >= 252:
            week_52_low = df['Close'].iloc[-252:].min()
            indicators['distance_from_52w_low_pct'] = ((current_price - week_52_low) / week_52_low) * 100

        # Support/Resistance (20-day swing)
        if len(df) >= 20:
            low_20 = df['Close'].rolling(window=20).min().iloc[-1]
            high_20 = df['Close'].rolling(window=20).max().iloc[-1]
            indicators['distance_from_20d_low_pct'] = ((current_price - low_20) / low_20) * 100 if low_20 > 0 else None
            indicators['distance_from_20d_high_pct'] = ((high_20 - current_price) / high_20) * 100 if high_20 > 0 else None

        # ATR(14)
        if len(df) >= 15:
            high = df['High']
            low = df['Low']
            close = df['Close']
            prev_close = close.shift(1)
            tr = pd.concat([
                (high - low),
                (high - prev_close).abs(),
                (low - prev_close).abs()
            ], axis=1).max(axis=1)
            atr14 = tr.rolling(window=14).mean()
            indicators['atr_14'] = float(atr14.iloc[-1])
            indicators['atr_pct'] = float(atr14.iloc[-1] / current_price * 100) if current_price else None

        # Bollinger Bands (20, 2)
        if len(df) >= 20:
            sma20 = df['SMA_20']
            std20 = df['Close'].rolling(window=20).std()
            upper = sma20 + 2 * std20
            lower = sma20 - 2 * std20
            indicators['bb_upper'] = float(upper.iloc[-1]) if not math.isnan(upper.iloc[-1]) else None
            indicators['bb_lower'] = float(lower.iloc[-1]) if not math.isnan(lower.iloc[-1]) else None
            indicators['bb_bandwidth_pct'] = float((upper.iloc[-1] - lower.iloc[-1]) / sma20.iloc[-1] * 100) if sma20.iloc[-1] else None
            indicators['bb_position_z'] = float((current_price - sma20.iloc[-1]) / (std20.iloc[-1] if std20.iloc[-1] else 1)) if std20.iloc[-1] else None

        # Multi-timeframe trend (weekly/monthly)
        try:
            weekly = df['Close'].resample('W-FRI').last()
            if len(weekly) >= 4:
                indicators['weekly_trend'] = 'down' if weekly.iloc[-1] < weekly.iloc[-4] else 'up'
            # Pandas FutureWarning: alias 'M' will be removed; use 'ME' (month end)
            monthly = df['Close'].resample('ME').last()
            if len(monthly) >= 3:
                indicators['monthly_trend'] = 'down' if monthly.iloc[-1] < monthly.iloc[-3] else 'up'
        except Exception:
            pass

        return indicators

    except Exception as e:
        print(f"⚠️  Error calculating technical indicators: {e}", file=sys.stderr)
        return {}


def assess_technical_exit_signals(indicators: Dict) -> Tuple[int, str, List[str]]:
    """Assess technical indicators for exit signals.

    Returns:
        (exit_score, severity, reasons)
        - exit_score: 0-100 (higher = more urgent to exit)
        - severity: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'NONE'
        - reasons: List of specific technical concerns
    """
    if not indicators:
        return 0, 'NONE', ['No technical data available']

    exit_score = 0
    reasons = []

    # 1. Price below moving averages (breakdown)
    if indicators.get('price_vs_sma20_pct') is not None:
        if indicators['price_vs_sma20_pct'] < -5:
            exit_score += 15
            reasons.append(f"Price {abs(indicators['price_vs_sma20_pct']):.1f}% below 20-day SMA (breakdown)")
        elif indicators['price_vs_sma20_pct'] < -10:
            exit_score += 25
            reasons.append(f"Price {abs(indicators['price_vs_sma20_pct']):.1f}% below 20-day SMA (severe breakdown)")

    if indicators.get('price_vs_sma50_pct') is not None:
        if indicators['price_vs_sma50_pct'] < -8:
            exit_score += 20
            reasons.append(f"Price {abs(indicators['price_vs_sma50_pct']):.1f}% below 50-day SMA")

    # 2. RSI conditions
    if indicators.get('rsi') is not None:
        rsi = indicators['rsi']
        if rsi < 30:
            exit_score += 10
            reasons.append(f"RSI oversold at {rsi:.1f} (potential further downside)")
        elif rsi > 70 and indicators.get('momentum_10d_pct', 0) < 0:
            exit_score += 15
            reasons.append(f"RSI overbought at {rsi:.1f} with negative momentum (reversal risk)")

    # 3. Negative momentum
    if indicators.get('momentum_10d_pct') is not None:
        momentum = indicators['momentum_10d_pct']
        if momentum < -5:
            exit_score += 15
            reasons.append(f"Negative 10-day momentum: {momentum:.1f}%")
        elif momentum < -10:
            exit_score += 25
            reasons.append(f"Severe negative momentum: {momentum:.1f}%")

    # 4. Volume deterioration or spike conditions
    if indicators.get('volume_ratio') is not None:
        if indicators.get('recent_trend') == 'down' and indicators['volume_ratio'] < 0.7:
            exit_score += 8
            reasons.append("Low volume on downtrend (weak support)")
        if indicators['volume_ratio'] >= 1.5 and indicators.get('recent_trend') == 'down':
            exit_score += 10
            reasons.append("Unusual volume spike on down move")

    # 5. Near 52-week low (support break)
    if indicators.get('distance_from_52w_low_pct') is not None:
        distance = indicators['distance_from_52w_low_pct']
        if distance < 5:
            exit_score += 20
            reasons.append(f"Near 52-week low ({distance:.1f}% above, high breakdown risk)")

    # 6. Death cross detection (SMA 20 crosses below SMA 50)
    if indicators.get('sma_20') and indicators.get('sma_50'):
        if indicators['sma_20'] < indicators['sma_50'] * 0.98:  # 2% buffer
            exit_score += 20
            reasons.append("Death cross: 20-day SMA below 50-day SMA (bearish)")

    # 7. Bollinger band breach
    if indicators.get('bb_lower') and indicators.get('current_price'):
        if indicators['current_price'] < indicators['bb_lower']:
            exit_score += 10
            reasons.append("Close below lower Bollinger band")

    # 8. Volatility risk via ATR
    if indicators.get('atr_pct') is not None:
        if indicators['atr_pct'] >= 3:
            exit_score += 5
            reasons.append(f"High short-term volatility (ATR {indicators['atr_pct']:.1f}% of price)")

    # 9. Multi-timeframe alignment
    daily_down = indicators.get('recent_trend') == 'down'
    weekly_down = indicators.get('weekly_trend') == 'down'
    if daily_down and weekly_down:
        exit_score += 7
        reasons.append("Daily and weekly trends aligned down")

    # Determine severity
    if exit_score >= 75:
        severity = 'CRITICAL'
    elif exit_score >= 60:
        severity = 'HIGH'
    elif exit_score >= 40:
        severity = 'MEDIUM'
    elif exit_score >= 20:
        severity = 'LOW'
    else:
        severity = 'NONE'

    if not reasons:
        reasons = ['No significant technical exit signals']

    return min(exit_score, 100), severity, reasons


def _compute_liquidity_risk(indicators: Dict) -> int:
    """Compute liquidity risk score (0-100: higher = more risk). Uses ADV and price.

    Heuristic scale based on 20-day average volume and rupee-notional if possible.
    """
    try:
        adv = indicators.get('avg_volume_20') or 0
        price = indicators.get('current_price') or 0
        notional = adv * price
        # If notional is zero, fallback to volume-only thresholds
        if notional <= 0:
            if adv <= 5e4:
                return 80
            if adv <= 2e5:
                return 60
            if adv <= 1e6:
                return 40
            return 20
        # Notional thresholds (rough INR heuristic)
        if notional < 2e7:   # < 2 cr
            return 80
        if notional < 1e8:   # 2-10 cr
            return 55
        if notional < 5e8:   # 10-50 cr
            return 35
        return 20
    except Exception:
        return 50


def _compute_levels(indicators: Dict) -> Dict:
    """Compute stop/trail/alerts from indicators (structure + ATR-based)."""
    levels = {}
    try:
        price = indicators.get('current_price')
        atr = indicators.get('atr_14')
        low_20_pct = indicators.get('distance_from_20d_low_pct')
        sma20 = indicators.get('sma_20')
        # Approx swing low from 20D low distance
        if price and low_20_pct is not None and low_20_pct >= 0:
            swing_low = price / (1 + low_20_pct / 100)
        else:
            swing_low = None
        if swing_low and atr:
            levels['stop'] = f"close< {swing_low - 1.0*atr:.2f} (swing_low - 1.0*ATR)"
        elif swing_low:
            levels['stop'] = f"close< {swing_low:.2f} (swing low)"
        if atr:
            levels['trail'] = f"{1.5*atr:.2f} (1.5×ATR)"
        if sma20:
            levels['alert_reclaim'] = "20DMA"
    except Exception:
        pass
    return levels


def _colorize(decision: str, use_color: bool = True) -> str:
    if not use_color:
        return decision
    RED='\033[0;31m'; YEL='\033[0;33m'; GRN='\033[0;32m'; GREY='\033[0;90m'; NC='\033[0m'
    mapping = {
        'EXIT': RED,
        'STRONG EXIT': RED,
        'IMMEDIATE_EXIT': RED,
        'MONITOR': YEL,
        'HOLD': GRN,
        'STRONG HOLD': GRN,
        'DATA-ISSUE': GREY,
    }
    color = mapping.get(decision, '')
    return f"{color}{decision}{NC}" if color else decision


def _write_jsonl(path: str, obj: Dict) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(obj, separators=(',', ':')) + "\n")
    except Exception as e:
        print(f"⚠️  Failed to write JSONL: {e}", file=sys.stderr)


# ============================================================================
# AI-POWERED COMPREHENSIVE EXIT ASSESSMENT
# ============================================================================

def _normalize_exit_response(
    raw_response: Dict,
    technical_data: Dict,
    ai_provider: str,
) -> Dict:
    """Normalize any provider response to the exit schema expected by this module.

    Bridges for codex/gemini (and our Claude bridge when using its news template)
    may return a generic news-analysis schema. This adapter converts that into the
    exit-specific fields so downstream logic remains consistent.

    Expected output keys:
      - exit_recommendation: IMMEDIATE_EXIT | MONITOR | HOLD
      - exit_urgency_score: 0-100
      - exit_confidence: 0-100
      - technical_breakdown_score: 0-100
      - fundamental_risk_score: 0-100
      - negative_sentiment_score: 0-100
      - primary_exit_reasons: list[str]
      - hold_rationale: list[str]
      - risk_factors: list[str]
      - recommendation_summary: str
      - stop_loss_suggestion: int (percentage)
    """

    # If it already looks like an exit response, normalize and clamp values
    if 'exit_recommendation' in raw_response and 'exit_urgency_score' in raw_response:
        out = dict(raw_response)
        # Map common synonyms to internal buckets
        rec = str(out.get('exit_recommendation', '') or '').strip().upper()
        if rec in ('WATCH', 'WATCHLIST'):
            rec = 'MONITOR'
        elif rec in ('SELL', 'EXIT', 'IMMEDIATE SELL', 'IMMEDIATE_EXIT'):
            rec = 'IMMEDIATE_EXIT'
        elif rec in ('HOLD', 'KEEP'):
            rec = 'HOLD'
        else:
            # Unknown -> default conservative hold
            rec = 'HOLD'
        out['exit_recommendation'] = rec

        # Coerce numeric fields
        def _num(v, default=50):
            try:
                return float(v)
            except Exception:
                return float(default)

        out['exit_urgency_score'] = max(0.0, min(100.0, _num(out.get('exit_urgency_score', 50))))
        out['exit_confidence'] = int(max(0, min(100, int(_num(out.get('exit_confidence', out.get('confidence', 50)), 50)))))

        out.setdefault('technical_breakdown_score', 0)
        out.setdefault('fundamental_risk_score', 50)
        out.setdefault('negative_sentiment_score', 50)
        out.setdefault('primary_exit_reasons', [])
        out.setdefault('hold_rationale', [])
        out.setdefault('risk_factors', [])
        out.setdefault('recommendation_summary', '')
        out.setdefault('stop_loss_suggestion', 10)

        # Detect obviously generic/low-information Gemini outputs and replace with
        # a technical-driven summary to avoid flat scores across tickers.
        generic_sig = False
        try:
            rsn = (out.get('reasoning') or out.get('recommendation_summary') or '')
            if isinstance(rsn, str) and (
                'Detected 0 catalyst' in rsn or 'unknown source' in rsn.lower()
            ):
                generic_sig = True
        except Exception:
            pass
        if abs(out['exit_urgency_score'] - 43.26) < 0.01:
            generic_sig = True

        if generic_sig:
            tech_score, _severity, reasons = assess_technical_exit_signals(technical_data or {})
            # Build a more informative replacement using technicals
            base_exit = 30 if tech_score < 35 else (55 if tech_score < 60 else 75)
            neg_sent = 50
            fundamental = 50
            combined_hint = int(0.45 * tech_score + 0.25 * neg_sent + 0.20 * fundamental + 0.10 * base_exit)
            if combined_hint >= 70:
                rec2 = 'IMMEDIATE_EXIT'
            elif combined_hint >= 50:
                rec2 = 'MONITOR'
            else:
                rec2 = 'HOLD'
            out.update({
                'exit_recommendation': rec2,
                'exit_urgency_score': combined_hint,
                'exit_confidence': max(40, int(out.get('exit_confidence', 40))),
                'technical_breakdown_score': tech_score,
                'fundamental_risk_score': fundamental,
                'negative_sentiment_score': neg_sent,
                'primary_exit_reasons': reasons[:5],
                'hold_rationale': [] if rec2 == 'IMMEDIATE_EXIT' else (['No urgent exit signals'] if rec2 == 'HOLD' else ['Some warning signs present']),
                'recommendation_summary': f"Tech-driven assessment: score={combined_hint}; signals: {'; '.join(reasons[:2])}",
            })

        return out

    # Compute technical score from provided indicators
    tech_score, _severity, tech_reasons = assess_technical_exit_signals(technical_data or {})

    # Generic mapping from news-style response
    rec_generic = str(raw_response.get('recommendation', 'HOLD')).upper()
    sentiment = str(raw_response.get('sentiment', 'neutral')).lower()
    impact = str(raw_response.get('impact', 'medium')).lower()
    certainty = float(raw_response.get('confidence', raw_response.get('certainty', 50)) or 50)
    risks_list = raw_response.get('risks', []) or []
    catalysts_list = raw_response.get('catalysts', raw_response.get('exit_catalysts', [])) or []
    reasoning = raw_response.get('reasoning', '') or ''

    # Catalyst typing (fundamental vs technical) to bias scoring
    fund_c, tech_c, _typed_cats = _classify(catalysts_list)
    fund_r, tech_r, _typed_risks = _classify(risks_list)

    # Map to exit urgency baseline from generic recommendation
    base_exit = 50
    if rec_generic == 'SELL':
        base_exit = 70
    elif rec_generic == 'HOLD':
        base_exit = 50
    elif rec_generic == 'BUY':
        base_exit = 30

    # Adjust baseline by impact and certainty
    if impact == 'high':
        base_exit += 5
    elif impact == 'low':
        base_exit -= 5
    base_exit = max(0, min(100, base_exit))

    # Sentiment -> negative sentiment score
    if sentiment == 'bearish':
        neg_sent = 70
    elif sentiment == 'neutral':
        neg_sent = 50
    else:  # bullish
        neg_sent = 30

    # Fundamental risk approximation from typed risks and impact
    # Fundamental risks weigh more than technical warnings for exit.
    fundamental = 50 + min(fund_r, 5) * 7 + min(tech_r, 5) * 3  # up to +50
    if impact == 'high':
        fundamental += 10
    elif impact == 'low':
        fundamental -= 5
    fundamental = max(0, min(100, fundamental))

    # Compose recommendation and reasons
    # Favor fundamental catalysts when present; promote exits if both
    cat_bias = 0
    if fund_c >= 1 and tech_c >= 1:
        cat_bias = 5
    elif fund_c >= 1:
        cat_bias = 3
    elif tech_c >= 2:
        cat_bias = 2

    combined_hint = int(0.35 * tech_score + 0.30 * fundamental + 0.25 * neg_sent + 0.10 * base_exit + cat_bias)
    if combined_hint >= 70 or rec_generic == 'SELL':
        exit_rec = 'IMMEDIATE_EXIT'
    elif combined_hint >= 50:
        exit_rec = 'MONITOR'
    else:
        exit_rec = 'HOLD'

    reasons = []
    # Prefer up to 3 risk bullets, otherwise fallback to generic reasoning
    for r in risks_list[:3]:
        if isinstance(r, str) and r.strip():
            reasons.append(r.strip())
    if tech_reasons and (len(reasons) < 3):
        reasons.extend(tech_reasons[: max(0, 3 - len(reasons))])
    if not reasons and reasoning:
        reasons.append(reasoning[:120])

    summary = (
        f"{exit_rec.replace('_', ' ')} suggested. "
        f"Tech={tech_score}/100, FundRisk~{fundamental}/100, SentimentRisk~{neg_sent}/100. "
        f"Provider={ai_provider}."
    )

    stop_loss = 10
    if exit_rec == 'IMMEDIATE_EXIT' and certainty >= 70:
        stop_loss = 5
    elif exit_rec == 'MONITOR' and certainty >= 70:
        stop_loss = 8

    return {
        'exit_recommendation': exit_rec,
        'exit_urgency_score': max(base_exit, combined_hint),
        'exit_confidence': int(certainty),
        'technical_breakdown_score': tech_score,
        'fundamental_risk_score': fundamental,
        'negative_sentiment_score': neg_sent,
        'primary_exit_reasons': reasons,
        'hold_rationale': [] if exit_rec == 'IMMEDIATE_EXIT' else (['No urgent exit signals'] if exit_rec == 'HOLD' else ['Some warning signs present']),
        'risk_factors': risks_list if isinstance(risks_list, list) else [],
        'recommendation_summary': summary,
        'stop_loss_suggestion': stop_loss,
    }


def call_ai_for_exit_assessment(
    ticker: str,
    ai_provider: str,
    technical_data: Dict,
    news_context: str = ""
) -> Dict:
    """Use AI (Claude/Codex/Gemini) to assess comprehensive exit decision.

    Always returns a dict in the exit schema via normalization.
    """

    # Build comprehensive assessment prompt with temporal context
    current_date = datetime.now().strftime('%Y-%m-%d')
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    prompt = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 TEMPORAL CONTEXT - CRITICAL FOR AVOIDING TRAINING DATA BIAS 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**TODAY'S DATE**: {current_date}
**ANALYSIS TIMESTAMP**: {current_datetime}
**DATA SOURCE**: Real-time (fetched just now from yfinance)

⚠️  CRITICAL INSTRUCTIONS:
1. All technical data below is CURRENT as of {current_date}
2. Price and technical indicators are REAL-TIME (not historical)
3. DO NOT apply historical knowledge or training data about {ticker}
4. If any provided data contradicts your training knowledge, THE PROVIDED DATA IS CORRECT

This is a REAL-TIME exit assessment of CURRENT market conditions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMPREHENSIVE EXIT ASSESSMENT FOR {ticker}

You are an expert portfolio manager assessing whether to EXIT/SELL this stock position.

**TECHNICAL DATA:**
{json.dumps(technical_data, indent=2)}

**NEWS CONTEXT (if available):**
{news_context if news_context else "No recent news available - assess based on technical and fundamental factors only"}

**YOUR TASK:**
Provide a comprehensive EXIT assessment considering:
1. Technical breakdown risks (support breaks, bearish patterns)
2. Fundamental deterioration (earnings issues, debt concerns, margin compression)
3. Sentiment and news (regulatory issues, downgrades, negative catalysts)
4. Volume and momentum deterioration
5. Overall risk/reward at current levels

**RESPOND WITH ONLY THIS VALID JSON:**
{{
  "exit_recommendation": "IMMEDIATE_EXIT" or "HOLD" or "MONITOR",
  "exit_urgency_score": <0-100, higher = more urgent to exit>,
  "exit_confidence": <0-100, confidence in recommendation>,
  "technical_breakdown_score": <0-100>,
  "fundamental_risk_score": <0-100>,
  "negative_sentiment_score": <0-100>,
  "primary_exit_reasons": ["reason1", "reason2", "reason3"],
  "hold_rationale": ["reason1", "reason2"] (if HOLD/MONITOR),
  "risk_factors": ["risk1", "risk2"],
  "recommendation_summary": "<2-3 sentence clear recommendation>",
  "stop_loss_suggestion": <percentage below current, if applicable>
}}

**SCORING GUIDELINES:**
- exit_urgency_score > 75 = IMMEDIATE_EXIT (critical issues, high risk)
- exit_urgency_score 50-75 = MONITOR (warning signs, consider exit)
- exit_urgency_score < 50 = HOLD (no urgent exit signals)

    **IMPORTANT:**
    - Be decisive and clear
    - Assess even WITHOUT news (use technical + fundamental only if needed)
    - Consider if risk/reward justifies holding
    - Factor in opportunity cost (is capital better deployed elsewhere?)

    Respond with ONLY valid JSON, no markdown, no explanations outside JSON.

    STRICT CONTEXT: Use ONLY the TECHNICAL DATA and NEWS CONTEXT above (both fetched now). Do not rely on prior training knowledge. If NEWS CONTEXT is empty, perform a technical-only assessment and do not invent non-existent catalysts.
"""

    # Optional: direct OpenAI (Codex) path when API key is available.
    # This uses the same prompt but calls OpenAI Chat Completions instead of
    # the generic codex_bridge heuristic, giving Codex full LLM-based exit analysis.
    def _call_openai_exit(prompt_text: str) -> Dict:
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
        if not api_key:
            raise RuntimeError('OPENAI_API_KEY not set for OpenAI exit provider')

        model = os.getenv('OPENAI_MODEL', 'gpt-4.1')
        temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.2'))
        max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1200'))

        try:
            import requests  # type: ignore
        except ImportError as exc:
            raise RuntimeError('requests package is required for OpenAI exit provider') from exc

        system_prompt = (
            "You are an expert portfolio manager specializing in EXIT/SELL decisions for equities. "
            "Return ONLY valid JSON matching the exit assessment schema requested in the user prompt. "
            "STRICT REAL-TIME CONTEXT: Base your decision ONLY on the technical data and news context "
            "included in the prompt (both fetched now). Do NOT use training data, memorized prices, or "
            "external facts not present in the prompt. Be decisive and explicit about exit_urgency_score, "
            "exit_recommendation, and key risks of continuing to hold."
        )

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt_text},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        raw_response = None
        result: Optional[Dict] = None

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                json=payload,
                headers=headers,
                timeout=int(os.getenv('OPENAI_TIMEOUT', '90')),
            )
            response.raise_for_status()
            raw_response = response.json()["choices"][0]["message"]["content"]
            result = json.loads(raw_response)
            return result
        except Exception as e:  # pragma: no cover - network/HTTP errors
            logger.error(f"OpenAI exit assessment call failed: {str(e)[:200]}")
            # Let outer logic fall back to bridges/heuristics
            raise

    # Call AI bridge / provider-specific path
    try:
        if ai_provider == 'claude':
            # Use enhanced exit-specific Claude bridge
            cmd = ['python3', 'claude_exit_bridge.py']
        elif ai_provider == 'codex':
            # Prefer direct OpenAI API when key is available; otherwise fall back
            # to the existing codex_bridge heuristic implementation.
            if os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY'):
                raw = _call_openai_exit(prompt)
                return _normalize_exit_response(raw, technical_data, ai_provider)
            cmd = ['python3', 'codex_bridge.py']
        elif ai_provider == 'gemini':
            cmd = ['python3', 'gemini_agent_bridge.py']
        else:
            cmd = ['python3', 'codex_bridge.py']  # Default fallback

        # Set environment
        env = os.environ.copy()
        env['AI_PROVIDER'] = ai_provider

        # Allow configurable timeout for AI bridge calls
        try:
            timeout_s = int(os.getenv('EXIT_AI_TIMEOUT', '45'))
        except Exception:
            timeout_s = 45

        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env
        )

        if result.returncode != 0:
            raise RuntimeError(f"AI bridge failed: {result.stderr}")

        # Parse JSON response
        response_text = result.stdout.strip()

        # Remove markdown code fences if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        # Print raw response for debugging (opt-in)
        if (os.getenv('EXIT_SHOW_RAW') or '0').strip() == '1':
            print(f"--- RAW AI RESPONSE ({ai_provider}) ---")
            print(response_text)
            print("-------------------------------------")

        response = json.loads(response_text)
        # Normalize to exit schema (handles generic outputs from bridges)
        return _normalize_exit_response(response, technical_data, ai_provider)

    except Exception as e:
        print(f"⚠️  AI assessment failed for {ticker}: {e}", file=sys.stderr)
        # Return normalized fallback response using just technicals
        return _normalize_exit_response(
            {
                'recommendation': 'HOLD',
                'sentiment': 'neutral',
                'impact': 'medium',
                'risks': ["AI service error"],
                'reasoning': f"AI assessment unavailable: {str(e)[:100]}",
                'confidence': 40,
            },
            technical_data,
            ai_provider,
        )


# ============================================================================
# NEWS GATHERING (OPTIONAL)
# ============================================================================

def fetch_recent_news(ticker: str, hours_back: int = 72) -> str:
    """Fetch recent news for the ticker using existing news collection systems."""
    try:
        # Try to use existing news collector
        result = subprocess.run(
            ['python3', 'enhanced_india_finance_collector.py',
             '--tickers-file', '/tmp/exit_single_ticker.txt',
             '--hours-back', str(hours_back),
             '--max-articles', '5'],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Parse output for news
        if result.returncode == 0:
            # Look for news in output
            output = result.stdout
            if ticker.upper() in output:
                return output

        return ""

    except Exception as e:
        print(f"⚠️  News fetch failed for {ticker}: {e}", file=sys.stderr)
        return ""


# ============================================================================
# MAIN EXIT ASSESSMENT ENGINE
# ============================================================================

def assess_single_stock(ticker: str, ai_provider: str = 'codex', hours_back: int = 72, index_symbols: Optional[List[str]] = None, verbose: bool = False) -> Dict:
    """Perform comprehensive exit assessment for a single stock."""

    if verbose:
        print(f"\n{'='*80}", file=sys.stderr)
        print(f"📊 ASSESSING EXIT DECISION: {ticker}", file=sys.stderr)
        print(f"{'='*80}", file=sys.stderr)

    assessment = {
        'ticker': ticker,
        'timestamp': datetime.now().isoformat(),
        'technical_indicators': {},
        'technical_exit_score': 0,
        'technical_severity': 'NONE',
        'technical_reasons': [],
        'ai_assessment': {},
        'final_recommendation': 'HOLD',
        'final_exit_score': 0,
        'exit_confidence': 0,
        'summary': '',
        'decision_band': 'HOLD',
        'subscores': {},
        'levels': {},
        'coverage': {},
    }

    # Step 1: Technical Analysis
    if verbose:
        print(f"🔍 Fetching technical data for {ticker}...", file=sys.stderr)
    df = get_stock_data(ticker)

    data_issue = False
    if df is not None and not df.empty:
        if verbose:
            print(f"✅ Calculating technical indicators...", file=sys.stderr)
        indicators = calculate_technical_indicators(df)
        assessment['technical_indicators'] = indicators

        tech_score, tech_severity, tech_reasons = assess_technical_exit_signals(indicators)
        assessment['technical_exit_score'] = tech_score
        assessment['technical_severity'] = tech_severity
        assessment['technical_reasons'] = tech_reasons

        # Compute action levels (stop/trail/alerts)
        assessment['levels'] = _compute_levels(indicators)

        if verbose:
            print(f"📈 Technical Exit Score: {tech_score}/100 ({tech_severity})", file=sys.stderr)
            if tech_reasons:
                for reason in tech_reasons[:3]:
                    print(f"   • {reason}", file=sys.stderr)
    else:
        if verbose:
            print(f"⚠️  No technical data available for {ticker}", file=sys.stderr)
        # If infra is available but specific symbol has no data, treat as DATA-ISSUE
        if YFINANCE_AVAILABLE and PANDAS_AVAILABLE:
            data_issue = True
        else:
            data_issue = False  # global infra missing; do not penalize per-symbol

    if data_issue:
        assessment['final_recommendation'] = 'DATA-ISSUE'
        assessment['decision_band'] = 'DATA-ISSUE'
        assessment['final_exit_score'] = None  # exclude from averages
        assessment['exit_confidence'] = 0
        assessment['summary'] = 'Symbol not found or data unavailable (verify mapping; try .BO)'
        return assessment

    # Step 2: News Context (optional, non-blocking)
    if verbose:
        print(f"📰 Checking for recent news...", file=sys.stderr)
    news_context = ""  # Keeping it simple for now

    # Step 3: AI-Powered Comprehensive Assessment
    if verbose:
        print(f"🤖 Running AI exit assessment (provider: {ai_provider})...", file=sys.stderr)
    ai_result = call_ai_for_exit_assessment(
        ticker=ticker,
        ai_provider=ai_provider,
        technical_data=assessment['technical_indicators'],
        news_context=news_context
    )
    assessment['ai_assessment'] = ai_result

    # Step 4: Final Decision using new framework
    exit_urgency = ai_result.get('exit_urgency_score', 50)
    ai_confidence = ai_result.get('exit_confidence', 50)
    recommendation = ai_result.get('exit_recommendation', 'MONITOR')

    tech = max(0, min(100, assessment['technical_exit_score']))
    news = max(0, min(100, ai_result.get('negative_sentiment_score', 50)))
    fund = max(0, min(100, ai_result.get('fundamental_risk_score', 50)))
    liq = _compute_liquidity_risk(assessment['technical_indicators']) if assessment['technical_indicators'] else 70

    # Index tailwind adjustment (-10 to +10): uptrend => +5 tailwind, downtrend => -5 headwind
    index_adjust = 0
    try:
        if index_symbols and YFINANCE_AVAILABLE and PANDAS_AVAILABLE:
            # Use first symbol only for simple adjustment
            idx_sym = index_symbols[0]
            idx = get_stock_data(idx_sym, period='6mo')
            if idx is not None and not idx.empty:
                idx['SMA_20'] = idx['Close'].rolling(window=20).mean()
                idx['SMA_50'] = idx['Close'].rolling(window=50).mean()
                if idx['Close'].iloc[-1] > idx['SMA_50'].iloc[-1] and idx['SMA_20'].iloc[-1] > idx['SMA_50'].iloc[-1]:
                    index_adjust = 5  # tailwind
                elif idx['Close'].iloc[-1] < idx['SMA_50'].iloc[-1] and idx['SMA_20'].iloc[-1] < idx['SMA_50'].iloc[-1]:
                    index_adjust = -5  # headwind
    except Exception:
        index_adjust = 0

    base_score = (
        tech * NEW_WEIGHTS['tech'] +
        news * NEW_WEIGHTS['news'] +
        fund * NEW_WEIGHTS['fund'] +
        liq * NEW_WEIGHTS['liquidity']
    )
    combined_score = base_score - index_adjust  # subtract tailwind, add headwind

    # Coverage-based confidence
    coverage = {
        'price_hist': bool(assessment['technical_indicators']),
        'volume': bool(assessment['technical_indicators'].get('avg_volume_20')) if assessment['technical_indicators'] else False,
        'news_count': 0,  # placeholder
        'fundamentals': True,  # AI-proxy present
    }
    coverage_conf = int(round(100 * (sum(1 for k, v in coverage.items() if v) / 4), 0))
    assessment['coverage'] = coverage

    # Calibrated confidence (favor coverage)
    assessment['exit_confidence'] = coverage_conf

    assessment['subscores'] = {
        'tech': int(tech),
        'news': int(news),
        'fund': int(fund),
        'liquidity': int(liq),
        'index_tailwind': int(index_adjust),
        'urgency': int(exit_urgency),
    }

    assessment['final_exit_score'] = int(round(combined_score))

    # Decision band mapping
    score = assessment['final_exit_score']
    if score >= DECISION_BANDS['STRONG_EXIT']:
        decision_band = 'STRONG EXIT'
    elif score >= DECISION_BANDS['EXIT']:
        decision_band = 'EXIT'
    elif score >= DECISION_BANDS['MONITOR']:
        decision_band = 'MONITOR'
    elif score >= DECISION_BANDS['HOLD']:
        decision_band = 'HOLD'
    else:
        decision_band = 'STRONG HOLD'

    assessment['decision_band'] = decision_band

    # Maintain backward-compatible final_recommendation buckets
    if decision_band in ('STRONG EXIT', 'EXIT') or recommendation == 'IMMEDIATE_EXIT':
        assessment['final_recommendation'] = 'IMMEDIATE_EXIT'
    elif decision_band == 'MONITOR' or recommendation == 'MONITOR':
        assessment['final_recommendation'] = 'MONITOR'
    else:
        assessment['final_recommendation'] = 'HOLD'

    # Summary
    assessment['summary'] = ai_result.get('recommendation_summary', '') or ai_result.get('reasoning', '') or ''
    # Improve generic or empty summaries with concrete technical narrative
    try:
        summ = assessment['summary'] or ''
        generic = ('Detected 0 catalyst' in summ) or ('unknown source' in summ.lower()) or (len(summ) < 12)
        if generic or 'Tech=' in summ:
            sigs = assessment.get('technical_reasons', [])
            lv = assessment.get('levels', {})
            parts = []
            if sigs:
                parts.append('; '.join(sigs[:3]))
            if lv.get('stop'):
                parts.append(f"proposed stop {lv.get('stop')}")
            if lv.get('trail'):
                parts.append(f"trail {lv.get('trail')}")
            narrative = f"{assessment.get('decision_band','')}: " + (', '.join(parts) or 'No urgent technical exits detected')
            assessment['summary'] = narrative.strip()
    except Exception:
        pass

    if verbose:
        print(f"\n{'='*80}", file=sys.stderr)
        print(f"🎯 FINAL ASSESSMENT FOR {ticker}:", file=sys.stderr)
        print(f"   Recommendation: {assessment['final_recommendation']}", file=sys.stderr)
        print(f"   Exit Score: {assessment['final_exit_score']}/100", file=sys.stderr)
        print(f"   Confidence: {assessment['exit_confidence']}%", file=sys.stderr)
        print(f"   Summary: {assessment['summary']}", file=sys.stderr)
        print(f"{'='*80}\n", file=sys.stderr)

    return assessment


def process_exit_assessment(
    tickers_file: str,
    ai_provider: str = 'codex',
    hours_back: int = 72,
    quiet: bool = False,
    explain: Optional[str] = None,
    jsonl_path: Optional[str] = None,
    no_color: bool = False,
    max_tickers: Optional[int] = None,
    alerts_path: Optional[str] = None,
    fail_on_data_issue: bool = False,
    index_symbols: Optional[List[str]] = None,
):
    """Process exit assessments for all tickers in the file."""

    # Read tickers
    tickers = []
    with open(tickers_file, 'r') as f:
        for line in f:
            ticker = line.strip().upper()
            if ticker and not ticker.startswith('#'):
                tickers.append(ticker)

    if max_tickers is not None and max_tickers > 0:
        tickers = tickers[:max_tickers]

    if not tickers:
        print("❌ No tickers found in file", file=sys.stderr)
        return

    print(f"\n{'='*80}", file=sys.stderr)
    print(f"🚀 EXIT INTELLIGENCE ANALYZER", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(f"Processing {len(tickers)} tickers from {tickers_file}", file=sys.stderr)
    print(f"AI Provider: {ai_provider}", file=sys.stderr)
    print(f"News Window: {hours_back} hours", file=sys.stderr)
    print(f"Cutoffs: EXIT≥{DECISION_BANDS['EXIT']} | MONITOR {DECISION_BANDS['MONITOR']}-{DECISION_BANDS['EXIT']-1} | HOLD<{DECISION_BANDS['HOLD']}", file=sys.stderr)
    print(f"(w: Tech {int(NEW_WEIGHTS['tech']*100)}, News {int(NEW_WEIGHTS['news']*100)}, Fund {int(NEW_WEIGHTS['fund']*100)}, Lqd {int(NEW_WEIGHTS['liquidity']*100)})", file=sys.stderr)
    print(f"{'='*80}\n", file=sys.stderr)

    # Process each ticker
    assessments = []
    immediate_exit = []
    monitor = []
    hold = []

    # Prepare compact table header
    if not quiet:
        hdr = f"{'Ticker':<9} {'Score':<5} {'Decision':<12} {'Tech':<5} {'News':<5} {'Fund':<5} {'Lqd':<4} {'Conf':<5} {'Key Signals':<34} {'Action'}"
        print(hdr)

    for i, ticker in enumerate(tickers, 1):
        # Always show minimal progress, even in quiet mode
        if quiet:
            print(f"[{i}/{len(tickers)}] Processing {ticker}...", file=sys.stderr)
        else:
            print(f"\n[{i}/{len(tickers)}] Processing {ticker}...", file=sys.stderr)
        try:
            sys.stderr.flush()
        except Exception:
            pass

        try:
            assessment = assess_single_stock(ticker, ai_provider, hours_back, index_symbols=index_symbols, verbose=not quiet)
            assessments.append(assessment)

            # Categorize
            if assessment['final_recommendation'] == 'IMMEDIATE_EXIT':
                immediate_exit.append(ticker)
            elif assessment['final_recommendation'] == 'MONITOR':
                monitor.append(ticker)
            else:
                hold.append(ticker)

            # JSONL record (if enabled)
            if jsonl_path:
                ai = assessment.get('ai_assessment', {})
                _write_jsonl(jsonl_path, {
                    'run_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                    'asof': datetime.now().isoformat(),
                    'provider': ai_provider,
                    'ticker': assessment['ticker'],
                    'decision': assessment.get('decision_band'),
                    'score': assessment.get('final_exit_score'),
                    'confidence': assessment.get('exit_confidence'),
                    'subscores': assessment.get('subscores'),
                    'signals': assessment.get('technical_reasons', [])[:5],
                    'levels': assessment.get('levels', {}),
                    'coverage': assessment.get('coverage', {}),
                    'data': {},
                    'notes': assessment.get('summary', '')[:200],
                })

            # Alerts file (if enabled) for non-HOLD decisions
            if alerts_path and assessment['final_recommendation'] in ('IMMEDIATE_EXIT', 'MONITOR'):
                try:
                    os.makedirs(os.path.dirname(alerts_path), exist_ok=True)
                    with open(alerts_path, 'a') as af:
                        lv = assessment.get('levels', {})
                        af.write(f"{ticker}: stop={lv.get('stop','n/a')}; trail={lv.get('trail','n/a')}; alert={lv.get('alert_reclaim','n/a')}\n")
                except Exception as e:
                    print(f"⚠️  Failed to write alerts: {e}", file=sys.stderr)

            # Print compact row unless quiet
            if not quiet:
                subs = assessment.get('subscores', {})
                dec = assessment.get('decision_band', 'HOLD')
                dec_disp = _colorize(dec, use_color=(not no_color))
                sigs = assessment.get('technical_reasons', [])
                key_sig = "; ".join(sigs[:2])[:34]
                act_lv = assessment.get('levels', {})
                action = f"Trail: {act_lv.get('trail','n/a')}" if act_lv.get('trail') else ""
                score_val = assessment.get('final_exit_score')
                score_str = f"{score_val}" if isinstance(score_val, int) else '—'
                print(f"{ticker:<9} {score_str:<5} {dec_disp:<12} {subs.get('tech',0):<5} {subs.get('news',0):<5} {subs.get('fund',0):<5} {subs.get('liquidity',0):<4} {assessment.get('exit_confidence',0):<5} {key_sig:<34} {action}")

        except Exception as e:
            print(f"❌ Error processing {ticker}: {e}", file=sys.stderr)
            continue

    # Generate output files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 1. Immediate Exit List
    immediate_exit_file = os.path.join(_RECOMMENDATIONS_DIR, f'exit_assessment_immediate_{timestamp}.txt')
    with open(immediate_exit_file, 'w') as f:
        f.write(f"# IMMEDIATE EXIT RECOMMENDATIONS\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total stocks requiring immediate exit: {len(immediate_exit)}\n\n")
        for ticker in immediate_exit:
            f.write(f"{ticker}\n")

    # 2. Hold List (combined HOLD + MONITOR)
    hold_file = os.path.join(_RECOMMENDATIONS_DIR, f'exit_assessment_hold_{timestamp}.txt')
    with open(hold_file, 'w') as f:
        f.write(f"# HOLD / MONITOR RECOMMENDATIONS\n")
        f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Stocks safe to hold: {len(hold)}\n")
        f.write(f"# Stocks to monitor: {len(monitor)}\n\n")
        f.write(f"# HOLD:\n")
        for ticker in hold:
            f.write(f"{ticker}\n")
        f.write(f"\n# MONITOR (watch closely):\n")
        for ticker in monitor:
            f.write(f"{ticker}\n")

    # 3. Detailed CSV Report
    csv_file = os.path.join(_RECOMMENDATIONS_DIR, f'exit_assessment_detailed_{timestamp}.csv')
    with open(csv_file, 'w', newline='') as f:
        fieldnames = [
            'ticker', 'recommendation', 'decision_band', 'exit_score', 'confidence',
            'technical_score', 'technical_severity',
            'fundamental_risk', 'sentiment_risk', 'liquidity_risk', 'index_tailwind', 'urgency_score',
            'primary_reasons', 'summary'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for assessment in assessments:
            ai = assessment.get('ai_assessment', {})
            reasons = ', '.join(ai.get('primary_exit_reasons', [])[:3])
            subs = assessment.get('subscores', {})
            writer.writerow({
                'ticker': assessment['ticker'],
                'recommendation': assessment['final_recommendation'],
                'decision_band': assessment.get('decision_band'),
                'exit_score': assessment.get('final_exit_score'),
                'confidence': assessment.get('exit_confidence'),
                'technical_score': assessment.get('technical_exit_score'),
                'technical_severity': assessment.get('technical_severity'),
                'fundamental_risk': ai.get('fundamental_risk_score', subs.get('fund', 0)),
                'sentiment_risk': ai.get('negative_sentiment_score', subs.get('news', 0)),
                'liquidity_risk': subs.get('liquidity', 0),
                'index_tailwind': subs.get('index_tailwind', 0),
                'urgency_score': ai.get('exit_urgency_score', subs.get('urgency', 0)),
                'primary_reasons': reasons,
                'summary': (assessment.get('summary') or '')[:200]
            })

    # Print summary
    print(f"\n{'='*80}", file=sys.stderr)
    print(f"✅ EXIT ASSESSMENT COMPLETE", file=sys.stderr)
    print(f"{'='*80}", file=sys.stderr)
    print(f"\n📊 SUMMARY:", file=sys.stderr)
    print(f"   Total Assessed: {len(assessments)}", file=sys.stderr)
    print(f"   🚨 Immediate Exit: {len(immediate_exit)}", file=sys.stderr)
    print(f"   ⚠️  Monitor: {len(monitor)}", file=sys.stderr)
    print(f"   ✅ Hold: {len(hold)}", file=sys.stderr)

    print(f"\n📁 OUTPUT FILES:", file=sys.stderr)
    print(f"   • {immediate_exit_file} - Stocks to exit immediately", file=sys.stderr)
    print(f"   • {hold_file} - Stocks to hold/monitor", file=sys.stderr)
    print(f"   • {csv_file} - Detailed analysis report", file=sys.stderr)

    if immediate_exit:
        print(f"\n🚨 IMMEDIATE EXIT REQUIRED:", file=sys.stderr)
        for ticker in immediate_exit:
            for assessment in assessments:
                if assessment['ticker'] == ticker:
                    print(f"   • {ticker} (Score: {assessment['final_exit_score']}/100)", file=sys.stderr)
                    print(f"     {assessment['summary'][:100]}...", file=sys.stderr)

    # Print HOLD and MONITOR lists clearly on screen as well
    if hold:
        print(f"\n✅ HOLD LIST ({len(hold)}):", file=sys.stderr)
        for ticker in hold:
            for assessment in assessments:
                if assessment['ticker'] == ticker:
                    print(f"   • {ticker} (Score: {assessment['final_exit_score']}/100)", file=sys.stderr)
                    break

    if monitor:
        print(f"\n⚠️  MONITOR LIST ({len(monitor)}):", file=sys.stderr)
        for ticker in monitor:
            for assessment in assessments:
                if assessment['ticker'] == ticker:
                    print(f"   • {ticker} (Score: {assessment['final_exit_score']}/100)", file=sys.stderr)
                    break

    # Explain view for a single ticker if requested
    if explain:
        exp_t = explain.strip().upper()
        for a in assessments:
            if a['ticker'] == exp_t:
                subs = a.get('subscores', {})
                lv = a.get('levels', {})
                print(f"\n{exp_t} — Explain", file=sys.stderr)
                print(f"Tech: {subs.get('tech',0)}/100   Signals: {', '.join(a.get('technical_reasons', [])[:5])}", file=sys.stderr)
                print(f"News: {subs.get('news',0)}/100   Fund: {subs.get('fund',0)}/100   Lqd: {subs.get('liquidity',0)}/100", file=sys.stderr)
                print(f"Index Tailwind: {subs.get('index_tailwind',0)}", file=sys.stderr)
                print(f"ExitScore: {a.get('final_exit_score',0)} ({a.get('decision_band','')})    Confidence: {a.get('exit_confidence',0)}", file=sys.stderr)
                print(f"Levels:", file=sys.stderr)
                for k,v in lv.items():
                    print(f"  • {k}: {v}", file=sys.stderr)
                print(f"Notes: {a.get('summary','')}", file=sys.stderr)
                break

    # Flags file for DATA-ISSUE (if any)
    data_issues = [a['ticker'] for a in assessments if a.get('final_recommendation') == 'DATA-ISSUE']
    if data_issues:
        flags_file = os.path.join(_RECOMMENDATIONS_DIR, f'exit_assessment_flags_{timestamp}.txt')
        try:
            with open(flags_file, 'w') as ff:
                ff.write("# Tickers requiring manual check\n")
                for t in data_issues:
                    ff.write(f"{t}\n")
            print(f"   • {flags_file} - Manual check flags", file=sys.stderr)
        except Exception:
            pass

    if fail_on_data_issue and data_issues:
        sys.exit(2)

    print(f"\n{'='*80}\n", file=sys.stderr)


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Exit Intelligence Analyzer - Comprehensive sell/exit assessment system',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--tickers-file',
        default='exit.check.txt',
        help='File containing tickers to assess (default: exit.check.txt)'
    )

    parser.add_argument(
        '--ai-provider',
        choices=['claude', 'codex', 'gemini', 'auto'],
        default='codex',
        help='AI provider for assessment (default: codex)'
    )

    parser.add_argument(
        '--hours-back',
        type=int,
        default=72,
        help='Hours of news to consider (default: 72)'
    )

    parser.add_argument('--quiet', action='store_true', help='Compact table only')
    parser.add_argument('--explain', help='Show deep view for a specific ticker')
    parser.add_argument('--jsonl', dest='jsonl_path', help='Write JSONL records to this path')
    parser.add_argument('--no-color', action='store_true', help='Disable ANSI colors')
    parser.add_argument('--max', dest='max_tickers', type=int, help='Limit number of tickers processed')
    parser.add_argument('--alerts', dest='alerts_path', help='Write alerts (stops/trails) to file')
    parser.add_argument('--fail-on-data-issue', action='store_true', help='Return non-zero if DATA-ISSUE tickers exist')
    parser.add_argument('--index', dest='index_symbols', help='Comma-separated index symbols for regime filter (e.g., NIFTY50.NS)')

    args = parser.parse_args()

    # Load optional dynamic config produced by feedback updater
    _load_exit_ai_config()

    # Validate tickers file
    if not os.path.exists(args.tickers_file):
        print(f"❌ Tickers file not found: {args.tickers_file}", file=sys.stderr)
        sys.exit(1)

    # Parse index symbols
    index_symbols = None
    if args.index_symbols:
        index_symbols = [s.strip() for s in args.index_symbols.split(',') if s.strip()]

    # Default JSONL path if requested but not provided
    jsonl_path = args.jsonl_path
    if jsonl_path is None and os.environ.get('EXIT_JSONL', '').lower() in ('1', 'true', 'yes'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        jsonl_path = os.path.join(_RECOMMENDATIONS_DIR, f'exit_assessment_detailed_{timestamp}.jsonl')

    # Run assessment
    process_exit_assessment(
        tickers_file=args.tickers_file,
        ai_provider=args.ai_provider,
        hours_back=args.hours_back,
        quiet=args.quiet,
        explain=args.explain,
        jsonl_path=jsonl_path,
        no_color=args.no_color,
        max_tickers=args.max_tickers,
        alerts_path=args.alerts_path,
        fail_on_data_issue=args.fail_on_data_issue,
        index_symbols=index_symbols,
    )


if __name__ == '__main__':
    main()
