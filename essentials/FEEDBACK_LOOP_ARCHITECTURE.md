# Real-Time AI Feedback Loop - System Architecture

## 🔄 Complete Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    PHASE 1: INITIAL ANALYSIS                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  AI Analyzer     │
                    │  (Claude/Codex)  │◄──── News Sources
                    └──────────────────┘      (ET, BL, Mint)
                              │
                              ▼
                    ┌──────────────────┐
                    │  Base Analysis   │
                    │  • Score: 75     │
                    │  • RSI: 82       │
                    │  • Catalyst: X   │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Adaptive Layer   │◄──── Learned Weights
                    │ (if available)   │      (learned_weights.json)
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Adjusted Score   │
                    │ • Score: 68      │      (Overbought penalty applied)
                    │ • Rec: HOLD      │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Record Prediction│──────► predictions_tracking.json
                    │ • Ticker: SAIL   │        {
                    │ • Score: 68      │          "SAIL": {
                    │ • Price: ₹245    │            "timestamp": "...",
                    │ • Timestamp      │            "score": 68,
                    └──────────────────┘            "initial_price": 245,
                              │                     "recommendation": "HOLD"
                              │                   }
                              │                 }
                              │
┌─────────────────────────────────────────────────────────────────┐
│                   PHASE 2: MONITORING (3-24h)                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Price Monitor    │
                    │ (Continuous)     │
                    └──────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
        ┌───────────────────┐   ┌───────────────────┐
        │ Fetch Live Price  │   │ Check Age         │
        │ (yfinance/API)    │   │ (3+ hours?)       │
        └───────────────────┘   └───────────────────┘
                    │                   │
                    └─────────┬─────────┘
                              ▼
                    ┌──────────────────┐
                    │ Current State    │
                    │ • Price: ₹238    │      ❌ Down -2.9%
                    │ • RSI: 68        │         (Prediction failed)
                    │ • Volume: -15%   │
                    └──────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 3: EVALUATION                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Compare Results  │
                    │ Predicted: +5%   │
                    │ Actual: -2.9%    │
                    │ Correct? ❌      │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Create Record    │──────► performance_history.json
                    │ • Accuracy: 0%   │        [
                    │ • Catalyst: X    │          {
                    │ • RSI: 82→68     │            "ticker": "SAIL",
                    │ • Volume: -15%   │            "predicted_move": 5,
                    └──────────────────┘            "actual_move": -2.9,
                              │                     "prediction_correct": false,
                              │                     "weights_used": {...}
                              │                   }
                              │                 ]
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 4: LEARNING (5+ samples)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Analyze Patterns │
                    │ • Overbought     │
                    │   success: 0%    │
                    │ • Volume conf.   │
                    │   success: 100%  │
                    │ • Fundamentals   │
                    │   success: 80%   │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Update Weights   │
                    │ Overbought:      │
                    │   0.15 → 0.19    │      +27% increase
                    │ Volume:          │
                    │   0.08 → 0.12    │      +46% increase
                    │ Fundamentals:    │
                    │   0.25 → 0.24    │      (stable)
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Save Config      │──────► learned_weights.json
                    │ • New weights    │        {
                    │ • Catalyst scores│          "weights": {
                    │ • Timestamp      │            "overbought": 0.19,
                    │ • Insights       │            "volume": 0.12,
                    └──────────────────┘            ...
                              │                   },
                              │                   "catalyst_scores": {...}
                              │                 }
                              │
┌─────────────────────────────────────────────────────────────────┐
│                  PHASE 5: NEXT CYCLE (IMPROVED)                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ New Analysis     │
                    │ (with learned    │
                    │  weights)        │◄──── Learned Weights
                    └──────────────────┘      (automatically loaded)
                              │
                              ▼
                    ┌──────────────────┐
                    │ Smarter Scoring  │
                    │ • RSI >70: ⚠️    │      Heavy penalty applied
                    │ • No volume: ❌  │      Auto-reject
                    │ • Strong fund.: ✅│     Boost score
                    └──────────────────┘
                              │
                              ▼
                         REPEAT CYCLE
                    (Gets better each time)
```

---

## 🏗️ System Components

### Core Modules

#### 1. **realtime_feedback_loop.py**
```
FeedbackLoopTracker
├── record_prediction()           # Store AI prediction
├── update_actual_performance()   # Log market outcome
├── learn_from_performance()      # Update weights
├── _analyze_performance_patterns()
├── _update_weights()
├── _update_catalyst_scores()
└── generate_performance_report()
```

**Data Files:**
- `predictions_tracking.json` - Active predictions
- `performance_history.json` - Historical results
- `learned_weights.json` - Learned configuration

#### 2. **realtime_price_monitor.py**
```
RealTimePriceMonitor
├── fetch_current_price()         # Get live market data
├── check_active_predictions()    # Review all tracked stocks
├── auto_update_predictions()     # Auto-evaluate when ready
├── monitor_continuous()          # Daemon mode
└── generate_monitoring_dashboard()
```

**Features:**
- Live price fetching (yfinance)
- Auto-update after 3+ hours
- Continuous monitoring daemon
- Auto-trigger learning

#### 3. **adaptive_ai_analyzer.py**
```
AdaptiveAIAnalyzer
├── adjust_score_with_learned_weights()
├── _apply_overbought_penalty()
├── _apply_volume_boost()
├── _apply_catalyst_adjustments()
└── compare_analyses()            # Standard vs Adaptive
```

**Improvements:**
- Dynamic score adjustments
- Context-aware penalties/boosts
- Historical performance integration

---

## 📊 Data Flow

### Input Sources
```
┌────────────────────┐
│ News Articles      │─────┐
│ (ET, BL, Mint)     │     │
└────────────────────┘     │
                           │
┌────────────────────┐     │    ┌──────────────────┐
│ Market Data        │─────┼───►│  AI Analyzer     │
│ (Price, RSI, Vol.) │     │    └──────────────────┘
└────────────────────┘     │
                           │
┌────────────────────┐     │
│ Technical Indicators│────┘
│ (MACD, Support/Res)│
└────────────────────┘
```

### Processing Pipeline
```
Raw Data
   │
   ▼
Base Analysis (Claude/Codex)
   │
   ▼
Adaptive Layer (Learned Weights)
   │
   ▼
Adjusted Score & Recommendation
   │
   ▼
Record Prediction
   │
   ▼
Monitor (3-24h)
   │
   ▼
Evaluate Performance
   │
   ▼
Learn & Update Weights
   │
   ▼
Apply to Next Analysis (Loop)
```

---

## 🎯 Learning Algorithm Details

### Weight Adjustment Formula

```python
# Simplified version
if success_rate < 40:
    new_weight = old_weight * 1.3  # Increase penalty
elif success_rate > 70:
    new_weight = old_weight * 1.5  # Increase boost

# Normalize to ensure sum = 1.0
total = sum(all_weights)
normalized_weight = new_weight / total
```

### Catalyst Scoring

```python
success_rate = correct_predictions / total_predictions * 100

if success_rate >= 80:
    catalyst_score = 92
elif success_rate >= 70:
    catalyst_score = 85
elif success_rate >= 60:
    catalyst_score = 75
else:
    catalyst_score = 55
```

### Example Learning Cycle

**Before Learning (Default Weights):**
```json
{
  "technical_overbought": 0.15,
  "volume_confirmation": 0.08,
  "fundamental_catalyst": 0.25
}
```

**After 3 Predictions (SAGILITY ❌, WORTH ✅, BHEL ❌):**
```json
{
  "technical_overbought": 0.19,  // +27% (RSI failures)
  "volume_confirmation": 0.12,   // +46% (volume critical)
  "fundamental_catalyst": 0.24   // -2% (slightly less weight)
}
```

---

## 🔧 Integration Points

### With Existing System

```bash
# 1. Run your normal analysis
python3 run_swing_paths.py --path ai --top 50

# 2. Wrap with adaptive layer (automatic)
# The system checks for learned_weights.json automatically

# 3. Record predictions
python3 realtime_feedback_loop.py --record TICKER --analysis-file output.json

# 4. Monitor automatically
python3 realtime_price_monitor.py --monitor --auto-learn &
```

### Manual Override

```python
# Disable learning (use defaults)
analyzer = AdaptiveAIAnalyzer(use_learned_weights=False)

# Force specific weights
analyzer.weights = {'technical_overbought': 0.25, ...}
```

---

## 📈 Performance Tracking

### Metrics Captured

For each prediction:
```json
{
  "ticker": "SAIL",
  "prediction_time": "2025-10-30T13:51:45",
  "evaluation_time": "2025-10-30T16:30:00",
  "predicted_move_pct": 5.0,
  "actual_move_pct": -2.9,
  "prediction_correct": false,
  "prediction_accuracy": 0.0,
  "catalysts": ["earnings_beat"],
  "initial_rsi": 82,
  "current_rsi": 68,
  "volume_change_pct": -15,
  "weights_used": {...}
}
```

### Aggregated Stats
```
Overall Accuracy: 72%
By Recommendation:
  - STRONG BUY: 80% (8/10)
  - BUY: 67% (10/15)
  - HOLD: 75% (3/4)

By Catalyst:
  - order_book_expansion: 92% (11/12)
  - earnings_beat: 65% (13/20)
  - technical_breakout: 40% (4/10)
```

---

## 🚀 Scaling Considerations

### For Production Use

1. **Database Backend**: Replace JSON files with PostgreSQL/MongoDB
2. **Real-Time Streaming**: Use WebSocket for live price updates
3. **Multi-Threaded**: Monitor 100+ stocks simultaneously
4. **API Integration**: RESTful API for external systems
5. **Dashboard UI**: Web interface for visualization

### Performance Optimizations

- **Batch Updates**: Process multiple stocks in parallel
- **Caching**: Cache price data for 1-minute intervals
- **Async I/O**: Non-blocking network requests
- **Rate Limiting**: Respect API limits (yfinance, news sources)

---

## 🎓 Advanced Features (Future)

### Planned Enhancements

1. **Multi-Timeframe Learning**
   - Separate weights for intraday vs swing vs long-term
   - Time-weighted performance (recent > old)

2. **Market Regime Detection**
   - Bull market vs bear market weights
   - Volatility-adjusted scoring

3. **Ensemble Learning**
   - Combine multiple AI models
   - Weighted voting based on historical performance

4. **Auto-Strategy Generation**
   - Discover optimal entry/exit rules
   - Backtesting integration

5. **Risk-Adjusted Scoring**
   - Sharpe ratio consideration
   - Drawdown analysis

---

## 📊 Visual Summary

```
┌─────────────────────────────────────────────────────────┐
│  FEEDBACK LOOP CYCLE                                    │
│                                                         │
│  1. PREDICT    →  AI scores stock (with learned weights)│
│  2. RECORD     →  Store prediction & timestamp         │
│  3. MONITOR    →  Track price movements (live)         │
│  4. EVALUATE   →  Compare predicted vs actual          │
│  5. LEARN      →  Adjust weights based on results      │
│  6. IMPROVE    →  Next prediction is smarter           │
│                                                         │
│  Repeat → AI accuracy improves over time               │
└─────────────────────────────────────────────────────────┘

ACCURACY TRAJECTORY:

  85%│                                        ╱─────
  80%│                                  ╱────╯
  75%│                            ╱────╯
  70%│                      ╱────╯
  65%│                ╱────╯
  60%│          ╱────╯
  55%│    ╱────╯
  50%│───╯
     └─────────────────────────────────────────────────
      0   5   10  15  20  25  30  35  40  45  50  (samples)

     Initial  Learning   Calibrated    Optimized
```

---

## 🎯 Key Takeaways

1. **Self-Improving**: AI gets smarter with each prediction
2. **Transparent**: All adjustments are logged and explainable
3. **Automated**: Runs continuously without manual intervention
4. **Adaptive**: Learns your market's specific patterns
5. **Measurable**: Clear metrics show improvement over time

**Start simple** (manual recording) → **Scale up** (automated monitoring) → **Optimize** (let AI learn)

The system is designed to be:
- ✅ Easy to start (run simulation first)
- ✅ Incremental (add features as needed)
- ✅ Transparent (all decisions logged)
- ✅ Measurable (track accuracy over time)
- ✅ Scalable (from 1 stock to 1000+)

---

**Ready to build a self-improving AI trading assistant!** 🚀
