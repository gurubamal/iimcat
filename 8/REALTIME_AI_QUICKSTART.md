# QUICK START GUIDE: Real-time AI News Analysis

## TL;DR - Run This Now

```bash
cd /home/vagrant/R/essentials
./run_realtime_ai_scan.sh
```

That's it! The system will:
1. ✅ Fetch latest news (48h window)
2. ✅ Analyze each article INSTANTLY with AI
3. ✅ Update rankings in real-time
4. ✅ Generate scored recommendations

## What You Get

**Instant Results** as news is fetched:
```
[5/50] Processing RELIANCE...
  🤖 Analyzing: Reliance Retail IPO valued at $200B...
     ✅ Score: 87.5 | BULLISH | STRONG BUY

🏆 LIVE TOP 5:
1. RELIANCE - 87.5 | STRONG BUY | M&A, investment
2. HCLTECH - 82.1 | BUY | earnings, expansion
3. TCS - 78.9 | BUY | contract, strategic
...
```

**Final CSV Output**:
- Ranked stocks with AI scores
- Investment recommendations
- Catalysts and risks identified
- Certainty levels
- Expected moves

## Command Options

### Basic Usage
```bash
# Default: all.txt, 48h, top 50
./run_realtime_ai_scan.sh

# Custom tickers file
./run_realtime_ai_scan.sh priority_tickers.txt

# Custom time window (24 hours)
./run_realtime_ai_scan.sh all.txt 24

# Custom number of stocks (top 25)
./run_realtime_ai_scan.sh all.txt 48 25

# Force Claude for AI analysis
AI_PROVIDER=claude ./run_realtime_ai_scan.sh priority_tickers.txt 24 25

# Force Codex/OpenAI
AI_PROVIDER=codex ./run_realtime_ai_scan.sh

# Use Codex without API keys (shell bridge)
AI_PROVIDER=codex CODEX_SHELL_CMD="python3 codex_bridge.py" ./run_realtime_ai_scan.sh

# Cap external AI calls (switches to heuristics afterwards)
AI_MAX_CALLS=60 ./run_realtime_ai_scan.sh priority_tickers.txt 24 25
```

### Python Direct
```bash
python3 realtime_ai_news_analyzer.py \
    --tickers-file all.txt \
    --hours-back 48 \
    --ai-provider codex \
    --max-ai-calls 60 \
    --top 50 \
    --output my_results.csv
```

## How It Works (Behind the Scenes)

### 1. News Fetching + Instant Analysis
```
For each ticker:
  Fetch article 1 → AI analyzes → Score: 85 → Update rank
  Fetch article 2 → AI analyzes → Score: 78 → Update rank
  Fetch article 3 → AI analyzes → Score: 92 → Update rank
  ...
```

### 2. AI Analysis (Per Article)
```
Article: "Reliance Retail IPO valued at $200B by 2027"

AI Processing:
├─ Catalyst Detection: M&A, investment ✓
├─ Deal Value: $200B → ₹16.5L crores 💰
├─ Sentiment: BULLISH 📈
├─ Certainty: 89% (confirmed source) ✓
├─ Impact: HIGH (mega deal) 🚀
└─ Recommendation: STRONG BUY ⭐⭐⭐⭐⭐

Score: 87.5/100
```

### 3. Real-time Ranking
```
After RELIANCE analyzed: #1 (87.5)
After TCS analyzed: #2 (82.1), RELIANCE still #1
After INFY analyzed: #2 (85.0), RELIANCE #1, TCS #3
... continuously updated
```

## Integration with Existing System

### Replace Your Current Scanner

**OLD way** (batch processing):
```bash
./run_real_ai_full.sh  # Fetch all → Wait → Analyze
```

**NEW way** (real-time):
```bash
./run_realtime_ai_scan.sh  # Fetch + analyze simultaneously
```

### Codex Without API Keys

To run Stage 2 with Codex but without API keys, use the built-in shell bridge:

```bash
export AI_PROVIDER=codex
export CODEX_SHELL_CMD="python3 codex_bridge.py"

# NIFTY50 default (48h)
./run_realtime_ai_scan.sh

# Focus on 10 NIFTY names
TOP_FOCUS=10 MAX_ARTICLES_STAGE2=2 ./run_realtime_ai_scan.sh nifty50_tickers.txt 48
```

See `REALTIME_AI_CODEX_SHELL_BRIDGE.md` for details and tuning options.

### Use with Frontier AI Quant

```bash
# Step 1: Real-time analysis
./run_realtime_ai_scan.sh all.txt 48 50

# Step 2: Apply quant filters
python3 frontier_ai_quant_alpha.py \
    --input realtime_ai_analysis_*.csv \
    --apply-gates \
    --output final_picks.csv
```

## Output Files

```
realtime_ai_analysis_20251022_132644.csv  ← Your results!
realtime_ai_20251022_132644.log           ← Detailed log
```

### CSV Format
```csv
rank,ticker,ai_score,sentiment,recommendation,catalysts,risks,certainty,articles_count
1,RELIANCE,87.5,bullish,STRONG BUY,"M&A,investment",Competition,89,3
2,HCLTECH,82.1,bullish,BUY,"earnings,expansion",Regulation,85,2
3,TCS,78.9,bullish,BUY,"contract,strategic",Market,81,4
```

## Reading the Results

### Score Interpretation
- **90-100**: 🔥 Exceptional opportunity - confirmed major catalyst
- **75-89**: ⭐ Strong opportunity - solid catalyst
- **60-74**: ✓ Moderate opportunity - decent catalyst
- **45-59**: ⚠️ Weak opportunity - minor catalyst or low certainty
- **0-44**: ❌ Poor opportunity - avoid

### Recommendations
- **STRONG BUY**: High score + high certainty - immediate entry
- **BUY**: Good score - accumulate on dips
- **ACCUMULATE**: Moderate score - dollar-cost average
- **HOLD**: Existing positions only
- **WATCH**: Wait for better setup

### Certainty Levels
- **80-95%**: High certainty - specific numbers, confirmed actions
- **60-79%**: Good certainty - credible sources, some specifics
- **40-59%**: Moderate certainty - reasonable but limited info
- **20-39%**: Low certainty - speculation or vague

## Example Real Trade Setup

**From CSV Output**:
```
HCLTECH,82.1,bullish,BUY,"earnings,expansion",Regulation,85,2
```

**Your Action**:
1. **Validate**: Check the 2 news articles (in log file)
2. **Verify**: Look up HCLTECH recent earnings
3. **Entry**: Set buy order at current price
4. **Stop Loss**: Use ATR-based (from quant system)
5. **Target**: 5-8% based on catalyst magnitude
6. **Position Size**: Based on certainty (85% → larger position)

## Troubleshooting

### "No output file generated"
```bash
# Check if script ran
ls -lt realtime_ai_*.csv

# Check log for errors
tail -50 realtime_ai_*.log
```

### "Analysis too slow"
```bash
# Reduce scope
./run_realtime_ai_scan.sh priority_tickers.txt 24 10

# Only 10 tickers, 24h window
```

### "Scores seem wrong"
```bash
# Enable verbose mode
python3 realtime_ai_news_analyzer.py \
    --tickers-file all.txt \
    --verbose
```

### "Integration error"
```bash
# Check dependencies
python3 -c "import pandas, numpy"

# Verify files exist
ls realtime_ai_news_analyzer.py ai_enhanced_collector.py
```

## Performance Expectations

### Speed
- **Analysis**: 1-2 seconds per article
- **Per ticker**: 5-10 seconds (with 5-10 articles)
- **Full scan (50 tickers)**: 5-8 minutes

### Quality
- **Win rate target**: >60% of top 10 picks
- **False positive rate**: <20%
- **Certainty accuracy**: >70% correlation

## Next Steps After First Run

1. **Review top 10 picks** in CSV
2. **Read detailed reasoning** in log file
3. **Validate catalysts** with original news sources
4. **Set up trades** for highest-scoring picks
5. **Track results** for system improvement

## Pro Tips

### Best Practices
```bash
# Run daily at market close
0 16 * * 1-5 /home/vagrant/R/essentials/run_realtime_ai_scan.sh

# Focus on top performers
./run_realtime_ai_scan.sh priority_tickers.txt 24 25

# Cross-reference with quant
./run_realtime_ai_scan.sh && \
python3 frontier_ai_quant_alpha.py --input realtime_ai_*.csv
```

### Watchlist Management
```bash
# Create watchlist from top picks
head -11 realtime_ai_analysis_*.csv | tail -10 | cut -d',' -f2 > watchlist.txt

# Monitor watchlist next day
./run_realtime_ai_scan.sh watchlist.txt 24 10
```

### Performance Tracking
```bash
# Save results daily
mkdir -p results/$(date +%Y%m)
cp realtime_ai_analysis_*.csv results/$(date +%Y%m)/

# Compare over time
diff results/202510/realtime_*.csv
```

## Advanced Usage

### Custom AI Prompt
Edit `realtime_ai_news_analyzer.py` → `_build_ai_prompt()` function

### Adjust Scoring Weights
Edit `realtime_ai_news_analyzer.py`:
```python
AI_WEIGHT = 0.6  # Change to 0.7 for more AI influence
FRONTIER_WEIGHT = 0.4  # Change to 0.3
```

### Add Custom Catalysts
Edit `_intelligent_pattern_analysis()`:
```python
catalyst_patterns = {
    'your_custom': (['keywords'], points),
    ...
}
```

## Getting Help

### Check System Status
```bash
# Verify installation
python3 realtime_ai_news_analyzer.py --help

# Test with small sample
./run_realtime_ai_scan.sh priority_tickers.txt 24 5
```

### Debug Mode
```bash
# Full verbose output
python3 realtime_ai_news_analyzer.py \
    --tickers RELIANCE TCS INFY \
    --verbose
```

### Common Issues
1. **ImportError**: Install requirements: `pip install -r requirements.txt`
2. **No news found**: Check internet connection, try wider time window
3. **AI slow**: Normal for first run, uses pattern matching as fallback
4. **Empty results**: Check ticker symbols are valid NSE tickers

---

## Success Checklist

- [ ] Script runs without errors
- [ ] CSV file generated with rankings
- [ ] Top picks have scores >70
- [ ] Recommendations make sense
- [ ] Catalysts identified correctly
- [ ] Ready to validate with research
- [ ] Set up trades with proper risk management

---

**Ready to start?** Run this command now:
```bash
cd /home/vagrant/R/essentials && ./run_realtime_ai_scan.sh
```

**Questions?** Check `REALTIME_AI_ANALYSIS_README.md` for full documentation.
