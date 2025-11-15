# EXIT INTELLIGENCE ANALYZER - Comprehensive Documentation

## 🚨 Overview

The Exit Intelligence Analyzer is a comprehensive, AI-powered system for assessing whether to sell/exit stock positions. Unlike `./run_without_api.sh` which focuses on buy opportunities, this system evaluates **sell/exit decisions** using multiple factors.

## ✅ Key Features

### Multi-Factor Assessment (Works WITHOUT News!)

The system assesses stocks comprehensively, **irrespective of whether news is available**:

1. **Technical Analysis (35% weight)**
   - Support/resistance break detection
   - Bearish chart patterns (head & shoulders, double top)
   - Moving average crosses (death cross detection)
   - RSI conditions (oversold/overbought)
   - Volume deterioration analysis
   - Momentum indicators (10-day returns)
   - 52-week low proximity

2. **Fundamental Analysis (30% weight)**
   - Recent earnings performance
   - Debt level concerns
   - Margin compression
   - Cash flow issues
   - Valuation overextension

3. **News Sentiment (25% weight - if available)**
   - Regulatory issues
   - Legal problems
   - Analyst downgrades
   - Management changes
   - Sector headwinds

4. **Volume & Momentum (10% weight)**
   - Trading volume trends
   - Price momentum
   - Liquidity concerns

### AI-Powered Intelligence

- Uses same AI bridges as `./run_without_api.sh` (Claude, Codex, Gemini)
- Comprehensive reasoning and decision making
- Considers opportunity cost (better uses for capital)
- Provides clear, actionable recommendations

## 📋 Files Created

### 1. `exit.check.txt`
Template file where you list tickers to assess (one per line):
```
CANBK
HYUNDAI
IOC
MARUTI
ACC
RELIANCE
```

### 2. `run_exit_assessment.sh`
Main entry point - simple command-line interface similar to `run_without_api.sh`:
```bash
./run_exit_assessment.sh <provider> [tickers_file] [hours_back]
```

### 3. `exit_intelligence_analyzer.py`
Core Python module that performs comprehensive exit assessment.

## 🚀 Quick Start

### Basic Usage (Codex - Fast & Free)
```bash
./run_exit_assessment.sh codex exit.check.txt 72
```

### Best Accuracy (Claude)
```bash
./run_exit_assessment.sh claude exit.check.txt 72
```

### Alternative (Gemini)
```bash
./run_exit_assessment.sh gemini exit.check.txt 72
```

## 📊 Command Line Options

### Providers
- **`codex`** - Fast heuristic + AI (FREE, instant, ~60% accuracy)
- **`claude`** - Claude CLI (requires subscription, ~95% accuracy, best for critical decisions)
- **`gemini`** - Gemini agent (FREE, ~80% accuracy)

### Parameters
1. **Provider**: AI provider to use (default: `codex`)
2. **Tickers File**: File with tickers to assess (default: `exit.check.txt`)
3. **Hours Back**: News window in hours (default: `72`)

## 📁 Output Files

The system generates three output files with timestamps:

### 1. `exit_assessment_immediate_YYYYMMDD_HHMMSS.txt`
**Stocks requiring IMMEDIATE EXIT**

```
# IMMEDIATE EXIT RECOMMENDATIONS
# Generated: 2025-11-01 18:30:00
# Total stocks requiring immediate exit: 2

RETAILSTOCK
WEAKCOMPANY
```

These stocks have:
- Exit score > 70/100
- Critical technical breakdown OR
- Severe fundamental issues OR
- Strong negative sentiment

**Action**: Consider exiting these positions immediately.

### 2. `exit_assessment_hold_YYYYMMDD_HHMMSS.txt`
**Stocks safe to HOLD or MONITOR**

```
# HOLD / MONITOR RECOMMENDATIONS
# Generated: 2025-11-01 18:30:00
# Stocks safe to hold: 5
# Stocks to monitor: 2

# HOLD:
RELIANCE
TCS
INFY
HDFCBANK
ICICIBANK

# MONITOR (watch closely):
MARUTI
TATASTEEL
```

- **HOLD**: Exit score < 50, no significant concerns
- **MONITOR**: Exit score 50-70, some warning signs but not critical

**Action**:
- HOLD: Keep positions, no urgent action needed
- MONITOR: Watch closely, consider setting stop losses

### 3. `exit_assessment_detailed_YYYYMMDD_HHMMSS.csv`
**Comprehensive analysis report**

Columns:
- `ticker`: Stock symbol
- `recommendation`: IMMEDIATE_EXIT / MONITOR / HOLD
- `exit_score`: Overall exit urgency (0-100)
- `confidence`: Confidence in recommendation (0-100%)
- `technical_score`: Technical breakdown score
- `technical_severity`: CRITICAL / HIGH / MEDIUM / LOW / NONE
- `fundamental_risk`: Fundamental risk score
- `sentiment_risk`: Negative sentiment score
- `urgency_score`: AI-assessed urgency
- `primary_reasons`: Key exit reasons
- `summary`: AI recommendation summary

## 🎯 Scoring System

### Exit Score (0-100)
- **0-50**: HOLD - No urgent exit signals
- **50-70**: MONITOR - Warning signs, watch closely
- **70-100**: IMMEDIATE EXIT - Critical issues, consider exiting

### Component Scores

**Technical Breakdown Score (0-100)**
- Assesses chart patterns, support breaks, momentum
- Based on: MA crosses, RSI, volume, 52-week low proximity

**Fundamental Risk Score (0-100)**
- Evaluates business health and financial stability
- Based on: Earnings, debt, margins, cash flow

**Negative Sentiment Score (0-100)**
- Measures news and market sentiment
- Based on: News headlines, analyst ratings, market perception

### Confidence Level (0-100%)
- **80-100%**: High confidence - act on recommendation
- **60-80%**: Medium-high confidence - likely accurate
- **40-60%**: Medium confidence - review carefully
- **0-40%**: Low confidence - seek additional analysis

## 💡 Usage Scenarios

### Scenario 1: Portfolio Review (Weekly/Monthly)
```bash
# Add all your holdings to exit.check.txt
echo "RELIANCE
TCS
INFY
HDFCBANK
TATASTEEL" > exit.check.txt

# Run comprehensive assessment with Claude (best accuracy)
./run_exit_assessment.sh claude exit.check.txt 168  # 7 days
```

### Scenario 2: Quick Check After Market Hours
```bash
# Use codex for fast assessment
./run_exit_assessment.sh codex exit.check.txt 24
```

### Scenario 3: Critical Decision (Before Earnings)
```bash
# Use Claude for highest accuracy
./run_exit_assessment.sh claude single_stock.txt 48
```

### Scenario 4: Monitor Watchlist
```bash
# Create watchlist of concerning stocks
echo "STOCK1
STOCK2
STOCK3" > watchlist.txt

# Monitor with Gemini (good balance)
./run_exit_assessment.sh gemini watchlist.txt 72
```

## 🔍 Understanding Assessment Factors

### Technical Signals (Examples)

**Bearish Signals Detected:**
- Price 5%+ below 20-day SMA
- Death cross (20-day SMA crosses below 50-day SMA)
- RSI < 30 (oversold, potential further downside)
- Negative 10-day momentum
- Volume deterioration on down days
- Near 52-week low (< 5% above)

**Example Output:**
```
Technical Exit Score: 75/100 (HIGH)
Reasons:
  • Price 8.5% below 20-day SMA (breakdown)
  • Death cross: 20-day SMA below 50-day SMA (bearish)
  • Negative 10-day momentum: -12.3%
```

### AI Assessment Process

The AI considers:
1. **Technical context** - What do the charts say?
2. **Fundamental health** - Is the business deteriorating?
3. **News sentiment** - Any red flags in recent news?
4. **Risk/reward** - Is holding worth the risk?
5. **Opportunity cost** - Better uses for this capital?

**AI Output Example:**
```json
{
  "exit_recommendation": "IMMEDIATE_EXIT",
  "exit_urgency_score": 85,
  "exit_confidence": 80,
  "primary_exit_reasons": [
    "Severe technical breakdown with price below all major MAs",
    "Q2 earnings miss with margin compression",
    "Negative sector momentum in auto space"
  ],
  "recommendation_summary": "Strong sell. Multiple concerning factors including technical breakdown, weak fundamentals, and sector headwinds. Risk/reward no longer favorable."
}
```

## ⚠️ Important Notes

### 1. **Assessment is ALWAYS Performed**
Unlike news-based analysis, this system assesses stocks **even without recent news**. It relies on:
- Real-time technical data (price, volume, indicators)
- Historical fundamental data
- AI reasoning based on available data

### 2. **This is a Decision Support Tool**
- NOT financial advice
- Use your own judgment
- Consider your personal situation (tax implications, time horizon, goals)
- Consult with a financial advisor for major decisions

### 3. **Data Limitations**
- Technical analysis requires market data (uses yfinance)
- Some stocks may have limited data availability
- AI assessment quality depends on available information

### 4. **Best Practices**
- Run assessments regularly (weekly/monthly)
- Always review the detailed CSV report
- Don't panic-sell based solely on scores
- Consider setting stop losses for MONITOR stocks
- Use Claude for critical decisions

### 5. **When to Act**
- **IMMEDIATE_EXIT (70+)**: Review urgently, consider exit
- **MONITOR (50-70)**: Set alerts, watch closely, consider stop loss
- **HOLD (<50)**: Continue holding, no urgent action

## 🔧 Troubleshooting

### Issue: "No technical data available"
**Solution**:
- Check if ticker symbol is correct (NSE format)
- Some stocks may not have data on Yahoo Finance
- System will still perform AI assessment based on news/fundamentals

### Issue: "AI assessment failed"
**Solution**:
- Check AI provider is configured correctly
- For Claude: Ensure `claude` CLI is installed and authenticated
- For Codex: Should always work (uses heuristic fallback)
- Check internet connectivity

### Issue: "No data for ticker"
**Solution**:
- Verify ticker symbol is correct
- Try adding `.NS` suffix (e.g., `RELIANCE.NS`)
- Check if stock is actively traded

### Issue: Low confidence scores
**Solution**:
- Increase `--hours-back` to get more news context
- Use Claude instead of Codex for better reasoning
- Manually review the stock if critical

## 📈 Comparison with run_without_api.sh

| Feature | run_without_api.sh | run_exit_assessment.sh |
|---------|-------------------|----------------------|
| **Purpose** | Find BUY opportunities | Find SELL/EXIT decisions |
| **Focus** | Positive catalysts | Risk and deterioration |
| **News Dependency** | Requires news | Works WITHOUT news |
| **Technical Analysis** | Limited | Comprehensive |
| **Output** | Rankings, buy scores | Exit lists, hold lists |
| **Assessment Factors** | Mainly news-based | Multi-factor (tech+fundamental+news) |
| **Use Case** | Entry decisions | Exit decisions |

## 🎓 Example Workflow

### Daily Workflow
```bash
# 1. Morning: Quick check of portfolio
./run_exit_assessment.sh codex exit.check.txt 24

# 2. Review immediate_exit file
cat exit_assessment_immediate_*.txt

# 3. If stocks flagged, run detailed analysis with Claude
./run_exit_assessment.sh claude flagged_stocks.txt 72

# 4. Review detailed CSV and make decisions
```

### Weekly Portfolio Review
```bash
# 1. Update exit.check.txt with all holdings
# 2. Run comprehensive assessment
./run_exit_assessment.sh claude exit.check.txt 168

# 3. Review outputs:
#    - Immediate exit list → Consider selling
#    - Monitor list → Set stop losses
#    - Hold list → Continue holding

# 4. Document decisions and rationale
```

## 📞 Support

For issues or questions:
1. Check this README
2. Review error messages in stderr output
3. Try with different AI providers
4. Verify ticker symbols and data availability

## 🔄 Updates and Enhancements

Future enhancements may include:
- Integration with portfolio management systems
- Automated stop-loss recommendations
- Historical accuracy tracking
- Machine learning-based scoring
- Real-time alerts for critical signals

---

## Quick Reference Card

```bash
# BASIC USAGE
./run_exit_assessment.sh codex exit.check.txt 72

# BEST ACCURACY
./run_exit_assessment.sh claude exit.check.txt 72

# PARAMETERS
# $1: Provider (codex/claude/gemini)
# $2: Tickers file (default: exit.check.txt)
# $3: Hours back (default: 72)

# OUTPUT FILES
# exit_assessment_immediate_*.txt  → Stocks to exit
# exit_assessment_hold_*.txt       → Stocks to hold/monitor
# exit_assessment_detailed_*.csv   → Full analysis

# EXIT SCORE INTERPRETATION
# 70-100: IMMEDIATE EXIT (critical)
# 50-70:  MONITOR (warning signs)
# 0-50:   HOLD (no urgent concerns)
```

---

**Built with the same architecture as run_without_api.sh**
**Comprehensive • Intelligent • Actionable**
