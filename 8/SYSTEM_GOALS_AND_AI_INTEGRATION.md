# System Goals and AI Integration

## 🎯 PRIMARY OBJECTIVE

Build a **real-time AI-powered stock analysis system** that:

1. **Fetches** latest Indian stock market news (NSE/BSE tickers)
2. **Analyzes** each article using **real AI** (Claude/GPT) - NOT just pattern matching
3. **Scores** stocks based on catalyst quality, magnitude, and certainty
4. **Ranks** stocks with "complete justice" - AI assessment of news quality
5. **Processes** ALL stocks with news in efficient batches

---

## 🚨 THE CRITICAL PROBLEM (NOW FIXED)

### Previous Issue:
```bash
# This was happening:
$ ./run_realtime_ai_scan.sh

⚠️  No AI shell bridge configured
Using heuristic analyzer for RELIANCE (no external AI configured).
```

**Result**: System defaulted to keyword pattern matching. No actual AI involved!

### Why This Matters:

| Heuristic (Pattern Matching) | Real AI (Claude/GPT) |
|------------------------------|----------------------|
| Keywords: "profit", "earnings" → Score 80 | Analyzes: "Q2 profit up 52%, capacity expanded" → Score 92 |
| Can't assess magnitude | Understands ₹1000cr deal >> ₹10cr deal |
| Treats all "M&A" equally | Distinguishes strategic acquisition vs minority stake |
| No context understanding | Reads full article, assesses credibility |
| Generic catalyst labels | Specific, nuanced analysis |

**The Fix**: `cursor_ai_bridge.py` - Routes prompts to Claude API for genuine AI analysis

---

## 🏗️ SYSTEM ARCHITECTURE

### Two-Stage Intelligence Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 1: Fast Heuristic Scan (FREE, NO API CALLS)              │
├─────────────────────────────────────────────────────────────────┤
│ Purpose: Quick pre-filter to identify stocks with ANY news     │
│                                                                 │
│ Input:  21 NIFTY50 tickers (or custom list)                    │
│ Process: Fetch news (12-48h window), basic pattern matching    │
│ Output: Shortlist of stocks WITH news                          │
│ Example: RELIANCE (2 articles), MARUTI (2 articles), TCS (1)  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ STAGE 2: Deep AI Analysis (USES API, REAL AI)                  │
├─────────────────────────────────────────────────────────────────┤
│ Purpose: Proper assessment with AI for final ranking           │
│                                                                 │
│ Input:  ALL stocks with news from Stage 1                      │
│ Process: Batch processing (5 stocks at a time)                 │
│         Each article → Claude AI → Detailed analysis           │
│ Output: Ranked CSV with AI scores & recommendations            │
│                                                                 │
│ What AI Does:                                                   │
│ ✅ Reads full article content                                   │
│ ✅ Assesses catalyst significance (not just keywords)           │
│ ✅ Evaluates deal magnitude vs company size                     │
│ ✅ Determines certainty based on specificity                    │
│ ✅ Predicts price impact                                        │
│ ✅ Provides reasoning and recommendation                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 KEY INNOVATION: AI Shell Bridge

### The Concept

Instead of hardcoding AI provider logic, we route prompts through a **shell bridge**:

```
[News Article] 
    ↓
[Analysis Prompt] 
    ↓
[Shell Bridge: cursor_ai_bridge.py]
    ↓
[Claude API / OpenAI API / Local LLM]
    ↓
[JSON Response with scores, catalysts, reasoning]
    ↓
[Final Ranking]
```

### Benefits

1. **Pluggable AI**: Switch between Claude, GPT-4, local LLMs without code changes
2. **Budget Control**: Cap API calls with `AI_MAX_CALLS`
3. **Graceful Fallback**: If API fails, uses enhanced heuristics
4. **Testable**: Analyze prompts separately from main pipeline

---

## 🎓 WHAT WE'RE ACHIEVING

### 1. **Real AI Involvement in Scoring**

```python
# OLD (Heuristic):
if "profit" in headline:
    score += 15
    catalysts.append("earnings")

# NEW (AI):
claude_analysis = """
This article reports Q2 PAT of ₹1,235 crores, up 52% YoY.
- Major catalyst: Strong earnings beat
- High certainty: Specific numbers provided
- Deal magnitude: Significant for mid-cap stock
- Expected move: 10-15% upside potential
Score: 88/100
"""
```

### 2. **Batch Processing for Efficiency**

```bash
# Process 5 stocks at a time (configurable)
STAGE2_BATCH_SIZE=5

# Example:
Batch 1: RELIANCE, MARUTI, TCS, ITC, WIPRO → Claude analyzes
Batch 2: INFY, HDFCBANK, SBIN, ... → Claude analyzes
...
```

This balances:
- **Speed**: Not analyzing serially (too slow)
- **Cost**: Not hitting API rate limits
- **Quality**: Each article gets proper AI assessment

### 3. **Complete Justice with Quant + AI**

```
Final Score = (AI Score × 0.6) + (Quant Score × 0.4)

Where:
- AI Score: Claude's assessment of news catalyst
- Quant Score: Technical indicators (ATR, volume, trend)
```

**Why This Matters:**

| Stock | News Quality | Quant Score | Final Rank |
|-------|--------------|-------------|------------|
| RELIANCE | Mega IPO announcement (AI: 95) | Uptrend (80) | **#1** |
| MARUTI | Minor export stat (AI: 65) | Downtrend (40) | #8 |
| TCS | Generic m-cap mention (AI: 70) | Sideways (60) | #5 |

AI ensures **news quality** determines ranking, not just keyword presence.

### 4. **ALL Stocks with News Get AI Assessment**

```bash
# Stage 1 finds: RELIANCE, MARUTI, TCS, ITC (4 stocks with news)
# Stage 2 processes: ALL 4 with AI (not just top 3)

📈 Selecting ALL tickers with news for Stage 2 (external AI)
🎯 Stage 2 targets (with news): RELIANCE MARUTI TCS ITC
```

**Complete Justice**: Every stock with news gets the same thorough AI analysis.

---

## 🚀 HOW TO USE

### Option A: Quick Start with AI (Recommended)

```bash
# 1. Set API key
export ANTHROPIC_API_KEY='sk-ant-api03-your-key-here'

# 2. Run with AI
./run_with_ai.sh

# That's it! System will:
# ✅ Fetch news for NIFTY50 (48h window)
# ✅ Use Claude AI to analyze each article
# ✅ Process in batches of 5
# ✅ Generate ranked CSV with AI scores
```

### Option B: Manual Configuration

```bash
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"
export ANTHROPIC_API_KEY='your-key'
export AI_MAX_CALLS=60              # Budget control
export STAGE2_BATCH_SIZE=5          # Batch size

./run_realtime_ai_scan.sh nifty50_tickers.txt 48 2999 codex
```

### Option C: Test with Small Sample

```bash
# Create test file with 5 tickers
cat > test_tickers.txt <<EOF
RELIANCE
TCS
INFY
MARUTI
ITC
EOF

# Run with AI
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh test_tickers.txt 24
```

---

## 📊 OUTPUT INTERPRETATION

### CSV Columns Explained

```csv
rank,ticker,ai_score,sentiment,recommendation,catalysts,risks,certainty,articles_count,reasoning
1,RELIANCE,92.0,bullish,STRONG BUY,"earnings,M&A,investment",market_risk,95,2,"Mega IPO valued at $200B. Strategic expansion."
```

| Column | Description | AI Impact |
|--------|-------------|-----------|
| `rank` | Final ranking (AI + Quant) | AI assesses news quality |
| `ai_score` | 0-100 score from AI | Claude's assessment |
| `sentiment` | bullish/bearish/neutral | AI interprets context |
| `recommendation` | STRONG BUY/BUY/HOLD/etc | AI's action suggestion |
| `catalysts` | earnings, M&A, contract, etc | AI identifies from content |
| `certainty` | 0-100% confidence | AI judges specificity |
| `reasoning` | Why this score? | AI explains its thinking |

### Score Ranges (AI-Powered)

- **90-100**: Major confirmed catalyst
  - Example: "Q2 PAT ₹4,235cr, up 52%, capacity doubled"
  - AI recognizes: Specific numbers + Strong growth + Expansion
  
- **75-89**: Strong catalyst with good certainty
  - Example: "Wins ₹800cr contract from Fortune 500 client"
  - AI recognizes: Significant deal + Credible source
  
- **60-74**: Moderate catalyst
  - Example: "Q2 results scheduled next week"
  - AI recognizes: Routine announcement, no specifics
  
- **40-59**: Weak or speculative
  - Example: "May consider fund raising in future"
  - AI recognizes: Vague, no commitment
  
- **0-39**: Negative or irrelevant
  - Example: "Company under regulatory investigation"
  - AI recognizes: Risk factor

---

## 🔧 CONFIGURATION TUNING

### For High-Quality Analysis (Expensive)

```bash
export AI_MAX_CALLS=200             # Analyze more stocks
export STAGE2_BATCH_SIZE=3          # Smaller batches, more careful
export HOURS_BACK=72                # Wider time window
```

### For Budget-Conscious (Cheaper)

```bash
export AI_MAX_CALLS=20              # Limit API usage
export STAGE2_BATCH_SIZE=10         # Larger batches, faster
export HOURS_BACK=12                # Narrower window
```

### For Testing (Fast)

```bash
export AI_MAX_CALLS=10
./run_with_ai.sh test_tickers.txt 12
```

---

## 📈 SUCCESS METRICS

### What Good Results Look Like

```
✅ AI Analysis Output:

1. RELIANCE - Score: 92/100
   Sentiment: BULLISH | Rec: STRONG BUY
   Catalysts: M&A, investment
   Reasoning: "Retail IPO valued at $200B by 2027. Strategic mega-deal."
   Certainty: 95% | Articles: 2

2. MARUTI - Score: 88/100
   Sentiment: BULLISH | Rec: STRONG BUY
   Catalysts: export, expansion
   Reasoning: "Exports up 18% YoY, leads segment. Strong growth trajectory."
   Certainty: 90% | Articles: 2
```

**Key Indicators:**
- ✅ Scores vary based on news quality (not all 92)
- ✅ Reasoning explains the score
- ✅ Catalysts are specific to the article
- ✅ Certainty reflects information specificity

### What Bad Results Look Like (Heuristics Only)

```
❌ Heuristic Output:

1. RELIANCE - Score: 92.0
   Catalysts: earnings, M&A, investment, contract
   Reasoning: "Detected 4 catalyst(s). Score: 100/100."

2. MARUTI - Score: 92.0
   Catalysts: earnings, M&A, investment, contract
   Reasoning: "Detected 4 catalyst(s). Score: 100/100."
```

**Problems:**
- ❌ All stocks get same score (92)
- ❌ Same generic catalysts for everyone
- ❌ No actual analysis of content
- ❌ No differentiation based on news quality

---

## 🎯 SUMMARY: WHAT WE'VE BUILT

### The Goal
A system that uses **real AI** (not just keywords) to:
1. Analyze Indian stock news as it's published
2. Score stocks based on catalyst quality and magnitude
3. Provide actionable buy/sell recommendations
4. Process efficiently in batches
5. Give every stock with news a fair AI assessment

### The Solution
- **`cursor_ai_bridge.py`**: Routes analysis to Claude API
- **`run_with_ai.sh`**: Easy launcher with proper AI config
- **Two-stage pipeline**: Fast heuristic pre-filter + Deep AI analysis
- **Batch processing**: 5 stocks at a time for efficiency
- **Budget controls**: Cap API calls to manage costs

### The Outcome
```bash
# Run this to get AI-powered stock analysis:
export ANTHROPIC_API_KEY='your-key'
./run_with_ai.sh

# Output: CSV ranked by AI assessment of news quality
# Each stock gets proper analysis, not just keyword matching
# Complete justice for all stocks with news
```

---

## 📝 QUICK REFERENCE

```bash
# With AI (Real analysis)
export ANTHROPIC_API_KEY='sk-ant-...'
./run_with_ai.sh

# Without AI (Heuristics fallback)
./run_realtime_ai_scan.sh

# Custom configuration
export AI_MAX_CALLS=60
export STAGE2_BATCH_SIZE=5
./run_with_ai.sh nifty50_tickers.txt 48

# Test mode
./run_with_ai.sh test_tickers.txt 12
```

**Files Generated:**
- `realtime_ai_analysis_*.csv` - Final AI-ranked results ← **This is what you want**
- `realtime_ai_*.log` - Detailed analysis log
- `realtime_ai_stage1_*.csv` - Initial heuristic filter

**Key Insight**: AI involvement happens in Stage 2, giving proper assessment to final rankings. The bridge (`cursor_ai_bridge.py`) is what enables real AI analysis instead of just pattern matching.
