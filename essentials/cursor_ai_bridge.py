#!/usr/bin/env python3
"""
Cursor AI Bridge - Real AI Analysis using Claude
Reads analysis prompt from stdin, uses Claude for deep analysis, returns JSON

This bridge ensures REAL AI is used for news analysis, not just heuristics.
"""

import sys
import json
import re
import os
from typing import Dict, List, Optional

def parse_analysis_prompt(prompt: str) -> Dict:
    """Extract key information from the analysis prompt."""
    info = {
        'ticker': 'UNKNOWN',
        'headline': '',
        'url': '',
        'snippet': '',
        'source': ''
    }
    
    # Extract ticker
    ticker_match = re.search(r'Ticker:\s*([A-Z]+)', prompt)
    if ticker_match:
        info['ticker'] = ticker_match.group(1)
    
    # Extract headline
    headline_match = re.search(r'Headline:\s*(.+?)(?:\n|$)', prompt)
    if headline_match:
        info['headline'] = headline_match.group(1).strip()
    
    # Extract URL
    url_match = re.search(r'(?:URL|Link):\s*(https?://[^\s\n]+)', prompt)
    if url_match:
        info['url'] = url_match.group(1)
    
    # Extract snippet
    snippet_match = re.search(r'Snippet:\s*(.+?)(?:\n\n|$)', prompt, re.DOTALL)
    if snippet_match:
        info['snippet'] = snippet_match.group(1).strip()
    
    # Extract source
    source_match = re.search(r'Source:\s*(.+?)(?:\n|$)', prompt)
    if source_match:
        info['source'] = source_match.group(1).strip()
    
    return info


def analyze_with_claude(prompt: str, info: Dict) -> Dict:
    """
    Use Claude (via Anthropic API) to deeply analyze the news.
    This is where REAL AI analysis happens.
    """
    try:
        import anthropic
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            return fallback_analysis(prompt, info, "No ANTHROPIC_API_KEY set")
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Build structured analysis prompt for Claude
        analysis_prompt = f"""You are an expert financial analyst specializing in Indian stock markets.

STRICT REAL-TIME GROUNDING:
- Base your analysis ONLY on the information supplied in this prompt. Do NOT use prior training data or external facts.
- PRIORITY: Treat CURRENT PRICE (if provided) as the anchor and compute entry zone, targets, and stop-loss FIRST before broader reasoning.

Analyze this news article and provide a structured assessment:

**Ticker:** {info['ticker']}
**Headline:** {info['headline']}
**Source:** {info['source']}
**Content:** {info['snippet']}

Provide your analysis in the following JSON format (no code blocks, just raw JSON):

{{
  "score": <0-100 integer>,
  "sentiment": "<bullish|bearish|neutral>",
  "impact": "<high|medium|low>",
  "catalysts": [<list of catalyst keywords like "earnings", "M&A", "contract", "expansion", etc>],
  "deal_value_cr": <deal value in crores if mentioned, else 0>,
  "risks": [<list of risk keywords>],
  "certainty": <0-100 integer for how confident you are>,
  "recommendation": "<STRONG BUY|BUY|ACCUMULATE|HOLD|SELL>",
  "reasoning": "<2-3 sentence explanation of your score and recommendation>",
  "expected_move_pct": <expected price move percentage, positive or negative>,
  "confidence": <0-100 integer>
}}

**Scoring Guidelines:**
- 90-100: Major confirmed catalyst (specific numbers, big deals, strategic moves)
- 75-89: Strong catalyst with good certainty (earnings beats, significant contracts)
- 60-74: Moderate catalyst (routine announcements, smaller deals)
- 40-59: Weak catalyst or speculation
- 0-39: Negative news or pure speculation

**Catalyst Detection:**
- "earnings" - quarterly results, profit growth
- "M&A" - mergers, acquisitions, strategic investments
- "contract" - new orders, client wins
- "expansion" - new plants, capacity addition
- "investment" - capex announcements
- "regulatory" - approvals, licenses
- "export" - international growth
- "technology" - innovation, R&D

**Assessment Factors:**
1. Deal magnitude vs company size
2. Specificity of numbers (actual figures = high certainty)
3. Source credibility
4. News recency
5. Market impact potential

Return ONLY valid JSON, no other text."""

        # Call Claude API
        message = client.messages.create(
            model=os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-4-20250514'),
            max_tokens=1000,
            messages=[{
                "role": "user",
                "content": analysis_prompt
            }]
        )
        
        # Extract JSON from response
        response_text = message.content[0].text.strip()
        
        # Remove code blocks if present
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text)
        response_text = re.sub(r'\s*```$', '', response_text)
        
        # Parse JSON
        result = json.loads(response_text)
        
        # Ensure all required fields
        result.setdefault('score', 50)
        result.setdefault('sentiment', 'neutral')
        result.setdefault('impact', 'medium')
        result.setdefault('catalysts', [])
        result.setdefault('deal_value_cr', 0)
        result.setdefault('risks', [])
        result.setdefault('certainty', 50)
        result.setdefault('recommendation', 'HOLD')
        result.setdefault('reasoning', 'Analysis complete')
        result.setdefault('expected_move_pct', 0)
        result.setdefault('confidence', result.get('certainty', 50))
        
        return result
        
    except ImportError:
        return fallback_analysis(prompt, info, "anthropic library not installed")
    except Exception as e:
        return fallback_analysis(prompt, info, f"Claude API error: {str(e)}")


def fallback_analysis(prompt: str, info: Dict, error_msg: str) -> Dict:
    """Fallback to intelligent heuristic analysis if AI unavailable."""
    print(f"⚠️  AI Analysis failed: {error_msg}, using enhanced heuristics", file=sys.stderr)
    
    text = (info['headline'] + ' ' + info['snippet']).lower()
    
    # Enhanced pattern matching
    score = 50
    sentiment = 'neutral'
    catalysts = []
    risks = []
    certainty = 40
    
    # Catalyst detection with scoring
    catalyst_patterns = {
        'earnings': ([r'q\d\s+(?:results|profit|earnings)', r'\d+%\s+(?:profit|revenue|growth)', r'pat\s+of', r'ebitda'], 15),
        'M&A': ([r'acquir', r'merger', r'buyout', r'stake', r'investment.*crore'], 20),
        'contract': ([r'order', r'contract', r'deal\s+worth', r'wins\s+.*\scrore'], 18),
        'expansion': ([r'expand', r'new\s+plant', r'capacity', r'facility'], 15),
        'export': ([r'export.*\d+%', r'overseas', r'international\s+sales'], 12),
        'regulatory': ([r'approval', r'license', r'clearance', r'nod'], 10),
        'investment': ([r'capex', r'invest.*crore', r'fund\s+raising'], 12),
        'technology': ([r'innovation', r'r&d', r'patent', r'tech\s+upgrade'], 10)
    }
    
    for catalyst, (patterns, points) in catalyst_patterns.items():
        if any(re.search(p, text) for p in patterns):
            catalysts.append(catalyst)
            score += points
    
    # Look for specific numbers (increases certainty)
    if re.search(r'₹\s*\d+(?:,\d+)*(?:\s+crore)?|\$\d+(?:\.\d+)?\s*(?:billion|million)', text):
        certainty += 20
        score += 10
    
    if re.search(r'\d+%\s+(?:rise|growth|increase|up)', text):
        certainty += 15
        score += 10
        sentiment = 'bullish'
    
    # Negative indicators
    negative_patterns = [
        r'loss', r'decline', r'down\s+\d+%', r'miss', r'weak', r'concern',
        r'investigation', r'penalty', r'lawsuit'
    ]
    for pattern in negative_patterns:
        if re.search(pattern, text):
            risks.append('negative_news')
            score -= 15
            sentiment = 'bearish'
    
    # Positive indicators
    positive_patterns = [
        r'beat.*estimate', r'strong', r'record', r'highest', r'leads\s+segment',
        r'surge', r'jumps', r'rallies'
    ]
    for pattern in positive_patterns:
        if re.search(pattern, text):
            score += 10
            sentiment = 'bullish'
    
    # Cap score
    score = max(0, min(100, score))
    certainty = max(20, min(95, certainty))
    
    # Determine recommendation
    if score >= 85 and sentiment == 'bullish':
        recommendation = 'STRONG BUY'
    elif score >= 70:
        recommendation = 'BUY'
    elif score >= 55:
        recommendation = 'ACCUMULATE'
    elif score >= 40:
        recommendation = 'HOLD'
    else:
        recommendation = 'WATCH'
    
    expected_move = 0
    if sentiment == 'bullish' and score >= 70:
        expected_move = (score - 50) / 5  # Rough estimate
    elif sentiment == 'bearish':
        expected_move = -(60 - score) / 5
    
    reasoning = f"Detected {len(catalysts)} catalyst(s). Score: {score}/100. Certainty: {certainty}%. {sentiment.upper()} sentiment."
    
    return {
        'score': score,
        'sentiment': sentiment,
        'impact': 'high' if score >= 75 else 'medium' if score >= 50 else 'low',
        'catalysts': catalysts,
        'deal_value_cr': 0,
        'risks': risks if risks else ['market_risk'],
        'certainty': certainty,
        'recommendation': recommendation,
        'reasoning': reasoning,
        'expected_move_pct': round(expected_move, 1),
        'confidence': certainty
    }


def main():
    """Main entry point - reads prompt from stdin, returns JSON to stdout."""
    prompt = sys.stdin.read()
    
    if not prompt.strip():
        print(json.dumps({
            'score': 50,
            'sentiment': 'neutral',
            'impact': 'medium',
            'catalysts': [],
            'deal_value_cr': 0,
            'risks': ['no_input'],
            'certainty': 30,
            'recommendation': 'HOLD',
            'reasoning': 'No analysis prompt provided',
            'expected_move_pct': 0,
            'confidence': 30
        }))
        return
    
    # Parse the prompt
    info = parse_analysis_prompt(prompt)
    
    # Analyze with Claude (or fallback to heuristics)
    result = analyze_with_claude(prompt, info)
    
    # Output JSON
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
