#!/usr/bin/env python3
"""
Gemini Agent Bridge (no external API)

Goal: align Gemini shell bridge behavior with Codex/Claude bridges by:
- Fetching real article content from URLs present in the prompt
- Using the same calibrated heuristic analyzer as codex_bridge
- Returning strictly valid JSON compatible with realtime_ai_news_analyzer

Environment:
- Optionally set AI_SHELL_INSTRUCTION or GEMINI_SHELL_INSTRUCTION to inject guidance

Usage:
  export GEMINI_SHELL_CMD="python3 gemini_agent_bridge.py"
  ./run_without_api.sh gemini all.txt 48 10
"""

import sys
import json
import re
import hashlib
from typing import Optional
import os
import subprocess

# Import AI conversation logger for QA (optional)
try:
    from ai_conversation_logger import log_ai_conversation
except ImportError:
    def log_ai_conversation(*args, **kwargs):
        pass

def call_gemini_cli(prompt: str) -> Optional[str]:
    """Invoke the locally installed Gemini CLI with best-effort compatibility.

    Different community "gemini" CLIs accept different argument conventions.
    Try a few safe patterns before falling back to stdin mode.
    """
    cli = os.getenv('GEMINI_CLI', 'gemini').strip()
    # Configurable timeout and stdin fallback
    try:
        GEMINI_TIMEOUT = int(os.getenv('GEMINI_TIMEOUT', '20'))
    except Exception:
        GEMINI_TIMEOUT = 20
    allow_stdin = (os.getenv('GEMINI_ALLOW_STDIN', '0').strip().lower() in ('1', 'true', 'yes'))
    candidates = [
        [cli, '--prompt'],
        [cli, '-p'],
    ]
    for base in candidates:
        try:
            cmd = base + [prompt]
            print(f"--- Running Gemini CLI command: {' '.join(base)} <prompt> ---", file=sys.stderr)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=GEMINI_TIMEOUT
            )
            if result.returncode == 0 and (result.stdout or '').strip():
                print(f"--- Gemini CLI Output ---", file=sys.stderr)
                print(result.stdout, file=sys.stderr)
                print("-------------------------", file=sys.stderr)
                return result.stdout
            else:
                print(f"--- Gemini CLI returned code {result.returncode}; trying next mode ---", file=sys.stderr)
        except Exception as e:
            print(f"Mode {' '.join(base)} failed: {e}", file=sys.stderr)

    # Final fallback: pipe prompt via stdin (disabled by default)
    if not allow_stdin:
        print("--- Skipping Gemini CLI stdin mode (GEMINI_ALLOW_STDIN not set) ---", file=sys.stderr)
        return None
    try:
        print("--- Running Gemini CLI in stdin mode ---", file=sys.stderr)
        result = subprocess.run(
            [cli],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=GEMINI_TIMEOUT
        )
        if result.returncode != 0:
            print(f"--- Gemini CLI Error (stdin mode) ---", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            print("-------------------------------------", file=sys.stderr)
            return None
        print(f"--- Gemini CLI Output ---", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print("-------------------------", file=sys.stderr)
        return result.stdout
    except Exception as e:
        print(f"Error calling Gemini CLI (stdin mode): {e}", file=sys.stderr)
        return None



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
    """Handle connectivity probe requests (parity with codex bridge)."""
    if "Fetch the exact bytes at URL:" in prompt and '"sha256"' in prompt:
        m = re.search(r'URL:\s*(https?://[^\s\n]+)', prompt)
        if m:
            url = m.group(1)
            content = fetch_url(url)
            if content:
                return {"sha256": hashlib.sha256(content).hexdigest()}
            return {"sha256": None, "error": "failed to fetch URL"}
    return None


def handle_ticker_validation(prompt: str) -> Optional[dict]:
    """Support local ticker validation prompts for consistency with codex bridge."""
    if '"is_valid"' in prompt and '"company_name"' in prompt and 'Ticker to validate:' in prompt:
        import csv, os
        m = re.search(r'Ticker to validate:\s*([A-Za-z0-9_.-]+)', prompt)
        ticker = (m.group(1).strip().upper() if m else '').replace('.NS', '')
        if not ticker:
            return {"is_valid": False, "exchange": "NONE", "company_name": "NOT FOUND", "reason": "ticker not provided"}
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
    urls = []
    patterns = [
        r'\*\*URL\*\*:\s*(https?://[^\s\n]+)',
        r'(?:URL|url|link|article):\s*(https?://[^\s\n]+)',
        r'https?://(?:www\.)?(?:moneycontrol|economictimes|livemint|reuters|bloomberg)[^\s\n]+'
    ]
    for p in patterns:
        urls.extend(re.findall(p, prompt))
    # Deduplicate while preserving order
    seen = set()
    dedup = []
    for u in urls:
        if u not in seen:
            dedup.append(u)
            seen.add(u)
    return dedup


def _html_to_text(content: bytes) -> str:
    text = content.decode('utf-8', errors='ignore')
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _inject_full_text(prompt: str, article_text: str) -> str:
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

    # Fallback: minimal prompt structure the analyzer accepts
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
    return (
        f"# SWING TRADE SETUP ANALYSIS - {tkr}\n\n"
        f"## Stock Information\n"
        f"- **Ticker**: {tkr}\n"
        f"- **Headline**: {hed}\n"
        f"- **Full Text**: {article_text}\n"
        f"- **URL**: {url}\n"
    )


def fetch_and_enhance_prompt(prompt: str) -> str:
    urls = extract_article_urls(prompt)
    if not urls:
        return prompt
    fetched = []
    for url in urls[:3]:
        content = fetch_url(url)
        if content:
            try:
                text = _html_to_text(content)
                if text:
                    fetched.append(text)
                    print(f"✅ Fetched article content from {url} ({len(text)} chars)", file=sys.stderr)
            except Exception as e:
                print(f"⚠️ Error processing content from {url}: {e}", file=sys.stderr)
    if not fetched:
        return prompt
    combined = ' '.join(fetched)
    return _inject_full_text(prompt, combined)


def main():
    prompt = sys.stdin.read()
    error_msg = None
    result = None
    is_probe = False

    if not prompt.strip():
        result = {
            "exit_urgency_score": 50,
            "sentiment": "neutral",
            "exit_recommendation": "HOLD",
            "exit_catalysts": [],
            "hold_reasons": ["insufficient_input"],
            "risks_of_holding": [],
            "certainty": 40,
            "reasoning": "No prompt content provided to Gemini bridge.",
        }
        print(json.dumps(result, ensure_ascii=False))
        log_ai_conversation(
            provider='gemini-bridge',
            prompt=prompt,
            response=json.dumps(result, indent=2),
            metadata={'bridge': 'gemini_agent_bridge.py', 'type': 'empty_prompt'},
            error=None
        )
        return

    # Handle connectivity probe (parity with other bridges)
    probe = handle_probe_request(prompt)
    if probe:
        is_probe = True
        print(json.dumps(probe))
        log_ai_conversation(
            provider='gemini-probe',
            prompt=prompt,
            response=json.dumps(probe, indent=2),
            metadata={'bridge': 'gemini_agent_bridge.py', 'type': 'connectivity_probe'},
            error=None
        )
        return

    # Handle local ticker validation prompts
    tv = handle_ticker_validation(prompt)
    if tv:
        print(json.dumps(tv))
        log_ai_conversation(
            provider='gemini-bridge',
            prompt=prompt,
            response=json.dumps(tv, indent=2),
            metadata={'bridge': 'gemini_agent_bridge.py', 'type': 'ticker_validation'},
            error=None
        )
        return

    try:
        # Enhance prompt by fetching actual article content
        enhanced_prompt = fetch_and_enhance_prompt(prompt)

        instr = (os.getenv('GEMINI_SHELL_INSTRUCTION') or os.getenv('AI_SHELL_INSTRUCTION') or '').strip()
        strict = (
            "STRICT REAL-TIME CONTEXT: Base your decision ONLY on the provided article text and TECHNICAL CONTEXT (both fetched now). "
            "Do not use prior training knowledge or external facts not fetched now. PRIORITY: Use CURRENT PRICE as anchor and compute entry zone, targets, and stop-loss FIRST before broader reasoning. "
            "If technical context is missing, do not invent values.\n\n"
        )
        full_prompt = (f"Additional Analyst Guidance: {instr}\n\n" if instr else "") + strict + enhanced_prompt

        gemini_response = call_gemini_cli(full_prompt)

        if gemini_response:
            cleaned = gemini_response.strip()
            # If extra text surrounds JSON, try to extract the first JSON object
            if not cleaned.startswith('{'):
                m = re.search(r'(\{.*\})', cleaned, flags=re.DOTALL)
                if m:
                    cleaned = m.group(1).strip()
            try:
                # Attempt to parse Gemini's response as JSON
                gemini_json = json.loads(cleaned)
                # Validate if it has the expected keys for exit analysis
                if all(k in gemini_json for k in ['exit_urgency_score', 'sentiment', 'exit_recommendation', 'certainty', 'reasoning']):
                    # Map common synonyms and coerce types
                    rec = str(gemini_json.get('exit_recommendation', '') or '').strip().upper()
                    if rec in ('WATCH', 'WATCHLIST'):
                        rec = 'MONITOR'
                    elif rec in ('SELL', 'EXIT', 'IMMEDIATE SELL', 'IMMEDIATE_EXIT'):
                        rec = 'IMMEDIATE_EXIT'
                    elif rec in ('HOLD', 'KEEP'):
                        rec = 'HOLD'
                    else:
                        rec = 'HOLD'
                    def _num(v, d=50):
                        try:
                            return float(v)
                        except Exception:
                            return float(d)
                    urgency = max(0.0, min(100.0, _num(gemini_json.get('exit_urgency_score', 50))))

                    # Detect generic/low-information default answers and avoid passing them through
                    rsn = str(gemini_json.get('reasoning', '') or '')
                    generic = ('Detected 0 catalyst' in rsn) or ('unknown source' in rsn.lower()) or abs(urgency - 43.26) < 0.01
                    if generic:
                        raise ValueError('Generic Gemini response detected; forcing heuristic fallback')

                    result = {
                        "exit_urgency_score": urgency,
                        "sentiment": gemini_json.get("sentiment", "neutral"),
                        "exit_recommendation": rec,
                        "exit_catalysts": gemini_json.get("exit_catalysts", []),
                        "hold_reasons": gemini_json.get("hold_reasons", []),
                        "risks_of_holding": gemini_json.get("risks_of_holding", []),
                        "certainty": max(0, min(100, int(_num(gemini_json.get("certainty", 50), 50)))),
                        "reasoning": gemini_json.get("reasoning", ""),
                    }
                    print(json.dumps(result, ensure_ascii=False))
                    log_ai_conversation(
                        provider='gemini-cli',
                        prompt=full_prompt,
                        response=json.dumps(result, indent=2),
                        metadata={'bridge': 'gemini_agent_bridge.py', 'type': 'gemini_cli_analysis'},
                        error=None
                    )
                    return
                else:
                    print(f"Warning: Gemini CLI response missing expected keys, falling back to heuristic: {gemini_response}", file=sys.stderr)
            except json.JSONDecodeError:
                print(f"Warning: Gemini CLI returned invalid JSON, falling back to heuristic: {gemini_response}", file=sys.stderr)
            except Exception as e:
                print(f"Warning: Error processing Gemini CLI response, falling back to heuristic: {e}", file=sys.stderr)

        # Fallback to heuristic analysis if Gemini CLI failed or returned invalid/incomplete data
        import realtime_ai_news_analyzer as rt
        analyzer = rt.RealtimeAIAnalyzer(ai_provider='heuristic', max_ai_calls=0)
        ai = analyzer._intelligent_pattern_analysis(full_prompt)  # type: ignore
        out = {
            "exit_urgency_score": ai.get("score", 50),
            "sentiment": ai.get("sentiment", "neutral"),
            "exit_recommendation": ai.get("recommendation", "HOLD"),
            "exit_catalysts": ai.get("catalysts", []),
            "hold_reasons": [], # Heuristic doesn't provide this, default to empty
            "risks_of_holding": ai.get("risks", []),
            "certainty": ai.get("certainty", 50),
            "reasoning": ai.get("reasoning", ""),
        }
        result = out
        print(json.dumps(out, ensure_ascii=False))

    except Exception as e:
        error_msg = str(e)
        result = {
            "exit_urgency_score": 45,
            "sentiment": "neutral",
            "exit_recommendation": "HOLD",
            "exit_catalysts": [],
            "hold_reasons": [],
            "risks_of_holding": ["bridge_error"],
            "certainty": 35,
            "reasoning": f"Gemini bridge error: {e}",
        }
        print(json.dumps(result))
    finally:
        if result and not is_probe:
            urls = extract_article_urls(prompt)
            log_ai_conversation(
                provider='gemini-bridge',
                prompt=prompt,
                response=json.dumps(result, indent=2),
                metadata={'bridge': 'gemini_agent_bridge.py', 'type': 'heuristic_analysis', 'urls_fetched': len(urls), 'article_urls': urls[:3]},
                error=error_msg
            )


if __name__ == "__main__":
    main()
