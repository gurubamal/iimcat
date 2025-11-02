#!/usr/bin/env python3
"""Analyze latest news for TOP investment options"""

import re
from collections import defaultdict, Counter
from datetime import datetime
import sys

print("🔍 ANALYZING LATEST NEWS FOR INVESTMENT OPTIONS")
print("="*80)

# Use the latest file
news_file = "aggregated_full_articles_48h_20251013_200042.txt"

# Storage
stocks = defaultdict(list)
current_stock = None
article = {}

with open(news_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        
        if line.startswith("Full Article Fetch Test - "):
            current_stock = line.replace("Full Article Fetch Test - ", "").strip()
        elif line.startswith("Title   :"):
            article = {'title': line.replace("Title   :", "").strip()}
        elif line.startswith("Source  :"):
            article['source'] = line.replace("Source  :", "").strip()
        elif line.startswith("Published:"):
            article['published'] = line.replace("Published:", "").strip()
            if current_stock and 'title' in article:
                stocks[current_stock].append(article.copy())

print(f"📊 Analyzed: {len(stocks)} stocks with news\n")

def analyze_investment_potential(title, content=""):
    """Score based on investment signals"""
    score = 0
    signals = []
    t = (title + " " + content).lower()
    
    # Strong buy signals
    if re.search(r'profit.*growth|profit.*up|revenue.*growth|revenue.*up', t):
        score += 10
        signals.append("PROFIT_GROWTH")
    if re.search(r'fund.*rais|investment|funding|capital', t):
        score += 8
        signals.append("FUNDING")
    if re.search(r'acquisition|acquires|buys|merger', t):
        score += 9
        signals.append("M&A")
    if re.search(r'dividend', t):
        score += 7
        signals.append("DIVIDEND")
    if re.search(r'expansion|launches|new.*business', t):
        score += 6
        signals.append("EXPANSION")
    if re.search(r'contract|order|deal.*worth', t):
        score += 7
        signals.append("CONTRACTS")
    if re.search(r'ipo|listing', t):
        score += 6
        signals.append("IPO")
    if re.search(r'record.*high|all.*time.*high|surge', t):
        score += 8
        signals.append("MOMENTUM")
    if re.search(r'beats.*estimate|exceeds.*expectation', t):
        score += 9
        signals.append("BEAT_EST")
    
    # Negative signals
    if re.search(r'loss|losses|decline.*profit|profit.*fall', t):
        score -= 8
        signals.append("LOSSES")
    if re.search(r'investigation|probe|fraud|scam', t):
        score -= 10
        signals.append("LEGAL")
    if re.search(r'layoff|retrench|job.*cut', t):
        score -= 6
        signals.append("LAYOFFS")
    if re.search(r'downgrade|cut.*rating', t):
        score -= 7
        signals.append("DOWNGRADE")
    
    # Extract deal size
    magnitude = 0
    money = re.search(r'₹?\$?(\d+(?:,\d+)*)\s*(crore|million|billion|lakh)', t)
    if money:
        amount = int(money.group(1).replace(',', ''))
        unit = money.group(2)
        
        if unit == 'crore':
            magnitude = amount
        elif unit == 'million':
            magnitude = amount / 10
        elif unit == 'billion':
            magnitude = amount * 100
        elif unit == 'lakh':
            magnitude = amount / 100
        
        if magnitude >= 100:
            score += 3
        if magnitude >= 500:
            score += 3
        if magnitude >= 1000:
            score += 4
    
    return score, signals, magnitude

# Analyze all stocks
results = []
for stock, articles in stocks.items():
    if not articles:
        continue
    
    total_score = 0
    all_signals = []
    max_magnitude = 0
    headlines = []
    
    for art in articles:
        title = art.get('title', '')
        score, signals, mag = analyze_investment_potential(title)
        total_score += score
        all_signals.extend(signals)
        max_magnitude = max(max_magnitude, mag)
        headlines.append(title)
    
    if total_score > 5:  # Only positive stocks
        results.append({
            'stock': stock,
            'score': total_score,
            'count': len(articles),
            'magnitude': max_magnitude,
            'signals': all_signals,
            'headlines': headlines[:3]
        })

# Sort by score
results.sort(key=lambda x: (x['score'], x['magnitude']), reverse=True)

print("="*80)
print("🏆 TOP 15 INVESTMENT OPTIONS")
print("="*80)

for i, r in enumerate(results[:15], 1):
    print(f"\n{i}. {r['stock']}")
    print(f"   {'─'*76}")
    print(f"   Investment Score: {r['score']} points")
    print(f"   News Coverage: {r['count']} articles")
    if r['magnitude'] > 0:
        print(f"   Deal Magnitude: ₹{r['magnitude']:.0f} crore")
    
    # Top signals
    sig_count = Counter(r['signals'])
    top_sigs = sig_count.most_common(3)
    if top_sigs:
        print(f"   Key Signals: {', '.join([s[0] for s in top_sigs])}")
    
    print(f"\n   📰 Headlines:")
    for j, h in enumerate(r['headlines'], 1):
        print(f"      {j}. {h[:75]}...")

print("\n" + "="*80)
print("📈 MARKET INSIGHTS")
print("="*80)

# Sector analysis
all_sigs = []
for r in results[:15]:
    all_sigs.extend(r['signals'])

sig_dist = Counter(all_sigs)
print("\n🎯 Top Market Signals:")
for sig, count in sig_dist.most_common(5):
    print(f"   • {sig}: {count} occurrences")

# High value deals
big_deals = [r for r in results if r['magnitude'] >= 100]
if big_deals:
    print(f"\n💰 Large Deal Activity ({len(big_deals)} stocks with ₹100Cr+ deals):")
    for r in big_deals[:5]:
        print(f"   • {r['stock']}: ₹{r['magnitude']:.0f} crore")

print("\n" + "="*80)
print("⚡ QUICK PICKS BY CATEGORY")
print("="*80)

# Categorize
growth = [r for r in results if 'PROFIT_GROWTH' in r['signals']][:3]
funding = [r for r in results if 'FUNDING' in r['signals']][:3]
dividend = [r for r in results if 'DIVIDEND' in r['signals']][:3]
ma = [r for r in results if 'M&A' in r['signals']][:3]

if growth:
    print("\n📈 PROFIT GROWTH STORIES:")
    for r in growth:
        print(f"   • {r['stock']} (Score: {r['score']})")

if funding:
    print("\n💰 CAPITAL RAISING / FUNDED:")
    for r in funding:
        print(f"   • {r['stock']} (Score: {r['score']})")

if dividend:
    print("\n💎 DIVIDEND PLAYS:")
    for r in dividend:
        print(f"   • {r['stock']} (Score: {r['score']})")

if ma:
    print("\n🤝 M&A ACTIVITY:")
    for r in ma:
        print(f"   • {r['stock']} (Score: {r['score']})")

print("\n" + "="*80)
print("⚠️  Always conduct thorough due diligence before investing!")
print("="*80)

