#!/usr/bin/env python3
"""
Local Codex shell bridge (no external API).

Reads an analysis prompt from stdin and returns a JSON object compatible with
realtime_ai_news_analyzer.py expected schema. Internally uses the built-in
heuristic analyzer so Stage 2 can run without API keys.

NOW WITH INTERNET ACCESS:
- Handles connectivity probe requests (fetches URL and returns SHA256)
- Extracts article URLs from analysis prompts and fetches actual content
- Analyzes real article text, not just headlines

Environment:
- Optionally set AI_SHELL_INSTRUCTION to include custom guidance text.

Usage:
  export CODEX_SHELL_CMD="python3 codex_bridge.py"
  export AI_PROVIDER=codex
  ./run_realtime_ai_scan.sh nifty50_tickers.txt 48
"""

import sys
import json
import re
import hashlib
from typing import Optional

# Import AI conversation logger for QA
try:
    from ai_conversation_logger import log_ai_conversation
except ImportError:
    # Fallback if logger is not available
    def log_ai_conversation(*args, **kwargs):
        pass

def fetch_url(url: str, timeout: int = 10) -> Optional[bytes]:
    """Fetch URL content with timeout."""
    try:
        import requests
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None

def handle_probe_request(prompt: str) -> Optional[dict]:
    """Detect and handle connectivity probe requests.
    
    Probe format: "Fetch the exact bytes at URL: <url>... Return ONLY valid JSON with this shape: {"sha256":"<hex>"}"
    """
    # Check if this is a probe request
    if "Fetch the exact bytes at URL:" in prompt and '"sha256"' in prompt:
        # Extract URL from probe prompt
        match = re.search(r'URL:\s*(https?://[^\s\n]+)', prompt)
        if match:
            url = match.group(1)
            content = fetch_url(url)
            if content:
                sha = hashlib.sha256(content).hexdigest()
                return {"sha256": sha}
            else:
                return {"sha256": None, "error": "failed to fetch URL"}
    return None


def handle_ticker_validation(prompt: str) -> Optional[dict]:
    """Detect and handle local ticker validation prompts.

    Expects a prompt that asks to check if 'TICKER' is a valid NSE/BSE stock and to
    return a JSON with is_valid, exchange, company_name, reason. We satisfy it locally
    using sec_list.csv and valid_nse_tickers.txt.
    """
    if '"is_valid"' in prompt and '"company_name"' in prompt and 'Ticker to validate:' in prompt:
        import csv, os, re
        # Extract ticker
        m = re.search(r'Ticker to validate:\s*([A-Za-z0-9_.-]+)', prompt)
        ticker = (m.group(1).strip().upper() if m else '').replace('.NS', '')
        if not ticker:
            return {"is_valid": False, "exchange": "NONE", "company_name": "NOT FOUND", "reason": "ticker not provided"}
        # Load symbol set and names
        valid = set()
        try:
            with open('valid_nse_tickers.txt', 'r', encoding='utf-8', errors='ignore') as vf:
                for line in vf:
                    s = (line.strip() or '').upper().replace('.NS', '')
                    if s:
                        valid.add(s)
        except Exception:
            pass
        company_name = None
        try:
            with open('sec_list.csv', 'r', encoding='utf-8', errors='ignore') as cf:
                reader = csv.DictReader(cf)
                for row in reader:
                    sym = (row.get('Symbol') or '').strip().upper().replace('.NS', '')
                    nm = (row.get('Security Name') or '').strip()
                    if sym:
                        if nm:
                            if sym == ticker:
                                company_name = nm
                        valid.add(sym)
        except Exception:
            pass

        is_valid = ticker in valid
        exchange = 'NSE' if is_valid else 'NONE'
        return {
            "is_valid": bool(is_valid),
            "exchange": exchange,
            "company_name": company_name or ("NOT FOUND" if not is_valid else ticker),
            "reason": ("Found in local symbol lists" if is_valid else "Not found in local symbol lists")
        }
    return None

def extract_article_urls(prompt: str) -> list:
    """Extract article URLs from analysis prompt."""
    urls = []
    # Look for URLs in the prompt (common patterns in analysis requests)
    url_patterns = [
        r'\*\*URL\*\*:\s*(https?://[^\s\n]+)',  # Match **URL**: format
        r'(?:URL|url|link|article):\s*(https?://[^\s\n]+)',
        r'https?://(?:www\.)?(?:moneycontrol|economictimes|livemint|reuters|bloomberg)[^\s\n]+'
    ]
    for pattern in url_patterns:
        matches = re.findall(pattern, prompt)
        urls.extend(matches)
    return list(set(urls))  # Deduplicate

def _html_to_text(content: bytes) -> str:
    text = content.decode('utf-8', errors='ignore')
    # Strip scripts/styles and tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _inject_full_text(prompt: str, article_text: str) -> str:
    """Replace the **Full Text** section in the analyzer prompt with fetched article text.

    Looks for the section between '**Full Text**:' and the next '- **URL**:' line and replaces its body.
    If the section is not found, return the original prompt.
    """
    if not article_text:
        return prompt
    article_text = article_text.strip()
    if len(article_text) > 5000:
        article_text = article_text[:5000] + '... [truncated]'

    pattern = re.compile(r'(\*\*Full Text\*\*:\s*)(.*?)(\n- \*\*URL\*\*:\s*https?://)', re.DOTALL | re.IGNORECASE)

    def repl(m):
        return f"{m.group(1)}{article_text}{m.group(3)}"

    new_prompt, n = pattern.subn(repl, prompt, count=1)
    if n == 1:
        return new_prompt

    # Fallback: build a minimal prompt analyzer can parse
    try:
        tkr = re.search(r'- \*\*Ticker\*\*:\s*(\w+)', prompt).group(1)
    except Exception:
        tkr = 'UNKNOWN'
    try:
        hed = re.search(r'- \*\*Headline\*\*:\s*(.+?)(?:\n|$)', prompt).group(1).strip()
    except Exception:
        hed = ''
    try:
        url = re.search(r'- \*\*URL\*\*:\s*(https?://[^\s\n]+)', prompt).group(1).strip()
    except Exception:
        url = ''
    minimal = f"""# SWING TRADE SETUP ANALYSIS - {tkr}

## Stock Information
- **Ticker**: {tkr}
- **Headline**: {hed}
- **Full Text**: {article_text}
- **URL**: {url}
"""
    return minimal


def fetch_and_enhance_prompt(prompt: str) -> str:
    """Extract URLs, fetch content, and inject into the Full Text field for better analysis."""
    urls = extract_article_urls(prompt)
    if not urls:
        return prompt

    fetched_texts = []
    for url in urls[:3]:
        content = fetch_url(url)
        if content:
            try:
                text = _html_to_text(content)
                if text:
                    fetched_texts.append(text)
                    print(f"✅ Fetched article content from {url} ({len(text)} chars)", file=sys.stderr)
            except Exception as e:
                print(f"⚠️ Error processing content from {url}: {e}", file=sys.stderr)

    if not fetched_texts:
        return prompt

    combined = ' '.join(fetched_texts)
    return _inject_full_text(prompt, combined)

def main():
    prompt = sys.stdin.read()
    error_msg = None
    result = None
    is_probe = False

    if not prompt.strip():
        result = {
            "score": 50,
            "sentiment": "neutral",
            "impact": "medium",
            "catalysts": [],
            "deal_value_cr": 0,
            "risks": ["insufficient_input"],
            "certainty": 40,
            "recommendation": "HOLD",
            "reasoning": "No prompt content provided to shell bridge.",
            "expected_move_pct": 0,
            "confidence": 40
        }
        print(json.dumps(result))
        # Log empty prompt
        log_ai_conversation(
            provider='codex-heuristic',
            prompt=prompt,
            response=json.dumps(result, indent=2),
            metadata={'bridge': 'codex_bridge.py', 'type': 'empty_prompt'},
            error=None
        )
        return

    # Check if this is a connectivity probe request
    probe_result = handle_probe_request(prompt)
    if probe_result:
        is_probe = True
        print(json.dumps(probe_result))
        # Log probe request
        log_ai_conversation(
            provider='codex-probe',
            prompt=prompt,
            response=json.dumps(probe_result, indent=2),
            metadata={'bridge': 'codex_bridge.py', 'type': 'connectivity_probe'},
            error=None
        )
        return
    # Check if this is a local ticker validation request
    val_result = handle_ticker_validation(prompt)
    if val_result:
        print(json.dumps(val_result))
        log_ai_conversation(
            provider='codex-heuristic',
            prompt=prompt,
            response=json.dumps(val_result, indent=2),
            metadata={'bridge': 'codex_bridge.py', 'type': 'ticker_validation'},
            error=None
        )
        return

    try:
        # Enhance prompt by fetching actual article content
        enhanced_prompt = fetch_and_enhance_prompt(prompt)

        # Reuse the built-in intelligent heuristic analyzer
        import os
        import realtime_ai_news_analyzer as rt
        instr = os.getenv('AI_SHELL_INSTRUCTION', '').strip()
        # Enforce strict real-time grounding and price-first analysis guidance
        strict = (
            "STRICT REAL-TIME CONTEXT: Base your decision ONLY on the provided article text and technical context (if present). "
            "Do not use prior training knowledge or external facts. PRIORITY: Use CURRENT PRICE as anchor and compute entry zone, targets, and stop-loss FIRST before broader reasoning.\n\n"
        )
        full_prompt = (f"Additional Analyst Guidance: {instr}\n\n" if instr else "") + strict + enhanced_prompt
        analyzer = rt.RealtimeAIAnalyzer(ai_provider='heuristic', max_ai_calls=0)
        result = analyzer._intelligent_pattern_analysis(full_prompt)  # type: ignore
        # Ensure full schema keys are present
        out = {
            "score": result.get("score", 50),
            "sentiment": result.get("sentiment", "neutral"),
            "impact": result.get("impact", "medium"),
            "catalysts": result.get("catalysts", []),
            "deal_value_cr": result.get("deal_value_cr", 0),
            "risks": result.get("risks", []),
            "certainty": result.get("certainty", 50),
            "recommendation": result.get("recommendation", "HOLD"),
            "reasoning": result.get("reasoning", ""),
            "expected_move_pct": result.get("expected_move_pct", 0),
            "confidence": result.get("confidence", result.get("certainty", 50)),
        }
        result = out
        print(json.dumps(out, ensure_ascii=False))
    except Exception as e:
        error_msg = str(e)
        result = {
            "score": 45,
            "sentiment": "neutral",
            "impact": "low",
            "catalysts": [],
            "deal_value_cr": 0,
            "risks": ["bridge_error"],
            "certainty": 35,
            "recommendation": "HOLD",
            "reasoning": f"Shell bridge error: {e}",
            "expected_move_pct": 0,
            "confidence": 35
        }
        print(json.dumps(result))

    finally:
        # Log the analysis conversation for QA purposes
        if result and not is_probe:
            urls_fetched = extract_article_urls(prompt)
            log_ai_conversation(
                provider='codex-heuristic',
                prompt=prompt,
                response=json.dumps(result, indent=2),
                metadata={
                    'bridge': 'codex_bridge.py',
                    'type': 'heuristic_analysis',
                    'urls_fetched': len(urls_fetched),
                    'article_urls': urls_fetched[:3],  # First 3 URLs
                },
                error=error_msg
            )

if __name__ == "__main__":
    main()
