#!/bin/bash

echo "=================================================="
echo "🔍 FULL TRUSTWORTHY SCAN - Configuration Driven"
echo "=================================================="
echo ""
echo "Starting at: $(date)"
echo ""

# Monitor scan progress
SCAN_PID=$(pgrep -f "run_swing_paths" | head -1)

if [ -z "$SCAN_PID" ]; then
    echo "❌ No scan process found!"
    exit 1
fi

echo "✅ Scan process running: PID $SCAN_PID"
echo ""

# Wait for completion with progress updates
LAST_PROGRESS=""
while ps -p $SCAN_PID > /dev/null 2>&1; do
    LOG_FILE=$(ls -t full_scan_*.log 2>/dev/null | head -1)
    if [ -n "$LOG_FILE" ]; then
        PROGRESS=$(tail -1 "$LOG_FILE" | grep -o '\[[0-9]*/[0-9]* ([0-9.]*%)\]' || echo "")
        if [ -n "$PROGRESS" ] && [ "$PROGRESS" != "$LAST_PROGRESS" ]; then
            echo "Progress: $PROGRESS"
            LAST_PROGRESS="$PROGRESS"
        fi
    fi
    sleep 30
done

echo ""
echo "✅ Scan completed at: $(date)"
echo ""

# Check if we have new output files
LATEST_CSV=$(ls -t outputs/ai_adjusted_top50_*.csv 2>/dev/null | head -1)

if [ -z "$LATEST_CSV" ]; then
    echo "❌ No output files found!"
    exit 1
fi

echo "📊 Latest results: $LATEST_CSV"
echo ""

# Run configuration-driven trustworthy analysis
echo "=================================================="
echo "🔍 Running Trustworthy Analysis (Config-Driven)"
echo "=================================================="
echo ""

python3 trustworthy_news_analyzer.py

echo ""
echo "=================================================="
echo "✅ COMPLETE - Results Available"
echo "=================================================="
echo ""
echo "📁 Output Files:"
ls -lh outputs/trustworthy_analysis_results.csv outputs/ai_adjusted_top50_*.csv | tail -2
echo ""
echo "📋 View trustworthy results:"
echo "   cat outputs/trustworthy_analysis_results.csv"
echo ""
echo "🔧 Adjust rules:"
echo "   nano configs/trustworthy_analysis_config.json"
echo ""
