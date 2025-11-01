#!/usr/bin/env python3
"""
Comparison Report Generator

Re-scores yesterday's AI picks using the new enhanced scoring formula
that includes volume and sector momentum.

Shows:
- Old ranking vs New ranking
- What changed and why
- Which stocks would have been prioritized differently
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict
from volume_and_sector_momentum import VolumeAndSectorMomentum


def load_csv_results(csv_path: str) -> List[Dict]:
    """Load CSV results from previous scan"""
    results = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results


def rerank_with_enhanced_scoring(results: List[Dict]) -> List[Dict]:
    """Re-rank results with volume and sector momentum"""
    print("\n🔄 Re-ranking with Enhanced Scoring Formula...")
    print("="*80)

    vsm = VolumeAndSectorMomentum()

    # Fetch sector momentum once for all stocks
    print("\n📊 Fetching sector momentum data...")
    vsm.sector_cache = vsm.fetch_sector_momentum()

    enhanced_results = []

    for idx, row in enumerate(results, 1):
        ticker = row.get('ticker', '').strip().upper()
        ai_score = float(row.get('ai_score', '50'))

        print(f"\n[{idx}/{len(results)}] Processing {ticker}...")

        # Enrich with volume and sector data
        enriched = vsm.enrich_stock_data(
            ticker=ticker,
            ai_score=ai_score,
            news_timestamp=None  # Assume 24h old
        )

        # Combine original row with enriched data
        enhanced_row = {**row}
        enhanced_row['sector'] = enriched['sector']
        enhanced_row['sector_momentum'] = enriched['sector_momentum']
        enhanced_row['volume_multiplier'] = enriched['volume_multiplier']
        enhanced_row['volume_score'] = enriched['volume_score']
        enhanced_row['catalyst_freshness'] = enriched['catalyst_freshness']
        enhanced_row['enhanced_final_score'] = enriched['enhanced_final_score']
        enhanced_row['old_rank'] = idx

        # Calculate score improvement
        score_diff = enriched['enhanced_final_score'] - ai_score
        enhanced_row['score_improvement'] = round(score_diff, 2)

        enhanced_results.append(enhanced_row)

        print(f"   AI Score: {ai_score:.1f}")
        print(f"   Sector: {enriched['sector']} (Momentum: {enriched['sector_momentum']:.1f})")
        print(f"   Volume: {enriched['volume_multiplier']:.2f}x (Score: {enriched['volume_score']:.1f})")
        print(f"   Enhanced Score: {enriched['enhanced_final_score']:.2f} ({score_diff:+.2f})")

    # Sort by enhanced final score
    enhanced_results.sort(key=lambda x: x['enhanced_final_score'], reverse=True)

    # Add new rank
    for new_rank, row in enumerate(enhanced_results, 1):
        row['new_rank'] = new_rank
        row['rank_change'] = row['old_rank'] - new_rank  # Positive = moved up

    return enhanced_results


def generate_report(enhanced_results: List[Dict], output_path: str):
    """Generate comparison report"""
    print("\n" + "="*80)
    print("📊 COMPARISON REPORT: Old Ranking vs New Enhanced Ranking")
    print("="*80)

    # Top movers up
    print("\n🚀 TOP MOVERS UP (Stocks that improved most):")
    print("-"*80)
    movers_up = sorted(enhanced_results, key=lambda x: x['rank_change'], reverse=True)[:5]

    for row in movers_up:
        ticker = row['ticker']
        old_rank = row['old_rank']
        new_rank = row['new_rank']
        rank_change = row['rank_change']
        ai_score = float(row.get('ai_score', 0))
        enhanced_score = row['enhanced_final_score']

        if rank_change > 0:
            print(f"\n{ticker}: #{old_rank} → #{new_rank} (↑{rank_change} positions)")
            print(f"   Old Score: {ai_score:.1f} → New Score: {enhanced_score:.2f}")
            print(f"   Sector: {row['sector']} (Momentum: {row['sector_momentum']:.1f})")
            print(f"   Volume: {row['volume_multiplier']:.2f}x")
            print(f"   Why improved: ", end="")
            reasons = []
            if row['volume_score'] > 75:
                reasons.append(f"High volume ({row['volume_multiplier']:.1f}x)")
            if row['sector_momentum'] > 60:
                reasons.append(f"Strong sector ({row['sector_momentum']:.1f})")
            print(" + ".join(reasons) if reasons else "Multiple factors")

    # Top movers down
    print("\n\n⬇️  TOP MOVERS DOWN (Stocks that fell most):")
    print("-"*80)
    movers_down = sorted(enhanced_results, key=lambda x: x['rank_change'])[:5]

    for row in movers_down:
        ticker = row['ticker']
        old_rank = row['old_rank']
        new_rank = row['new_rank']
        rank_change = row['rank_change']
        ai_score = float(row.get('ai_score', 0))
        enhanced_score = row['enhanced_final_score']

        if rank_change < 0:
            print(f"\n{ticker}: #{old_rank} → #{new_rank} (↓{abs(rank_change)} positions)")
            print(f"   Old Score: {ai_score:.1f} → New Score: {enhanced_score:.2f}")
            print(f"   Sector: {row['sector']} (Momentum: {row['sector_momentum']:.1f})")
            print(f"   Volume: {row['volume_multiplier']:.2f}x")
            print(f"   Why declined: ", end="")
            reasons = []
            if row['volume_score'] < 40:
                reasons.append(f"Low volume ({row['volume_multiplier']:.2f}x)")
            if row['sector_momentum'] < 45:
                reasons.append(f"Weak sector ({row['sector_momentum']:.1f})")
            print(" + ".join(reasons) if reasons else "Multiple factors")

    # New Top 10
    print("\n\n🏆 NEW TOP 10 RANKING (With Enhanced Scoring):")
    print("-"*80)
    print(f"{'Rank':<6} {'Ticker':<12} {'Old→New':<10} {'AI Score':<10} {'Enhanced':<10} {'Sector':<10} {'Vol':<8}")
    print("-"*80)

    for row in enhanced_results[:10]:
        ticker = row['ticker']
        old_rank = row['old_rank']
        new_rank = row['new_rank']
        rank_change = row['rank_change']
        ai_score = float(row.get('ai_score', 0))
        enhanced_score = row['enhanced_final_score']
        sector = row['sector'][:8]
        volume = f"{row['volume_multiplier']:.1f}x"

        rank_indicator = f"↑{rank_change}" if rank_change > 0 else f"↓{abs(rank_change)}" if rank_change < 0 else "="
        old_new = f"#{old_rank}→#{new_rank}"

        print(f"{new_rank:<6} {ticker:<12} {old_new:<10} {ai_score:<10.1f} {enhanced_score:<10.2f} {sector:<10} {volume:<8} {rank_indicator}")

    # Analysis summary
    print("\n\n📈 SCORING BREAKDOWN ANALYSIS:")
    print("-"*80)

    # Find example of each scoring component impact
    best_volume = max(enhanced_results, key=lambda x: x['volume_score'])
    best_sector = max(enhanced_results, key=lambda x: x['sector_momentum'])

    print(f"\n🔊 Best Volume Performance:")
    print(f"   {best_volume['ticker']}: {best_volume['volume_multiplier']:.2f}x volume")
    print(f"   Volume Score: {best_volume['volume_score']:.1f}/100")
    print(f"   Contributed +{best_volume['volume_score'] * 0.20:.1f} points to final score")

    print(f"\n🎯 Best Sector Momentum:")
    print(f"   {best_sector['ticker']} ({best_sector['sector']} sector)")
    print(f"   Sector Momentum: {best_sector['sector_momentum']:.1f}/100")
    print(f"   Contributed +{best_sector['sector_momentum'] * 0.25:.1f} points to final score")

    # Save to CSV
    print(f"\n\n💾 Saving enhanced results to: {output_path}")

    fieldnames = [
        'new_rank', 'old_rank', 'rank_change', 'ticker', 'company_name',
        'ai_score', 'enhanced_final_score', 'score_improvement',
        'sector', 'sector_momentum', 'volume_multiplier', 'volume_score',
        'catalyst_freshness', 'sentiment', 'recommendation', 'catalysts',
        'certainty', 'articles_count', 'headline', 'reasoning'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for row in enhanced_results:
            writer.writerow(row)

    print(f"✅ Report saved successfully!")

    # Final insights
    print("\n\n💡 KEY INSIGHTS:")
    print("-"*80)

    high_volume_count = sum(1 for r in enhanced_results if r['volume_score'] > 75)
    strong_sector_count = sum(1 for r in enhanced_results if r['sector_momentum'] > 60)
    significant_changes = sum(1 for r in enhanced_results if abs(r['rank_change']) >= 3)

    print(f"   • {high_volume_count} stocks had high volume (>1.5x average)")
    print(f"   • {strong_sector_count} stocks in strong sectors (momentum >60)")
    print(f"   • {significant_changes} stocks changed rank by ±3 or more positions")

    # Identify what old #1 became
    old_first = [r for r in enhanced_results if r['old_rank'] == 1][0]
    if old_first['new_rank'] != 1:
        print(f"\n   ⚠️  OLD #1 ({old_first['ticker']}) dropped to #{old_first['new_rank']}")
        print(f"       Reason: Volume {old_first['volume_multiplier']:.2f}x, Sector {old_first['sector_momentum']:.1f}")

    # New #1
    new_first = enhanced_results[0]
    if new_first['old_rank'] != 1:
        print(f"\n   🎯 NEW #1 ({new_first['ticker']}) rose from #{new_first['old_rank']}")
        print(f"       Why: Volume {new_first['volume_multiplier']:.2f}x, Sector {new_first['sector_momentum']:.1f}")

    print("\n" + "="*80)


def main():
    """Main execution"""
    if len(sys.argv) < 2:
        print("Usage: python3 generate_comparison_report.py <csv_file>")
        print("\nExample:")
        print("  python3 generate_comparison_report.py realtime_ai_results_2025-10-30_06-53-00_claude-shell.csv")
        sys.exit(1)

    csv_path = sys.argv[1]

    if not Path(csv_path).exists():
        print(f"❌ Error: File not found: {csv_path}")
        sys.exit(1)

    print("="*80)
    print("🔬 ENHANCED SCORING COMPARISON REPORT GENERATOR")
    print("="*80)
    print(f"\n📂 Input CSV: {csv_path}")

    # Load results
    results = load_csv_results(csv_path)
    print(f"✅ Loaded {len(results)} stocks from CSV")

    # Re-rank with enhanced scoring
    enhanced_results = rerank_with_enhanced_scoring(results)

    # Generate report
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = f"enhanced_comparison_report_{timestamp}.csv"

    generate_report(enhanced_results, output_path)

    print("\n✅ Analysis Complete!")
    print(f"\n📁 Output file: {output_path}")
    print("\nNext steps:")
    print("  1. Review the NEW TOP 10 ranking")
    print("  2. Compare with actual market performance")
    print("  3. Identify which factors (volume/sector) were most predictive")


if __name__ == '__main__':
    main()
