#!/bin/bash
# EXIT ASSESSMENT SYSTEM - AI-Powered Exit/Sell Decision Analysis
# Similar interface to run_without_api.sh but for exit decisions

set -e

# Parse arguments
PROVIDER="${1:-codex}"
TICKERS_FILE="${2:-exit.check.txt}"
HOURS_BACK="${3:-72}"

# Normalize provider name
PROVIDER=$(echo "$PROVIDER" | tr '[:upper:]' '[:lower:]')

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚨 EXIT INTELLIGENCE ANALYZER"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Comprehensive Multi-Factor Exit Assessment System"
echo ""

# Validate tickers file
if [ ! -f "$TICKERS_FILE" ]; then
    echo "❌ ERROR: Tickers file not found: $TICKERS_FILE"
    echo ""
    echo "Please create $TICKERS_FILE with one ticker per line, e.g.:"
    echo "  RELIANCE"
    echo "  TCS"
    echo "  INFY"
    exit 1
fi

# Configure based on provider
if [ "$PROVIDER" = "claude" ]; then
    echo "AI Provider: Claude CLI (Best Accuracy)"
    echo "Cost: FREE with Claude subscription"
    echo "Speed: ~8-12s per stock"
    echo "Accuracy: ~95% (best for critical decisions)"
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

    AI_PROVIDER_DISPLAY="Claude CLI"

elif [ "$PROVIDER" = "gemini" ]; then
    echo "AI Provider: Gemini CLI"
    echo "Cost: FREE (with Google account)"
    echo "Speed: ~5-8s per stock"
    echo "Accuracy: ~85%"
    echo ""

    # Check if gemini CLI is available
    if ! command -v gemini &> /dev/null; then
        echo "❌ ERROR: 'gemini' CLI not found!"
        echo ""
        echo "Please install Gemini CLI:"
        echo "  npm install -g @google/gemini-cli"
        echo ""
        echo "Or set up authentication:"
        echo "  gemini auth"
        exit 1
    fi

    AI_PROVIDER_DISPLAY="Gemini CLI"

elif [ "$PROVIDER" = "codex" ]; then
    echo "AI Provider: Codex (Calibrated Heuristic + AI)"
    echo "Cost: FREE"
    echo "Speed: Fast (~3-5s per stock)"
    echo "Accuracy: High on technical + fundamental factors"
    echo ""
    AI_PROVIDER_DISPLAY="Codex Bridge"

elif [ "$PROVIDER" = "auto" ]; then
    echo "AI Provider: Auto (prefers Codex locally)"
    echo "Cost: FREE"
    echo "Speed: Fast (~3-5s per stock)"
    echo "Accuracy: Balanced (falls back to heuristics)"
    echo ""
    AI_PROVIDER_DISPLAY="Auto (Codex baseline)"
else
    echo "❌ ERROR: Unknown provider '$PROVIDER'"
    echo ""
    echo "Usage: $0 <provider> [tickers_file] [hours_back]"
    echo ""
    echo "Providers:"
    echo "  codex  - Fast heuristic + AI analysis (FREE, recommended)"
    echo "  claude - Claude CLI analysis (requires Claude subscription, best accuracy)"
    echo "  gemini - Gemini analysis (FREE, good accuracy)"
    echo "  auto   - Choose best available locally (defaults to codex)"
    echo ""
    echo "Examples:"
    echo "  $0 codex exit.check.txt 72"
    echo "  $0 claude exit.check.txt 48"
    echo "  $0 gemini my_portfolio.txt 96"
    echo "  $0 auto exit.check.txt 72"
    exit 1
fi

echo "Configuration:"
echo "  Provider: $AI_PROVIDER_DISPLAY"
echo "  Tickers File: $TICKERS_FILE"
echo "  News Window: $HOURS_BACK hours"
echo ""

# Count tickers (exclude comments and blank lines)
TICKER_COUNT=$(grep -Ecv '^(#|\s*$)' "$TICKERS_FILE" 2>/dev/null || echo "0")
echo "  Stocks to Assess: $TICKER_COUNT"
echo ""

echo "Assessment Factors:"
echo "  ✅ Technical breakdown detection (support breaks, bearish patterns)"
echo "  ✅ Volume and momentum analysis"
echo "  ✅ Fundamental risk assessment"
echo "  ✅ News sentiment analysis (if available)"
echo "  ✅ AI-powered comprehensive evaluation"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Starting exit assessment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Set environment for AI provider
export AI_PROVIDER="$PROVIDER"

# Enforce strict real-time grounding to avoid reliance on training data across providers
export AI_STRICT_CONTEXT=1
export EXIT_STRICT_CONTEXT=1
export NEWS_STRICT_CONTEXT=1

# Optional: apply feedback-based config update before running analysis
if [ -f "ai_feedback_simulation.json" ]; then
  echo "🛠️  Applying feedback-based EXIT AI calibration (top-3 simulation)..."
  python3 update_exit_ai_config.py || true
  export EXIT_AI_CONFIG="exit_ai_config.json"
  echo "   Using updated config: $EXIT_AI_CONFIG"
  echo ""
fi

# Default: enable live intraday feedback using yfinance (requires internet).
# Set EXIT_USE_INTRADAY=0 to disable.
EXIT_USE_INTRADAY="${EXIT_USE_INTRADAY:-1}"
if [ "$EXIT_USE_INTRADAY" = "1" ]; then
  echo "⏱️  Applying live intraday feedback (yfinance, top-3 from latest CSV)..."
  # Prefer using the tickers file's first 3 symbols for this run
  python3 intraday_feedback_updater.py \
    --tickers-file "$TICKERS_FILE" \
    --interval "${EXIT_INTRADAY_INTERVAL:-5m}" \
    --window "${EXIT_INTRADAY_WINDOW:-240}" || true
  export EXIT_AI_CONFIG="exit_ai_config.json"
  echo "   Using updated config: $EXIT_AI_CONFIG"
  echo ""
fi

# Run the REALTIME exit AI analyzer (same sharpness as buying predictions)
echo "🤖 Using REALTIME AI NEWS ANALYSIS for exit decisions..."
echo "   (Same sharp analysis as your buying predictions!)"
echo ""

python3 realtime_exit_ai_analyzer.py \
  --tickers-file "$TICKERS_FILE" \
  --ai-provider "$PROVIDER" \
  --hours-back "$HOURS_BACK" \
  --max-articles 10

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ REALTIME EXIT AI ANALYSIS COMPLETE!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 Output file created:"
    echo "   • realtime_exit_ai_results_*_${PROVIDER}.csv"
    echo ""
    echo "📋 CSV columns include:"
    echo "   • rank - Priority ranking by exit urgency"
    echo "   • exit_urgency_score - 0-100 (90+ = IMMEDIATE_EXIT)"
    echo "   • exit_recommendation - IMMEDIATE_EXIT / MONITOR / HOLD"
    echo "   • exit_catalysts - Specific reasons to exit"
    echo "   • hold_reasons - Reasons to continue holding"
    echo "   • risks_of_holding - Risks if position maintained"
    echo "   • certainty - Confidence in recommendation (0-100%)"
    echo "   • reasoning - Sharp AI analysis explaining decision"
    echo "   • expected_exit_price - AI surface price for exit"
    echo "   • stop_loss_price - AI/technical stop level"
    echo ""

    if [ "$PROVIDER" = "codex" ] || [ "$PROVIDER" = "auto" ]; then
        echo "💡 For MAXIMUM accuracy on critical exit decisions:"
        echo "   $0 claude $TICKERS_FILE $HOURS_BACK"
        echo ""
    fi

    echo "📝 SHARP EXIT ANALYSIS NOTES:"
    echo "   ✅ Same AI analysis quality as buying predictions"
    echo "   ✅ Real-time news analysis for exit signals"
    echo "   ✅ Detailed catalysts, risks, and reasoning"
    echo "   ✅ Certainty scores to gauge confidence"
    echo "   • Review IMMEDIATE_EXIT recommendations first"
    echo "   • MONITOR stocks warrant close watching"
    echo "   • This is intelligent decision support - apply your judgment"
    echo ""

    # Optional second pass: comprehensive exit intelligence (tech + AI) even without news
    echo "🧠 Running comprehensive EXIT INTELLIGENCE (tech+AI) for confirmation..."
    python3 exit_intelligence_analyzer.py \
      --tickers-file "$TICKERS_FILE" \
      --ai-provider "$PROVIDER" \
      --hours-back "$HOURS_BACK" \
      --quiet || true
    echo ""

else
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "❌ EXIT ASSESSMENT FAILED (Exit code: $EXIT_CODE)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Please check the error messages above."
    exit $EXIT_CODE
fi
