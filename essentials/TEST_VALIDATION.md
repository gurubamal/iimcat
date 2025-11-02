# TEST VALIDATION GUIDE

## All Fixes Applied ✅

1. ✅ Verbose logging in `cursor_cli_bridge_enhanced.py`
2. ✅ Improved market data error handling
3. ✅ News quality filtering (reject generic headlines)
4. ✅ Stricter heuristic scoring (require confirmation + numbers)
5. ✅ 40% certainty threshold enforcement

---

## Quick Test Commands

### Test 1: Market Data Fetch (Manual)
Test if yfinance is working:
```bash
python3 << 'EOF'
import yfinance as yf
from datetime import datetime, timedelta

ticker = "RELIANCE.NS"
stock = yf.Ticker(ticker)

print(f"Ticker: {ticker}")
print(f"Name: {stock.info.get('longName')}")
print(f"Market Cap: ₹{stock.info.get('marketCap', 0)/1e7:.0f} crores")

end_date = datetime.now()
start_date = end_date - timedelta(days=90)
hist = stock.history(start=start_date, end=end_date)

print(f"\nHistory: {len(hist)} days")
if not hist.empty:
    print(hist.tail(3))
    print(f"\nLatest close: ₹{hist['Close'].iloc[-1]:.2f}")
    print(f"Avg volume (20d): {hist['Volume'].tail(20).mean():,.0f}")
else:
    print("⚠️  No history available (weekend/holiday)")
EOF
```

**Expected output:**
- ✅ Company name shown
- ✅ Market cap in crores
- ✅ Price history (or warning if weekend)

---

### Test 2: Cursor Bridge (Manual)
Test the bridge with sample data:
```bash
echo "
Ticker: RELIANCE
Headline: Reliance Industries reports Q2 profit up 15% to ₹21,000 crores
Snippet: Reliance Industries reported consolidated net profit of ₹21,000 crores for Q2 FY25, marking a 15% year-on-year growth. The company announced strong performance across all segments.
Source: Economic Times
" | python3 cursor_cli_bridge_enhanced.py
```

**Expected output:**
- ✅ Bridge debug header shown
- ✅ Ticker parsed: RELIANCE
- ✅ Market data fetched successfully
- ✅ Score between 40-80 (realistic)
- ✅ JSON output with all fields

---

### Test 3: Small Batch Run (3 Stocks, 48h)
Test the full system with 3 stocks:
```bash
./run_with_quant_ai.sh test_3_stocks.txt 48
```

**Expected behaviors:**

1. **News Filtering:**
   - ⏭️  SKIPPED messages for generic headlines
   - Only quality news analyzed
   - Examples:
     - ❌ "Q2 results this week" → SKIPPED
     - ❌ "Among 300 firms" → SKIPPED
     - ✅ "Reports ₹X profit" → ANALYZED

2. **Market Data:**
   - Bridge logs show:
     - ✅ Valid ticker confirmation
     - ✅ Market cap in crores
     - ✅ Price history fetched
   - No "Zero market cap" errors

3. **Scoring:**
   - Stage 1 and Stage 2 scores similar (within 20 points)
   - Realistic certainty (30-70%, not 0% or 95%)
   - Few or no catalysts detected (if news is generic)

4. **Certainty Filtering:**
   - Stocks with <40% certainty go to rejected file
   - Log shows: "X qualified stocks, Y rejected stocks"
   - Rejected file created: `*_rejected.csv`

5. **Output Files:**
   - `realtime_ai_analysis_*.csv` (qualified stocks only)
   - `realtime_ai_analysis_*_rejected.csv` (rejected stocks with reasons)
   - `realtime_ai_*.log` (detailed logs)

---

## What to Check in Results

### In Main CSV (`realtime_ai_analysis_*.csv`):
- ✅ All stocks have certainty ≥ 40%
- ✅ Scores are realistic (not all 90+)
- ✅ Catalysts only if confirmed news
- ✅ Reasoning mentions specific factors

### In Rejected CSV (`*_rejected.csv`):
- ✅ Clear rejection reasons
- ✅ Certainty < 40% shown
- ✅ Headlines explain why rejected

### In Logs (`realtime_ai_*.log`):
- ✅ "SKIPPED" messages for generic news
- ✅ Bridge debug info showing market data
- ✅ "Qualified/Rejected" count summary

---

## Success Criteria

✅ **All systems working if:**

1. No "No data available" in AI reasoning
2. Market cap logs show actual values (not zero)
3. 50-80% of news articles skipped (generic filtered)
4. Stage 1 ≈ Stage 2 scores (within 15-20 points)
5. Certainty scores realistic (30-70% range)
6. Rejected stocks file shows clear reasons
7. 0-2 qualified stocks (not 4/4 like before)

---

## Troubleshooting

### Issue: "Invalid ticker" in bridge logs
**Solution:** Check if ticker format correct (should be RELIANCE.NS)

### Issue: "No price history available"
**Solution:** Weekend/holiday - normal. Bridge uses info dict fallback.

### Issue: All news skipped
**Solution:** Good! Means only generic news available. Try 48-72h window.

### Issue: yfinance timeout
**Solution:** Network issue. Add retry or wait and try again.

### Issue: Still getting 0% certainty
**Solution:** Check that heuristic fixes applied correctly (confirmation words required).

---

## Next Steps After Validation

If tests pass:
1. Run on full ticker list with 48h window
2. Monitor rejected file to tune filters
3. Adjust certainty threshold if needed (via `MIN_CERTAINTY_THRESHOLD` env var)

If tests fail:
1. Check logs for specific errors
2. Test components individually (market data, bridge, news filter)
3. Verify all code changes applied correctly
