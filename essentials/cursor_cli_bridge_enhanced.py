#!/usr/bin/env python3
"""
Enhanced Cursor CLI Bridge - Comprehensive Quant + News Analysis
AI receives BOTH news AND market data for complete analysis

This bridge provides AI with:
1. News (headline, content)
2. Market data (volume, price, market cap)
3. Technical indicators (momentum, RSI, etc.)
4. Volume deviations
5. News magnitude vs market cap ratio

AI then does COMPLETE analysis combining all factors.
"""

import sys
import json
import re
import os
import subprocess
from typing import Dict, Optional
import yfinance as yf
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def parse_analysis_prompt(prompt: str) -> Dict:
    """Extract key information from the analysis prompt."""
    info = {
        'ticker': 'UNKNOWN',
        'headline': '',
        'url': '',
        'snippet': '',
        'source': '',
        'deal_value_cr': 0
    }
    
    # Extract ticker
    ticker_match = re.search(r'Ticker:\s*([A-Z]+)', prompt)
    if ticker_match:
        info['ticker'] = ticker_match.group(1)
    
    # Extract headline
    headline_match = re.search(r'Headline:\s*(.+?)(?:\n|$)', prompt)
    if headline_match:
        info['headline'] = headline_match.group(1).strip()
    
    # Extract URL
    url_match = re.search(r'(?:URL|Link):\s*(https?://[^\s\n]+)', prompt)
    if url_match:
        info['url'] = url_match.group(1)
    
    # Extract snippet
    snippet_match = re.search(r'Snippet:\s*(.+?)(?:\n\n|$)', prompt, re.DOTALL)
    if snippet_match:
        info['snippet'] = snippet_match.group(1).strip()
    
    # Extract source
    source_match = re.search(r'Source:\s*(.+?)(?:\n|$)', prompt)
    if source_match:
        info['source'] = source_match.group(1).strip()
    
    # Extract deal value if present
    text = info['headline'] + ' ' + info['snippet']
    crore_match = re.search(r'₹\s*(\d+(?:,\d+)*)\s*(?:crore|cr)', text.lower())
    if crore_match:
        info['deal_value_cr'] = float(crore_match.group(1).replace(',', ''))
    
    return info


def fetch_market_data(ticker: str) -> Dict:
    """Fetch real-time market data and quant metrics for the ticker."""
    try:
        # Add .NS suffix for NSE stocks
        yf_ticker = f"{ticker}.NS"
        print(f"   Querying yfinance for: {yf_ticker}", file=sys.stderr)
        stock = yf.Ticker(yf_ticker)
        
        # First, validate ticker by checking info
        print(f"   Fetching company info...", file=sys.stderr)
        info = stock.info
        
        # Check if valid ticker (yfinance returns empty/minimal dict for invalid tickers)
        if not info or len(info) < 5:
            print(f"   ❌ Invalid ticker {yf_ticker}: No company info available", file=sys.stderr)
            return get_fallback_market_data()
        
        company_name = info.get('longName', info.get('shortName', 'N/A'))
        market_cap = info.get('marketCap', 0)
        
        print(f"   ✅ Valid ticker: {company_name}", file=sys.stderr)
        
        if market_cap == 0:
            print(f"   ⚠️  Warning: Zero market cap in info dict", file=sys.stderr)
        else:
            print(f"   Market cap: ₹{market_cap/1e7:.0f} crores", file=sys.stderr)
        
        # Get historical data (90 days)
        print(f"   Fetching price history (90 days)...", file=sys.stderr)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        hist = stock.history(start=start_date, end=end_date)
        
        if hist.empty:
            print(f"   ⚠️  No price history available (market closed or weekend)", file=sys.stderr)
            print(f"   Using fallback with info data only", file=sys.stderr)
            # Use info dict for basic data
            return {
                'price': info.get('currentPrice', info.get('previousClose', 0)),
                'volume': 0,
                'avg_volume_20': info.get('averageVolume', 0),
                'avg_volume_60': info.get('averageVolume', 0),
                'volume_ratio': 1.0,
                'volume_deviation_pct': 0,
                'volume_spike': False,
                'momentum_3d': 0,
                'momentum_20d': 0,
                'momentum_60d': 0,
                'atr': 0,
                'rsi': 50,
                'market_cap_cr': market_cap / 10000000 if market_cap > 0 else 0,
                'data_available': True  # We have SOME data
            }
        
        if len(hist) < 20:
            print(f"   ⚠️  Only {len(hist)} days of data (need 20+ for full metrics)", file=sys.stderr)
            # Use what we have but with warnings
        
        print(f"   ✅ Fetched {len(hist)} days of price history", file=sys.stderr)
        
        # Calculate key metrics
        current_price = float(hist['Close'].iloc[-1])
        current_volume = float(hist['Volume'].iloc[-1])
        avg_volume_20 = float(hist['Volume'].tail(20).mean())
        avg_volume_60 = float(hist['Volume'].tail(60).mean() if len(hist) >= 60 else avg_volume_20)
        
        # Validate data
        if current_price == 0:
            print(f"   ❌ Zero price detected! Data may be corrupted", file=sys.stderr)
            return get_fallback_market_data()
        
        # Volume deviation (critical!)
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0
        volume_deviation_pct = ((current_volume - avg_volume_20) / avg_volume_20 * 100) if avg_volume_20 > 0 else 0
        
        # Momentum calculations
        close_3d_ago = float(hist['Close'].iloc[-4]) if len(hist) >= 4 else current_price
        close_20d_ago = float(hist['Close'].iloc[-21]) if len(hist) >= 21 else current_price
        close_60d_ago = float(hist['Close'].iloc[-61]) if len(hist) >= 61 else current_price
        
        momentum_3 = ((current_price - close_3d_ago) / close_3d_ago * 100) if close_3d_ago > 0 else 0
        momentum_20 = ((current_price - close_20d_ago) / close_20d_ago * 100) if close_20d_ago > 0 else 0
        momentum_60 = ((current_price - close_60d_ago) / close_60d_ago * 100) if close_60d_ago > 0 else 0
        
        # ATR (volatility)
        high = hist['High'].tail(20)
        low = hist['Low'].tail(20)
        close = hist['Close'].tail(20)
        tr = pd.DataFrame({
            'hl': high - low,
            'hc': abs(high - close.shift()),
            'lc': abs(low - close.shift())
        }).max(axis=1)
        atr = float(tr.mean())
        
        # RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = float(rsi.iloc[-1]) if not rsi.empty and not pd.isna(rsi.iloc[-1]) else 50
        
        # Use market cap from info dict (more reliable)
        market_cap_cr = market_cap / 10000000 if market_cap > 0 else 0  # Convert to crores
        
        print(f"   ✅ Metrics calculated successfully", file=sys.stderr)
        
        return {
            'price': current_price,
            'volume': current_volume,
            'avg_volume_20': avg_volume_20,
            'avg_volume_60': avg_volume_60,
            'volume_ratio': volume_ratio,
            'volume_deviation_pct': volume_deviation_pct,
            'volume_spike': volume_ratio > 1.5,  # Flag if volume is 50%+ above average
            'momentum_3d': momentum_3,
            'momentum_20d': momentum_20,
            'momentum_60d': momentum_60,
            'atr': atr,
            'rsi': current_rsi,
            'market_cap_cr': market_cap_cr,
            'data_available': True
        }
        
    except Exception as e:
        print(f"   ❌ Market data fetch failed for {ticker}: {str(e)[:100]}", file=sys.stderr)
        import traceback
        print(f"   Error details: {traceback.format_exc()[:200]}", file=sys.stderr)
        return get_fallback_market_data()


def get_fallback_market_data() -> Dict:
    """Return default values when market data is unavailable."""
    return {
        'price': 0,
        'volume': 0,
        'avg_volume_20': 0,
        'avg_volume_60': 0,
        'volume_ratio': 1.0,
        'volume_deviation_pct': 0,
        'volume_spike': False,
        'momentum_3d': 0,
        'momentum_20d': 0,
        'momentum_60d': 0,
        'atr': 0,
        'rsi': 50,
        'market_cap_cr': 0,
        'data_available': False
    }


def analyze_with_cursor_cli_enhanced(prompt: str, info: Dict, market_data: Dict) -> Dict:
    """
    Enhanced Cursor agent analysis with COMPLETE data:
    - News (headline, content)
    - Market data (volume, price, momentum)
    - Quant indicators (RSI, ATR, volume deviation)
    - Impact ratio (news magnitude vs market cap)
    """
    
    cursor_cmd = os.getenv('CURSOR_CLI_PATH', 'cursor')
    cursor_agent_cmd = [cursor_cmd, 'agent']
    
    # Calculate impact ratio (news magnitude vs market cap)
    impact_ratio = 0
    if info['deal_value_cr'] > 0 and market_data['market_cap_cr'] > 0:
        impact_ratio = (info['deal_value_cr'] / market_data['market_cap_cr']) * 100
    
    # Build COMPREHENSIVE analysis prompt
    analysis_prompt = f"""You are an expert quant + fundamental analyst for Indian stock markets.

**COMPREHENSIVE ANALYSIS REQUEST:**

**NEWS:**
- Ticker: {info['ticker']}
- Headline: {info['headline']}
- Content: {info['snippet']}
- Deal Value: ₹{info['deal_value_cr']:.0f} crores
- Source: {info['source']}

**MARKET DATA:**
- Current Price: ₹{market_data['price']:.2f}
- Market Cap: ₹{market_data['market_cap_cr']:.0f} crores
- Current Volume: {market_data['volume']:,.0f}
- Avg Volume (20d): {market_data['avg_volume_20']:,.0f}
- Volume Ratio: {market_data['volume_ratio']:.2f}x
- Volume Deviation: {market_data['volume_deviation_pct']:+.1f}%
- Volume Spike: {"YES ⚠️" if market_data['volume_spike'] else "No"}

**MOMENTUM:**
- 3-day: {market_data['momentum_3d']:+.2f}%
- 20-day: {market_data['momentum_20d']:+.2f}%
- 60-day: {market_data['momentum_60d']:+.2f}%

**TECHNICAL:**
- RSI(14): {market_data['rsi']:.1f}
- ATR(20): {market_data['atr']:.2f}

**IMPACT ANALYSIS:**
- News Magnitude vs Market Cap: {impact_ratio:.2f}%

**YOUR TASK:**

Analyze ALL the above data together and provide a comprehensive score.

Consider:
1. **News Impact**: Deal size relative to market cap (high impact = higher score)
2. **Volume Confirmation**: Volume spike + news = strong confirmation (boost score)
3. **Momentum Alignment**: Positive news + positive momentum = synergy (boost score)
4. **Technical Setup**: RSI, momentum trends support the news direction
5. **Magnitude**: Larger deals relative to market cap deserve higher scores

**SCORING LOGIC:**
- Base score from news quality (40-60)
- Add +20 if volume spike confirms news (volume ratio > 1.5x)
- Add +15 if positive momentum (20d > 3%)
- Add +10 if deal size > 5% of market cap
- Add +5 if RSI shows room to run (<70 for bullish, >30 for bearish)

Return ONLY valid JSON (no markdown):

{{
  "score": <0-100 integer based on above>,
  "sentiment": "<bullish|bearish|neutral>",
  "impact": "<high|medium|low>",
  "catalysts": [<list of specific catalysts from news>],
  "deal_value_cr": {info['deal_value_cr']},
  "risks": [<list of risk keywords>],
  "certainty": <0-100 based on data quality and confirmation>,
  "recommendation": "<STRONG BUY|BUY|ACCUMULATE|HOLD|SELL>",
  "reasoning": "<2-3 sentences explaining score considering news + volume + momentum + impact ratio>",
  "expected_move_pct": <expected price move % considering all factors>,
  "confidence": <0-100>,
  "volume_confirmation": <true|false>,
  "momentum_alignment": <true|false>,
  "impact_ratio_pct": {impact_ratio:.2f}
}}

**CRITICAL**: Your score MUST reflect the complete picture:
- Great news + volume spike + positive momentum = 85-95
- Great news + no volume + weak momentum = 65-75
- Good news + volume spike = 75-85
- Weak news regardless of technicals = 40-55"""

    try:
        print(f"🤖 Calling Cursor agent for {info['ticker']} with COMPLETE data...", file=sys.stderr)
        
        # Method 1: Command argument
        result = subprocess.run(
            cursor_agent_cmd + [analysis_prompt],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Method 2: Fallback to stdin
        if result.returncode != 0 or not result.stdout.strip():
            print(f"⚠️  Trying stdin method...", file=sys.stderr)
            result = subprocess.run(
                cursor_agent_cmd,
                input=analysis_prompt,
                capture_output=True,
                text=True,
                timeout=60
            )
        
        if result.returncode != 0:
            print(f"⚠️  Cursor agent error: {result.stderr[:200]}", file=sys.stderr)
            return fallback_analysis_enhanced(prompt, info, market_data)
        
        response_text = result.stdout.strip()
        
        if not response_text:
            return fallback_analysis_enhanced(prompt, info, market_data)
        
        # Extract JSON
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'\s*```$', '', response_text, flags=re.MULTILINE)
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        result_json = json.loads(response_text)
        
        # Ensure all fields
        result_json.setdefault('score', 50)
        result_json.setdefault('volume_confirmation', market_data['volume_spike'])
        result_json.setdefault('momentum_alignment', market_data['momentum_20d'] > 3)
        result_json.setdefault('impact_ratio_pct', impact_ratio)
        
        print(f"✅ Cursor agent analysis complete for {info['ticker']}", file=sys.stderr)
        return result_json
        
    except Exception as e:
        print(f"⚠️  Cursor agent error: {e}", file=sys.stderr)
        return fallback_analysis_enhanced(prompt, info, market_data)


def fallback_analysis_enhanced(prompt: str, info: Dict, market_data: Dict) -> Dict:
    """Enhanced fallback that considers market data too."""
    print(f"⚠️  Using enhanced fallback for {info['ticker']}", file=sys.stderr)
    
    text = (info['headline'] + ' ' + info['snippet']).lower()
    
    # Base score from news
    score = 50
    sentiment = 'neutral'
    catalysts = []
    
    # News patterns
    if re.search(r'profit|earnings|beat|strong', text):
        catalysts.append('earnings')
        score += 15
        sentiment = 'bullish'
    if re.search(r'acquir|merger|deal.*crore', text):
        catalysts.append('M&A')
        score += 20
        sentiment = 'bullish'
    if re.search(r'contract|order|wins', text):
        catalysts.append('contract')
        score += 18
        sentiment = 'bullish'
    
    # VOLUME CONFIRMATION BOOST
    if market_data['volume_spike']:
        score += 20  # Major boost for volume confirmation!
        print(f"  ✅ Volume spike detected: {market_data['volume_ratio']:.2f}x", file=sys.stderr)
    
    # MOMENTUM ALIGNMENT
    if market_data['momentum_20d'] > 3:
        score += 15  # Positive momentum
        print(f"  ✅ Positive momentum: {market_data['momentum_20d']:.1f}%", file=sys.stderr)
    elif market_data['momentum_20d'] < -3:
        score -= 10  # Negative momentum
    
    # IMPACT RATIO (news magnitude vs market cap)
    if info['deal_value_cr'] > 0 and market_data['market_cap_cr'] > 0:
        impact_ratio = (info['deal_value_cr'] / market_data['market_cap_cr']) * 100
        if impact_ratio > 5:
            score += 10
            print(f"  ✅ High impact ratio: {impact_ratio:.1f}%", file=sys.stderr)
    else:
        impact_ratio = 0
    
    # RSI consideration
    if market_data['rsi'] < 70 and sentiment == 'bullish':
        score += 5  # Room to run
    
    score = max(0, min(100, score))
    certainty = 70 if market_data['data_available'] else 40
    
    # Recommendation
    if score >= 85 and market_data['volume_spike']:
        recommendation = 'STRONG BUY'
    elif score >= 70:
        recommendation = 'BUY'
    elif score >= 55:
        recommendation = 'ACCUMULATE'
    else:
        recommendation = 'HOLD'
    
    reasoning = f"Score: {score}. {len(catalysts)} catalyst(s). "
    if market_data['volume_spike']:
        reasoning += f"Volume spike {market_data['volume_ratio']:.1f}x confirms news. "
    if market_data['momentum_20d'] > 3:
        reasoning += f"Positive momentum {market_data['momentum_20d']:.1f}%. "
    if impact_ratio > 5:
        reasoning += f"High impact ratio {impact_ratio:.1f}%. "
    
    return {
        'score': score,
        'sentiment': sentiment,
        'impact': 'high' if score >= 75 else 'medium' if score >= 50 else 'low',
        'catalysts': catalysts,
        'deal_value_cr': info['deal_value_cr'],
        'risks': ['market_risk'],
        'certainty': certainty,
        'recommendation': recommendation,
        'reasoning': reasoning,
        'expected_move_pct': (score - 50) / 5 if sentiment == 'bullish' else 0,
        'confidence': certainty,
        'volume_confirmation': market_data['volume_spike'],
        'momentum_alignment': market_data['momentum_20d'] > 3,
        'impact_ratio_pct': impact_ratio
    }


def main():
    """Main entry point."""
    prompt = sys.stdin.read()
    
    # Debug header
    print("=" * 70, file=sys.stderr)
    print("🔍 CURSOR BRIDGE DEBUG - START", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    if not prompt.strip():
        print("❌ ERROR: Empty prompt received!", file=sys.stderr)
        print(json.dumps({
            'score': 50,
            'sentiment': 'neutral',
            'recommendation': 'HOLD',
            'reasoning': 'No prompt provided'
        }))
        return
    
    print(f"📥 Prompt received ({len(prompt)} chars)", file=sys.stderr)
    print(f"   Preview: {prompt[:150]}...", file=sys.stderr)
    
    # Parse prompt
    info = parse_analysis_prompt(prompt)
    
    print(f"\n📊 Parsed Information:", file=sys.stderr)
    print(f"   Ticker: {info['ticker']}", file=sys.stderr)
    print(f"   Headline: {info['headline'][:80]}", file=sys.stderr)
    print(f"   Deal Value: ₹{info['deal_value_cr']:.0f} cr", file=sys.stderr)
    print(f"   Source: {info['source']}", file=sys.stderr)
    
    # Fetch market data
    print(f"\n📊 Fetching market data for {info['ticker']}...", file=sys.stderr)
    market_data = fetch_market_data(info['ticker'])
    
    if market_data['data_available']:
        print(f"\n✅ Market Data Successfully Fetched:", file=sys.stderr)
        print(f"   Price: ₹{market_data['price']:.2f}", file=sys.stderr)
        print(f"   Market Cap: ₹{market_data['market_cap_cr']:.0f} cr", file=sys.stderr)
        print(f"   Volume Ratio: {market_data['volume_ratio']:.2f}x", file=sys.stderr)
        print(f"   Volume Spike: {'YES ⚠️' if market_data['volume_spike'] else 'No'}", file=sys.stderr)
        print(f"   Momentum (20d): {market_data['momentum_20d']:+.1f}%", file=sys.stderr)
        print(f"   RSI: {market_data['rsi']:.1f}", file=sys.stderr)
    else:
        print(f"\n⚠️  WARNING: Using fallback market data (no real data available)", file=sys.stderr)
    
    # Analyze with Cursor agent (with complete data)
    print(f"\n🤖 Calling Cursor agent for analysis...", file=sys.stderr)
    result = analyze_with_cursor_cli_enhanced(prompt, info, market_data)
    
    print(f"\n✅ Analysis Complete:", file=sys.stderr)
    print(f"   Score: {result.get('score', 0):.1f}/100", file=sys.stderr)
    print(f"   Sentiment: {result.get('sentiment', 'unknown')}", file=sys.stderr)
    print(f"   Recommendation: {result.get('recommendation', 'UNKNOWN')}", file=sys.stderr)
    print("=" * 70, file=sys.stderr)
    
    # Output JSON
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
