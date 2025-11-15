#!/bin/bash
#
# REAL AI-POWERED ANALYSIS (Not Heuristics!)
# Uses Claude via Cursor AI Bridge for genuine AI analysis
#

set -e

cd /home/vagrant/R/essentials

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️  WARNING: No ANTHROPIC_API_KEY found!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "To enable REAL AI analysis with Claude:"
    echo ""
    echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
    echo ""
    echo "Without this, the system will use enhanced heuristics (pattern matching)."
    echo ""
    read -p "Continue with heuristics only? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                    ║"
echo "║       🤖 AI-POWERED STOCK ANALYSIS                                 ║"
echo "║                                                                    ║"
echo "║       Real AI • Batch Processing • Complete Justice               ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration for REAL AI analysis
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_ai_bridge.py"
export VERIFY_AGENT_INTERNET=0  # We use Claude API, not shell internet

# Process ALL stocks with news, in batches of 5
export STAGE2_BATCH_SIZE=5

# AI call limits (adjust based on your API budget)
export AI_MAX_CALLS=60  # Increase for more stocks

# Default parameters
TICKERS_FILE="${1:-nifty50_tickers.txt}"
HOURS_BACK="${2:-48}"
TOP_N="${3:-2999}"

echo "📋 Configuration:"
echo "   AI Provider:     Claude (via Anthropic API)"
echo "   Bridge:          cursor_ai_bridge.py"
echo "   Batch Size:      5 stocks at a time"
echo "   Max AI Calls:    $AI_MAX_CALLS"
echo "   Tickers:         $TICKERS_FILE"
echo "   Time Window:     ${HOURS_BACK}h"
echo ""

if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ REAL AI ENABLED - Claude will analyze each article"
else
    echo "⚠️  HEURISTICS MODE - Enhanced pattern matching only"
fi
echo ""

# Run the analysis
./run_realtime_ai_scan.sh "$TICKERS_FILE" "$HOURS_BACK" "$TOP_N" codex

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ AI-POWERED ANALYSIS COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
