#!/bin/bash
# Run AI analysis with different providers
# Usage: ./run_without_api_fixed.sh [claude|codex|cursor|heuristic]

set -e

PROVIDER="${1:-codex}"  # Default to codex if not specified
TICKERS_FILE="${2:-all.txt}"
HOURS_BACK="${3:-48}"
MAX_ARTICLES="${4:-10}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 AI Analysis Provider Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

case "$PROVIDER" in
  claude)
    echo "Provider: Claude (Anthropic)"
    echo ""

    # Check if API key is set
    if [ -n "$ANTHROPIC_API_KEY" ]; then
      echo "✅ ANTHROPIC_API_KEY is set"
      echo "   Using: Claude API (93% accuracy, costs apply)"
      AI_PROVIDER="claude"
    else
      echo "❌ ANTHROPIC_API_KEY not set"
      echo ""
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo "⚠️  IMPORTANT: There is NO 'Claude CLI'"
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo ""
      echo "Anthropic does NOT provide a CLI tool like 'codex' or 'cursor'."
      echo ""
      echo "Your options to use Claude:"
      echo ""
      echo "1. Set API key (costs ~\$5-22 per 1000 stocks):"
      echo "   export ANTHROPIC_API_KEY='sk-ant-api03-xxxxx'"
      echo "   ./run_without_api_fixed.sh claude"
      echo ""
      echo "2. Use Cursor (if you have Cursor Pro with Claude):"
      echo "   ./run_without_api_fixed.sh cursor"
      echo ""
      echo "3. Use FREE heuristic instead (60% accuracy):"
      echo "   ./run_without_api_fixed.sh codex"
      echo ""
      echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
      echo ""
      echo "Falling back to heuristic (free, instant, 60% accuracy)..."
      echo ""
      export CODEX_SHELL_CMD="python3 codex_bridge.py"
      AI_PROVIDER="codex"
    fi
    ;;

  codex)
    echo "Provider: Codex Bridge (Heuristic)"
    echo "   Using: Pattern-based analysis (FREE, instant, 60% accuracy)"
    export CODEX_SHELL_CMD="python3 codex_bridge.py"
    AI_PROVIDER="codex"
    ;;

  cursor)
    echo "Provider: Cursor CLI"
    echo ""

    # Check if cursor is installed
    if command -v cursor &> /dev/null; then
      echo "✅ Cursor CLI found: $(which cursor)"
      echo "   Using: Cursor's built-in AI (may use Claude)"
      echo "   Note: May require Cursor Pro subscription"
      export CURSOR_SHELL_CMD="python3 cursor_cli_bridge.py"
      AI_PROVIDER="cursor"
    else
      echo "❌ Cursor CLI not found"
      echo "   Install from: https://cursor.sh"
      echo ""
      echo "Falling back to heuristic (free, instant)..."
      export CODEX_SHELL_CMD="python3 codex_bridge.py"
      AI_PROVIDER="codex"
    fi
    ;;

  heuristic)
    echo "Provider: Heuristic (Built-in)"
    echo "   Using: Pattern matching (FREE, instant, 60% accuracy)"
    AI_PROVIDER="heuristic"
    ;;

  *)
    echo "❌ Unknown provider: $PROVIDER"
    echo ""
    echo "Valid providers:"
    echo "  claude     - Claude API (requires ANTHROPIC_API_KEY)"
    echo "  codex      - Heuristic bridge (FREE, no API key)"
    echo "  cursor     - Cursor CLI (requires Cursor installation)"
    echo "  heuristic  - Direct heuristic (FREE, simplest)"
    echo ""
    echo "Example:"
    echo "  ./run_without_api_fixed.sh codex"
    echo "  ./run_without_api_fixed.sh claude  # (needs API key)"
    exit 1
    ;;
esac

echo ""
echo "Configuration:"
echo "  Tickers: $TICKERS_FILE"
echo "  Hours: $HOURS_BACK"
echo "  Max Articles: $MAX_ARTICLES"
echo "  Provider: $AI_PROVIDER"
echo ""
echo "Starting analysis..."
echo ""

# Run the analyzer
python3 realtime_ai_news_analyzer.py \
  --tickers-file "$TICKERS_FILE" \
  --hours-back "$HOURS_BACK" \
  --max-articles "$MAX_ARTICLES" \
  --ai-provider "$AI_PROVIDER"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Analysis Complete"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Results: realtime_ai_rankings.csv"
echo ""
