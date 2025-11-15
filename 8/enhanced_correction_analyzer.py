#!/usr/bin/env python3
"""
ENHANCED CORRECTION ANALYZER - Practical Correction Boost Strategy
Implements 6-layer confirmation system for stock rebound identification

Key Features:
- Correction Detection (10-35% pullback with volume confirmation)
- Reversal Confirmation (consolidation, MA cross, RSI signals)
- Oversold Measurement (RSI + BB + volume scoring)
- Fundamental Health Check (earnings, debt, cash assessment)
- Catalyst Strength (AI news mapping)
- Risk Filters (debt, volume, cap, beta, IPO age)
- Market Context Adjustments (bull/bear/VIX awareness)
- Emergency Safeguards (crash/crisis detection)

Usage:
    analyzer = EnhancedCorrectionAnalyzer()
    result = analyzer.analyze_stock(ticker, ai_score, certainty)
"""

import logging
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedCorrectionAnalyzer:
    """
    Main analyzer implementing 6-layer correction boost strategy.

    Architecture:
    1. Detect meaningful correction (10-35% pullback)
    2. Confirm reversal (consolidation + price action)
    3. Measure oversold (technical scoring)
    4. Evaluate fundamentals (financial health)
    5. Calculate catalyst strength (news mapping)
    6. Apply risk filters (safety checks)
    + Market context adjustments
    + Emergency safeguards
    """

    def __init__(self):
        """Initialize analyzer with caching and configuration."""
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.analysis_log = []  # For AI supervision

        # Configuration thresholds
        self.correction_range = (10, 35)  # Valid correction % range
        self.min_decline_days = 5  # Minimum consecutive decline days
        self.min_volume_spike = 1.3  # Minimum volume ratio for confirmation

        # Risk filter thresholds
        self.max_debt_to_equity = 2.0
        self.min_current_ratio = 0.8
        self.min_market_cap_cr = 500  # ₹500 Crore
        self.min_daily_volume = 100000
        self.max_beta_strict = 1.5
        self.min_listing_months = 6

        # Confidence thresholds (market-adjusted)
        self.confidence_threshold_default = 0.30
        self.confidence_threshold_bull = 0.25
        self.confidence_threshold_bear = 0.35

        # Boost factors by confidence tier
        self.boost_factors = {
            'very_high': 20,  # >= 0.85
            'high': 15,       # >= 0.70
            'medium': 10,     # >= 0.55
            'low': 5,         # >= 0.40
            'insufficient': 0 # < 0.40
        }

    def analyze_stock(
        self,
        ticker: str,
        ai_score: float,
        certainty: float,
        df_price: Optional[pd.DataFrame] = None,
        fundamental_data: Optional[Dict] = None,
        market_context: Optional[Dict] = None
    ) -> Dict:
        """
        Main analysis method - orchestrates all layers.

        Args:
            ticker: Stock symbol
            ai_score: AI news sentiment score (0-100)
            certainty: Certainty of AI analysis (0-1)
            df_price: Optional price data (fetches if not provided)
            fundamental_data: Optional fundamental metrics
            market_context: Optional market conditions

        Returns:
            Complete analysis dict with all metrics and boost decision
        """
        analysis = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'ai_score': ai_score,
            'certainty': certainty,
            'layers_passed': [],
            'layers_failed': [],
            'final_decision': 'NO_BOOST',
            'final_score_adjustment': 0.0,
            'reasoning': '',
            'supervision_notes': ''
        }

        try:
            # LAYER 1: CORRECTION DETECTION
            logger.info(f"Analyzing {ticker} - Layer 1: Correction Detection")
            correction_result = self.detect_correction(ticker, df_price)

            if not correction_result['detected']:
                analysis['layers_failed'].append(f"No valid correction: {correction_result.get('reason', '')}")
                analysis['reasoning'] = f"Correction detection failed: {correction_result.get('reason', '')}"
                self._log_analysis(analysis)
                return analysis

            analysis['layers_passed'].append('Correction Detected')
            analysis['correction_pct'] = correction_result['correction_pct']
            analysis['recent_high'] = correction_result['recent_high']
            analysis['decline_days'] = correction_result.get('decline_days', 0)
            analysis['volume_ratio'] = correction_result.get('volume_ratio', 0)

            # LAYER 2: REVERSAL CONFIRMATION (CRITICAL)
            logger.info(f"Analyzing {ticker} - Layer 2: Reversal Confirmation")
            reversal_result = self.confirm_reversal(ticker, df_price or correction_result.get('df'))

            if not reversal_result['reversal_confirmed']:
                analysis['layers_failed'].append(f"Reversal not confirmed: {reversal_result.get('reason', '')}")
                analysis['reasoning'] = f"Stock showing correction but reversal signals insufficient: {reversal_result.get('reason', '')}"
                self._log_analysis(analysis)
                return analysis

            analysis['layers_passed'].append('Reversal Confirmed')
            analysis['reversal_signals'] = reversal_result['reversal_signals']
            analysis['consolidation_range'] = reversal_result.get('consolidation_range', 0)
            analysis['reversal_details'] = reversal_result.get('signals_detail', [])

            # LAYER 3: OVERSOLD MEASUREMENT
            logger.info(f"Analyzing {ticker} - Layer 3: Oversold Measurement")
            df = df_price if df_price is not None and not df_price.empty else correction_result.get('df')
            oversold_score = self.measure_oversold(df)

            analysis['layers_passed'].append('Oversold Measured')
            analysis['oversold_score'] = oversold_score

            # LAYER 4: FUNDAMENTAL HEALTH CHECK
            logger.info(f"Analyzing {ticker} - Layer 4: Fundamental Health")
            fundamental_confidence = self.evaluate_fundamentals(ticker, fundamental_data)

            analysis['layers_passed'].append('Fundamentals Assessed')
            analysis['fundamental_confidence'] = fundamental_confidence

            # LAYER 5: CATALYST STRENGTH
            logger.info(f"Analyzing {ticker} - Layer 5: Catalyst Strength")
            catalyst_strength = self.calculate_catalyst_strength(ai_score, certainty)

            analysis['layers_passed'].append('Catalyst Assessed')
            analysis['catalyst_strength'] = catalyst_strength

            # LAYER 6: CALCULATE CORRECTION CONFIDENCE
            logger.info(f"Analyzing {ticker} - Layer 6: Correction Confidence")
            correction_confidence = self.calculate_correction_confidence(
                oversold_score,
                fundamental_confidence,
                catalyst_strength
            )

            analysis['correction_confidence'] = correction_confidence
            analysis['layers_passed'].append('Confidence Calculated')

            # RISK FILTERS
            logger.info(f"Analyzing {ticker} - Risk Filters")
            risk_filter_data = {
                'ticker': ticker,
                'correction_confidence': correction_confidence
            }
            if fundamental_data:
                risk_filter_data.update(fundamental_data)
            risk_result = self.apply_risk_filters(risk_filter_data)

            if not risk_result['passed']:
                analysis['layers_failed'].append(f"Risk filters failed: {', '.join(risk_result['failures'])}")
                analysis['reasoning'] = f"Stock fails risk management criteria: {', '.join(risk_result['failures'])}"
                self._log_analysis(analysis)
                return analysis

            analysis['layers_passed'].append('Risk Filters Passed')
            analysis['risk_details'] = risk_result['details']

            # MARKET CONTEXT & ADJUSTMENTS
            logger.info(f"Analyzing {ticker} - Market Context")
            market_ctx = market_context or self.detect_market_context()
            context_adjustment = self.apply_market_context_adjustment(correction_confidence, market_ctx)

            adjusted_confidence = context_adjustment['adjusted_confidence']
            adjusted_threshold = context_adjustment['confidence_threshold']
            boost_multiplier = context_adjustment['boost_factor_multiplier']

            analysis['market_context'] = market_ctx.get('regime', 'uncertain')
            analysis['vix_level'] = market_ctx.get('vix_level', 20)
            analysis['confidence_adjustment'] = context_adjustment

            # EMERGENCY SAFEGUARDS
            logger.info(f"Analyzing {ticker} - Emergency Safeguards")
            safeguard_result = self.check_emergency_safeguards(ticker, market_ctx)

            if not safeguard_result['safe_to_boost']:
                analysis['layers_failed'].append(f"Emergency safeguard triggered: {', '.join(safeguard_result['triggered_safeguards'])}")
                analysis['reasoning'] = f"Market emergency conditions detected - boost paused"
                analysis['emergency_level'] = safeguard_result['emergency_level']
                self._log_analysis(analysis)
                return analysis

            analysis['layers_passed'].append('Emergency Safeguards Clear')

            # APPLY BOOST
            logger.info(f"Analyzing {ticker} - Apply Boost")
            boost_result = self.apply_boost(
                hybrid_score=75.0,  # Placeholder - will be used in caller
                correction_confidence=adjusted_confidence,
                market_context=market_ctx,
                safe_to_boost=True
            )

            # Determine final decision
            if adjusted_confidence < adjusted_threshold:
                analysis['final_decision'] = 'BELOW_THRESHOLD'
                analysis['reasoning'] = f"Adjusted confidence ({adjusted_confidence:.2f}) below threshold ({adjusted_threshold:.2f})"
                analysis['layers_failed'].append('Confidence below threshold')
            else:
                analysis['final_decision'] = 'APPLY_BOOST'
                analysis['final_score_adjustment'] = boost_result['boost_applied']
                analysis['boost_tier'] = boost_result['boost_tier']
                analysis['reasoning'] = boost_result['reasoning']
                analysis['layers_passed'].append('Boost Applied')

            # Add supervision notes
            analysis['supervision_notes'] = self._generate_supervision_notes(analysis)

            self._log_analysis(analysis)
            return analysis

        except Exception as e:
            logger.error(f"Error analyzing {ticker}: {e}", exc_info=True)
            analysis['final_decision'] = 'ERROR'
            analysis['reasoning'] = str(e)
            analysis['layers_failed'].append(f"Exception: {str(e)}")
            self._log_analysis(analysis)
            return analysis

    def detect_correction(
        self,
        ticker: str,
        df: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        LAYER 1: Detect meaningful correction (10-35% pullback).

        Returns:
            {
                'detected': bool,
                'correction_pct': float,
                'recent_high': float,
                'current_price': float,
                'decline_days': int,
                'volume_spike': bool,
                'volume_ratio': float,
                'confirmed': bool,
                'reason': str,
                'df': DataFrame
            }
        """
        try:
            # Fetch price history if not provided
            if df is None or df.empty:
                df = yf.Ticker(ticker).history(period='3mo')
                if df.empty:
                    return {
                        'detected': False,
                        'reason': 'No price data available',
                        'df': df
                    }

            # Find recent high (last 90 days)
            recent_high = df['Close'].max()
            current_price = df['Close'].iloc[-1]
            correction_pct = ((recent_high - current_price) / recent_high) * 100

            # Check range: 10-35%
            if not (self.correction_range[0] <= correction_pct <= self.correction_range[1]):
                return {
                    'detected': False,
                    'correction_pct': round(correction_pct, 2),
                    'recent_high': round(recent_high, 2),
                    'current_price': round(current_price, 2),
                    'reason': f'Outside valid range: {correction_pct:.1f}% (need 10-35%)',
                    'df': df
                }

            # Count consecutive decline days
            recent_closes = df['Close'].tail(10).values
            decline_days = 0
            for i in range(len(recent_closes) - 1, 0, -1):
                if recent_closes[i] < recent_closes[i-1]:
                    decline_days += 1
                else:
                    break

            # Check volume spike
            avg_volume_10d = df['Volume'].tail(10).mean()
            current_volume = df['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume_10d if avg_volume_10d > 0 else 1.0
            volume_spike = volume_ratio > self.min_volume_spike

            # Confirmation: decline days + volume spike
            confirmed = decline_days >= self.min_decline_days and volume_spike

            return {
                'detected': True,
                'correction_pct': round(correction_pct, 2),
                'recent_high': round(recent_high, 2),
                'current_price': round(current_price, 2),
                'decline_days': decline_days,
                'volume_spike': volume_spike,
                'volume_ratio': round(volume_ratio, 2),
                'confirmed': confirmed,
                'reason': 'Confirmed' if confirmed else f'Decline {decline_days}d (need {self.min_decline_days}+), vol {volume_ratio:.1f}x',
                'df': df
            }

        except Exception as e:
            logger.warning(f"Correction detection failed for {ticker}: {e}")
            return {'detected': False, 'reason': str(e), 'df': None}

    def confirm_reversal(
        self,
        ticker: str,
        df: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        LAYER 2: Confirm reversal signals (consolidation + price action).
        Critical layer - prevents "falling knife" entries.

        Returns:
            {
                'reversal_confirmed': bool,
                'consolidation_confirmed': bool,
                'consolidation_range': float,
                'reversal_signals': int,
                'signals_detail': List[str],
                'reason': str
            }
        """
        try:
            if df is None or df.empty:
                df = yf.Ticker(ticker).history(period='3mo')
                if df.empty:
                    return {'reversal_confirmed': False, 'reason': 'No data'}

            # 1. CONSOLIDATION CHECK: Trading range < 10%
            recent_closes = df['Close'].tail(10)
            trading_range = (recent_closes.max() - recent_closes.min()) / df['Close'].iloc[-1]
            consolidation_confirmed = trading_range < 0.10
            consolidation_range = round(trading_range * 100, 2)

            # 2. PRICE > 20-DAY MA
            ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
            current_price = df['Close'].iloc[-1]
            price_above_ma20 = current_price > ma20

            # 3. RSI SIGNAL
            rsi = self._calculate_rsi(df['Close'])
            rsi_current = rsi.iloc[-1] if not rsi.empty else None
            rsi_bullish = rsi_current > 50 if rsi_current else False

            # Momentum crossover
            momentum_cross = False
            if len(rsi) >= 2:
                momentum_cross = rsi.iloc[-2] < 50 and rsi.iloc[-1] > 50

            # 4. BULLISH PATTERN
            bullish_pattern = self._detect_bullish_pattern(df)

            # Count signals (need >= 2 of 4)
            reversal_signals = sum([
                consolidation_confirmed,
                price_above_ma20,
                rsi_bullish or momentum_cross,
                bullish_pattern is not None
            ])

            signals_detail = []
            if consolidation_confirmed:
                signals_detail.append(f"Consolidation: {consolidation_range}% range")
            if price_above_ma20:
                signals_detail.append(f"Price above 20-MA (uptrend starting)")
            if rsi_bullish:
                signals_detail.append(f"RSI bullish: {rsi_current:.1f} > 50")
            if momentum_cross:
                signals_detail.append(f"RSI momentum crossing above 50")
            if bullish_pattern:
                signals_detail.append(f"Pattern: {bullish_pattern}")

            reversal_confirmed = reversal_signals >= 2

            return {
                'reversal_confirmed': reversal_confirmed,
                'consolidation_confirmed': consolidation_confirmed,
                'consolidation_range': consolidation_range,
                'reversal_signals': reversal_signals,
                'signals_detail': signals_detail,
                'price_above_ma20': price_above_ma20,
                'rsi_bullish': rsi_bullish,
                'bullish_pattern': bullish_pattern,
                'reason': f'{reversal_signals}/4 signals confirmed'
            }

        except Exception as e:
            logger.warning(f"Reversal confirmation failed for {ticker}: {e}")
            return {'reversal_confirmed': False, 'reason': str(e)}

    def measure_oversold(self, df: pd.DataFrame) -> float:
        """
        LAYER 3: Calculate oversold score (0-100).
        Combines RSI, Bollinger Band position, and volume.
        """
        try:
            if df is None or df.empty:
                return 0.0

            oversold_score = 0.0

            # RSI component (0-30 points)
            rsi = self._calculate_rsi(df['Close'])
            rsi_current = rsi.iloc[-1] if not rsi.empty else 50

            if rsi_current < 25:
                oversold_score += 30
            elif rsi_current < 35:
                oversold_score += 20
            elif rsi_current < 45:
                oversold_score += 10

            # Bollinger Band position (0-25 points)
            bb_position = self._calculate_bb_position(df['Close'])
            bb_current = bb_position.iloc[-1] if not bb_position.empty else 0.5

            if bb_current < 0.15:
                oversold_score += 25
            elif bb_current < 0.35:
                oversold_score += 15
            elif bb_current < 0.50:
                oversold_score += 5

            # Volume anomaly (0-15 points)
            avg_volume_10d = df['Volume'].tail(10).mean()
            current_volume = df['Volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume_10d if avg_volume_10d > 0 else 1.0

            if volume_ratio > 1.5:
                oversold_score += 15
            elif volume_ratio > 1.2:
                oversold_score += 8

            return min(100.0, oversold_score)

        except Exception as e:
            logger.warning(f"Oversold calculation failed: {e}")
            return 0.0

    def evaluate_fundamentals(
        self,
        ticker: str,
        fundamental_data: Optional[Dict] = None
    ) -> float:
        """
        LAYER 4: Evaluate fundamental health (0-100).
        Earnings, debt, profitability, cash position.
        """
        try:
            fundamental_confidence = 0.0

            # Use provided data or fetch from yfinance
            if fundamental_data is None:
                info = yf.Ticker(ticker).info
            else:
                info = fundamental_data

            # Earnings growth (0-25 points)
            earnings_growth = info.get('forwardEps', 0) if isinstance(info, dict) else 0
            if earnings_growth > 0.15:
                fundamental_confidence += 25
            elif earnings_growth > 0.05:
                fundamental_confidence += 15
            elif earnings_growth > 0:
                fundamental_confidence += 5

            # Profitability (0-10 points)
            profit_margin = info.get('profitMargins', 0) if isinstance(info, dict) else 0
            if profit_margin > 0:
                fundamental_confidence += 10

            # Debt levels (0-15 points)
            debt_to_equity = info.get('debtToEquity', 1.5) if isinstance(info, dict) else 1.5
            if debt_to_equity < 0.5:
                fundamental_confidence += 15
            elif debt_to_equity < 1.0:
                fundamental_confidence += 8

            # Quick ratio (0-5 points)
            quick_ratio = info.get('quickRatio', 0.8) if isinstance(info, dict) else 0.8
            if quick_ratio > 0.8:
                fundamental_confidence += 5

            # Dividend yield (0-10 points)
            dividend_yield = info.get('dividendYield', 0) if isinstance(info, dict) else 0
            if dividend_yield > 0:
                fundamental_confidence += 10

            return min(100.0, fundamental_confidence)

        except Exception as e:
            logger.warning(f"Fundamental evaluation failed for {ticker}: {e}")
            return 0.0

    def calculate_catalyst_strength(
        self,
        ai_score: float,
        certainty: float
    ) -> float:
        """
        LAYER 5: Map AI news score to catalyst strength (0-100).
        """
        catalyst_strength = 0.0

        # Base catalyst from AI score
        if ai_score >= 80:
            catalyst_strength = 25
        elif ai_score >= 70:
            catalyst_strength = 18
        elif ai_score >= 60:
            catalyst_strength = 12
        else:
            catalyst_strength = 0  # No significant catalyst

        # Certainty bonus
        if catalyst_strength > 0:
            if certainty >= 0.8:
                catalyst_strength += 10
            elif certainty >= 0.6:
                catalyst_strength += 5

        return min(100.0, catalyst_strength)

    def calculate_correction_confidence(
        self,
        oversold_score: float,
        fundamental_confidence: float,
        catalyst_strength: float
    ) -> float:
        """
        LAYER 6: Combine three factors into correction confidence (0-1).

        Formula:
        confidence = (0.3*oversold + 0.3*fundamentals + 0.4*catalyst) / 100

        Weights:
        - 30% technical (oversold signals)
        - 30% fundamentals (company health)
        - 40% catalyst (news/catalyst trigger - weighted highest as immediate trigger)
        """
        confidence = (
            (0.3 * oversold_score) +
            (0.3 * fundamental_confidence) +
            (0.4 * catalyst_strength)
        ) / 100.0

        return max(0.0, min(1.0, confidence))

    def apply_risk_filters(self, stock_data: Dict) -> Dict:
        """
        Risk filter checks before allowing boost.
        """
        failures = []
        details = {}

        # Debt check
        debt_to_equity = stock_data.get('debt_to_equity', 2.5)
        details['debt_to_equity'] = debt_to_equity
        if debt_to_equity > self.max_debt_to_equity:
            failures.append(f"High debt ({debt_to_equity:.1f} > {self.max_debt_to_equity})")

        # Liquidity check
        current_ratio = stock_data.get('current_ratio', 1.0)
        details['current_ratio'] = current_ratio
        if current_ratio < self.min_current_ratio:
            failures.append(f"Low liquidity ({current_ratio:.2f} < {self.min_current_ratio})")

        # Market cap check
        market_cap_cr = stock_data.get('market_cap_cr', 0)
        details['market_cap_cr'] = market_cap_cr
        if market_cap_cr < self.min_market_cap_cr:
            failures.append(f"Small cap (₹{market_cap_cr}Cr < ₹{self.min_market_cap_cr}Cr)")

        # Volume check
        daily_volume = stock_data.get('daily_volume', 0)
        details['daily_volume'] = daily_volume
        if daily_volume < self.min_daily_volume:
            failures.append(f"Low volume ({daily_volume:.0f} < {self.min_daily_volume})")

        # Beta check
        beta = stock_data.get('beta', 1.0)
        correction_confidence = stock_data.get('correction_confidence', 0.5)
        details['beta'] = beta
        if beta > self.max_beta_strict and correction_confidence < 0.5:
            failures.append(f"High volatility (beta {beta:.1f}) + low confidence")

        # IPO age check
        listed_months = stock_data.get('listed_months', 12)
        details['listed_months'] = listed_months
        if listed_months < self.min_listing_months:
            failures.append(f"Too new ({listed_months}m < {self.min_listing_months}m)")

        return {
            'passed': len(failures) == 0,
            'failures': failures,
            'details': details
        }

    def detect_market_context(self) -> Dict:
        """
        Detect current market regime (bull/bear/uncertain).
        """
        try:
            # Fetch NIFTY50 data
            nifty_data = yf.Ticker('^NSEI').history(period='3mo')

            if nifty_data.empty:
                return {
                    'regime': 'uncertain',
                    'index_momentum': 0.0,
                    'vix_level': 20.0,
                    'market_volatility': 'normal'
                }

            # Calculate momentum
            ma_50 = nifty_data['Close'].rolling(window=50).mean().iloc[-1]
            current_price = nifty_data['Close'].iloc[-1]
            index_momentum = (current_price - ma_50) / ma_50

            # Determine regime
            if index_momentum > 0.05:
                regime = 'bull'
            elif index_momentum < -0.05:
                regime = 'bear'
            else:
                regime = 'uncertain'

            # VIX proxy
            recent_volatility = nifty_data['Close'].pct_change().std() * 100
            vix_level = recent_volatility

            return {
                'regime': regime,
                'index_momentum': round(index_momentum, 3),
                'vix_level': round(vix_level, 1),
                'market_volatility': 'high' if vix_level > 20 else 'normal'
            }

        except Exception as e:
            logger.warning(f"Market context detection failed: {e}")
            return {
                'regime': 'uncertain',
                'index_momentum': 0.0,
                'vix_level': 20.0,
                'market_volatility': 'normal'
            }

    def apply_market_context_adjustment(
        self,
        correction_confidence: float,
        market_context: Dict
    ) -> Dict:
        """
        Adjust confidence thresholds and boost based on market regime.
        """
        regime = market_context.get('regime', 'uncertain')
        vix_level = market_context.get('vix_level', 20)

        adjusted_confidence = correction_confidence
        confidence_threshold = self.confidence_threshold_default
        boost_multiplier = 1.0
        adjustments = []

        # REGIME-BASED ADJUSTMENTS
        if regime == 'bull':
            confidence_threshold = self.confidence_threshold_bull
            boost_multiplier = 1.1
            adjustments.append(f"Bull market → threshold {confidence_threshold}, boost +10%")

        elif regime == 'bear':
            confidence_threshold = self.confidence_threshold_bear
            boost_multiplier = 0.8
            adjustments.append(f"Bear market → threshold {confidence_threshold}, boost -20%")

        else:
            adjustments.append("Uncertain market → neutral adjustments")

        # VOLATILITY ADJUSTMENT
        if vix_level > 30:
            confidence_threshold = min(0.40, confidence_threshold + 0.05)
            boost_multiplier *= 0.8
            adjustments.append(f"High VIX ({vix_level:.1f}) → raise threshold, reduce boost")

        return {
            'adjusted_confidence': round(adjusted_confidence, 3),
            'confidence_threshold': round(confidence_threshold, 3),
            'boost_factor_multiplier': round(boost_multiplier, 2),
            'adjustment_reason': ' | '.join(adjustments)
        }

    def check_emergency_safeguards(
        self,
        ticker: str,
        market_context: Dict
    ) -> Dict:
        """
        Check for emergency conditions (market crash, sector crisis, company crisis).
        """
        triggered = []
        emergency_level = 'none'

        try:
            # MARKET CRASH CHECK
            nifty_data = yf.Ticker('^NSEI').history(period='5d')
            if not nifty_data.empty and len(nifty_data) >= 2:
                recent_close = nifty_data['Close'].iloc[-1]
                prev_close = nifty_data['Close'].iloc[-2]
                daily_change = ((recent_close - prev_close) / prev_close) * 100

                if daily_change < -5:
                    triggered.append(f"Market crash: NIFTY down {daily_change:.1f}%")
                    emergency_level = 'critical'

        except Exception as e:
            logger.warning(f"Emergency safeguard check failed: {e}")

        safe_to_boost = emergency_level != 'critical' and len(triggered) == 0

        return {
            'safe_to_boost': safe_to_boost,
            'triggered_safeguards': triggered,
            'emergency_level': emergency_level
        }

    def apply_boost(
        self,
        hybrid_score: float,
        correction_confidence: float,
        market_context: Dict,
        safe_to_boost: bool
    ) -> Dict:
        """
        Calculate final boost to apply to score.
        """
        if not safe_to_boost:
            return {
                'final_score': hybrid_score,
                'boost_applied': 0.0,
                'boost_factor': 0.0,
                'boost_tier': 'None - Emergency safeguard',
                'reasoning': 'Boost cancelled due to emergency'
            }

        # Get adjusted confidence
        adjusted_result = self.apply_market_context_adjustment(correction_confidence, market_context)
        adjusted_confidence = adjusted_result['adjusted_confidence']
        threshold = adjusted_result['confidence_threshold']
        multiplier = adjusted_result['boost_factor_multiplier']

        # Check threshold
        if adjusted_confidence < threshold:
            return {
                'final_score': hybrid_score,
                'boost_applied': 0.0,
                'boost_factor': 0.0,
                'boost_tier': f'Below threshold',
                'reasoning': f'Confidence {adjusted_confidence:.2f} < threshold {threshold:.2f}'
            }

        # Determine boost tier
        if adjusted_confidence >= 0.85:
            base_boost_factor = self.boost_factors['very_high']
            tier = 'Very High'
        elif adjusted_confidence >= 0.70:
            base_boost_factor = self.boost_factors['high']
            tier = 'High'
        elif adjusted_confidence >= 0.55:
            base_boost_factor = self.boost_factors['medium']
            tier = 'Medium'
        elif adjusted_confidence >= 0.40:
            base_boost_factor = self.boost_factors['low']
            tier = 'Low'
        else:
            return {
                'final_score': hybrid_score,
                'boost_applied': 0.0,
                'boost_factor': 0.0,
                'boost_tier': 'Insufficient',
                'reasoning': f'Confidence below minimum'
            }

        # Apply market multiplier
        boost_factor = base_boost_factor * multiplier
        confidence_boost = adjusted_confidence * boost_factor

        # Calculate final score (capped at 100)
        final_score = min(100.0, hybrid_score + confidence_boost)

        # Avoid over-boosting already high scores
        if hybrid_score >= 85 and confidence_boost > 5:
            confidence_boost = 5
            final_score = min(100.0, hybrid_score + confidence_boost)

        return {
            'final_score': round(final_score, 2),
            'boost_applied': round(confidence_boost, 2),
            'boost_factor': round(boost_factor, 2),
            'boost_tier': tier,
            'reasoning': f'{tier} confidence ({adjusted_confidence:.2f}) → +{confidence_boost:.1f}pt boost'
        }

    # ==================== HELPER METHODS ====================

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator."""
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except:
            return pd.Series([50] * len(prices))

    def _calculate_bb_position(
        self,
        prices: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> pd.Series:
        """Calculate Bollinger Band position (0 at lower band, 1 at upper band)."""
        try:
            sma = prices.rolling(window=period).mean()
            std = prices.rolling(window=period).std()
            lower_band = sma - (std * std_dev)
            upper_band = sma + (std * std_dev)
            bb_position = (prices - lower_band) / (upper_band - lower_band)
            return bb_position.clip(0, 1)
        except:
            return pd.Series([0.5] * len(prices))

    def _detect_bullish_pattern(self, df: pd.DataFrame) -> Optional[str]:
        """
        Detect bullish candlestick patterns.
        Simple detection for: hammer, morning star
        """
        try:
            if len(df) < 2:
                return None

            recent = df.tail(1).iloc[0]
            open_price = recent['Open']
            close_price = recent['Close']
            high_price = recent['High']
            low_price = recent['Low']

            # Hammer pattern: small body, long lower wick
            body = abs(close_price - open_price)
            lower_wick = open_price if open_price < close_price else close_price
            lower_wick_length = lower_wick - low_price
            upper_wick = high_price - (close_price if close_price > open_price else open_price)

            if lower_wick_length > body * 2 and upper_wick < body and close_price > open_price:
                return 'hammer'

            # Morning star (requires 3 bars) - simplified
            if len(df) >= 3:
                # Simple check: gap up and close
                prev_close = df.iloc[-2]['Close']
                if close_price > prev_close and close_price > open_price:
                    return 'morning_star'

            return None

        except:
            return None

    def _log_analysis(self, analysis: Dict):
        """Log analysis for AI supervision."""
        self.analysis_log.append(analysis)

    def _generate_supervision_notes(self, analysis: Dict) -> str:
        """Generate notes for AI supervisor review."""
        notes = []

        # Summary
        decision = analysis.get('final_decision', 'UNKNOWN')
        notes.append(f"Decision: {decision}")

        # Layers passed
        if analysis.get('layers_passed'):
            notes.append(f"✓ Passed: {', '.join(analysis['layers_passed'][:3])}")

        # Layers failed
        if analysis.get('layers_failed'):
            notes.append(f"✗ Failed: {analysis['layers_failed'][0][:50]}")

        # Boost amount
        if analysis.get('final_score_adjustment', 0) > 0:
            notes.append(f"Boost: +{analysis['final_score_adjustment']:.1f}pt")

        # Confidence
        if 'correction_confidence' in analysis:
            notes.append(f"Confidence: {analysis['correction_confidence']:.2f}")

        return " | ".join(notes)

    def get_analysis_log(self) -> List[Dict]:
        """Return all analyses for supervision review."""
        return self.analysis_log

    def clear_analysis_log(self):
        """Clear analysis log."""
        self.analysis_log = []


if __name__ == '__main__':
    # Test
    analyzer = EnhancedCorrectionAnalyzer()
    result = analyzer.analyze_stock(
        ticker='TCS.NS',
        ai_score=75.0,
        certainty=0.85
    )

    print("\n=== CORRECTION ANALYSIS RESULT ===")
    print(f"Decision: {result['final_decision']}")
    print(f"Layers Passed: {', '.join(result.get('layers_passed', []))}")
    print(f"Layers Failed: {', '.join(result.get('layers_failed', []))}")
    print(f"Reasoning: {result.get('reasoning', 'N/A')}")
    print(f"Boost Applied: {result.get('final_score_adjustment', 0):.1f}pt")
