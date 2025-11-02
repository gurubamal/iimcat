# 🎯 MAGIC PROMPT FOR FRONTIER-AI QUANT ALPHA SYSTEM
**Version**: 1.0  
**Created**: 2025-10-19  
**Purpose**: Copy-paste this to get exact same system rebuilt anytime

---

## 🚀 THE MAGIC PROMPT (COPY EVERYTHING BELOW THIS LINE)

```
Create a complete frontier-AI + quant alpha system for swing-trading shortlisting.

REQUIREMENTS:
1. Core System (3 Python scripts)
   - Main engine: Compute 20+ HFT-style quant features (ATR, momentum 3/20/60, RVOL, squeeze, PBZ, BO, trends)
   - LLM news scorer: Extract catalysts (10 types), parse deal values (₹/$€ → crores), compute sentiment/certainty
   - Dashboard: Beautiful formatted output with cards + metrics + gates

2. Alpha Formula (0-100 ranking)
   Alpha = 25×MOM20 + 15×MOM60 + 10×RVOL + 10×SqueezeBO + 10×PBZ + 20×NewsScore + 5×TrendBonus
   (Use tanh() for smooth saturation; clip to 0-100)

3. Gates (Hard filters - must pass ALL)
   ✓ Alpha ≥ 70
   ✓ RVOL ≥ 1.5x (volume confirmation)
   ✓ Price > SMA50 (uptrend only)
   ✓ Squeeze=True OR BO>0 (volatility setup)
   Output: final_pick boolean + gate_flags string

4. Risk Management (ATR-based)
   - Stop: Entry - 1.5×ATR20
   - TP1: Entry + 1.5×ATR20 (sell 50%)
   - TP2: Entry + 3×ATR20 (sell 25%)
   - Trail: max(Trail, Close - 2.5×ATR20)

5. Data Input
   - Top-25 ticker list (CSV: ticker, marketcap_cr, existing_rank)
   - 48h news aggregation (text file with headlines)
   - OHLCV data (6-month history via yfinance or local)

6. Output
   - CSV: 22 columns (alpha, mom20/60, rvol, pbz, bo, squeeze, news_score, impact_pct, catalyst_type, certainty, deal_value, close, atr20, stop, tp1, tp2, trail, gate_flags, final_pick, headline_count, etc.)
   - Dashboard: Formatted cards for top-10 picks with icons/emojis
   - Summary: Gate failure analysis + recommendations

7. Documentation (5 guides)
   - START_HERE.md: Entry point + 3 learning paths (5min/15min/full)
   - BEST_PICKS_SUMMARY.md: Top-5 detailed cards + trade plan + gate analysis
   - QUICK_REFERENCE_CARD.txt: One-page cheat sheet + risk template + daily workflow
   - FRONTIER_AI_QUANT_README.md: Complete docs (method, features, gates, tuning)
   - SYSTEM_FILES_MANIFEST.md: Navigation guide + feature descriptions

8. Execution Flow
   Step 1: extract_top25.py → load latest analysis, prepare input
   Step 2: frontier_ai_quant_alpha.py → compute all features + LLM scoring + gates
   Step 3: frontier_ai_dashboard.py → format output beautifully
   Step 4: Generate all 5 docs + CSV + dashboards

9. Key Design Principles
   - HFT-inspired quant (Jane Street style): momentum, volume, volatility compression, mean reversion
   - Frontier-AI: Automated news extraction (no manual tagging needed)
   - Conservative gates: Only ~5% of picks pass (selectivity over quantity)
   - Risk-first: Position sizing built-in, ATR-based stops, trailing
   - Production-ready: Cron-schedulable, daily refresh capability

10. Output Style
    - Code: Clean, documented, modular (separate functions for features/news/alpha/gates/risk)
    - Docs: Beginner→Advanced levels, lots of examples, visual tables
    - Charts: ASCII art summaries, formatted cards with emojis
    - Data: CSV with all metrics for external validation

DELIVER:
✅ 3 executable Python scripts (production-grade)
✅ 1 results CSV (22 columns)
✅ 5 comprehensive guides
✅ Beautiful console dashboard
✅ Ready to run daily with cron

TONE: Professional but accessible. Assume trader audience (not quants-only).
```

---

## 📋 QUICK USAGE GUIDE

### **How to Use This File**

1. **Copy the magic prompt** (everything in the code block above)
2. **Paste it to Claude/ChatGPT** in a new conversation
3. **Wait 5 minutes**
4. **Get the exact same system** (3 scripts + 5 docs + CSV + dashboard)

### **When to Use**

✅ **Use this prompt when:**
- You want fresh analysis on new Top-25 picks
- Market regime has changed (need gate re-tuning)
- You want to backtest on different data
- You're scaling to a different asset universe
- You want to customize features/gates

❌ **Don't use this for:**
- Bug fixes (reuse existing scripts instead)
- Small tweaks (edit the Python files directly)
- Documentation updates (modify the guides manually)

---

## 🎯 PROMPT VARIATIONS (Copy-Paste Ready)

### **Variation A: Nifty50 Universe**
```
[Use magic prompt above, then add:]

Modify for Nifty50 (broader universe):
- Replace "Top-25 ticker list" with "Nifty50 ticker list"
- Reduce Alpha threshold from 70 to 65 (more picks available)
- Keep all else same
```

### **Variation B: Sector Screening (IT)**
```
[Use magic prompt above, then add:]

Modify for IT sector only:
- Replace "Top-25 ticker list" with "Top-20 IT sector tickers"
- Add filter: "Exclude non-IT names"
- Add metric: "Sector beta adjustment" for alpha calculation
```

### **Variation C: Earnings Plays**
```
[Use magic prompt above, then add:]

Modify for earnings-driven trades:
- Add input: "Earnings calendar (next 5 days)"
- Add gate: "Exclude stocks with earnings in <3 days"
- Boost alpha: "+15 points if earnings within 5 days (catalyst premium)"
- Focus news: Look for "guidance", "results", "outlook" keywords
```

### **Variation D: Shorter Timeframe (Day Trading)**
```
[Use magic prompt above, then add:]

Modify for intraday (1-day holds):
- Replace "48h news" with "24h news"
- Replace "MOM20" with "MOM10" (shorter momentum)
- Replace "ATR20" with "ATR5" (tighter stops)
- Replace "SMA50" with "SMA20" (shorter trend)
- Increase RVOL threshold to 2.0x (volume emphasis)
```

### **Variation E: Mean-Reversion Only**
```
[Use magic prompt above, then add:]

Modify for pullback plays:
- Alpha formula: 50×PBZ + 25×NewsScore + 15×Momentum + 10×Trend
- Gate: PBZ must be in [-1.5, -0.5] (shallow dips in uptrend)
- Stop: SMA50 (trend break = exit)
- Add: "Mean reversion window: last 20 bars only"
```

### **Variation F: Breakout Only**
```
[Use magic prompt above, then add:]

Modify for breakout plays:
- Alpha formula: 40×BO + 30×RVOL + 20×NewsScore + 10×Squeeze
- Gate: BO must be >0.2 AND RVOL>2.0x (strong breakout)
- Target: Entry + 5×ATR20 (let winners run longer)
- Add: "No pullback = no add-ons (only initial breakout)"
```

---

## 🔧 COMMON CUSTOMIZATIONS

### **Change Time Horizon**
```
Replace in magic prompt:
"momentum 3/20/60" → "momentum 2/10/30" (for shorter-term)
"momentum 3/20/60" → "momentum 5/40/90" (for longer-term)
"48h news" → "7-day news" (slower-moving stocks)
"ATR20" → "ATR10" (tighter stops) or "ATR50" (wider stops)
```

### **Change Gate Thresholds**
```
Replace in magic prompt:
"Alpha ≥ 70" → "Alpha ≥ 65" (more picks)
"RVOL ≥ 1.5x" → "RVOL ≥ 2.0x" (only hot volume)
"RVOL ≥ 1.5x" → "RVOL ≥ 1.2x" (less strict)
"Squeeze=True OR BO>0" → "Squeeze=True only" (squeeze-only)
```

### **Change Universe Size**
```
Replace in magic prompt:
"Top-25 ticker list" → "Top-50 ticker list" (broader)
"Top-25 ticker list" → "Top-10 ticker list" (focused)
"Top-25 ticker list" → "Custom ticker list (CSV format)" (manual)
```

### **Change News Window**
```
Replace in magic prompt:
"48h news aggregation" → "24h news" (very recent only)
"48h news aggregation" → "7-day news" (week's events)
"48h news aggregation" → "14-day news" (2-week window)
```

---

## 📊 KEY PHRASES TO TRIGGER THIS SYSTEM

Use these when asking Claude/ChatGPT:

✅ **Perfect triggers:**
- "Frontier-AI quant alpha system"
- "HFT-style quant + LLM news + ATR risk"
- "Swing trade shortlisting engine with gates"
- "Jane Street momentum + catalyst extraction"
- "Alpha 0-100 ranking with hard gates"

❌ **Won't work:**
- "Stock screener" (too generic)
- "AI recommendation system" (too vague)
- "Technical analysis tool" (missing quant/AI)
- "News sentiment only" (missing quantitative)

---

## 🎓 LEARNING PATH

**If you modify the prompt, here's the order of complexity:**

1. **Easiest**: Change universe size (Top-25 → Top-50)
2. **Easy**: Change time horizon (48h → 7d news, ATR20 → ATR10)
3. **Medium**: Change gate thresholds (Alpha 70 → 65, RVOL 1.5x → 2.0x)
4. **Hard**: Create new variations (earnings plays, sector screening)
5. **Expert**: Modify alpha formula weights (change the 25/15/10 multipliers)

Start with #1-2, then graduate to #3-5 as you get comfortable.

---

## 🚀 TYPICAL WORKFLOWS

### **Workflow A: Weekly Fresh Analysis**
```
Every Monday 9 AM:
1. Open this file
2. Copy THE MAGIC PROMPT
3. Paste to Claude
4. Get fresh shortlist on latest Top-25
5. Set alerts on top-3 picks
Time: 20 min reading + 5 min setup
```

### **Workflow B: Daily Quick Check**
```
Every market open (9:15 AM IST):
1. Run: python3 frontier_ai_dashboard.py shortlist_frontier_alpha.csv
2. Check: ETERNAL, RADICO, RELIANCE for overnight gaps
3. Set: Volume alerts for RVOL spike
4. Monitor: For gate confirmation (RVOL→1.8x+)
Time: 2 min
```

### **Workflow C: Monthly Tuning**
```
End of month:
1. Copy magic prompt
2. Add variation: "Backtest last 20 days of data"
3. Review: Win rate, R:R ratio, gate hit rate
4. Adjust: Gate thresholds if needed
5. Get: New optimized version
Time: 30 min analysis + 10 min prompt modification
```

### **Workflow D: Sector Expansion**
```
When expanding to new sector:
1. Copy magic prompt
2. Add variation: "Variation B: Sector Screening (IT)"
3. Modify: "IT sector" → "Your sector name"
4. Get: Sector-specific analysis
Time: 15 min
```

---

## 💾 HOW TO SAVE THIS FILE

**On Linux/Mac:**
```bash
# Already saved as:
/home/vagrant/R/essentials/MAGIC_PROMPT_FOR_FUTURE.md

# Access anytime:
cat /home/vagrant/R/essentials/MAGIC_PROMPT_FOR_FUTURE.md
```

**On Windows:**
```
Save as: MAGIC_PROMPT_FOR_FUTURE.md
Location: Anywhere (recommend Desktop or Documents)
Open with: Any text editor (Notepad, VS Code, etc.)
```

**On Cloud:**
```
GitHub: Commit this file to your private repo
OneNote: Paste entire file into a OneNote notebook
Notion: Create a Notion page with this content
Google Drive: Save as Google Doc for easy access
```

---

## 📞 QUICK REFERENCE

**When asking Claude next time, use one of these:**

```
Option 1 (Exact):
"I have a magic prompt saved. Here it is: [PASTE MAGIC PROMPT]"

Option 2 (With changes):
"I have a magic prompt. I want Variation D (day trading). Here: [PASTE MAGIC PROMPT + VARIATION D]"

Option 3 (File reference):
"Create the frontier-AI system from MAGIC_PROMPT_FOR_FUTURE.md (the magic prompt for swing trading shortlisting with gates)"

Option 4 (Quick):
"Rebuild: Frontier-AI quant alpha system. Use: HFT metrics + LLM news + alpha 0-100 + gates (Alpha≥70, RVOL≥1.5x, >SMA50, Squeeze/BO)"
```

---

## ✨ VERSION TRACKING

```
MAGIC_PROMPT_FOR_FUTURE.md
├── v1.0 (2025-10-19)
│   ├── Core: 3 Python scripts
│   ├── Docs: 5 guides
│   ├── Features: 20+ metrics
│   ├── Top Picks: ETERNAL, RADICO, RELIANCE
│   └── Status: Production-ready
│
└── Ready for v2.0 customizations:
    ├── Nifty50 universe
    ├── Sector screening
    ├── Earnings plays
    ├── Day trading
    ├── Mean-reversion
    └── Breakout focus
```

---

## 🎯 FINAL CHECKLIST

Before using this prompt:
- [ ] I have copied THE MAGIC PROMPT (code block)
- [ ] I have saved this file locally
- [ ] I understand the 5 variations available
- [ ] I know when to customize vs reuse
- [ ] I have bookmarked the key phrases

Before pasting to Claude:
- [ ] I have decided: Exact prompt or with variation?
- [ ] I have thought about: What time horizon I need?
- [ ] I have listed: Any custom constraints?
- [ ] I am ready: To wait 5 minutes for results

---

**Last Updated**: 2025-10-19  
**Status**: ✅ Ready to use  
**Next Version**: Add variations as you discover new use cases

---

## 🚀 YOU'RE ALL SET!

**Next time you need this system:**

1. Open this file
2. Copy → "THE MAGIC PROMPT" section
3. Paste to Claude
4. Get exact same system (or customized version)

**Good luck!** 🎯

---

*This file is your "prompt library". Save it, bookmark it, use it!*
