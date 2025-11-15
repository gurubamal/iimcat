#!/usr/bin/env python3
"""
Screener.in Data Fetcher

Fetches quarterly results and shareholding data from Screener.in
This is a FREE alternative to yfinance with fresh Indian stock data.

Features:
- Quarterly financial results (revenue, profit, margins)
- Shareholding patterns (promoter, FII, DII)
- Financial ratios and metrics
- No API key required

Usage:
    from screener_in_fetcher import ScreenerFetcher

    fetcher = ScreenerFetcher()
    data = fetcher.get_comprehensive_data('RELIANCE')
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import Dict, List, Optional
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScreenerFetcher:
    """Fetch data from Screener.in"""

    def __init__(self):
        self.base_url = "https://www.screener.in"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _parse_number(self, value: str) -> Optional[float]:
        """Parse Indian number format (e.g., '1,234.5' or '1,23,45,678')"""
        if not value or value in ['-', 'N/A', '']:
            return None

        try:
            # Remove commas and convert
            cleaned = re.sub(r'[,\s]', '', str(value))
            return float(cleaned)
        except:
            return None

    def get_quarterly_results(self, ticker: str) -> Dict:
        """
        Get quarterly financial results from Screener.in

        Returns:
            Dict with quarterly revenue, profit, and growth rates
        """
        logger.info(f"Fetching quarterly data for {ticker} from Screener.in")

        result = {
            'ticker': ticker,
            'source': 'Screener.in',
            'timestamp': datetime.now().isoformat(),
            'data_available': False,
            'quarters': [],
            'latest_quarter': {},
            'yoy_growth': {},
            'error': None
        }

        try:
            # Screener.in consolidated financials page
            url = f"{self.base_url}/company/{ticker}/consolidated/"
            response = self.session.get(url, timeout=15)

            if response.status_code != 200:
                result['error'] = f'HTTP {response.status_code}'
                return result

            soup = BeautifulSoup(response.content, 'html.parser')

            # Find quarterly results table
            tables = soup.find_all('table')

            for table in tables:
                # Look for table with quarterly data (has months like 'Sep 2025', 'Jun 2025')
                header_row = table.find('thead')
                if not header_row:
                    continue

                headers = [th.text.strip() for th in header_row.find_all('th')]

                # Check if this looks like quarterly table (has month names)
                if any(re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', h) for h in headers):
                    logger.debug(f"Found quarterly table with headers: {headers}")

                    # Extract quarters (skip first header which is metric name)
                    quarters = headers[1:]

                    # Extract financial metrics
                    body = table.find('tbody')
                    if not body:
                        continue

                    rows = body.find_all('tr')

                    quarterly_data = {q: {} for q in quarters}

                    for row in rows:
                        cells = row.find_all('td')
                        if len(cells) < 2:
                            continue

                        metric_name = cells[0].text.strip()

                        # Extract values for each quarter
                        for i, quarter in enumerate(quarters):
                            if i + 1 < len(cells):
                                value = cells[i + 1].text.strip()
                                quarterly_data[quarter][metric_name] = value

                    # Parse latest quarter
                    if quarters:
                        latest_q = quarters[0]
                        latest_data = quarterly_data[latest_q]

                        # Extract key metrics
                        sales = self._parse_number(latest_data.get('Sales', latest_data.get('Sales\xa0+', None)))
                        expenses = self._parse_number(latest_data.get('Expenses', latest_data.get('Expenses\xa0+', None)))
                        operating_profit = self._parse_number(latest_data.get('Operating Profit', None))
                        net_profit = self._parse_number(latest_data.get('Net Profit', latest_data.get('Net Profit\xa0+', None)))
                        eps = self._parse_number(latest_data.get('EPS in Rs', None))

                        result['latest_quarter'] = {
                            'period': latest_q,
                            'sales': sales,
                            'expenses': expenses,
                            'operating_profit': operating_profit,
                            'net_profit': net_profit,
                            'eps': eps
                        }

                        # Calculate YoY growth (compare with same quarter last year - 4 quarters ago)
                        if len(quarters) >= 5:  # Need at least 5 quarters for YoY
                            yoy_quarter = quarters[4]
                            yoy_data = quarterly_data[yoy_quarter]

                            sales_yoy = self._parse_number(yoy_data.get('Sales', yoy_data.get('Sales\xa0+', None)))
                            profit_yoy = self._parse_number(yoy_data.get('Net Profit', yoy_data.get('Net Profit\xa0+', None)))

                            if sales and sales_yoy and sales_yoy > 0:
                                sales_growth = ((sales - sales_yoy) / sales_yoy) * 100
                                result['yoy_growth']['sales'] = sales_growth

                            if net_profit and profit_yoy and profit_yoy > 0:
                                profit_growth = ((net_profit - profit_yoy) / profit_yoy) * 100
                                result['yoy_growth']['profit'] = profit_growth

                        result['quarters'] = quarters
                        result['data_available'] = True
                        break

        except Exception as e:
            result['error'] = str(e)[:100]
            logger.warning(f"Screener.in fetch failed for {ticker}: {str(e)[:100]}")

        return result

    def get_shareholding_pattern(self, ticker: str) -> Dict:
        """
        Get shareholding pattern (promoter, FII, DII, public)

        Returns:
            Dict with shareholding percentages
        """
        logger.info(f"Fetching shareholding data for {ticker} from Screener.in")

        result = {
            'ticker': ticker,
            'source': 'Screener.in',
            'timestamp': datetime.now().isoformat(),
            'data_available': False,
            'shareholding': {},
            'error': None
        }

        try:
            url = f"{self.base_url}/company/{ticker}/consolidated/"
            response = self.session.get(url, timeout=15)

            if response.status_code != 200:
                result['error'] = f'HTTP {response.status_code}'
                return result

            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for shareholding pattern section
            # Screener.in typically has this in a dedicated section
            shareholding_section = soup.find(string=re.compile(r'Shareholding Pattern', re.IGNORECASE))

            if shareholding_section:
                # Find nearby table or data
                parent = shareholding_section.find_parent()
                if parent:
                    # Look for percentages near common terms
                    text = parent.get_text()

                    promoter_match = re.search(r'Promoters?[:\s]+([0-9.]+)%', text, re.IGNORECASE)
                    fii_match = re.search(r'FII[:\s]+([0-9.]+)%', text, re.IGNORECASE)
                    dii_match = re.search(r'DII[:\s]+([0-9.]+)%', text, re.IGNORECASE)
                    public_match = re.search(r'Public[:\s]+([0-9.]+)%', text, re.IGNORECASE)

                    if promoter_match:
                        result['shareholding']['promoter'] = float(promoter_match.group(1))
                    if fii_match:
                        result['shareholding']['fii'] = float(fii_match.group(1))
                    if dii_match:
                        result['shareholding']['dii'] = float(dii_match.group(1))
                    if public_match:
                        result['shareholding']['public'] = float(public_match.group(1))

                    if result['shareholding']:
                        result['data_available'] = True

        except Exception as e:
            result['error'] = str(e)[:100]
            logger.warning(f"Shareholding fetch failed for {ticker}: {str(e)[:100]}")

        return result

    def get_comprehensive_data(self, ticker: str) -> Dict:
        """
        Get all available data from Screener.in

        Returns:
            Complete package with quarterly results and shareholding
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Fetching comprehensive data for {ticker} from Screener.in")
        logger.info(f"{'='*80}")

        quarterly = self.get_quarterly_results(ticker)
        time.sleep(0.5)  # Be polite

        shareholding = self.get_shareholding_pattern(ticker)

        return {
            'ticker': ticker,
            'source': 'Screener.in',
            'timestamp': datetime.now().isoformat(),
            'quarterly_results': quarterly,
            'shareholding': shareholding
        }


# Convenience function
def get_screener_data(ticker: str) -> Dict:
    """Convenience function to get Screener.in data"""
    fetcher = ScreenerFetcher()
    return fetcher.get_comprehensive_data(ticker)


# Test/Demo
if __name__ == '__main__':
    print("=" * 80)
    print("SCREENER.IN DATA FETCHER TEST")
    print("=" * 80)
    print()

    fetcher = ScreenerFetcher()

    # Test with RELIANCE and TRENT
    test_tickers = ['RELIANCE', 'TRENT']

    for ticker in test_tickers:
        data = fetcher.get_comprehensive_data(ticker)

        print(f"\n{'='*80}")
        print(f"Results for: {ticker}")
        print(f"{'='*80}")

        # Display quarterly results
        quarterly = data['quarterly_results']
        if quarterly['data_available']:
            latest = quarterly['latest_quarter']
            yoy = quarterly.get('yoy_growth', {})

            print(f"\n📈 QUARTERLY RESULTS (Latest: {latest['period']}):")
            print(f"   Sales: ₹{latest['sales']:.0f} cr" if latest['sales'] else "   Sales: N/A")
            print(f"   Net Profit: ₹{latest['net_profit']:.0f} cr" if latest['net_profit'] else "   Net Profit: N/A")
            print(f"   EPS: ₹{latest['eps']:.2f}" if latest['eps'] else "   EPS: N/A")

            if yoy:
                print(f"\n   YoY Growth:")
                if 'sales' in yoy:
                    print(f"   • Sales: {yoy['sales']:+.1f}%")
                if 'profit' in yoy:
                    print(f"   • Profit: {yoy['profit']:+.1f}%")

            print(f"\n   Available Quarters: {', '.join(quarterly['quarters'][:5])}")
        else:
            print(f"\n❌ Quarterly data not available")
            if quarterly['error']:
                print(f"   Error: {quarterly['error']}")

        # Display shareholding
        shareholding = data['shareholding']
        if shareholding['data_available']:
            sh = shareholding['shareholding']
            print(f"\n👥 SHAREHOLDING PATTERN:")
            if 'promoter' in sh:
                print(f"   Promoter: {sh['promoter']:.2f}%")
            if 'fii' in sh:
                print(f"   FII: {sh['fii']:.2f}%")
            if 'dii' in sh:
                print(f"   DII: {sh['dii']:.2f}%")
            if 'public' in sh:
                print(f"   Public: {sh['public']:.2f}%")
        else:
            print(f"\n⚠️  Shareholding data not found on page")

        time.sleep(1)  # Rate limiting

    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}")

    print("\n🎯 COMPARISON WITH yfinance:")
    print("   • Screener.in: FREE, no API key needed")
    print("   • Data freshness: Similar to yfinance (quarterly reports)")
    print("   • Structure: Requires web scraping (more fragile)")
    print("   • yfinance: Clean API, better for automation")
    print("\n✅ RECOMMENDATION: Use yfinance as primary, Screener.in as backup")
