#!/usr/bin/env python3
"""
Two-Path Orchestrator: Script Path vs AI Path

Purpose
- Let the user choose between:
  A) Script Path: Use original rules in screen_full_articles.py
  B) AI Path: Re-rank with entity-aware, deduplicated, magnitude-weighted heuristics

Behavior
- Auto-detect latest aggregated_full_articles_*.txt (or prompt to fetch first)
- For Script Path: run screen_full_articles.py to produce all_news_screen.csv
- For AI Path: ensure all_news_screen.csv exists (generate if missing), then
  adjust ranking and save ai_adjusted_top25_*.csv
- Optionally ask to continue with the institutional screener for technicals

Safe output
- Writes CSV(s) in current directory and prints concise Top N to console.

Rate limiting
- The institutional screener uses batched yfinance with internal throttling.
"""

from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Tuple
import learning_db
import json
import argparse
import price_eval
from orchestrator.config import load_config as _load_config, OUTPUTS_DIR, LEARNING_DIR
from orchestrator.archive import archive_old_outputs
from orchestrator.organize import organize_workspace
from orchestrator.suggestions import analyze_and_suggest
from orchestrator.ranking import ai_adjust_rank as AI_ADJUST_RANK
from orchestrator.ranking import parse_amount_crore as ORCH_PARSE_AMOUNT_CRORE
from orchestrator.ranking import get_company_name
from orchestrator.enhanced_scoring import EnhancedScorer, add_enhanced_scoring_to_csv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, os.pardir))

# Global auto flags (set via CLI)
AUTO_APPLY_CONFIG = False
AUTO_SCREENER = False
FORCE_PATH: str | None = None  # 'ai' or 'script'


def find_latest_aggregated(prefix: str = "aggregated_full_articles_") -> str | None:
    """Return latest aggregated file path.
    Accepts files with or without .txt extension to accommodate collectors
    that don't append an extension when --output-file is provided.
    """
    candidates: list[tuple[float, str]] = []
    try:
        from orchestrator.config import AGGREGATES_DIR as _AGG
        roots = (BASE_DIR, _AGG)
    except Exception:
        roots = (BASE_DIR,)
    for root in roots:
        try:
            for name in os.listdir(root):
                if not name.startswith(prefix):
                    continue
                p = os.path.join(root, name)
                if not os.path.isfile(p):
                    continue
                try:
                    mt = os.path.getmtime(p)
                    candidates.append((mt, p))
                except Exception:
                    continue
        except Exception:
            continue
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


def run_screen_full_articles(agg_path: str, top: int = 300) -> str:
    """Run the original script path to generate the news CSV."""
    try:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
    except Exception:
        pass
    csv_path = os.path.join(OUTPUTS_DIR, "all_news_screen.csv")
    script_path = os.path.join(ROOT_DIR, "screen_full_articles.py")
    if os.path.exists(script_path):
        cmd = [
            sys.executable,
            script_path,
            "--input", agg_path,
            "--top", str(top),
            "--export", csv_path,
        ]
        print(f"[Script Path] Running screen_full_articles.py -> {csv_path}")
        subprocess.run(cmd, check=True)
        return csv_path
    # Fallback: minimal parser to CSV if screen_full_articles.py absent
    print("[Script Path] screen_full_articles.py not found — using minimal aggregated parser to build CSV")
    try:
        rows: list[dict[str, str]] = []
        import re, urllib.parse
        current = None
        titles_seen = set()
        with open(agg_path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                line = raw.strip()
                m = re.match(r"^Full Article Fetch Test -\s+([A-Z0-9.&'-]+)\s*$", line)
                if m:
                    current = m.group(1).upper()
                    continue
                if not current:
                    continue
                if line.lower().startswith("title") and ":" in line:
                    title = line.split(":", 1)[1].strip()
                    # Lookahead: next few lines for URL
                    # We'll read directly from the file iterator; store position
                    # Since we can't push back, we just peek via next lines logic
                    # Simple approach: we rely on URL appearing within next 3 lines
                    url = ""
                    for _ in range(3):
                        try:
                            nxt = next(f).strip()
                        except StopIteration:
                            break
                        if nxt.lower().startswith("url") and ":" in nxt:
                            url = nxt.split(":", 1)[1].strip()
                            break
                    if not title or title in titles_seen:
                        continue
                    titles_seen.add(title)
                    host = urllib.parse.urlparse(url).netloc if url else ""
                    rows.append({
                        "ticker": current,
                        "company_name": "",
                        "combined_score": "1.0",
                        "adj_score": "",
                        "articles": "1",
                        "dups": "1",
                        "has_word": "",
                        "amt_cr": "",
                        "reason": "",
                        "event_type": "",
                        "top_title": title,
                        "top_source": host,
                    })
        # Write CSV
        import csv
        with open(csv_path, "w", newline="", encoding="utf-8") as wf:
            w = csv.DictWriter(wf, fieldnames=[
                "ticker","company_name","combined_score","adj_score","articles","dups","has_word","amt_cr","reason","event_type","top_title","top_source"
            ])
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"[Script Path] Wrote minimal CSV with {len(rows)} rows -> {csv_path}")
        return csv_path
    except Exception as e:
        print(f"[error] Minimal CSV build failed: {e}")
        raise


def fresh_fetch_news(hours_back: int = 24, max_articles: int = 10, tickers_file: str = None) -> None:
    """Fetch fresh aggregated news using the enhanced collector.
    Safe wrapper: if network is blocked or command fails, continue gracefully.
    """
    try:
        sources = [
            'reuters.com', 'livemint.com', 'economictimes.indiatimes.com',
            'business-standard.com', 'moneycontrol.com', 'thehindubusinessline.com',
            'financialexpress.com', 'cnbctv18.com', 'zeebiz.com'
        ]
        # Use provided ticker file or default to sec_tickers.txt
        if not tickers_file:
            tickers_file = os.path.join(BASE_DIR, 'sec_tickers.txt')
        elif not os.path.isabs(tickers_file):
            tickers_file = os.path.join(BASE_DIR, tickers_file)
            
        cmd = [
            sys.executable,
            os.path.join(BASE_DIR, 'enhanced_india_finance_collector.py'),
            '--tickers-file', tickers_file,
            '--hours-back', str(int(hours_back)),
            '--max-articles', str(int(max_articles)),
            '--no-per-ticker',
            '--sources', *sources,
            '--output-file', f'aggregated_full_articles_{int(hours_back)}h'
        ]
        print(f"[fetch] Fetching fresh news for last {hours_back}h from {os.path.basename(tickers_file)}…")
        subprocess.run(cmd, check=True)
    except Exception as e:
        print(f"[warn] Fresh fetch failed or network blocked: {e}")


def parse_amount_crore(title: str) -> float:
    """Extract a rough INR crore magnitude from the title."""
    if not title:
        return 0.0
    t = title.strip()
    # crore/cr/lakh/mn/million/bn/billion
    m = re.search(r"([0-9][0-9,\.]*?)\s*(crore|cr\b|lakh|million|mn\b|billion|bn\b)", t, re.I)
    if m:
        num = m.group(1).replace(",", "")
        unit = m.group(2).lower()
        try:
            v = float(num)
        except ValueError:
            v = 0.0
        if unit in ("crore", "cr"):
            return v
        if unit == "lakh":
            return v / 100.0
        if unit in ("million", "mn"):
            return v / 10.0
        if unit in ("billion", "bn"):
            return v * 100.0
        return 0.0
    return 0.0


def load_news_csv(csv_path: str) -> List[Dict[str, str]]:
    with open(csv_path, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        return [row for row in rdr]


def _load_config() -> Dict[str, any]:
    cfg_path = os.path.join(BASE_DIR, "ranking_config.json")
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "dedup_exponent": 1.0,
            "name_factor_missing": 0.75,
            "name_factor_short_ticker": 0.6,
            "magnitude_cap": 0.5,
            "magnitude_log_divisor": 6.0,
            "source_bonus": {}
        }


def ai_adjust_rank(csv_path: str, top_n: int = 25) -> Tuple[List[Dict[str, str]], str]:
    """
    Adjust ranking to reduce duplication and improve entity linkage.
    - Deduplicate identical titles across tickers (1/dups factor)
    - Boost only if ticker appears as a whole word in title
    - Penalize likely fund/PE-only mentions
    - Add capped magnitude boost from parsed INR crore values
    """
    rows = load_news_csv(csv_path)
    # Load config
    cfg = _load_config()
    dedup_exp = float(cfg.get("dedup_exponent", 1.0))
    name_missing = float(cfg.get("name_factor_missing", 0.75))
    name_short = float(cfg.get("name_factor_short_ticker", 0.6))
    mag_cap = float(cfg.get("magnitude_cap", 0.5))
    mag_div = float(cfg.get("magnitude_log_divisor", 6.0))
    src_bonus: Dict[str, float] = cfg.get("source_bonus", {}) or {}

    # Build duplicate counts by title
    dup: Dict[str, int] = {}
    for r in rows:
        title = (r.get("top_title") or "").strip()
        if title:
            dup[title] = dup.get(title, 0) + 1

    adjusted: List[Tuple[float, Dict[str, str]]] = []
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
        if re.search(r"upgrade|downgrade|target price|brokerage", t):
            return "Brokerage"
        if re.search(r"result|profit|ebitda|margin|q[1-4]|quarter|yoy|growth", t):
            return "Results/metrics"
        if re.search(r"appoints|resigns|ceo|cfo", t):
            return "Management"
        return "General"

    def top_reasons(title: str, ticker: str, has_word: bool, dups: int, cr: float, source: str) -> str:
        reasons: List[str] = []
        # Event
        ev = classify_event(title)
        if ev != "General":
            reasons.append(ev)
        # Magnitude
        if cr > 0:
            # Round to nearest 10 if large
            cr_disp = f"{cr:.0f}" if cr >= 100 else f"{cr:.1f}"
            reasons.append(f"~₹{cr_disp} Cr")
        # Ticker presence
        reasons.append("ticker in title" if has_word else "no exact ticker")
        # Dedup
        if dups > 1:
            reasons.append(f"dedup x{dups}")
        # Source cue (short)
        dom = (source or "").lower()
        src_tag = None
        for key in ("reuters.com", "livemint.com", "economictimes.indiatimes.com", "business-standard.com", "thehindubusinessline.com"):
            if key in dom:
                src_tag = key.split(".")[0]
                break
        if src_tag:
            reasons.append(src_tag)
        # Limit to 3 concise reasons
        return "; ".join(reasons[:3]) or "news impact"

    for r in rows:
        ticker = (r.get("ticker") or "").strip().upper()
        title = (r.get("top_title") or "").strip()
        try:
            base = float(r.get("combined_score") or 0.0)
        except ValueError:
            base = 0.0

        # Dedup factor
        dups = max(1, dup.get(title, 1))
        dedup_factor = (1.0 / float(dups)) ** max(0.0, dedup_exp)

        # Whole-word ticker presence
        has_word = False
        if ticker and title:
            if re.search(rf"\b{re.escape(ticker)}\b", title, re.I):
                has_word = True
        # Penalize if not present (short tickers penalized more)
        if has_word:
            name_factor = 1.0
        elif len(ticker) <= 2:
            name_factor = name_short
        else:
            name_factor = name_missing

        # Heuristic fund/PE penalty when no listed company word appears
        if title and re.search(r"\bfund(s)?\b", title, re.I) and not re.search(
            r"limited|ltd|industr|labs|hospitals|company|bank|motors|pharma|energy|steel|cement|infra",
            title,
            re.I,
        ):
            name_factor *= 0.8

        # Magnitude boost (capped)
            cr = ORCH_PARSE_AMOUNT_CRORE(title)
        mag_factor = 1.0 + min(mag_cap, (0.0 if cr <= 0 else (max(0.0, __import__("math").log10(1.0 + cr)) / max(1e-6, mag_div))))

        # Source bonus (small multiplier)
        sdom = (r.get("top_source") or "").lower()
        sb = 0.0
        for dom, b in src_bonus.items():
            if dom in sdom:
                try:
                    sb = float(b)
                except Exception:
                    sb = 0.0
                break
        src_factor = 1.0 + max(0.0, sb)

        # Event bonus (small multiplier)
        ev = classify_event(title)
        event_bonus = 0.0
        try:
            event_bonus = float((_load_config().get("event_bonus", {}) or {}).get(ev, 0.0))
        except Exception:
            event_bonus = 0.0
        ev_factor = 1.0 + max(0.0, event_bonus)

        # Ticker penalty (small negative multiplier)
        pen = 0.0
        try:
            pen = float((_load_config().get("ticker_penalty", {}) or {}).get(ticker, 0.0))
        except Exception:
            pen = 0.0
        pen_factor = 1.0 + min(0.0, pen)  # penalty should be <= 0

        adj = base * dedup_factor * name_factor * mag_factor * src_factor * ev_factor * pen_factor
        r_out = dict(r)
        r_out["adj_score"] = f"{adj:.6f}"
        r_out["dups"] = str(dups)
        r_out["has_word"] = str(has_word)
        r_out["amt_cr"] = f"{cr:.3f}"
        r_out["reason"] = top_reasons(title, ticker, has_word, dups, cr, (r.get("top_source") or ""))
        r_out["event_type"] = ev
        adjusted.append((adj, r_out))

    adjusted.sort(key=lambda x: x[0], reverse=True)
    top = [row for _, row in adjusted[:top_n]]
    
    # === ENHANCED SCORING INTEGRATION ===
    # Add certainty, fake rally detection, and expected rise
    print("\n🎯 Applying Enhanced Scoring (Certainty, Fake Rally Detection, Magnitude Filter)...")
    enhanced_top = []
    rejected_count = 0
    
    for row in top:
        title = row.get('top_title', '')
        source = row.get('top_source', '')
        ticker = row.get('ticker', '')
        
        # Calculate enhanced metrics
        certainty, reasons = EnhancedScorer.calculate_certainty(title, source, 1)
        magnitude = EnhancedScorer.extract_magnitude(title)
        sentiment = EnhancedScorer.calculate_sentiment_score(title)
        is_fake, fake_reason = EnhancedScorer.detect_fake_rally(title, magnitude)
        rise_min, rise_max, rise_conf = EnhancedScorer.calculate_expected_rise(
            magnitude, 0, sentiment  # Market cap loaded separately if needed
        )
        
        # Apply quality filters
        if is_fake:
            rejected_count += 1
            continue
        if certainty < EnhancedScorer.MIN_CERTAINTY:
            rejected_count += 1
            continue
        if magnitude > 0 and magnitude < EnhancedScorer.MIN_MAGNITUDE_CR:
            rejected_count += 1
            continue
        
        # Add enhanced fields
        row['certainty_score'] = f"{certainty:.1f}"
        row['expected_rise_min'] = f"{rise_min:.1f}"
        row['expected_rise_max'] = f"{rise_max:.1f}"
        row['rise_confidence'] = rise_conf
        row['magnitude_cr'] = f"{magnitude:.1f}"
        row['sentiment_score'] = str(sentiment)
        row['fake_rally_risk'] = fake_reason
        
        enhanced_top.append(row)
    
    if rejected_count > 0:
        print(f"   ❌ Filtered out {rejected_count} stocks (fake rallies/low quality)")
    print(f"   ✅ Qualified: {len(enhanced_top)} stocks")
    
    # Save enhanced results
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_csv = os.path.join(BASE_DIR, f"ai_adjusted_top25_{ts}.csv")
    
    if enhanced_top:
        with open(out_csv, "w", newline="", encoding="utf-8") as f:
            # Include enhanced fields in output
            fieldnames = [
                "ticker",
                "combined_score",
                "adj_score",
                "certainty_score",
                "expected_rise_min",
                "expected_rise_max",
                "rise_confidence",
                "magnitude_cr",
                "sentiment_score",
                "fake_rally_risk",
                "articles",
                "dups",
                "has_word",
                "amt_cr",
                "reason",
                "event_type",
                "top_title",
                "top_source",
            ]
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            for row in enhanced_top:
                w.writerow(row)
    
    return enhanced_top, out_csv


def print_top(rows: List[Dict[str, str]], key_field: str = "combined_score") -> None:
    print("\n" + "="*90)
    print("🏆 TOP INVESTMENT PICKS (Enhanced with Certainty & Fake Rally Protection)")
    print("="*90)
    
    # Build duplicate title counts within the displayed set
    dup: Dict[str, int] = {}
    for r in rows:
        ttle = (r.get("top_title") or "").strip()
        if ttle:
            dup[ttle] = dup.get(ttle, 0) + 1

    for i, r in enumerate(rows, 1):
        t = (r.get("ticker") or "").strip().upper()
        k = r.get(key_field) or "0"
        title = r.get("top_title") or ""
        reason = r.get("reason") or ""
        
        # Get enhanced metrics
        certainty = r.get("certainty_score", "N/A")
        rise_min = r.get("expected_rise_min", "N/A")
        rise_max = r.get("expected_rise_max", "N/A")
        rise_conf = r.get("rise_confidence", "N/A")
        magnitude = r.get("magnitude_cr", "0")
        fake_risk = r.get("fake_rally_risk", "N/A")
        
        if not reason:
            # Enriched reasons for Script Path rows
            reasons: List[str] = []
            low = title.lower()
            # Event
            if re.search(r"\bipo\b|listing|fpo|qip|rights issue", low):
                reasons.append("IPO/listing")
            elif re.search(r"acquisit|merger|buyout|joint venture|\bjv\b|stake (?:buy|sale)", low):
                reasons.append("M&A/JV")
            elif re.search(r"order\b|contract\b|tender|project|deal", low):
                reasons.append("Order/contract")
            elif re.search(r"approval|usfda|sebi|nod|clearance|regulator", low):
                reasons.append("Regulatory")
            elif re.search(r"block deal", low):
                reasons.append("Block deal")
            elif re.search(r"dividend|buyback|payout", low):
                reasons.append("Dividend/return")
            elif re.search(r"result|profit|ebitda|margin|q[1-4]|quarter|yoy|growth", low):
                reasons.append("Results/metrics")
            elif re.search(r"appoints|resigns|ceo|cfo", low):
                reasons.append("Management")
            else:
                reasons.append("news impact")

            # Magnitude
            cr = ORCH_PARSE_AMOUNT_CRORE(title)
            if cr > 0:
                cr_disp = f"{cr:.0f}" if cr >= 100 else f"{cr:.1f}"
                reasons.append(f"~₹{cr_disp} Cr")

            # Ticker presence
            has_word = bool(t and title and re.search(rf"\b{re.escape(t)}\b", title, re.I))
            reasons.append("ticker in title" if has_word else "no exact ticker")

            # Dedup
            dups = dup.get(title, 1)
            if dups > 1:
                reasons.append(f"dedup x{dups}")

            # Source cue
            dom = (r.get("top_source") or "").lower()
            for key in ("reuters.com", "livemint.com", "economictimes.indiatimes.com", "business-standard.com", "thehindubusinessline.com"):
                if key in dom:
                    reasons.append(key.split(".")[0])
                    break

            reason = "; ".join(reasons[:3])

        # Format display with enhanced metrics
        company_name = get_company_name(t)
        
        print(f"\n{i}. {t} ({company_name if company_name != t else 'Company'})")
        print(f"   {'─'*86}")
        print(f"   💯 Certainty: {certainty}%  |  📈 Expected Rise: {rise_min}-{rise_max}% ({rise_conf})")
        
        if float(magnitude) > 0:
            print(f"   💼 Deal Size: ₹{magnitude} crore")
        
        print(f"   🛡️  Fake Rally Risk: {fake_risk}")
        print(f"   📊 Score: {k}  |  Articles: {r.get('articles', '1')}")
        print(f"   📰 {title[:80]}...")
        
        if reason:
            print(f"   🔍 Signals: {reason}")


def prompt_yes_no(msg: str) -> bool:
    try:
        # Auto-apply config prompt
        if "Apply recommended ranking_config.json changes" in msg and AUTO_APPLY_CONFIG:
            print(msg + " [y/N]: y (auto)")
            return True
        # Auto-run screener prompt
        if "Run institutional+technicals screener" in msg and AUTO_SCREENER:
            print(msg + " [y/N]: y (auto)")
            return True
        ans = input(msg + " [y/N]: ").strip().lower()
        return ans in ("y", "yes")
    except EOFError:
        return False


def main() -> None:
    global AUTO_APPLY_CONFIG, AUTO_SCREENER, FORCE_PATH
    # CLI args
    ap = argparse.ArgumentParser(description="Two-Path Orchestrator: Script vs AI")
    ap.add_argument("--path", choices=["ai", "script"], help="Force path selection without prompt")
    ap.add_argument("--auto-apply-config", action="store_true", help="Auto-apply recommended ranking config changes")
    ap.add_argument("--auto-screener", action="store_true", help="Auto-run institutional screener after ranking")
    ap.add_argument("--top", type=int, default=25, help="Top N to show (and feed to screener)")
    ap.add_argument("--fresh", action="store_true", help="Fetch fresh news before ranking (uses enhanced collector)")
    ap.add_argument("--hours", type=int, default=24, help="Hours back for fresh news fetch (default: 24)")
    ap.add_argument("--tickers-file", type=str, default=None, help="Ticker file to use for fresh news fetch (default: sec_tickers.txt)")
    ap.add_argument("--deadline-mins", type=int, default=15, help="Time budget in minutes for AI + learning after fetch (default: 15)")
    args, unknown = ap.parse_known_args()
    AUTO_APPLY_CONFIG = bool(args.auto_apply_config)
    AUTO_SCREENER = bool(args.auto_screener)
    FORCE_PATH = args.path
    print("Two-Path Orchestrator: Script Path vs AI Path")

    # Optional fresh fetch
    ai_deadline_ts = None
    if args.fresh:
        fresh_fetch_news(hours_back=args.hours, tickers_file=args.tickers_file)
        import time
        ai_deadline_ts = time.time() + (args.deadline_mins * 60)
    agg = find_latest_aggregated()
    if not agg or not os.path.exists(agg):
        print("[!] No aggregated_full_articles_* file found in this folder.")
        print("    Fetch news first, e.g. (48h, full NSE tickers):")
        print("    python .\\enhanced_india_finance_collector.py --tickers-file sec_tickers.txt --hours-back 48 --max-articles 2 --no-per-ticker --sources reuters.com livemint.com economictimes.indiatimes.com business-standard.com moneycontrol.com thehindubusinessline.com financialexpress.com cnbctv18.com zeebiz.com --output-file aggregated_full_articles_48h")
        sys.exit(1)
    print(f"Using aggregated: {os.path.basename(agg)}")

    # Choose path
    print("\nChoose path:\n  1) Script Path (original rules)\n  2) AI Path (entity-aware, dedup, magnitude)")
    if FORCE_PATH == "script":
        choice = "1"
    elif FORCE_PATH == "ai":
        choice = "2"
    else:
        try:
            choice = input("Enter 1 or 2 [default 2]: ").strip()
        except EOFError:
            choice = "2"
    if choice not in ("1", "2", ""):
        print("Invalid choice; defaulting to 2 (AI Path)")
        choice = "2"
    if choice == "1":
        # Script Path
        csv_path = run_screen_full_articles(agg, top=max(25, args.top * 12))
        rows = load_news_csv(csv_path)
        rows.sort(key=lambda r: float(r.get("combined_score") or 0.0), reverse=True)
        top = rows[: args.top]
        print_top(top, key_field="combined_score")
        out_csv = csv_path
        label = "Script Path"
        key_field = "combined_score"
    else:
        # AI Path: ensure base CSV exists; create if missing
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        csv_path = os.path.join(OUTPUTS_DIR, "all_news_screen.csv")
        # Ensure CSV exists and is not header-only; rebuild if needed
        need_build = False
        if not os.path.exists(csv_path):
            need_build = True
        else:
            try:
                with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
                    line_count = sum(1 for _ in f)
                if line_count < 2:
                    need_build = True
            except Exception:
                need_build = True
        if need_build:
            run_screen_full_articles(agg, top=max(25, args.top * 12))
        top, out_csv = AI_ADJUST_RANK(csv_path, top_n=args.top)
        print_top(top, key_field="adj_score")
        label = "AI Path"
        key_field = "adj_score"

        # Update learning DB and learning context
        try:
            os.makedirs(LEARNING_DIR, exist_ok=True)
            db_path = os.path.join(LEARNING_DIR, "learning.db")
            learning_db.ensure_db(db_path)
            run_id = learning_db.update_from_ai_results(db_path, top, agg)
            learning_md = os.path.join(LEARNING_DIR, "learning_context.md")
            learning_db.generate_context_update(db_path, learning_md, run_id)
            # Generate debate & recommendations and preview a config file to apply
            debate_md = os.path.join(LEARNING_DIR, "learning_debate.md")
            os.makedirs(OUTPUTS_DIR, exist_ok=True)
            rec_json = os.path.join(OUTPUTS_DIR, f"ranking_config_recommendation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            learning_db.generate_debate_and_recommendations(db_path, run_id, debate_md, rec_json)
            print(f"Learning DB updated: {db_path}\nContext appended: {learning_md}\nDebate & recommendations: {debate_md}\nProposed config: {rec_json}")

            # Price evaluation (post-news returns). Best efforts only.
            import time
            if (ai_deadline_ts is None) or (time.time() < ai_deadline_ts - 60):  # reserve 60s buffer
                print("Evaluating post-news price reactions (1d/3d/5d)…")
                evals = price_eval.evaluate_reactions(top, agg)
                if evals:
                    # Persist into DB and update reliability counters
                    try:
                        con = __import__('sqlite3').connect(db_path)
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
                            # Update ticker_stats reliability
                            cur.execute("SELECT success_2p, fake_rise_cnt, appearances FROM ticker_stats WHERE ticker=?", (e['ticker'],))
                            row = cur.fetchone()
                            if row is None:
                                succ = 0; fake = 0; apps = 0
                            else:
                                succ = int(row[0] or 0); fake = int(row[1] or 0); apps = int(row[2] or 0)
                            succ += int(e.get('consistent') or 0)
                            fake += int(e.get('fake') or 0)
                            # reliability: successes minus 1.25*fake scaled by appearances+1
                            denom = max(1, apps)
                            rel = (succ - 1.25 * fake) / float(denom)
                            cur.execute(
                                """
                                UPDATE ticker_stats SET success_2p=?, fake_rise_cnt=?, reliability_score=? WHERE ticker=?
                                """,
                                (succ, fake, rel, e['ticker'])
                            )
                        con.commit()
                        con.close()
                        print(f"Price evaluation saved: {len(evals)} items. Reliability updated.")
                    except Exception as e2:
                        print(f"[warn] Could not persist price evaluation: {e2}")
                else:
                    print("[info] Price evaluation skipped or no data (network limits).")
            else:
                print("[time] Skipping price evaluation to meet 15-minute deadline.")

            # Mandatory: present-day feedback using live prices and news certainty/trust
            try:
                from orchestrator.config import load_config as _cfg_load
                cfg = _cfg_load()
                src_bonus = (cfg.get("source_bonus", {}) or {})
            except Exception:
                src_bonus = {}

            def _event_baseline(ev: str) -> float:
                e = (ev or '').lower()
                if e.startswith('ipo') or 'listing' in e:
                    return 0.65
                if 'm&a' in e or 'jv' in e:
                    return 0.7
                if 'order' in e or 'contract' in e or 'tender' in e or 'project' in e or 'deal' in e:
                    return 0.8
                if 'regulatory' in e or 'approval' in e:
                    return 0.75
                if 'results' in e or 'metrics' in e:
                    return 0.55
                if 'block deal' in e:
                    return 0.45
                if 'management' in e:
                    return 0.4
                return 0.35

            from math import sqrt
            def _clamp(v: float, lo: float, hi: float) -> float:
                return lo if v < lo else hi if v > hi else v

            # Map ticker -> top row metadata
            meta = {}
            for r in top:
                t = (r.get("ticker") or "").strip().upper()
                if t and t not in meta:
                    meta[t] = r

            # Fetch live returns
            live_rows = price_eval.evaluate_live(top)
            if not live_rows:
                # Fallback: create placeholders to keep feedback mandatory
                from datetime import datetime as _dt
                live_rows = [{
                    'ticker': (r.get('ticker') or '').strip().upper(),
                    'symbol': (r.get('ticker') or '').strip().upper() + '.NS',
                    'asof': _dt.now().strftime('%Y-%m-%dT%H:%M:%S'),
                    'price': None,
                    'prev_close': None,
                    'live_ret': None,
                } for r in top]
            # Enrich with certainty/trust and persist
            # Pull reliability for these tickers
            reliability = {}
            try:
                con = __import__('sqlite3').connect(db_path)
                cur = con.cursor()
                tickers = [ (row.get('ticker') or '').strip().upper() for row in live_rows ]
                if tickers:
                    qmarks = ",".join(["?"] * len(tickers))
                    cur.execute(f"SELECT ticker, reliability_score FROM ticker_stats WHERE ticker IN ({qmarks})", tickers)
                    for tk, rel in cur.fetchall():
                        reliability[(tk or '').upper()] = float(rel or 0.0)
                con.close()
            except Exception:
                reliability = {}

            enriched = []
            for lr in live_rows:
                t = (lr.get("ticker") or "").strip().upper()
                info = meta.get(t, {})
                ev = (info.get("event_type") or "").strip() or "General"
                title = (info.get("top_title") or "").strip()
                src = (info.get("top_source") or "").strip().lower()
                has_word = str(info.get("has_word") or '').lower() in ("1", "true", "yes")
                try:
                    dups = int(info.get("dups") or 1)
                except Exception:
                    dups = 1
                base = _event_baseline(ev)
                name_factor = 1.0 if has_word else 0.85
                dups_factor = (1.0 / float(max(1, dups))) ** 0.5
                s_boost = 0.0
                for dom, b in (src_bonus.items() if isinstance(src_bonus, dict) else []):
                    if dom.lower() in src:
                        try:
                            s_boost = max(s_boost, float(b))
                        except Exception:
                            pass
                src_factor = 1.0 + _clamp(s_boost, 0.0, 0.1)
                news_certainty = _clamp(base * name_factor * dups_factor * src_factor, 0.0, 1.2)
                rel = float(reliability.get(t, 0.0))
                rel_scaled = _clamp((rel + 1.0) / 2.0, 0.0, 1.0)
                trust = _clamp(0.7 * news_certainty + 0.3 * rel_scaled, 0.0, 1.0)
                row_out = dict(lr)
                row_out.update({
                    "source": src,
                    "event_type": ev,
                    "title": title,
                    "news_certainty": news_certainty,
                    "trust_score": trust,
                })
                enriched.append(row_out)

            # Save live feedback and export CSV
            if enriched:
                try:
                    learning_db.save_live_feedback(db_path, run_id, enriched)
                except Exception as ee:
                    print(f"[warn] Could not persist live feedback: {ee}")
                try:
                    import csv as _csv
                    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
                    out_csv_fb = os.path.join(OUTPUTS_DIR, f"feedback_live_{ts}.csv")
                    with open(out_csv_fb, 'w', newline='', encoding='utf-8') as f:
                        w = _csv.DictWriter(f, fieldnames=[
                            'ticker','asof','price','prev_close','live_ret','news_certainty','trust_score','event_type','title','source'
                        ])
                        w.writeheader()
                        for r in enriched:
                            w.writerow({
                                'ticker': r.get('ticker'),
                                'asof': r.get('asof'),
                                'price': r.get('price'),
                                'prev_close': r.get('prev_close'),
                                'live_ret': r.get('live_ret'),
                                'news_certainty': f"{float(r.get('news_certainty') or 0.0):.3f}",
                                'trust_score': f"{float(r.get('trust_score') or 0.0):.3f}",
                                'event_type': r.get('event_type'),
                                'title': r.get('title'),
                                'source': r.get('source'),
                            })
                    print(f"Live feedback saved: {len(enriched)} items -> {out_csv_fb}")
                except Exception as ee:
                    print(f"[warn] Could not write live feedback CSV: {ee}")

            # Ask whether to apply proposed config immediately
            if prompt_yes_no("Apply recommended ranking_config.json changes now?"):
                try:
                    import shutil
                    shutil.copyfile(rec_json, os.path.join(BASE_DIR, "ranking_config.json"))
                    print("Applied recommended config changes.")
                except Exception as ee:
                    print(f"[warn] Could not apply config: {ee}")
        except Exception as e:
            print(f"[warn] Learning DB update failed: {e}")

    # Optional institutional screener
    # Only run screener if within deadline or no deadline set
    import time
    if ((ai_deadline_ts is None) or (time.time() < ai_deadline_ts - 60)) and prompt_yes_no("Run institutional+technicals screener on this shortlist now?"):
        # Build a temp ticker file from the top list
        tickers = [ (r.get("ticker") or "").strip().upper() for r in (top if isinstance(top, list) else []) ]
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
        tfile = os.path.join(OUTPUTS_DIR, "tickers_news_top25.txt")
        with open(tfile, "w", encoding="utf-8") as f:
            f.write("\n".join(tickers))
        print(f"Shortlist written: {tfile}")

        screener = os.path.join(BASE_DIR, "swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_txt = os.path.join(OUTPUTS_DIR, f"swing_top25_{ts}.txt")
        cmd = [
            sys.executable,
            screener,
            "--top", str(args.top),
            "--soft-mode",
            "--skip-5min",
            "--enhanced-analytics",
            "--institutional-filters",
            "--ticker-file", tfile,
            "--ticker-count", "25",
            "--csv-enhanced",
        ]
        print("Running institutional screener (rate-limited yfinance)…")
        try:
            with open(out_txt, "w", encoding="utf-8") as outf:
                proc = subprocess.run(cmd, stdout=outf, stderr=subprocess.STDOUT, check=False)
            print(f"Screener finished with code {proc.returncode}; output saved: {out_txt}")
            if proc.returncode != 0:
                print("[warn] Screener returned a non-zero code (likely due to network limits). Output file still created.")
        except Exception as e:
            print(f"[error] Screener execution failed: {e}")
    else:
        print(f"{label} complete. CSV: {out_csv}")

    # Maintenance: organize base directory clutter and archive old outputs
    try:
        moved_count, moved_details = organize_workspace(BASE_DIR)
        if moved_count:
            print(f"[organize] Moved {moved_count} items into organized folders.")
        a, d = archive_old_outputs(min_age_hours=24)
        if a or d:
            print(f"[archive] Archived {a} and deleted {d} old output files.")
        # Analyze outputs and write suggestions
        sug_path, rec_cfg = analyze_and_suggest()
        print(f"[suggest] Wrote suggestions: {sug_path}")
    except Exception as e:
        print(f"[warn] Archiving failed: {e}")


if __name__ == "__main__":
    # Ensure UTF-8 output on Windows consoles
    try:
        import sys
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    main()
