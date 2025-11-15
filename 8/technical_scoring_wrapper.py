#!/usr/bin/env python3
"""
Technical Scoring Wrapper - Lightweight Integration with Swing Screener

Extracts the most effective components from swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods.py
for hybrid ranking with AI news analysis.

Key Features:
- Quality filters (volume, price, data sufficiency)
- Core indicators (RSI, Bollinger Bands, ATR)
- Opportunity scoring (Tier1/Tier2/Watch classification)
- Fast, vectorized calculations
- Maintains temporal bias protection (uses real-time yfinance data)

Usage:
    from technical_scoring_wrapper import TechnicalScorer

    scorer = TechnicalScorer()
    tech_score = scorer.score_ticker("INFY.NS", period="3mo")

    if tech_score:
        print(f"Score: {tech_score['score']}/100")
        print(f"Tier: {tech_score['tier']}")
        print(f"Setup Quality: {tech_score['setup_quality']}")
"""

import logging
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from typing import Optional, Dict
import os

# Import swing screener components
try:
    from swing_screener_v23_9o_full_TECH_plus_TECHOUT_check_methods import (
        apply_quality_filters,
        calculate_opportunity_score,
        rsi14,
        bollinger_band_position,
        average_true_range
    )
    SWING_SCREENER_AVAILABLE = True
except ImportError:
    SWING_SCREENER_AVAILABLE = False
    logging.warning("⚠️  Swing screener module not available - technical scoring disabled")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalScorer:
    """
    Lightweight technical analysis scorer for stock ranking.

    Integrates with AI news analysis to provide hybrid ranking that combines:
    - AI news sentiment/certainty (realtime_ai_news_analyzer.py)
    - Technical setup quality (this module)

    Maintains temporal bias protection by using real-time yfinance data.
    """

    def __init__(self, cache_ttl: int = 300):
        """
        Initialize technical scorer.

        Args:
            cache_ttl: Cache TTL in seconds (default 5 minutes)
        """
        self.cache = {}
        self.cache_ttl = cache_ttl
        self.enabled = SWING_SCREENER_AVAILABLE and os.getenv('ENABLE_TECHNICAL_SCORING', '0') == '1'

        if self.enabled:
            logger.info("✅ Technical scoring enabled (swing screener integration)")
        else:
            logger.info("ℹ️  Technical scoring disabled (enable with ENABLE_TECHNICAL_SCORING=1)")

    def _normalize_symbol(self, ticker: str) -> str:
        """Ensure ticker has .NS suffix for Indian stocks."""
        ticker = ticker.strip().upper()
        if not ticker.endswith('.NS') and not ticker.endswith('.BO'):
            # Assume NSE if no exchange specified
            ticker += '.NS'
        return ticker

    def _fetch_price_data(self, ticker: str, period: str = "3mo") -> Optional[pd.DataFrame]:
        """
        Fetch real-time price data from yfinance.

        TEMPORAL BIAS PROTECTION:
        - Uses yfinance real-time data (not training data)
        - Explicit timestamp in fetch
        - Data is CURRENT as of fetch time

        Args:
            ticker: Stock symbol (will add .NS if needed)
            period: Historical period (default 3mo for indicators)

        Returns:
            DataFrame with OHLCV data or None if fetch fails
        """
        # Check cache
        cache_key = f"{ticker}_{period}"
        if cache_key in self.cache:
            cached_data, cached_time = self.cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                logger.debug(f"Using cached data for {ticker}")
                return cached_data

        try:
            # Fetch real-time data from yfinance
            stock = yf.Ticker(ticker)
            df = stock.history(period=period)

            if df.empty:
                logger.warning(f"⚠️  No data for {ticker}")
                return None

            # Add fetch timestamp for temporal tracking
            fetch_timestamp = datetime.now()
            logger.debug(f"Fetched {len(df)} bars for {ticker} at {fetch_timestamp.isoformat()}")

            # Cache the result
            self.cache[cache_key] = (df, fetch_timestamp)

            return df

        except Exception as e:
            logger.error(f"❌ Error fetching {ticker}: {e}")
            return None

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators using swing screener functions.

        Args:
            df: OHLCV DataFrame

        Returns:
            DataFrame with RSI, BB_Pos, ATR columns added
        """
        if not SWING_SCREENER_AVAILABLE:
            return df

        try:
            # Calculate indicators using swing screener's proven implementations
            df['RSI'] = rsi14(df['Close'])
            df['BB_Pos'] = bollinger_band_position(df['Close'], period=20, std_dev=2.0)
            # ATR function takes full DataFrame, not separate columns
            df['ATR'] = average_true_range(df, period=14)

            return df

        except Exception as e:
            logger.error(f"❌ Error calculating indicators: {e}")
            return df

    def score_ticker(self, ticker: str, period: str = "3mo") -> Optional[Dict]:
        """
        Score a ticker using technical analysis.

        TEMPORAL BIAS PROTECTION:
        - All data from yfinance (real-time)
        - No reliance on training data
        - Explicit timestamps for traceability

        Args:
            ticker: Stock symbol
            period: Historical period for analysis

        Returns:
            Dictionary with:
                - score: 0-100 normalized score
                - tier: Tier1/Tier2/Watch classification
                - opportunity_score: Raw opportunity score (0-30+)
                - setup_quality: Setup quality rating
                - breakdown: Detailed score breakdown
                - indicators: Current indicator values
                - fetch_time: When data was fetched (temporal tracking)
            Or None if scoring fails
        """
        if not self.enabled:
            return None

        # Normalize symbol
        ticker = self._normalize_symbol(ticker)

        # Fetch real-time price data
        df = self._fetch_price_data(ticker, period)
        if df is None:
            return None

        # Apply quality filters
        if not apply_quality_filters(df, ticker):
            logger.debug(f"❌ {ticker} failed quality filters")
            return {
                'score': 0.0,
                'tier': 'Rejected',
                'opportunity_score': 0.0,
                'setup_quality': 'Poor',
                'breakdown': {},
                'indicators': {},
                'fetch_time': datetime.now().isoformat(),
                'passed_filters': False
            }

        # Calculate indicators
        df = self._calculate_indicators(df)

        # Calculate opportunity score using swing screener logic
        opp_score = calculate_opportunity_score(df, ticker)

        # Normalize to 0-100 scale for hybrid ranking
        # Tier1 threshold is 25, so we scale: score/25 * 100 (capped at 100)
        raw_score = opp_score.get('total_score', 0.0)
        normalized_score = min(100.0, (raw_score / 25.0) * 100.0)

        # Determine setup quality
        tier = opp_score.get('tier', 'Watch')
        if tier == 'Tier1':
            setup_quality = 'Excellent'
        elif tier == 'Tier2':
            setup_quality = 'Good'
        else:
            setup_quality = 'Fair'

        # Extract current indicator values for display
        indicators = {
            'rsi': df['RSI'].iloc[-1] if 'RSI' in df.columns else None,
            'bb_position': df['BB_Pos'].iloc[-1] if 'BB_Pos' in df.columns else None,
            'atr_pct': (df['ATR'].iloc[-1] / df['Close'].iloc[-1] * 100) if 'ATR' in df.columns else None,
            'current_price': df['Close'].iloc[-1],
            'volume_ratio': df['Volume'].iloc[-1] / df['Volume'].tail(20).mean() if len(df) >= 20 else 1.0
        }

        return {
            'score': normalized_score,
            'tier': tier,
            'opportunity_score': raw_score,
            'setup_quality': setup_quality,
            'breakdown': opp_score.get('breakdown', {}),
            'indicators': indicators,
            'fetch_time': datetime.now().isoformat(),
            'passed_filters': True
        }

    def get_hybrid_score(self, ai_score: float, ticker: str, period: str = "3mo",
                         ai_weight: float = 0.6) -> Dict:
        """
        Calculate hybrid score combining AI news analysis + technical setup.

        SCORING STRATEGY:
        - AI news score (0-100): sentiment, certainty, catalysts from recent news
        - Technical score (0-100): RSI, BB, volume, momentum setup quality
        - Hybrid = (ai_weight * AI) + ((1-ai_weight) * Technical)

        Default weights: 60% AI, 40% Technical
        Rationale: News drives immediate moves, but technical confirms sustainability

        Args:
            ai_score: AI news analysis score (0-100)
            ticker: Stock symbol
            period: Historical period for technical analysis
            ai_weight: Weight for AI score (default 0.6, technical gets 0.4)

        Returns:
            Dictionary with:
                - hybrid_score: Combined score (0-100)
                - ai_score: AI component
                - technical_score: Technical component
                - technical_tier: Technical setup tier
                - ranking_boost: How much technical analysis boosted/reduced ranking
                - recommendation: Enhanced recommendation
        """
        # Get technical score
        tech_result = self.score_ticker(ticker, period)

        if not tech_result or not tech_result.get('passed_filters'):
            # Technical scoring unavailable or stock failed filters
            # Use AI score only
            return {
                'hybrid_score': ai_score,
                'ai_score': ai_score,
                'technical_score': None,
                'technical_tier': 'N/A',
                'ranking_boost': 0.0,
                'recommendation': 'AI-only ranking (technical data unavailable)',
                'technical_details': None
            }

        # Calculate hybrid score
        tech_score = tech_result['score']
        hybrid_score = (ai_weight * ai_score) + ((1 - ai_weight) * tech_score)
        ranking_boost = hybrid_score - ai_score

        # Enhanced recommendation
        tier = tech_result['tier']
        setup = tech_result['setup_quality']

        if tier == 'Tier1' and ai_score >= 70:
            recommendation = "🔥 STRONG BUY - Excellent news + Tier1 technical setup"
        elif tier == 'Tier2' and ai_score >= 60:
            recommendation = "✅ BUY - Good news + Tier2 technical confirmation"
        elif tier == 'Watch' and ai_score >= 70:
            recommendation = "⚠️  CAUTION - Strong news but weak technical setup"
        elif tier == 'Tier1' and ai_score < 50:
            recommendation = "🤔 CONSIDER - Weak news but strong technical setup"
        else:
            recommendation = f"📊 {tier} technical setup"

        return {
            'hybrid_score': round(hybrid_score, 2),
            'ai_score': round(ai_score, 2),
            'technical_score': round(tech_score, 2),
            'technical_tier': tier,
            'setup_quality': setup,
            'ranking_boost': round(ranking_boost, 2),
            'recommendation': recommendation,
            'technical_details': tech_result
        }


# Convenience function for quick testing
def quick_score(ticker: str) -> None:
    """Quick test of technical scoring for a ticker."""
    scorer = TechnicalScorer()
    result = scorer.score_ticker(ticker)

    if result:
        print(f"\n{'='*60}")
        print(f"Technical Analysis: {ticker}")
        print(f"{'='*60}")
        print(f"Score: {result['score']:.1f}/100")
        print(f"Tier: {result['tier']}")
        print(f"Setup Quality: {result['setup_quality']}")
        print(f"\nIndicators:")
        print(f"  RSI: {result['indicators']['rsi']:.1f}")
        print(f"  BB Position: {result['indicators']['bb_position']:.1f}")
        print(f"  ATR%: {result['indicators']['atr_pct']:.2f}%")
        print(f"  Volume Ratio: {result['indicators']['volume_ratio']:.2f}x")
        print(f"\nFetched: {result['fetch_time']}")
    else:
        print(f"❌ Could not score {ticker}")


if __name__ == '__main__':
    import sys

    # Test with command line argument
    if len(sys.argv) > 1:
        test_ticker = sys.argv[1]
        quick_score(test_ticker)
    else:
        # Default test
        os.environ['ENABLE_TECHNICAL_SCORING'] = '1'
        quick_score("INFY.NS")
