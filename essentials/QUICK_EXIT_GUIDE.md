# Quick Exit Assessment Guide

## 🎯 Purpose
Exit Intelligence Analyzer helps you decide **WHEN TO SELL** stocks using AI-powered multi-factor analysis.

## ⚡ Quick Start (3 Steps)

### Step 1: Create your exit watchlist
```bash
# Edit exit.check.txt and add tickers (one per line)
nano exit.check.txt
```

Example `exit.check.txt`:
```
RELIANCE
TCS
INFY
MARUTI
TATASTEEL
```

### Step 2: Run assessment
```bash
# Fast (Codex - FREE)
./run_exit_assessment.sh codex exit.check.txt 72

# Best accuracy (Claude - requires subscription)
./run_exit_assessment.sh claude exit.check.txt 72

# Alternative (Gemini - FREE)
./run_exit_assessment.sh gemini exit.check.txt 72
```

### Step 3: Review results
```bash
# Check immediate exit recommendations
cat exit_assessment_immediate_*.txt

# Check hold/monitor recommendations
cat exit_assessment_hold_*.txt

# Detailed analysis
cat exit_assessment_detailed_*.csv
```

## 📊 Output Interpretation

### Immediate Exit File
Stocks with **critical issues** requiring urgent attention:
- Exit score > 70/100
- Technical breakdown OR fundamental issues OR negative sentiment
- **Action**: Review immediately, consider selling

### Hold/Monitor File
Stocks safe to keep or watch:
- **HOLD section**: Exit score < 50 (safe to keep)
- **MONITOR section**: Exit score 50-70 (warning signs, watch closely)
- **Action**: Set stop losses for MONITOR stocks

### Detailed CSV
Full analysis with scores, reasons, and AI summary

## 🔄 Parallel to run_without_api.sh

| Task | Command |
|------|---------|
| **Find BUY opportunities** | `./run_without_api.sh claude test.txt 8 10` |
| **Find SELL decisions** | `./run_exit_assessment.sh claude exit.check.txt 72` |

**Key Difference**: Exit assessment works **WITHOUT requiring news** - it uses technical indicators, fundamentals, and AI reasoning.

## ⚙️ Assessment Factors (All Applied)

✅ **Technical**: Support breaks, bearish patterns, RSI, momentum
✅ **Fundamental**: Earnings, debt, margins, cash flow
✅ **Sentiment**: News (if available), analyst ratings
✅ **Volume/Momentum**: Trading activity, price trends

## 🎓 Common Use Cases

### Portfolio Review (Weekly)
```bash
./run_exit_assessment.sh claude my_portfolio.txt 168
```

### Quick Check (After market hours)
```bash
./run_exit_assessment.sh codex exit.check.txt 24
```

### Critical Decision (Before earnings)
```bash
./run_exit_assessment.sh claude single_stock.txt 48
```

## 📋 Exit Score Guide

| Score | Recommendation | Action |
|-------|---------------|--------|
| **0-50** | HOLD | No urgent concerns, continue holding |
| **50-70** | MONITOR | Warning signs, set stop loss, watch closely |
| **70-100** | IMMEDIATE EXIT | Critical issues, consider selling |

## 💡 Pro Tips

1. **Run regularly**: Weekly or after major market events
2. **Use Claude for critical decisions**: Best accuracy (~95%)
3. **Review detailed CSV**: Understand the reasoning
4. **Don't panic sell**: System is a decision support tool
5. **Set stop losses**: For stocks in MONITOR category
6. **Consider context**: Your time horizon, tax implications, goals

## ⚠️ Important Notes

- This is NOT financial advice
- Always use your own judgment
- Assessment is based on available data and AI analysis
- Works irrespective of news availability
- Consider consulting a financial advisor for major decisions

## 🚀 Examples

### Example 1: Portfolio with 5 stocks
```bash
# File: exit.check.txt
RELIANCE
TCS
INFY
HDFCBANK
TATASTEEL

# Run assessment
./run_exit_assessment.sh claude exit.check.txt 72

# Output files created:
# exit_assessment_immediate_*.txt  → 1 stock (TATASTEEL)
# exit_assessment_hold_*.txt       → 4 stocks (others)
# exit_assessment_detailed_*.csv   → Full details

# Result: Consider exiting TATASTEEL, hold others
```

### Example 2: Single stock deep dive
```bash
# File: single.txt
MARUTI

# Run with extended news window
./run_exit_assessment.sh claude single.txt 168

# Review detailed CSV for comprehensive analysis
```

## 📞 Help

```bash
# View help
./run_exit_assessment.sh --help

# Or try with just provider name
./run_exit_assessment.sh codex
```

---

**Ready to use!** Start with codex (fast) and upgrade to claude for critical decisions.
