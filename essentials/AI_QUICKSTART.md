# AI-Powered Stock Analysis - Quick Start

## 🎯 What We're Doing

**Goal**: Use **real AI** (Claude) to analyze stock news and rank stocks based on news quality, not just keyword matching.

**The Problem We Fixed**: System was using pattern matching (heuristics) instead of actual AI.

**The Solution**: `cursor_ai_bridge.py` routes analysis to Claude API for genuine intelligence.

---

## 🚀 FASTEST WAY TO RUN

### Option 1: With Your Anthropic API Key (Best Results)

```bash
cd /home/vagrant/R/essentials

# Set your API key
export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'

# Run AI-powered analysis
./run_with_ai.sh

# Done! Check results:
ls -lt realtime_ai_analysis_*.csv | head -1
```

### Option 2: Without API Key (Enhanced Heuristics)

```bash
cd /home/vagrant/R/essentials

# Configure bridge (will use smart pattern matching)
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"

# Run analysis
./run_realtime_ai_scan.sh nifty50_tickers.txt 48 2999 codex
```

---

## 📋 What You Get

### With AI (Recommended):

```
1. RELIANCE - Score: 92/100
   Sentiment: BULLISH | Rec: STRONG BUY
   Catalysts: M&A, investment
   Reasoning: "Retail IPO valued at $200B by 2027. Strategic mega-deal with confirmed numbers."
   Certainty: 95%

2. MARUTI - Score: 88/100
   Sentiment: BULLISH | Rec: STRONG BUY
   Catalysts: export, expansion
   Reasoning: "Exports up 18% YoY, leads segment. Strong growth with specific metrics."
   Certainty: 90%

3. TCS - Score: 72/100
   Sentiment: BULLISH | Rec: BUY
   Catalysts: earnings
   Reasoning: "Generic m-cap rise article. Limited catalyst specificity."
   Certainty: 65%
```

**Notice**: Scores reflect actual news quality. AI understands context.

### Without AI (Fallback):

```
1. RELIANCE - Score: 92.0
   Catalysts: earnings, M&A, investment, contract
   Reasoning: "Detected 4 catalyst(s). Score: 100/100."

2. MARUTI - Score: 92.0
   Catalysts: earnings, M&A, investment, contract
   Reasoning: "Detected 4 catalyst(s). Score: 100/100."

3. TCS - Score: 92.0
   Catalysts: earnings, M&A, investment, contract
   Reasoning: "Detected 4 catalyst(s). Score: 100/100."
```

**Notice**: Everything scores the same. Just keyword matching.

---

## ⚙️ Key Configuration

### Variables You Can Tune:

```bash
# AI Provider (codex uses bridge, claude uses direct API)
export AI_PROVIDER=codex

# Shell bridge command
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"

# Your API key (for real AI)
export ANTHROPIC_API_KEY='sk-ant-...'

# Budget control (max AI API calls)
export AI_MAX_CALLS=60

# Batch size (stocks analyzed together)
export STAGE2_BATCH_SIZE=5

# Time window (hours of news to fetch)
HOURS_BACK=48
```

### Default Behavior:

```bash
./run_with_ai.sh
# Uses: nifty50_tickers.txt, 48h window, batch size 5, max 60 AI calls
```

### Custom Run:

```bash
./run_with_ai.sh my_tickers.txt 24
# Uses: my_tickers.txt, 24h window, rest defaults
```

---

## 📊 Understanding Results

### CSV Output (`realtime_ai_analysis_*.csv`)

```csv
rank,ticker,ai_score,sentiment,recommendation,catalysts,risks,certainty,articles_count,reasoning
1,RELIANCE,92.0,bullish,STRONG BUY,"M&A,investment",market_risk,95,2,"Retail IPO valued at $200B..."
2,MARUTI,88.0,bullish,STRONG BUY,"export,expansion",,90,2,"Exports up 18% YoY..."
```

**Key Columns:**
- `ai_score`: 0-100 (AI's assessment of news quality)
- `sentiment`: bullish/bearish/neutral
- `recommendation`: STRONG BUY, BUY, ACCUMULATE, HOLD, SELL
- `catalysts`: What's driving the stock
- `certainty`: 0-100% (how confident AI is)
- `reasoning`: AI's explanation

---

## 🎓 How It Works

### Two-Stage Process:

```
Stage 1: Heuristic Scan (Fast, Free)
├─ Fetches news for ALL tickers
├─ Basic pattern matching
└─ Identifies stocks WITH news

Stage 2: AI Analysis (Smart, Uses API)
├─ Takes ALL stocks with news
├─ Processes in batches of 5
├─ Claude analyzes each article
└─ Generates final rankings
```

### AI Bridge Flow:

```
Article → Prompt → cursor_ai_bridge.py → Claude API → JSON Response → Final Score
```

**What Claude Does:**
1. Reads full article content
2. Identifies catalysts (earnings, M&A, contracts, etc.)
3. Assesses magnitude (₹1000cr deal >> ₹10cr deal)
4. Evaluates certainty (specific numbers = high certainty)
5. Predicts price impact
6. Provides recommendation with reasoning

---

## 🔍 Verification

### Check If AI Is Being Used:

```bash
./run_with_ai.sh 2>&1 | grep -E "AI ENABLED|HEURISTICS"
```

**Good Output:**
```
✅ REAL AI ENABLED - Claude will analyze each article
```

**Bad Output:**
```
⚠️  HEURISTICS MODE - Enhanced pattern matching only
```

### Check Results Quality:

```bash
head -5 realtime_ai_analysis_*.csv
```

Look for:
- ✅ Different scores (not all the same)
- ✅ Specific reasoning
- ✅ Varied catalyst lists
- ✅ Meaningful certainty values

---

## 💡 Pro Tips

### 1. Start Small (Test)

```bash
# Create test file
cat > test.txt <<EOF
RELIANCE
TCS
INFY
EOF

# Quick test
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh test.txt 12
```

### 2. Budget Management

```bash
# Low budget (20 API calls)
AI_MAX_CALLS=20 ./run_with_ai.sh

# High budget (200 API calls for comprehensive analysis)
AI_MAX_CALLS=200 ./run_with_ai.sh
```

### 3. Custom Ticker Lists

```bash
# Focus on specific sectors
cat > fintech.txt <<EOF
HDFCBANK
ICICIBANK
SBIN
AXISBANK
KOTAKBANK
EOF

./run_with_ai.sh fintech.txt 48
```

### 4. Time Windows

```bash
# Intraday (12h)
./run_with_ai.sh nifty50_tickers.txt 12

# Weekend scan (72h)
./run_with_ai.sh nifty50_tickers.txt 72
```

---

## 📁 Output Files

After running, you'll have:

```bash
realtime_ai_analysis_20251026_153434.csv  # Final AI-ranked results ⭐
realtime_ai_20251026_153434.log            # Detailed log
realtime_ai_stage1_20251026_153434.csv     # Heuristic pre-filter
```

**The file you want**: `realtime_ai_analysis_*.csv`

### View Results:

```bash
# Top 10 picks
head -11 realtime_ai_analysis_*.csv

# Full view
cat realtime_ai_analysis_*.csv
```

---

## 🐛 Troubleshooting

### Problem: "No AI shell bridge configured"

**Solution:**
```bash
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"
./run_realtime_ai_scan.sh
```

Or just use: `./run_with_ai.sh`

### Problem: "anthropic library not installed"

**Solution:**
```bash
pip install anthropic
```

### Problem: All scores are the same (92.0)

**Cause**: Heuristics mode (no AI)

**Solution**: Set `ANTHROPIC_API_KEY` and use `./run_with_ai.sh`

### Problem: "API rate limit exceeded"

**Solution**: Reduce `AI_MAX_CALLS`
```bash
AI_MAX_CALLS=20 ./run_with_ai.sh
```

---

## ✅ Complete Example

```bash
#!/bin/bash
cd /home/vagrant/R/essentials

# 1. Set API key (get from https://console.anthropic.com/)
export ANTHROPIC_API_KEY='sk-ant-api03-your-actual-key-here'

# 2. Configure for quality analysis
export AI_MAX_CALLS=60          # Budget: 60 API calls
export STAGE2_BATCH_SIZE=5      # Process 5 stocks at a time
export HOURS_BACK=48            # 48-hour news window

# 3. Run analysis
./run_with_ai.sh nifty50_tickers.txt 48

# 4. View results
echo ""
echo "=== TOP 10 AI-RANKED STOCKS ==="
head -11 realtime_ai_analysis_*.csv | column -t -s,

# 5. Check log for details
echo ""
echo "=== ANALYSIS LOG ==="
tail -50 realtime_ai_*.log
```

---

## 🎯 Bottom Line

**What you're trying to achieve**: Use real AI to analyze stock news and rank stocks based on news quality, not just keyword matching.

**How to do it**:
```bash
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh
```

**Result**: CSV file with AI-powered rankings where scores reflect actual news significance.

**Key Files**:
- `cursor_ai_bridge.py` - Routes to Claude API
- `run_with_ai.sh` - Easy launcher
- `realtime_ai_analysis_*.csv` - Your results

**Next Step**: Run it and compare AI vs heuristic results to see the difference!
