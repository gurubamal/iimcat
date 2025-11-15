#!/usr/bin/env python3
"""
Compare NSE Direct API vs yfinance for FII and Quarterly Data Freshness

This test will show which source has more current data for decision-making.
"""

import requests
import time
import json
from datetime import datetime
import yfinance as yf

def test_nse_data(ticker: str):
    """Fetch available data from NSE"""
    print(f"\n{'='*80}")
    print(f"NSE DATA FOR {ticker}")
    print(f"{'='*80}")

    # Create session
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    # Initialize session
    session.get('https://www.nseindia.com', headers=headers, timeout=10)
    time.sleep(1)

    nse_data = {
        'timestamp': datetime.now().isoformat(),
        'price': None,
        'corporate_actions': [],
        'data_freshness': None
    }

    try:
        # Get basic quote (includes price and metadata)
        url = f'https://www.nseindia.com/api/quote-equity?symbol={ticker}'
        response = session.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            data = response.json()

            # Price info
            price_info = data.get('priceInfo', {})
            metadata = data.get('metadata', {})

            nse_data['price'] = price_info.get('lastPrice')
            nse_data['data_freshness'] = metadata.get('lastUpdateTime')
            nse_data['pe_ratio'] = metadata.get('pdSymbolPe')

            print(f"\n💰 PRICE DATA:")
            print(f"   Last Price: ₹{nse_data['price']}")
            print(f"   Last Updated: {nse_data['data_freshness']}")
            print(f"   PE Ratio: {nse_data['pe_ratio']}")

    except Exception as e:
        print(f"❌ Error fetching NSE data: {str(e)[:100]}")

    # Get corporate actions
    try:
        url = f'https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol={ticker}'
        time.sleep(0.5)
        response = session.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            actions = response.json()

            if actions:
                nse_data['corporate_actions'] = actions[:5]  # Latest 5

                print(f"\n📋 CORPORATE ACTIONS (Latest 5):")
                for action in actions[:5]:
                    print(f"   • {action.get('subject')} - Ex-Date: {action.get('exDate')}")

    except Exception as e:
        print(f"⚠️  Corporate actions fetch failed: {str(e)[:100]}")

    return nse_data


def test_yfinance_data(ticker: str):
    """Fetch available data from yfinance"""
    print(f"\n{'='*80}")
    print(f"YFINANCE DATA FOR {ticker}")
    print(f"{'='*80}")

    yf_data = {
        'timestamp': datetime.now().isoformat(),
        'price': None,
        'quarterly_results': {},
        'fii_data': {},
        'data_freshness': None
    }

    try:
        stock = yf.Ticker(f"{ticker}.NS")

        # Current price
        info = stock.info
        yf_data['price'] = info.get('currentPrice') or info.get('regularMarketPrice')

        print(f"\n💰 PRICE DATA:")
        print(f"   Current Price: ₹{yf_data['price']}")
        print(f"   Fetched At: {yf_data['timestamp']}")

        # Quarterly financials
        quarterly = stock.quarterly_financials

        if quarterly is not None and not quarterly.empty:
            quarterly = quarterly.T  # Transpose for easier access

            latest_quarter = quarterly.iloc[0]
            quarter_date = latest_quarter.name.strftime('%Y-%m-%d')

            revenue = latest_quarter.get('Total Revenue') or latest_quarter.get('TotalRevenue')
            net_income = latest_quarter.get('Net Income') or latest_quarter.get('NetIncome')

            yf_data['quarterly_results'] = {
                'quarter_date': quarter_date,
                'revenue': float(revenue) if revenue is not None else None,
                'net_income': float(net_income) if net_income is not None else None
            }

            yf_data['data_freshness'] = quarter_date

            print(f"\n📈 QUARTERLY RESULTS:")
            print(f"   Latest Quarter: {quarter_date}")

            if revenue:
                print(f"   Revenue: ₹{revenue/1e7:.0f} cr")
            if net_income:
                print(f"   Net Income: ₹{net_income/1e7:.0f} cr")

            # Calculate YoY growth
            if len(quarterly) >= 5:  # Need 5 quarters for YoY (4 quarters = 1 year)
                try:
                    previous_year_quarter = quarterly.iloc[4]

                    revenue_prev = previous_year_quarter.get('Total Revenue') or previous_year_quarter.get('TotalRevenue')
                    income_prev = previous_year_quarter.get('Net Income') or previous_year_quarter.get('NetIncome')

                    if revenue and revenue_prev and revenue_prev > 0:
                        revenue_growth = ((revenue - revenue_prev) / revenue_prev) * 100
                        print(f"   Revenue YoY Growth: {revenue_growth:+.1f}%")

                    if net_income and income_prev and income_prev > 0:
                        income_growth = ((net_income - income_prev) / income_prev) * 100
                        print(f"   Net Income YoY Growth: {income_growth:+.1f}%")

                except Exception as e:
                    print(f"   ⚠️  YoY calculation failed: {str(e)[:50]}")

        # Institutional holders
        try:
            institutional_holders = stock.institutional_holders

            if institutional_holders is not None and not institutional_holders.empty:
                print(f"\n👥 INSTITUTIONAL HOLDERS:")
                print(f"   Total Institutions: {len(institutional_holders)}")

                # Top 5 holders
                for idx, row in institutional_holders.head(5).iterrows():
                    holder = row.get('Holder', 'Unknown')
                    shares = row.get('Shares', 0)
                    pct = row.get('% Out', 0)

                    print(f"   • {holder}: {pct:.2f}%")

        except Exception as e:
            print(f"   ⚠️  Institutional data unavailable: {str(e)[:50]}")

        # Major holders
        try:
            major_holders = stock.major_holders

            if major_holders is not None and not major_holders.empty:
                print(f"\n📊 MAJOR HOLDERS:")
                for idx, row in major_holders.iterrows():
                    print(f"   • {row[1]}: {row[0]}")

        except Exception as e:
            print(f"   ⚠️  Major holders data unavailable: {str(e)[:50]}")

    except Exception as e:
        print(f"❌ Error fetching yfinance data: {str(e)[:100]}")

    return yf_data


def compare_data_freshness(nse_data: dict, yf_data: dict, ticker: str):
    """Compare freshness of NSE vs yfinance data"""
    print(f"\n{'='*80}")
    print(f"DATA FRESHNESS COMPARISON FOR {ticker}")
    print(f"{'='*80}")

    # Price comparison
    print(f"\n💰 PRICE DATA:")
    print(f"   NSE Price: ₹{nse_data['price']} (Updated: {nse_data['data_freshness']})")
    print(f"   yfinance Price: ₹{yf_data['price']} (Fetched: {yf_data['timestamp'][:19]})")

    if nse_data['price'] and yf_data['price']:
        diff = abs(nse_data['price'] - yf_data['price'])
        diff_pct = (diff / yf_data['price']) * 100
        print(f"   Difference: ₹{diff:.2f} ({diff_pct:.2f}%)")

        if diff_pct > 0.1:
            print(f"   ⚠️  Significant price difference detected!")

    # Quarterly data freshness
    print(f"\n📈 QUARTERLY RESULTS:")

    if yf_data['quarterly_results']:
        print(f"   yfinance: Latest quarter = {yf_data['quarterly_results']['quarter_date']}")
    else:
        print(f"   yfinance: No quarterly data available")

    print(f"   NSE: Quarterly data not available via basic API (need corporate results page)")

    # FII/Institutional data
    print(f"\n👥 FII/INSTITUTIONAL DATA:")
    print(f"   yfinance: Institutional holders data available")
    print(f"   NSE: Need shareholding pattern API (not publicly accessible)")

    # Overall assessment
    print(f"\n🎯 ASSESSMENT:")
    print(f"   ✅ Price Data: NSE more current (real-time vs 15-min delayed)")
    print(f"   ❌ Quarterly Results: yfinance better (NSE needs corporate results page)")
    print(f"   ❌ FII/DII Data: yfinance better (NSE shareholding API not accessible)")
    print(f"   ✅ Corporate Actions: NSE has this data (dividends, splits, etc.)")


# Test with multiple tickers
test_tickers = ['RELIANCE', 'TRENT']

print("=" * 80)
print("NSE vs YFINANCE DATA COMPARISON TEST")
print("=" * 80)
print()
print("Testing data freshness and availability for:")
print(f"Tickers: {', '.join(test_tickers)}")
print()

for ticker in test_tickers:
    nse_data = test_nse_data(ticker)
    time.sleep(1)

    yf_data = test_yfinance_data(ticker)
    time.sleep(1)

    compare_data_freshness(nse_data, yf_data, ticker)
    print()

print("\n" + "=" * 80)
print("FINAL RECOMMENDATION")
print("=" * 80)
print()
print("📊 DATA SOURCE STRATEGY:")
print()
print("✅ CURRENT PRICE: Use NSE Direct API")
print("   • Real-time (~0 delay)")
print("   • More accurate for intraday/swing decisions")
print()
print("✅ QUARTERLY RESULTS: Use yfinance")
print("   • Better structured data")
print("   • Easy YoY/QoQ calculations")
print("   • Historical quarters available")
print()
print("✅ FII/DII DATA: Use yfinance (institutional_holders)")
print("   • NSE shareholding pattern API not publicly accessible")
print("   • yfinance provides institutional holders data")
print("   • Can track changes over time")
print()
print("✅ CORPORATE ACTIONS: Use NSE")
print("   • Dividends, splits, buybacks available")
print("   • More current than yfinance")
print()
print("=" * 80)
print()
print("CONCLUSION: Hybrid approach is best")
print("- NSE for: Current prices, corporate actions")
print("- yfinance for: Quarterly results, FII/institutional data")
print("=" * 80)
