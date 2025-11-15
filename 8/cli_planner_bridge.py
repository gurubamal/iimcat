#!/usr/bin/env python3
"""
CLI Planner Bridge - AI Coding Planner & Questioning Framework
================================================================
Main bridge for coordinating AI-driven task planning and execution.

The workflow now runs through a PlannerEngine that owns PlannerContext,
persists state to disk, enforces state transitions, supports interactive
questioning, critic-driven auto revisions, and structured logging.

Usage:
    echo '{"task": "Add Trivy scanning to pipeline"}' | python3 cli_planner_bridge.py
"""

import sys
import json
import subprocess
import os
import re
import time
import hashlib
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime

# Import our schemas and prompts
try:
    from schemas import (
        PlannerState,
        ExecutionPlan,
        QuestionSet,
        PlannerContext,
        StateTransition,
        validate_execution_plan,
        validate_question_set,
        deserialize_plan,
        deserialize_question_set,
        QuestionPriority,
        QuestionType,
        Question,
    )
    from prompts import (
        build_analyzer_prompt,
        build_questioner_prompt,
        build_planner_prompt,
        build_critic_prompt,
        ANALYZER_SYSTEM_PROMPT,
        QUESTIONER_SYSTEM_PROMPT,
        PLANNER_SYSTEM_PROMPT,
        CRITIC_SYSTEM_PROMPT,
    )
except ImportError as e:
    print(f"ERROR: Missing dependencies: {e}", file=sys.stderr)
    print("Ensure schemas.py and prompts.py are in the same directory", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# CONFIGURATION (Claude CLI Only)
# ============================================================================

MODEL = os.getenv("PLANNER_MODEL", "sonnet")
TIMEOUT = int(os.getenv("PLANNER_TIMEOUT", "120"))

# Feature flags & advanced settings
ENABLE_CRITIC = os.getenv("PLANNER_ENABLE_CRITIC", "1") != "0"
ENABLE_QUESTIONS = os.getenv("PLANNER_ENABLE_QUESTIONS", "1") != "0"
AUTO_APPROVE_HIGH_CONFIDENCE = os.getenv("PLANNER_AUTO_APPROVE", "0") == "1"
AUTO_APPROVE_THRESHOLD = float(os.getenv("PLANNER_AUTO_APPROVE_THRESHOLD", "85"))
CRITIC_MAX_ACCEPTABLE_RISK = os.getenv("PLANNER_CRITIC_MAX_RISK", "MEDIUM").upper()
MAX_REVISION_ITERATIONS = int(os.getenv("PLANNER_MAX_REVISIONS", "2"))
STATE_STORAGE_DIR = os.getenv("PLANNER_STATE_DIR", ".planner_runs")


# ============================================================================
# CLAUDE CLI INTERFACE (Following claude_cli_bridge.py pattern)
# ============================================================================

def call_claude_cli(prompt: str, system_prompt: str, timeout: int = TIMEOUT) -> str:
    """Call Claude CLI with --print mode and return response."""

    cmd = [
        "claude",
        "--print",  # Non-interactive mode
        "--output-format",
        "text",
        "--model",
        MODEL,
        "--system-prompt",
        system_prompt,
        prompt,
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=True
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"Claude CLI timed out after {timeout}s")
    except subprocess.CalledProcessError as e:
        stderr = e.stderr if e.stderr else str(e)
        raise RuntimeError(f"Claude CLI failed: {stderr[:300]}")
    except FileNotFoundError:
        raise RuntimeError("claude CLI not found. Is it installed and in PATH?")
    except Exception as e:
        raise RuntimeError(f"Claude CLI error: {str(e)[:300]}")


def extract_json_from_response(response: str) -> Dict:
    """Extract and parse JSON from Claude's response."""
    text = response.strip()

    # Remove markdown code fences if present
    if text.startswith("```"):
        text = text[3:]
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
        if "```" in text:
            text = text.split("```")[0].strip()

    # Try to parse JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not parse JSON from response: {text[:500]}")


# ============================================================================
# PROVIDERS
# ============================================================================


class BaseLLMProvider:
    """Interface for LLM providers used by the planner."""

    label: str = "unknown"

    def complete(
        self, prompt: str, system_prompt: str, *, timeout: int, phase: str
    ) -> str:
        raise NotImplementedError


class ClaudeCLIProvider(BaseLLMProvider):
    """Concrete provider backed by the Claude CLI."""

    label = f"claude-cli ({MODEL})"

    def complete(
        self, prompt: str, system_prompt: str, *, timeout: int, phase: str
    ) -> str:
        return call_claude_cli(prompt, system_prompt, timeout=timeout)


class ReplayLLMProvider(BaseLLMProvider):
    """
    Deterministic provider used for tests.

    Responses are pulled from a JSON fixture keyed by phase.
    """

    label = "fake-provider"

    def __init__(self, fixture_path: str):
        self.fixture_path = Path(fixture_path)
        if not self.fixture_path.exists():
            raise FileNotFoundError(f"Fake response file not found: {fixture_path}")
        with self.fixture_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        self.responses: Dict[str, List[Any]] = {
            (key.upper()): list(value) for key, value in data.items()
        }

    def complete(
        self, prompt: str, system_prompt: str, *, timeout: int, phase: str
    ) -> str:
        phase_key = (phase or "DEFAULT").upper()
        queue = self.responses.get(phase_key)
        if not queue:
            raise RuntimeError(
                f"No fake responses remaining for phase '{phase_key}' "
                f"in {self.fixture_path}"
            )
        response = queue.pop(0)
        if isinstance(response, str):
            return response
        return json.dumps(response)


# ============================================================================
# PLANNER ENGINE
# ============================================================================


class PlannerEngine:
    """Stateful engine orchestrating the planning workflow."""

    RISK_RANK = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}

    def __init__(
        self,
        provider: BaseLLMProvider,
        *,
        storage_dir: str,
        timeout: int,
        enable_questions: bool,
        enable_critic: bool,
        auto_approve_enabled: bool,
        auto_approve_threshold: float,
        critic_max_risk: str,
        max_revisions: int,
        initial_answers: Optional[Dict[str, str]] = None,
        task_context: Optional[Dict] = None,
    ):
        self.provider = provider
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.enable_questions = enable_questions
        self.enable_critic = enable_critic
        self.auto_approve_enabled = auto_approve_enabled
        self.auto_approve_threshold = auto_approve_threshold
        self.critic_max_risk = critic_max_risk.upper()
        self.max_revisions = max(0, max_revisions)
        self.initial_answers = initial_answers or {}
        self.request_context = task_context or {}

        self.context: Optional[PlannerContext] = None
        self.analysis: Optional[Dict] = None
        self.assumptions: List[str] = []
        self.pending_critic_feedback: Optional[Dict] = None
        self.previous_plan_for_revision: Optional[ExecutionPlan] = None
        self.revision_count = 0
        self.auto_approved = False
        self._state_started_at = time.monotonic()
        self.state_timings: Dict[str, float] = {}
        self.result_message = ""
        self._tty_input = self._open_tty()

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    def run(self, task_description: Optional[str], workflow_id: Optional[str]) -> Dict:
        """Execute the planning workflow and return the final payload."""
        self.context = self._load_or_init_context(task_description, workflow_id)
        if self.context.state == PlannerState.INIT:
            self._set_state(PlannerState.ANALYZING)

        while True:
            state = self.context.state
            if state == PlannerState.ANALYZING:
                self._handle_analyzing()
            elif state == PlannerState.QUESTIONING:
                result = self._handle_questioning()
                if result:
                    return result
            elif state == PlannerState.PLANNING:
                self._handle_planning()
            elif state == PlannerState.VALIDATING:
                result = self._handle_validating()
                if result:
                    return result
            elif state == PlannerState.COMPLETE:
                return self._build_success_payload()
            elif state == PlannerState.FAILED:
                return self._build_failure_payload()
            else:
                raise RuntimeError(f"Unhandled planner state: {state}")

    # ---------------------------------------------------------------------
    # State Handlers
    # ---------------------------------------------------------------------

    def _handle_analyzing(self):
        self._log("analyzing_start")
        analysis = self._analyze_task()
        self.analysis = analysis
        self.assumptions = analysis.get("assumptions_made", [])
        self.context.metadata["analysis"] = analysis
        self.context.metadata["assumptions"] = self.assumptions
        self._save_context()

        should_question = (
            self.enable_questions and analysis.get("should_ask_questions", False)
        )
        next_state = PlannerState.QUESTIONING if should_question else PlannerState.PLANNING
        self._set_state(next_state)

    def _handle_questioning(self) -> Optional[Dict]:
        if not self.enable_questions:
            self._set_state(PlannerState.PLANNING)
            return None

        if not self.context.questions:
            question_data = self._generate_questions()
            question_set = deserialize_question_set(question_data)
            self.context.questions = question_set
            self._save_context()
        else:
            question_set = self.context.questions

        answers_ready = self._collect_answers(question_set)
        if not answers_ready:
            return self._pending_questions_response(question_set)

        self._set_state(PlannerState.PLANNING)
        return None

    def _handle_planning(self):
        iteration = self.revision_count + 1
        self._log("planning_start", iteration=iteration)

        answers = self.context.answers or {}
        plan = self._create_plan(
            answers=answers,
            assumptions=self.assumptions,
            critic_feedback=self.pending_critic_feedback,
            previous_plan=self.previous_plan_for_revision,
            iteration=iteration,
        )

        self.context.plan = plan
        self.previous_plan_for_revision = None
        self.pending_critic_feedback = None
        self._save_context()
        self._log(
            "planning_complete",
            steps=len(plan.steps),
            duration=plan.estimated_total_duration,
            confidence=plan.confidence,
        )
        self._set_state(PlannerState.VALIDATING)

    def _handle_validating(self) -> Optional[Dict]:
        if not self.enable_critic:
            self.auto_approved = self._should_auto_approve(self.context.plan, None)
            self._set_state(PlannerState.COMPLETE)
            return None

        critic_feedback = self._validate_plan_with_critic(self.context.plan)
        self.context.metadata["critic_feedback"] = critic_feedback
        self._save_context()
        self._log(
            "critic_feedback",
            approved=critic_feedback.get("approved", False),
            recommendation=critic_feedback.get("recommendation"),
            risk=critic_feedback.get("risk_assessment"),
        )

        if self._needs_revision(critic_feedback):
            if self.revision_count >= self.max_revisions:
                self.result_message = (
                    "Plan rejected after maximum automatic revisions attempted"
                )
                self._set_state(PlannerState.FAILED)
                return None

            self.previous_plan_for_revision = self.context.plan
            self.pending_critic_feedback = critic_feedback
            self.revision_count += 1
            self._log("revision_requested", iteration=self.revision_count)
            self._set_state(PlannerState.PLANNING)
            return None

        self.auto_approved = self._should_auto_approve(self.context.plan, critic_feedback)
        self.result_message = "Plan ready for execution"
        self._set_state(PlannerState.COMPLETE)
        return None

    # ---------------------------------------------------------------------
    # LLM Call Helpers
    # ---------------------------------------------------------------------

    def _complete(self, prompt: str, system_prompt: str, phase: str) -> Dict:
        raw = self.provider.complete(
            prompt,
            system_prompt,
            timeout=self.timeout,
            phase=phase,
        )
        return extract_json_from_response(raw)

    def _analyze_task(self) -> Dict:
        prompt = build_analyzer_prompt(self.context.task_description, self.request_context)
        try:
            data = self._complete(prompt, ANALYZER_SYSTEM_PROMPT, phase="ANALYZER")
            return data
        except Exception as exc:
            self._log("analysis_error", error=str(exc))
            return {
                "task_clarity_score": 50,
                "technical_completeness_score": 50,
                "should_ask_questions": False,
                "identified_gaps": [],
                "assumptions_made": [f"Analysis failed: {exc}"],
                "next_state": "PLANNING",
                "reasoning": "Analysis failed, proceeding with assumptions",
            }

    def _generate_questions(self) -> Dict:
        gaps = self.analysis.get("identified_gaps", []) if self.analysis else []
        assumptions = self.assumptions or []
        prompt = build_questioner_prompt(
            self.context.task_description,
            gaps,
            assumptions,
            self.request_context,
        )
        try:
            data = self._complete(prompt, QUESTIONER_SYSTEM_PROMPT, phase="QUESTIONING")
            is_valid, error = validate_question_set(data)
            if not is_valid:
                raise ValueError(f"Invalid question set: {error}")
            return data
        except Exception as exc:
            self._log("question_error", error=str(exc))
            return {
                "summary": "Question generation failed, proceeding with assumptions",
                "questions": [],
                "can_proceed_without_answers": True,
            }

    def _create_plan(
        self,
        *,
        answers: Dict[str, str],
        assumptions: List[str],
        critic_feedback: Optional[Dict],
        previous_plan: Optional[ExecutionPlan],
        iteration: int,
    ) -> ExecutionPlan:
        prompt = build_planner_prompt(
            self.context.task_description,
            answers,
            assumptions,
            self.request_context,
            critic_feedback=critic_feedback,
            previous_plan=previous_plan,
            iteration=iteration,
        )
        data = self._complete(prompt, PLANNER_SYSTEM_PROMPT, phase="PLANNING")
        is_valid, error = validate_execution_plan(data)
        if not is_valid:
            raise ValueError(f"Invalid execution plan: {error}")
        return deserialize_plan(data)

    def _validate_plan_with_critic(self, plan: ExecutionPlan) -> Dict:
        prompt = build_critic_prompt(self.context.task_description, plan, self.request_context)
        try:
            return self._complete(prompt, CRITIC_SYSTEM_PROMPT, phase="CRITIC")
        except Exception as exc:
            self._log("critic_error", error=str(exc))
            return {
                "approved": True,
                "confidence": 50,
                "concerns": [f"Critic unavailable: {exc}"],
                "suggestions": [],
                "missing_steps": [],
                "unnecessary_steps": [],
                "risk_assessment": "MEDIUM",
                "recommendation": "APPROVE (critic unavailable)",
            }

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _load_or_init_context(
        self, task_description: Optional[str], workflow_id: Optional[str]
    ) -> PlannerContext:
        if workflow_id:
            path = self.storage_dir / f"{workflow_id}.json"
            if not path.exists():
                raise FileNotFoundError(f"No workflow found for ID '{workflow_id}'")
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            context = self._context_from_dict(data)
            self.state_timings = context.metadata.get("state_durations", {})
            self.analysis = context.metadata.get("analysis")
            self.assumptions = context.metadata.get("assumptions", [])
            stored_context = context.metadata.get("task_context") or {}
            if not self.request_context:
                self.request_context = stored_context
            if task_description and task_description != context.task_description:
                self._log(
                    "task_mismatch",
                    stored=context.task_description,
                    provided=task_description,
                )
            return context

        if not task_description:
            raise ValueError("Task description required when no workflow_id provided")

        workflow_id = self._generate_workflow_id(task_description)
        context = PlannerContext(
            state=PlannerState.INIT,
            task_description=task_description,
            workflow_id=workflow_id,
            answers=dict(self.initial_answers),
            metadata={
                "task_context": self.request_context,
                "created_at": datetime.now().isoformat(),
            },
        )
        self._save_context(context)
        return context

    def _context_from_dict(self, data: Dict) -> PlannerContext:
        questions = (
            deserialize_question_set(data["questions"]) if data.get("questions") else None
        )
        plan = deserialize_plan(data["plan"]) if data.get("plan") else None
        return PlannerContext(
            state=PlannerState(data["state"]),
            task_description=data["task_description"],
            workflow_id=data.get("workflow_id"),
            questions=questions,
            answers=data.get("answers") or {},
            plan=plan,
            execution_log=data.get("execution_log") or [],
            metadata=data.get("metadata") or {},
        )

    def _save_context(self, context: Optional[PlannerContext] = None):
        ctx = context or self.context
        if ctx is None:
            return

        ctx.metadata["task_context"] = self.request_context
        if self.analysis:
            ctx.metadata["analysis"] = self.analysis
        if self.assumptions:
            ctx.metadata["assumptions"] = self.assumptions
        ctx.metadata["state_durations"] = self.state_timings
        ctx.metadata["last_updated"] = datetime.now().isoformat()

        path = self.storage_dir / f"{ctx.workflow_id}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(ctx.to_dict(), handle, indent=2, ensure_ascii=False)

    def _set_state(self, new_state: PlannerState):
        if not StateTransition.is_valid_transition(self.context.state, new_state):
            raise RuntimeError(
                f"Invalid state transition: {self.context.state.value} → {new_state.value}"
            )
        now = time.monotonic()
        prev_state = self.context.state
        duration = now - self._state_started_at if self._state_started_at else 0
        if prev_state:
            self.state_timings[prev_state.value] = round(
                self.state_timings.get(prev_state.value, 0.0) + duration, 3
            )
        self.context.state = new_state
        self._state_started_at = now
        self._log(
            "state_transition",
            from_state=prev_state.value if prev_state else None,
            to_state=new_state.value,
        )
        self._save_context()

    def _collect_answers(self, question_set: QuestionSet) -> bool:
        answers = self.context.answers or {}
        answers.update(self.initial_answers)

        missing = []
        for question in question_set.questions:
            if answers.get(question.id):
                continue
            if question_set.can_proceed_without_answers:
                answers[question.id] = question.default_answer or ""
                continue
            # When can_proceed_without_answers=False, we need to prompt the user
            # even if defaults exist (defaults are only used if user skips)
            missing.append(question)

        if not missing:
            self.context.answers = answers
            self._save_context()
            return True

        for question in missing:
            response = self._prompt_for_answer(question)
            if response:
                answers[question.id] = response

        still_missing = [
            q.id for q in question_set.questions if not answers.get(q.id)
        ]
        if still_missing:
            self.context.answers = answers
            self._save_context()
            return False

        self.context.answers = answers
        self._save_context()
        return True

    def _prompt_for_answer(self, question: Question) -> Optional[str]:
        if not self._tty_input:
            return None

        sys.stderr.write("\n")
        sys.stderr.write(f"[QUESTION] {question.text}\n")
        sys.stderr.write(f"  Context: {question.context}\n")
        sys.stderr.write(
            f"  Priority: {question.priority.value}, Type: {question.type.value}\n"
        )
        if question.default_answer:
            sys.stderr.write(f"  Default: {question.default_answer}\n")
        sys.stderr.write("Your answer (leave blank to skip): ")
        sys.stderr.flush()

        response = self._tty_input.readline()
        if response is None:
            return None
        response = response.strip()
        if not response and question.default_answer:
            return question.default_answer
        return response or None

    def _pending_questions_response(self, question_set: QuestionSet) -> Dict:
        self.result_message = (
            "Clarifications required. Provide answers via the 'answers' field "
            "or rerun interactively."
        )
        self._save_context()
        return {
            "workflow_id": self.context.workflow_id,
            "state": "QUESTIONING",
            "questions": question_set.to_dict(),
            "analysis": self.analysis,
            "message": self.result_message,
        }

    def _build_success_payload(self) -> Dict:
        self._save_context()
        plan_dict = self.context.plan.to_dict() if self.context.plan else None
        return {
            "workflow_id": self.context.workflow_id,
            "state": "COMPLETE",
            "plan": plan_dict,
            "analysis": self.analysis,
            "critic_feedback": self.context.metadata.get("critic_feedback"),
            "auto_approved": self.auto_approved,
            "message": self.result_message or "Plan ready for execution",
            "provider": self.provider.label,
            "revisions": self.revision_count,
            "metrics": {"state_durations": self.state_timings},
        }

    def _build_failure_payload(self) -> Dict:
        self._save_context()
        return {
            "workflow_id": self.context.workflow_id,
            "state": "FAILED",
            "plan": self.context.plan.to_dict() if self.context.plan else None,
            "analysis": self.analysis,
            "critic_feedback": self.context.metadata.get("critic_feedback"),
            "message": self.result_message or "Planning workflow failed",
            "provider": self.provider.label,
            "revisions": self.revision_count,
            "metrics": {"state_durations": self.state_timings},
        }

    def _needs_revision(self, critic_feedback: Dict) -> bool:
        recommendation = (critic_feedback.get("recommendation") or "").upper()
        approved = critic_feedback.get("approved", False)
        if recommendation.startswith("REJECT") or recommendation.startswith("REVISE"):
            return True
        return not approved

    def _should_auto_approve(
        self, plan: Optional[ExecutionPlan], critic_feedback: Optional[Dict]
    ) -> bool:
        if not self.auto_approve_enabled:
            return False
        if not plan:
            return False
        if plan.confidence < self.auto_approve_threshold:
            return False
        if critic_feedback:
            risk = (critic_feedback.get("risk_assessment") or "HIGH").upper()
            return self._risk_allows_auto(risk)
        return True

    def _risk_allows_auto(self, risk: str) -> bool:
        max_allowed = self.RISK_RANK.get(self.critic_max_risk, 3)
        current = self.RISK_RANK.get(risk.upper(), 3)
        return current <= max_allowed

    def _generate_workflow_id(self, task_description: str) -> str:
        token = f"{task_description}{datetime.now().isoformat()}".encode()
        return hashlib.md5(token).hexdigest()[:8]

    def _open_tty(self):
        try:
            return open("/dev/tty", "r", encoding="utf-8")
        except OSError:
            return None

    def _log(self, event: str, **fields):
        payload = {
            "ts": datetime.now().isoformat(),
            "workflow_id": self.context.workflow_id if self.context else None,
            "state": self.context.state.value if self.context else None,
            "event": event,
        }
        payload.update(fields)
        print(json.dumps(payload), file=sys.stderr)


# ============================================================================
# WORKFLOW FACADE
# ============================================================================


def _load_provider() -> BaseLLMProvider:
    fake_path = os.getenv("PLANNER_FAKE_RESPONSES_FILE")
    if fake_path:
        return ReplayLLMProvider(fake_path)
    return ClaudeCLIProvider()


def run_planning_workflow(
    task_description: Optional[str],
    context: Dict = None,
    answers: Dict[str, str] = None,
    workflow_id: Optional[str] = None,
) -> Dict:
    provider = _load_provider()
    engine = PlannerEngine(
        provider,
        storage_dir=STATE_STORAGE_DIR,
        timeout=TIMEOUT,
        enable_questions=ENABLE_QUESTIONS,
        enable_critic=ENABLE_CRITIC,
        auto_approve_enabled=AUTO_APPROVE_HIGH_CONFIDENCE,
        auto_approve_threshold=AUTO_APPROVE_THRESHOLD,
        critic_max_risk=CRITIC_MAX_ACCEPTABLE_RISK,
        max_revisions=MAX_REVISION_ITERATIONS,
        initial_answers=answers,
        task_context=context,
    )
    return engine.run(task_description, workflow_id)


# ============================================================================
# CLI INTERFACE
# ============================================================================


def main():
    """Main entry point - reads task from stdin, outputs plan to stdout"""
    input_data = sys.stdin.read()

    if not input_data.strip():
        result = {"error": "No input provided", "state": "FAILED"}
        print(json.dumps(result, indent=2))
        return

    # Parse input JSON
    try:
        request = json.loads(input_data)
        if isinstance(request, str):
            request = {"task": request}
    except json.JSONDecodeError:
        request = {"task": input_data.strip()}

    task_description = request.get("task") or request.get("task_description")
    workflow_id = request.get("workflow_id")
    answers = request.get("answers") or {}
    context = request.get("context") or {}

    if not task_description and not workflow_id:
        result = {
            "error": "No task description or workflow_id provided",
            "state": "FAILED",
        }
        print(json.dumps(result, indent=2))
        return

    try:
        result = run_planning_workflow(
            task_description=task_description,
            context=context,
            answers=answers,
            workflow_id=workflow_id,
        )
    except FileNotFoundError as exc:
        result = {"error": str(exc), "state": "FAILED"}
        print(f"❌ Workflow failed: {exc}", file=sys.stderr)
    except Exception as exc:
        result = {"error": str(exc), "state": "FAILED"}
        print(f"❌ Workflow failed: {exc}", file=sys.stderr)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
