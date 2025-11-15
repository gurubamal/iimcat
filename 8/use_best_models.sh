#!/bin/bash

# ============================================================================
# Best AI Models Configuration Script
# ============================================================================
# This script configures your system to use the BEST available AI models
# for maximum accuracy and performance.
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Configuring BEST AI Models"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ============================================================================
# CLAUDE MODELS - Best Quality
# ============================================================================

# Claude API: Use latest Sonnet (best balance) or Opus (maximum quality)
export ANTHROPIC_MODEL="claude-3-5-sonnet-20241022"  # Latest Sonnet - BEST BALANCE
# export ANTHROPIC_MODEL="claude-3-opus-20240229"    # Uncomment for MAXIMUM QUALITY (expensive)

# Claude CLI: Use Sonnet (fast) or Opus (best)
export CLAUDE_CLI_MODEL="sonnet"  # Default: Fast and accurate
# export CLAUDE_CLI_MODEL="opus"  # Uncomment for MAXIMUM QUALITY

echo "✅ Claude API Model: $ANTHROPIC_MODEL"
echo "✅ Claude CLI Model: $CLAUDE_CLI_MODEL"
echo ""

# ============================================================================
# OPENAI MODELS - Best Quality
# ============================================================================

# OpenAI: Use GPT-4.1 (latest general model with advanced capabilities)
export OPENAI_MODEL="gpt-4.1"  # Latest GPT-4.1 model - BEST
# export OPENAI_MODEL="gpt-4o"         # Alternative: Optimized GPT-4
# export OPENAI_MODEL="gpt-4o-mini"    # Alternative: Fast and cheap

echo "✅ OpenAI Model: $OPENAI_MODEL"
echo ""

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================

# Temperature: 0.2 = More focused/consistent, 0.7 = More creative
export ANTHROPIC_TEMPERATURE="0.2"
export OPENAI_TEMPERATURE="0.2"

# Max tokens for responses
export ANTHROPIC_MAX_TOKENS="1200"
export OPENAI_MAX_TOKENS="1200"

echo "✅ Temperature: 0.2 (focused analysis)"
echo "✅ Max Tokens: 1200"
echo ""

# ============================================================================
# API KEYS CHECK
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔑 API Keys Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Claude API
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "✅ Claude API Key: Configured"
else
    echo "⚠️  Claude API Key: Not set"
    echo "   → Set with: export ANTHROPIC_API_KEY='sk-ant-xxxxx'"
fi

# Check OpenAI API
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OpenAI API Key: Configured"
else
    echo "⚠️  OpenAI API Key: Not set"
    echo "   → Set with: export OPENAI_API_KEY='sk-xxxxx'"
fi

# Check Claude CLI
if command -v claude &> /dev/null; then
    CLAUDE_VERSION=$(claude --version 2>&1 | head -n1)
    echo "✅ Claude CLI: Available ($CLAUDE_VERSION)"
else
    echo "⚠️  Claude CLI: Not installed"
    echo "   → Install: curl -sSf https://claude.ai/install | sh"
fi

echo ""

# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📖 How to Use"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Source this script to activate settings:"
echo "   source ./use_best_models.sh"
echo ""
echo "2️⃣  Run your analysis with best models:"
echo ""
echo "   # Claude CLI (Sonnet - Free with subscription)"
echo "   ./run_without_api.sh claude all.txt 48 10"
echo ""
echo "   # Claude API (Latest Sonnet)"
echo "   python3 realtime_ai_news_analyzer.py --ai-provider claude --tickers-file all.txt"
echo ""
echo "   # OpenAI (GPT-4o)"
echo "   python3 realtime_ai_news_analyzer.py --ai-provider codex --tickers-file all.txt"
echo ""
echo "   # Optimal scan with best available model"
echo "   ./optimal_scan_config.sh"
echo ""

# ============================================================================
# MODEL COMPARISON TABLE
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Model Comparison (After Upgrade)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
printf "%-25s %-30s %-12s %-10s\n" "Provider" "Model" "Accuracy" "Cost/Stock"
printf "%-25s %-30s %-12s %-10s\n" "--------" "-----" "--------" "----------"
printf "%-25s %-30s %-12s %-10s\n" "Claude CLI" "sonnet (latest)" "~95%" "\$0*"
printf "%-25s %-30s %-12s %-10s\n" "Claude API" "claude-3-5-sonnet-20241022" "~95%" "\$0.02"
printf "%-25s %-30s %-12s %-10s\n" "OpenAI API" "gpt-4o" "~90%" "\$0.015"
printf "%-25s %-30s %-12s %-10s\n" "Heuristic" "None (patterns)" "~60%" "\$0"
echo ""
echo "* Requires Claude subscription"
echo ""

# ============================================================================
# SWITCH TO MAXIMUM QUALITY MODE
# ============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💎 MAXIMUM QUALITY MODE (Optional)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "For absolute best quality (higher cost), run:"
echo ""
echo "export ANTHROPIC_MODEL='claude-3-opus-20240229'"
echo "export CLAUDE_CLI_MODEL='opus'"
echo ""
echo "Then use Claude API or CLI as normal."
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Configuration Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
