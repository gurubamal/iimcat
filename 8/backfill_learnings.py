#!/usr/bin/env python3
from __future__ import annotations

"""
Backfill learnings from recent aggregated full-article files.

- Finds aggregated_full_articles_*.txt in current folder, sorted by mtime (newest first).
- For each file within the time window, runs screen_full_articles.py to build CSV,
  applies AI Path re-ranking, updates learning DB/context, runs debate + recommendations,
  and evaluates post-news price reactions (1d/3d/5d) when network is available.

Usage:
  python backfill_learnings.py --days 7 --top 100 --apply-config
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, os.pardir))

sys.path.insert(0, BASE_DIR)

import learning_db  # type: ignore
import price_eval   # type: ignore
import run_swing_paths as rsp  # type: ignore
from orchestrator.config import OUTPUTS_DIR, LEARNING_DIR, BASE_DIR, AGGREGATES_DIR
from orchestrator.organize import organize_workspace


def find_aggregated(max_days: int) -> list[str]:
    cut = datetime.now().timestamp() - (max_days * 86400)
    out: list[tuple[float, str]] = []
    for root in (BASE_DIR, AGGREGATES_DIR):
        try:
            for name in os.listdir(root):
                if name.startswith("aggregated_full_articles_") and name.endswith(".txt"):
                    p = os.path.join(root, name)
                    try:
                        mt = os.path.getmtime(p)
                        if mt >= cut:
                            out.append((mt, p))
                    except Exception:
                        continue
        except Exception:
            pass
    out.sort(reverse=True)
    return [p for _, p in out]


def run_screen(agg_path: str, top: int) -> str:
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    csv_path = os.path.join(OUTPUTS_DIR, f"all_news_screen_{os.path.basename(agg_path)}.csv")
    cmd = [
        sys.executable,
        os.path.join(ROOT_DIR, "screen_full_articles.py"),
        "--input", agg_path,
        "--top", str(max(25, top * 2)),
        "--export", csv_path,
    ]
    print(f"[screen] {os.path.basename(agg_path)} → {os.path.basename(csv_path)}")
    import subprocess
    subprocess.run(cmd, check=True)
    return csv_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Backfill learnings from aggregated news")
    ap.add_argument("--days", type=int, default=7, help="How many days back to scan aggregated files")
    ap.add_argument("--top", type=int, default=100, help="Top N (AI) to persist per aggregated file")
    ap.add_argument("--apply-config", action="store_true", help="Apply recommended ranking_config.json after each run")
    args = ap.parse_args()

    agg_files = find_aggregated(args.days)
    if not agg_files:
        print("[warn] No aggregated_full_articles_* files found in window.")
        sys.exit(0)

    os.makedirs(LEARNING_DIR, exist_ok=True)
    db_path = os.path.join(LEARNING_DIR, "learning.db")
    learning_db.ensure_db(db_path)

    # Organize workspace before backfill
    try:
        moved, _ = organize_workspace(BASE_DIR)
        if moved:
            print(f"[organize] Moved {moved} base items into organized folders.")
    except Exception:
        pass

    for i, agg in enumerate(agg_files, 1):
        print(f"\n=== [{i}/{len(agg_files)}] {os.path.basename(agg)} ===")
        try:
            csv_path = run_screen(agg, args.top)
        except Exception as e:
            print(f"[skip] screen failed: {e}")
            continue

        # AI path rank
        try:
            top_rows, _ = rsp.ai_adjust_rank(csv_path, top_n=args.top)
        except Exception as e:
            print(f"[skip] ai_adjust_rank failed: {e}")
            continue

        # Persist run + picks
        run_id = learning_db.update_from_ai_results(db_path, top_rows, agg)
        learning_md = os.path.join(LEARNING_DIR, "learning_context.md")
        learning_db.generate_context_update(db_path, learning_md, run_id)

        # Debate + recommendations
        debate_md = os.path.join(LEARNING_DIR, "learning_debate.md")
        rec_json = os.path.join(OUTPUTS_DIR, f"ranking_config_recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        learning_db.generate_debate_and_recommendations(db_path, run_id, debate_md, rec_json)
        print(f"[learn] Context + debate updated. Proposed config: {os.path.basename(rec_json)}")
        if args.apply_config:
            try:
                shutil.copyfile(rec_json, os.path.join(BASE_DIR, "ranking_config.json"))
                print("[learn] Applied proposed ranking_config.json")
            except Exception as e:
                print(f"[warn] Could not apply config: {e}")

        # Price evaluation
        print("[price] Evaluating 1d/3d/5d reactions…")
        evals = price_eval.evaluate_reactions(top_rows, agg)
        if not evals:
            print("[price] No data or network blocked; skipping.")
            continue
        import sqlite3
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            for e in evals:
                cur.execute(
                    """
                    INSERT OR REPLACE INTO price_eval (run_id, ticker, event_ts, event_type, title, source, ret_1d, ret_3d, ret_5d, consistent, fake)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (run_id, e['ticker'], e['event_ts'], e.get('event_type') or '', e.get('title') or '', e.get('source') or '',
                     float(e.get('ret_1d') or 0.0), float(e.get('ret_3d') or 0.0), float(e.get('ret_5d') or 0.0), int(e.get('consistent') or 0), int(e.get('fake') or 0))
                )
                # Update ticker reliability
                cur.execute("SELECT success_2p, fake_rise_cnt, appearances FROM ticker_stats WHERE ticker=?", (e['ticker'],))
                row = cur.fetchone()
                succ = int(row[0] or 0) if row else 0
                fake = int(row[1] or 0) if row else 0
                apps = int(row[2] or 0) if row else 0
                succ += int(e.get('consistent') or 0)
                fake += int(e.get('fake') or 0)
                rel = (succ - 1.25 * fake) / float(max(1, apps))
                cur.execute("UPDATE ticker_stats SET success_2p=?, fake_rise_cnt=?, reliability_score=? WHERE ticker=?", (succ, fake, rel, e['ticker']))
            con.commit()
            con.close()
            print(f"[price] Saved {len(evals)} evals; reliability updated.")
        except Exception as e:
            print(f"[warn] Price persistence failed: {e}")

    print("\nBackfill completed. See learning_context.md and learning_debate.md for summaries.")


if __name__ == "__main__":
    main()
