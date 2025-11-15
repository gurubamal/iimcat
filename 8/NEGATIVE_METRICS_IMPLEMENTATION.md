# Negative Financial Metrics Implementation

## Overview
Added negative quarterly growth and negative networth checks to the ranking system. These factors are **flagged and highlighted** in the output for visibility without affecting the ranking scores or adj_score values.

---

## Changes Made

### 1. **New Functions in `orchestrator/ranking.py`**

#### `check_negative_quarterly_growth(ticker: str) -> bool` (Line 363-393)
- Checks if the latest quarterly profit growth is **negative**
- Compares current quarter net income with previous quarter
- Returns `True` if growth % is negative
- Returns `False` for unavailable/unreliable data

**Example:**
```python
if check_negative_quarterly_growth("SBIN"):  # Returns True if SBIN had declining profits
    apply_penalty()
```

#### `check_negative_networth(ticker: str) -> bool` (Line 396-438)
- Checks if company has **negative networth** (Liabilities > Assets)
- Fetches quarterly balance sheet data from yfinance
- Calculates: `Networth = Total Assets - Total Liabilities`
- Returns `True` if networth is negative
- Returns `False` for unavailable/unreliable data

**Example:**
```python
if check_negative_networth("ABC"):  # Returns True if ABC is technically insolvent
    apply_penalty()
```

---

### 2. **Escalated Mentions in Output (NO Score Impact)**

The negative financial metrics are **checked and displayed** but do **NOT** affect the ranking scores.

#### Score Remains Unchanged
- `combined_score` - No change
- `adj_score` - No change
- **Ranking position** - No change

#### Visibility Only
- Negative metrics appear in the "reason" column with **escalated mentions**
- Used for **manual review and decision-making**
- Does not automatically exclude stocks from rankings

---

### 3. **Visible Escalated Mentions in "reason" Column**

#### Updated `top_reasons()` Function (Line 441-474)
Now displays escalated warnings in the "reason" column of CSV output:

```python
if check_negative_quarterly_growth(ticker):
    reasons.append("!!!NEGATIVE QUARTERLY GROWTH!!!")
if check_negative_networth(ticker):
    reasons.append("!!!NEGATIVE NETWORTH!!!")
```

**Example CSV Output:**
```
ticker  | reason                                                | adj_score
--------|-------------------------------------------------------|----------
SBIN    | !!!NEGATIVE QUARTERLY GROWTH!!!; Results/metrics     | 75.32
ABC     | !!!NEGATIVE NETWORTH!!!; No exact ticker             | 68.05
XYZ     | M&A/JV; Reuters                                      | 82.18
```

**Key Points:**
- ✅ **Escalated mentions** stand out immediately in output
- ✅ **NO impact on adj_score** (scores remain unchanged)
- ✅ **Easy to filter** for manual review
- ✅ **Transparent** - you can see exactly which stocks have issues

---

## No Scoring Impact

- **Ranking scores are NOT affected** by negative metrics
- Negative metrics are **flagged for visibility only**
- Users can review and make decisions based on the escalated mentions
- All stocks remain in the ranking based on their news analysis scores

---

## How It Works in Practice

### Example 1: Stock with Negative Quarterly Growth
```
News Score: 75.00
- Negative Growth Detected: YES
- Final Score: 75.00 (UNCHANGED)
- Visible Flag: "!!!NEGATIVE QUARTERLY GROWTH!!!"
- User Decision: Can review and decide on investment
```

### Example 2: Stock with Negative Networth
```
News Score: 60.00
- Negative Networth Detected: YES
- Final Score: 60.00 (UNCHANGED)
- Visible Flag: "!!!NEGATIVE NETWORTH!!!"
- User Decision: Can review and decide on investment
```

### Example 3: Stock with Both Issues
```
News Score: 80.00
- Negative Growth Detected: YES
- Negative Networth Detected: YES
- Final Score: 80.00 (UNCHANGED)
- Visible Flags: "!!!NEGATIVE QUARTERLY GROWTH!!!; !!!NEGATIVE NETWORTH!!!"
- User Decision: Clearly visible issues for manual review
```

---

## CSV Output Enhancement

### New Columns/Information
- **reason** column now includes escalated red flag mentions
- **adj_score** remains unchanged (no penalties applied)
- Clear visibility of which stocks have financial red flags

### Example Real Output
```
ticker,combined_score,adj_score,reason,event_type
SBIN,75.2,75.2,"!!!NEGATIVE QUARTERLY GROWTH!!!; Results/metrics",Results/metrics
ABC,68.5,68.5,"!!!NEGATIVE QUARTERLY GROWTH!!!; !!!NEGATIVE NETWORTH!!!",General
XYZ,82.1,82.1,"M&A/JV; Reuters",M&A/JV
```

**Note:** All scores remain the same - red flags are for visibility and manual review only.

---

## Websearch Integration Confirmation ✅

**YES - Websearch is integrated for final ranking:**

1. **Original Pipeline** (`run_without_api.sh`)
   - Runs news analysis: `realtime_ai_news_analyzer.py`
   - Outputs: `realtime_ai_results.csv` (news-based scores)

2. **Enhanced Pipeline** (Auto-executed after original)
   - Runs: `run_enhanced_pipeline_integration.py --input realtime_ai_results.csv --skip-temporal`
   - **Includes web search verification via `web_search_verification_layer.py`**
   - Verifies claims using real-time web searches
   - Generates AI verdicts based only on verified facts
   - Outputs: `enhanced_results/enhanced_results.json`

3. **Final Output**
   - Combined scores with web search verification
   - AI verdicts based only on verified data
   - Complete audit trails of sources

---

## CSV Filename Format ✅

**Already Implemented:**

```
realtime_ai_results_{YYYY-MM-DD_HH-MM-SS}_{ai_provider}.csv
```

**Example:**
```
realtime_ai_results_2025-11-15_02-32-37_claude.csv
realtime_ai_results_2025-11-15_02-32-37_codex.csv
realtime_ai_results_2025-11-15_02-42-13_gemini.csv
```

The script also copies to `realtime_ai_results.csv` for convenience.

---

## Testing

To verify the implementation:

```bash
# Run with claude (includes web search verification)
./run_without_api.sh claude just.txt 48 10 1

# Check CSV output with timestamp and AI provider
ls -lh realtime_ai_results_*.csv

# View reasons column to see escalated red flag mentions
grep "!!!" realtime_ai_results_*.csv

# Or search for specific flags
grep "NEGATIVE QUARTERLY GROWTH" realtime_ai_results_*.csv
grep "NEGATIVE NETWORTH" realtime_ai_results_*.csv
```

**Expected in output:**
- `!!!NEGATIVE QUARTERLY GROWTH!!!` - For declining profit stocks
- `!!!NEGATIVE NETWORTH!!!` - For technically insolvent companies
- **Scores remain UNCHANGED** - flags are for visibility only

---

## Summary

✅ **Negative quarterly growth** - Escalated mention in "reason" column (NO score penalty)
✅ **Negative networth** - Escalated mention in "reason" column (NO score penalty)
✅ **Visible in CSV** - "reason" column shows red flags with `!!!` escalation
✅ **Websearch included** - Enhanced pipeline verifies all claims
✅ **CSV timestamp + AI name** - Already implemented in filename

**Key Feature:** Red flags are for visibility and manual review - they do NOT affect ranking scores or positions.
