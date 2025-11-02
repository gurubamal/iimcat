#!/usr/bin/env python3
"""
Lightweight feedback calibrator for EXIT AI config.

- Reads ai_feedback_simulation.json if present. Expected minimal schema:
  {
    "asof": "2025-10-30T14:30:00",
    "entries": [
      {"ticker": "SAGILITY", "initial_action": "BUY", "change_pct": -2.65},
      {"ticker": "WORTH",    "initial_action": "BUY", "change_pct":  3.46},
      {"ticker": "BHEL",     "initial_action": "BUY", "change_pct": -1.45}
    ]
  }

- Computes simple success score (directional hit) and nudges EXIT weights and thresholds.
  This is a pragmatic stepping stone until full attribution/backtesting.

Outputs: exit_ai_config.json with fields:
  {
    "weights": {"tech": 0.45, "news": 0.25, "fund": 0.20, "liquidity": 0.10},
    "bands": {"STRONG_EXIT": 90, "EXIT": 70, "MONITOR": 50, "HOLD": 30}
  }
"""

from __future__ import annotations
import json, os, sys
from pathlib import Path
from typing import Dict, Any

CONFIG_PATH = Path('exit_ai_config.json')
SIM_PATH = Path('ai_feedback_simulation.json')

DEFAULT_WEIGHTS = {"tech": 0.45, "news": 0.25, "fund": 0.20, "liquidity": 0.10}
DEFAULT_BANDS = {"STRONG_EXIT": 90, "EXIT": 70, "MONITOR": 50, "HOLD": 30}

def _load_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text())
        except Exception:
            pass
    return {"weights": DEFAULT_WEIGHTS.copy(), "bands": DEFAULT_BANDS.copy()}

def _save_config(cfg: Dict[str, Any]) -> None:
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2, sort_keys=True))
        print(f"✅ Updated {CONFIG_PATH}")
    except Exception as e:
        print(f"⚠️  Failed to write {CONFIG_PATH}: {e}", file=sys.stderr)

def _normalize_weights(w: Dict[str, float]) -> Dict[str, float]:
    # Clamp each weight to [0.05, 0.8] and renormalize to 1.0
    clamped = {k: max(0.05, min(0.8, float(v))) for k, v in w.items()}
    s = sum(clamped.values()) or 1.0
    return {k: v / s for k, v in clamped.items()}

def main() -> int:
    cfg = _load_config()
    weights = cfg.get('weights', DEFAULT_WEIGHTS).copy()
    bands = cfg.get('bands', DEFAULT_BANDS).copy()

    # No simulation file -> noop (keep config as-is).
    if not SIM_PATH.exists():
        print("ℹ️  No ai_feedback_simulation.json found; keeping existing EXIT AI config.")
        _save_config({"weights": _normalize_weights(weights), "bands": bands})
        return 0

    try:
        sim = json.loads(SIM_PATH.read_text())
        entries = sim.get('entries') or []
        if not entries:
            print("ℹ️  Empty feedback entries; no changes.")
            _save_config({"weights": _normalize_weights(weights), "bands": bands})
            return 0
    except Exception as e:
        print(f"⚠️  Failed to parse {SIM_PATH}: {e}", file=sys.stderr)
        return 1

    # Directional success: BUY expects +, SELL expects -, HOLD expects |chg| <= band
    band = float(os.getenv('EXIT_HOLD_BAND_PCT', '1.5'))  # +/- band in percent (default 1.5%)
    hits = 0
    misses = 0
    for e in entries:
        act = str(e.get('initial_action', '')).upper()
        chg = float(e.get('change_pct', 0.0))
        if act in ("BUY",):
            if chg > 0: hits += 1
            elif chg < 0: misses += 1
        elif act in ("SELL", "EXIT", "IMMEDIATE_EXIT"):
            if chg < 0: hits += 1
            elif chg > 0: misses += 1
        else:  # HOLD/MONITOR
            if abs(chg) <= band:
                hits += 1
            else:
                misses += 1

    total = max(1, hits + misses)
    hit_rate = hits / total
    print(f"📈 Feedback: hits={hits}, misses={misses}, hit_rate={hit_rate:.2f}")

    # Nudge weights: if hit_rate < 0.5, emphasize tech and liquidity (execution discipline),
    # otherwise emphasize fund and news (signals working). Small steps to avoid thrash.
    step_good = 0.03
    step_bad = 0.03

    if hit_rate < 0.5:
        weights['tech'] = weights.get('tech', 0.45) + step_bad
        weights['liquidity'] = weights.get('liquidity', 0.10) + 0.01
        # Be more conservative on exits: raise EXIT threshold slightly
        bands['EXIT'] = int(min(95, bands.get('EXIT', 70) + 2))
        bands['STRONG_EXIT'] = int(min(99, bands.get('STRONG_EXIT', 90) + 1))
        # Trim news/fund lightly
        weights['news'] = weights.get('news', 0.25) - 0.02
        weights['fund'] = weights.get('fund', 0.20) - 0.02
    else:
        # Signals working: give more credence to fundamentals/news
        weights['fund'] = weights.get('fund', 0.20) + step_good
        weights['news'] = weights.get('news', 0.25) + 0.01
        # Allow slightly easier exits (responsive)
        bands['EXIT'] = int(max(50, bands.get('EXIT', 70) - 2))
        # Keep strong exit band stable to avoid over-aggression
        weights['tech'] = weights.get('tech', 0.45) - 0.02
        weights['liquidity'] = weights.get('liquidity', 0.10) - 0.01

    weights = _normalize_weights(weights)
    _save_config({"weights": weights, "bands": bands})
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
