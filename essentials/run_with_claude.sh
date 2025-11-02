#!/bin/bash
# Convenience wrapper for running analysis with Claude AI
# Usage: ./run_with_claude.sh [options]
# Example: ./run_with_claude.sh --hours 48 --articles 10

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}❌ Error: ANTHROPIC_API_KEY not set${NC}"
    echo ""
    echo "Set your Claude API key first:"
    echo "  export ANTHROPIC_API_KEY='sk-ant-api03-xxxxx'"
    echo ""
    echo "Get your key from: https://console.anthropic.com/account/keys"
    exit 1
fi

# Default parameters
TICKERS_FILE="${TICKERS_FILE:-all.txt}"
HOURS_BACK="${HOURS_BACK:-48}"
MAX_ARTICLES="${MAX_ARTICLES:-10}"
MODEL="${ANTHROPIC_MODEL:-claude-3-5-sonnet-20240620}"
OUTPUT_FILE="${OUTPUT_FILE:-realtime_ai_rankings_claude.csv}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tickers|-t)
            TICKERS_FILE="$2"
            shift 2
            ;;
        --hours|-h)
            HOURS_BACK="$2"
            shift 2
            ;;
        --articles|-a)
            MAX_ARTICLES="$2"
            shift 2
            ;;
        --output|-o)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --model|-m)
            ANTHROPIC_MODEL="$2"
            export ANTHROPIC_MODEL
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --tickers, -t FILE    Ticker file (default: all.txt)"
            echo "  --hours, -h NUM       Hours back (default: 48)"
            echo "  --articles, -a NUM    Max articles per ticker (default: 10)"
            echo "  --output, -o FILE     Output CSV file (default: realtime_ai_rankings_claude.csv)"
            echo "  --model, -m MODEL     Claude model (default: claude-3-5-sonnet-20240620)"
            echo "  --help                Show this help"
            echo ""
            echo "Available models:"
            echo "  claude-3-5-sonnet-20240620  (default, balanced)"
            echo "  claude-3-opus-20240229      (most capable, slower)"
            echo "  claude-3-haiku-20240307     (fastest, cheapest)"
            echo ""
            echo "Examples:"
            echo "  $0                           # Run with defaults"
            echo "  $0 --hours 24 --articles 5   # Quick scan"
            echo "  $0 --model claude-3-opus-20240229  # Use Opus"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Display configuration
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🤖 Running with Claude AI${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Configuration:"
echo "  Model:        $MODEL"
echo "  Tickers:      $TICKERS_FILE"
echo "  Hours back:   $HOURS_BACK"
echo "  Max articles: $MAX_ARTICLES"
echo "  Output:       $OUTPUT_FILE"
echo ""
echo -e "${YELLOW}Starting analysis...${NC}"
echo ""

# Run the analyzer
python3 realtime_ai_news_analyzer.py \
    --tickers-file "$TICKERS_FILE" \
    --hours-back "$HOURS_BACK" \
    --max-articles "$MAX_ARTICLES" \
    --ai-provider claude \
    --verify-internet \
    --output "$OUTPUT_FILE" \
    "$@"

# Check if output exists and display summary
if [ -f "$OUTPUT_FILE" ]; then
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Analysis complete!${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Results saved to: $OUTPUT_FILE"
    echo ""

    # Count qualified stocks
    QUALIFIED_COUNT=$(tail -n +2 "$OUTPUT_FILE" | wc -l)
    echo "Qualified stocks: $QUALIFIED_COUNT"

    # Show top 5 opportunities
    if [ $QUALIFIED_COUNT -gt 0 ]; then
        echo ""
        echo "Top 5 opportunities:"
        echo ""
        head -6 "$OUTPUT_FILE" | column -t -s','
    fi

    echo ""
    echo "View full results:"
    echo "  cat $OUTPUT_FILE"
    echo ""
    echo "Filter high-confidence (≥70%):"
    echo "  cat $OUTPUT_FILE | awk -F',' 'NR==1 || \$4>=70' | column -t -s','"
    echo ""
else
    echo -e "${RED}❌ Output file not created. Check logs for errors.${NC}"
    exit 1
fi
