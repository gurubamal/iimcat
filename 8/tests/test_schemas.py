#!/usr/bin/env python3
"""
Pytest unit tests for CLI Planner AI schemas
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import json
from schemas import (
    PlannerState, QuestionPriority, QuestionType,
    Question, PlanStep, ExecutionPlan, QuestionSet, CriticFeedback,
    StateTransition, validate_execution_plan, validate_question_set,
    serialize_to_json, deserialize_plan, deserialize_question_set,
    PlannerContext,
    get_example_plan, get_example_questions
)


class TestPlannerState:
    """Test planner state machine"""
    
    def test_all_states_exist(self):
        """Verify all required states are defined"""
        required_states = [
            'INIT', 'ANALYZING', 'QUESTIONING', 'PLANNING',
            'VALIDATING', 'EXECUTING', 'REVIEWING', 'COMPLETE', 'FAILED'
        ]
        for state_name in required_states:
            assert hasattr(PlannerState, state_name)
    
    def test_state_transitions_valid(self):
        """Test valid state transitions"""
        # INIT can go to ANALYZING
        assert StateTransition.is_valid_transition(
            PlannerState.INIT, PlannerState.ANALYZING
        )
        
        # ANALYZING can go to QUESTIONING or PLANNING
        assert StateTransition.is_valid_transition(
            PlannerState.ANALYZING, PlannerState.QUESTIONING
        )
        assert StateTransition.is_valid_transition(
            PlannerState.ANALYZING, PlannerState.PLANNING
        )
        
        # PLANNING goes to VALIDATING
        assert StateTransition.is_valid_transition(
            PlannerState.PLANNING, PlannerState.VALIDATING
        )
    
    def test_state_transitions_invalid(self):
        """Test invalid state transitions"""
        # Cannot skip from INIT to COMPLETE
        assert not StateTransition.is_valid_transition(
            PlannerState.INIT, PlannerState.COMPLETE
        )
        
        # Cannot go backwards from COMPLETE
        assert not StateTransition.is_valid_transition(
            PlannerState.COMPLETE, PlannerState.PLANNING
        )
    
    def test_get_next_states(self):
        """Test getting valid next states"""
        next_states = StateTransition.get_next_states(PlannerState.ANALYZING)
        assert PlannerState.PLANNING in next_states or PlannerState.QUESTIONING in next_states


class TestPlannerContext:
    """Test planner context helpers"""

    def test_context_serialization_includes_workflow(self):
        """PlannerContext should round-trip workflow metadata"""
        ctx = PlannerContext(
            state=PlannerState.INIT,
            task_description="Demo task",
            workflow_id="abcd1234"
        )
        data = ctx.to_dict()
        assert data['workflow_id'] == "abcd1234"

    def test_deserialize_question_set(self):
        """Question set deserialization builds dataclasses"""
        payload = {
            'summary': 'Need clarity',
            'can_proceed_without_answers': False,
            'questions': [
                {
                    'id': 'Q1',
                    'text': 'Which DB?',
                    'priority': 'HIGH',
                    'type': 'TECHNICAL',
                    'context': 'Impacts schema',
                    'default_answer': 'Postgres',
                    'dependencies': []
                }
            ]
        }
        question_set = deserialize_question_set(payload)
        assert isinstance(question_set, QuestionSet)
        assert question_set.questions[0].id == 'Q1'
        assert question_set.questions[0].priority == QuestionPriority.HIGH


class TestQuestionSchema:
    """Test question-related schemas"""
    
    def test_question_creation(self):
        """Test creating a question"""
        q = Question(
            id="Q1",
            text="Which database to use?",
            priority=QuestionPriority.CRITICAL,
            type=QuestionType.TECHNICAL,
            context="Database choice affects entire architecture",
            default_answer="PostgreSQL"
        )
        
        assert q.id == "Q1"
        assert q.priority == QuestionPriority.CRITICAL
        assert q.default_answer == "PostgreSQL"
    
    def test_question_to_dict(self):
        """Test question serialization"""
        q = Question(
            id="Q2",
            text="Enable caching?",
            priority=QuestionPriority.LOW,
            type=QuestionType.REQUIREMENT,
            context="Improves performance",
            default_answer="Yes"
        )
        
        q_dict = q.to_dict()
        assert q_dict['id'] == "Q2"
        assert q_dict['priority'] == "LOW"
        assert 'context' in q_dict
    
    def test_question_set_validation_valid(self):
        """Test valid question set"""
        qs = {
            'summary': 'Need database choice',
            'questions': [
                {
                    'id': 'Q1',
                    'text': 'Which DB?',
                    'priority': 'CRITICAL',
                    'type': 'TECHNICAL',
                    'context': 'Matters',
                    'default_answer': 'Postgres',
                    'dependencies': []
                }
            ],
            'can_proceed_without_answers': True
        }
        
        is_valid, error = validate_question_set(qs)
        assert is_valid
        assert error is None
    
    def test_question_set_validation_missing_field(self):
        """Test question set with missing field"""
        qs = {
            'summary': 'Missing questions field',
            'can_proceed_without_answers': True
        }
        
        is_valid, error = validate_question_set(qs)
        assert not is_valid
        assert 'questions' in error


class TestExecutionPlanSchema:
    """Test execution plan schemas"""
    
    def test_plan_step_creation(self):
        """Test creating a plan step"""
        step = PlanStep(
            id="S1",
            description="Install dependencies",
            rationale="Need tools before work",
            dependencies=[],
            estimated_duration="10 minutes",
            validation_criteria=["npm install exits 0"],
            risks=["Network issues"]
        )
        
        assert step.id == "S1"
        assert len(step.validation_criteria) == 1
        assert step.rollback_strategy is None
    
    def test_execution_plan_creation(self):
        """Test creating execution plan"""
        plan = ExecutionPlan(
            task_summary="Add logging",
            approach="Use winston library",
            assumptions=["Node.js environment"],
            steps=[
                PlanStep(
                    id="S1",
                    description="Install winston",
                    rationale="Logging library",
                    dependencies=[],
                    estimated_duration="5m",
                    validation_criteria=["winston installed"],
                    risks=[]
                )
            ],
            success_criteria=["Logs work"],
            risks=["None"],
            estimated_total_duration="5m",
            confidence=90.0
        )
        
        assert plan.confidence == 90.0
        assert len(plan.steps) == 1
    
    def test_plan_validation_valid(self):
        """Test valid plan validation"""
        plan_dict = {
            'task_summary': 'Test task',
            'approach': 'Test approach',
            'steps': [
                {
                    'id': 'S1',
                    'description': 'Do something',
                    'validation_criteria': ['Check it works']
                }
            ],
            'success_criteria': ['Task complete'],
            'confidence': 85
        }
        
        is_valid, error = validate_execution_plan(plan_dict)
        assert is_valid
        assert error is None
    
    def test_plan_validation_missing_steps(self):
        """Test plan validation with no steps"""
        plan_dict = {
            'task_summary': 'Test task',
            'approach': 'Test approach',
            'steps': [],
            'success_criteria': ['Task complete'],
            'confidence': 85
        }
        
        is_valid, error = validate_execution_plan(plan_dict)
        assert not is_valid
        assert 'at least one step' in error.lower()
    
    def test_plan_serialization_roundtrip(self):
        """Test plan serialization and deserialization"""
        original_plan = get_example_plan()
        
        # Serialize to dict
        plan_dict = original_plan.to_dict()
        
        # Deserialize back
        restored_plan = deserialize_plan(plan_dict)
        
        # Verify key fields match
        assert restored_plan.task_summary == original_plan.task_summary
        assert len(restored_plan.steps) == len(original_plan.steps)
        assert restored_plan.confidence == original_plan.confidence


class TestExampleSchemas:
    """Test example schema generators"""
    
    def test_example_plan_generation(self):
        """Test example plan generation"""
        plan = get_example_plan()
        
        assert isinstance(plan, ExecutionPlan)
        assert len(plan.steps) > 0
        assert plan.confidence > 0
        assert plan.confidence <= 100
    
    def test_example_questions_generation(self):
        """Test example questions generation"""
        questions = get_example_questions()
        
        assert isinstance(questions, QuestionSet)
        assert len(questions.questions) > 0
        
        # Verify questions have priority
        for q in questions.questions:
            assert isinstance(q.priority, QuestionPriority)


class TestSerialization:
    """Test serialization helpers"""
    
    def test_serialize_to_json(self):
        """Test JSON serialization"""
        plan = get_example_plan()
        json_str = serialize_to_json(plan)
        
        assert isinstance(json_str, str)
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert 'task_summary' in parsed
    
    def test_serialize_to_json_compact(self):
        """Test compact JSON serialization"""
        plan = get_example_plan()
        json_str = serialize_to_json(plan, pretty=False)
        
        # Compact should have no extra whitespace
        assert '\n  ' not in json_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
