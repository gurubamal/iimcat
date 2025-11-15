# AI Feedback Loop System - Complete Guide

## 🎯 Overview

Your system now has **automated learning** that improves with each analysis cycle. The AI learns from past predictions and adjusts future analyses accordingly.

## 🔄 How It Works

### 1. **Analysis Phase** (Automatic)
When you run: `./run_without_api.sh claude 100.txt 8 10`

The system:
- ✅ Loads historical learnings from `learning/learned_weights.json`
- ✅ Loads ticker-specific performance from `learning/learning.db`
- ✅ Passes this context to Claude for analysis
- ✅ Records predictions to learning database
- ✅ Generates results CSV

### 2. **Feedback Phase** (Manual - after 3-24 hours)
```bash
# View active predictions
python3 update_feedback.py --list

# Update with actual performance
python3 update_feedback.py --ticker MARUTI --current-price 12950 --current-rsi 62
```

### 3. **Learning Phase** (After 3+ updates)
```bash
python3 update_feedback.py --learn
```

### 4. **Continuous Improvement** (Automatic)
Next analysis automatically uses learned weights!

## 📊 Quick Start

```bash
# 1. Run analysis
./run_without_api.sh claude 100.txt 8 10

# 2. Wait 3-6 hours

# 3. Update top stocks
python3 update_feedback.py --ticker STOCK1 --current-price <PRICE>
python3 update_feedback.py --ticker STOCK2 --current-price <PRICE>

# 4. After 3+ updates
python3 update_feedback.py --learn

# 5. Run analysis again - now improved!
./run_without_api.sh claude 100.txt 8 10
```

## 📈 Example Learning Cycle

**Iteration 1:**
- MARUTI Score: 78/100 → Actual: -2.5% (LOSS)
- System learns: "Overbought stocks underperform"

**Iteration 2:**
- MARUTI Score: 69/100 (auto-adjusted based on history)
- Prompt includes: "⚠️ This ticker has underperformed"
- More conservative targets

**Result:** Improved accuracy through continuous learning!

---

See full documentation in the system.
