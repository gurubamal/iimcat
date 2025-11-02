#!/bin/bash
# Test script for enhanced Claude exit analysis
# Compares Claude vs Codex on same dataset

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 CLAUDE vs CODEX EXIT STRATEGY TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ERROR: ANTHROPIC_API_KEY not set"
    echo ""
    echo "To test Claude enhanced exit analysis:"
    echo "  export ANTHROPIC_API_KEY='sk-ant-xxxxx'"
    echo "  ./test_claude_exit_enhanced.sh"
    echo ""
    echo "For now, showing system status only..."
    echo ""
fi

# Test dataset
TICKERS_FILE="exit.small.txt"
HOURS_BACK=72

echo "Test Configuration:"
echo "  Dataset: $TICKERS_FILE"
echo "  News Window: $HOURS_BACK hours"
echo "  Providers: Codex (baseline) vs Claude (enhanced)"
echo ""

# Check ticker file
if [ ! -f "$TICKERS_FILE" ]; then
    echo "❌ ERROR: $TICKERS_FILE not found"
    exit 1
fi

TICKER_COUNT=$(grep -Ecv '^(#|\s*$)' "$TICKERS_FILE" 2>/dev/null || echo "0")
echo "  Stocks in test: $TICKER_COUNT"
echo ""

# Check dependencies
echo "Dependency Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Python version
python3 --version 2>&1 | head -1

# Required libraries
echo -n "  anthropic library: "
python3 -c "import anthropic; print('✅ installed')" 2>/dev/null || echo "❌ missing (pip install anthropic)"

echo -n "  requests library: "
python3 -c "import requests; print('✅ installed')" 2>/dev/null || echo "❌ missing (pip install requests)"

echo -n "  beautifulsoup4: "
python3 -c "import bs4; print('✅ installed')" 2>/dev/null || echo "❌ missing (pip install beautifulsoup4)"

echo -n "  yfinance: "
python3 -c "import yfinance; print('✅ installed')" 2>/dev/null || echo "❌ missing (pip install yfinance)"

echo ""

# Check enhanced bridge exists
echo "Enhanced Bridge Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "claude_exit_bridge.py" ]; then
    echo "  ✅ claude_exit_bridge.py found"
    LINES=$(wc -l < claude_exit_bridge.py)
    echo "     Lines of code: $LINES"
    echo "     Features: 7 enhancements (see CLAUDE_EXIT_ENHANCEMENT_PLAN.md)"
else
    echo "  ❌ claude_exit_bridge.py not found"
    exit 1
fi

echo ""

# Check integration
echo "Integration Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if grep -q "claude_exit_bridge.py" exit_intelligence_analyzer.py; then
    echo "  ✅ exit_intelligence_analyzer.py integrated"
else
    echo "  ❌ exit_intelligence_analyzer.py not integrated"
fi

if grep -q "claude_exit_bridge.py" realtime_exit_ai_analyzer.py; then
    echo "  ✅ realtime_exit_ai_analyzer.py integrated"
else
    echo "  ❌ realtime_exit_ai_analyzer.py not integrated"
fi

echo ""

# If API key is set, run actual test
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🚀 Running Comparative Test"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Run Codex baseline
    echo "1️⃣  Running Codex Baseline..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    timeout 120 python3 realtime_exit_ai_analyzer.py \
        --tickers-file "$TICKERS_FILE" \
        --ai-provider codex \
        --hours-back "$HOURS_BACK" \
        --max-articles 5 \
        --output codex_exit_test.csv || true

    echo ""
    echo ""

    # Run Claude Enhanced
    echo "2️⃣  Running Claude Enhanced..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    timeout 120 python3 realtime_exit_ai_analyzer.py \
        --tickers-file "$TICKERS_FILE" \
        --ai-provider claude \
        --hours-back "$HOURS_BACK" \
        --max-articles 5 \
        --output claude_exit_test.csv || true

    echo ""
    echo ""

    # Compare results
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 COMPARISON RESULTS"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    if [ -f "codex_exit_test.csv" ] && [ -f "claude_exit_test.csv" ]; then
        echo "Codex Results:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        awk -F, 'NR==1 || NR<=6 {print}' codex_exit_test.csv | column -t -s,
        echo ""

        echo "Claude Enhanced Results:"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        awk -F, 'NR==1 || NR<=6 {print}' claude_exit_test.csv | column -t -s,
        echo ""

        # Calculate averages
        CODEX_AVG=$(awk -F, 'NR>1 {sum+=$4; count++} END {if(count>0) print sum/count; else print 0}' codex_exit_test.csv)
        CLAUDE_AVG=$(awk -F, 'NR>1 {sum+=$4; count++} END {if(count>0) print sum/count; else print 0}' claude_exit_test.csv)

        echo "Average Exit Urgency Score:"
        echo "  Codex:  $CODEX_AVG/100"
        echo "  Claude: $CLAUDE_AVG/100"
        echo ""

        CODEX_CERT=$(awk -F, 'NR>1 {sum+=$10; count++} END {if(count>0) print sum/count; else print 0}' codex_exit_test.csv)
        CLAUDE_CERT=$(awk -F, 'NR>1 {sum+=$10; count++} END {if(count>0) print sum/count; else print 0}' claude_exit_test.csv)

        echo "Average Certainty:"
        echo "  Codex:  $CODEX_CERT%"
        echo "  Claude: $CLAUDE_CERT%"
        echo ""

        # Check for JSONL log
        if [ -f "outputs/claude_exit_decisions.jsonl" ]; then
            echo "✅ Claude decision log created: outputs/claude_exit_decisions.jsonl"
            DECISION_COUNT=$(wc -l < outputs/claude_exit_decisions.jsonl)
            echo "   Logged $DECISION_COUNT decisions for feedback learning"
            echo ""
        fi

        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ TEST COMPLETE"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Review full results:"
        echo "  cat codex_exit_test.csv"
        echo "  cat claude_exit_test.csv"
        echo ""
        echo "See enhancement details:"
        echo "  cat CLAUDE_EXIT_ENHANCEMENT_PLAN.md"
        echo "  cat CLAUDE_VS_CODEX_EXIT_COMPARISON.md"

    else
        echo "⚠️  One or both test runs failed"
        echo "   Check logs above for errors"
    fi

else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "ℹ️  Test Ready (API key required to run)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Enhanced Claude exit bridge is ready to use!"
    echo ""
    echo "To run comparison test:"
    echo "  export ANTHROPIC_API_KEY='your-key-here'"
    echo "  ./test_claude_exit_enhanced.sh"
    echo ""
    echo "Or run directly:"
    echo "  ./run_exit_assessment.sh claude exit.small.txt 72"
fi

echo ""
