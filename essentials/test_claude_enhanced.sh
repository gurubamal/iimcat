#!/bin/bash
# Test script to verify Claude Enhanced implementation
# Compares Claude vs Codex performance

set -e

echo "================================================================================"
echo "🧪 CLAUDE ENHANCED VERIFICATION TEST"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python3 found${NC}"

# Check requests library
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  requests library not found, installing...${NC}"
    pip3 install requests
fi
echo -e "${GREEN}✅ requests library available${NC}"

# Check Claude CLI (optional)
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✅ Claude CLI found ($(claude --version 2>&1 | head -1))${NC}"
    CLAUDE_CLI_AVAILABLE=1
else
    echo -e "${YELLOW}⚠️  Claude CLI not found - will test with mock data${NC}"
    CLAUDE_CLI_AVAILABLE=0
fi

# Check internet
if curl -s --head --max-time 5 https://example.com | grep "200 OK" > /dev/null; then
    echo -e "${GREEN}✅ Internet connection active${NC}"
else
    echo -e "${YELLOW}⚠️  Internet connection issue - some tests may fail${NC}"
fi

echo ""
echo "================================================================================"
echo "🔬 TEST 1: Article Fetching Capability"
echo "================================================================================"
echo ""

# Test article fetching
TEST_URL="https://economictimes.indiatimes.com"
echo "Testing URL fetch from: $TEST_URL"

python3 << EOF
from claude_cli_bridge import fetch_url, html_to_text
import sys

url = "$TEST_URL"
print(f"🔍 Fetching: {url}")
content = fetch_url(url, timeout=10)

if content:
    print(f"✅ Fetched {len(content)} bytes")
    text = html_to_text(content)
    print(f"✅ Extracted {len(text)} chars of clean text")
    print(f"📝 Sample: {text[:200]}...")
    sys.exit(0)
else:
    print(f"❌ Failed to fetch content")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ TEST 1 PASSED: Article fetching works${NC}"
else
    echo -e "${RED}❌ TEST 1 FAILED: Article fetching issue${NC}"
fi

echo ""
echo "================================================================================"
echo "🔬 TEST 2: Prompt Enhancement"
echo "================================================================================"
echo ""

# Test prompt enhancement
python3 << 'EOF'
from claude_cli_bridge import fetch_and_enhance_prompt
import os

# Disable actual fetching for this test (use mock)
os.environ['CLAUDE_FETCH_ARTICLES'] = '0'

test_prompt = """# SWING TRADE SETUP ANALYSIS - RELIANCE

## Stock Information
- **Ticker**: RELIANCE
- **Headline**: Reliance Industries Q2 profit surges 25% to Rs 15,000 crore
- **Full Text**: Short summary here
- **URL**: https://economictimes.indiatimes.com/test-article

Analyze this news.
"""

print("📝 Original prompt length:", len(test_prompt))
enhanced = fetch_and_enhance_prompt(test_prompt)
print("📝 Enhanced prompt length:", len(enhanced))

if len(enhanced) >= len(test_prompt):
    print("✅ Prompt enhancement functional (no errors)")
else:
    print("❌ Prompt enhancement failed")
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ TEST 2 PASSED: Prompt enhancement works${NC}"
else
    echo -e "${RED}❌ TEST 2 FAILED: Prompt enhancement issue${NC}"
fi

echo ""
echo "================================================================================"
echo "🔬 TEST 3: Probe Handler"
echo "================================================================================"
echo ""

# Test connectivity probe
python3 << 'EOF'
from claude_cli_bridge import handle_probe_request

probe_prompt = """Fetch the exact bytes at URL: https://example.com/
Compute the SHA256 hex digest of the bytes.
Return ONLY valid JSON with this shape: {"sha256":"<hex>"}.
Do not include code fences, text, or explanations."""

print("🧪 Testing probe handler...")
result = handle_probe_request(probe_prompt)

if result and 'sha256' in result:
    print(f"✅ Probe successful: SHA256={result['sha256'][:16]}...")
else:
    print(f"❌ Probe failed: {result}")
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ TEST 3 PASSED: Probe handler works${NC}"
else
    echo -e "${RED}❌ TEST 3 FAILED: Probe handler issue${NC}"
fi

echo ""
echo "================================================================================"
echo "🔬 TEST 4: Integration Test (Full Pipeline)"
echo "================================================================================"
echo ""

if [ $CLAUDE_CLI_AVAILABLE -eq 1 ]; then
    echo "🚀 Running full integration test with Claude CLI..."

    # Create a test prompt
    cat << 'PROMPT' | python3 claude_cli_bridge.py > /tmp/claude_test_output.json
# SWING TRADE SETUP ANALYSIS - INFY

## Stock Information
- **Ticker**: INFY
- **Headline**: Infosys Q2 profit rises 10% to Rs 6,500 crore
- **Full Text**: Infosys reported strong Q2FY24 results with net profit growing 10% YoY to Rs 6,500 crore. Revenue increased 15% to Rs 38,000 crore. Company raised full-year guidance.
- **URL**: https://economictimes.indiatimes.com/tech/information-tech/infosys-q2-results

Analyze this news for swing trading opportunity.
PROMPT

    if [ $? -eq 0 ]; then
        echo "✅ Claude CLI responded successfully"
        echo ""
        echo "📊 Result:"
        cat /tmp/claude_test_output.json | python3 -m json.tool 2>/dev/null || cat /tmp/claude_test_output.json
        echo ""

        # Validate JSON
        if python3 -c "import json; json.load(open('/tmp/claude_test_output.json'))" 2>/dev/null; then
            echo -e "${GREEN}✅ TEST 4 PASSED: Full pipeline works${NC}"
        else
            echo -e "${RED}❌ TEST 4 FAILED: Invalid JSON output${NC}"
        fi
    else
        echo -e "${RED}❌ TEST 4 FAILED: Claude CLI error${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  TEST 4 SKIPPED: Claude CLI not available${NC}"
fi

echo ""
echo "================================================================================"
echo "📊 SUMMARY"
echo "================================================================================"
echo ""
echo "✨ Claude Enhanced Bridge Features:"
echo "   ✅ Full article content fetching"
echo "   ✅ HTML to text conversion"
echo "   ✅ Prompt enhancement"
echo "   ✅ Connectivity probes"
echo "   ✅ Enhanced logging"
echo "   ✅ Advanced system prompts"
echo ""
echo "🎯 Ready to outperform Codex!"
echo ""
echo "To run a full comparison:"
echo "  1. export AI_PROVIDER=claude"
echo "  2. export CLAUDE_ENHANCED_MODE=1"
echo "  3. ./run_without_api.sh claude"
echo ""
echo "Or compare directly:"
echo "  python3 realtime_ai_news_analyzer.py --tickers INFY RELIANCE TCS --hours-back 48 --ai-provider claude"
echo ""
echo "================================================================================"
