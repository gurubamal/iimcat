#!/usr/bin/env python3
"""
Local Learning DB for AI Path

Stores structured data from each AI-path run to a SQLite database and writes a
human-readable learning_context.md with summarized insights.
"""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def ensure_db(db_path: str) -> None:
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY,
                ts TEXT,
                agg_file TEXT,
                path TEXT,
                top_n INTEGER,
                notes TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS picks (
                run_id INTEGER,
                rank INTEGER,
                ticker TEXT,
                adj_score REAL,
                combined_score REAL,
                articles INTEGER,
                title TEXT,
                source TEXT,
                reason TEXT,
                amt_cr REAL,
                dups INTEGER,
                has_word INTEGER,
                event_type TEXT,
                FOREIGN KEY(run_id) REFERENCES runs(id)
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS ix_picks_ticker ON picks(ticker)")
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ticker_stats (
                ticker TEXT PRIMARY KEY,
                appearances INTEGER DEFAULT 0,
                last_seen TEXT,
                avg_adj REAL DEFAULT 0.0,
                last_adj REAL DEFAULT 0.0,
                best_adj REAL DEFAULT 0.0,
                best_title TEXT,
                best_reason TEXT,
                best_source TEXT,
                total_articles INTEGER DEFAULT 0,
                sum_amt_cr REAL DEFAULT 0.0,
                success_2p INTEGER DEFAULT 0,
                fake_rise_cnt INTEGER DEFAULT 0,
                reliability_score REAL DEFAULT 0.0
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ticker_event_counts (
                ticker TEXT,
                event_type TEXT,
                cnt INTEGER DEFAULT 0,
                last_seen TEXT,
                PRIMARY KEY(ticker, event_type)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS source_stats (
                source TEXT PRIMARY KEY,
                cnt INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0.0,
                last_seen TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS event_stats (
                event_type TEXT PRIMARY KEY,
                cnt INTEGER DEFAULT 0,
                avg_score REAL DEFAULT 0.0,
                avg_amt_cr REAL DEFAULT 0.0,
                success_2p INTEGER DEFAULT 0,
                fake_rise_cnt INTEGER DEFAULT 0,
                last_seen TEXT
            )
            """
        )
        # Price evaluation table
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS price_eval (
                run_id INTEGER,
                ticker TEXT,
                event_ts TEXT,
                event_type TEXT,
                title TEXT,
                source TEXT,
                ret_1d REAL,
                ret_3d REAL,
                ret_5d REAL,
                consistent INTEGER,
                fake INTEGER,
                PRIMARY KEY (run_id, ticker, event_ts)
            )
            """
        )
        # Live feedback table capturing present-day returns and trust
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS live_feedback (
                run_id INTEGER,
                asof TEXT,
                ticker TEXT,
                price REAL,
                prev_close REAL,
                live_ret REAL,
                source TEXT,
                event_type TEXT,
                title TEXT,
                news_certainty REAL,
                trust_score REAL,
                PRIMARY KEY (run_id, ticker, asof)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS decision_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                ticker TEXT,
                verdict TEXT,
                expected_return REAL,
                actual_return REAL,
                rating REAL,
                confidence REAL,
                notes TEXT,
                event_ts TEXT,
                created TEXT,
                UNIQUE(run_id, ticker, event_ts)
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS assistant_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER,
                assistant TEXT,
                status TEXT,
                command TEXT,
                response TEXT,
                error TEXT,
                created TEXT
            )
            """
        )
        # Attempt to add new columns to existing tables (schema migration light)
        for alter in [
            "ALTER TABLE ticker_stats ADD COLUMN success_2p INTEGER DEFAULT 0",
            "ALTER TABLE ticker_stats ADD COLUMN fake_rise_cnt INTEGER DEFAULT 0",
            "ALTER TABLE ticker_stats ADD COLUMN reliability_score REAL DEFAULT 0.0",
            "ALTER TABLE event_stats ADD COLUMN success_2p INTEGER DEFAULT 0",
            "ALTER TABLE event_stats ADD COLUMN fake_rise_cnt INTEGER DEFAULT 0",
            "ALTER TABLE decision_feedback ADD COLUMN event_ts TEXT"
        ]:
            try:
                cur.execute(alter)
            except Exception:
                pass
        try:
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_decision_feedback_unique ON decision_feedback(run_id, ticker, event_ts)")
        except Exception:
            pass
        try:
            cur.execute("CREATE INDEX IF NOT EXISTS ix_assistant_feedback_run ON assistant_feedback(run_id)")
        except Exception:
            pass
        con.commit()
    finally:
        con.close()

def save_live_feedback(db_path: str, run_id: int, rows: List[Dict[str, object]]) -> None:
    """Persist live feedback rows into SQLite live_feedback table."""
    if not rows or run_id is None or run_id < 0:
        return
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        for r in rows:
            cur.execute(
                """
                INSERT OR REPLACE INTO live_feedback
                (run_id, asof, ticker, price, prev_close, live_ret, source, event_type, title, news_certainty, trust_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    str(r.get("asof") or ""),
                    (str(r.get("ticker") or "").upper()),
                    float(r.get("price") or 0.0),
                    float(r.get("prev_close") or 0.0),
                    float(r.get("live_ret") or 0.0),
                    str(r.get("source") or ""),
                    str(r.get("event_type") or ""),
                    str(r.get("title") or ""),
                    float(r.get("news_certainty") or 0.0),
                    float(r.get("trust_score") or 0.0),
                ),
            )
        con.commit()
    finally:
        con.close()


def classify_event(title: str) -> str:
    t = (title or "").lower()
    if re.search(r"\bipo\b|listing|fpo|qip|rights issue", t):
        return "IPO/listing"
    if re.search(r"acquisit|merger|buyout|joint venture|\bjv\b|stake (?:buy|sale)", t):
        return "M&A/JV"
    if re.search(r"order\b|contract\b|tender|project|deal", t):
        return "Order/contract"
    if re.search(r"approval|usfda|sebi|nod|clearance|regulator", t):
        return "Regulatory"
    if re.search(r"block deal", t):
        return "Block deal"
    if re.search(r"dividend|buyback|payout", t):
        return "Dividend/return"
    if re.search(r"result|profit|ebitda|margin|q[1-4]|quarter|yoy|growth", t):
        return "Results/metrics"
    if re.search(r"appoints|resigns|ceo|cfo", t):
        return "Management"
    return "General"


def _upsert_ticker_stats(cur: sqlite3.Cursor, ticker: str, adj: float, title: str, reason: str, source: str, articles: int, amt_cr: float, ts: str) -> None:
    # Fetch existing
    cur.execute("SELECT appearances, avg_adj, best_adj, total_articles, sum_amt_cr FROM ticker_stats WHERE ticker=?", (ticker,))
    row = cur.fetchone()
    if row is None:
        appearances = 0
        avg_adj = 0.0
        best_adj = 0.0
        total_articles = 0
        sum_amt_cr = 0.0
    else:
        appearances, avg_adj, best_adj, total_articles, sum_amt_cr = row
    new_apps = appearances + 1
    new_avg = ((avg_adj * appearances) + adj) / new_apps if new_apps > 0 else adj
    new_best = max(best_adj, adj)
    total_articles = int(total_articles or 0) + int(articles or 0)
    sum_amt_cr = float(sum_amt_cr or 0.0) + float(amt_cr or 0.0)
    cur.execute(
        """
        INSERT INTO ticker_stats (ticker, appearances, last_seen, avg_adj, last_adj, best_adj, best_title, best_reason, best_source, total_articles, sum_amt_cr)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker) DO UPDATE SET
            appearances=excluded.appearances,
            last_seen=excluded.last_seen,
            avg_adj=excluded.avg_adj,
            last_adj=excluded.last_adj,
            best_adj=CASE WHEN excluded.best_adj > ticker_stats.best_adj THEN excluded.best_adj ELSE ticker_stats.best_adj END,
            best_title=CASE WHEN excluded.best_adj > ticker_stats.best_adj THEN excluded.best_title ELSE ticker_stats.best_title END,
            best_reason=CASE WHEN excluded.best_adj > ticker_stats.best_adj THEN excluded.best_reason ELSE ticker_stats.best_reason END,
            best_source=CASE WHEN excluded.best_adj > ticker_stats.best_adj THEN excluded.best_source ELSE ticker_stats.best_source END,
            total_articles=excluded.total_articles,
            sum_amt_cr=excluded.sum_amt_cr
        """,
        (ticker, new_apps, ts, new_avg, adj, adj, title, reason, source, total_articles, sum_amt_cr),
    )


def _upsert_ticker_event(cur: sqlite3.Cursor, ticker: str, event: str, ts: str) -> None:
    cur.execute(
        """
        INSERT INTO ticker_event_counts (ticker, event_type, cnt, last_seen)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(ticker, event_type) DO UPDATE SET
            cnt = ticker_event_counts.cnt + 1,
            last_seen = excluded.last_seen
        """,
        (ticker, event, ts),
    )


def _upsert_source(cur: sqlite3.Cursor, source: str, adj: float, ts: str) -> None:
    if not source:
        return
    cur.execute("SELECT cnt, avg_score FROM source_stats WHERE source=?", (source,))
    row = cur.fetchone()
    if row is None:
        cnt = 0
        avg = 0.0
    else:
        cnt, avg = row
    new_cnt = cnt + 1
    new_avg = ((avg * cnt) + adj) / new_cnt if new_cnt > 0 else adj
    cur.execute(
        """
        INSERT INTO source_stats (source, cnt, avg_score, last_seen)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(source) DO UPDATE SET
            cnt=excluded.cnt,
            avg_score=excluded.avg_score,
            last_seen=excluded.last_seen
        """,
        (source, new_cnt, new_avg, ts),
    )


def _upsert_event(cur: sqlite3.Cursor, event: str, adj: float, amt_cr: float, ts: str) -> None:
    cur.execute("SELECT cnt, avg_score, avg_amt_cr FROM event_stats WHERE event_type=?", (event,))
    row = cur.fetchone()
    if row is None:
        cnt = 0
        avg = 0.0
        avg_amt = 0.0
    else:
        cnt, avg, avg_amt = row
    new_cnt = cnt + 1
    new_avg = ((avg * cnt) + adj) / new_cnt if new_cnt > 0 else adj
    new_avg_amt = ((avg_amt * cnt) + (amt_cr or 0.0)) / new_cnt if new_cnt > 0 else (amt_cr or 0.0)
    cur.execute(
        """
        INSERT INTO event_stats (event_type, cnt, avg_score, avg_amt_cr, last_seen)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(event_type) DO UPDATE SET
            cnt=excluded.cnt,
            avg_score=excluded.avg_score,
            avg_amt_cr=excluded.avg_amt_cr,
            last_seen=excluded.last_seen
        """,
        (event, new_cnt, new_avg, new_avg_amt, ts),
    )


def update_from_ai_results(db_path: str, top_rows: List[Dict[str, str]], agg_file: str) -> int:
    """Persist a run and picks. Returns run_id."""
    if not top_rows:
        return -1
    ts = _now_iso()
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO runs (ts, agg_file, path, top_n, notes) VALUES (?, ?, ?, ?, ?)",
            (ts, os.path.basename(agg_file), agg_file, len(top_rows), "AI Path"),
        )
        run_id = cur.lastrowid

        for idx, row in enumerate(top_rows, 1):
            ticker = (row.get("ticker") or "").strip().upper()
            try:
                adj = float(row.get("adj_score") or 0.0)
            except Exception:
                adj = 0.0
            try:
                comb = float(row.get("combined_score") or 0.0)
            except Exception:
                comb = 0.0
            articles = int((row.get("articles") or 0) or 0)
            title = (row.get("top_title") or "").strip()
            source = (row.get("top_source") or "").strip()
            reason = (row.get("reason") or "").strip()
            try:
                amt_cr = float(row.get("amt_cr") or 0.0)
            except Exception:
                amt_cr = 0.0
            dups = int((row.get("dups") or 1) or 1)
            has_word = 1 if str(row.get("has_word") or "").lower() in ("true", "1", "yes") else 0
            event = classify_event(title)

            cur.execute(
                """
                INSERT INTO picks (run_id, rank, ticker, adj_score, combined_score, articles, title, source, reason, amt_cr, dups, has_word, event_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, idx, ticker, adj, comb, articles, title, source, reason, amt_cr, dups, has_word, event),
            )

            _upsert_ticker_stats(cur, ticker, adj, title, reason, source, articles, amt_cr, ts)
            _upsert_ticker_event(cur, ticker, event, ts)
            _upsert_source(cur, source, adj, ts)
            _upsert_event(cur, event, adj, amt_cr, ts)

        con.commit()
        return run_id
    finally:
        con.close()


def generate_context_update(db_path: str, context_md_path: str, latest_run_id: int) -> None:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        cur = con.cursor()
        # Pull latest run
        cur.execute("SELECT * FROM runs WHERE id=?", (latest_run_id,))
        run = cur.fetchone()
        if not run:
            return
        # Picks for this run
        cur.execute(
            "SELECT rank, ticker, adj_score, articles, title, reason, source FROM picks WHERE run_id=? ORDER BY rank ASC",
            (latest_run_id,),
        )
        picks = cur.fetchall()
        # Event distribution
        cur.execute(
            "SELECT event_type, COUNT(*) as cnt FROM picks WHERE run_id=? GROUP BY event_type ORDER BY cnt DESC",
            (latest_run_id,),
        )
        ev_dist = cur.fetchall()
        # Sources seen
        cur.execute(
            "SELECT source, COUNT(*) as cnt FROM picks WHERE run_id=? GROUP BY source ORDER BY cnt DESC",
            (latest_run_id,),
        )
        src_dist = cur.fetchall()

        ts = run["ts"]
        agg_file = run["agg_file"]
        lines: List[str] = []
        lines.append(f"## Run {latest_run_id} — {ts}")
        lines.append(f"Aggregated: {agg_file}")
        lines.append("")
        lines.append("Top 10 reasons:")
        for r in picks[:10]:
            lines.append(f"- {r['rank']:2d}. {r['ticker']:<10} {r['adj_score']:.3f} — {r['reason']}")
        lines.append("")
        lines.append("Event mix:")
        if ev_dist:
            lines.append("- " + ", ".join([f"{row['event_type']} x{row['cnt']}" for row in ev_dist]))
        else:
            lines.append("- n/a")
        lines.append("")
        lines.append("Top sources:")
        if src_dist:
            lines.append("- " + ", ".join([f"{(row['source'] or 'n/a').split('/')[0]} x{row['cnt']}" for row in src_dist]))
        else:
            lines.append("- n/a")
        lines.append("")
        lines.append("Notable titles:")
        for r in picks[:5]:
            title = (r["title"] or "").strip()
            if title:
                lines.append(f"- {r['ticker']}: {title[:140]}")
        lines.append("")
        lines.append("——")
        lines.append("")

        with open(context_md_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    finally:
        con.close()


def generate_debate_and_recommendations(db_path: str, latest_run_id: int, out_md_path: str, out_json_path: str) -> None:
    """
    Create a debate-style analysis comparing latest run vs prior stats and emit
    data-driven recommendations for ranking config adjustments.
    """
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        cur = con.cursor()
        # Latest run details and picks
        cur.execute("SELECT * FROM runs WHERE id=?", (latest_run_id,))
        run = cur.fetchone()
        if not run:
            return
        cur.execute("SELECT * FROM picks WHERE run_id=? ORDER BY rank ASC", (latest_run_id,))
        picks = cur.fetchall()

        # Historical aggregates
        cur.execute("SELECT * FROM ticker_stats")
        tstats = cur.fetchall()
        cur.execute("SELECT * FROM event_stats")
        estats = cur.fetchall()
        cur.execute("SELECT * FROM source_stats")
        sstats = cur.fetchall()
        cur.execute("SELECT * FROM ticker_stats")
        tstats_all = cur.fetchall()

        # Compute latest run metrics
        latest_no_exact = sum(1 for r in picks if (r["has_word"] or 0) == 0)
        latest_dup_avg = sum((r["dups"] or 1) for r in picks) / max(1, len(picks))
        amt_cr_vals = [float(r["amt_cr"] or 0.0) for r in picks]
        amt_median = 0.0
        if amt_cr_vals:
            amt_cr_vals_sorted = sorted(amt_cr_vals)
            n = len(amt_cr_vals_sorted)
            mid = n // 2
            amt_median = (amt_cr_vals_sorted[mid] if n % 2 == 1 else (amt_cr_vals_sorted[mid-1] + amt_cr_vals_sorted[mid]) / 2.0)

        # Correlations proxy: rank vs magnitude (Spearman-lite)
        try:
            import math
            ranks = [r["rank"] for r in picks]
            mags = [float(r["amt_cr"] or 0.0) for r in picks]
            # Convert rank to descending score proxy
            scr = [1.0 / (i) for i in ranks]
            mean_scr = sum(scr) / len(scr)
            mean_mag = sum(mags) / len(mags) if mags else 0.0
            cov = sum((s - mean_scr) * (m - mean_mag) for s, m in zip(scr, mags))
            var_s = sum((s - mean_scr) ** 2 for s in scr) or 1e-6
            var_m = sum((m - mean_mag) ** 2 for m in mags) or 1e-6
            corr_mag = cov / math.sqrt(var_s * var_m)
        except Exception:
            corr_mag = 0.0

        # Event distribution latest
        cur.execute("SELECT event_type, COUNT(*) as cnt FROM picks WHERE run_id=? GROUP BY event_type ORDER BY cnt DESC", (latest_run_id,))
        ev_latest = {row["event_type"]: row["cnt"] for row in cur.fetchall()}

        # Reliability summary
        unreliable = []
        for row in tstats_all:
            succ = int(row["success_2p"] or 0)
            fake = int(row["fake_rise_cnt"] or 0)
            apps = int(row["appearances"] or 0)
            if apps >= 2 and fake >= succ + 1:
                unreliable.append((row["ticker"], succ, fake))

        # Build recommendations for ranking_config.json
        rec = {
            "recommend": {},
            "rationale": {}
        }

        # 1) If too many no-exact-ticker, increase missing-name penalty
        no_exact_ratio = latest_no_exact / max(1, len(picks))
        if no_exact_ratio >= 0.25:
            rec["recommend"]["name_factor_missing"] = {"delta": -0.05, "min": 0.5}
            rec["rationale"]["name_factor_missing"] = f"No exact ticker in {no_exact_ratio*100:.1f}% of picks; increase penalty to force entity precision."

        # 2) If duplicates common, strengthen dedup exponent
        if latest_dup_avg > 1.15:
            rec["recommend"]["dedup_exponent"] = {"delta": +0.1, "max": 2.0}
            rec["rationale"]["dedup_exponent"] = f"Avg duplicate factor {latest_dup_avg:.2f}; strengthen 1/dups^alpha to reduce duplication bias."

        # 3) Magnitude correlation low? boost magnitude
        if corr_mag < 0.1 and amt_median > 0:
            rec["recommend"]["magnitude_cap"] = {"delta": +0.05, "max": 0.8}
            rec["rationale"]["magnitude_cap"] = f"Low score-magnitude correlation ({corr_mag:.2f}) despite median amount ~₹{amt_median:.1f} Cr; increase cap slightly."

        # 4) Source adjustments based on source_stats avg_score (relative)
        # Favor reuters/business-standard if present
        src_adj: Dict[str, float] = {}
        for row in sstats:
            src = row["source"] or ""
            avg = float(row["avg_score"] or 0.0)
            if not src:
                continue
            if "reuters.com" in src:
                src_adj["reuters.com"] = 0.01
            elif "business-standard.com" in src:
                src_adj["business-standard.com"] = 0.01
            elif "economictimes.indiatimes.com" in src and "live updates" in (src or "").lower():
                src_adj["economictimes.indiatimes.com"] = -0.01
        if src_adj:
            rec["recommend"]["source_bonus"] = src_adj
            rec["rationale"]["source_bonus"] = "Adjust minor source bonuses to reflect reliability (small nudges)."

        # 5) Penalize unreliable tickers
        if unreliable:
            tp = {t: -0.05 for (t, _, _) in unreliable}
            rec["recommend"]["ticker_penalty"] = tp
            rec["rationale"]["ticker_penalty"] = "Flagged as unreliable (fake rises exceeded successes). Apply small penalties."

        # Debate narrative
        lines: List[str] = []
        lines.append(f"## Debate & Recommendations — Run {latest_run_id} ({run['ts']})")
        lines.append("")
        if unreliable:
            lines.append("Unreliable tickers (fake rises > successes):")
            for t, s, f in unreliable:
                lines.append(f"- {t}: successes={s}, fake_rises={f}")
            lines.append("")
        lines.append("This section captures a reasoning-heavy analysis contrasting latest picks with prior learnings, proposing concrete, data-driven adjustments.")
        lines.append("")
        lines.append("Key observations:")
        lines.append(f"- No-exact-ticker ratio: {no_exact_ratio*100:.1f}% (target < 25%)")
        lines.append(f"- Avg duplication factor: {latest_dup_avg:.2f} (target <= 1.10)")
        lines.append(f"- Median magnitude: ~₹{amt_median:.1f} Cr; correlation with score proxy: {corr_mag:.2f}")
        if ev_latest:
            ev_str = ", ".join([f"{k}:{v}" for k, v in ev_latest.items()])
            lines.append(f"- Event distribution (latest): {ev_str}")
        lines.append("")
        lines.append("Recommendations for next run (config deltas):")
        for k, v in rec["recommend"].items():
            if isinstance(v, dict) and "delta" in v:
                lines.append(f"- {k}: delta {v['delta']} (bounds: {v.get('min','-inf')}..{v.get('max','inf')}) — {rec['rationale'].get(k,'')}")
            else:
                lines.append(f"- {k}: {v} — {rec['rationale'].get(k,'')}")
        lines.append("")
        lines.append("Implementation notes:")
        lines.append("- name_factor_missing: increases penalty when ticker not in title; improves entity precision.")
        lines.append("- dedup_exponent: strengthens 1/dups^alpha so duplicated headlines don't dominate.")
        lines.append("- magnitude_cap: allows larger ₹ deals to contribute slightly more to ranking.")
        lines.append("- source_bonus: tiny multipliers to reflect source reliability; remains conservative.")

        # Write debate markdown
        with open(out_md_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n\n")

        # Write recommendation JSON (absolute values to apply)
        # We read current config, then apply deltas to preview target values
        cfg_path = os.path.join(os.path.dirname(out_json_path), "ranking_config.json")
        try:
            import json
            with open(cfg_path, "r", encoding="utf-8") as cf:
                cfg = json.load(cf)
        except Exception:
            cfg = {}
        # Apply numeric deltas
        if "dedup_exponent" in rec["recommend"]:
            cur = float(cfg.get("dedup_exponent", 1.0))
            delta = rec["recommend"]["dedup_exponent"]["delta"]
            maxv = rec["recommend"]["dedup_exponent"].get("max", 2.0)
            cfg["dedup_exponent"] = min(maxv, cur + delta)
        if "name_factor_missing" in rec["recommend"]:
            cur = float(cfg.get("name_factor_missing", 0.75))
            delta = rec["recommend"]["name_factor_missing"]["delta"]
            minv = rec["recommend"]["name_factor_missing"].get("min", 0.5)
            cfg["name_factor_missing"] = max(minv, cur + delta)
        if "magnitude_cap" in rec["recommend"]:
            cur = float(cfg.get("magnitude_cap", 0.5))
            delta = rec["recommend"]["magnitude_cap"]["delta"]
            maxv = rec["recommend"]["magnitude_cap"].get("max", 0.8)
            cfg["magnitude_cap"] = min(maxv, cur + delta)
        if "source_bonus" in rec["recommend"]:
            sb = cfg.get("source_bonus", {}) or {}
            sb.update(rec["recommend"]["source_bonus"])  # small nudges
            cfg["source_bonus"] = sb
        if "ticker_penalty" in rec["recommend"]:
            tp = cfg.get("ticker_penalty", {}) or {}
            tp.update(rec["recommend"]["ticker_penalty"])
            cfg["ticker_penalty"] = tp

        import json
        with open(out_json_path, "w", encoding="utf-8") as jf:
            json.dump(cfg, jf, indent=2)

    finally:
        con.close()


def record_decision_feedback(db_path: str, feedback_entries: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Store manual decision feedback and update reliability cues.

    Each entry may contain: run_id, ticker, verdict, expected_return, actual_return,
    rating, confidence, notes. Verdict is interpreted to adjust reliability."""
    entries = []
    for raw in feedback_entries or []:
        if not raw:
            continue
        ticker = str(raw.get('ticker') or '').strip().upper()
        if not ticker:
            continue
        verdict = str(raw.get('verdict') or '').strip().lower()
        event_ts = str(raw.get('event_ts') or '').strip()
        entries.append({
            'run_id': int(raw.get('run_id') or 0) or None,
            'ticker': ticker,
            'verdict': verdict,
            'expected_return': _safe_float(raw.get('expected_return')),
            'actual_return': _safe_float(raw.get('actual_return')),
            'rating': _safe_float(raw.get('rating')),
            'confidence': _safe_float(raw.get('confidence')),
            'notes': str(raw.get('notes') or '').strip(),
            'event_ts': event_ts if event_ts else None,
        })
    if not entries:
        return {'inserted': 0, 'updated_tickers': 0, 'positives': 0, 'negatives': 0}

    ensure_db(db_path)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    positives = negatives = 0
    try:
        cur = con.cursor()
        positive_tags = {'win', 'wins', 'success', 'successful', 'positive', 'gain', 'profit', 'hit', 'beat'}
        negative_tags = {'loss', 'losses', 'negative', 'fail', 'failed', 'miss', 'drawdown', 'drop', 'missed'}
        touched_tickers: set[str] = set()
        now = _now_iso()
        for item in entries:
            inserted = False
            try:
                cur.execute(
                    """
                    INSERT INTO decision_feedback
                    (run_id, ticker, verdict, expected_return, actual_return, rating, confidence, notes, event_ts, created)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        item['run_id'],
                        item['ticker'],
                        item['verdict'],
                        item['expected_return'],
                        item['actual_return'],
                        item['rating'],
                        item['confidence'],
                        item['notes'],
                        item['event_ts'],
                        now,
                    ),
                )
                inserted = True
            except sqlite3.IntegrityError:
                inserted = False

            if not inserted:
                continue

            verdict = item['verdict']
            ticker = item['ticker']
            if ticker not in touched_tickers:
                touched_tickers.add(ticker)
            cur.execute("SELECT * FROM ticker_stats WHERE ticker=?", (ticker,))
            row = cur.fetchone()
            if row is None:
                cur.execute(
                    """
                    INSERT INTO ticker_stats (ticker, appearances, last_seen, success_2p, fake_rise_cnt, reliability_score)
                    VALUES (?, 0, ?, 0, 0, 0.0)
                    """,
                    (ticker, now),
                )
                successes = 0
                failures = 0
                appearances = 0
            else:
                successes = int(row['success_2p'] or 0)
                failures = int(row['fake_rise_cnt'] or 0)
                appearances = int(row['appearances'] or 0)
            normalized = verdict.lower()
            if normalized in positive_tags:
                successes += 1
                positives += 1
            elif normalized in negative_tags:
                failures += 1
                negatives += 1
            denom = max(1, appearances)
            reliability = (successes - 1.25 * failures) / float(denom)
            cur.execute(
                """
                UPDATE ticker_stats
                SET success_2p=?, fake_rise_cnt=?, reliability_score=?, last_seen=?
                WHERE ticker=?
                """,
                (successes, failures, reliability, now, ticker),
            )
        con.commit()
        return {
            'inserted': len(entries),
            'updated_tickers': len(touched_tickers),
            'positives': positives,
            'negatives': negatives,
        }
    finally:
        con.close()


def generate_self_assessment(db_path: str, run_limit: int = 10) -> Dict[str, Any]:
    """Return compact self-assessment metrics summarizing recent performance."""
    if not os.path.exists(db_path):
        return {'status': 'no_db', 'message': f'Learning DB not found: {db_path}'}
    ensure_db(db_path)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        cur = con.cursor()
        cur.execute('SELECT COUNT(*) AS cnt FROM runs')
        total_runs = int(cur.fetchone()['cnt'])
        if total_runs == 0:
            return {'status': 'empty', 'message': 'No AI runs recorded yet.'}

        run_limit = max(1, min(run_limit, total_runs))
        cur.execute('SELECT id, ts FROM runs ORDER BY id DESC LIMIT ?', (run_limit,))
        runs = cur.fetchall()
        run_ids = [row['id'] for row in runs]
        latest_run_id = run_ids[0]
        latest_ts = runs[0]['ts']

        placeholders = ','.join('?' for _ in run_ids)
        cur.execute(
            f'SELECT run_id, AVG(adj_score) AS avg_adj FROM picks WHERE run_id IN ({placeholders}) GROUP BY run_id',
            run_ids,
        )
        avg_map = {row['run_id']: row['avg_adj'] or 0.0 for row in cur.fetchall()}
        latest_avg_adj = float(avg_map.get(latest_run_id, 0.0))
        prev_ids = run_ids[1:]
        prev_avg_adj = 0.0
        if prev_ids:
            placeholders_prev = ','.join('?' for _ in prev_ids)
            cur.execute(
                f'SELECT AVG(adj_score) AS avg_adj FROM picks WHERE run_id IN ({placeholders_prev})',
                prev_ids,
            )
            prev_avg_adj = float(cur.fetchone()['avg_adj'] or 0.0)

        cur.execute('SELECT verdict, COUNT(*) AS cnt FROM decision_feedback GROUP BY verdict ORDER BY cnt DESC')
        feedback_counts = {row['verdict'] or '': row['cnt'] for row in cur.fetchall()}
        cur.execute('SELECT AVG(actual_return) AS avg_ret, AVG(rating) AS avg_rating FROM decision_feedback')
        row = cur.fetchone()
        avg_actual_return = _safe_float(row['avg_ret'])
        avg_rating = _safe_float(row['avg_rating'])

        cur.execute(
            '''
            SELECT ticker, reliability_score, success_2p, fake_rise_cnt, appearances
            FROM ticker_stats
            WHERE reliability_score IS NOT NULL
            ORDER BY reliability_score DESC
            LIMIT 6
            '''
        )
        leaders = [
            {
                'ticker': r['ticker'],
                'reliability': round(float(r['reliability_score'] or 0.0), 3),
                'successes': int(r['success_2p'] or 0),
                'failures': int(r['fake_rise_cnt'] or 0),
                'appearances': int(r['appearances'] or 0),
            }
            for r in cur.fetchall()
        ]

        cur.execute(
            '''
            SELECT ticker, reliability_score, success_2p, fake_rise_cnt, appearances
            FROM ticker_stats
            WHERE reliability_score IS NOT NULL
            ORDER BY reliability_score ASC
            LIMIT 6
            '''
        )
        at_risk = [
            {
                'ticker': r['ticker'],
                'reliability': round(float(r['reliability_score'] or 0.0), 3),
                'successes': int(r['success_2p'] or 0),
                'failures': int(r['fake_rise_cnt'] or 0),
                'appearances': int(r['appearances'] or 0),
            }
            for r in cur.fetchall()
        ]

        cur.execute(
            '''
            SELECT event_type, cnt, avg_score, avg_amt_cr, success_2p, fake_rise_cnt
            FROM event_stats
            ORDER BY avg_score DESC
            LIMIT 5
            '''
        )
        event_leaders = [
            {
                'event_type': r['event_type'],
                'count': int(r['cnt'] or 0),
                'avg_score': round(float(r['avg_score'] or 0.0), 3),
                'avg_amt_cr': round(float(r['avg_amt_cr'] or 0.0), 2),
                'successes': int(r['success_2p'] or 0),
                'failures': int(r['fake_rise_cnt'] or 0),
            }
            for r in cur.fetchall()
        ]

        cur.execute(
            '''
            SELECT source, cnt, avg_score
            FROM source_stats
            ORDER BY avg_score DESC, cnt DESC
            LIMIT 5
            '''
        )
        source_leaders = [
            {
                'source': r['source'],
                'count': int(r['cnt'] or 0),
                'avg_score': round(float(r['avg_score'] or 0.0), 3),
            }
            for r in cur.fetchall()
        ]

        cur.execute('SELECT COUNT(DISTINCT ticker) AS uniq FROM picks')
        coverage = int(cur.fetchone()['uniq'] or 0)

        return {
            'status': 'ok',
            'runs_analyzed': run_limit,
            'latest_run_id': latest_run_id,
            'latest_timestamp': latest_ts,
            'latest_avg_adj': round(latest_avg_adj, 4),
            'prev_avg_adj': round(prev_avg_adj, 4),
            'avg_adj_delta': round(latest_avg_adj - prev_avg_adj, 4),
            'feedback_summary': {
                'counts': feedback_counts,
                'avg_actual_return': avg_actual_return,
                'avg_rating': avg_rating,
            },
            'reliability': {
                'leaders': leaders,
                'at_risk': at_risk,
                'coverage': coverage,
            },
            'event_performance': event_leaders,
            'source_leaders': source_leaders,
        }
    finally:
        con.close()


def harvest_price_feedback(db_path: str, min_hours: int = 24) -> Dict[str, Any]:
    """Harvest price_eval rows into decision feedback for autonomous learning."""
    if not os.path.exists(db_path):
        return {"status": "no_db", "message": f"Learning DB not found: {db_path}"}

    ensure_db(db_path)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    harvested: List[Dict[str, Any]] = []
    skipped_recent = 0
    considered = 0
    try:
        cur = con.cursor()
        cutoff = datetime.utcnow() - timedelta(hours=max(0, min_hours))
        cur.execute(
            """
            SELECT p.run_id, p.ticker, p.event_ts, p.event_type, p.title,
                   p.ret_1d, p.ret_3d, p.ret_5d, p.consistent, p.fake
            FROM price_eval AS p
            LEFT JOIN decision_feedback AS d
              ON d.run_id = p.run_id
             AND d.ticker = p.ticker
             AND (d.event_ts = p.event_ts OR (d.event_ts IS NULL AND (p.event_ts IS NULL OR p.event_ts = "")))
            WHERE d.id IS NULL
            """
        )
        rows = cur.fetchall()
    finally:
        con.close()

    for row in rows:
        considered += 1
        event_ts_str = row['event_ts'] or ''
        try:
            event_dt = datetime.fromisoformat(event_ts_str.replace('Z', '+00:00')) if event_ts_str else None
        except Exception:
            event_dt = None
        if event_dt and event_dt > cutoff:
            skipped_recent += 1
            continue

        ret_5 = _safe_float(row['ret_5d'])
        ret_3 = _safe_float(row['ret_3d'])
        ret_1 = _safe_float(row['ret_1d'])
        actual = next((val for val in (ret_5, ret_3, ret_1) if val is not None), None)
        expected = next((val for val in (ret_3, ret_1, ret_5) if val is not None), None)
        verdict = 'neutral'
        if row['consistent']:
            verdict = 'win'
        elif row['fake']:
            verdict = 'loss'
        elif actual is not None:
            if actual >= 2.0:
                verdict = 'win'
            elif actual <= -1.0:
                verdict = 'loss'

        rating = None
        if actual is not None:
            rating = max(0.0, min(10.0, 5.0 + (actual / 2.0)))
        confidence = 0.5
        if verdict == 'win':
            confidence = 0.8 if row['consistent'] else 0.65
        elif verdict == 'loss':
            confidence = 0.35

        notes = f"Auto feedback from price_eval — {row['event_type'] or 'event'}"
        title = (row['title'] or '').strip()
        if title:
            notes += f" | {title[:90]}"

        harvested.append({
            'run_id': row['run_id'],
            'ticker': (row['ticker'] or '').upper(),
            'verdict': verdict,
            'expected_return': expected,
            'actual_return': actual,
            'rating': rating,
            'confidence': confidence,
            'notes': notes,
            'event_ts': event_ts_str or None,
        })

    if not harvested:
        return {
            'status': 'noop',
            'considered': considered,
            'skipped_recent': skipped_recent,
            'harvested': 0
        }

    result = record_decision_feedback(db_path, harvested)
    result.update({
        'status': 'harvested',
        'considered': considered,
        'skipped_recent': skipped_recent,
        'harvested': len(harvested)
    })
    return result



def get_latest_run_info(db_path: str) -> Dict[str, Any]:
    ensure_db(db_path)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        cur = con.cursor()
        cur.execute('SELECT id, ts, agg_file FROM runs ORDER BY id DESC LIMIT 1')
        row = cur.fetchone()
        if not row:
            return {}
        return {'run_id': row['id'], 'timestamp': row['ts'], 'agg_file': row['agg_file']}
    finally:
        con.close()



def get_run_snapshot(db_path: str, run_id: int, top_n: int = 5) -> Dict[str, Any]:
    ensure_db(db_path)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        cur = con.cursor()
        cur.execute('SELECT id, ts, agg_file FROM runs WHERE id=?', (run_id,))
        run = cur.fetchone()
        if not run:
            return {}
        cur.execute(
            'SELECT rank, ticker, adj_score, title, source, event_type FROM picks WHERE run_id=? ORDER BY rank ASC LIMIT ?',
            (run_id, max(1, top_n)),
        )
        picks = [dict(row) for row in cur.fetchall()]
        return {
            'run_id': run['id'],
            'timestamp': run['ts'],
            'agg_file': run['agg_file'],
            'picks': picks,
        }
    finally:
        con.close()



def record_assistant_feedback(db_path: str, run_id: int, feedback_entries: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    if run_id is None or run_id < 0:
        return {'inserted': 0, 'errors': len(list(feedback_entries or []))}
    entries = [entry for entry in (feedback_entries or []) if entry]
    if not entries:
        return {'inserted': 0, 'errors': 0}
    ensure_db(db_path)
    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        inserted = 0
        errors = 0
        for item in entries:
            try:
                cur.execute(
                    """
                    INSERT INTO assistant_feedback (run_id, assistant, status, command, response, error, created)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        str(item.get('assistant') or ''),
                        str(item.get('status') or ''),
                        str(item.get('command') or ''),
                        str(item.get('response') or ''),
                        str(item.get('error') or ''),
                        _now_iso(),
                    ),
                )
                inserted += 1
            except Exception:
                errors += 1
        con.commit()
        return {'inserted': inserted, 'errors': errors}
    finally:
        con.close()



def get_assistant_attempts(db_path: str, run_id: int) -> List[Dict[str, Any]]:
    ensure_db(db_path)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        cur = con.cursor()
        cur.execute(
            'SELECT assistant, status, command, response, error, created FROM assistant_feedback WHERE run_id=? ORDER BY id ASC',
            (run_id,),
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()



def build_verdict_summary(
    db_path: str,
    run_id: int,
    *,
    assistant_attempts: Iterable[Dict[str, Any]] | None = None,
    learning_report: Optional[Dict[str, Any]] = None,
    top_n: int = 5,
) -> str:
    snapshot = get_run_snapshot(db_path, run_id, top_n=top_n)
    lines: List[str] = []
    lines.append(f"Verdict Helper — Run {run_id}")
    timestamp = snapshot.get('timestamp') or ''
    if timestamp:
        lines.append(f"Timestamp: {timestamp}")
    agg_file = snapshot.get('agg_file') or ''
    if agg_file:
        lines.append(f"Aggregated file: {agg_file}")
    lines.append('')
    lines.append('Top opportunities:')
    picks = snapshot.get('picks') or []
    if picks:
        for pick in picks:
            rank = pick.get('rank')
            ticker = pick.get('ticker') or ''
            score = pick.get('adj_score')
            event = (pick.get('event_type') or '').strip()
            title = (pick.get('title') or '').strip()
            source = (pick.get('source') or '').strip()
            score_txt = f"{score:.3f}" if isinstance(score, (int, float)) else str(score or '')
            lines.append(f"{rank}. {ticker} (score {score_txt}) [{event}] — {title} ({source})")
    else:
        lines.append('(no picks recorded)')
    lines.append('')
    if assistant_attempts is not None:
        attempts = list(assistant_attempts)
        if attempts:
            lines.append('Assistant feedback:')
            for attempt in attempts:
                name = attempt.get('assistant') or 'unknown'
                status = attempt.get('status') or 'unknown'
                response = (attempt.get('response_preview')
                           or attempt.get('response')
                           or '').strip()
                error = (attempt.get('error_preview')
                        or attempt.get('error')
                        or '').strip()
                lines.append(f"- {name}: {status}")
                if response:
                    lines.append(f"    response: {response[:200]}")
                if error:
                    lines.append(f"    error: {error[:200]}")
        else:
            lines.append('Assistant feedback: none recorded')
        lines.append('')
    if learning_report:
        sa = learning_report.get('self_assessment') if isinstance(learning_report, dict) else None
        harvest = learning_report.get('harvest') if isinstance(learning_report, dict) else None
        if sa:
            lines.append('Self-assessment snapshot:')
            runs_analyzed = sa.get('runs_analyzed')
            latest_avg = sa.get('latest_avg_adj')
            delta = sa.get('avg_adj_delta')
            if runs_analyzed is not None:
                lines.append(f"- runs_analyzed: {runs_analyzed}")
            if latest_avg is not None:
                lines.append(f"- latest_avg_adj: {latest_avg}")
            if delta is not None:
                lines.append(f"- avg_adj_delta: {delta}")
            feedback = sa.get('feedback_summary') or {}
            counts = feedback.get('counts')
            if counts:
                lines.append(f"- verdict counts: {counts}")
            lines.append('')
        if harvest:
            lines.append('Harvest summary:')
            lines.append(f"- status: {harvest.get('status')}")
            lines.append(f"- harvested: {harvest.get('harvested')}")
            lines.append(f"- skipped_recent: {harvest.get('skipped_recent')}")
            lines.append('')
    lines.append('Use this verdict to adjust rankings and follow-up actions.')
    return "\n".join(lines)



def _safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None
