#!/bin/bash
# Quick scan with enhanced logging - Common use cases

show_help() {
    cat << EOF
Enhanced News Collection - Quick Logging Commands

USAGE:
    ./quick_scan.sh [mode] [options]

MODES:
    standard        Standard logging (default) - clean, progress-focused
    verbose         Verbose logging - shows rejected URLs and reasons
    diagnostic      Full diagnostic - verbose with more samples
    weekend         Weekend scan - 96 hours, verbose logging
    priority        Quick priority tickers scan (top 20)
    full            Full ticker list scan

OPTIONS:
    --tickers "T1 T2 T3"    Specific tickers to scan
    --hours N               Hours back (default: 48)
    --limit N               Limit number of tickers
    --all-news              Disable financial URL filtering
    --save-log FILE         Save output to file

EXAMPLES:
    # Standard scan with priority tickers
    ./quick_scan.sh priority

    # Verbose scan for specific tickers
    ./quick_scan.sh verbose --tickers "RELIANCE TCS INFY"

    # Weekend diagnostic scan
    ./quick_scan.sh weekend

    # Full diagnostic for single ticker
    ./quick_scan.sh diagnostic --tickers "RELIANCE"

    # Save scan output to file
    ./quick_scan.sh verbose --save-log scan_output.log

For full documentation, see: LOGGING_GUIDE.md
EOF
}

# Default values
MODE="standard"
TICKERS_FILE="all.txt"
HOURS=48
LIMIT=0
EXTRA_ARGS=""
SAVE_LOG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        standard|verbose|diagnostic|weekend|priority|full)
            MODE=$1
            shift
            ;;
        --tickers)
            TICKERS_LIST=$2
            shift 2
            ;;
        --hours)
            HOURS=$2
            shift 2
            ;;
        --limit)
            LIMIT=$2
            shift 2
            ;;
        --all-news)
            EXTRA_ARGS="$EXTRA_ARGS --all-news"
            shift
            ;;
        --save-log)
            SAVE_LOG=$2
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command based on mode
CMD="python3 enhanced_india_finance_collector.py"

case $MODE in
    standard)
        echo "🔍 Running STANDARD scan with clean logging..."
        if [ -n "$TICKERS_LIST" ]; then
            CMD="$CMD --tickers $TICKERS_LIST"
        else
            CMD="$CMD --tickers-file $TICKERS_FILE"
        fi
        CMD="$CMD --hours-back $HOURS --max-articles 5"
        ;;
    
    verbose)
        echo "🔍 Running VERBOSE scan with detailed diagnostics..."
        if [ -n "$TICKERS_LIST" ]; then
            CMD="$CMD --tickers $TICKERS_LIST"
        else
            CMD="$CMD --tickers-file $TICKERS_FILE"
        fi
        CMD="$CMD --hours-back $HOURS --max-articles 5 --verbose"
        ;;
    
    diagnostic)
        echo "🔬 Running DIAGNOSTIC scan with full details..."
        if [ -n "$TICKERS_LIST" ]; then
            CMD="$CMD --tickers $TICKERS_LIST"
        else
            CMD="$CMD --tickers-file $TICKERS_FILE --limit 10"
        fi
        CMD="$CMD --hours-back $HOURS --max-articles 10 --verbose --show-samples 5"
        ;;
    
    weekend)
        echo "🗓️  Running WEEKEND scan (96 hours)..."
        if [ -n "$TICKERS_LIST" ]; then
            CMD="$CMD --tickers $TICKERS_LIST"
        else
            CMD="$CMD --tickers-file $TICKERS_FILE"
        fi
        CMD="$CMD --hours-back 96 --max-articles 10 --verbose"
        ;;
    
    priority)
        echo "⚡ Running PRIORITY scan (top 20 tickers)..."
        CMD="$CMD --tickers-file all.txt --limit 20"
        CMD="$CMD --hours-back $HOURS --max-articles 5"
        ;;
    
    full)
        echo "📊 Running FULL scan (all tickers)..."
        CMD="$CMD --tickers-file sec_tickers.txt"
        CMD="$CMD --hours-back $HOURS --max-articles 5"
        ;;
esac

# Add limit if specified
if [ $LIMIT -gt 0 ]; then
    CMD="$CMD --limit $LIMIT"
fi

# Add extra args
CMD="$CMD $EXTRA_ARGS"

# Show command being run
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Command: $CMD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run command with optional log saving
if [ -n "$SAVE_LOG" ]; then
    echo "💾 Saving output to: $SAVE_LOG"
    $CMD 2>&1 | tee "$SAVE_LOG"
else
    $CMD
fi
