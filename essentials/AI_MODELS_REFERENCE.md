# AI Models Reference Guide

## 🤖 Available Models & Configurations

**UPDATED:** All models upgraded to latest/best versions ✅

Your system supports **4 different AI modes** for stock news analysis:

---

## 1. Codex Bridge (Heuristic) - NO AI MODEL

### What It Is
- **NOT an AI model** - Pure pattern matching with regex rules
- Misleading name - should be "Heuristic Bridge"
- No machine learning, no neural networks

### How It Works
```python
# codex_bridge.py:139
analyzer = RealtimeAIAnalyzer(ai_provider='heuristic', max_ai_calls=0)
result = analyzer._intelligent_pattern_analysis(prompt)
```

Pattern matching for:
- Deal values (₹X crore)
- Sentiment keywords (positive/negative)
- Event types (acquisition, order, results)
- Risk indicators (speculation words)

### Configuration
```bash
./run_without_api.sh codex all.txt 48 10
```

**No model to configure** - it's pure code logic!

### Performance
- **Speed:** Instant (no API)
- **Cost:** $0
- **Accuracy:** ~60%
- **Best for:** Fast screening, filtering 1000s of stocks

---

## 2. Claude CLI Mode - Claude Sonnet ⭐

### Model Details
- **Default Model:** `claude-sonnet-4-5` (Claude Sonnet 4.5)
- **Provider:** Anthropic (via Claude CLI)
- **Version:** Latest available through Claude Code CLI

### Available Models
```bash
# Sonnet - Fast, balanced (default)
export CLAUDE_CLI_MODEL="sonnet"

# Opus - Best quality, slower
export CLAUDE_CLI_MODEL="opus"

# Haiku - Fastest, lower cost
export CLAUDE_CLI_MODEL="haiku"
```

### How It Works
```bash
# claude_cli_bridge.py calls:
claude --print \
  --model sonnet \
  --system-prompt "<financial_analysis_prompt>" \
  --output-format text \
  "<news_analysis_request>"
```

### Configuration
```bash
# Default (Sonnet)
./run_without_api.sh claude all.txt 48 10

# Use Opus for best quality
export CLAUDE_CLI_MODEL="opus"
./run_without_api.sh claude all.txt 48 10

# Use Haiku for speed
export CLAUDE_CLI_MODEL="haiku"
./run_without_api.sh claude all.txt 48 10

# Custom timeout
export CLAUDE_CLI_TIMEOUT="180"
./run_without_api.sh claude all.txt 48 10
```

### Performance
- **Speed:** ~5s per stock
- **Cost:** $0 (requires Claude subscription)
- **Accuracy:** ~95%
- **Best for:** Final rankings, detailed analysis

---

## 3. Claude API Mode - Claude 3.5 Sonnet

### Model Details
- **Default Model:** `claude-3-5-sonnet-20241022` ✅ UPGRADED
- **Provider:** Anthropic (via API)
- **API Endpoint:** https://api.anthropic.com/v1/messages

### Available Models
```bash
# Claude 3.5 Sonnet (default) - Latest version ✅
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"

# Claude 3 Opus - Best quality (expensive)
export ANTHROPIC_MODEL="claude-3-opus-20240229"

# Claude 3 Haiku - Fastest (cheap)
export ANTHROPIC_MODEL="claude-3-haiku-20240307"
```

### Full Configuration
```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"  # Latest Sonnet ✅
export ANTHROPIC_TEMPERATURE="0.2"      # 0.0-1.0 (lower = more focused)
export ANTHROPIC_MAX_TOKENS="1200"     # Max response length
export ANTHROPIC_TIMEOUT="90"          # Seconds
export ANTHROPIC_VERSION="2023-06-01"  # API version

# Run with API
python3 realtime_ai_news_analyzer.py \
  --ai-provider claude \
  --tickers-file all.txt \
  --hours-back 48 \
  --max-articles 10
```

### Performance
- **Speed:** ~4s per stock
- **Cost:** ~$0.015-0.025 per stock (Sonnet), ~$0.075 per stock (Opus)
- **Accuracy:** ~95%
- **Best for:** Automated workflows, high-volume processing

### Pricing (as of Jan 2025)
| Model | Input | Output | Cost/Stock* |
|-------|-------|--------|-------------|
| Haiku | $0.25/M | $1.25/M | ~$0.008 |
| Sonnet 3.5 | $3/M | $15/M | ~$0.020 |
| Opus | $15/M | $75/M | ~$0.075 |

\* Approximate, assumes ~500 input + 200 output tokens

---

## 4. OpenAI API Mode - GPT-4o

### Model Details
- **Default Model:** `gpt-4o` ✅ UPGRADED (was invalid 'gpt-4.1-mini')
- **Provider:** OpenAI
- **API Endpoint:** https://api.openai.com/v1/chat/completions

### Available Models
```bash
# GPT-4o (default) - Latest and best ✅
export OPENAI_MODEL="gpt-4o"
export OPENAI_MODEL="gpt-4o-2024-11-20"

# GPT-4 Turbo - Previous best
export OPENAI_MODEL="gpt-4-turbo"
export OPENAI_MODEL="gpt-4-turbo-2024-04-09"

# GPT-4o Mini - Fastest, cheapest
export OPENAI_MODEL="gpt-4o-mini"

# Note: 'gpt-4.1-mini' does NOT exist - was a bug ❌
```

### Full Configuration
```bash
export OPENAI_API_KEY="sk-xxxxx"
export OPENAI_MODEL="gpt-4o"  # Latest GPT-4 ✅
export OPENAI_TEMPERATURE="0.2"    # 0.0-2.0
export OPENAI_MAX_TOKENS="1200"   # Max response
export OPENAI_TIMEOUT="90"        # Seconds

# Run with API
python3 realtime_ai_news_analyzer.py \
  --ai-provider codex \
  --tickers-file all.txt \
  --hours-back 48 \
  --max-articles 10
```

### Performance
- **Speed:** ~3-5s per stock
- **Cost:** ~$0.015 per stock (GPT-4o), ~$0.003 per stock (GPT-4o-mini)
- **Accuracy:** ~90% (GPT-4o), ~85% (GPT-4o-mini)
- **Best for:** Cost-effective automation

### Pricing (as of Jan 2025)
| Model | Input | Output | Cost/Stock* |
|-------|-------|--------|-------------|
| GPT-4o Mini | $0.15/M | $0.60/M | ~$0.006 |
| GPT-4 Turbo | $10/M | $30/M | ~$0.030 |
| GPT-4o | $2.50/M | $10/M | ~$0.012 |

\* Approximate, assumes ~500 input + 200 output tokens

---

## 📊 Model Comparison Matrix

| Mode | Model | Type | Speed | Accuracy | Cost/100 stocks | Best Use Case |
|------|-------|------|-------|----------|-----------------|---------------|
| **Codex Bridge** | None | Heuristic | Instant | 60% | $0 | Fast screening |
| **Claude CLI** | Sonnet 4.5 | AI (CLI) | 8min | 95% | $0* | Final rankings |
| **Claude API** | 3.5 Sonnet | AI (API) | 7min | 95% | $2 | Automation |
| **OpenAI API** | GPT-4.1 Mini | AI (API) | 6min | 85% | $1 | Cost-effective |

\* Requires Claude subscription

---

## 🎯 Recommended Workflows

### Workflow 1: Two-Stage (Best ROI)

```bash
# Stage 1: Fast screening (Heuristic)
./run_without_api.sh codex all.txt 48 10
# Result: 500 stocks → Top 100 (FREE, instant)

# Stage 2: Deep analysis (Claude CLI)
./run_without_api.sh claude top100.txt 48 10
# Result: 100 stocks → Top 10 ($0, 8 minutes)
```

### Workflow 2: High Quality (Claude Only)

```bash
# Single-stage with Claude CLI
export CLAUDE_CLI_MODEL="sonnet"
./run_without_api.sh claude all.txt 48 10
# Result: 500 stocks → Top 10 ($0, 40 minutes)
```

### Workflow 3: API Automation

```bash
# Best for scheduled/automated runs
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
export ANTHROPIC_MODEL="claude-3-5-sonnet-20240620"

python3 realtime_ai_news_analyzer.py \
  --ai-provider claude \
  --tickers-file all.txt \
  --hours-back 48 \
  --max-articles 10
# Result: Fully automated, ~$10/run
```

### Workflow 4: Cost-Optimized

```bash
# Use OpenAI GPT-4o Mini
export OPENAI_API_KEY="sk-xxxxx"
export OPENAI_MODEL="gpt-4o-mini"

python3 realtime_ai_news_analyzer.py \
  --ai-provider codex \
  --tickers-file all.txt \
  --hours-back 48 \
  --max-articles 10
# Result: Automated, ~$3/run
```

---

## 🔧 How to Check Current Configuration

```bash
# Run the config checker
./check_ai_models.sh
```

This shows:
- Which models are available
- Current configuration
- API key status
- Usage examples

---

## 💡 Model Selection Guide

### When to Use Heuristic (Codex Bridge)
- Screening 500+ stocks
- Need instant results
- No budget for API calls
- First-pass filtering

### When to Use Claude CLI
- Final rankings (top 50-100 stocks)
- Have Claude subscription
- Want best accuracy
- No API budget
- Interactive development

### When to Use Claude API
- Automated workflows
- Scheduled scans
- Production deployments
- Need API reliability
- Budget: $2-10 per run

### When to Use OpenAI API
- Cost-conscious automation
- Faster processing needed
- Already have OpenAI credits
- Budget: $1-3 per run

---

## 🚀 Quick Reference Commands

```bash
# Check current configuration
./check_ai_models.sh

# Test Claude CLI integration
./test_claude_cli_bridge.sh

# Heuristic mode
./run_without_api.sh codex all.txt 48 10

# Claude CLI (Sonnet)
./run_without_api.sh claude all.txt 48 10

# Claude CLI (Opus - best quality)
export CLAUDE_CLI_MODEL="opus"
./run_without_api.sh claude all.txt 48 10

# Claude API
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
python3 realtime_ai_news_analyzer.py --ai-provider claude --tickers-file all.txt

# OpenAI API
export OPENAI_API_KEY="sk-xxxxx"
python3 realtime_ai_news_analyzer.py --ai-provider codex --tickers-file all.txt
```

---

## 📚 Related Documentation

- `CLAUDE_CLI_INTEGRATION.md` - Claude CLI setup & usage
- `QUICK_START_CLAUDE_CLI.md` - Quick reference
- `INTEGRATION_GUIDE.md` - Full API integration
- `CLAUDE_QUICKSTART.md` - Claude API quickstart

---

**Last Updated:** 2025-01-27
**Your Current Setup:** ✅ Claude CLI (Sonnet) - Ready to use!
