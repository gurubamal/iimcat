#!/usr/bin/env python3
"""
JSON Schemas for AI Coding Planner & Questioning Framework
============================================================
Defines strict schemas for plans, questions, and state transitions.

Based on: ref_code_cli_planner_ai/claude_cli_bridge.py pattern
"""

from typing import Dict, List, Optional, Literal
from enum import Enum
from dataclasses import dataclass, asdict
import json


# ============================================================================
# STATE MACHINE DEFINITIONS
# ============================================================================

class PlannerState(str, Enum):
    """State machine states for the planning workflow"""
    INIT = "INIT"                   # Initial state, awaiting task
    ANALYZING = "ANALYZING"         # Analyzing task requirements
    QUESTIONING = "QUESTIONING"     # Gathering clarifications
    PLANNING = "PLANNING"           # Creating execution plan
    VALIDATING = "VALIDATING"       # Validating plan with critic
    EXECUTING = "EXECUTING"         # Executing plan steps
    REVIEWING = "REVIEWING"         # Reviewing execution results
    COMPLETE = "COMPLETE"           # Task completed successfully
    FAILED = "FAILED"               # Task failed, needs intervention


class QuestionPriority(str, Enum):
    """Question priority taxonomy (ranked by urgency)"""
    CRITICAL = "CRITICAL"           # Blocker - cannot proceed without answer (P0)
    HIGH = "HIGH"                   # Major impact on approach/architecture (P1)
    MEDIUM = "MEDIUM"               # Affects implementation details (P2)
    LOW = "LOW"                     # Nice-to-have clarification (P3)
    OPTIONAL = "OPTIONAL"           # For completeness only (P4)


class QuestionType(str, Enum):
    """Question categorization by type"""
    REQUIREMENT = "REQUIREMENT"     # Clarifying requirements
    TECHNICAL = "TECHNICAL"         # Technical approach/architecture
    CONSTRAINT = "CONSTRAINT"       # Constraints, limitations, boundaries
    VALIDATION = "VALIDATION"       # How to validate/test
    SCOPE = "SCOPE"                 # What's in/out of scope
    ASSUMPTION = "ASSUMPTION"       # Confirm/reject assumptions


# ============================================================================
# DATA SCHEMAS
# ============================================================================

@dataclass
class Question:
    """Single question in the questioning phase"""
    id: str                         # Unique question ID (Q1, Q2, ...)
    text: str                       # The question text
    priority: QuestionPriority      # Priority level
    type: QuestionType              # Question category
    context: str                    # Why this question matters
    default_answer: Optional[str] = None  # Suggested default if user skips
    dependencies: List[str] = None  # IDs of questions this depends on

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'text': self.text,
            'priority': self.priority.value,
            'type': self.type.value,
            'context': self.context,
            'default_answer': self.default_answer,
            'dependencies': self.dependencies
        }


@dataclass
class PlanStep:
    """Single step in the execution plan"""
    id: str                         # Unique step ID (S1, S2, ...)
    description: str                # What to do
    rationale: str                  # Why this step is needed
    dependencies: List[str]         # IDs of previous steps this depends on
    estimated_duration: str         # Estimated time (e.g., "5 minutes")
    validation_criteria: List[str]  # How to know if step succeeded
    risks: List[str]                # Potential risks/blockers
    rollback_strategy: Optional[str] = None  # How to undo if needed

    def __post_init__(self):
        if not isinstance(self.dependencies, list):
            self.dependencies = []

    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'description': self.description,
            'rationale': self.rationale,
            'dependencies': self.dependencies,
            'estimated_duration': self.estimated_duration,
            'validation_criteria': self.validation_criteria,
            'risks': self.risks,
            'rollback_strategy': self.rollback_strategy
        }


@dataclass
class ExecutionPlan:
    """Complete execution plan with all steps"""
    task_summary: str               # High-level task description
    approach: str                   # Overall approach/strategy
    assumptions: List[str]          # Key assumptions made
    steps: List[PlanStep]           # Ordered execution steps
    success_criteria: List[str]     # How to measure overall success
    risks: List[str]                # Overall project risks
    estimated_total_duration: str   # Total estimated time
    confidence: float               # Confidence score 0-100

    def to_dict(self) -> Dict:
        return {
            'task_summary': self.task_summary,
            'approach': self.approach,
            'assumptions': self.assumptions,
            'steps': [step.to_dict() for step in self.steps],
            'success_criteria': self.success_criteria,
            'risks': self.risks,
            'estimated_total_duration': self.estimated_total_duration,
            'confidence': self.confidence
        }


@dataclass
class QuestionSet:
    """Set of questions to ask user"""
    summary: str                    # Why we need these questions
    questions: List[Question]       # All questions
    can_proceed_without_answers: bool  # Can we continue with defaults?

    def to_dict(self) -> Dict:
        return {
            'summary': self.summary,
            'questions': [q.to_dict() for q in self.questions],
            'can_proceed_without_answers': self.can_proceed_without_answers
        }

    def get_by_priority(self) -> Dict[QuestionPriority, List[Question]]:
        """Group questions by priority"""
        grouped = {p: [] for p in QuestionPriority}
        for q in self.questions:
            grouped[q.priority].append(q)
        return grouped


@dataclass
class PlannerContext:
    """Complete context for the planner state machine"""
    state: PlannerState
    task_description: str
    workflow_id: Optional[str] = None
    questions: Optional[QuestionSet] = None
    answers: Dict[str, str] = None
    plan: Optional[ExecutionPlan] = None
    execution_log: List[Dict] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.answers is None:
            self.answers = {}
        if self.execution_log is None:
            self.execution_log = []
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict:
        return {
            'state': self.state.value,
            'task_description': self.task_description,
            'workflow_id': self.workflow_id,
            'questions': self.questions.to_dict() if self.questions else None,
            'answers': self.answers,
            'plan': self.plan.to_dict() if self.plan else None,
            'execution_log': self.execution_log,
            'metadata': self.metadata
        }


@dataclass
class CriticFeedback:
    """Feedback from the critic reviewer"""
    approved: bool                  # Is plan approved?
    confidence: float               # Critic's confidence 0-100
    concerns: List[str]             # Specific concerns raised
    suggestions: List[str]          # Improvement suggestions
    missing_steps: List[str]        # Steps that should be added
    unnecessary_steps: List[str]    # Steps that can be removed
    risk_assessment: str            # Overall risk level (LOW/MEDIUM/HIGH)
    recommendation: str             # Final recommendation

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# STATE TRANSITION SCHEMA
# ============================================================================

class StateTransition:
    """Valid state transitions in the state machine"""

    TRANSITIONS = {
        PlannerState.INIT: [PlannerState.ANALYZING],
        PlannerState.ANALYZING: [PlannerState.QUESTIONING, PlannerState.PLANNING],
        PlannerState.QUESTIONING: [PlannerState.PLANNING, PlannerState.FAILED],
        PlannerState.PLANNING: [PlannerState.VALIDATING],
        PlannerState.VALIDATING: [PlannerState.EXECUTING, PlannerState.PLANNING, PlannerState.FAILED, PlannerState.COMPLETE],
        PlannerState.EXECUTING: [PlannerState.REVIEWING, PlannerState.FAILED],
        PlannerState.REVIEWING: [PlannerState.COMPLETE, PlannerState.PLANNING, PlannerState.FAILED],
        PlannerState.COMPLETE: [],
        PlannerState.FAILED: [PlannerState.ANALYZING]  # Can restart after fixing issues
    }

    @classmethod
    def is_valid_transition(cls, from_state: PlannerState, to_state: PlannerState) -> bool:
        """Check if transition is valid"""
        return to_state in cls.TRANSITIONS.get(from_state, [])

    @classmethod
    def get_next_states(cls, current_state: PlannerState) -> List[PlannerState]:
        """Get all valid next states"""
        return cls.TRANSITIONS.get(current_state, [])


# ============================================================================
# SCHEMA VALIDATION
# ============================================================================

def validate_execution_plan(plan_dict: Dict) -> tuple[bool, Optional[str]]:
    """Validate execution plan schema"""
    required_fields = ['task_summary', 'approach', 'steps', 'success_criteria', 'confidence']

    for field in required_fields:
        if field not in plan_dict:
            return False, f"Missing required field: {field}"

    if not isinstance(plan_dict['steps'], list) or len(plan_dict['steps']) == 0:
        return False, "Plan must have at least one step"

    if not isinstance(plan_dict['confidence'], (int, float)) or not (0 <= plan_dict['confidence'] <= 100):
        return False, "Confidence must be a number between 0 and 100"

    # Validate each step
    for i, step in enumerate(plan_dict['steps']):
        if not isinstance(step, dict):
            return False, f"Step {i} is not a dictionary"

        required_step_fields = ['id', 'description', 'validation_criteria']
        for field in required_step_fields:
            if field not in step:
                return False, f"Step {i} missing required field: {field}"

    return True, None


def validate_question_set(questions_dict: Dict) -> tuple[bool, Optional[str]]:
    """Validate question set schema"""
    required_fields = ['summary', 'questions', 'can_proceed_without_answers']

    for field in required_fields:
        if field not in questions_dict:
            return False, f"Missing required field: {field}"

    if not isinstance(questions_dict['questions'], list):
        return False, "Questions must be a list"

    # Validate each question
    for i, q in enumerate(questions_dict['questions']):
        if not isinstance(q, dict):
            return False, f"Question {i} is not a dictionary"

        required_q_fields = ['id', 'text', 'priority', 'type', 'context']
        for field in required_q_fields:
            if field not in q:
                return False, f"Question {i} missing required field: {field}"

        # Validate priority and type enums
        try:
            QuestionPriority(q['priority'])
            QuestionType(q['type'])
        except ValueError as e:
            return False, f"Question {i} has invalid enum value: {e}"

    return True, None


# ============================================================================
# EXAMPLE SCHEMAS
# ============================================================================

def get_example_plan() -> ExecutionPlan:
    """Example execution plan for registry-rewrite/Trivy pipeline"""
    return ExecutionPlan(
        task_summary="Implement Trivy vulnerability scanning in container registry pipeline",
        approach="Integrate Trivy as a post-build scan step with configurable severity thresholds",
        assumptions=[
            "Container registry supports webhook notifications",
            "Trivy database can be cached for performance",
            "CI/CD system supports pipeline stages"
        ],
        steps=[
            PlanStep(
                id="S1",
                description="Install and configure Trivy scanner in CI environment",
                rationale="Need Trivy available in pipeline execution context",
                dependencies=[],
                estimated_duration="10 minutes",
                validation_criteria=[
                    "trivy --version returns expected version",
                    "Trivy DB download completes successfully"
                ],
                risks=["Network issues downloading vulnerability database"],
                rollback_strategy="Remove Trivy installation, revert pipeline config"
            ),
            PlanStep(
                id="S2",
                description="Create pipeline stage for image scanning",
                rationale="Scan images after build, before push to registry",
                dependencies=["S1"],
                estimated_duration="15 minutes",
                validation_criteria=[
                    "Pipeline stage appears in CI configuration",
                    "Stage runs after build step"
                ],
                risks=["Pipeline syntax errors", "Stage ordering conflicts"],
                rollback_strategy="Revert pipeline configuration to previous version"
            ),
            PlanStep(
                id="S3",
                description="Configure severity thresholds and failure conditions",
                rationale="Block critical/high severity vulnerabilities from reaching production",
                dependencies=["S2"],
                estimated_duration="10 minutes",
                validation_criteria=[
                    "Scan fails when critical vulnerabilities found",
                    "Scan passes for acceptable vulnerability levels"
                ],
                risks=["Too strict thresholds blocking legitimate deployments"],
                rollback_strategy="Adjust thresholds or set to warning-only mode"
            ),
            PlanStep(
                id="S4",
                description="Add scan result reporting to pipeline artifacts",
                rationale="Provide visibility into vulnerabilities even when scans pass",
                dependencies=["S3"],
                estimated_duration="10 minutes",
                validation_criteria=[
                    "Scan reports appear in pipeline artifacts",
                    "Reports are human-readable and parseable"
                ],
                risks=["Large report files consuming storage"],
                rollback_strategy="Disable artifact upload"
            ),
            PlanStep(
                id="S5",
                description="Write acceptance tests for scan integration",
                rationale="Ensure scanning works as expected across scenarios",
                dependencies=["S4"],
                estimated_duration="20 minutes",
                validation_criteria=[
                    "All acceptance tests pass",
                    "Tests cover success and failure scenarios"
                ],
                risks=["Test data (vulnerable images) not available"],
                rollback_strategy="N/A - tests are additions only"
            )
        ],
        success_criteria=[
            "Vulnerable images are blocked from registry",
            "Scan reports are generated for all builds",
            "Pipeline execution time increases by <2 minutes",
            "All acceptance tests pass"
        ],
        risks=[
            "Trivy database download failures causing build delays",
            "False positives blocking legitimate deployments",
            "Performance impact on pipeline execution time"
        ],
        estimated_total_duration="65 minutes",
        confidence=85.0
    )


def get_example_questions() -> QuestionSet:
    """Example question set for registry-rewrite/Trivy pipeline"""
    return QuestionSet(
        summary="Need clarification on registry configuration and vulnerability policies",
        questions=[
            Question(
                id="Q1",
                text="Which container registry are you using (Docker Hub, ECR, GCR, Harbor, other)?",
                priority=QuestionPriority.CRITICAL,
                type=QuestionType.REQUIREMENT,
                context="Different registries have different authentication and integration patterns",
                default_answer="Docker Hub",
                dependencies=[]
            ),
            Question(
                id="Q2",
                text="What severity level should block deployments (CRITICAL only, or CRITICAL+HIGH)?",
                priority=QuestionPriority.HIGH,
                type=QuestionType.CONSTRAINT,
                context="Determines the failure threshold for vulnerability scans",
                default_answer="CRITICAL only (allow HIGH with warnings)",
                dependencies=[]
            ),
            Question(
                id="Q3",
                text="Should we cache the Trivy vulnerability database between builds?",
                priority=QuestionPriority.MEDIUM,
                type=QuestionType.TECHNICAL,
                context="Caching improves performance but needs cache invalidation strategy",
                default_answer="Yes, cache for 24 hours",
                dependencies=[]
            ),
            Question(
                id="Q4",
                text="Do you want Trivy to scan for misconfigurations in addition to vulnerabilities?",
                priority=QuestionPriority.LOW,
                type=QuestionType.SCOPE,
                context="Trivy supports config scanning (Dockerfiles, IaC) in addition to CVE scanning",
                default_answer="No, vulnerabilities only for now",
                dependencies=[]
            ),
            Question(
                id="Q5",
                text="Should scan results be sent to a security dashboard or SIEM?",
                priority=QuestionPriority.OPTIONAL,
                type=QuestionType.REQUIREMENT,
                context="Integration with security tools for centralized monitoring",
                default_answer="No, pipeline artifacts only",
                dependencies=[]
            )
        ],
        can_proceed_without_answers=True  # All questions have reasonable defaults
    )


# ============================================================================
# SERIALIZATION HELPERS
# ============================================================================

def serialize_to_json(obj, pretty: bool = True) -> str:
    """Serialize dataclass to JSON string"""
    if hasattr(obj, 'to_dict'):
        data = obj.to_dict()
    else:
        data = asdict(obj)

    if pretty:
        return json.dumps(data, indent=2, ensure_ascii=False)
    else:
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)


def deserialize_plan(data: Dict) -> ExecutionPlan:
    """Deserialize JSON to ExecutionPlan"""
    steps = [
        PlanStep(
            id=s['id'],
            description=s['description'],
            rationale=s['rationale'],
            dependencies=s.get('dependencies', []),
            estimated_duration=s['estimated_duration'],
            validation_criteria=s['validation_criteria'],
            risks=s.get('risks', []),
            rollback_strategy=s.get('rollback_strategy')
        )
        for s in data['steps']
    ]

    return ExecutionPlan(
        task_summary=data['task_summary'],
        approach=data['approach'],
        assumptions=data.get('assumptions', []),
        steps=steps,
        success_criteria=data['success_criteria'],
        risks=data.get('risks', []),
        estimated_total_duration=data['estimated_total_duration'],
        confidence=data['confidence']
    )


def deserialize_question_set(data: Dict) -> QuestionSet:
    """Deserialize JSON to QuestionSet"""
    questions = [
        Question(
            id=q['id'],
            text=q['text'],
            priority=QuestionPriority(q['priority']),
            type=QuestionType(q['type']),
            context=q['context'],
            default_answer=q.get('default_answer'),
            dependencies=q.get('dependencies', [])
        )
        for q in data.get('questions', [])
    ]

    return QuestionSet(
        summary=data.get('summary', ''),
        questions=questions,
        can_proceed_without_answers=data.get('can_proceed_without_answers', False)
    )


# ============================================================================
# MAIN DEMO
# ============================================================================

if __name__ == "__main__":
    # Demo: Generate example schemas
    print("=" * 80)
    print("AI CODING PLANNER - EXAMPLE SCHEMAS")
    print("=" * 80)

    # Example execution plan
    plan = get_example_plan()
    print("\n📋 EXECUTION PLAN:")
    print(serialize_to_json(plan))

    # Validate plan
    is_valid, error = validate_execution_plan(plan.to_dict())
    print(f"\n✅ Plan validation: {'PASS' if is_valid else f'FAIL - {error}'}")

    # Example questions
    questions = get_example_questions()
    print("\n❓ QUESTION SET:")
    print(serialize_to_json(questions))

    # Validate questions
    is_valid, error = validate_question_set(questions.to_dict())
    print(f"\n✅ Questions validation: {'PASS' if is_valid else f'FAIL - {error}'}")

    # State machine example
    print("\n🔄 STATE MACHINE TRANSITIONS:")
    for state in PlannerState:
        next_states = StateTransition.get_next_states(state)
        print(f"  {state.value:15s} → {', '.join([s.value for s in next_states]) if next_states else 'TERMINAL'}")
