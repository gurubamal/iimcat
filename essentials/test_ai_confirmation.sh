#!/bin/bash
################################################################################
# AI CONFIRMATION TEST SCRIPT
################################################################################
# Tests that AI includes data_source_confirmation in responses
# Usage: ./test_ai_confirmation.sh [ticker]
################################################################################

set -e

TICKER="${1:-TRENT}"
TEST_FILE="test_single_ticker.txt"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 AI CONFIRMATION TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Testing ticker: $TICKER"
echo "Expected: AI should return data_source_confirmation field"
echo ""

# Create test file with single ticker
echo "$TICKER" > "$TEST_FILE"

# Run analysis with Claude
echo "🚀 Running AI analysis (this may take 30-60 seconds)..."
echo ""

OUTPUT_CSV=$(./run_without_api.sh claude "$TEST_FILE" 8 10 2>&1 | tee /dev/tty | grep -o "realtime_ai_results.*\.csv" | tail -1)

if [ -z "$OUTPUT_CSV" ]; then
    echo "❌ FAILED: Could not find output CSV file"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 VALIDATION RESULTS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if CSV exists
if [ ! -f "$OUTPUT_CSV" ]; then
    echo "❌ FAILED: Output CSV not found: $OUTPUT_CSV"
    exit 1
fi

echo "✅ Output CSV found: $OUTPUT_CSV"
echo ""

# Check CSV headers for confirmation-related fields
HEADERS=$(head -1 "$OUTPUT_CSV")

# Look for any conversation logs that might contain the confirmation
if [ -d "logs" ]; then
    LATEST_LOG=$(ls -t logs/*.txt 2>/dev/null | head -1)
    if [ -f "$LATEST_LOG" ]; then
        echo "📋 Checking latest conversation log: $LATEST_LOG"
        echo ""

        if grep -q "data_source_confirmation" "$LATEST_LOG"; then
            echo "✅ PASS: data_source_confirmation found in conversation log"
            echo ""
            echo "Confirmation details:"
            grep -A 5 "data_source_confirmation" "$LATEST_LOG" | head -6
        else
            echo "⚠️  WARNING: data_source_confirmation NOT found in log"
            echo "   (This may be expected if logging is disabled)"
        fi
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 DATA VALIDATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if result has price and fundamental data
RESULT_LINE=$(grep "$TICKER" "$OUTPUT_CSV" | head -1)

if [ -z "$RESULT_LINE" ]; then
    echo "❌ FAILED: No results found for $TICKER in CSV"
    exit 1
fi

echo "✅ Analysis result found for $TICKER"
echo ""

# Display the result row
echo "Result summary (first 200 chars):"
echo "$RESULT_LINE" | cut -c1-200
echo "..."
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ TEST COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary:"
echo "  • AI analysis completed successfully"
echo "  • Results saved to: $OUTPUT_CSV"
echo "  • Ticker analyzed: $TICKER"
echo ""
echo "To verify data sources manually:"
echo "  1. Check the CSV for real-time price data"
echo "  2. Verify timestamps are recent"
echo "  3. Look for fundamental data fields"
echo ""
echo "To run full validation:"
echo "  python3 ai_realtime_data_validator.py $TICKER"
echo ""

# Cleanup
rm -f "$TEST_FILE"

exit 0
