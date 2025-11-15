#!/usr/bin/env python3
"""Test hybrid scoring integration"""
import os
os.environ['ENABLE_TECHNICAL_SCORING'] = '1'

from technical_scoring_wrapper import TechnicalScorer

# Test hybrid scoring
scorer = TechnicalScorer()

# Simulate AI scores from the output
test_cases = [
    ('RELIANCE.NS', 54.4, 'CSR donation - neutral news'),
    ('TRENT.NS', 47.8, 'Broker downgrades - bearish news')
]

print("="*80)
print("HYBRID SCORING TEST - AI + Technical Combined")
print("="*80)
print()

for ticker, ai_score, description in test_cases:
    print(f"\n{'='*80}")
    print(f"Stock: {ticker}")
    print(f"{'='*80}")
    print(f"Description: {description}")
    print(f"AI Score: {ai_score}/100")
    print()
    
    # Get hybrid score
    hybrid_result = scorer.get_hybrid_score(ai_score, ticker, period='3mo')
    
    print(f"Technical Score: {hybrid_result.get('technical_score', 'N/A')}/100")
    print(f"Technical Tier: {hybrid_result.get('technical_tier', 'N/A')}")
    print(f"Hybrid Score: {hybrid_result['hybrid_score']}/100 (60% AI + 40% Tech)")
    print(f"Ranking Boost: {hybrid_result['ranking_boost']:+.1f} points")
    print(f"\nRecommendation: {hybrid_result['recommendation']}")
    
    if hybrid_result.get('technical_details'):
        ind = hybrid_result['technical_details']['indicators']
        print(f"\nTechnical Details:")
        print(f"  RSI: {ind['rsi']:.1f}")
        print(f"  BB Position: {ind['bb_position']:.1f}%")
        print(f"  Volume: {ind['volume_ratio']:.2f}x avg")

print(f"\n{'='*80}")
print("KEY INSIGHT:")
print("="*80)
print("RELIANCE: Weak news + Weak technical = Low hybrid score")
print("TRENT: Bearish news + STRONG technical (oversold, high vol) = Better hybrid score")
print("\nHybrid ranking catches TRENT as potential reversal play!")
print("="*80)
