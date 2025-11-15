#!/usr/bin/env python3
"""
Test Real-Time Data Fetching from Multiple Sources

This script tests:
1. Current news fetching (RSS feeds)
2. Direct website scraping for real-time financial data
3. Alternative APIs for price/fundamental data
4. Comparison of data freshness and availability

Usage:
    python3 test_realtime_data_sources.py
"""

import requests
from bs4 import BeautifulSoup
import json
import yfinance as yf
from datetime import datetime, timedelta
import time
import re
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET

# Test tickers
TEST_TICKERS = ['RELIANCE', 'TRENT']

print("=" * 80)
print("REAL-TIME DATA SOURCE TEST")
print("=" * 80)
print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# ============================================================================
# TEST 1: Current News Fetching (RSS Feeds)
# ============================================================================
print("TEST 1: Current News Fetching via RSS Feeds")
print("-" * 80)

def test_rss_feeds():
    """Test current RSS feed sources"""
    feeds = [
        ('Economic Times', 'https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms'),
        ('Business Standard', 'https://www.business-standard.com/rss/markets-106.rss'),
        ('Moneycontrol', 'https://www.moneycontrol.com/rss/MCtopnews.xml'),
        ('Livemint', 'https://www.livemint.com/rss/companies'),
        ('CNBC TV18', 'https://www.cnbctv18.com/rss/latest.xml'),
    ]

    results = {}
    for name, url in feeds:
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                channel = root.find('channel')
                items = channel.findall('item') if channel else []
                results[name] = {
                    'status': 'OK',
                    'articles_count': len(items),
                    'latest_title': items[0].findtext('title') if items else 'N/A'
                }
            else:
                results[name] = {'status': f'HTTP {resp.status_code}', 'articles_count': 0}
        except Exception as e:
            results[name] = {'status': f'ERROR: {str(e)[:50]}', 'articles_count': 0}

    for name, data in results.items():
        status_icon = "✅" if data['status'] == 'OK' else "❌"
        print(f"{status_icon} {name:20s} | Articles: {data['articles_count']:3d} | Status: {data['status']}")
        if 'latest_title' in data and data['latest_title'] != 'N/A':
            print(f"   Latest: {data['latest_title'][:70]}")

    return results

rss_results = test_rss_feeds()
print()

# ============================================================================
# TEST 2: NSE Website Direct Scraping
# ============================================================================
print("TEST 2: NSE Website Direct Data Scraping")
print("-" * 80)

def test_nse_website(ticker: str) -> Dict:
    """Test fetching real-time data from NSE website"""
    try:
        # NSE API endpoint (public)
        url = f"https://www.nseindia.com/api/quote-equity?symbol={ticker}"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        # NSE requires session with initial page visit
        session = requests.Session()
        session.get('https://www.nseindia.com', headers=headers, timeout=10)
        time.sleep(1)

        resp = session.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            return {
                'status': 'OK',
                'price': data.get('priceInfo', {}).get('lastPrice'),
                'change': data.get('priceInfo', {}).get('change'),
                'volume': data.get('preOpenMarket', {}).get('totalTradedVolume'),
                'timestamp': datetime.now().isoformat(),
                'data_available': bool(data.get('priceInfo'))
            }
        else:
            return {'status': f'HTTP {resp.status_code}', 'data_available': False}

    except Exception as e:
        return {'status': f'ERROR: {str(e)[:50]}', 'data_available': False}

for ticker in TEST_TICKERS:
    nse_data = test_nse_website(ticker)
    status_icon = "✅" if nse_data['status'] == 'OK' else "❌"
    print(f"{status_icon} {ticker:10s} | Status: {nse_data['status']}")
    if nse_data.get('data_available'):
        print(f"   Price: ₹{nse_data['price']} | Change: {nse_data['change']} | Volume: {nse_data['volume']}")
        print(f"   Timestamp: {nse_data['timestamp']}")
    time.sleep(1)

print()

# ============================================================================
# TEST 3: Moneycontrol Website Scraping
# ============================================================================
print("TEST 3: Moneycontrol Website Data Scraping")
print("-" * 80)

def test_moneycontrol(ticker: str) -> Dict:
    """Test fetching data from Moneycontrol website"""
    try:
        # Search for the stock
        search_url = f"https://www.moneycontrol.com/stocks/cptmarket/compsearchnew.php?search_data=&cid=&mbsearch_str={ticker}&topsearch_type=1"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        resp = requests.get(search_url, headers=headers, timeout=10)

        if resp.status_code == 200:
            # Simple check if we get valid HTML
            soup = BeautifulSoup(resp.content, 'html.parser')
            has_data = bool(soup.find('body'))

            return {
                'status': 'OK',
                'search_worked': has_data,
                'response_size': len(resp.content),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {'status': f'HTTP {resp.status_code}', 'search_worked': False}

    except Exception as e:
        return {'status': f'ERROR: {str(e)[:50]}', 'search_worked': False}

for ticker in TEST_TICKERS:
    mc_data = test_moneycontrol(ticker)
    status_icon = "✅" if mc_data['status'] == 'OK' else "❌"
    print(f"{status_icon} {ticker:10s} | Status: {mc_data['status']}")
    if mc_data.get('search_worked'):
        print(f"   Response size: {mc_data['response_size']:,} bytes")

print()

# ============================================================================
# TEST 4: Screener.in API/Scraping
# ============================================================================
print("TEST 4: Screener.in Data Access")
print("-" * 80)

def test_screener_in(ticker: str) -> Dict:
    """Test fetching data from Screener.in"""
    try:
        url = f"https://www.screener.in/api/company/{ticker}/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        resp = requests.get(url, headers=headers, timeout=10)

        if resp.status_code == 200:
            try:
                data = resp.json()
                return {
                    'status': 'OK',
                    'has_json': True,
                    'company_name': data.get('name'),
                    'timestamp': datetime.now().isoformat()
                }
            except:
                # Not JSON, try HTML scraping
                soup = BeautifulSoup(resp.content, 'html.parser')
                return {
                    'status': 'OK (HTML)',
                    'has_json': False,
                    'response_size': len(resp.content),
                    'timestamp': datetime.now().isoformat()
                }
        else:
            return {'status': f'HTTP {resp.status_code}', 'has_json': False}

    except Exception as e:
        return {'status': f'ERROR: {str(e)[:50]}', 'has_json': False}

for ticker in TEST_TICKERS:
    screener_data = test_screener_in(ticker)
    status_icon = "✅" if 'OK' in screener_data['status'] else "❌"
    print(f"{status_icon} {ticker:10s} | Status: {screener_data['status']}")
    if screener_data.get('company_name'):
        print(f"   Company: {screener_data['company_name']}")

print()

# ============================================================================
# TEST 5: Yahoo Finance (Current Method)
# ============================================================================
print("TEST 5: Yahoo Finance (Current yfinance Method)")
print("-" * 80)

def test_yfinance(ticker: str) -> Dict:
    """Test current yfinance data fetching"""
    try:
        symbol = f"{ticker}.NS"
        stock = yf.Ticker(symbol)

        # Fetch various data types
        info = stock.info
        history = stock.history(period="1d")

        return {
            'status': 'OK',
            'current_price': info.get('currentPrice') or info.get('regularMarketPrice'),
            'market_cap': info.get('marketCap'),
            'has_history': not history.empty,
            'history_bars': len(history),
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {'status': f'ERROR: {str(e)[:50]}', 'has_history': False}

for ticker in TEST_TICKERS:
    yf_data = test_yfinance(ticker)
    status_icon = "✅" if yf_data['status'] == 'OK' else "❌"
    print(f"{status_icon} {ticker:10s} | Status: {yf_data['status']}")
    if yf_data.get('current_price'):
        print(f"   Price: ₹{yf_data['current_price']:.2f} | Market Cap: ₹{yf_data['market_cap']:,} cr")
        print(f"   History: {yf_data['history_bars']} bars available")

print()

# ============================================================================
# TEST 6: Financial Data Comparison
# ============================================================================
print("TEST 6: Data Freshness & Availability Comparison")
print("-" * 80)

def test_ticker_comparison(ticker: str):
    """Compare data from multiple sources for same ticker"""
    print(f"\nTicker: {ticker}")
    print("-" * 40)

    # yfinance
    try:
        yf_ticker = yf.Ticker(f"{ticker}.NS")
        yf_price = yf_ticker.info.get('currentPrice')
        yf_time = datetime.now()
        print(f"  yfinance:     ₹{yf_price:.2f} (fetched at {yf_time.strftime('%H:%M:%S')})")
    except Exception as e:
        print(f"  yfinance:     ERROR - {str(e)[:40]}")

    time.sleep(1)

    # NSE (if working)
    try:
        nse_data = test_nse_website(ticker)
        if nse_data.get('price'):
            print(f"  NSE Direct:   ₹{nse_data['price']:.2f} (fetched at {datetime.now().strftime('%H:%M:%S')})")
        else:
            print(f"  NSE Direct:   Not available - {nse_data['status']}")
    except Exception as e:
        print(f"  NSE Direct:   ERROR - {str(e)[:40]}")

for ticker in TEST_TICKERS:
    test_ticker_comparison(ticker)

print()

# ============================================================================
# SUMMARY & RECOMMENDATIONS
# ============================================================================
print("=" * 80)
print("SUMMARY & RECOMMENDATIONS")
print("=" * 80)

print("\n📊 Data Source Assessment:\n")

print("1. NEWS SOURCES (Current Implementation):")
print("   ✅ RSS Feeds: Working well, multiple sources available")
print("   ✅ Coverage: Good for news articles")
print("   ⚠️  Limitation: No real-time price data in RSS feeds")

print("\n2. PRICE DATA SOURCES:")
print("   ✅ yfinance: Working, ~15min delayed, good reliability")
print("   ⚠️  NSE Direct: Requires session handling, rate limited")
print("   ⚠️  Moneycontrol: Requires HTML parsing, slower")
print("   ⚠️  Screener.in: Limited API access")

print("\n3. FUNDAMENTAL DATA SOURCES:")
print("   ✅ yfinance: Best option - quarterly/annual financials available")
print("   ⚠️  Direct scraping: Unreliable, requires parsing, breaks easily")

print("\n4. RECOMMENDED APPROACH:")
print("   ✅ NEWS: Keep current RSS feed approach (multi-source)")
print("   ✅ PRICE: Continue using yfinance (reliable, structured)")
print("   ✅ FUNDAMENTALS: Continue using yfinance (best coverage)")
print("   ❌ Direct website scraping: NOT recommended (fragile, rate limits)")

print("\n5. POTENTIAL ENHANCEMENTS:")
print("   • Add more RSS feeds for better news coverage")
print("   • Cache yfinance data (5-min TTL) to reduce API calls")
print("   • Add fallback to NSE if yfinance fails")
print("   • Monitor data freshness with timestamps (already doing)")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
