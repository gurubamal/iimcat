#!/bin/bash
# Quick Start Script for Feedback Loop System

set -e

show_menu() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║        AI Feedback Loop - Quick Start Menu                 ║"
    echo "╠════════════════════════════════════════════════════════════╣"
    echo "║ 1. Run simulation (see how it works)                       ║"
    echo "║ 2. Record a prediction                                     ║"
    echo "║ 3. Update actual performance                               ║"
    echo "║ 4. Run learning algorithm                                  ║"
    echo "║ 5. View performance report                                 ║"
    echo "║ 6. Start continuous monitoring                             ║"
    echo "║ 7. Show monitoring dashboard                               ║"
    echo "║ 8. Compare standard vs adaptive AI                         ║"
    echo "║ 9. Exit                                                    ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

run_simulation() {
    echo ""
    echo "🧪 Running feedback loop simulation..."
    echo "   (This demonstrates the system with SAGILITY/WORTH/BHEL example)"
    echo ""
    python3 test_feedback_loop_simulation.py
    echo ""
    read -p "Press Enter to continue..."
}

record_prediction() {
    echo ""
    echo "📝 Record a New Prediction"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    read -p "Ticker (e.g., RELIANCE): " ticker
    read -p "AI Score (0-100): " score
    read -p "Recommendation (BUY/SELL/HOLD): " action
    read -p "Current Price: " price
    read -p "Analysis file path (optional, press Enter to skip): " analysis_file

    if [ -n "$analysis_file" ] && [ -f "$analysis_file" ]; then
        python3 realtime_feedback_loop.py --record "$ticker" \
            --score "$score" --action "$action" --price "$price" \
            --analysis-file "$analysis_file"
    else
        python3 realtime_feedback_loop.py --record "$ticker" \
            --score "$score" --action "$action" --price "$price"
    fi

    echo ""
    echo "✅ Prediction recorded! Monitor with option 6 or 7."
    read -p "Press Enter to continue..."
}

update_performance() {
    echo ""
    echo "📊 Update Actual Performance"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Show active predictions
    echo "Active predictions:"
    python3 -c "
import json, os
if os.path.exists('learning/predictions_tracking.json'):
    with open('learning/predictions_tracking.json', 'r') as f:
        preds = json.load(f)
    for ticker, pred in preds.items():
        print(f'  • {ticker}: {pred[\"recommendation\"]} @ ₹{pred[\"initial_price\"]}')
else:
    print('  (none)')
"

    echo ""
    read -p "Ticker to update: " ticker
    read -p "Current market price: " current_price
    read -p "Volume change % (0 if unknown): " volume_change
    read -p "Current RSI (50 if unknown): " current_rsi

    python3 realtime_feedback_loop.py --update "$ticker" \
        --current-price "$current_price" \
        --volume-change "${volume_change:-0}" \
        --current-rsi "${current_rsi:-50}"

    echo ""
    read -p "Press Enter to continue..."
}

run_learning() {
    echo ""
    echo "🧠 Running Learning Algorithm..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    python3 realtime_feedback_loop.py --learn --output learning/learned_weights.json

    echo ""
    echo "✅ Learning complete! Updated weights saved."
    echo "   Use option 8 to see how this improves predictions."
    read -p "Press Enter to continue..."
}

show_report() {
    echo ""
    python3 realtime_feedback_loop.py --report
    echo ""
    read -p "Press Enter to continue..."
}

start_monitoring() {
    echo ""
    echo "🔍 Starting Continuous Monitoring"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    read -p "Check interval in seconds (default 180): " interval
    interval=${interval:-180}

    read -p "Auto-learn when threshold met? (y/n, default n): " auto_learn

    if [[ "$auto_learn" == "y" ]]; then
        read -p "Minimum samples before learning (default 5): " min_samples
        min_samples=${min_samples:-5}

        echo ""
        echo "Starting monitor with auto-learning (min samples: $min_samples)..."
        echo "Press Ctrl+C to stop"
        echo ""
        python3 realtime_price_monitor.py --monitor --interval "$interval" \
            --auto-learn --min-samples "$min_samples"
    else
        echo ""
        echo "Starting monitor (manual learning only)..."
        echo "Press Ctrl+C to stop"
        echo ""
        python3 realtime_price_monitor.py --monitor --interval "$interval"
    fi

    echo ""
    read -p "Press Enter to continue..."
}

show_dashboard() {
    echo ""
    python3 realtime_price_monitor.py --dashboard
    echo ""
    read -p "Press Enter to continue..."
}

compare_ai() {
    echo ""
    echo "⚖️  Compare Standard vs Adaptive AI"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    read -p "Ticker to analyze: " ticker
    read -p "News file path (or Enter to use mock data): " news_file

    if [ -n "$news_file" ] && [ -f "$news_file" ]; then
        python3 adaptive_ai_analyzer.py --ticker "$ticker" \
            --news-file "$news_file" --compare
    else
        python3 adaptive_ai_analyzer.py --ticker "$ticker" --compare
    fi

    echo ""
    read -p "Press Enter to continue..."
}

# Check if required files exist
check_dependencies() {
    if [ ! -f "realtime_feedback_loop.py" ]; then
        echo "❌ Error: realtime_feedback_loop.py not found"
        echo "   Please run this script from the essentials directory"
        exit 1
    fi

    # Create learning directory if it doesn't exist
    mkdir -p learning
}

# Main loop
main() {
    check_dependencies

    while true; do
        clear
        show_menu
        read -p "Select option (1-9): " choice

        case $choice in
            1) run_simulation ;;
            2) record_prediction ;;
            3) update_performance ;;
            4) run_learning ;;
            5) show_report ;;
            6) start_monitoring ;;
            7) show_dashboard ;;
            8) compare_ai ;;
            9) echo "Goodbye!"; exit 0 ;;
            *) echo "Invalid option. Press Enter to try again..."; read ;;
        esac
    done
}

# Run main
main
