# Real-time AI Scanner (Quick Guide)

## 1. Prerequisites
- Python 3.10+
- `pip install -r requirements.txt`
- Coding agents (optional, only if you need external models):
  - Claude coding agent → `ANTHROPIC_API_KEY`
  - OpenAI Codex coding agent → `OPENAI_API_KEY`

## 2. One-command Run
```bash
cd /home/vagrant/R/essentials
./run_realtime_ai_scan.sh            # all tickers, 48h, auto AI
```

### Popular variants
```bash
AI_PROVIDER=claude ./run_realtime_ai_scan.sh priority_tickers.txt 24 50
AI_PROVIDER=codex AI_MAX_CALLS=60 ./run_realtime_ai_scan.sh all.txt 12 25
```

Outputs appear as `realtime_ai_analysis_<timestamp>.csv` + matching `.log`.

## 3. Direct Python Control
```bash
python3 realtime_ai_news_analyzer.py \
  --tickers-file priority_tickers.txt \
  --hours-back 24 \
  --ai-provider claude \
  --max-ai-calls 40 \
  --top 25 \
  --output realtime_ai_results.csv
```

## 4. Managing AI Usage
- `AI_PROVIDER` / `--ai-provider`: `auto`, `claude`, `codex`, or `heuristic`.
- `AI_MAX_CALLS` env or `--max-ai-calls`: hard cap before the analyzer switches to the built-in heuristic scorer.
- Built-in cache skips duplicate headlines automatically, so repeated runs on the same feed reuse scores.

## 5. Post-processing
Feed the CSV into the quant layer for deeper filtering:
```bash
python3 frontier_ai_quant_alpha.py --top25 top25_for_frontier_ai.csv --news realtime_ai_*.log
```

## 6. Troubleshooting
- Missing output? Check the latest `realtime_ai_*.log` for API errors or rate limits.
- Slow run? Reduce tickers/time window or lower `--top`.
- No coding agents? Leave `AI_PROVIDER=auto`; the system will detect the absence and stay in heuristic mode.
