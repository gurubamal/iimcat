#!/bin/bash
# CLI Planner Runner - Convenience script for Claude CLI planner
# ================================================================
# Always uses Claude CLI (no provider selection needed)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANNER_BRIDGE="$SCRIPT_DIR/cli_planner_bridge.py"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default configuration
MODEL="${PLANNER_MODEL:-sonnet}"
TIMEOUT="${PLANNER_TIMEOUT:-120}"
ENABLE_CRITIC="${PLANNER_ENABLE_CRITIC:-1}"
ENABLE_QUESTIONS="${PLANNER_ENABLE_QUESTIONS:-1}"

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] "<task_description>"
   or: $0 [OPTIONS] --file <task_file.json>

CLI Planner AI - Always uses Claude CLI

OPTIONS:
    -m, --model MODEL          Claude model (sonnet, opus, haiku) [default: $MODEL]
    -t, --timeout SECONDS      Timeout in seconds [default: $TIMEOUT]
    --no-critic                Disable critic validation
    --no-questions             Disable questioning phase
    --auto-approve             Auto-approve high-confidence plans
    -f, --file FILE            Read task from JSON file
    -o, --output FILE          Save output to file
    -v, --verbose              Verbose output
    -h, --help                 Show this help message

EXAMPLES:
    # Basic usage
    $0 "Add Trivy scanning to CI pipeline"
    
    # Use opus model with verbose output
    $0 -m opus -v "Implement rate limiting"
    
    # From file
    $0 --file task.json --output plan.json
    
    # No critic, auto-approve
    $0 --no-critic --auto-approve "Add logging to API"

ENVIRONMENT VARIABLES:
    PLANNER_MODEL              Claude model (sonnet, opus, haiku)
    PLANNER_TIMEOUT            Timeout in seconds
    PLANNER_ENABLE_CRITIC      Enable critic (1/0)
    PLANNER_ENABLE_QUESTIONS   Enable questions (1/0)

REQUIREMENTS:
    - Claude CLI must be installed and authenticated
    - Run: claude --version to verify
EOF
}

# Parse arguments
TASK=""
INPUT_FILE=""
OUTPUT_FILE=""
VERBOSE=0
AUTO_APPROVE=0

while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --no-critic)
            ENABLE_CRITIC=0
            shift
            ;;
        --no-questions)
            ENABLE_QUESTIONS=0
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE=1
            shift
            ;;
        -f|--file)
            INPUT_FILE="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            if [[ -z "$TASK" ]]; then
                TASK="$1"
            else
                echo -e "${RED}Error: Unknown argument: $1${NC}" >&2
                usage
                exit 1
            fi
            shift
            ;;
    esac
done

# Check dependencies
if ! command -v claude &> /dev/null; then
    echo -e "${RED}Error: Claude CLI not found${NC}" >&2
    echo "Install with: pip install claude-cli" >&2
    echo "Or visit: https://github.com/anthropics/claude-cli" >&2
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 not found${NC}" >&2
    exit 1
fi

# Check if planner bridge exists
if [[ ! -f "$PLANNER_BRIDGE" ]]; then
    echo -e "${RED}Error: Planner bridge not found: $PLANNER_BRIDGE${NC}" >&2
    exit 1
fi

# Export configuration
export PLANNER_MODEL="$MODEL"
export PLANNER_TIMEOUT="$TIMEOUT"
export PLANNER_ENABLE_CRITIC="$ENABLE_CRITIC"
export PLANNER_ENABLE_QUESTIONS="$ENABLE_QUESTIONS"
export PLANNER_AUTO_APPROVE="$AUTO_APPROVE"

# Prepare input
if [[ -n "$INPUT_FILE" ]]; then
    if [[ ! -f "$INPUT_FILE" ]]; then
        echo -e "${RED}Error: Input file not found: $INPUT_FILE${NC}" >&2
        exit 1
    fi
    INPUT_JSON=$(cat "$INPUT_FILE")
elif [[ -n "$TASK" ]]; then
    INPUT_JSON=$(echo "{\"task\": \"$TASK\"}" | python3 -m json.tool)
else
    echo -e "${RED}Error: No task provided${NC}" >&2
    usage
    exit 1
fi

# Header
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}" >&2
echo -e "${GREEN}CLI Planner AI${NC}" >&2
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}" >&2
echo -e "Model: ${YELLOW}$MODEL${NC}" >&2
echo -e "Timeout: ${YELLOW}$TIMEOUT${NC}s" >&2
echo -e "Critic: ${YELLOW}$([ $ENABLE_CRITIC -eq 1 ] && echo 'enabled' || echo 'disabled')${NC}" >&2
echo -e "Questions: ${YELLOW}$([ $ENABLE_QUESTIONS -eq 1 ] && echo 'enabled' || echo 'disabled')${NC}" >&2
echo -e "${BLUE}───────────────────────────────────────────────────────────────────────────${NC}" >&2

if [[ $VERBOSE -eq 1 ]]; then
    echo "Input JSON:" >&2
    echo "$INPUT_JSON" >&2
    echo "" >&2
fi

# Run planner
RESULT=$(echo "$INPUT_JSON" | python3 "$PLANNER_BRIDGE")
EXIT_CODE=$?

if [[ $EXIT_CODE -ne 0 ]]; then
    echo -e "${RED}Error: Planner failed with exit code $EXIT_CODE${NC}" >&2
    echo "$RESULT"
    exit $EXIT_CODE
fi

# Output result
if [[ -n "$OUTPUT_FILE" ]]; then
    echo "$RESULT" > "$OUTPUT_FILE"
    echo -e "${GREEN}✓ Plan saved to: $OUTPUT_FILE${NC}" >&2
fi

# Always output to stdout
echo "$RESULT"

# Summary
echo "" >&2
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}" >&2
STATE=$(echo "$RESULT" | python3 -c "import sys, json; print(json.load(sys.stdin).get('state', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
echo -e "State: ${YELLOW}$STATE${NC}" >&2
echo -e "${BLUE}═══════════════════════════════════════════════════════════════════════════${NC}" >&2
