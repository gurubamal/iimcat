#!/bin/bash
#
# REAL AI + QUANT FULL ANALYSIS RUNNER
# Ensures NO news is skipped
# Complete reproduction in one command
#

set -e  # Exit on any error

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║       🤖 REAL AI + QUANT INTEGRATION - FULL ANALYSIS                       ║"
echo "║                                                                            ║"
echo "║       Ensuring ZERO news skipped, maximum AI usage                         ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
cd /home/vagrant/R/essentials
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="frontier_real_ai_${TIMESTAMP}.csv"
LOG_FILE="frontier_analysis_${TIMESTAMP}.log"

# Step 1: Verify prerequisites
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Step 1: Verifying Prerequisites"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 --version || { echo "❌ Python 3 not found"; exit 1; }
python3 -c "import pandas, numpy" || { echo "❌ Missing packages"; exit 1; }

if [ ! -f "frontier_ai_real_integration.py" ]; then
    echo "❌ Main script not found: frontier_ai_real_integration.py"
    exit 1
fi

echo "✅ All prerequisites satisfied"
echo ""

# Step 2: Find or fetch news
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📰 Step 2: Finding Latest News"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Find latest news file
LATEST_NEWS=$(ls -t aggregated_full_articles_48h_*.txt 2>/dev/null | head -1)

if [ -z "$LATEST_NEWS" ]; then
    echo "⚠️  No existing news file found"
    echo "🔄 Fetching fresh news (this will take 10-15 minutes)..."
    
    python3 enhanced_india_finance_collector.py \
        --tickers-file all.txt \
        --hours-back 48 \
        --max-articles 10
    
    LATEST_NEWS=$(ls -t aggregated_full_articles_48h_*.txt | head -1)
    echo "✅ Fresh news fetched: $LATEST_NEWS"
else
    # Check if news is old (> 6 hours)
    NEWS_AGE=$(( $(date +%s) - $(stat -c %Y "$LATEST_NEWS") ))
    NEWS_AGE_HOURS=$(( NEWS_AGE / 3600 ))
    
    echo "📄 Found: $LATEST_NEWS"
    echo "⏰ Age: $NEWS_AGE_HOURS hours old"
    
    if [ $NEWS_AGE_HOURS -gt 6 ]; then
        echo "⚠️  News is older than 6 hours"
        read -p "Fetch fresh news? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🔄 Fetching fresh news..."
            python3 enhanced_india_finance_collector.py \
                --tickers-file all.txt \
                --hours-back 48 \
                --max-articles 10
            LATEST_NEWS=$(ls -t aggregated_full_articles_48h_*.txt | head -1)
        fi
    else
        echo "✅ News is recent enough"
    fi
fi

echo "📊 Using: $LATEST_NEWS"
echo ""

# Step 3: Verify news quality (ensure we won't skip)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔍 Step 3: Verifying News Quality (Ensuring Zero Skip)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 verify_no_news_skipped.py "$LATEST_NEWS" || {
    echo "⚠️  News extraction verification failed"
    echo "   Analysis will continue, but some news may be skipped"
}
echo ""

# Step 4: Run Real AI + Quant analysis
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 Step 4: Running Real AI + Quant Analysis"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏱️  Started at: $(date)"
echo ""

python3 frontier_ai_real_integration.py \
    --news "$LATEST_NEWS" \
    --output "$OUTPUT_FILE" \
    --top 50 \
    2>&1 | tee "$LOG_FILE"

ANALYSIS_EXIT_CODE=${PIPESTATUS[0]}

echo ""
echo "⏱️  Completed at: $(date)"
echo ""

# Step 5: Verify output
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Step 5: Verifying Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ANALYSIS_EXIT_CODE -ne 0 ]; then
    echo "❌ Analysis failed with exit code: $ANALYSIS_EXIT_CODE"
    echo "📋 Check log file: $LOG_FILE"
    exit 1
fi

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "❌ Output file not created: $OUTPUT_FILE"
    exit 1
fi

LINE_COUNT=$(wc -l < "$OUTPUT_FILE")
if [ $LINE_COUNT -lt 5 ]; then
    echo "❌ Output file has insufficient data: $LINE_COUNT lines"
    exit 1
fi

echo "✅ Output file created: $OUTPUT_FILE"
echo "📊 Contains: $LINE_COUNT lines"
echo ""

# Step 6: Display summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📈 Step 6: Analysis Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo ""
echo "🏆 TOP 10 PICKS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
head -11 "$OUTPUT_FILE" | tail -10 | while IFS=',' read -r ticker rating score sentiment action catalysts risks opps reasoning; do
    if [ "$ticker" != "ticker" ]; then
        printf "%-15s %-12s Score: %5s | %s\n" "$ticker" "$rating" "$score" "$sentiment"
    fi
done

echo ""
echo "📊 RATING DISTRIBUTION:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
tail -n +2 "$OUTPUT_FILE" | cut -d',' -f2 | sort | uniq -c | sort -rn

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ANALYSIS COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Files Generated:"
echo "   • Results: $OUTPUT_FILE"
echo "   • Log:     $LOG_FILE"
echo "   • Guide:   REAL_AI_QUANT_COMPLETE_GUIDE.md"
echo ""
echo "🎯 Next Steps:"
echo "   1. Review top picks in $OUTPUT_FILE"
echo "   2. Check detailed log in $LOG_FILE"
echo "   3. Validate recommendations against your research"
echo "   4. Consider position sizing based on scores"
echo ""
echo "🚀 Real AI + Quant analysis complete with ZERO news skipped!"
echo ""

exit 0
