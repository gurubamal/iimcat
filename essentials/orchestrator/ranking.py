from __future__ import annotations

import csv
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple

from orchestrator.config import load_config, OUTPUTS_DIR, load_entities
import math


# Company name lookup cache
_COMPANY_NAME_CACHE: Dict[str, str] = {}

def load_company_names() -> Dict[str, str]:
    """Load ticker to company name mapping from sec_list.csv"""
    global _COMPANY_NAME_CACHE
    if _COMPANY_NAME_CACHE:
        return _COMPANY_NAME_CACHE
    
    # Look for sec_list.csv in the parent directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(current_dir)
    sec_list_path = os.path.join(base_dir, "sec_list.csv")
    
    if not os.path.exists(sec_list_path):
        return {}
    
    try:
        with open(sec_list_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    ticker = row[0].strip()
                    company_name = row[1].strip()
                    _COMPANY_NAME_CACHE[ticker] = company_name
    except Exception:
        pass
    
    return _COMPANY_NAME_CACHE

def get_company_name(ticker: str) -> str:
    """Get full company name for a ticker symbol"""
    company_names = load_company_names()
    return company_names.get(ticker.upper(), ticker)


def parse_amount_crore(title: str) -> float:
    if not title:
        return 0.0
    t = title.strip()
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


def calculate_relative_magnitude(title: str, ticker: str) -> float:
    """Calculate news magnitude relative to company market cap for true impact assessment"""
    news_amount_cr = parse_amount_crore(title)
    
    if news_amount_cr <= 0:
        return 0.0
    
    try:
        import yfinance as yf
        symbol = f"{ticker}.NS" if not ticker.endswith('.NS') else ticker
        stock = yf.Ticker(symbol)
        info = stock.info
        market_cap = info.get('marketCap', 0)
        
        if market_cap <= 0:
            return 0.0
            
        market_cap_cr = market_cap / 1e7  # Convert to crores
        
        # Calculate relative impact as percentage of market cap
        relative_impact = (news_amount_cr / market_cap_cr) * 100
        
        # Cap at reasonable maximum (50% of market cap)
        return min(relative_impact, 50.0)
        
    except Exception:
        # Fallback: use absolute amount with small scaling
        return min(news_amount_cr / 1000.0, 5.0)  # Max 5% equivalent for large absolute amounts


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


INST_CUES_RE = re.compile(
    r"\b(FII|FPI|DII|mutual fund|institutional|QIB|anchor investor|AIF|block deal|bulk deal)s?\b",
    re.I,
)

CIRCUIT_LOWER_RE = re.compile(r"\blower circuit(s)?\b", re.I)
CIRCUIT_UPPER_RE = re.compile(r"\bupper circuit(s)?\b", re.I)
LIVE_UPDATES_RE = re.compile(r"(live updates|share price live)", re.I)
LISTICLE_RE = re.compile(r"(stocks? to watch|stocks? in focus|top stocks? (today|for the day))", re.I)

# --- Dynamic entity precision (no hard-coded mapping required) ---
_ALIAS_CACHE: Dict[str, List[str]] = {}
_STOPWORDS = {
    'limited','ltd','inc','co','company','industries','industry','india','the','and','&','private','pvt','corp','corporation','plc','group','science','sciences','pharma','pharmaceuticals','bank','financial','finance','services','technology','technologies','global','intl','international'
}

def _tokenize(text: str) -> List[str]:
    s = re.sub(r"[^a-z0-9\s]"," ", (text or '').lower())
    toks = [t for t in s.split() if t and t not in _STOPWORDS and len(t) > 1]
    return toks

def _get_company_aliases(ticker: str) -> List[str]:
    from typing import Set
    if ticker in _ALIAS_CACHE:
        return _ALIAS_CACHE[ticker]
    aliases: Set[str] = set()
    # Basic alias: split ticker tokens
    aliases.update(_tokenize(ticker))
    # Add tokens from local company name mapping (sec_list.csv)
    try:
        name = get_company_name(ticker)
        if name and name.upper() != ticker.upper():
            aliases.update(_tokenize(name))
    except Exception:
        pass
    # Try yfinance for long/short names
    try:
        import yfinance as yf
        sym = _ensure_ns(ticker)
        info = yf.Ticker(sym).info or {}
        for k in ('longName','shortName'):  # type: ignore
            if k in info and info[k]:
                aliases.update(_tokenize(str(info[k])))
        # From website domain
        if 'website' in info and info['website']:
            host = re.sub(r"^https?://","", info['website']).split('/')[0]
            base = host.split('.')[-2] if '.' in host else host
            aliases.update(_tokenize(base))
    except Exception:
        pass
    # Cache and return
    _ALIAS_CACHE[ticker] = list(aliases)
    return _ALIAS_CACHE[ticker]

def _entity_precision_factor(title: str, ticker: str) -> float:
    """Return a factor in [0.5, 1.1] based on how precisely the title refers to the company.
    - Boost slightly if multiple alias tokens appear; penalize if none and generic/fund context.
    """
    toks = set(_tokenize(title))
    aliases = set(_get_company_aliases(ticker))
    if not toks:
        return 1.0
    overlap = len(toks & aliases)
    # Penalize fund/PE context when overlap is weak
    fund_context = bool(re.search(r"\b(fund|funds|global management|private equity|pe firm)\b", title.lower()))
    if overlap >= 2:
        return 1.05  # small boost for strong name match
    if overlap == 1 and not fund_context:
        return 1.0
    # Weak overlap
    return 0.7 if fund_context else 0.85


def _ensure_ns(sym: str) -> str:
    s = (sym or "").strip().upper()
    return s if "." in s else f"{s}.NS"

def resolve_ambiguous_ticker(title: str, ticker: str) -> str:
    """Multi-strategy entity resolution with rejection capability.
    Stage 1: Exact company name matching
    Stage 2: Operating company preference over ETFs
    Stage 3: Contextual disambiguation with rejection
    """
    tkr = (ticker or "").upper().strip()
    company_names = load_company_names()
    if not tkr:
        return tkr
    
    title_lower = (title or "").lower()
    title_tokens = set(_tokenize(title))
    
    # Stage 1: Exact company name matching (highest priority)
    for candidate_ticker, company_name in company_names.items():
        # Extract main company name (before LIMITED/LTD/etc)
        main_name = re.sub(r'\s+(limited|ltd|pvt|private|corp|corporation|inc).*$', '', company_name, flags=re.I)
        name_words = [w for w in main_name.lower().split() if len(w) > 3]
        
        if len(name_words) >= 2:
            # Multi-word company: check exact and fuzzy matches
            exact_matches = [word for word in name_words if word in title_lower]
            fuzzy_matches = []
            
            # Check fuzzy matches for remaining words
            for word in name_words:
                if word not in exact_matches:
                    for title_word in title_lower.split():
                        if len(word) > 4 and len(title_word) > 3:
                            if word.startswith(title_word) or title_word.startswith(word[:4]):
                                fuzzy_matches.append(word)
                                break
            
            total_matches = len(exact_matches) + len(fuzzy_matches)
            if total_matches >= len(name_words):  # All words matched (exact or fuzzy)
                return candidate_ticker
                
        elif len(name_words) == 1 and len(name_words[0]) > 5:
            # Single distinctive word (6+ chars) - exact match
            if name_words[0] in title_lower:
                return candidate_ticker
    
    # Stage 2: Operating company preference over ETFs/Funds
    if tkr in company_names:
        current_name = company_names[tkr].lower()
        is_etf = any(pattern in current_name for pattern in ['etf', 'fund', 'index', 'mutual'])
        
        if is_etf:
            # Check if this is company-specific news (should not go to ETF)
            company_signals = ['ceo', 'acquisition', 'merger', 'revenue', 'profit', 'quarter', 'shares rise', 'shares fall']
            if any(signal in title_lower for signal in company_signals):
                # Look for operating company alternative using original algorithm
                root_tokens = set(_tokenize(tkr))
                candidates = []
                
                for cand, cname in company_names.items():
                    # Skip ETFs in candidates
                    if any(pattern in cname.lower() for pattern in ['etf', 'fund', 'index', 'mutual']):
                        continue
                    nm = (cname or "").lower()
                    if any(rt in nm for rt in root_tokens):
                        candidates.append(cand)
                
                # Score candidates by alias overlap
                best = tkr
                best_score = 0
                for cand in candidates:
                    aliases = set(_get_company_aliases(cand))
                    exact_score = len(title_tokens & aliases)
                    fuzzy_score = 0
                    for alias in aliases:
                        for title_token in title_tokens:
                            if (len(alias) > 3 and len(title_token) > 3 and 
                                (alias.startswith(title_token[:4]) or title_token.startswith(alias[:4]))):
                                fuzzy_score += 0.5
                    
                    total_score = exact_score + fuzzy_score
                    if total_score > best_score:
                        best_score = total_score
                        best = cand
                
                # Return operating company if found with reasonable confidence
                if best != tkr and best_score >= 0.5:
                    return best
                
                # If no good operating company found, reject the ETF mapping
                # This prevents confident misattribution
                return "REJECTED_" + tkr
    
    # Stage 3: Original logic for non-ETF cases
    if tkr not in company_names:
        # Use the raw token(s) of the ambiguous label to find a family of candidates
        root_tokens = set(_tokenize(tkr))
        if not root_tokens:
            return tkr
        candidates = []
        for cand, cname in company_names.items():
            nm = (cname or "").lower()
            # Candidate if any root token appears in the company name
            if any(rt in nm for rt in root_tokens):
                candidates.append(cand)
        
        if candidates:
            # Score by alias overlap with title (with fuzzy matching for geographic terms)
            best = tkr
            best_score = 0
            for cand in candidates:
                aliases = set(_get_company_aliases(cand))
                # Exact token overlap
                exact_score = len(title_tokens & aliases)
                # Fuzzy geographic matching (italy/italian, etc.)
                fuzzy_score = 0
                for alias in aliases:
                    for title_token in title_tokens:
                        if (len(alias) > 3 and len(title_token) > 3 and 
                            (alias.startswith(title_token[:4]) or title_token.startswith(alias[:4]))):
                            fuzzy_score += 0.5
                
                total_score = exact_score + fuzzy_score
                if total_score > best_score:
                    best_score = total_score
                    best = cand
            
            # Require at least a minimal overlap to remap (accepting fuzzy matches too)
            if best != tkr and best_score >= 0.5:
                return best
    
    return tkr


def try_profit_growth(ticker: str) -> float:
    """Best-effort quarterly profit growth (%). Returns 0 if unavailable.
    Computes latest YoY growth if possible, else sequential.
    """
    try:
        import yfinance as yf
        sym = _ensure_ns(ticker)
        tk = yf.Ticker(sym)
        qis = getattr(tk, 'quarterly_income_stmt', None)
        if qis is None or qis.empty:
            return 0.0
        # Prefer Net Income
        label = None
        for cand in ("Net Income", "NetIncome", "Net Income Applicable To Common Shares"):
            if cand in qis.index:
                label = cand
                break
        if not label:
            return 0.0
        s = qis.loc[label].dropna()
        if len(s) < 2:
            return 0.0
        latest = float(s.iloc[0]); prev = float(s.iloc[1])
        if prev == 0:
            return 0.0
        return max(-100.0, min(300.0, (latest - prev) / abs(prev) * 100.0))
    except Exception:
        return 0.0


def top_reasons(title: str, ticker: str, has_word: bool, dups: int, cr: float, source: str) -> str:
    reasons: List[str] = []
    ev = classify_event(title)
    if ev != "General":
        reasons.append(ev)
    
    # Show relative impact if available
    relative_impact = calculate_relative_magnitude(title, ticker)
    if relative_impact > 0:
        reasons.append(f"~{relative_impact:.1f}% mcap impact")
    elif cr > 0:
        cr_disp = f"{cr:.0f}" if cr >= 100 else f"{cr:.1f}"
        reasons.append(f"~₹{cr_disp} Cr")
    
    reasons.append("ticker in title" if has_word else "no exact ticker")
    if dups > 1:
        reasons.append(f"dedup x{dups}")
    dom = (source or "").lower()
    src_tag = None
    for key in ("reuters.com", "livemint.com", "economictimes.indiatimes.com", "business-standard.com", "thehindubusinessline.com"):
        if key in dom:
            src_tag = key.split(".")[0]
            break
    if src_tag:
        reasons.append(src_tag)
    return "; ".join(reasons[:3]) or "news impact"


def load_news_csv(csv_path: str) -> List[Dict[str, str]]:
    with open(csv_path, "r", encoding="utf-8") as f:
        rdr = csv.DictReader(f)
        return [row for row in rdr]


def ai_adjust_rank(csv_path: str, top_n: int = 25) -> Tuple[List[Dict[str, str]], str]:
    rows = load_news_csv(csv_path)
    cfg = load_config()
    entities = load_entities()
    dedup_exp = float(cfg.get("dedup_exponent", 1.0))
    name_missing = float(cfg.get("name_factor_missing", 0.75))
    name_short = float(cfg.get("name_factor_short_ticker", 0.6))
    mag_cap = float(cfg.get("magnitude_cap", 0.5))
    mag_div = float(cfg.get("magnitude_log_divisor", 6.0))
    src_bonus: Dict[str, float] = cfg.get("source_bonus", {}) or {}
    ev_bonus: Dict[str, float] = cfg.get("event_bonus", {}) or {}
    tkr_penalty: Dict[str, float] = cfg.get("ticker_penalty", {}) or {}

    # Build duplicate counts by title
    dup: Dict[str, int] = {}
    for r in rows:
        title = (r.get("top_title") or "").strip()
        if title:
            dup[title] = dup.get(title, 0) + 1

    adjusted: List[Tuple[float, Dict[str, str]]] = []
    for r in rows:
        ticker = (r.get("ticker") or "").strip().upper()
        title = (r.get("top_title") or "").strip()
        try:
            base = float(r.get("combined_score") or 0.0)
        except ValueError:
            base = 0.0

        # Dedup
        dups = max(1, dup.get(title, 1))
        dedup_factor = (1.0 / float(dups)) ** max(0.0, dedup_exp)

        # Resolve ambiguity generically using local company names and alias overlap
        orig_ticker = ticker
        ticker = resolve_ambiguous_ticker(title, ticker)
        
        # Filter out rejected mappings
        if ticker.startswith("REJECTED_"):
            continue  # Skip this row entirely

        # Name factor
        has_word = False
        if ticker and title and re.search(rf"\b{re.escape(ticker)}\b", title, re.I):
            has_word = True
        if has_word:
            name_factor = 1.0
        elif len(ticker) <= 2:
            name_factor = name_short
        else:
            name_factor = name_missing

        # Fund/PE penalty context
        if title and re.search(r"\bfund(s)?\b", title, re.I) and not re.search(
            r"limited|ltd|industr|labs|hospitals|company|bank|motors|pharma|energy|steel|cement|infra",
            title,
            re.I,
        ):
            name_factor *= 0.8

        # Magnitude boost (relative impact-based)
        cr = parse_amount_crore(title)
        relative_impact = calculate_relative_magnitude(title, ticker)
        
        # Use relative impact for more meaningful magnitude scoring
        if relative_impact > 0:
            # Scale: 1% market cap impact = significant boost
            mag_factor = 1.0 + min(mag_cap, relative_impact / 100.0 * 10.0)  # 1% impact = 10% boost
        else:
            # Fallback to absolute amount for non-financial news
            mag_factor = 1.0 + min(mag_cap, (0.0 if cr <= 0 else (max(0.0, __import__("math").log10(1.0 + cr)) / max(1e-6, mag_div))))

        # Source bonus
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

        # Live updates hard penalty
        live_penalty = 1.0
        if LIVE_UPDATES_RE.search(title or ""):
            # Hard penalty of -30%
            live_penalty = 0.7
        # Generic listicles (not specific corporate events) penalty
        if LISTICLE_RE.search(title or ""):
            live_penalty *= 0.8  # additional -20%

        # Event factor
        ev = classify_event(title)
        event_bonus = 0.0
        try:
            event_bonus = float(ev_bonus.get(ev, 0.0))
        except Exception:
            event_bonus = 0.0
        ev_factor = 1.0 + max(0.0, event_bonus)

        # Ticker penalty
        pen = 0.0
        try:
            pen = float(tkr_penalty.get(ticker, 0.0))
        except Exception:
            pen = 0.0
        pen_factor = 1.0 + min(0.0, pen)

        # Additional features (small multipliers)
        fw = cfg.get("feature_weights", {}) or {}
        fc = cfg.get("feature_caps", {}) or {}
        # Institutional cues from title
        inst_hits = 1 if INST_CUES_RE.search(title or "") else 0
        inst_boost = min(float(fw.get("inst_cues", 0.0)) * inst_hits, float(fc.get("inst_cues_max", 0.05)))
        # FII/DII cues (same regex)
        fii_dii_hits = inst_hits
        fii_dii_boost = min(float(fw.get("fii_dii_cues", 0.0)) * fii_dii_hits, float(fc.get("fii_dii_cues_max", 0.04)))
        # Circuit cues
        lower = 1 if CIRCUIT_LOWER_RE.search(title or "") else 0
        upper = 1 if CIRCUIT_UPPER_RE.search(title or "") else 0
        circ_boost = max(
            -float(fc.get("circuit_abs_max", 0.02)),
            min(
                float(fw.get("circuit_lower", 0.0)) * lower + float(fw.get("circuit_upper", 0.0)) * upper,
                float(fc.get("circuit_abs_max", 0.02)),
            ),
        )
        # Profit growth factor (scaled)
        pg = try_profit_growth(ticker)
        pg_norm = max(-0.5, min(0.5, (pg / 100.0)))  # cap to [-50%, 50%] normalized
        pg_boost = min(max(0.0, pg_norm) * float(fw.get("profit_growth", 0.0)), float(fc.get("profit_growth_max", 0.10)))

        extra_factor = 1.0 + inst_boost + fii_dii_boost + circ_boost + pg_boost

        # Entity mapping rules (hard precision) + dynamic precision penalty
        ent = entities.get(ticker, {}) if isinstance(entities, dict) else {}
        if ent:
            tx = f"{title} \n {r.get('top_title') or ''} {r.get('top_source') or ''}".lower()
            # Exclusions
            for ex in ent.get('exclude_phrases', []) or []:
                if ex.lower() in tx:
                    extra_factor *= 0.5  # 50% penalty if excluded phrase present
                    break
            # Requirements (if defined)
            req = ent.get('require_any', []) or []
            if req and not any(kw.lower() in tx for kw in req):
                extra_factor *= 0.6  # 40% penalty if required keywords not present
        # Penalize unresolved ambiguous label (ticker not in local company list)
        if orig_ticker == ticker and ticker not in load_company_names():
            extra_factor *= 0.7  # 30% penalty for unresolved entity

        # Dynamic precision factor (no hard-coding)
        extra_factor *= _entity_precision_factor(title or '', ticker)

        adj = base * dedup_factor * name_factor * mag_factor * src_factor * live_penalty * ev_factor * pen_factor * extra_factor
        r_out = dict(r)
        r_out["adj_score"] = f"{adj:.6f}"
        r_out["dups"] = str(dups)
        r_out["has_word"] = str(has_word)
        r_out["amt_cr"] = f"{cr:.3f}"
        r_out["event_type"] = ev
        r_out["reason"] = top_reasons(title, ticker, has_word, dups, cr, (r.get("top_source") or ""))
        # Persist remapped ticker for output
        r_out["ticker"] = ticker
        adjusted.append((adj, r_out))

    adjusted.sort(key=lambda x: x[0], reverse=True)
    top = [row for _, row in adjusted[:top_n]]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    try:
        os.makedirs(OUTPUTS_DIR, exist_ok=True)
    except Exception:
        pass
    out_csv = os.path.join(OUTPUTS_DIR, f"ai_adjusted_top{top_n}_{ts}.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "ticker",
                "company_name",
                "combined_score",
                "adj_score",
                "articles",
                "dups",
                "has_word",
                "amt_cr",
                "reason",
                "event_type",
                "top_title",
                "top_source",
            ],
        )
        w.writeheader()
        for row in top:
            ticker = row.get("ticker", "")
            w.writerow({
                "ticker": ticker,
                "company_name": get_company_name(ticker),
                "combined_score": row.get("combined_score"),
                "adj_score": row.get("adj_score"),
                "articles": row.get("articles"),
                "dups": row.get("dups"),
                "has_word": row.get("has_word"),
                "amt_cr": row.get("amt_cr"),
                "reason": row.get("reason"),
                "event_type": row.get("event_type"),
                "top_title": row.get("top_title"),
                "top_source": row.get("top_source"),
            })
    return top, out_csv
