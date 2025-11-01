#!/usr/bin/env python3
"""
Volume and Sector Momentum Module

Fetches real-time volume and sector index data to enhance stock scoring.

Features:
- Volume analysis (current vs 20-day average)
- Sector momentum scoring (PSU, Metal, Energy, etc.)
- Catalyst freshness calculation
- Technical setup validation

Data Sources:
- Yahoo Finance for volume data
- NSE India for sector indices
- Fallback to cached data if APIs fail
"""

from __future__ import annotations

import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import requests
from pathlib import Path

# Try importing yfinance, but make it optional
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    print("⚠️  yfinance not available - volume analysis will use fallback data")


class VolumeAndSectorMomentum:
    """Enhanced scoring with volume and sector momentum"""

    # Sector index mappings (NSE symbols)
    SECTOR_INDICES = {
        'PSU': '^NSEBANK',  # Nifty PSU Bank as proxy
        'METAL': '^CNXMETAL',  # Nifty Metal
        'ENERGY': '^CNXENERGY',  # Nifty Energy
        'BANK': '^NSEBANK',  # Nifty Bank
        'IT': '^CNXIT',  # Nifty IT
        'PHARMA': '^CNXPHARMA',  # Nifty Pharma
        'AUTO': '^CNXAUTO',  # Nifty Auto
        'REALTY': '^CNXREALTY',  # Nifty Realty
        'INFRA': '^CNXINFRA',  # Nifty Infrastructure
    }

    # Ticker to sector mapping (common stocks)
    TICKER_SECTORS = {
        'BHEL': 'PSU',
        'SAIL': 'METAL',
        'NMDC': 'METAL',
        'COALINDIA': 'PSU',
        'ONGC': 'ENERGY',
        'IOC': 'ENERGY',
        'BPCL': 'ENERGY',
        'HPCL': 'ENERGY',
        'POWERGRID': 'PSU',
        'NTPC': 'ENERGY',
        'TATASTEEL': 'METAL',
        'HINDALCO': 'METAL',
        'JSWSTEEL': 'METAL',
        'VEDL': 'METAL',
        'SBIN': 'BANK',
        'PNB': 'BANK',
        'BANKBARODA': 'BANK',
        'HDFCBANK': 'BANK',
        'ICICIBANK': 'BANK',
        'AXISBANK': 'BANK',
        'TCS': 'IT',
        'INFY': 'IT',
        'WIPRO': 'IT',
        'HCLTECH': 'IT',
        'TECHM': 'IT',
        'SUNPHARMA': 'PHARMA',
        'DRREDDY': 'PHARMA',
        'CIPLA': 'PHARMA',
        'DIVISLAB': 'PHARMA',
        'MARUTI': 'AUTO',
        'TATAMOTORS': 'AUTO',
        'M&M': 'AUTO',
        'BAJAJ-AUTO': 'AUTO',
        'BRIGADE': 'REALTY',
        'DLF': 'REALTY',
        'GODREJPROP': 'REALTY',
        'PRESTIGE': 'REALTY',
        'L&T': 'INFRA',
        'ADANIPORTS': 'INFRA',
        'SOLEX': 'ENERGY',  # Solar/renewable
    }

    # Cache directory
    CACHE_DIR = Path(__file__).parent / '.cache'
    CACHE_EXPIRY_HOURS = 2  # Cache valid for 2 hours

    def __init__(self):
        """Initialize with cache directory"""
        self.CACHE_DIR.mkdir(exist_ok=True)
        self.sector_cache: Dict[str, float] = {}
        self.volume_cache: Dict[str, Dict] = {}

    def get_ticker_sector(self, ticker: str) -> str:
        """Get sector for a ticker"""
        ticker = ticker.upper().replace('.NS', '').replace('.BO', '')
        return self.TICKER_SECTORS.get(ticker, 'GENERAL')

    def fetch_sector_momentum(self, sector: str = None) -> Dict[str, float]:
        """
        Fetch sector momentum scores (0-100)

        Returns: Dict of {sector: momentum_score}
        """
        cache_file = self.CACHE_DIR / 'sector_momentum.json'

        # Try loading from cache
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    cached = json.load(f)
                cache_time = datetime.fromisoformat(cached.get('timestamp', '2000-01-01'))
                if datetime.now() - cache_time < timedelta(hours=self.CACHE_EXPIRY_HOURS):
                    print(f"   📊 Using cached sector data (age: {(datetime.now() - cache_time).seconds // 60} min)")
                    return cached.get('data', {})
            except Exception as e:
                print(f"   ⚠️  Cache read error: {e}")

        # Fetch fresh data
        print("   🌐 Fetching live sector momentum data...")
        sector_scores = {}

        if not YFINANCE_AVAILABLE:
            print("   ⚠️  yfinance not available, using default sector scores")
            sector_scores = self._get_default_sector_scores()
        else:
            # Fetch from Yahoo Finance (NSE indices)
            for sector_name, index_symbol in self.SECTOR_INDICES.items():
                try:
                    ticker_obj = yf.Ticker(index_symbol)
                    hist = ticker_obj.history(period='5d')

                    if len(hist) >= 2:
                        # Calculate % change over last day
                        latest_close = hist['Close'].iloc[-1]
                        prev_close = hist['Close'].iloc[-2]
                        pct_change = ((latest_close - prev_close) / prev_close) * 100

                        # Convert to 0-100 score (normalize -5% to +5% range)
                        momentum_score = max(0, min(100, 50 + (pct_change * 10)))
                        sector_scores[sector_name] = round(momentum_score, 1)

                        print(f"      {sector_name}: {pct_change:+.2f}% → Score: {momentum_score:.1f}")
                    else:
                        sector_scores[sector_name] = 50.0  # Neutral

                except Exception as e:
                    print(f"      ⚠️  {sector_name} fetch failed: {e}")
                    sector_scores[sector_name] = 50.0  # Neutral fallback

                time.sleep(0.5)  # Rate limiting

        # Cache the results
        try:
            with open(cache_file, 'w') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'data': sector_scores
                }, f, indent=2)
        except Exception as e:
            print(f"   ⚠️  Cache write error: {e}")

        return sector_scores

    def _get_default_sector_scores(self) -> Dict[str, float]:
        """Default sector scores when API is unavailable"""
        # Based on Oct 30, 2025 observations
        return {
            'PSU': 75.0,      # Strong (BHEL, SAIL performed well)
            'METAL': 72.0,    # Strong (metals led market)
            'ENERGY': 65.0,   # Moderate
            'BANK': 55.0,     # Neutral
            'IT': 50.0,       # Neutral
            'PHARMA': 48.0,   # Slightly weak
            'AUTO': 45.0,     # Weak
            'REALTY': 60.0,   # Moderate (BRIGADE did well)
            'INFRA': 58.0,    # Moderate
            'GENERAL': 50.0,  # Neutral default
        }

    def fetch_volume_data(self, ticker: str) -> Dict:
        """
        Fetch volume data for a ticker

        Returns: {
            'current_volume': float,
            'avg_volume_20d': float,
            'volume_multiplier': float,
            'volume_score': float (0-100)
        }
        """
        ticker = ticker.upper()
        if not ticker.endswith('.NS') and not ticker.endswith('.BO'):
            ticker_ns = f"{ticker}.NS"
        else:
            ticker_ns = ticker

        # Check cache
        if ticker in self.volume_cache:
            return self.volume_cache[ticker]

        if not YFINANCE_AVAILABLE:
            # Default fallback
            return {
                'current_volume': 0,
                'avg_volume_20d': 0,
                'volume_multiplier': 1.0,
                'volume_score': 50.0
            }

        try:
            ticker_obj = yf.Ticker(ticker_ns)
            hist = ticker_obj.history(period='30d')

            if len(hist) >= 2:
                current_volume = hist['Volume'].iloc[-1]
                avg_volume_20d = hist['Volume'].iloc[-20:].mean()

                volume_multiplier = current_volume / avg_volume_20d if avg_volume_20d > 0 else 1.0

                # Convert to 0-100 score
                # 1.0x = 50, 1.5x = 75, 2.0x+ = 100
                volume_score = min(100, 50 + (volume_multiplier - 1.0) * 100)
                volume_score = max(0, volume_score)

                result = {
                    'current_volume': int(current_volume),
                    'avg_volume_20d': int(avg_volume_20d),
                    'volume_multiplier': round(volume_multiplier, 2),
                    'volume_score': round(volume_score, 1)
                }

                self.volume_cache[ticker] = result
                return result

        except Exception as e:
            print(f"      ⚠️  Volume fetch failed for {ticker}: {e}")

        # Fallback
        return {
            'current_volume': 0,
            'avg_volume_20d': 0,
            'volume_multiplier': 1.0,
            'volume_score': 50.0
        }

    def calculate_catalyst_freshness(self, hours_ago: float = 24) -> float:
        """
        Calculate catalyst freshness score (0-100)

        Args:
            hours_ago: How old is the news (hours)

        Returns: Freshness score
        """
        if hours_ago < 24:
            return 100.0
        elif hours_ago < 48:
            return 75.0
        elif hours_ago < 72:
            return 50.0
        else:
            return 25.0

    def calculate_enhanced_final_score(
        self,
        ai_score: float,
        sector_momentum: float,
        volume_score: float,
        catalyst_freshness: float,
        technical_setup: float = 50.0
    ) -> float:
        """
        Calculate final enhanced score using weighted formula

        Formula:
        Final_Score = (AI_Score * 0.35) +
                      (Sector_Momentum * 0.25) +
                      (Volume_Score * 0.20) +
                      (Catalyst_Freshness * 0.15) +
                      (Technical_Setup * 0.05)

        Returns: Enhanced final score (0-100)
        """
        final_score = (
            ai_score * 0.35 +
            sector_momentum * 0.25 +
            volume_score * 0.20 +
            catalyst_freshness * 0.15 +
            technical_setup * 0.05
        )

        return round(final_score, 2)

    def enrich_stock_data(
        self,
        ticker: str,
        ai_score: float,
        news_timestamp: datetime = None
    ) -> Dict:
        """
        Enrich stock data with volume and sector momentum

        Returns: Dict with all enhanced metrics
        """
        # Get sector
        sector = self.get_ticker_sector(ticker)

        # Fetch sector momentum
        if not self.sector_cache:
            self.sector_cache = self.fetch_sector_momentum()
        sector_momentum = self.sector_cache.get(sector, 50.0)

        # Fetch volume data
        print(f"   📊 Fetching volume for {ticker}...")
        volume_data = self.fetch_volume_data(ticker)

        # Calculate catalyst freshness
        if news_timestamp:
            hours_ago = (datetime.now() - news_timestamp).total_seconds() / 3600
        else:
            hours_ago = 24  # Assume 24h old if not specified
        catalyst_freshness = self.calculate_catalyst_freshness(hours_ago)

        # Calculate final score
        final_score = self.calculate_enhanced_final_score(
            ai_score=ai_score,
            sector_momentum=sector_momentum,
            volume_score=volume_data['volume_score'],
            catalyst_freshness=catalyst_freshness,
            technical_setup=50.0  # Default neutral
        )

        return {
            'sector': sector,
            'sector_momentum': sector_momentum,
            'volume_multiplier': volume_data['volume_multiplier'],
            'volume_score': volume_data['volume_score'],
            'catalyst_freshness': catalyst_freshness,
            'enhanced_final_score': final_score,
            'current_volume': volume_data['current_volume'],
            'avg_volume_20d': volume_data['avg_volume_20d'],
        }


def test_module():
    """Test the module with sample data"""
    print("="*80)
    print("🧪 Testing Volume and Sector Momentum Module")
    print("="*80)

    vsm = VolumeAndSectorMomentum()

    # Test sector momentum
    print("\n1️⃣  Testing Sector Momentum Fetch...")
    sectors = vsm.fetch_sector_momentum()
    print(f"\n   Fetched {len(sectors)} sector scores")

    # Test volume data
    print("\n2️⃣  Testing Volume Data Fetch...")
    test_tickers = ['BHEL', 'SAIL', 'SOLEX']
    for ticker in test_tickers:
        print(f"\n   Testing {ticker}:")
        volume_data = vsm.fetch_volume_data(ticker)
        print(f"      Volume Multiplier: {volume_data['volume_multiplier']}x")
        print(f"      Volume Score: {volume_data['volume_score']}")

    # Test enrichment
    print("\n3️⃣  Testing Full Enrichment...")
    enriched = vsm.enrich_stock_data(
        ticker='BHEL',
        ai_score=65.4,
        news_timestamp=datetime.now() - timedelta(hours=12)
    )
    print(f"\n   BHEL Enhanced Metrics:")
    print(f"      Sector: {enriched['sector']}")
    print(f"      Sector Momentum: {enriched['sector_momentum']}")
    print(f"      Volume Score: {enriched['volume_score']}")
    print(f"      Catalyst Freshness: {enriched['catalyst_freshness']}")
    print(f"      Enhanced Final Score: {enriched['enhanced_final_score']} (vs AI Score: 65.4)")

    print("\n" + "="*80)
    print("✅ Module Test Complete")
    print("="*80)


if __name__ == '__main__':
    test_module()
