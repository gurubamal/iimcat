# Quick Start: Claude CLI Integration

## 🚀 Usage (Same as Codex!)

```bash
# Use Claude CLI (95% accuracy, best for final rankings)
./run_without_api.sh claude all.txt 48 10

# Use Codex (60% accuracy, instant, good for screening)
./run_without_api.sh codex all.txt 48 10
```

## ✅ Verify Installation

```bash
# Test Claude CLI bridge
./test_claude_cli_bridge.sh

# Check Claude is available
claude --help
```

## 📊 Comparison

| Mode | Speed | Accuracy | Cost | Best For |
|------|-------|----------|------|----------|
| **codex** | Instant | ~60% | $0 | Fast screening |
| **claude** | ~5s/stock | ~95% | $0* | Final rankings |

\* Requires Claude subscription (no API key needed)

## 🎯 Recommended Workflow

### Two-Stage Analysis

```bash
# Stage 1: Fast screening with Codex
./run_without_api.sh codex all.txt 48 10
# Result: 500 stocks → Top 50

# Stage 2: Deep analysis with Claude
# (Extract top 50 tickers from stage 1 output)
./run_without_api.sh claude top50_tickers.txt 48 10
# Result: 50 stocks → Top 10 picks
```

### Single-Stage (Claude Only)

```bash
# Best accuracy, slower
./run_without_api.sh claude all.txt 48 10
```

## 🔧 Advanced Options

### Change Claude Model

```bash
export CLAUDE_CLI_MODEL="sonnet"  # Fast (default)
export CLAUDE_CLI_MODEL="opus"    # Best quality
./run_without_api.sh claude all.txt 48 10
```

### Custom Timeout

```bash
export CLAUDE_CLI_TIMEOUT="180"
./run_without_api.sh claude all.txt 48 10
```

## 📝 Examples

### Weekend Analysis

```bash
# 48-hour window for weekend scan
./run_without_api.sh claude all.txt 48 10
```

### Quick Test (Single Stock)

```bash
echo "RELIANCE" > test.txt
./run_without_api.sh claude test.txt 24 3
```

### Top 50 Stocks

```bash
./run_without_api.sh claude nifty50.txt 24 5
```

## 🐛 Troubleshooting

### Claude CLI not found?

```bash
# Check installation
which claude

# Set up authentication
claude setup-token
```

### Integration issues?

```bash
# Run diagnostics
./test_claude_cli_bridge.sh
```

## 📚 Full Documentation

See `CLAUDE_CLI_INTEGRATION.md` for complete details.

---

**🎉 You're all set!** Just run:

```bash
./run_without_api.sh claude all.txt 48 10
```
