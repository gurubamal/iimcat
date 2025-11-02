#!/usr/bin/env python3
"""
Claude Bridge - Simple Claude Analysis WITHOUT Direct API Calls
Uses the `anthropic` Python library (cleaner than raw API)

Usage:
    echo '{"prompt": "Analyze RELIANCE stock news..."}' | python3 claude_bridge.py

    OR as shell command:
    export AI_SHELL_CMD="python3 claude_bridge.py"
    export ANTHROPIC_API_KEY="sk-ant-xxxxx"
    python3 realtime_ai_news_analyzer.py --ai-provider codex
"""

import sys
import json
import os
import re
from typing import Dict, Optional

def analyze_with_anthropic_library(prompt: str) -> Dict:
    """
    Use Anthropic's Python library (cleaner than REST API calls)
    Falls back to heuristic if library not available
    """
    try:
        import anthropic
    except ImportError:
        return fallback_heuristic(prompt, "anthropic library not installed. Run: pip install anthropic")

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        return fallback_heuristic(prompt, "ANTHROPIC_API_KEY not set")

    try:
        client = anthropic.Anthropic(api_key=api_key)

        model = os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20240620')
        temperature = float(os.getenv('ANTHROPIC_TEMPERATURE', '0.2'))
        max_tokens = int(os.getenv('ANTHROPIC_MAX_TOKENS', '1200'))

        # Call Claude using the library (much cleaner than REST!)
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system="""You are an expert Indian equity analyst specializing in swing trading.

CRITICAL CALIBRATION RULES:
1. Use the FULL scoring range (20-95) - don't default to 30-40 scores
2. Confirmed news from tier-1 sources = 70-85 scores (not 33)
3. Tier-1 English sources = 60-80% certainty (not 30%)
4. Growth/profit/investment news = "bullish" sentiment (not "neutral")
5. Always identify catalysts - never say "None"
6. Consider indirect sector/supply chain impacts
7. 75+ scores → "BUY" recommendations (not "HOLD")

Return valid JSON only with realistic, well-calibrated scores.""",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract text from response
        response_text = message.content[0].text if message.content else "{}"

        # Parse JSON response
        response_text = response_text.strip()

        # Strip markdown code blocks if present
        if response_text.startswith('```'):
            response_text = re.sub(r'^```(?:json)?\n', '', response_text)
            response_text = re.sub(r'\n```$', '', response_text)

        result = json.loads(response_text)

        # Ensure required fields
        if 'score' not in result:
            result['score'] = 50
        if 'certainty' not in result:
            result['certainty'] = 50
        if 'sentiment' not in result:
            result['sentiment'] = 'neutral'

        # Log successful AI usage
        print(f"✅ Claude ({model}) analysis complete", file=sys.stderr)

        return result

    except anthropic.APIError as e:
        return fallback_heuristic(prompt, f"Anthropic API error: {e}")
    except json.JSONDecodeError as e:
        return fallback_heuristic(prompt, f"Invalid JSON from Claude: {e}")
    except Exception as e:
        return fallback_heuristic(prompt, f"Unexpected error: {e}")


def fallback_heuristic(prompt: str, reason: str) -> Dict:
    """
    Fallback to pattern-based heuristic analysis
    """
    print(f"⚠️  Falling back to heuristic: {reason}", file=sys.stderr)

    # Extract key information from prompt
    score = 40
    certainty = 30
    sentiment = 'neutral'

    # Simple pattern matching
    prompt_lower = prompt.lower()

    # Positive signals
    if any(word in prompt_lower for word in ['profit', 'growth', 'record', 'high', 'surge', 'jump']):
        score += 20
        sentiment = 'bullish'

    # Negative signals
    if any(word in prompt_lower for word in ['loss', 'decline', 'fall', 'drop', 'weak']):
        score -= 15
        sentiment = 'bearish'

    # Confirmation words increase certainty
    if any(word in prompt_lower for word in ['reported', 'announced', 'confirmed', 'signed']):
        certainty += 20

    # Speculation words decrease certainty
    if any(word in prompt_lower for word in ['may', 'might', 'could', 'plans', 'expects']):
        certainty -= 15

    # Extract magnitude if present
    magnitude = 0
    magnitude_match = re.search(r'₹?\s*(\d+(?:,\d+)*)\s*(?:cr|crore|lakh)', prompt_lower)
    if magnitude_match:
        magnitude_str = magnitude_match.group(1).replace(',', '')
        magnitude = int(magnitude_str)
        if magnitude >= 100:
            score += 10
            certainty += 10

    # Clamp values
    score = max(0, min(100, score))
    certainty = max(0, min(100, certainty))

    return {
        'score': score,
        'certainty': certainty,
        'sentiment': sentiment,
        'impact': 'medium' if score > 50 else 'low',
        'catalysts': [],
        'reasoning': f'Heuristic analysis (fallback): {reason}',
        'price_targets': [],
        'expected_rise_min': 0,
        'expected_rise_max': 0,
        'fake_rally_risk': 'Unknown'
    }


def main():
    """
    Main entry point - reads prompt from stdin or args
    Returns JSON to stdout
    """
    # Read input
    if len(sys.argv) > 1:
        # From command line argument
        input_data = ' '.join(sys.argv[1:])
    else:
        # From stdin (pipe)
        input_data = sys.stdin.read()

    # Parse input JSON if it's JSON, otherwise treat as raw prompt
    try:
        input_json = json.loads(input_data)
        prompt = input_json.get('prompt', input_data)
    except json.JSONDecodeError:
        prompt = input_data

    # Analyze using Claude (via anthropic library)
    result = analyze_with_anthropic_library(prompt)

    # Output JSON
    print(json.dumps(result, indent=2))

    return 0


if __name__ == '__main__':
    sys.exit(main())
