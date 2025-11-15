# Enhanced Swing Trade Prompts - Now Active!

## What Changed

The AI prompts have been **upgraded** to include comprehensive swing trading analysis.

## Before vs After

### ❌ BEFORE (Generic Analysis)
```
Analyze this stock: RELIANCE - Reports Q1 profit of ₹5000 crores

Provide:
- Score
- Sentiment
- Impact
- Catalysts
- Risks
```

### ✅ AFTER (Swing Trading Analysis)
```
# SWING TRADE SETUP ANALYSIS - RELIANCE

## Task
Analyze this news for **swing trading opportunity (5-15 day horizon)** using:
1. Fundamental catalyst analysis (news impact assessment)
2. Technical analysis (support/resistance, indicators, entry/exit levels)
3. Risk management (stop-loss, risk-reward ratio)
4. Real-time market data verification

## Stock Information
- **Ticker**: RELIANCE
- **Headline**: Reports Q1 profit of ₹5000 crores
- **Full Text**: [truncated to 1000 chars]
- **URL**: https://...

## Analysis Framework

### 1. Fundamental Catalyst Analysis (30 points)
- Catalyst type, deal value, specificity
- Impact magnitude, fake rally risk

### 2. Technical Analysis - REQUIRED (30 points)
**Use internet to fetch current technical data and provide:**
- **Current Price**: Latest trading price
- **Support Levels**: At least 2-3 key support levels
- **Resistance Levels**: At least 2-3 key resistance levels
- **RSI Reading**: Current RSI value and interpretation
- **MACD Signals**: Current MACD status
- **Volume Trend**: Recent volume analysis
- **Price Action**: Recent trend

### 3. Swing Trade Setup (25 points)
**Provide specific actionable levels:**
- **Entry Zone**: Optimal buy zone/price range
- **Target 1**: Conservative exit target
- **Target 2**: Aggressive exit target
- **Stop Loss**: Strict stop-loss level
- **Time Horizon**: 5-15 day holding period
- **Risk-Reward Ratio**: Calculate R:R ratio

### 4. Market Context & Sentiment (15 points)
- Sector momentum
- Market breadth
- Certainty level
- Source credibility

## Output Format (JSON)
{
    "score": 0-100,
    "sentiment": "bullish|bearish|neutral",
    "impact": "high|medium|low",
    "catalysts": [...],
    "risks": [...],
    "certainty": 0-100,
    "recommendation": "STRONG BUY|BUY|ACCUMULATE|HOLD|REDUCE|SELL",
    "reasoning": "...",
    "expected_move_pct": number,
    "confidence": 0-100,

    "technical_analysis": {
        "current_price": number,
        "support_levels": [level1, level2, level3],
        "resistance_levels": [level1, level2, level3],
        "rsi": number (0-100),
        "rsi_interpretation": "overbought|neutral|oversold",
        "macd_signal": "bullish|bearish|neutral",
        "volume_trend": "increasing|decreasing|average",
        "price_trend": "uptrend|downtrend|sideways"
    },

    "swing_trade_setup": {
        "entry_zone_low": number,
        "entry_zone_high": number,
        "target_1": number,
        "target_2": number,
        "stop_loss": number,
        "time_horizon_days": "5-15",
        "risk_reward_ratio": "1:X",
        "sector_momentum": "strong|moderate|weak"
    }
}
```

## What You'll Now Get

When you run your analysis, the AI will be asked for:

### Fundamental Analysis
- ✅ Catalyst detection (earnings, M&A, contracts, etc.)
- ✅ Deal value in crores
- ✅ Impact magnitude
- ✅ Fake rally risk assessment

### Technical Analysis (NEW!)
- ✅ Current stock price
- ✅ Support levels (2-3 specific levels)
- ✅ Resistance levels (2-3 specific levels)
- ✅ RSI reading and interpretation
- ✅ MACD signals (bullish/bearish)
- ✅ Volume trend analysis
- ✅ Price action trend

### Swing Trade Setup (NEW!)
- ✅ Entry zone (buy range)
- ✅ Target 1 (conservative profit)
- ✅ Target 2 (aggressive profit)
- ✅ Stop loss (risk management)
- ✅ 5-15 day time horizon
- ✅ Risk-reward ratio
- ✅ Sector momentum context

## Verify with Logging

Now when you enable logging, you'll see these enhanced prompts:

```bash
# Enable logging
export AI_LOG_ENABLED=true

# Run your analysis
./run_without_api.sh claude all.txt 18 10

# View the logs
./ai_log_helper.sh view claude

# You'll see the full swing trade prompt!
```

## Example Log Output

**Prompt Section**:
```
# SWING TRADE SETUP ANALYSIS - RELIANCE

## Task
Analyze this news for **swing trading opportunity (5-15 day horizon)** using:
1. Fundamental catalyst analysis (news impact assessment)
2. Technical analysis (support/resistance, indicators, entry/exit levels)
3. Risk management (stop-loss, risk-reward ratio)
4. Real-time market data verification

## Stock Information
- **Ticker**: RELIANCE
- **Headline**: Reports Q1 profit of ₹18,000 crores, up 12% YoY
- **Full Text**: Reliance Industries reported...
- **URL**: https://economictimes.com/...

### 2. Technical Analysis - REQUIRED (30 points)
**Use internet to fetch current technical data and provide:**
- **Current Price**: Latest trading price
- **Support Levels**: At least 2-3 key support levels
- **Resistance Levels**: At least 2-3 key resistance levels
- **RSI Reading**: Current RSI value
- **MACD Signals**: Current MACD status
- **Volume Trend**: Recent volume analysis
...
```

**Response Section**:
```json
{
  "score": 85,
  "sentiment": "bullish",
  "technical_analysis": {
    "current_price": 1289.50,
    "support_levels": [1250, 1220, 1180],
    "resistance_levels": [1310, 1350, 1400],
    "rsi": 62,
    "rsi_interpretation": "neutral",
    "macd_signal": "bullish",
    "volume_trend": "increasing",
    "price_trend": "uptrend"
  },
  "swing_trade_setup": {
    "entry_zone_low": 1260,
    "entry_zone_high": 1280,
    "target_1": 1340,
    "target_2": 1390,
    "stop_loss": 1235,
    "time_horizon_days": "5-15",
    "risk_reward_ratio": "1:2.5",
    "sector_momentum": "strong"
  }
}
```

## Files Modified

| File | Change |
|------|--------|
| `realtime_ai_news_analyzer.py:795-910` | Enhanced `_build_ai_prompt()` with swing trade requirements |

## Testing the Changes

### 1. Quick Test with Logging

```bash
# Enable logging
export AI_LOG_ENABLED=true

# Run a test
./run_without_api.sh claude all.txt 18 10

# View the prompt that was sent
./ai_log_helper.sh view claude

# Check if it includes:
# - "SWING TRADE SETUP ANALYSIS"
# - "Technical Analysis - REQUIRED"
# - "support_levels", "resistance_levels"
# - "RSI Reading", "MACD Signals"
# - "Entry Zone", "Target 1", "Target 2", "Stop Loss"
```

### 2. Verify Response Structure

```bash
# View the JSON response
cat logs/ai_conversations/*claude*.json | jq '.response | fromjson | .technical_analysis'

# Should show:
# {
#   "current_price": ...,
#   "support_levels": [...],
#   "resistance_levels": [...],
#   "rsi": ...,
#   ...
# }
```

## What AI Providers Will Do

### Claude (with internet access)
- ✅ Will fetch current price from Yahoo Finance/Google Finance
- ✅ Will look up RSI/MACD from TradingView or similar
- ✅ Will calculate support/resistance based on recent price action
- ✅ Will provide specific entry/exit/stop-loss levels

### Codex/Heuristic (no internet)
- ⚠️ Will provide estimated values based on news content
- ⚠️ May use generic support/resistance patterns
- ⚠️ Risk-reward ratios will be approximate

### Recommendation
For best results with swing trading analysis, use:
1. **Claude API** (with `ANTHROPIC_API_KEY`) - Has internet access
2. **Claude CLI** (if you have Claude Pro subscription) - Has internet access

Avoid Codex/heuristic mode for technical analysis - they lack real-time data.

## Next Steps

1. **Enable logging**: `export AI_LOG_ENABLED=true`
2. **Run analysis**: `./run_without_api.sh claude all.txt 18 10`
3. **Review logs**: `./ai_log_helper.sh view claude`
4. **Verify prompts**: Check for swing trade setup content
5. **Review responses**: Check for technical_analysis and swing_trade_setup fields

## Important Notes

- The enhanced prompts are now **active in all analyses**
- Logging will capture the **full detailed prompts**
- AI responses will include **technical analysis** and **swing trade setups**
- Use **Claude API or CLI** for best results (internet access required)
- The heuristic mode will work but with limited technical accuracy

---

**Result**: Your AI analyses will now include comprehensive swing trading information including support/resistance, RSI/MACD, entry/exit targets, stop-loss, and risk-reward ratios!
