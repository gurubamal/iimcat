#!/bin/bash
# Check which AI models are configured

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 AI Model Configuration Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "1️⃣  CODEX BRIDGE (Heuristic - No AI)"
echo "   Model: None (pattern matching only)"
echo "   Status: Always available ✅"
echo ""

echo "2️⃣  CLAUDE CLI MODE"
if command -v claude &> /dev/null; then
    echo "   Status: Available ✅"
    echo "   Model: ${CLAUDE_CLI_MODEL:-sonnet (default)}"
    claude --version 2>/dev/null || echo "   CLI Version: (unknown)"
else
    echo "   Status: Not available ❌"
    echo "   Install: npm install -g @anthropic-ai/claude-code"
fi
echo ""

echo "3️⃣  CLAUDE API MODE"
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "   Status: Available ✅"
    echo "   Model: ${ANTHROPIC_MODEL:-claude-3-5-sonnet-20240620 (default)}"
    echo "   Temperature: ${ANTHROPIC_TEMPERATURE:-0.2 (default)}"
    echo "   Max Tokens: ${ANTHROPIC_MAX_TOKENS:-1200 (default)}"
else
    echo "   Status: Not configured ❌"
    echo "   Setup: export ANTHROPIC_API_KEY='sk-ant-xxxxx'"
fi
echo ""

echo "4️⃣  OPENAI API MODE"
if [ -n "$OPENAI_API_KEY" ] || [ -n "$OPENAI_KEY" ]; then
    echo "   Status: Available ✅"
    echo "   Model: ${OPENAI_MODEL:-gpt-4.1 (default)}"
    echo "   Temperature: ${OPENAI_TEMPERATURE:-0.2 (default)}"
    echo "   Max Tokens: ${OPENAI_MAX_TOKENS:-1200 (default)}"
else
    echo "   Status: Not configured ❌"
    echo "   Setup: export OPENAI_API_KEY='sk-xxxxx'"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 Usage Examples"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Heuristic (no AI):"
echo "  ./run_without_api.sh codex all.txt 48 10"
echo ""
echo "Claude CLI (Sonnet by default):"
echo "  ./run_without_api.sh claude all.txt 48 10"
echo ""
echo "Claude CLI (change to Opus):"
echo "  export CLAUDE_CLI_MODEL='opus'"
echo "  ./run_without_api.sh claude all.txt 48 10"
echo ""
echo "Claude API (with custom model):"
echo "  export ANTHROPIC_API_KEY='sk-ant-xxxxx'"
echo "  export ANTHROPIC_MODEL='claude-3-opus-20240229'"
echo "  python3 realtime_ai_news_analyzer.py --ai-provider claude --tickers-file all.txt"
echo ""
echo "OpenAI API (GPT-4 Turbo):"
echo "  export OPENAI_API_KEY='sk-xxxxx'"
echo "  export OPENAI_MODEL='gpt-4-turbo'"
echo "  python3 realtime_ai_news_analyzer.py --ai-provider codex --tickers-file all.txt"
echo ""
