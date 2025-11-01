#!/bin/bash
# Claude Setup Verification Script
# Usage: ./check_claude_setup.sh

set -e

echo "🔍 Checking Claude AI Provider Setup..."
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check 1: API Key
echo -n "1. Checking ANTHROPIC_API_KEY... "
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}❌ NOT SET${NC}"
    echo -e "${YELLOW}   Solution: export ANTHROPIC_API_KEY='sk-ant-api03-xxxxx'${NC}"
    exit 1
else
    echo -e "${GREEN}✅ SET${NC}"
    KEY_PREFIX=$(echo $ANTHROPIC_API_KEY | cut -c1-15)
    echo "   Key prefix: ${KEY_PREFIX}..."
fi

# Check 2: Python dependencies
echo -n "2. Checking Python requests library... "
if python3 -c "import requests" 2>/dev/null; then
    echo -e "${GREEN}✅ INSTALLED${NC}"
else
    echo -e "${RED}❌ MISSING${NC}"
    echo -e "${YELLOW}   Solution: pip3 install requests${NC}"
    exit 1
fi

# Check 3: API connectivity
echo -n "3. Testing Claude API connectivity... "
API_TEST=$(python3 -c "
import os, requests, json, sys
api_key = os.getenv('ANTHROPIC_API_KEY')
headers = {
    'x-api-key': api_key,
    'anthropic-version': '2023-06-01',
    'content-type': 'application/json'
}
data = {
    'model': 'claude-3-5-sonnet-20240620',
    'max_tokens': 50,
    'messages': [{'role': 'user', 'content': 'Return only the word OK'}]
}
try:
    r = requests.post('https://api.anthropic.com/v1/messages', headers=headers, json=data, timeout=10)
    if r.status_code == 200:
        print('OK')
        sys.exit(0)
    else:
        print(f'ERROR:{r.status_code}')
        sys.exit(1)
except Exception as e:
    print(f'FAILED:{str(e)}')
    sys.exit(1)
" 2>&1)

if echo "$API_TEST" | grep -q "^OK"; then
    echo -e "${GREEN}✅ WORKING${NC}"
elif echo "$API_TEST" | grep -q "ERROR:401"; then
    echo -e "${RED}❌ INVALID API KEY${NC}"
    echo -e "${YELLOW}   Get a new key: https://console.anthropic.com/account/keys${NC}"
    exit 1
elif echo "$API_TEST" | grep -q "ERROR:429"; then
    echo -e "${YELLOW}⚠️  RATE LIMITED${NC}"
    echo "   API is working but you've hit rate limits. Wait a bit."
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "   Error: $API_TEST"
    echo -e "${YELLOW}   Check internet connection and API key${NC}"
    exit 1
fi

# Check 4: Provider selection
echo -n "4. Testing provider selection logic... "
PROVIDER_TEST=$(python3 -c "
import os, sys
os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', 'test')
try:
    from realtime_ai_news_analyzer import AIModelClient
    client = AIModelClient(provider='auto')
    if client.selected_provider == 'claude':
        print('CLAUDE')
        sys.exit(0)
    else:
        print(f'WRONG:{client.selected_provider}')
        sys.exit(1)
except Exception as e:
    print(f'ERROR:{str(e)}')
    sys.exit(1)
" 2>&1)

if echo "$PROVIDER_TEST" | grep -q "^CLAUDE"; then
    echo -e "${GREEN}✅ CORRECT${NC}"
    echo "   Auto-detection selects Claude ✓"
else
    echo -e "${RED}❌ FAILED${NC}"
    echo "   Error: $PROVIDER_TEST"
    exit 1
fi

# Check 5: Main analyzer file
echo -n "5. Checking main analyzer file... "
if [ -f "realtime_ai_news_analyzer.py" ]; then
    if grep -q "_call_claude" realtime_ai_news_analyzer.py; then
        echo -e "${GREEN}✅ FOUND${NC}"
    else
        echo -e "${RED}❌ MISSING CLAUDE FUNCTION${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ FILE NOT FOUND${NC}"
    echo -e "${YELLOW}   Run this script from /home/vagrant/Govt/essentials/${NC}"
    exit 1
fi

# Check 6: Ticker files
echo -n "6. Checking ticker files... "
if [ -f "all.txt" ]; then
    TICKER_COUNT=$(wc -l < all.txt)
    echo -e "${GREEN}✅ FOUND${NC}"
    echo "   $TICKER_COUNT tickers available"
else
    echo -e "${YELLOW}⚠️  all.txt not found${NC}"
    echo "   Using NSE tickers from sec_list.csv"
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}🚀 Claude is READY TO USE!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Quick commands:"
echo ""
echo "# Run with Claude (small test)"
echo "python3 realtime_ai_news_analyzer.py --ai-provider claude --tickers-file all.txt --hours-back 24 --max-articles 5"
echo ""
echo "# Run optimal scan (auto-detects Claude)"
echo "./optimal_scan_config.sh"
echo ""
echo "# Run swing path with Claude"
echo "python3 run_swing_paths.py --path ai --top 50 --fresh --hours 48"
echo ""
echo "Configuration:"
echo "  Model: ${ANTHROPIC_MODEL:-claude-3-5-sonnet-20240620 (default)}"
echo "  Temperature: ${ANTHROPIC_TEMPERATURE:-0.2 (default)}"
echo "  Max Tokens: ${ANTHROPIC_MAX_TOKENS:-1200 (default)}"
echo "  Timeout: ${ANTHROPIC_TIMEOUT:-90s (default)}"
echo ""
echo "For help: cat CLAUDE_QUICKSTART.md"
