#!/usr/bin/env python3
"""
AI-Driven Web Search Health Data Collector
==========================================

Dynamically collects real-time profit/loss, revenue, and financial health data
using Claude AI to generate search queries and extract insights.

NO hardcoding - completely flexible and works for any stock.

Features:
- AI generates optimal search queries for each stock
- Web searches for recent quarterly results
- AI extracts key metrics from search results
- AI analyzes profit health status dynamically
- Returns structured health data with sources
"""

import json
import logging
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
from datetime import datetime
import re

logger = logging.getLogger(__name__)


@dataclass
class HealthDataPoint:
    """Single health data point with source"""
    metric: str  # e.g., "quarterly_profit_loss", "revenue", "growth_rate"
    value: Optional[str]  # Actual value from source
    unit: str  # e.g., "%", "₹Cr", "USD"
    period: str  # e.g., "Q2 FY26", "FY 2025"
    confidence: float  # 0-1, how confident in this data
    source: str  # Where it came from
    is_recent: bool  # Is this data recent (last 3 months)?
    extracted_date: Optional[str]  # When was this data published


@dataclass
class StockHealthReport:
    """Complete health report for a stock - FOR INFORMATION ONLY, NOT FOR RANKING DECISIONS"""
    ticker: str
    company_name: str

    # Financial status
    is_profitable: Optional[bool]  # True/False/None
    latest_profit_loss: Optional[str]  # e.g., "₹29 Cr profit" or "Loss of ₹23.56 Cr"
    profit_loss_value: Optional[float]  # Numeric value in crores/millions
    profit_loss_currency: str  # "₹", "$"
    profit_loss_period: str  # Which quarter/year

    # Revenue data
    latest_revenue: Optional[str]  # e.g., "₹151 Cr"
    revenue_value: Optional[float]  # Numeric value
    revenue_currency: str  # "₹", "$"
    revenue_period: str  # Which quarter/year

    # Growth metrics
    yoy_revenue_growth: Optional[float]  # %, can be negative
    qoq_growth: Optional[float]  # %, can be negative

    # Data assessment (informational only)
    health_status: str  # "healthy", "warning", "critical" - FYI only
    health_reasoning: str  # Why this status - for context only

    # Consistency check
    consecutive_loss_quarters: int  # How many quarters with losses (informational)
    data_consistency: float  # 0-1, how consistent are the findings

    # Raw data
    all_data_points: List[HealthDataPoint]  # All extracted data points

    # Metadata
    collection_time: str
    ai_analysis: str  # AI's analysis - informational, not for scoring
    warning_flags: List[str]  # Flags for user awareness, NOT for penalizing score
    note: str = "IMPORTANT: Health data is for information only. AI decides final ranking considering news + financials."


class AIHealthDataCollector:
    """
    Uses Claude AI to dynamically collect and analyze stock health data.
    No hardcoding - all queries and extractions are AI-generated.
    """

    def __init__(self, ai_client=None):
        """
        Initialize collector with AI client

        Args:
            ai_client: Claude API client or bridge (e.g., claude_cli_bridge)
        """
        self.ai_client = ai_client
        self.search_function = self._default_web_search

    def set_search_function(self, search_func):
        """
        Allow custom web search function

        Args:
            search_func: Function that takes (query: str) -> str (search results)
        """
        self.search_function = search_func

    def _default_web_search(self, query: str) -> str:
        """Default web search using requests (can be overridden)"""
        import requests
        try:
            # Using DuckDuckGo as free alternative
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            url = f"https://html.duckduckgo.com/?q={query.replace(' ', '+')}"
            response = requests.get(url, headers=headers, timeout=10)
            return response.text[:2000]  # First 2000 chars
        except Exception as e:
            logger.warning(f"Web search failed for '{query}': {e}")
            return ""

    def collect_health_data(self, ticker: str, company_name: str = None) -> StockHealthReport:
        """
        Collect health data for a stock using AI-driven web search

        Args:
            ticker: Stock ticker (e.g., "BLACKBUCK", "IDEAFORGE")
            company_name: Optional company name for better searches

        Returns:
            StockHealthReport with all collected health data
        """
        logger.info(f"🔍 Starting AI-driven health data collection for {ticker}...")

        # Step 1: Generate search queries using AI
        search_queries = self._generate_search_queries(ticker, company_name)
        logger.info(f"  Generated {len(search_queries)} search queries")

        # Step 2: Execute web searches
        search_results = {}
        for query_type, query in search_queries.items():
            logger.info(f"  🔎 Searching: {query}")
            results = self.search_function(query)
            search_results[query_type] = results

        # Step 3: AI extracts key metrics from search results
        data_points = self._extract_metrics_with_ai(ticker, search_results)
        logger.info(f"  Extracted {len(data_points)} data points")

        # Step 4: AI analyzes health status
        health_analysis = self._analyze_health_with_ai(ticker, data_points)
        logger.info(f"  Health status: {health_analysis['status']}")

        # Step 5: Build report
        report = self._build_report(ticker, company_name, data_points, health_analysis)

        return report

    def _generate_search_queries(self, ticker: str, company_name: str = None) -> Dict[str, str]:
        """
        Use AI to generate optimal web search queries for the stock

        Returns:
            Dict of {query_type: search_query}
        """
        if not self.ai_client:
            return self._default_queries(ticker, company_name)

        # Build prompt for AI to generate queries
        prompt = f"""Generate optimal web search queries to find RECENT financial data for stock ticker {ticker}{f' ({company_name})' if company_name else ''}.

We need to find:
1. Latest quarterly profit/loss (Q1, Q2, Q3, Q4 results)
2. Recent revenue figures
3. Year-over-year growth rates
4. Financial health indicators
5. Number of consecutive loss quarters (if any)
6. Any recent analyst warnings or critical issues

Generate 6-8 specific, targeted search queries that will find this data.
Return as JSON with keys: quarterly_results, revenue, growth, analyst_outlook, etc.

Example format:
{{
  "quarterly_results": "TICKER Q2 FY26 quarterly results profit loss",
  "revenue": "TICKER latest quarterly revenue earnings",
  ...
}}

Replace TICKER with {ticker}."""

        try:
            # Call AI to generate queries
            response = self.ai_client.call_claude(prompt)

            # Parse JSON response
            queries = self._parse_json_response(response)
            if queries:
                return queries
        except Exception as e:
            logger.warning(f"AI query generation failed: {e}")

        # Fallback to default queries
        return self._default_queries(ticker, company_name)

    def _default_queries(self, ticker: str, company_name: str = None) -> Dict[str, str]:
        """Default queries if AI fails"""
        return {
            "quarterly_results": f"{ticker} Q2 FY26 quarterly results profit loss",
            "recent_earnings": f"{ticker} latest earnings net profit financial results 2025",
            "revenue": f"{ticker} quarterly revenue earnings recent",
            "yoy_growth": f"{ticker} year over year growth earnings revenue",
            "analyst_view": f"{ticker} analyst outlook financial health warning",
            "losses": f"{ticker} consecutive loss quarters declining revenue"
        }

    def _extract_metrics_with_ai(self, ticker: str, search_results: Dict[str, str]) -> List[HealthDataPoint]:
        """
        Use AI to extract key metrics from search results

        Returns:
            List of HealthDataPoint objects
        """
        if not self.ai_client:
            return self._extract_metrics_manually(ticker, search_results)

        # Build prompt for metric extraction
        search_summary = "\n\n".join([
            f"=== {query_type.upper()} ===\n{results[:1000]}"
            for query_type, results in search_results.items()
            if results
        ])

        prompt = f"""From the search results below for stock {ticker}, extract ALL financial health data points.

SEARCH RESULTS:
{search_summary}

Extract these metrics if present:
- Latest quarterly profit/loss amount and period
- Latest revenue and period
- YoY growth percentage
- QoQ growth percentage
- Financial health status
- Number of consecutive loss quarters
- Any critical warnings

Return as JSON with array of data points:
{{
  "data_points": [
    {{
      "metric": "quarterly_profit_loss",
      "value": "29",  // numeric only
      "unit": "₹Cr",
      "period": "Q2 FY26",
      "confidence": 0.95,  // 0-1
      "source": "trendlyne.com",
      "is_recent": true,
      "extracted_date": "2025-11-15"
    }},
    ...
  ]
}}

Be strict: only include data you found in search results. Use confidence 0.5-1.0.
Do NOT invent data. Return [] if no relevant data found."""

        try:
            response = self.ai_client.call_claude(prompt)
            parsed = self._parse_json_response(response)

            if parsed and "data_points" in parsed:
                return [HealthDataPoint(**dp) for dp in parsed["data_points"]]
        except Exception as e:
            logger.warning(f"AI metric extraction failed: {e}")

        return self._extract_metrics_manually(ticker, search_results)

    def _extract_metrics_manually(self, ticker: str, search_results: Dict[str, str]) -> List[HealthDataPoint]:
        """Fallback: manually extract metrics from search results with enhanced patterns"""
        data_points = []

        # Enhanced pattern matching for common metrics
        for query_type, results in search_results.items():
            if not results:
                continue

            # Look for profit/loss patterns (expanded for better matching)
            patterns = [
                (r"(?:net\s+)?profit[:\s]*₹?([\d.]+)\s*(?:Cr|crore|cr\b)", "₹Cr", "profit"),
                (r"loss[:\s]*₹?([\d.]+)\s*(?:Cr|crore|cr\b)", "₹Cr", "loss"),
                (r"net\s+loss[:\s]*(?:₹|Rs)?\s*([\d.]+)\s*(?:Cr|crore)", "₹Cr", "loss"),
                (r"revenue[:\s]*₹?([\d.]+)\s*(?:Cr|crore)", "₹Cr", "revenue"),
                (r"(?:growth|increased?)\s+([\d.]+)%", "%", "growth"),
                (r"([\d.]+)%\s+(?:growth|up)", "%", "growth"),
            ]

            for pattern, unit, metric_type in patterns:
                matches = re.findall(pattern, results, re.IGNORECASE)
                if matches:
                    for match in matches[:1]:  # Get first match
                        try:
                            data_points.append(HealthDataPoint(
                                metric=metric_type,
                                value=match,
                                unit=unit,
                                period="recent",
                                confidence=0.65,  # Higher confidence for actual data
                                source=query_type,
                                is_recent=True,
                                extracted_date=datetime.now().strftime("%Y-%m-%d")
                            ))
                        except Exception as e:
                            logger.debug(f"Failed to create data point: {e}")

        if data_points:
            logger.info(f"Extracted {len(data_points)} metrics from search results")
        return data_points

    def _analyze_health_with_ai(self, ticker: str, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """
        Use AI to analyze overall health status based on collected data

        Returns:
            Dict with: status, reasoning, risk_level, recommendations
        """
        if not self.ai_client:
            return self._analyze_health_manually(data_points)

        # Build data summary for AI
        data_summary = json.dumps([asdict(dp) for dp in data_points], indent=2)

        prompt = f"""Analyze the financial health of stock {ticker} based on these collected data points:

{data_summary}

Provide comprehensive health analysis:

1. Is the company profitable right now?
2. What is the profit/loss trend?
3. How many consecutive loss quarters?
4. Is revenue growing or declining?
5. What is the overall financial health status?
6. What are the key risk factors?
7. Should investors be warned?

Return JSON:
{{
  "status": "healthy|warning|critical",
  "is_profitable": true|false|null,
  "reasoning": "Detailed explanation...",
  "risk_level": "low|medium|high|critical",
  "consecutive_loss_quarters": 0,
  "data_consistency": 0.85,
  "ai_analysis": "Detailed AI analysis...",
  "warning_flags": ["flag1", "flag2"],
  "recommendations": ["rec1", "rec2"]
}}"""

        try:
            response = self.ai_client.call_claude(prompt)
            analysis = self._parse_json_response(response)
            if analysis:
                return analysis
        except Exception as e:
            logger.warning(f"AI health analysis failed: {e}")

        return self._analyze_health_manually(data_points)

    def _analyze_health_manually(self, data_points: List[HealthDataPoint]) -> Dict[str, Any]:
        """Fallback: manual health analysis"""
        loss_count = sum(1 for dp in data_points if dp.metric == "loss")
        profit_count = sum(1 for dp in data_points if dp.metric == "profit")

        return {
            "status": "critical" if loss_count > profit_count else "warning" if loss_count > 0 else "healthy",
            "is_profitable": profit_count > 0,
            "reasoning": f"Found {profit_count} profit(s) and {loss_count} loss(es)",
            "risk_level": "critical" if loss_count > profit_count else "medium" if loss_count > 0 else "low",
            "consecutive_loss_quarters": loss_count,
            "data_consistency": 0.6,
            "ai_analysis": "Manual analysis based on search results",
            "warning_flags": ["Needs AI verification"] if loss_count > 0 else [],
            "recommendations": ["Review latest quarterly results", "Check analyst reports"]
        }

    def _build_report(self, ticker: str, company_name: str, data_points: List[HealthDataPoint],
                     analysis: Dict[str, Any]) -> StockHealthReport:
        """Build final health report"""

        # Extract specific metrics
        profit_loss = next((dp for dp in data_points if dp.metric in ["profit", "loss"]), None)
        revenue = next((dp for dp in data_points if dp.metric == "revenue"), None)
        growth = next((dp for dp in data_points if dp.metric == "growth"), None)

        return StockHealthReport(
            ticker=ticker,
            company_name=company_name or ticker,
            is_profitable=analysis.get("is_profitable"),
            latest_profit_loss=f"{profit_loss.value} {profit_loss.unit}" if profit_loss else None,
            profit_loss_value=float(profit_loss.value) if profit_loss else None,
            profit_loss_currency="₹" if profit_loss and "₹" in profit_loss.unit else "$",
            profit_loss_period=profit_loss.period if profit_loss else "unknown",
            latest_revenue=f"{revenue.value} {revenue.unit}" if revenue else None,
            revenue_value=float(revenue.value) if revenue else None,
            revenue_currency="₹" if revenue and "₹" in revenue.unit else "$",
            revenue_period=revenue.period if revenue else "unknown",
            yoy_revenue_growth=float(growth.value) if growth else None,
            qoq_growth=None,
            health_status=analysis.get("status", "unknown"),
            health_reasoning=analysis.get("reasoning", ""),
            consecutive_loss_quarters=analysis.get("consecutive_loss_quarters", 0),
            data_consistency=analysis.get("data_consistency", 0.6),
            all_data_points=data_points,
            collection_time=datetime.now().isoformat(),
            ai_analysis=analysis.get("ai_analysis", ""),
            warning_flags=analysis.get("warning_flags", [])
        )

    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """Extract JSON from AI response"""
        try:
            # Try to find JSON in response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        return None


def main():
    """Example usage"""
    # This would be called from realtime_ai_news_analyzer.py
    print("AI Health Data Collector - Example Usage")
    print("=" * 50)

    # Initialize collector
    collector = AIHealthDataCollector()

    # Example: collect health data for a stock
    print("\nNote: Requires web search capability and Claude AI client")
    print("See integration example in realtime_ai_news_analyzer.py")


if __name__ == "__main__":
    main()
