# AI Stock Scanner - Complete Usage Guide

## 🎯 Quick Commands

### Primary Scan Commands
```bash
# Natural language interface (recommended)
python smart_scan.py load context and run scan

# Maximum intelligence scan (48h window, enhanced)
./optimal_scan_config.sh

# AI Path with custom parameters
python run_swing_paths.py --path ai --top 25 --fresh --hours 48 --auto-apply-config --auto-screener
```

### Quick Context Check
```bash
python smart_scan.py read context
```

## 🧠 AI Ranking System Features

### 1. **Multi-Strategy Entity Resolution**
- **Stage 1**: Exact company name matching (Tata Tech → TATATECH)
- **Stage 2**: Operating company preference over ETFs
- **Stage 3**: Smart rejection of mismatched entities

### 2. **Relative Magnitude Assessment** 
- News impact calculated as: **News Amount / Company Market Cap**
- Example: ₹300 Cr for ₹22,000 Cr company = 1.36% impact
- Higher relative impact = higher ranking priority

### 3. **Event Classification & Scoring**
- **IPO/listing**: 65% baseline confidence
- **M&A/JV**: 70% baseline confidence  
- **Order/contract**: 80% baseline confidence
- **Regulatory**: 75% baseline confidence
- **Results/metrics**: 55% baseline confidence

### 4. **Learning System**
- Auto-blacklists poor performers (RETAIL, HINDALCO, APOLLO, WEL, BEL)
- Tracks 1d/3d/5d price reactions
- Updates confidence based on success rates

## 📊 Understanding Output

### Sample Output Format
```
 1. TATATECH    (1.334) - CEO Warren Harris banks on AI as Tata Tech chases $1bn target
    ↳ TATA TECHNOLOGIES LIMITED
    ↳ Management; ~0.35% mcap impact; ticker in title | Management

 2. CESC        (1.205) - CESC raises Rs 300 cr via NCDs  
    ↳ CESC LIMITED
    ↳ General; ~1.36% mcap impact; ticker in title | General
```

### Key Metrics Explained
- **Score**: AI-calculated confidence (higher = better opportunity)
- **Relative Impact**: News size vs company market cap (%)
- **Event Type**: Classified news category
- **Entity Resolution**: Correct company mapping

## 🔧 Configuration Files

### Core Files
- `orchestrator/config.py`: Main ranking configuration
- `configs/entities.json`: Entity resolution rules
- `learning/learning_debate.md`: AI recommendations
- `learning/core_priorities.md`: System priorities

### Key Parameters
```json
{
  "dedup_exponent": 1.0,
  "name_factor_missing": 0.75,
  "magnitude_cap": 0.5,
  "feature_weights": {
    "profit_growth": 0.05,
    "inst_cues": 0.03,
    "circuit_lower": 0.01
  }
}
```

## 📁 Output Structure

### Generated Files
- `outputs/ai_adjusted_top*.csv`: AI-ranked results
- `outputs/swing_top*.txt`: Technical screener results  
- `outputs/feedback_live_*.csv`: Live price tracking
- `learning/learning_context.md`: Updated context
- `learning/learning_debate.md`: AI recommendations

### Archive Organization
- `outputs/aggregates/`: News data
- `outputs/news_runs/`: Historical runs
- `archives/YYYY-MM/`: Monthly archives

## 🚀 Advanced Usage

### Custom Time Windows
```bash
# Weekend/comprehensive scan
python run_swing_paths.py --path ai --top 50 --fresh --hours 168  # 7 days

# Quick intraday scan  
python run_swing_paths.py --path ai --top 15 --fresh --hours 6
```

### Learning System Commands
```bash
# Backfill historical learnings
python smart_scan.py  # Choose option 5

# Archive old outputs
python smart_scan.py  # Choose option 6

# Force config application
python run_swing_paths.py --path ai --auto-apply-config
```

### Debug & Analysis
```bash
# Check entity resolution
python -c "from orchestrator.ranking import resolve_ambiguous_ticker; print(resolve_ambiguous_ticker('Tata Tech news', 'TECH'))"

# Test relative magnitude
python -c "from orchestrator.ranking import calculate_relative_magnitude; print(calculate_relative_magnitude('Rs 100 cr deal', 'COMPANYNAME'))"
```

## 🎪 Menu Options (smart_scan.py)

1. **Run AI Path full auto**: Complete automated scan with config updates
2. **Run AI Path (apply config, no screener)**: Ranking only, skip technical analysis
3. **Run AI Path (dry run)**: Ranking without applying recommendations
4. **Script Path**: Original rule-based system
5. **Backfill learnings (7 days)**: Historical analysis for pattern learning
6. **Archive old outputs**: Clean workspace and create monthly archives

## 🔍 Troubleshooting

### No Results Issue
```bash
# Check for fresh news
ls -1tr aggregated_full_articles_*h_* | tail -n 3
grep -c "Title.*:" aggregated_full_articles_*latest*

# Force broader time window
python run_swing_paths.py --path ai --fresh --hours 48
```

### Entity Resolution Issues
- Check `configs/entities.json` for custom mappings
- Verify company names in `sec_list.csv`
- Review `learning/learning_debate.md` for AI suggestions

### Performance Optimization
- Use priority tickers: `priority_tickers.txt` (faster)
- Limit sources: `--sources reuters.com livemint.com`
- Reduce article count: `--max-articles 5`

## 📈 Success Metrics

### Hit Rate Targets
- **Target**: 2%+ news hit rate (5x improvement over baseline 0.4%)
- **Quality**: Full financial analysis required
- **Precision**: Specific price targets preferred (₹999, $200B)

### Performance Tracking
- Monitor `learning/enhanced_intelligence_update.md`
- Check reliability scores in learning database
- Review price reaction success rates

## 💡 Best Practices

1. **Use 48h windows** for weekend/comprehensive scans
2. **Apply AI recommendations** from learning_debate.md  
3. **Monitor relative magnitude** - prioritize high % impact news
4. **Review entity resolution** - ensure proper company mapping
5. **Track learning updates** - system improves with each run

---

**System Intelligence Level: MAXIMUM** 🧠🚀

*For support: Check learning/learning_debate.md for latest AI recommendations*