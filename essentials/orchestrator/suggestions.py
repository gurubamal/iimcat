from __future__ import annotations

import csv
import glob
import os
from datetime import datetime
from typing import Dict, List, Tuple

from orchestrator.config import OUTPUTS_DIR, LEARNING_DIR


def _latest(pattern: str) -> str | None:
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return candidates[0]


def _load_csv(path: str) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return list(csv.DictReader(f))


def analyze_and_suggest() -> Tuple[str, Dict[str, object]]:
    """Analyze latest outputs and propose config/code suggestions.

    Returns path to suggestions markdown and a dict of proposed config tweaks.
    """
    # Find latest AI adjusted CSV and 30D top10 CSV
    ai_csv = _latest(os.path.join(OUTPUTS_DIR, "ai_adjusted_top*_.csv"))
    if ai_csv is None:
        # fallback: any ai_adjusted_top csv
        ai_csv = _latest(os.path.join(OUTPUTS_DIR, "ai_adjusted_top*.csv"))
    rank_csv = _latest(os.path.join(OUTPUTS_DIR, "top10_news_rank_*.csv"))

    rows: List[Dict[str, str]] = []
    if ai_csv and os.path.exists(ai_csv):
        try:
            rows = _load_csv(ai_csv)
        except Exception:
            rows = []

    # Metrics
    total = len(rows)
    live_updates = 0
    no_exact = 0
    dup_sum = 0
    apollo_funds = 0
    acc_dev = 0
    global_hcg = 0

    for r in rows:
        title = (r.get("top_title") or "").lower()
        source = (r.get("top_source") or "").lower()
        ticker = (r.get("ticker") or "").upper()
        has_word = (r.get("has_word") or "").lower() == "true"
        dups = int((r.get("dups") or 1) or 1)
        dup_sum += max(1, dups)
        if "live updates" in title or "share price live" in title:
            live_updates += 1
        if not has_word:
            no_exact += 1
        if ticker == "APOLLO" and "apollo fund" in title:
            apollo_funds += 1
        if ticker == "ACC" and ("dev accelerator" in title or "accelerator" in title):
            acc_dev += 1
        if ticker == "GLOBAL" and ("healthcare global" in title or "hcg" in title):
            global_hcg += 1

    suggestions: List[str] = []
    rec: Dict[str, object] = {"source_bonus": {}, "ticker_penalty": {}, "feature_weights": {}, "event_bonus": {}}

    # Suggest down-weight for live updates
    if total and (live_updates / total) > 0.25:
        suggestions.append(f"High share of 'live updates' ({live_updates}/{total}). Suggest down-weight live-update pages by -30%.")
        # encode as negative source bonus for economictimes live pages (soft recommendation)
        rec["source_bonus"]["economictimes.indiatimes.com"] = -0.01

    # Strengthen entity precision if many no-exact-ticker
    if total and (no_exact / total) > 0.2:
        suggestions.append(f"Many picks missing exact ticker in title ({no_exact}/{total}). Increase name penalty by -0.05.")
        rec["feature_weights"]["name_penalty_delta"] = -0.05  # custom key; orchestrator applies as decrease to name_factor_missing

    # Stronger dedup if duplicates often
    avg_dup = (dup_sum / total) if total else 1.0
    if avg_dup > 1.10:
        suggestions.append(f"Average duplicate factor {avg_dup:.2f}. Suggest increasing dedup exponent by +0.1.")
        rec["dedup_exponent_delta"] = +0.1

    # Entity disambiguation
    if apollo_funds:
        suggestions.append("APOLLO is lifted by 'Apollo Funds' headlines. Add entity mapping to exclude PE-fund-only context.")
    if acc_dev:
        suggestions.append("'ACC' matched 'Dev Accelerator'. Add entity mapping to ensure ACC Ltd only.")
    if global_hcg:
        suggestions.append("Ticker 'GLOBAL' likely Healthcare Global (HCG). Add mapping to HCG and ensure valid NSE tickers filter.")

    # Institutional cues importance (if block/bulk deals present, boost event_bonus)
    block_deal_hits = sum(1 for r in rows if "block deal" in (r.get("top_title") or "").lower())
    if block_deal_hits > 0:
        suggestions.append("Block deals observed. Consider a small positive event bonus for 'Block deal'.")
        rec["event_bonus"]["Block deal"] = 0.01

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_md = os.path.join(LEARNING_DIR, f"suggestions_{ts}.md")
    os.makedirs(LEARNING_DIR, exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("# Output Suggestions\n\n")
        f.write(f"Latest AI CSV: {os.path.basename(ai_csv) if ai_csv else 'n/a'}\n\n")
        if rank_csv:
            f.write(f"Latest 30D Rank CSV: {os.path.basename(rank_csv)}\n\n")
        if suggestions:
            f.write("## Suggested Fixes\n")
            for s in suggestions:
                f.write(f"- {s}\n")
        else:
            f.write("No major issues detected in latest outputs.\n")
    return out_md, rec

