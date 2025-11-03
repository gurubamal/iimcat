#!/usr/bin/env python3
"""
Cursor CLI Bridge - Real AI Analysis using Cursor's Coding Agent
Reads analysis prompt from stdin, uses Cursor CLI agent, returns JSON

NO API KEYS NEEDED - Uses your existing Cursor installation!
"""

import sys
import json
import re
import os
import subprocess
from typing import Dict, Optional

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


def analyze_with_cursor_cli(prompt: str, info: Dict) -> Dict:
    """
    Use Cursor CLI agent to analyze the news.
    This calls the local Cursor agent - NO API KEYS NEEDED!
    """
    
    # Use cursor agent command (not just cursor)
    cursor_cmd = os.getenv('CURSOR_CLI_PATH', 'cursor')
    cursor_agent_cmd = [cursor_cmd, 'agent']
    
    # Build structured analysis prompt for Cursor agent
    analysis_prompt = f"""You are an expert financial analyst for Indian stock markets.

STRICT REAL-TIME GROUNDING:
- Base your analysis ONLY on the information supplied in this prompt. Do NOT use any prior training data or external facts.
- PRIORITY: Treat CURRENT PRICE (if provided) as the anchor and compute entry zone, targets, and stop-loss FIRST before broader reasoning.

Analyze this news article and provide a JSON response (no markdown, just raw JSON):

**Ticker:** {info['ticker']}
**Headline:** {info['headline']}
**Source:** {info['source']}
**Content:** {info['snippet']}

Return ONLY valid JSON in this exact format:

{{
  "score": <0-100 integer>,
  "sentiment": "<bullish|bearish|neutral>",
  "impact": "<high|medium|low>",
  "catalysts": [<list of catalyst keywords>],
  "deal_value_cr": <deal value in crores or 0>,
  "risks": [<list of risk keywords>],
  "certainty": <0-100 integer>,
  "recommendation": "<STRONG BUY|BUY|ACCUMULATE|HOLD|SELL>",
  "reasoning": "<brief explanation>",
  "expected_move_pct": <expected price move %>,
  "confidence": <0-100 integer>
}}

**Scoring Guidelines:**
- 90-100: Major confirmed catalyst (₹1000cr+ deals, strategic moves)
- 75-89: Strong catalyst (earnings beats, significant contracts)
- 60-74: Moderate catalyst (routine announcements)
- 40-59: Weak/speculation
- 0-39: Negative news

**Catalysts:** earnings, M&A, contract, expansion, investment, regulatory, export, technology

**Key Factors:**
1. Deal magnitude vs company size
2. Specificity (actual numbers = high certainty)
3. Source credibility
4. Market impact potential

Return ONLY the JSON object, no other text."""

    try:
        # Call Cursor agent via CLI
        print(f"🤖 Calling Cursor agent for {info['ticker']}...", file=sys.stderr)
        
        # Method 1: Try as command argument (preferred for cursor agent)
        result = subprocess.run(
            cursor_agent_cmd + [analysis_prompt],
            capture_output=True,
            text=True,
            timeout=60  # Increase timeout for agent
        )
        
        # Method 2: If that fails, try stdin
        if result.returncode != 0 or not result.stdout.strip():
            print(f"⚠️  Trying stdin method...", file=sys.stderr)
            result = subprocess.run(
                cursor_agent_cmd,
                input=analysis_prompt,
                capture_output=True,
                text=True,
                timeout=60
            )
        
        if result.returncode != 0:
            print(f"⚠️  Cursor agent error (code {result.returncode}): {result.stderr[:200]}", file=sys.stderr)
            return fallback_analysis(prompt, info, f"Agent error: {result.stderr[:100]}")
        
        response_text = result.stdout.strip()
        
        if not response_text:
            print(f"⚠️  Cursor CLI returned empty response", file=sys.stderr)
            return fallback_analysis(prompt, info, "Empty CLI response")
        
        # Extract JSON from response (handle markdown code blocks if present)
        response_text = re.sub(r'^```(?:json)?\s*', '', response_text, flags=re.MULTILINE)
        response_text = re.sub(r'\s*```$', '', response_text, flags=re.MULTILINE)
        
        # Try to find JSON object
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        # Parse JSON
        result_json = json.loads(response_text)
        
        # Ensure all required fields
        result_json.setdefault('score', 50)
        result_json.setdefault('sentiment', 'neutral')
        result_json.setdefault('impact', 'medium')
        result_json.setdefault('catalysts', [])
        result_json.setdefault('deal_value_cr', 0)
        result_json.setdefault('risks', [])
        result_json.setdefault('certainty', 50)
        result_json.setdefault('recommendation', 'HOLD')
        result_json.setdefault('reasoning', 'Analysis complete')
        result_json.setdefault('expected_move_pct', 0)
        result_json.setdefault('confidence', result_json.get('certainty', 50))
        
        print(f"✅ Cursor CLI analysis complete for {info['ticker']}", file=sys.stderr)
        return result_json
        
    except subprocess.TimeoutExpired:
        print(f"⚠️  Cursor CLI timeout", file=sys.stderr)
        return fallback_analysis(prompt, info, "CLI timeout")
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse Cursor response as JSON: {e}", file=sys.stderr)
        print(f"Response was: {response_text[:200]}", file=sys.stderr)
        return fallback_analysis(prompt, info, f"JSON parse error: {e}")
    except FileNotFoundError:
        print(f"⚠️  Cursor CLI not found at: {cursor_cmd}", file=sys.stderr)
        return fallback_analysis(prompt, info, "Cursor CLI not found")
    except Exception as e:
        print(f"⚠️  Cursor CLI error: {e}", file=sys.stderr)
        return fallback_analysis(prompt, info, f"CLI error: {str(e)}")


def fallback_analysis(prompt: str, info: Dict, error_msg: str) -> Dict:
    """Enhanced heuristic analysis as fallback."""
    print(f"⚠️  Using fallback heuristics: {error_msg}", file=sys.stderr)
    
    text = (info['headline'] + ' ' + info['snippet']).lower()
    
    score = 50
    sentiment = 'neutral'
    catalysts = []
    risks = []
    certainty = 40
    
    # Enhanced pattern matching
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
    
    # Specific numbers increase certainty
    if re.search(r'₹\s*\d+(?:,\d+)*(?:\s+crore)?|\$\d+(?:\.\d+)?\s*(?:billion|million)', text):
        certainty += 20
        score += 10
    
    if re.search(r'\d+%\s+(?:rise|growth|increase|up)', text):
        certainty += 15
        score += 10
        sentiment = 'bullish'
    
    # Negative indicators
    negative_patterns = [r'loss', r'decline', r'down\s+\d+%', r'miss', r'weak', r'concern']
    for pattern in negative_patterns:
        if re.search(pattern, text):
            risks.append('negative_news')
            score -= 15
            sentiment = 'bearish'
    
    # Positive indicators
    positive_patterns = [r'beat.*estimate', r'strong', r'record', r'highest', r'leads', r'surge', r'jumps']
    for pattern in positive_patterns:
        if re.search(pattern, text):
            score += 10
            sentiment = 'bullish'
    
    score = max(0, min(100, score))
    certainty = max(20, min(95, certainty))
    
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
        expected_move = (score - 50) / 5
    elif sentiment == 'bearish':
        expected_move = -(60 - score) / 5
    
    reasoning = f"Detected {len(catalysts)} catalyst(s). Score: {score}/100. Certainty: {certainty}%. {sentiment.upper()} sentiment. [Fallback: {error_msg}]"
    
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
    
    # Analyze with Cursor CLI (or fallback to heuristics)
    result = analyze_with_cursor_cli(prompt, info)
    
    # Output JSON
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
