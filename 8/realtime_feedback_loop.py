#!/usr/bin/env python3
"""
Real-Time AI Feedback Loop - Learning System
Tracks predictions vs actual performance and dynamically adjusts AI weights

Usage:
    # Record initial prediction
    python3 realtime_feedback_loop.py --record SAGILITY --score 81 --action BUY --price 245.0

    # Update with actual performance (3 hours later)
    python3 realtime_feedback_loop.py --update SAGILITY --current-price 238.5

    # Generate updated configuration
    python3 realtime_feedback_loop.py --learn --output updated_config.json

    # View performance report
    python3 realtime_feedback_loop.py --report
"""

import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse
from pathlib import Path

# File paths
PREDICTIONS_DB = 'learning/predictions_tracking.json'
PERFORMANCE_DB = 'learning/performance_history.json'
LEARNED_CONFIG = 'learning/learned_weights.json'

# Default weights (baseline)
DEFAULT_WEIGHTS = {
    'technical_overbought': 0.15,
    'resistance_levels': 0.12,
    'volume_confirmation': 0.08,
    'fundamental_catalyst': 0.25,
    'sentiment_momentum': 0.20,
    'certainty_score': 0.20
}

# Catalyst effectiveness baseline
DEFAULT_CATALYST_SCORES = {
    'earnings_beat': 90,
    'order_book_expansion': 85,
    'investment_announcement': 80,
    'technical_breakout': 75,
    'sector_momentum': 70,
    'partnership': 75,
    'expansion': 78,
    'contract_win': 82,
    'negative_earnings': 30
}


class FeedbackLoopTracker:
    """Tracks predictions and actual outcomes for learning"""

    def __init__(self):
        self.predictions = self._load_predictions()
        self.performance = self._load_performance()
        self.weights = self._load_learned_weights()

    def _load_predictions(self) -> Dict:
        """Load active predictions"""
        if os.path.exists(PREDICTIONS_DB):
            with open(PREDICTIONS_DB, 'r') as f:
                return json.load(f)
        return {}

    def _load_performance(self) -> List[Dict]:
        """Load historical performance data"""
        if os.path.exists(PERFORMANCE_DB):
            with open(PERFORMANCE_DB, 'r') as f:
                return json.load(f)
        return []

    def _load_learned_weights(self) -> Dict:
        """Load previously learned weights or defaults"""
        if os.path.exists(LEARNED_CONFIG):
            with open(LEARNED_CONFIG, 'r') as f:
                data = json.load(f)
                return data.get('weights', DEFAULT_WEIGHTS)
        return DEFAULT_WEIGHTS.copy()

    def _save_predictions(self):
        """Save predictions to disk"""
        os.makedirs(os.path.dirname(PREDICTIONS_DB), exist_ok=True)
        with open(PREDICTIONS_DB, 'w') as f:
            json.dump(self.predictions, f, indent=2)

    def _save_performance(self):
        """Save performance history to disk"""
        os.makedirs(os.path.dirname(PERFORMANCE_DB), exist_ok=True)
        with open(PERFORMANCE_DB, 'w') as f:
            json.dump(self.performance, f, indent=2)

    def record_prediction(self, ticker: str, analysis: Dict):
        """Record an AI prediction for tracking"""
        prediction = {
            'timestamp': datetime.now().isoformat(),
            'ticker': ticker,
            'score': analysis.get('score', 0),
            'recommendation': analysis.get('recommendation', 'HOLD'),
            'sentiment': analysis.get('sentiment', 'neutral'),
            'catalysts': analysis.get('catalysts', []),
            'initial_price': analysis.get('technical_analysis', {}).get('current_price', 0),
            'target_1': analysis.get('swing_trade_setup', {}).get('target_1', 0),
            'target_2': analysis.get('swing_trade_setup', {}).get('target_2', 0),
            'stop_loss': analysis.get('swing_trade_setup', {}).get('stop_loss', 0),
            'expected_move_pct': analysis.get('expected_move_pct', 0),
            'certainty': analysis.get('certainty', 0),
            'rsi': analysis.get('technical_analysis', {}).get('rsi', 50),
            'volume_trend': analysis.get('technical_analysis', {}).get('volume_trend', 'average'),
            'weights_used': self.weights.copy()
        }

        self.predictions[ticker] = prediction
        self._save_predictions()

        print(f"✅ Recorded prediction for {ticker}: {analysis.get('recommendation')} @ ₹{prediction['initial_price']}")

    def update_actual_performance(self, ticker: str, current_price: float,
                                   volume_change_pct: float = 0,
                                   current_rsi: int = 50):
        """Update with actual market performance"""
        if ticker not in self.predictions:
            print(f"❌ No prediction found for {ticker}")
            return

        pred = self.predictions[ticker]
        initial_price = pred['initial_price']

        if initial_price == 0:
            print(f"❌ Invalid initial price for {ticker}")
            return

        # Calculate actual performance
        actual_change_pct = ((current_price - initial_price) / initial_price) * 100

        # Determine if prediction was correct
        prediction_correct = self._evaluate_prediction(pred, actual_change_pct)

        # Create performance record
        performance_record = {
            'timestamp': datetime.now().isoformat(),
            'prediction_time': pred['timestamp'],
            'ticker': ticker,
            'initial_price': initial_price,
            'current_price': current_price,
            'actual_change_pct': actual_change_pct,
            'predicted_move_pct': pred['expected_move_pct'],
            'recommendation': pred['recommendation'],
            'score': pred['score'],
            'certainty': pred['certainty'],
            'catalysts': pred['catalysts'],
            'initial_rsi': pred['rsi'],
            'current_rsi': current_rsi,
            'volume_change_pct': volume_change_pct,
            'volume_trend': pred['volume_trend'],
            'prediction_correct': prediction_correct,
            'prediction_accuracy': self._calculate_accuracy(pred['expected_move_pct'], actual_change_pct),
            'weights_used': pred['weights_used']
        }

        # Add to performance history
        self.performance.append(performance_record)
        self._save_performance()

        # Remove from active predictions
        del self.predictions[ticker]
        self._save_predictions()

        print(f"\n📊 Performance Update: {ticker}")
        print(f"   Predicted: {pred['expected_move_pct']:+.2f}% | Actual: {actual_change_pct:+.2f}%")
        print(f"   Recommendation: {pred['recommendation']} | Correct: {'✅' if prediction_correct else '❌'}")
        print(f"   Accuracy: {performance_record['prediction_accuracy']:.1f}%")

        return performance_record

    def _evaluate_prediction(self, prediction: Dict, actual_change_pct: float) -> bool:
        """Determine if prediction was directionally correct"""
        recommendation = prediction['recommendation']

        if recommendation in ['STRONG BUY', 'BUY']:
            return actual_change_pct > 0  # Should go up
        elif recommendation in ['SELL', 'REDUCE']:
            return actual_change_pct < 0  # Should go down
        elif recommendation == 'HOLD':
            return abs(actual_change_pct) < 2  # Should stay flat
        else:
            return True  # ACCUMULATE - any positive is good

    def _calculate_accuracy(self, predicted_pct: float, actual_pct: float) -> float:
        """Calculate prediction accuracy percentage"""
        if predicted_pct == 0:
            return 0

        error = abs(predicted_pct - actual_pct)
        max_error = abs(predicted_pct) + abs(actual_pct)

        if max_error == 0:
            return 100

        accuracy = max(0, 100 - (error / max_error * 100))
        return accuracy

    def learn_from_performance(self) -> Dict:
        """Analyze performance and update weights"""
        if len(self.performance) < 3:
            print(f"⚠️  Need at least 3 performance records to learn (have {len(self.performance)})")
            return self.weights

        print(f"\n🧠 Learning from {len(self.performance)} performance records...")

        # Analyze recent performance (last 20 records or all if less)
        recent_performance = self.performance[-20:]

        # Calculate success rates for different factors
        analysis = self._analyze_performance_patterns(recent_performance)

        # Update weights based on analysis
        updated_weights = self._update_weights(analysis)

        # Update catalyst scores
        updated_catalyst_scores = self._update_catalyst_scores(recent_performance)

        # Save learned configuration
        learned_config = {
            'weights': updated_weights,
            'catalyst_scores': updated_catalyst_scores,
            'learning_timestamp': datetime.now().isoformat(),
            'samples_analyzed': len(recent_performance),
            'overall_accuracy': analysis['overall_accuracy'],
            'insights': analysis['insights']
        }

        os.makedirs(os.path.dirname(LEARNED_CONFIG), exist_ok=True)
        with open(LEARNED_CONFIG, 'w') as f:
            json.dump(learned_config, f, indent=2)

        self.weights = updated_weights

        print(f"✅ Learning complete! Overall accuracy: {analysis['overall_accuracy']:.1f}%")
        self._print_weight_changes(DEFAULT_WEIGHTS, updated_weights)

        return learned_config

    def _analyze_performance_patterns(self, records: List[Dict]) -> Dict:
        """Analyze patterns in performance data"""
        total = len(records)
        correct = sum(1 for r in records if r['prediction_correct'])

        # Analyze by different factors
        overbought_analysis = self._analyze_factor(records, 'initial_rsi', lambda rsi: rsi > 70, 'Overbought stocks')
        volume_analysis = self._analyze_factor(records, 'volume_change_pct', lambda v: v > 20, 'High volume stocks')
        high_certainty_analysis = self._analyze_factor(records, 'certainty', lambda c: c > 70, 'High certainty predictions')
        catalyst_analysis = self._analyze_catalyst_performance(records)

        overall_accuracy = (correct / total * 100) if total > 0 else 0

        insights = []

        # Generate insights
        if overbought_analysis['success_rate'] < 40:
            insights.append(f"Overbought stocks (RSI>70) have low success rate ({overbought_analysis['success_rate']:.0f}%) - increase overbought penalty")

        if volume_analysis['success_rate'] > 70:
            insights.append(f"High volume confirmations perform well ({volume_analysis['success_rate']:.0f}%) - increase volume weight")

        if high_certainty_analysis['success_rate'] < 60:
            insights.append(f"High certainty predictions underperforming ({high_certainty_analysis['success_rate']:.0f}%) - recalibrate certainty scoring")

        return {
            'overall_accuracy': overall_accuracy,
            'overbought_analysis': overbought_analysis,
            'volume_analysis': volume_analysis,
            'high_certainty_analysis': high_certainty_analysis,
            'catalyst_analysis': catalyst_analysis,
            'insights': insights
        }

    def _analyze_factor(self, records: List[Dict], field: str, condition, label: str) -> Dict:
        """Analyze success rate for a specific factor"""
        matching = [r for r in records if condition(r.get(field, 0))]

        if not matching:
            return {'count': 0, 'success_rate': 0, 'label': label}

        correct = sum(1 for r in matching if r['prediction_correct'])
        success_rate = (correct / len(matching) * 100) if matching else 0

        return {
            'count': len(matching),
            'success_rate': success_rate,
            'label': label
        }

    def _analyze_catalyst_performance(self, records: List[Dict]) -> Dict:
        """Analyze performance by catalyst type"""
        catalyst_stats = {}

        for record in records:
            catalysts = record.get('catalysts', [])
            correct = record['prediction_correct']

            for catalyst in catalysts:
                if catalyst not in catalyst_stats:
                    catalyst_stats[catalyst] = {'total': 0, 'correct': 0}

                catalyst_stats[catalyst]['total'] += 1
                if correct:
                    catalyst_stats[catalyst]['correct'] += 1

        # Calculate success rates
        for catalyst, stats in catalyst_stats.items():
            stats['success_rate'] = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0

        return catalyst_stats

    def _update_weights(self, analysis: Dict) -> Dict:
        """Update weights based on performance analysis"""
        new_weights = self.weights.copy()

        # Adjust overbought weight
        if analysis['overbought_analysis']['success_rate'] < 40:
            new_weights['technical_overbought'] = min(0.30, new_weights['technical_overbought'] * 1.3)

        # Adjust volume weight
        if analysis['volume_analysis']['success_rate'] > 70:
            new_weights['volume_confirmation'] = min(0.20, new_weights['volume_confirmation'] * 1.5)

        # Adjust certainty weight
        if analysis['high_certainty_analysis']['success_rate'] < 60:
            new_weights['certainty_score'] = max(0.05, new_weights['certainty_score'] * 0.7)

        # Normalize weights to sum to 1.0
        total = sum(new_weights.values())
        for key in new_weights:
            new_weights[key] = new_weights[key] / total

        return new_weights

    def _update_catalyst_scores(self, records: List[Dict]) -> Dict:
        """Update catalyst effectiveness scores"""
        catalyst_stats = self._analyze_catalyst_performance(records)
        updated_scores = DEFAULT_CATALYST_SCORES.copy()

        for catalyst, stats in catalyst_stats.items():
            if stats['total'] >= 2:  # Need at least 2 samples
                success_rate = stats['success_rate']

                # Map success rate to score (30-95 range)
                if success_rate >= 80:
                    updated_scores[catalyst] = 92
                elif success_rate >= 70:
                    updated_scores[catalyst] = 85
                elif success_rate >= 60:
                    updated_scores[catalyst] = 75
                elif success_rate >= 50:
                    updated_scores[catalyst] = 65
                else:
                    updated_scores[catalyst] = 55

        return updated_scores

    def _print_weight_changes(self, old_weights: Dict, new_weights: Dict):
        """Print weight changes in a readable format"""
        print("\n📊 Weight Adjustments:")
        print("-" * 60)

        for key in sorted(old_weights.keys()):
            old = old_weights[key]
            new = new_weights[key]
            change_pct = ((new - old) / old * 100) if old > 0 else 0

            arrow = "↑" if change_pct > 0 else "↓" if change_pct < 0 else "→"
            print(f"{key:25s}: {old:.3f} → {new:.3f} {arrow} {abs(change_pct):5.1f}%")

    def generate_performance_report(self) -> str:
        """Generate a comprehensive performance report"""
        if not self.performance:
            return "No performance data available yet."

        total = len(self.performance)
        correct = sum(1 for r in self.performance if r['prediction_correct'])
        accuracy = (correct / total * 100) if total > 0 else 0

        # Calculate by recommendation type
        by_recommendation = {}
        for record in self.performance:
            rec = record['recommendation']
            if rec not in by_recommendation:
                by_recommendation[rec] = {'total': 0, 'correct': 0}

            by_recommendation[rec]['total'] += 1
            if record['prediction_correct']:
                by_recommendation[rec]['correct'] += 1

        # Recent performance (last 10)
        recent = self.performance[-10:]
        recent_correct = sum(1 for r in recent if r['prediction_correct'])
        recent_accuracy = (recent_correct / len(recent) * 100) if recent else 0

        # Build report
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║            AI PERFORMANCE REPORT                              ║
╠══════════════════════════════════════════════════════════════╣
║ Total Predictions: {total:>3}                                      ║
║ Correct Predictions: {correct:>3}                                    ║
║ Overall Accuracy: {accuracy:>5.1f}%                                  ║
║ Recent Accuracy (last 10): {recent_accuracy:>5.1f}%                        ║
╠══════════════════════════════════════════════════════════════╣
║ By Recommendation Type:                                      ║
"""

        for rec, stats in sorted(by_recommendation.items()):
            acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            report += f"║   {rec:12s}: {stats['correct']:>2}/{stats['total']:>2} ({acc:>5.1f}%)                         ║\n"

        report += "╚══════════════════════════════════════════════════════════════╝"

        return report


def main():
    parser = argparse.ArgumentParser(description='Real-time AI Feedback Loop')
    parser.add_argument('--record', type=str, help='Record prediction for ticker')
    parser.add_argument('--score', type=float, help='AI score')
    parser.add_argument('--action', type=str, help='Recommendation (BUY/SELL/HOLD)')
    parser.add_argument('--price', type=float, help='Current price')
    parser.add_argument('--analysis-file', type=str, help='Path to full analysis JSON')

    parser.add_argument('--update', type=str, help='Update actual performance for ticker')
    parser.add_argument('--current-price', type=float, help='Current market price')
    parser.add_argument('--volume-change', type=float, default=0, help='Volume change percentage')
    parser.add_argument('--current-rsi', type=int, default=50, help='Current RSI')

    parser.add_argument('--learn', action='store_true', help='Run learning algorithm')
    parser.add_argument('--output', type=str, help='Output file for learned config')

    parser.add_argument('--report', action='store_true', help='Generate performance report')

    args = parser.parse_args()

    tracker = FeedbackLoopTracker()

    # Record prediction
    if args.record:
        if args.analysis_file:
            # Load full analysis
            with open(args.analysis_file, 'r') as f:
                analysis = json.load(f)
        else:
            # Build minimal analysis from args
            analysis = {
                'score': args.score or 50,
                'recommendation': args.action or 'HOLD',
                'technical_analysis': {'current_price': args.price or 0},
                'swing_trade_setup': {},
                'expected_move_pct': 0,
                'certainty': 50,
                'catalysts': []
            }

        tracker.record_prediction(args.record, analysis)

    # Update actual performance
    elif args.update:
        if not args.current_price:
            print("❌ --current-price required for updates")
            return 1

        tracker.update_actual_performance(
            args.update,
            args.current_price,
            args.volume_change,
            args.current_rsi
        )

    # Run learning
    elif args.learn:
        config = tracker.learn_from_performance()

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"\n💾 Saved learned configuration to: {args.output}")

    # Generate report
    elif args.report:
        report = tracker.generate_performance_report()
        print(report)

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
