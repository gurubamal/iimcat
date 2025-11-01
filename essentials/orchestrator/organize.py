from __future__ import annotations

import os
import shutil
import time
from typing import List, Tuple

from orchestrator.config import (
    OUTPUTS_DIR,
    AGGREGATES_DIR,
    NEWS_RUNS_DIR,
    RECOMMENDATIONS_DIR,
    LEARNING_DIR,
)


def _safe_mkdir(p: str) -> None:
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass


def _move(src: str, dst_dir: str) -> bool:
    try:
        _safe_mkdir(dst_dir)
        base = os.path.basename(src)
        dst = os.path.join(dst_dir, base)
        # If exists, add timestamp suffix
        if os.path.exists(dst):
            name, ext = os.path.splitext(base)
            ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            dst = os.path.join(dst_dir, f"{name}_{ts}{ext}")
        shutil.move(src, dst)
        return True
    except Exception:
        return False


def organize_workspace(base_dir: str) -> Tuple[int, List[str]]:
    """Move stray outputs into organized folders without breaking code.

    - aggregated_full_articles_*.txt → outputs/aggregates/
    - aggregated_nifty50_* → outputs/aggregates/
    - ranking_config_recommendation_*.json → outputs/recommendations/
    - full_articles_run_* (dirs) → outputs/news_runs/
    - all_news_screen.csv in base → outputs/
    - swing_top*.txt, ai_adjusted_top*.csv, tickers_news_top*.txt → outputs/
    """
    moved = 0
    details: List[str] = []

    try:
        entries = os.listdir(base_dir)
    except OSError:
        return 0, []

    # File patterns
    for name in entries:
        p = os.path.join(base_dir, name)
        try:
            if os.path.isdir(p):
                # Move news run folders
                if name.startswith("full_articles_run_"):
                    if _move(p, NEWS_RUNS_DIR):
                        moved += 1; details.append(f"dir→news_runs: {name}")
                continue

            lname = name.lower()
            # Aggregates
            if name.startswith("aggregated_full_articles_") and lname.endswith(".txt"):
                if _move(p, AGGREGATES_DIR):
                    moved += 1; details.append(f"agg→aggregates: {name}")
                continue
            if name.startswith("aggregated_nifty50_"):
                if _move(p, AGGREGATES_DIR):
                    moved += 1; details.append(f"nifty→aggregates: {name}")
                continue
            # Recommendations
            if name.startswith("ranking_config_recommendation_") and lname.endswith(".json"):
                if _move(p, RECOMMENDATIONS_DIR):
                    moved += 1; details.append(f"rec→recommendations: {name}")
                continue
            # Outputs common
            if name in ("all_news_screen.csv",) or \
               name.startswith("all_news_screen_") or \
               name.startswith("adjusted_news_top") or \
               name.startswith("ai_adjusted_top") or \
               name.startswith("swing_top") or \
               name.startswith("tickers_news_top"):
                if _move(p, OUTPUTS_DIR):
                    moved += 1; details.append(f"out→outputs: {name}")
                continue
            # Learning artifacts accidentally in base
            if name in ("learning.db", "learning_context.md", "learning_debate.md") or \
               name.startswith("suggestions_"):
                if _move(p, LEARNING_DIR):
                    moved += 1; details.append(f"learn→learning: {name}")
                continue
        except Exception:
            continue

    return moved, details
