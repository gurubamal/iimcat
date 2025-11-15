#!/usr/bin/env python3
"""
Test NSE API Endpoints to discover what's available
"""

import requests
import time
import json
from datetime import datetime

# Create session
session = requests.Session()
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Initialize session
print("Initializing NSE session...")
response = session.get('https://www.nseindia.com', headers=headers, timeout=10)
time.sleep(1)
print(f"Session initialized: {response.status_code}")
print()

# Test ticker
ticker = 'RELIANCE'

# List of endpoints to test
endpoints = [
    ('Basic Quote', f'https://www.nseindia.com/api/quote-equity?symbol={ticker}'),
    ('Quote Info', f'https://www.nseindia.com/api/quote-equity-info?symbol={ticker}'),
    ('Corporate Info', f'https://www.nseindia.com/api/corporate-info?symbol={ticker}&series=EQ'),
    ('Corporate Actions', f'https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol={ticker}'),
    ('Financial Results', f'https://www.nseindia.com/api/results-financial?symbol={ticker}'),
    ('Shareholding Pattern', f'https://www.nseindia.com/api/corporates-shareholding?index=equities&symbol={ticker}'),
]

print("=" * 80)
print(f"TESTING NSE ENDPOINTS FOR: {ticker}")
print("=" * 80)
print()

for name, url in endpoints:
    print(f"\nTesting: {name}")
    print(f"URL: {url}")
    print("-" * 80)

    try:
        response = session.get(url, headers=headers, timeout=15)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ SUCCESS - Data received")

                # Show structure
                if isinstance(data, dict):
                    keys = list(data.keys())[:10]  # First 10 keys
                    print(f"Keys: {keys}")

                    # Show interesting fields
                    if 'shareholdingPatterns' in data:
                        print(f"\n📊 SHAREHOLDING DATA FOUND:")
                        patterns = data['shareholdingPatterns']
                        if patterns and len(patterns) > 0:
                            latest = patterns[0]
                            print(f"   Latest Quarter: {latest.get('asOnDate')}")
                            print(f"   Promoter: {latest.get('promoterPercent', 'N/A')}%")
                            print(f"   FII: {latest.get('fiiPercent', 'N/A')}%")
                            print(f"   DII: {latest.get('diiPercent', 'N/A')}%")

                    if 'financialResults' in data:
                        print(f"\n📈 FINANCIAL RESULTS FOUND:")
                        results = data['financialResults']
                        if results and len(results) > 0:
                            latest = results[0]
                            print(f"   Period: {latest.get('period')}")
                            print(f"   Total Income: {latest.get('totalIncome')}")
                            print(f"   Net Profit: {latest.get('netProfitAfterTax')}")

                    if 'priceInfo' in data:
                        print(f"\n💰 PRICE INFO FOUND:")
                        price_info = data['priceInfo']
                        print(f"   Last Price: {price_info.get('lastPrice')}")
                        print(f"   Change: {price_info.get('change')}")

                    # Save full response for inspection
                    filename = f"nse_{name.lower().replace(' ', '_')}_{ticker}.json"
                    with open(filename, 'w') as f:
                        json.dump(data, f, indent=2)
                    print(f"\n💾 Saved full response to: {filename}")

                elif isinstance(data, list):
                    print(f"List with {len(data)} items")
                    if len(data) > 0:
                        print(f"First item keys: {list(data[0].keys())[:10]}")

            except json.JSONDecodeError:
                print(f"❌ Not JSON - Response: {response.text[:200]}")

        elif response.status_code == 404:
            print(f"❌ NOT FOUND - Endpoint doesn't exist or wrong parameters")
        elif response.status_code == 403:
            print(f"❌ FORBIDDEN - Session issue or rate limited")
        else:
            print(f"❌ FAILED - HTTP {response.status_code}")

    except Exception as e:
        print(f"❌ ERROR: {str(e)[:100]}")

    time.sleep(1)  # Rate limiting

print("\n" + "=" * 80)
print("ENDPOINT TESTING COMPLETE")
print("=" * 80)
print("\nCheck generated JSON files for detailed data structures")
