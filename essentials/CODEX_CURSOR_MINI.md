Codex + Cursor: AI-Powered Analysis

## REAL AI Analysis (RECOMMENDED)

Uses Claude via Anthropic API for genuine AI-powered news analysis.

### Quick Start with AI

```bash
# Set your API key
export ANTHROPIC_API_KEY='sk-ant-...'

# Run with AI (processes ALL stocks with news in batches of 5)
./run_with_ai.sh
```

### Manual Configuration

```bash
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"
export ANTHROPIC_API_KEY='your-key'
export AI_MAX_CALLS=60
export STAGE2_BATCH_SIZE=5

./run_realtime_ai_scan.sh nifty50_tickers.txt 48 2999 codex
```

## Fallback Options

### Enhanced Heuristics (No API Key)
```bash
# Uses intelligent pattern matching (no AI)
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"
# Don't set ANTHROPIC_API_KEY

./run_realtime_ai_scan.sh top10_nifty.txt 12 2999 codex
```

### OpenAI/Codex (Alternative AI)
```bash
export OPENAI_API_KEY='sk-...'
./run_realtime_ai_scan.sh top10_nifty.txt 12 2999 codex
```

## Key Features

✅ **Real AI Analysis**: Claude analyzes each article for:
   - Catalyst detection (earnings, M&A, contracts, expansion)
   - Deal magnitude assessment
   - Sentiment analysis (bullish/bearish/neutral)
   - Certainty scoring (based on specificity)
   - Price impact prediction
   
✅ **Batch Processing**: Analyzes 5 stocks at a time for efficiency

✅ **Complete Justice**: ALL stocks with news get AI assessment

✅ **Budget Control**: `AI_MAX_CALLS` caps API usage

## Configuration Variables

- `AI_PROVIDER`: `codex` (uses bridge), `claude` (direct), `heuristic` (no AI)
- `CODEX_SHELL_CMD`: Bridge script (`python3 cursor_ai_bridge.py`)
- `ANTHROPIC_API_KEY`: Your Claude API key
- `AI_MAX_CALLS`: Max AI calls (default: 60)
- `STAGE2_BATCH_SIZE`: Stocks per batch (default: 5)
- `HOURS_BACK`: News window in hours (default: 48)

## Output Files

- `realtime_ai_analysis_*.csv` - Final ranked results with AI scores
- `realtime_ai_*.log` - Detailed analysis log
- `realtime_ai_stage1_*.csv` - Heuristic pre-filter results

## Scoring System

**AI-Powered (with API key):**
- 90-100: Major confirmed catalyst (specific numbers, big deals)
- 75-89: Strong catalyst with good certainty
- 60-74: Moderate catalyst (routine announcements)
- 40-59: Weak catalyst or speculation
- 0-39: Negative news

**Heuristics (no API key):**
- Pattern matching based on keywords
- Less nuanced than AI analysis
- Good for initial screening

## Example: Full AI Analysis

```bash
# Analyze NIFTY50, 48h window, with real AI
export ANTHROPIC_API_KEY='your-key'

./run_with_ai.sh nifty50_tickers.txt 48

# Output shows:
# - AI scores (not just keyword matching)
# - Proper sentiment analysis
# - Catalyst identification
# - Risk assessment
# - Recommendation (STRONG BUY, BUY, etc.)
```

## Notes

- AI bridge (`cursor_ai_bridge.py`) automatically falls back to enhanced heuristics if no API key
- `VERIFY_AGENT_INTERNET=1` not needed for Claude API (only for shell-based bridges)
- 4th arg selects AI: `auto|heuristic|codex|claude|cursor`
