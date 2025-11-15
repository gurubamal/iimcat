#!/usr/bin/env python3
"""
NSE Direct API Data Fetcher

Fetches real-time price data from NSE (National Stock Exchange) Direct API.
Provides more current prices than yfinance (~0 delay vs ~15 min delay).

Features:
- Real-time price fetching from NSE
- Automatic session management
- Smart caching (5-min TTL during market hours)
- Fallback to yfinance if NSE fails
- Market hours detection

Usage:
    from nse_data_fetcher import NSEDataFetcher

    fetcher = NSEDataFetcher()
    data = fetcher.get_realtime_price('RELIANCE')
    print(f"Price: ₹{data['price']}, Source: {data['source']}")
"""

import requests
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
import yfinance as yf
from threading import Lock
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSEDataFetcher:
    """Fetch real-time data from NSE Direct API with yfinance fallback"""

    def __init__(self, cache_ttl: int = 300):
        """
        Initialize NSE data fetcher

        Args:
            cache_ttl: Cache time-to-live in seconds (default: 300 = 5 minutes)
        """
        self.cache_ttl = cache_ttl
        self.session = None
        self.session_created_at = None
        self.cache = {}
        self.cache_lock = Lock()

        # NSE API endpoints
        self.base_url = "https://www.nseindia.com"
        self.quote_url = f"{self.base_url}/api/quote-equity"

        # Headers for NSE requests
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

        logger.info("NSEDataFetcher initialized with %ds cache TTL", cache_ttl)

    def _create_session(self) -> requests.Session:
        """Create a new NSE session with proper cookies"""
        try:
            session = requests.Session()

            # Simpler headers that work
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            }

            # NSE requires initial page visit to set cookies
            logger.debug("Creating NSE session...")
            response = session.get(self.base_url, headers=headers, timeout=10)

            # Critical: Wait for cookies to be set
            time.sleep(1)

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
        # Session expires after 30 minutes
        if self.session is None or \
           (self.session_created_at and (datetime.now() - self.session_created_at) > timedelta(minutes=30)):
            return self._create_session()
        return self.session

    def _is_market_hours(self) -> bool:
        """Check if NSE market is currently open"""
        now = datetime.now()

        # NSE hours: Monday-Friday, 9:15 AM - 3:30 PM IST
        if now.weekday() >= 5:  # Saturday/Sunday
            return False

        market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return market_start <= now <= market_end

    def _get_cached_price(self, ticker: str) -> Optional[Dict]:
        """Get cached price if still valid"""
        with self.cache_lock:
            if ticker in self.cache:
                cached_data = self.cache[ticker]
                age = (datetime.now() - cached_data['cached_at']).total_seconds()

                # Shorter TTL during market hours (5 min), longer outside (15 min)
                ttl = self.cache_ttl if self._is_market_hours() else self.cache_ttl * 3

                if age < ttl:
                    logger.debug(f"Using cached price for {ticker} (age: {age:.0f}s)")
                    return cached_data

        return None

    def _cache_price(self, ticker: str, data: Dict):
        """Cache price data"""
        with self.cache_lock:
            data['cached_at'] = datetime.now()
            self.cache[ticker] = data

    def fetch_nse_price(self, ticker: str) -> Optional[Dict]:
        """
        Fetch real-time price from NSE Direct API

        Args:
            ticker: Stock symbol (e.g., 'RELIANCE', 'TRENT')

        Returns:
            Dict with price data or None if failed
        """
        try:
            session = self._get_session()
            if not session:
                logger.debug(f"No NSE session available for {ticker}")
                return None

            # Small delay to avoid rate limiting
            time.sleep(0.5)

            # Use same simple headers for API call
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
            }

            url = f"{self.quote_url}?symbol={ticker.upper()}"
            response = session.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Extract price info
                price_info = data.get('priceInfo', {})
                pre_open = data.get('preOpenMarket', {})

                if not price_info:
                    logger.warning(f"No price info in NSE response for {ticker}")
                    return None

                result = {
                    'price': price_info.get('lastPrice'),
                    'change': price_info.get('change'),
                    'change_pct': price_info.get('pChange'),
                    'open': price_info.get('open'),
                    'high': price_info.get('intraDayHighLow', {}).get('max'),
                    'low': price_info.get('intraDayHighLow', {}).get('min'),
                    'volume': pre_open.get('totalTradedVolume', 0),
                    'timestamp': datetime.now(),
                    'source': 'NSE_DIRECT',
                    'market_status': 'OPEN' if self._is_market_hours() else 'CLOSED'
                }

                logger.debug(f"NSE: {ticker} = ₹{result['price']} (change: {result['change']})")
                return result

            else:
                logger.warning(f"NSE API returned HTTP {response.status_code} for {ticker}")
                return None

        except requests.exceptions.Timeout:
            logger.warning(f"NSE API timeout for {ticker}")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"NSE API request failed for {ticker}: {str(e)[:100]}")
            return None
        except Exception as e:
            logger.warning(f"NSE fetch error for {ticker}: {str(e)[:100]}")
            return None

    def fetch_yfinance_price(self, ticker: str) -> Optional[Dict]:
        """
        Fetch price from yfinance as fallback

        Args:
            ticker: Stock symbol (e.g., 'RELIANCE', 'TRENT')

        Returns:
            Dict with price data or None if failed
        """
        try:
            symbol = f"{ticker}.NS"
            stock = yf.Ticker(symbol)
            info = stock.info

            # Try multiple price fields
            price = info.get('currentPrice') or \
                    info.get('regularMarketPrice') or \
                    info.get('previousClose')

            if not price:
                logger.warning(f"No price found in yfinance for {ticker}")
                return None

            result = {
                'price': price,
                'change': info.get('regularMarketChange'),
                'change_pct': info.get('regularMarketChangePercent'),
                'open': info.get('regularMarketOpen') or info.get('open'),
                'high': info.get('regularMarketDayHigh') or info.get('dayHigh'),
                'low': info.get('regularMarketDayLow') or info.get('dayLow'),
                'volume': info.get('regularMarketVolume') or info.get('volume'),
                'timestamp': datetime.now(),
                'source': 'YFINANCE',
                'market_status': 'UNKNOWN'
            }

            logger.debug(f"yfinance: {ticker} = ₹{result['price']}")
            return result

        except Exception as e:
            logger.warning(f"yfinance fetch error for {ticker}: {str(e)[:100]}")
            return None

    def get_realtime_price(self, ticker: str, force_nse: bool = False) -> Dict:
        """
        Get most current price with smart source selection

        Priority during market hours:
        1. Check cache (if valid)
        2. Try NSE Direct API (real-time)
        3. Fallback to yfinance (15-min delayed)

        Priority outside market hours:
        1. Check cache (if valid)
        2. Use yfinance (delay doesn't matter)
        3. Fallback to NSE if yfinance fails

        Args:
            ticker: Stock symbol (e.g., 'RELIANCE', 'TRENT')
            force_nse: Force NSE fetch even outside market hours

        Returns:
            Dict with price, source, timestamp, etc.
        """
        # Normalize ticker
        ticker = ticker.upper().replace('.NS', '').replace('.BO', '')

        # Check cache first
        cached = self._get_cached_price(ticker)
        if cached:
            return cached

        result = None
        is_market_open = self._is_market_hours()

        # During market hours OR if forced, prefer NSE
        if is_market_open or force_nse:
            result = self.fetch_nse_price(ticker)

            # If NSE failed, fallback to yfinance
            if not result:
                logger.debug(f"NSE failed for {ticker}, falling back to yfinance")
                result = self.fetch_yfinance_price(ticker)
        else:
            # Outside market hours, prefer yfinance (faster, no session needed)
            result = self.fetch_yfinance_price(ticker)

            # If yfinance failed, try NSE
            if not result:
                logger.debug(f"yfinance failed for {ticker}, trying NSE")
                result = self.fetch_nse_price(ticker)

        # If both failed, return error
        if not result:
            logger.error(f"All price sources failed for {ticker}")
            return {
                'price': None,
                'source': 'FAILED',
                'timestamp': datetime.now(),
                'error': 'All data sources failed'
            }

        # Cache the result
        self._cache_price(ticker, result)

        return result

    def get_multiple_prices(self, tickers: list) -> Dict[str, Dict]:
        """
        Fetch prices for multiple tickers efficiently

        Args:
            tickers: List of stock symbols

        Returns:
            Dict mapping ticker to price data
        """
        results = {}

        for ticker in tickers:
            try:
                results[ticker] = self.get_realtime_price(ticker)
                # Small delay to avoid rate limiting
                time.sleep(0.3)
            except Exception as e:
                logger.warning(f"Failed to fetch {ticker}: {str(e)[:100]}")
                results[ticker] = {
                    'price': None,
                    'source': 'ERROR',
                    'error': str(e)[:100]
                }

        return results

    def clear_cache(self):
        """Clear price cache"""
        with self.cache_lock:
            self.cache.clear()
            logger.debug("Price cache cleared")


# Singleton instance for reuse
_fetcher_instance = None
_fetcher_lock = Lock()

def get_nse_fetcher() -> NSEDataFetcher:
    """Get singleton NSE fetcher instance"""
    global _fetcher_instance

    if _fetcher_instance is None:
        with _fetcher_lock:
            if _fetcher_instance is None:
                _fetcher_instance = NSEDataFetcher()

    return _fetcher_instance


# ============================================================================
# Convenience Functions
# ============================================================================

def get_realtime_price(ticker: str) -> Dict:
    """
    Convenience function to get real-time price

    Args:
        ticker: Stock symbol (e.g., 'RELIANCE', 'TRENT')

    Returns:
        Dict with price, source, timestamp, etc.
    """
    fetcher = get_nse_fetcher()
    return fetcher.get_realtime_price(ticker)


def get_multiple_prices(tickers: list) -> Dict[str, Dict]:
    """
    Convenience function to get multiple prices

    Args:
        tickers: List of stock symbols

    Returns:
        Dict mapping ticker to price data
    """
    fetcher = get_nse_fetcher()
    return fetcher.get_multiple_prices(tickers)


# ============================================================================
# Test/Demo Code
# ============================================================================

if __name__ == '__main__':
    print("=" * 80)
    print("NSE DATA FETCHER TEST")
    print("=" * 80)
    print()

    fetcher = NSEDataFetcher()

    # Test single ticker
    print("Testing RELIANCE...")
    data = fetcher.get_realtime_price('RELIANCE')
    print(f"Price: ₹{data.get('price', 'N/A')}")
    print(f"Source: {data.get('source', 'N/A')}")
    print(f"Timestamp: {data.get('timestamp', 'N/A')}")
    print(f"Market Status: {data.get('market_status', 'N/A')}")
    print()

    # Test multiple tickers
    print("Testing multiple tickers...")
    tickers = ['RELIANCE', 'TRENT', 'INFY']
    results = fetcher.get_multiple_prices(tickers)

    for ticker, data in results.items():
        if data.get('price'):
            print(f"{ticker:10s}: ₹{data['price']:.2f} ({data['source']})")
        else:
            print(f"{ticker:10s}: FAILED ({data.get('source', 'UNKNOWN')})")

    print()
    print("=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
