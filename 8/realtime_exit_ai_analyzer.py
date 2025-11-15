#!/usr/bin/env python3
"""
REAL-TIME EXIT AI ANALYZER - Sharp Exit Intelligence with News Analysis
========================================================================
Applies the same sharp AI analysis to EXIT decisions as buying predictions.

KEY FEATURES:
✅ Real-time news analysis for exit signals
✅ Sharp AI prompts specifically for EXIT/SELL decisions
✅ Catalysts for selling (downgrades, warnings, regulatory issues)
✅ Risk assessment for continued holding
✅ Certainty scoring on exit recommendations
✅ Detailed reasoning matching buying prediction quality
✅ Multi-AI provider support (Claude, Codex, Gemini)

EXIT-SPECIFIC ANALYSIS:
- Profit warnings and earnings misses
- Analyst downgrades and target cuts
- Regulatory/legal issues
- Management problems
- Sector headwinds
- Technical breakdowns
- Liquidity concerns
- Better opportunity cost elsewhere

Usage:
    python3 realtime_exit_ai_analyzer.py --tickers-file exit.check.txt --ai-provider claude --hours-back 72
"""

import hashlib
import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
import logging
import subprocess
from pathlib import Path
import csv

# Import AI conversation logger for QA
try:
    from ai_conversation_logger import log_ai_conversation
except ImportError:
    def log_ai_conversation(*args, **kwargs):
        pass

# Import base news collector
import fetch_full_articles as news_collector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def _to_float(val) -> Optional[float]:
    """Coerce input to float when possible; handles numeric strings with symbols.
    Returns None if parsing is not possible.
    """
    try:
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        if not s:
            return None
        # Extract first numeric token (supports optional sign and decimal)
        import re as _re
        m = _re.search(r'-?\d+(?:\.\d+)?', s)
        if not m:
            return None
        return float(m.group(0))
    except Exception:
        return None

@dataclass
class ExitAIAnalysis:
    """Real-time AI exit analysis result"""
    ticker: str
    headline: str
    timestamp: datetime
    exit_urgency_score: float  # 0-100 (higher = more urgent to exit)
    sentiment: str  # bearish/neutral/bullish
    exit_recommendation: str  # IMMEDIATE_EXIT/MONITOR/HOLD
    exit_catalysts: List[str]  # Reasons to exit
    hold_reasons: List[str]  # Reasons to continue holding
    risks_of_holding: List[str]  # Risks if we don't exit
    certainty: float  # 0-100
    reasoning: str
    company_name: Optional[str] = None
    articles_count: int = 0
    technical_score: Optional[float] = None
    final_rank: Optional[int] = None
    expected_exit_price: Optional[float] = None
    stop_loss_price: Optional[float] = None
    reentry_price: Optional[float] = None


EXIT_ANALYSIS_PROMPT = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 TEMPORAL CONTEXT - CRITICAL FOR AVOIDING TRAINING DATA BIAS 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**TODAY'S DATE**: {{current_date}}
**ANALYSIS TIMESTAMP**: {{current_datetime}}
**NEWS PUBLISHED**: {{published}}
**TIME WINDOW**: Last 72 hours

⚠️  CRITICAL INSTRUCTIONS:
1. All data provided below is CURRENT as of {{current_date}}
2. This news article is from the LAST 72 HOURS (recent/current event)
3. Technical and price data are REAL-TIME (fetched just now)
4. DO NOT apply historical knowledge or training data about {{ticker}}
5. If any provided data contradicts your training knowledge, THE PROVIDED DATA IS CORRECT

This is a REAL-TIME exit assessment of CURRENT market conditions.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

You are an expert portfolio manager analyzing whether to EXIT/SELL stock positions.

STOCK: {ticker} ({company_name})
NEWS HEADLINE: {headline}
NEWS SUMMARY: {summary}
PUBLISHED: {published}

TECHNICAL CONTEXT:
{technical_data}

YOUR TASK: Assess if this news justifies EXITING the position.

PRIORITY CONTEXT:
- Use the CURRENT PRICE from the technical context as the anchor.
- FIRST determine precise exit management levels: expected_exit_price/zone, stop_loss_price, and (optional) reentry_price if a re-entry is prudent after exit.
- Treat these levels as the primary decision inputs before narrative reasoning.

CRITICAL EXIT SIGNALS (High Priority):
- Profit warnings or earnings guidance cuts
- Analyst downgrades or target price reductions
- Regulatory investigations or legal issues
- Management scandals or departures
- Debt covenant breaches or liquidity concerns
- Major customer/contract losses
- Sector-wide headwinds affecting fundamentals
- Technical support breaks with high volume

MODERATE EXIT SIGNALS:
- Margin compression trends
- Market share losses to competitors
- Delayed projects or reduced capex
- Weakening demand indicators
- Rising competitive threats

REASONS TO HOLD (Counter-signals):
- Temporary/one-time issues that don't affect thesis
- News already priced in
- Strong fundamentals despite short-term noise
- Attractive valuation with margin of safety
- Upcoming positive catalysts

RESPOND WITH ONLY THIS VALID JSON:
{{
  "exit_urgency_score": <0-100: 90-100=IMMEDIATE_EXIT, 60-89=MONITOR, 0-59=HOLD>,
  "sentiment": "bearish" | "neutral" | "bullish",
  "exit_recommendation": "IMMEDIATE_EXIT" | "MONITOR" | "HOLD",
  "exit_catalysts": ["catalyst1", "catalyst2", "catalyst3"],
  "hold_reasons": ["reason1", "reason2"],
  "risks_of_holding": ["risk1", "risk2", "risk3"],
  "certainty": <0-100: confidence in recommendation>,
  "reasoning": "<2-3 sentence sharp analysis explaining the exit decision>",
  "expected_exit_price": <number or 0 if not computable>,
  "stop_loss_price": <number or 0 if not computable>,
  "reentry_price": <number or 0 if not applicable>
}}

SCORING GUIDELINES:
- exit_urgency_score 90-100: Critical issues requiring immediate exit (regulatory, fraud, bankruptcy risk)
- exit_urgency_score 75-89: Serious deterioration warranting exit (downgrade, earnings miss, broken support)
- exit_urgency_score 60-74: Warning signs to monitor closely (may exit if worsens)
- exit_urgency_score 40-59: Minor concerns but thesis intact (hold with monitoring)
- exit_urgency_score 0-39: No exit signals, continue holding

BE DECISIVE: Don't be afraid to recommend IMMEDIATE_EXIT when fundamentals deteriorate.
OPPORTUNITY COST: Consider if capital is better deployed elsewhere.

Respond with ONLY valid JSON, no markdown, no explanations outside JSON.
"""


class ExitAIClient:
    """AI client for sharp exit analysis using Claude/Codex/Gemini"""

    def __init__(self, provider: str = 'auto'):
        self.provider = self._select_provider(provider)
        self.cache = {}
        logger.info(f"Exit AI Client initialized with provider: {self.provider}")

    def _select_provider(self, requested: str) -> str:
        """Select best available AI provider"""
        requested = requested.lower()

        # Direct provider selection
        if requested in ['claude', 'codex', 'gemini', 'cursor']:
            return requested

        # Auto-select based on availability
        if requested == 'auto':
            # Prefer Claude for accuracy, fallback to Codex
            if os.environ.get('ANTHROPIC_API_KEY'):
                return 'claude'
            elif os.environ.get('CODEX_SHELL_CMD') or os.environ.get('AI_SHELL_CMD'):
                return 'codex'
            else:
                logger.warning("No AI provider configured, using heuristic fallback")
                return 'heuristic'

        return 'codex'  # Default

    def _call_ai_bridge(self, prompt: str) -> Dict:
        """Call AI bridge with prompt"""
        try:
            if self.provider == 'claude':
                # Use enhanced exit-specific Claude bridge
                cmd = ['python3', 'claude_exit_bridge.py']
            elif self.provider == 'codex':
                cmd = ['python3', 'codex_bridge.py']
            elif self.provider == 'gemini':
                cmd = ['python3', 'gemini_agent_bridge.py']
            elif self.provider == 'cursor':
                cmd = ['python3', 'cursor_agent_bridge.py']
            else:
                # Heuristic fallback
                return self._heuristic_analysis(prompt)

            env = os.environ.copy()
            env['AI_PROVIDER'] = self.provider

            # Allow configurable timeout for AI bridge calls
            try:
                timeout_s = int(os.getenv('EXIT_AI_TIMEOUT', '45'))
            except Exception:
                timeout_s = 45

            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=timeout_s,
                env=env
            )

            if result.returncode != 0:
                logger.error(f"AI bridge failed: {result.stderr}")
                return self._heuristic_analysis(prompt)

            # Parse JSON response
            response_text = result.stdout.strip()

            # Remove markdown code fences if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            return json.loads(response_text)

        except Exception as e:
            logger.error(f"AI call failed: {e}")
            return self._heuristic_analysis(prompt)

    def _heuristic_analysis(self, prompt: str) -> Dict:
        """Fallback heuristic analysis when AI unavailable"""
        # Extract ticker from prompt
        ticker_match = re.search(r'STOCK: (\w+)', prompt)
        headline_match = re.search(r'NEWS HEADLINE: (.+)', prompt)

        ticker = ticker_match.group(1) if ticker_match else "UNKNOWN"
        headline = headline_match.group(1) if headline_match else ""

        # Simple keyword-based analysis
        bearish_keywords = [
            'downgrade', 'loss', 'miss', 'warning', 'investigation', 'fraud',
            'lawsuit', 'bankruptcy', 'debt', 'decline', 'plunge', 'crash',
            'regulatory', 'penalty', 'fine', 'scandal', 'resignation'
        ]

        exit_score = 50
        sentiment = 'neutral'
        recommendation = 'MONITOR'

        headline_lower = headline.lower()

        # Count bearish signals
        bearish_count = sum(1 for kw in bearish_keywords if kw in headline_lower)

        if bearish_count >= 2:
            exit_score = 85
            sentiment = 'bearish'
            recommendation = 'IMMEDIATE_EXIT'
        elif bearish_count == 1:
            exit_score = 70
            sentiment = 'bearish'
            recommendation = 'MONITOR'

        return {
            'exit_urgency_score': exit_score,
            'sentiment': sentiment,
            'exit_recommendation': recommendation,
            'exit_catalysts': ['Heuristic analysis - AI unavailable'],
            'hold_reasons': [] if exit_score > 70 else ['No critical exit signals detected'],
            'risks_of_holding': ['AI analysis unavailable - manual review recommended'],
            'certainty': 40,  # Low certainty for heuristic
            'reasoning': f'Heuristic analysis based on keyword matching. AI provider {self.provider} unavailable.'
        }

    def analyze_exit(
        self,
        ticker: str,
        company_name: str,
        headline: str,
        summary: str,
        published: str,
        technical_data: Dict
    ) -> Dict:
        """Analyze news for exit signals"""

        # Create cache key
        cache_key = hashlib.md5(
            f"{ticker}:{headline}:{summary}".encode()
        ).hexdigest()

        if cache_key in self.cache:
            logger.debug(f"Cache hit for {ticker}")
            return self.cache[cache_key]

        # Format technical data
        tech_summary = "No technical data available"
        if technical_data:
            tech_summary = f"""
Current Price: {technical_data.get('current_price', 'N/A')}
RSI: {technical_data.get('rsi', 'N/A')}
Price vs 20-day MA: {technical_data.get('price_vs_sma20_pct', 'N/A')}%
Price vs 50-day MA: {technical_data.get('price_vs_sma50_pct', 'N/A')}%
10-day Momentum: {technical_data.get('momentum_10d_pct', 'N/A')}%
Volume Ratio: {technical_data.get('volume_ratio', 'N/A')}
Recent Trend: {technical_data.get('recent_trend', 'N/A')}
""".strip()

        # Build prompt with temporal context
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        prompt = EXIT_ANALYSIS_PROMPT.format(
            ticker=ticker,
            company_name=company_name,
            headline=headline,
            summary=summary,
            published=published,
            technical_data=tech_summary,
            current_date=current_date,
            current_datetime=current_datetime
        )

        # Strict real-time context (always on): ground AI in provided data only
        prompt += "\n\nSTRICT CONTEXT: Base your decision ONLY on the provided TECHNICAL CONTEXT and NEWS SUMMARY (both fetched now). Do not use prior training knowledge or external facts not included here. If news summary is empty, clearly state 'technical-only assessment' and do not invent catalysts."

        # Call AI
        result = self._call_ai_bridge(prompt)

        # Cache result
        self.cache[cache_key] = result

        # Log conversation for QA
        try:
            log_ai_conversation(
                provider=self.provider,
                prompt=prompt,
                response=result,
                task='exit_analysis',
                metadata={'ticker': ticker}
            )
        except Exception:
            pass  # Logging is optional

        return result


def fetch_exit_news(ticker: str, hours_back: int = 72, max_articles: int = 10) -> List[Dict]:
    """Fetch recent news for exit analysis"""
    try:
        from datetime import timedelta

        # Use existing news collector - same as buying predictions
        sources = [
            'reuters.com',
            'livemint.com',
            'economictimes.indiatimes.com',
            'business-standard.com',
            'moneycontrol.com',
            'thehindubusinessline.com',
            'financialexpress.com'
        ]

        # Fetch publisher items only for quality (no Google News fallback)
        items = news_collector.fetch_rss_items(
            ticker=ticker,
            sources=sources,
            publishers_only=True
        )
        if not items:
            logger.warning(f"No RSS items found for {ticker}")
            return []

        # Filter by time window and convert to article format
        cutoff = datetime.now() - timedelta(hours=hours_back)
        articles = []

        for url, title, desc, pub_date in items[:max_articles]:
            if pub_date and pub_date < cutoff:
                continue

            articles.append({
                'title': title,
                'summary': desc or title,
                'description': desc or title,
                'url': url,
                'published_date': pub_date.isoformat() if pub_date else '',
                'company_name': ticker
            })

        logger.info(f"Found {len(articles)} recent articles for {ticker}")
        return articles

    except Exception as e:
        logger.error(f"News fetch failed for {ticker}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def get_technical_data(ticker: str) -> Dict:
    """Get technical data for ticker (reuse from exit_intelligence_analyzer)"""
    try:
        # Import technical analysis from main exit analyzer
        sys.path.insert(0, os.path.dirname(__file__))
        import exit_intelligence_analyzer as exit_analyzer

        df = exit_analyzer.get_stock_data(ticker)
        if df is not None and not df.empty:
            return exit_analyzer.calculate_technical_indicators(df)
        return {}
    except Exception as e:
        logger.error(f"Technical data fetch failed for {ticker}: {e}")
        return {}


def analyze_ticker_for_exit(
    ticker: str,
    ai_client: ExitAIClient,
    hours_back: int = 72,
    max_articles: int = 10
) -> List[ExitAIAnalysis]:
    """Analyze all news for a ticker to assess exit decision"""

    logger.info(f"Analyzing exit signals for {ticker}")

    # Fetch news
    articles = fetch_exit_news(ticker, hours_back, max_articles)

    # Get technical data once for the ticker (non-blocking; may be empty if data unavailable)
    technical_data = get_technical_data(ticker)

    # If no articles are available (e.g., offline or no coverage), still return a
    # single, technically-informed assessment so users get a baseline view.
    if not articles:
        logger.warning(f"No news found for {ticker}; performing technical-only assessment")
        try:
            # Use the comprehensive exit analyzer's AI bridge to produce an exit-specific
            # assessment that fully incorporates technical indicators even without news.
            import exit_intelligence_analyzer as exit_analyzer
            ai_provider = getattr(ai_client, 'provider', os.environ.get('AI_PROVIDER', 'codex'))
            result = exit_analyzer.call_ai_for_exit_assessment(
                ticker=ticker,
                ai_provider=ai_provider,
                technical_data=technical_data or {},
                news_context="No recent news available in the selected window"
            )

            # Map fields to this module's schema
            exit_catalysts = result.get('exit_catalysts') or result.get('primary_exit_reasons', []) or []
            hold_reasons = result.get('hold_reasons') or result.get('hold_rationale', []) or []

            # Calibrate urgency more aggressively in technical-only mode by
            # leaning on the technical_breakdown_score when present.
            base_urgency = float(result.get('exit_urgency_score', 50) or 50)
            tech_break = result.get('technical_breakdown_score')
            if isinstance(tech_break, (int, float)):
                calibrated_urgency = round(0.8 * float(tech_break) + 0.2 * base_urgency, 1)
            else:
                calibrated_urgency = base_urgency

            analysis = ExitAIAnalysis(
                ticker=ticker,
                headline="Technical-only assessment (no recent news)",
                timestamp=datetime.now(),
                exit_urgency_score=calibrated_urgency,
                sentiment=result.get('sentiment', 'neutral'),
                exit_recommendation=result.get('exit_recommendation', 'MONITOR'),
                exit_catalysts=exit_catalysts,
                hold_reasons=hold_reasons,
                risks_of_holding=result.get('risk_factors', result.get('risks_of_holding', [])) or [],
                certainty=result.get('exit_confidence', result.get('certainty', 40)),
                reasoning=(
                    result.get('recommendation_summary', '')
                    or result.get('reasoning', '')
                    or _compose_technical_reasoning(technical_data)
                ),
                company_name=ticker,
                articles_count=0,
                technical_score=(
                    result.get('technical_breakdown_score')
                    if result.get('technical_breakdown_score') is not None
                    else (technical_data.get('rsi', None) if technical_data else None)
                ),
                expected_exit_price=_to_float(result.get('expected_exit_price')),
                stop_loss_price=_to_float(result.get('stop_loss_price')),
                reentry_price=_to_float(result.get('reentry_price'))
            )

            return [analysis]
        except Exception as e:
            logger.error(f"Technical-only assessment failed for {ticker}: {e}")
            return []

    # Analyze each article
    analyses = []

    for article in articles:
        try:
            result = ai_client.analyze_exit(
                ticker=ticker,
                company_name=article.get('company_name', ticker),
                headline=article.get('title', ''),
                summary=article.get('summary', article.get('description', '')),
                published=article.get('published_date', ''),
                technical_data=technical_data
            )

            # Normalize catalyst/hold keys from bridges
            exit_catalysts = result.get('exit_catalysts') or result.get('primary_exit_reasons', []) or []
            hold_reasons = result.get('hold_reasons') or result.get('hold_rationale', []) or []

            analysis = ExitAIAnalysis(
                ticker=ticker,
                headline=article.get('title', ''),
                timestamp=datetime.now(),
                exit_urgency_score=result.get('exit_urgency_score', 50),
                sentiment=result.get('sentiment', 'neutral'),
                exit_recommendation=result.get('exit_recommendation', 'MONITOR'),
                exit_catalysts=exit_catalysts,
                hold_reasons=hold_reasons,
                risks_of_holding=result.get('risk_factors', result.get('risks_of_holding', [])) or [],
                certainty=result.get('exit_confidence', result.get('certainty', 50)),
                reasoning=result.get('recommendation_summary', result.get('reasoning', '')),
                company_name=article.get('company_name', ticker),
                articles_count=len(articles),
                technical_score=(
                    result.get('technical_breakdown_score')
                    if result.get('technical_breakdown_score') is not None
                    else (technical_data.get('rsi', None) if technical_data else None)
                ),
                expected_exit_price=_to_float(result.get('expected_exit_price')),
                stop_loss_price=_to_float(result.get('stop_loss_price')),
                reentry_price=_to_float(result.get('reentry_price'))
            )

            analyses.append(analysis)

        except Exception as e:
            logger.error(f"Analysis failed for {ticker} article: {e}")
            continue

    return analyses


def _compose_technical_reasoning(tech: Dict) -> str:
    """Compose a concise, human-readable reasoning from technical indicators."""
    try:
        parts = []
        rsi = tech.get('rsi')
        if isinstance(rsi, (int, float)):
            if rsi < 30:
                parts.append(f"RSI {rsi:.1f} (oversold; momentum weak)")
            elif rsi > 70:
                parts.append(f"RSI {rsi:.1f} (overbought; mean-revert risk)")
        p20 = tech.get('price_vs_sma20_pct')
        if isinstance(p20, (int, float)):
            parts.append(f"{p20:+.1f}% vs 20DMA")
        p50 = tech.get('price_vs_sma50_pct')
        if isinstance(p50, (int, float)):
            parts.append(f"{p50:+.1f}% vs 50DMA")
        mom10 = tech.get('momentum_10d_pct')
        if isinstance(mom10, (int, float)):
            parts.append(f"10d momentum {mom10:+.1f}%")
        vr = tech.get('volume_ratio')
        if isinstance(vr, (int, float)) and vr:
            parts.append(f"volume x{vr:.2f}")
        if parts:
            return "; ".join(parts)
    except Exception:
        pass
    return "Technical-only assessment: key signals summarized."


def aggregate_exit_decision(analyses: List[ExitAIAnalysis]) -> Dict:
    """Aggregate multiple news analyses into single exit decision"""

    if not analyses:
        return {
            'ticker': 'UNKNOWN',
            'exit_recommendation': 'HOLD',
            'exit_urgency_score': 0,
            'certainty': 0,
            'exit_catalysts': [],
            'hold_reasons': ['No news available'],
            'risks_of_holding': [],
            'reasoning': 'No recent news found for analysis',
            'articles_analyzed': 0
        }

    ticker = analyses[0].ticker

    # Weighted average of exit urgency scores (weighted by certainty)
    total_weighted_score = 0
    total_weight = 0

    for analysis in analyses:
        weight = analysis.certainty / 100.0
        total_weighted_score += analysis.exit_urgency_score * weight
        total_weight += weight

    avg_exit_score = total_weighted_score / total_weight if total_weight > 0 else 50

    # Aggregate certainty (average)
    avg_certainty = sum(a.certainty for a in analyses) / len(analyses)

    # Collect unique catalysts and risks
    all_exit_catalysts = []
    all_hold_reasons = []
    all_risks = []

    for analysis in analyses:
        all_exit_catalysts.extend(analysis.exit_catalysts)
        all_hold_reasons.extend(analysis.hold_reasons)
        all_risks.extend(analysis.risks_of_holding)

    # Deduplicate while preserving order
    exit_catalysts = list(dict.fromkeys(all_exit_catalysts))[:5]
    hold_reasons = list(dict.fromkeys(all_hold_reasons))[:3]
    risks_of_holding = list(dict.fromkeys(all_risks))[:5]

    # Determine final recommendation with adaptive thresholds.
    # If we only have technical-only assessments (no articles), use slightly
    # lower thresholds to reflect higher reliance on price action.
    tech_only = all((getattr(a, 'articles_count', 0) == 0) or ('Technical-only' in (a.headline or '')) for a in analyses)
    imm_thresh = 80 if tech_only else 90
    mon_thresh = 50 if tech_only else 60

    if avg_exit_score >= imm_thresh:
        recommendation = 'IMMEDIATE_EXIT'
    elif avg_exit_score >= mon_thresh:
        recommendation = 'MONITOR'
    else:
        recommendation = 'HOLD'

    # Best reasoning (from highest urgency analysis)
    best_analysis = max(analyses, key=lambda a: a.exit_urgency_score)

    # Surface price levels, preferring best_analysis; fallback to first available
    expected_exit_price = None
    stop_loss_price = None
    reentry_price = None

    expected_exit_price = _to_float(getattr(best_analysis, 'expected_exit_price', None))
    stop_loss_price = _to_float(getattr(best_analysis, 'stop_loss_price', None))
    reentry_price = _to_float(getattr(best_analysis, 'reentry_price', None))

    if expected_exit_price is None or stop_loss_price is None:
        for a in analyses:
            if expected_exit_price is None:
                expected_exit_price = _to_float(getattr(a, 'expected_exit_price', None))
            if stop_loss_price is None:
                stop_loss_price = _to_float(getattr(a, 'stop_loss_price', None))
            if reentry_price is None:
                reentry_price = _to_float(getattr(a, 'reentry_price', None))
            if expected_exit_price is not None and stop_loss_price is not None:
                break

    return {
        'ticker': ticker,
        'company_name': analyses[0].company_name,
        'exit_recommendation': recommendation,
        'exit_urgency_score': round(avg_exit_score, 1),
        'certainty': round(avg_certainty, 1),
        'sentiment': best_analysis.sentiment,
        'exit_catalysts': exit_catalysts,
        'hold_reasons': hold_reasons,
        'risks_of_holding': risks_of_holding,
        'reasoning': best_analysis.reasoning,
        'headline': best_analysis.headline,
        'articles_analyzed': len(analyses),
        'technical_score': analyses[0].technical_score,
        'expected_exit_price': expected_exit_price,
        'stop_loss_price': stop_loss_price,
        'reentry_price': reentry_price
    }


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Real-time Exit AI Analyzer - Sharp exit intelligence with news analysis'
    )
    parser.add_argument('--tickers-file', required=True, help='File with tickers to analyze')
    parser.add_argument('--ai-provider', default='auto', choices=['auto', 'claude', 'codex', 'gemini', 'cursor', 'heuristic'])
    parser.add_argument('--hours-back', type=int, default=72, help='Hours of news to analyze')
    parser.add_argument('--max-articles', type=int, default=10, help='Max articles per ticker')
    parser.add_argument('--output', default='', help='Output CSV file')

    args = parser.parse_args()

    # Read tickers
    with open(args.tickers_file, 'r') as f:
        tickers = [line.strip().upper() for line in f if line.strip() and not line.startswith('#')]

    if not tickers:
        logger.error("No tickers found in file")
        sys.exit(1)

    logger.info(f"Analyzing {len(tickers)} tickers for exit signals")
    logger.info(f"AI Provider: {args.ai_provider}")
    logger.info(f"News Window: {args.hours_back} hours")

    # Initialize AI client
    ai_client = ExitAIClient(provider=args.ai_provider)

    # Analyze each ticker
    results = []

    for i, ticker in enumerate(tickers, 1):
        logger.info(f"[{i}/{len(tickers)}] Processing {ticker}")

        try:
            analyses = analyze_ticker_for_exit(
                ticker=ticker,
                ai_client=ai_client,
                hours_back=args.hours_back,
                max_articles=args.max_articles
            )

            if analyses:
                aggregated = aggregate_exit_decision(analyses)
                results.append(aggregated)

                # Print summary
                print(f"\n{ticker}: {aggregated['exit_recommendation']} "
                      f"(Urgency: {aggregated['exit_urgency_score']}/100, "
                      f"Certainty: {aggregated['certainty']}%)")
                print(f"  Catalysts: {', '.join(aggregated['exit_catalysts'][:2])}")

        except Exception as e:
            logger.error(f"Failed to analyze {ticker}: {e}")
            continue

    # Sort by exit urgency
    results.sort(key=lambda x: x['exit_urgency_score'], reverse=True)

    # Add rank
    for rank, result in enumerate(results, 1):
        result['rank'] = rank

    # Output to CSV
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    output_file = args.output or f'realtime_exit_ai_results_{timestamp}_{args.ai_provider}.csv'

    with open(output_file, 'w', newline='') as f:
        fieldnames = [
            'rank', 'ticker', 'company_name', 'exit_urgency_score', 'sentiment',
            'exit_recommendation', 'exit_catalysts', 'hold_reasons', 'risks_of_holding',
            'certainty', 'articles_analyzed', 'technical_score', 'headline', 'reasoning',
            'expected_exit_price', 'stop_loss_price',
            'stop', 'trail', 'alert'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # Compute levels per ticker for quick actioning
        levels_cache = {}
        try:
            import exit_intelligence_analyzer as exit_analyzer  # reuse levels logic
        except Exception:
            exit_analyzer = None

        for result in results:
            tkr = result['ticker']
            lv = {'stop': '', 'trail': '', 'alert': ''}
            if exit_analyzer is not None:
                try:
                    tech = get_technical_data(tkr)  # reuse local helper
                    if tech:
                        lv = exit_analyzer._compute_levels(tech) or {'stop': '', 'trail': '', 'alert_reclaim': ''}
                except Exception:
                    pass

            # Use AI-provided stop_loss_price if present, else fallback to technical levels 'stop'
            ai_stop = result.get('stop_loss_price')
            if ai_stop in (None, ''):
                ai_stop = lv.get('stop', '')
            # Normalize expected_exit_price for CSV
            ai_expected = result.get('expected_exit_price')
            if ai_expected in (None, ''):
                ai_expected = ''

            writer.writerow({
                'rank': result['rank'],
                'ticker': result['ticker'],
                'company_name': result['company_name'],
                'exit_urgency_score': result['exit_urgency_score'],
                'sentiment': result['sentiment'],
                'exit_recommendation': result['exit_recommendation'],
                'exit_catalysts': '; '.join(result['exit_catalysts']),
                'hold_reasons': '; '.join(result['hold_reasons']),
                'risks_of_holding': '; '.join(result['risks_of_holding']),
                'certainty': result['certainty'],
                'articles_analyzed': result['articles_analyzed'],
                'technical_score': result.get('technical_score', ''),
                'headline': result['headline'],
                'reasoning': result['reasoning'],
                'expected_exit_price': ai_expected,
                'stop_loss_price': ai_stop,
                'stop': lv.get('stop', ''),
                'trail': lv.get('trail', ''),
                'alert': lv.get('alert_reclaim', '')
            })

    logger.info(f"\n✅ Analysis complete! Results saved to: {output_file}")
    logger.info(f"\n📊 SUMMARY:")
    logger.info(f"   Total analyzed: {len(results)}")
    logger.info(f"   IMMEDIATE_EXIT: {sum(1 for r in results if r['exit_recommendation'] == 'IMMEDIATE_EXIT')}")
    logger.info(f"   MONITOR: {sum(1 for r in results if r['exit_recommendation'] == 'MONITOR')}")
    logger.info(f"   HOLD: {sum(1 for r in results if r['exit_recommendation'] == 'HOLD')}")

    # Print top exit candidates
    immediate_exits = [r for r in results if r['exit_recommendation'] == 'IMMEDIATE_EXIT']
    if immediate_exits:
        logger.info(f"\n🚨 IMMEDIATE EXIT RECOMMENDATIONS:")
        for result in immediate_exits[:10]:
            logger.info(f"   {result['rank']}. {result['ticker']} - Urgency {result['exit_urgency_score']}/100")
            logger.info(f"      {result['reasoning'][:100]}")


if __name__ == '__main__':
    main()
