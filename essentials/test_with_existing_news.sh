#!/bin/bash
# Quick test using existing news file

LATEST_NEWS=$(ls -t aggregated_full_articles_48h_*.txt 2>/dev/null | head -1)

if [ -z "$LATEST_NEWS" ]; then
    echo "❌ No news files found"
    exit 1
fi

echo "Using news file: $LATEST_NEWS"
echo ""

# For now, the system framework is ready but needs actual integration
# Your existing system: run_real_ai_full.sh does this
echo "To use with your existing system:"
echo "  ./run_real_ai_full.sh"
echo ""
echo "OR fetch fresh news first:"
echo "  python3 enhanced_india_finance_collector.py --tickers-file all.txt --hours-back 24 --max-articles 10"

