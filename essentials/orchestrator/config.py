from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import glob
import ast


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
LEARNING_DIR = os.path.join(BASE_DIR, "learning")
CONFIGS_DIR = os.path.join(BASE_DIR, "configs")
AGGREGATES_DIR = os.path.join(OUTPUTS_DIR, "aggregates")
NEWS_RUNS_DIR = os.path.join(OUTPUTS_DIR, "news_runs")
RECOMMENDATIONS_DIR = os.path.join(OUTPUTS_DIR, "recommendations")


def _ensure_dirs() -> None:
    for d in (OUTPUTS_DIR, LEARNING_DIR, CONFIGS_DIR, AGGREGATES_DIR, NEWS_RUNS_DIR, RECOMMENDATIONS_DIR):
        try:
            os.makedirs(d, exist_ok=True)
        except Exception:
            pass


def load_config() -> Dict[str, Any]:
    """Load ranking config with sensible defaults and merge user overrides.
    Ensures new features (inst/circuits/profit growth) are enabled by default
    without requiring changes to an existing minimal ranking_config.json.
    """
    _ensure_dirs()
    defaults: Dict[str, Any] = {
        "dedup_exponent": 1.0,
        "name_factor_missing": 0.75,
        "name_factor_short_ticker": 0.6,
        "magnitude_cap": 0.5,
        "magnitude_log_divisor": 6.0,
        "source_bonus": {},
        "event_bonus": {},
        "ticker_penalty": {},
        "feature_weights": {
            "profit_growth": 0.05,
            "inst_cues": 0.03,
            "fii_dii_cues": 0.02,
            "circuit_lower": 0.01,
            "circuit_upper": 0.00,
        },
        "feature_caps": {
            "profit_growth_max": 0.10,
            "inst_cues_max": 0.05,
            "fii_dii_cues_max": 0.04,
            "circuit_abs_max": 0.02,
        },
    }

    cfg_path = os.path.join(BASE_DIR, "ranking_config.json")
    cfg_alt = os.path.join(CONFIGS_DIR, "ranking_config.json")
    path = cfg_path if os.path.exists(cfg_path) else cfg_alt
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                user = json.load(f) or {}
            # Shallow merge for top-level scalars
            for k, v in user.items():
                if k in ("source_bonus", "event_bonus", "ticker_penalty", "feature_weights", "feature_caps"):
                    # Merge nested dicts
                    base = defaults.get(k, {}) or {}
                    base.update(v or {})
                    defaults[k] = base
                else:
                    defaults[k] = v
        except Exception:
            pass

    # Merge latest recommendation (context-driven) if available
    # Can be disabled by setting env DISABLE_AUTO_RECOMMEND_APPLY=1
    if os.environ.get("DISABLE_AUTO_RECOMMEND_APPLY", "0") != "1":
        try:
            rec_glob = os.path.join(OUTPUTS_DIR, "ranking_config_recommendation_*.json")
            cand = sorted(glob.glob(rec_glob))
            if cand:
                latest = cand[-1]
                with open(latest, "r", encoding="utf-8") as f:
                    rec = json.load(f) or {}
                for k, v in rec.items():
                    if k in ("source_bonus", "event_bonus", "ticker_penalty", "feature_weights", "feature_caps"):
                        base = defaults.get(k, {}) or {}
                        base.update(v or {})
                        defaults[k] = base
                    else:
                        defaults[k] = v
        except Exception:
            pass

    # Attempt to parse learning_debate.md for ticker_penalty suggestions
    try:
        debate_path = os.path.join(LEARNING_DIR, "learning_debate.md")
        if os.path.exists(debate_path):
            with open(debate_path, "r", encoding="utf-8", errors="ignore") as f:
                txt = f.read()
            # Look for a line like: ticker_penalty: {'ABC': -0.05, ...}
            import re as _re
            m = _re.search(r"ticker_penalty:\s*(\{[^\}]*\})", txt)
            if m:
                try:
                    tp = ast.literal_eval(m.group(1))  # type: ignore[arg-type]
                    if isinstance(tp, dict):
                        base = defaults.get("ticker_penalty", {}) or {}
                        base.update(tp)
                        defaults["ticker_penalty"] = base
                except Exception:
                    pass
    except Exception:
        pass

    # Derive event_bonus from core priorities when not provided
    if not defaults.get("event_bonus"):
        try:
            priorities_path = os.path.join(LEARNING_DIR, "core_priorities.md")
            if os.path.exists(priorities_path):
                with open(priorities_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                # Find a line starting with 'Event priority:'
                pri_line: Optional[str] = None
                for line in lines:
                    if line.lower().strip().startswith("event priority:"):
                        pri_line = line
                        break
                if pri_line:
                    pri = pri_line.split(":", 1)[1]
                    # Split by comma and normalize
                    order = [p.strip().lower() for p in pri.split(",") if p.strip()]
                    # Map known keywords to our classifier labels
                    mapping = {
                        "ipo/listing": "IPO/listing",
                        "ipo": "IPO/listing",
                        "listing": "IPO/listing",
                        "m&a/jv": "M&A/JV",
                        "m&a": "M&A/JV",
                        "jv": "M&A/JV",
                        "large orders/contracts": "Order/contract",
                        "orders/contracts": "Order/contract",
                        "order": "Order/contract",
                        "contract": "Order/contract",
                        "approvals": "Regulatory",
                        "regulatory": "Regulatory",
                        "block/bulk deals": "Block deal",
                        "block deals": "Block deal",
                        "bulk deals": "Block deal",
                    }
                    weights: Dict[str, float] = {}
                    # Descending weights: first items get higher bonus
                    base_w = 0.06
                    step = 0.01
                    for idx, key in enumerate(order):
                        lab = mapping.get(key, None)
                        if not lab:
                            # attempt partial key match
                            for mk, mv in mapping.items():
                                if key.startswith(mk.split()[0]):
                                    lab = mv
                                    break
                        if lab:
                            weights[lab] = max(0.0, base_w - step * idx)
                    if weights:
                        base = defaults.get("event_bonus", {}) or {}
                        base.update(weights)
                        defaults["event_bonus"] = base
        except Exception:
            pass
    return defaults


def load_entities() -> Dict[str, Any]:
    """Load entities mapping for disambiguation (require/include/exclude phrases)."""
    _ensure_dirs()
    ent_path = os.path.join(CONFIGS_DIR, "entities.json")
    # Fall back to base configs/entities.json
    base_ent = os.path.join(BASE_DIR, "configs", "entities.json")
    path = ent_path if os.path.exists(ent_path) else base_ent
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception:
        return {}
