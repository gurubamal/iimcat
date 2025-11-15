# FRONTIER-AI QUANT ALPHA - COMPLETE TECHNICAL DOCUMENTATION

## Quick Summary

HFT-inspired quant system for swing trading shortlisting. Combines:
- **20+ quant metrics** (momentum, volume, volatility compression)
- **LLM news scoring** (automated catalyst detection)
- **4 hard gates** (quality filters)
- **ATR-based risk management**

**Result:** ~5-20% of tickers pass (highest-conviction picks only)

---

## System Architecture

```
Input (CSV + News)
       ↓
Tier 1: Quant Engine (compute 20+ metrics)
       ↓
Tier 2: News Scorer (extract catalysts, sentiment, certainty)
       ↓
Tier 3: Alpha Calculator (combine scores + apply gates)
       ↓
Output (CSV + Dashboard + Risk levels)
```

---

## The 20+ Quant Features

### Volatility Metrics
1. **ATR20** - Average True Range for position sizing
2. **BB Width** - Bollinger Band width (normal vs compressed)
3. **Keltner Width** - Keltner Channel width

### Momentum Metrics
4. **MOM3** - 3-day rate of change
5. **MOM20** - 20-day rate of change (PRIMARY)
6. **MOM60** - 60-day rate of change
7. **RSI14** - Relative Strength Index
8. **MACD Signal** - MACD signal line

### Volume Metrics
9. **RVOL** - Relative Volume (current vs 20-day avg)

### Compression & Setup
10. **Squeeze** - Boolean (BB inside KC?)
11. **BB Width** - Numeric width for degree of compression
12. **Breakout** - +1 (up), -1 (down), 0 (none)

### Price Position
13. **PBZ** - Price-to-Bollinger-Zone (0-100)
14. **Close** - Current price

### Trend Filters
15. **Trend SMA50** - Price > 50-day moving average?
16. **Trend SMA200** - Price > 200-day moving average?

### News-Based Metrics
17. **Catalyst Type** - earnings, M&A, expansion, etc.
18. **Catalyst Count** - How many catalysts detected
19. **Deal Value (₹cr)** - Size of deal/announcement
20. **Sentiment** - positive/negative/neutral
21. **Certainty %** - Confidence in signal (0-100)

---

## Alpha Formula (in Plain English)

**The Recipe:**
```
Alpha = 25×Momentum(20d) + 15×Momentum(60d) + 10×Volume + 10×Setup
        + 10×Price_Zone + 20×News_Score + 5×Trend_Bonus
```

**Why this weighting?**
- 40% to momentum (primary driver)
- 20% to volume (confirmation)
- 20% to news (catalyst verification)
- 20% to setup + price zone (technical setup quality)

**Output: Alpha score (0-100)**

---

## The 4 Hard Gates

| Gate | Threshold | Why | Fail Rate |
|------|-----------|-----|-----------|
| Alpha ≥ 70 | Conviction score | Only highest quality | 40-50% |
| RVOL ≥ 1.5x | Volume confirmation | Avoid illiquid trades | 10-20% |
| Price > SMA50 | Uptrend check | Avoid counter-trend | 15-30% |
| Squeeze OR BO | Volatility setup | Entry conditions met | 20-40% |

**ALL must pass** → `final_pick = 1`

---

## News Scoring (10 Catalyst Types)

Automatically detected patterns:
- Earnings (reports, profit, revenue)
- M&A (acquisition, merger, deal)
- Investment (funding, stake, capital)
- Expansion (factory, capacity, facility)
- Contract (order, supply, partnership)
- Product (launch, feature, service)
- Dividend (buyback, shareholder return)
- Strategic (board, CEO, restructure)
- Regulatory (approval, license, permit)
- IPO (listing, public offering)

**Deal value parsing:**
```
"₹50,000 crore acquisition" → 50,000 cr ✓
"$100 million investment" → 83 cr (converted) ✓
"May raise funds" → 0 cr (no amount) → low certainty
```

**Certainty formula:**
- Base: 30%
- Specificity: +3% per number found
- Sources: +5% per news source
- Catalyst: +10% if confirmed
- Result: 30-100% certainty

---

## Risk Management (ATR-Based)

For every trade:

```
Entry Price = ₹2,850
ATR20 = ₹42.50

Stop Loss = ₹2,850 - (1.5 × ₹42.50) = ₹2,786  (tight!)
TP1 = ₹2,850 + (1.5 × ₹42.50) = ₹2,914  (SELL 50%)
TP2 = ₹2,850 + (3 × ₹42.50) = ₹2,978   (SELL 25%)
Trailing Stop = ₹2,850 - (2.5 × ₹42.50) = ₹2,744  (SELL LAST 25%)
```

**Position sizing (2% risk rule):**
```
Account = ₹1,000,000
Max risk per trade = ₹20,000
Stop distance = ₹2,850 - ₹2,786 = ₹64
Position = ₹20,000 / ₹64 = 312 shares
→ Risk = 312 × ₹64 / ₹1,000,000 = 2% ✓
```

---

## Tuning Parameters

All in `frontier_ai_quant_alpha_core.py`, `AlphaCalculator` class:

```python
# Adjust weights (must consider changing alpha thresholds)
self.weights = {
    'mom20': 25,           # ↑ for momentum bias
    'mom60': 15,
    'rvol': 10,            # ↑ for volume confirmation
    'squeeze_bo': 10,
    'pbz': 10,
    'news': 20,            # ↑ for news bias, ↓ to ignore news
    'trend_bonus': 5
}

# Adjust gate thresholds
self.gate_thresholds = {
    'alpha': 70,           # ↓ 65 for more picks, ↑ 75 for fewer
    'rvol': 1.5,           # ↓ 1.0 for illiquid, ↑ 2.0 for tight filters
    'trend': True,         # False = allow downtrends (risky!)
    'volatility_setup': True  # False = allow range-bound trades
}
```

---

## Daily Execution Flow

### Step 1: Prepare inputs
```bash
# Top-25 ticker list
top25_for_frontier_ai.csv

# Latest 48-hour news
aggregated_full_articles_48h_latest.txt
```

### Step 2: Run system
```bash
python3 frontier_ai_quant_alpha.py \
  --top25 top25_for_frontier_ai.csv \
  --news aggregated_full_articles_48h_latest.txt \
  --output results.csv
```

### Step 3: Review results
```bash
python3 frontier_ai_dashboard.py results.csv
```

**Expected time:** 2-3 minutes for 25 tickers

### Step 4: Trade execution
- Review top picks
- Validate catalysts with original news
- Set up orders (entry, stop, TP1, TP2)
- Enter on confirmation (not at open)

---

## Example: Good Pick vs Bad Pick

### ✅ GOOD PICK (All gates pass)
```
RELIANCE:
- Alpha: 78 (≥70) ✓
- RVOL: 2.1x (≥1.5x) ✓
- Trend: SMA50 ✓ SMA200 ✓ ✓
- Setup: Squeeze=Yes, BO=+1 ✓
- News: "Q3 earnings beat +11% YoY, ₹50,000cr deal"
- Certainty: 89%
- Risk/Reward: 2.9:1
→ FINAL_PICK = 1 ✓
```

### ❌ BAD PICK (Fails gates)
```
ABC:
- Alpha: 62 (<70) ✗ GATE 1 FAILS
- RVOL: 0.9x (<1.5x) ✗ GATE 2 FAILS
- Trend: SMA50 ✗ ✗ GATE 3 FAILS
- Setup: Squeeze=No, BO=0 ✗ GATE 4 FAILS
- News: "May explore funding options"
- Certainty: 18%
→ FINAL_PICK = 0 ✗
```

---

## CSV Output (22 Columns)

```
ticker, close, alpha, final_pick, marketcap_cr, existing_rank,
momentum_20, momentum_60, momentum_3,
rvol, rvol_norm, pbz, pbz_norm,
squeeze, breakout, squeeze_bo_score, bb_width,
trend_sma50, trend_sma200, rsi14,
catalyst_type, catalyst_count, deal_value_cr, sentiment, certainty,
news_score, mom20_norm, mom60_norm,
atr20, stop_loss, tp1, tp2, trail_stop, impact_pct,
gate_flags, headline_text, headline_count
```

---

## Troubleshooting

**"No picks passing gates?"**
- Lower alpha threshold to 65
- Lower RVOL to 1.0
- Increase news weight
- Check market regime (might be downtrend)

**"Takes 5+ minutes?"**
- First run: downloads 6 months data (slow)
- Subsequent: uses cache (faster)
- Can parallelize (advanced)

**"Results don't match news headlines?"**
- News file may be outdated
- Regenerate with 48h window
- Check ticker symbol matching

---

## Performance Targets

**Pick Quality:**
- Win rate: >60%
- Avg gain: 2-4% per trade
- Profit factor: >2.0 (gains/losses)

**System Health:**
- Avg alpha of picks: >75
- Avg RVOL of picks: >1.8x
- Catalyst confirmation: >60%

---

**Next:** See BEST_PICKS_SUMMARY.md for real trade setups.
