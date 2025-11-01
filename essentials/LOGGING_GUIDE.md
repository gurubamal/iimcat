# Enhanced News Collection Logging Guide

## Overview
The enhanced logging system provides detailed insights into the news collection process, helping you understand exactly what's happening at each step.

## Standard Logging (Default)

### Example Output
```
================================================================================
🔍 ENHANCED NEWS COLLECTION STARTED
================================================================================
📅 Time window: Last 48 hours (cutoff: 2025-10-07 18:30:40 UTC)
🎯 Tickers to scan: 5
📰 News sources: 12
================================================================================

[1/5 (20.0%)] Processing RELIANCE... ✅ FOUND 5 articles
    ├─ Fetched: 103 items from base sources
    ├─ Filtered out: 28 (too old), 75 (non-financial)
    └─ Latest headlines:
       1. [2h ago] Reliance Industries announces new green energy initiative...
       2. [5h ago] RIL Q2 earnings beat estimates with 15% YoY growth...
       3. [12h ago] Reliance Jio expands fiber network to 10 new cities...
    └─ 💾 Saved to: aggregated_full_articles_48h_20251009_183040.txt
```

### Key Indicators

- ✅ **FOUND X articles** - Successfully collected news
- ⚫ **NO NEWS** - No fresh articles found after filtering
- ❌ **Error** - An error occurred during collection
- ⚠️ **Warning** - Non-critical issue

### Progress Information

- **[X/Y (Z%)]** - Current ticker number, total, and percentage complete
- **Fetched: N items** - Total items retrieved from all sources
- **Filtered (old): N** - Items rejected because they're older than the time window
- **Filtered (non-financial): N** - Items rejected because the URL doesn't look financial

## Verbose Logging (--verbose or -v)

### Enable Verbose Mode
```bash
python3 enhanced_india_finance_collector.py \
  --tickers RELIANCE TCS \
  --hours-back 48 \
  --verbose
```

### Additional Information Shown

#### Sample Rejected URLs (Old)
```
└─ Sample OLD articles rejected:
   • [52.3h ago] Reliance Consumer revives Velvette, targets HUL... (www.livemint.com)
   • [68.1h ago] Flat profit, rising debt are growing worries... (www.livemint.com)
```

#### Sample Rejected URLs (Non-Financial)
```
└─ Sample NON-FINANCIAL URLs rejected:
   • TCS Q2 results 2025 today: Is it the... (news.google.com/rss/articles/CBMi-wF...)
   • Stocks to buy or sell: Osho Krishan... (news.google.com/rss/articles/CBMigw...)
```

Shows you exactly which URLs were rejected and why, helping you understand if the filters are working correctly.

### Adjust Sample Size
```bash
# Show 5 sample rejected URLs instead of default 3
python3 enhanced_india_finance_collector.py \
  --tickers RELIANCE \
  --hours-back 48 \
  --verbose \
  --show-samples 5
```

## Summary Statistics

### Collection Summary
```
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

⚠️  Errors encountered: 2

🎯 Hit Rate: 16.00%
   ✅ EXCELLENT - Above 2% target!

📁 Output file: aggregated_full_articles_48h_20251009_183040.txt
📁 Per-ticker files: full_articles_run_20251009_183040/
================================================================================
```

### Understanding Hit Rate

- **≥ 2.0%** - ✅ EXCELLENT - Above target
- **1.0-2.0%** - ⚠️ GOOD - Acceptable performance
- **< 1.0%** - ⚠️ LOW - Consider adjusting parameters

### Hit Rate Improvement Tips

1. **Increase time window**: Use `--hours-back 72` or `--hours-back 96` for weekends
2. **Add more sources**: Include additional trusted news domains
3. **Disable financial filtering**: Use `--all-news` to see all matched articles
4. **Check verbose output**: Use `-v` to see what's being filtered

## Understanding Filtering

### Why Articles Get Filtered

#### 1. Too Old (Outside Time Window)
Articles published before the cutoff time are automatically filtered.

**Solution**: Increase `--hours-back` parameter
```bash
--hours-back 72  # 3 days
--hours-back 168 # 1 week
```

#### 2. Non-Financial URL
URLs that don't appear to be financial content are filtered.

The system checks for financial indicators in the URL path:
- `/business/`, `/finance/`, `/markets/`
- `/earnings/`, `/companies/`, `/economy/`
- `/stocks/`, `/trading/`, `/investing/`

**Solution A**: Disable filtering for broader results
```bash
--all-news  # Includes all news, not just financial
```

**Solution B**: Add domain hints for specific sites (advanced)
```bash
--ir-domains tatamotors.com relianceindustries.com
```

## Common Scenarios

### Scenario 1: All tickers showing "NO NEWS"
**Diagnosis**: Check verbose output to see rejection reasons
```bash
python3 enhanced_india_finance_collector.py \
  --tickers-file priority_tickers.txt \
  --hours-back 48 \
  --verbose | tee scan.log
```

**Common causes**:
- Time window too narrow (especially on weekends)
- Most URLs filtered as non-financial
- Sources returning old articles

**Solutions**:
1. Increase time window: `--hours-back 72`
2. Try `--all-news` to bypass financial filtering
3. Add more news sources with `--sources`

### Scenario 2: Low hit rate (< 1%)
**Check**:
1. Are articles being fetched? (Look at "Fetched: N items")
2. What's the main filter reason? (old vs non-financial)

**If many items fetched but filtered**:
- Use `--all-news` to see what you're missing
- Check verbose output to understand URL patterns

**If few items fetched**:
- Add more news sources
- Check network connectivity
- Try specific high-quality tickers (RELIANCE, TCS, INFY)

### Scenario 3: Many errors
Check the error messages in the output. Common issues:
- Network timeouts (temporary, will retry)
- Invalid RSS feeds (check `--extra-rss` URLs)
- NewsAPI key issues (check `--newsapi-key`)

## Performance Optimization

### Fast Scan (Priority Tickers Only)
```bash
python3 enhanced_india_finance_collector.py \
  --tickers-file priority_tickers.txt \
  --limit 20 \
  --hours-back 24
```

### Comprehensive Weekend Scan
```bash
python3 enhanced_india_finance_collector.py \
  --tickers-file sec_tickers.txt \
  --hours-back 96 \
  --max-articles 10 \
  --verbose
```

### Maximum Intelligence Scan (Recommended)
```bash
./optimal_scan_config.sh
```

This runs the complete intelligence pipeline with optimized settings.

## Log Files

### Aggregate Output File
**File**: `aggregated_full_articles_48h_YYYYMMDD_HHMMSS.txt`

Contains all collected articles with full text, metadata, and analysis.

### Per-Ticker Files
**Directory**: `full_articles_run_YYYYMMDD_HHMMSS/`

Individual files for each ticker with news.

### Console Output Redirection
```bash
# Save console output to file
python3 enhanced_india_finance_collector.py ... 2>&1 | tee collection.log

# Save only to file (no console output)
python3 enhanced_india_finance_collector.py ... > collection.log 2>&1
```

## Quick Reference Commands

### Basic scan with good logging
```bash
python3 enhanced_india_finance_collector.py \
  --tickers RELIANCE TCS INFY HDFCBANK ICICIBANK \
  --hours-back 48 \
  --max-articles 5
```

### Verbose diagnostic scan
```bash
python3 enhanced_india_finance_collector.py \
  --tickers RELIANCE TCS \
  --hours-back 48 \
  --verbose \
  --show-samples 5
```

### Full scan with all news (no filtering)
```bash
python3 enhanced_india_finance_collector.py \
  --tickers-file priority_tickers.txt \
  --hours-back 72 \
  --all-news \
  --max-articles 10
```

## Interpreting Results

### Good Results
- Hit rate ≥ 2%
- Most filtering is "too old" (means URLs are financial)
- Clear, recent headlines shown
- Minimal errors

### Needs Adjustment
- Hit rate < 1%
- Most filtering is "non-financial"
- Many errors
- No recent articles

### Next Steps for Poor Results
1. Run with `--verbose` to diagnose
2. Check sample rejected URLs
3. Adjust time window or filtering
4. Try `--all-news` as a test
5. Verify news sources are responding

## Support

For issues or questions:
1. Check verbose output first
2. Review filtering statistics
3. Test with known-good tickers (RELIANCE, TCS, INFY)
4. Check network connectivity
5. Verify news source domains are accessible

## Version
Enhanced logging system v2.0 - Updated October 2025
