#!/bin/bash
#
# COMPLETE AI ANALYSIS: News + Quant Data
# AI receives BOTH news AND market data for comprehensive scoring
#
# What AI analyzes:
# 1. News impact (headline, content, deal size)
# 2. Volume deviations (spike detection)
# 3. Momentum alignment (3d, 20d, 60d)
# 4. Technical indicators (RSI, ATR)
# 5. Impact ratio (news magnitude vs market cap)
#

set -e

cd /home/vagrant/R/essentials

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                    ║"
echo "║       🤖 COMPLETE AI ANALYSIS: News + Quant                        ║"
echo "║                                                                    ║"
echo "║       AI analyzes: News • Volume • Momentum • Impact Ratio        ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check dependencies
if ! python3 -c "import yfinance" 2>/dev/null; then
    echo "⚠️  WARNING: yfinance not installed"
    echo "Install with: pip install yfinance"
    echo ""
    read -p "Continue without market data? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check cursor
if ! command -v cursor &> /dev/null; then
    echo "❌ ERROR: Cursor CLI not found"
    echo "Install from: https://cursor.com/download"
    exit 1
fi

echo "✅ Cursor CLI: $(which cursor)"
echo "✅ Enhanced bridge: cursor_cli_bridge_enhanced.py"
echo ""

# Configuration for ENHANCED analysis
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_cli_bridge_enhanced.py"
export CURSOR_CLI_PATH="cursor"

# Process ALL stocks with news, in batches
export STAGE2_BATCH_SIZE="${STAGE2_BATCH_SIZE:-5}"
export AI_MAX_CALLS="${AI_MAX_CALLS:-60}"

# Default parameters
TICKERS_FILE="${1:-nifty50_tickers.txt}"
HOURS_BACK="${2:-48}"
TOP_N="${3:-2999}"

echo "📋 Configuration:"
echo "   AI Provider:     Cursor Agent (Enhanced)"
echo "   Bridge:          cursor_cli_bridge_enhanced.py"
echo "   Batch Size:      $STAGE2_BATCH_SIZE stocks at a time"
echo "   Max AI Calls:    $AI_MAX_CALLS"
echo "   Tickers:         $TICKERS_FILE"
echo "   Time Window:     ${HOURS_BACK}h"
echo ""
echo "📊 What AI Analyzes:"
echo "   ✅ News impact (headline, content, deal size)"
echo "   ✅ Volume deviations (spike = confirmation)"
echo "   ✅ Momentum (3d, 20d, 60d trends)"
echo "   ✅ Technical indicators (RSI, ATR)"
echo "   ✅ Impact ratio (deal size vs market cap)"
echo ""
echo "🎯 Scoring Logic:"
echo "   • Base score from news quality"
echo "   • +20 points if volume spike confirms news"
echo "   • +15 points if positive momentum"
echo "   • +10 points if deal > 5% of market cap"
echo "   • +5 points if technical setup supports move"
echo ""

# Run the analysis
./run_realtime_ai_scan.sh "$TICKERS_FILE" "$HOURS_BACK" "$TOP_N" codex

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ COMPLETE AI ANALYSIS DONE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Results: realtime_ai_analysis_*.csv"
echo ""
echo "AI analyzed BOTH news AND market data for each stock:"
echo "  • Volume confirmation"
echo "  • Momentum alignment"
echo "  • Impact ratio"
echo "  • Technical setup"
echo ""
