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
    echo "AI Provider: Gemini Agent"
    echo "Cost: FREE"
    echo "Speed: ~5-8s per stock"
    echo "Accuracy: ~80%"
    echo ""
    AI_PROVIDER_DISPLAY="Gemini Agent"

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

# Run the exit intelligence analyzer
python3 exit_intelligence_analyzer.py \
  --tickers-file "$TICKERS_FILE" \
  --ai-provider "$PROVIDER" \
  --hours-back "$HOURS_BACK"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✅ EXIT ASSESSMENT COMPLETE!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📊 Check the output files:"
    echo "   • exit_assessment_immediate_*.txt - Stocks requiring immediate exit"
    echo "   • exit_assessment_hold_*.txt - Stocks safe to hold/monitor"
    echo "   • exit_assessment_detailed_*.csv - Full analysis report"
    echo ""

    if [ "$PROVIDER" = "codex" ]; then
        echo "💡 For higher accuracy on critical decisions:"
        echo "   $0 claude $TICKERS_FILE $HOURS_BACK"
        echo ""
    fi

    echo "📝 IMPORTANT NOTES:"
    echo "   • Review immediate exit recommendations carefully"
    echo "   • Consider setting stop losses for MONITOR stocks"
    echo "   • This is a decision support tool - use your judgment"
    echo "   • Assessment is based on available data and AI analysis"
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
