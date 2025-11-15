#!/bin/bash
# Test script for Claude CLI Bridge integration

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing Claude CLI Bridge Integration"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Check if Claude CLI is available
echo "Test 1: Checking Claude CLI availability..."
if command -v claude &> /dev/null; then
    echo "✅ Claude CLI found"
    claude --version 2>/dev/null || echo "  (version check not available)"
else
    echo "❌ Claude CLI not found"
    echo ""
    echo "Please install Claude Code or ensure it's in your PATH:"
    echo "  npm install -g @anthropic-ai/claude-code"
    exit 1
fi
echo ""

# Test 2: Check if bridge script exists
echo "Test 2: Checking bridge script..."
if [ -f "claude_cli_bridge.py" ]; then
    echo "✅ claude_cli_bridge.py exists"
else
    echo "❌ claude_cli_bridge.py not found"
    exit 1
fi
echo ""

# Test 3: Test bridge with sample prompt
echo "Test 3: Testing bridge with sample financial news..."
cat > /tmp/test_prompt.txt << 'EOF'
Analyze this news for stock impact:

**Company:** Reliance Industries Ltd
**Headline:** Reliance Industries secures ₹5,000 crore order for green energy project
**Source:** Economic Times
**Date:** 2025-01-27

Provide your analysis in JSON format.
EOF

echo "Sending test prompt to bridge..."
if python3 claude_cli_bridge.py < /tmp/test_prompt.txt > /tmp/claude_response.json 2>/tmp/claude_error.log; then
    echo "✅ Bridge executed successfully"
    echo ""
    echo "Response:"
    cat /tmp/claude_response.json | python3 -m json.tool 2>/dev/null || cat /tmp/claude_response.json
    echo ""

    # Validate JSON structure
    echo "Validating JSON structure..."
    if python3 -c "
import json
import sys
with open('/tmp/claude_response.json') as f:
    data = json.load(f)
required_fields = ['score', 'sentiment', 'impact', 'catalysts', 'deal_value_cr',
                   'risks', 'certainty', 'recommendation', 'reasoning',
                   'expected_move_pct', 'confidence']
missing = [f for f in required_fields if f not in data]
if missing:
    print(f'❌ Missing fields: {missing}')
    sys.exit(1)
print('✅ All required fields present')
"; then
        echo ""
    else
        echo "⚠️ JSON validation failed"
        exit 1
    fi
else
    echo "❌ Bridge execution failed"
    echo ""
    echo "Error log:"
    cat /tmp/claude_error.log
    exit 1
fi
echo ""

# Test 4: Integration test with run_without_api.sh
echo "Test 4: Testing run_without_api.sh integration..."
if [ -f "run_without_api.sh" ]; then
    echo "✅ run_without_api.sh exists"

    # Check if it has claude support
    if grep -q "claude" run_without_api.sh; then
        echo "✅ Script includes Claude support"
    else
        echo "⚠️ Script may not have Claude support"
    fi
else
    echo "⚠️ run_without_api.sh not found"
fi
echo ""

# Test 5: Environment variable setup
echo "Test 5: Testing environment variable setup..."
export CLAUDE_SHELL_CMD="python3 claude_cli_bridge.py"
export AI_PROVIDER=claude

echo "✅ Environment variables set:"
echo "   CLAUDE_SHELL_CMD=$CLAUDE_SHELL_CMD"
echo "   AI_PROVIDER=$AI_PROVIDER"
echo ""

# Clean up
rm -f /tmp/test_prompt.txt /tmp/claude_response.json /tmp/claude_error.log

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All Tests Passed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🚀 You can now run:"
echo "   ./run_without_api.sh claude all.txt 48 10"
echo ""
echo "Or for a quick test with a small ticker list:"
echo "   echo 'RELIANCE' > test_tickers.txt"
echo "   ./run_without_api.sh claude test_tickers.txt 24 3"
echo ""
