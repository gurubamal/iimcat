## Debate & Recommendations — Run 1 (2025-09-13T13:07:28)

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 24.0% (target < 25%)
- Avg duplication factor: 1.24 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.08
- Event distribution (latest): General:13, Order/contract:5, IPO/listing:3, Results/metrics:1, Management:1, M&A/JV:1, Dividend/return:1

Recommendations for next run (config deltas):
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.24; strengthen 1/dups^alpha to reduce duplication bias.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 2 (2025-09-13T13:34:46)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=1
- HINDALCO: successes=0, fake_rises=1
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=1
- BEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 24.0% (target < 25%)
- Avg duplication factor: 1.24 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.07
- Event distribution (latest): General:13, Order/contract:5, IPO/listing:3, Results/metrics:1, Management:1, M&A/JV:1, Dividend/return:1

Recommendations for next run (config deltas):
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.24; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 3 (2025-09-13T13:46:25)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=1
- HINDALCO: successes=0, fake_rises=1
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=1
- BEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 24.0% (target < 25%)
- Avg duplication factor: 1.24 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.07
- Event distribution (latest): General:13, Order/contract:5, IPO/listing:3, Results/metrics:1, Management:1, M&A/JV:1, Dividend/return:1

Recommendations for next run (config deltas):
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.24; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 4 (2025-09-13T15:31:42)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=1
- HINDALCO: successes=0, fake_rises=1
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=1
- BEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 24.0% (target < 25%)
- Avg duplication factor: 1.24 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.00
- Event distribution (latest): General:14, Order/contract:5, IPO/listing:2, Results/metrics:1, Management:1, M&A/JV:1, Dividend/return:1

Recommendations for next run (config deltas):
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.24; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 5 (2025-09-13T15:59:28)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=1
- HINDALCO: successes=0, fake_rises=1
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=1
- BEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 24.0% (target < 25%)
- Avg duplication factor: 1.24 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.00
- Event distribution (latest): General:14, Order/contract:5, IPO/listing:2, Results/metrics:1, Management:1, M&A/JV:1, Dividend/return:1

Recommendations for next run (config deltas):
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.24; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 6 (2025-09-14T23:57:03)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 24.0% (target < 25%)
- Avg duplication factor: 1.16 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.00
- Event distribution (latest): General:14, Order/contract:4, IPO/listing:3, Results/metrics:1, Management:1, M&A/JV:1, Dividend/return:1

Recommendations for next run (config deltas):
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.16; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 7 (2025-09-15T01:51:10)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 24.0% (target < 25%)
- Avg duplication factor: 1.16 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.02
- Event distribution (latest): General:14, Order/contract:4, IPO/listing:3, Results/metrics:1, Management:1, M&A/JV:1, Dividend/return:1

Recommendations for next run (config deltas):
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.16; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 8 (2025-09-15T16:17:20)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:1

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 9 (2025-09-16T01:47:11)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:1

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 10 (2025-09-16T10:34:27)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:1

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 11 (2025-09-16T10:41:08)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:1

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 12 (2025-09-16T14:48:08)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:1

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 13 (2025-09-16T14:50:52)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:1

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 14 (2025-09-17T01:10:05)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:1

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 15 (2025-09-17T14:28:56)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 16 (2025-09-17T14:50:56)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 17 (2025-09-17T18:52:32)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 18 (2025-09-18T09:20:07)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 19 (2025-09-18T13:50:32)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 20 (2025-09-18T20:50:53)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 21 (2025-09-21T23:52:36)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 22 (2025-09-22T09:00:35)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 23 (2025-09-22T14:50:05)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 24 (2025-09-22T14:51:33)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 25 (2025-09-22T15:00:51)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 26 (2025-09-22T23:30:24)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 27 (2025-09-22T23:30:58)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 28 (2025-09-23T08:13:54)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 0.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 29 (2025-09-23T10:32:58)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 24.0% (target < 25%)
- Avg duplication factor: 1.36 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.03
- Event distribution (latest): General:18, Order/contract:2, Management:2, IPO/listing:2, Results/metrics:1

Recommendations for next run (config deltas):
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.36; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 30 (2025-09-23T14:13:19)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 24.0% (target < 25%)
- Avg duplication factor: 1.36 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.03
- Event distribution (latest): General:18, Order/contract:2, Management:2, IPO/listing:2, Results/metrics:1

Recommendations for next run (config deltas):
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.36; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 31 (2025-09-23T23:53:13)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 24.0% (target < 25%)
- Avg duplication factor: 1.36 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.03
- Event distribution (latest): General:18, Order/contract:2, Management:2, IPO/listing:2, Results/metrics:1

Recommendations for next run (config deltas):
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.36; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 32 (2025-09-24T08:37:17)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 28.6% (target < 25%)
- Avg duplication factor: 1.40 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.05
- Event distribution (latest): General:27, IPO/listing:3, Order/contract:2, Management:2, Results/metrics:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 28.6% of picks; increase penalty to force entity precision.
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.40; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 33 (2025-09-24T10:24:42)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 28.6% (target < 25%)
- Avg duplication factor: 1.40 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: -0.05
- Event distribution (latest): General:27, IPO/listing:3, Order/contract:2, Management:2, Results/metrics:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 28.6% of picks; increase penalty to force entity precision.
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.40; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 34 (2025-09-25T00:18:20)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 50.0% (target < 25%)
- Avg duplication factor: 1.27 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.10
- Event distribution (latest): General:32, Order/contract:5, Results/metrics:3, M&A/JV:2, IPO/listing:2

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 50.0% of picks; increase penalty to force entity precision.
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.27; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 35 (2025-09-26T13:29:45)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 50.0% (target < 25%)
- Avg duplication factor: 1.27 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.10
- Event distribution (latest): General:32, Order/contract:5, Results/metrics:3, M&A/JV:2, IPO/listing:2

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 50.0% of picks; increase penalty to force entity precision.
- dedup_exponent: delta 0.1 (bounds: -inf..2.0) — Avg duplicate factor 1.27; strengthen 1/dups^alpha to reduce duplication bias.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 36 (2025-10-14T01:28:17)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 64.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.02
- Event distribution (latest): General:38, Results/metrics:4, Dividend/return:3, Order/contract:2, M&A/JV:2, Management:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 64.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 37 (2025-10-14T16:41:01)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 64.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.02
- Event distribution (latest): General:38, Results/metrics:4, Dividend/return:3, Order/contract:2, M&A/JV:2, Management:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 64.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 38 (2025-10-14T16:41:05)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 64.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.02
- Event distribution (latest): General:38, Results/metrics:4, Dividend/return:3, Order/contract:2, M&A/JV:2, Management:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 64.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 39 (2025-10-14T22:11:58)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 64.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.02
- Event distribution (latest): General:38, Results/metrics:4, Dividend/return:3, Order/contract:2, M&A/JV:2, Management:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 64.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 40 (2025-10-15T02:48:09)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 64.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.02
- Event distribution (latest): General:38, Results/metrics:4, Dividend/return:3, Order/contract:2, M&A/JV:2, Management:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 64.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 41 (2025-10-15T12:29:25)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 70.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.88
- Event distribution (latest): General:30, Results/metrics:10, Management:3, Regulatory:2, Order/contract:2, M&A/JV:2, IPO/listing:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 70.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 42 (2025-10-16T23:19:42)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 70.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.88
- Event distribution (latest): General:30, Results/metrics:10, Management:3, Regulatory:2, Order/contract:2, M&A/JV:2, IPO/listing:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 70.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 43 (2025-10-17T00:12:48)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 54.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.80
- Event distribution (latest): General:27, Results/metrics:18, M&A/JV:3, Management:1, Dividend/return:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 54.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 44 (2025-10-17T13:11:55)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 54.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.80
- Event distribution (latest): General:27, Results/metrics:18, M&A/JV:3, Management:1, Dividend/return:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 54.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 45 (2025-10-18T17:42:38)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2
- EXCEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 54.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.80
- Event distribution (latest): General:27, Results/metrics:18, M&A/JV:3, Management:1, Dividend/return:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 54.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05, 'EXCEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 46 (2025-10-19T00:24:25)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2
- EXCEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 70.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.26
- Event distribution (latest): General:32, Results/metrics:15, M&A/JV:2, Order/contract:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 70.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05, 'EXCEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 47 (2025-10-20T01:54:44)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2
- EXCEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 70.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.26
- Event distribution (latest): General:32, Results/metrics:15, M&A/JV:2, Order/contract:1

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 70.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05, 'EXCEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 48 (2025-10-21T00:13:53)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2
- EXCEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 78.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.14
- Event distribution (latest): General:26, Results/metrics:11, Order/contract:4

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 78.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05, 'EXCEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 49 (2025-10-21T15:45:55)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2
- EXCEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 78.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.14
- Event distribution (latest): General:26, Results/metrics:11, Order/contract:4

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 78.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05, 'EXCEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 50 (2025-10-22T03:34:18)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2
- EXCEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 78.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 0.14
- Event distribution (latest): General:26, Results/metrics:11, Order/contract:4

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 78.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05, 'EXCEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 51 (2025-10-26T15:13:57)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2
- EXCEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 50.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 1.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 50.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05, 'EXCEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 52 (2025-10-26T15:15:46)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2
- EXCEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 50.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 1.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 50.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05, 'EXCEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 53 (2025-10-26T15:22:16)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2
- EXCEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 50.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 1.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 50.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05, 'EXCEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

## Debate & Recommendations — Run 54 (2025-10-26T15:25:13)

Unreliable tickers (fake rises > successes):
- RETAIL: successes=0, fake_rises=2
- HINDALCO: successes=0, fake_rises=2
- APOLLO: successes=0, fake_rises=1
- WEL: successes=0, fake_rises=2
- BEL: successes=0, fake_rises=2
- EXCEL: successes=0, fake_rises=1

This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.

Key observations:
- No-exact-ticker ratio: 50.0% (target < 25%)
- Avg duplication factor: 1.00 (target <= 1.10)
- Median magnitude: ~₹0.0 Cr; correlation with score proxy: 1.00
- Event distribution (latest): General:2

Recommendations for next run (config deltas):
- name_factor_missing: delta -0.05 (bounds: 0.5..inf) — No exact ticker in 50.0% of picks; increase penalty to force entity precision.
- ticker_penalty: {'RETAIL': -0.05, 'HINDALCO': -0.05, 'APOLLO': -0.05, 'WEL': -0.05, 'BEL': -0.05, 'EXCEL': -0.05} — Flagged as unreliable (fake rises exceeded successes). Apply small penalties.

Implementation notes:
- name_factor_missing: increases penalty when ticker not in title; improves entity precision.
- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.
- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.
- source_bonus: tiny multipliers to reflect source reliability; remains conservative.

