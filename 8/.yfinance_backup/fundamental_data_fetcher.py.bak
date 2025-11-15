#!/usr/bin/env python3
"""
FUNDAMENTAL DATA FETCHER - Comprehensive Financial Analysis
===========================================================
Fetches quarterly/annual results, institutional ownership, financial health.
Uses yfinance for recent data, allows training data for historical context.

Key Features:
- Quarterly results (Q-o-Q and Y-o-Y growth)
- Annual results (Y-o-Y comparison)
- Institutional ownership changes
- Financial health validation (profitability, net worth)
- No IP blocking (rate-limited, cached)
"""

import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import pandas as pd
import time
import json
import os

# Cache to avoid repeated requests (opt-in via env)
CACHE_FILE = 'fundamental_data_cache.json'
CACHE_DURATION_HOURS = 24
ALLOW_FUNDAMENTAL_CACHE = os.getenv('ALLOW_FUNDAMENTAL_CACHE', '0').strip() == '1'

class FundamentalDataFetcher:
    """
    Fetches comprehensive fundamental data from yfinance.
    """

    def __init__(self, use_cache: bool = False):
        self.use_cache = bool(use_cache and ALLOW_FUNDAMENTAL_CACHE)
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        """Load cache from disk."""
        if not self.use_cache or not os.path.exists(CACHE_FILE):
            return {}

        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_cache(self):
        """Save cache to disk."""
        if not self.use_cache:
            return

        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    def _is_cache_valid(self, ticker: str) -> bool:
        """Check if cached data is still valid."""
        if not self.use_cache:
            return False
        if ticker not in self.cache:
            return False

        cache_time = self.cache[ticker].get('fetch_time')
        if not cache_time:
            return False

        cache_dt = datetime.fromisoformat(cache_time)
        age_hours = (datetime.now() - cache_dt).total_seconds() / 3600

        return age_hours < CACHE_DURATION_HOURS

    def fetch_comprehensive_fundamentals(self, ticker: str) -> Dict:
        """
        Main function: Fetch ALL fundamental data for a ticker.

        Returns comprehensive dictionary with:
        - Quarterly financials (Q-o-Q, Y-o-Y)
        - Annual financials (Y-o-Y)
        - Institutional ownership
        - Financial health metrics
        - Validation flags
        """

        # Check cache first
        if self._is_cache_valid(ticker):
            print(f"  Using cached fundamental data for {ticker}")
            return self.cache[ticker]['data']

        print(f"  Fetching fundamental data for {ticker}...")

        result = {
            'ticker': ticker,
            'fetch_time': datetime.now().isoformat(),
            'quarterly': {},
            'annual': {},
            'institutional': {},
            'financial_health': {},
            'validation': {},
            'data_available': False
        }

        try:
            ticker_obj = yf.Ticker(f"{ticker}.NS")

            # Fetch all data types
            result['quarterly'] = self._fetch_quarterly_data(ticker_obj)
            time.sleep(0.5)  # Rate limiting

            result['annual'] = self._fetch_annual_data(ticker_obj)
            time.sleep(0.5)

            result['institutional'] = self._fetch_institutional_data(ticker_obj)
            time.sleep(0.5)

            result['financial_health'] = self._fetch_financial_health(ticker_obj)
            time.sleep(0.5)

            result['validation'] = self._validate_financial_health(result)

            result['data_available'] = True

            # Cache the result (optional)
            if self.use_cache:
                self.cache[ticker] = {
                    'fetch_time': result['fetch_time'],
                    'data': result
                }
                self._save_cache()

        except Exception as e:
            print(f"    Warning: Could not fetch fundamental data for {ticker}: {e}")
            result['error'] = str(e)

        return result

    def _fetch_quarterly_data(self, ticker_obj) -> Dict:
        """
        Fetch quarterly financial data and calculate growth rates.

        Returns:
        - Most recent quarter results
        - Q-o-Q growth % (vs previous quarter)
        - Y-o-Y growth % (vs same quarter last year)
        """

        result = {
            'data_available': False,
            'most_recent_quarter': None,
            'previous_quarter': None,
            'same_quarter_last_year': None,
            'revenue_qoq_growth_pct': None,
            'revenue_yoy_growth_pct': None,
            'earnings_qoq_growth_pct': None,
            'earnings_yoy_growth_pct': None,
            'profit_margin_pct': None,
            'quarters_available': 0
        }

        try:
            # Get quarterly financials
            quarterly_income = ticker_obj.quarterly_financials

            if quarterly_income is None or quarterly_income.empty:
                return result

            # Transpose for easier access (dates as rows)
            quarterly_income = quarterly_income.T
            quarters_available = len(quarterly_income)
            result['quarters_available'] = quarters_available

            if quarters_available == 0:
                return result

            # Get the most recent quarter (index 0)
            most_recent = quarterly_income.iloc[0]
            result['most_recent_quarter'] = most_recent.name.strftime('%Y-%m-%d')

            # Extract revenue and earnings
            revenue_current = self._safe_get(most_recent, ['Total Revenue', 'TotalRevenue'])
            earnings_current = self._safe_get(most_recent, ['Net Income', 'NetIncome'])

            # Q-o-Q comparison (vs previous quarter)
            if quarters_available >= 2:
                previous_quarter = quarterly_income.iloc[1]
                result['previous_quarter'] = previous_quarter.name.strftime('%Y-%m-%d')

                revenue_previous = self._safe_get(previous_quarter, ['Total Revenue', 'TotalRevenue'])
                earnings_previous = self._safe_get(previous_quarter, ['Net Income', 'NetIncome'])

                if (revenue_current is not None and revenue_previous is not None
                        and revenue_previous != 0):
                    result['revenue_qoq_growth_pct'] = ((revenue_current - revenue_previous) / abs(revenue_previous)) * 100

                if (earnings_current is not None and earnings_previous is not None
                        and earnings_previous != 0):
                    result['earnings_qoq_growth_pct'] = ((earnings_current - earnings_previous) / abs(earnings_previous)) * 100

            # Y-o-Y comparison (vs same quarter last year - typically 4 quarters back)
            if quarters_available >= 5:
                same_quarter_ly = quarterly_income.iloc[4]
                result['same_quarter_last_year'] = same_quarter_ly.name.strftime('%Y-%m-%d')

                revenue_ly = self._safe_get(same_quarter_ly, ['Total Revenue', 'TotalRevenue'])
                earnings_ly = self._safe_get(same_quarter_ly, ['Net Income', 'NetIncome'])

                if revenue_current is not None and revenue_ly is not None and revenue_ly != 0:
                    result['revenue_yoy_growth_pct'] = ((revenue_current - revenue_ly) / abs(revenue_ly)) * 100

                if (earnings_current is not None and earnings_ly is not None
                        and earnings_ly != 0):
                    result['earnings_yoy_growth_pct'] = ((earnings_current - earnings_ly) / abs(earnings_ly)) * 100

            # Calculate profit margin
            if (revenue_current is not None and earnings_current is not None
                    and revenue_current != 0):
                result['profit_margin_pct'] = (earnings_current / revenue_current) * 100

            result['data_available'] = True

        except Exception as e:
            print(f"    Warning: Quarterly data fetch failed: {e}")
            result['error'] = str(e)

        return result

    def _fetch_annual_data(self, ticker_obj) -> Dict:
        """
        Fetch annual financial data and calculate Y-o-Y growth.

        Returns:
        - Most recent year results
        - Y-o-Y growth % (vs previous year)
        """

        result = {
            'data_available': False,
            'most_recent_year': None,
            'previous_year': None,
            'revenue_yoy_growth_pct': None,
            'earnings_yoy_growth_pct': None,
            'profit_margin_pct': None,
            'years_available': 0
        }

        try:
            # Get annual financials
            annual_income = ticker_obj.financials

            if annual_income is None or annual_income.empty:
                return result

            # Transpose for easier access
            annual_income = annual_income.T
            years_available = len(annual_income)
            result['years_available'] = years_available

            if years_available == 0:
                return result

            # Most recent year
            most_recent = annual_income.iloc[0]
            result['most_recent_year'] = most_recent.name.strftime('%Y-%m-%d')

            revenue_current = self._safe_get(most_recent, ['Total Revenue', 'TotalRevenue'])
            earnings_current = self._safe_get(most_recent, ['Net Income', 'NetIncome'])

            # Y-o-Y comparison
            if years_available >= 2:
                previous_year = annual_income.iloc[1]
                result['previous_year'] = previous_year.name.strftime('%Y-%m-%d')

                revenue_previous = self._safe_get(previous_year, ['Total Revenue', 'TotalRevenue'])
                earnings_previous = self._safe_get(previous_year, ['Net Income', 'NetIncome'])

                if (revenue_current is not None and revenue_previous is not None
                        and revenue_previous != 0):
                    result['revenue_yoy_growth_pct'] = ((revenue_current - revenue_previous) / abs(revenue_previous)) * 100

                if (earnings_current is not None and earnings_previous is not None
                        and earnings_previous != 0):
                    result['earnings_yoy_growth_pct'] = ((earnings_current - earnings_previous) / abs(earnings_previous)) * 100

            # Profit margin
            if (revenue_current is not None and earnings_current is not None
                    and revenue_current != 0):
                result['profit_margin_pct'] = (earnings_current / revenue_current) * 100

            result['data_available'] = True

        except Exception as e:
            print(f"    Warning: Annual data fetch failed: {e}")
            result['error'] = str(e)

        return result

    def _fetch_institutional_data(self, ticker_obj) -> Dict:
        """
        Fetch institutional ownership data.

        Returns:
        - Current institutional ownership %
        - Change in ownership
        - Major holders information
        """

        result = {
            'data_available': False,
            'institutional_ownership_pct': None,
            'institutions_count': None,
            'top_5_holders_pct': None,
            'ownership_trend': 'unknown'
        }

        try:
            # Get institutional holders
            institutional_holders = ticker_obj.institutional_holders

            if institutional_holders is not None and not institutional_holders.empty:
                result['institutions_count'] = len(institutional_holders)

                # Calculate total institutional ownership
                if 'Shares' in institutional_holders.columns:
                    total_inst_shares = institutional_holders['Shares'].sum()

                    # Get total shares outstanding
                    info = ticker_obj.info
                    shares_outstanding = info.get('sharesOutstanding', 0)

                    if shares_outstanding > 0:
                        result['institutional_ownership_pct'] = (total_inst_shares / shares_outstanding) * 100

                # Get top 5 holders percentage
                if 'Holder' in institutional_holders.columns and len(institutional_holders) >= 5:
                    top_5_shares = institutional_holders.head(5)['Shares'].sum()
                    shares_outstanding = ticker_obj.info.get('sharesOutstanding', 0)
                    if shares_outstanding > 0:
                        result['top_5_holders_pct'] = (top_5_shares / shares_outstanding) * 100

                result['data_available'] = True

            # Try to get major holders (simplified view)
            major_holders = ticker_obj.major_holders
            if major_holders is not None and not major_holders.empty:
                result['major_holders_data'] = True

        except Exception as e:
            print(f"    Warning: Institutional data fetch failed: {e}")
            result['error'] = str(e)

        return result

    def _fetch_financial_health(self, ticker_obj) -> Dict:
        """
        Fetch financial health indicators.

        Returns:
        - Profitability metrics
        - Balance sheet health
        - Debt metrics
        - Cash flow health
        """

        result = {
            'data_available': False,
            'is_profitable': None,
            'net_worth_positive': None,
            'debt_to_equity': None,
            'current_ratio': None,
            'roe_pct': None,
            'roa_pct': None,
            'free_cash_flow_positive': None
        }

        try:
            info = ticker_obj.info

            # Profitability
            trailing_eps = info.get('trailingEps')
            if trailing_eps is not None:
                result['is_profitable'] = trailing_eps > 0

            # Balance sheet metrics
            balance_sheet = ticker_obj.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                balance_sheet = balance_sheet.T
                most_recent = balance_sheet.iloc[0]

                # Net worth (Total Assets - Total Liabilities)
                total_assets = self._safe_get(most_recent, ['Total Assets', 'TotalAssets'])
                total_liabilities = self._safe_get(most_recent, ['Total Liabilities Net Minority Interest', 'TotalLiabilitiesNetMinorityInterest'])

                if total_assets is not None and total_liabilities is not None:
                    net_worth = total_assets - total_liabilities
                    result['net_worth_positive'] = net_worth > 0

                # Debt to equity
                total_debt = self._safe_get(most_recent, ['Total Debt', 'TotalDebt'])
                stockholder_equity = self._safe_get(most_recent, ['Stockholders Equity', 'StockholdersEquity'])

                if (total_debt is not None and stockholder_equity is not None
                        and stockholder_equity != 0):
                    result['debt_to_equity'] = total_debt / stockholder_equity

                # Current ratio
                current_assets = self._safe_get(most_recent, ['Current Assets', 'CurrentAssets'])
                current_liabilities = self._safe_get(most_recent, ['Current Liabilities', 'CurrentLiabilities'])

                if (current_assets is not None and current_liabilities is not None
                        and current_liabilities != 0):
                    result['current_ratio'] = current_assets / current_liabilities

            # ROE and ROA
            result['roe_pct'] = info.get('returnOnEquity', None)
            if result['roe_pct'] is not None:
                result['roe_pct'] *= 100  # Convert to percentage

            result['roa_pct'] = info.get('returnOnAssets', None)
            if result['roa_pct'] is not None:
                result['roa_pct'] *= 100

            # Cash flow
            cash_flow = ticker_obj.cashflow
            if cash_flow is not None and not cash_flow.empty:
                cash_flow = cash_flow.T
                most_recent_cf = cash_flow.iloc[0]

                free_cash_flow = self._safe_get(most_recent_cf, ['Free Cash Flow', 'FreeCashFlow'])
                if free_cash_flow is not None:
                    result['free_cash_flow_positive'] = free_cash_flow > 0

            result['data_available'] = True

        except Exception as e:
            print(f"    Warning: Financial health fetch failed: {e}")
            result['error'] = str(e)

        return result

    def _validate_financial_health(self, fundamental_data: Dict) -> Dict:
        """
        Validate financial health and return flags.

        Returns validation flags:
        - Has positive earnings growth
        - Has positive net worth
        - Debt is manageable
        - Overall health status
        """

        validation = {
            'quarterly_growth_positive': False,
            'annual_growth_positive': False,
            'is_profitable': False,
            'net_worth_positive': False,
            'debt_manageable': True,  # Assume true unless proven otherwise
            'overall_health': 'unknown',
            'red_flags': [],
            'green_flags': []
        }

        # Check quarterly growth
        quarterly = fundamental_data.get('quarterly', {})
        if quarterly.get('earnings_yoy_growth_pct') is not None:
            if quarterly['earnings_yoy_growth_pct'] > 0:
                validation['quarterly_growth_positive'] = True
                validation['green_flags'].append(f"Quarterly earnings up {quarterly['earnings_yoy_growth_pct']:.1f}% Y-o-Y")
            else:
                validation['red_flags'].append(f"Quarterly earnings down {quarterly['earnings_yoy_growth_pct']:.1f}% Y-o-Y")

        # Check annual growth
        annual = fundamental_data.get('annual', {})
        if annual.get('earnings_yoy_growth_pct') is not None:
            if annual['earnings_yoy_growth_pct'] > 0:
                validation['annual_growth_positive'] = True
                validation['green_flags'].append(f"Annual earnings up {annual['earnings_yoy_growth_pct']:.1f}% Y-o-Y")
            else:
                validation['red_flags'].append(f"Annual earnings down {annual['earnings_yoy_growth_pct']:.1f}% Y-o-Y")

        # Check profitability
        health = fundamental_data.get('financial_health', {})
        if health.get('is_profitable') is True:
            validation['is_profitable'] = True
            validation['green_flags'].append("Company is profitable")
        elif health.get('is_profitable') is False:
            validation['red_flags'].append("Company is not profitable")

        # Check net worth
        if health.get('net_worth_positive') is True:
            validation['net_worth_positive'] = True
            validation['green_flags'].append("Net worth is positive")
        elif health.get('net_worth_positive') is False:
            validation['red_flags'].append("Net worth is negative")

        # Check debt
        debt_to_equity = health.get('debt_to_equity')
        if debt_to_equity is not None:
            if debt_to_equity < 1:
                validation['green_flags'].append(f"Healthy debt-to-equity ratio: {debt_to_equity:.2f}")
            elif debt_to_equity > 2:
                validation['debt_manageable'] = False
                validation['red_flags'].append(f"High debt-to-equity ratio: {debt_to_equity:.2f}")

        # Overall health assessment
        if len(validation['red_flags']) == 0:
            validation['overall_health'] = 'healthy'
        elif len(validation['red_flags']) >= 3:
            validation['overall_health'] = 'concerning'
        else:
            validation['overall_health'] = 'moderate'

        return validation

    def _safe_get(self, series, keys: List[str]):
        """Safely get value from series, trying multiple key names."""
        for key in keys:
            if key in series.index:
                value = series[key]
                if pd.notna(value):
                    return float(value)
        return None

    def format_for_ai_prompt(self, fundamental_data: Dict) -> str:
        """
        Format fundamental data for AI prompt.
        Returns human-readable summary string.
        """

        if not fundamental_data.get('data_available'):
            return "⚠️ Fundamental data not available for this ticker"

        lines = []
        lines.append("=" * 80)
        lines.append("📊 FUNDAMENTAL ANALYSIS DATA (Real-Time from YFinance)")
        lines.append("=" * 80)
        lines.append("")

        # Quarterly results
        quarterly = fundamental_data.get('quarterly', {})
        if quarterly.get('data_available'):
            lines.append("📅 QUARTERLY RESULTS:")
            lines.append(f"  Most Recent Quarter: {quarterly.get('most_recent_quarter', 'N/A')}")

            if quarterly.get('revenue_qoq_growth_pct') is not None:
                lines.append(f"  Revenue Growth (Q-o-Q): {quarterly['revenue_qoq_growth_pct']:+.2f}%")

            if quarterly.get('revenue_yoy_growth_pct') is not None:
                lines.append(f"  Revenue Growth (Y-o-Y): {quarterly['revenue_yoy_growth_pct']:+.2f}%")

            if quarterly.get('earnings_qoq_growth_pct') is not None:
                lines.append(f"  Earnings Growth (Q-o-Q): {quarterly['earnings_qoq_growth_pct']:+.2f}%")

            if quarterly.get('earnings_yoy_growth_pct') is not None:
                lines.append(f"  Earnings Growth (Y-o-Y): {quarterly['earnings_yoy_growth_pct']:+.2f}%")

            if quarterly.get('profit_margin_pct') is not None:
                lines.append(f"  Profit Margin: {quarterly['profit_margin_pct']:.2f}%")

            lines.append("")

        # Annual results
        annual = fundamental_data.get('annual', {})
        if annual.get('data_available'):
            lines.append("📈 ANNUAL RESULTS:")
            lines.append(f"  Most Recent Year: {annual.get('most_recent_year', 'N/A')}")

            if annual.get('revenue_yoy_growth_pct') is not None:
                lines.append(f"  Revenue Growth (Y-o-Y): {annual['revenue_yoy_growth_pct']:+.2f}%")

            if annual.get('earnings_yoy_growth_pct') is not None:
                lines.append(f"  Earnings Growth (Y-o-Y): {annual['earnings_yoy_growth_pct']:+.2f}%")

            if annual.get('profit_margin_pct') is not None:
                lines.append(f"  Profit Margin: {annual['profit_margin_pct']:.2f}%")

            lines.append("")

        # Institutional ownership
        institutional = fundamental_data.get('institutional', {})
        if institutional.get('data_available'):
            lines.append("🏦 INSTITUTIONAL OWNERSHIP:")

            if institutional.get('institutional_ownership_pct') is not None:
                lines.append(f"  Institutional Ownership: {institutional['institutional_ownership_pct']:.2f}%")

            if institutional.get('institutions_count') is not None:
                lines.append(f"  Number of Institutions: {institutional['institutions_count']}")

            if institutional.get('top_5_holders_pct') is not None:
                lines.append(f"  Top 5 Holders: {institutional['top_5_holders_pct']:.2f}%")

            lines.append("")

        # Financial health
        health = fundamental_data.get('financial_health', {})
        if health.get('data_available'):
            lines.append("💊 FINANCIAL HEALTH:")

            if health.get('is_profitable') is not None:
                status = "✅ Profitable" if health['is_profitable'] else "❌ Not Profitable"
                lines.append(f"  Profitability: {status}")

            if health.get('net_worth_positive') is not None:
                status = "✅ Positive" if health['net_worth_positive'] else "❌ Negative"
                lines.append(f"  Net Worth: {status}")

            if health.get('debt_to_equity') is not None:
                lines.append(f"  Debt-to-Equity Ratio: {health['debt_to_equity']:.2f}")

            if health.get('current_ratio') is not None:
                lines.append(f"  Current Ratio: {health['current_ratio']:.2f}")

            if health.get('roe_pct') is not None:
                lines.append(f"  Return on Equity: {health['roe_pct']:.2f}%")

            if health.get('roa_pct') is not None:
                lines.append(f"  Return on Assets: {health['roa_pct']:.2f}%")

            lines.append("")

        # Validation summary
        validation = fundamental_data.get('validation', {})
        if validation:
            lines.append("🎯 VALIDATION SUMMARY:")
            lines.append(f"  Overall Health: {validation.get('overall_health', 'unknown').upper()}")

            if validation.get('green_flags'):
                lines.append(f"  ✅ Strengths:")
                for flag in validation['green_flags']:
                    lines.append(f"     • {flag}")

            if validation.get('red_flags'):
                lines.append(f"  ⚠️  Concerns:")
                for flag in validation['red_flags']:
                    lines.append(f"     • {flag}")

            lines.append("")

        lines.append("=" * 80)
        lines.append("⚠️  CRITICAL: Use ONLY the data provided above. Do NOT use training data!")
        lines.append("=" * 80)

        return "\n".join(lines)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    import sys

    # Test with a ticker
    test_ticker = sys.argv[1] if len(sys.argv) > 1 else 'RELIANCE'

    print(f"\n{'='*80}")
    print(f"TESTING FUNDAMENTAL DATA FETCHER: {test_ticker}")
    print(f"{'='*80}\n")

    fetcher = FundamentalDataFetcher()
    data = fetcher.fetch_comprehensive_fundamentals(test_ticker)

    # Print formatted output
    formatted = fetcher.format_for_ai_prompt(data)
    print(formatted)

    # Save raw data
    output_file = f'fundamental_data_{test_ticker}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2, default=str)

    print(f"\n📄 Raw data saved to: {output_file}")
