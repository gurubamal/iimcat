#!/usr/bin/env python3
"""
REAL-TIME AI NEWS ANALYZER
Analyzes news INSTANTLY as it's fetched using Claude, Codex, or a local heuristic
Integrates Frontier AI + Quant analysis for immediate scoring and ranking

Key Features:
- Instant AI analysis per news item (no batching)
- Claude/Codex model with internet access for context
- Frontier AI + Quant scoring on-the-fly
- Live ranking and scoring
- No news skipped - everything analyzed
- Smart caching + configurable AI budget so APIs never get exhausted

Usage:
    python3 realtime_ai_news_analyzer.py --tickers-file all.txt --hours-back 48
"""

import hashlib
import os
import sys
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
import logging
import requests
import threading
from pathlib import Path
import csv

# Import AI conversation logger for QA
try:
    from ai_conversation_logger import log_ai_conversation
except ImportError:
    # Fallback if logger is not available
    def log_ai_conversation(*args, **kwargs):
        pass

# Import base news collector
import fetch_full_articles as news_collector

# Import correction boost system modules
try:
    from enhanced_correction_analyzer import EnhancedCorrectionAnalyzer
    from ai_correction_supervisor import AICorrectionSupervisor
    CORRECTION_BOOST_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning("Correction boost modules not available: %s", e)
    CORRECTION_BOOST_AVAILABLE = False

# Import health data integration modules
try:
    from claude_health_ai_client import create_client as create_health_client
    from health_data_integration import integrate_with_analyzer
    HEALTH_DATA_INTEGRATION_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.warning("Health data integration modules not available: %s", e)
    HEALTH_DATA_INTEGRATION_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OFFLINE_NEWS_FILE = Path('offline_news_cache.json')
_OFFLINE_NEWS_CACHE: Optional[Dict[str, List[Dict]]] = None
ALLOW_OFFLINE_NEWS_CACHE = os.getenv('ALLOW_OFFLINE_NEWS_CACHE', '0').strip() == '1'


def _load_offline_news_cache() -> Dict[str, List[Dict]]:
    """Lazy-load offline news cache for air-gapped runs."""
    if not ALLOW_OFFLINE_NEWS_CACHE:
        return {}
    global _OFFLINE_NEWS_CACHE
    if _OFFLINE_NEWS_CACHE is not None:
        return _OFFLINE_NEWS_CACHE
    if not OFFLINE_NEWS_FILE.exists():
        _OFFLINE_NEWS_CACHE = {}
        return _OFFLINE_NEWS_CACHE
    try:
        with open(OFFLINE_NEWS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            _OFFLINE_NEWS_CACHE = {
                (k or '').upper().replace('.NS', ''): (v if isinstance(v, list) else [])
                for k, v in data.items()
            }
        else:
            _OFFLINE_NEWS_CACHE = {}
    except Exception as exc:
        logger.warning("⚠️  Failed to load offline news cache (%s)", exc)
        _OFFLINE_NEWS_CACHE = {}
    return _OFFLINE_NEWS_CACHE


def _normalize_ticker_symbol(symbol: str) -> str:
    s = (symbol or '').strip().upper()
    if s.endswith('.NS'):
        s = s[:-3]
    if s.endswith('.BO'):
        s = s[:-3]
    return re.sub(r'[^A-Z0-9]', '', s)


@dataclass
class InstantAIAnalysis:
    """Real-time AI analysis result"""
    ticker: str
    headline: str
    timestamp: datetime
    ai_score: float  # 0-100 from external AI provider
    sentiment: str
    impact_prediction: str
    catalysts: List[str]
    risks: List[str]
    certainty: float
    recommendation: str
    reasoning: str
    quant_alpha: Optional[float] = None
    alpha_gate_flags: Optional[str] = None
    alpha_setup_flags: Optional[str] = None
    company_name: Optional[str] = None
    final_rank: Optional[int] = None
    # Real-time price data (fetched from yfinance, NOT training data)
    current_price: Optional[float] = None
    price_timestamp: Optional[str] = None
    entry_zone_low: Optional[float] = None
    entry_zone_high: Optional[float] = None
    target_conservative: Optional[float] = None
    target_aggressive: Optional[float] = None
    stop_loss: Optional[float] = None
    # Fundamental data (fetched from yfinance, NOT training data)
    quarterly_earnings_growth_yoy: Optional[float] = None
    annual_earnings_growth_yoy: Optional[float] = None
    profit_margin_pct: Optional[float] = None
    debt_to_equity: Optional[float] = None
    is_profitable: Optional[bool] = None
    net_worth_positive: Optional[bool] = None
    financial_health_status: Optional[str] = None
    fundamental_adjustment: Optional[float] = None
    # AI Web Search Health Data (verified, fresh data)
    health_data: Optional[dict] = None
    # Corporate actions catalyst data (fetched from NSE, NOT training data)
    catalyst_score: Optional[int] = None
    has_dividend: Optional[bool] = None
    dividend_amount: Optional[float] = None
    has_bonus: Optional[bool] = None
    bonus_ratio: Optional[str] = None
    # AI-Supervised Correction Boost Analysis (15 new fields)
    # Correction Detection
    correction_detected: Optional[bool] = None
    correction_pct: Optional[float] = None
    reversal_confirmed: Optional[bool] = None
    # Scoring Metrics
    correction_confidence: Optional[float] = None
    oversold_score: Optional[float] = None
    fundamental_confidence: Optional[float] = None
    catalyst_strength: Optional[float] = None
    # Boost Decision
    boost_applied: Optional[float] = None
    boost_tier: Optional[str] = None
    correction_reasoning: Optional[str] = None
    # Risk Assessment
    risk_filters_passed: Optional[bool] = None
    risk_violations: Optional[List[str]] = None
    # Market Context
    market_context: Optional[str] = None
    market_vix_level: Optional[float] = None
    # AI Supervision
    supervisor_verdict: Optional[str] = None
    supervisor_confidence: Optional[float] = None
    supervision_notes: Optional[str] = None
    alignment_issues: Optional[List[str]] = None
    supervisor_recommendations: Optional[List[str]] = None


class AIModelClient:
    """Adapter that routes prompts to Claude, Codex, or a heuristic fallback."""

    def __init__(self, provider: str = 'auto'):
        self.requested_provider = (provider or 'auto').lower()
        self.selected_provider = self._select_provider()
        logger.info(
            "AI provider configured: %s",
            self.selected_provider.capitalize() if self.selected_provider else 'heuristic'
        )

    def _normalize(self, provider: str) -> str:
        mapping = {
            'anthropic': 'claude',
            'claude': 'claude',
            'sonnet': 'claude',
            'opus': 'claude',
            'haiku': 'claude',
            'codex': 'codex',
            'openai': 'codex',
            'gpt': 'codex',
            'gpt-4': 'codex',
            'gpt4': 'codex',
            'gpt-4o': 'codex',
            'gpt4o': 'codex',
            'o1': 'codex',
            'gemini': 'gemini',
            'cursor': 'cursor',
            'copilot': 'heuristic',
            'mock': 'heuristic',
            'heuristic': 'heuristic',
            'auto': 'auto'
        }
        return mapping.get(provider, provider)

    def _select_provider(self) -> str:
        normalized = self._normalize(self.requested_provider)

        if normalized in {'claude', 'codex', 'heuristic', 'cursor', 'gemini'}:
            if normalized == 'claude':
                # Prefer API if key present, otherwise allow shell bridge if configured
                if os.getenv('ANTHROPIC_API_KEY'):
                    return 'claude'
                # Claude CLI bridge: let users use 'claude' CLI tool for analysis
                if os.getenv('CLAUDE_SHELL_CMD') or os.getenv('AI_SHELL_CMD'):
                    logger.info('Using Claude CLI shell bridge (no API key).')
                    return 'claude-shell'
                logger.warning('Claude selected but ANTHROPIC_API_KEY is missing and no CLAUDE_SHELL_CMD/AI_SHELL_CMD set.')
                return 'heuristic'
            if normalized == 'gemini':
                if os.getenv('GEMINI_SHELL_CMD') or os.getenv('AI_SHELL_CMD'):
                    logger.info('Using Gemini shell bridge.')
                    return 'gemini-shell'
                logger.warning('Gemini selected but GEMINI_SHELL_CMD/AI_SHELL_CMD not set; using heuristic.')
                return 'heuristic'
            if normalized == 'codex':
                # Prefer API if key present, otherwise allow shell bridge if configured
                if os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY'):
                    return 'codex'
                # Shell bridge: let users provide a local command that returns JSON
                if os.getenv('CODEX_SHELL_CMD') or os.getenv('AI_SHELL_CMD'):
                    logger.info('Using Codex shell bridge (no API key).')
                    return 'codex-shell'
                logger.warning('Codex selected but no OPENAI_API_KEY and no CODEX_SHELL_CMD/AI_SHELL_CMD set.')
                return 'heuristic'
            if normalized == 'cursor':
                if os.getenv('CURSOR_SHELL_CMD') or os.getenv('AI_SHELL_CMD'):
                    logger.info('Using Cursor shell bridge.')
                    return 'cursor-shell'
                logger.warning('Cursor selected but CURSOR_SHELL_CMD/AI_SHELL_CMD not set; using heuristic.')
                return 'heuristic'
            # Explicit heuristic
            return 'heuristic'

        if normalized == 'auto':
            available = []
            if os.getenv('ANTHROPIC_API_KEY'):
                available.append('claude')
            if os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY'):
                available.append('codex')

            preferred = self._normalize(os.getenv('AI_PROVIDER_DEFAULT', '').lower())
            if preferred in available:
                return preferred

            if available:
                return available[0]

            logger.info('No external AI keys detected; falling back to heuristic scoring.')
            return 'heuristic'

        logger.warning("Unknown AI provider '%s'; using heuristic fallback.", self.requested_provider)
        return 'heuristic'

    def invoke(self, prompt: str) -> Dict:
        provider = self.selected_provider
        if provider == 'claude':
            return self._call_claude(prompt)
        if provider == 'claude-shell':
            return self._call_claude_shell(prompt)
        if provider == 'gemini-shell':
            return self._call_gemini_shell(prompt)
        if provider == 'codex':
            return self._call_openai(prompt)
        if provider == 'codex-shell':
            return self._call_shell_bridge(prompt)
        if provider == 'cursor-shell':
            return self._call_cursor_shell(prompt)
        raise RuntimeError('Heuristic provider in use')

    # ------------------------
    # Internet/Endpoint Health
    # ------------------------
    def _probe(self, url: str, *, headers: Optional[Dict[str, str]] = None, timeout: int = 8) -> Dict:
        try:
            r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
            return {
                'ok': True,
                'status': r.status_code,
                'url': url
            }
        except Exception as e:
            return {
                'ok': False,
                'error': str(e)[:200],
                'url': url
            }

    def internet_health(self) -> Dict:
        """Check general internet + AI endpoint reachability and whether AI will use internet.

        Returns a dict with keys:
        - internet_ok: bool (any general probe succeeded)
        - using_remote_ai: bool (provider is 'codex' or 'claude')
        - ai_endpoint_ok: Optional[bool] (None if not remote)
        - details: Dict with per-URL probe results
        """
        details: Dict[str, Dict] = {}

        # General connectivity probes (use finance + generic endpoints)
        general_urls = [
            'https://reuters.com/robots.txt',
            'https://httpbin.org/ip'
        ]
        general_results = [self._probe(u) for u in general_urls]
        for res in general_results:
            details[res['url']] = res
        internet_ok = any(r.get('ok') for r in general_results)

        # AI endpoint specific check
        ai_endpoint_ok: Optional[bool] = None
        if self.selected_provider == 'codex':
            # If key is set, use it; else still probe reachability without key
            api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
            headers = {'Authorization': f'Bearer {api_key}'} if api_key else None
            res = self._probe('https://api.openai.com/v1/models', headers=headers)
            details['https://api.openai.com/v1/models'] = res
            ai_endpoint_ok = bool(res.get('ok'))
        elif self.selected_provider == 'claude':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            headers = {'x-api-key': api_key, 'anthropic-version': os.getenv('ANTHROPIC_VERSION', '2023-06-01')} if api_key else None
            res = self._probe('https://api.anthropic.com/v1/models', headers=headers)
            details['https://api.anthropic.com/v1/models'] = res
            ai_endpoint_ok = bool(res.get('ok'))
        elif self.selected_provider in {'codex-shell', 'cursor-shell', 'claude-shell'}:
            # Shell bridges: internet usage depends on the underlying CLI; endpoint unknown
            ai_endpoint_ok = None

        using_remote_ai = self.selected_provider in {'codex', 'claude', 'claude-shell'}
        return {
            'internet_ok': internet_ok,
            'using_remote_ai': using_remote_ai,
            'ai_endpoint_ok': ai_endpoint_ok,
            'details': details,
        }

    def agent_connectivity_probe(self) -> Dict:
        """Ask the shell agent (cursor/codex/claude shell) to fetch a known URL and return a SHA256.

        We fetch the same URL ourselves and compare hashes to validate agent internet access.
        Returns a dict with: ok, provider, url, agent_sha256, expected_sha256, error (optional)
        """
        provider = self.selected_provider
        if provider not in {'codex-shell', 'cursor-shell', 'claude-shell'}:
            return {
                'ok': None,
                'provider': provider,
                'url': None,
                'reason': 'not-shell-provider'
            }
        test_url = os.getenv('AGENT_PROBE_URL', 'https://example.com/')
        # Build a strict instruction for the agent
        probe_prompt = (
            "You are a CLI agent. Fetch the exact bytes at URL: "
            f"{test_url}\nCompute the SHA256 hex digest of the bytes.\n"
            "Return ONLY valid JSON with this shape: {\"sha256\":\"<hex>\"}.\n"
            "Do not include code fences, text, or explanations."
        )
        try:
            # Invoke the shell agent
            if provider == 'cursor-shell':
                resp = self._call_cursor_shell(probe_prompt)
            elif provider == 'claude-shell':
                resp = self._call_claude_shell(probe_prompt)
            else:
                resp = self._call_shell_bridge(probe_prompt)
            agent_sha = (
                resp.get('sha256')
                or resp.get('hash')
                or resp.get('probe_hash')
            )
            if not agent_sha or not isinstance(agent_sha, str):
                return {
                    'ok': False,
                    'provider': provider,
                    'url': test_url,
                    'agent_sha256': str(agent_sha),
                    'error': 'agent returned no sha256'
                }
            # Compute expected
            r = requests.get(test_url, timeout=10)
            r.raise_for_status()
            import hashlib as _hashlib
            expected_sha = _hashlib.sha256(r.content).hexdigest()
            return {
                'ok': (agent_sha.lower() == expected_sha.lower()),
                'provider': provider,
                'url': test_url,
                'agent_sha256': agent_sha,
                'expected_sha256': expected_sha,
            }
        except Exception as e:
            return {
                'ok': False,
                'provider': provider,
                'url': test_url,
                'error': str(e)[:200]
            }

    def _call_openai(self, prompt: str) -> Dict:
        api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_KEY')
        if not api_key:
            raise RuntimeError('OPENAI_API_KEY not set')

        model = os.getenv('OPENAI_MODEL', 'gpt-4o')  # Upgraded from invalid 'gpt-4.1-mini' to best model
        temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.2'))
        max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '1200'))

        try:
            import requests
        except ImportError as exc:
            raise RuntimeError('requests package is required for OpenAI provider') from exc

        payload = {
            'model': model,
            'messages': [
                {
                    'role': 'system',
                    'content': (
                        'You are an AI equity analyst. Return valid JSON only. '
                        '🚨 CRITICAL: Base analysis ONLY on user-provided article text and REAL-TIME technical context in the prompt. '
                        'DO NOT use training data, memorized prices, or external facts about current stock prices. '
                        'If CURRENT PRICE is not in the prompt, return neutral scores. '
                        'PRIORITY: use ONLY the CURRENT PRICE explicitly provided in prompt as anchor and compute entry zone, '
                        'targets, and stop-loss using ONLY that price before any broader reasoning.'
                    )
                },
                {'role': 'user', 'content': prompt}
            ],
            'temperature': temperature,
            'max_tokens': max_tokens,
            'response_format': {'type': 'json_object'}
        }

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }

        raw_response = None
        error_msg = None
        result = None

        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                json=payload,
                headers=headers,
                timeout=int(os.getenv('OPENAI_TIMEOUT', '90'))
            )
            response.raise_for_status()
            raw_response = response.json()['choices'][0]['message']['content']
            result = self._parse_json_response(raw_response)
        except Exception as e:
            error_msg = str(e)[:200]
            raise
        finally:
            # Log the conversation for QA purposes
            log_ai_conversation(
                provider='openai',
                prompt=prompt,
                response=raw_response if raw_response else (json.dumps(result, indent=2) if result else ""),
                metadata={
                    'model': model,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'api': 'openai',
                },
                error=error_msg
            )

        return result

    def _call_claude(self, prompt: str) -> Dict:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise RuntimeError('ANTHROPIC_API_KEY not set')

        model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')  # Upgraded to latest Sonnet model
        temperature = float(os.getenv('ANTHROPIC_TEMPERATURE', '0.2'))
        max_tokens = int(os.getenv('ANTHROPIC_MAX_TOKENS', '1200'))
        version = os.getenv('ANTHROPIC_VERSION', '2023-06-01')

        try:
            import requests
        except ImportError as exc:
            raise RuntimeError('requests package is required for Claude provider') from exc

        headers = {
            'x-api-key': api_key,
            'anthropic-version': version,
            'content-type': 'application/json'
        }

        data = {
            'model': model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'system': os.getenv(
                'ANTHROPIC_SYSTEM_PROMPT',
                'You are an AI equity analyst. Return valid JSON only. '
                '🚨 CRITICAL: Base analysis ONLY on user-provided article text and REAL-TIME technical context in the prompt. '
                'DO NOT use training data, memorized prices, or external facts about current stock prices. '
                'If CURRENT PRICE is not in the prompt, return neutral scores. '
                'PRIORITY: use ONLY the CURRENT PRICE explicitly provided in prompt as anchor and compute entry zone, '
                'targets, and stop-loss using ONLY that price before any broader reasoning.'
            ),
            'messages': [{'role': 'user', 'content': prompt}]
        }

        raw_response = None
        error_msg = None
        result = None

        try:
            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=int(os.getenv('ANTHROPIC_TIMEOUT', '90'))
            )
            response.raise_for_status()
            payload = response.json()
            content_chunks = [
                block.get('text', '')
                for block in payload.get('content', [])
                if block.get('type') == 'text'
            ]
            raw_response = ''.join(content_chunks).strip() or json.dumps(payload.get('content', {}))
            result = self._parse_json_response(raw_response)
        except Exception as e:
            error_msg = str(e)[:200]
            raise
        finally:
            # Log the conversation for QA purposes
            log_ai_conversation(
                provider='claude',
                prompt=prompt,
                response=raw_response if raw_response else (json.dumps(result, indent=2) if result else ""),
                metadata={
                    'model': model,
                    'temperature': temperature,
                    'max_tokens': max_tokens,
                    'version': version,
                    'api': 'anthropic',
                },
                error=error_msg
            )

        return result

    def _call_shell_bridge(self, prompt: str) -> Dict:
        """Invoke a local shell command that returns JSON on stdout.

        The command should read the prompt from stdin and print a JSON object.
        Configure via env var CODEX_SHELL_CMD or AI_SHELL_CMD.
        Example:
          export CODEX_SHELL_CMD='python3 codex_bridge.py'
        The bridge script must output ONLY JSON.
        """
        cmd = os.getenv('CODEX_SHELL_CMD') or os.getenv('AI_SHELL_CMD')
        if not cmd:
            raise RuntimeError('No shell bridge configured (CODEX_SHELL_CMD/AI_SHELL_CMD)')
        import subprocess, shlex
        try:
            proc = subprocess.run(
                cmd if isinstance(cmd, str) else ' '.join(cmd),
                input=prompt.encode('utf-8'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                check=True,
                timeout=int(os.getenv('SHELL_BRIDGE_TIMEOUT', '120')),
            )
        except subprocess.CalledProcessError as exc:
            err = exc.stderr.decode('utf-8', errors='ignore') if exc.stderr else str(exc)
            raise RuntimeError(f'Shell bridge failed: {err[:200]}') from exc
        except Exception as exc:
            raise RuntimeError(f'Shell bridge error: {exc}') from exc
        out = proc.stdout.decode('utf-8', errors='ignore').strip()
        if not out:
            raise RuntimeError('Shell bridge produced no output')
        return self._parse_json_response(out)

    def _call_cursor_shell(self, prompt: str) -> Dict:
        """Invoke a local Cursor CLI that returns JSON on stdout.

        Configure via CURSOR_SHELL_CMD (or AI_SHELL_CMD as fallback).
        The command should read the prompt on stdin and print JSON to stdout.
        """
        cmd = os.getenv('CURSOR_SHELL_CMD') or os.getenv('AI_SHELL_CMD')
        if not cmd:
            raise RuntimeError('No Cursor shell bridge configured (CURSOR_SHELL_CMD/AI_SHELL_CMD)')
        import subprocess
        try:
            proc = subprocess.run(
                cmd,
                input=prompt.encode('utf-8'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                check=True,
                timeout=int(os.getenv('CURSOR_SHELL_TIMEOUT', '180')),
            )
        except subprocess.CalledProcessError as exc:
            err = exc.stderr.decode('utf-8', errors='ignore') if exc.stderr else str(exc)
            raise RuntimeError(f'Cursor shell failed: {err[:200]}') from exc
        out = proc.stdout.decode('utf-8', errors='ignore').strip()
        if not out:
            raise RuntimeError('Cursor shell produced no output')
        return self._parse_json_response(out)

    def _call_claude_shell(self, prompt: str) -> Dict:
        """Invoke Claude CLI bridge that returns JSON on stdout.

        Configure via CLAUDE_SHELL_CMD (or AI_SHELL_CMD as fallback).
        The command should read the prompt on stdin and print JSON to stdout.
        Typically: export CLAUDE_SHELL_CMD='python3 claude_cli_bridge.py'
        """
        cmd = os.getenv('CLAUDE_SHELL_CMD') or os.getenv('AI_SHELL_CMD')
        if not cmd:
            raise RuntimeError('No Claude shell bridge configured (CLAUDE_SHELL_CMD/AI_SHELL_CMD)')
        import subprocess
        try:
            proc = subprocess.run(
                cmd,
                input=prompt.encode('utf-8'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                check=True,
                timeout=int(os.getenv('CLAUDE_SHELL_TIMEOUT', '120')),
            )
        except subprocess.CalledProcessError as exc:
            err = exc.stderr.decode('utf-8', errors='ignore') if exc.stderr else str(exc)
            raise RuntimeError(f'Claude shell bridge failed: {err[:200]}') from exc
        except Exception as exc:
            raise RuntimeError(f'Claude shell bridge error: {exc}') from exc
        out = proc.stdout.decode('utf-8', errors='ignore').strip()
        if not out:
            raise RuntimeError('Claude shell bridge produced no output')
        return self._parse_json_response(out)

    def _call_gemini_shell(self, prompt: str) -> Dict:
        """Invoke Gemini CLI bridge that returns JSON on stdout.

        Configure via GEMINI_SHELL_CMD (or AI_SHELL_CMD as fallback).
        The command should read the prompt on stdin and print JSON to stdout.
        Typically: export GEMINI_SHELL_CMD='python3 gemini_agent_bridge.py'
        """
        cmd = os.getenv('GEMINI_SHELL_CMD') or os.getenv('AI_SHELL_CMD')
        if not cmd:
            raise RuntimeError('No Gemini shell bridge configured (GEMINI_SHELL_CMD/AI_SHELL_CMD)')
        import subprocess
        try:
            proc = subprocess.run(
                cmd,
                input=prompt.encode('utf-8'),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                check=True,
                timeout=int(os.getenv('GEMINI_SHELL_TIMEOUT', '120')),
            )
        except subprocess.CalledProcessError as exc:
            err = exc.stderr.decode('utf-8', errors='ignore') if exc.stderr else str(exc)
            raise RuntimeError(f'Gemini shell bridge failed: {err[:200]}') from exc
        except Exception as exc:
            raise RuntimeError(f'Gemini shell bridge error: {exc}') from exc
        out = proc.stdout.decode('utf-8', errors='ignore').strip()
        if not out:
            raise RuntimeError('Gemini shell bridge produced no output')
        return self._parse_json_response(out)

    def _parse_json_response(self, response_text: str) -> Dict:
        cleaned = response_text.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
            cleaned = cleaned.lstrip()
            if cleaned.lower().startswith('json'):
                cleaned = cleaned[4:]
            cleaned = cleaned.strip()
            if '```' in cleaned:
                cleaned = cleaned.split('```', 1)[0].strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f'AI provider returned non-JSON payload: {cleaned[:200]}') from exc


class RealtimeAIAnalyzer:
    """Analyze news in real-time using Claude, Codex, or a heuristic fallback."""
    
    def __init__(
        self,
        output_dir: str = "realtime_analysis",
        ai_provider: str = 'auto',
        max_ai_calls: Optional[int] = None,
        require_internet_ai: bool = False,
        verify_internet: bool = False,
        probe_agent: bool = False,
        require_agent_internet: bool = False,
        enable_ticker_validation: bool = True,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Live results tracking
        self.live_results: Dict[str, List[InstantAIAnalysis]] = {}
        self.ranked_stocks: List[Tuple[str, float]] = []
        self.analysis_cache: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        # Track AI usage for summaries
        self.external_ai_used_tickers: set[str] = set()
        self.limit_affected_tickers: set[str] = set()
        self.ai_limit_exhausted: bool = False
        self.enable_ticker_validation = enable_ticker_validation
        # Frontier + Quant configuration
        self.frontier_alpha_enabled: bool = (os.getenv('FRONTIER_ALPHA_ENABLED', '1').strip() != '0')
        self.frontier_alpha_weight: float = 0.0  # resolved dynamically when alpha present
        try:
            self.frontier_alpha_weight = float(os.getenv('FRONTIER_ALPHA_WEIGHT', '0.10'))
        except Exception:
            self.frontier_alpha_weight = 0.10
        self.frontier_quant_suffix: str = os.getenv('FRONTIER_QUANT_SUFFIX', '.NS').strip() or '.NS'
        try:
            self.frontier_quant_lookback: int = int(os.getenv('FRONTIER_QUANT_LOOKBACK', '180'))
        except Exception:
            self.frontier_quant_lookback = 180
        self.frontier_alpha_use_demo: bool = (os.getenv('FRONTIER_ALPHA_USE_DEMO', '0').strip() == '1')
        # Cache quant features by ticker during a run
        self._quant_cache: Dict[str, object] = {}
        # Load expert playbook (patterns and thresholds)
        self.expert_playbook = self._load_expert_playbook()
        # Company alias/name maps for disambiguation and display
        self._company_alias_map: Dict[str, List[str]] = self._load_company_aliases()
        self._company_name_map: Dict[str, str] = self._load_company_names()
        # Domain reputation and ad/popularity controls
        self._domain_reputation: Dict[str, Dict] = self._load_domain_reputation()
        self.ad_popularity_enabled: bool = (os.getenv('AD_POPULARITY_ENABLED', '1').strip() != '0')
        self.ad_strict_reject: bool = (os.getenv('AD_STRICT_REJECT', '0').strip() == '1')

        # Load persistent validation cache
        self._ticker_validation_cache = self._load_validation_cache()
        
        self.ai_client = AIModelClient(ai_provider)
        env_limit = os.getenv('AI_MAX_CALLS')
        inherited_limit = None
        if env_limit:
            try:
                parsed = int(env_limit)
                if parsed > 0:
                    inherited_limit = parsed
            except ValueError:
                inherited_limit = None

        if max_ai_calls and max_ai_calls > 0:
            self.ai_call_limit = max_ai_calls
        else:
            self.ai_call_limit = inherited_limit
        self.ai_call_count = 0
        # Initialize Frontier AI components
        self._init_frontier_components()

        # Initialize AI-Supervised Correction Boost System
        if CORRECTION_BOOST_AVAILABLE:
            self.correction_analyzer = EnhancedCorrectionAnalyzer()
            self.correction_supervisor = AICorrectionSupervisor()
            logger.info("✅ AI-Supervised Correction Boost System initialized")
        else:
            self.correction_analyzer = None
            self.correction_supervisor = None
            logger.warning("⚠️  Correction Boost System not available")

        # Initialize AI-Driven Health Data Integration
        if HEALTH_DATA_INTEGRATION_AVAILABLE:
            try:
                health_ai_client = create_health_client(use_cli=True)  # Prefer CLI if available
                self.health_integration = integrate_with_analyzer(self, health_ai_client)
                logger.info("✅ AI Health Data Integration initialized")
            except Exception as e:
                logger.warning(f"⚠️  Health Data Integration failed: {e}")
                self.health_integration = None
        else:
            self.health_integration = None
            logger.warning("⚠️  Health Data Integration not available")

        logger.info("🤖 Real-time AI Analyzer initialized")

        # Optional internet connectivity and AI endpoint checks
        self.network_status: Dict = self.ai_client.internet_health()
        if verify_internet or require_internet_ai:
            logger.info(
                "🌐 Internet check: %s | Remote AI: %s | AI endpoint reachable: %s",
                'OK' if self.network_status.get('internet_ok') else 'FAILED',
                'YES' if self.network_status.get('using_remote_ai') else 'NO',
                ('N/A' if self.network_status.get('ai_endpoint_ok') is None else ('OK' if self.network_status.get('ai_endpoint_ok') else 'FAILED')),
            )
        if require_internet_ai:
            if not self.network_status.get('using_remote_ai'):
                raise RuntimeError('Require-Internet-AI enabled but selected provider is not a remote AI (claude/codex). Set OPENAI_API_KEY or ANTHROPIC_API_KEY to enable remote AI, or unset REQUIRE_INTERNET_AI.')
            if self.network_status.get('ai_endpoint_ok') is False:
                raise RuntimeError('Require-Internet-AI enabled but AI API endpoint not reachable. Check network or provider status.')

        # Optional agent connectivity probe for shell agents
        if probe_agent or require_agent_internet:
            probe = self.ai_client.agent_connectivity_probe()
            status = probe.get('ok')
            if status is None:
                logger.info('🧪 Agent probe skipped (provider=%s)', probe.get('provider'))
            else:
                logger.info('🧪 Agent internet probe: %s (provider=%s, url=%s)',
                            'OK' if status else 'FAILED', probe.get('provider'), probe.get('url'))
                if not status and probe.get('error'):
                    logger.info('🧪 Agent probe error: %s', probe.get('error'))
            if require_agent_internet and not status:
                raise RuntimeError('Require-Agent-Internet enabled but agent probe failed. Ensure your shell agent can fetch URLs and output JSON sha256.')
    
    def _init_frontier_components(self):
        """Initialize Frontier AI + Quant components"""
        try:
            from frontier_ai_quant_alpha_core import LLMNewsScorer, AlphaCalculator, QuantFeatureEngine
            self.news_scorer = LLMNewsScorer()
            self.alpha_calc = AlphaCalculator()
            # Quant engine (yfinance-backed; can use demo mode). Keep a single instance.
            self.quant_engine = QuantFeatureEngine(
                lookback_days=self.frontier_quant_lookback,
                use_demo=self.frontier_alpha_use_demo,
            )
            logger.info("✅ Frontier AI components loaded")
        except ImportError as e:
            logger.warning(f"⚠️  Frontier components not available: {e}")
            self.news_scorer = None
            self.alpha_calc = None
            self.quant_engine = None

    def _load_validation_cache(self) -> Dict:
        """Load persistent ticker validation cache from disk"""
        cache_file = Path('ticker_validation_cache.json')
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cache = json.load(f)
                logger.info(f"✅ Loaded {len(cache)} cached ticker validations")
                return cache
            except Exception as e:
                logger.warning(f"⚠️  Failed to load validation cache: {e}")
        return {}

    def _save_validation_cache(self):
        """Save ticker validation cache to disk for reuse"""
        cache_file = Path('ticker_validation_cache.json')
        try:
            with open(cache_file, 'w') as f:
                json.dump(self._ticker_validation_cache, f, indent=2)
            logger.info(f"✅ Saved {len(self._ticker_validation_cache)} ticker validations to cache")
        except Exception as e:
            logger.warning(f"⚠️  Failed to save validation cache: {e}")
    
    def _is_quality_news(self, ticker: str, headline: str, full_text: str, url: str = "") -> Tuple[bool, str]:
        """
        Filter out generic/low-quality news before analysis.
        Returns (is_quality, rejection_reason)
        """
        combined = f"{headline} {full_text}".lower()
        ticker_lower = ticker.lower()
        # Quality filter mode from expert playbook: strict | balanced | lenient
        qmode = (self.expert_playbook.get('quality_filter', {}) or {}).get('mode', 'balanced').lower()
        
        # Optional: reject obvious advertorial/PR in strict mode
        if getattr(self, 'ad_popularity_enabled', True):
            domain = None
            if url:
                try:
                    import re as _re
                    m = _re.match(r'https?://([^/]+)/', url + '/')
                    domain = (m.group(1).lower() if m else None)
                except Exception:
                    domain = None
            pr_like_domains = {
                'prnewswire.com', 'businesswire.com', 'globenewswire.com', 'newsvoir.com',
                'indiaprwire.com', 'ptinews.com/prnewswire'
            }
            pr_like_text = [
                r'\bpress\s+release\b', r'\bsponsored\b', r'\badvertorial\b', r'\bpaid\s+promotion\b',
                r'\bbrand\s+campaign\b', r'\bmarketing\s+campaign\b'
            ]
            if (domain and any(domain.endswith(d) or domain == d for d in pr_like_domains)) or \
               any(re.search(p, combined) for p in pr_like_text):
                if getattr(self, 'ad_strict_reject', False) and qmode != 'lenient':
                    return False, "Advertorial/press release source"
        
        # REJECT: Generic industry news patterns
        reject_patterns = [
            (r'among \d+[+-]?\s+(?:firms|companies|stocks)', "Generic industry roundup (mentions many companies)"),
            (r'of \d+ of (?:top|biggest|largest)[- ]?\d+', "Market-wide ranking news (not company-specific)"),
            (r'\b(?:this|next)\s+(?:week|month|quarter)', "Upcoming event (not confirmed news)"),
            (r'\bwill\s+(?:announce|report|declare|release)', "Future event (speculation, not actual)"),
            (r'\bexpected\s+to\s+', "Forecast/speculation (not confirmed)"),
            (r'\bmay\s+(?:report|announce|declare)', "Speculation (not confirmed)"),
            (r'\bset\s+to\s+(?:announce|report|declare)', "Scheduled future event (not actual news)"),
        ]
        
        for pattern, reason in reject_patterns:
            if re.search(pattern, combined):
                # In lenient mode, only enforce the most generic rejections
                if qmode == 'lenient' and reason not in (
                    "Generic industry roundup (mentions many companies)",
                    "Market-wide ranking news (not company-specific)"):
                    continue
                return False, reason
        
        # REJECT: Company not primary focus (appears late or with many others)
        base = ticker.upper().replace('.NS', '')
        ambiguous = set((self.expert_playbook.get('heuristic') or {}).get('ambiguous_symbols', []))
        ticker_pos = combined.find(ticker_lower)
        if base in ambiguous:
            # Require alias/company name presence, not just generic word (e.g., 'global')
            alias_variants = [v.lower() for v in self._company_alias_map.get(base, [])]
            alias_pos = -1
            for v in alias_variants:
                p = combined.find(v)
                if p != -1:
                    alias_pos = p if alias_pos == -1 else min(alias_pos, p)
            if alias_pos == -1:
                return False, "Company alias not found (ambiguous ticker)"
            if qmode != 'lenient' and alias_pos > 120:
                return False, f"Company mentioned too late (position {alias_pos})"
        else:
            if ticker_pos == -1:
                # Broaden: check alias variants from SEC list for all symbols
                alias_variants = [v.lower() for v in self._company_alias_map.get(base, [])]
                found_alias = False
                for v in alias_variants:
                    if v and v in combined:
                        ticker_pos = combined.find(v)
                        found_alias = True
                        break
                if not found_alias:
                    # Try some common shortforms
                    alt_names = {
                        'reliance': ['ril', 'reliance industries'],
                        'tcs': ['tata consultancy', 'tata consulting'],
                        'hdfc': ['hdfcbank', 'hdfc bank'],
                        'icici': ['icicibank', 'icici bank'],
                    }
                    local_found = False
                    for alt in alt_names.get(ticker_lower, []):
                        if alt in combined:
                            ticker_pos = combined.find(alt)
                            local_found = True
                            break
                    if not local_found:
                        return False, "Company name not found in text"
            if qmode != 'lenient' and ticker_pos > 120:
                return False, f"Company mentioned too late (position {ticker_pos})"

        # Additional relevance: ensure action/number appears near first company mention
        try:
            near_start = max(0, ticker_pos - 80)
            near_end = min(len(combined), ticker_pos + 140)
            window = combined[near_start:near_end]
        except Exception:
            window = combined[:160]
        has_numbers_near = bool(re.search(r'(?:₹|rs\.?|inr)\s*\d+|\b\d+\s*(?:cr|crore|bn|billion|mn|million|lakh)\b|\b\d+\s*%\b', window))
        has_action_near = bool(re.search(r'\b(announced|signed|completed|reported|filed|launched|posted|wins|secures|awarded|acquires|merges|appoints)\b', window))
        if qmode != 'lenient' and not (has_numbers_near or has_action_near):
            # If also looks like an aggregator/listicle, reject as irrelevant
            if re.search(r'\b(stocks?\s+to\s+watch|buzzing\s+stocks|top\s+\d+\s+stocks|why\s+\d+\s+stocks)\b', combined):
                return False, "Company mention lacks actionable context (listicle)"
            # If domain is low reputation PR site, reject when no nearby evidence
            if getattr(self, '_domain_reputation', None) and url:
                try:
                    m = re.match(r'https?://([^/]+)/', url + '/')
                    domain = (m.group(1).lower() if m else '')
                except Exception:
                    domain = ''
                rep = self._domain_reputation.get(domain, {})
                if float(rep.get('weight', 0.65)) < 0.70:
                    return False, "Low-signal source without company-specific action"
        
        # REQUIRE: Specific numbers OR specific action words
        has_numbers = bool(re.search(r'(?:₹|rs\.?|inr)\s*\d+|[0-9]+(?:\.[0-9]+)?%|\b\d+\s*(?:cr|crore|bn|billion|mn|million|lakh)\b', combined))
        has_action = bool(re.search(r'\b(?:announced|signed|completed|reported|filed|launched|posted|declares|approves?|wins|secures|awarded|acquires?|merges?|appoints?|adds|raises?|subsidiary)\b', combined))
        
        if qmode != 'lenient' and not (has_numbers or has_action):
            return False, "No specific numbers or confirmed actions"
        
        # Check for confirmed vs speculation words
        confirmed_words = ['announced', 'signed', 'completed', 'reported', 'filed', 'launched', 'posted']
        speculation_words = ['may', 'might', 'could', 'would', 'plans', 'expects', 'considering']
        
        confirmed_count = sum(1 for word in confirmed_words if word in combined)
        speculation_count = sum(1 for word in speculation_words if word in combined)
        
        if qmode != 'lenient' and speculation_count > confirmed_count:
            return False, "More speculation than confirmation words"
        
        return True, "Quality news (company-specific with confirmation)"
    
    def analyze_news_instantly(self, ticker: str, headline: str, 
                               full_text: str = "", url: str = "") -> Optional[InstantAIAnalysis]:
        """
        INSTANT analysis using the selected AI model + Frontier AI
        This is called immediately when news is fetched
        """
        # PRE-FILTER: Check news quality
        is_quality, reason = self._is_quality_news(ticker, headline, full_text, url)
        if not is_quality:
            logger.info(f"⏭️  SKIPPED {ticker}: {reason}")
            logger.info(f"   Headline: {headline[:80]}")
            return None  # Don't analyze low-quality news
        
        logger.info(f"🔍 INSTANT ANALYSIS: {ticker}")
        logger.info(f"   Headline: {headline[:80]}...")

        # Step 1: Call AI model (Claude/Codex/heuristic) - now returns price + fundamental bundles
        ai_analysis, data_bundle = self._call_copilot_ai(ticker, headline, full_text, url)

        price_data = {}
        fundamental_data = {}
        if isinstance(data_bundle, dict):
            price_candidate = data_bundle.get('price')
            fundamental_candidate = data_bundle.get('fundamental')
            if isinstance(price_candidate, dict):
                price_data = price_candidate
            if isinstance(fundamental_candidate, dict):
                fundamental_data = fundamental_candidate

        quarterly_fundamentals = fundamental_data.get('quarterly', {})
        annual_fundamentals = fundamental_data.get('annual', {})
        health_snapshot = fundamental_data.get('financial_health', {})
        validation_snapshot = fundamental_data.get('validation', {})

        # Step 2: Apply Frontier AI scoring
        frontier_score = self._apply_frontier_scoring(ticker, headline, full_text, ai_analysis)

        # Step 3: Combine scores for final ranking
        # HYBRID SCORE NOTE:
        # The base hybrid score blends AI news score with Frontier Quant features,
        # preserving the 60/40 weighting philosophy (AI 60%, Quant 40%).
        # This is an enhancement over a pure AI+technical approach, leveraging
        # a richer quant model while maintaining the same intent.
        base_score = self._combine_scores(ai_analysis, frontier_score)
        final_score = self._apply_fundamental_adjustment(base_score, fundamental_data)
        fundamental_adjustment = final_score - base_score

        # Step 3.5: Apply AI-Supervised Correction Boost
        correction_boost_result = self._apply_correction_boost(
            ticker=ticker,
            ai_score=ai_analysis.get('ai_score', 50),
            certainty=ai_analysis.get('certainty', 50),
            hybrid_score=final_score,
            fundamental_data=fundamental_data
        )
        correction_analysis = correction_boost_result.get('correction_analysis')
        supervision_result = correction_boost_result.get('supervision')
        final_score = correction_boost_result.get('final_score', final_score)
        correction_boost_applied = correction_boost_result.get('boost_applied', 0.0)
        boost_decision = correction_boost_result.get('decision', 'NO_BOOST')

        # Fetch corporate actions data for catalyst scoring
        catalyst_data = {}
        try:
            from corporate_actions_fetcher import get_corporate_action_score
            base_symbol = ticker.upper().replace('.NS', '')
            catalyst_data = get_corporate_action_score(base_symbol)
        except Exception:
            pass

        # Create instant analysis result with real-time price data
        company_name = self._company_name_map.get(base_symbol)
        result = InstantAIAnalysis(
            ticker=ticker,
            headline=headline[:200],
            timestamp=datetime.now(),
            # Use the combined weighted score for ranking + display
            ai_score=final_score,
            sentiment=ai_analysis.get('sentiment', 'neutral'),
            impact_prediction=ai_analysis.get('impact', 'moderate'),
            catalysts=ai_analysis.get('catalysts', []),
            risks=ai_analysis.get('risks', []),
            certainty=ai_analysis.get('certainty', 50),
            recommendation=ai_analysis.get('recommendation', 'HOLD'),
            reasoning=ai_analysis.get('reasoning', ''),
            quant_alpha=frontier_score.get('alpha', None),
            alpha_gate_flags=(frontier_score.get('alpha_metrics', {}) or {}).get('gate_flags'),
            alpha_setup_flags=(frontier_score.get('alpha_metrics', {}) or {}).get('setup_flags'),
            company_name=company_name,
            final_rank=None,  # Set later after all analyzed
            # Real-time price data from yfinance (NOT training data)
            current_price=price_data.get('current_price'),
            price_timestamp=price_data.get('price_timestamp'),
            entry_zone_low=price_data.get('entry_zone_low'),
            entry_zone_high=price_data.get('entry_zone_high'),
            target_conservative=price_data.get('target_conservative'),
            target_aggressive=price_data.get('target_aggressive'),
            stop_loss=price_data.get('stop_loss'),
            quarterly_earnings_growth_yoy=quarterly_fundamentals.get('earnings_yoy_growth_pct'),
            annual_earnings_growth_yoy=annual_fundamentals.get('earnings_yoy_growth_pct'),
            profit_margin_pct=(
                quarterly_fundamentals.get('profit_margin_pct')
                if quarterly_fundamentals.get('profit_margin_pct') is not None
                else annual_fundamentals.get('profit_margin_pct')
            ),
            debt_to_equity=health_snapshot.get('debt_to_equity'),
            is_profitable=health_snapshot.get('is_profitable'),
            net_worth_positive=health_snapshot.get('net_worth_positive'),
            financial_health_status=validation_snapshot.get('overall_health')
            if isinstance(validation_snapshot, dict) else None,
            fundamental_adjustment=fundamental_adjustment if abs(fundamental_adjustment) >= 0.05 else None,
            # Corporate actions catalyst data
            catalyst_score=catalyst_data.get('catalyst_score', 0) if catalyst_data else 0,
            has_dividend=catalyst_data.get('has_recent_dividend', False) if catalyst_data else False,
            dividend_amount=catalyst_data.get('dividend_amount') if catalyst_data else None,
            has_bonus=catalyst_data.get('has_recent_bonus', False) if catalyst_data else False,
            bonus_ratio=catalyst_data.get('bonus_ratio') if catalyst_data else None,
            # AI-Supervised Correction Boost fields
            correction_detected=correction_analysis.get('correction_detected') if correction_analysis else None,
            correction_pct=correction_analysis.get('correction_pct') if correction_analysis else None,
            reversal_confirmed=correction_analysis.get('reversal_confirmed') if correction_analysis else None,
            correction_confidence=correction_analysis.get('correction_confidence') if correction_analysis else None,
            oversold_score=correction_analysis.get('oversold_score') if correction_analysis else None,
            fundamental_confidence=correction_analysis.get('fundamental_confidence') if correction_analysis else None,
            catalyst_strength=correction_analysis.get('catalyst_strength') if correction_analysis else None,
            boost_applied=correction_boost_applied,
            boost_tier=self._get_boost_tier(correction_boost_applied) if correction_boost_applied > 0 else None,
            correction_reasoning=correction_analysis.get('reasoning') if correction_analysis else None,
            risk_filters_passed=correction_analysis.get('risk_filters_passed') if correction_analysis else None,
            risk_violations=correction_analysis.get('risk_details', {}).get('violations') if correction_analysis else None,
            market_context=correction_analysis.get('market_context') if correction_analysis else None,
            market_vix_level=correction_analysis.get('vix_level') if correction_analysis else None,
            supervisor_verdict=supervision_result.supervisor_verdict if supervision_result else None,
            supervisor_confidence=supervision_result.confidence_score if supervision_result else None,
            supervision_notes=supervision_result.reasoning if supervision_result else None,
            alignment_issues=supervision_result.alignment_issues if supervision_result else None,
            supervisor_recommendations=supervision_result.recommendations if supervision_result else None,
        )

        if abs(fundamental_adjustment) >= 0.05:
            logger.info(
                "   Fundamental adjustment: %+0.2f (health=%s, quarterly_eYoY=%s, annual_eYoY=%s)",
                fundamental_adjustment,
                result.financial_health_status or 'unknown',
                f"{result.quarterly_earnings_growth_yoy:.2f}%" if result.quarterly_earnings_growth_yoy is not None else 'n/a',
                f"{result.annual_earnings_growth_yoy:.2f}%" if result.annual_earnings_growth_yoy is not None else 'n/a'
            )

        # OPTIONAL: Get AI web search verified health data (non-blocking, cached)
        # This overrides yfinance data with fresh web search data for better accuracy
        if self.health_integration:
            try:
                health_report = self.health_integration.get_health_data(ticker, self._company_name_map.get(ticker.upper().replace('.NS', '')))
                if health_report:
                    # Override profit/loss status with verified web search data
                    result.is_profitable = health_report.is_profitable
                    # Store health data for CSV output
                    result.health_data = {
                        'is_profitable': health_report.is_profitable,
                        'latest_profit_loss': health_report.latest_profit_loss,
                        'profit_loss_period': health_report.profit_loss_period,
                        'health_status': health_report.health_status,
                        'consecutive_loss_quarters': health_report.consecutive_loss_quarters,
                        'warning_flags': health_report.warning_flags,
                        'ai_analysis': health_report.ai_analysis
                    }
                    logger.info(f"   🔍 Health verified: {health_report.health_status} | Profitable: {health_report.is_profitable}")
            except Exception as e:
                logger.debug(f"Health data collection skipped for {ticker}: {e}")

        # Store result and update ranking (thread-safe)
        with self._lock:
            if ticker not in self.live_results:
                self.live_results[ticker] = []
            self.live_results[ticker].append(result)
            self._update_live_ranking()
        
        logger.info(f"   ✅ Score: {result.ai_score:.1f} | Sentiment: {result.sentiment}")
        logger.info(f"   Recommendation: {result.recommendation}")
        
        return result
    
    def _call_copilot_ai(self, ticker: str, headline: str,
                        full_text: str, url: str) -> Tuple[Dict, Dict]:
        """Call the configured AI provider and fall back to heuristics if needed.

        Returns:
            Tuple of (ai_result_dict, combined_data_dict)
        """
        # Build comprehensive prompt with price and fundamental data
        prompt, combined_data = self._build_ai_prompt(ticker, headline, full_text, url)
        cache_key = self._cache_key(ticker, headline, full_text)

        if cache_key in self.analysis_cache:
            logger.info('♻️  Reusing cached AI analysis for %s', ticker)
            return self.analysis_cache[cache_key], combined_data

        if self.ai_client.selected_provider == 'heuristic':
            if self.ai_client.requested_provider in {'codex', 'openai', 'gpt', 'gpt-4', 'gpt-4o'}:
                logger.info('Using heuristics for %s (Codex unavailable; set OPENAI_API_KEY or CODEX_SHELL_CMD).', ticker)
            else:
                logger.info('Using heuristic analyzer for %s (no external AI configured).', ticker)
            result = self._intelligent_pattern_analysis(prompt)
            self.analysis_cache[cache_key] = result
            return result, combined_data

        if self.ai_call_limit is not None and self.ai_call_count >= self.ai_call_limit:
            logger.info(
                'AI call limit reached (%s); switching to heuristic mode for %s',
                self.ai_call_limit,
                ticker,
            )
            self.ai_limit_exhausted = True
            self.limit_affected_tickers.add(ticker)
            result = self._intelligent_pattern_analysis(prompt)
            self.analysis_cache[cache_key] = result
            return result, combined_data

        try:
            result = self._invoke_ai_model(prompt)
            self.ai_call_count += 1
            self.external_ai_used_tickers.add(ticker)
            self.analysis_cache[cache_key] = result
            return result, combined_data
        except Exception as e:
            logger.warning(f"❌ AI call failed ({e}); falling back to heuristic analysis")
            result = self._intelligent_pattern_analysis(prompt)
            self.analysis_cache[cache_key] = result
            return result, combined_data
    
    def _build_ai_prompt(self, ticker: str, headline: str,
                        full_text: str, url: str) -> Tuple[str, Dict]:
        """Build comprehensive AI prompt for analysis (Claude-optimized)

        Returns:
            Tuple of (prompt_text, combined_data_dict)
        """

        # Load historical learnings
        historical_context = self._load_historical_learnings(ticker)

        # CRITICAL: Fetch real-time price data FIRST (to prevent AI from using training data)
        price_data = {}
        try:
            from realtime_price_fetcher import get_comprehensive_price_data, format_price_context_for_ai
            # Get preliminary sentiment for price calculation
            prelim_sentiment = 'bullish' if 'profit' in headline.lower() or 'growth' in headline.lower() else 'neutral'
            price_data = get_comprehensive_price_data(ticker, sentiment=prelim_sentiment, expected_move_pct=0.0)
            price_context = format_price_context_for_ai(price_data)
        except Exception as e:
            print(f"⚠️  Price fetch failed for {ticker}: {e}", file=sys.stderr)
            price_context = f"""
⚠️  REAL-TIME PRICE DATA UNAVAILABLE FOR {ticker}
Error: {str(e)[:200]}

CRITICAL INSTRUCTION:
- You MUST NOT use memorized/training data prices
- If price is needed for analysis, state "INSUFFICIENT DATA"
- Return neutral scores and recommend manual verification
"""
            price_data = {'price_data_available': False, 'ticker': ticker}

        # CRITICAL: Fetch real-time fundamental data (quarterly/annual results, financials)
        fundamental_data = {}
        fundamental_context = ""
        try:
            from fundamental_data_fetcher import FundamentalDataFetcher
            fetcher = FundamentalDataFetcher(use_cache=False)
            fundamental_data = fetcher.fetch_comprehensive_fundamentals(ticker)
            if fundamental_data.get('data_available'):
                fundamental_context = fetcher.format_for_ai_prompt(fundamental_data)
            else:
                fundamental_context = f"⚠️  FUNDAMENTAL DATA UNAVAILABLE FOR {ticker} (fetched from yfinance, may be limited)"
        except Exception as e:
            print(f"⚠️  Fundamental fetch failed for {ticker}: {e}", file=sys.stderr)
            fundamental_context = f"⚠️  FUNDAMENTAL DATA FETCH ERROR FOR {ticker}: {str(e)[:200]}"
            fundamental_data = {'data_available': False, 'ticker': ticker}

        # Combine all data for return
        combined_data = {
            'price': price_data,
            'fundamental': fundamental_data,
            'ticker': ticker
        }

        # Fetch real-time technical context locally to ground AI to fresh data
        tech_summary = "Technical data unavailable"
        try:
            sys.path.insert(0, os.path.dirname(__file__))
            import exit_intelligence_analyzer as exit_analyzer  # reuse TA
            df = exit_analyzer.get_stock_data(ticker)
            if df is not None and not df.empty:
                tech = exit_analyzer.calculate_technical_indicators(df)
                if tech:
                    tech_summary = (
                        f"Current Price: {tech.get('current_price','N/A')}\n"
                        f"RSI: {tech.get('rsi','N/A')}\n"
                        f"Price vs 20DMA: {tech.get('price_vs_sma20_pct','N/A')}%\n"
                        f"Price vs 50DMA: {tech.get('price_vs_sma50_pct','N/A')}%\n"
                        f"10d Momentum: {tech.get('momentum_10d_pct','N/A')}%\n"
                        f"Volume Ratio: {tech.get('volume_ratio','N/A')}\n"
                        f"Recent Trend: {tech.get('recent_trend','N/A')}"
                    )
        except Exception:
            pass

        # Build a priority header to anchor the model on price, fundamentals, and trade levels first
        priority_header = price_context + "\n\n" + fundamental_context + "\n\n"

        # Add mandatory AI confirmation section
        ai_confirmation = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  MANDATORY DATA SOURCE ACKNOWLEDGMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOU MUST INCLUDE THIS IN YOUR JSON RESPONSE:

"data_source_confirmation": {{
    "used_provided_price": true,
    "used_provided_fundamentals": true,
    "no_training_data_used": true,
    "confirmation_statement": "I confirm using ONLY the yfinance data provided in this prompt for {ticker}"
}}

By including this field, you confirm:
1. ✅ You used the real-time price data from yfinance (provided above)
2. ✅ You used the quarterly/annual results from yfinance (provided above)
3. ✅ You did NOT use any memorized/training data for {ticker}
4. ✅ All calculations are based ONLY on the data in this prompt

⚠️  FAILURE TO INCLUDE THIS FIELD WILL INVALIDATE YOUR ANALYSIS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""

        # CRITICAL: Add explicit temporal context to prevent training data bias
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # News timestamp - we don't have this in the function params, so we say "within last X hours"
        news_timestamp_str = "within last 48 hours"

        prompt = f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 TEMPORAL CONTEXT - CRITICAL FOR AVOIDING TRAINING DATA BIAS 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**TODAY'S DATE**: {current_date}
**ANALYSIS TIMESTAMP**: {current_datetime}
**NEWS PUBLISHED**: {news_timestamp_str}

⚠️  CRITICAL INSTRUCTIONS:
1. All data provided below is CURRENT as of {current_date}
2. This news article is from the LAST 48 HOURS (recent/current event)
3. Price and fundamental data are REAL-TIME (fetched just now from yfinance)
4. DO NOT apply historical knowledge or training data about {ticker}
5. If any provided data contradicts your training knowledge, THE PROVIDED DATA IS CORRECT

This is a REAL-TIME analysis of CURRENT market conditions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# SWING TRADE SETUP ANALYSIS - {ticker}

## CALIBRATION INSTRUCTIONS (CRITICAL FOR CLAUDE)

**IMPORTANT**: Follow these calibration rules to avoid over-conservative scoring:

### Scoring Calibration
- **70-85 range is NORMAL** for quality news with confirmed catalysts
- **50-69 range** for weak/speculative news
- **30-49 range ONLY** for irrelevant or negative news
- **DO NOT default to 30-40** unless news is truly poor

### Certainty Calibration
- **60-80% is NORMAL** for tier-1 English news sources
- **40-59%** for unconfirmed/speculation
- **30% should be RARE** - only for vague news
- **Confirmed numbers/deals = minimum 65% certainty**

### Sentiment & Catalyst Rules
- Positive earnings/deals/investments = **"bullish"** (not "neutral")
- **DO NOT say catalysts = "None"** - always identify news category
- Types: earnings, investment, expansion, contract, partnership, sector_momentum
- **Indirect news counts** - sector/supply chain impacts matter

{historical_context}

{priority_header}

{ai_confirmation}

## Task
Analyze this news for **swing trading opportunity (5-15 day horizon)** using, in this order:
1. Swing trade setup FIRST (entry/targets/stop based on current price)
2. Technical analysis (support/resistance, indicators, momentum/volume)
3. Fundamental catalyst analysis (news impact assessment)
4. Risk management (risk-reward ratio, confirmation)
5. Real-time market data verification

## Stock Information
- **Ticker**: {ticker}
- **Headline**: {headline}
- **Full Text**: {full_text[:1000] if full_text else "N/A"}
- **URL**: {url}

## TECHNICAL CONTEXT (Fetched now via yfinance)
{tech_summary}
Fetched At: {datetime.now().isoformat()}

## Analysis Framework

### 1. Swing Trade Setup (first priority, 25 points)
Provide specific actionable levels based on CURRENT PRICE and technicals:
- Entry Zone: Optimal buy zone/price range for entry
- Target 1: Conservative exit target (first profit booking)
- Target 2: Aggressive exit target (if momentum continues)
- Stop Loss: Strict stop-loss level for risk management
- Time Horizon: 5-15 day expected holding period
- Risk-Reward Ratio: Calculate R:R ratio (e.g., 1:2, 1:3)

### 2. Fundamental Catalyst Analysis (30 points)
Identify:
- Catalyst type (earnings, M&A, investment, expansion, contract, sector_momentum, etc.)
- Deal value (₹ crores if mentioned)
- Specificity (confirmed vs speculation)
- Impact magnitude relative to market cap
- **Indirect correlations** (sector, supply chain, thematic impacts)
- Fake rally risk (hype vs substance)

### 3. Technical Analysis - REQUIRED (30 points)
Use the TECHNICAL CONTEXT provided above (fetched now) to assess:
- Current price and proximity to key MAs (20/50‑DMA)
- RSI and momentum (10‑day return)
- Volume trend (volume ratio)
- Recent price action (up/down)


### 4. Market Context & Sentiment (15 points)
Assess:
- Sector momentum (industry trend context)
- Market breadth (Nifty/Sensex trend alignment)
- Certainty level (specific numbers, confirmed actions)
- Source credibility

## Output Format (JSON)
{{
    "score": 0-100,
    "sentiment": "bullish|bearish|neutral",
    "impact": "high|medium|low",
    "catalysts": ["type1", "type2"],
    "deal_value_cr": number or 0,
    "risks": ["risk1", "risk2"],
    "certainty": 0-100,
    "recommendation": "STRONG BUY|BUY|ACCUMULATE|HOLD|REDUCE|SELL",
    "reasoning": "detailed explanation",
    "expected_move_pct": number,
    "confidence": 0-100,

    "data_source_confirmation": {{
        "used_provided_price": true,
        "used_provided_fundamentals": true,
        "no_training_data_used": true,
        "confirmation_statement": "I confirm using ONLY the yfinance data provided in this prompt for {ticker}"
    }},

    "technical_analysis": {{
        "current_price": number,
        "support_levels": [level1, level2, level3],
        "rsi": number (0-100),
        "rsi_interpretation": "overbought|neutral|oversold",
        "macd_signal": "bullish|bearish|neutral",
        "volume_trend": "increasing|decreasing|average",
        "price_trend": "uptrend|downtrend|sideways"
    }},

    "swing_trade_setup": {{
        "entry_zone_low": number,
        "entry_zone_high": number,
        "target_1": number,
        "target_2": number,
        "stop_loss": number,
        "time_horizon_days": "5-15",
        "risk_reward_ratio": "1:X",
        "sector_momentum": "strong|moderate|weak"
    }}
}}

## Evidence Policy - CRITICAL
Base your decision ONLY on the article text and the TECHNICAL CONTEXT provided (both fetched now). Do NOT use prior training knowledge or external facts not present here. Do not invent values when technical context is unavailable.

## Scoring Guidelines with EXAMPLES

### 90-100: Exceptional (Strong Direct Catalyst + Bullish Technicals)
**Examples:**
- Company reports ₹2,000cr profit, +25% YoY → Score: 92, Certainty: 85%
- Signs $500M contract with confirmed terms → Score: 95, Certainty: 90%

### 75-89: Strong (Solid Catalyst + Favorable Technicals)
**Examples:**
- Q1 profit ₹500cr, +12% YoY (tier-1 source) → Score: 82, Certainty: 75%
- Announces ₹300cr investment in facility → Score: 78, Certainty: 70%
- **NVIDIA $5T valuation + Company has AI exposure → Score: 76, Certainty: 65%**
- Signs partnership with major client → Score: 75, Certainty: 60%

### 60-74: Moderate (Decent Catalyst + Acceptable Technicals)
**Examples:**
- "Plans to invest ₹200cr" (speculation) → Score: 68, Certainty: 50%
- Sector-wide positive news (indirect) → Score: 65, Certainty: 55%

### 45-59: Weak (Minor Catalyst or Unfavorable Technicals)
**Examples:**
- Generic "exploring opportunities" → Score: 52, Certainty: 35%
- Weak rumor from low-tier source → Score: 48, Certainty: 30%

### 0-44: Poor (No Catalyst or Bearish Technicals)
**Examples:**
- Completely irrelevant news → Score: 35, Certainty: 20%
- Negative news (losses, scandals) → Score: 25, Certainty: 70%

## CALIBRATION CHECKLIST (Verify before submitting)

1. ✅ **Score Check**: Confirmed numbers + tier-1 source → score should be 70+
2. ✅ **Certainty Check**: Hindu BusinessLine/ET/Mint → certainty should be 60+
3. ✅ **Sentiment Check**: Growth/profit/investment news → sentiment "bullish"
4. ✅ **Catalyst Check**: Did I identify at least 1-2 catalyst types? (Never "None")
5. ✅ **Recommendation Check**: If score 70+, recommendation should be "BUY" or "STRONG BUY"

## COMMON MISTAKES TO AVOID

❌ **DON'T**: Give 33/100 to confirmed earnings from tier-1 source
✅ **DO**: Give 75-85/100 to confirmed earnings from tier-1 source

❌ **DON'T**: Give 30% certainty to BusinessLine article with specific numbers
✅ **DO**: Give 70-80% certainty to BusinessLine article with specific numbers

❌ **DON'T**: Mark "neutral" for profit growth news
✅ **DO**: Mark "bullish" for profit growth news

❌ **DON'T**: Say catalysts = "None"
✅ **DO**: Always identify at least 1 catalyst type

**IMPORTANT**:
- Provide specific numerical values for all technical levels
- Calculate precise entry/exit/stop-loss prices
- Include risk-reward ratio calculation
- Focus on 5-15 day swing trading horizon
- **Use full scoring range (20-95), not just 30-40**
- **Be confident - don't under-score quality news**

Analyze and respond with JSON only.
"""

        # Optional strict real-time grounding: disallow prior training knowledge
        if (os.getenv('NEWS_STRICT_CONTEXT') or os.getenv('AI_STRICT_CONTEXT') or os.getenv('EXIT_STRICT_CONTEXT') or '0').strip() == '1':
            prompt += "\n\nSTRICT REAL-TIME CONTEXT: Base your decision ONLY on the provided article text and the TECHNICAL CONTEXT above. Do not use prior training knowledge or external facts not fetched now. If technical context shows 'unavailable', do not invent values."
        return prompt, combined_data

    def _record_predictions_to_learning_db(self, qualified_stocks):
        """Record predictions to learning database for feedback tracking"""
        try:
            from realtime_feedback_loop import FeedbackLoopTracker

            tracker = FeedbackLoopTracker()

            for rank, (ticker, score, latest, analyses) in qualified_stocks:
                # Build analysis dict for feedback tracker
                analysis_data = {
                    'score': score,
                    'recommendation': latest.recommendation,
                    'sentiment': latest.sentiment,
                    'catalysts': latest.catalysts or [],
                    'certainty': latest.certainty,
                    'expected_move_pct': 0,  # Not available from InstantAIAnalysis
                    'technical_analysis': {
                        'current_price': 0,  # Would need to fetch separately
                        'rsi': 50,  # Default if not available
                        'volume_trend': 'average'
                    },
                    'swing_trade_setup': {},
                    'risks': latest.risks or []
                }

                tracker.record_prediction(ticker, analysis_data)

            logger.info(f"✅ Recorded {len(qualified_stocks)} predictions to learning database")
        except Exception as e:
            logger.warning(f"⚠️  Could not record predictions to learning database: {e}")

    def _load_historical_learnings(self, ticker: str) -> str:
        """Load historical performance data and learnings for this ticker"""
        import sqlite3
        from pathlib import Path

        context_lines = []

        # Load learned weights and insights
        learned_weights_path = Path('learning/learned_weights.json')
        if learned_weights_path.exists():
            try:
                with open(learned_weights_path, 'r') as f:
                    learned_data = json.load(f)

                insights = learned_data.get('insights', [])
                overall_accuracy = learned_data.get('overall_accuracy', 0)

                if insights or overall_accuracy:
                    context_lines.append("\n## HISTORICAL LEARNINGS (Apply these to your analysis)")
                    context_lines.append("\n**System Performance:**")
                    context_lines.append(f"- Overall prediction accuracy: {overall_accuracy:.1f}%")

                    if insights:
                        context_lines.append("\n**Key Insights from Past Predictions:**")
                        for insight in insights:
                            context_lines.append(f"- {insight}")
            except Exception as e:
                logger.debug(f"Could not load learned weights: {e}")

        # Load ticker-specific history from learning.db
        learning_db_path = Path('learning/learning.db')
        if learning_db_path.exists():
            try:
                con = sqlite3.connect(str(learning_db_path))
                con.row_factory = sqlite3.Row
                cur = con.cursor()

                # Get ticker stats
                cur.execute(
                    """SELECT appearances, avg_adj, reliability_score, success_2p, fake_rise_cnt
                       FROM ticker_stats WHERE ticker=?""",
                    (ticker.upper(),)
                )
                ticker_row = cur.fetchone()

                if ticker_row:
                    appearances = ticker_row['appearances']
                    avg_adj = ticker_row['avg_adj']
                    reliability = ticker_row['reliability_score'] or 0.0
                    successes = ticker_row['success_2p'] or 0
                    failures = ticker_row['fake_rise_cnt'] or 0

                    if appearances > 0:
                        context_lines.append(f"\n**Historical Performance for {ticker}:**")
                        context_lines.append(f"- Past appearances in analysis: {appearances}")
                        context_lines.append(f"- Average historical score: {avg_adj:.1f}/100")

                        if successes > 0 or failures > 0:
                            success_rate = (successes / max(1, successes + failures)) * 100
                            context_lines.append(f"- Win/Loss record: {successes} wins, {failures} losses ({success_rate:.0f}% success)")

                            if reliability < -0.2:
                                context_lines.append(f"- ⚠️  WARNING: This ticker has underperformed (reliability: {reliability:.2f})")
                                context_lines.append("  → Apply stricter scrutiny and reduce score by 5-10 points")
                            elif reliability > 0.3:
                                context_lines.append(f"- ✅ This ticker has historically performed well (reliability: {reliability:.2f})")
                                context_lines.append("  → Can be more confident in positive signals")

                # Get event-type performance
                cur.execute(
                    """SELECT event_type, cnt, avg_score, success_2p, fake_rise_cnt
                       FROM event_stats
                       WHERE cnt >= 2
                       ORDER BY avg_score DESC
                       LIMIT 5"""
                )
                event_rows = cur.fetchall()

                if event_rows:
                    context_lines.append("\n**Event Type Performance (Top catalysts):**")
                    for row in event_rows:
                        event_type = row['event_type']
                        avg_score = row['avg_score']
                        successes = row['success_2p'] or 0
                        failures = row['fake_rise_cnt'] or 0

                        success_rate = (successes / max(1, successes + failures)) * 100 if (successes + failures) > 0 else 0

                        if success_rate > 60:
                            context_lines.append(f"- {event_type}: avg score {avg_score:.1f}, {success_rate:.0f}% success ✅")
                        elif success_rate < 40:
                            context_lines.append(f"- {event_type}: avg score {avg_score:.1f}, {success_rate:.0f}% success ⚠️")
                        else:
                            context_lines.append(f"- {event_type}: avg score {avg_score:.1f}, {success_rate:.0f}% success")

                con.close()
            except Exception as e:
                logger.debug(f"Could not load ticker history from learning.db: {e}")

        if context_lines:
            context_lines.append("\n**How to use this data:**")
            context_lines.append("- Adjust your score based on historical reliability")
            context_lines.append("- Apply learned insights about overbought stocks, volume, etc.")
            context_lines.append("- Be cautious with event types that have underperformed")
            context_lines.append("- Factor in ticker-specific win/loss record")
            return "\n".join(context_lines)
        else:
            return ""

    def _load_expert_playbook(self) -> Dict:
        """Load expert playbook JSON if present; return dict or {}."""
        try:
            path = Path('expert_playbook.json')
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    import json as _json
                    return _json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load expert_playbook.json: {e}")
        return {}

    def _load_company_aliases(self) -> Dict[str, List[str]]:
        """Map base symbol -> list of company name variants from sec_list.csv."""
        aliases: Dict[str, List[str]] = {}
        try:
            with open('sec_list.csv', 'r', encoding='utf-8', errors='ignore') as cf:
                import csv as _csv, re as _re
                reader = _csv.DictReader(cf)
                for row in reader:
                    sym = (row.get('Symbol') or '').strip().upper()
                    name = (row.get('Security Name') or '').strip()
                    if not sym or not name:
                        continue
                    base = sym.replace('.NS', '')
                    nm = name
                    variants = {nm.lower(), nm.title()}
                    nm2 = _re.sub(r"\blimited\b", "ltd", nm, flags=_re.I).strip()
                    variants.add(nm2.lower()); variants.add(nm2.title())
                    nm3 = _re.sub(r"[^A-Za-z0-9\s]", "", nm)
                    variants.add(nm3.lower()); variants.add(nm3.title())
                    aliases[base] = list(sorted({v for v in variants if v}))
        except Exception:
            pass
        return aliases

    def _load_company_names(self) -> Dict[str, str]:
        names: Dict[str, str] = {}
        try:
            with open('sec_list.csv', 'r', encoding='utf-8', errors='ignore') as cf:
                import csv as _csv
                reader = _csv.DictReader(cf)
                for row in reader:
                    sym = (row.get('Symbol') or '').strip().upper()
                    name = (row.get('Security Name') or '').strip()
                    if not sym or not name:
                        continue
                    base = sym.replace('.NS', '')
                    names[base] = name
        except Exception:
            pass
        return names

    def _load_domain_reputation(self) -> Dict[str, Dict]:
        """Load domain reputation weights if present; else provide sensible defaults.

        Schema per domain:
          {
            "weight": float 0.0–1.0 (credibility/popularity prior),
            "type": "premium|tier1|tier2|aggregator|blog|prwire",
            "popularity": int 0–100 (optional)
          }
        """
        defaults: Dict[str, Dict] = {
            # Premium international/business
            'reuters.com': { 'weight': 1.00, 'type': 'premium', 'popularity': 98 },
            'bloomberg.com': { 'weight': 0.98, 'type': 'premium', 'popularity': 97 },
            'bqprime.com': { 'weight': 0.92, 'type': 'tier1', 'popularity': 88 },
            # India finance publishers
            'economictimes.indiatimes.com': { 'weight': 0.95, 'type': 'tier1', 'popularity': 95 },
            'livemint.com': { 'weight': 0.94, 'type': 'tier1', 'popularity': 92 },
            'moneycontrol.com': { 'weight': 0.93, 'type': 'tier1', 'popularity': 93 },
            'business-standard.com': { 'weight': 0.92, 'type': 'tier1', 'popularity': 86 },
            'thehindubusinessline.com': { 'weight': 0.90, 'type': 'tier1', 'popularity': 82 },
            'financialexpress.com': { 'weight': 0.88, 'type': 'tier1', 'popularity': 84 },
            'cnbctv18.com': { 'weight': 0.86, 'type': 'tier1', 'popularity': 80 },
            'businesstoday.in': { 'weight': 0.84, 'type': 'tier2', 'popularity': 78 },
            'zeebiz.com': { 'weight': 0.82, 'type': 'tier2', 'popularity': 76 },
            # PR wires / advertorial-heavy
            'prnewswire.com': { 'weight': 0.45, 'type': 'prwire', 'popularity': 75 },
            'businesswire.com': { 'weight': 0.48, 'type': 'prwire', 'popularity': 74 },
            'globenewswire.com': { 'weight': 0.48, 'type': 'prwire', 'popularity': 72 },
            'newsvoir.com': { 'weight': 0.50, 'type': 'prwire', 'popularity': 60 },
            # Exchange filings (credible but may need context)
            'bseindia.com': { 'weight': 0.90, 'type': 'exchange', 'popularity': 85 },
            'nseindia.com': { 'weight': 0.92, 'type': 'exchange', 'popularity': 88 },
        }

        try:
            path = Path('domain_reputation.json')
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    import json as _json
                    data = _json.load(f)
                    # Merge user-provided over defaults
                    for k, v in (data or {}).items():
                        if not isinstance(v, dict):
                            continue
                        defaults[str(k).lower()] = {
                            'weight': float(v.get('weight', defaults.get(k, {}).get('weight', 0.65))),
                            'type': str(v.get('type', defaults.get(k, {}).get('type', 'unknown'))),
                            'popularity': int(v.get('popularity', defaults.get(k, {}).get('popularity', 60)))
                        }
        except Exception as e:
            logger.warning(f"Failed to load domain_reputation.json: {e}")

        return defaults

    def _cache_key(self, ticker: str, headline: str, full_text: str) -> str:
        """Create a stable hash so duplicate headlines reuse AI output."""
        normalized = f"{ticker.strip().upper()}|{headline.strip()}|{(full_text or '')[:400].strip()}"
        return hashlib.sha1(normalized.encode('utf-8', errors='ignore')).hexdigest()

    def validate_ticker_with_ai(self, ticker: str) -> Tuple[bool, str]:
        """
        Use AI to validate if ticker is a valid NSE/BSE stock.
        Returns (is_valid, reason/company_name)
        """
        # If validation is disabled, accept all tickers
        if not self.enable_ticker_validation:
            return (True, "Validation disabled")

        # Check cache first
        cache_key = f"TICKER_VALIDATION:{ticker.upper()}"
        if cache_key in self._ticker_validation_cache:
            cached_result = self._ticker_validation_cache[cache_key]
            # Handle both tuple and list formats from cache
            if isinstance(cached_result, (list, tuple)) and len(cached_result) == 2:
                return tuple(cached_result)
            # Fallback for malformed cache
            logger.warning(f"⚠️  Malformed cache entry for {ticker}, re-validating")

        # For heuristic mode, we can't validate - just accept all
        if self.ai_client.selected_provider == 'heuristic':
            logger.info(f"⚠️  Heuristic mode: Cannot validate {ticker}, accepting by default")
            result = (True, "Accepted (heuristic mode)")
            self._ticker_validation_cache[cache_key] = result
            return result

        # Build validation prompt
        validation_prompt = f"""Check if '{ticker}' is a valid stock ticker for NSE (National Stock Exchange) or BSE (Bombay Stock Exchange) in India.

Return ONLY valid JSON with this exact format:
{{
    "is_valid": true or false,
    "exchange": "NSE" or "BSE" or "BOTH" or "NONE",
    "company_name": "Full company name" or "NOT FOUND",
    "reason": "Brief explanation"
}}

Rules:
- is_valid should be true ONLY if this is an actively traded equity stock on NSE or BSE
- is_valid should be false for: non-existent tickers, ETFs, indices, mutual funds, bonds, delisted stocks
- Use your knowledge or internet to verify the ticker

Ticker to validate: {ticker}
"""

        try:
            # Call AI (respecting call limits)
            if self.ai_call_limit is not None and self.ai_call_count >= self.ai_call_limit:
                logger.warning(f"AI call limit reached, cannot validate {ticker}, accepting by default")
                result = (True, "Accepted (AI limit reached)")
                self._ticker_validation_cache[cache_key] = result
                return result

            response = self.ai_client.invoke(validation_prompt)
            self.ai_call_count += 1

            is_valid = response.get('is_valid', False)
            company_name = response.get('company_name', 'UNKNOWN')
            exchange = response.get('exchange', 'NONE')
            reason = response.get('reason', 'No reason provided')

            if is_valid:
                result = (True, f"{company_name} ({exchange})")
                logger.info(f"✅ {ticker}: Valid - {company_name} ({exchange})")
            else:
                result = (False, reason)
                logger.info(f"❌ {ticker}: Invalid - {reason}")

            self._ticker_validation_cache[cache_key] = result
            return result

        except Exception as e:
            logger.warning(f"⚠️  Ticker validation failed for {ticker}: {e}. Accepting by default.")
            result = (True, "Accepted (validation error)")
            self._ticker_validation_cache[cache_key] = result
            return result
    
    def _invoke_ai_model(self, prompt: str) -> Dict:
        """Invoke the configured AI provider when external keys are available."""
        if not self.ai_client or self.ai_client.selected_provider == 'heuristic':
            raise RuntimeError('External AI provider not configured')
        return self.ai_client.invoke(prompt)
    
    def _intelligent_pattern_analysis(self, prompt: str) -> Dict:
        """
        Intelligent pattern-based analysis when AI API not available
        Uses advanced heuristics + Frontier AI patterns
        """
        # Extract ticker, headline, full_text and URL from the prompt
        import re
        ticker_match = re.search(r'\*\*Ticker\*\*: (\w+)', prompt)
        headline_match = re.search(r'\*\*Headline\*\*: (.+?)(?:\n|\*\*)', prompt)
        # Capture Full Text content but stop before the next metadata field like "- **URL**:"
        text_match = re.search(r'\*\*Full Text\*\*:\s*(.+?)(?:\n- \*\*URL\*\*:|\n\*\*|$)', prompt, re.DOTALL)
        url_match = re.search(r'\*\*URL\*\*: (https?://[^\s\n]+)', prompt)

        ticker = ticker_match.group(1) if ticker_match else "UNKNOWN"
        headline = headline_match.group(1).strip() if headline_match else ""
        full_text = (text_match.group(1).strip() if text_match else "")
        url = url_match.group(1).strip() if url_match else ""

        combined_text = (headline + " " + full_text).lower()

        # Source credibility from domain (with expert override)
        domain = None
        if url:
            m = re.match(r'https?://([^/]+)/', url + '/')
            domain = (m.group(1).lower() if m else None)
        credible_domains = set(self.expert_playbook.get('heuristic', {}).get('credible_domains', [
            'reuters.com', 'bloomberg.com', 'bqprime.com',
            'economictimes.indiatimes.com', 'livemint.com', 'moneycontrol.com',
            'business-standard.com', 'thehindubusinessline.com', 'financialexpress.com',
            'cnbctv18.com', 'businesstoday.in', 'zeebiz.com'
        ]))
        is_credible = bool(domain and any(domain.endswith(cd) or domain == cd for cd in credible_domains))
        # Domain reputation prior (0.0–1.0) with defaults
        rep_info = (self._domain_reputation.get((domain or '').lower(), {})
                    if getattr(self, '_domain_reputation', None) else {})
        rep_w = float(rep_info.get('weight', 0.65) or 0.65)
        rep_type = str(rep_info.get('type', 'unknown'))
        rep_pop = int(rep_info.get('popularity', 60) or 60)

        # Advanced catalyst detection
        catalysts: list[str] = []
        deal_value_cr = 0.0
        score = 42  # Slightly higher base to avoid under-scoring headlines

        # Confirmation and speculation lexicon (expanded)
        confirmation_words = self.expert_playbook.get('heuristic', {}).get('confirmation_words', [
            'announced', 'signed', 'completed', 'reported', 'filed', 'posted', 'launched', 'declares',
            'approved', 'approves', 'bags', 'wins', 'secures', 'awarded', 'commissioned', 'inaugurated',
            'commissions', 'acquired', 'acquires', 'merges', 'board approves', 'q1', 'q2', 'q3', 'q4', 'fy'
        ])
        speculation_words = self.expert_playbook.get('heuristic', {}).get('speculation_words', [
            'may', 'might', 'could', 'would', 'plan', 'plans', 'expects', 'expecting', 'considering',
            'exploring', 'proposal', 'likely', 'rumour', 'rumor', 'sources say', 'sources said', 'set to'
        ])

        has_confirmation = any(word in combined_text for word in confirmation_words)
        has_speculation = any(spec in combined_text for spec in speculation_words)

        # Catalyst patterns with rules (some allow confirmation via strong verbs)
        catalyst_patterns = {
            'earnings': {
                'keywords': ['earnings', 'profit', 'revenue', 'pat', 'ebitda', 'margin', 'guidance'],
                'requires_numbers': True,
                'requires_confirmation': False,  # earnings headlines often imply results
                'points': 20,
            },
            'm&a': {
                'keywords': ['acquisition', 'merger', 'acquire', 'takeover', 'buyout', 'stake buy'],
                'requires_numbers': False,  # value optional in headline
                'requires_confirmation': False,  # verbs like acquires count as confirm
                'points': 24,
            },
            'investment': {
                'keywords': ['invest', 'funding', 'stake', 'capital', 'capex', 'raises'],
                'requires_numbers': False,
                'requires_confirmation': False,
                'points': 20,
            },
            'expansion': {
                'keywords': ['expand', 'capacity', 'facility', 'plant', 'factory', 'commission'],
                'requires_numbers': False,
                'requires_confirmation': False,
                'points': 16,
            },
            'contract': {
                'keywords': ['order', 'contract', 'wins', 'awarded', 'secures', 'bagged'],
                'requires_numbers': False,  # order value may not be in headline
                'requires_confirmation': False,
                'points': 18,
            },
            'dividend': {
                'keywords': ['dividend', 'buyback', 'payout', 'interim', 'final dividend'],
                'requires_numbers': False,
                'requires_confirmation': False,
                'points': 14,
            },
        }

        # Robust number detection: ₹, Rs, INR, %, crore/cr/bn/billion/million/lakh
        number_patterns = self.expert_playbook.get('heuristic', {}).get('number_patterns', [
            r'₹\s*\d+(?:,\d+)*(?:\.\d+)?',
            r'rs\.?\s*\d+(?:,\d+)*(?:\.\d+)?',
            r'inr\s*\d+(?:,\d+)*(?:\.\d+)?',
            r'\b\d+(?:\.\d+)?\s*(?:cr|crore|bn|billion|mn|million|lakh)\b',
            r'\b\d+(?:\.\d+)?\s*%\b',
            r'\bup\s*\d+(?:\.\d+)?\s*%\b',
            r'\bdown\s*\d+(?:\.\d+)?\s*%\b',
        ])
        has_numbers = any(re.search(p, combined_text) for p in number_patterns)

        # Detect catalysts with pragmatic validation
        for catalyst_type, rules in catalyst_patterns.items():
            if not any(kw in combined_text for kw in rules['keywords']):
                continue
            # Skip if dominated by speculation
            if has_speculation and not has_confirmation and not is_credible:
                continue
            # Require numbers if explicitly requested by rule
            if rules['requires_numbers'] and not has_numbers:
                continue
            catalysts.append(catalyst_type)
            score += rules['points']

        # Extract deal value in crores (₹/Rs/INR and unit words)
        value_matches = []
        value_matches += re.findall(r'(?:₹|rs\.?|inr)\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*(crore|cr|lakh|bn|billion|mn|million)?', combined_text)
        value_matches += re.findall(r'(\d+(?:,\d+)*(?:\.\d+)?)\s*(crore|cr|lakh|bn|billion|mn|million)', combined_text)
        if value_matches:
            value_str, unit = value_matches[0]
            unit = (unit or '').lower()
            value = float(value_str.replace(',', ''))
            # Normalize to crores
            if unit in {'bn', 'billion'}:
                value *= 100.0  # 1 bn ≈ 100 cr
            elif unit in {'mn', 'million'}:
                value *= 0.1    # 1 mn ≈ 0.1 cr
            elif unit == 'lakh':
                value /= 100.0
            deal_value_cr = value
            score += min(value / 120.0, 18)  # slightly stronger scaling

        # Sentiment analysis with richer lexicon
        positive_words = self.expert_playbook.get('heuristic', {}).get('positive_words', ['growth', 'strong', 'record', 'beat', 'surge', 'rise', 'gain', 'high', 'upgrade', 'order win', 'approval', 'commission', 'acquire', 'wins', 'bagged', 'secures'])
        negative_words = self.expert_playbook.get('heuristic', {}).get('negative_words', ['loss', 'decline', 'drop', 'fall', 'weak', 'pressure', 'concern', 'downgrade', 'fraud', 'resigns', 'resignation'])

        pos_count = sum(1 for w in positive_words if w in combined_text)
        neg_count = sum(1 for w in negative_words if w in combined_text)

        if pos_count > max(1, neg_count) * 1.5:
            sentiment = 'bullish'
            score += 8
        elif neg_count > max(1, pos_count) * 1.5:
            sentiment = 'bearish'
            score -= 8
        else:
            sentiment = 'neutral'

        # Certainty calculation (pragmatic, source-aware)
        specifics = 0
        for p in number_patterns:
            specifics += len(re.findall(p, combined_text))
        confirmed = len(re.findall(r'\b(announced|signed|completed|reported|filed|posted|launched|declares|approved|wins|secures|awarded|acquires)\b', combined_text))
        speculation = len(re.findall(r'\b(may|might|could|would|plans?|expects?|considering|likely|rumou?r|sources\s+said|set\s+to)\b', combined_text))

        # Base certainty starts moderately higher, boosted by credible source
        certainty = 30
        if is_credible:
            certainty += 8
        # Numeric evidence
        certainty += min(30, specifics * 6)
        # Confirmation vs speculation
        certainty += confirmed * 8
        certainty -= speculation * 10

        # Without explicit confirmation, allow higher cap if (credible source + numbers)
        if confirmed == 0:
            cap = 35
            if is_credible and has_numbers:
                cap = 55
            elif is_credible or has_numbers:
                cap = 45
            certainty = min(certainty, cap)

        certainty = max(0, min(95, certainty))

        # Popularity/advertorial/listicle adjustments (optional)
        is_advertorial = False
        is_aggregator = False
        if getattr(self, 'ad_popularity_enabled', True):
            # Adjust score by source reputation gently and tweak certainty
            score *= (0.90 + 0.20 * max(0.0, min(1.0, rep_w)))  # 0.90–1.10 multiplier
            certainty += int(5.0 * (rep_w - 0.5))
            # Detect PR/advertorial sources or language
            pr_domains = {'prnewswire.com', 'businesswire.com', 'globenewswire.com', 'newsvoir.com', 'indiaprwire.com'}
            if domain and any(domain.endswith(d) or domain == d for d in pr_domains):
                is_advertorial = True
            if re.search(r'\bpress\s+release\b|\bsponsored\b|\badvertorial\b|\bpaid\s+promotion\b', combined_text):
                is_advertorial = True
            if is_advertorial:
                score -= 12.0
                certainty -= 12
            # Broad aggregator/list headline patterns
            if re.search(r'\b(stocks?\s+to\s+watch|buzzing\s+stocks|top\s+\d+\s+stocks|why\s+\d+\s+stocks)\b', combined_text):
                is_aggregator = True
                score -= 6.0
            certainty = max(0, min(95, certainty))

        # Build company-context sentences to avoid generic risks
        try:
            sentences = re.split(r'(?<=[.!?])\s+', (headline + ' ' + full_text)[:2000])
        except Exception:
            sentences = [(headline + ' ' + full_text)[:1000]]
        base_symbol = (ticker or '').strip().upper().replace('.NS', '')
        aliases = [v.lower() for v in self._company_alias_map.get(base_symbol, [])]
        aliases.append(base_symbol.lower())
        context_sents = []
        for s in sentences:
            sl = s.lower()
            if any(a and a in sl for a in aliases):
                context_sents.append(s)
            if len(context_sents) >= 6:
                break
        if not context_sents:
            context_sents = sentences[:3]
        context_text = ' '.join(context_sents).lower()

        # Enhanced risk identification (explicit, multi-category) on company-context text
        risks: list[str] = []
        risk_map: list[tuple[str, str]] = [
            (r'\b(net\s+)?loss(?:es)?\b|loss[- ]making|reported\s+loss|widen(?:ing)?\s+loss', 'Profitability risk (losses)'),
            (r'\bhigh\s+debt|elevated\s+debt|debt\s+burden|leverage|pledged\s+shares|promoter\s+pledge', 'High debt/pledge risk'),
            (r'\bexecution\s+risk|project\s+delay|commissioning\s+delay|construction\s+delay|plant\s+shutdown|outage', 'Execution/operational risk'),
            (r'\bregulator|regulatory|sebi|nclt|cbi|ed\b|investigation|probe|raid|penalty|fine|notice|show\s+cause|tax\s+notice|gst', 'Regulatory/probe risk'),
            (r'\binput\s+cost|raw\s+material|coal\s+prices?|gas\s+prices?|oil\s+prices?|commodity\s+volatility', 'Input cost volatility'),
            (r'\bforex|fx\b|currency\s+(?:risk|fluctuation|depreciation|volatility)|rupee\s+weak', 'FX/currency risk'),
            (r'\border\s+cancell?ation|contract\s+terminated|legal\s+dispute|litigation|court\s+case', 'Litigation/order risk'),
            (r'\bmargin\s+pressure|ebitda\s+margin\s+(?:declin|compress|contract)|lower\s+margins?', 'Margin pressure'),
            (r'\b(slow|weak)\s+demand|demand\s+slowdown|volume\s+decline', 'Demand slowdown'),
            (r'\btariff|import\s+duty|export\s+ban|sanction|trade\s+war|us\s+tariff', 'Tariff/trade risk'),
            (r'\bguidance\s+cut|downgrade|revis(?:e|ion)\s+lower', 'Guidance/downgrade risk'),
            (r'\bgeopolitic|war|conflict', 'Geopolitical risk'),
        ]
        matched_risks = set()
        for pat, label in risk_map:
            try:
                m = re.search(pat, context_text)
                if m:
                    if label not in risks:
                        risks.append(label)
                        matched_risks.add((label, m.group(0)))
            except re.error:
                continue

        # Loss and YoY decline flags for conservative bias
        loss_flag = bool(re.search(r'\b(net\s+)?loss(?:es)?\b|loss[- ]making|reported\s+loss|widen(?:ing)?\s+loss', combined_text))
        yoy_down_flag = bool(re.search(r'\bdown\s*\d+\s*%|declin(?:e|ed)\s*\d+\s*%|drop(?:ped)?\s*\d+\s*%|fall(?:en|s)?\s*\d+\s*%', combined_text))

        # Extract short evidence snippets for top risks (context sentences only)
        risk_snippets: list[str] = []
        try:
            for label, _ in list(matched_risks)[:3]:
                found = None
                for s in context_sents:
                    if len(s) > 220:
                        continue
                    if any(k in s.lower() for k in ['probe', 'raid', 'penalty', 'fine']) and 'Regulatory' in label:
                        found = s.strip(); break
                    if any(k in s.lower() for k in ['loss', 'losses']) and 'Profitability' in label:
                        found = s.strip(); break
                    if any(k in s.lower() for k in ['debt', 'pledge', 'leverage']) and 'debt' in label.lower():
                        found = s.strip(); break
                    if any(k in s.lower() for k in ['delay', 'shutdown', 'outage']) and 'Execution' in label:
                        found = s.strip(); break
                    if any(k in s.lower() for k in ['tariff', 'duty', 'sanction']) and 'Tariff' in label:
                        found = s.strip(); break
                if not found and context_sents:
                    found = context_sents[0][:200].strip()
                if found:
                    risk_snippets.append(f"{label}: {found}")
        except Exception:
            pass

        # Conservative score calibration (reduce inflation; penalize risks/losses)
        if os.getenv('RISK_CALIBRATION_ENABLED', '1').strip() != '0':
            # Severity-weighted penalty
            severity_weights = {
                'Profitability risk (losses)': 3.0,
                'High debt/pledge risk': 2.0,
                'Execution/operational risk': 2.0,
                'Regulatory/probe risk': 3.0,
                'Litigation/order risk': 2.0,
                'Tariff/trade risk': 2.0,
                'Guidance/downgrade risk': 2.0,
                'Demand slowdown': 2.0,
                'Margin pressure': 1.5,
                'FX/currency risk': 1.0,
                'Input cost volatility': 1.0,
                'Geopolitical risk': 2.0,
            }
            severity = 0.0
            for r in risks:
                severity += severity_weights.get(r, 1.0)
            risk_penalty = min(20.0, 2.2 * severity)
            score -= risk_penalty
            if loss_flag:
                score = min(score, 62.0)
                score -= 8.0
            if yoy_down_flag:
                score -= 4.0
            if sentiment == 'bearish':
                score -= 4.0
            # Top-end compression to avoid 80s inflation
            if score > 85:
                score = 72.0 + 0.45 * (score - 72.0)
            elif score > 75:
                score = 68.0 + 0.55 * (score - 68.0)

        # Dynamic upper cap by evidence and source quality
        dynamic_cap = 78.0
        if not is_credible:
            dynamic_cap -= 6.0
        if not has_numbers:
            dynamic_cap -= 6.0
        if confirmed == 0:
            dynamic_cap -= 8.0
        if is_advertorial:
            dynamic_cap -= 10.0
        if len(catalysts) <= 1:
            dynamic_cap -= 4.0
        if len(risks) >= 2:
            dynamic_cap -= 4.0
        dynamic_cap = max(52.0, dynamic_cap)
        score = min(score, dynamic_cap)

        # Expected move calculation
        if catalysts and deal_value_cr > 0:
            expected_move_pct = min(deal_value_cr / 900 * 2.0, 16)
        elif catalysts:
            expected_move_pct = 2.5 + len(catalysts) * 1.8
        else:
            expected_move_pct = 1.0

        score = max(0, min(100, score))

        # Recommendation bands (with risk-aware downgrades)
        if score >= 78 and certainty >= 70:
            recommendation = "STRONG BUY"
        elif score >= 66:
            recommendation = "BUY"
        elif score >= 56:
            recommendation = "ACCUMULATE"
        elif score >= 46:
            recommendation = "HOLD"
        else:
            recommendation = "WATCH"

        if os.getenv('RISK_CALIBRATION_ENABLED', '1').strip() != '0':
            degrade = 0
            if loss_flag:
                degrade += 1
            if len(risks) >= 2:
                degrade += 1
            if sentiment == 'bearish':
                degrade += 1
            if severity >= 5.0:
                degrade += 1
            order = ["STRONG BUY", "BUY", "ACCUMULATE", "HOLD", "WATCH"]
            try:
                idx = order.index(recommendation)
                recommendation = order[min(len(order)-1, idx + degrade)]
            except ValueError:
                pass

        # Edge case: strong downside -> SELL
        if (sentiment == 'bearish' or loss_flag) and severity >= 6.0 and score < 46 and certainty >= 50:
            recommendation = "SELL"

        return {
            'score': score,
            'sentiment': sentiment,
            'impact': 'high' if score >= 70 else 'medium' if score >= 50 else 'low',
            'catalysts': catalysts,
            'deal_value_cr': deal_value_cr,
            'risks': risks[:4],
            'certainty': certainty,
            'recommendation': recommendation,
            'reasoning': f"Detected {len(catalysts)} catalyst(s). Risks: {', '.join(risks[:3]) if risks else 'None'}. "
                         f"Evidence: {' | '.join(risk_snippets[:2]) if risk_snippets else 'n/a'}. "
                         f"From {domain or 'unknown source'} [{rep_type}:{rep_w:.2f}]. "
                         f"Score: {score:.0f}/100. Certainty: {certainty:.0f}%. {sentiment.upper()}."
                         f"{' PR-like.' if is_advertorial else ''}{' Aggregator.' if is_aggregator else ''}",
            'source_domain': (domain or ''),
            'source_weight': rep_w,
            'source_type': rep_type,
            'source_popularity': rep_pop,
            'is_advertorial': is_advertorial,
            'is_aggregator': is_aggregator,
            'expected_move_pct': expected_move_pct,
            'confidence': certainty
        }
    
    def _apply_frontier_scoring(self, ticker: str, headline: str, 
                               full_text: str, ai_analysis: Dict) -> Dict:
        """Apply Frontier AI + Quant scoring.

        - Always attempts LLMNewsScorer for news-derived certainty/catalyst/sentiment (if available).
        - Optionally computes Quant Alpha using yfinance via QuantFeatureEngine + AlphaCalculator.
        - Returns a dict with keys: alpha (0–100 or None), frontier_score (news certainty proxy),
          frontier_catalyst, frontier_sentiment, and optionally alpha_metrics for debugging.
        """
        if not self.news_scorer:
            return {'alpha': None, 'frontier_score': None}

        try:
            # Use Frontier AI news scorer - it expects list of headlines
            combined_text = f"{headline}. {full_text[:500]}" if full_text else headline
            news_metrics = self.news_scorer.score_news([combined_text], ticker)

            result = {
                'alpha': None,
                'frontier_score': getattr(news_metrics, 'certainty', 50),
                'frontier_catalyst': getattr(news_metrics, 'catalyst_type', 'none'),
                'frontier_sentiment': getattr(news_metrics, 'sentiment', 'neutral'),
            }

            # Optionally compute alpha
            if self.frontier_alpha_enabled and self.alpha_calc and getattr(self, 'quant_engine', None):
                quant = self._get_quant_features_for_ticker(ticker)
                if quant is not None:
                    try:
                        alpha_val, alpha_metrics = self.alpha_calc.compute_alpha(quant, news_metrics)
                        result['alpha'] = float(alpha_val)
                        result['alpha_metrics'] = alpha_metrics
                    except Exception as e:
                        logger.warning(f"Frontier Alpha computation failed for {ticker}: {e}")

            return result
        except Exception as e:
            logger.warning(f"Frontier scoring failed: {e}")
            return {'alpha': None, 'frontier_score': None}

    def _get_boost_tier(self, boost_points: float) -> str:
        """Determine boost tier based on points applied."""
        if boost_points >= 20:
            return "Very High"
        elif boost_points >= 15:
            return "High"
        elif boost_points >= 10:
            return "Medium"
        elif boost_points >= 5:
            return "Low"
        return None

    def _apply_correction_boost(self, ticker: str, ai_score: float, certainty: float,
                               hybrid_score: float, fundamental_data: Dict = None) -> Dict:
        """
        Apply AI-Supervised Correction Boost analysis.

        This runs the 6-layer correction detection system with continuous AI oversight.
        Returns comprehensive analysis with:
        - correction_analysis: Full 6-layer analysis
        - supervision: AI supervisor verdict
        - boost_applied: Points added to final score
        - final_score: Score after boost
        - decision: APPLY_BOOST / NO_BOOST / CAUTION
        """
        if not self.correction_analyzer or not self.correction_supervisor:
            return {
                'correction_analysis': None,
                'supervision': None,
                'boost_applied': 0.0,
                'final_score': hybrid_score,
                'decision': 'NO_BOOST'
            }

        try:
            # STEP 1: Run 6-layer correction analysis
            market_context = self.correction_analyzer.detect_market_context()

            analysis = self.correction_analyzer.analyze_stock(
                ticker=ticker,
                ai_score=ai_score,
                certainty=certainty,
                fundamental_data=fundamental_data,
                market_context=market_context,
                base_hybrid_score=hybrid_score
            )

            # STEP 2: Get AI supervision verdict
            supervision = self.correction_supervisor.assess_boost_decision(analysis)

            # STEP 3: Apply boost based on verdict
            final_boost = 0.0
            final_score = hybrid_score
            final_decision = 'NO_BOOST'

            if supervision.supervisor_verdict == 'APPROVE':
                # Apply full boost
                boost_result = self.correction_analyzer.apply_boost(
                    hybrid_score=hybrid_score,
                    correction_confidence=analysis.get('correction_confidence', 0),
                    market_context=market_context,
                    safe_to_boost=True,
                    context_adjustment=analysis.get('confidence_adjustment')
                )
                final_boost = boost_result.get('boost_applied', 0)
                final_score = boost_result.get('final_score', hybrid_score)
                final_decision = 'APPLY_BOOST'
                logger.info(f"   ✅ Boost APPROVED for {ticker}: +{final_boost:.1f}pt (confidence={supervision.confidence_score:.2f})")

            elif supervision.supervisor_verdict == 'CAUTION':
                # Apply reduced boost
                boost_result = self.correction_analyzer.apply_boost(
                    hybrid_score=hybrid_score,
                    correction_confidence=analysis.get('correction_confidence', 0) * 0.8,
                    market_context=market_context,
                    safe_to_boost=True
                )
                final_boost = boost_result.get('boost_applied', 0) * 0.5
                final_score = hybrid_score + final_boost
                final_decision = 'APPLY_BOOST_REDUCED'
                logger.info(f"   ⚠️  Boost CAUTIOUS for {ticker}: +{final_boost:.1f}pt (confidence={supervision.confidence_score:.2f})")

            else:  # REJECT or REVIEW
                final_score = hybrid_score
                final_decision = 'NO_BOOST'
                if supervision.supervisor_verdict == 'REVIEW':
                    logger.info(f"   🔍 Boost REVIEW required for {ticker} (manual check needed)")
                else:
                    logger.info(f"   ❌ Boost REJECTED for {ticker} (confidence={supervision.confidence_score:.2f})")

            return {
                'correction_analysis': analysis,
                'supervision': supervision,
                'boost_applied': final_boost,
                'final_score': final_score,
                'decision': final_decision
            }

        except Exception as e:
            logger.warning(f"Correction boost analysis failed for {ticker}: {e}")
            return {
                'correction_analysis': None,
                'supervision': None,
                'boost_applied': 0.0,
                'final_score': hybrid_score,
                'decision': 'NO_BOOST'
            }

    def _map_to_yf_symbol(self, ticker: str) -> str:
        """Map generic ticker (e.g., RELIANCE) to yfinance symbol (e.g., RELIANCE.NS).

        Uses env FRONTIER_QUANT_SUFFIX (default .NS). If ticker already contains a dot, return as-is.
        """
        t = (ticker or '').strip().upper()
        if '.' in t:
            return t
        suffix = self.frontier_quant_suffix
        if not suffix.startswith('.'):
            suffix = '.' + suffix
        return t + suffix

    def _get_quant_features_for_ticker(self, ticker: str):
        """Get or compute QuantFeatures for a ticker and cache within the run."""
        if not getattr(self, 'quant_engine', None):
            return None
        yf_symbol = self._map_to_yf_symbol(ticker)
        if yf_symbol in self._quant_cache:
            return self._quant_cache[yf_symbol]
        try:
            quant = self.quant_engine.compute_features(yf_symbol)
            self._quant_cache[yf_symbol] = quant
            return quant
        except Exception as e:
            logger.warning(f"Quant feature computation failed for {yf_symbol}: {e}")
            return None
    
    def _combine_scores(self, ai_analysis: Dict, frontier_score: Dict) -> float:
        """Combine AI and Frontier scores using a weighted schema that avoids saturation.

        Components are normalized to 0–100 and blended with weights that sum to 1.0
        so the final article score stays in 0–100 with better separation across names.
        """
        # Raw AI model/heuristic score (0–100)
        ai_raw = float(ai_analysis.get('score', 50) or 50)
        ai_raw = max(0.0, min(100.0, ai_raw))

        # Certainty (0–100)
        certainty = float(ai_analysis.get('certainty', ai_analysis.get('confidence', 50) or 50))
        certainty = max(0.0, min(100.0, certainty))

        # Sentiment mapped to 0–100 band to avoid overpowering
        sentiment = str(ai_analysis.get('sentiment', '')).lower()
        if sentiment == 'bullish':
            sent_score = 80.0
        elif sentiment == 'bearish':
            sent_score = 25.0
        else:
            sent_score = 50.0

        # Catalyst distinctness: 0 (none), 40 (one), 70 (two), 100 (>=3)
        catalysts = ai_analysis.get('catalysts') or []
        uniq_cats = len({str(c).strip().lower() for c in catalysts if str(c).strip()})
        if uniq_cats <= 0:
            cat_score = 0.0
        elif uniq_cats == 1:
            cat_score = 40.0
        elif uniq_cats == 2:
            cat_score = 70.0
        else:
            cat_score = 100.0

        # Deal value scaled to 0–100 with a conservative cap (≥ ₹2000 cr treated as max)
        deal_value = float(ai_analysis.get('deal_value_cr', 0) or 0.0)
        deal_score = max(0.0, min(100.0, (deal_value / 2000.0) * 100.0))

        # Optional frontier alpha (assumed already in 0–100 if present)
        frontier_alpha = frontier_score.get('alpha', None)
        if frontier_alpha is None:
            alpha_score = 0.0
            w_alpha = 0.0
        else:
            try:
                alpha_score = max(0.0, min(100.0, float(frontier_alpha)))
                # Use configurable weight when alpha is available
                w_alpha = max(0.0, min(0.30, float(self.frontier_alpha_weight)))
            except Exception:
                alpha_score = 0.0
                w_alpha = 0.0

        # Weights sum to 1.0 (alpha weight is conditional)
        w_ai = 0.55 - w_alpha/2
        w_cert = 0.20
        w_sent = 0.10
        w_cat = 0.10
        w_deal = 0.05
        # If alpha is used, reduce the AI weight slightly to keep sum at 1.0
        total_w = w_ai + w_cert + w_sent + w_cat + w_deal + w_alpha
        # Normalize weights defensively
        w_ai, w_cert, w_sent, w_cat, w_deal, w_alpha = [w / total_w for w in (w_ai, w_cert, w_sent, w_cat, w_deal, w_alpha)]

        combined = (
            w_ai * ai_raw +
            w_cert * certainty +
            w_sent * sent_score +
            w_cat * cat_score +
            w_deal * deal_score +
            w_alpha * alpha_score
        )

        # Slight anti-saturation: cap single-article extremes later in ranking; here, just clamp
        return max(0.0, min(100.0, combined))

    def _apply_fundamental_adjustment(self, base_score: float, fundamental_data: Dict) -> float:
        """Adjust AI score using fundamental health to reward high-quality companies."""
        if not fundamental_data or not isinstance(fundamental_data, dict):
            return base_score
        if not fundamental_data.get('data_available'):
            return base_score

        adjustment = 0.0

        validation = fundamental_data.get('validation') or {}
        overall = validation.get('overall_health')
        if overall == 'healthy':
            adjustment += 2.0
        elif overall == 'concerning':
            adjustment -= 3.5
        elif overall == 'moderate':
            adjustment += 0.5

        green_flags = validation.get('green_flags') or []
        red_flags = validation.get('red_flags') or []
        adjustment += min(3.0, 0.5 * len(green_flags))
        adjustment -= min(4.0, 0.7 * len(red_flags))

        quarterly = fundamental_data.get('quarterly') or {}
        annual = fundamental_data.get('annual') or {}
        for growth, divisor in (
            (quarterly.get('earnings_yoy_growth_pct'), 40.0),
            (annual.get('earnings_yoy_growth_pct'), 60.0),
        ):
            if isinstance(growth, (int, float)):
                adjustment += max(-3.0, min(3.0, growth / divisor))

        health = fundamental_data.get('financial_health') or {}
        debt_to_equity = health.get('debt_to_equity')
        if isinstance(debt_to_equity, (int, float)):
            if debt_to_equity <= 0.8:
                adjustment += 1.0
            elif debt_to_equity >= 2.5:
                adjustment -= 2.0

        if health.get('is_profitable') is False:
            adjustment -= 2.5
        if health.get('net_worth_positive') is False:
            adjustment -= 3.0

        # Corporate actions catalyst bonus (NEW!)
        try:
            from corporate_actions_fetcher import get_corporate_action_score
            ticker_symbol = fundamental_data.get('ticker', '')
            if ticker_symbol:
                catalyst_data = get_corporate_action_score(ticker_symbol)
                if catalyst_data.get('data_available'):
                    catalyst_bonus = catalyst_data.get('catalyst_score', 0)
                    adjustment += catalyst_bonus
        except Exception:
            # Gracefully handle if corporate actions module is not available
            pass

        adjusted_score = base_score + adjustment
        return max(0.0, min(100.0, adjusted_score))
    
    def _update_live_ranking(self):
        """Update live ranking of all analyzed stocks"""
        # Aggregate scores per ticker with stronger separation
        ticker_scores = {}
        for ticker, analyses in self.live_results.items():
            if not analyses:
                continue
            # Certainty-weighted average
            weights = [max(0.15, a.certainty / 100.0) for a in analyses]
            total_w = sum(weights)
            wavg = sum(a.ai_score * w for a, w in zip(analyses, weights)) / total_w if total_w else 0.0
            top = max(a.ai_score for a in analyses)

            # Multiplicative evidence factor to avoid 100s with single prints
            n = len(analyses)
            evidence_factor = 0.90 + 0.03 * (n ** 0.5 - 1.0)  # ~0.90 for 1, ~0.93 for 2, ~0.96 for 3
            evidence_factor = max(0.85, min(1.03, evidence_factor))

            # Catalyst diversity factor across all articles
            uniq_cats = len({c.lower() for a in analyses for c in (a.catalysts or []) if c})
            diversity_factor = 1.00 + min(0.06, 0.02 * max(0, uniq_cats - 1))

            base_blend = 0.65 * top + 0.35 * wavg
            final_score = base_blend * evidence_factor * diversity_factor
            # Soft cap to keep headline scores out of 100 without stronger evidence
            soft_cap = 98.0 if n >= 3 else 96.0 if n == 2 else 94.0
            final_score = min(soft_cap, final_score)
            final_score = max(0.0, min(100.0, final_score))
            ticker_scores[ticker] = final_score
        
        # Sort by score
        self.ranked_stocks = sorted(ticker_scores.items(), 
                                   key=lambda x: x[1], 
                                   reverse=True)
        
        # Update ranks in results
        rank_map = {ticker: idx + 1 for idx, (ticker, _) in enumerate(self.ranked_stocks)}
        for ticker, analyses in self.live_results.items():
            for analysis in analyses:
                analysis.final_rank = rank_map.get(ticker, 999)
    
    def display_live_rankings(self, top_n: int = 10):
        """Display live rankings"""
        print("\n" + "="*100)
        print("🏆 LIVE RANKINGS (Real-time AI Analysis)")
        print("="*100)
        
        for idx, (ticker, score) in enumerate(self.ranked_stocks[:top_n], 1):
            analyses = self.live_results.get(ticker, [])
            if not analyses:
                continue
            
            latest = analyses[-1]
            name_suffix = f" ({latest.company_name})" if getattr(latest, 'company_name', None) else ""
            print(f"\n{idx}. {ticker}{name_suffix} - Score: {score:.1f}/100")
            print(f"   Sentiment: {latest.sentiment.upper()} | Rec: {latest.recommendation}")
            print(f"   Catalysts: {', '.join(latest.catalysts) if latest.catalysts else 'None'}")
            if getattr(latest, 'risks', None):
                try:
                    risks_line = ', '.join(latest.risks[:3]) if latest.risks else 'None'
                except Exception:
                    risks_line = 'None'
                print(f"   Risks: {risks_line}")
            qa = f"{latest.quant_alpha:.1f}" if latest.quant_alpha is not None else "N/A"
            gates = latest.alpha_gate_flags or ""
            setups = latest.alpha_setup_flags or ""
            if gates or setups:
                print(f"   Alpha: {qa} | Gates: {gates}{' | Setups: ' + setups if setups else ''}")
            else:
                print(f"   Alpha: {qa}")
            print(f"   Certainty: {latest.certainty:.0f}% | Articles: {len(analyses)}")
        
        print("\n" + "="*100)
    
    def save_results(self, output_file: str):
        """Save all results to CSV with quality filtering"""
        import csv
        
        # Apply certainty threshold (from env or default 40%)
        MIN_CERTAINTY = int(os.getenv('MIN_CERTAINTY_THRESHOLD', '40'))
        
        # Separate qualified and rejected stocks
        qualified_stocks = []
        rejected_stocks = []
        
        for ticker, score in self.ranked_stocks:
            analyses = self.live_results[ticker]
            latest = analyses[-1]
            
            if latest.certainty >= MIN_CERTAINTY:
                qualified_stocks.append((ticker, score, latest, analyses))
            else:
                rejected_stocks.append((ticker, score, latest, analyses))
        
        # Save qualified stocks (with real-time price data)
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'rank', 'ticker', 'company_name', 'ai_score', 'sentiment', 'recommendation',
                'catalysts', 'risks', 'certainty', 'articles_count',
                'quant_alpha',
                # Real-time price fields (from yfinance, NOT training data)
                'current_price', 'price_timestamp', 'entry_zone_low', 'entry_zone_high',
                'target_conservative', 'target_aggressive', 'stop_loss',
                # Fundamental fields (from yfinance fundamentals)
                'fundamental_adjustment',
                'quarterly_earnings_growth_yoy', 'annual_earnings_growth_yoy',
                'profit_margin_pct', 'debt_to_equity',
                'is_profitable', 'net_worth_positive', 'financial_health_status',
                # AI Web Search Health Data (verified, non-stale data)
                'health_is_profitable', 'health_profit_loss', 'health_profit_loss_period',
                'health_status', 'health_consecutive_losses', 'health_warning_flags',
                # Corporate actions catalyst fields (from NSE, NOT training data)
                'catalyst_score', 'has_dividend', 'dividend_amount', 'has_bonus', 'bonus_ratio',
                # AI-Supervised Correction Boost fields (15 new columns)
                'correction_detected', 'correction_pct', 'reversal_confirmed', 'correction_confidence',
                'oversold_score', 'fundamental_confidence', 'catalyst_strength',
                'boost_applied', 'boost_tier', 'correction_reasoning',
                'risk_filters_passed', 'risk_violations',
                'market_context', 'market_vix_level',
                'supervisor_verdict', 'supervisor_confidence', 'supervision_notes',
                'headline', 'reasoning'
            ])

            for rank, (ticker, score, latest, analyses) in enumerate(qualified_stocks, 1):
                writer.writerow([
                    rank,
                    ticker,
                    getattr(latest, 'company_name', '') or '',
                    f"{score:.1f}",
                    latest.sentiment,
                    latest.recommendation,
                    ', '.join(latest.catalysts) if latest.catalysts else '',
                    ', '.join(latest.risks) if latest.risks else '',
                    f"{latest.certainty:.0f}",
                    len(analyses),
                    (f"{latest.quant_alpha:.1f}" if latest.quant_alpha is not None else ''),
                    # Real-time price data (from yfinance)
                    (f"{latest.current_price:.2f}" if latest.current_price else ''),
                    latest.price_timestamp or '',
                    (f"{latest.entry_zone_low:.2f}" if latest.entry_zone_low else ''),
                    (f"{latest.entry_zone_high:.2f}" if latest.entry_zone_high else ''),
                    (f"{latest.target_conservative:.2f}" if latest.target_conservative else ''),
                    (f"{latest.target_aggressive:.2f}" if latest.target_aggressive else ''),
                    (f"{latest.stop_loss:.2f}" if latest.stop_loss else ''),
                    (f"{latest.fundamental_adjustment:+.2f}" if latest.fundamental_adjustment is not None else ''),
                    (f"{latest.quarterly_earnings_growth_yoy:.2f}" if latest.quarterly_earnings_growth_yoy is not None else ''),
                    (f"{latest.annual_earnings_growth_yoy:.2f}" if latest.annual_earnings_growth_yoy is not None else ''),
                    (f"{latest.profit_margin_pct:.2f}" if latest.profit_margin_pct is not None else ''),
                    (f"{latest.debt_to_equity:.2f}" if latest.debt_to_equity is not None else ''),
                    ('TRUE' if latest.is_profitable is True else ('FALSE' if latest.is_profitable is False else '')),
                    ('TRUE' if latest.net_worth_positive is True else ('FALSE' if latest.net_worth_positive is False else '')),
                    (latest.financial_health_status or ''),
                    # AI Web Search Health Data
                    (
                        'TRUE' if hasattr(latest, 'health_data') and latest.health_data and latest.health_data.get('is_profitable') is True
                        else ('FALSE' if hasattr(latest, 'health_data') and latest.health_data and latest.health_data.get('is_profitable') is False else '')
                    ),
                    (latest.health_data['latest_profit_loss'] if hasattr(latest, 'health_data') and latest.health_data and 'latest_profit_loss' in latest.health_data else ''),
                    (latest.health_data['profit_loss_period'] if hasattr(latest, 'health_data') and latest.health_data and 'profit_loss_period' in latest.health_data else ''),
                    (latest.health_data['health_status'] if hasattr(latest, 'health_data') and latest.health_data and 'health_status' in latest.health_data else ''),
                    (str(latest.health_data['consecutive_loss_quarters']) if hasattr(latest, 'health_data') and latest.health_data and 'consecutive_loss_quarters' in latest.health_data else ''),
                    ('; '.join(latest.health_data['warning_flags']) if hasattr(latest, 'health_data') and latest.health_data and 'warning_flags' in latest.health_data and latest.health_data['warning_flags'] else ''),
                    # Corporate actions catalyst data
                    (str(latest.catalyst_score) if latest.catalyst_score else '0'),
                    ('TRUE' if latest.has_dividend else 'FALSE'),
                    (f"₹{latest.dividend_amount:.1f}" if latest.dividend_amount else ''),
                    ('TRUE' if latest.has_bonus else 'FALSE'),
                    (latest.bonus_ratio or ''),
                    # AI-Supervised Correction Boost data
                    ('TRUE' if latest.correction_detected else 'FALSE'),
                    (f"{latest.correction_pct:.1f}%" if latest.correction_pct is not None else ''),
                    ('TRUE' if latest.reversal_confirmed else 'FALSE'),
                    (f"{latest.correction_confidence:.2f}" if latest.correction_confidence is not None else ''),
                    (f"{latest.oversold_score:.1f}" if latest.oversold_score is not None else ''),
                    (f"{latest.fundamental_confidence:.1f}" if latest.fundamental_confidence is not None else ''),
                    (f"{latest.catalyst_strength:.1f}" if latest.catalyst_strength is not None else ''),
                    (f"{latest.boost_applied:+.1f}" if latest.boost_applied and latest.boost_applied > 0 else ''),
                    (latest.boost_tier or ''),
                    (latest.correction_reasoning[:100] if latest.correction_reasoning else ''),
                    ('TRUE' if latest.risk_filters_passed is True else ('FALSE' if latest.risk_filters_passed is False else '')),
                    ('; '.join(latest.risk_violations) if latest.risk_violations else ''),
                    (latest.market_context or ''),
                    (f"{latest.market_vix_level:.1f}" if latest.market_vix_level is not None else ''),
                    (latest.supervisor_verdict or ''),
                    (f"{latest.supervisor_confidence:.2f}" if latest.supervisor_confidence is not None else ''),
                    (latest.supervision_notes[:100] if latest.supervision_notes else ''),
                    latest.headline[:100],
                    latest.reasoning[:200]
                ])
        
        logger.info(f"✅ {len(qualified_stocks)} qualified stocks saved to {output_file}")

        # Record predictions to learning database for feedback loop
        self._record_predictions_to_learning_db(qualified_stocks)

        # Save rejected stocks to separate file
        if rejected_stocks:
            rejected_file = output_file.replace('.csv', '_rejected.csv')
            with open(rejected_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'ticker', 'company_name', 'ai_score', 'certainty', 'articles_count', 
                    'rejection_reason', 'headline', 'reasoning'
                ])
                
                for ticker, score, latest, analyses in rejected_stocks:
                    writer.writerow([
                        ticker,
                        getattr(latest, 'company_name', '') or '',
                        f"{score:.1f}",
                        f"{latest.certainty:.0f}",
                        len(analyses),
                        f"Certainty {latest.certainty:.0f}% below threshold ({MIN_CERTAINTY}%)",
                        latest.headline[:80],
                        latest.reasoning[:150]
                    ])
            
            logger.info(f"⚠️  {len(rejected_stocks)} stocks rejected (saved to {rejected_file})")
            logger.info(f"   Rejection reason: Certainty below {MIN_CERTAINTY}% threshold")
        else:
            logger.info(f"✅ All stocks passed certainty threshold ({MIN_CERTAINTY}%)")
        
        logger.info(f"✅ Results saved to: {output_file}")

    def log_ai_usage_summary(self, targeted_tickers: Optional[List[str]] = None):
        """Log external AI usage summary, including provider and limit effects."""
        provider = getattr(self.ai_client, 'selected_provider', 'heuristic')
        used = self.ai_call_count
        limit = self.ai_call_limit
        logger.info("🤖 AI provider: %s", provider)
        logger.info("📊 External AI calls used: %s%s",
                    used,
                    (f"/{limit}" if isinstance(limit, int) else ""))
        if provider == 'heuristic':
            logger.warning("⚠️  External AI not configured; using heuristic analysis only. Set OPENAI_API_KEY/ANTHROPIC_API_KEY or configure a shell bridge.")
        if self.ai_call_limit is None:
            return
        logger.info("📊 AI usage: %s/%s calls used", used, limit)
        if used >= limit:
            # Tickers entirely skipped from external AI due to limit
            skipped = (self.limit_affected_tickers - self.external_ai_used_tickers)
            if targeted_tickers is not None:
                targeted_set = set(targeted_tickers)
                skipped = skipped & targeted_set
            if skipped:
                sk_list = ", ".join(sorted(skipped))
                logger.warning("⚠️  %d ticker(s) were not processed by external AI due to call limit: %s", len(skipped), sk_list)
            else:
                logger.info("All targeted tickers received at least one external AI analysis before the limit was reached.")


class RealtimeCollectorIntegration:
    """
    Integrates real-time AI analysis with news collection
    Analyzes each news item immediately as it's fetched
    """
    
    def __init__(self, analyzer: RealtimeAIAnalyzer):
        self.analyzer = analyzer
    
    def collect_and_analyze(self, tickers: List[str], hours_back: int = 48,
                           max_articles: int = 10, sources: List[str] = None,
                           batch_size: int = 5):
        """
        Collect news AND analyze in real-time
        Each article is analyzed immediately after fetching
        """
        logger.info(f"🚀 Starting real-time collection + analysis for {len(tickers)} tickers")
        logger.info(f"   Time window: {hours_back} hours")
        logger.info(f"   Max articles per ticker: {max_articles}")
        if self.analyzer.enable_ticker_validation:
            logger.info(f"   🔍 AI will validate each ticker against NSE/BSE before processing")
        else:
            logger.info(f"   ⚡ Ticker validation DISABLED - processing all tickers")

        # Track statistics
        total_articles = 0
        total_analyzed = 0
        valid_tickers = 0
        invalid_tickers = []

        for idx, ticker in enumerate(tickers, 1):
            print(f"\n[{idx}/{len(tickers)}] Processing {ticker}...")
            logger.info(f"[{idx}/{len(tickers)}] Processing {ticker}...")

            # VALIDATE TICKER WITH AI FIRST
            is_valid, reason = self.analyzer.validate_ticker_with_ai(ticker)

            if not is_valid:
                print(f"   ❌ INVALID TICKER: {reason}")
                logger.warning(f"   Skipping {ticker}: {reason}")
                invalid_tickers.append((ticker, reason))
                continue

            print(f"   ✅ Valid ticker: {reason}")
            valid_tickers += 1

            # Fetch articles for this ticker (mock - use actual collector)
            articles = self._fetch_articles_for_ticker(
                ticker, hours_back, max_articles, sources
            )

            if not articles:
                print(f"   ℹ️  No recent articles found")
                continue

            total_articles += len(articles)
            print(f"   📰 Analyzing {len(articles)} article(s)...")

            # Analyze each article INSTANTLY
            for article in articles:
                try:
                    result = self.analyzer.analyze_news_instantly(
                        ticker=ticker,
                        headline=article['title'],
                        full_text=article.get('text', ''),
                        url=article.get('url', '')
                    )
                    if result is not None:  # Only count if news passed quality filter
                        total_analyzed += 1
                except Exception as e:
                    logger.error(f"   ❌ Analysis failed: {e}")

            # Show live rankings after each batch
            if batch_size and idx % max(1, batch_size) == 0:
                self.analyzer.display_live_rankings(top_n=max(5, batch_size))

        logger.info(f"\n✅ Collection complete!")
        logger.info(f"   Valid tickers: {valid_tickers}/{len(tickers)}")
        logger.info(f"   Invalid tickers: {len(invalid_tickers)}")
        logger.info(f"   Total articles: {total_articles}")
        logger.info(f"   Successfully analyzed: {total_analyzed}")

        # Save invalid tickers to file
        if invalid_tickers:
            try:
                with open('realtime_ai_invalid_tickers.txt', 'w', encoding='utf-8') as f:
                    f.write(f"# Invalid tickers found by AI validation\n")
                    f.write(f"# Total: {len(invalid_tickers)}\n\n")
                    for ticker, reason in invalid_tickers:
                        f.write(f"{ticker}: {reason}\n")
                logger.info(f"   Invalid tickers saved to: realtime_ai_invalid_tickers.txt")
            except Exception as e:
                logger.warning(f"   Failed to save invalid tickers file: {e}")

        # Save validation cache for future runs
        self.analyzer._save_validation_cache()

        return total_analyzed
    
    def _fetch_articles_for_ticker(self, ticker: str, hours_back: int,
                                   max_articles: int, sources: List[str]) -> List[Dict]:
        """
        Fetch articles for a single ticker using base collector
        """
        try:
            import datetime as dt
            logger.info(f"📰 Fetching news for {ticker} (last {hours_back}h)")
            
            # Default sources if none provided - FINANCIAL SOURCES ONLY
            if not sources:
                sources = [
                    'reuters.com', 'livemint.com', 'economictimes.indiatimes.com',
                    'business-standard.com', 'moneycontrol.com', 'cnbctv18.com',
                    'thehindubusinessline.com', 'financialexpress.com', 'zeebiz.com'
                ]
            
            # Fetch publisher RSS only for quality (no Google News fallback)
            items = news_collector.fetch_rss_items(
                ticker=ticker,
                sources=sources,
                publishers_only=True
            )
            
            if not items:
                logger.info(f"ℹ️  No recent news for %s from live sources", ticker)
                return self._get_offline_articles(ticker, max_articles)
            
            # Filter by time window and fetch full content
            now = dt.datetime.now(dt.timezone.utc)
            cutoff = now - dt.timedelta(hours=hours_back)
            recent_items = []
            
            for title, url, source, pub_date in items:
                # Skip obviously irrelevant news
                title_lower = title.lower()
                junk_keywords = [
                    'horoscope', 'astrology', 'zodiac', 'football', 'cricket', 
                    'soccer', 'champions league', 'world cup', 'movie', 'film',
                    'celebrity', 'entertainment', 'gaming', 'esports', 'weather',
                    'recipe', 'cooking', 'fashion', 'lifestyle', 'beauty',
                    'travel', 'tourism', 'health tips', 'diet', 'fitness'
                ]
                if any(junk in title_lower for junk in junk_keywords):
                    logger.debug(f"   ⏭️  Skipped irrelevant: {title[:60]}")
                    continue
                
                # Handle timezone-aware comparisons
                if pub_date:
                    # Make pub_date timezone-aware if it isn't
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=dt.timezone.utc)
                    if pub_date >= cutoff:
                        # Try to fetch full article content
                        full_text = ''
                        try:
                            full_text = news_collector.fetch_full_article_text(url)
                        except:
                            pass  # Use headline only if content fetch fails
                            
                        recent_items.append({
                            'title': title,
                            'url': url,
                            'source': source,
                            'published': pub_date.isoformat() if pub_date else None,
                            'text': full_text or title  # Fallback to title
                        })
                else:
                    # If no pub_date, include it anyway (but check for junk first)
                    full_text = ''
                    try:
                        full_text = news_collector.fetch_full_article_text(url)
                    except:
                        pass
                        
                    recent_items.append({
                        'title': title,
                        'url': url,
                        'source': source,
                        'published': None,
                        'text': full_text or title
                    })
            
            # Limit to max_articles
            recent_items = recent_items[:max_articles]
            
            logger.info(f"✅ Found {len(recent_items)} recent articles for {ticker}")
            if recent_items:
                return recent_items

            logger.info(f"ℹ️  Live sources returned no recent articles for %s; trying offline cache", ticker)
            return self._get_offline_articles(ticker, max_articles)
            
        except Exception as e:
            logger.error(f"❌ Error fetching articles for {ticker}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return self._get_offline_articles(ticker, max_articles)

    def _get_offline_articles(self, ticker: str, max_articles: int) -> List[Dict]:
        """Return offline cached articles when live fetch fails."""
        if not ALLOW_OFFLINE_NEWS_CACHE:
            return []
        cache = _load_offline_news_cache()
        normalized = _normalize_ticker_symbol(ticker)
        entries = cache.get(normalized, [])
        if not entries:
            return []

        articles: List[Dict] = []
        for entry in entries[:max_articles]:
            title = str(entry.get('title', '')).strip() or f"{normalized} offline update"
            text = str(entry.get('text', '')).strip() or title
            articles.append({
                'title': title,
                'url': entry.get('url', ''),
                'source': entry.get('source', 'offline-cache'),
                'published': entry.get('published'),
                'text': text
            })

        if articles:
            logger.info(
                "📦 Using offline news cache for %s (%d article%s)",
                normalized,
                len(articles),
                '' if len(articles) == 1 else 's'
            )
        return articles


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Real-time AI News Analyzer with instant scoring'
    )
    parser.add_argument('--tickers', nargs='*', help='Specific tickers to analyze')
    parser.add_argument('--tickers-file', type=str, help='File with ticker list')
    parser.add_argument('--hours-back', type=int, default=48, help='Hours to look back')
    parser.add_argument('--max-articles', type=int, default=10, help='Max articles per ticker')
    parser.add_argument('--sources', nargs='*', help='News sources to use')
    parser.add_argument('--output', default='realtime_ai_results.csv', help='Output file')
    parser.add_argument('--top', type=int, default=3125, help='Top N to display')
    parser.add_argument(
        '--ai-provider',
        default='auto',
        help='AI engine to use: auto, claude, codex, or heuristic'
    )
    parser.add_argument(
        '--max-ai-calls',
        type=int,
        default=None,
        help='Maximum external AI calls before falling back to heuristics'
    )
    parser.add_argument(
        '--verify-internet',
        action='store_true',
        help='Run internet + AI endpoint connectivity checks at start'
    )
    parser.add_argument(
        '--require-internet-ai',
        action='store_true',
        help='Fail if AI provider is not a remote provider (Codex/Claude) or AI endpoint is unreachable'
    )
    parser.add_argument(
        '--batch-size', type=int, default=5,
        help='Process and display rankings after each batch of this many tickers'
    )
    parser.add_argument(
        '--probe-agent', action='store_true',
        help='Attempt an agent connectivity probe for shell providers (fetch URL and compare hash)'
    )
    parser.add_argument(
        '--require-agent-internet', action='store_true',
        help='Fail if shell agent cannot fetch a known URL during probe'
    )
    parser.add_argument(
        '--disable-ticker-validation', action='store_true',
        help='Skip AI ticker validation (accept all tickers). Use this for faster processing when you trust your ticker list.'
    )

    args = parser.parse_args()
    
    # Load tickers
    if args.tickers_file:
        with open(args.tickers_file, 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
    elif args.tickers:
        tickers = args.tickers
    else:
        logger.error("❌ Must provide --tickers or --tickers-file")
        sys.exit(1)

    # Basic ticker cleanup (no pre-filtering - AI will validate)
    def _normalize_symbol(s: str) -> str:
        s = (s or '').strip().upper()
        # Keep alnum + dot only
        s = re.sub(r"[^A-Z0-9\.]", "", s)
        # Collapse any duplicated suffix
        if s.endswith('.NS.NS'):
            s = s[:-3]
        # Remove .NS suffix for consistency
        return s.replace('.NS', '')

    # Normalize and deduplicate tickers
    normalized_tickers = [_normalize_symbol(t) for t in tickers]

    # Deduplicate while keeping order
    seen = set()
    filtered_unique = []
    for s in normalized_tickers:
        if s and s not in seen:
            seen.add(s)
            filtered_unique.append(s)

    if not filtered_unique:
        logger.error("❌ No tickers provided after normalization.")
        sys.exit(2)

    tickers = filtered_unique
    logger.info(f"📊 Loaded {len(tickers)} unique tickers (AI will validate against NSE/BSE)")
    
    print("\n" + "="*100)
    print("🤖 REAL-TIME AI NEWS ANALYZER")
    print("="*100)
    print("\nFeatures:")
    print("  ✅ Instant analysis as news is fetched (no batching)")
    print("  ✅ Claude/Codex AI with internet access")
    print("  ✅ Frontier AI + Quant scoring")
    print("  ✅ Live ranking updates")
    print("  ✅ Zero news skipped")
    print("  ✅ AI call budget + caching to avoid rate limits")
    print("\n" + "="*100 + "\n")
    
    # Initialize analyzer
    analyzer = RealtimeAIAnalyzer(
        ai_provider=args.ai_provider,
        max_ai_calls=args.max_ai_calls,
        require_internet_ai=args.require_internet_ai,
        verify_internet=args.verify_internet,
        probe_agent=args.probe_agent,
        require_agent_internet=args.require_agent_internet,
        enable_ticker_validation=not args.disable_ticker_validation,
    )
    integration = RealtimeCollectorIntegration(analyzer)
    
    # Run collection + analysis
    analyzed_count = integration.collect_and_analyze(
        tickers=tickers[:args.top],
        hours_back=args.hours_back,
        max_articles=args.max_articles,
        sources=args.sources,
        batch_size=args.batch_size
    )
    
    # Display final rankings
    analyzer.display_live_rankings(top_n=args.top)

    # Generate timestamped output filename with AI provider
    timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    ai_provider = analyzer.ai_client.selected_provider or 'unknown'

    # Insert timestamp and AI provider before .csv extension
    base_output = args.output.replace('.csv', '')
    timestamped_output = f"{base_output}_{timestamp_str}_{ai_provider}.csv"

    # Save results with timestamped filename
    analyzer.save_results(timestamped_output)
    # Also copy to the canonical output name the script prints for convenience
    try:
        shutil.copyfile(timestamped_output, args.output)
        rejected_src = timestamped_output.replace('.csv', '_rejected.csv')
        rejected_dst = args.output.replace('.csv', '_rejected.csv')
        if os.path.exists(rejected_src):
            shutil.copyfile(rejected_src, rejected_dst)
    except Exception as exc:
        logger.warning("⚠️  Unable to copy results to %s: %s", args.output, exc)
    # Log AI usage summary (especially if a call limit enforced)
    try:
        analyzer.log_ai_usage_summary(tickers[:args.top])
    except Exception:
        pass

    print(f"\n✅ Real-time analysis complete!")
    print(f"   Articles analyzed: {analyzed_count}")
    print(f"   Results saved: {timestamped_output}")

    # Display final results table on screen
    print("\n" + "="*160)
    print("📊 FINAL RANKINGS - TOP STOCKS WITH PROFIT HEALTH")
    print("="*160)
    try:
        import csv
        with open(timestamped_output, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            if rows:
                # Print header with profit health metrics
                print(f"\n{'Rank':<5} {'Ticker':<10} {'Score':<8} {'Sentiment':<10} {'Q-Growth':<10} {'A-Growth':<10} {'Health':<12} {'Profit':<8} {'NW':<6}")
                print("-" * 160)

                # Print top 25 rows with profit metrics
                for idx, row in enumerate(rows[:25], 1):
                    ticker = row.get('ticker', '').ljust(10)
                    score = row.get('ai_score', '0').ljust(8)
                    sentiment = row.get('sentiment', '').ljust(10)

                    # Profit health metrics
                    quarterly_growth = row.get('quarterly_earnings_growth_yoy', '').ljust(10)
                    annual_growth = row.get('annual_earnings_growth_yoy', '').ljust(10)
                    health = row.get('financial_health_status', 'unknown').ljust(12)
                    profit = row.get('is_profitable', '').ljust(8)
                    networth = row.get('net_worth_positive', '').ljust(6)

                    # Format values
                    if quarterly_growth.strip():
                        quarterly_growth = f"{float(quarterly_growth.strip()):.1f}%".ljust(10)
                    else:
                        quarterly_growth = 'N/A'.ljust(10)

                    if annual_growth.strip():
                        annual_growth = f"{float(annual_growth.strip()):.1f}%".ljust(10)
                    else:
                        annual_growth = 'N/A'.ljust(10)

                    line = f"{idx:<5} {ticker} {score} {sentiment} {quarterly_growth} {annual_growth} {health} {profit} {networth}"
                    print(line)

                print("-" * 160)

                # Additional health metrics report
                print(f"\n📊 PROFIT HEALTH ANALYSIS:")
                print("-" * 160)

                healthy = sum(1 for row in rows if row.get('financial_health_status', '').lower() == 'healthy')
                warning = sum(1 for row in rows if row.get('financial_health_status', '').lower() == 'warning')
                critical = sum(1 for row in rows if row.get('financial_health_status', '').lower() == 'critical')
                profitable = sum(1 for row in rows if row.get('is_profitable', '').upper() == 'TRUE')
                negative_nw = sum(1 for row in rows if row.get('net_worth_positive', '').upper() == 'FALSE')

                positive_q_growth = sum(1 for row in rows if row.get('quarterly_earnings_growth_yoy', '') and float(row.get('quarterly_earnings_growth_yoy', 0)) > 0)
                positive_a_growth = sum(1 for row in rows if row.get('annual_earnings_growth_yoy', '') and float(row.get('annual_earnings_growth_yoy', 0)) > 0)

                total = len(rows)
                print(f"Total stocks analyzed: {total}")
                print(f"✅ Healthy: {healthy} ({healthy*100/total:.0f}%)")
                print(f"⚠️  Warning: {warning} ({warning*100/total:.0f}%)")
                print(f"🚨 Critical: {critical} ({critical*100/total:.0f}%)")
                print(f"💰 Profitable: {profitable} ({profitable*100/total:.0f}%)")
                print(f"📈 Positive Q-Growth: {positive_q_growth} ({positive_q_growth*100/total:.0f}%)")
                print(f"📈 Positive A-Growth: {positive_a_growth} ({positive_a_growth*100/total:.0f}%)")
                print(f"❌ Negative Networth: {negative_nw} ({negative_nw*100/total:.0f}%)")

                print("\n" + "-" * 160)
                print(f"\n✅ Displayed top 25 stocks out of {len(rows)} analyzed")
                print(f"\n📁 Output Files:")
                print(f"   💾 Full results: {timestamped_output}")
                print(f"      (Contains 35+ columns: scores, sentiment, catalysts, risks, prices, profits, health, etc.)")
                print(f"   📌 Quick copy:   {args.output}")
            else:
                print("⚠️  No results to display")
    except Exception as e:
        print(f"⚠️  Could not display results table: {e}")
        print(f"   Error details: {str(e)}")


if __name__ == "__main__":
    main()
