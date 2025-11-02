#!/usr/bin/env python3
"""Generate refined investment report with company names"""

import yfinance as yf
from datetime import datetime

print("📊 TOP INVESTMENT OPTIONS - REFINED ANALYSIS")
print("="*80)
print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("Based on: 48-hour news scan (2,599 stocks analyzed)")
print("="*80)

# Top picks with details
top_picks = [
    {
        'ticker': 'HCLTECH',
        'score': 47,
        'reason': 'Q2 Results: PAT ₹4,235 crore, revenue up 11% YoY. Fastest Q2 growth in 5 years. 91st consecutive dividend (₹12/share). Strong AI revenue.',
        'magnitude': 4235,
        'sentiment': 'BULLISH'
    },
    {
        'ticker': 'CHANDAN',
        'score': 22,
        'reason': 'Board approves ₹104 crore fund raise via preferential issue. Capital expansion signal.',
        'magnitude': 104,
        'sentiment': 'BULLISH'
    },
    {
        'ticker': 'CANTABIL',
        'score': 11,
        'reason': 'Eyes revenues of ₹1,000 crore by FY27. Aggressive growth targets in apparel retail.',
        'magnitude': 1000,
        'sentiment': 'BULLISH'
    }
]

# Additional mentions from news
other_signals = [
    "GoodScore (Fintech) - Raises $13M Series A from Peak XV Partners",
    "Lenskart - Record IPO month activity",
    "Scimplify (Chemicals) - Eyes $100M investment for overseas expansion",
    "Snapmint (Lending) - General Atlantic leads $100M round",
]

print("\n🏆 TOP 3 STRONG BUY CANDIDATES")
print("="*80)

for i, pick in enumerate(top_picks, 1):
    print(f"\n{i}. {pick['ticker']}")
    print(f"   {'─'*76}")
    
    # Try to get current price
    try:
        stock = yf.Ticker(f"{pick['ticker']}.NS")
        hist = stock.history(period='1d')
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            print(f"   💰 Current Price: ₹{current_price:.2f}")
            
            # Get 52-week range if available
            info = stock.info
            if 'fiftyTwoWeekHigh' in info and 'fiftyTwoWeekLow' in info:
                high_52 = info['fiftyTwoWeekHigh']
                low_52 = info['fiftyTwoWeekLow']
                print(f"   📊 52W Range: ₹{low_52:.2f} - ₹{high_52:.2f}")
    except Exception as e:
        print(f"   💰 Price data unavailable")
    
    print(f"   ⭐ Investment Score: {pick['score']}/10")
    print(f"   📈 Sentiment: {pick['sentiment']}")
    print(f"   💼 Deal Size: ₹{pick['magnitude']} crore")
    print(f"\n   📝 Investment Thesis:")
    print(f"      {pick['reason']}")

print("\n\n💡 OTHER NOTEWORTHY DEVELOPMENTS")
print("="*80)

for signal in other_signals:
    print(f"   • {signal}")

print("\n\n📈 MACRO CONTEXT (From News)")
print("="*80)
print("   ✅ Retail inflation at 99-month low (1.5% in Sept)")
print("   ✅ India market setting up for next bull run (per analysts)")
print("   ✅ Record month for India IPOs")
print("   ✅ Gold/Silver at record highs (safe haven demand)")
print("   ⚠️  US tariff concerns (textile sector impact)")
print("   ⚠️  Global trade tensions (Trump-China)")

print("\n\n🎯 INVESTMENT STRATEGY RECOMMENDATIONS")
print("="*80)

strategies = [
    {
        'profile': 'AGGRESSIVE GROWTH',
        'picks': ['HCLTECH (IT sector momentum)', 'CANTABIL (growth story)', 'Consider IPO opportunities'],
        'allocation': '60% established, 40% growth stories'
    },
    {
        'profile': 'BALANCED',
        'picks': ['HCLTECH (dividend + growth)', 'CHANDAN (capital raising)', 'Monitor fintech startups'],
        'allocation': '70% blue-chip, 30% mid-cap'
    },
    {
        'profile': 'CONSERVATIVE',
        'picks': ['HCLTECH (consistent dividend)', 'Wait for market correction', 'Gold/Silver exposure'],
        'allocation': '80% large-cap, 20% precious metals'
    }
]

for strategy in strategies:
    print(f"\n   {strategy['profile']}:")
    print(f"   {'─'*76}")
    for pick in strategy['picks']:
        print(f"      • {pick}")
    print(f"      Allocation: {strategy['allocation']}")

print("\n\n⚠️  RISK FACTORS TO MONITOR")
print("="*80)
print("   1. Global trade tensions and tariff impacts")
print("   2. Currency fluctuations (USD/INR)")
print("   3. Sector-specific regulations")
print("   4. Market valuation levels")
print("   5. Geopolitical developments")

print("\n\n🔍 NEXT STEPS")
print("="*80)
print("   1. Technical Analysis: Check charts for entry points")
print("   2. Fundamental Deep Dive: Review full financials")
print("   3. Risk Assessment: Position sizing based on risk tolerance")
print("   4. Monitor: Set alerts for price levels and news")
print("   5. Review: Reassess as full scan completes (86% done)")

print("\n" + "="*80)
print("📌 DISCLAIMER: This analysis is based on news sentiment and should not be")
print("   considered as financial advice. Always consult with a qualified financial")
print("   advisor and conduct your own research before making investment decisions.")
print("="*80)

