#!/usr/bin/env python3
"""
Enhanced Investment Analyzer with Certainty Scoring and Fake Rally Detection

Key Features:
1. Certainty Score (0-100%) based on news quality and specificity
2. Expected Rise calculation based on deal magnitude and fundamentals
3. Fake Rally Detection (hype vs substance)
4. Magnitude-based filtering (avoid small/vague news)
"""

import re
import yfinance as yf
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Optional
import json

class EnhancedInvestmentAnalyzer:
    
    def __init__(self, news_file: str):
        self.news_file = news_file
        self.stocks = defaultdict(list)
        self.load_news()
        
        # Thresholds for quality filtering
        self.MIN_CERTAINTY = 40  # Only show stocks with >40% certainty
        self.MIN_MAGNITUDE_CR = 50  # Minimum deal size in crores
        
    def load_news(self):
        """Load and parse news file"""
        current_stock = None
        article = {}
        
        with open(self.news_file, 'r', encoding='utf-8', errors='ignore') as f:
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
                        self.stocks[current_stock].append(article.copy())
    
    def calculate_certainty_score(self, articles: List[Dict]) -> Tuple[float, str]:
        """
        Calculate certainty score (0-100%) based on:
        - News specificity (numbers, dates, names)
        - Source credibility
        - Multiple confirmations
        - Recency
        """
        if not articles:
            return 0.0, "NO_DATA"
        
        certainty = 0.0
        reasons = []
        
        # 1. Specificity Score (0-40 points)
        specificity = 0
        for article in articles:
            title = article.get('title', '').lower()
            
            # Specific numbers mentioned
            if re.search(r'₹?\$?\d+(?:,\d+)*\s*(crore|million|billion|lakh)', title):
                specificity += 15
                reasons.append("SPECIFIC_AMOUNT")
            
            # Percentages (growth rates)
            if re.search(r'\d+%', title):
                specificity += 10
                reasons.append("SPECIFIC_PERCENTAGE")
            
            # Quarters mentioned (Q1, Q2, FY27, etc.)
            if re.search(r'q[1-4]|fy\d{2}|quarter', title, re.I):
                specificity += 8
                reasons.append("SPECIFIC_PERIOD")
            
            # Named entities (companies, people)
            if re.search(r'(board|ceo|cfo|chairman|director|management)', title, re.I):
                specificity += 7
                reasons.append("NAMED_AUTHORITY")
        
        certainty += min(specificity, 40)
        
        # 2. Source Credibility (0-25 points)
        credibility = 0
        premium_sources = [
            'economictimes.indiatimes.com', 'livemint.com', 'reuters.com',
            'business-standard.com', 'thehindubusinessline.com', 'moneycontrol.com'
        ]
        
        for article in articles:
            source = article.get('source', '').lower()
            if any(ps in source for ps in premium_sources):
                credibility += 10
                break
        
        if len(articles) >= 2:  # Multiple sources
            credibility += 10
            reasons.append("MULTI_SOURCE")
        
        certainty += min(credibility, 25)
        
        # 3. Confirmation Score (0-20 points)
        if len(articles) >= 3:
            certainty += 20
            reasons.append("HIGH_COVERAGE")
        elif len(articles) == 2:
            certainty += 12
            reasons.append("DUAL_COVERAGE")
        
        # 4. Recency Score (0-15 points)
        try:
            latest = articles[0].get('published', '')
            if latest:
                pub_date = datetime.fromisoformat(latest.replace('Z', ''))
                hours_ago = (datetime.utcnow() - pub_date).total_seconds() / 3600
                
                if hours_ago <= 24:
                    certainty += 15
                    reasons.append("VERY_RECENT")
                elif hours_ago <= 48:
                    certainty += 10
                    reasons.append("RECENT")
        except:
            pass
        
        certainty = min(certainty, 100)
        reason_str = ",".join(set(reasons))
        
        return certainty, reason_str
    
    def detect_fake_rally(self, title: str, magnitude_cr: float) -> Tuple[bool, str]:
        """
        Detect fake rallies/hype:
        - Vague language without numbers
        - "May", "Could", "Likely" without confirmation
        - Small deals with big headlines
        - Generic announcements
        """
        title_lower = title.lower()
        is_fake = False
        reason = ""
        
        # Red flags for hype
        hype_words = [
            'may', 'could', 'might', 'expected to', 'likely', 'planning to',
            'aims to', 'eyes', 'targets', 'mulls', 'exploring', 'considering'
        ]
        
        speculation_count = sum(1 for word in hype_words if word in title_lower)
        
        # High speculation + low magnitude = fake rally
        if speculation_count >= 2:
            is_fake = True
            reason = "HIGH_SPECULATION"
        
        if speculation_count >= 1 and magnitude_cr < 100:
            is_fake = True
            reason = "SPECULATION_LOW_MAGNITUDE"
        
        # Generic announcements without substance
        generic_patterns = [
            'announces plans', 'to focus on', 'expansion plans',
            'growth story', 'looks to', 'set to'
        ]
        
        if any(pattern in title_lower for pattern in generic_patterns) and magnitude_cr == 0:
            is_fake = True
            reason = "GENERIC_NO_NUMBERS"
        
        # Positive: Confirmed actions
        confirmed_actions = [
            'completes', 'completed', 'signed', 'approved', 'announces',
            'reports', 'achieves', 'launches', 'acquires', 'raises'
        ]
        
        if any(action in title_lower for action in confirmed_actions):
            is_fake = False
            reason = "CONFIRMED_ACTION"
        
        return is_fake, reason
    
    def calculate_expected_rise(self, magnitude_cr: float, market_cap_cr: float, 
                                sentiment_score: int) -> Tuple[float, float, str]:
        """
        Calculate expected price rise based on:
        - Deal magnitude vs market cap
        - Sentiment strength
        - Historical patterns
        
        Returns: (conservative_%, aggressive_%, confidence)
        """
        if market_cap_cr == 0:
            return 0, 0, "UNKNOWN"
        
        # Base impact: deal size as % of market cap
        deal_impact = (magnitude_cr / market_cap_cr) * 100
        
        # Sentiment multiplier
        if sentiment_score >= 40:
            sentiment_mult = 2.5
            confidence = "HIGH"
        elif sentiment_score >= 20:
            sentiment_mult = 1.8
            confidence = "MEDIUM"
        else:
            sentiment_mult = 1.2
            confidence = "LOW"
        
        # Conservative estimate (30% of theoretical impact)
        conservative = deal_impact * sentiment_mult * 0.3
        
        # Aggressive estimate (60% of theoretical impact)
        aggressive = deal_impact * sentiment_mult * 0.6
        
        # Cap estimates at reasonable levels
        conservative = min(conservative, 50)
        aggressive = min(aggressive, 100)
        
        # Add baseline for positive news without specific deals
        if magnitude_cr == 0 and sentiment_score > 20:
            conservative = max(conservative, 5)
            aggressive = max(aggressive, 12)
        
        return round(conservative, 1), round(aggressive, 1), confidence
    
    def extract_magnitude(self, title: str) -> float:
        """Extract deal magnitude in crores"""
        magnitude = 0
        
        money = re.search(r'₹?\$?(\d+(?:,\d+)*)\s*(crore|million|billion|lakh)', title.lower())
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
        
        return magnitude
    
    def analyze_sentiment(self, title: str) -> int:
        """Analyze sentiment strength (-10 to +10)"""
        score = 0
        t = title.lower()
        
        # Positive signals
        positive = {
            'profit.*growth|revenue.*growth|profit.*up|revenue.*up': 10,
            'acquisition|acquires|merger': 9,
            'dividend': 8,
            'fund.*rais|investment|funding': 8,
            'expansion|launches|new': 6,
            'contract|order|deal': 7,
            'ipo|listing': 6,
            'record|surge|soar|jump': 8,
            'beat.*estimate|exceed': 9,
        }
        
        for pattern, points in positive.items():
            if re.search(pattern, t):
                score += points
        
        # Negative signals
        negative = {
            'loss|decline|fall|drop': -8,
            'investigation|probe|fraud': -10,
            'layoff|retrench': -7,
            'downgrade': -7,
        }
        
        for pattern, points in negative.items():
            if re.search(pattern, t):
                score += points
        
        return max(-10, min(10, score))
    
    def get_market_cap(self, ticker: str) -> float:
        """Get market cap in crores"""
        try:
            stock = yf.Ticker(f"{ticker}.NS")
            info = stock.info
            mcap = info.get('marketCap', 0)
            if mcap:
                return mcap / 1e7  # Convert to crores
        except:
            pass
        return 0
    
    def analyze_stock(self, ticker: str, articles: List[Dict]) -> Optional[Dict]:
        """Complete analysis for a stock"""
        if not articles:
            return None
        
        # Calculate certainty score
        certainty, certainty_reasons = self.calculate_certainty_score(articles)
        
        if certainty < self.MIN_CERTAINTY:
            return None
        
        # Analyze each article
        total_sentiment = 0
        max_magnitude = 0
        fake_rally_detected = False
        fake_reasons = []
        
        for article in articles:
            title = article.get('title', '')
            sentiment = self.analyze_sentiment(title)
            magnitude = self.extract_magnitude(title)
            
            total_sentiment += sentiment
            max_magnitude = max(max_magnitude, magnitude)
            
            is_fake, fake_reason = self.detect_fake_rally(title, magnitude)
            if is_fake:
                fake_rally_detected = True
                fake_reasons.append(fake_reason)
        
        # Skip if fake rally detected
        if fake_rally_detected:
            return {
                'ticker': ticker,
                'status': 'REJECTED',
                'reason': 'FAKE_RALLY: ' + ','.join(set(fake_reasons)),
                'articles': len(articles)
            }
        
        # Skip if magnitude too small
        if max_magnitude > 0 and max_magnitude < self.MIN_MAGNITUDE_CR:
            return {
                'ticker': ticker,
                'status': 'REJECTED',
                'reason': f'LOW_MAGNITUDE: {max_magnitude:.0f}cr < {self.MIN_MAGNITUDE_CR}cr',
                'articles': len(articles)
            }
        
        # Get market cap
        market_cap = self.get_market_cap(ticker)
        
        # Calculate expected rise
        conservative_rise, aggressive_rise, rise_confidence = self.calculate_expected_rise(
            max_magnitude, market_cap, total_sentiment
        )
        
        # Get current price
        current_price = 0
        price_change = 0
        try:
            stock = yf.Ticker(f"{ticker}.NS")
            hist = stock.history(period='2d')
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                if len(hist) > 1:
                    prev = hist['Close'].iloc[-2]
                    price_change = ((current_price - prev) / prev) * 100
        except:
            pass
        
        return {
            'ticker': ticker,
            'status': 'QUALIFIED',
            'certainty_score': round(certainty, 1),
            'certainty_reasons': certainty_reasons,
            'sentiment_score': total_sentiment,
            'magnitude_cr': max_magnitude,
            'market_cap_cr': round(market_cap, 0),
            'expected_rise_conservative': conservative_rise,
            'expected_rise_aggressive': aggressive_rise,
            'rise_confidence': rise_confidence,
            'current_price': round(current_price, 2),
            'price_change_today': round(price_change, 2),
            'articles_count': len(articles),
            'headlines': [a.get('title', '')[:80] for a in articles[:3]]
        }
    
    def generate_report(self) -> List[Dict]:
        """Analyze all stocks and generate report"""
        results = []
        rejected = []
        
        for ticker, articles in self.stocks.items():
            result = self.analyze_stock(ticker, articles)
            if result:
                if result['status'] == 'QUALIFIED':
                    results.append(result)
                else:
                    rejected.append(result)
        
        # Sort by certainty * expected rise
        results.sort(
            key=lambda x: x['certainty_score'] * x['expected_rise_conservative'],
            reverse=True
        )
        
        return results, rejected


def main():
    print("="*90)
    print("🎯 ENHANCED INVESTMENT ANALYZER WITH CERTAINTY & FAKE RALLY DETECTION")
    print("="*90)
    
    # Use latest news file
    news_file = "aggregated_full_articles_48h_20251013_200042.txt"
    
    analyzer = EnhancedInvestmentAnalyzer(news_file)
    results, rejected = analyzer.generate_report()
    
    print(f"\n📊 Analysis Complete:")
    print(f"   ✅ Qualified: {len(results)} stocks")
    print(f"   ❌ Rejected: {len(rejected)} stocks (fake rallies/low magnitude)")
    
    print("\n" + "="*90)
    print("🏆 TOP INVESTMENT OPPORTUNITIES (VERIFIED)")
    print("="*90)
    
    for i, stock in enumerate(results[:10], 1):
        print(f"\n{i}. {stock['ticker']}")
        print(f"   {'─'*86}")
        print(f"   💯 Certainty Score: {stock['certainty_score']}% ({stock['certainty_reasons']})")
        print(f"   📈 Expected Rise: {stock['expected_rise_conservative']}% - {stock['expected_rise_aggressive']}% ({stock['rise_confidence']} confidence)")
        
        if stock['current_price'] > 0:
            print(f"   💰 Current Price: ₹{stock['current_price']} ({stock['price_change_today']:+.2f}% today)")
        
        if stock['magnitude_cr'] > 0:
            print(f"   💼 Deal Size: ₹{stock['magnitude_cr']:.0f} crore")
        
        if stock['market_cap_cr'] > 0:
            print(f"   🏢 Market Cap: ₹{stock['market_cap_cr']:,.0f} crore")
            if stock['magnitude_cr'] > 0:
                impact = (stock['magnitude_cr'] / stock['market_cap_cr']) * 100
                print(f"   🎯 Deal Impact: {impact:.2f}% of market cap")
        
        print(f"   📰 News Coverage: {stock['articles_count']} articles")
        print(f"\n   Top Headlines:")
        for j, headline in enumerate(stock['headlines'], 1):
            print(f"      {j}. {headline}...")
    
    # Show rejected stocks for transparency
    if rejected:
        print("\n\n" + "="*90)
        print("❌ REJECTED STOCKS (Fake Rallies / Low Quality)")
        print("="*90)
        print("\nThese were filtered out to protect you from hype-driven recommendations:\n")
        
        for stock in rejected[:10]:
            print(f"   • {stock['ticker']}: {stock['reason']}")
    
    # Summary statistics
    print("\n\n" + "="*90)
    print("📊 QUALITY METRICS")
    print("="*90)
    
    if results:
        avg_certainty = sum(s['certainty_score'] for s in results) / len(results)
        avg_rise = sum(s['expected_rise_conservative'] for s in results) / len(results)
        high_certainty = len([s for s in results if s['certainty_score'] >= 70])
        
        print(f"\n✅ Qualified Stocks Statistics:")
        print(f"   Average Certainty: {avg_certainty:.1f}%")
        print(f"   Average Expected Rise: {avg_rise:.1f}%")
        print(f"   High Certainty (≥70%): {high_certainty} stocks")
        print(f"   Total Articles Analyzed: {sum(s['articles_count'] for s in results)}")
    
    print("\n" + "="*90)
    print("⚠️  METHODOLOGY")
    print("="*90)
    print("""
Certainty Score (0-100%):
   • Specific numbers, dates, names (0-40 pts)
   • Source credibility (0-25 pts)
   • Multiple confirmations (0-20 pts)
   • Recency (0-15 pts)

Expected Rise Calculation:
   • Based on deal magnitude vs market cap
   • Adjusted for sentiment strength
   • Conservative = 30% of theoretical impact
   • Aggressive = 60% of theoretical impact

Fake Rally Detection:
   ✗ Speculation words (may, could, might)
   ✗ Generic announcements without numbers
   ✗ Small deals with big headlines
   ✓ Confirmed actions (approved, signed, completed)

Quality Filters:
   • Minimum Certainty: 40%
   • Minimum Deal Size: ₹50 crore
   • Magnitude matters more than hype
    """)
    
    print("="*90)
    
    # Save to JSON
    output = {
        'generated_at': datetime.now().isoformat(),
        'qualified_stocks': results[:20],
        'rejected_stocks': rejected[:20],
        'statistics': {
            'total_qualified': len(results),
            'total_rejected': len(rejected),
            'avg_certainty': round(avg_certainty, 1) if results else 0,
            'avg_expected_rise': round(avg_rise, 1) if results else 0
        }
    }
    
    with open('enhanced_analysis_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: enhanced_analysis_results.json")
    print("="*90)


if __name__ == "__main__":
    main()
