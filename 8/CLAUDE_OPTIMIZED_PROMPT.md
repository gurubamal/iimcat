# CLAUDE-OPTIMIZED SWING TRADE ANALYSIS PROMPT

## Problem Identified
Claude AI is producing overly conservative scores compared to Codex:
- **Claude**: Scores 33-34/100, 30% certainty, "HOLD" recommendations
- **Codex**: Scores 76-82/100, 60-76% certainty, "BUY/STRONG BUY" recommendations

## Root Causes
1. **Overly strict interpretation** of news relevance
2. **Conservative scoring bias** - afraid to use higher scores
3. **Poor certainty calibration** - defaulting to 30% too often
4. **Missing indirect correlations** - not seeing sector/supply chain impacts
5. **Over-emphasis on fake rally detection** - rejecting valid news

## Optimized Prompt for Claude

```python
def _build_ai_prompt_claude_optimized(self, ticker: str, headline: str,
                                      full_text: str, url: str) -> str:
    """Build Claude-optimized AI prompt with better calibration"""

    prompt = f"""# SWING TRADE SETUP ANALYSIS - {ticker}

## CALIBRATION INSTRUCTIONS FOR CLAUDE AI

**IMPORTANT**: You have a tendency to be overly conservative. Follow these calibration rules:

### Scoring Calibration (CRITICAL)
- **70-85 range is NORMAL** for quality news with confirmed catalysts
- **50-69 range** is for weak/speculative news
- **30-49 range** is ONLY for irrelevant or negative news
- **DO NOT default to 30-40 scores** unless news is truly poor

### Certainty Calibration (CRITICAL)
- **60-80% certainty** is NORMAL for tier-1 English news sources
- **40-59% certainty** is for unconfirmed/speculation
- **30% certainty** should be RARE - only for completely vague news
- **Confirmed numbers/deals = minimum 65% certainty**

### Sentiment Calibration
- Positive earnings/deals/investments = **"bullish"** (not "neutral")
- Actual growth numbers = **"bullish"** (not "neutral")
- "Neutral" should be rare - only for truly mixed/unclear news

### Catalyst Detection
- **DO NOT say "None"** - always identify at least the news category
- Types: earnings, investment, expansion, contract, partnership, product_launch, regulatory, sector_momentum
- **Indirect news counts** - NVIDIA impacts all AI-exposed stocks

## Task
Analyze this news for **swing trading opportunity (5-15 day horizon)** using:
1. Fundamental catalyst analysis (news impact assessment)
2. Technical analysis (support/resistance, indicators, entry/exit levels)
3. Risk management (stop-loss, risk-reward ratio)
4. Real-time market data verification

## Stock Information
- **Ticker**: {ticker}
- **Headline**: {headline}
- **Full Text**: {full_text[:1000] if full_text else "N/A"}
- **URL**: {url}

## Analysis Framework

### 1. Fundamental Catalyst Analysis (30 points)
Identify:
- Catalyst type (earnings, M&A, investment, expansion, contract, sector_momentum, etc.)
- Deal value (₹ crores if mentioned)
- Specificity (confirmed vs speculation)
- Impact magnitude relative to market cap
- **Indirect correlations** (e.g., NVIDIA news → Indian AI stocks, oil prices → energy stocks)
- Fake rally risk (hype vs substance)

**IMPORTANT**: Consider supply chain, sector, and thematic impacts. Don't require DIRECT company mention.

### 2. Technical Analysis - REQUIRED (30 points)
**Use internet to fetch current technical data and provide:**
- **Current Price**: Latest trading price
- **Support Levels**: At least 2-3 key support levels below current price
- **Resistance Levels**: At least 2-3 key resistance levels above current price
- **RSI Reading**: Current RSI value and interpretation (overbought/oversold/neutral)
- **MACD Signals**: Current MACD status (bullish/bearish crossover, divergence)
- **Volume Trend**: Recent volume analysis (increasing/decreasing/average)
- **Price Action**: Recent trend (uptrend/downtrend/sideways)

### 3. Swing Trade Setup (25 points)
**Provide specific actionable levels:**
- **Entry Zone**: Optimal buy zone/price range for entry
- **Target 1**: Conservative exit target (first profit booking)
- **Target 2**: Aggressive exit target (if momentum continues)
- **Stop Loss**: Strict stop-loss level for risk management
- **Time Horizon**: 5-15 day expected holding period
- **Risk-Reward Ratio**: Calculate R:R ratio (e.g., 1:2, 1:3)

### 4. Market Context & Sentiment (15 points)
Assess:
- Sector momentum (industry trend context)
- Market breadth (Nifty/Sensex trend alignment)
- Certainty level (specific numbers, confirmed actions)
- Source credibility

## Output Format (JSON)
{{
    "score": 0-100,
    "sentiment": "bullish|bearish|neutral",
    "impact": "high|medium|low",
    "catalysts": ["type1", "type2"],
    "deal_value_cr": number or 0,
    "risks": ["risk1", "risk2"],
    "certainty": 0-100,
    "recommendation": "STRONG BUY|BUY|ACCUMULATE|HOLD|REDUCE|SELL",
    "reasoning": "detailed explanation",
    "expected_move_pct": number,
    "confidence": 0-100,

    "technical_analysis": {{
        "current_price": number,
        "support_levels": [level1, level2, level3],
        "resistance_levels": [level1, level2, level3],
        "rsi": number (0-100),
        "rsi_interpretation": "overbought|neutral|oversold",
        "macd_signal": "bullish|bearish|neutral",
        "volume_trend": "increasing|decreasing|average",
        "price_trend": "uptrend|downtrend|sideways"
    }},

    "swing_trade_setup": {{
        "entry_zone_low": number,
        "entry_zone_high": number,
        "target_1": number,
        "target_2": number,
        "stop_loss": number,
        "time_horizon_days": "5-15",
        "risk_reward_ratio": "1:X",
        "sector_momentum": "strong|moderate|weak"
    }}
}}

## Internet Research - CRITICAL
**You MUST use internet access to:**
1. Fetch current stock price for {ticker}
2. Look up recent technical indicators (RSI, MACD, support/resistance)
3. Check recent volume patterns
4. Verify sector/industry momentum
5. Cross-reference news source credibility
6. Validate company market cap and fundamentals
7. **Check for indirect correlations** (supply chain, sector themes, global trends)

## Scoring Guidelines with EXAMPLES

### 90-100: Exceptional (Strong Direct Catalyst + Bullish Technicals)
**Examples:**
- Company reports ₹2,000cr profit, +25% YoY → Score: 92, Certainty: 85%
- Signs $500M contract with confirmed deal terms → Score: 95, Certainty: 90%
- Board approves ₹1,000cr capex for new plant → Score: 88, Certainty: 80%

### 75-89: Strong (Solid Catalyst + Favorable Technicals)
**Examples:**
- Q1 profit ₹500cr, +12% YoY (tier-1 source) → Score: 82, Certainty: 75%
- Announces ₹300cr investment in new facility → Score: 78, Certainty: 70%
- NVIDIA $5T valuation + Company has AI exposure → Score: 76, Certainty: 65%
- Signs partnership with major client (no deal size) → Score: 75, Certainty: 60%

### 60-74: Moderate (Decent Catalyst + Acceptable Technicals)
**Examples:**
- "Plans to invest ₹200cr" (speculation) → Score: 68, Certainty: 50%
- Sector-wide positive news (indirect impact) → Score: 65, Certainty: 55%
- Product launch announcement (no revenue projection) → Score: 62, Certainty: 45%

### 45-59: Weak (Minor Catalyst or Unfavorable Technicals)
**Examples:**
- Generic "company exploring opportunities" → Score: 52, Certainty: 35%
- Weak rumor from low-tier source → Score: 48, Certainty: 30%
- News is old (>1 week) or already priced in → Score: 55, Certainty: 40%

### 0-44: Poor (No Catalyst or Bearish Technicals)
**Examples:**
- Completely irrelevant news to the ticker → Score: 35, Certainty: 20%
- Negative news (losses, scandals, downgrades) → Score: 25, Certainty: 70%
- Pure speculation with no substance → Score: 30, Certainty: 25%

## CALIBRATION CHECKLIST (Use this before finalizing)

Before you submit your analysis, verify:

1. ✅ **Score Check**: If news has confirmed numbers + tier-1 source → score should be 70+
2. ✅ **Certainty Check**: If news is from Hindu BusinessLine/ET/Mint → certainty should be 60+
3. ✅ **Sentiment Check**: If news mentions growth/profit/investment → sentiment should be "bullish"
4. ✅ **Catalyst Check**: Did I identify at least 1-2 catalyst types? (Never say "None")
5. ✅ **Indirect Impact**: Did I consider sector/supply chain/thematic correlations?
6. ✅ **Recommendation Check**: If score is 70+, recommendation should be "BUY" or "STRONG BUY"

## COMMON MISTAKES TO AVOID

❌ **DON'T**: Give 33/100 score to confirmed earnings news from tier-1 source
✅ **DO**: Give 75-85/100 score to confirmed earnings news from tier-1 source

❌ **DON'T**: Give 30% certainty to Hindu BusinessLine article with specific numbers
✅ **DO**: Give 70-80% certainty to Hindu BusinessLine article with specific numbers

❌ **DON'T**: Mark sentiment as "neutral" for profit growth news
✅ **DO**: Mark sentiment as "bullish" for profit growth news

❌ **DON'T**: Say catalysts = "None" for any real news
✅ **DO**: Always identify at least 1 catalyst type (even if indirect)

❌ **DON'T**: Give "HOLD" recommendation for 76/100 score
✅ **DO**: Give "BUY" or "STRONG BUY" for 75+ scores

## INDIRECT CORRELATION EXAMPLES

**NVIDIA news → Indian stocks:**
- Reliance (AI investments, Jio AI platform) → Score: 75+, Certainty: 65%
- TCS/Infosys (AI services, cloud) → Score: 72+, Certainty: 60%
- L&T (datacenter infra) → Score: 70+, Certainty: 55%

**Oil price surge → Energy stocks:**
- BPCL, ONGC, Reliance Energy → Score: 70+, Certainty: 70%

**Federal Reserve rate cut → Rate-sensitive stocks:**
- Banks, REITs, Auto finance → Score: 68+, Certainty: 65%

**IMPORTANT**:
- Provide specific numerical values for all technical levels
- Calculate precise entry/exit/stop-loss prices
- Include risk-reward ratio calculation
- Focus on 5-15 day swing trading horizon
- **Use the full scoring range (20-95), not just 30-40**
- **Be confident in your assessments - don't under-score quality news**

Analyze and respond with JSON only.
"""
    return prompt
```

## Implementation Steps

### Option 1: Update Existing Prompt (Recommended)

Edit `realtime_ai_news_analyzer.py` line 917-1028 and replace the existing prompt with the optimized version above.

### Option 2: Create Claude-Specific Mode

Add a flag to use the optimized prompt only for Claude:

```python
# In realtime_ai_news_analyzer.py, around line 914

def _build_ai_prompt(self, ticker: str, headline: str,
                    full_text: str, url: str) -> str:
    """Build AI prompt - use optimized version for Claude"""

    # Check if using Claude
    is_claude = self.ai_client.selected_provider in ['claude', 'anthropic']

    if is_claude:
        return self._build_ai_prompt_claude_optimized(ticker, headline, full_text, url)
    else:
        return self._build_ai_prompt_standard(ticker, headline, full_text, url)
```

### Option 3: Add System Message Enhancement

Update `claude_bridge.py` line 47 with better system message:

```python
# OLD (line 47):
system="You are an expert Indian equity analyst. Return valid JSON only."

# NEW (more calibrated):
system="""You are an expert Indian equity analyst specializing in swing trading.

CRITICAL CALIBRATION RULES:
1. Use the FULL scoring range (20-95) - don't default to 30-40 scores
2. Confirmed news from tier-1 sources = 70-85 scores (not 33)
3. Tier-1 English sources = 60-80% certainty (not 30%)
4. Growth/profit/investment news = "bullish" sentiment (not "neutral")
5. Always identify catalysts - never say "None"
6. Consider indirect sector/supply chain impacts
7. 75+ scores → "BUY" recommendations (not "HOLD")

Return valid JSON only with realistic, well-calibrated scores."""
```

## Testing the Fix

### 1. Run Comparison Test

```bash
# Test with the same news
export AI_LOG_ENABLED=true

# Claude with optimized prompt
./run_without_api.sh claude all.txt 18 10

# Check if scores improved
./ai_log_helper.sh view claude
# Look for:
# - Scores in 70-85 range (not 33)
# - Certainty in 60-80% range (not 30%)
# - "bullish" sentiment (not "neutral")
# - Catalysts identified (not "None")
```

### 2. Compare Before/After

Create a test script to validate:

```bash
#!/bin/bash
# test_claude_calibration.sh

echo "Testing Claude calibration fix..."

# Test case: BPCL earnings (should score 75+)
echo "Test 1: Confirmed earnings news"
# Expected: Score 75-85, Certainty 70-80%, Sentiment "bullish"

# Test case: NVIDIA news for Reliance (should score 70+)
echo "Test 2: Indirect sector news"
# Expected: Score 70-80, Certainty 60-70%, Catalysts ["sector_momentum", "investment"]

# Test case: Generic speculation (should score 45-55)
echo "Test 3: Weak speculation"
# Expected: Score 45-55, Certainty 30-40%
```

## Expected Improvements

### Before (Claude with old prompt):
```json
{
  "score": 33.6,
  "sentiment": "neutral",
  "certainty": 30,
  "catalysts": ["None"],
  "recommendation": "HOLD"
}
```

### After (Claude with optimized prompt):
```json
{
  "score": 76.8,
  "sentiment": "bullish",
  "certainty": 72,
  "catalysts": ["earnings", "investment"],
  "recommendation": "BUY"
}
```

## Why This Works

1. **Explicit Calibration**: Shows Claude exact score ranges with examples
2. **Permission to Score Higher**: Removes implicit conservative bias
3. **Examples-Based Learning**: Claude learns better with concrete examples
4. **Checklist Format**: Claude responds well to structured verification steps
5. **Common Mistakes Section**: Directly addresses observed failure modes
6. **Better System Message**: Sets expectations upfront in the system prompt

## Rollback Plan

If the optimized prompt makes Claude too aggressive:

1. Adjust the score ranges downward by 5-10 points
2. Increase the certainty thresholds slightly
3. Add more weight to fake rally detection
4. Keep the examples but soften the calibration language

---

**Result**: Claude should now produce scores comparable to Codex (70-85 range) while maintaining accuracy.
