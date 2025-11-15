#!/usr/bin/env python3
"""
AI CORRECTION SUPERVISOR - Continuous Oversight & Outcome Assessment
Provides AI-driven supervision, alignment verification, and performance tracking

Key Features:
- Real-time supervision of correction boost decisions
- Alignment verification with trading principles
- Outcome assessment and feedback loops
- Performance metrics tracking
- Decision transparency and reasoning validation
- AI coaching and calibration recommendations

Usage:
    supervisor = AICorrectionSupervisor()
    assessment = supervisor.assess_boost_decision(analysis_result)
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, asdict
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class SupervisionResult:
    """Result from AI supervision assessment."""
    ticker: str
    timestamp: str
    original_decision: str
    supervisor_verdict: str  # APPROVE, CAUTION, REJECT, REVIEW
    confidence_score: float  # 0-1, how confident supervisor is
    alignment_issues: List[str]
    reasoning: str
    recommendations: List[str]
    risk_flags: List[str]


class AICorrectionSupervisor:
    """
    AI-powered supervisor for correction boost decisions.

    Responsibilities:
    1. Validate decision logic alignment with principles
    2. Assess outcome patterns (wins/losses)
    3. Detect and flag anomalies
    4. Recommend threshold adjustments
    5. Track performance metrics
    6. Provide continuous feedback
    """

    def __init__(self):
        """Initialize supervisor."""
        self.decision_history = []
        self.outcome_tracking = {}  # ticker -> [outcomes]
        self.performance_metrics = {
            'total_boosts': 0,
            'successful_boosts': 0,
            'failed_boosts': 0,
            'precision': 0.0,
            'hit_rate': 0.0,
            'avg_return': 0.0
        }

        # Thresholds for flagging
        self.precision_warning_threshold = 0.75  # Alert if < 75%
        self.false_positive_warning = 0.20  # Alert if > 20%
        self.low_confidence_threshold = 0.40

        # Alignment principles
        self.principles = {
            'reversal_confirmation_critical': True,
            'risk_filters_mandatory': True,
            'market_context_required': True,
            'emergency_safeguards_essential': True,
            'min_fundamentals_required': True
        }

    def assess_boost_decision(self, analysis: Dict) -> SupervisionResult:
        """
        Assess a boost decision for alignment and viability.

        Args:
            analysis: Output from EnhancedCorrectionAnalyzer

        Returns:
            SupervisionResult with verdict and recommendations
        """
        ticker = analysis.get('ticker', 'UNKNOWN')
        timestamp = datetime.now().isoformat()
        original_decision = analysis.get('final_decision', 'UNKNOWN')

        alignment_issues = []
        risk_flags = []
        recommendations = []
        supervisor_verdict = 'APPROVE'
        confidence_score = 1.0

        # PRINCIPLE 1: Reversal Confirmation
        if 'Reversal Confirmed' not in analysis.get('layers_passed', []):
            alignment_issues.append('Reversal confirmation failed - critical layer')
            risk_flags.append('FALLING_KNIFE_RISK - Stock still declining')
            supervisor_verdict = 'REJECT'
            confidence_score = 0.1

        # PRINCIPLE 2: Risk Filters
        if 'Risk Filters Passed' not in analysis.get('layers_passed', []):
            alignment_issues.append('Risk filters failed')
            risk_flags.append('SAFETY_VIOLATION - Risky stock profile')
            supervisor_verdict = 'REJECT'
            confidence_score = 0.1

        # PRINCIPLE 3: Market Context
        if 'market_context' not in analysis:
            alignment_issues.append('Market context not assessed')
            risk_flags.append('CONTEXT_MISSING - Market awareness required')
            supervisor_verdict = 'CAUTION'
            confidence_score = max(0.5, confidence_score - 0.2)

        # PRINCIPLE 4: Emergency Safeguards
        if analysis.get('emergency_level') == 'critical':
            alignment_issues.append('Emergency safeguard triggered')
            risk_flags.append('EMERGENCY_CONDITION - Markets in distress')
            supervisor_verdict = 'REJECT'
            confidence_score = 0.0

        # Check confidence levels
        correction_confidence = analysis.get('correction_confidence', 0)
        if correction_confidence < self.low_confidence_threshold:
            alignment_issues.append(f'Low correction confidence: {correction_confidence:.2f}')
            risk_flags.append('LOW_CONFIDENCE - Marginal setup quality')
            recommendations.append(f'Consider higher confidence threshold for this regime')
            if supervisor_verdict != 'REJECT':
                supervisor_verdict = 'CAUTION'
            confidence_score = max(0.4, confidence_score - 0.3)

        # Check fundamental health
        fundamental_confidence = analysis.get('fundamental_confidence', 0)
        if fundamental_confidence < 30:
            alignment_issues.append(f'Weak fundamentals: {fundamental_confidence:.0f}/100')
            risk_flags.append('WEAK_FUNDAMENTALS - Company health questionable')
            recommendations.append('Require stronger earnings/cash position')
            if supervisor_verdict != 'REJECT':
                supervisor_verdict = 'CAUTION'
            confidence_score = max(0.5, confidence_score - 0.2)

        # Check oversold severity
        oversold_score = analysis.get('oversold_score', 0)
        if oversold_score < 30:
            alignment_issues.append(f'Mild oversold condition: {oversold_score:.0f}/100')
            recommendations.append('Require stronger technical confirmation')
            if supervisor_verdict == 'APPROVE':
                supervisor_verdict = 'CAUTION'
            confidence_score = max(0.6, confidence_score - 0.2)

        # Check catalyst strength
        catalyst_strength = analysis.get('catalyst_strength', 0)
        if catalyst_strength < 12:
            alignment_issues.append(f'Weak catalyst: {catalyst_strength:.0f}/100')
            recommendations.append('Require stronger news catalyst (AI score ≥70)')
            confidence_score = max(0.5, confidence_score - 0.1)

        # Approval logic
        if original_decision == 'NO_BOOST' and supervisor_verdict == 'APPROVE':
            supervisor_verdict = 'NO_BOOST'  # Respect original decision
        elif original_decision == 'ERROR':
            supervisor_verdict = 'REVIEW'
            confidence_score = 0.0

        # Generate reasoning
        reasoning = self._generate_reasoning(
            alignment_issues,
            risk_flags,
            original_decision,
            supervisor_verdict,
            correction_confidence
        )

        # Add recommendations based on verdict
        if supervisor_verdict == 'REJECT':
            recommendations.append('Do not apply boost - decision violates safety principles')
        elif supervisor_verdict == 'CAUTION':
            recommendations.append('Apply boost with reduced size or wait for confirmation')
        elif supervisor_verdict == 'REVIEW':
            recommendations.append('Manual review required before applying boost')
        else:  # APPROVE
            recommendations.append('Boost approved - all checks passed')

        # Store decision
        self.decision_history.append({
            'ticker': ticker,
            'timestamp': timestamp,
            'original_decision': original_decision,
            'supervisor_verdict': supervisor_verdict,
            'confidence_score': confidence_score
        })

        return SupervisionResult(
            ticker=ticker,
            timestamp=timestamp,
            original_decision=original_decision,
            supervisor_verdict=supervisor_verdict,
            confidence_score=confidence_score,
            alignment_issues=alignment_issues,
            reasoning=reasoning,
            recommendations=recommendations,
            risk_flags=risk_flags
        )

    def track_outcome(
        self,
        ticker: str,
        boost_decision: str,
        predicted_return: float,
        actual_return: Optional[float] = None,
        holding_period: int = 30
    ) -> Dict:
        """
        Track outcome of a boost decision for future calibration.

        Args:
            ticker: Stock symbol
            boost_decision: What was decided (APPLY_BOOST, NO_BOOST, etc)
            predicted_return: Expected return % from analysis
            actual_return: Actual return if available
            holding_period: Days held (default 30)

        Returns:
            Outcome assessment
        """
        outcome = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'boost_decision': boost_decision,
            'predicted_return': predicted_return,
            'actual_return': actual_return,
            'holding_period': holding_period,
            'success': None,
            'confidence_in_prediction': 'unknown'
        }

        # Determine success
        if actual_return is not None:
            # Consider success if actual >= 70% of predicted
            threshold = predicted_return * 0.70
            outcome['success'] = actual_return >= threshold

            # Confidence assessment
            if abs(actual_return - predicted_return) < predicted_return * 0.1:
                outcome['confidence_in_prediction'] = 'high'
            elif abs(actual_return - predicted_return) < predicted_return * 0.3:
                outcome['confidence_in_prediction'] = 'medium'
            else:
                outcome['confidence_in_prediction'] = 'low'

        # Store outcome
        if ticker not in self.outcome_tracking:
            self.outcome_tracking[ticker] = []
        self.outcome_tracking[ticker].append(outcome)

        # Update metrics
        self._update_performance_metrics()

        return outcome

    def get_performance_report(self) -> Dict:
        """
        Generate performance report for model calibration.

        Returns:
            {
                'total_boosts': int,
                'successful': int,
                'failed': int,
                'precision': float 0-1,
                'hit_rate': float 0-1,
                'avg_return': float %,
                'recent_accuracy': float,
                'by_market_regime': {},
                'recommendations': []
            }
        """
        total = self.performance_metrics['total_boosts']
        successful = self.performance_metrics['successful_boosts']
        failed = self.performance_metrics['failed_boosts']

        precision = successful / total if total > 0 else 0.0
        hit_rate = (successful / total) if total > 0 else 0.0

        # Accuracy warnings
        alerts = []
        if precision < 0.75:
            alerts.append(f'⚠️  Precision below 75%: {precision:.1%} - Recalibrate thresholds')
        if (failed / total) > 0.20 if total > 0 else False:
            alerts.append(f'⚠️  False positive rate high: {(failed/total):.1%} - Review reversal confirmation')

        # Recent accuracy (last 20 decisions)
        recent = self.decision_history[-20:] if len(self.decision_history) >= 20 else self.decision_history
        recent_approvals = [d for d in recent if d['supervisor_verdict'] in ['APPROVE', 'CAUTION']]
        recent_accuracy = len([d for d in recent_approvals if d.get('outcome_success')]) / len(recent_approvals) if recent_approvals else 0.0

        return {
            'total_boosts_analyzed': total,
            'successful_boosts': successful,
            'failed_boosts': failed,
            'precision': round(precision, 4),
            'hit_rate': round(hit_rate, 4),
            'avg_return_pct': round(self.performance_metrics['avg_return'], 2),
            'recent_accuracy': round(recent_accuracy, 4),
            'alerts': alerts,
            'decisions_pending_outcome': len([d for d in self.decision_history if not d.get('outcome_tracked')]),
            'calibration_recommendations': self._generate_calibration_recommendations()
        }

    def analyze_decision_pattern(self, recent_days: int = 7) -> Dict:
        """
        Analyze patterns in recent decisions for alignment issues.

        Args:
            recent_days: Number of days to look back

        Returns:
            Pattern analysis with insights
        """
        cutoff = datetime.now() - timedelta(days=recent_days)
        recent_decisions = [
            d for d in self.decision_history
            if datetime.fromisoformat(d['timestamp']) > cutoff
        ]

        if not recent_decisions:
            return {'analysis': 'No recent decisions', 'patterns': []}

        verdicts = {}
        for decision in recent_decisions:
            verdict = decision['supervisor_verdict']
            verdicts[verdict] = verdicts.get(verdict, 0) + 1

        patterns = []

        # High reject rate
        reject_rate = verdicts.get('REJECT', 0) / len(recent_decisions)
        if reject_rate > 0.30:
            patterns.append({
                'pattern': 'HIGH_REJECTION_RATE',
                'severity': 'warning',
                'message': f'30%+ decisions rejected in last {recent_days}d - Review decision logic'
            })

        # Low approval rate
        approve_rate = verdicts.get('APPROVE', 0) / len(recent_decisions)
        if approve_rate < 0.20:
            patterns.append({
                'pattern': 'LOW_APPROVAL_RATE',
                'severity': 'info',
                'message': f'<20% decisions approved - Market may lack good setups'
            })

        # High caution rate
        caution_rate = verdicts.get('CAUTION', 0) / len(recent_decisions)
        if caution_rate > 0.50:
            patterns.append({
                'pattern': 'UNCERTAIN_DECISIONS',
                'severity': 'warning',
                'message': f'>50% decisions flagged CAUTION - Thresholds may be too strict'
            })

        return {
            'period': f'Last {recent_days} days',
            'total_decisions': len(recent_decisions),
            'verdict_distribution': verdicts,
            'patterns': patterns,
            'recommendation': self._get_pattern_recommendation(verdicts)
        }

    def generate_alignment_report(self) -> Dict:
        """
        Generate comprehensive alignment report for strategy verification.
        """
        decisions = self.decision_history

        if not decisions:
            return {'status': 'NO_DATA', 'message': 'No decisions to analyze'}

        verdicts = {}
        for d in decisions:
            verdict = d['supervisor_verdict']
            verdicts[verdict] = verdicts.get(verdict, 0) + 1

        total = len(decisions)
        approval_rate = (verdicts.get('APPROVE', 0) + verdicts.get('CAUTION', 0)) / total

        return {
            'total_decisions_supervised': total,
            'approved_count': verdicts.get('APPROVE', 0),
            'caution_count': verdicts.get('CAUTION', 0),
            'rejected_count': verdicts.get('REJECT', 0),
            'review_count': verdicts.get('REVIEW', 0),
            'approval_rate': round(approval_rate, 4),
            'last_updated': datetime.now().isoformat(),
            'alignment_status': 'ALIGNED' if approval_rate > 0.60 else 'NEEDS_REVIEW',
            'performance': self.get_performance_report()
        }

    # ==================== PRIVATE METHODS ====================

    def _generate_reasoning(
        self,
        alignment_issues: List[str],
        risk_flags: List[str],
        original_decision: str,
        supervisor_verdict: str,
        correction_confidence: float
    ) -> str:
        """Generate detailed reasoning for supervisor verdict."""
        lines = []

        if supervisor_verdict == 'APPROVE':
            lines.append(f'✅ Decision approved - All confirmation layers passed')
            lines.append(f'Correction confidence: {correction_confidence:.2f}/1.0 (sufficient)')

        elif supervisor_verdict == 'CAUTION':
            lines.append(f'⚠️  Decision flagged for caution review')
            if alignment_issues:
                lines.append(f'Issues: {alignment_issues[0]}')
            lines.append(f'Recommendation: Verify or reduce position size')

        elif supervisor_verdict == 'REJECT':
            lines.append(f'❌ Decision rejected - Safety principles violated')
            if risk_flags:
                lines.append(f'Risk: {risk_flags[0]}')
            lines.append(f'No boost will be applied')

        elif supervisor_verdict == 'REVIEW':
            lines.append(f'🔍 Manual review required')
            lines.append(f'Original decision status: {original_decision}')

        return ' | '.join(lines)

    def _generate_calibration_recommendations(self) -> List[str]:
        """Generate recommendations based on performance trends."""
        recommendations = []
        precision = self.performance_metrics.get('precision', 0)

        if precision < 0.65:
            recommendations.append('Increase reversal confirmation requirements')
            recommendations.append('Raise oversold score minimum to 40')
            recommendations.append('Require catalyst strength ≥ 15')

        elif precision < 0.75:
            recommendations.append('Tighten fundamental confidence requirement')
            recommendations.append('Increase minimum consolidation period')
            recommendations.append('Add sector momentum check')

        else:
            recommendations.append('Current thresholds performing well - maintain')
            recommendations.append('Consider slight market regime adjustments')

        return recommendations

    def _update_performance_metrics(self):
        """Update aggregated performance metrics."""
        successful = 0
        failed = 0

        for ticker_outcomes in self.outcome_tracking.values():
            for outcome in ticker_outcomes:
                if outcome['success'] is not None:
                    if outcome['success']:
                        successful += 1
                    else:
                        failed += 1

        total = successful + failed
        self.performance_metrics.update({
            'total_boosts': total,
            'successful_boosts': successful,
            'failed_boosts': failed,
            'precision': successful / total if total > 0 else 0.0,
            'hit_rate': successful / total if total > 0 else 0.0
        })

    def _get_pattern_recommendation(self, verdicts: Dict) -> str:
        """Get recommendation based on verdict distribution."""
        total = sum(verdicts.values())
        if total == 0:
            return 'No data'

        reject_rate = verdicts.get('REJECT', 0) / total

        if reject_rate > 0.40:
            return 'Consider relaxing thresholds - too many rejections'
        elif reject_rate < 0.10:
            return 'Consider tightening risk filters - few rejections may indicate insufficient safety'
        else:
            return 'Current rejection rate is balanced'

    def get_decision_history(self, limit: int = 100) -> List[Dict]:
        """Get recent decision history."""
        return self.decision_history[-limit:]

    def export_supervision_log(self, filepath: str):
        """Export supervision log to JSON."""
        with open(filepath, 'w') as f:
            json.dump({
                'decisions': self.decision_history,
                'outcomes': {k: v for k, v in self.outcome_tracking.items()},
                'performance': self.get_performance_report(),
                'exported_at': datetime.now().isoformat()
            }, f, indent=2)
        logger.info(f'Supervision log exported to {filepath}')


if __name__ == '__main__':
    # Test
    supervisor = AICorrectionSupervisor()

    # Mock analysis
    mock_analysis = {
        'ticker': 'TCS.NS',
        'final_decision': 'APPLY_BOOST',
        'layers_passed': ['Correction Detected', 'Reversal Confirmed', 'Risk Filters Passed'],
        'layers_failed': [],
        'correction_confidence': 0.68,
        'fundamental_confidence': 62,
        'oversold_score': 75,
        'catalyst_strength': 28,
        'market_context': 'bull'
    }

    result = supervisor.assess_boost_decision(mock_analysis)
    print(f"\n=== SUPERVISION RESULT ===")
    print(f"Verdict: {result.supervisor_verdict}")
    print(f"Confidence: {result.confidence_score:.2f}")
    print(f"Reasoning: {result.reasoning}")
    print(f"Risk Flags: {', '.join(result.risk_flags) if result.risk_flags else 'None'}")
