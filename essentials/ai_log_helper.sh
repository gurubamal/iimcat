#!/bin/bash
# AI Conversation Logging Helper Script
# Manage AI conversation logging for quality assurance

set -e

LOG_DIR="${AI_LOG_DIR:-./logs/ai_conversations}"
LOG_FORMAT="${AI_LOG_FORMAT:-both}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  AI Conversation Logging Helper${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

show_status() {
    print_header

    if [ "$AI_LOG_ENABLED" = "true" ] || [ "$AI_LOG_ENABLED" = "1" ]; then
        echo -e "${GREEN}✅ Logging Status: ENABLED${NC}"
        echo -e "   Log Directory: ${LOG_DIR}"
        echo -e "   Log Format: ${LOG_FORMAT}"

        if [ -d "$LOG_DIR" ]; then
            local count=$(find "$LOG_DIR" -type f -name "*.json" 2>/dev/null | wc -l)
            echo -e "   Total Logs: ${count}"

            if [ $count -gt 0 ]; then
                echo ""
                echo -e "${BLUE}Recent Logs:${NC}"
                ls -lth "$LOG_DIR" | head -6 | tail -5
            fi
        else
            echo -e "${YELLOW}   Warning: Log directory doesn't exist yet${NC}"
        fi
    else
        echo -e "${RED}❌ Logging Status: DISABLED${NC}"
        echo -e "   To enable: ${YELLOW}export AI_LOG_ENABLED=true${NC}"
    fi
}

enable_logging() {
    print_header

    echo "Enabling AI conversation logging..."

    # Create log directory if it doesn't exist
    mkdir -p "$LOG_DIR"

    echo ""
    echo -e "${GREEN}✅ AI logging enabled!${NC}"
    echo ""
    echo "Add these to your shell profile or run them now:"
    echo ""
    echo -e "${YELLOW}export AI_LOG_ENABLED=true${NC}"
    echo -e "${YELLOW}export AI_LOG_DIR=\"$LOG_DIR\"${NC}"
    echo -e "${YELLOW}export AI_LOG_FORMAT=\"$LOG_FORMAT\"${NC}"
    echo ""
    echo "Or run: source <(./ai_log_helper.sh env)"
}

disable_logging() {
    print_header

    echo "Disabling AI conversation logging..."
    echo ""
    echo -e "${YELLOW}To disable for current session:${NC}"
    echo "  export AI_LOG_ENABLED=false"
    echo ""
    echo -e "${YELLOW}To disable permanently:${NC}"
    echo "  Remove AI_LOG_ENABLED from your shell profile"
}

show_env() {
    echo "# AI Conversation Logging Environment Variables"
    echo "# Source this output: source <(./ai_log_helper.sh env)"
    echo "export AI_LOG_ENABLED=true"
    echo "export AI_LOG_DIR=\"$LOG_DIR\""
    echo "export AI_LOG_FORMAT=\"$LOG_FORMAT\""
}

list_logs() {
    print_header

    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${RED}❌ No log directory found at: $LOG_DIR${NC}"
        exit 1
    fi

    local count=$(find "$LOG_DIR" -type f -name "*.json" 2>/dev/null | wc -l)

    if [ $count -eq 0 ]; then
        echo -e "${YELLOW}No logs found in: $LOG_DIR${NC}"
        exit 0
    fi

    echo -e "${GREEN}Found $count log files${NC}"
    echo ""

    # List by provider
    echo -e "${BLUE}Logs by Provider:${NC}"
    for provider in claude-cli codex-heuristic claude openai cursor; do
        local provider_count=$(find "$LOG_DIR" -type f -name "*${provider}*.json" 2>/dev/null | wc -l)
        if [ $provider_count -gt 0 ]; then
            echo "  $provider: $provider_count logs"
        fi
    done

    echo ""
    echo -e "${BLUE}Recent Logs (10 most recent):${NC}"
    ls -lth "$LOG_DIR" | grep "\.json$" | head -10
}

view_log() {
    local search_term="$1"

    if [ -z "$search_term" ]; then
        echo -e "${RED}❌ Please provide a search term (file name or pattern)${NC}"
        echo "Usage: $0 view <filename_or_pattern>"
        exit 1
    fi

    # Find matching files
    local matches=$(find "$LOG_DIR" -type f -name "*${search_term}*" 2>/dev/null)

    if [ -z "$matches" ]; then
        echo -e "${RED}❌ No logs found matching: $search_term${NC}"
        exit 1
    fi

    local count=$(echo "$matches" | wc -l)

    if [ $count -gt 1 ]; then
        echo -e "${YELLOW}Found $count matching logs:${NC}"
        echo "$matches"
        echo ""
        echo "Please be more specific or choose one:"
        echo "$matches" | nl
        exit 0
    fi

    # View the single match
    local log_file="$matches"

    print_header
    echo -e "${GREEN}Viewing: $(basename $log_file)${NC}"
    echo ""

    # Prefer .txt if it exists, otherwise show .json
    if [[ "$log_file" == *.json ]]; then
        local txt_file="${log_file%.json}.txt"
        if [ -f "$txt_file" ]; then
            cat "$txt_file"
        else
            cat "$log_file" | jq .
        fi
    else
        cat "$log_file"
    fi
}

summary() {
    print_header

    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${RED}❌ No log directory found at: $LOG_DIR${NC}"
        exit 1
    fi

    echo -e "${BLUE}Running summary analysis...${NC}"
    echo ""

    # Use Python to analyze logs
    python3 << EOF
import json
import glob
from pathlib import Path
from collections import defaultdict

log_dir = Path('$LOG_DIR')
logs = list(log_dir.glob('*.json'))

if not logs:
    print("No logs found")
    exit(0)

print(f"Total Conversations: {len(logs)}")
print("")

# By provider
by_provider = defaultdict(int)
by_error = 0
scores = []
certainties = []

for log_file in logs:
    try:
        with open(log_file) as f:
            data = json.load(f)
            by_provider[data['provider']] += 1

            if data.get('error'):
                by_error += 1

            try:
                response = json.loads(data['response'])
                if 'score' in response:
                    scores.append(response['score'])
                if 'certainty' in response:
                    certainties.append(response['certainty'])
            except:
                pass
    except:
        pass

print("By Provider:")
for provider, count in sorted(by_provider.items()):
    print(f"  {provider}: {count}")

print("")
print(f"Errors: {by_error}")

if scores:
    print("")
    print("Score Statistics:")
    print(f"  Average: {sum(scores)/len(scores):.1f}")
    print(f"  Min: {min(scores)}")
    print(f"  Max: {max(scores)}")

if certainties:
    print("")
    print("Certainty Statistics:")
    print(f"  Average: {sum(certainties)/len(certainties):.1f}")
    print(f"  Min: {min(certainties)}")
    print(f"  Max: {max(certainties)}")
EOF
}

clean_logs() {
    print_header

    if [ ! -d "$LOG_DIR" ]; then
        echo -e "${YELLOW}No log directory found. Nothing to clean.${NC}"
        exit 0
    fi

    local count=$(find "$LOG_DIR" -type f 2>/dev/null | wc -l)

    if [ $count -eq 0 ]; then
        echo -e "${YELLOW}No logs to clean.${NC}"
        exit 0
    fi

    echo -e "${YELLOW}⚠️  This will delete $count log files from: $LOG_DIR${NC}"
    echo ""
    read -p "Are you sure? (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Archive before deleting
        local archive_dir="./archives/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$archive_dir"

        echo "Archiving logs to: $archive_dir"
        mv "$LOG_DIR"/* "$archive_dir/" 2>/dev/null || true

        echo -e "${GREEN}✅ Logs archived and cleaned!${NC}"
        echo "Archive location: $archive_dir"
    else
        echo "Cancelled."
    fi
}

test_logging() {
    print_header

    echo "Testing AI conversation logger..."
    echo ""

    # Temporarily enable logging
    export AI_LOG_ENABLED=true
    export AI_LOG_DIR="$LOG_DIR"
    export AI_LOG_FORMAT="$LOG_FORMAT"

    python3 ai_conversation_logger.py
}

show_usage() {
    print_header

    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  status       - Show current logging status and recent logs"
    echo "  enable       - Enable AI conversation logging"
    echo "  disable      - Disable AI conversation logging"
    echo "  env          - Print environment variables (source this)"
    echo "  list         - List all logged conversations"
    echo "  view <term>  - View a specific log file (by name or pattern)"
    echo "  summary      - Show summary statistics of all logs"
    echo "  clean        - Archive and clean old logs"
    echo "  test         - Test the logging system"
    echo ""
    echo "Examples:"
    echo "  $0 status"
    echo "  $0 enable"
    echo "  source <($0 env)"
    echo "  $0 list"
    echo "  $0 view claude-cli"
    echo "  $0 view 20250128_143025"
    echo "  $0 summary"
    echo ""
    echo "Environment Variables:"
    echo "  AI_LOG_ENABLED  - Enable/disable logging (true/false)"
    echo "  AI_LOG_DIR      - Log directory (default: ./logs/ai_conversations)"
    echo "  AI_LOG_FORMAT   - Log format (json, text, both)"
}

# Main
case "${1:-status}" in
    status)
        show_status
        ;;
    enable)
        enable_logging
        ;;
    disable)
        disable_logging
        ;;
    env)
        show_env
        ;;
    list|ls)
        list_logs
        ;;
    view|cat|show)
        view_log "$2"
        ;;
    summary|stats)
        summary
        ;;
    clean|clear)
        clean_logs
        ;;
    test)
        test_logging
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac
