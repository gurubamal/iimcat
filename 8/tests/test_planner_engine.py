#!/usr/bin/env python3
"""
PlannerEngine unit tests using a fake provider.
"""

import json

import pytest

from cli_planner_bridge import PlannerEngine, BaseLLMProvider


class StubProvider(BaseLLMProvider):
    """Simple provider that returns canned responses per phase."""

    label = "stub-provider"

    def __init__(self, responses):
        # Normalize keys to uppercase for easier matching
        self.responses = {phase.upper(): list(payloads) for phase, payloads in responses.items()}

    def complete(self, prompt: str, system_prompt: str, *, timeout: int, phase: str) -> str:
        queue = self.responses.get((phase or "DEFAULT").upper())
        if not queue:
            raise RuntimeError(f"No stub response for phase {phase}")
        payload = queue.pop(0)
        return json.dumps(payload)


def _plan_payload(summary: str) -> dict:
    """Helper to craft minimal valid plans."""
    return {
        "task_summary": summary,
        "approach": "Test approach",
        "assumptions": ["A1"],
        "steps": [
            {
                "id": "S1",
                "description": "Do work",
                "rationale": "Needed",
                "dependencies": [],
                "estimated_duration": "5 minutes",
                "validation_criteria": ["Done"],
                "risks": ["None"],
                "rollback_strategy": "Undo",
            }
        ],
        "success_criteria": ["All good"],
        "risks": ["None"],
        "estimated_total_duration": "5 minutes",
        "confidence": 90,
    }


def _critic_payload(recommendation: str, approved: bool) -> dict:
    return {
        "approved": approved,
        "confidence": 80,
        "concerns": ["Add tests"] if not approved else [],
        "suggestions": [],
        "missing_steps": [],
        "unnecessary_steps": [],
        "risk_assessment": "LOW",
        "recommendation": recommendation,
    }


def test_engine_handles_questions_and_completion(tmp_path):
    responses = {
        "ANALYZER": [
            {
                "task_clarity_score": 60,
                "technical_completeness_score": 55,
                "should_ask_questions": True,
                "identified_gaps": ["Need DB"],
                "assumptions_made": [],
                "next_state": "QUESTIONING",
                "reasoning": "Missing DB",
            }
        ],
        "QUESTIONING": [
            {
                "summary": "Need clarification",
                "questions": [
                    {
                        "id": "Q1",
                        "text": "Which database?",
                        "priority": "CRITICAL",
                        "type": "TECHNICAL",
                        "context": "Determines tooling",
                        "default_answer": None,
                        "dependencies": [],
                    }
                ],
                "can_proceed_without_answers": False,
            }
        ],
        "PLANNING": [_plan_payload("Test plan")],
        "CRITIC": [_critic_payload("APPROVE", True)],
    }
    provider = StubProvider(responses)
    engine = PlannerEngine(
        provider,
        storage_dir=tmp_path,
        timeout=5,
        enable_questions=True,
        enable_critic=True,
        auto_approve_enabled=True,
        auto_approve_threshold=80,
        critic_max_risk="HIGH",
        max_revisions=1,
        initial_answers={"Q1": "PostgreSQL"},
        task_context={"stack": "python"},
    )

    result = engine.run("Add persistence layer", workflow_id=None)
    assert result["state"] == "COMPLETE"
    assert result["plan"]["task_summary"] == "Test plan"
    assert result["revisions"] == 0
    assert result["metrics"]["state_durations"]


def test_engine_auto_revision_cycle(tmp_path):
    responses = {
        "ANALYZER": [
            {
                "task_clarity_score": 90,
                "technical_completeness_score": 90,
                "should_ask_questions": False,
                "identified_gaps": [],
                "assumptions_made": [],
                "next_state": "PLANNING",
                "reasoning": "Clear task",
            }
        ],
        "PLANNING": [_plan_payload("Initial plan"), _plan_payload("Revised plan")],
        "CRITIC": [
            _critic_payload("REVISE: add tests", False),
            _critic_payload("APPROVE", True),
        ],
    }
    provider = StubProvider(responses)
    engine = PlannerEngine(
        provider,
        storage_dir=tmp_path,
        timeout=5,
        enable_questions=False,
        enable_critic=True,
        auto_approve_enabled=False,
        auto_approve_threshold=85,
        critic_max_risk="MEDIUM",
        max_revisions=2,
        task_context={},
    )

    result = engine.run("Ship feature", workflow_id=None)
    assert result["state"] == "COMPLETE"
    assert result["plan"]["task_summary"] == "Revised plan"
    assert result["revisions"] == 1
