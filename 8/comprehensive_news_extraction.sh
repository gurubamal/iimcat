#!/bin/bash
# COMPREHENSIVE NEWS EXTRACTION - Maximum Coverage for All 2993 Stocks
# Optimized for fetching ALL news headlines and full articles

echo "🚀 LAUNCHING COMPREHENSIVE NEWS EXTRACTION"
echo "==========================================="
echo "📊 Target: 2993 stocks with maximum news coverage"
echo "⏰ Started: $(date)"
echo ""

# Configuration for maximum coverage
TICKERS_FILE="sec_tickers.txt"
HOURS_BACK=24
MAX_ARTICLES=15
OUTPUT_PREFIX="comprehensive_news_extraction"

# Comprehensive source list for maximum coverage
SOURCES=(
    "reuters.com"
    "livemint.com"
    "economictimes.indiatimes.com"
    "business-standard.com"
    "moneycontrol.com"
    "thehindubusinessline.com"
    "financialexpress.com"
    "cnbctv18.com"
    "zeebiz.com"
    "businesstoday.in"
    "bqprime.com"
    "ndtv.com"
    "news18.com"
    "outlookindia.com"
    "timesofindia.indiatimes.com"
    "indianexpress.com"
    "deccanherald.com"
    "firstpost.com"
    "thequint.com"
    "scroll.in"
)

# Join sources into a single string
SOURCES_STR="${SOURCES[*]}"

echo "📰 News Sources (${#SOURCES[@]} total):"
for i in "${!SOURCES[@]}"; do
    echo "  $((i+1)). ${SOURCES[$i]}"
done
echo ""

echo "🔍 Extraction Parameters:"
echo "  - Tickers file: $TICKERS_FILE"
echo "  - Hours back: $HOURS_BACK"
echo "  - Max articles per ticker: $MAX_ARTICLES"
echo "  - Total sources: ${#SOURCES[@]}"
echo "  - Expected tickers: ~2993"
echo ""

# Run the comprehensive extraction
echo "📡 Starting comprehensive news extraction..."
echo "⚠️  This may take 30-60 minutes for complete coverage"
echo ""

python3 enhanced_india_finance_collector.py \
    --tickers-file "$TICKERS_FILE" \
    --hours-back "$HOURS_BACK" \
    --max-articles "$MAX_ARTICLES" \
    --sources $SOURCES_STR \
    --all-news \
    --output-file "${OUTPUT_PREFIX}_${HOURS_BACK}h" \
    --extra-rss "https://www.bqprime.com/feed" "https://www.businesstoday.in/rssfeeds/?id=0"

EXTRACTION_EXIT_CODE=$?

echo ""
echo "📊 EXTRACTION COMPLETION STATUS"
echo "==============================="
if [ $EXTRACTION_EXIT_CODE -eq 0 ]; then
    echo "✅ Extraction completed successfully"
    
    # Find the generated file
    LATEST_FILE=$(ls -t ${OUTPUT_PREFIX}_${HOURS_BACK}h_*.txt 2>/dev/null | head -1)
    
    if [ -n "$LATEST_FILE" ]; then
        echo "📁 Output file: $LATEST_FILE"
        echo "📈 File size: $(ls -lh "$LATEST_FILE" | awk '{print $5}')"
        echo "📝 Line count: $(wc -l < "$LATEST_FILE")"
        
        # Basic statistics
        echo ""
        echo "📊 EXTRACTION STATISTICS:"
        echo "========================"
        ARTICLE_COUNT=$(grep -c "TICKER:" "$LATEST_FILE" 2>/dev/null || echo "0")
        WORD_COUNT=$(wc -w < "$LATEST_FILE" 2>/dev/null || echo "0")
        
        echo "📰 Articles extracted: $ARTICLE_COUNT"
        echo "📝 Total words: $WORD_COUNT"
        echo "💾 Storage: $(ls -lh "$LATEST_FILE" | awk '{print $5}')"
        
        if [ "$ARTICLE_COUNT" -gt 100 ]; then
            echo "🟢 HIGH YIELD - Excellent news coverage"
        elif [ "$ARTICLE_COUNT" -gt 50 ]; then
            echo "🟡 MEDIUM YIELD - Good news coverage" 
        else
            echo "🔴 LOW YIELD - Limited news activity"
        fi
    else
        echo "⚠️  Output file not found"
    fi
else
    echo "❌ Extraction failed with exit code: $EXTRACTION_EXIT_CODE"
fi

echo ""
echo "⏰ Completed: $(date)"
echo "🎯 Ready for analysis!"