#!/bin/bash
# Monitor the running scan

echo "📊 SCAN MONITORING DASHBOARD"
echo "="
while true; do
    clear
    echo "📊 ENHANCED SCAN MONITORING"
    echo "Time: $(date)"
    echo "="
    
    # Check if process is running
    if ps aux | grep -q "[e]nhanced_india_finance_collector"; then
        echo "✅ Status: RUNNING"
        
        # Check latest log
        if [ -f scan_output_*.log ]; then
            LATEST_LOG=$(ls -t scan_output_*.log 2>/dev/null | head -1)
            echo "📝 Latest log: $LATEST_LOG"
            echo ""
            echo "Recent activity:"
            tail -10 "$LATEST_LOG" 2>/dev/null | grep -E "Processing|articles|Qualified|Rejected|complete" || echo "Processing..."
        fi
        
        # Check aggregated file
        LATEST_AGG=$(ls -t aggregated_full_articles_48h_*.txt 2>/dev/null | head -1)
        if [ -f "$LATEST_AGG" ]; then
            SIZE=$(du -h "$LATEST_AGG" | cut -f1)
            TICKERS=$(grep -c "Full Article Fetch Test" "$LATEST_AGG" 2>/dev/null || echo "0")
            ARTICLES=$(grep -c "Title   :" "$LATEST_AGG" 2>/dev/null || echo "0")
            echo ""
            echo "📈 Progress:"
            echo "   File size: $SIZE"
            echo "   Tickers: $TICKERS/2993 ($(echo "scale=1; $TICKERS*100/2993" | bc 2>/dev/null)%)"
            echo "   Articles: $ARTICLES"
        fi
    else
        echo "⏸️  Status: COMPLETED or NOT RUNNING"
        break
    fi
    
    echo ""
    echo "Press Ctrl+C to exit monitoring"
    sleep 10
done

echo ""
echo "✅ Scan complete or stopped"
