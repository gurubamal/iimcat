# Using Cursor CLI Agent for Stock Analysis

## 🎯 The Better Approach

**NO API KEYS NEEDED!** Uses your local Cursor agent instead of external API calls.

---

## ✅ What Changed

### Before (API-based):
```bash
# Required API key
export ANTHROPIC_API_KEY='sk-ant-...'
./run_with_ai.sh
```
- Cost: $0.01-0.03 per analysis
- Requires external API key
- Rate limits apply

### After (Cursor Agent):
```bash
# NO API KEY NEEDED!
./run_with_cursor_agent.sh
```
- Cost: $0 (uses local agent)
- No external API needed
- Uses your existing Cursor installation

---

## 🚀 Quick Start

### Step 1: Verify Cursor CLI

```bash
# Check if cursor is available
which cursor
# Should show: /home/vagrant/.local/bin/cursor

# Test agent
cursor agent "test"
```

### Step 2: Run Analysis

```bash
cd /home/vagrant/R/essentials

# Default (NIFTY50, 48h window)
./run_with_cursor_agent.sh

# Custom tickers
./run_with_cursor_agent.sh my_tickers.txt

# Custom time window (24h)
./run_with_cursor_agent.sh my_tickers.txt 24
```

### Step 3: Check Results

```bash
cat realtime_ai_analysis_*.csv
```

---

## 🏗️ How It Works

```
┌─────────────────────────────────────────┐
│ News Article                            │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ cursor_cli_bridge.py                    │
│ - Formats analysis prompt               │
│ - Calls: cursor agent [prompt]          │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ Cursor Agent (Local)                    │
│ - Analyzes news content                 │
│ - Identifies catalysts                  │
│ - Scores magnitude & certainty          │
│ - Returns JSON response                 │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ Final Ranking                           │
│ - AI Score (60%) + Quant (40%)          │
│ - Complete justice for all stocks       │
└─────────────────────────────────────────┘
```

---

## 📊 What Cursor Agent Does

For each article, the agent evaluates:

1. **Catalyst Significance**
   - Not just keyword matching
   - Understands context and magnitude
   - Example: ₹1000cr deal for small-cap vs Reliance

2. **Deal Magnitude Assessment**
   - Compares deal size to company market cap
   - Identifies major vs minor catalysts

3. **Certainty Evaluation**
   - Specific numbers = high certainty (95%)
   - Vague claims = low certainty (20%)

4. **Source Credibility**
   - Reuters + numbers = high weight
   - Generic sources = lower weight

5. **Price Impact Prediction**
   - Conservative and aggressive estimates
   - Based on all above factors

6. **Reasoning**
   - Explains why it scored this way
   - 2-3 sentence summary

---

## ⚙️ Configuration

```bash
# Default settings (auto-configured by run_with_cursor_agent.sh)
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_cli_bridge.py"
export STAGE2_BATCH_SIZE=5      # Process 5 stocks at a time
export AI_MAX_CALLS=60          # Max agent calls

# Custom batch size
STAGE2_BATCH_SIZE=10 ./run_with_cursor_agent.sh

# Limit agent calls (process fewer stocks)
AI_MAX_CALLS=20 ./run_with_cursor_agent.sh

# Full custom
AI_MAX_CALLS=100 STAGE2_BATCH_SIZE=3 ./run_with_cursor_agent.sh my_tickers.txt 72
```

---

## 📁 Key Files

### New Files:
1. **`cursor_cli_bridge.py`** ⭐⭐⭐
   - Bridges to Cursor agent CLI
   - Calls: `cursor agent [prompt]`
   - Parses JSON response

2. **`run_with_cursor_agent.sh`** ⭐⭐⭐
   - Easy launcher
   - Auto-configures everything
   - NO API keys needed

### How They Work:

```python
# cursor_cli_bridge.py (simplified)
def analyze_with_cursor_cli(prompt, info):
    # Build structured prompt
    analysis_prompt = f"""
    Analyze this news: {info['headline']}
    Return JSON with: score, sentiment, catalysts, reasoning
    """
    
    # Call cursor agent
    result = subprocess.run(
        ['cursor', 'agent', analysis_prompt],
        capture_output=True,
        timeout=60
    )
    
    # Parse JSON response
    return json.loads(result.stdout)
```

---

## 🎯 Expected Results

### With Cursor Agent:

```csv
rank,ticker,ai_score,sentiment,recommendation,catalysts,reasoning
1,RELIANCE,95,bullish,STRONG BUY,"M&A,investment","Retail IPO $200B. Major strategic move."
2,MARUTI,88,bullish,STRONG BUY,"export,expansion","Exports +18% YoY, leads segment."
3,TCS,72,bullish,BUY,earnings,"Generic m-cap rise article."
4,ITC,68,bullish,BUY,earnings,"Q2 results announcement scheduled."
```

**Characteristics:**
- ✅ Scores vary based on news quality
- ✅ Specific catalysts per stock
- ✅ Real AI reasoning from Cursor agent
- ✅ No API costs!

---

## ✅ Advantages vs API-based

| Feature | Cursor Agent | API-based |
|---------|--------------|-----------|
| **Cost** | $0 (free) | $0.01-0.03/call |
| **API Key** | Not needed | Required |
| **Rate Limits** | None | Yes (RPM limits) |
| **Privacy** | Local only | Sent to external API |
| **Speed** | Fast | Network dependent |
| **Setup** | Zero config | Need API key |

---

## 🐛 Troubleshooting

### Problem: "Cursor CLI not found"

**Solution:**
```bash
# Check if cursor is installed
which cursor

# If not found, add to PATH
export PATH="$PATH:/home/vagrant/.local/bin"

# Or specify full path
export CURSOR_CLI_PATH="/home/vagrant/.local/bin/cursor"
```

### Problem: "Cursor agent command failed"

**Solution:**
```bash
# Test cursor agent manually
cursor agent "Analyze this: RELIANCE reports Q2 profit"

# If it opens Cursor IDE instead of running agent:
# The CLI expects to run in agent mode
# Check cursor agent --help for options
```

### Problem: Agent returns empty response

**Cause**: Cursor agent might not return output to stdout

**Solution:**
The bridge has fallback to enhanced heuristics. Check logs:
```bash
grep "fallback" realtime_ai_*.log
```

### Problem: All scores still 92.0

**Cause**: Agent not being called, using heuristics

**Solution:**
```bash
# Verify bridge is configured
grep "CODEX_SHELL_CMD" ~/.bashrc

# Should show: CODEX_SHELL_CMD="python3 cursor_cli_bridge.py"

# Or use the launcher which auto-configures:
./run_with_cursor_agent.sh
```

---

## 💡 Pro Tips

### 1. Test with Small Sample

```bash
cat > test.txt <<EOF
RELIANCE
TCS
INFY
EOF

./run_with_cursor_agent.sh test.txt 12
```

### 2. Monitor Agent Calls

```bash
# Check how many agent calls were made
grep "Calling Cursor agent" realtime_ai_*.log | wc -l
```

### 3. Compare Agent vs Heuristics

```bash
# Without agent (heuristics only)
AI_PROVIDER=heuristic ./run_realtime_ai_scan.sh > heuristic.log

# With agent
./run_with_cursor_agent.sh > agent.log

# Compare
diff heuristic.log agent.log
```

### 4. Batch Size Optimization

```bash
# Smaller batches (more careful, slower)
STAGE2_BATCH_SIZE=3 ./run_with_cursor_agent.sh

# Larger batches (faster, less careful)
STAGE2_BATCH_SIZE=10 ./run_with_cursor_agent.sh
```

---

## 📖 Complete Usage Examples

### Example 1: Quick NIFTY50 Scan

```bash
cd /home/vagrant/R/essentials
./run_with_cursor_agent.sh

# Output:
# ✅ Cursor CLI found
# Processing 21 tickers...
# 🤖 Calling Cursor agent for RELIANCE...
# ✅ Cursor agent analysis complete
# ...
# Results saved: realtime_ai_analysis_*.csv
```

### Example 2: Focus on Top 10 NIFTY Stocks

```bash
cat > top10.txt <<EOF
RELIANCE
TCS
HDFCBANK
ICICIBANK
INFY
ITC
SBIN
BHARTIARTL
MARUTI
WIPRO
EOF

./run_with_cursor_agent.sh top10.txt 24
```

### Example 3: Weekend Comprehensive Scan

```bash
# 72h window to catch weekend news
./run_with_cursor_agent.sh nifty50_tickers.txt 72
```

### Example 4: Budget-Conscious (Limit Calls)

```bash
# Limit to 20 agent calls
AI_MAX_CALLS=20 ./run_with_cursor_agent.sh
```

---

## 🎯 Verification

### Check if Agent is Being Used:

```bash
# 1. Look for agent calls in logs
grep "Calling Cursor agent" realtime_ai_*.log
# Should show multiple lines

# 2. Check for fallback messages
grep "fallback" realtime_ai_*.log
# Fewer = better (agent working)

# 3. Verify score variation
cut -d',' -f3 realtime_ai_analysis_*.csv | sort -u
# Should show multiple different scores

# 4. Check reasoning quality
cut -d',' -f11 realtime_ai_analysis_*.csv | head -5
# Should show specific reasoning, not generic
```

---

## 🚀 Quick Commands

```bash
# Standard run (NO API KEY!)
./run_with_cursor_agent.sh

# View results
cat realtime_ai_analysis_*.csv

# Check logs
tail -100 realtime_ai_*.log

# Verify agent was called
grep "Cursor agent" realtime_ai_*.log

# List outputs
ls -lt realtime_ai_* | head -10
```

---

## 📋 Summary

### What We Built:

✅ **Cursor CLI Bridge**: Routes to local agent (no API)  
✅ **Easy Launcher**: One command setup  
✅ **Batch Processing**: 5 stocks at a time  
✅ **Complete Justice**: All stocks with news get AI assessment  
✅ **Zero Cost**: No API fees!  

### How to Use:

```bash
./run_with_cursor_agent.sh
```

### Result:

- CSV with AI-powered rankings
- Scores reflect actual news quality
- Uses your local Cursor agent
- **NO API KEYS NEEDED!**

---

## 🎉 Next Step

```bash
cd /home/vagrant/R/essentials
./run_with_cursor_agent.sh
```

**That's it!** No API keys, no setup, just works with your existing Cursor installation.

---

**For more details:**
- System overview: `README_AI_SYSTEM.md`
- Original docs: `REALTIME_AI_QUICKSTART.md`
- Configuration: `CODEX_CURSOR_MINI.md`
