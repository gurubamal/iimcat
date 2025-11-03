# YFinance Data Fetching Strategy - Comprehensive Plan

## 🎯 Goal
After valid news is fetched, fetch **exactly the right data** from yfinance and pass **NEWS + DATA** together to AI for comprehensive analysis.

## 📊 Data Categories & Priority

### **TIER 1: Essential Data (Always Fetch)**
These are critical for any news analysis:

1. **Current Price Context**
   - Current/Last price
   - Previous close
   - Day open
   - Day high/low
   - **Timestamp** (when fetched)
   - **Source** (fast_info vs history)

2. **Basic Technical Indicators**
   - **RSI (14)** - Overbought/oversold levels
   - **20-day SMA** - Short-term trend
   - **50-day SMA** - Medium-term trend
   - **Price vs MA %** - Distance from support/resistance

3. **Volume Analysis**
   - Current volume
   - 20-day average volume
   - Volume ratio (current vs average)
   - Volume trend (increasing/decreasing)

4. **Recent Momentum**
   - 5-day return %
   - 10-day return %
   - Recent trend direction

### **TIER 2: Important Context (Usually Fetch)**
Important for quality analysis but not always critical:

5. **Extended Technical Indicators**
   - **200-day SMA** - Long-term trend
   - **MACD** - Momentum direction
   - **Bollinger Bands** - Volatility bounds
   - **ATR (14)** - Volatility measure

6. **Price Levels**
   - 52-week high/low
   - Distance from 52W high/low %
   - Recent swing high/low (20-day)
   - Support/Resistance estimates

7. **Market Context**
   - Market cap (from info)
   - Shares outstanding
   - Float (if available)

### **TIER 3: Conditional Data (Fetch Based on News Type)**

8. **For Earnings News:**
   - Trailing P/E
   - Forward P/E (if available)
   - EPS (trailing)
   - Quarterly earnings history (last 4Q)
   - Revenue growth trends

9. **For Dividend News:**
   - Dividend yield
   - Dividend rate
   - Payout ratio
   - Ex-dividend date
   - Dividend history

10. **For M&A/Institutional News:**
    - Institutional ownership %
    - Top institutional holders
    - Recent insider transactions (if available)
    - Major shareholders

11. **For Sector/Industry News:**
    - Sector name
    - Industry name
    - Beta (market sensitivity)
    - Correlation with sector ETF

### **TIER 4: Advanced (Optional/Future)**

12. **Fundamental Ratios** (if available without extra API calls)
    - P/B ratio
    - Debt/Equity
    - Current ratio
    - ROE, ROA

13. **Options Data** (if high volume stock)
    - Implied volatility
    - Put/Call ratio
    - Options volume

## 🏗️ Data Fetching Architecture

### **Workflow:**

```
┌─────────────────────────────────────────┐
│ 1. NEWS ARRIVES                         │
│    Source: Google News, RSS, etc.       │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 2. QUALITY CHECK                        │
│    ✓ Is news substantive?               │
│    ✓ Has catalyst?                      │
│    ✓ Not advertorial?                   │
└────────────┬────────────────────────────┘
             ↓ (if quality)
┌─────────────────────────────────────────┐
│ 3. CLASSIFY NEWS TYPE                   │
│    • Earnings                           │
│    • Dividend                           │
│    • M&A/Corporate Action               │
│    • Sector/Industry                    │
│    • General                            │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 4. FETCH YFINANCE DATA                  │
│    ├─ TIER 1: Essential (all cases)     │
│    ├─ TIER 2: Important (most cases)    │
│    └─ TIER 3: Conditional (based on     │
│               news type)                │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 5. BUILD COMPREHENSIVE CONTEXT          │
│    ├─ News Content                      │
│    ├─ Real-Time Price Data              │
│    ├─ Technical Indicators              │
│    ├─ Fundamental Context               │
│    └─ Explicit AI Instructions          │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 6. AI ANALYZES NEWS + DATA              │
│    (using ONLY provided data)           │
└────────────┬────────────────────────────┘
             ↓
┌─────────────────────────────────────────┐
│ 7. OUTPUT RESULTS                       │
│    CSV with all data + analysis         │
└─────────────────────────────────────────┘
```

## 📦 Data Package Structure

```python
{
    # NEWS CONTENT
    "news": {
        "headline": "...",
        "full_text": "...",
        "url": "...",
        "published_date": "...",
        "source": "...",
        "news_type": "earnings|dividend|ma|sector|general"
    },

    # TIER 1: ESSENTIAL DATA (always included)
    "price": {
        "current": 1234.56,
        "previous_close": 1220.00,
        "day_open": 1225.00,
        "day_high": 1240.00,
        "day_low": 1215.00,
        "timestamp": "2025-11-03T10:30:00",
        "source": "fast_info|history",
        "currency": "INR"
    },

    "technical": {
        "rsi_14": 55.2,
        "sma_20": 1200.00,
        "sma_50": 1180.00,
        "price_vs_sma20_pct": 2.88,
        "price_vs_sma50_pct": 4.62,
        "volume_current": 1250000,
        "volume_avg_20d": 1000000,
        "volume_ratio": 1.25,
        "momentum_5d_pct": 1.2,
        "momentum_10d_pct": 3.5,
        "trend_recent": "up|down|sideways"
    },

    # TIER 2: IMPORTANT CONTEXT (usually included)
    "extended_technical": {
        "sma_200": 1150.00,
        "macd": 12.5,
        "macd_signal": 10.2,
        "bb_upper": 1260.00,
        "bb_lower": 1140.00,
        "atr_14": 25.5,
        "week_52_high": 1350.00,
        "week_52_low": 980.00,
        "distance_from_52w_high_pct": -8.5,
        "distance_from_52w_low_pct": 26.0
    },

    "market_context": {
        "market_cap": 850000000000,  # in base currency
        "market_cap_formatted": "₹8.5 lakh crore",
        "shares_outstanding": 640000000,
        "float": 320000000  # if available
    },

    # TIER 3: CONDITIONAL (based on news type)
    "earnings_data": {  # Only if news_type == "earnings"
        "trailing_pe": 22.5,
        "forward_pe": 20.1,
        "eps_trailing": 55.0,
        "quarterly_earnings": [
            {"quarter": "Q2 2025", "eps": 14.2, "revenue": 2.1e11},
            {"quarter": "Q1 2025", "eps": 13.8, "revenue": 2.0e11},
            # ...
        ],
        "earnings_growth_yoy": 15.2
    },

    "dividend_data": {  # Only if news_type == "dividend"
        "dividend_yield": 1.8,
        "dividend_rate": 22.0,
        "payout_ratio": 35.0,
        "ex_dividend_date": "2025-11-10",
        "dividend_history": [...]
    },

    "institutional_data": {  # Only if news_type == "ma"
        "institutional_ownership_pct": 68.5,
        "top_holders": [...],
        "insider_transactions": [...]
    },

    # CALCULATED LEVELS (based on real-time data)
    "trading_levels": {
        "entry_zone_low": 1210.00,
        "entry_zone_high": 1230.00,
        "target_conservative": 1280.00,
        "target_aggressive": 1320.00,
        "stop_loss": 1190.00,
        "risk_reward_ratio": 2.5
    },

    # METADATA
    "metadata": {
        "ticker": "RELIANCE",
        "symbol_yfinance": "RELIANCE.NS",
        "fetch_timestamp": "2025-11-03T10:30:00",
        "data_quality": "complete|partial|minimal",
        "fetch_duration_ms": 1250
    }
}
```

## ⚡ Performance Optimization

### **Single API Call Strategy:**

Instead of multiple calls:
```python
# ❌ BAD: Multiple calls
ticker.history(period='1mo')  # For price
ticker.history(period='6mo')  # For MA
ticker.info                   # For fundamentals
```

Use single optimized call:
```python
# ✅ GOOD: Single comprehensive call
ticker.history(period='6mo')  # Gets all historical data needed
ticker.fast_info             # Quick current price
ticker.info                  # Only if needed for fundamentals
```

### **Caching Strategy:**

```python
# Cache structure
{
    "RELIANCE": {
        "historical_data": df,  # 6-month history
        "fetched_at": timestamp,
        "ttl": 300,  # 5 minutes
        "info_data": {...},
        "info_fetched_at": timestamp,
        "info_ttl": 3600  # 1 hour (fundamentals change slowly)
    }
}
```

### **Rate Limiting:**

```python
import time
from collections import deque

class YFinanceRateLimiter:
    def __init__(self, max_requests=10, window_seconds=60):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = deque()

    def wait_if_needed(self):
        now = time.time()
        # Remove old requests outside window
        while self.requests and self.requests[0] < now - self.window:
            self.requests.popleft()

        # If at limit, wait
        if len(self.requests) >= self.max_requests:
            sleep_time = self.window - (now - self.requests[0])
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.requests.append(now)
```

## 🎨 News Type Classification

```python
def classify_news_type(headline: str, full_text: str) -> str:
    """Classify news to determine what data to fetch."""

    text = (headline + " " + full_text).lower()

    # Earnings indicators
    earnings_keywords = ['earnings', 'profit', 'revenue', 'q1', 'q2', 'q3', 'q4',
                         'quarterly', 'eps', 'pat', 'net income', 'results']
    if any(kw in text for kw in earnings_keywords):
        return 'earnings'

    # Dividend indicators
    dividend_keywords = ['dividend', 'payout', 'interim dividend', 'final dividend',
                        'dividend yield', 'dividend announcement']
    if any(kw in text for kw in dividend_keywords):
        return 'dividend'

    # M&A indicators
    ma_keywords = ['merger', 'acquisition', 'buyout', 'takeover', 'acquires',
                   'stake', 'institutional', 'fii', 'dii', 'promoter']
    if any(kw in text for kw in ma_keywords):
        return 'ma'

    # Sector/Industry indicators
    sector_keywords = ['sector', 'industry', 'nifty', 'sensex', 'index',
                      'pharma stocks', 'it stocks', 'bank stocks']
    if any(kw in text for kw in sector_keywords):
        return 'sector'

    return 'general'
```

## 📋 Implementation Plan

### **Phase 1: Core Data Fetcher (TIER 1 + 2)**

Create `enhanced_yfinance_fetcher.py`:

```python
class ComprehensiveDataFetcher:
    """Fetch all needed data from yfinance efficiently."""

    def fetch_for_news_analysis(self, ticker: str, news_type: str) -> dict:
        """Fetch appropriate data based on news type."""

        # TIER 1: Essential (always)
        data = {
            'price': self._fetch_price_data(ticker),
            'technical': self._fetch_technical_indicators(ticker),
        }

        # TIER 2: Important (usually)
        data['extended_technical'] = self._fetch_extended_technical(ticker)
        data['market_context'] = self._fetch_market_context(ticker)

        # TIER 3: Conditional
        if news_type == 'earnings':
            data['earnings_data'] = self._fetch_earnings_data(ticker)
        elif news_type == 'dividend':
            data['dividend_data'] = self._fetch_dividend_data(ticker)
        elif news_type == 'ma':
            data['institutional_data'] = self._fetch_institutional_data(ticker)

        # Calculate trading levels
        data['trading_levels'] = self._calculate_trading_levels(
            current_price=data['price']['current'],
            sentiment='bullish',  # Adjust based on news
            volatility=data['extended_technical'].get('atr_14', 0)
        )

        return data
```

### **Phase 2: Integration with News Analyzer**

Update `realtime_ai_news_analyzer.py`:

```python
def analyze_news_instantly(self, ticker: str, headline: str,
                           full_text: str, url: str):
    # 1. Quality check (existing)
    is_quality, reason = self._is_quality_news(...)
    if not is_quality:
        return None

    # 2. Classify news type (NEW)
    news_type = self._classify_news_type(headline, full_text)

    # 3. Fetch comprehensive data (NEW - ENHANCED)
    from enhanced_yfinance_fetcher import ComprehensiveDataFetcher
    fetcher = ComprehensiveDataFetcher()
    yf_data = fetcher.fetch_for_news_analysis(ticker, news_type)

    # 4. Build prompt with NEWS + DATA (ENHANCED)
    prompt = self._build_comprehensive_prompt(
        news={'headline': headline, 'full_text': full_text, 'url': url},
        yf_data=yf_data,
        news_type=news_type
    )

    # 5. AI analyzes (existing)
    ai_result = self._call_copilot_ai(...)

    # 6. Return with all data
    return result_with_all_data
```

### **Phase 3: Enhanced AI Prompt**

```python
def _build_comprehensive_prompt(self, news: dict, yf_data: dict, news_type: str):
    """Build prompt with NEWS + COMPLETE DATA package."""

    prompt = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 NEWS ANALYSIS REQUEST - {yf_data['metadata']['ticker']}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🚨 CRITICAL: Base analysis ONLY on NEWS + DATA below. NO TRAINING DATA!

## 📰 NEWS CONTENT

**Type**: {news_type.upper()}
**Headline**: {news['headline']}
**Source**: {news['url']}

**Full Text**:
{news['full_text']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 REAL-TIME MARKET DATA (Fetched: {yf_data['metadata']['fetch_timestamp']})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### CURRENT PRICE
- Current Price: ₹{yf_data['price']['current']:.2f}
- Previous Close: ₹{yf_data['price']['previous_close']:.2f}
- Day Range: ₹{yf_data['price']['day_low']:.2f} - ₹{yf_data['price']['day_high']:.2f}
- Change: {((yf_data['price']['current']/yf_data['price']['previous_close']-1)*100):.2f}%

### TECHNICAL INDICATORS
- RSI(14): {yf_data['technical']['rsi_14']:.1f}
- Price vs 20-SMA: {yf_data['technical']['price_vs_sma20_pct']:.2f}%
- Price vs 50-SMA: {yf_data['technical']['price_vs_sma50_pct']:.2f}%
- 10-day Momentum: {yf_data['technical']['momentum_10d_pct']:.2f}%
- Volume Ratio: {yf_data['technical']['volume_ratio']:.2f}x

### VOLATILITY & LEVELS
- ATR(14): ₹{yf_data['extended_technical']['atr_14']:.2f}
- 52W High: ₹{yf_data['extended_technical']['week_52_high']:.2f} ({yf_data['extended_technical']['distance_from_52w_high_pct']:.1f}%)
- 52W Low: ₹{yf_data['extended_technical']['week_52_low']:.2f} ({yf_data['extended_technical']['distance_from_52w_low_pct']:.1f}%)

{self._add_conditional_data(news_type, yf_data)}

### SUGGESTED TRADING LEVELS (Based on current data)
- Entry Zone: ₹{yf_data['trading_levels']['entry_zone_low']:.2f} - ₹{yf_data['trading_levels']['entry_zone_high']:.2f}
- Target (Conservative): ₹{yf_data['trading_levels']['target_conservative']:.2f}
- Target (Aggressive): ₹{yf_data['trading_levels']['target_aggressive']:.2f}
- Stop Loss: ₹{yf_data['trading_levels']['stop_loss']:.2f}
- Risk:Reward: 1:{yf_data['trading_levels']['risk_reward_ratio']:.1f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## ANALYSIS TASK

Analyze this {news_type.upper()} news using the real-time data above.

Return JSON with:
- score (0-100)
- sentiment (bullish/bearish/neutral)
- catalysts (list)
- risks (list)
- certainty (0-100)
- recommendation (BUY/SELL/HOLD)
- reasoning (2-3 sentences using SPECIFIC NUMBERS from data above)
- expected_move_pct (based on news + technical setup)

⚠️ USE ONLY THE DATA PROVIDED ABOVE. NO TRAINING DATA!
"""
    return prompt
```

## 🎯 Benefits of This Approach

1. **Comprehensive Context**: AI gets full picture (news + market data)
2. **Efficient**: Single optimized fetch per ticker
3. **Conditional**: Only fetch what's needed based on news type
4. **Cached**: Reduce redundant API calls
5. **Rate Limited**: Avoid IP blocking
6. **Explicit**: AI knows exactly what data is real-time
7. **Traceable**: All data timestamped and sourced

## 📊 Data Quality Indicators

```python
def assess_data_quality(yf_data: dict) -> str:
    """Assess quality of fetched data."""

    score = 0
    max_score = 10

    # Essential data present
    if yf_data['price']['current']:
        score += 3
    if yf_data['technical']['rsi_14']:
        score += 2
    if yf_data['technical']['sma_20']:
        score += 2

    # Extended data present
    if yf_data.get('extended_technical', {}).get('atr_14'):
        score += 1
    if yf_data.get('market_context', {}).get('market_cap'):
        score += 1

    # Conditional data present (if expected)
    if yf_data.get('earnings_data') or yf_data.get('dividend_data'):
        score += 1

    if score >= 9:
        return 'complete'
    elif score >= 6:
        return 'good'
    elif score >= 4:
        return 'partial'
    else:
        return 'minimal'
```

## 🚀 Next Steps

1. ✅ Create `enhanced_yfinance_fetcher.py`
2. ✅ Implement news type classification
3. ✅ Update prompt builder with comprehensive data
4. ✅ Add conditional data fetching
5. ✅ Implement rate limiting
6. ✅ Add data quality assessment
7. ✅ Test with real news samples

This ensures AI has everything it needs while being efficient and respectful of rate limits!
