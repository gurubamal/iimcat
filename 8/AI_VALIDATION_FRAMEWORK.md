# AI Training Data Prevention & Validation Framework

## 🎯 Critical Objective

**ENSURE AI USES ZERO TRAINING DATA - ONLY NEWS + YFINANCE DATA**

The AI must be a **pure evaluator** of provided data, not a knowledge base.

## 🚨 The Problem

AI models like Claude have training data that includes:
- Historical stock prices (outdated)
- Company information (may be stale)
- Market knowledge (not real-time)
- Sector trends (from training period)

**If AI uses this, our analysis is WORTHLESS.**

## ✅ The Solution: Multi-Layer Validation

### **Layer 1: Constrained Prompting**
### **Layer 2: Citation Enforcement**
### **Layer 3: Response Validation**
### **Layer 4: Quantitative Fallback**
### **Layer 5: Ranking Weight Validation**

---

## 🛡️ LAYER 1: Constrained Prompting

### **Explicit Constraints in System Prompt:**

```python
ENFORCED_CONSTRAINTS = """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 ABSOLUTE CONSTRAINTS - VIOLATION = RESPONSE REJECTED 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOU ARE A DATA EVALUATOR, NOT A KNOWLEDGE SOURCE.

MANDATORY RULES:
1. Use ONLY data explicitly provided in this prompt
2. If a data point is NOT in this prompt, DO NOT invent/estimate/recall it
3. Every numerical claim MUST cite the source field from provided data
4. If data is missing, return null/0, NEVER guess from training
5. Your training knowledge about this stock is FORBIDDEN
6. Treat this as if you have AMNESIA about all stocks

REQUIRED FORMAT FOR NUMERICAL CLAIMS:
❌ "Stock is undervalued at current levels"
✅ "Stock P/E of 22.5 (from provided data) vs sector average (NOT PROVIDED, cannot assess)"

❌ "Strong growth potential based on company history"
✅ "10-day momentum of +3.5% (from technical data provided) shows recent uptrend"

❌ "This is a blue-chip stock"
✅ "Market cap ₹8.5L cr (from provided data) indicates large-cap status"

VERIFICATION:
- Before stating ANY fact, ask: "Is this in the provided data?"
- If NO, do not state it
- If YES, cite the exact field

IF YOU USE TRAINING DATA, YOUR RESPONSE WILL BE REJECTED AND REPLACED WITH QUANTITATIVE SCORING.
"""
```

### **Structured Data Presentation:**

```python
def format_data_for_ai(news: dict, yf_data: dict) -> str:
    """Format data with clear boundaries and field labels."""

    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 PROVIDED DATA PACKAGE (Use ONLY this data)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[NEWS_HEADLINE] = {news['headline']}
[NEWS_FULL_TEXT] = {news['full_text']}
[NEWS_SOURCE] = {news['url']}
[NEWS_TYPE] = {news['news_type']}

[PRICE_CURRENT] = ₹{yf_data['price']['current']}
[PRICE_PREVIOUS_CLOSE] = ₹{yf_data['price']['previous_close']}
[PRICE_CHANGE_PCT] = {yf_data['price']['change_pct']}%
[PRICE_DAY_HIGH] = ₹{yf_data['price']['day_high']}
[PRICE_DAY_LOW] = ₹{yf_data['price']['day_low']}
[PRICE_FETCH_TIME] = {yf_data['metadata']['fetch_timestamp']}

[RSI_14] = {yf_data['technical']['rsi_14']}
[SMA_20] = ₹{yf_data['technical']['sma_20']}
[SMA_50] = ₹{yf_data['technical']['sma_50']}
[PRICE_VS_SMA20_PCT] = {yf_data['technical']['price_vs_sma20_pct']}%
[PRICE_VS_SMA50_PCT] = {yf_data['technical']['price_vs_sma50_pct']}%
[VOLUME_CURRENT] = {yf_data['technical']['volume_current']}
[VOLUME_AVG_20D] = {yf_data['technical']['volume_avg_20d']}
[VOLUME_RATIO] = {yf_data['technical']['volume_ratio']}
[MOMENTUM_5D_PCT] = {yf_data['technical']['momentum_5d_pct']}%
[MOMENTUM_10D_PCT] = {yf_data['technical']['momentum_10d_pct']}%

[MARKET_CAP] = ₹{yf_data['market_context']['market_cap_formatted']}
[WEEK_52_HIGH] = ₹{yf_data['extended_technical']['week_52_high']}
[WEEK_52_LOW] = ₹{yf_data['extended_technical']['week_52_low']}
[ATR_14] = ₹{yf_data['extended_technical']['atr_14']}

{conditional_data}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️ DATA OUTSIDE THIS SECTION DOES NOT EXIST FOR YOU
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR TASK:
Evaluate this news using ONLY the labeled fields above.
In your reasoning, reference field names: "[PRICE_CURRENT]", "[RSI_14]", etc.
"""
```

---

## 🛡️ LAYER 2: Citation Enforcement

### **Required Response Format:**

```python
REQUIRED_RESPONSE_SCHEMA = {
    "score": 0-100,
    "sentiment": "bullish|bearish|neutral",
    "catalysts": [...],
    "risks": [...],
    "certainty": 0-100,
    "recommendation": "BUY|SELL|HOLD",

    # NEW: MANDATORY CITATIONS
    "reasoning_with_citations": {
        "summary": "2-3 sentences",
        "data_points_used": [
            {
                "field": "[PRICE_CURRENT]",
                "value": "1587.20",
                "usage": "Used for entry zone calculation"
            },
            {
                "field": "[RSI_14]",
                "value": "44.9",
                "usage": "RSI below 50 indicates weakening momentum"
            },
            {
                "field": "[NEWS_HEADLINE]",
                "value": "Q2 PAT declines 13% YoY",
                "usage": "Primary negative catalyst"
            }
        ]
    },

    # NEW: VALIDATION METADATA
    "validation": {
        "used_training_data": false,  # AI must self-declare
        "missing_data_noted": ["sector_pe", "analyst_consensus"],  # What AI wanted but wasn't provided
        "all_numbers_cited": true,  # AI confirms all numbers from provided data
        "confidence_in_constraints": 100  # AI's confidence it followed rules
    }
}
```

### **Post-Processing Citation Validation:**

```python
def validate_ai_citations(ai_response: dict, provided_data: dict) -> dict:
    """Verify AI actually used provided data, not training data."""

    validation = {
        'passed': True,
        'violations': [],
        'score_adjustment': 0
    }

    # Check 1: All cited values must match provided data
    for citation in ai_response.get('reasoning_with_citations', {}).get('data_points_used', []):
        field = citation['field']
        claimed_value = citation['value']

        # Extract actual value from provided_data
        actual_value = extract_field_value(provided_data, field)

        if actual_value is None:
            validation['violations'].append(f"Field {field} not in provided data")
            validation['passed'] = False
        elif str(actual_value) != str(claimed_value):
            validation['violations'].append(
                f"Field {field}: AI claimed {claimed_value}, actual was {actual_value}"
            )
            validation['passed'] = False

    # Check 2: Detect uncited numbers (possible training data use)
    reasoning_text = ai_response.get('reasoning', '')
    uncited_numbers = find_uncited_numbers(reasoning_text, ai_response)

    if uncited_numbers:
        validation['violations'].append(f"Uncited numbers found: {uncited_numbers}")
        validation['passed'] = False
        validation['score_adjustment'] = -20  # Penalize heavily

    # Check 3: Detect external knowledge phrases
    forbidden_phrases = [
        "historically",
        "typically",
        "usually",
        "known for",
        "is a blue-chip",
        "is a leader in",
        "has a strong track record",
        "compared to industry average",  # Unless industry avg provided
        "analyst consensus",  # Unless provided
        "fair value"  # Unless calculated from provided data
    ]

    for phrase in forbidden_phrases:
        if phrase.lower() in reasoning_text.lower():
            # Check if the data was actually provided
            if not is_data_provided(phrase, provided_data):
                validation['violations'].append(f"Forbidden phrase (training data): '{phrase}'")
                validation['passed'] = False
                validation['score_adjustment'] -= 10

    return validation
```

---

## 🛡️ LAYER 3: Quantitative Fallback Scoring

### **Pure Data-Driven Score (No AI Needed):**

```python
def quantitative_score(news: dict, yf_data: dict) -> dict:
    """
    Calculate score using ONLY provided data, no AI interpretation.
    This is the fallback if AI violates constraints.
    """

    score = 50  # Neutral baseline

    # NEWS COMPONENT (40% weight)
    news_score = 0

    # Earnings impact
    if news['news_type'] == 'earnings':
        # Extract numbers from headline/text
        earnings_growth = extract_yoy_growth(news['full_text'])
        if earnings_growth:
            if earnings_growth > 20:
                news_score += 20
            elif earnings_growth > 10:
                news_score += 15
            elif earnings_growth > 0:
                news_score += 10
            elif earnings_growth > -10:
                news_score += 5
            else:
                news_score += 0  # Negative growth

    # Dividend impact
    elif news['news_type'] == 'dividend':
        dividend_yield = extract_dividend_yield(news['full_text'])
        if dividend_yield:
            if dividend_yield > 3:
                news_score += 15
            elif dividend_yield > 2:
                news_score += 10
            else:
                news_score += 5

    # Deal/M&A impact
    elif news['news_type'] == 'ma':
        deal_size = extract_deal_size(news['full_text'])
        market_cap = yf_data['market_context']['market_cap']
        if deal_size and market_cap:
            deal_impact_pct = (deal_size / market_cap) * 100
            if deal_impact_pct > 10:
                news_score += 20
            elif deal_impact_pct > 5:
                news_score += 15
            else:
                news_score += 10

    score += news_score * 0.4

    # TECHNICAL COMPONENT (40% weight)
    tech_score = 0

    # RSI scoring
    rsi = yf_data['technical'].get('rsi_14')
    if rsi:
        if 40 <= rsi <= 60:
            tech_score += 15  # Neutral/healthy
        elif rsi > 70:
            tech_score += 5  # Overbought
        elif rsi < 30:
            tech_score += 10  # Oversold but risky
        else:
            tech_score += 12

    # Trend scoring (Price vs MA)
    price_vs_sma20 = yf_data['technical'].get('price_vs_sma20_pct')
    if price_vs_sma20:
        if price_vs_sma20 > 5:
            tech_score += 10
        elif price_vs_sma20 > 0:
            tech_score += 15
        elif price_vs_sma20 > -5:
            tech_score += 10
        else:
            tech_score += 5

    # Momentum scoring
    momentum_10d = yf_data['technical'].get('momentum_10d_pct')
    if momentum_10d:
        if momentum_10d > 10:
            tech_score += 15
        elif momentum_10d > 5:
            tech_score += 12
        elif momentum_10d > 0:
            tech_score += 10
        else:
            tech_score += 5

    score += tech_score * 0.4

    # VOLUME COMPONENT (20% weight)
    volume_score = 0
    volume_ratio = yf_data['technical'].get('volume_ratio')
    if volume_ratio:
        if volume_ratio > 2:
            volume_score += 20  # High volume
        elif volume_ratio > 1.5:
            volume_score += 15
        elif volume_ratio > 1:
            volume_score += 10
        else:
            volume_score += 5

    score += volume_score * 0.2

    # Calculate certainty based on data completeness
    certainty = calculate_data_completeness(yf_data) * 100

    return {
        'score': min(100, max(0, score)),
        'sentiment': 'bullish' if score > 60 else ('bearish' if score < 40 else 'neutral'),
        'certainty': certainty,
        'method': 'quantitative_fallback',
        'reasoning': f"Pure quantitative: news={news_score:.0f}, tech={tech_score:.0f}, vol={volume_score:.0f}"
    }
```

---

## 🛡️ LAYER 4: Pre-Planned Validation Checks

### **Mandatory Checks Before Accepting AI Response:**

```python
class AIResponseValidator:
    """Validate AI response meets all constraints."""

    MANDATORY_CHECKS = [
        'check_no_training_data',
        'check_all_numbers_cited',
        'check_data_consistency',
        'check_reasoning_grounded',
        'check_score_reasonable',
        'check_sentiment_matches_data'
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

        # CHECK 3: Data Consistency
        results['data_consistency'] = self.check_data_consistency(
            ai_response, yf_data
        )

        # CHECK 4: Reasoning Grounded
        results['reasoning_grounded'] = self.check_reasoning_grounded(
            ai_response, news, yf_data
        )

        # CHECK 5: Score Reasonable
        results['score_reasonable'] = self.check_score_reasonable(
            ai_response, news, yf_data
        )

        # CHECK 6: Sentiment Matches Data
        results['sentiment_matches'] = self.check_sentiment_matches_data(
            ai_response, news, yf_data
        )

        # Overall pass/fail
        all_passed = all(r['passed'] for r in results.values())

        return {
            'passed': all_passed,
            'checks': results,
            'action': 'accept' if all_passed else 'use_quantitative_fallback'
        }

    def check_no_training_data(self, ai_response, news, yf_data):
        """Detect if AI used training data."""

        violations = []
        reasoning = ai_response.get('reasoning', '')

        # Pattern 1: References to external knowledge
        external_refs = [
            r"historically",
            r"typically trades at",
            r"compared to peers",
            r"industry average",
            r"analyst[s]? (?:expect|estimate|forecast)",
            r"fair value",
            r"intrinsic value",
            r"is known for",
            r"has a track record"
        ]

        for pattern in external_refs:
            if re.search(pattern, reasoning, re.IGNORECASE):
                # Check if this data was actually provided
                if not self._is_data_provided(pattern, yf_data):
                    violations.append(f"External reference: {pattern}")

        # Pattern 2: Specific numerical claims not in data
        numbers_in_reasoning = re.findall(r'[\d,]+\.?\d*', reasoning)
        for num in numbers_in_reasoning:
            if not self._number_in_provided_data(num, yf_data):
                violations.append(f"Uncited number: {num}")

        return {
            'passed': len(violations) == 0,
            'violations': violations
        }

    def check_score_reasonable(self, ai_response, news, yf_data):
        """Verify score aligns with data (not arbitrary)."""

        ai_score = ai_response['score']

        # Calculate what score SHOULD be from pure data
        expected = quantitative_score(news, yf_data)
        expected_score = expected['score']

        # Allow 15-point deviation
        deviation = abs(ai_score - expected_score)

        if deviation > 15:
            return {
                'passed': False,
                'deviation': deviation,
                'ai_score': ai_score,
                'expected_score': expected_score,
                'reason': 'Score deviates too much from data-driven score'
            }

        return {'passed': True}

    def check_sentiment_matches_data(self, ai_response, news, yf_data):
        """Verify sentiment matches actual data."""

        ai_sentiment = ai_response['sentiment']

        # Calculate expected sentiment from data
        news_sentiment = classify_news_sentiment(news)
        tech_sentiment = classify_technical_sentiment(yf_data)

        # Combine
        if news_sentiment == 'bearish' or tech_sentiment == 'bearish':
            expected = 'bearish'
        elif news_sentiment == 'bullish' and tech_sentiment == 'bullish':
            expected = 'bullish'
        else:
            expected = 'neutral'

        if ai_sentiment != expected:
            return {
                'passed': False,
                'ai_sentiment': ai_sentiment,
                'expected_sentiment': expected,
                'reason': f'Sentiment mismatch: AI said {ai_sentiment}, data suggests {expected}'
            }

        return {'passed': True}
```

---

## 🛡️ LAYER 5: Ranking Weight Validation

### **Ensure Optimal Ranking Across All Stocks:**

```python
class RankingValidator:
    """Validate that ranking weights are optimal and consistent."""

    def validate_rankings(self, all_analyses: list) -> dict:
        """Check if rankings make sense across all stocks."""

        issues = []

        # CHECK 1: Scores should correlate with data quality
        for analysis in all_analyses:
            data_quality = analysis['metadata']['data_quality']
            certainty = analysis['certainty']

            if data_quality == 'minimal' and certainty > 60:
                issues.append(f"{analysis['ticker']}: High certainty ({certainty}%) with minimal data")

        # CHECK 2: Similar news should have similar scores (±10)
        earnings_news = [a for a in all_analyses if a['news_type'] == 'earnings']

        for i, a1 in enumerate(earnings_news):
            for a2 in earnings_news[i+1:]:
                # If similar earnings growth, scores should be similar
                growth1 = extract_yoy_growth(a1['news']['full_text'])
                growth2 = extract_yoy_growth(a2['news']['full_text'])

                if growth1 and growth2 and abs(growth1 - growth2) < 5:
                    # Earnings growth similar, scores should be too
                    if abs(a1['score'] - a2['score']) > 15:
                        issues.append(
                            f"Inconsistent scoring: {a1['ticker']} ({growth1}% growth) = {a1['score']}, "
                            f"{a2['ticker']} ({growth2}% growth) = {a2['score']}"
                        )

        # CHECK 3: Extreme scores should have extreme data
        for analysis in all_analyses:
            if analysis['score'] > 85:
                # High score should have strong justification
                if not self._has_strong_positive_signals(analysis):
                    issues.append(f"{analysis['ticker']}: Score {analysis['score']} too high for data")

            if analysis['score'] < 25:
                # Low score should have clear negatives
                if not self._has_strong_negative_signals(analysis):
                    issues.append(f"{analysis['ticker']}: Score {analysis['score']} too low for data")

        # CHECK 4: Relative rankings should make sense
        sorted_by_score = sorted(all_analyses, key=lambda x: x['score'], reverse=True)

        for i in range(len(sorted_by_score) - 1):
            higher = sorted_by_score[i]
            lower = sorted_by_score[i + 1]

            # Verify higher-ranked actually has better data
            if not self._compare_analyses(higher, lower):
                issues.append(
                    f"Ranking issue: {higher['ticker']} (rank {i+1}) may not deserve higher rank than "
                    f"{lower['ticker']} (rank {i+2})"
                )

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'total_stocks': len(all_analyses),
            'issues_found': len(issues)
        }

    def _has_strong_positive_signals(self, analysis: dict) -> bool:
        """Check if data supports high score."""

        strong_signals = 0

        # Positive earnings
        if analysis['news_type'] == 'earnings':
            growth = extract_yoy_growth(analysis['news']['full_text'])
            if growth and growth > 20:
                strong_signals += 1

        # Strong technicals
        if analysis['yf_data']['technical'].get('momentum_10d_pct', 0) > 10:
            strong_signals += 1

        # Good volume
        if analysis['yf_data']['technical'].get('volume_ratio', 0) > 1.5:
            strong_signals += 1

        # Need at least 2 strong signals for score > 85
        return strong_signals >= 2

    def _compare_analyses(self, higher: dict, lower: dict) -> bool:
        """Verify higher-ranked deserves higher rank."""

        # Calculate objective scores
        higher_obj = quantitative_score(higher['news'], higher['yf_data'])
        lower_obj = quantitative_score(lower['news'], lower['yf_data'])

        # Higher should have better objective score
        return higher_obj['score'] >= lower_obj['score'] - 5  # Allow 5-point tolerance
```

---

## 🎯 Complete Validation Flow

```python
def analyze_with_validation(ticker: str, news: dict, yf_data: dict) -> dict:
    """
    Complete analysis flow with multi-layer validation.
    Falls back to quantitative if AI violates constraints.
    """

    # STEP 1: Get AI response
    ai_response = call_ai_with_constrained_prompt(news, yf_data)

    # STEP 2: Validate AI response
    validator = AIResponseValidator()
    validation = validator.validate(ai_response, news, yf_data)

    if validation['passed']:
        # AI response is valid
        result = ai_response
        result['validation_status'] = 'ai_validated'
        result['validation_details'] = validation
    else:
        # AI violated constraints - use quantitative fallback
        print(f"⚠️ AI validation failed for {ticker}: {validation['checks']}")
        result = quantitative_score(news, yf_data)
        result['validation_status'] = 'quantitative_fallback'
        result['ai_violations'] = validation['checks']
        result['original_ai_response'] = ai_response  # For debugging

    # STEP 3: Add metadata
    result['ticker'] = ticker
    result['news'] = news
    result['yf_data'] = yf_data
    result['timestamp'] = datetime.now().isoformat()

    return result


def rank_all_stocks(all_analyses: list) -> list:
    """
    Rank stocks with validation.
    """

    # STEP 1: Sort by score
    ranked = sorted(all_analyses, key=lambda x: x['score'], reverse=True)

    # STEP 2: Validate rankings
    ranking_validator = RankingValidator()
    ranking_validation = ranking_validator.validate_rankings(ranked)

    if not ranking_validation['valid']:
        print("⚠️ Ranking validation issues found:")
        for issue in ranking_validation['issues']:
            print(f"   - {issue}")

        # Option: Re-rank using pure quantitative
        # ranked = sorted(all_analyses, key=lambda x: quantitative_score(x['news'], x['yf_data'])['score'], reverse=True)

    # STEP 3: Add rank metadata
    for i, analysis in enumerate(ranked, 1):
        analysis['rank'] = i
        analysis['ranking_validation'] = ranking_validation

    return ranked
```

---

## 📊 Validation Report Example

```python
{
    "ticker": "CDSL",
    "validation_status": "ai_validated",  # or "quantitative_fallback"
    "score": 72,
    "sentiment": "bullish",

    "validation_details": {
        "passed": true,
        "checks": {
            "no_training_data": {
                "passed": true,
                "violations": []
            },
            "all_numbers_cited": {
                "passed": true,
                "uncited_numbers": []
            },
            "score_reasonable": {
                "passed": true,
                "deviation": 8,
                "ai_score": 72,
                "expected_score": 64
            },
            "sentiment_matches": {
                "passed": true,
                "ai_sentiment": "bullish",
                "expected_sentiment": "bullish"
            }
        }
    },

    "data_used": {
        "[PRICE_CURRENT]": "Used",
        "[RSI_14]": "Used",
        "[NEWS_HEADLINE]": "Used",
        "[MOMENTUM_10D_PCT]": "Used"
    },

    "training_data_used": false,  # CRITICAL FLAG
    "pure_quantitative_score": 64,  # For comparison
    "ai_enhancement": +8  # AI added value vs pure quantitative
}
```

---

## ✅ Implementation Checklist

- [ ] Create `ai_validation_framework.py`
- [ ] Implement `AIResponseValidator` class
- [ ] Implement `RankingValidator` class
- [ ] Create constrained prompt templates
- [ ] Implement citation enforcement
- [ ] Implement quantitative fallback scoring
- [ ] Add validation reporting
- [ ] Test with known cases
- [ ] Document all checks

---

## 🎯 Success Criteria

**AI Response is ONLY accepted if:**

1. ✅ All numbers cited from provided data
2. ✅ No forbidden phrases (training data indicators)
3. ✅ Score within 15 points of quantitative baseline
4. ✅ Sentiment matches data
5. ✅ Reasoning references specific data fields
6. ✅ No uncited numerical claims
7. ✅ Rankings consistent across similar stocks

**Otherwise: Use quantitative fallback (no AI needed)**

This ensures **zero dependence on AI training data** while still leveraging AI's analysis capabilities when it follows the rules!
