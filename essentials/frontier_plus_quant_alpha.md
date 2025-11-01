Frontier Quant Alpha is now computed and blended into the final score for every article. This makes the “Frontier + Quant”
  claim accurate for both claude-shell and codex-shell runs.

  What Changed

  - Realtime analyzer now computes Quant Alpha and uses it in ranking
      - Adds yfinance-powered Quant features + AlphaCalculator; caches per ticker.
      - Blends alpha into the final score with a configurable weight.
      - Still uses the improved AI/heuristic + Frontier news certainty and catalyst signal.

  Key Code Updates

  - realtime_ai_news_analyzer.py:625–635
      - Loads LLMNewsScorer, AlphaCalculator, and new QuantFeatureEngine (with demo toggle).
  - realtime_ai_news_analyzer.py:652–666, 679–681
      - New Frontier + Quant config and cache:
          - FRONTIER_ALPHA_ENABLED (default 1)
          - FRONTIER_ALPHA_WEIGHT (default 0.10; clamps to 0.30)
          - FRONTIER_QUANT_SUFFIX (default .NS)
          - FRONTIER_QUANT_LOOKBACK (default 180)
          - FRONTIER_ALPHA_USE_DEMO (default 0)
          - In-memory _quant_cache
  - realtime_ai_news_analyzer.py:1249–1271
      - _apply_frontier_scoring(...) computes:
          - Frontier news metrics (certainty/catalyst/sentiment)
          - Optional Quant Alpha via QuantFeatureEngine + AlphaCalculator
          - Returns alpha and alpha_metrics for downstream use
  - realtime_ai_news_analyzer.py:1272–1316
      - _combine_scores(...) now uses env-driven alpha weight when alpha is present.
  - frontier_ai_quant_alpha_core.py:110–142
      - Flatten yfinance’s MultiIndex DataFrame into standard OHLCV to avoid runtime errors.

  Config Options

  - FRONTIER_ALPHA_ENABLED=1 to enable (default ON).
  - FRONTIER_ALPHA_WEIGHT=0.15 tunes alpha influence (0.0–0.30).
  - FRONTIER_QUANT_SUFFIX=.NS maps tickers like HINDALCO -> HINDALCO.NS.
  - FRONTIER_QUANT_LOOKBACK=180 controls history length.
  - FRONTIER_ALPHA_USE_DEMO=1 forces synthetic OHLCV if you want zero network reliance.

  Validation Snapshot

  - Example run inside the analyzer (heuristic path):
      - HINDALCO with credible earnings headline:
          - Quant alpha computed (e.g., ~74)
          - Final ai_score blended with alpha (with FRONTIER_ALPHA_WEIGHT=0.15)
          - quant_alpha field is included in InstantAIAnalysis and saved to CSV as before.

  How To Use

  - Keep your existing commands. Alpha is now used by default:
      - ./run_without_api.sh codex 2.txt 48 10
      - ./run_without_api.sh claude 2.txt 48 10
  - Optional tuning:
      - FRONTIER_ALPHA_WEIGHT=0.15 ./run_without_api.sh codex 2.txt 48 10
      - FRONTIER_ALPHA_USE_DEMO=1 if you want to avoid yfinance and still compute alpha.

  File References

  - realtime_ai_news_analyzer.py:625–635, 652–681, 1249–1271, 1272–1316
  - frontier_ai_quant_alpha_core.py:110–142

  If you want, I can add a small line in the live rankings to display Quant Alpha (e.g., “Alpha: 74”) under each ticker.
