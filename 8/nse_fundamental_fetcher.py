#!/usr/bin/env python3
"""
NSE FUNDAMENTAL DATA FETCHER
=============================

Fetches FII/DII investments, quarterly results, and shareholding data directly from NSE.
This data is FRESHER than yfinance and includes critical decision-making metrics.

Key Data Points:
1. FII/DII Investments (latest vs previous - magnitude & impact)
2. Quarterly Results (revenue, profit, margins)
3. Shareholding Patterns (promoter, FII, DII changes)
4. Corporate Announcements (dividends, splits, buybacks)

Usage:
    from nse_fundamental_fetcher import NSEFundamentalFetcher

    fetcher = NSEFundamentalFetcher()

    # Get FII data
    fii_data = fetcher.get_fii_dii_data('RELIANCE')

    # Get quarterly results
    results = fetcher.get_quarterly_results('RELIANCE')

    # Get complete fundamental package
    data = fetcher.get_comprehensive_fundamentals('RELIANCE')
"""

import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json
from threading import Lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSEFundamentalFetcher:
    """Fetch fundamental data directly from NSE APIs"""

    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize NSE fundamental fetcher

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 3600 = 1 hour)
        """
        self.cache_ttl = cache_ttl
        self.session = None
        self.session_created_at = None
        self.cache = {}
        self.cache_lock = Lock()

        # NSE API endpoints
        self.base_url = "https://www.nseindia.com"
        self.endpoints = {
            'quote': f"{self.base_url}/api/quote-equity",
            'quote_info': f"{self.base_url}/api/quote-equity-info",
            'corporate_info': f"{self.base_url}/api/corporate-info",
            'corporate_announcements': f"{self.base_url}/api/corporate-announcements",
            'fiidii_stats': f"{self.base_url}/api/fiidiiTrading",
            'shareholding': f"{self.base_url}/api/corporates-shareholding",
            'financial_results': f"{self.base_url}/api/corporate-financial-results",
        }

        # Headers for NSE requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        logger.info("NSEFundamentalFetcher initialized")

    def _create_session(self) -> Optional[requests.Session]:
        """Create NSE session with cookies"""
        try:
            session = requests.Session()

            # Initial page visit to set cookies
            response = session.get(self.base_url, headers=self.headers, timeout=10)
            time.sleep(1)  # Wait for cookies

            if response.status_code == 200:
                self.session = session
                self.session_created_at = datetime.now()
                logger.debug("NSE session created successfully")
                return session
            else:
                logger.warning(f"NSE session creation failed: HTTP {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"Failed to create NSE session: {str(e)[:100]}")
            return None

    def _get_session(self) -> Optional[requests.Session]:
        """Get current session or create new one if expired"""
        if self.session is None or \
           (self.session_created_at and (datetime.now() - self.session_created_at) > timedelta(minutes=30)):
            return self._create_session()
        return self.session

    def _get_cached(self, key: str) -> Optional[Dict]:
        """Get cached data if still valid"""
        with self.cache_lock:
            if key in self.cache:
                cached_data = self.cache[key]
                age = (datetime.now() - cached_data['cached_at']).total_seconds()
                if age < self.cache_ttl:
                    logger.debug(f"Using cached data for {key} (age: {age:.0f}s)")
                    return cached_data['data']
        return None

    def _set_cache(self, key: str, data: Dict):
        """Cache data"""
        with self.cache_lock:
            self.cache[key] = {
                'data': data,
                'cached_at': datetime.now()
            }

    def get_fii_dii_data(self, ticker: str) -> Dict:
        """
        Get FII/DII investment data for a ticker

        Returns:
            Dict with FII/DII buy/sell data, net investment, and changes
        """
        cache_key = f"fii_dii_{ticker}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        result = {
            'ticker': ticker,
            'data_available': False,
            'timestamp': datetime.now().isoformat(),
            'fii_data': {},
            'dii_data': {},
            'error': None
        }

        try:
            session = self._get_session()
            if not session:
                result['error'] = 'No NSE session available'
                return result

            # Get quote info which includes shareholding data
            url = f"{self.endpoints['quote_info']}?symbol={ticker.upper()}"
            time.sleep(0.5)

            response = session.get(url, headers=self.headers, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # Extract shareholding pattern
                shareholding = data.get('shareholdingPatterns', [])

                if shareholding and len(shareholding) >= 2:
                    # Most recent quarter
                    latest = shareholding[0]
                    previous = shareholding[1]

                    # FII data
                    fii_latest = float(latest.get('fiiPercent', 0) or 0)
                    fii_previous = float(previous.get('fiiPercent', 0) or 0)
                    fii_change = fii_latest - fii_previous
                    fii_change_pct = (fii_change / fii_previous * 100) if fii_previous > 0 else 0

                    # DII data
                    dii_latest = float(latest.get('diiPercent', 0) or 0)
                    dii_previous = float(previous.get('diiPercent', 0) or 0)
                    dii_change = dii_latest - dii_previous
                    dii_change_pct = (dii_change / dii_previous * 100) if dii_previous > 0 else 0

                    result['fii_data'] = {
                        'latest_percent': fii_latest,
                        'previous_percent': fii_previous,
                        'change_percent': fii_change,
                        'change_pct': fii_change_pct,
                        'latest_quarter': latest.get('asOnDate'),
                        'previous_quarter': previous.get('asOnDate'),
                        'trend': 'INCREASING' if fii_change > 0 else 'DECREASING' if fii_change < 0 else 'STABLE'
                    }

                    result['dii_data'] = {
                        'latest_percent': dii_latest,
                        'previous_percent': dii_previous,
                        'change_percent': dii_change,
                        'change_pct': dii_change_pct,
                        'latest_quarter': latest.get('asOnDate'),
                        'previous_quarter': previous.get('asOnDate'),
                        'trend': 'INCREASING' if dii_change > 0 else 'DECREASING' if dii_change < 0 else 'STABLE'
                    }

                    result['data_available'] = True
                    logger.info(f"FII: {fii_latest:.2f}% ({fii_change:+.2f}pp, {fii_change_pct:+.1f}%)")
                    logger.info(f"DII: {dii_latest:.2f}% ({dii_change:+.2f}pp, {dii_change_pct:+.1f}%)")
                else:
                    result['error'] = 'Insufficient shareholding data'
            else:
                result['error'] = f'HTTP {response.status_code}'

        except Exception as e:
            result['error'] = str(e)[:100]
            logger.warning(f"FII/DII fetch failed for {ticker}: {str(e)[:100]}")

        self._set_cache(cache_key, result)
        return result

    def get_quarterly_results(self, ticker: str) -> Dict:
        """
        Get quarterly financial results from NSE

        Returns:
            Dict with latest quarterly results, YoY and QoQ comparisons
        """
        cache_key = f"quarterly_{ticker}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        result = {
            'ticker': ticker,
            'data_available': False,
            'timestamp': datetime.now().isoformat(),
            'latest_quarter': {},
            'yoy_comparison': {},
            'qoq_comparison': {},
            'error': None
        }

        try:
            session = self._get_session()
            if not session:
                result['error'] = 'No NSE session available'
                return result

            # Get financial results
            url = f"{self.endpoints['quote_info']}?symbol={ticker.upper()}"
            time.sleep(0.5)

            response = session.get(url, headers=self.headers, timeout=15)

            if response.status_code == 200:
                data = response.json()

                # Extract financial results
                financials = data.get('financialResults', [])

                if financials and len(financials) >= 2:
                    # Latest quarter
                    latest = financials[0]
                    previous_qtr = financials[1] if len(financials) > 1 else None

                    # Try to find same quarter last year (YoY)
                    latest_period = latest.get('period', '')
                    yoy_match = None
                    for fin in financials[1:]:
                        if fin.get('period', '').split()[0] == latest_period.split()[0]:  # Same quarter
                            yoy_match = fin
                            break

                    # Extract values
                    revenue_latest = self._parse_financial_value(latest.get('totalIncome'))
                    profit_latest = self._parse_financial_value(latest.get('netProfitAfterTax'))

                    result['latest_quarter'] = {
                        'period': latest.get('period'),
                        'revenue': revenue_latest,
                        'profit': profit_latest,
                        'revenue_from_operations': self._parse_financial_value(latest.get('revenue')),
                        'date': latest.get('resultDate'),
                        'audited': latest.get('audited', False)
                    }

                    # QoQ comparison
                    if previous_qtr:
                        revenue_prev = self._parse_financial_value(previous_qtr.get('totalIncome'))
                        profit_prev = self._parse_financial_value(previous_qtr.get('netProfitAfterTax'))

                        result['qoq_comparison'] = {
                            'previous_quarter': previous_qtr.get('period'),
                            'revenue_growth_pct': ((revenue_latest - revenue_prev) / revenue_prev * 100) if revenue_prev else 0,
                            'profit_growth_pct': ((profit_latest - profit_prev) / profit_prev * 100) if profit_prev else 0,
                        }

                    # YoY comparison
                    if yoy_match:
                        revenue_yoy = self._parse_financial_value(yoy_match.get('totalIncome'))
                        profit_yoy = self._parse_financial_value(yoy_match.get('netProfitAfterTax'))

                        result['yoy_comparison'] = {
                            'previous_year_quarter': yoy_match.get('period'),
                            'revenue_growth_pct': ((revenue_latest - revenue_yoy) / revenue_yoy * 100) if revenue_yoy else 0,
                            'profit_growth_pct': ((profit_latest - profit_yoy) / profit_yoy * 100) if profit_yoy else 0,
                        }

                    result['data_available'] = True
                    logger.info(f"Quarterly: {latest.get('period')} | Revenue: ₹{revenue_latest:.0f}cr | Profit: ₹{profit_latest:.0f}cr")
                else:
                    result['error'] = 'No financial results available'
            else:
                result['error'] = f'HTTP {response.status_code}'

        except Exception as e:
            result['error'] = str(e)[:100]
            logger.warning(f"Quarterly results fetch failed for {ticker}: {str(e)[:100]}")

        self._set_cache(cache_key, result)
        return result

    def _parse_financial_value(self, value) -> float:
        """Parse financial value (handles strings like '1,234.5' or None)"""
        if value is None:
            return 0.0

        if isinstance(value, (int, float)):
            return float(value)

        # Remove commas and convert to float
        try:
            return float(str(value).replace(',', ''))
        except:
            return 0.0

    def calculate_impact_score(self, fii_data: Dict, quarterly_data: Dict, market_cap: float = None) -> Dict:
        """
        Calculate magnitude and impact scores for decision-making

        Args:
            fii_data: FII/DII data from get_fii_dii_data()
            quarterly_data: Quarterly results from get_quarterly_results()
            market_cap: Market cap in crores (optional, for magnitude calculation)

        Returns:
            Dict with impact scores and decision signals
        """
        score = {
            'overall_score': 0,
            'fii_impact': 0,
            'fundamental_impact': 0,
            'magnitude': 'LOW',
            'decision_signal': 'NEUTRAL',
            'key_factors': []
        }

        # FII Impact Score (0-50)
        if fii_data.get('data_available'):
            fii = fii_data['fii_data']
            fii_change_pct = fii.get('change_pct', 0)

            # FII impact scoring
            if abs(fii_change_pct) > 10:
                score['fii_impact'] = 50
                score['magnitude'] = 'VERY HIGH'
                score['key_factors'].append(f"FII {'surge' if fii_change_pct > 0 else 'exodus'}: {fii_change_pct:+.1f}%")
            elif abs(fii_change_pct) > 5:
                score['fii_impact'] = 35
                score['magnitude'] = 'HIGH'
                score['key_factors'].append(f"FII {'increase' if fii_change_pct > 0 else 'decrease'}: {fii_change_pct:+.1f}%")
            elif abs(fii_change_pct) > 2:
                score['fii_impact'] = 20
                score['magnitude'] = 'MEDIUM'
                score['key_factors'].append(f"FII change: {fii_change_pct:+.1f}%")
            else:
                score['fii_impact'] = 5
                score['magnitude'] = 'LOW'

        # Fundamental Impact Score (0-50)
        if quarterly_data.get('data_available'):
            yoy = quarterly_data.get('yoy_comparison', {})
            profit_growth = yoy.get('profit_growth_pct', 0)
            revenue_growth = yoy.get('revenue_growth_pct', 0)

            # Profit growth impact
            if profit_growth > 50:
                score['fundamental_impact'] = 50
                score['key_factors'].append(f"Profit surge: +{profit_growth:.1f}% YoY")
            elif profit_growth > 25:
                score['fundamental_impact'] = 40
                score['key_factors'].append(f"Strong profit growth: +{profit_growth:.1f}% YoY")
            elif profit_growth > 15:
                score['fundamental_impact'] = 30
                score['key_factors'].append(f"Good profit growth: +{profit_growth:.1f}% YoY")
            elif profit_growth > 0:
                score['fundamental_impact'] = 15
            elif profit_growth < -15:
                score['fundamental_impact'] = -20
                score['key_factors'].append(f"Profit decline: {profit_growth:.1f}% YoY")
            else:
                score['fundamental_impact'] = 5

            # Revenue growth bonus/penalty
            if revenue_growth > 20:
                score['fundamental_impact'] += 10
                score['key_factors'].append(f"Revenue growth: +{revenue_growth:.1f}% YoY")
            elif revenue_growth < -10:
                score['fundamental_impact'] -= 10
                score['key_factors'].append(f"Revenue decline: {revenue_growth:.1f}% YoY")

        # Overall score and signal
        score['overall_score'] = score['fii_impact'] + score['fundamental_impact']

        if score['overall_score'] >= 60:
            score['decision_signal'] = 'STRONG BUY'
        elif score['overall_score'] >= 40:
            score['decision_signal'] = 'BUY'
        elif score['overall_score'] >= 20:
            score['decision_signal'] = 'ACCUMULATE'
        elif score['overall_score'] >= -20:
            score['decision_signal'] = 'HOLD'
        elif score['overall_score'] >= -40:
            score['decision_signal'] = 'REDUCE'
        else:
            score['decision_signal'] = 'SELL'

        return score

    def get_comprehensive_fundamentals(self, ticker: str) -> Dict:
        """
        Get all fundamental data in one call

        Returns:
            Complete package with FII, quarterly results, and impact scores
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Fetching comprehensive fundamentals for {ticker}")
        logger.info(f"{'='*80}")

        fii_data = self.get_fii_dii_data(ticker)
        quarterly_data = self.get_quarterly_results(ticker)
        impact_score = self.calculate_impact_score(fii_data, quarterly_data)

        return {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'fii_dii': fii_data,
            'quarterly_results': quarterly_data,
            'impact_score': impact_score,
            'data_sources': 'NSE Direct API'
        }


# Convenience function
def get_nse_fundamentals(ticker: str) -> Dict:
    """Convenience function to get NSE fundamental data"""
    fetcher = NSEFundamentalFetcher()
    return fetcher.get_comprehensive_fundamentals(ticker)


# Test/Demo
if __name__ == '__main__':
    print("=" * 80)
    print("NSE FUNDAMENTAL DATA FETCHER TEST")
    print("=" * 80)
    print()

    fetcher = NSEFundamentalFetcher()

    # Test with multiple tickers
    test_tickers = ['RELIANCE', 'TRENT', 'INFY']

    for ticker in test_tickers:
        print(f"\n{'='*80}")
        print(f"Testing: {ticker}")
        print(f"{'='*80}")

        # Get comprehensive data
        data = fetcher.get_comprehensive_fundamentals(ticker)

        # Display FII data
        if data['fii_dii']['data_available']:
            fii = data['fii_dii']['fii_data']
            dii = data['fii_dii']['dii_data']

            print(f"\n📊 FII/DII INVESTMENT DATA:")
            print(f"   FII Holding: {fii['latest_percent']:.2f}% ({fii['change_percent']:+.2f}pp, {fii['change_pct']:+.1f}% QoQ)")
            print(f"   FII Trend: {fii['trend']}")
            print(f"   DII Holding: {dii['latest_percent']:.2f}% ({dii['change_percent']:+.2f}pp, {dii['change_pct']:+.1f}% QoQ)")
            print(f"   DII Trend: {dii['trend']}")

        # Display quarterly results
        if data['quarterly_results']['data_available']:
            latest = data['quarterly_results']['latest_quarter']
            yoy = data['quarterly_results'].get('yoy_comparison', {})
            qoq = data['quarterly_results'].get('qoq_comparison', {})

            print(f"\n📈 QUARTERLY RESULTS:")
            print(f"   Period: {latest['period']}")
            print(f"   Revenue: ₹{latest['revenue']:.0f} cr")
            print(f"   Profit: ₹{latest['profit']:.0f} cr")

            if yoy:
                print(f"   YoY Growth: Revenue {yoy['revenue_growth_pct']:+.1f}%, Profit {yoy['profit_growth_pct']:+.1f}%")
            if qoq:
                print(f"   QoQ Growth: Revenue {qoq['revenue_growth_pct']:+.1f}%, Profit {qoq['profit_growth_pct']:+.1f}%")

        # Display impact score
        impact = data['impact_score']
        print(f"\n🎯 IMPACT SCORE:")
        print(f"   Overall Score: {impact['overall_score']}/100")
        print(f"   FII Impact: {impact['fii_impact']}/50")
        print(f"   Fundamental Impact: {impact['fundamental_impact']}/50")
        print(f"   Magnitude: {impact['magnitude']}")
        print(f"   Decision Signal: {impact['decision_signal']}")

        if impact['key_factors']:
            print(f"\n   Key Factors:")
            for factor in impact['key_factors']:
                print(f"   • {factor}")

        time.sleep(2)  # Rate limiting

    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")
