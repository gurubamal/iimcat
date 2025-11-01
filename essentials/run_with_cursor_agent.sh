#!/bin/bash
#
# AI-POWERED ANALYSIS using Cursor Agent CLI
# NO API KEYS NEEDED - Uses your local Cursor agent!
#

set -e

cd /home/vagrant/R/essentials

echo ""
echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║                                                                    ║"
echo "║       🤖 CURSOR AGENT STOCK ANALYSIS                               ║"
echo "║                                                                    ║"
echo "║       No API Keys • Local Agent • Complete Justice                ║"
echo "║                                                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if cursor agent is available
if ! command -v cursor &> /dev/null; then
    echo "❌ ERROR: Cursor CLI not found in PATH"
    echo ""
    echo "Install Cursor from: https://cursor.com/download"
    echo "Or ensure cursor is in your PATH"
    exit 1
fi

# Test cursor agent
if ! cursor agent "test" &> /dev/null; then
    echo "⚠️  WARNING: Cursor agent command failed test"
    echo "This might still work, continuing..."
fi

echo "✅ Cursor CLI found: $(which cursor)"
echo ""

# Configuration for Cursor Agent
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 cursor_cli_bridge.py"
export CURSOR_CLI_PATH="cursor"  # Use system cursor

# Process ALL stocks with news, in batches of 5
export STAGE2_BATCH_SIZE=5

# Agent call limits (adjust as needed)
export AI_MAX_CALLS=60

# Default parameters
TICKERS_FILE="${1:-nifty50_tickers.txt}"
HOURS_BACK="${2:-48}"
TOP_N="${3:-2999}"

echo "📋 Configuration:"
echo "   AI Provider:     Cursor Agent (local CLI)"
echo "   Bridge:          cursor_cli_bridge.py"
echo "   Batch Size:      5 stocks at a time"
echo "   Max AI Calls:    $AI_MAX_CALLS"
echo "   Tickers:         $TICKERS_FILE"
echo "   Time Window:     ${HOURS_BACK}h"
echo ""
echo "✅ NO API KEYS NEEDED - Using local Cursor agent"
echo ""

# Run the analysis
./run_realtime_ai_scan.sh "$TICKERS_FILE" "$HOURS_BACK" "$TOP_N" codex

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ CURSOR AGENT ANALYSIS COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Results: realtime_ai_analysis_*.csv"
echo ""
