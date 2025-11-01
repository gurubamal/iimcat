# 🚀 Frontier-AI Quant Alpha System - START HERE

Welcome! This guide will get you from zero to finding swing-trade candidates in minutes. The system combines **HFT-style quant metrics** with **AI-powered news analysis** to shortlist the best opportunities.

**Choose your learning path:**

---

## ⚡ 5-Minute Quick Start

**You have 5 minutes? Start here:**

```bash
cd /home/vagrant/R/essentials

# 1. Prepare your data
# (You should already have: top25_for_frontier_ai.csv, aggregated_48h_news.txt)

# 2. Run the system
python3 frontier_ai_quant_alpha.py \
  --top25 top25_for_frontier_ai.csv \
  --news aggregated_48h_news.txt \
  --output results.csv

# 3. View beautiful dashboard
python3 frontier_ai_dashboard.py results.csv
```

**What happens:**
- Loads 25 tickers + news
- Computes 20+ quant metrics per ticker
- Scores news catalysts (earnings, M&A, investments)
- Runs 4 gate filters (alpha, volume, trend, setup)
- Outputs CSV + dashboard

**Expected output:** 1-5 "final picks" from 25 tickers (~5-20% pass rate)

---

## 🎯 15-Minute Understanding

**Want to understand the "why"? Read this.**

### The Problem
Picking swing-trade candidates manually is slow and subjective. Most "hot stocks" are noise. You need:
- **Quantitative edge** (momentum, volume, volatility)
- **Catalysts** (earnings beats, acquisitions, expansions)
- **Risk filters** (only uptrends, squeezed volatility, high conviction news)

### The Solution: Frontier-AI Quant Alpha

**3 components working together:**

#### 1. Quant Feature Engine (HFT-style)
Computes 20+ metrics like a Jane Street trader:
- **Momentum** (3/20/60-day ROC) → captures trend strength
- **Relative Volume (RVOL)** → confirms buying pressure
- **BB-KC Squeeze** → identifies volatility compression
- **Breakout signals** → detects breakout direction
- **Price-to-BB-Zone** → shows where price is in range
- **Trend confirmations** (SMA50, SMA200) → uptrend filter

#### 2. LLM News Scorer
Automatically extracts catalysts (no manual tagging):
- **10 catalyst types** detected: earnings, M&A, IPO, expansion, etc.
- **Deal value parsing** (₹, $, €) → converts to crores
- **Sentiment analysis** → positive/negative/neutral
- **Certainty scoring** → based on specificity, sources, timing
- **Impact weighting** → bigger deals = higher confidence

#### 3. Alpha Calculator + Gates
Combines scores with hard filters:

**Alpha Formula (0-100):**
```
Alpha = 25×MOM20 + 15×MOM60 + 10×RVOL + 10×SqueezeBO 
        + 10×PBZ + 20×NewsScore + 5×TrendBonus
```
Uses smooth saturation (tanh) to avoid outliers.

**4 Hard Gates (must pass ALL):**
```
Gate 1: Alpha ≥ 70             (conviction score)
Gate 2: RVOL ≥ 1.5x            (volume confirmation)
Gate 3: Price > SMA50          (uptrend only)
Gate 4: Squeeze OR Breakout    (volatility setup)
```

**Output:**
- ✅ `final_pick=1` → Trade-ready signal
- ❌ `final_pick=0` → Filtered (see gate_flags for why)

### Risk Management
**ATR-based position sizing** (market-neutral):
```
Stop Loss:  Entry - 1.5×ATR20      (tight risk)
TP1:        Entry + 1.5×ATR20      (sell 50% here)
TP2:        Entry + 3×ATR20        (sell 25% here)
Trailing:   max(Trail, Close - 2.5×ATR20)
```

### Example: Good vs Bad Signal

**✅ HIGH-QUALITY PICK (passes all gates):**
```
RELIANCE:
  Alpha: 78 (above 70)
  RVOL: 2.1x (above 1.5x)
  Trend: SMA50 ✓ (uptrend)
  Setup: Squeeze=Yes, Breakout=Up (volatility ready)
  News: "Q3 earnings beat +11% YoY, ₹50,000cr deal"
  Certainty: 92% (specific, confirmed, large deal)
  Expected rise: +18-32%
→ FINAL PICK ✓
```

**❌ FILTERED OUT (fails gates):**
```
ABC:
  Alpha: 62 (below 70) ← FAILS GATE 1
  RVOL: 0.9x (below 1.5x) ← FAILS GATE 2
  Trend: SMA50 ✗ (downtrend) ← FAILS GATE 3
  News: "May explore funding"
  Certainty: 15% (vague, speculative)
→ REJECTED (would need +8 alpha points, +0.6x volume, uptrend)
```

---

## 📖 30-Minute Deep Dive

Read these in order:
1. **FRONTIER_AI_QUANT_README.md** - Complete technical docs (features, formulas, tuning)
2. **BEST_PICKS_SUMMARY.md** - Top-5 detailed cards with trade plans
3. **QUICK_REFERENCE_CARD.txt** - One-page cheat sheet + daily workflow
4. **SYSTEM_FILES_MANIFEST.md** - File navigation guide

---

## 📊 Your First Run

### Step 1: Prepare Data
```bash
# You need 3 things:
# 1. CSV with columns: ticker, marketcap_cr, existing_rank
ls -la top25_for_frontier_ai.csv

# 2. News file (any recent 24-48h aggregation)
ls -la aggregated_full_articles_48h_*.txt | tail -1

# 3. Directory with sufficient disk space (for yfinance caching)
df -h /home/vagrant/R/essentials
```

### Step 2: Run Analysis
```bash
python3 frontier_ai_quant_alpha.py \
  --top25 top25_for_frontier_ai.csv \
  --news aggregated_full_articles_48h_20251020.txt \
  --output my_results.csv
```

**Watch the progress:**
- Each ticker takes ~5-10 seconds (yfinance fetch + compute)
- 25 tickers ≈ 2-3 minutes total

### Step 3: View Results
```bash
python3 frontier_ai_dashboard.py my_results.csv
```

**You'll see:**
- 📊 Summary stats (picks, pass rates, average metrics)
- 🚪 Gate analysis (which filters eliminated most stocks)
- 🏆 Top 10 picks as formatted cards
- ⛔ Rejection analysis (why most didn't make it)
- 📋 Daily workflow (how to trade these)

---

## ✅ Next Steps

**Once you have results:**

1. **Validate top picks:** Cross-check news with original sources (MoneyControl, ET Markets)

2. **Pre-market prep:**
   - Check overnight news
   - Monitor pre-market volume
   - Set alerts on support levels

3. **Entry execution:**
   - Wait for pullback to SMA20 + RVOL spike
   - Enter on reversal (high of day breakout)
   - Set stop immediately (discipline)

4. **Position management:**
   - Sell 50% at TP1 (lock in profits)
   - Sell 25% at TP2 (trail stop remaining)
   - Risk only 2% per trade

5. **Learn & adjust:**
   - Track results in a spreadsheet
   - Note which catalysts worked best
   - Adjust gates for your risk tolerance

---

## 🔧 Customization

**Want to adjust thresholds?**

Open `frontier_ai_quant_alpha_core.py`, find `AlphaCalculator` class:

```python
self.gate_thresholds = {
    'alpha': 70,           # Lower = more picks, lower conviction
    'rvol': 1.5,          # Higher = fewer picks, better volume confirmation
    'trend': True,        # False = allow downtrends (risky)
    'volatility_setup': True  # False = allow non-squeezed trades
}
```

**Adjust weights in formula:**
```python
self.weights = {
    'mom20': 25,    # Increase for more momentum bias
    'mom60': 15,    # Decrease for shorter timeframe bias
    'news': 20,     # Increase to prioritize catalysts
    ...
}
```

---

## 🚨 Important Notes

**This system is a FILTER, not a holy grail:**
- It identifies high-probability setups, not guaranteed wins
- Gate filters are conservative (~5-20% pass rate)
- News scoring is automated (human review still required)
- Always validate top picks with fundamental research

**Risk Management Rules:**
1. Never average down on losses
2. Stop losses are HARD (not suggestions)
3. Max 2% risk per trade
4. No revenge trading after 2 losses
5. Trade only pre-market open confirmation (9:30 AM - 11:00 AM IST best)

---

## 📞 Troubleshooting

**"No results.csv file generated?"**
- Check if top25 CSV exists and has correct columns
- Check news file path
- Run with `--output` flag explicitly

**"All tickers show alpha < 50?"**
- Market may be downtrending (check /^NIFTY50 RSI, <30 = oversold)
- News file might be outdated (regenerate with 48h window)
- Adjust weights to emphasize different factors

**"Takes 5+ minutes to run?"**
- First run downloads 6 months of data per ticker (slow)
- Subsequent runs use cache (faster)
- Can parallelize for production (contact dev team)

---

## 📚 Full Documentation Map

```
START_HERE (you are here)
  ├─ 5-min: Quick start + commands
  ├─ 15-min: System overview + examples
  └─ 30-min: Deep dive resources

FRONTIER_AI_QUANT_README.md
  ├─ Architecture (3-tier system)
  ├─ Each metric explained (with formulas)
  ├─ Gate logic detailed
  ├─ Tuning guide
  └─ Production deployment

BEST_PICKS_SUMMARY.md
  ├─ Top-5 cards (real examples)
  ├─ Trade setup for each
  ├─ Risk/reward analysis
  └─ Market context

QUICK_REFERENCE_CARD.txt
  ├─ Metric cheat sheet
  ├─ Gate thresholds quick ref
  ├─ Risk template
  ├─ Daily checklist
  └─ Command reference

SYSTEM_FILES_MANIFEST.md
  ├─ File descriptions
  ├─ Input/output specs
  ├─ Feature dictionary
  └─ Integration guide
```

---

**Ready to trade? Let's go! 🚀**

```bash
cd /home/vagrant/R/essentials
python3 frontier_ai_quant_alpha.py --top25 top25_for_frontier_ai.csv --news <latest_news_file> --output results.csv
python3 frontier_ai_dashboard.py results.csv
```

Questions? Check FRONTIER_AI_QUANT_README.md for deep technical details.
