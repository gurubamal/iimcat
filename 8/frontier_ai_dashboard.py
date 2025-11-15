#!/usr/bin/env python3
"""
FRONTIER-AI DASHBOARD
Beautiful formatted output with cards, metrics, and gate analysis.
"""

import pandas as pd
import numpy as np
import sys
import argparse
from datetime import datetime
from pathlib import Path

class DashboardFormatter:
    """Format results into beautiful ASCII dashboard."""
    
    def __init__(self, results_csv: str):
        self.df = pd.read_csv(results_csv)
        self.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def format_metric(self, value, decimals: int = 2, prefix: str = '', suffix: str = '') -> str:
        """Format a metric with color codes (if terminal supports)."""
        if isinstance(value, bool) or isinstance(value, (int, np.integer)):
            if value == 1 or value is True:
                return f"{prefix}✓ Yes{suffix}"
            else:
                return f"{prefix}✗ No{suffix}"
        
        if pd.isna(value):
            return "N/A"
        
        try:
            val = float(value)
            return f"{prefix}{val:.{decimals}f}{suffix}"
        except:
            return str(value)
    
    def header(self):
        """Print header."""
        print("\n" + "="*100)
        print("  🚀 FRONTIER-AI QUANT ALPHA SYSTEM - SWING TRADE SHORTLIST")
        print(f"  Generated: {self.timestamp}")
        print("="*100)
    
    def summary_stats(self):
        """Print summary statistics."""
        print("\n📊 SUMMARY STATISTICS")
        print("-" * 100)
        
        total = len(self.df)
        picks = (self.df['final_pick'] == 1).sum()
        pass_rate = (picks / total * 100) if total > 0 else 0
        
        print(f"  Total tickers processed:     {total:3d}")
        print(f"  Final picks (gates passed):  {picks:3d}  ({pass_rate:.1f}% pass rate)")
        print(f"  Average alpha score:         {self.df['alpha'].mean():6.2f}")
        print(f"  Median alpha score:          {self.df['alpha'].median():6.2f}")
        print(f"  Alpha range:                 {self.df['alpha'].min():.2f} - {self.df['alpha'].max():.2f}")
        print(f"  Average RVOL:                {self.df['rvol'].mean():.2f}x")
        print(f"  Average expected rise:       {self.df['impact_pct'].mean():.2f}%")
        print(f"  Max deal value detected:     ₹{self.df['deal_value_cr'].max():,.0f} cr")
        print(f"  Avg news certainty:          {self.df['certainty'].mean():.1f}%")
        print()
    
    def gate_analysis(self):
        """Analyze and print gate filter details."""
        print("\n🚪 GATE FILTER ANALYSIS")
        print("-" * 100)
        
        # Parse gate flags
        total = len(self.df)
        
        # Estimate pass rates by parsing gate_flags
        alpha_pass = 0
        rvol_pass = 0
        trend_pass = 0
        vol_pass = 0
        
        for flags in self.df['gate_flags']:
            if 'alpha:True' in str(flags):
                alpha_pass += 1
            if 'rvol:True' in str(flags):
                rvol_pass += 1
            if 'trend:True' in str(flags):
                trend_pass += 1
            if 'volatility:True' in str(flags):
                vol_pass += 1
        
        print(f"  Alpha ≥ 70:                  {alpha_pass:3d}/{total:3d}  ({alpha_pass/total*100:5.1f}%) pass")
        print(f"  RVOL ≥ 1.5x:                 {rvol_pass:3d}/{total:3d}  ({rvol_pass/total*100:5.1f}%) pass")
        print(f"  Price > SMA50:               {trend_pass:3d}/{total:3d}  ({trend_pass/total*100:5.1f}%) pass")
        print(f"  Squeeze OR Breakout:         {vol_pass:3d}/{total:3d}  ({vol_pass/total*100:5.1f}%) pass")
        print(f"  ALL gates passed:            {(self.df['final_pick']==1).sum():3d}/{total:3d}  ({(self.df['final_pick']==1).sum()/total*100:5.1f}%) pass")
        print()
    
    def top_picks_cards(self, limit: int = 10):
        """Print formatted cards for top picks."""
        print("\n🏆 TOP PICKS (by alpha score)")
        print("-" * 100)
        
        picks = self.df[self.df['final_pick'] == 1].head(limit)
        
        if picks.empty:
            print("  ⚠️  No tickers passed gate filters. Consider relaxing thresholds.")
            # Show all by alpha
            picks = self.df.head(limit)
            print(f"\n  Showing top {limit} by raw alpha score (all filtered):\n")
        
        for idx, (_, row) in enumerate(picks.iterrows(), 1):
            self.print_card(row, idx)
        
        print()
    
    def print_card(self, row, idx: int):
        """Print a single card."""
        ticker = row['ticker']
        alpha = row['alpha']
        status = "✓ FINAL PICK" if row['final_pick'] == 1 else "⚠ FILTERED"
        
        print(f"\n  ┌─ Card #{idx}: {ticker:12s} {status:15s} Alpha: {alpha:6.2f}/100")
        print(f"  ├─ Price: ₹{row['close']:10.2f} | ATR20: ₹{row['atr20']:8.2f} | RVOL: {row['rvol']:5.2f}x")
        
        # Momentum metrics
        print(f"  ├─ Momentum: 3-day={row['momentum_3']:5.1f}  20-day={row['momentum_20']:5.1f}  60-day={row['momentum_60']:5.1f}")
        
        # Setup
        squeeze_str = "🔵 Yes" if row['squeeze'] else "○ No"
        bo_str = "↑ Up" if row['breakout'] > 0 else ("↓ Dn" if row['breakout'] < 0 else "- No")
        print(f"  ├─ Setup: Squeeze={squeeze_str:8s} | Breakout={bo_str:6s} | PBZ={row['pbz']:5.1f}")
        
        # Trend
        sma50_str = "✓" if row['trend_sma50'] else "✗"
        sma200_str = "✓" if row['trend_sma200'] else "✗"
        print(f"  ├─ Trend: SMA50={sma50_str}  SMA200={sma200_str}  RSI14={row['rsi14']:5.1f}")
        
        # News
        catalyst = row['catalyst_type']
        sentiment = row['sentiment'].upper()
        print(f"  ├─ News: {catalyst:12s} | Sentiment={sentiment:8s} | Certainty={row['certainty']:3.0f}% | Deal=₹{row['deal_value_cr']:8.0f}cr")
        
        # Risk/Reward
        print(f"  ├─ Risk/Reward:")
        print(f"  │  Entry: ₹{row['close']:8.2f}  | Stop: ₹{row['stop_loss']:8.2f}  | TP1: ₹{row['tp1']:8.2f} (+{row['impact_pct']:5.1f}%)")
        print(f"  │  TP2: ₹{row['tp2']:8.2f}  | Trail: ₹{row['trail_stop']:8.2f}")
        
        # Headline
        headline = row['headline_text'][:60] if pd.notna(row['headline_text']) else "N/A"
        print(f"  └─ Latest: {headline}...")
        print(f"  │  Gates: {row['gate_flags']}")

    def rejection_report(self):
        """Print rejected stocks analysis."""
        rejected = self.df[self.df['final_pick'] == 0]
        
        if rejected.empty:
            return
        
        print("\n⛔ REJECTION ANALYSIS (Stocks that didn't pass gates)")
        print("-" * 100)
        
        # Categorize rejections - simpler approach
        alpha_fails_count = (rejected['alpha'] < 70).sum()
        rvol_fails_count = (rejected['rvol'] < 1.5).sum()
        trend_fails_count = (rejected['trend_sma50'] == 0).sum()
        vol_fails_count = ((rejected['squeeze'] == 0) & (rejected['breakout'] == 0)).sum()
        
        print(f"  Alpha gate failures:         {alpha_fails_count:3d} stocks (alpha < 70)")
        print(f"  RVOL gate failures:          {rvol_fails_count:3d} stocks (volume too low)")
        print(f"  Trend gate failures:         {trend_fails_count:3d} stocks (below SMA50)")
        print(f"  Volatility gate failures:    {vol_fails_count:3d} stocks (no squeeze/BO setup)")
        
        alpha_fails = rejected[rejected['alpha'] < 70].nlargest(3, 'alpha')
        if len(alpha_fails) > 0:
            print(f"\n  Top alpha failures (closest to threshold):")
            for idx, (_, row) in enumerate(alpha_fails.iterrows(), 1):
                print(f"    {idx}. {row['ticker']:8s} - Alpha={row['alpha']:6.2f} (needs {70-row['alpha']:.1f} more points)")
        
        print()
    
    def daily_workflow(self):
        """Print suggested daily workflow."""
        print("\n📋 DAILY WORKFLOW & NEXT STEPS")
        print("-" * 100)
        print("""
  1. REVIEW PICKS: Check top cards for setup quality and news catalysts
  
  2. VALIDATE: Cross-check headlines with original source (finviz, moneycontrol)
  
  3. PRE-MARKET: 
     - Identify any overnight news (4 AM - 9:30 AM)
     - Check if RVI (relative volatility index) spiked
     - Monitor pre-market volume
  
  4. ENTRY LOGIC:
     - ✓ Wait for first pullback to SMA20 with RVOL > 1.2x
     - ✓ Enter on reversal candle (not at open)
     - ✓ Set stop at Entry - 1.5×ATR20 (hard discipline)
  
  5. EXIT RULES:
     - Sell 50% at TP1 (Entry + 1.5×ATR20)
     - Sell 25% at TP2 (Entry + 3×ATR20)
     - Trailing stop at max(Trail, Close - 2.5×ATR20)
  
  6. RISK MANAGEMENT:
     - Max 2% risk per trade
     - Position sizing: Risk / (Entry - Stop) = Position Size
     - Never revenge trade if 2 losses in a row
""")
    
    def render(self):
        """Render complete dashboard."""
        self.header()
        self.summary_stats()
        self.gate_analysis()
        self.top_picks_cards(limit=10)
        self.rejection_report()
        self.daily_workflow()
        
        print("="*100)
        print(f"  End of report. Full results saved to CSV for external validation.")
        print("="*100 + "\n")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Frontier-AI Dashboard')
    parser.add_argument('results_csv', help='Results CSV file')
    parser.add_argument('--limit', type=int, default=10, help='Number of top picks to show')
    
    args = parser.parse_args()
    
    if not Path(args.results_csv).exists():
        print(f"Error: File not found: {args.results_csv}")
        sys.exit(1)
    
    dashboard = DashboardFormatter(args.results_csv)
    dashboard.render()

if __name__ == '__main__':
    main()
