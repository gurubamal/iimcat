#!/usr/bin/env python3
"""Analyze collected news for investment opportunities"""

import re
from collections import defaultdict
from datetime import datetime

print("🔍 ANALYZING NEWS FOR TOP INVESTMENT OPTIONS")
print("="*80)

# Read the aggregated news file
news_file = "aggregated_full_articles_48h_20251013_160203.txt"

# Storage for analysis
stocks_with_news = {}
current_stock = None
current_article = {}

with open(news_file, 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        line = line.strip()
        
        # Detect stock section
        if line.startswith("Full Article Fetch Test - "):
            current_stock = line.replace("Full Article Fetch Test - ", "").strip()
            if current_stock not in stocks_with_news:
                stocks_with_news[current_stock] = []
        
        # Detect article title
        elif line.startswith("Title   :"):
            title = line.replace("Title   :", "").strip()
            current_article = {'title': title, 'stock': current_stock}
        
        # Detect source
        elif line.startswith("Source  :"):
            current_article['source'] = line.replace("Source  :", "").strip()
        
        # Detect published date
        elif line.startswith("Published:"):
            pub_date = line.replace("Published:", "").strip()
            current_article['published'] = pub_date
            
            # When we have all key fields, save the article
            if current_stock and 'title' in current_article:
                stocks_with_news[current_stock].append(current_article.copy())

# Analyze and score stocks
def score_news(title, article_data):
    """Score news based on investment potential indicators"""
    score = 0
    category = "NEUTRAL"
    
    title_lower = title.lower()
    
    # Positive indicators
    positive_keywords = {
        'fund raise|funding|investment': 8,
        'crore|million|billion': 6,
        'acquisition|acquires|buys': 7,
        'partnership|collaboration': 5,
        'expansion|growth|launches': 6,
        'ipo|listing': 7,
        'profit|revenue': 6,
        'approves|approval': 5,
        'record high|surges|soars': 7,
        'contract|order|deal': 6,
    }
    
    # Negative indicators
    negative_keywords = {
        'loss|losses|decline': -6,
        'reject|rejected|fails': -5,
        'tariff|duty|tax': -4,
        'investigation|probe': -5,
        'lawsuit|legal': -4,
        'drops|falls|tumbles': -6,
    }
    
    # Check positive
    for pattern, points in positive_keywords.items():
        if re.search(pattern, title_lower):
            score += points
            category = "BULLISH"
    
    # Check negative
    for pattern, points in negative_keywords.items():
        if re.search(pattern, title_lower):
            score += points
            if score < 0:
                category = "BEARISH"
    
    # Extract monetary values
    money_match = re.search(r'₹?(\d+(?:,\d+)*)\s*(crore|million|billion)', title_lower)
    if money_match:
        amount = int(money_match.group(1).replace(',', ''))
        unit = money_match.group(2)
        
        if unit == 'crore':
            value_cr = amount
        elif unit == 'million':
            value_cr = amount / 10  # approx
        elif unit == 'billion':
            value_cr = amount * 100
        
        # Bonus for large deals
        if value_cr >= 100:
            score += 3
        if value_cr >= 500:
            score += 2
            
        article_data['magnitude_cr'] = value_cr
    
    return score, category

# Score and rank all stocks
ranked_stocks = []

for stock, articles in stocks_with_news.items():
    if not articles:
        continue
    
    total_score = 0
    max_magnitude = 0
    categories = []
    
    for article in articles:
        title = article.get('title', '')
        score, category = score_news(title, article)
        total_score += score
        categories.append(category)
        
        if 'magnitude_cr' in article:
            max_magnitude = max(max_magnitude, article['magnitude_cr'])
    
    if total_score > 0:  # Only include stocks with positive signals
        ranked_stocks.append({
            'stock': stock,
            'score': total_score,
            'articles_count': len(articles),
            'max_magnitude': max_magnitude,
            'categories': categories,
            'titles': [a['title'][:80] for a in articles[:3]]  # Top 3 headlines
        })

# Sort by score
ranked_stocks.sort(key=lambda x: (x['score'], x['max_magnitude']), reverse=True)

# Display top investment options
print(f"\n📊 ANALYSIS COMPLETE - {len(stocks_with_news)} stocks scanned")
print(f"✅ Found {len(ranked_stocks)} stocks with positive signals\n")

print("="*80)
print("🏆 TOP 10 INVESTMENT OPTIONS (Based on Current News)")
print("="*80)

for i, stock_data in enumerate(ranked_stocks[:10], 1):
    print(f"\n{i}. {stock_data['stock']}")
    print(f"   {'='*70}")
    print(f"   Investment Score: {stock_data['score']}/10 ⭐")
    print(f"   News Articles: {stock_data['articles_count']}")
    
    if stock_data['max_magnitude'] > 0:
        print(f"   Deal Size: ₹{stock_data['max_magnitude']:.0f} crore")
    
    print(f"   Sentiment: {', '.join(set(stock_data['categories']))}")
    print(f"\n   📰 Key Headlines:")
    
    for j, title in enumerate(stock_data['titles'], 1):
        print(f"      {j}. {title}...")

print("\n" + "="*80)
print("💡 INVESTMENT INSIGHTS")
print("="*80)

# Category analysis
all_categories = []
for s in ranked_stocks[:10]:
    all_categories.extend(s['categories'])

from collections import Counter
cat_count = Counter(all_categories)

print(f"\n📈 Top 10 Sentiment Distribution:")
print(f"   • Bullish signals: {cat_count.get('BULLISH', 0)}")
print(f"   • Neutral signals: {cat_count.get('NEUTRAL', 0)}")
print(f"   • Bearish signals: {cat_count.get('BEARISH', 0)}")

# Find high-value deals
high_value = [s for s in ranked_stocks if s['max_magnitude'] >= 100]
if high_value:
    print(f"\n💰 Large Deal Activity ({len(high_value)} stocks):")
    for s in high_value[:5]:
        print(f"   • {s['stock']}: ₹{s['max_magnitude']:.0f} crore")

print("\n⚠️  DISCLAIMER: This is news-based analysis only. Always conduct thorough")
print("   due diligence including technical analysis, fundamentals, and risk assessment.")

print("\n" + "="*80)
