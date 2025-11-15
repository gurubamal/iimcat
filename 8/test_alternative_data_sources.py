#!/usr/bin/env python3
"""
Test Alternative Data Sources for FII and Quarterly Results

Sources to test:
1. BSE (Bombay Stock Exchange) API
2. Screener.in
3. MoneyControl
4. Trendlyne
5. Alpha Vantage (India stocks)
6. Economic Times Market Data
7. Tickertape by Smallcase
8. Company Investor Relations pages
"""

import requests
import time
import json
from datetime import datetime
from bs4 import BeautifulSoup
import re

def test_bse_api(ticker: str):
    """Test BSE (Bombay Stock Exchange) API"""
    print(f"\n{'='*80}")
    print(f"1. BSE API - {ticker}")
    print(f"{'='*80}")

    results = {
        'source': 'BSE',
        'quarterly_data': None,
        'fii_data': None,
        'price_data': None,
        'status': 'TESTING'
    }

    try:
        # BSE API endpoints (need to find the right ones)
        base_url = "https://api.bseindia.com"

        # Try common BSE endpoints
        endpoints = [
            f"{base_url}/BseIndiaAPI/api/StockReachGraph/w?scripcode=500325&flag=0&fromdate=&todate=&seriesid=",  # RELIANCE BSE code
            f"https://www.bseindia.com/stock-share-price/reliance-industries-ltd/reliance/500325/",
        ]

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        for url in endpoints:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                print(f"   Testing: {url[:60]}...")
                print(f"   Status: {response.status_code}")

                if response.status_code == 200:
                    print(f"   ✅ BSE endpoint accessible")
                    # Try to parse response
                    try:
                        data = response.json()
                        print(f"   Data type: JSON")
                        print(f"   Keys: {list(data.keys())[:5]}")
                    except:
                        print(f"   Data type: HTML/Text ({len(response.text)} chars)")
                else:
                    print(f"   ❌ HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}")

            time.sleep(0.5)

        results['status'] = 'TESTED - Need BSE scrip code mapping'

    except Exception as e:
        results['status'] = f'ERROR: {str(e)[:50]}'
        print(f"   ❌ BSE test failed: {str(e)[:100]}")

    return results


def test_screener_in(ticker: str):
    """Test Screener.in for quarterly data"""
    print(f"\n{'='*80}")
    print(f"2. Screener.in - {ticker}")
    print(f"{'='*80}")

    results = {
        'source': 'Screener.in',
        'quarterly_data': None,
        'fii_data': None,
        'status': 'TESTING'
    }

    try:
        # Screener.in company page
        url = f"https://www.screener.in/company/{ticker}/consolidated/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)
        print(f"   URL: {url}")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Try to extract quarterly results
            # Screener.in has tables with quarterly data
            tables = soup.find_all('table')
            print(f"   ✅ Found {len(tables)} tables on page")

            # Look for quarterly results table
            for table in tables:
                if 'Quarterly Results' in str(table) or 'quarterly' in str(table).lower():
                    print(f"   ✅ QUARTERLY RESULTS TABLE FOUND!")

                    # Extract headers
                    headers_row = table.find('thead')
                    if headers_row:
                        headers = [th.text.strip() for th in headers_row.find_all('th')]
                        print(f"   Headers: {headers[:5]}")

                    # Extract first data row (latest quarter)
                    body = table.find('tbody')
                    if body:
                        first_row = body.find('tr')
                        if first_row:
                            values = [td.text.strip() for td in first_row.find_all('td')]
                            print(f"   Latest Quarter Data: {values[:5]}")

                            results['quarterly_data'] = {
                                'available': True,
                                'headers': headers[:5],
                                'latest_values': values[:5]
                            }
                    break

            # Look for shareholding pattern
            if 'Shareholding Pattern' in response.text or 'FII' in response.text:
                print(f"   ✅ SHAREHOLDING DATA AVAILABLE")
                results['fii_data'] = {'available': True, 'needs_parsing': True}

            results['status'] = 'SUCCESS - Data available via web scraping'

        else:
            results['status'] = f'HTTP {response.status_code}'
            print(f"   ❌ Page not accessible")

    except Exception as e:
        results['status'] = f'ERROR: {str(e)[:50]}'
        print(f"   ❌ Screener.in test failed: {str(e)[:100]}")

    return results


def test_moneycontrol(ticker: str):
    """Test MoneyControl for quarterly data"""
    print(f"\n{'='*80}")
    print(f"3. MoneyControl - {ticker}")
    print(f"{'='*80}")

    results = {
        'source': 'MoneyControl',
        'quarterly_data': None,
        'fii_data': None,
        'status': 'TESTING'
    }

    try:
        # MoneyControl uses different URL structure
        # Need to search first to get the right URL
        search_url = f"https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data=&cid=&mbsearch_str={ticker}&topsearch_type=1"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(search_url, headers=headers, timeout=15)
        print(f"   Search URL: {search_url[:60]}...")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Look for quarterly results link
            if 'Quarterly Results' in response.text or 'quarterly-results' in response.text:
                print(f"   ✅ QUARTERLY RESULTS SECTION FOUND")
                results['quarterly_data'] = {'available': True, 'needs_parsing': True}

            # Look for shareholding pattern
            if 'Shareholding Pattern' in response.text or 'shareholding' in response.text:
                print(f"   ✅ SHAREHOLDING DATA AVAILABLE")
                results['fii_data'] = {'available': True, 'needs_parsing': True}

            results['status'] = 'SUCCESS - Data available via web scraping'
        else:
            results['status'] = f'HTTP {response.status_code}'
            print(f"   ❌ Page not accessible")

    except Exception as e:
        results['status'] = f'ERROR: {str(e)[:50]}'
        print(f"   ❌ MoneyControl test failed: {str(e)[:100]}")

    return results


def test_trendlyne(ticker: str):
    """Test Trendlyne for quarterly data"""
    print(f"\n{'='*80}")
    print(f"4. Trendlyne - {ticker}")
    print(f"{'='*80}")

    results = {
        'source': 'Trendlyne',
        'quarterly_data': None,
        'fii_data': None,
        'status': 'TESTING'
    }

    try:
        # Trendlyne URL format
        url = f"https://trendlyne.com/equity/{ticker}/1/financials/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)
        print(f"   URL: {url}")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            # Trendlyne might have data in JavaScript or API calls
            if 'quarterly' in response.text.lower() or 'revenue' in response.text.lower():
                print(f"   ✅ FINANCIAL DATA FOUND")
                results['quarterly_data'] = {'available': True, 'needs_parsing': True}

            if 'shareholding' in response.text.lower() or 'fii' in response.text.lower():
                print(f"   ✅ SHAREHOLDING DATA FOUND")
                results['fii_data'] = {'available': True, 'needs_parsing': True}

            results['status'] = 'SUCCESS - Data available via web scraping'
        else:
            results['status'] = f'HTTP {response.status_code}'
            print(f"   ❌ Page not accessible")

    except Exception as e:
        results['status'] = f'ERROR: {str(e)[:50]}'
        print(f"   ❌ Trendlyne test failed: {str(e)[:100]}")

    return results


def test_alpha_vantage(ticker: str):
    """Test Alpha Vantage API for India stocks"""
    print(f"\n{'='*80}")
    print(f"5. Alpha Vantage API - {ticker}")
    print(f"{'='*80}")

    results = {
        'source': 'Alpha Vantage',
        'quarterly_data': None,
        'status': 'TESTING'
    }

    try:
        # Alpha Vantage supports NSE stocks with .NS suffix
        # Free tier: 5 API calls per minute, 500 per day
        # Demo key: 'demo' (limited)

        print(f"   NOTE: Alpha Vantage requires API key (free tier available)")
        print(f"   Endpoint: https://www.alphavantage.co/query")
        print(f"   Functions: INCOME_STATEMENT, BALANCE_SHEET, CASH_FLOW")
        print(f"   India stocks: Use {ticker}.BSE or {ticker}.NS format")

        results['status'] = 'AVAILABLE - Requires API key (free tier: 500 calls/day)'
        results['quarterly_data'] = {'available': True, 'requires_api_key': True}

    except Exception as e:
        results['status'] = f'ERROR: {str(e)[:50]}'

    return results


def test_tickertape(ticker: str):
    """Test Tickertape by Smallcase"""
    print(f"\n{'='*80}")
    print(f"6. Tickertape by Smallcase - {ticker}")
    print(f"{'='*80}")

    results = {
        'source': 'Tickertape',
        'quarterly_data': None,
        'fii_data': None,
        'status': 'TESTING'
    }

    try:
        # Tickertape URL format
        url = f"https://www.tickertape.in/stocks/{ticker.lower()}-{ticker}/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, headers=headers, timeout=15)
        print(f"   URL: {url}")
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            # Tickertape loads data via JavaScript/API
            if 'quarterly' in response.text.lower() or 'financial' in response.text.lower():
                print(f"   ✅ FINANCIAL DATA SECTION FOUND")
                results['quarterly_data'] = {'available': True, 'loads_via_js': True}

            if 'shareholding' in response.text.lower():
                print(f"   ✅ SHAREHOLDING DATA FOUND")
                results['fii_data'] = {'available': True, 'loads_via_js': True}

            results['status'] = 'SUCCESS - Data loads via JavaScript'
        else:
            results['status'] = f'HTTP {response.status_code}'
            print(f"   ❌ Page not accessible")

    except Exception as e:
        results['status'] = f'ERROR: {str(e)[:50]}'
        print(f"   ❌ Tickertape test failed: {str(e)[:100]}")

    return results


def test_economic_times(ticker: str):
    """Test Economic Times Market Data"""
    print(f"\n{'='*80}")
    print(f"7. Economic Times Market Data - {ticker}")
    print(f"{'='*80}")

    results = {
        'source': 'Economic Times',
        'quarterly_data': None,
        'status': 'TESTING'
    }

    try:
        # ET Market URL
        url = f"https://economictimes.indiatimes.com/markets/stocks/stock-quotes"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        print(f"   Economic Times has market data but structure varies")
        print(f"   Typically requires stock-specific URL mapping")

        results['status'] = 'AVAILABLE - Requires URL mapping per stock'

    except Exception as e:
        results['status'] = f'ERROR: {str(e)[:50]}'

    return results


# Run all tests
print("=" * 80)
print("ALTERNATIVE DATA SOURCES TEST FOR FII & QUARTERLY RESULTS")
print("=" * 80)
print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Test Ticker: RELIANCE")
print()

ticker = 'RELIANCE'
all_results = []

# Test each source
all_results.append(test_bse_api(ticker))
time.sleep(1)

all_results.append(test_screener_in(ticker))
time.sleep(1)

all_results.append(test_moneycontrol(ticker))
time.sleep(1)

all_results.append(test_trendlyne(ticker))
time.sleep(1)

all_results.append(test_alpha_vantage(ticker))
time.sleep(1)

all_results.append(test_tickertape(ticker))
time.sleep(1)

all_results.append(test_economic_times(ticker))

# Summary
print(f"\n{'='*80}")
print("SUMMARY - DATA SOURCE COMPARISON")
print(f"{'='*80}\n")

print(f"{'Source':<25} {'Quarterly Data':<20} {'FII Data':<20} {'Status'}")
print(f"{'-'*80}")

for result in all_results:
    source = result['source']
    quarterly = '✅ Yes' if result.get('quarterly_data', {}).get('available') else '❌ No'
    fii = '✅ Yes' if result.get('fii_data', {}).get('available') else '❌ No'
    status = result['status']

    print(f"{source:<25} {quarterly:<20} {fii:<20} {status[:30]}")

print(f"\n{'='*80}")
print("RECOMMENDATIONS")
print(f"{'='*80}\n")

print("🥇 BEST FOR QUARTERLY RESULTS:")
print("   1. Screener.in - Free, comprehensive, well-structured")
print("   2. yfinance - Already using, good API")
print("   3. Alpha Vantage - Free API (500 calls/day)")

print("\n🥈 BEST FOR FII DATA:")
print("   1. Screener.in - Has shareholding pattern")
print("   2. yfinance - institutional_holders (already using)")
print("   3. MoneyControl - Comprehensive but needs scraping")

print("\n⚠️  CHALLENGES:")
print("   • Most sources require web scraping (no clean APIs)")
print("   • Rate limiting and blocking risks")
print("   • Data structure changes frequently")
print("   • NSE/BSE official APIs are restricted")

print("\n✅ RECOMMENDATION:")
print("   Keep current setup (yfinance) - it's reliable and has clean API")
print("   Optional: Add Screener.in for backup/validation")
print("   Optional: Add Alpha Vantage if you need more data points")

print(f"\n{'='*80}")
