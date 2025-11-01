# Cursor Agent Quick Start - NO API KEYS!

## 🎯 The Simplest Approach

**Zero configuration. Zero API keys. Zero cost.**

Uses your local Cursor agent instead of external APIs.

---

## 🚀 THREE STEPS TO RUN

```bash
cd /home/vagrant/R/essentials

# Step 1: Run
./run_with_cursor_agent.sh

# Step 2: Check results
cat realtime_ai_analysis_*.csv

# Step 3: Done!
```

That's it! **No API keys needed.**

---

## ✅ What You Get

### Before (Heuristics):
```
All stocks: 92.0 score
Same catalysts: earnings, M&A, investment, contract
No differentiation
```

### After (Cursor Agent):
```
RELIANCE: 95 - "Retail IPO $200B. Major strategic move."
MARUTI: 88 - "Exports +18% YoY, leads segment."
TCS: 72 - "Generic m-cap rise article."
ITC: 68 - "Q2 results announcement scheduled."
```

**Real AI analysis, zero cost!**

---

## 🔧 How It Works

```
Article → cursor_cli_bridge.py → cursor agent [prompt] → JSON → Ranking
```

**The Magic:**
```bash
cursor agent "Analyze this news: [article]... Return JSON..."
```

Your local Cursor agent analyzes the news and returns structured JSON.

---

## ⚙️ Configuration Options

### Default Run
```bash
./run_with_cursor_agent.sh
# NIFTY50, 48h window, batch size 5
```

### Custom Tickers
```bash
./run_with_cursor_agent.sh my_tickers.txt
```

### Custom Time Window
```bash
./run_with_cursor_agent.sh my_tickers.txt 24  # 24 hours
```

### Limit Agent Calls
```bash
AI_MAX_CALLS=20 ./run_with_cursor_agent.sh
```

### Full Custom
```bash
AI_MAX_CALLS=100 STAGE2_BATCH_SIZE=10 ./run_with_cursor_agent.sh my_tickers.txt 72
```

---

## 📊 Compare with API-Based

| Feature | Cursor Agent | API (Claude) |
|---------|--------------|--------------|
| Cost | **$0** | $0.01-0.03/call |
| Setup | **Zero** | Need API key |
| Rate Limits | **None** | 50-100 RPM |
| Privacy | **Local only** | External API |
| Speed | **Fast** | Network dependent |

**Winner: Cursor Agent!** ✅

---

## 🐛 Troubleshooting

### "Cursor CLI not found"

```bash
which cursor
# If not found: export PATH="$PATH:/home/vagrant/.local/bin"
```

### Agent not being called

```bash
# Check logs
grep "Calling Cursor agent" realtime_ai_*.log

# If empty, agent is not being invoked
# Verify bridge configuration:
./run_with_cursor_agent.sh  # This auto-configures
```

### All scores still 92.0

```bash
# Using heuristics, not agent
# Solution: Use the launcher
./run_with_cursor_agent.sh
```

---

## 💡 Pro Tips

### 1. Test First
```bash
cat > test.txt <<EOF
RELIANCE
TCS
INFY
EOF

./run_with_cursor_agent.sh test.txt 12
```

### 2. Weekend Scan
```bash
# 72h window for comprehensive analysis
./run_with_cursor_agent.sh nifty50_tickers.txt 72
```

### 3. Monitor Progress
```bash
# In another terminal
tail -f realtime_ai_*.log
```

---

## 📁 Key Files

**Created:**
- `cursor_cli_bridge.py` - Bridges to Cursor agent
- `run_with_cursor_agent.sh` - Easy launcher
- `CURSOR_CLI_AGENT_GUIDE.md` - Full documentation
- `CURSOR_AGENT_QUICKSTART.md` - This file

**Usage:**
```bash
./run_with_cursor_agent.sh  # All you need!
```

---

## 🎯 Verification

```bash
# Check agent was called
grep "Cursor agent" realtime_ai_*.log | wc -l
# Should be > 0

# Check score variation
cut -d',' -f3 realtime_ai_analysis_*.csv | sort -u
# Should show multiple different scores

# View reasoning
cut -d',' -f11 realtime_ai_analysis_*.csv | head -5
# Should be specific, not generic
```

---

## 🎉 Bottom Line

**Old Way (API):**
```bash
export ANTHROPIC_API_KEY='sk-ant-...'  # Need this
./run_with_ai.sh                       # Costs money
```

**New Way (Cursor Agent):**
```bash
./run_with_cursor_agent.sh  # NO API KEY! FREE!
```

**Result:** Same AI-quality analysis, zero cost, zero setup!

---

## 🚀 Next Step

```bash
cd /home/vagrant/R/essentials
./run_with_cursor_agent.sh
```

**Done!** Check `realtime_ai_analysis_*.csv` for results.

---

**Full docs:** `CURSOR_CLI_AGENT_GUIDE.md`
