# SYSTEM FILES MANIFEST - FRONTIER-AI QUANT ALPHA

Complete navigation guide and file descriptions.

---

## 📁 Directory Structure

```
/home/vagrant/R/essentials/
├─ CORE SYSTEM
│  ├─ frontier_ai_quant_alpha_core.py        (Main engine - 400+ lines)
│  ├─ frontier_ai_quant_alpha.py             (Orchestrator - 200+ lines)
│  └─ frontier_ai_dashboard.py               (Dashboard - 300+ lines)
│
├─ INPUT FILES
│  ├─ top25_for_frontier_ai.csv              (Top 25 tickers list)
│  └─ aggregated_full_articles_48h_*.txt     (Latest 48h news)
│
├─ OUTPUT FILES (Generated daily)
│  ├─ frontier_ai_alpha_results_YYYYMMDD.csv (22-column results)
│  └─ dashboard_YYYYMMDD.txt                 (Formatted output)
│
├─ DOCUMENTATION (5 guides)
│  ├─ FRONTIER_START_HERE.md                 (Entry point - 3 paths)
│  ├─ FRONTIER_AI_QUANT_README.md            (Technical deep-dive)
│  ├─ BEST_PICKS_SUMMARY.md                  (Real trade examples)
│  ├─ QUICK_REFERENCE_CARD.txt               (Cheat sheet)
│  └─ SYSTEM_FILES_MANIFEST.md               (This file)
│
└─ UTILITY
   ├─ run_daily_alpha.sh                     (Cron script template)
   └─ archives/                              (Historical results)
```

---

## 📖 QUICK NAVIGATION

| Need Help With... | Read This File | Section |
|-------------------|----------------|---------|
| **Just get started** | FRONTIER_START_HERE.md | ⚡ 5-Minute Quick Start |
| **Understand the system** | FRONTIER_START_HERE.md | 🎯 15-Minute Understanding |
| **Technical details** | FRONTIER_AI_QUANT_README.md | Architecture + all 20+ metrics |
| **Real trade examples** | BEST_PICKS_SUMMARY.md | 5 detailed trade setups |
| **Daily cheat sheet** | QUICK_REFERENCE_CARD.txt | Commands + gates + risk template |
| **File specifications** | SYSTEM_FILES_MANIFEST.md | Input/output formats (this file) |
| **Troubleshooting** | QUICK_REFERENCE_CARD.txt | "🎯 Common Issues & Fixes" section |

---

## 📥 INPUT FILES SPECIFICATION

### 1. top25_for_frontier_ai.csv

**CSV Format:**
```
ticker,marketcap_cr,existing_rank
RELIANCE.NS,1800000,1
INFY.NS,850000,2
TCS.NS,950000,3
HCLTECH.NS,450000,4
...
```

**Column Details:**
- `ticker` - NSE symbol (with or without .NS suffix)
- `marketcap_cr` - Market cap in ₹ crores (integer)
- `existing_rank` - Previous rank for comparison (integer)

**Requirements:**
- At least 5-25 rows (system processes all)
- Valid yfinance tickers (download succeeds)
- Unique ticker per row

**How to generate:**
```bash
# NSE top-25 by market cap
python3 << 'EOF'
import pandas as pd
data = {
    'ticker': ['RELIANCE.NS', 'INFY.NS', 'TCS.NS'],
    'marketcap_cr': [1800000, 850000, 950000],
    'existing_rank': [1, 2, 3]
}
pd.DataFrame(data).to_csv('top25_for_frontier_ai.csv', index=False)
EOF
```

### 2. aggregated_full_articles_48h_*.txt

**Format:** One headline per line

```
RELIANCE eyes Rs 2,000 crore buyback on strong Q3 earnings
Reliance Q3 profit up 11% YoY to Rs 5,427 crore
INFY announces new subsidiary for AI ventures
INFY $200 million investment approved by board
TCS expands capacity in Pune facility
ABC Limited exploring strategic alternatives
...
```

**Requirements:**
- UTF-8 encoding
- Ticker mentions clear in text
- 48-72 hour aggregation window
- At least 10 lines total

**Optional:** Can include URL or publication name (will be parsed but not required)

**File naming pattern:** `aggregated_full_articles_48h_YYYYMMDD_HHMMSS.txt`

**How to generate:**
```bash
# Using existing news collector
python3 enhanced_india_finance_collector.py \
  --tickers-file all.txt \
  --hours-back 48 \
  --max-articles 10
```

---

## 📤 OUTPUT FILES SPECIFICATION

### frontier_ai_alpha_results_YYYYMMDD_HHMMSS.csv

**22 Column Output**

| # | Column | Type | Range | Description |
|---|--------|------|-------|-------------|
| 1 | ticker | str | - | Stock symbol |
| 2 | close | float | ₹ | Current price |
| 3 | alpha | float | 0-100 | Final alpha score |
| 4 | final_pick | int | 0/1 | Gate filter result |
| 5 | marketcap_cr | float | ₹cr | Market cap |
| 6 | existing_rank | int | 1-25 | Previous rank |
| 7 | momentum_20 | float | 0-100 | 20-day momentum |
| 8 | momentum_60 | float | 0-100 | 60-day momentum |
| 9 | momentum_3 | float | 0-100 | 3-day momentum |
| 10 | rvol | float | 0-3x | Relative volume |
| 11 | pbz | float | 0-100 | Price-to-BB-Zone |
| 12 | squeeze | int | 0/1 | Squeeze detected? |
| 13 | breakout | int | -1/0/1 | Direction |
| 14 | trend_sma50 | int | 0/1 | Above SMA50? |
| 15 | trend_sma200 | int | 0/1 | Above SMA200? |
| 16 | rsi14 | float | 0-100 | RSI-14 |
| 17 | catalyst_type | str | 10 types | Primary catalyst |
| 18 | catalyst_count | int | 0+ | # of catalysts |
| 19 | deal_value_cr | float | ₹cr | Deal size |
| 20 | sentiment | str | pos/neg/neu | News sentiment |
| 21 | certainty | int | 0-100 | News confidence |
| 22 | atr20 | float | ₹ | ATR20 volatility |

**Example row:**
```csv
RELIANCE.NS,2850.25,78.5,1,1800000,1,75,68,71,2.1,74,1,1,1,1,52,earnings,2,2000,positive,89,42.5
```

**CSV Size:** One row per ticker (25 rows typical)

**Retention:** Archive 30 days minimum

---

## 🔧 CORE SYSTEM FILES

### frontier_ai_quant_alpha_core.py

**Main Classes:**

1. **QuantFeatureEngine** (150 lines)
   - `fetch_data()` - yfinance download
   - `compute_atr()` - Average True Range
   - `compute_momentum()` - ROC (3/20/60-day)
   - `compute_rvol()` - Relative volume
   - `compute_squeeze()` - BB-KC squeeze
   - `compute_breakout()` - Higher high/low
   - `compute_pbz()` - Price-to-BB-Zone
   - `compute_rsi()` - RSI-14
   - `compute_macd()` - MACD signal
   - `compute_features()` - Orchestrates all

2. **LLMNewsScorer** (100 lines)
   - `parse_deal_value()` - Extract ₹/$€
   - `score_news()` - Main scoring
   - CATALYST_TYPES dict (10 regex patterns)
   - SENTIMENT_WORDS dict

3. **AlphaCalculator** (80 lines)
   - `compute_alpha()` - Final score + gates
   - `compute_news_score()` - News impact
   - `compute_squeeze_bo_score()` - Setup quality
   - gate_thresholds dict (customizable)

4. **RiskManager** (20 lines)
   - `compute_levels()` - Stop/TP/Trail

### frontier_ai_quant_alpha.py

**Main Class:**

1. **FrontierAIOrchestrator** (100 lines)
   - `load_top25()` - Read ticker CSV
   - `load_news_for_ticker()` - Extract per ticker
   - `process_ticker()` - Full pipeline
   - `run()` - Loop all 25 tickers
   - `save_results()` - Export 22-column CSV

**CLI:** argparse interface with 3 arguments:
```
--top25: Path to ticker CSV
--news: Path to aggregated news file
--output: Output CSV filename
```

### frontier_ai_dashboard.py

**Main Class:**

1. **DashboardFormatter** (150 lines)
   - `render()` - Full dashboard
   - `header()` - Title
   - `summary_stats()` - Key metrics
   - `gate_analysis()` - Filter breakdown
   - `top_picks_cards()` - Formatted display
   - `rejection_report()` - Why filtered

**CLI:** `python3 frontier_ai_dashboard.py <results.csv>`

---

## 📊 THE 22 QUANT METRICS (Detail)

### Volatility (ATR20)
- **Formula:** EMA(True Range, 20)
- **Usage:** Position sizing, stop distances
- **Range:** ₹ (stock-specific)

### Momentum (MOM3, MOM20, MOM60)
- **Formula:** tanh(ROC / 20) × 50 + 50
- **Range:** 0-100 (normalized)
- **Interpretation:** 70+ = bullish, 30- = bearish

### Volume (RVOL)
- **Formula:** Current_Vol / Avg_Vol_20days
- **Range:** 0-3x typical
- **Gate:** ≥1.5x required

### Compression (Squeeze, BB_Width)
- **Formula:** BB_width < KC_width
- **Output:** Boolean + numeric width
- **Significance:** Volatility expansion imminent

### Breakout (Direction)
- **Formula:** Close > 20H or Close < 20L
- **Output:** +1 (up), -1 (down), 0 (none)

### Price Zone (PBZ)
- **Formula:** 50 + 50×(C-SMA) / BB_width
- **Range:** 0-100
- **Meaning:** Position in Bollinger Band

### Trends (SMA50, SMA200)
- **Formula:** Close > SMA(50) or SMA(200)
- **Output:** Boolean (0/1)
- **Gate:** SMA50 required (no downtrends)
- **Bonus:** +5 alpha if both true

### Momentum Secondary (RSI14)
- **Formula:** 100 - 100/(1+RS)
- **Range:** 0-100
- **Use:** Identify extremes

### News Metrics (Catalyst, Deal_Value, Sentiment, Certainty)
- **Catalyst:** 10 pattern-matched types (earnings, M&A, etc.)
- **Deal_Value:** Parsed from ₹/$€ (converted to crores)
- **Sentiment:** pos/neg/neutral
- **Certainty:** 0-100 (based on specificity + sources)

---

## 🚀 EXECUTION SEQUENCE

```
1. Load top25_for_frontier_ai.csv
          ↓
2. For each ticker:
   a. Fetch 6-month OHLCV (yfinance)
   b. Compute 20+ metrics (QuantFeatureEngine)
   c. Extract news headlines (from aggregated file)
   d. Score news (LLMNewsScorer)
   e. Compute alpha (AlphaCalculator)
   f. Apply 4 gates (AND logic)
   g. Compute risk levels (RiskManager)
   h. Store in results DataFrame
          ↓
3. Sort by alpha descending
          ↓
4. Export to CSV (22 columns)
          ↓
5. Generate dashboard (DashboardFormatter)
          ↓
6. Print summary to stdout
```

**Time per ticker:** ~5-10 seconds (first run)  
**Total for 25:** 2-5 minutes

---

## 📋 DAILY EXECUTION TEMPLATE

```bash
#!/bin/bash
cd /home/vagrant/R/essentials

# Get latest 48h news
LATEST_NEWS=$(ls -t aggregated_full_articles_48h_*.txt 2>/dev/null | head -1)
if [ -z "$LATEST_NEWS" ]; then
  echo "Error: No news file found"
  exit 1
fi

# Run analysis
python3 frontier_ai_quant_alpha.py \
  --top25 top25_for_frontier_ai.csv \
  --news "$LATEST_NEWS" \
  --output "results_$(date +%Y%m%d_%H%M%S).csv"

# Generate dashboard
LATEST_RESULTS=$(ls -t results_*.csv | head -1)
python3 frontier_ai_dashboard.py "$LATEST_RESULTS"

# Archive
cp "$LATEST_RESULTS" archives/

echo "✓ Completed: $(date)"
```

**Crontab entry (6:00 AM IST):**
```
0 6 * * 1-5 bash /home/vagrant/R/essentials/run_daily_alpha.sh >> /var/log/frontier_ai.log 2>&1
```

---

## 🔍 VALIDATION CHECKLIST

Before first run:
- [ ] Python 3.8+ installed
- [ ] yfinance, pandas, numpy available
- [ ] top25_for_frontier_ai.csv exists and valid
- [ ] aggregated_full_articles_48h_*.txt exists
- [ ] Output directory writable
- [ ] 500+ MB disk space available

After first run:
- [ ] CSV file created with 22 columns
- [ ] Dashboard displayed without errors
- [ ] At least 1-5 final picks generated
- [ ] Headlines matched to tickers

---

## 🎓 CUSTOMIZATION GUIDE

**To adjust gate thresholds:**
Edit `frontier_ai_quant_alpha_core.py`, line ~180:
```python
self.gate_thresholds = {
    'alpha': 70,            # ↓ for more picks
    'rvol': 1.5,            # ↓ for illiquid
    'trend': True,          # False = downtrends OK
    'volatility_setup': True  # False = any trade
}
```

**To adjust formula weights:**
Edit same file, line ~160:
```python
self.weights = {
    'mom20': 25,    # ↑ for momentum bias
    'mom60': 15,
    'rvol': 10,     # ↑ for volume bias
    'squeeze_bo': 10,
    'pbz': 10,
    'news': 20,     # ↑ for news bias
    'trend_bonus': 5
}
```

---

## 📞 SUPPORT RESOURCES

| Issue | Solution |
|-------|----------|
| No picks? | Lower alpha gate from 70 to 65 |
| Missing news? | Check news file ticker format |
| Slow execution? | Run again (uses cache) |
| Error in imports? | `pip install yfinance pandas numpy` |

---

**Version:** 1.0 | **Last Updated:** 2025-10-20 | **Status:** Production Ready
