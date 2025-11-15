#!/usr/bin/env python3
"""
Integration module to add AI health data collection to the analyzer.

Seamlessly integrates with realtime_ai_news_analyzer.py
"""

import logging
from ai_health_data_collector import AIHealthDataCollector, StockHealthReport
from typing import Optional, Callable

logger = logging.getLogger(__name__)


class HealthDataIntegration:
    """Integrates AI health data collection into the analysis pipeline"""

    def __init__(self, ai_client=None, web_search_func: Optional[Callable] = None):
        """
        Initialize integration

        Args:
            ai_client: Claude AI client for generating queries and analysis
            web_search_func: Custom web search function (optional)
        """
        self.collector = AIHealthDataCollector(ai_client)

        if web_search_func:
            self.collector.set_search_function(web_search_func)

        self.cache = {}  # Cache health reports by ticker

    def get_health_data(self, ticker: str, company_name: str = None,
                       use_cache: bool = True) -> Optional[StockHealthReport]:
        """
        Get health data for a stock

        Args:
            ticker: Stock ticker
            company_name: Optional company name
            use_cache: Use cached results if available

        Returns:
            StockHealthReport or None if collection fails
        """
        # Check cache
        if use_cache and ticker in self.cache:
            logger.info(f"📦 Using cached health data for {ticker}")
            return self.cache[ticker]

        # Collect fresh data
        try:
            logger.info(f"🔍 Collecting AI health data for {ticker}...")
            report = self.collector.collect_health_data(ticker, company_name)

            # Cache result
            self.cache[ticker] = report

            return report
        except Exception as e:
            logger.error(f"❌ Failed to collect health data for {ticker}: {e}")
            return None

    def update_analysis_with_health(self, analysis: dict, ticker: str) -> dict:
        """
        Update analysis result with health data

        Args:
            analysis: Original analysis dict
            ticker: Stock ticker

        Returns:
            Updated analysis dict with health data
        """
        health = self.get_health_data(ticker)

        if health:
            # Add health data to analysis
            analysis["health_data"] = {
                "is_profitable": health.is_profitable,
                "latest_profit_loss": health.latest_profit_loss,
                "profit_loss_period": health.profit_loss_period,
                "latest_revenue": health.latest_revenue,
                "revenue_period": health.revenue_period,
                "yoy_growth": health.yoy_revenue_growth,
                "health_status": health.health_status,
                "consecutive_loss_quarters": health.consecutive_loss_quarters,
                "data_consistency": health.data_consistency,
                "warning_flags": health.warning_flags,
                "collection_time": health.collection_time,
            }

            # Override potentially stale financial health status
            if health.health_status == "critical":
                analysis["override_health_status"] = "critical"
                analysis["critical_warning"] = f"{ticker} has critical financial health: {health.health_reasoning}"

            logger.info(f"✅ Added health data to {ticker} analysis")

        return analysis

    def generate_health_warning(self, ticker: str, analysis: dict) -> Optional[str]:
        """
        Generate warning message if health data shows issues

        Args:
            ticker: Stock ticker
            analysis: Analysis dict

        Returns:
            Warning message or None
        """
        health = self.get_health_data(ticker)

        if not health:
            return None

        warnings = []

        # Check for profitability issues
        if health.is_profitable is False:
            warnings.append(f"⚠️ {ticker} is currently unprofitable ({health.latest_profit_loss})")

        # Check for consecutive losses
        if health.consecutive_loss_quarters >= 3:
            warnings.append(f"🚨 {ticker} has {health.consecutive_loss_quarters} consecutive loss quarters")

        # Check for critical health
        if health.health_status == "critical":
            warnings.append(f"🚨 CRITICAL: {ticker} - {health.health_reasoning}")

        # Check for revenue decline
        if health.yoy_revenue_growth and health.yoy_revenue_growth < -50:
            warnings.append(f"🚨 {ticker} revenue collapsed {health.yoy_revenue_growth:.1f}% YoY")

        if warnings:
            return " | ".join(warnings)

        return None


def integrate_with_analyzer(analyzer, ai_client=None, web_search_func: Optional[Callable] = None):
    """
    Quick integration function to add health data collection to analyzer

    Usage in realtime_ai_news_analyzer.py:
    ```
    from health_data_integration import integrate_with_analyzer

    # In RealTimeAINewsAnalyzer.__init__:
    self.health_integration = integrate_with_analyzer(self, ai_client)

    # In analyze_ticker method:
    result = self.analyze_news_instant(...)
    result = self.health_integration.update_analysis_with_health(result, ticker)
    warning = self.health_integration.generate_health_warning(ticker, result)
    if warning:
        logger.info(f"HEALTH WARNING: {warning}")
    ```
    """
    return HealthDataIntegration(ai_client, web_search_func)


# Example usage for testing
if __name__ == "__main__":
    print("Health Data Integration Module")
    print("=" * 50)

    # Example: create integration
    integration = HealthDataIntegration()

    print("""
Usage:
------
from health_data_integration import integrate_with_analyzer

# In analyzer initialization:
self.health_integration = integrate_with_analyzer(self, ai_client)

# When analyzing a stock:
health_data = self.health_integration.get_health_data(ticker)
analysis = self.health_integration.update_analysis_with_health(analysis, ticker)
warning = self.health_integration.generate_health_warning(ticker, analysis)
""")
