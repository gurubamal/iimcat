#!/usr/bin/env python3
"""
Real-Time Price Monitor - Automated Performance Tracking
Monitors stock prices and automatically updates feedback loop

Usage:
    # Monitor all active predictions (continuous)
    python3 realtime_price_monitor.py --monitor --interval 180

    # Monitor specific stocks
    python3 realtime_price_monitor.py --monitor --tickers SAGILITY,WORTH,BHEL

    # One-time check
    python3 realtime_price_monitor.py --check-all

    # Auto-learn when threshold met
    python3 realtime_price_monitor.py --monitor --auto-learn --min-samples 5
"""

import json
import os
import sys
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import subprocess

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not available. Install with: pip install yfinance")

from realtime_feedback_loop import FeedbackLoopTracker

# Configuration
PREDICTIONS_DB = 'learning/predictions_tracking.json'
CHECK_INTERVAL_SECONDS = 180  # 3 minutes default
MAX_PREDICTION_AGE_HOURS = 24  # Auto-update after 24 hours


class RealTimePriceMonitor:
    """Monitors stock prices and updates feedback loop automatically"""

    def __init__(self, tracker: Optional[FeedbackLoopTracker] = None):
        self.tracker = tracker or FeedbackLoopTracker()
        self.last_check = {}

    def fetch_current_price(self, ticker: str) -> Optional[Dict]:
        """Fetch current price and technical data for a stock"""
        if not YFINANCE_AVAILABLE:
            return self._mock_price_fetch(ticker)

        try:
            # Add .NS for NSE stocks (Indian market)
            symbol = f"{ticker}.NS" if not ticker.endswith('.NS') else ticker

            stock = yf.Ticker(symbol)
            info = stock.info

            # Get recent data for RSI/volume
            hist = stock.history(period='5d')

            if hist.empty:
                print(f"⚠️  No data for {ticker}")
                return None

            current_price = hist['Close'].iloc[-1]
            current_volume = hist['Volume'].iloc[-1]

            # Calculate volume change
            avg_volume = hist['Volume'].mean()
            volume_change_pct = ((current_volume - avg_volume) / avg_volume * 100) if avg_volume > 0 else 0

            # Simple RSI calculation (14-period)
            rsi = self._calculate_rsi(hist['Close'])

            return {
                'price': round(current_price, 2),
                'volume_change_pct': round(volume_change_pct, 1),
                'rsi': int(rsi),
                'timestamp': datetime.now().isoformat(),
                'source': 'yfinance'
            }

        except Exception as e:
            print(f"❌ Error fetching {ticker}: {e}")
            return None

    def _calculate_rsi(self, prices, period=14) -> float:
        """Calculate RSI indicator"""
        if len(prices) < period + 1:
            return 50  # Default neutral

        deltas = prices.diff()
        gains = deltas.where(deltas > 0, 0)
        losses = -deltas.where(deltas < 0, 0)

        avg_gain = gains.rolling(window=period).mean().iloc[-1]
        avg_loss = losses.rolling(window=period).mean().iloc[-1]

        if avg_loss == 0:
            return 100

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def _mock_price_fetch(self, ticker: str) -> Dict:
        """Mock price data for testing without yfinance"""
        import random

        # Generate realistic mock data
        base_price = random.uniform(100, 1000)
        change_pct = random.uniform(-5, 5)

        return {
            'price': round(base_price, 2),
            'volume_change_pct': round(random.uniform(-30, 50), 1),
            'rsi': random.randint(30, 80),
            'timestamp': datetime.now().isoformat(),
            'source': 'mock'
        }

    def check_active_predictions(self) -> List[Dict]:
        """Check all active predictions and identify those ready for update"""
        predictions = self.tracker._load_predictions()

        if not predictions:
            print("ℹ️  No active predictions to monitor")
            return []

        print(f"\n🔍 Checking {len(predictions)} active predictions...")

        updates_ready = []

        for ticker, prediction in predictions.items():
            # Check if prediction is old enough to evaluate
            pred_time = datetime.fromisoformat(prediction['timestamp'])
            age_hours = (datetime.now() - pred_time).total_seconds() / 3600

            # Fetch current price
            current_data = self.fetch_current_price(ticker)

            if not current_data:
                continue

            current_price = current_data['price']
            initial_price = prediction['initial_price']

            if initial_price == 0:
                continue

            change_pct = ((current_price - initial_price) / initial_price) * 100

            status = {
                'ticker': ticker,
                'age_hours': round(age_hours, 1),
                'initial_price': initial_price,
                'current_price': current_price,
                'change_pct': round(change_pct, 2),
                'predicted_move': prediction['expected_move_pct'],
                'recommendation': prediction['recommendation'],
                'current_data': current_data,
                'ready_for_update': age_hours >= 3  # Update after 3+ hours
            }

            updates_ready.append(status)

            # Print status
            direction = "✅" if change_pct > 0 else "❌" if change_pct < 0 else "➡️"
            ready_marker = "🔔" if status['ready_for_update'] else "⏳"

            print(f"{ready_marker} {ticker:12s} | {age_hours:>5.1f}h | "
                  f"₹{initial_price:>7.2f} → ₹{current_price:>7.2f} | "
                  f"{direction} {change_pct:>+6.2f}% | {prediction['recommendation']}")

        return updates_ready

    def auto_update_predictions(self, updates: List[Dict]) -> int:
        """Automatically update predictions that are ready"""
        updated_count = 0

        for update in updates:
            if not update['ready_for_update']:
                continue

            ticker = update['ticker']
            current_data = update['current_data']

            print(f"\n📝 Auto-updating {ticker}...")

            record = self.tracker.update_actual_performance(
                ticker,
                current_data['price'],
                current_data['volume_change_pct'],
                current_data['rsi']
            )

            if record:
                updated_count += 1

        return updated_count

    def monitor_continuous(self, interval_seconds: int = 180,
                          auto_learn: bool = False,
                          min_samples_for_learning: int = 5):
        """Continuously monitor predictions and auto-update"""
        print(f"\n🚀 Starting continuous monitoring (interval: {interval_seconds}s)")
        print(f"   Auto-learn: {auto_learn} (min samples: {min_samples_for_learning})")
        print("   Press Ctrl+C to stop\n")

        iteration = 0

        try:
            while True:
                iteration += 1
                print(f"\n{'='*60}")
                print(f"Iteration {iteration} - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*60}")

                # Check predictions
                updates = self.check_active_predictions()

                # Auto-update ready predictions
                if updates:
                    ready_count = sum(1 for u in updates if u['ready_for_update'])
                    if ready_count > 0:
                        updated = self.auto_update_predictions(updates)
                        print(f"\n✅ Updated {updated} predictions")

                        # Trigger learning if threshold met
                        if auto_learn:
                            performance_count = len(self.tracker._load_performance())
                            if performance_count >= min_samples_for_learning:
                                print(f"\n🧠 Learning threshold met ({performance_count} samples), running learning...")
                                self.tracker.learn_from_performance()

                # Wait for next iteration
                print(f"\n⏳ Waiting {interval_seconds}s until next check...")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n\n⛔ Monitoring stopped by user")
            return 0

    def generate_monitoring_dashboard(self) -> str:
        """Generate a real-time dashboard view"""
        predictions = self.tracker._load_predictions()
        performance = self.tracker._load_performance()

        if not predictions and not performance:
            return "No data available"

        dashboard = f"""
╔══════════════════════════════════════════════════════════════╗
║           REAL-TIME MONITORING DASHBOARD                      ║
╠══════════════════════════════════════════════════════════════╣
║ Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):49s} ║
╠══════════════════════════════════════════════════════════════╣
"""

        # Active predictions section
        if predictions:
            dashboard += f"║ ACTIVE PREDICTIONS ({len(predictions)}):                                  ║\n"
            dashboard += "║ " + "-" * 58 + " ║\n"

            for ticker, pred in predictions.items():
                age = (datetime.now() - datetime.fromisoformat(pred['timestamp'])).total_seconds() / 3600
                dashboard += f"║ {ticker:8s} | {pred['recommendation']:10s} | ₹{pred['initial_price']:>7.2f} | {age:>4.1f}h ago ║\n"
        else:
            dashboard += "║ No active predictions                                        ║\n"

        dashboard += "╠══════════════════════════════════════════════════════════════╣\n"

        # Recent performance section
        if performance:
            recent_perf = performance[-5:]  # Last 5
            correct = sum(1 for p in recent_perf if p['prediction_correct'])
            accuracy = (correct / len(recent_perf) * 100) if recent_perf else 0

            dashboard += f"║ RECENT PERFORMANCE (last {len(recent_perf)}):                               ║\n"
            dashboard += "║ " + "-" * 58 + " ║\n"

            for perf in reversed(recent_perf):
                result = "✅" if perf['prediction_correct'] else "❌"
                change = perf['actual_change_pct']
                dashboard += f"║ {result} {perf['ticker']:8s} | {change:>+6.2f}% | {perf['recommendation']:10s}              ║\n"

            dashboard += f"║ Accuracy: {accuracy:>5.1f}%                                              ║\n"

        dashboard += "╚══════════════════════════════════════════════════════════════╝"

        return dashboard


def main():
    parser = argparse.ArgumentParser(description='Real-Time Price Monitor')
    parser.add_argument('--monitor', action='store_true', help='Start continuous monitoring')
    parser.add_argument('--interval', type=int, default=180, help='Check interval in seconds (default: 180)')
    parser.add_argument('--check-all', action='store_true', help='Check all active predictions once')
    parser.add_argument('--tickers', type=str, help='Comma-separated tickers to monitor')
    parser.add_argument('--auto-learn', action='store_true', help='Auto-trigger learning when threshold met')
    parser.add_argument('--min-samples', type=int, default=5, help='Minimum samples before auto-learning')
    parser.add_argument('--dashboard', action='store_true', help='Show monitoring dashboard')

    args = parser.parse_args()

    monitor = RealTimePriceMonitor()

    # Show dashboard
    if args.dashboard:
        dashboard = monitor.generate_monitoring_dashboard()
        print(dashboard)
        return 0

    # Check all predictions once
    if args.check_all:
        updates = monitor.check_active_predictions()

        if updates:
            ready = [u for u in updates if u['ready_for_update']]
            print(f"\n📊 Summary: {len(ready)}/{len(updates)} predictions ready for update")

            if ready:
                response = input("\nUpdate ready predictions now? (y/n): ")
                if response.lower() == 'y':
                    count = monitor.auto_update_predictions(updates)
                    print(f"\n✅ Updated {count} predictions")

        return 0

    # Continuous monitoring
    if args.monitor:
        monitor.monitor_continuous(
            interval_seconds=args.interval,
            auto_learn=args.auto_learn,
            min_samples_for_learning=args.min_samples
        )
        return 0

    # Default: show help
    parser.print_help()
    return 1


if __name__ == '__main__':
    sys.exit(main())
