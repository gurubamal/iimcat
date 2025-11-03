# AI DATA SOURCE VALIDATION SYSTEM

## 🎯 Purpose

This system **ensures that AI uses ONLY real-time yfinance data** and **NOT training data** for stock analysis.

## ✅ What Data is Fetched from YFinance

### 1. **Real-Time Price Data** (via `realtime_price_fetcher.py`)
- ✅ Current price (fetched live)
- ✅ Timestamp (when fetched)
- ✅ Entry zone (calculated from current price)
- ✅ Target prices (conservative & aggressive)
- ✅ Stop loss levels

**Source**: `yfinance.fast_info` or `yfinance.history()`

### 2. **Fundamental Data** (via `fundamental_data_fetcher.py`)
#### Quarterly Results (Q-o-Q and Y-o-Y):
- ✅ Revenue growth % (quarter-over-quarter)
- ✅ Revenue growth % (year-over-year)
- ✅ Earnings growth % (quarter-over-quarter)
- ✅ Earnings growth % (year-over-year)
- ✅ Profit margin %
- ✅ Most recent quarter date

#### Annual Results (Y-o-Y):
- ✅ Annual revenue growth %
- ✅ Annual earnings growth %
- ✅ Annual profit margin %
- ✅ Most recent year date

#### Financial Health:
- ✅ Profitability status (yes/no)
- ✅ Net worth status (positive/negative)
- ✅ Debt-to-equity ratio
- ✅ Current ratio
- ✅ Return on Equity (ROE)
- ✅ Return on Assets (ROA)
- ✅ Free cash flow status

#### Institutional Ownership (when available):
- ⚠️  Institutional ownership % (limited for Indian stocks)
- ⚠️  Number of institutions (limited)
- ⚠️  Top 5 holders % (limited)

**Source**: `yfinance.quarterly_financials`, `yfinance.financials`, `yfinance.balance_sheet`, `yfinance.info`

### 3. **Technical Context** (via `exit_intelligence_analyzer.py`)
- ✅ Current price
- ✅ RSI (14-day)
- ✅ Price vs 20DMA (%)
- ✅ Price vs 50DMA (%)
- ✅ 10-day momentum (%)
- ✅ Volume ratio
- ✅ Recent trend (up/down/sideways)

**Source**: `yfinance.history()` with calculations

---

## 🔒 How Training Data Contamination is Prevented

### 1. **Explicit Warnings in AI Prompts**

Every AI prompt includes:

```
⚠️  CRITICAL INSTRUCTIONS FOR AI:
1. Use ONLY the above current price (₹XXXX) fetched just now
2. DO NOT use any memorized/training data prices for {TICKER}
3. Base ALL calculations on the real-time price above
4. If you need historical context, request it explicitly
5. Your analysis must be grounded in THIS price data ONLY
```

### 2. **Mandatory AI Confirmation**

AI **MUST** include this in every JSON response:

```json
"data_source_confirmation": {
    "used_provided_price": true,
    "used_provided_fundamentals": true,
    "no_training_data_used": true,
    "confirmation_statement": "I confirm using ONLY the yfinance data provided in this prompt for {TICKER}"
}
```

**Validation**: If this field is missing or contains `false` values, the analysis is **INVALID**.

### 3. **Data Freshness Timestamps**

Every data point includes:
- `fetch_time` / `timestamp` - When data was fetched
- `source` - Confirmation it's from yfinance

Example:
```
Current Price: ₹4699.00
Fetched At: 2025-11-03T11:14:44.281648
Source: yfinance.fast_info
```

---

## 🧪 How to Validate the System

### Option 1: Quick Validation (Single Ticker)

```bash
python3 ai_realtime_data_validator.py RELIANCE
```

**What it checks:**
- ✅ Price data fetched successfully
- ✅ Quarterly results available
- ✅ Annual results available
- ✅ Financial health data present
- ✅ Training data warnings present in prompts
- ✅ Institutional ownership (best effort)

**Expected Output:**
```
✅ Overall Status: PASS

Data Availability:
  ✅ Price Available: Available
  ✅ Quarterly Results: Available
  ✅ Annual Results: Available
  ❌ Institutional Ownership: Not Available (yfinance limitation)
  ✅ Financial Health: Available
```

### Option 2: Batch Validation (Multiple Tickers)

```bash
python3 ai_realtime_data_validator.py --test-file tickers_test.txt
```

Validates multiple tickers and saves comprehensive report.

### Option 3: Live Analysis Test

```bash
./run_without_api.sh claude test.txt 8 10
```

Check the output CSV for:
- `data_source_confirmation` field in logs
- Real-time prices in results
- Fetch timestamps

---

## 📊 What the AI Sees (Example Prompt)

When analyzing TRENT, the AI receives:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 REAL-TIME PRICE DATA (FETCHED FROM YFINANCE NOW)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Ticker: TRENT
Current Price: ₹4699.00
Fetched At: 2025-11-03T11:14:44.281648
Source: yfinance.fast_info
Symbol: TRENT.NS

SUGGESTED TRADING LEVELS (based on current price):
├─ Entry Zone: ₹4628.52 - ₹4722.49
├─ Target 1 (Conservative): ₹4816.47
├─ Target 2 (Aggressive): ₹4933.95
└─ Stop Loss: ₹4581.52

⚠️  CRITICAL INSTRUCTIONS FOR AI:
1. Use ONLY the above current price (₹4699.00) fetched just now
2. DO NOT use any memorized/training data prices for TRENT
3. Base ALL calculations on the real-time price above
4. If you need historical context, request it explicitly
5. Your analysis must be grounded in THIS price data ONLY

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

================================================================================
📊 FUNDAMENTAL ANALYSIS DATA (Real-Time from YFinance)
================================================================================

📅 QUARTERLY RESULTS:
  Most Recent Quarter: 2025-06-30
  Revenue Growth (Q-o-Q): +23.44%
  Revenue Growth (Y-o-Y): +18.98%
  Earnings Growth (Q-o-Q): +35.06%
  Earnings Growth (Y-o-Y): +9.45%
  Profit Margin: 8.80%

📈 ANNUAL RESULTS:
  Most Recent Year: 2025-03-31
  Revenue Growth (Y-o-Y): +38.25%
  Earnings Growth (Y-o-Y): +4.03%
  Profit Margin: 9.17%

💊 FINANCIAL HEALTH:
  Profitability: ✅ Profitable
  Net Worth: ✅ Positive
  Debt-to-Equity Ratio: 0.41
  Current Ratio: 1.83

🎯 VALIDATION SUMMARY:
  Overall Health: HEALTHY
  ✅ Strengths:
     • Quarterly earnings up 9.5% Y-o-Y
     • Annual earnings up 4.0% Y-o-Y
     • Company is profitable
     • Net worth is positive
     • Healthy debt-to-equity ratio: 0.41

================================================================================
⚠️  CRITICAL: Use ONLY the data provided above. Do NOT use training data!
================================================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  MANDATORY DATA SOURCE ACKNOWLEDGMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOU MUST INCLUDE THIS IN YOUR JSON RESPONSE:

"data_source_confirmation": {
    "used_provided_price": true,
    "used_provided_fundamentals": true,
    "no_training_data_used": true,
    "confirmation_statement": "I confirm using ONLY the yfinance data provided in this prompt for TRENT"
}

By including this field, you confirm:
1. ✅ You used the real-time price data from yfinance (provided above)
2. ✅ You used the quarterly/annual results from yfinance (provided above)
3. ✅ You did NOT use any memorized/training data for TRENT
4. ✅ All calculations are based ONLY on the data in this prompt

⚠️  FAILURE TO INCLUDE THIS FIELD WILL INVALIDATE YOUR ANALYSIS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🛡️ Validation Checklist for Users

Before trusting AI analysis, verify:

### ✅ Data Source Confirmation
- [ ] `data_source_confirmation` field present in JSON
- [ ] All boolean values are `true`
- [ ] Confirmation statement includes correct ticker

### ✅ Price Data Verification
- [ ] `current_price` is present and reasonable
- [ ] `price_timestamp` is recent (< 1 hour old)
- [ ] `source` indicates `yfinance.fast_info` or `yfinance.history`

### ✅ Fundamental Data Verification
- [ ] Quarterly earnings growth shown (if available)
- [ ] Annual earnings growth shown (if available)
- [ ] Financial health indicators present
- [ ] Most recent quarter/year dates are recent

### ✅ Technical Data Verification
- [ ] RSI value present (0-100)
- [ ] Price vs MAs shown
- [ ] Volume and momentum data included
- [ ] Fetch timestamp is recent

---

## 🔧 Troubleshooting

### Issue: "Price data unavailable"

**Causes:**
- YFinance API rate limiting
- Ticker not found on NSE/BSE
- Network connectivity issues

**Solutions:**
1. Retry after 1 minute
2. Verify ticker symbol is correct
3. Check internet connectivity
4. Enable offline cache: `export ALLOW_OFFLINE_PRICE_CACHE=1`

### Issue: "Institutional ownership not available"

**This is normal** - YFinance has limited institutional data for Indian stocks.

**Workaround:**
- Use Moneycontrol or Screener.in for institutional holding data manually
- Focus on quarterly/annual results which are reliably available

### Issue: "Fundamental data fetch failed"

**Causes:**
- Company too new (no financial history)
- Data not available on YFinance
- API timeout

**Solutions:**
1. Verify company has at least 1 year of trading history
2. Check if company files quarterly results
3. Use backup sources for fundamental data

---

## 📈 Historic Data vs Real-Time Data

### When to Use Real-Time Data (YFinance):
- ✅ Current price
- ✅ Recent quarterly/annual results (last 4 quarters, last 4 years)
- ✅ Current financial health metrics
- ✅ Recent technical indicators (last 200 days)

### When Training Data is Acceptable:
- ✅ Historical context (pre-2025 data for trends)
- ✅ Industry benchmarks and standards
- ✅ Company background and business model
- ✅ Sector correlations and patterns

**Rule of Thumb**: If it affects **current price targets or recommendations**, it MUST be from yfinance.

---

## 🎯 Success Indicators

Your system is working correctly if:

1. ✅ Every AI response includes `data_source_confirmation`
2. ✅ Price data is fetched within last hour
3. ✅ Quarterly/annual data shows recent quarters (2024-2025)
4. ✅ AI's price-based calculations use the provided current price
5. ✅ Validation script shows "PASS" status

---

## 📝 Quick Reference Commands

```bash
# Validate single ticker
python3 ai_realtime_data_validator.py RELIANCE

# Validate multiple tickers
python3 ai_realtime_data_validator.py --test-file tickers_test.txt

# Run full analysis with validation
./run_without_api.sh claude test.txt 48 10

# Check specific fetchers directly
python3 realtime_price_fetcher.py TRENT bullish 5.0
python3 fundamental_data_fetcher.py TRENT
```

---

## 🔐 Security & Privacy

- ✅ No data is sent to external servers (except YFinance API)
- ✅ All caching is local and optional
- ✅ API keys (for Claude/Codex) are stored in environment variables
- ✅ No sensitive user data is logged

---

## 📚 Related Documentation

- `REALTIME_DATA_IMPLEMENTATION.md` - Implementation details
- `YFINANCE_VALIDATION_REPORT.md` - YFinance data quality analysis
- `realtime_price_fetcher.py` - Price fetching code
- `fundamental_data_fetcher.py` - Fundamental data code
- `ai_realtime_data_validator.py` - Validation tool

---

## ✅ Final Verification

Run this command to verify your system:

```bash
python3 ai_realtime_data_validator.py TRENT && \
  echo "✅ Validation system is working correctly!"
```

Expected output should show:
- ✅ Price data fetched
- ✅ Fundamental data available
- ✅ Training data warnings present
- ✅ Overall Status: PASS

---

**Last Updated**: 2025-11-03
**System Version**: 3.0 (Real-Time Data Validation)
