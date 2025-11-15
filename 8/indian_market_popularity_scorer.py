#!/usr/bin/env python3
"""
INDIAN MARKET POPULARITY & REACHABILITY SCORER
===============================================

This module assesses news impact based on:
1. Media source popularity & reach in India
2. Stock popularity (retail interest, liquidity)
3. Seasonal factors (festivals, result season)
4. Coverage density (how many outlets covered it)
5. Language reach (English, Hindi, regional)

Key Insight: In Indian markets, retail sentiment drives 40-60% of volume.
News from high-reach sources or about popular stocks creates MORE impact.

Author: Claude Enhanced System
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class PopularityScore:
    """Comprehensive popularity assessment"""
    media_reach_score: float  # 0-100: Source popularity
    stock_popularity: float  # 0-100: Stock retail interest
    seasonal_multiplier: float  # 0.7-1.5: Time-based factors
    coverage_density: float  # 0-100: Multi-source coverage
    language_reach: float  # 0-100: Language accessibility

    retail_impact_score: float  # 0-100: Combined retail impact
    reasoning: str


class IndianMediaReachScorer:
    """Scores news sources by actual readership/viewership in India"""

    # Based on actual readership data (IRS, BARC, circulation numbers)
    MEDIA_TIERS = {
        # TIER 1: National English - High credibility + reach (10M+ readers/viewers)
        'tier1_english': {
            'domains': [
                'economictimes.indiatimes.com',
                'timesofindia.indiatimes.com',
                'livemint.com',
                'hindustantimes.com',
                'indianexpress.com',
                'thehindubusinessline.com',
                'business-standard.com',
                'moneycontrol.com',
                'ndtv.com',
                'news18.com',
            ],
            'score': 95,
            'reach_millions': 15,
            'credibility': 'very_high',
        },

        # TIER 1A: Global/Premium English (high credibility, moderate Indian reach)
        'tier1a_global': {
            'domains': [
                'reuters.com',
                'bloomberg.com',
                'bqprime.com',
                'wsj.com',
                'ft.com',
                'cnbc.com',
            ],
            'score': 90,
            'reach_millions': 5,  # Lower in India but high credibility
            'credibility': 'very_high',
        },

        # TIER 2: Regional English + Business focused (5-10M reach)
        'tier2_business': {
            'domains': [
                'financialexpress.com',
                'businesstoday.in',
                'cnbctv18.com',
                'zeebiz.com',
                'businessinsider.in',
                'forbes.com',
                'forbesindia.com',
                'entrepreneur.com',
            ],
            'score': 75,
            'reach_millions': 8,
            'credibility': 'high',
        },

        # TIER 3: Hindi/Regional (MASSIVE reach, high word-of-mouth)
        'tier3_hindi_regional': {
            'domains': [
                'aajtak.in',
                'abplive.com',
                'amarujala.com',
                'dainikbhaskar.com',
                'jagran.com',
                'navbharattimes.indiatimes.com',
                'livehindustan.com',
                'patrika.com',
            ],
            'score': 85,  # High score due to massive reach + word-of-mouth
            'reach_millions': 25,  # Hindi belt penetration
            'credibility': 'medium',
        },

        # TIER 4: Industry/Niche (low reach, high credibility for specific sectors)
        'tier4_niche': {
            'domains': [
                'vccircle.com',
                'dealstreetasia.com',
                'inc42.com',
                'yourstory.com',
                'entrackr.com',
            ],
            'score': 60,
            'reach_millions': 2,
            'credibility': 'medium',
        },

        # TIER 5: Local/Small (limited reach)
        'tier5_local': {
            'domains': [
                # Catch-all for unknown sources
            ],
            'score': 40,
            'reach_millions': 1,
            'credibility': 'low',
        },
    }

    # TV Channels bonus (if mentioned in article or source)
    TV_CHANNELS = {
        'CNBC-TV18': 95,
        'ET NOW': 90,
        'Bloomberg Quint': 85,
        'Zee Business': 80,
        'NDTV Profit': 75,
        'Aaj Tak': 90,  # Hindi, massive reach
        'ABP News': 85,
    }

    @classmethod
    def score_source(cls, url: str, article_text: str = "") -> Tuple[float, str, Dict]:
        """Score a news source by its reach and credibility.

        Returns:
            (score, tier_name, metadata)
        """
        if not url:
            return (40.0, "unknown", {"reach": "unknown", "credibility": "unknown"})

        url_lower = url.lower()

        # Extract domain
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', url_lower)
        domain = domain_match.group(1) if domain_match else url_lower

        # Check each tier
        for tier_name, tier_data in cls.MEDIA_TIERS.items():
            for tier_domain in tier_data['domains']:
                if tier_domain in domain or domain in tier_domain:
                    metadata = {
                        'reach_millions': tier_data['reach_millions'],
                        'credibility': tier_data['credibility'],
                        'tier': tier_name,
                    }
                    return (tier_data['score'], tier_name, metadata)

        # Check for TV channel mentions (boosts score)
        tv_bonus = 0
        if article_text:
            for channel, score in cls.TV_CHANNELS.items():
                if channel.lower() in article_text.lower():
                    tv_bonus = max(tv_bonus, score - 50)  # Up to +45 bonus

        # Default to tier 5
        base_score = cls.MEDIA_TIERS['tier5_local']['score']
        final_score = min(100, base_score + tv_bonus)

        metadata = {
            'reach_millions': 1,
            'credibility': 'unknown',
            'tier': 'tier5_local',
            'tv_bonus': tv_bonus,
        }

        return (final_score, "tier5_local", metadata)


class StockPopularityScorer:
    """Scores stocks by retail investor interest and liquidity"""

    # Nifty 50 stocks (most popular, highest retail interest)
    NIFTY_50 = [
        'RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'HINDUNILVR', 'ICICIBANK', 'KOTAKBANK',
        'SBIN', 'BHARTIARTL', 'ITC', 'AXISBANK', 'LT', 'ASIANPAINT', 'MARUTI', 'TITAN',
        'BAJFINANCE', 'HCLTECH', 'WIPRO', 'ULTRACEMCO', 'NESTLEIND', 'SUNPHARMA',
        'NTPC', 'POWERGRID', 'TATAMOTORS', 'ONGC', 'M&M', 'ADANIPORTS', 'TATASTEEL',
        'TECHM', 'INDUSINDBK', 'BAJAJFINSV', 'COALINDIA', 'DRREDDY', 'GRASIM',
        'HEROMOTOCO', 'CIPLA', 'EICHERMOT', 'UPL', 'JSWSTEEL', 'BRITANNIA',
        'DIVISLAB', 'SHREECEM', 'HINDALCO', 'APOLLOHOSP', 'BPCL', 'ADANIENT',
        'SBILIFE', 'TATACONSUM', 'BAJAJ-AUTO', 'LTIM',
    ]

    # High retail interest stocks (heavily traded retail names)
    HIGH_RETAIL_INTEREST = [
        'ADANIGREEN', 'ADANIPOWER', 'YESBANK', 'SUZLON', 'IRCTC', 'ZOMATO',
        'PAYTM', 'NYKAA', 'POLICYBZR', 'DMART', 'IRFC', 'RVNL', 'SJVN',
        'PNB', 'IOB', 'BANKBARODA', 'CANBK', 'RAILTEL', 'SAIL', 'NMDC',
    ]

    # PSU stocks (government-backed, trusted by retail)
    PSU_FAVORITES = [
        'SBI', 'PNB', 'IOB', 'CANBK', 'BANKBARODA', 'NTPC', 'POWERGRID',
        'COALINDIA', 'ONGC', 'BPCL', 'IOCL', 'GAIL', 'NHPC', 'SJVN',
        'IRCTC', 'IRFC', 'RVNL', 'RAILTEL', 'BEL', 'HAL', 'BHEL',
    ]

    @classmethod
    def score_stock(cls, ticker: str, market_cap_cr: Optional[float] = None) -> Tuple[float, str]:
        """Score a stock by retail popularity.

        Returns:
            (score, reasoning)
        """
        ticker_clean = ticker.upper().replace('.NS', '').replace('.BO', '')

        # Nifty 50 = highest popularity
        if ticker_clean in cls.NIFTY_50:
            return (95.0, f"{ticker} is Nifty 50 stock (highest retail interest)")

        # High retail interest stocks
        if ticker_clean in cls.HIGH_RETAIL_INTEREST:
            return (85.0, f"{ticker} has very high retail trading interest")

        # PSU stocks (trusted by retail)
        if ticker_clean in cls.PSU_FAVORITES:
            return (80.0, f"{ticker} is PSU stock (high retail trust)")

        # Market cap based scoring (if available)
        if market_cap_cr:
            if market_cap_cr > 100000:  # > ₹1 lakh crore
                return (90.0, f"{ticker} is large cap (₹{market_cap_cr/100000:.1f}L cr)")
            elif market_cap_cr > 30000:  # > ₹30k crore
                return (75.0, f"{ticker} is mid-large cap (₹{market_cap_cr:,.0f} cr)")
            elif market_cap_cr > 10000:  # > ₹10k crore
                return (60.0, f"{ticker} is mid cap (₹{market_cap_cr:,.0f} cr)")
            elif market_cap_cr > 2000:  # > ₹2k crore
                return (45.0, f"{ticker} is small cap (₹{market_cap_cr:,.0f} cr)")
            else:
                return (30.0, f"{ticker} is micro cap (₹{market_cap_cr:,.0f} cr)")

        # Default: unknown stock
        return (50.0, f"{ticker} popularity unknown (assuming mid-tier)")


class SeasonalFactorScorer:
    """Scores based on seasonal factors affecting Indian retail sentiment"""

    # Festival/Event calendar (peak retail participation times)
    SEASONAL_EVENTS = {
        # Diwali muhurat trading (Oct-Nov) - PEAK retail activity
        'diwali': {'months': [10, 11], 'multiplier': 1.4, 'reason': 'Diwali season (peak retail buying)'},

        # Budget season (Jan-Feb) - High market interest
        'budget': {'months': [1, 2], 'multiplier': 1.3, 'reason': 'Union Budget season (high attention)'},

        # Result season (Apr-May, Jul-Aug, Oct-Nov, Jan-Feb)
        'results_q4': {'months': [4, 5], 'multiplier': 1.25, 'reason': 'Q4 result season'},
        'results_q1': {'months': [7, 8], 'multiplier': 1.25, 'reason': 'Q1 result season'},

        # Year-end (Mar) - Financial year end speculation
        'year_end': {'months': [3], 'multiplier': 1.2, 'reason': 'FY end (portfolio rebalancing)'},

        # Summer lull (Jun) - Lower activity
        'summer': {'months': [6], 'multiplier': 0.9, 'reason': 'Summer season (lower retail activity)'},

        # Pre-Diwali weakness (Sep) - Cautious sentiment
        'pre_diwali': {'months': [9], 'multiplier': 0.85, 'reason': 'Pre-Diwali caution'},
    }

    @classmethod
    def get_seasonal_multiplier(cls, date: Optional[datetime] = None) -> Tuple[float, str]:
        """Get seasonal multiplier for given date.

        Returns:
            (multiplier, reasoning)
        """
        if date is None:
            date = datetime.now()

        month = date.month

        # Check all seasonal events
        for event_name, event_data in cls.SEASONAL_EVENTS.items():
            if month in event_data['months']:
                return (event_data['multiplier'], event_data['reason'])

        # Default: normal season
        return (1.0, "Normal trading season")


class CoverageDensityScorer:
    """Scores based on how many outlets covered the news"""

    @classmethod
    def score_coverage(cls, num_sources: int, source_urls: List[str]) -> Tuple[float, str]:
        """Score based on coverage density.

        Multiple sources = higher confidence that news is impactful.

        Returns:
            (score, reasoning)
        """
        if num_sources >= 10:
            return (95.0, f"Covered by {num_sources} sources (viral/major news)")
        elif num_sources >= 5:
            return (85.0, f"Covered by {num_sources} sources (significant news)")
        elif num_sources >= 3:
            return (70.0, f"Covered by {num_sources} sources (moderate coverage)")
        elif num_sources >= 2:
            return (55.0, f"Covered by {num_sources} sources (limited coverage)")
        else:
            return (40.0, "Single source (limited reach)")


class RetailImpactCalculator:
    """Combines all factors into a comprehensive retail impact score"""

    @staticmethod
    def calculate_retail_impact(
        media_score: float,
        stock_popularity: float,
        seasonal_multiplier: float,
        coverage_density: float,
        language_reach: float = 80.0,  # Default: English (80% accessible)
    ) -> Tuple[float, str]:
        """Calculate composite retail impact score.

        Weights:
        - Media reach: 30% (source matters)
        - Stock popularity: 25% (popular stocks get more attention)
        - Coverage density: 20% (multiple sources = viral)
        - Language reach: 15% (Hindi/regional = word of mouth)
        - Seasonal: 10% (timing matters)

        Returns:
            (retail_impact_score 0-100, reasoning)
        """
        # Base weighted score
        base_score = (
            media_score * 0.30 +
            stock_popularity * 0.25 +
            coverage_density * 0.20 +
            language_reach * 0.15 +
            ((seasonal_multiplier - 1.0) * 100 + 50) * 0.10  # Normalize seasonal
        )

        # Apply seasonal multiplier
        final_score = base_score * seasonal_multiplier

        # Clamp to 0-100
        final_score = max(0, min(100, final_score))

        # Generate reasoning
        reasoning_parts = []
        if media_score >= 85:
            reasoning_parts.append("high-reach media")
        if stock_popularity >= 85:
            reasoning_parts.append("popular stock")
        if coverage_density >= 70:
            reasoning_parts.append("multi-source coverage")
        if language_reach >= 85:
            reasoning_parts.append("high language accessibility")
        if seasonal_multiplier >= 1.2:
            reasoning_parts.append("favorable season")
        elif seasonal_multiplier <= 0.9:
            reasoning_parts.append("seasonal headwind")

        reasoning = f"Retail impact: {final_score:.0f}/100"
        if reasoning_parts:
            reasoning += f" ({', '.join(reasoning_parts)})"

        return (final_score, reasoning)


def assess_popularity(
    ticker: str,
    url: str,
    article_text: str = "",
    market_cap_cr: Optional[float] = None,
    num_sources: int = 1,
    additional_urls: List[str] = None,
    date: Optional[datetime] = None,
) -> PopularityScore:
    """Main function to assess comprehensive popularity/reachability.

    Args:
        ticker: Stock ticker (e.g., 'RELIANCE')
        url: News article URL
        article_text: Full article text (for TV channel detection)
        market_cap_cr: Market cap in crores (optional)
        num_sources: Number of sources covering this news
        additional_urls: List of additional URLs for coverage analysis
        date: Date of news (for seasonal factors)

    Returns:
        PopularityScore with all metrics
    """
    # 1. Media reach score
    media_score, tier, media_meta = IndianMediaReachScorer.score_source(url, article_text)

    # 2. Stock popularity
    stock_score, stock_reason = StockPopularityScorer.score_stock(ticker, market_cap_cr)

    # 3. Seasonal multiplier
    seasonal_mult, seasonal_reason = SeasonalFactorScorer.get_seasonal_multiplier(date)

    # 4. Coverage density
    all_urls = [url] + (additional_urls or [])
    coverage_score, coverage_reason = CoverageDensityScorer.score_coverage(
        num_sources, all_urls
    )

    # 5. Language reach (infer from source)
    # Hindi/regional sources = higher word-of-mouth reach
    if 'hindi' in tier or 'regional' in tier:
        language_reach = 95.0  # Massive word-of-mouth in Hindi belt
    elif tier.startswith('tier1'):
        language_reach = 85.0  # English educated + some Hindi penetration
    else:
        language_reach = 70.0  # Limited reach

    # 6. Calculate composite retail impact
    retail_impact, retail_reason = RetailImpactCalculator.calculate_retail_impact(
        media_score, stock_score, seasonal_mult, coverage_score, language_reach
    )

    # Build comprehensive reasoning
    reasoning = f"""
Retail Impact Analysis:
• Media Reach: {media_score:.0f}/100 ({tier}, {media_meta.get('reach_millions', '?')}M reach)
• Stock Popularity: {stock_score:.0f}/100 ({stock_reason})
• Coverage Density: {coverage_score:.0f}/100 ({coverage_reason})
• Language Reach: {language_reach:.0f}/100
• Seasonal Factor: {seasonal_mult:.2f}x ({seasonal_reason})
• {retail_reason}
""".strip()

    return PopularityScore(
        media_reach_score=media_score,
        stock_popularity=stock_score,
        seasonal_multiplier=seasonal_mult,
        coverage_density=coverage_score,
        language_reach=language_reach,
        retail_impact_score=retail_impact,
        reasoning=reasoning,
    )


# Quick test
if __name__ == "__main__":
    print("🔍 Testing Indian Market Popularity Scorer\n")

    # Test 1: Nifty 50 stock + Tier 1 media + Diwali
    print("=" * 80)
    print("TEST 1: RELIANCE + Economic Times + Diwali Season")
    print("=" * 80)
    score1 = assess_popularity(
        ticker="RELIANCE",
        url="https://economictimes.indiatimes.com/test",
        market_cap_cr=1800000,  # ₹18 lakh crore
        num_sources=5,
        date=datetime(2024, 10, 25),  # Diwali time
    )
    print(score1.reasoning)
    print(f"\n🎯 RETAIL IMPACT SCORE: {score1.retail_impact_score:.1f}/100")
    print()

    # Test 2: Small cap + Tier 5 media + Normal season
    print("=" * 80)
    print("TEST 2: Unknown Small Cap + Unknown Source + Normal Season")
    print("=" * 80)
    score2 = assess_popularity(
        ticker="SMALLCAP",
        url="https://unknownsource.com/article",
        market_cap_cr=500,  # ₹500 crore
        num_sources=1,
        date=datetime(2024, 6, 15),  # Summer lull
    )
    print(score2.reasoning)
    print(f"\n🎯 RETAIL IMPACT SCORE: {score2.retail_impact_score:.1f}/100")
    print()

    # Test 3: High retail interest + Hindi media
    print("=" * 80)
    print("TEST 3: IRCTC + Aaj Tak (Hindi) + Result Season")
    print("=" * 80)
    score3 = assess_popularity(
        ticker="IRCTC",
        url="https://aajtak.in/business/irctc-news",
        num_sources=8,
        date=datetime(2024, 8, 10),  # Q1 results
    )
    print(score3.reasoning)
    print(f"\n🎯 RETAIL IMPACT SCORE: {score3.retail_impact_score:.1f}/100")
