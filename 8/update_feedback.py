#!/usr/bin/env python3
"""
Update Feedback - Track actual performance vs predictions

This script helps you update the feedback loop with actual market performance
after your predictions have had time to play out (e.g., 3 hours, 1 day, 3 days).

Usage:
    # View active predictions
    python3 update_feedback.py --list

    # Update specific ticker with current price
    python3 update_feedback.py --ticker MARUTI --current-price 12950 --current-rsi 62

    # Auto-update all predictions older than 3 hours
    python3 update_feedback.py --auto-update --min-age-hours 3

    # Generate learning report
    python3 update_feedback.py --learn
"""

import sys
import argparse
import json
from datetime import datetime, timedelta
from realtime_feedback_loop import FeedbackLoopTracker
from pathlib import Path


def list_active_predictions():
    """Display all active predictions waiting for feedback"""
    tracker = FeedbackLoopTracker()

    if not tracker.predictions:
        print("📭 No active predictions found.")
        print("   Run a new analysis to generate predictions.")
        return

    print(f"\n📊 Active Predictions: {len(tracker.predictions)}")
    print("="*80)

    for ticker, pred in tracker.predictions.items():
        timestamp = datetime.fromisoformat(pred['timestamp'])
        age_hours = (datetime.now() - timestamp).total_seconds() / 3600

        print(f"\n{ticker}")
        print(f"  Prediction time: {timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Age: {age_hours:.1f} hours")
        print(f"  Score: {pred['score']}/100")
        print(f"  Recommendation: {pred['recommendation']}")
        print(f"  Initial price: ₹{pred['initial_price']:.2f}")
        print(f"  Expected move: {pred['expected_move_pct']:+.1f}%")
        print(f"  Certainty: {pred['certainty']:.0f}%")


def update_ticker_performance(ticker: str, current_price: float,
                               volume_change_pct: float = 0,
                               current_rsi: int = 50):
    """Update actual performance for a specific ticker"""
    tracker = FeedbackLoopTracker()

    if ticker not in tracker.predictions:
        print(f"❌ No active prediction found for {ticker}")
        print(f"   Active predictions: {', '.join(tracker.predictions.keys())}")
        return False

    pred = tracker.predictions[ticker]
    initial_price = pred['initial_price']

    print(f"\n📊 Updating {ticker} Performance")
    print(f"   Initial: ₹{initial_price:.2f}")
    print(f"   Current: ₹{current_price:.2f}")
    print(f"   Change: {((current_price - initial_price) / initial_price * 100):+.2f}%")

    tracker.update_actual_performance(ticker, current_price, volume_change_pct, current_rsi)

    print("\n✅ Performance updated successfully!")
    return True


def auto_update_predictions(min_age_hours: int = 3):
    """
    Attempt to auto-update predictions by fetching current prices
    Note: This requires a price fetching mechanism
    """
    tracker = FeedbackLoopTracker()

    if not tracker.predictions:
        print("📭 No active predictions to update.")
        return

    print(f"\n🔄 Auto-updating predictions older than {min_age_hours} hours...")
    cutoff_time = datetime.now() - timedelta(hours=min_age_hours)

    updated_count = 0
    skipped_count = 0

    for ticker, pred in list(tracker.predictions.items()):
        timestamp = datetime.fromisoformat(pred['timestamp'])

        if timestamp > cutoff_time:
            print(f"⏭️  Skipping {ticker} (too recent: {timestamp.strftime('%H:%M')})")
            skipped_count += 1
            continue

        # Try to fetch current price (would need yfinance or similar)
        try:
            # TODO: Implement actual price fetching
            # For now, just show what would happen
            print(f"📊 {ticker}: Would fetch current price and update")
            # current_price = fetch_current_price(ticker)
            # tracker.update_actual_performance(ticker, current_price)
            # updated_count += 1
        except Exception as e:
            print(f"⚠️  Could not update {ticker}: {e}")

    print(f"\n✅ Auto-update complete: {updated_count} updated, {skipped_count} skipped")


def run_learning_algorithm():
    """Run the learning algorithm to update weights"""
    tracker = FeedbackLoopTracker()

    print("\n🧠 Running Learning Algorithm...")
    print(f"   Performance records: {len(tracker.performance)}")

    if len(tracker.performance) < 3:
        print(f"\n⚠️  Need at least 3 performance records to learn.")
        print(f"   Current records: {len(tracker.performance)}")
        print("\n   To generate more data:")
        print("   1. Run analysis to create predictions")
        print("   2. Wait 3-24 hours")
        print("   3. Update performance with actual results")
        print("   4. Repeat several times")
        return

    config = tracker.learn_from_performance()

    print("\n✅ Learning complete!")
    print(f"   Updated config saved to: learning/learned_weights.json")
    print(f"\n   Next analysis will use these improved weights automatically.")


def show_performance_report():
    """Display performance report"""
    tracker = FeedbackLoopTracker()
    report = tracker.generate_performance_report()
    print(report)


def main():
    parser = argparse.ArgumentParser(description='Update Feedback Loop')

    parser.add_argument('--list', action='store_true',
                        help='List active predictions')

    parser.add_argument('--ticker', type=str,
                        help='Ticker to update')
    parser.add_argument('--current-price', type=float,
                        help='Current market price')
    parser.add_argument('--volume-change', type=float, default=0,
                        help='Volume change percentage')
    parser.add_argument('--current-rsi', type=int, default=50,
                        help='Current RSI')

    parser.add_argument('--auto-update', action='store_true',
                        help='Auto-update predictions (experimental)')
    parser.add_argument('--min-age-hours', type=int, default=3,
                        help='Minimum age in hours for auto-update')

    parser.add_argument('--learn', action='store_true',
                        help='Run learning algorithm to update weights')

    parser.add_argument('--report', action='store_true',
                        help='Show performance report')

    args = parser.parse_args()

    # List predictions
    if args.list:
        list_active_predictions()
        return 0

    # Update specific ticker
    if args.ticker and args.current_price:
        success = update_ticker_performance(
            args.ticker,
            args.current_price,
            args.volume_change,
            args.current_rsi
        )
        if success:
            print("\n💡 Tip: Run `python3 update_feedback.py --learn` after updating several tickers")
        return 0 if success else 1

    # Auto-update
    if args.auto_update:
        auto_update_predictions(args.min_age_hours)
        return 0

    # Run learning
    if args.learn:
        run_learning_algorithm()
        return 0

    # Show report
    if args.report:
        show_performance_report()
        return 0

    # No action specified
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
