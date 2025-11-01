#!/bin/bash
#
# REAL-TIME AI ANALYSIS RUNNER
# Fetches news and analyzes INSTANTLY with Claude/Codex AI + Frontier AI
# Each article scored and ranked in real-time
#

set -e

cd /home/vagrant/R/essentials

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                            ║"
echo "║       🤖 REAL-TIME AI NEWS ANALYZER                                        ║"
echo "║                                                                            ║"
echo "║       Instant analysis • Claude/Codex AI • Live ranking                    ║"
echo "║                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Configuration
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="realtime_ai_analysis_${TIMESTAMP}.csv"
LOG_FILE="realtime_ai_${TIMESTAMP}.log"

# Default to NIFTY50 unless overridden
TICKERS_FILE="${1:-nifty50_tickers.txt}"
HOURS_BACK="${2:-12}"
TOP_N="${3:-2999}"

# Optional 4th arg to choose AI provider (auto|heuristic|codex|claude|cursor)
if [ -n "${4:-}" ]; then
  AI_PROVIDER="$4"
fi

# AI usage controls (optimize to avoid exhaustion)
AI_PROVIDER="${AI_PROVIDER:-auto}"
AI_MAX_CALLS="${AI_MAX_CALLS:-15}"

# Two-stage scan tuning
TOP_FOCUS="${TOP_FOCUS:-15}"              # Refine top N with external AI (legacy; unused when targeting all with news)
MAX_ARTICLES_STAGE1="${MAX_ARTICLES_STAGE1:-10}"  # Heuristic pass articles/ticker
MAX_ARTICLES_STAGE2="${MAX_ARTICLES_STAGE2:-3}"   # External AI pass articles/ticker
STAGE2_BATCH_SIZE="${STAGE2_BATCH_SIZE:-5}"       # Process 5 tickers at a time in Stage 2

# Optional internet/AI enforcement for Stage 2
EXTRA_NET_ARGS=""
if [ -n "${VERIFY_INTERNET:-}" ]; then
  EXTRA_NET_ARGS+=" --verify-internet"
fi
if [ -n "${REQUIRE_INTERNET_AI:-}" ]; then
  EXTRA_NET_ARGS+=" --require-internet-ai"
fi
if [ -n "${VERIFY_AGENT_INTERNET:-}" ]; then
  EXTRA_NET_ARGS+=" --probe-agent"
fi
if [ -n "${REQUIRE_AGENT_INTERNET:-}" ]; then
  EXTRA_NET_ARGS+=" --require-agent-internet"
fi

# High-quality Indian finance sources (mirror optimal_scan_config.sh)
SOURCES=(
  reuters.com
  livemint.com
  economictimes.indiatimes.com
  business-standard.com
  moneycontrol.com
  thehindubusinessline.com
  financialexpress.com
  cnbctv18.com
  zeebiz.com
)

echo "📋 Configuration:"
echo "   Tickers file:      $TICKERS_FILE"
echo "   Hours back:        $HOURS_BACK"
echo "   Stage1 articles:   $MAX_ARTICLES_STAGE1"
echo "   Stage2 articles:   $MAX_ARTICLES_STAGE2"
echo "   Refine top:        $TOP_FOCUS (legacy)"
echo "   AI provider:       $AI_PROVIDER"
echo "   AI max calls:      $AI_MAX_CALLS"
echo "   Sources:           ${SOURCES[*]}"
echo "   Final output:      $OUTPUT_FILE"
echo ""
echo "🤖 AI Bridge Status:"
if [ "$AI_PROVIDER" = "codex" ] || [ "$AI_PROVIDER" = "cursor" ] || [ "$AI_PROVIDER" = "auto" ]; then
  if [ -n "${CODEX_SHELL_CMD:-}" ] || [ -n "${CURSOR_SHELL_CMD:-}" ] || [ -n "${AI_SHELL_CMD:-}" ]; then
    echo "   ✅ AI shell bridge configured"
    [ -n "${CODEX_SHELL_CMD:-}" ] && echo "      CODEX_SHELL_CMD: $CODEX_SHELL_CMD"
    [ -n "${CURSOR_SHELL_CMD:-}" ] && echo "      CURSOR_SHELL_CMD: $CURSOR_SHELL_CMD"
    [ -n "${AI_SHELL_CMD:-}" ] && echo "      AI_SHELL_CMD: $AI_SHELL_CMD"
    [ -n "${REQUIRE_AGENT_INTERNET:-}" ] && echo "      Internet validation: ENABLED ✅"
  else
    echo "   ⚠️  No AI shell bridge configured"
    echo "      To enable: export CODEX_SHELL_CMD='python3 codex_bridge.py'"
    echo "      Will fall back to heuristic analysis"
  fi
else
  echo "   ℹ️  Using provider: $AI_PROVIDER"
fi
echo ""

# Verify prerequisites
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📋 Verifying Prerequisites"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

python3 --version || { echo "❌ Python 3 not found"; exit 1; }

if [ ! -f "realtime_ai_news_analyzer.py" ]; then
    echo "❌ realtime_ai_news_analyzer.py not found"
    exit 1
fi

if [ ! -f "$TICKERS_FILE" ]; then
    echo "❌ Tickers file not found: $TICKERS_FILE"
    exit 1
fi

echo "✅ All prerequisites satisfied"
echo ""

################################################################################
# Two-stage analysis to optimize AI usage
# Stage 1: Heuristic-only scan for all tickers → coarse ranking
# Stage 2: External AI on top N from Stage 1 → refined ranking
################################################################################

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Stage 1: Heuristic scan for all tickers"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏱️  Started at: $(date)"
echo ""

STAGE1_OUTPUT="realtime_ai_stage1_${TIMESTAMP}.csv"

python3 realtime_ai_news_analyzer.py \
    --tickers-file "$TICKERS_FILE" \
    --hours-back "$HOURS_BACK" \
    --max-articles "$MAX_ARTICLES_STAGE1" \
    --output "$STAGE1_OUTPUT" \
    --top "$TOP_N" \
    --ai-provider heuristic \
    --sources "${SOURCES[@]}" \
    2>&1 | tee "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ Stage 1 failed with exit code: $EXIT_CODE"
    echo "📋 Check log: $LOG_FILE"
    exit 1
fi

if [ ! -f "$STAGE1_OUTPUT" ]; then
    echo "❌ Stage 1 output file not created"
    exit 1
fi

echo ""
echo "📈 Selecting ALL tickers with news for Stage 2 (external AI)"

# Extract all tickers that appear in Stage 1 results (i.e., with news)
TOP_TICKERS=$(python3 - "$STAGE1_OUTPUT" <<'PY'
import csv, sys
path = sys.argv[1]
tickers = []
with open(path, newline='') as f:
    r = csv.reader(f)
    header = next(r, None)
    for row in r:
        if len(row) > 1:
            t = (row[1] or '').strip()
            if t and t not in tickers:
                tickers.append(t)
print(' '.join(tickers))
PY
)

if [ -z "$TOP_TICKERS" ]; then
    echo "⚠️  No tickers with news derived from Stage 1; skipping Stage 2"
else
    echo "🎯 Stage 2 targets (with news): $TOP_TICKERS"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🤖 Stage 2: External AI on top selections"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "⏱️  Started at: $(date)"
echo ""

if [ -n "$TOP_TICKERS" ]; then
  python3 realtime_ai_news_analyzer.py \
      --tickers $TOP_TICKERS \
      --hours-back "$HOURS_BACK" \
      --max-articles "$MAX_ARTICLES_STAGE2" \
      --output "$OUTPUT_FILE" \
      --top "$TOP_N" \
      --max-ai-calls "$AI_MAX_CALLS" \
      --ai-provider "$AI_PROVIDER" \
      --batch-size "$STAGE2_BATCH_SIZE" \
      $EXTRA_NET_ARGS \
      --sources "${SOURCES[@]}" \
      2>&1 | tee -a "$LOG_FILE"

  EXIT_CODE=${PIPESTATUS[0]}
else
  EXIT_CODE=0
fi

echo ""
echo "⏱️  Completed at: $(date)"
echo ""

# Verify output
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Verifying Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $EXIT_CODE -ne 0 ]; then
    echo "❌ Analysis failed with exit code: $EXIT_CODE"
    echo "📋 Check log: $LOG_FILE"
    exit 1
fi

if [ ! -f "$OUTPUT_FILE" ]; then
    echo "❌ Output file not created"
    exit 1
fi

echo "✅ Output file: $OUTPUT_FILE"
echo ""

# Display top picks
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🏆 TOP 10 PICKS (Real-time AI Analysis)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

head -11 "$OUTPUT_FILE" | tail -10

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ REAL-TIME ANALYSIS COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Files Generated:"
echo "   • Results: $OUTPUT_FILE"
echo "   • Log:     $LOG_FILE"
echo ""
echo "🎯 Each news article was analyzed INSTANTLY with:"
echo "   • Claude/Codex AI with internet access"
echo "   • Frontier AI + Quant scoring"
echo "   • Real-time ranking updates"
echo ""
echo "🚀 Analysis complete!"
echo ""

exit 0
