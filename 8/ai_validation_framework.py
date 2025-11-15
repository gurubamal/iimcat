#!/usr/bin/env python3
"""
AI VALIDATION FRAMEWORK
=======================
Ensures AI uses ZERO training data - only provided NEWS + YFINANCE data.

Multi-layer validation:
1. Constrained prompting
2. Citation enforcement
3. Response validation
4. Quantitative fallback
5. Ranking validation
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime


class AIResponseValidator:
    """Validate AI response meets all constraints - NO TRAINING DATA ALLOWED."""

    FORBIDDEN_PHRASES = [
        # Historical knowledge
        r"\bhistorically\b",
        r"\btypically\b",
        r"\busually\b",
        r"\btraditionally\b",
        r"\bgenerally\b",

        # External knowledge
        r"\bknown for\b",
        r"\btrack record\b",
        r"\breputation\b",
        r"\bis a leader\b",
        r"\bblue.?chip\b",
        r"\bbellwether\b",

        # Comparisons without provided data
        r"\bcompared to (?:industry|sector|peers)\b",
        r"\bindustry average\b",
        r"\bsector average\b",
        r"\bpeer comparison\b",

        # Analyst/external opinions
        r"\banalyst[s]?\b(?! in the article| mentioned)",
        r"\bconsensus\b",
        r"\bforecast[s]?\b(?! in| mentioned)",
        r"\bexpect(?:ed|ation|s)?\b(?! in| mentioned)",

        # Valuation without provided data
        r"\bfair value\b",
        r"\bintrinsic value\b",
        r"\bundervalued\b(?! based on)",
        r"\bovervalued\b(?! based on)",
    ]

    def validate(self, ai_response: dict, news: dict, yf_data: dict) -> dict:
        """Run all validation checks."""

        results = {}

        # CHECK 1: No Training Data Usage
        results['no_training_data'] = self.check_no_training_data(
            ai_response, news, yf_data
        )

        # CHECK 2: All Numbers Cited
        results['all_numbers_cited'] = self.check_all_numbers_cited(
            ai_response, yf_data
        )

        # CHECK 3: Score Reasonable
        results['score_reasonable'] = self.check_score_reasonable(
            ai_response, news, yf_data
        )

        # CHECK 4: Sentiment Matches Data
        results['sentiment_matches'] = self.check_sentiment_matches_data(
            ai_response, news, yf_data
        )

        # Overall pass/fail
        all_passed = all(r.get('passed', False) for r in results.values())

        return {
            'passed': all_passed,
            'checks': results,
            'action': 'accept' if all_passed else 'use_quantitative_fallback',
            'violations_count': sum(
                len(r.get('violations', [])) for r in results.values()
            )
        }

    def check_no_training_data(self, ai_response: dict, news: dict, yf_data: dict) -> dict:
        """Detect if AI used training data."""

        violations = []
        reasoning = ai_response.get('reasoning', '')

        # Check forbidden phrases
        for pattern in self.FORBIDDEN_PHRASES:
            matches = re.finditer(pattern, reasoning, re.IGNORECASE)
            for match in matches:
                context = reasoning[max(0, match.start()-30):min(len(reasoning), match.end()+30)]
                violations.append({
                    'type': 'forbidden_phrase',
                    'pattern': pattern,
                    'context': context.strip()
                })

        # Check for price references not in data
        price_mentions = re.findall(r'₹\s*[\d,]+\.?\d*|\$\s*[\d,]+\.?\d*', reasoning)
        for price in price_mentions:
            price_value = float(re.sub(r'[₹$,\s]', '', price))
            if not self._price_in_data(price_value, yf_data):
                violations.append({
                    'type': 'uncited_price',
                    'value': price,
                    'note': 'Price not found in provided data'
                })

        return {
            'passed': len(violations) == 0,
            'violations': violations,
            'check': 'no_training_data'
        }

    def check_all_numbers_cited(self, ai_response: dict, yf_data: dict) -> dict:
        """Verify all numerical claims are from provided data."""

        reasoning = ai_response.get('reasoning', '')
        violations = []

        # Extract all numbers from reasoning
        numbers = re.findall(r'\b\d+\.?\d*\b', reasoning)

        for num in numbers:
            num_float = float(num)

            # Skip generic numbers (days, percentages thresholds)
            if num_float in [7, 14, 20, 30, 50, 52, 100, 200]:
                continue

            # Check if number exists in data
            if not self._number_in_data(num_float, yf_data):
                context = self._get_number_context(reasoning, num)
                violations.append({
                    'type': 'uncited_number',
                    'value': num,
                    'context': context
                })

        return {
            'passed': len(violations) == 0,
            'violations': violations,
            'check': 'all_numbers_cited'
        }

    def check_score_reasonable(self, ai_response: dict, news: dict, yf_data: dict) -> dict:
        """Verify score aligns with data (not arbitrary)."""

        ai_score = ai_response.get('score', 50)

        # Calculate what score SHOULD be from pure data
        from ai_quantitative_scorer import quantitative_score
        expected = quantitative_score(news, yf_data)
        expected_score = expected['score']

        # Allow 20-point deviation (AI can add interpretation value)
        deviation = abs(ai_score - expected_score)

        if deviation > 20:
            return {
                'passed': False,
                'deviation': deviation,
                'ai_score': ai_score,
                'expected_score': expected_score,
                'reason': f'Score deviates {deviation} points from data-driven score (max allowed: 20)',
                'check': 'score_reasonable'
            }

        return {
            'passed': True,
            'deviation': deviation,
            'ai_score': ai_score,
            'expected_score': expected_score,
            'check': 'score_reasonable'
        }

    def check_sentiment_matches_data(self, ai_response: dict, news: dict, yf_data: dict) -> dict:
        """Verify sentiment matches actual data."""

        ai_sentiment = ai_response.get('sentiment', 'neutral')

        # Calculate expected sentiment from data
        news_sentiment = self._classify_news_sentiment(news)
        tech_sentiment = self._classify_technical_sentiment(yf_data)

        # Combine sentiments
        if news_sentiment == 'bearish' or tech_sentiment == 'bearish':
            expected = 'bearish'
        elif news_sentiment == 'bullish' and tech_sentiment in ['bullish', 'neutral']:
            expected = 'bullish'
        else:
            expected = 'neutral'

        # Allow some flexibility
        if ai_sentiment != expected:
            # Only fail if completely opposite
            if (ai_sentiment == 'bullish' and expected == 'bearish') or \
               (ai_sentiment == 'bearish' and expected == 'bullish'):
                return {
                    'passed': False,
                    'ai_sentiment': ai_sentiment,
                    'expected_sentiment': expected,
                    'reason': f'Sentiment mismatch: AI said {ai_sentiment}, data suggests {expected}',
                    'check': 'sentiment_matches'
                }

        return {
            'passed': True,
            'ai_sentiment': ai_sentiment,
            'expected_sentiment': expected,
            'check': 'sentiment_matches'
        }

    # Helper methods
    def _price_in_data(self, price: float, yf_data: dict) -> bool:
        """Check if price value exists in provided data."""
        price_data = yf_data.get('price', {})

        # Check against all price fields (with 1% tolerance)
        price_fields = [
            price_data.get('current'),
            price_data.get('previous_close'),
            price_data.get('day_high'),
            price_data.get('day_low'),
        ]

        for field_value in price_fields:
            if field_value and abs(price - field_value) / field_value < 0.01:
                return True

        return False

    def _number_in_data(self, num: float, yf_data: dict) -> bool:
        """Check if number exists anywhere in provided data."""

        # Check in all data structures
        def check_dict(d):
            for v in d.values():
                if isinstance(v, (int, float)):
                    if abs(num - v) < 0.1 or abs(num - abs(v)) < 0.1:
                        return True
                elif isinstance(v, dict):
                    if check_dict(v):
                        return True
            return False

        return check_dict(yf_data)

    def _get_number_context(self, text: str, num: str) -> str:
        """Get context around a number in text."""
        idx = text.find(num)
        if idx == -1:
            return ""
        start = max(0, idx - 40)
        end = min(len(text), idx + len(num) + 40)
        return "..." + text[start:end] + "..."

    def _classify_news_sentiment(self, news: dict) -> str:
        """Classify sentiment from news content."""
        text = (news.get('headline', '') + ' ' + news.get('full_text', '')).lower()

        positive_words = ['profit', 'growth', 'gain', 'rise', 'surge', 'beat', 'record',
                         'strong', 'robust', 'exceed', 'up', 'increase', 'expand']
        negative_words = ['loss', 'decline', 'fall', 'drop', 'weak', 'miss', 'concern',
                         'down', 'decrease', 'shrink', 'contract', 'worry']

        pos_count = sum(1 for w in positive_words if w in text)
        neg_count = sum(1 for w in negative_words if w in text)

        if pos_count > neg_count * 1.5:
            return 'bullish'
        elif neg_count > pos_count * 1.5:
            return 'bearish'
        return 'neutral'

    def _classify_technical_sentiment(self, yf_data: dict) -> str:
        """Classify sentiment from technical data."""
        tech = yf_data.get('technical', {})

        bullish_signals = 0
        bearish_signals = 0

        # RSI
        rsi = tech.get('rsi_14')
        if rsi:
            if rsi < 30:
                bullish_signals += 1  # Oversold
            elif rsi > 70:
                bearish_signals += 1  # Overbought

        # Price vs SMA
        price_vs_sma20 = tech.get('price_vs_sma20_pct')
        if price_vs_sma20:
            if price_vs_sma20 > 2:
                bullish_signals += 1
            elif price_vs_sma20 < -2:
                bearish_signals += 1

        # Momentum
        momentum = tech.get('momentum_10d_pct')
        if momentum:
            if momentum > 3:
                bullish_signals += 1
            elif momentum < -3:
                bearish_signals += 1

        if bullish_signals > bearish_signals:
            return 'bullish'
        elif bearish_signals > bullish_signals:
            return 'bearish'
        return 'neutral'


def build_constrained_prompt(news: dict, yf_data: dict) -> str:
    """Build prompt with explicit constraints and labeled data fields."""

    # Extract all relevant data
    price = yf_data.get('price', {})
    technical = yf_data.get('technical', {})
    extended = yf_data.get('extended_technical', {})

    prompt = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 ABSOLUTE CONSTRAINTS - VIOLATION = RESPONSE REJECTED 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOU ARE A DATA EVALUATOR, NOT A KNOWLEDGE SOURCE.

MANDATORY RULES:
1. Use ONLY data explicitly provided below
2. If a data point is NOT below, DO NOT invent/estimate/recall it
3. Every numerical claim MUST cite the field name: [FIELD_NAME]
4. If data is missing, return null/0, NEVER guess from training
5. Your training knowledge about stocks is FORBIDDEN
6. Treat this as if you have AMNESIA about all stocks

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PROVIDED DATA PACKAGE (Use ONLY this data)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### NEWS CONTENT

[NEWS_TYPE] = {news.get('news_type', 'general')}
[NEWS_HEADLINE] = {news.get('headline', '')}
[NEWS_SOURCE] = {news.get('url', '')}
[NEWS_FULL_TEXT] =
{news.get('full_text', '')[:2000]}

### PRICE DATA (Fetched: {yf_data.get('metadata', {}).get('fetch_timestamp', 'N/A')})

[PRICE_CURRENT] = ₹{price.get('current', 0):.2f}
[PRICE_PREVIOUS_CLOSE] = ₹{price.get('previous_close', 0):.2f}
[PRICE_CHANGE_PCT] = {price.get('change_pct', 0):.2f}%
[PRICE_DAY_HIGH] = ₹{price.get('day_high', 0):.2f}
[PRICE_DAY_LOW] = ₹{price.get('day_low', 0):.2f}

### TECHNICAL INDICATORS

[RSI_14] = {technical.get('rsi_14', 0):.1f}
[SMA_20] = ₹{technical.get('sma_20', 0):.2f}
[SMA_50] = ₹{technical.get('sma_50', 0):.2f}
[PRICE_VS_SMA20_PCT] = {technical.get('price_vs_sma20_pct', 0):.2f}%
[PRICE_VS_SMA50_PCT] = {technical.get('price_vs_sma50_pct', 0):.2f}%
[MOMENTUM_5D_PCT] = {technical.get('momentum_5d_pct', 0):.2f}%
[MOMENTUM_10D_PCT] = {technical.get('momentum_10d_pct', 0):.2f}%
[VOLUME_CURRENT] = {technical.get('volume_current', 0):,}
[VOLUME_AVG_20D] = {technical.get('volume_avg_20d', 0):,}
[VOLUME_RATIO] = {technical.get('volume_ratio', 0):.2f}x

### EXTENDED INDICATORS

[WEEK_52_HIGH] = ₹{extended.get('week_52_high', 0):.2f}
[WEEK_52_LOW] = ₹{extended.get('week_52_low', 0):.2f}
[ATR_14] = ₹{extended.get('atr_14', 0):.2f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ DATA OUTSIDE THIS SECTION DOES NOT EXIST FOR YOU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### YOUR TASK:

Analyze this news using ONLY the labeled fields above.

Return JSON with:
{{
    "score": 0-100,
    "sentiment": "bullish|bearish|neutral",
    "catalysts": [...],
    "risks": [...],
    "certainty": 0-100,
    "recommendation": "BUY|SELL|HOLD",
    "reasoning": "2-3 sentences using SPECIFIC field references like [PRICE_CURRENT], [RSI_14]",
    "expected_move_pct": number
}}

EXAMPLE OF GOOD REASONING:
"[NEWS_HEADLINE] indicates earnings decline. [PRICE_CURRENT] is ₹1587.20 with [RSI_14] at 44.9 showing neutral momentum. [PRICE_VS_SMA20_PCT] at -0.31% suggests short-term weakness."

EXAMPLE OF BAD REASONING (DO NOT DO THIS):
"Stock is undervalued based on historical trends. Company has strong fundamentals."
(These use training data, not provided data!)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    return prompt


# Quick test
if __name__ == '__main__':
    # Test validation
    validator = AIResponseValidator()

    test_response = {
        'score': 65,
        'sentiment': 'bullish',
        'reasoning': 'Stock looks good based on historical performance'  # BAD - uses training data
    }

    test_news = {'headline': 'Test', 'full_text': 'Test news', 'news_type': 'general'}
    test_data = {'price': {'current': 100}, 'technical': {}}

    result = validator.validate(test_response, test_news, test_data)
    print("Validation result:", result)
    print(f"Passed: {result['passed']}")
    print(f"Violations: {result['violations_count']}")
