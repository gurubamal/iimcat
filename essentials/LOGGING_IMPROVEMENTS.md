# Enhanced Logging System - Quick Start

## What Changed?

The news collection system now has **comprehensive, beautiful logging** that shows you exactly what's happening at every step.

### Before (Old Logging)
```
[OSWALSEEDS] No fresh items in last 48h
[PALREDTEC] No fresh items in last 48h
[PANSARI] No fresh items in last 48h
...
```

### After (New Logging)
```
================================================================================
🔍 ENHANCED NEWS COLLECTION STARTED
================================================================================
📅 Time window: Last 48 hours (cutoff: 2025-10-07 18:30:40 UTC)
🎯 Tickers to scan: 50
📰 News sources: 12
================================================================================

[1/50 (2.0%)] Processing RELIANCE... ✅ FOUND 5 articles
    ├─ Fetched: 103 items from base sources
    ├─ Filtered out: 28 (too old), 75 (non-financial)
    └─ Latest headlines:
       1. [2h ago] Reliance Industries announces new green energy initiative...
       2. [5h ago] RIL Q2 earnings beat estimates with 15% YoY growth...
       3. [12h ago] Reliance Jio expands fiber network to 10 new cities...
    └─ 💾 Saved to: aggregated_full_articles_48h_20251009_183040.txt

[2/50 (4.0%)] Processing TCS... ⚫ NO NEWS
    └─ Fetched: 118 items
    └─ Filtered (old): 36, (non-financial): 82

...

================================================================================
📊 COLLECTION SUMMARY
================================================================================
✅ Successfully processed: 50/50 tickers
📰 Tickers with news: 8 (16.0%)
⚫ Tickers with no news: 42 (84.0%)
📄 Total articles saved: 23

🔍 Filtering statistics:
   ├─ Filtered (too old): 1,234
   └─ Filtered (non-financial): 3,456

🎯 Hit Rate: 16.00%
   ✅ EXCELLENT - Above 2% target!

📁 Output file: aggregated_full_articles_48h_20251009_183040.txt
================================================================================
```

## Key Features

### 1. Progress Tracking
- Shows `[X/Y (Z%)]` progress indicator
- Real-time updates as each ticker is processed
- Clear visual feedback

### 2. Detailed Statistics
- **Fetched**: How many items were retrieved
- **Filtered (old)**: Items outside time window
- **Filtered (non-financial)**: Items that don't look like financial news
- **Found**: Articles successfully saved

### 3. Visual Indicators
- ✅ **Success** - Found and saved articles
- ⚫ **No news** - No matching articles
- ❌ **Error** - Something went wrong
- ⚠️ **Warning** - Non-critical issue

### 4. Smart Summary
- Hit rate calculation and evaluation
- Total articles collected
- Filtering breakdown
- Performance assessment

### 5. Verbose Mode (NEW!)
Shows sample rejected URLs so you can understand what's being filtered:

```bash
python3 enhanced_india_finance_collector.py \
  --tickers RELIANCE TCS \
  --hours-back 48 \
  --verbose
```

Output includes:
```
└─ Sample OLD articles rejected:
   • [52.3h ago] Reliance Consumer revives Velvette... (www.livemint.com)
   • [68.1h ago] Flat profit, rising debt are worries... (www.livemint.com)

└─ Sample NON-FINANCIAL URLs rejected:
   • TCS Q2 results: Is it the right time to buy... (news.google.com/...)
   • Stocks to buy or sell: Osho Krishan suggests... (news.google.com/...)
```

## Quick Usage

### 1. Standard Scan (Clean Logging)
```bash
python3 enhanced_india_finance_collector.py \
  --tickers-file priority_tickers.txt \
  --hours-back 48 \
  --max-articles 5
```

### 2. Verbose Diagnostic Scan
```bash
python3 enhanced_india_finance_collector.py \
  --tickers RELIANCE TCS \
  --hours-back 48 \
  --verbose
```

### 3. Using Quick Scan Helper
```bash
# Standard priority scan
./quick_scan.sh priority

# Verbose scan for specific tickers
./quick_scan.sh verbose --tickers "RELIANCE TCS INFY"

# Weekend scan (96 hours)
./quick_scan.sh weekend

# Full diagnostic
./quick_scan.sh diagnostic --limit 10
```

### 4. Maximum Intelligence Scan
```bash
./optimal_scan_config.sh
```

## Command Line Options

### New Logging Options
- `--verbose` or `-v` - Enable detailed diagnostic logging
- `--show-samples N` - Number of sample URLs to show (default: 3)

### Existing Options Enhanced
- `--hours-back N` - Time window (now shown in summary)
- `--max-articles N` - Max per ticker (progress tracked)
- `--all-news` - Disable financial filtering (shows impact in stats)

## Understanding the Output

### Hit Rate Evaluation
- **≥ 2.0%** → ✅ EXCELLENT - Above target
- **1.0-2.0%** → ⚠️ GOOD - Acceptable
- **< 1.0%** → ⚠️ LOW - Needs adjustment

### Common Patterns

#### High "Filtered (old)" Count
→ **Good sign!** Means URLs are financial, just outside time window
→ **Solution**: Normal on weekdays. Use `--hours-back 72` on weekends

#### High "Filtered (non-financial)" Count  
→ **Investigation needed** - URLs don't look financial
→ **Solution**: Use `--verbose` to see samples, consider `--all-news`

#### Low "Fetched" Count
→ **Connection issue** or tickers have little news
→ **Solution**: Try high-profile tickers (RELIANCE, TCS, INFY) to test

## Troubleshooting

### No Articles Found
1. Run with `--verbose` to see what's being rejected
2. Check if filtering is too aggressive
3. Try `--all-news` to test without filtering
4. Increase `--hours-back` (especially on weekends)

### Low Hit Rate
1. Check "Filtered" counts - which is higher?
2. If mostly "old": Increase time window
3. If mostly "non-financial": Review verbose output, consider `--all-news`
4. Try with known-good tickers first

### Many Errors
1. Check network connectivity
2. Verify news source domains are accessible
3. Check verbose output for specific error messages

## Helpful Scripts

### quick_scan.sh
Convenient wrapper with predefined modes:
```bash
./quick_scan.sh --help           # Show all options
./quick_scan.sh standard         # Clean logging
./quick_scan.sh verbose          # Detailed diagnostics
./quick_scan.sh diagnostic       # Full details
./quick_scan.sh weekend          # 96-hour scan
./quick_scan.sh priority         # Top 20 tickers
```

### demo_logging.sh
Interactive demonstration of all logging modes:
```bash
./demo_logging.sh                # Shows all modes step by step
```

### optimal_scan_config.sh
Maximum intelligence scan with best parameters:
```bash
./optimal_scan_config.sh         # Complete AI-powered analysis
```

## Save Logs to File

```bash
# Save to file with console output
python3 enhanced_india_finance_collector.py ... 2>&1 | tee scan.log

# Quick scan with auto-save
./quick_scan.sh verbose --save-log scan.log

# Save only to file (no console)
python3 enhanced_india_finance_collector.py ... > scan.log 2>&1
```

## Complete Documentation

- **LOGGING_GUIDE.md** - Comprehensive logging documentation
- **AI_STOCK_SCANNER_GUIDE.md** - Complete system guide
- **QUICK_START.md** - Getting started guide

## Examples

### Example 1: Quick Test
```bash
python3 enhanced_india_finance_collector.py \
  --tickers RELIANCE TCS INFY \
  --hours-back 48
```

### Example 2: Diagnostic Investigation
```bash
python3 enhanced_india_finance_collector.py \
  --tickers RELIANCE \
  --hours-back 48 \
  --verbose \
  --show-samples 5 \
  --all-news
```

### Example 3: Weekend Scan
```bash
./quick_scan.sh weekend --limit 50
```

### Example 4: Production Scan
```bash
python3 enhanced_india_finance_collector.py \
  --tickers-file priority_tickers.txt \
  --hours-back 48 \
  --max-articles 10 \
  --verbose 2>&1 | tee "scan_$(date +%Y%m%d_%H%M%S).log"
```

## What to Look For

### Good Run
- ✅ Hit rate ≥ 2%
- ✅ Most filtering is "too old" (financial URLs)
- ✅ Recent headlines shown
- ✅ Minimal errors

### Needs Attention
- ⚠️ Hit rate < 1%
- ⚠️ Most filtering is "non-financial"
- ⚠️ Many errors
- ⚠️ All articles > 48h old

## Next Steps

1. **Test the new logging**: Run `./demo_logging.sh`
2. **Try verbose mode**: See what's being filtered and why
3. **Read the guide**: Check LOGGING_GUIDE.md for details
4. **Run production scans**: Use `./optimal_scan_config.sh`

## Version
Enhanced Logging System v2.0 - October 2025

The logging improvements maintain backward compatibility while providing dramatically better visibility into the collection process. All existing scripts and commands continue to work with enhanced output.
