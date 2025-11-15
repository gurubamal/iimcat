#!/usr/bin/env python3
"""
QUANTITATIVE SCORER - Pure Data-Driven Analysis
================================================
Fallback scorer when AI violates constraints or for validation baseline.

Uses ONLY provided data - NO AI interpretation needed.
This is the "ground truth" score that AI should approximate.
"""

import re
from typing import Dict, Optional


def quantitative_score(news: dict, yf_data: dict) -> dict:
    """
    Calculate score using ONLY provided data, no AI interpretation.

    Returns:
        dict with score, sentiment, certainty, reasoning
    """

    score = 50  # Neutral baseline
    components = {'news': 0, 'technical': 0, 'volume': 0}

    # ========================================================================
    # NEWS COMPONENT (40% weight)
    # ========================================================================
    news_score = 0
    news_type = news.get('news_type', 'general')

    # Earnings analysis
    if news_type == 'earnings':
        earnings_growth = extract_yoy_growth(news.get('full_text', ''))
        if earnings_growth is not None:
            if earnings_growth > 30:
                news_score = 35
            elif earnings_growth > 20:
                news_score = 30
            elif earnings_growth > 10:
                news_score = 25
            elif earnings_growth > 5:
                news_score = 20
            elif earnings_growth > 0:
                news_score = 15
            elif earnings_growth > -5:
                news_score = 10
            elif earnings_growth > -10:
                news_score = 5
            else:
                news_score = 0
        else:
            news_score = 15  # Default for earnings news without clear numbers

    # Dividend analysis
    elif news_type == 'dividend':
        dividend_yield = extract_dividend_yield(news.get('full_text', ''))
        if dividend_yield:
            if dividend_yield > 4:
                news_score = 25
            elif dividend_yield > 3:
                news_score = 20
            elif dividend_yield > 2:
                news_score = 15
            else:
                news_score = 10
        else:
            news_score = 12  # Default for dividend news

    # M&A/Deal analysis
    elif news_type == 'ma':
        deal_size = extract_deal_size_cr(news.get('full_text', ''))
        market_cap = yf_data.get('market_context', {}).get('market_cap')

        if deal_size and market_cap:
            deal_impact_pct = (deal_size * 10000000 / market_cap) * 100  # crores to actual
            if deal_impact_pct > 15:
                news_score = 35
            elif deal_impact_pct > 10:
                news_score = 30
            elif deal_impact_pct > 5:
                news_score = 25
            else:
                news_score = 15
        else:
            news_score = 18  # Default for M&A news

    # Sector news
    elif news_type == 'sector':
        news_score = 15  # Neutral for sector-wide news

    # General news - sentiment based
    else:
        text = (news.get('headline', '') + ' ' + news.get('full_text', '')).lower()
        positive_count = count_positive_words(text)
        negative_count = count_negative_words(text)

        if positive_count > negative_count * 1.5:
            news_score = 20
        elif negative_count > positive_count * 1.5:
            news_score = 5
        else:
            news_score = 12

    components['news'] = news_score

    # ========================================================================
    # TECHNICAL COMPONENT (40% weight)
    # ========================================================================
    tech_score = 0
    technical = yf_data.get('technical', {})

    # RSI scoring (15 points max)
    rsi = technical.get('rsi_14')
    if rsi:
        if 45 <= rsi <= 55:
            tech_score += 12  # Neutral zone
        elif 40 <= rsi <= 60:
            tech_score += 10  # Healthy range
        elif rsi > 70:
            tech_score += 6  # Overbought (risky)
        elif rsi < 30:
            tech_score += 8  # Oversold (opportunity but risky)
        else:
            tech_score += 10

    # Trend scoring - Price vs SMA (15 points max)
    price_vs_sma20 = technical.get('price_vs_sma20_pct')
    if price_vs_sma20 is not None:
        if price_vs_sma20 > 5:
            tech_score += 12
        elif price_vs_sma20 > 2:
            tech_score += 14
        elif price_vs_sma20 > 0:
            tech_score += 15
        elif price_vs_sma20 > -2:
            tech_score += 12
        elif price_vs_sma20 > -5:
            tech_score += 8
        else:
            tech_score += 4

    # Momentum scoring (10 points max)
    momentum_10d = technical.get('momentum_10d_pct')
    if momentum_10d is not None:
        if momentum_10d > 15:
            tech_score += 10
        elif momentum_10d > 10:
            tech_score += 9
        elif momentum_10d > 5:
            tech_score += 8
        elif momentum_10d > 0:
            tech_score += 7
        elif momentum_10d > -5:
            tech_score += 5
        else:
            tech_score += 3

    components['technical'] = tech_score

    # ========================================================================
    # VOLUME COMPONENT (20% weight)
    # ========================================================================
    volume_score = 0
    volume_ratio = technical.get('volume_ratio')

    if volume_ratio:
        if volume_ratio > 2.5:
            volume_score = 20  # Very high volume
        elif volume_ratio > 2:
            volume_score = 18
        elif volume_ratio > 1.5:
            volume_score = 16
        elif volume_ratio > 1.2:
            volume_score = 14
        elif volume_ratio > 1:
            volume_score = 12
        elif volume_ratio > 0.8:
            volume_score = 10
        else:
            volume_score = 8  # Low volume

    components['volume'] = volume_score

    # ========================================================================
    # COMBINE COMPONENTS
    # ========================================================================
    final_score = (
        components['news'] * 0.40 +
        components['technical'] * 0.40 +
        components['volume'] * 0.20
    )

    final_score = min(100, max(0, final_score))

    # ========================================================================
    # DETERMINE SENTIMENT
    # ========================================================================
    if final_score > 65:
        sentiment = 'bullish'
    elif final_score < 45:
        sentiment = 'bearish'
    else:
        sentiment = 'neutral'

    # ========================================================================
    # CALCULATE CERTAINTY (based on data completeness)
    # ========================================================================
    certainty = calculate_data_completeness(yf_data) * 100

    # ========================================================================
    # BUILD REASONING
    # ========================================================================
    reasoning = (
        f"Quantitative scoring: News={components['news']:.0f}/40, "
        f"Technical={components['technical']:.0f}/40, "
        f"Volume={components['volume']:.0f}/20. "
        f"Total={final_score:.0f}/100."
    )

    return {
        'score': round(final_score, 1),
        'sentiment': sentiment,
        'certainty': round(certainty, 0),
        'recommendation': 'BUY' if final_score > 70 else ('SELL' if final_score < 35 else 'HOLD'),
        'reasoning': reasoning,
        'expected_move_pct': estimate_move_pct(final_score, sentiment),
        'method': 'quantitative',
        'components': components
    }


# ============================================================================
# HELPER FUNCTIONS - Data Extraction
# ============================================================================

def extract_yoy_growth(text: str) -> Optional[float]:
    """Extract YoY growth percentage from text."""

    # Patterns: "up 15% YoY", "15% YoY growth", "declined 10% YoY"
    patterns = [
        r'(?:up|rise|rose|gain|increase[d]?|growth)\s+(?:by\s+)?(\d+\.?\d*)%?\s*(?:yoy|y-o-y|year.over.year)',
        r'(\d+\.?\d*)%?\s*(?:yoy|y-o-y|year.over.year)\s*(?:growth|increase|rise)',
        r'(?:down|decline[d]?|fall|fell|drop(?:ped)?)\s+(?:by\s+)?(\d+\.?\d*)%?\s*(?:yoy|y-o-y|year.over.year)',
        r'(\d+\.?\d*)%?\s*(?:yoy|y-o-y|year.over.year)\s*(?:decline|decrease|fall)',
    ]

    text_lower = text.lower()

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            value = float(match.group(1))
            # Check if it's a decline
            if any(word in text_lower[max(0, match.start()-30):match.end()+10]
                   for word in ['decline', 'fall', 'drop', 'down', 'decrease']):
                return -value
            return value

    return None


def extract_dividend_yield(text: str) -> Optional[float]:
    """Extract dividend yield percentage from text."""

    patterns = [
        r'dividend\s+yield\s+of\s+(\d+\.?\d*)%',
        r'(\d+\.?\d*)%\s+dividend\s+yield',
        r'yield:\s+(\d+\.?\d*)%'
    ]

    text_lower = text.lower()

    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return float(match.group(1))

    return None


def extract_deal_size_cr(text: str) -> Optional[float]:
    """Extract deal size in crores from text."""

    patterns = [
        r'₹?\s*(\d+(?:,\d+)*)\s*(?:crore|cr)',
        r'rs\.?\s*(\d+(?:,\d+)*)\s*(?:crore|cr)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value_str = match.group(1).replace(',', '')
            return float(value_str)

    return None


def count_positive_words(text: str) -> int:
    """Count positive sentiment words."""

    positive_words = [
        'profit', 'growth', 'gain', 'rise', 'surge', 'beat', 'record', 'strong',
        'robust', 'exceed', 'up', 'increase', 'expand', 'improve', 'positive',
        'success', 'win', 'achieve', 'outperform', 'boost', 'jump'
    ]

    return sum(1 for word in positive_words if word in text)


def count_negative_words(text: str) -> int:
    """Count negative sentiment words."""

    negative_words = [
        'loss', 'decline', 'fall', 'drop', 'weak', 'miss', 'concern', 'down',
        'decrease', 'shrink', 'contract', 'worry', 'negative', 'fail', 'disappoint',
        'underperform', 'slump', 'plunge', 'cut', 'reduce'
    ]

    return sum(1 for word in negative_words if word in text)


def calculate_data_completeness(yf_data: dict) -> float:
    """Calculate what % of expected data fields are present."""

    expected_fields = [
        ('price', 'current'),
        ('price', 'previous_close'),
        ('technical', 'rsi_14'),
        ('technical', 'sma_20'),
        ('technical', 'sma_50'),
        ('technical', 'volume_ratio'),
        ('technical', 'momentum_10d_pct'),
        ('extended_technical', 'week_52_high'),
        ('extended_technical', 'atr_14'),
    ]

    present = 0
    for category, field in expected_fields:
        if yf_data.get(category, {}).get(field) is not None:
            present += 1

    return present / len(expected_fields)


def estimate_move_pct(score: float, sentiment: str) -> float:
    """Estimate expected price move % based on score."""

    if sentiment == 'bullish':
        if score > 85:
            return 8.0
        elif score > 75:
            return 6.0
        elif score > 65:
            return 4.0
        else:
            return 2.0
    elif sentiment == 'bearish':
        if score < 25:
            return -8.0
        elif score < 35:
            return -6.0
        elif score < 45:
            return -4.0
        else:
            return -2.0
    else:
        return 0.0


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    # Test with sample data
    test_news = {
        'headline': 'Company Q2 PAT rises 25% YoY',
        'full_text': 'The company reported Q2 PAT up 25% YoY to Rs 500 crore.',
        'news_type': 'earnings'
    }

    test_yf_data = {
        'price': {
            'current': 1500,
            'previous_close': 1480
        },
        'technical': {
            'rsi_14': 55.2,
            'sma_20': 1450,
            'sma_50': 1420,
            'price_vs_sma20_pct': 3.4,
            'price_vs_sma50_pct': 5.6,
            'momentum_10d_pct': 6.5,
            'volume_ratio': 1.8
        },
        'extended_technical': {
            'week_52_high': 1600,
            'week_52_low': 1100,
            'atr_14': 35
        }
    }

    result = quantitative_score(test_news, test_yf_data)

    print("Quantitative Score Result:")
    print(f"  Score: {result['score']}")
    print(f"  Sentiment: {result['sentiment']}")
    print(f"  Certainty: {result['certainty']}%")
    print(f"  Recommendation: {result['recommendation']}")
    print(f"  Reasoning: {result['reasoning']}")
    print(f"  Components: {result['components']}")
