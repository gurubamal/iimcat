#!/bin/bash
# Run AI analysis WITHOUT API keys using CLI bridges (codex or claude)
# Supports: codex (heuristic - free), claude (Claude CLI - requires login)
# Optional: Enhanced ranking with technical analysis (swing screener integration)

set -e

# Parse provider argument (default to codex)
PROVIDER="${1:-codex}"
TICKERS_FILE="${2:-all.txt}"
HOURS_BACK="${3:-48}"
MAX_ARTICLES="${4:-10}"
ENABLE_TECH_SCORING="${5:-0}"  # Optional 5th argument for technical scoring

# Normalize provider name
PROVIDER=$(echo "$PROVIDER" | tr '[:upper:]' '[:lower:]')

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🆓 Running AI Analysis WITHOUT API Keys"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Configure based on provider
if [ "$PROVIDER" = "claude" ]; then
    echo "Method: Claude CLI Bridge"
    echo "Cost: FREE with Claude subscription"
    echo "Speed: ~5s per analysis"
    echo "Accuracy: ~90%+ (best for final rankings)"
    echo ""

    # Check if claude CLI is available
    if ! command -v claude &> /dev/null; then
        echo "❌ ERROR: 'claude' CLI not found!"
        echo ""
        echo "Please install Claude Code:"
        echo "  npm install -g @anthropic-ai/claude-code"
        echo ""
        echo "Or set up authentication:"
        echo "  claude setup-token"
        exit 1
    fi

    # Set up Claude CLI bridge
    export CLAUDE_SHELL_CMD="python3 claude_cli_bridge.py"
    export AI_PROVIDER=claude
    PROVIDER_DISPLAY="Claude CLI Bridge"

elif [ "$PROVIDER" = "gemini" ]; then
    echo "Method: Gemini Agent Bridge"
    echo "Cost: FREE"
    echo "Speed: ~5s per analysis"
    echo "Accuracy: ~80% (dependent on search results)"
    echo ""

    # Set up gemini agent bridge
    export GEMINI_SHELL_CMD="python3 gemini_agent_bridge.py"
    export AI_PROVIDER=gemini
    PROVIDER_DISPLAY="Gemini Agent Bridge"

elif [ "$PROVIDER" = "codex" ]; then
    echo "Method: Codex Bridge (Calibrated Heuristic)"
    echo "Cost: FREE"
    echo "Speed: Instant"
    echo "Accuracy: High on credible sources (v2 heuristic)"
    echo ""

    # Set up codex bridge (uses heuristic, no API needed)
    export CODEX_SHELL_CMD="python3 codex_bridge.py"
    export AI_PROVIDER=codex
    PROVIDER_DISPLAY="Codex Bridge (Calibrated Heuristic)"

else
    echo "❌ ERROR: Unknown provider '$PROVIDER'"
    echo ""
    echo "Usage: $0 <provider> [tickers_file] [hours_back] [max_articles] [enable_tech]"
    echo ""
    echo "Providers:"
    echo "  codex  - Heuristic analysis (free, instant, ~60% accuracy)"
    echo "  claude - Claude CLI analysis (requires Claude subscription, ~90%+ accuracy)"
    echo "  gemini - Gemini analysis using Google Search (free, ~80% accuracy)"
    echo ""
    echo "Examples:"
    echo "  $0 codex all.txt 48 10        # AI-only ranking (news sentiment)"
    echo "  $0 claude all.txt 48 10 1     # Hybrid ranking (AI + Technical)"
    echo "  $0 claude nifty50.txt 24 5"
    echo "  $0 gemini nifty50.txt 24 5"
    echo ""
    echo "Technical Scoring (5th argument = 1):"
    echo "  Enables hybrid ranking: 60% AI News + 40% Technical Setup"
    echo "  Uses swing screener: RSI, Bollinger Bands, ATR, Volume, Momentum"
    echo "  Best for: Combining news catalysts with optimal entry timing"
    exit 1
fi

echo "Configuration:"
echo "  Provider: $PROVIDER_DISPLAY"
echo "  Tickers: $TICKERS_FILE"
echo "  Hours: $HOURS_BACK"
echo "  Max Articles: $MAX_ARTICLES"
echo "  Ticker Validation: DISABLED (all tickers will be processed)"
echo "  Popularity/Ad Filter: ENABLED (tunable via AD_POPULARITY_ENABLED/AD_STRICT_REJECT)"

# Technical scoring display
if [ "$ENABLE_TECH_SCORING" = "1" ]; then
    echo "  Technical Scoring: ✅ ENABLED (hybrid ranking: 60% AI + 40% Technical)"
    echo "    └─ Indicators: RSI, Bollinger Bands, ATR, Volume, Momentum"
    echo "    └─ Quality Filters: Volume ≥300k, Price ≥₹20, Data ≥50 bars"
    echo "    └─ Tiers: Tier1 ≥25pts, Tier2 ≥15pts, Watch <15pts"
else
    echo "  Technical Scoring: ⬜ DISABLED (AI-only ranking)"
    echo "    └─ Enable with: $0 $PROVIDER $TICKERS_FILE $HOURS_BACK $MAX_ARTICLES 1"
fi

echo ""
echo "Starting analysis..."
echo "  Tip: export MIN_CERTAINTY_THRESHOLD=35 to widen candidates (optional)"
echo ""

# Enforce strict real-time grounding for all providers to avoid reliance on training data
export AI_STRICT_CONTEXT=1
export NEWS_STRICT_CONTEXT=1
export EXIT_STRICT_CONTEXT=1

# Enable technical scoring if requested (hybrid ranking with swing screener)
export ENABLE_TECHNICAL_SCORING="$ENABLE_TECH_SCORING"

# Run analysis (with ticker validation disabled for speed)
python3 realtime_ai_news_analyzer.py \
  --tickers-file "$TICKERS_FILE" \
  --hours-back "$HOURS_BACK" \
  --max-articles "$MAX_ARTICLES" \
  --ai-provider "$AI_PROVIDER" \
  --verify-internet \
  --probe-agent \
  --disable-ticker-validation

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Analysis Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Results: realtime_ai_results.csv (convenience copy; timestamped CSV also generated)"
echo ""
if [ "$PROVIDER" = "codex" ]; then
    echo "To try Claude CLI:"
    echo "  $0 claude $TICKERS_FILE $HOURS_BACK $MAX_ARTICLES"
    echo ""
    echo "Or use API mode (requires API key):"
    echo "  export ANTHROPIC_API_KEY='sk-ant-xxxxx'"
    echo "  ./run_with_claude.sh"
fi
