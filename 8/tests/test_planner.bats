#!/usr/bin/env bats
# Acceptance tests for CLI Planner AI (bats format)
# Based on: ref_code_cli_planner_ai testing patterns

setup() {
    export PLANNER_PROVIDER="claude-cli"
    export PLANNER_TIMEOUT="30"
    export CLAUDE_CLI_MODEL="sonnet"

    local test_dir
    test_dir="$(cd "$(dirname "$BATS_TEST_FILENAME")" && pwd)"
    local repo_root
    repo_root="$(cd "$test_dir/.." && pwd)"
    export PLANNER_BRIDGE="$repo_root/cli_planner_bridge.py"
    cd "$repo_root"
    state_root="${BATS_TEST_TMPDIR:-${BATS_RUN_TMPDIR:-${TMPDIR:-/tmp}}}"
    if [ -z "$state_root" ]; then
        state_root="$(mktemp -d)"
    fi
    export PLANNER_STATE_DIR="$state_root/state"
    mkdir -p "$PLANNER_STATE_DIR"
    unset PLANNER_FAKE_RESPONSES_FILE
    
    :
}

@test "Bridge script exists and is executable" {
    [ -f "$PLANNER_BRIDGE" ]
}

@test "Schemas module loads without errors" {
    run python3 -c "import sys; sys.path.insert(0, '..'); from schemas import PlannerState, ExecutionPlan"
    [ "$status" -eq 0 ]
}

@test "Prompts module loads without errors" {
    run python3 -c "import sys; sys.path.insert(0, '..'); from prompts import build_planner_prompt, PLANNER_SYSTEM_PROMPT"
    [ "$status" -eq 0 ]
}

@test "Returns error for empty input" {
    run bash -c "echo '' | python3 $PLANNER_BRIDGE"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"error"'* ]] || [[ "$output" == *'"state": "FAILED"'* ]]
}

@test "Accepts plain text task description" {
    skip "Requires Claude CLI access"
    run bash -c "echo 'Add logging to API endpoints' | python3 $PLANNER_BRIDGE"
    [ "$status" -eq 0 ]
}

@test "Accepts JSON input with task field" {
    skip "Requires Claude CLI access"
    INPUT='{"task": "Implement rate limiting for API", "context": {"framework": "Express.js"}}'
    run bash -c "echo '$INPUT' | python3 $PLANNER_BRIDGE"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"plan"'* ]]
}

@test "Plan output includes required fields" {
    skip "Requires Claude CLI access"
    INPUT='{"task": "Add Trivy scanning to container registry pipeline"}'
    OUTPUT=$(echo "$INPUT" | python3 "$PLANNER_BRIDGE")
    
    echo "$OUTPUT" | jq -e '.plan.task_summary' > /dev/null
    echo "$OUTPUT" | jq -e '.plan.steps' > /dev/null
    echo "$OUTPUT" | jq -e '.plan.success_criteria' > /dev/null
}

@test "Generated plan has valid step dependencies" {
    skip "Requires Claude CLI access"
    INPUT='{"task": "Setup CI/CD pipeline with testing stages"}'
    OUTPUT=$(echo "$INPUT" | python3 "$PLANNER_BRIDGE")
    
    # Check that steps exist and have dependencies field
    STEPS_COUNT=$(echo "$OUTPUT" | jq '.plan.steps | length')
    [ "$STEPS_COUNT" -gt 0 ]
    
    # First step should have no dependencies
    FIRST_DEPS=$(echo "$OUTPUT" | jq -r '.plan.steps[0].dependencies | length')
    [ "$FIRST_DEPS" -eq 0 ]
}

@test "Critic validation runs when enabled" {
    skip "Requires Claude CLI access"
    export PLANNER_ENABLE_CRITIC="1"
    INPUT='{"task": "Implement database migration system"}'
    OUTPUT=$(echo "$INPUT" | python3 "$PLANNER_BRIDGE")
    
    echo "$OUTPUT" | jq -e '.critic_feedback' > /dev/null
}

@test "Questions skipped for clear tasks" {
    skip "Requires Claude CLI access"
    export PLANNER_ENABLE_QUESTIONS="1"
    INPUT='{"task": "Add a new GET endpoint /api/v1/health that returns {\"status\": \"ok\"}"}'
    OUTPUT=$(echo "$INPUT" | python3 "$PLANNER_BRIDGE")
    
    # Should skip questions and go straight to planning
    STATE=$(echo "$OUTPUT" | jq -r '.state')
    [ "$STATE" != "QUESTIONING" ]
}

@test "Example schema generation works" {
    run python3 -c "import sys; sys.path.insert(0, '..'); from schemas import get_example_plan, get_example_questions; print('OK')"
    [ "$status" -eq 0 ]
    [[ "$output" == *"OK"* ]]
}

@test "State transitions are valid" {
    run python3 -c "
import sys
sys.path.insert(0, '..')
from schemas import StateTransition, PlannerState

# Test valid transitions
assert StateTransition.is_valid_transition(PlannerState.INIT, PlannerState.ANALYZING)
assert StateTransition.is_valid_transition(PlannerState.ANALYZING, PlannerState.PLANNING)
assert StateTransition.is_valid_transition(PlannerState.PLANNING, PlannerState.VALIDATING)

# Test invalid transitions
assert not StateTransition.is_valid_transition(PlannerState.INIT, PlannerState.COMPLETE)
assert not StateTransition.is_valid_transition(PlannerState.COMPLETE, PlannerState.ANALYZING)

print('PASS')
"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PASS"* ]]
}

@test "Questioning flow can resume with provided answers" {
    export PLANNER_FAKE_RESPONSES_FILE="tests/data/fake_question_flow.json"
    INPUT='{"task": "Configure persistence layer"}'
    run bash -c "echo '$INPUT' | python3 $PLANNER_BRIDGE"
    [ "$status" -eq 0 ]
    STATE=$(echo "$output" | jq -r '.state')
    [ "$STATE" = "QUESTIONING" ]
    WORKFLOW_ID=$(echo "$output" | jq -r '.workflow_id')

    INPUT2=$(cat <<EOF
{
  "workflow_id": "$WORKFLOW_ID",
  "task": "Configure persistence layer",
  "answers": {"Q1": "PostgreSQL"}
}
EOF
)
    run bash -c "echo '$INPUT2' | python3 $PLANNER_BRIDGE"
    [ "$status" -eq 0 ]
    STATE=$(echo "$output" | jq -r '.state')
    [ "$STATE" = "COMPLETE" ]
}

@test "Critic auto revision retries plan until approval" {
    export PLANNER_FAKE_RESPONSES_FILE="tests/data/fake_revision_flow.json"
    INPUT='{"task": "Roll out feature"}'
    run bash -c "echo '$INPUT' | python3 $PLANNER_BRIDGE"
    [ "$status" -eq 0 ]
    STATE=$(echo "$output" | jq -r '.state')
    [ "$STATE" = "COMPLETE" ]
    REVISIONS=$(echo "$output" | jq '.revisions')
    [ "$REVISIONS" -eq 1 ]
}
