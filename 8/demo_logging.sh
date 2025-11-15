#!/bin/bash
# Quick logging demonstration script
# Shows different logging modes and their outputs

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║         Enhanced News Collection - Logging Demonstration                   ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Test tickers - small set for quick demonstration
TEST_TICKERS="RELIANCE TCS INFY"

echo "🔍 Mode 1: Standard Logging (Default)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Shows progress, found articles, and summary statistics"
echo ""
read -p "Press Enter to run standard scan..."
echo ""

python3 enhanced_india_finance_collector.py \
  --tickers $TEST_TICKERS \
  --hours-back 48 \
  --max-articles 3

echo ""
echo ""
echo "🔍 Mode 2: Verbose Logging (--verbose)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Shows sample rejected URLs and detailed filtering reasons"
echo ""
read -p "Press Enter to run verbose scan..."
echo ""

python3 enhanced_india_finance_collector.py \
  --tickers $TEST_TICKERS \
  --hours-back 48 \
  --max-articles 3 \
  --verbose

echo ""
echo ""
echo "🔍 Mode 3: Verbose with More Samples (--verbose --show-samples 5)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Shows 5 sample URLs instead of default 3"
echo ""
read -p "Press Enter to run verbose scan with more samples..."
echo ""

python3 enhanced_india_finance_collector.py \
  --tickers $TEST_TICKERS \
  --hours-back 48 \
  --max-articles 3 \
  --verbose \
  --show-samples 5

echo ""
echo ""
echo "🔍 Mode 4: Verbose with All News (--verbose --all-news)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Disables financial URL filtering to show what's being missed"
echo ""
read -p "Press Enter to run with all news (no financial filtering)..."
echo ""

python3 enhanced_india_finance_collector.py \
  --tickers $TEST_TICKERS \
  --hours-back 48 \
  --max-articles 3 \
  --verbose \
  --all-news

echo ""
echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                          Demonstration Complete                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "📖 For complete documentation, see: LOGGING_GUIDE.md"
echo ""
echo "💡 Quick Tips:"
echo "   • Use --verbose to diagnose filtering issues"
echo "   • Use --all-news to bypass financial URL filtering"
echo "   • Increase --hours-back on weekends (72-96 hours)"
echo "   • Check hit rate in summary (target: ≥2%)"
echo ""
echo "🚀 Run full scan with: ./optimal_scan_config.sh"
echo ""
