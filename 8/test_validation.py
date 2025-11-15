#!/usr/bin/env python3
"""Quick test of the AI ticker validation"""

import os
import sys

# Set up environment for testing
os.environ['CLAUDE_SHELL_CMD'] = 'python3 claude_cli_bridge.py'
os.environ['AI_PROVIDER'] = 'claude'

# Import the analyzer
from realtime_ai_news_analyzer import RealtimeAIAnalyzer

print("Testing AI Ticker Validation")
print("=" * 60)

# Create analyzer
analyzer = RealtimeAIAnalyzer(ai_provider='claude', max_ai_calls=10)

# Test a few tickers
test_tickers = ['RELIANCE', 'INVALIDTICKER123', 'TCS', 'FAKESTOCKXYZ', 'INFY']

print(f"\nTesting {len(test_tickers)} tickers:")
print("-" * 60)

valid_count = 0
invalid_count = 0

for ticker in test_tickers:
    print(f"\n{ticker}:")
    is_valid, reason = analyzer.validate_ticker_with_ai(ticker)

    if is_valid:
        print(f"  ✅ VALID: {reason}")
        valid_count += 1
    else:
        print(f"  ❌ INVALID: {reason}")
        invalid_count += 1

print("\n" + "=" * 60)
print(f"Results: {valid_count} valid, {invalid_count} invalid")
print("=" * 60)
