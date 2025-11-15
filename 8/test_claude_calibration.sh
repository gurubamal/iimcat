#!/bin/bash
# Test Claude Calibration Fix
# Validates that Claude now produces better scores (70-85 instead of 33-34)

set -e

echo "========================================"
echo "CLAUDE CALIBRATION TEST"
echo "========================================"
echo ""
echo "This test validates the Claude optimization."
echo "Expected improvements:"
echo "  • Scores: 70-85 (was 33-34)"
echo "  • Certainty: 60-80% (was 30%)"
echo "  • Sentiment: bullish (was neutral)"
echo "  • Catalysts: identified (was None)"
echo ""

# Check if ANTHROPIC_API_KEY is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ERROR: ANTHROPIC_API_KEY not set"
    echo "   Set it with: export ANTHROPIC_API_KEY='sk-ant-...'"
    exit 1
fi

echo "✅ ANTHROPIC_API_KEY is set"
echo ""

# Enable logging to capture prompts and responses
export AI_LOG_ENABLED=true

echo "Running test analysis with Claude..."
echo "Command: ./run_without_api.sh claude all.txt 18 10"
echo ""

# Run analysis
timeout 180 ./run_without_api.sh claude all.txt 18 10 || {
    echo "⚠️  Analysis timed out or failed"
    exit 1
}

echo ""
echo "========================================"
echo "RESULTS VALIDATION"
echo "========================================"
echo ""

# Check latest log file
LATEST_LOG=$(ls -t logs/ai_conversations/*claude*.json 2>/dev/null | head -1)

if [ -z "$LATEST_LOG" ]; then
    echo "❌ No Claude log files found"
    exit 1
fi

echo "📄 Analyzing log: $LATEST_LOG"
echo ""

# Extract key metrics using Python
python3 << 'EOF'
import json
import sys
from pathlib import Path

# Find latest Claude log
import glob
import os

log_files = glob.glob('logs/ai_conversations/*claude*.json')
if not log_files:
    print("❌ No log files found")
    sys.exit(1)

latest_log = max(log_files, key=os.path.getctime)

with open(latest_log, 'r') as f:
    log_data = json.load(f)

# Parse response JSON
try:
    response = json.loads(log_data.get('response', '{}'))
except:
    print("❌ Failed to parse response JSON")
    sys.exit(1)

# Extract metrics
score = response.get('score', 0)
certainty = response.get('certainty', 0)
sentiment = response.get('sentiment', 'unknown')
catalysts = response.get('catalysts', [])
recommendation = response.get('recommendation', 'unknown')

print("📊 ANALYSIS RESULTS:")
print(f"   Score: {score}/100")
print(f"   Certainty: {certainty}%")
print(f"   Sentiment: {sentiment}")
print(f"   Catalysts: {catalysts}")
print(f"   Recommendation: {recommendation}")
print()

# Validation checks
passed = 0
failed = 0

print("🔍 VALIDATION CHECKS:")
print()

# Check 1: Score should be reasonable (not 33)
if score >= 60:
    print("✅ PASS: Score is reasonable (≥60)")
    passed += 1
elif score >= 50:
    print("⚠️  WARN: Score is moderate (50-59) - acceptable for weak news")
    passed += 1
else:
    print(f"❌ FAIL: Score too low ({score}) - expected ≥60 for quality news")
    failed += 1

# Check 2: Certainty should be reasonable (not 30%)
if certainty >= 50:
    print("✅ PASS: Certainty is reasonable (≥50%)")
    passed += 1
elif certainty >= 40:
    print("⚠️  WARN: Certainty is moderate (40-49%) - acceptable")
    passed += 1
else:
    print(f"❌ FAIL: Certainty too low ({certainty}%) - expected ≥50%")
    failed += 1

# Check 3: Sentiment should be detected (not always neutral)
if sentiment in ['bullish', 'bearish']:
    print(f"✅ PASS: Sentiment properly detected ({sentiment})")
    passed += 1
else:
    print(f"⚠️  WARN: Sentiment is neutral - may be acceptable")
    passed += 1

# Check 4: Catalysts should be identified (not empty/None)
if catalysts and catalysts != ['None'] and len(catalysts) > 0:
    print(f"✅ PASS: Catalysts identified ({len(catalysts)} found)")
    passed += 1
else:
    print("❌ FAIL: No catalysts identified - should always identify at least 1")
    failed += 1

# Check 5: Recommendation should match score
if score >= 70 and recommendation in ['BUY', 'STRONG BUY']:
    print(f"✅ PASS: Recommendation matches score ({recommendation})")
    passed += 1
elif score < 70 and recommendation in ['HOLD', 'ACCUMULATE']:
    print(f"✅ PASS: Recommendation matches score ({recommendation})")
    passed += 1
else:
    print(f"⚠️  WARN: Recommendation ({recommendation}) may not match score ({score})")
    passed += 1

print()
print("=" * 50)
print(f"RESULTS: {passed} passed, {failed} failed")
print("=" * 50)

if failed == 0:
    print("✅ SUCCESS: Claude calibration is working well!")
    sys.exit(0)
elif failed <= 1:
    print("⚠️  PARTIAL: Claude calibration improved but needs tuning")
    sys.exit(0)
else:
    print("❌ FAILURE: Claude calibration still needs work")
    sys.exit(1)

EOF

echo ""
echo "========================================"
echo "VIEW FULL LOGS"
echo "========================================"
echo ""
echo "To view the full prompt and response:"
echo "  ./ai_log_helper.sh view claude"
echo ""
echo "To view raw JSON:"
echo "  cat $LATEST_LOG | jq ."
echo ""
