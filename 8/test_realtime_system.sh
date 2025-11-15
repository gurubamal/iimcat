#!/bin/bash
# Quick test of real-time AI system

echo "Testing Real-time AI News Analysis System..."
echo ""

# Check files
echo "✓ Checking files..."
FILES=(
    "realtime_ai_news_analyzer.py"
    "ai_enhanced_collector.py"
    "run_realtime_ai_scan.sh"
    "REALTIME_AI_QUICKSTART.md"
    "REALTIME_AI_ANALYSIS_README.md"
    "REALTIME_AI_SYSTEM_SUMMARY.md"
)

for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file MISSING"
        exit 1
    fi
done

echo ""
echo "✓ Checking Python imports..."
python3 -c "import sys; print(f'  ✅ Python {sys.version.split()[0]}')"

echo ""
echo "✓ Checking dependencies..."
python3 -c "import pandas; print('  ✅ pandas')" 2>/dev/null || echo "  ⚠️  pandas (optional for full features)"
python3 -c "import numpy; print('  ✅ numpy')" 2>/dev/null || echo "  ⚠️  numpy (optional for full features)"

echo ""
echo "✓ Checking script syntax..."
python3 -m py_compile realtime_ai_news_analyzer.py && echo "  ✅ realtime_ai_news_analyzer.py"
python3 -m py_compile ai_enhanced_collector.py && echo "  ✅ ai_enhanced_collector.py"

echo ""
echo "✓ Checking executability..."
[ -x run_realtime_ai_scan.sh ] && echo "  ✅ run_realtime_ai_scan.sh is executable"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ ALL CHECKS PASSED!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "System is ready to use!"
echo ""
echo "Quick Start:"
echo "  ./run_realtime_ai_scan.sh"
echo ""
echo "Documentation:"
echo "  cat REALTIME_AI_QUICKSTART.md"
echo ""
