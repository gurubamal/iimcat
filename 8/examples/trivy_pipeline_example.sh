#!/bin/bash
# Worked Example: Using CLI Planner AI for Trivy Pipeline Integration
# =====================================================================

set -e

PLANNER_BRIDGE="$(dirname "$0")/../cli_planner_bridge.py"

echo "========================================================================"
echo "CLI PLANNER AI - Worked Example: Trivy Vulnerability Scanning"
echo "========================================================================"

# Example 1: Basic task
echo -e "\n📋 Example 1: Clear, well-defined task\n"

TASK1='{"task": "Add Trivy vulnerability scanning to Docker build pipeline. Block deployment if CRITICAL vulnerabilities found.", "context": {"ci_system": "GitHub Actions", "registry": "AWS ECR"}}'

echo "Task: Add Trivy to pipeline"
echo "Expected: Should skip questions and generate plan directly"
echo ""

# Example would call: echo "$TASK1" | python3 "$PLANNER_BRIDGE"

echo "✅ This example demonstrates the complete workflow"
echo ""
