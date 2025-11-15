#!/usr/bin/env python3
"""
Claude AI Client for Health Data Collection

Provides Claude API integration for:
1. Generating dynamic web search queries
2. Extracting metrics from search results
3. Analyzing financial health
"""

import logging
import json
import os
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ClaudeHealthAIClient:
    """
    Wrapper around Claude API for health data collection.

    Supports both:
    - Direct API calls (via ANTHROPIC_API_KEY)
    - CLI bridge (via claude command)
    """

    def __init__(self, api_key: Optional[str] = None, use_cli: bool = False):
        """
        Initialize Claude client

        Args:
            api_key: Anthropic API key (auto-loaded from env if not provided)
            use_cli: Use claude CLI instead of API
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.use_cli = use_cli
        # Use simple model name for CLI, full ID for API
        self.model = os.getenv('CLAUDE_CLI_MODEL', 'sonnet') if use_cli else "claude-3-5-sonnet-20241022"

        if use_cli:
            self._init_cli_client()
        else:
            self._init_api_client()

    def _init_cli_client(self):
        """Initialize Claude CLI client"""
        try:
            import subprocess
            result = subprocess.run(['claude', '--version'], capture_output=True)
            if result.returncode == 0:
                logger.info("✅ Claude CLI available")
                self.cli_available = True
            else:
                logger.warning("⚠️  Claude CLI not available - falling back to API")
                self.cli_available = False
        except:
            self.cli_available = False

    def _init_api_client(self):
        """Initialize Anthropic API client"""
        if not self.api_key:
            logger.warning("⚠️  ANTHROPIC_API_KEY not set - health data collection disabled")
            return

        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info("✅ Anthropic API client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Anthropic client: {e}")
            self.client = None

    def call_claude(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """
        Call Claude with a prompt

        Args:
            prompt: The prompt to send
            max_tokens: Maximum tokens in response

        Returns:
            Claude's response or None
        """
        if self.use_cli and self.cli_available:
            return self._call_cli(prompt, max_tokens)
        elif hasattr(self, 'client') and self.client:
            return self._call_api(prompt, max_tokens)
        else:
            logger.error("No Claude client available")
            return None

    def _call_api(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Call via Anthropic API"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            return message.content[0].text
        except Exception as e:
            logger.error(f"❌ API call failed: {e}")
            return None

    def _call_cli(self, prompt: str, max_tokens: int = 2000) -> Optional[str]:
        """Call via Claude CLI using stdin for long prompts"""
        import subprocess
        import sys

        try:
            # Build command with correct Claude CLI syntax
            cmd = [
                'claude',
                '--print',  # Non-interactive mode
                '--output-format', 'text',  # Text output
                '--model', self.model,
            ]

            # Call Claude CLI with prompt via stdin (for long prompts)
            result = subprocess.run(
                cmd,
                input=prompt,  # Pass prompt via stdin
                capture_output=True,
                text=True,
                timeout=90  # Increased timeout for web search data
            )

            # Check return code
            if result.returncode != 0:
                stderr_msg = result.stderr.strip() if result.stderr else "No error output"
                stdout_msg = result.stdout.strip() if result.stdout else "No stdout"
                logger.warning(f"Claude CLI returned {result.returncode}: {stderr_msg[:100]} | stdout: {stdout_msg[:100]}")
                return None

            # Return the output, stripping whitespace
            output = result.stdout.strip()
            if not output:
                logger.warning("Claude CLI returned empty output")
                return None

            return output

        except subprocess.TimeoutExpired:
            logger.error(f"Claude CLI call timed out after 90s")
            return None
        except FileNotFoundError:
            logger.error("Claude CLI not found - make sure it's installed and in PATH")
            return None
        except Exception as e:
            logger.error(f"Claude CLI call failed: {str(e)[:200]}")
            return None

    def generate_search_queries(self, ticker: str, company_name: str = None) -> Optional[Dict[str, str]]:
        """
        Generate optimal web search queries for a stock

        Returns:
            Dict of {query_type: query_string}
        """
        prompt = f"""Generate 6-8 optimal web search queries to find recent financial data for stock {ticker}{f' ({company_name})' if company_name else ''}.

Find:
1. Latest quarterly profit/loss
2. Recent revenue
3. YoY growth rates
4. Financial health
5. Loss history

Return ONLY valid JSON (no markdown, no explanation):
{{
  "quarterly_results": "...",
  "revenue": "...",
  "yoy_growth": "...",
  "analyst_outlook": "...",
  "losses": "...",
  "fundamentals": "..."
}}"""

        response = self.call_claude(prompt, max_tokens=500)
        if response:
            try:
                # Parse JSON
                data = json.loads(response)
                logger.info(f"✅ Generated {len(data)} search queries for {ticker}")
                return data
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse queries response: {response[:200]}")

        return None

    def extract_metrics(self, ticker: str, search_results: Dict[str, str]) -> Optional[list]:
        """
        Extract financial metrics from search results

        Returns:
            List of extracted data points
        """
        # Build search summary
        summary = "\n\n".join([
            f"=== {k.upper()} ===\n{v[:500]}"
            for k, v in search_results.items() if v
        ])

        prompt = f"""Extract ALL financial metrics from search results for {ticker}.

SEARCH RESULTS:
{summary}

Return ONLY valid JSON with data points:
{{
  "data_points": [
    {{
      "metric": "profit_loss",
      "value": "29",
      "unit": "₹Cr",
      "period": "Q2 FY26",
      "confidence": 0.95,
      "source": "source_name",
      "is_recent": true
    }}
  ]
}}"""

        response = self.call_claude(prompt, max_tokens=1000)
        if response:
            try:
                data = json.loads(response)
                logger.info(f"✅ Extracted {len(data.get('data_points', []))} metrics for {ticker}")
                return data.get('data_points', [])
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse metrics response")

        return []

    def analyze_health(self, ticker: str, data_points: list) -> Optional[Dict[str, Any]]:
        """
        Analyze overall financial health

        Returns:
            Health analysis dict
        """
        # Build data summary
        summary = json.dumps(data_points, indent=2)

        prompt = f"""Analyze financial health of {ticker} based on:

{summary}

Determine:
1. Is it profitable?
2. Profit/loss trend?
3. Consecutive loss quarters?
4. Revenue trend?
5. Overall health status?
6. Risk factors?

Return ONLY valid JSON:
{{
  "status": "healthy|warning|critical",
  "is_profitable": true|false|null,
  "reasoning": "...",
  "consecutive_loss_quarters": 0,
  "data_consistency": 0.85,
  "risk_level": "low|medium|high|critical",
  "warning_flags": ["flag1"],
  "ai_analysis": "..."
}}"""

        response = self.call_claude(prompt, max_tokens=800)
        if response:
            try:
                analysis = json.loads(response)
                logger.info(f"✅ Health analysis for {ticker}: {analysis.get('status')}")
                return analysis
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse health analysis response")

        return None


def create_client(use_cli: bool = False, api_key: Optional[str] = None) -> Optional[ClaudeHealthAIClient]:
    """
    Create Claude health AI client

    Args:
        use_cli: Use CLI instead of API
        api_key: API key (auto-loaded if not provided)

    Returns:
        ClaudeHealthAIClient or None if no Claude available
    """
    try:
        return ClaudeHealthAIClient(api_key=api_key, use_cli=use_cli)
    except Exception as e:
        logger.error(f"Failed to create Claude client: {e}")
        return None


# Example usage
if __name__ == "__main__":
    print("Claude Health AI Client")
    print("=" * 50)

    # Create client - will auto-detect available method
    client = create_client(use_cli=True)  # Prefer CLI if available

    if client:
        print("✅ Client ready")
        print("\nMethods:")
        print("  - generate_search_queries(ticker)")
        print("  - extract_metrics(ticker, search_results)")
        print("  - analyze_health(ticker, data_points)")
    else:
        print("❌ No Claude client available")
