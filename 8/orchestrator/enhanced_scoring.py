"""
Enhanced Scoring Module with Certainty, Expected Rise, and Fake Rally Detection
Integrated into the main analysis flow
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class EnhancedScorer:
    """Enhanced scoring with certainty, expected rise, and fake rally detection"""
    
    # Thresholds
    MIN_CERTAINTY = 40  # Minimum certainty to qualify
    MIN_MAGNITUDE_CR = 50  # Minimum deal size in crores
    
    # Premium sources for credibility scoring
    PREMIUM_SOURCES = [
        'economictimes.indiatimes.com', 'livemint.com', 'reuters.com',
        'business-standard.com', 'thehindubusinessline.com', 'moneycontrol.com'
    ]
    
    @staticmethod
    def calculate_certainty(title: str, source: str = "", article_count: int = 1) -> Tuple[float, List[str]]:
        """
        Calculate certainty score (0-100%) based on news quality
        
        Returns: (certainty_score, reasons_list)
        """
        certainty = 0.0
        reasons = []
        
        title_lower = title.lower()
        
        # 1. Specificity Score (0-40 points)
        specificity = 0
        
        # Specific amounts mentioned
        if re.search(r'₹?\$?\d+(?:,\d+)*\s*(crore|million|billion|lakh)', title_lower):
            specificity += 15
            reasons.append("SPECIFIC_AMOUNT")
        
        # Percentages (growth rates)
        if re.search(r'\d+%', title):
            specificity += 10
            reasons.append("SPECIFIC_PERCENTAGE")
        
        # Quarters/periods mentioned
        if re.search(r'q[1-4]|fy\d{2}|quarter', title_lower):
            specificity += 8
            reasons.append("SPECIFIC_PERIOD")
        
        # Named authorities
        if re.search(r'(board|ceo|cfo|chairman|director|management)', title_lower):
            specificity += 7
            reasons.append("NAMED_AUTHORITY")
        
        certainty += min(specificity, 40)
        
        # 2. Source Credibility (0-25 points)
        credibility = 0
        source_lower = source.lower()
        
        if any(ps in source_lower for ps in EnhancedScorer.PREMIUM_SOURCES):
            credibility += 15
            reasons.append("PREMIUM_SOURCE")
        
        certainty += min(credibility, 25)
        
        # 3. Multiple Confirmations (0-20 points)
        if article_count >= 3:
            certainty += 20
            reasons.append("HIGH_COVERAGE")
        elif article_count == 2:
            certainty += 12
            reasons.append("DUAL_COVERAGE")
        
        # 4. Recency bonus (assumed fresh if in recent scan) (0-15 points)
        certainty += 10  # Default recency bonus for news in scan
        reasons.append("RECENT")
        
        return min(certainty, 100), reasons
    
    @staticmethod
    def detect_fake_rally(title: str, magnitude_cr: float) -> Tuple[bool, str]:
        """
        Detect fake rallies based on speculation and low magnitude
        
        Returns: (is_fake, reason)
        """
        title_lower = title.lower()
        
        # Speculation words
        hype_words = [
            'may', 'could', 'might', 'expected to', 'likely', 'planning to',
            'aims to', 'eyes', 'targets', 'mulls', 'exploring', 'considering'
        ]
        
        speculation_count = sum(1 for word in hype_words if word in title_lower)
        
        # High speculation = fake rally
        if speculation_count >= 2:
            return True, "HIGH_SPECULATION"
        
        # Speculation + low magnitude = fake rally
        if speculation_count >= 1 and magnitude_cr < 100:
            return True, "SPECULATION_LOW_MAGNITUDE"
        
        # Generic patterns without substance
        generic_patterns = [
            'announces plans', 'to focus on', 'expansion plans',
            'growth story', 'looks to', 'set to'
        ]
        
        if any(pattern in title_lower for pattern in generic_patterns) and magnitude_cr == 0:
            return True, "GENERIC_NO_NUMBERS"
        
        # Confirmed actions are NOT fake rallies
        confirmed_actions = [
            'completes', 'completed', 'signed', 'approved', 'announces',
            'reports', 'achieves', 'launches', 'acquires', 'raises'
        ]
        
        if any(action in title_lower for action in confirmed_actions):
            return False, "CONFIRMED_ACTION"
        
        return False, "OK"
    
    @staticmethod
    def calculate_expected_rise(magnitude_cr: float, market_cap_cr: float, 
                                sentiment_score: int) -> Tuple[float, float, str]:
        """
        Calculate expected price rise based on deal magnitude and sentiment
        
        Returns: (conservative_%, aggressive_%, confidence_level)
        """
        if market_cap_cr == 0 or market_cap_cr is None:
            # No market cap data, use sentiment-based estimate
            if sentiment_score >= 8:
                return 5.0, 12.0, "LOW"
            elif sentiment_score >= 5:
                return 3.0, 8.0, "LOW"
            else:
                return 0.0, 0.0, "UNKNOWN"
        
        # Base impact: deal size as % of market cap
        deal_impact = (magnitude_cr / market_cap_cr) * 100 if magnitude_cr > 0 else 0
        
        # Sentiment multiplier
        if sentiment_score >= 8:
            sentiment_mult = 2.5
            confidence = "HIGH"
        elif sentiment_score >= 5:
            sentiment_mult = 1.8
            confidence = "MEDIUM"
        else:
            sentiment_mult = 1.2
            confidence = "LOW"
        
        # Conservative: 30% of theoretical impact
        conservative = deal_impact * sentiment_mult * 0.3
        
        # Aggressive: 60% of theoretical impact
        aggressive = deal_impact * sentiment_mult * 0.6
        
        # Cap at reasonable levels
        conservative = min(conservative, 50)
        aggressive = min(aggressive, 100)
        
        # Add baseline for positive news without specific deals
        if magnitude_cr == 0 and sentiment_score >= 5:
            conservative = max(conservative, 5)
            aggressive = max(aggressive, 12)
        
        return round(conservative, 1), round(aggressive, 1), confidence
    
    @staticmethod
    def calculate_sentiment_score(title: str) -> int:
        """Calculate sentiment strength (-10 to +10)"""
        score = 0
        t = title.lower()
        
        # Positive signals
        positive_patterns = {
            r'profit.*growth|profit.*up|revenue.*growth|revenue.*up': 10,
            r'acquisition|acquires|merger': 9,
            r'dividend': 8,
            r'fund.*rais|investment|funding': 8,
            r'expansion|launches|new': 6,
            r'contract|order|deal': 7,
            r'ipo|listing': 6,
            r'record|surge|soar|jump': 8,
            r'beat.*estimate|exceed': 9,
        }
        
        for pattern, points in positive_patterns.items():
            if re.search(pattern, t):
                score += points
        
        # Negative signals
        negative_patterns = {
            r'loss|decline|fall|drop': -8,
            r'investigation|probe|fraud': -10,
            r'layoff|retrench': -7,
            r'downgrade': -7,
        }
        
        for pattern, points in negative_patterns.items():
            if re.search(pattern, t):
                score += points
        
        return max(-10, min(10, score))
    
    @staticmethod
    def extract_magnitude(title: str) -> float:
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
    
    @staticmethod
    def enhance_row(row: Dict[str, str], market_cap_cr: float = 0) -> Dict[str, any]:
        """
        Enhance a single news row with all scoring metrics
        
        Args:
            row: Dict with 'ticker', 'title', 'source', etc.
            market_cap_cr: Market cap in crores (if available)
        
        Returns:
            Enhanced dict with additional fields:
            - certainty_score
            - certainty_reasons
            - fake_rally_detected
            - fake_rally_reason
            - magnitude_cr
            - sentiment_score
            - expected_rise_min
            - expected_rise_max
            - rise_confidence
            - quality_status (QUALIFIED/REJECTED)
        """
        title = row.get('title', '')
        source = row.get('source', '')
        
        # Calculate all metrics
        certainty, reasons = EnhancedScorer.calculate_certainty(title, source, 1)
        magnitude = EnhancedScorer.extract_magnitude(title)
        sentiment = EnhancedScorer.calculate_sentiment_score(title)
        is_fake, fake_reason = EnhancedScorer.detect_fake_rally(title, magnitude)
        rise_min, rise_max, rise_conf = EnhancedScorer.calculate_expected_rise(
            magnitude, market_cap_cr, sentiment
        )
        
        # Determine quality status
        quality_status = "QUALIFIED"
        rejection_reason = None
        
        if is_fake:
            quality_status = "REJECTED"
            rejection_reason = f"FAKE_RALLY:{fake_reason}"
        elif certainty < EnhancedScorer.MIN_CERTAINTY:
            quality_status = "REJECTED"
            rejection_reason = f"LOW_CERTAINTY:{certainty:.0f}%"
        elif magnitude > 0 and magnitude < EnhancedScorer.MIN_MAGNITUDE_CR:
            quality_status = "REJECTED"
            rejection_reason = f"LOW_MAGNITUDE:{magnitude:.0f}cr"
        
        # Add enhanced fields
        enhanced = row.copy()
        enhanced.update({
            'certainty_score': round(certainty, 1),
            'certainty_reasons': ','.join(reasons),
            'fake_rally_detected': is_fake,
            'fake_rally_reason': fake_reason,
            'magnitude_cr': round(magnitude, 2),
            'sentiment_score': sentiment,
            'expected_rise_min': rise_min,
            'expected_rise_max': rise_max,
            'rise_confidence': rise_conf,
            'quality_status': quality_status,
            'rejection_reason': rejection_reason or 'N/A'
        })
        
        return enhanced
    
    @staticmethod
    def filter_and_rank(rows: List[Dict], top_n: int = 25) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter fake rallies and low quality, then rank by combined score
        
        Returns: (qualified_list, rejected_list)
        """
        qualified = []
        rejected = []
        
        for row in rows:
            if row.get('quality_status') == 'QUALIFIED':
                # Calculate combined score for ranking
                certainty = row.get('certainty_score', 0)
                rise_min = row.get('expected_rise_min', 0)
                magnitude = row.get('magnitude_cr', 0)
                sentiment = row.get('sentiment_score', 0)
                
                # Combined score: certainty * expected_rise + magnitude bonus
                combined_score = (certainty / 100) * rise_min + (magnitude / 1000) + (sentiment / 10)
                row['combined_score'] = round(combined_score, 2)
                
                qualified.append(row)
            else:
                rejected.append(row)
        
        # Sort qualified by combined score
        qualified.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        return qualified[:top_n], rejected


def add_enhanced_scoring_to_csv(input_csv: str, output_csv: str, 
                                market_caps: Dict[str, float] = None) -> Tuple[int, int]:
    """
    Add enhanced scoring to an existing CSV file
    
    Args:
        input_csv: Path to input CSV with news
        output_csv: Path to output enhanced CSV
        market_caps: Optional dict of {ticker: market_cap_cr}
    
    Returns:
        (qualified_count, rejected_count)
    """
    if market_caps is None:
        market_caps = {}
    
    # Read input CSV
    rows = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Enhance each row
    enhanced_rows = []
    for row in rows:
        ticker = row.get('ticker', '')
        mcap = market_caps.get(ticker, 0)
        enhanced = EnhancedScorer.enhance_row(row, mcap)
        enhanced_rows.append(enhanced)
    
    # Filter and rank
    qualified, rejected = EnhancedScorer.filter_and_rank(enhanced_rows)
    
    # Write output CSV
    if qualified:
        fieldnames = list(qualified[0].keys())
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(qualified)
    
    # Also write rejected to separate file
    if rejected:
        rejected_csv = output_csv.replace('.csv', '_rejected.csv')
        fieldnames = list(rejected[0].keys())
        with open(rejected_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rejected)
    
    return len(qualified), len(rejected)
