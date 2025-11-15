# Hybrid Ranking System - AI News + Technical Analysis

## Executive Summary

The hybrid ranking system combines **AI-driven news analysis** with **swing screener technical analysis** to provide superior stock rankings that balance:
- **News catalysts** (60% weight) - What's driving the stock NOW
- **Technical setup** (40% weight) - Is the entry timing OPTIMAL

This document explains the integration, usage, and benefits while maintaining full temporal bias protection.

---

## 🎯 **Why Hybrid Ranking?**

### **Problem with AI-Only Ranking:**
- ✅ Excellent at identifying news catalysts and sentiment
- ✅ Fast, real-time analysis of breaking news
- ❌ **Missing**: Entry timing, technical confirmation, setup quality
- ❌ **Risk**: Strong news but poor technical setup = bad entry

### **Problem with Technical-Only Ranking:**
- ✅ Excellent at identifying entry setups (oversold, high volume, etc.)
- ✅ Clear risk/reward with ATR-based stops
- ❌ **Missing**: News catalysts, fundamental drivers
- ❌ **Risk**: Great setup but no catalyst = slow or no movement

### **Solution: Hybrid Approach**
- ✅ **60% AI News**: Identify stocks with strong catalysts (earnings, contracts, sector momentum)
- ✅ **40% Technical**: Confirm entry timing is optimal (oversold, volume surge, tight setup)
- ✅ **Result**: High-probability setups with both catalyst AND optimal entry

---

## 📊 **System Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                  run_without_api.sh                          │
│  (Optional 5th argument: 1 = enable technical scoring)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ├──> Export ENABLE_TECHNICAL_SCORING=1
                       │
                       v
┌─────────────────────────────────────────────────────────────┐
│           realtime_ai_news_analyzer.py                       │
│   (Main ranking engine with optional technical layer)        │
└──────────┬──────────────────────────────────────────────────┘
           │
           ├──> AI News Analysis (always enabled)
           │    └─ Sentiment, certainty, catalysts
           │       Source: claude_cli_bridge.py
           │       Score: 0-100
           │
           └──> Technical Analysis (optional)
                └─ technical_scoring_wrapper.py
                   └─ swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py
                      ├─ RSI (Wilder's implementation)
                      ├─ Bollinger Band Position (0-100 scale)
                      ├─ ATR (volatility assessment)
                      ├─ Volume Ratio (confirmation)
                      └─ Momentum (recent price action)
                   Score: 0-100 (normalized from opportunity score)
                   Tier: Tier1 / Tier2 / Watch

                Hybrid Score = (0.6 × AI) + (0.4 × Technical)
```

---

## 🔧 **Components**

### **1. AI News Analysis** (realtime_ai_news_analyzer.py)
**What it analyzes:**
- Recent news articles (last 8-48 hours)
- Sentiment (bullish/bearish/neutral)
- Catalysts (earnings, contracts, expansion, M&A, etc.)
- Certainty (based on source credibility and specificity)

**Scoring (0-100):**
- High certainty + strong catalyst + positive sentiment = 80-95
- Medium certainty + catalyst = 60-75
- Low certainty or speculation = 20-40

**Temporal Bias Protection:**
- ✅ Explicit TODAY'S DATE in prompts
- ✅ Real-time news fetching (not training data)
- ✅ AI instructed to prioritize provided data over training knowledge

### **2. Technical Analysis** (technical_scoring_wrapper.py)
**What it analyzes:**
- RSI (14-period Wilder's): Oversold = bullish (RSI < 30 = +10pts)
- Bollinger Band Position: Lower band = buying opportunity (BB < 20 = +10pts)
- Volume: Surge vs 20-day average (2x volume = +5pts)
- ATR %: Moderate volatility preferred (2-5% = +3pts)
- Momentum: Slight pullback = ideal (−2% to +1% = +2pts)

**Scoring (0-100):**
- Normalized from opportunity score (0-30+)
- Tier1 (≥25pts) → Score ~100
- Tier2 (≥15pts) → Score ~60
- Watch (<15pts) → Score ~30

**Quality Filters (must pass):**
- Average volume ≥ 300,000
- Recent volume ≥ 100,000
- Price ≥ ₹20 (no penny stocks)
- Data ≥ 50 bars (sufficient history)

**Temporal Bias Protection:**
- ✅ Real-time yfinance data (fetched NOW, not training data)
- ✅ Explicit fetch timestamps
- ✅ No reliance on memorized prices

### **3. Hybrid Scoring Logic**
```python
# Default weights
AI_WEIGHT = 0.6  # News catalysts
TECH_WEIGHT = 0.4  # Entry timing

hybrid_score = (AI_WEIGHT × ai_score) + (TECH_WEIGHT × technical_score)

# Example:
# AI Score = 85 (strong news: earnings beat)
# Technical Score = 75 (Tier2 setup: RSI 35, BB 25, volume 1.8x)
# Hybrid = (0.6 × 85) + (0.4 × 75) = 51 + 30 = 81
```

---

## 🚀 **Usage**

### **Quick Start**

```bash
# AI-only ranking (default, existing behavior)
./run_without_api.sh claude all.txt 48 10

# Hybrid ranking (AI + Technical)
./run_without_api.sh claude all.txt 48 10 1
                                          └─ 5th argument: 1 = enable technical

# With codex (fast heuristic)
./run_without_api.sh codex all.txt 48 10 1
```

### **Environment Variables**

```bash
# Enable technical scoring
export ENABLE_TECHNICAL_SCORING=1

# Then run normally
./run_without_api.sh claude all.txt 48 10
```

### **Expected Output**

**With technical scoring ENABLED:**
```
Configuration:
  Provider: Claude CLI Bridge
  Tickers: all.txt
  Hours: 48
  Max Articles: 10
  Ticker Validation: DISABLED (all tickers will be processed)
  Popularity/Ad Filter: ENABLED (tunable via AD_POPULARITY_ENABLED/AD_STRICT_REJECT)
  Technical Scoring: ✅ ENABLED (hybrid ranking: 60% AI + 40% Technical)
    └─ Indicators: RSI, Bollinger Bands, ATR, Volume, Momentum
    └─ Quality Filters: Volume ≥300k, Price ≥₹20, Data ≥50 bars
    └─ Tiers: Tier1 ≥25pts, Tier2 ≥15pts, Watch <15pts
```

**With technical scoring DISABLED (default):**
```
  Technical Scoring: ⬜ DISABLED (AI-only ranking)
    └─ Enable with: ./run_without_api.sh claude all.txt 48 10 1
```

---

## 📈 **Scoring Examples**

### **Example 1: 🔥 STRONG BUY (High AI + Tier1 Technical)**

**Stock: INFY.NS**
- AI News Score: 88
  - Catalyst: ₹4,235cr PAT, +11% YoY
  - Sentiment: Bullish
  - Certainty: 95% (confirmed earnings from Moneycontrol)

- Technical Score: 96 (Tier1)
  - RSI: 28.5 (oversold +10pts)
  - BB Position: 18 (near lower band +10pts)
  - Volume: 2.3x average (+5pts)
  - ATR%: 2.8% (moderate volatility +3pts)
  - Momentum: -1.2% (slight pullback +2pts)
  - Total: 30pts → Tier1

- **Hybrid Score: 91.2**
  - (0.6 × 88) + (0.4 × 96) = 52.8 + 38.4 = 91.2

- **Recommendation:** 🔥 STRONG BUY - Excellent news + Tier1 technical setup

---

### **Example 2: ⚠️ CAUTION (High AI + Poor Technical)**

**Stock: ABC.NS**
- AI News Score: 82
  - Catalyst: New contract worth ₹500cr
  - Sentiment: Bullish
  - Certainty: 75%

- Technical Score: 32 (Watch)
  - RSI: 68 (overbought +0pts)
  - BB Position: 85 (near upper band +0pts)
  - Volume: 1.2x average (+0pts)
  - ATR%: 1.2% (low volatility +1.5pts)
  - Momentum: +5.8% (extended +0pts)
  - Total: 1.5pts → Watch

- **Hybrid Score: 62.0**
  - (0.6 × 82) + (0.4 × 32) = 49.2 + 12.8 = 62.0

- **Recommendation:** ⚠️ CAUTION - Strong news but weak technical setup (overbought, extended)

---

### **Example 3: 🤔 CONSIDER (Weak AI + Tier1 Technical)**

**Stock: XYZ.NS**
- AI News Score: 45
  - Catalyst: Industry sector strength (generic)
  - Sentiment: Neutral
  - Certainty: 40%

- Technical Score: 88 (Tier1)
  - RSI: 32 (oversold +10pts)
  - BB Position: 22 (near lower band +10pts)
  - Volume: 1.9x average (+5pts)
  - ATR%: 3.1% (moderate +3pts)
  - Momentum: -0.8% (pullback +2pts)
  - Total: 30pts → Tier1

- **Hybrid Score: 62.2**
  - (0.6 × 45) + (0.4 × 88) = 27.0 + 35.2 = 62.2

- **Recommendation:** 🤔 CONSIDER - Weak news but strong technical setup (may need catalyst)

---

## 🛡️ **Temporal Bias Protection (MAINTAINED)**

### **AI News Analysis Layer**
```python
# realtime_ai_news_analyzer.py:1205-1217
current_date = datetime.now().strftime('%Y-%m-%d')
current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

🚨 TEMPORAL CONTEXT - CRITICAL FOR AVOIDING TRAINING DATA BIAS 🚨
**TODAY'S DATE**: {current_date}
**ANALYSIS TIMESTAMP**: {current_datetime}
**NEWS PUBLISHED**: within last 48 hours

⚠️ CRITICAL INSTRUCTIONS:
- DO NOT use training data, memorized prices, or external knowledge
- Base analysis ONLY on provided article text
```

### **Technical Analysis Layer**
```python
# technical_scoring_wrapper.py:_fetch_price_data()
# Fetch real-time data from yfinance
stock = yf.Ticker(ticker)
df = stock.history(period=period)

# Add fetch timestamp for temporal tracking
fetch_timestamp = datetime.now()
logger.debug(f"Fetched {len(df)} bars for {ticker} at {fetch_timestamp.isoformat()}")
```

### **Result: Complete Temporal Protection**
- ✅ AI uses ONLY current news (last 48 hours)
- ✅ Technical analysis uses ONLY current yfinance data
- ✅ Both layers have explicit timestamps
- ✅ No reliance on training data or memorized knowledge

---

## 📊 **Output CSV Format**

The hybrid system produces the same CSV format with optional technical columns:

```csv
rank,ticker,ai_score,headline,sentiment,certainty,catalysts,technical_score,technical_tier,hybrid_score,recommendation
1,INFY.NS,88,Reports ₹4235cr PAT +11% YoY,bullish,95,[earnings],96,Tier1,91.2,🔥 STRONG BUY
2,HDFCBANK.NS,85,Q4 NII grows 15%,bullish,90,[earnings],68,Tier2,78.2,✅ BUY
3,TCS.NS,75,Wins $200M deal,bullish,80,[contract],45,Watch,63.0,📊 Watch setup
```

---

## 🎛️ **Configuration & Tuning**

### **Weights (adjustable in code)**
```python
# technical_scoring_wrapper.py:get_hybrid_score()
AI_WEIGHT = 0.6  # Default: 60% AI news
TECH_WEIGHT = 0.4  # Default: 40% Technical

# For more news-driven trading:
AI_WEIGHT = 0.7
TECH_WEIGHT = 0.3

# For more technical-focused trading:
AI_WEIGHT = 0.5
TECH_WEIGHT = 0.5
```

### **Quality Filters (adjustable in swing screener)**
```python
# swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2453
avg_volume >= 300_000  # Minimum liquidity
current_price >= 20    # Avoid penny stocks
len(df) >= 50          # Sufficient data
recent_volume >= 100_000  # Recent activity
```

### **Tier Thresholds**
```python
# swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2564
if total_score >= 25:
    tier = "Tier1"  # Excellent setup
elif total_score >= 15:
    tier = "Tier2"  # Good setup
else:
    tier = "Watch"  # Fair/weak setup
```

---

## 🧪 **Testing**

### **Test Technical Scoring Standalone**
```bash
# Test wrapper directly
export ENABLE_TECHNICAL_SCORING=1
python3 technical_scoring_wrapper.py INFY.NS
```

**Expected Output:**
```
============================================================
Technical Analysis: INFY.NS
============================================================
Score: 88.0/100
Tier: Tier1
Setup Quality: Excellent

Indicators:
  RSI: 28.5
  BB Position: 18.2
  ATR%: 2.85%
  Volume Ratio: 2.30x

Fetched: 2025-11-10T18:45:32
```

### **Test Hybrid Ranking**
```bash
# Run full analysis with technical scoring
./run_without_api.sh claude all.txt 48 10 1

# Check output CSV
head -5 realtime_ai_results.csv
```

---

## ✅ **Benefits Summary**

| Aspect | AI-Only | Technical-Only | Hybrid |
|--------|---------|----------------|--------|
| **Catalyst Identification** | ✅ Excellent | ❌ None | ✅ Excellent |
| **Entry Timing** | ❌ Missing | ✅ Excellent | ✅ Excellent |
| **Risk Management** | ⚠️ Generic | ✅ ATR-based | ✅ ATR-based |
| **False Positives** | ⚠️ High (bad entries) | ⚠️ Medium (no catalyst) | ✅ Low (both filters) |
| **Speed** | ⚠️ Slow (~5s/stock) | ✅ Fast (<1s/stock) | ⚠️ Moderate (~6s/stock) |
| **Temporal Bias Protection** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Best For** | News-driven trades | Technical setups | High-probability setups |

---

## 🎯 **When to Use Each Mode**

### **AI-Only (Default)**
Use when:
- ✅ You need fast scanning (hundreds of stocks)
- ✅ You're focused on news-driven momentum plays
- ✅ You have your own technical analysis process
- ✅ You want maximum speed

### **Hybrid (Recommended)**
Use when:
- ✅ You want high-probability setups with both catalyst + timing
- ✅ You're willing to trade speed for accuracy
- ✅ You need to reduce false positives
- ✅ You want automated entry timing guidance
- ✅ You're screening smaller watchlists (50-200 stocks)

---

## 📚 **Related Documentation**

- `TEMPORAL_BIAS_MITIGATION_GUIDE.md` - Temporal bias protection details
- `RUN_WITHOUT_API.md` - Main script documentation
- `swing_screener_extraction_guide.md` - Technical analysis components (this file's source)
- `TECHNICAL_ARCHITECTURE.md` - System design overview

---

## 🔍 **Troubleshooting**

### **Problem: Technical scoring shows "N/A"**
**Cause:** Stock failed quality filters or yfinance data unavailable

**Solution:**
1. Check stock has sufficient volume (≥300k average)
2. Check price ≥ ₹20
3. Verify ticker symbol is correct (use .NS suffix for NSE)

### **Problem: Hybrid scores seem too conservative**
**Cause:** Technical filter is lowering scores for extended/overbought stocks

**Solution:** This is working as intended - technical analysis prevents chasing extended moves

### **Problem: Slow performance with technical scoring**
**Cause:** yfinance API calls add latency (~1s per stock)

**Solution:**
1. Use caching (already enabled, 5-minute TTL)
2. Reduce watchlist size
3. Run overnight for large lists
4. Or use AI-only mode for speed

---

## 📝 **Version History**

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-10 | Initial hybrid ranking implementation |

---

*Last Updated: 2025-11-10*
*Maintainer: System AI*
