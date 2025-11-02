# AI Stock Scanner - Quick Start

## 🚀 One-Line Commands

### Most Common Usage
```bash
# Load context and run intelligent scan
python smart_scan.py load context and run scan

# Maximum intelligence weekend scan
./optimal_scan_config.sh
```

### Quick Commands by Scenario

**Weekend/Comprehensive Analysis:**
```bash
python run_swing_paths.py --path ai --top 50 --fresh --hours 48 --auto-apply-config --auto-screener
```

**Quick Daily Check:**
```bash
python run_swing_paths.py --path ai --top 25 --fresh --hours 10
```

**Just Show Context:**
```bash
python smart_scan.py read context
```

## 📊 Understanding Results

### What to Look For
1. **High Relative Impact**: News with >1% market cap impact
2. **Event Types**: IPO/M&A (higher confidence) vs General news
3. **Entity Resolution**: Ensure company names match news content
4. **Learning Signals**: Check AI recommendations in output

### Sample Good Pick
```
 1. CESC        (1.205) - CESC raises Rs 300 cr via NCDs
    ↳ CESC LIMITED  
    ↳ General; ~1.36% mcap impact; ticker in title
```
**Why Good**: 1.36% market cap impact is significant for stock movement

### Sample Poor Pick (Avoid)
```
 1. TECH       (1.334) - Tata Tech news but mapped to IT ETF
    ↳ ADITYA BIRLA NIFTY IT ETF
    ↳ Wrong entity mapping!
```
**Why Poor**: News about Tata Tech wrongly attributed to an ETF

## 🎯 Files to Check

**Primary Results:**
- Latest `outputs/ai_adjusted_top*.csv` 
- `learning/learning_debate.md` (AI recommendations)

**System Health:**
- `learning/core_priorities.md` (system status)
- `learning/learning_context.md` (performance tracking)

## 🔧 Quick Fixes

**No Results? Try:**
```bash
# Broader time window
python run_swing_paths.py --path ai --fresh --hours 48

# Check what news is available
ls -1tr aggregated_full_articles_*h_* | tail -n 3
```

**Wrong Entity Mapping?**
- Review `configs/entities.json` for custom rules
- Check if company exists in `sec_list.csv`

---
**📖 For complete documentation: See `AI_STOCK_SCANNER_GUIDE.md`**