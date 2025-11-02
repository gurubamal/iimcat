# 🚀 HANDY AI SCAN GUIDE

**✅ Updated 2025-10-26:** Fixed bug where Step 2 scanned all stocks instead of respecting ticker file.

## Super Simple - Just 2 Arguments!

```bash
./ai_scan <provider> <ticker-file>
```

That's it! No complicated options, just provider and ticker file.

---

## ⚡ Quick Commands

### 1. Scan All Stocks (Easiest!)
```bash
./scan_all
```
Uses Codex AI, scans all.txt automatically.

### 2. Scan NIFTY 50 Only
```bash
./scan_nifty
```
Uses Codex AI, scans nifty50_tickers.txt automatically.

### 3. Custom Scan with Codex
```bash
./ai_scan codex my_stocks.txt
```

### 4. Quick Codex Scan (Short Form)
```bash
./ai_scan c all.txt
```

### 5. Scan with Cursor
```bash
./ai_scan cursor all.txt
```

---

## 🎯 Provider Options

| Option | Description | Example |
|--------|-------------|---------|
| `codex` | Codex AI (recommended) | `./ai_scan codex all.txt` |
| `c-agent` | Same as codex (alias) | `./ai_scan c-agent all.txt` |
| `c` | Same as codex (short) | `./ai_scan c all.txt` |
| `cursor` | Cursor AI | `./ai_scan cursor all.txt` |
| `auto` | Auto-detect | `./ai_scan auto all.txt` |

---

## 📁 Common Ticker Files

Check what you have:
```bash
ls *.txt
```

Common files:
- `all.txt` - All stocks
- `nifty50_tickers.txt` - NIFTY 50 only
- `nifty500_tickers.txt` - NIFTY 500
- Create your own: `my_picks.txt`

---

## ⚙️ What It Does (Automatic)

When you run `./ai_scan codex all.txt`:

✅ **Fixed Settings (No Config Needed):**
- Time window: Last 12 hours
- Articles per stock: 10 maximum
- Internet access: Enabled
- Certainty scoring: Enabled
- Fake rally detection: Enabled
- Enhanced scoring: Enabled

✅ **Auto-Configured:**
- AI bridge setup
- Environment variables
- Internet validation
- Quality filters

✅ **Output Files:**
- `ai_adjusted_top25_*.csv` - Your top picks!
- `*_rejected.csv` - Filtered stocks (transparency)
- `learning_debate.md` - AI recommendations
- `aggregated_full_articles_*` - Raw news data

---

## 📊 Example Session

```bash
$ ./ai_scan codex all.txt

╔════════════════════════════════════════════════════════════════╗
║               🤖 HANDY AI SCANNER                              ║
╚════════════════════════════════════════════════════════════════╝

📋 Scan Configuration:
   AI Provider:     Codex AI Shell Bridge
   Ticker File:     all.txt
   Ticker Count:    847 stocks
   Time Window:     12 hours (last 12h of news)
   Articles/Stock:  10 (maximum)
   Internet:        Enabled ✅

⏱️  This will scan 847 stocks for news in the last 12 hours...
   Press ENTER to continue (or Ctrl+C to cancel): 

🚀 Starting Scan...

📰 Step 1/2: Collecting News...
   ✅ Fetched 127 articles

🤖 Step 2/2: AI Analysis & Scoring...
   🧪 Agent probe: PASSED ✅
   ✅ Analyzed 42 stocks with news
   ✅ AI calls: 15/15

✅ SCAN COMPLETE!

📁 Results:
   Main Output:    ai_adjusted_top25_20251026_143045.csv
   Rejected:       ai_rejected_20251026_143045.csv
   AI Analysis:    learning_debate.md

🏆 Top 10 Stock Picks:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rank,Ticker,Score,Sentiment,Catalysts,Deal_Value,Certainty,Expected_Rise
1,RELIANCE,100,bullish,earnings|investment,18540,78,15
2,KEC,92,bullish,target_price,0,85,28
3,ALLCARGO,75,bullish,expansion,450,65,12
...
```

---

## 💡 Pro Tips

### 1. Create Custom Ticker Lists
```bash
# Create a file with one ticker per line
cat > my_picks.txt << EOF
RELIANCE
TCS
INFY
HDFCBANK
EOF

# Scan your custom list
./ai_scan c my_picks.txt
```

### 2. Multiple Scans Per Day
```bash
# Morning scan
./scan_all

# Evening scan (catches intraday news)
./scan_all
```

### 3. Quick Checks
```bash
# Just scan NIFTY 50 for quick check
./scan_nifty
```

### 4. Check Results Quickly
```bash
# View latest results
head -20 ai_adjusted_top25_*.csv | tail -10

# View rejected stocks
head -20 ai_*rejected*.csv | tail -10

# View AI analysis
cat learning_debate.md
```

---

## ❓ Common Questions

### Q: What if no news in last 12 hours?
**A:** Scan completes but shows "No output file found" - normal on quiet days.

### Q: How long does it take?
**A:** 
- Small list (50 stocks): 2-3 minutes
- NIFTY 50: 3-5 minutes
- All stocks (800+): 10-15 minutes

### Q: Can I scan more frequently?
**A:** Yes! Run every few hours to catch new news. News is only from last 12h.

### Q: What's the difference between providers?
**A:** All use the same enhanced `codex_bridge.py`. Use `codex` or `c` (they're identical).

### Q: Can I change the 12-hour window?
**A:** Not in handy mode (by design - keeps it simple). Use advanced mode if needed:
```bash
# Advanced: custom time window
python3 run_swing_paths.py --path ai --hours 48 --top 50
```

---

## 🆘 Troubleshooting

### Problem: "Ticker file not found"
```bash
# List available files
ls *.txt

# Use correct filename
./ai_scan codex <correct-filename>.txt
```

### Problem: "Invalid provider"
```bash
# Check valid options
./ai_scan --help

# Use valid provider
./ai_scan codex all.txt  # ✅
./ai_scan wrong all.txt  # ❌
```

### Problem: No results
- Check if there's news in last 12 hours
- Try longer window with advanced command:
  ```bash
  python3 run_swing_paths.py --path ai --hours 24 --top 50
  ```

---

## 📚 More Info

- **Test AI bridge:** `./test_ai_bridge_fix.sh`
- **Full details:** `cat AI_BRIDGE_FIX_SUMMARY.md`
- **Advanced usage:** `cat AI_QUICK_START.md`

---

## 🎯 Summary

**Super simple 3 commands to remember:**

1. **Scan everything:** `./scan_all`
2. **Scan NIFTY 50:** `./scan_nifty`
3. **Custom scan:** `./ai_scan c <yourfile>.txt`

That's it! 🚀

---

**Last Updated:** 2025-10-26  
**Time Window:** Fixed 12 hours  
**Articles:** Up to 10 per stock  
**Status:** ✅ Ready to use!
