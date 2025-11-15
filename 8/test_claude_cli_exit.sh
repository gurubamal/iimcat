#!/bin/bash
# Quick test of Claude CLI enhanced exit bridge

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 Testing Claude CLI Enhanced Exit Bridge"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test prompt
cat << 'EOF' | python3 claude_exit_bridge.py
EXIT ASSESSMENT REQUEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STOCK: KEC (KEC International)

TECHNICAL ANALYSIS DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Price: ₹825.50
20-Day SMA: ₹930.25 (-11.3%)
50-Day SMA: ₹945.10 (-12.7%)
RSI(14): 22.8
10-Day Momentum: -15.2%
Volume Ratio (20D avg): 0.68x
Distance from 52W Low: 8.5%
ATR(14): ₹23.76 (2.9% of price)
Recent Trend (5D): down
Weekly Trend: down
Bollinger Position: -2.1 σ

NEWS HEADLINE:
Technical-only assessment (no recent news)

ARTICLE CONTENT (Full Text):
No article content available

SOURCE: N/A

TASK: Assess whether this information justifies EXITING the position.
Consider: technical deterioration + fundamental risks + sentiment shift.

Return ONLY valid JSON with the exit assessment schema.
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Test complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
