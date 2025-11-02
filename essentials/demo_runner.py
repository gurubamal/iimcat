#!/usr/bin/env python3
"""Demo runner with mock data for testing without yfinance."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add mock data for demonstration
def create_mock_ohlcv(ticker: str, periods: int = 180) -> pd.DataFrame:
    """Create synthetic OHLCV data for testing."""
    np.random.seed(hash(ticker) % 2**32)
    
    # Base prices for major stocks
    base_prices = {
        'RELIANCE.NS': 2850,
        'TCS.NS': 3800,
        'INFY.NS': 2450,
        'HCLTECH.NS': 1800,
        'WIPRO.NS': 450,
    }
    
    base = base_prices.get(ticker, 500)
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='D')
    
    # Generate realistic price movement
    returns = np.random.normal(0.001, 0.015, periods)
    close = base * np.exp(np.cumsum(returns))
    
    high = close * (1 + np.abs(np.random.normal(0, 0.01, periods)))
    low = close * (1 - np.abs(np.random.normal(0, 0.01, periods)))
    volume = np.random.uniform(1e6, 5e7, periods)
    
    return pd.DataFrame({
        'Date': dates,
        'Open': close * (1 + np.random.normal(0, 0.005, periods)),
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume,
        'Adj Close': close
    }).set_index('Date')

print("🚀 FRONTIER-AI DEMO RUNNER (Mock Data Mode)")
print("=" * 80)
print()

# Check if yfinance is accessible
try:
    import yfinance as yf
    print("📡 Testing yfinance connectivity...")
    try:
        # Quick test with short timeout
        test = yf.download('RELIANCE.NS', period='1d', progress=False, timeout=3)
        if test is not None and len(test) > 0:
            print("✓ yfinance working - using live data")
            use_mock = False
        else:
            print("✗ yfinance returned empty - using mock data")
            use_mock = True
    except Exception as e:
        print(f"✗ yfinance timeout/error - using mock data")
        print(f"  Error: {type(e).__name__}")
        use_mock = True
except Exception as e:
    print(f"✗ yfinance not available: {e}")
    use_mock = True

print()

if use_mock:
    print("📊 MOCK DATA MODE")
    print("-" * 80)
    print("Generating synthetic data for demonstration...")
    print()
    
    # Load test tickers
    df_input = pd.read_csv('top25_test.csv')
    tickers = df_input['ticker'].tolist()[:5]  # Use first 5 for demo
    
    print(f"Processing {len(tickers)} tickers with mock data:")
    for ticker in tickers:
        data = create_mock_ohlcv(ticker)
        print(f"  ✓ {ticker:15s} - Price: ₹{data['Close'].iloc[-1]:8.2f}")
    
    print()
    print("✅ Mock data generation successful")
    print()
    print("To run full analysis:")
    print("  python3 frontier_ai_quant_alpha.py --top25 top25_test.csv --output results.csv")
    print()
    print("Note: System will use cached yfinance data or mock data if network unavailable")

else:
    print("📊 LIVE DATA MODE")
    print("-" * 80)
    print("Running with live market data...")
    print()
    
    # Run the full system
    os.system("python3 frontier_ai_quant_alpha.py --top25 top25_test.csv --output results.csv")

