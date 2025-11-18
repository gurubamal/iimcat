#!/usr/bin/env python3
"""
AI VERDICT ENGINE
Intelligent decision making for final verdicts using real-time data WITHOUT training data bias

Features:
- Uses Claude AI to synthesize verification results
- Generates unbiased verdicts based on web-verified data ONLY
- Provides transparent reasoning for every decision
- Flags temporal/currency issues
- Calibrates confidence based on verification quality
- Creates audit trails of decision logic

Design Principles:
1. NO TRAINING DATA: All verdicts based on web-verified facts only
2. REAL-TIME GROUNDING: Uses current data with explicit dates
3. TRANSPARENT REASONING: Shows exactly how decision was made
4. UNCERTAINTY FLAGGING: Explicitly notes unconfirmed data
5. TEMPORAL AWARENESS: Tracks when data was last verified
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VerdictDecision:
    """Final verdict based on verified data"""
    ticker: str
    timestamp: str  # When decision was made
    final_score: float  # 0-100
    final_sentiment: str  # bullish/bearish/neutral
    final_recommendation: str  # BUY/HOLD/SELL
    verdict_summary: str  # One-line summary
    reasoning: str  # Detailed explanation from Claude
    data_basis: List[str]  # Which verified data points were used
    unverified_claims: List[str]  # What couldn't be verified
    confidence_level: float  # 0-1, based on verification quality
    temporal_currency: str  # How current is this data?
    audit_trail: str  # JSON string of decision process
    flagged_issues: List[str]  # Any red flags or issues


class AIVerdictEngine:
    """
    Uses Claude AI to generate intelligent verdicts based ONLY on web-verified data.

    For shell/CLI providers like codex-shell where no Anthropic/Claude
    credentials are available, this engine automatically operates in a
    conservative fallback mode that:
      - preserves the original analyzer score and recommendation, and
      - uses web verification + analyzer certainty to calibrate confidence,
    without attempting any Claude CLI or API calls.
    """

    def __init__(self, ai_provider: Optional[str] = None):
        """Initialize the verdict engine"""
        # Track which upstream AI/provider generated the CSV so that we can
        # skip Claude entirely for codex-shell style runs while keeping the
        # existing Claude behavior untouched.
        self.ai_provider = (ai_provider or os.getenv('AI_VERDICT_PROVIDER', 'unknown')).strip().lower()
        self.model = os.getenv('AI_VERDICT_MODEL', 'claude-3-5-sonnet-20241022')
        self.temperature = 0.3  # Low temperature for consistency
        self.max_retries = 3

    def generate_verdict(self, ticker: str, analysis_data: Dict, verification_results: Dict) -> VerdictDecision:
        """
        Generate final verdict using Claude AI based on verified data ONLY

        Args:
            ticker: Stock ticker
            analysis_data: Original analysis from realtime_ai_news_analyzer
            verification_results: Results from WebSearchVerificationEngine

        Returns:
            VerdictDecision with Claude's intelligent verdict
        """
        timestamp = datetime.now().isoformat()

        # Decide whether to call Claude at all. By default we allow Claude to
        # run for every provider (including Codex-shell), because AI reasoning
        # is critical for final verdicts. If an environment flag explicitly
        # disables Claude for shell providers, we fall back to a purely
        # calibrated mode using the original analyzer score.
        disable_for_shell = os.getenv("AI_VERDICT_DISABLE_FOR_SHELL", "0").strip() == "1"
        use_claude = True
        if disable_for_shell and (
            self.ai_provider.startswith("codex") or
            self.ai_provider.startswith("cursor")
        ):
            use_claude = False

        if use_claude:
            # Build the prompt for Claude
            prompt = self._build_verdict_prompt(ticker, analysis_data, verification_results)

            # Get Claude's verdict (or fallback if unavailable)
            verdict_response = self._call_claude(prompt)

            # Parse Claude's response
            parsed_verdict = self._parse_verdict_response(verdict_response, ticker)
        else:
            # Shell/CLI provider in use (e.g., codex-shell) – do NOT invoke
            # Claude at all. Mark as a fallback verdict so we reuse the
            # existing conservative handling that preserves the original
            # analyzer ranking and uses verification to calibrate confidence.
            parsed_verdict = {
                "verdict_source": "fallback",
                "flags": [
                    "Verdict engine running in shell-provider fallback mode "
                    "- using original analyzer score and recommendation"
                ]
            }

        # If Claude was unavailable and we fell back, preserve the original
        # analyzer's ranking and recommendation (no extra penalty), while still
        # surfacing verification/temporal context in the metadata. This avoids
        # flattening scores to 50/HOLD when no AI verdict model is active.
        if parsed_verdict.get("verdict_source") == "fallback":
            final_score = analysis_data.get('ai_score', 50)
            final_sentiment = analysis_data.get('sentiment', 'neutral')
            final_recommendation = analysis_data.get('recommendation', 'HOLD')
            verdict_summary = "AI verdict engine unavailable - using original analysis ranking (see verification flags)"
            reasoning = (
                "Claude verdict system was not available for this run. "
                "Final score and recommendation are taken from the original real-time analysis, "
                "with web-search verification and temporal flags provided for context."
            )
        else:
            final_score = parsed_verdict.get('score', analysis_data.get('ai_score', 50))
            final_sentiment = parsed_verdict.get('sentiment', 'neutral')
            final_recommendation = parsed_verdict.get('recommendation', 'HOLD')
            verdict_summary = parsed_verdict.get('summary', 'Data verification in progress')
            reasoning = parsed_verdict.get('reasoning', verdict_response)

        # Confidence handling:
        # - When Claude verdict is available, keep the original behavior
        #   (confidence driven by verification quality).
        # - When we are in fallback mode (no Claude verdict), blend the original
        #   analyzer's certainty with verification confidence so confidence is
        #   non-zero but still penalized when verification is weak.
        if parsed_verdict.get("verdict_source") == "fallback":
            base_conf = float(analysis_data.get('certainty', 50) or 50) / 100.0
            ver_conf = float(verification_results.get('confidence_score', 0.0) or 0.0)
            # Down-weight base confidence if verification is bad, but never drop below 0.1
            combined_conf = 0.7 * base_conf + 0.3 * ver_conf
            overall_conf = max(0.1, min(1.0, combined_conf))
        else:
            overall_conf = self._calculate_confidence(verification_results)

        decision = VerdictDecision(
            ticker=ticker,
            timestamp=timestamp,
            final_score=final_score,
            final_sentiment=final_sentiment,
            final_recommendation=final_recommendation,
            verdict_summary=verdict_summary,
            reasoning=reasoning,
            data_basis=self._identify_verified_data(verification_results),
            unverified_claims=self._identify_unverified_data(verification_results),
            confidence_level=overall_conf,
            temporal_currency=self._assess_temporal_currency(verification_results),
            audit_trail=json.dumps({
                'input_analysis_score': analysis_data.get('ai_score'),
                'verification_summary': {
                    'total_verifications': verification_results.get('verification_count', 0),
                    'verified': verification_results.get('verified_count', 0),
                    'unverified': verification_results.get('unverified_count', 0),
                    'conflicting': verification_results.get('conflicting_count', 0),
                    'overall_assessment': verification_results.get('overall_assessment')
                },
                'verdict_process': (
                    'Claude AI analysis of verified facts only'
                    if parsed_verdict.get("verdict_source") != "fallback"
                    else 'Fallback: original analysis used (Claude verdict engine unavailable)'
                ),
                'timestamp': timestamp
            }),
            flagged_issues=parsed_verdict.get('flags', [])
        )

        return decision

    def _build_verdict_prompt(self, ticker: str, analysis_data: Dict, verification_results: Dict) -> str:
        """
        Build a comprehensive prompt for Claude that emphasizes verified data ONLY
        and avoids any reliance on training data
        """

        # Extract verified vs unverified data
        verified_data = self._extract_verified_data(verification_results)
        unverified_data = self._extract_unverified_data(verification_results)

        # Build the prompt with explicit temporal grounding
        prompt = f"""
================================================================================
STOCK VERDICT DECISION - REAL-TIME DATA ONLY (No Training Data)
================================================================================

Ticker: {ticker}
Current Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Analysis Timestamp: {analysis_data.get('timestamp', 'Unknown')}

🚨 CRITICAL INSTRUCTION 🚨
You are an AI making a verdict for: {ticker}
Your knowledge cutoff is BEFORE this analysis timestamp.
Therefore: You MUST ignore ALL training data about this stock.

⚠️  MANDATORY: Your verdict must be based EXCLUSIVELY on the VERIFIED DATA below.

❌ DO NOT USE:
- Any memorized prices, targets, or historical data about {ticker}
- Your training data knowledge about {ticker}'s past performance
- Historical analyst predictions or historical ratings
- Pattern matching from historical data
- Your knowledge of what happened to this stock before your training cutoff
- Any assumptions based on "what usually happens" in markets

✅ DO USE ONLY:
- The VERIFIED CURRENT DATA points explicitly listed below
- Current prices from yfinance (with timestamps)
- Recent news and catalysts (dated, within last 48 hours)
- Verified fundamental metrics (earnings, margins, health)
- Real-time institutional buying/selling data if verified
- Technical setup from current data only
- Logical analysis of ONLY the data provided

================================================================================
VERIFICATION QUALITY CHECK
================================================================================
Verification Status: {verification_results.get('overall_assessment', 'UNKNOWN')}
Confidence in Verification: {verification_results.get('confidence_score', 0):.1%}

⚠️  IF VERIFICATION CONFIDENCE < 50%: Be conservative in your verdict
⚠️  IF MANY DATA POINTS UNVERIFIED: Consider HOLD or lower confidence recommendation
✅ IF VERIFICATION CONFIDENCE > 80%: You can be more confident in your verdict

================================================================================
PART 1: VERIFIED DATA (Based on Web Search Verification)
================================================================================

Overall Verification Status: {verification_results.get('overall_assessment', 'UNKNOWN')}
Verification Confidence: {verification_results.get('confidence_score', 0):.1%}

VERIFIED FACTS (Can confidently use these):
{self._format_verified_data(verified_data)}

UNVERIFIED/QUESTIONABLE DATA (Use cautiously or flag):
{self._format_unverified_data(unverified_data)}

DATA CONFLICTS (Red flags to consider):
{self._format_conflicts(verification_results)}

================================================================================
PART 2: CURRENT STOCK ANALYSIS
================================================================================

Original AI Score: {analysis_data.get('ai_score', 'N/A')}/100
Original Sentiment: {analysis_data.get('sentiment', 'Unknown')}
Original Recommendation: {analysis_data.get('recommendation', 'Unknown')}

Current Price: ₹{analysis_data.get('current_price', 'Unknown')}
Price Timestamp: {analysis_data.get('price_timestamp', 'Unknown')}

Recent Catalysts:
{self._format_catalysts(analysis_data)}

Technical Setup:
- RSI: {analysis_data.get('rsi', 'N/A')}
- Price vs 20DMA: {analysis_data.get('price_vs_20dma_pct', 'N/A')}%
- Price vs 50DMA: {analysis_data.get('price_vs_50dma_pct', 'N/A')}%
- 10-day Momentum: {analysis_data.get('momentum_10d', 'N/A')}%
- Volume Ratio: {analysis_data.get('volume_ratio', 'N/A')}

================================================================================
PART 3: YOUR VERDICT TASK
================================================================================

Based ONLY on the VERIFIED DATA above, generate a final verdict with:

1. ADJUSTED SCORE: 0-100 based on verified facts
   - Consider: Verification quality, data conflicts, temporal issues
   - Adjust down if critical data unverified
   - Adjust down if conflicts found

2. SENTIMENT: bullish/neutral/bearish
   - BULLISH only if verified positive catalysts
   - BEARISH only if verified negative metrics
   - NEUTRAL if insufficient verification or mixed signals

3. RECOMMENDATION: BUY/HOLD/SELL
   - BUY: Score 70+, verified positive catalyst, good technicals
   - HOLD: Score 40-70, or mixed signals
   - SELL: Score <40 or verified negative fundamentals

4. REASONING: Explain exactly which verified facts led to this verdict
   - Reference specific verified data points
   - Note any unverified claims you had to ignore
   - Flag any temporal issues (old data, recent changes)
   - Mention any conflicts between different data sources

5. CONFIDENCE: Your confidence in this verdict (0-1)
   - Based on verification quality
   - Lower if many unverified claims
   - Lower if conflicts found

6. FLAGS: Any red flags or issues to highlight
   - Unverified critical claims
   - Data conflicts
   - Temporal currency issues
   - Unusual patterns

================================================================================
OUTPUT FORMAT
================================================================================

Provide your verdict in JSON format:

{{
    "score": <number 0-100>,
    "sentiment": "<bullish|neutral|bearish>",
    "recommendation": "<BUY|HOLD|SELL>",
    "summary": "<one-line summary of verdict>",
    "reasoning": "<detailed explanation using ONLY verified facts>",
    "confidence": <number 0-1>,
    "data_used": [
        "<list of verified data points that influenced decision>"
    ],
    "ignored_unverified": [
        "<list of unverified claims that were ignored>"
    ],
    "temporal_notes": "<any notes about data currency or timing>",
    "flags": [
        "<list of red flags or issues>"
    ]
}}

================================================================================
Remember: Your job is to be MORE CONSERVATIVE and flag uncertainties.
If data is unverified, SAY SO. If there are conflicts, HIGHLIGHT THEM.
Better to be cautious than to be wrong.
================================================================================
"""

        return prompt

    def _call_claude(self, prompt: str) -> str:
        """Call Claude API to generate verdict"""
        try:
            # Try using Claude via subprocess (claude CLI)
            result = subprocess.run(
                ['claude', 'message', prompt],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                return result.stdout.strip()

            # Fallback to direct API if available
            logger.warning("Claude CLI failed, trying API mode")
            return self._call_claude_api(prompt)

        except Exception as e:
            logger.error(f"Error calling Claude: {e}")
            # Return a safe default verdict (will be handled as fallback)
            return self._default_verdict()

    def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API directly if API key is available"""
        try:
            import anthropic

            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                return self._default_verdict()

            client = anthropic.Anthropic(api_key=api_key)

            message = client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            return message.content[0].text

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            return self._default_verdict()

    def _default_verdict(self) -> str:
        """Return a safe default verdict when Claude unavailable"""
        return json.dumps({
            "score": 50,
            "sentiment": "neutral",
            "recommendation": "HOLD",
            "summary": "Insufficient verified data for confident verdict",
            "reasoning": "Could not verify enough data points to make a confident recommendation",
            "confidence": 0.3,
            "data_used": [],
            "ignored_unverified": ["Most claims could not be verified"],
            "temporal_notes": "Data verification failed",
            "flags": ["Verdict system unavailable - conservative approach taken"],
            "verdict_source": "fallback"
        })

    def _parse_verdict_response(self, response: str, ticker: str) -> Dict[str, Any]:
        """Parse Claude's JSON response"""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse Claude response as JSON for {ticker}")

        # Fallback to safe defaults (mark as fallback so blended confidence is used)
        return {
            'score': 50,
            'sentiment': 'neutral',
            'recommendation': 'HOLD',
            'summary': 'Data verification incomplete',
            'reasoning': response[:500],  # Use first 500 chars as reasoning
            'confidence': 0.4,
            'flags': ['Response parsing failed - conservative approach taken'],
            'verdict_source': 'fallback'  # Mark as fallback to use blended confidence
        }

    def _extract_verified_data(self, verification_results: Dict) -> List[Dict]:
        """Extract verified data points from verification results"""
        verifications = verification_results.get('verifications', [])
        return [v for v in verifications if v.get('verification_status') == 'VERIFIED']

    def _extract_unverified_data(self, verification_results: Dict) -> List[Dict]:
        """Extract unverified data points"""
        verifications = verification_results.get('verifications', [])
        return [v for v in verifications if v.get('verification_status') in ['UNVERIFIED', 'PARTIALLY_VERIFIED']]

    def _format_verified_data(self, verified_data: List[Dict]) -> str:
        """Format verified data for prompt"""
        if not verified_data:
            return "No data could be verified through web search"

        formatted = []
        for item in verified_data:
            formatted.append(
                f"✅ {item.get('field_name')}: {item.get('claimed_value')} "
                f"(Verified: {item.get('verified_value')}, Confidence: {item.get('confidence'):.0%})"
            )
        return "\n".join(formatted)

    def _format_unverified_data(self, unverified_data: List[Dict]) -> str:
        """Format unverified data for prompt"""
        if not unverified_data:
            return "All data could be verified"

        formatted = []
        for item in unverified_data:
            formatted.append(
                f"⚠️  {item.get('field_name')}: {item.get('claimed_value')} "
                f"(Status: {item.get('verification_status')})"
            )
        return "\n".join(formatted)

    def _format_conflicts(self, verification_results: Dict) -> str:
        """Format data conflicts"""
        verifications = verification_results.get('verifications', [])
        conflicts = [v for v in verifications if v.get('verification_status') == 'CONFLICTING']

        if not conflicts:
            return "No conflicts detected in data"

        formatted = []
        for conflict in conflicts:
            formatted.append(
                f"🚨 {conflict.get('field_name')}: "
                f"Claimed {conflict.get('claimed_value')} "
                f"but found {conflict.get('verified_value')} "
                f"({conflict.get('discrepancy')})"
            )
        return "\n".join(formatted)

    def _format_catalysts(self, analysis_data: Dict) -> str:
        """Format catalysts from analysis"""
        catalysts = analysis_data.get('catalysts', [])
        if not catalysts:
            return "No specific catalysts identified"

        return "\n".join([f"- {cat}" for cat in catalysts])

    def _identify_verified_data(self, verification_results: Dict) -> List[str]:
        """Identify which data points were verified"""
        verified = self._extract_verified_data(verification_results)
        return [v.get('field_name', '') for v in verified if v]

    def _identify_unverified_data(self, verification_results: Dict) -> List[str]:
        """Identify which data points were NOT verified"""
        unverified = self._extract_unverified_data(verification_results)
        return [v.get('field_name', '') for v in unverified if v]

    def _calculate_confidence(self, verification_results: Dict) -> float:
        """
        Calculate overall confidence based on verification quality.
        Be HONEST about unverified data - don't artificially boost confidence.
        """
        conf = verification_results.get('confidence_score', 0.5)
        verified_count = verification_results.get('verified_count', 0)
        unverified_count = verification_results.get('unverified_count', 0)
        no_data_count = verification_results.get('no_data_found', 0)
        total_count = verification_results.get('verification_count', 0)

        # If no verifications were performed, return conservative confidence
        if total_count == 0:
            logger.warning("⚠️  No verification data available - returning low confidence")
            return 0.3  # Be honest: can't verify anything

        # Calculate verification ratio
        verified_ratio = verified_count / max(total_count, 1)
        unverified_ratio = (unverified_count + no_data_count) / max(total_count, 1)

        # Penalize heavily for unverified data
        # Formula: verified_ratio * base_conf, heavily penalized by unverified_ratio
        base_result = conf * verified_ratio
        penalty = 1.0 - (unverified_ratio * 0.5)  # Penalty proportional to unverified data
        result = base_result * penalty

        # Minimum: 0.2 (can make recommendations but with low confidence)
        # Maximum: 0.9 (never 100% confident without complete verification)
        final_confidence = min(0.9, max(0.2, result))

        logger.info(f"   Confidence calculation: {verified_count}/{total_count} verified → {final_confidence:.0%}")
        return final_confidence

    def _assess_temporal_currency(self, verification_results: Dict) -> str:
        """Assess how current the verified data is"""
        verifications = verification_results.get('verifications', [])

        if not verifications:
            return "Unknown - no verification performed"

        # Check publication dates
        from datetime import datetime, timedelta

        recent_count = 0
        for v in verifications:
            pub_dates = v.get('publication_dates', [])
            if pub_dates:
                try:
                    latest_date = max(pub_dates)
                    pub_datetime = datetime.fromisoformat(latest_date)
                    if datetime.now() - pub_datetime < timedelta(hours=48):
                        recent_count += 1
                except:
                    pass

        recent_ratio = recent_count / max(len(verifications), 1)

        if recent_ratio >= 0.8:
            return "🟢 CURRENT - Data verified within last 48 hours"
        elif recent_ratio >= 0.5:
            return "🟡 MOSTLY_CURRENT - Some data older than 48 hours"
        else:
            return "🔴 STALE - Data older than 48 hours, consider rechecking"


# Export main class
if __name__ == "__main__":
    engine = AIVerdictEngine()

    # Example usage
    test_analysis = {
        'ticker': 'SIEMENS',
        'ai_score': 48.8,
        'sentiment': 'bearish',
        'recommendation': 'HOLD',
        'catalysts': ['Q2 earnings (profit -7%)', 'Digital Industries weak'],
        'current_price': 3084.20,
        'price_timestamp': '2025-11-15T01:43:20',
        'rsi': 40.1,
        'momentum_10d': -1.38
    }

    test_verification = {
        'overall_assessment': 'TRUSTWORTHY',
        'confidence_score': 0.85,
        'verification_count': 3,
        'verified_count': 3,
        'unverified_count': 0,
        'conflicting_count': 0,
        'verifications': [
            {
                'field_name': 'Q2_profit',
                'claimed_value': 485,
                'verified_value': 485,
                'verification_status': 'VERIFIED',
                'confidence': 0.98,
                'publication_dates': ['2025-11-15']
            }
        ]
    }

    verdict = engine.generate_verdict('SIEMENS', test_analysis, test_verification)
    print(json.dumps(asdict(verdict), indent=2, default=str))
