# Swing Screener Extraction Guide

This guide documents the most effective, self‑contained components to extract from `swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py` and how to assemble them into a robust swing‑trading setup to rank stocks.

Scope: Data quality, indicators, swing signals, scoring/tiering, entry/risk, batching and performance.

Note: File/line references below point to the current repository version and may shift with edits.


## Why These Components

- Quality‑first pipeline avoids corrupted indicators (corporate actions/outliers).
- Vectorized indicators and fast swing signals scale well on watchlists.
- Clear, additive scoring and tiers make ranking explainable and tunable.
- Caching + batched I/O reduce latency and flakiness.


## Minimal Pipeline (Recommended)

1) Fetch + Clean
- Get and validate history with winsorization (cap returns/volume once, rebuild series):
  - `YFinanceDataValidator.safe_ticker_history` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:1677)
  - `apply_adaptive_winsorization` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:1766)
  - `align_to_nse_trading_calendar` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2031)

2) Compute Core Indicators (correct implementations)
- RSI (Wilder), Bollinger position (0–100), ATR (Wilder):
  - `rsi14` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2708)
  - `bollinger_band_position` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2740)
  - `average_true_range` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2770)
- Or the single‑pass vectorized engine:
  - `VectorizedIndicators.calculate_all_indicators` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:257)

3) Apply Quality Filters
- Liquidity, price floor, recency:
  - `apply_quality_filters` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2453)

4) Signals (optional but high impact)
- Fast reversal from highs/lows:
  - `calculate_swing_reversal_signals_fast` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3708)
- Robust reversal (uses capped data):
  - `calculate_swing_reversal_signals` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:4820)

5) Score + Tier (Ranking)
- Indicator‑based opportunity score with clear breakdown:
  - `calculate_opportunity_score` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2494)
    - Tier rules: Tier1 ≥ 25, Tier2 ≥ 15, else Watch
- Lightweight blended score (indicators + swing signal):
  - `calculate_basic_score_fast` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3740)

6) Entry & Risk (deployment)
- Simple long signal + ATR SL/TP:
  - `generate_trading_signals` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3075)
  - `calculate_signal_confidence` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3155)
- Tiered ATR entries/stops:
  - `EntryStrategy` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:9041)

7) Batch Orchestration + Performance
- Screen multiple tickers concurrently:
  - `batch_screen_tickers` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2665)
- Optimized history + TTL cache:
  - `get_history_optimized` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3636)
  - `EnhancedCacheManager` (swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3544)


## What To Extract (Most Effective Subset)

- Data Quality
  - `apply_adaptive_winsorization` (cap once → rebuild), `get_robust_price_data`, `validate_winsorization_quality`, `align_to_nse_trading_calendar`.
  - Benefit: Prevents outliers from corrupting RSI/BB/ATR; stable signals.

- Indicators
  - `rsi14`, `bollinger_band_position`, `average_true_range`, and/or `VectorizedIndicators.calculate_all_indicators` for EMA20/50 slope, volume ratio, RR, S/R.

- Filters
  - `apply_quality_filters` (avg/recent volume, price floor, min bars).

- Signals
  - `calculate_swing_reversal_signals_fast` (lightweight) or `calculate_swing_reversal_signals` (robust).

- Scoring + Tiering
  - `calculate_opportunity_score` as primary ranking (clear thresholds; explainable), or `calculate_basic_score_fast` for compact scoring.

- Entry/Risk
  - `generate_trading_signals` for simple deployment logic; `EntryStrategy` for consistent ATR stops/entries.

- Batch + Perf
  - `batch_screen_tickers`, `get_history_optimized`, `EnhancedCacheManager` for scale.


## Scoring Details (Out‑of‑the‑Box)

- `calculate_opportunity_score` (Tier1 ≥ 25, Tier2 ≥ 15):
  - RSI: ≤30=+10, ≤40=+7, ≤50=+3
  - Bollinger position: ≤20=+10, ≤30=+7, ≤40=+3
  - Volume ratio (vs 20‑day avg): 1.5x=+3, 2.0x=+5, 3.0x=+7
  - ATR% of price: 2–5%=+3, 1–6%=+1.5, else 0
  - 5‑day momentum: −2%..+1%=+2; −5%..+3%=+1

- `calculate_basic_score_fast` (0–10):
  - Adds RSI/BB/Volume/RR, and swing reversal (weighted 0.3). Clamped to [0,10].


## Suggested Extraction Layout

- `swing_screener/quality.py`
  - `apply_adaptive_winsorization`, `get_robust_price_data`, `validate_winsorization_quality`, `align_to_nse_trading_calendar`

- `swing_screener/indicators.py`
  - `rsi14`, `bollinger_band_position`, `average_true_range`, `VectorizedIndicators`

- `swing_screener/signals.py`
  - `calculate_swing_reversal_signals_fast`, `calculate_swing_reversal_signals`, `generate_trading_signals`, `calculate_signal_confidence`

- `swing_screener/scoring.py`
  - `calculate_opportunity_score`, `calculate_basic_score_fast`

- `swing_screener/screen.py`
  - `process_ticker_data_complete`, `apply_quality_filters`, `screen_single_ticker_complete`, `batch_screen_tickers`

- `swing_screener/data.py`
  - `YFinanceDataValidator.safe_ticker_history`, `get_history_optimized`, `EnhancedCacheManager`, `sanitize`, `ensure_ns_suffix`

- `swing_screener/entry.py`
  - `EntryStrategy`


## Minimal Usage Pattern

1) For each ticker:
- `df = process_ticker_data_complete(ticker, '1y')`
- `if not apply_quality_filters(df, ticker): continue`
- `signals = calculate_swing_reversal_signals_fast(df)` (optional)
- `score = calculate_opportunity_score(df, ticker)`
- Rank by `score['total_score']`, bucket by `score['tier']`

2) For deployment (optional):
- `sig = generate_trading_signals(df, ticker)` → entry, SL=1.5×ATR, TP=3×ATR
- Or use `EntryStrategy.tier1/tier2/tier3`


## Function Reference Map

- Data Access/Quality
  - `YFinanceDataValidator.safe_ticker_history` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:1677
  - `apply_adaptive_winsorization` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:1766
  - `get_robust_price_data` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:1856
  - `validate_winsorization_quality` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:1952
  - `align_to_nse_trading_calendar` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2031
  - `get_quality_safe_price_data` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2198
  - `sanitize`, `ensure_ns_suffix` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:486, 500

- Indicators
  - `VectorizedIndicators.calculate_all_indicators` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:257
  - `rsi14` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2708
  - `bollinger_band_position` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2740
  - `average_true_range` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2770

- Screening/Scoring
  - `process_ticker_data_complete` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2807
  - `apply_quality_filters` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2453
  - `calculate_opportunity_score` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2494
  - `calculate_basic_score_fast` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3740
  - `screen_single_ticker_complete` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2589
  - `batch_screen_tickers` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:2665

- Signals/Entry
  - `calculate_swing_reversal_signals_fast` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3708
  - `calculate_swing_reversal_signals` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:4820
  - `generate_trading_signals` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3075
  - `calculate_signal_confidence` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3155
  - `EntryStrategy` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:9041

- Performance
  - `get_history_optimized` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3636
  - `EnhancedCacheManager` — swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py:3544


## Practical Notes

- Liquidity guardrails: `apply_quality_filters` default avg volume ≥ 300k, recent ≥ 100k, price ≥ ₹20, bars ≥ 50.
- Risk/Reward: Vectorized engine includes S/R and R/R; use it to prioritize entries.
- India tickers: use raw symbols (e.g., `INFY`); `ensure_ns_suffix` adds `.NS` safely.
- Start simple: use `calculate_opportunity_score` for ranking; layer swing reversal and R/R for priority.


## Next Steps (Optional Enhancements)

- Institutional aggregation: `calculate_color_score` for FII growth, catalysts, AVWAP, order flow (advanced ranking).
- Fundamental/news tiers: `TierClassifier` (requires additional data sources).
- Backtesting hooks and paper trading (integrations exist in the script).


---

If you want, we can stub a `swing_screener/` package with this structure and a CLI that prints a ranked table using the components above.

