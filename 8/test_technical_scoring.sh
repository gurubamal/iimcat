#!/bin/bash
# Test technical scoring system
# This validates that yfinance data fetching and scoring works correctly

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 TECHNICAL SCORING VALIDATION TEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Enable technical scoring
export ENABLE_TECHNICAL_SCORING=1

echo "Testing technical scoring wrapper..."
echo ""

python3 << 'EOF'
from technical_scoring_wrapper import TechnicalScorer
import sys

scorer = TechnicalScorer()

# Test stocks
test_tickers = [
    ('RELIANCE.NS', 'Large cap, high liquidity'),
    ('TRENT.NS', 'Mid cap, recent volatility'),
    ('INFY.NS', 'IT sector bellwether')
]

print("="*80)
print("TECHNICAL SCORING VALIDATION RESULTS")
print("="*80)
print()

all_passed = True

for ticker, description in test_tickers:
    print(f"Testing: {ticker} ({description})")
    print("-"*80)

    result = scorer.score_ticker(ticker, period='3mo')

    if not result:
        print(f"  ❌ FAILED: Could not fetch data")
        all_passed = False
        continue

    if not result['passed_filters']:
        print(f"  ⚠️  FAILED FILTERS: {result.get('tier', 'N/A')}")
        all_passed = False
        continue

    # Display results
    print(f"  ✅ PASSED: Data fetched successfully")
    print(f"  Score: {result['score']:.1f}/100")
    print(f"  Tier: {result['tier']} ({result['setup_quality']} setup)")

    ind = result['indicators']
    print(f"  Technical Indicators:")
    print(f"    - RSI: {ind['rsi']:.1f}")
    print(f"    - BB Position: {ind['bb_position']:.1f}%")
    print(f"    - ATR: {ind['atr_pct']:.2f}%" if ind['atr_pct'] else "    - ATR: N/A")
    print(f"    - Volume: {ind['volume_ratio']:.2f}x average")
    print(f"  Fetch Time: {result['fetch_time']}")
    print()

print("="*80)
if all_passed:
    print("✅ ALL TESTS PASSED - Technical scoring is working correctly!")
    print("="*80)
    print()
    print("Next steps:")
    print("1. Run with technical scoring enabled:")
    print("   ./run_without_api.sh claude all.txt 48 10 1")
    print("                                            └─ Enable technical scoring")
    print()
    print("2. Check output for hybrid scores (AI + Technical combined)")
    sys.exit(0)
else:
    print("❌ SOME TESTS FAILED - Check errors above")
    print("="*80)
    sys.exit(1)
EOF

exit_code=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $exit_code -eq 0 ]; then
    echo "✅ VALIDATION COMPLETE - System ready for hybrid ranking"
else
    echo "❌ VALIDATION FAILED - Review errors above"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $exit_code
