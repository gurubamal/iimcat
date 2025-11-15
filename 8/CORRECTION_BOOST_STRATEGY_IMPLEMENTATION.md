# Correction Boost Strategy Implementation Documentation

## Hybrid Score Implementation Note

- Current base hybrid score: AI Score (60%) + Frontier Quant Model (40%)
- Deviation from original AI+Technical spec is intentional: the Frontier Quant model integrates advanced technical + fundamental features and momentum/volatility context.
- Weighting philosophy (60/40) is preserved while upgrading the technical component to a more expressive quant layer.

## Sector/Company Fail‑Safes

- Sector crisis: pause boosts if sector 7‑day return < −10% (sector index/ETF proxy).
- Company crisis: pause boosts on earnings surprise < −20% or high‑severity negative news/scandal flags.
- Integrated into emergency safeguards alongside market crash checks.

## Sector‑Aware Confidence Adjustment

- After market regime adjustment, apply ±10% confidence scaling based on sector momentum vs 20‑DMA:
  - Sector vs 20‑DMA < −5% → −10% confidence
  - Sector vs 20‑DMA > +5% → +10% confidence
  - Otherwise neutral

## Volume Spike Detection Enhancement

- Correction confirmation now analyzes the entire decline window from recent high to current close.
- Uses max volume ratio over the decline window vs rolling 30‑day (fallback 10‑day) averages.
- Preserves and reports last‑day volume ratio for transparency, but confirmation relies on decline‑window spike.

## Risk Management Completeness

- Market crash guard (daily drop >5%).
- Sector crisis guard (7‑day sector fall >10%).
- Company crisis guard (earnings miss >20%, high‑severity news/scandal).
- Financial filters (D/E, current ratio, market cap, liquidity, beta, listing age).
- Technical confirmation (consolidation + reversal signals) prior to boost.

## Confidence Combination

- correction_confidence = 0.3×oversold + 0.3×fundamentals + 0.4×catalyst
- Market regime adjustments (bull/bear/VIX), then sector momentum adjustment.
- Boost tiers: Very High 20 / High 15 / Medium 10 / Low 5; score capped at 100 with high‑base limiter.

## Notes

- All yfinance fetches are wrapped with fail‑safes; on data gaps, adjustments default to neutral (no false positives).
- Integration retains existing outputs and adds sector context fields for transparency.
