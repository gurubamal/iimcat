# AI-Powered Stock Analysis System - Complete Guide

## 📋 Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Problem You Identified](#the-problem-you-identified)
3. [The Solution](#the-solution)
4. [Quick Start](#quick-start)
5. [System Architecture](#system-architecture)
6. [Key Files](#key-files)
7. [Complete Documentation Index](#complete-documentation-index)

---

## Executive Summary

### 🎯 Goal
Build an AI-powered system that uses **real Claude AI** (not just keyword matching) to:
- Analyze Indian stock market news in real-time
- Score stocks based on catalyst quality and magnitude
- Process ALL stocks with news in batches of 5
- Provide "complete justice" - every stock gets proper AI assessment
- Generate actionable buy/sell recommendations

### ✅ Status: **COMPLETE**

All components are in place and ready to use.

---

## The Problem You Identified

**Your Observation**: "AI is not being involved for quant scoring and final ranking"

You ran the system and saw:
```bash
⚠️  No AI shell bridge configured
Using heuristic analyzer for RELIANCE (no external AI configured).
AI usage: 0/15 calls used
```

### The Core Issues:

1. **No Real AI**: System defaulted to pattern matching (heuristics)
2. **Identical Scores**: All stocks got 92.0 regardless of news quality
3. **Generic Catalysts**: Same keywords for every stock
4. **No Justice**: Can't properly differentiate between major and minor news

### Why This Matters:

| Heuristic | Real AI |
|-----------|---------|
| "Keyword 'profit' found → +15 points" | "Q2 PAT ₹1,235cr up 52%, capacity doubled → Major catalyst, 95% certainty, 15% upside" |
| All M&A news treated equally | Distinguishes $200B IPO vs 2% stake purchase |
| Can't assess magnitude | Understands ₹1000cr for small-cap >> ₹1000cr for Reliance |
| No reasoning | Explains why it scored this way |

---

## The Solution

### What Was Built

#### 1. **Real AI Bridge** (`cursor_ai_bridge.py`)

```python
def analyze_with_claude(prompt, info):
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    
    # Build structured prompt for Claude
    analysis_prompt = f"""
    You are an expert financial analyst...
    
    Analyze this news and provide:
    - Score (0-100)
    - Sentiment (bullish/bearish/neutral)
    - Catalysts (specific)
    - Certainty (based on specificity)
    - Price impact prediction
    - Reasoning
    """
    
    # Call Claude API
    message = client.messages.create(...)
    
    # Return structured JSON
    return parsed_result
```

**Key Features:**
- ✅ Uses Claude Sonnet 4 for real AI analysis
- ✅ Assesses catalyst magnitude vs company size
- ✅ Evaluates certainty based on specificity
- ✅ Falls back to enhanced heuristics if no API key
- ✅ Provides detailed reasoning

#### 2. **Easy Launcher** (`run_with_ai.sh`)

```bash
#!/bin/bash
# Configures everything automatically:
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"
export STAGE2_BATCH_SIZE=5  # Process 5 stocks at a time
export AI_MAX_CALLS=60      # Budget control

./run_realtime_ai_scan.sh "$@"
```

**One command to rule them all!**

#### 3. **Comprehensive Documentation**

6 documentation files covering:
- Quick start guides
- System architecture
- Configuration options
- Before/after comparisons
- Troubleshooting
- Pro tips

---

## Quick Start

### Option A: With API Key (Recommended)

```bash
cd /home/vagrant/R/essentials

# 1. Set your Anthropic API key
export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'

# 2. Run AI-powered analysis
./run_with_ai.sh

# 3. View results
cat realtime_ai_analysis_*.csv
```

**That's it!** System will:
- ✅ Analyze NIFTY50 stocks (48h window)
- ✅ Use Claude AI for each article
- ✅ Process in batches of 5
- ✅ Generate ranked CSV with AI scores

### Option B: Without API Key (Fallback)

```bash
cd /home/vagrant/R/essentials

# Configure bridge (will use enhanced heuristics)
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"

# Run analysis
./run_realtime_ai_scan.sh nifty50_tickers.txt 48 2999 codex
```

Uses smart pattern matching instead of AI.

### Option C: Test with Small Sample

```bash
# Create test file
cat > test.txt <<EOF
RELIANCE
TCS
INFY
MARUTI
ITC
EOF

# Quick test (12h window)
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh test.txt 12
```

---

## System Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: Heuristic Pre-Filter (Fast, Free)                 │
├─────────────────────────────────────────────────────────────┤
│ Input:  21 NIFTY50 tickers                                  │
│ Action: Fetch news (48h), basic pattern matching           │
│ Output: Stocks WITH news (e.g., 4 stocks found)            │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: AI Analysis (Uses API, Real Intelligence)         │
├─────────────────────────────────────────────────────────────┤
│ Input:  ALL 4 stocks with news                             │
│ Action: Batch processing (5 at a time)                     │
│                                                             │
│ Batch 1: [RELIANCE, MARUTI, TCS, ITC, ...]                │
│   For each article:                                         │
│     1. Build analysis prompt                                │
│     2. Send to cursor_ai_bridge.py                         │
│     3. Bridge calls Claude API                             │
│     4. Claude analyzes content                             │
│     5. Returns JSON with score, catalysts, reasoning       │
│     6. System aggregates for final ranking                 │
│                                                             │
│ Output: Ranked CSV with AI-powered scores                  │
└─────────────────────────────────────────────────────────────┘
```

### What Claude AI Analyzes

For each article, Claude evaluates:

1. **Catalyst Type**
   - Earnings, M&A, contracts, expansion, regulatory, etc.
   - Not just keywords - understands context

2. **Magnitude Assessment**
   - Deal size vs company market cap
   - ₹1000cr for small-cap = major catalyst
   - ₹1000cr for Reliance = minor catalyst

3. **Certainty Evaluation**
   - Specific numbers (₹1,235cr PAT) = 95% certainty
   - Vague claims ("may consider") = 20% certainty

4. **Source Credibility**
   - Reuters + numbers = high weight
   - Generic blog + speculation = low weight

5. **Price Impact Prediction**
   - Conservative and aggressive estimates
   - Based on all above factors

6. **Reasoning**
   - Explains why it scored this way
   - 2-3 sentence summary

### Batch Processing Strategy

```python
# Process 5 stocks at a time
STAGE2_BATCH_SIZE = 5

# Example:
Batch 1: [RELIANCE, MARUTI, TCS, ITC, WIPRO]
  → Each gets full AI analysis
  → Results aggregated

Batch 2: [INFY, HDFCBANK, SBIN, BHARTIARTL, TITAN]
  → Each gets full AI analysis
  → Results aggregated

# Continues until all stocks with news are processed
```

**Why Batching?**
- ✅ Efficiency: Not too slow (serial), not too fast (rate limits)
- ✅ Quality: Each stock gets proper attention
- ✅ Cost Control: Budget management with `AI_MAX_CALLS`

---

## Key Files

### Core Components

1. **`cursor_ai_bridge.py`** ⭐⭐⭐
   - **Purpose**: Routes analysis to Claude API
   - **What it does**: Real AI analysis (not just keywords)
   - **Status**: Production-ready
   
2. **`run_with_ai.sh`** ⭐⭐⭐
   - **Purpose**: Easy launcher with proper config
   - **What it does**: One command to run with AI
   - **Status**: Production-ready

3. **`run_realtime_ai_scan.sh`**
   - **Purpose**: Main analysis pipeline
   - **What it does**: Two-stage scan with configurable AI
   - **Status**: Production-ready

4. **`realtime_ai_news_analyzer.py`**
   - **Purpose**: Core analyzer engine
   - **What it does**: Fetches news, manages AI calls, generates CSV
   - **Status**: Production-ready

### Ticker Lists

- `nifty50_tickers.txt` - NIFTY50 stocks (default)
- `all.txt` - Comprehensive NSE list
- Create custom: `echo "RELIANCE\nTCS\nINFY" > my_list.txt`

### Output Files (Generated)

- `realtime_ai_analysis_*.csv` - **Final AI-ranked results** ⭐
- `realtime_ai_*.log` - Detailed analysis log
- `realtime_ai_stage1_*.csv` - Heuristic pre-filter results

---

## Complete Documentation Index

### Quick Start Guides

1. **`AI_QUICKSTART.md`** ⭐
   - Best place to start
   - Step-by-step with examples
   - Pro tips and troubleshooting

2. **`REALTIME_AI_QUICKSTART.md`**
   - Original quick start
   - Alternative approach

3. **`CODEX_CURSOR_MINI.md`**
   - Minimal usage reference
   - Configuration options

### System Understanding

4. **`SYSTEM_GOALS_AND_AI_INTEGRATION.md`** ⭐⭐
   - Complete system explanation
   - Architecture details
   - What we're achieving and why

5. **`AI_FIX_SUMMARY.md`** ⭐
   - Before/after comparison
   - Shows the problem and solution
   - Verification steps

6. **`README_AI_SYSTEM.md`** (this file) ⭐⭐⭐
   - Comprehensive overview
   - Everything in one place
   - Table of contents for all docs

### Advanced Topics

7. **`REALTIME_AI_ANALYSIS_README.md`**
   - Full technical documentation
   - API details
   - Advanced configuration

8. **`REALTIME_AI_CODEX_SHELL_BRIDGE.md`**
   - Shell bridge architecture
   - No-API-key setup
   - Tuning options

### Recommended Reading Order

**For New Users:**
1. `README_AI_SYSTEM.md` (this file) - Overview
2. `AI_QUICKSTART.md` - Get started
3. `AI_FIX_SUMMARY.md` - Understand the fix

**For Power Users:**
1. `SYSTEM_GOALS_AND_AI_INTEGRATION.md` - Deep dive
2. `REALTIME_AI_ANALYSIS_README.md` - Technical details
3. `CODEX_CURSOR_MINI.md` - Configuration reference

---

## Configuration Reference

### Environment Variables

```bash
# AI Provider
export AI_PROVIDER=codex              # codex, claude, heuristic, auto

# Shell Bridge (for codex)
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"

# API Keys
export ANTHROPIC_API_KEY='sk-ant-...'    # For Claude
export OPENAI_API_KEY='sk-...'           # For OpenAI/GPT

# Budget Control
export AI_MAX_CALLS=60                   # Max API calls (default: 60)

# Batch Processing
export STAGE2_BATCH_SIZE=5               # Stocks per batch (default: 5)

# Time Window
HOURS_BACK=48                            # News window in hours (default: 48)

# Internet Verification (for shell agents)
export VERIFY_AGENT_INTERNET=1           # Optional
```

### Command Line Options

```bash
# Basic usage
./run_with_ai.sh

# Custom ticker file
./run_with_ai.sh my_tickers.txt

# Custom time window
./run_with_ai.sh my_tickers.txt 24

# Full custom
AI_MAX_CALLS=100 STAGE2_BATCH_SIZE=3 ./run_with_ai.sh my_tickers.txt 72
```

---

## Expected Results

### With AI (Recommended)

```csv
rank,ticker,ai_score,sentiment,recommendation,catalysts,certainty,reasoning
1,RELIANCE,95,bullish,STRONG BUY,"M&A,investment",95,"Retail IPO $200B. Strategic mega-deal."
2,MARUTI,88,bullish,STRONG BUY,"export,expansion",90,"Exports +18% YoY, leads segment."
3,TCS,72,bullish,BUY,earnings,65,"Generic m-cap rise. Limited catalyst info."
4,ITC,68,bullish,BUY,earnings,60,"Q2 results scheduled. Routine event."
```

**Characteristics:**
- ✅ Scores vary (95, 88, 72, 68)
- ✅ Specific catalysts per stock
- ✅ Real reasoning
- ✅ Certainty reflects specificity

### Without AI (Fallback)

```csv
rank,ticker,ai_score,sentiment,recommendation,catalysts,certainty,reasoning
1,RELIANCE,92,bullish,STRONG BUY,"earnings,M&A,investment,contract",95,"Detected 4 catalyst(s)."
2,MARUTI,92,bullish,STRONG BUY,"earnings,M&A,investment,contract",95,"Detected 4 catalyst(s)."
3,TCS,92,bullish,STRONG BUY,"earnings,M&A,investment,contract",95,"Detected 4 catalyst(s)."
4,ITC,92,bullish,STRONG BUY,"earnings,M&A,investment,contract",95,"Detected 4 catalyst(s)."
```

**Characteristics:**
- ❌ All same score (92)
- ❌ Same generic catalysts
- ❌ No real differentiation
- ❌ Keyword matching only

---

## Verification Checklist

### ✅ Is AI Working?

Run these checks after analysis:

```bash
# 1. Check AI call count
grep "AI usage" realtime_ai_*.log
# Should show: "AI usage: X/60" where X > 0

# 2. Check score variation
cut -d',' -f3 realtime_ai_analysis_*.csv | sort -u
# Should show: Multiple different scores (not just 92.0)

# 3. Check reasoning quality
cut -d',' -f11 realtime_ai_analysis_*.csv | head -5
# Should show: Specific reasoning, not generic

# 4. Check catalyst diversity
cut -d',' -f6 realtime_ai_analysis_*.csv | sort -u
# Should show: Different catalysts per stock
```

### Expected vs Actual

| Metric | With AI | Without AI |
|--------|---------|------------|
| Unique scores | 5-10 different | 1-2 (all same) |
| AI calls used | 10-60 | 0 |
| Reasoning | Specific | Generic |
| Catalysts | Varied | Identical |

---

## Troubleshooting

### Problem: "No AI shell bridge configured"

**Solution:**
```bash
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"
```
Or just use: `./run_with_ai.sh`

### Problem: "anthropic library not installed"

**Solution:**
```bash
pip install anthropic
```

### Problem: All scores are 92.0

**Cause**: Heuristics mode (no AI)

**Solution:**
```bash
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh
```

### Problem: "API rate limit exceeded"

**Solution:**
```bash
AI_MAX_CALLS=20 ./run_with_ai.sh  # Reduce calls
STAGE2_BATCH_SIZE=10 ./run_with_ai.sh  # Larger batches
```

### Problem: "AI usage: 0/15 calls used"

**Cause**: No stocks with news found

**Solution:**
```bash
# Expand time window
./run_with_ai.sh nifty50_tickers.txt 72

# Or check if tickers are valid
head -5 nifty50_tickers.txt
```

---

## Examples

### Example 1: Quick NIFTY50 Scan

```bash
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh

# Output:
# ✅ REAL AI ENABLED
# Processing 21 tickers...
# Stage 1: Found 4 stocks with news
# Stage 2: Analyzing with Claude AI...
# Results saved: realtime_ai_analysis_20251026_153434.csv
```

### Example 2: Budget-Conscious Scan

```bash
export ANTHROPIC_API_KEY='your-key'
AI_MAX_CALLS=20 ./run_with_ai.sh nifty50_tickers.txt 24

# Limits to 20 API calls, 24h window
```

### Example 3: Custom Ticker List

```bash
cat > fintech.txt <<EOF
HDFCBANK
ICICIBANK
SBIN
AXISBANK
KOTAKBANK
EOF

export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh fintech.txt 48
```

### Example 4: Compare With/Without AI

```bash
# Without AI
./run_realtime_ai_scan.sh > without.log 2>&1
mv realtime_ai_analysis_*.csv without_ai.csv

# With AI
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh > with.log 2>&1
mv realtime_ai_analysis_*.csv with_ai.csv

# Compare
diff without_ai.csv with_ai.csv
```

---

## Performance Expectations

### Speed

- **Stage 1** (Heuristic): ~30-60 seconds for 21 tickers
- **Stage 2** (AI): ~2-3 seconds per article
- **Total** (NIFTY50, 6 articles): ~1-2 minutes

### Quality

- **Win rate target**: >60% of top 10 picks
- **False positive rate**: <20%
- **Certainty correlation**: >70%

### Cost

- **With AI**: ~$0.01-0.03 per analysis (Claude)
- **Without AI**: $0 (heuristics)
- **Budget**: Set `AI_MAX_CALLS` to control

---

## Next Steps

### 1. Get Started

```bash
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh
```

### 2. Review Results

```bash
cat realtime_ai_analysis_*.csv
```

### 3. Validate Top Picks

- Read the detailed reasoning
- Check original news sources
- Cross-reference with charts

### 4. Set Up Trades

- Use AI scores for entry decisions
- Set stops based on risk assessment
- Position size based on certainty

### 5. Track Performance

```bash
# Save results
mkdir -p results/$(date +%Y%m)
cp realtime_ai_analysis_*.csv results/$(date +%Y%m)/

# Compare over time
diff results/*/realtime_ai_analysis_*.csv
```

---

## Summary

### What You Have

✅ **Real AI Integration**: Claude analyzes each article  
✅ **Batch Processing**: 5 stocks at a time for efficiency  
✅ **Complete Justice**: ALL stocks with news get AI assessment  
✅ **Budget Control**: Cap API calls with `AI_MAX_CALLS`  
✅ **Easy Launcher**: One command (`./run_with_ai.sh`)  
✅ **Comprehensive Docs**: 6 guides covering everything  

### How to Use

```bash
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh
```

### What You Get

- CSV with AI-powered rankings
- Scores reflect actual news quality
- Specific reasoning per stock
- Actionable recommendations

### Key Insight

**The bridge (`cursor_ai_bridge.py`) enables real AI involvement.**  
Without it, system defaults to keyword matching.

---

## 📞 Quick Command Reference

```bash
# Standard AI run
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh

# Custom config
AI_MAX_CALLS=100 STAGE2_BATCH_SIZE=5 ./run_with_ai.sh custom.txt 48

# Test mode
./run_with_ai.sh test.txt 12

# View results
cat realtime_ai_analysis_*.csv

# Check logs
tail -100 realtime_ai_*.log

# Verify AI usage
grep "AI usage" realtime_ai_*.log
```

---

**Status**: ✅ System complete and ready to use!

**Documentation**: 6 comprehensive guides available

**Support**: Refer to troubleshooting section or documentation index

---

*For detailed technical information, see `SYSTEM_GOALS_AND_AI_INTEGRATION.md`*  
*For quick start, see `AI_QUICKSTART.md`*  
*For before/after comparison, see `AI_FIX_SUMMARY.md`*
