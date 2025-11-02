#!/usr/bin/env python3
"""
Adaptive AI Analyzer - Uses Learned Weights for Better Predictions
Integrates feedback loop learning into the analysis pipeline

Usage:
    # Analyze with learned weights
    python3 adaptive_ai_analyzer.py --ticker RELIANCE --news-file reliance_news.json

    # Compare: Standard vs Adaptive analysis
    python3 adaptive_ai_analyzer.py --ticker RELIANCE --news-file reliance_news.json --compare

    # Auto-record predictions for feedback loop
    python3 adaptive_ai_analyzer.py --ticker RELIANCE --news-file reliance_news.json --auto-record
"""

import json
import os
import sys
import argparse
from typing import Dict, Optional
from realtime_feedback_loop import FeedbackLoopTracker

# Import your existing analyzer (adjust path as needed)
# from realtime_ai_news_analyzer import analyze_stock_news


class AdaptiveAIAnalyzer:
    """AI Analyzer that adapts based on historical performance"""

    def __init__(self, use_learned_weights: bool = True):
        self.tracker = FeedbackLoopTracker()
        self.use_learned_weights = use_learned_weights

        if use_learned_weights:
            self.weights = self.tracker.weights
            self.catalyst_scores = self._load_catalyst_scores()
        else:
            self.weights = self.tracker._load_learned_weights()  # defaults
            self.catalyst_scores = {}

    def _load_catalyst_scores(self) -> Dict:
        """Load learned catalyst effectiveness scores"""
        if os.path.exists('learning/learned_weights.json'):
            with open('learning/learned_weights.json', 'r') as f:
                data = json.load(f)
                return data.get('catalyst_scores', {})
        return {}

    def adjust_score_with_learned_weights(self, base_analysis: Dict) -> Dict:
        """
        Adjust AI score using learned weights
        This applies the feedback loop learnings to improve predictions
        """

        base_score = base_analysis.get('score', 50)
        technical_analysis = base_analysis.get('technical_analysis', {})
        catalysts = base_analysis.get('catalysts', [])

        # Apply learned weight adjustments
        adjustments = []

        # 1. Overbought penalty (learned from SAGILITY failure)
        rsi = technical_analysis.get('rsi', 50)
        if rsi > 70:
            overbought_penalty = self.weights.get('technical_overbought', 0.15) * 100
            adjustments.append({
                'factor': 'Overbought (RSI > 70)',
                'adjustment': -overbought_penalty,
                'reason': f'RSI {rsi} indicates profit booking risk'
            })

        # 2. Volume confirmation boost (learned from BHEL failure)
        volume_trend = technical_analysis.get('volume_trend', 'average')
        if volume_trend == 'increasing':
            volume_boost = self.weights.get('volume_confirmation', 0.08) * 50
            adjustments.append({
                'factor': 'Volume Confirmation',
                'adjustment': +volume_boost,
                'reason': 'Strong volume supports move'
            })
        elif volume_trend == 'decreasing':
            volume_penalty = self.weights.get('volume_confirmation', 0.08) * 30
            adjustments.append({
                'factor': 'Weak Volume',
                'adjustment': -volume_penalty,
                'reason': 'Low volume questions sustainability'
            })

        # 3. Fundamental catalyst boost (learned from WORTH success)
        strong_fundamentals = any(cat in ['order_book_expansion', 'earnings_beat', 'contract_win']
                                  for cat in catalysts)
        if strong_fundamentals:
            fundamental_boost = self.weights.get('fundamental_catalyst', 0.25) * 30
            adjustments.append({
                'factor': 'Strong Fundamental Catalyst',
                'adjustment': +fundamental_boost,
                'reason': 'Fundamentals override technical resistance'
            })

        # 4. Catalyst-specific adjustments
        for catalyst in catalysts:
            if catalyst in self.catalyst_scores:
                learned_score = self.catalyst_scores[catalyst]
                base_catalyst_score = 75  # baseline

                if learned_score > base_catalyst_score:
                    boost = (learned_score - base_catalyst_score) * 0.2
                    adjustments.append({
                        'factor': f'Catalyst: {catalyst}',
                        'adjustment': +boost,
                        'reason': f'Historical success rate: {learned_score}/100'
                    })
                elif learned_score < base_catalyst_score:
                    penalty = (base_catalyst_score - learned_score) * 0.2
                    adjustments.append({
                        'factor': f'Catalyst: {catalyst}',
                        'adjustment': -penalty,
                        'reason': f'Historical underperformance: {learned_score}/100'
                    })

        # Calculate adjusted score
        total_adjustment = sum(adj['adjustment'] for adj in adjustments)
        adjusted_score = max(0, min(100, base_score + total_adjustment))

        # Update recommendation based on adjusted score
        adjusted_recommendation = self._score_to_recommendation(adjusted_score, base_analysis.get('sentiment', 'neutral'))

        return {
            **base_analysis,
            'original_score': base_score,
            'adjusted_score': round(adjusted_score, 1),
            'score_adjustments': adjustments,
            'total_adjustment': round(total_adjustment, 1),
            'original_recommendation': base_analysis.get('recommendation'),
            'adjusted_recommendation': adjusted_recommendation,
            'learning_applied': True,
            'weights_version': 'learned' if self.use_learned_weights else 'default'
        }

    def _score_to_recommendation(self, score: float, sentiment: str) -> str:
        """Convert adjusted score to recommendation"""
        if sentiment == 'bearish':
            if score < 40:
                return 'SELL'
            elif score < 55:
                return 'REDUCE'
            else:
                return 'HOLD'
        else:  # bullish or neutral
            if score >= 85:
                return 'STRONG BUY'
            elif score >= 75:
                return 'BUY'
            elif score >= 60:
                return 'ACCUMULATE'
            else:
                return 'HOLD'

    def analyze_with_adaptation(self, ticker: str, news_data: Dict,
                                base_analyzer_func=None) -> Dict:
        """
        Run analysis with adaptive learning

        Args:
            ticker: Stock ticker
            news_data: News article data
            base_analyzer_func: Function that performs base analysis

        Returns:
            Adapted analysis with learned adjustments
        """

        # Step 1: Get base analysis (from your existing system)
        if base_analyzer_func:
            base_analysis = base_analyzer_func(ticker, news_data)
        else:
            # Mock base analysis for testing
            base_analysis = self._mock_base_analysis(ticker, news_data)

        # Step 2: Apply learned adaptations
        adapted_analysis = self.adjust_score_with_learned_weights(base_analysis)

        return adapted_analysis

    def _mock_base_analysis(self, ticker: str, news_data: Dict) -> Dict:
        """Mock analysis for testing"""
        return {
            'score': 75,
            'recommendation': 'BUY',
            'sentiment': 'bullish',
            'catalysts': ['earnings_beat'],
            'certainty': 70,
            'expected_move_pct': 6.5,
            'technical_analysis': {
                'current_price': 250.0,
                'rsi': 65,
                'volume_trend': 'increasing'
            },
            'swing_trade_setup': {
                'target_1': 270,
                'target_2': 285,
                'stop_loss': 240
            }
        }

    def compare_analyses(self, ticker: str, news_data: Dict) -> Dict:
        """Compare standard vs adaptive analysis"""

        print("\n" + "="*70)
        print("COMPARISON: Standard AI vs Adaptive AI (with Learning)")
        print("="*70)

        # Standard analysis
        standard_analyzer = AdaptiveAIAnalyzer(use_learned_weights=False)
        standard_result = standard_analyzer.analyze_with_adaptation(ticker, news_data)

        # Adaptive analysis
        adaptive_result = self.analyze_with_adaptation(ticker, news_data)

        comparison = {
            'ticker': ticker,
            'standard': {
                'score': standard_result.get('original_score', 0),
                'recommendation': standard_result.get('original_recommendation', 'HOLD')
            },
            'adaptive': {
                'score': adaptive_result.get('adjusted_score', 0),
                'recommendation': adaptive_result.get('adjusted_recommendation', 'HOLD'),
                'adjustments': adaptive_result.get('score_adjustments', [])
            }
        }

        # Print comparison
        print(f"\nStandard AI:")
        print(f"  Score: {comparison['standard']['score']}")
        print(f"  Recommendation: {comparison['standard']['recommendation']}")

        print(f"\nAdaptive AI (with learning):")
        print(f"  Score: {comparison['adaptive']['score']}")
        print(f"  Recommendation: {comparison['adaptive']['recommendation']}")

        if adaptive_result.get('score_adjustments'):
            print(f"\n  Adjustments applied:")
            for adj in adaptive_result['score_adjustments']:
                sign = "+" if adj['adjustment'] > 0 else ""
                print(f"    • {adj['factor']}: {sign}{adj['adjustment']:.1f}")
                print(f"      → {adj['reason']}")

        score_diff = comparison['adaptive']['score'] - comparison['standard']['score']
        print(f"\n  Net change: {score_diff:+.1f} points")

        return comparison


def main():
    parser = argparse.ArgumentParser(description='Adaptive AI Analyzer with Learning')
    parser.add_argument('--ticker', type=str, required=True, help='Stock ticker')
    parser.add_argument('--news-file', type=str, help='Path to news JSON file')
    parser.add_argument('--compare', action='store_true', help='Compare standard vs adaptive')
    parser.add_argument('--auto-record', action='store_true', help='Auto-record prediction for feedback loop')
    parser.add_argument('--no-learning', action='store_true', help='Disable learned weights')

    args = parser.parse_args()

    # Load news data
    if args.news_file and os.path.exists(args.news_file):
        with open(args.news_file, 'r') as f:
            news_data = json.load(f)
    else:
        news_data = {'headline': 'Test news', 'content': 'Test content'}

    # Initialize analyzer
    analyzer = AdaptiveAIAnalyzer(use_learned_weights=not args.no_learning)

    # Compare mode
    if args.compare:
        comparison = analyzer.compare_analyses(args.ticker, news_data)
        print(f"\n💾 Comparison results:")
        print(json.dumps(comparison, indent=2))
        return 0

    # Standard analysis with adaptation
    result = analyzer.analyze_with_adaptation(args.ticker, news_data)

    print(f"\n📊 Analysis for {args.ticker}:")
    print(json.dumps(result, indent=2))

    # Auto-record prediction
    if args.auto_record:
        print(f"\n📝 Recording prediction for feedback loop...")
        analyzer.tracker.record_prediction(args.ticker, result)

    return 0


if __name__ == '__main__':
    sys.exit(main())
