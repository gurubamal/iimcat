#!/usr/bin/env python3
"""
CLAUDE EXIT BRIDGE - Elite Exit Intelligence with 7 Enhancements
================================================================
Purpose-built for EXIT decisions with internet access, feedback learning,
and comprehensive risk management.

ENHANCEMENTS OVER STANDARD CLAUDE:
1. Exit-specific system prompt (not generic swing trading)
2. Internet-enhanced article fetching (5000 char full text)
3. Structured technical data injection
4. Intraday feedback calibration hints
5. Adaptive thresholds based on data coverage
6. Auto-computed stop/trail levels
7. JSONL decision logging for learning

Usage:
    export ANTHROPIC_API_KEY="sk-ant-xxxxx"
    echo "EXIT ASSESSMENT REQUEST..." | python3 claude_exit_bridge.py
"""

import sys
import json
import os
import re
import hashlib
from datetime import datetime
from typing import Dict, Optional, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import AI conversation logger for QA
try:
    from ai_conversation_logger import log_ai_conversation
except ImportError:
    def log_ai_conversation(*args, **kwargs):
        pass


# ============================================================================
# ENHANCEMENT 1: EXIT-SPECIFIC SYSTEM PROMPT
# ============================================================================

CLAUDE_EXIT_SYSTEM_PROMPT = """You are an elite portfolio manager specializing in EXIT decisions for Indian equities.

Your CORE MANDATE: Protect capital by identifying deterioration EARLY.

STRICT REAL-TIME GROUNDING:
- Base your analysis ONLY on the provided prompt content (news headline/summary and technical data). Do NOT use training data or external memory.
- PRIORITY: Use CURRENT PRICE as the anchor; FIRST compute exit levels (expected_exit_price/zone, stop_loss_price, optional reentry_price) before narrative reasoning.

EXIT DECISION FRAMEWORK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. CRITICAL EXIT SIGNALS (Immediate Action):
   • Profit warnings / guidance cuts
   • Regulatory/legal investigations
   • Debt covenant breaches
   • Major customer/contract losses
   • Management fraud/scandals
   • Support breaks with volume confirmation

2. HIGH-PRIORITY SIGNALS (Monitor → Exit):
   • Analyst downgrades (esp. tier-1 firms)
   • Margin compression trends (>2 quarters)
   • Market share losses
   • Delayed projects/capex cuts
   • Death cross (20DMA < 50DMA)

3. MODERATE SIGNALS (Watch Closely):
   • Weakening demand indicators
   • Rising competitive threats
   • RSI oversold with volume spike down
   • Sector headwinds

4. HOLD SIGNALS (Counter-indicators):
   • Temporary/one-time issues
   • News already priced in
   • Strong fundamentals intact
   • Attractive valuation + margin of safety
   • Upcoming positive catalysts

SCORING CALIBRATION (Exit-Optimized):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• exit_urgency_score 90-100: CRITICAL - regulatory/fraud/bankruptcy risk
• exit_urgency_score 75-89: SERIOUS - fundamental deterioration, broken support
• exit_urgency_score 60-74: WARNING - monitor closely, partial exit consideration
• exit_urgency_score 40-59: MINOR - thesis intact, normal volatility
• exit_urgency_score 0-39: STRONG HOLD - no material risks

TECHNICAL BREAKDOWN SCORING:
• Price < 20DMA by >5%: +15 points
• Price < 50DMA by >8%: +20 points
• Death cross: +20 points
• RSI < 30 with down momentum: +15 points
• Volume spike on down move: +10 points
• Near 52-week low (<5%): +20 points

FUNDAMENTAL RISK SCORING:
• Earnings miss: +25 points
• Debt/EBITDA ratio deterioration: +20 points
• Margin compression >200bps: +15 points
• Cash flow negative: +30 points
• Customer concentration risk: +10 points

SENTIMENT RISK SCORING:
• Tier-1 downgrade: +30 points
• Regulatory investigation: +40 points
• Management scandal: +50 points
• Sector downgrade: +15 points
• Negative earnings surprise: +25 points

CONFIDENCE CALIBRATION:
• Hard data (earnings, official announcements): 85-95%
• Tier-1 analyst reports: 75-85%
• Tier-2 sources (Moneycontrol, ET): 60-75%
• Technical-only (no news): 50-65%
• Speculation/rumors: 20-40%

RESPONSE FORMAT:
Return ONLY valid JSON with these exact keys (you may include the additional price keys listed at the end):
{
  "exit_urgency_score": <0-100>,
  "sentiment": "bearish" | "neutral" | "bullish",
  "exit_recommendation": "IMMEDIATE_EXIT" | "MONITOR" | "HOLD",
  "exit_catalysts": [<max 5 specific reasons>],
  "hold_reasons": [<counter-arguments if any>],
  "risks_of_holding": [<specific risks>],
  "technical_breakdown_score": <0-100>,
  "fundamental_risk_score": <0-100>,
  "negative_sentiment_score": <0-100>,
  "certainty": <0-100>,
  "reasoning": "<2-3 sentences: decision + key factors + recommendation>",
  "stop_loss_suggestion": <percentage below current>,
  "expected_exit_price": <number or 0 if not computable>,
  "stop_loss_price": <number or 0 if not computable>,
  "reentry_price": <number or 0 if not applicable>
}

CRITICAL RULES:
✓ Be DECISIVE - don't hedge when data is clear
✓ Consider OPPORTUNITY COST - capital has alternatives
✓ Favor ACTION over inaction when risks mount
✓ Use FULL scoring range (don't cluster at 40-60)
✓ Technical deterioration is REAL - don't dismiss charts
✓ Multiple warning signs = AMPLIFY urgency (not average)
✓ Certainty reflects DATA QUALITY, not conviction
"""


# ============================================================================
# ENHANCEMENT 2: INTERNET-ENHANCED ARTICLE FETCHING
# ============================================================================

def fetch_article_content(url: str) -> Optional[str]:
    """Fetch and extract article body (5000 char limit)"""
    try:
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; ExitAnalyzer/1.0)'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove scripts, styles, ads
        for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'header']):
            tag.decompose()

        # Extract article body (prioritize article tags)
        article_candidates = soup.find_all(
            ['article', 'div'],
            class_=re.compile(r'article|content|story|post-body', re.I)
        )

        if article_candidates:
            text = ' '.join([c.get_text(separator=' ', strip=True)
                            for c in article_candidates])
        else:
            # Fallback to main content
            main = soup.find('main') or soup.find('body')
            text = main.get_text(separator=' ', strip=True) if main else ''

        # Clean and truncate
        text = re.sub(r'\s+', ' ', text).strip()
        text = text[:5000] if len(text) > 5000 else text

        logger.info(f"✅ Fetched {len(text)} chars from {url[:50]}...")
        return text

    except Exception as e:
        logger.warning(f"⚠️  Article fetch failed for {url}: {e}")
        return None


def extract_urls_from_prompt(prompt: str) -> List[str]:
    """Extract article URLs from prompt"""
    patterns = [
        r'\*\*URL\*\*:\s*(https?://[^\s\n]+)',
        r'(?:URL|url|link|article):\s*(https?://[^\s\n]+)',
        r'(https?://(?:www\.)?(?:moneycontrol|economictimes|livemint|reuters|bloomberg)[^\s\n]+)'
    ]

    urls = []
    for pattern in patterns:
        urls.extend(re.findall(pattern, prompt))

    return list(set(urls))  # Deduplicate


# ============================================================================
# ENHANCEMENT 3: STRUCTURED TECHNICAL DATA EXTRACTION
# ============================================================================

def extract_technical_data(prompt: str) -> Dict:
    """Extract structured technical indicators from prompt"""

    tech_data = {}

    # Extract key metrics using regex
    patterns = {
        'current_price': r'Current Price:\s*₹?([0-9,.]+)',
        'rsi': r'RSI(?:\(14\))?:\s*([0-9.]+)',
        'price_vs_sma20_pct': r'20-Day SMA:.*?\(([+-]?[0-9.]+)%\)',
        'price_vs_sma50_pct': r'50-Day SMA:.*?\(([+-]?[0-9.]+)%\)',
        'momentum_10d_pct': r'10-Day Momentum:\s*([+-]?[0-9.]+)%',
        'volume_ratio': r'Volume Ratio.*?:\s*([0-9.]+)x?',
        'distance_from_52w_low_pct': r'Distance from 52W Low:\s*([0-9.]+)%',
        'atr_14': r'ATR\(14\):\s*₹?([0-9.]+)',
        'atr_pct': r'ATR.*?\(([0-9.]+)%\s*of price\)',
        'recent_trend': r'Recent Trend.*?:\s*(\w+)',
        'weekly_trend': r'Weekly Trend:\s*(\w+)',
        'bb_position_z': r'Bollinger Position:\s*([+-]?[0-9.]+)\s*σ'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            try:
                value = match.group(1).replace(',', '')
                if key in ['current_price', 'rsi', 'price_vs_sma20_pct',
                          'price_vs_sma50_pct', 'momentum_10d_pct',
                          'volume_ratio', 'distance_from_52w_low_pct',
                          'atr_14', 'atr_pct', 'bb_position_z']:
                    tech_data[key] = float(value)
                else:
                    tech_data[key] = value
            except (ValueError, IndexError):
                pass

    return tech_data


# ============================================================================
# ENHANCEMENT 4: INTRADAY FEEDBACK CALIBRATION
# ============================================================================

def load_recent_decisions(limit: int = 50) -> List[Dict]:
    """Load recent Claude exit decisions from JSONL"""
    try:
        jsonl_path = 'outputs/claude_exit_decisions.jsonl'
        if not os.path.exists(jsonl_path):
            return []

        decisions = []
        with open(jsonl_path, 'r') as f:
            for line in f:
                if line.strip():
                    decisions.append(json.loads(line))

        return decisions[-limit:] if len(decisions) > limit else decisions

    except Exception as e:
        logger.warning(f"Failed to load recent decisions: {e}")
        return []


def generate_feedback_hints() -> str:
    """Generate dynamic calibration hints based on recent accuracy"""

    recent = load_recent_decisions(limit=30)

    if len(recent) < 10:
        return ""  # Not enough data

    # Categorize decisions
    exits = [d for d in recent if d.get('decision') == 'IMMEDIATE_EXIT']
    monitors = [d for d in recent if d.get('decision') == 'MONITOR']
    holds = [d for d in recent if d.get('decision') == 'HOLD']

    hints = []

    # Check for over-aggressive exits
    if len(exits) > len(recent) * 0.4:  # >40% exits
        hints.append("⚠️  Recent data shows high EXIT rate (>40%). "
                    "Verify 2+ critical signals before IMMEDIATE_EXIT. "
                    "Prefer MONITOR for single warning signs.")

    # Check for under-detection
    if len(holds) > len(recent) * 0.7:  # >70% holds
        hints.append("⚠️  High HOLD rate detected. "
                    "May be missing early deterioration signals. "
                    "Lower threshold for technical breakdowns.")

    # Average urgency check
    avg_urgency = sum(d.get('urgency_score', 50) for d in recent) / len(recent)
    if avg_urgency < 45:
        hints.append("📊 Average urgency score is low (45). "
                    "Consider amplifying scores when multiple risks present.")
    elif avg_urgency > 65:
        hints.append("📊 Average urgency score is high (65). "
                    "Ensure each signal is material before amplifying.")

    return "\n\n".join(hints) if hints else ""


# ============================================================================
# ENHANCEMENT 5: ADAPTIVE THRESHOLDS
# ============================================================================

def get_adaptive_thresholds(prompt: str) -> Dict:
    """Adjust decision thresholds based on data coverage"""

    has_news = 'NEWS HEADLINE:' in prompt and 'No article content' not in prompt
    has_tech = 'TECHNICAL ANALYSIS DATA:' in prompt
    has_full_article = len(prompt) > 2000  # Proxy for full article text

    if has_news and has_tech and has_full_article:
        # Full coverage - use strict thresholds
        return {
            'immediate_exit': 90,
            'monitor': 65,
            'hold': 40,
            'mode': 'FULL_COVERAGE'
        }
    elif has_tech and not has_news:
        # Technical-only - more aggressive on chart signals
        return {
            'immediate_exit': 80,  # Lower bar
            'monitor': 55,
            'hold': 35,
            'mode': 'TECHNICAL_ONLY'
        }
    elif has_news and not has_tech:
        # News-only - require stronger fundamental signals
        return {
            'immediate_exit': 95,
            'monitor': 70,
            'hold': 45,
            'mode': 'NEWS_ONLY'
        }
    else:
        # Limited data - conservative
        return {
            'immediate_exit': 95,
            'monitor': 70,
            'hold': 50,
            'mode': 'LIMITED_DATA'
        }


# ============================================================================
# ENHANCEMENT 6: RISK MANAGEMENT AUTO-COMPUTATION
# ============================================================================

def compute_risk_levels(
    technical_data: Dict,
    exit_urgency: float,
    certainty: float
) -> Dict:
    """Compute stop-loss and trailing stop levels"""

    price = technical_data.get('current_price')
    atr = technical_data.get('atr_14')
    low_20_pct = technical_data.get('distance_from_20d_low_pct', 0)

    if not price or not atr:
        return {'stop_loss': 'N/A', 'trailing_stop': 'N/A'}

    # Estimate swing low from distance
    swing_low = price / (1 + low_20_pct / 100) if low_20_pct > 0 else price * 0.95

    # Stop-loss: tighter for high urgency
    if exit_urgency >= 80:
        stop_mult = 0.5  # Tight
    elif exit_urgency >= 60:
        stop_mult = 1.0  # Normal
    else:
        stop_mult = 1.5  # Loose

    stop = swing_low - (stop_mult * atr)

    # Trailing stop: based on urgency
    trail_mult = 2.0 if exit_urgency >= 70 else 1.5
    trail = trail_mult * atr

    return {
        'stop_loss': f"₹{stop:.2f} (swing low - {stop_mult}×ATR)",
        'trailing_stop': f"₹{trail:.2f} ({trail_mult}×ATR)",
        'urgency_mode': 'TIGHT' if exit_urgency >= 80 else 'NORMAL'
    }


# ============================================================================
# ENHANCEMENT 7: DECISION LOGGING
# ============================================================================

def log_exit_decision(
    ticker: str,
    decision: Dict,
    technical_data: Dict,
    prompt_hash: str,
    response_length: int
) -> None:
    """Log Claude exit decision for feedback learning"""

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'provider': 'claude-exit',
        'ticker': ticker,
        'decision': decision.get('exit_recommendation'),
        'urgency_score': decision.get('exit_urgency_score'),
        'certainty': decision.get('certainty'),
        'technical_score': decision.get('technical_breakdown_score'),
        'fundamental_score': decision.get('fundamental_risk_score'),
        'sentiment_score': decision.get('negative_sentiment_score'),
        'catalysts': decision.get('exit_catalysts', []),
        'current_price': technical_data.get('current_price'),
        'rsi': technical_data.get('rsi'),
        'prompt_hash': prompt_hash,
        'response_length': response_length
    }

    try:
        os.makedirs('outputs', exist_ok=True)
        jsonl_path = 'outputs/claude_exit_decisions.jsonl'
        with open(jsonl_path, 'a') as f:
            f.write(json.dumps(log_entry, separators=(',', ':')) + '\n')
    except Exception as e:
        logger.warning(f"Failed to log decision: {e}")


# ============================================================================
# MAIN ANALYSIS FUNCTION
# ============================================================================

def analyze_with_claude_cli(prompt: str) -> Dict:
    """
    Use Claude CLI (shell command) for analysis - NO API KEY NEEDED!
    """
    import subprocess

    try:
        # ENHANCEMENT 2: Fetch article content if URLs present
        urls = extract_urls_from_prompt(prompt)
        if urls:
            logger.info(f"🌐 Fetching {len(urls)} article(s)...")
            for url in urls[:2]:
                article_text = fetch_article_content(url)
                if article_text:
                    prompt = prompt.replace('No article content available', article_text)

        # ENHANCEMENT 3: Extract technical data
        technical_data = extract_technical_data(prompt)

        # ENHANCEMENT 4: Generate feedback hints
        feedback_hints = generate_feedback_hints()

        # ENHANCEMENT 5: Get adaptive thresholds
        thresholds = get_adaptive_thresholds(prompt)

        # Build enhanced prompt with feedback
        enhanced_prompt = prompt
        if feedback_hints:
            enhanced_prompt = f"{feedback_hints}\n\n━━━━━━━━━━━━\n\n{prompt}"

        # Add threshold context
        enhanced_prompt += f"""

ADAPTIVE THRESHOLDS (Mode: {thresholds['mode']}):
• IMMEDIATE_EXIT: ≥{thresholds['immediate_exit']}
• MONITOR: {thresholds['monitor']}-{thresholds['immediate_exit']-1}
• HOLD: <{thresholds['monitor']}
"""

        # Enforce strict real-time grounding (always on):
        enhanced_prompt += "\n\nSTRICT CONTEXT: Base your decision ONLY on the TECHNICAL DATA and NEWS/ARTICLE content provided in this prompt (both fetched now). Do not use prior training knowledge or external facts not present here. If news is not available, perform a technical-only assessment and do not invent catalysts.\n"

        # Call Claude CLI with correct flags
        model = os.getenv('CLAUDE_MODEL', 'sonnet')

        # Call claude CLI with system prompt, passing user message via stdin
        cmd = [
            'claude',
            '--print',  # Non-interactive mode
            '--model', model,
            '--system-prompt', CLAUDE_EXIT_SYSTEM_PROMPT,
            '--output-format', 'text',  # We'll parse JSON from text
            '--tools', '',  # Disable tools for faster response
        ]

        result = subprocess.run(
            cmd,
            input=enhanced_prompt,  # Pass prompt via stdin
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.warning(f"⚠️  Claude CLI failed: {result.stderr}")
            return analyze_with_claude_api(prompt)  # Fallback to API

        response_text = result.stdout.strip()

        # Strip markdown code blocks
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\n', '', response_text)
            response_text = re.sub(r'\n```$', '', response_text)

        # Parse JSON
        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            json_match = re.search(r'\{[^}]+\}', response_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
            else:
                logger.warning("⚠️  Failed to parse Claude CLI response as JSON")
                return analyze_with_claude_api(prompt)  # Fallback

        # ENHANCEMENT 6: Compute risk levels
        if technical_data and parsed.get('exit_urgency_score'):
            risk_levels = compute_risk_levels(
                technical_data,
                parsed['exit_urgency_score'],
                parsed.get('certainty', 50)
            )
            parsed['risk_levels'] = risk_levels
            # If model did not supply stop_loss_price but we computed a stop, surface it
            if not parsed.get('stop_loss_price') and isinstance(risk_levels.get('stop_loss'), str):
                try:
                    import re as _re
                    m = _re.search(r'-?\d+(?:\.\d+)?', risk_levels['stop_loss'])
                    if m:
                        parsed['stop_loss_price'] = float(m.group(0))
                except Exception:
                    pass

        # Extract ticker
        ticker_match = re.search(r'STOCK:\s*(\w+)', prompt)
        ticker = ticker_match.group(1) if ticker_match else 'UNKNOWN'

        # ENHANCEMENT 7: Log decision
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        log_exit_decision(
            ticker=ticker,
            decision=parsed,
            technical_data=technical_data,
            prompt_hash=prompt_hash,
            response_length=len(response_text)
        )

        logger.info(f"✅ Claude CLI exit analysis complete for {ticker} "
                   f"(urgency={parsed.get('exit_urgency_score')}, "
                   f"certainty={parsed.get('certainty')}%)")

        return parsed

    except subprocess.TimeoutExpired:
        logger.warning("⚠️  Claude CLI timeout")
        return analyze_with_claude_api(prompt)
    except Exception as e:
        logger.warning(f"⚠️  Claude CLI error: {e}")
        return analyze_with_claude_api(prompt)


def analyze_with_claude_api(prompt: str) -> Dict:
    """
    Fallback to Anthropic API if CLI fails
    """

    # Check for anthropic library
    try:
        import anthropic
    except ImportError:
        logger.warning("⚠️  anthropic library not installed")
        return fallback_heuristic(prompt, "anthropic library not installed")

    # Check API key
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.warning("⚠️  ANTHROPIC_API_KEY not set")
        return fallback_heuristic(prompt, "ANTHROPIC_API_KEY not set")

    try:
        # ENHANCEMENT 2: Fetch article content if URLs present
        urls = extract_urls_from_prompt(prompt)
        if urls:
            logger.info(f"🌐 Fetching {len(urls)} article(s)...")
            for url in urls[:2]:  # Limit to 2 URLs
                article_text = fetch_article_content(url)
                if article_text:
                    # Replace placeholder with actual content
                    prompt = prompt.replace(
                        'No article content available',
                        article_text
                    )

        # ENHANCEMENT 3: Extract technical data
        technical_data = extract_technical_data(prompt)

        # ENHANCEMENT 4: Generate feedback hints
        feedback_hints = generate_feedback_hints()

        # ENHANCEMENT 5: Get adaptive thresholds
        thresholds = get_adaptive_thresholds(prompt)

        # Build enhanced prompt with feedback
        enhanced_prompt = prompt
        if feedback_hints:
            enhanced_prompt = f"{feedback_hints}\n\n━━━━━━━━━━━━\n\n{prompt}"

        # Add threshold context
        enhanced_prompt += f"""

ADAPTIVE THRESHOLDS (Mode: {thresholds['mode']}):
• IMMEDIATE_EXIT: ≥{thresholds['immediate_exit']}
• MONITOR: {thresholds['monitor']}-{thresholds['immediate_exit']-1}
• HOLD: <{thresholds['monitor']}
"""

        # Call Claude API
        client = anthropic.Anthropic(api_key=api_key)

        model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        temperature = float(os.getenv('ANTHROPIC_TEMPERATURE', '0.2'))
        max_tokens = int(os.getenv('ANTHROPIC_MAX_TOKENS', '1500'))

        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=CLAUDE_EXIT_SYSTEM_PROMPT,  # ENHANCEMENT 1
            messages=[{"role": "user", "content": enhanced_prompt}]
        )

        # Extract and parse response
        response_text = message.content[0].text if message.content else "{}"
        response_text = response_text.strip()

        # Strip markdown code blocks
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\n', '', response_text)
            response_text = re.sub(r'\n```$', '', response_text)

        result = json.loads(response_text)

        # ENHANCEMENT 6: Compute risk levels
        if technical_data and result.get('exit_urgency_score'):
            risk_levels = compute_risk_levels(
                technical_data,
                result['exit_urgency_score'],
                result.get('certainty', 50)
            )
            result['risk_levels'] = risk_levels
            if not result.get('stop_loss_price') and isinstance(risk_levels.get('stop_loss'), str):
                try:
                    import re as _re
                    m = _re.search(r'-?\d+(?:\.\d+)?', risk_levels['stop_loss'])
                    if m:
                        result['stop_loss_price'] = float(m.group(0))
                except Exception:
                    pass

        # Extract ticker from prompt
        ticker_match = re.search(r'STOCK:\s*(\w+)', prompt)
        ticker = ticker_match.group(1) if ticker_match else 'UNKNOWN'

        # ENHANCEMENT 7: Log decision
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        log_exit_decision(
            ticker=ticker,
            decision=result,
            technical_data=technical_data,
            prompt_hash=prompt_hash,
            response_length=len(response_text)
        )

        # Log AI conversation for QA
        log_ai_conversation(
            provider='claude-exit',
            prompt=enhanced_prompt,
            response=result,
            task='exit_analysis',
            metadata={'ticker': ticker, 'thresholds': thresholds}
        )

        logger.info(f"✅ Claude exit analysis complete for {ticker} "
                   f"(urgency={result.get('exit_urgency_score')}, "
                   f"certainty={result.get('certainty')}%)")

        return result

    except anthropic.APIError as e:
        logger.error(f"❌ Anthropic API error: {e}")
        return fallback_heuristic(prompt, f"API error: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"❌ Invalid JSON from Claude: {e}")
        return fallback_heuristic(prompt, f"JSON parse error: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return fallback_heuristic(prompt, f"Error: {e}")


def fallback_heuristic(prompt: str, reason: str) -> Dict:
    """Fallback to heuristic analysis when Claude unavailable"""

    logger.warning(f"⚠️  Using heuristic fallback: {reason}")

    # Extract technical data
    tech_data = extract_technical_data(prompt)

    # Basic heuristic scoring
    urgency = 50
    sentiment = 'neutral'

    # RSI signals
    rsi = tech_data.get('rsi')
    if rsi and rsi < 30:
        urgency += 15
        sentiment = 'bearish'

    # Price vs MA signals
    price_vs_sma20 = tech_data.get('price_vs_sma20_pct', 0)
    if price_vs_sma20 < -5:
        urgency += 15

    # Volume signals
    volume_ratio = tech_data.get('volume_ratio', 1.0)
    if volume_ratio > 1.5 and tech_data.get('recent_trend') == 'down':
        urgency += 10

    # News keywords
    prompt_lower = prompt.lower()
    bearish_keywords = [
        'downgrade', 'loss', 'miss', 'warning', 'investigation',
        'fraud', 'lawsuit', 'bankruptcy', 'decline', 'plunge'
    ]

    bearish_count = sum(1 for kw in bearish_keywords if kw in prompt_lower)
    urgency += bearish_count * 10

    urgency = min(100, max(0, urgency))

    return {
        'exit_urgency_score': urgency,
        'sentiment': sentiment,
        'exit_recommendation': 'MONITOR' if urgency >= 60 else 'HOLD',
        'exit_catalysts': [f'Heuristic analysis: {reason}'],
        'hold_reasons': [] if urgency >= 60 else ['No critical signals in heuristic'],
        'risks_of_holding': ['Limited analysis - Claude unavailable'],
        'technical_breakdown_score': min(100, urgency),
        'fundamental_risk_score': 50,
        'negative_sentiment_score': min(100, urgency + 10),
        'certainty': 30,
        'reasoning': f'Heuristic fallback analysis. Reason: {reason}',
        'stop_loss_suggestion': 10
    }


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main execution"""

    prompt = sys.stdin.read()

    if not prompt.strip():
        result = fallback_heuristic(prompt, "Empty prompt")
        print(json.dumps(result))
        return

    # Run enhanced Claude analysis - TRY CLI FIRST, then API
    result = analyze_with_claude_cli(prompt)

    # Output JSON response
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
