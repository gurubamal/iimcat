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
        self._meta_cache = {}
        self._sector_cache = {}

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
        market_context: Optional[Dict] = None,
        base_hybrid_score: float = 75.0
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
            base_hybrid_score: Baseline hybrid score used for preview boost calculations

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
            'supervision_notes': '',
            'correction_detected': False,
            'correction_notes': '',
            'risk_filters_passed': None
        }

        try:
            # LAYER 1: CORRECTION DETECTION
            logger.info(f"Analyzing {ticker} - Layer 1: Correction Detection")
            correction_result = self.detect_correction(ticker, df_price)

            df = df_price if df_price is not None and not df_price.empty else correction_result.get('df')

            if not correction_result['detected']:
                analysis['layers_failed'].append(f"No valid correction: {correction_result.get('reason', '')}")
                analysis['reasoning'] = f"Correction detection failed: {correction_result.get('reason', '')}"
                self._log_analysis(analysis)
                return analysis

            if not correction_result.get('confirmed', False):
                analysis['correction_pct'] = correction_result.get('correction_pct')
                analysis['recent_high'] = correction_result.get('recent_high')
                analysis['current_price'] = correction_result.get('current_price')
                analysis['decline_days'] = correction_result.get('decline_days', 0)
                analysis['volume_ratio'] = correction_result.get('volume_ratio', 0)
                analysis['layers_failed'].append(f"Correction not confirmed: {correction_result.get('reason', '')}")
                analysis['reasoning'] = f"Pullback detected but failed confirmation checks: {correction_result.get('reason', '')}"
                self._log_analysis(analysis)
                return analysis

            analysis['layers_passed'].append('Correction Detected')
            analysis['correction_detected'] = True
            analysis['correction_pct'] = correction_result['correction_pct']
            analysis['recent_high'] = correction_result['recent_high']
            analysis['current_price'] = correction_result.get('current_price')
            analysis['decline_days'] = correction_result.get('decline_days', 0)
            analysis['volume_ratio'] = correction_result.get('volume_ratio', 0)
            analysis['volume_spike'] = correction_result.get('volume_spike', False)
            analysis['avg_volume_30d'] = correction_result.get('avg_volume_30d')
            volume_ratio_val = correction_result.get('volume_ratio')
            if volume_ratio_val is None:
                volume_ratio_val = 0.0
            analysis['correction_notes'] = (
                f"{correction_result['correction_pct']:.1f}% off recent high over "
                f"{correction_result.get('decline_days', 0)}d decline | Volume "
                f"{volume_ratio_val:.2f}x avg"
            )
            analysis['correction_depth'] = correction_result.get('correction_pct')
            analysis['correction_detected_at'] = correction_result.get('detected_at')

            # LAYER 2: REVERSAL CONFIRMATION (CRITICAL)
            logger.info(f"Analyzing {ticker} - Layer 2: Reversal Confirmation")
            reversal_result = self.confirm_reversal(ticker, df)

            if not reversal_result['reversal_confirmed']:
                analysis['layers_failed'].append(f"Reversal not confirmed: {reversal_result.get('reason', '')}")
                analysis['reasoning'] = f"Stock showing correction but reversal signals insufficient: {reversal_result.get('reason', '')}"
                analysis['reversal_signals'] = reversal_result.get('reversal_signals', 0)
                analysis['reversal_details'] = reversal_result.get('signals_detail', [])
                self._log_analysis(analysis)
                return analysis

            analysis['layers_passed'].append('Reversal Confirmed')
            analysis['reversal_signals'] = reversal_result['reversal_signals']
            analysis['consolidation_range'] = reversal_result.get('consolidation_range', 0)
            analysis['reversal_details'] = reversal_result.get('signals_detail', [])

            # LAYER 3: OVERSOLD MEASUREMENT
            logger.info(f"Analyzing {ticker} - Layer 3: Oversold Measurement")
            oversold_score, oversold_components = self.measure_oversold(
                df,
                decline_max_volume_ratio=correction_result.get('volume_ratio_decline_max')
            )

            analysis['layers_passed'].append('Oversold Measured')
            analysis['oversold_score'] = oversold_score
            analysis['oversold_components'] = oversold_components

            # LAYER 4: FUNDAMENTAL HEALTH CHECK
            logger.info(f"Analyzing {ticker} - Layer 4: Fundamental Health")
            fundamental_confidence, fundamental_breakdown = self.evaluate_fundamentals(ticker, fundamental_data)

            analysis['layers_passed'].append('Fundamentals Assessed')
            analysis['fundamental_confidence'] = fundamental_confidence
            analysis['fundamental_breakdown'] = fundamental_breakdown

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
            analysis['correction_confidence_components'] = {
                'oversold': oversold_score,
                'fundamental': fundamental_confidence,
                'catalyst': catalyst_strength
            }

            # RISK FILTERS
            logger.info(f"Analyzing {ticker} - Risk Filters")
            metadata = self._get_stock_metadata(ticker, df)
            risk_filter_data = {
                'ticker': ticker,
                'correction_confidence': correction_confidence,
                'debt_to_equity': fundamental_breakdown.get('debt_to_equity'),
                'current_ratio': fundamental_breakdown.get('current_ratio'),
                'market_cap_cr': metadata.get('market_cap_cr'),
                'daily_volume': metadata.get('daily_volume'),
                'avg_volume_30d': metadata.get('avg_volume_30d'),
                'beta': metadata.get('beta'),
                'listed_months': metadata.get('listed_months')
            }
            risk_result = self.apply_risk_filters(risk_filter_data)

            if not risk_result['passed']:
                analysis['layers_failed'].append(f"Risk filters failed: {', '.join(risk_result['failures'])}")
                analysis['reasoning'] = f"Stock fails risk management criteria: {', '.join(risk_result['failures'])}"
                analysis['risk_filters_passed'] = False
                analysis['risk_details'] = risk_result['details']
                self._log_analysis(analysis)
                return analysis

            analysis['layers_passed'].append('Risk Filters Passed')
            analysis['risk_filters_passed'] = True
            analysis['risk_details'] = risk_result['details']

            # MARKET CONTEXT & ADJUSTMENTS
            logger.info(f"Analyzing {ticker} - Market Context")
            market_ctx = market_context or self.detect_market_context()
            context_adjustment = self.apply_market_context_adjustment(correction_confidence, market_ctx)

            adjusted_confidence = context_adjustment['adjusted_confidence']
            adjusted_threshold = context_adjustment['confidence_threshold']
            boost_multiplier = context_adjustment['boost_factor_multiplier']

            analysis['market_context'] = market_ctx.get('regime', 'uncertain')
            analysis['market_context_details'] = market_ctx
            analysis['vix_level'] = market_ctx.get('vix_level', 20)
            analysis['confidence_adjustment'] = context_adjustment
            analysis['correction_confidence_adjusted'] = adjusted_confidence
            analysis['confidence_threshold'] = adjusted_threshold

            # SECTOR-AWARE ADJUSTMENT (±10% based on sector vs 20-DMA)
            sector_adj = self.apply_sector_adjustment(ticker, adjusted_confidence, fundamental_data)
            adjusted_confidence = sector_adj['adjusted_confidence']
            analysis['sector_adjustment'] = sector_adj
            analysis['correction_confidence_adjusted_sector'] = adjusted_confidence

            # EMERGENCY SAFEGUARDS
            logger.info(f"Analyzing {ticker} - Emergency Safeguards")
            safeguard_result = self.check_emergency_safeguards(ticker, market_ctx, fundamental_data)

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
                hybrid_score=base_hybrid_score,
                correction_confidence=adjusted_confidence,
                market_context=market_ctx,
                safe_to_boost=True,
                context_adjustment=context_adjustment
            )
            analysis['boost_preview'] = boost_result

            # Determine final decision
            if adjusted_confidence < adjusted_threshold:
                analysis['final_decision'] = 'BELOW_THRESHOLD'
                analysis['reasoning'] = (
                    f"Adjusted confidence {adjusted_confidence:.2f} below requirement {adjusted_threshold:.2f}"
                )
                analysis['layers_failed'].append('Confidence below threshold')
            else:
                analysis['final_decision'] = 'APPLY_BOOST'
                analysis['final_score_adjustment'] = boost_result['boost_applied']
                analysis['boost_tier'] = boost_result['boost_tier']
                analysis['reasoning'] = boost_result['reasoning']
                analysis['boost_preview'] = boost_result
                analysis['layers_passed'].append('Boost Applied')

            analysis['final_score_preview'] = boost_result.get('final_score', base_hybrid_score)
            analysis['confidence_threshold'] = adjusted_threshold
            analysis['reasoning'] = analysis['reasoning'] or (
                f"Correction {analysis['correction_pct']:.1f}% | Oversold {oversold_score:.1f} | "
                f"Fundamental {fundamental_confidence:.1f} | Catalyst {catalyst_strength:.1f}"
            )

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
            normalized = self._normalize_symbol(ticker)

            # Fetch price history if not provided
            if df is None or df.empty:
                df = yf.Ticker(normalized).history(period='6mo')
                if df.empty:
                    return {
                        'detected': False,
                        'reason': 'No price data available',
                        'df': df
                    }

            df = df.copy()
            df = df[df['Close'].notna()]
            if df.empty:
                return {'detected': False, 'reason': 'Insufficient close data', 'df': df}

            recent_window = df.tail(90) if len(df) >= 90 else df
            recent_high = float(recent_window['Close'].max())
            recent_high_date = recent_window['Close'].idxmax()
            current_price = float(df['Close'].iloc[-1])

            if recent_high == 0:
                return {'detected': False, 'reason': 'Invalid price data (recent high is zero)', 'df': df}

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

            # Identify decline window from recent high date to latest bar
            try:
                high_idx = df.index.get_loc(recent_high_date)
            except Exception:
                # Fallback: use last 90 window relative position
                high_idx = len(df) - len(recent_window) + recent_window.index.get_loc(recent_high_date)

            decline_slice = df.iloc[high_idx:]

            # Longest consecutive decline streak within decline window
            longest_decline_streak = self._count_longest_decline_streak(decline_slice['Close'])

            # Volume spike within decline window against rolling averages
            vol_mean_30 = df['Volume'].rolling(30).mean()
            if vol_mean_30.isna().all():
                vol_mean_30 = df['Volume'].rolling(10).mean()
            ratios = []
            for i in range(high_idx, len(df)):
                denom = vol_mean_30.iloc[i]
                if denom and not np.isnan(denom) and denom > 0:
                    ratios.append(df['Volume'].iloc[i] / denom)
            volume_ratio_decline_max = max(ratios) if ratios else 1.0
            # Preserve existing last-day ratio for display
            avg_volume_30d = df['Volume'].tail(30).mean()
            if np.isnan(avg_volume_30d) or avg_volume_30d == 0:
                avg_volume_30d = df['Volume'].tail(10).mean()
            current_volume = float(df['Volume'].iloc[-1])
            volume_ratio = current_volume / avg_volume_30d if avg_volume_30d and not np.isnan(avg_volume_30d) else 1.0

            volume_spike = volume_ratio_decline_max >= self.min_volume_spike

            confirmed = (longest_decline_streak >= self.min_decline_days) and volume_spike

            reason = 'Confirmed'
            if not confirmed:
                reason = (
                    f"Decline streak {longest_decline_streak}d (need {self.min_decline_days}+), "
                    f"volume {volume_ratio:.2f}x"
                )

            return {
                'detected': True,
                'correction_pct': round(correction_pct, 2),
                'recent_high': round(recent_high, 2),
                'recent_high_date': recent_high_date.isoformat() if isinstance(recent_high_date, pd.Timestamp) else None,
                'current_price': round(current_price, 2),
                'decline_days': int(longest_decline_streak),
                'volume_spike': bool(volume_spike),
                'volume_ratio': round(volume_ratio, 2),
                'avg_volume_30d': float(avg_volume_30d) if avg_volume_30d and not np.isnan(avg_volume_30d) else None,
                'volume_ratio_decline_max': round(volume_ratio_decline_max, 2),
                'confirmed': confirmed,
                'reason': reason,
                'df': df,
                'detected_at': datetime.now().isoformat()
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
                df = yf.Ticker(self._normalize_symbol(ticker)).history(period='3mo')
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

            # Technical reversal signals (excluding consolidation)
            technical_signals = [
                ('Price above 20-MA', price_above_ma20),
                ('RSI momentum turn', (rsi_bullish or momentum_cross)),
                ('Bullish pattern', bullish_pattern is not None)
            ]
            active_signals = [label for label, is_active in technical_signals if is_active]

            # Confirmation logic: consolidation + ≥1 other, or ≥2 technical signals
            reversal_confirmed = False
            if consolidation_confirmed and len(active_signals) >= 1:
                reversal_confirmed = True
            elif len(active_signals) >= 2:
                reversal_confirmed = True

            reversal_signals = len(active_signals) + (1 if consolidation_confirmed else 0)

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

            return {
                'reversal_confirmed': reversal_confirmed,
                'consolidation_confirmed': consolidation_confirmed,
                'consolidation_range': consolidation_range,
                'reversal_signals': reversal_signals,
                'signals_detail': signals_detail,
                'price_above_ma20': price_above_ma20,
                'rsi_bullish': rsi_bullish,
                'bullish_pattern': bullish_pattern,
                'reason': (
                    'Consolidation + signal' if consolidation_confirmed and active_signals
                    else f"{len(active_signals)} technical signal(s)"
                )
            }

        except Exception as e:
            logger.warning(f"Reversal confirmation failed for {ticker}: {e}")
            return {'reversal_confirmed': False, 'reason': str(e)}

    def measure_oversold(self, df: pd.DataFrame, decline_max_volume_ratio: Optional[float] = None) -> Tuple[float, Dict[str, float]]:
        """
        LAYER 3: Calculate oversold score (0-100).
        Combines RSI, Bollinger Band position, and volume.
        """
        try:
            if df is None or df.empty:
                return 0.0, {}

            oversold_score = 0.0
            components: Dict[str, float] = {}

            # RSI component (0-30 points)
            rsi = self._calculate_rsi(df['Close'])
            rsi_current = rsi.iloc[-1] if not rsi.empty else 50

            if rsi_current < 25:
                oversold_score += 30
                components['rsi'] = 30
            elif rsi_current < 35:
                oversold_score += 20
                components['rsi'] = 20
            elif rsi_current < 45:
                oversold_score += 10
                components['rsi'] = 10
            else:
                components['rsi'] = 0

            # Bollinger Band position (0-25 points)
            bb_position = self._calculate_bb_position(df['Close'])
            bb_current = bb_position.iloc[-1] if not bb_position.empty else 0.5

            if bb_current < 0.15:
                oversold_score += 25
                components['bollinger'] = 25
            elif bb_current < 0.35:
                oversold_score += 15
                components['bollinger'] = 15
            elif bb_current < 0.50:
                oversold_score += 5
                components['bollinger'] = 5
            else:
                components['bollinger'] = 0

            # Volume anomaly: prefer decline-window spike if provided
            if isinstance(decline_max_volume_ratio, (int, float)) and decline_max_volume_ratio > 0:
                volume_ratio = float(decline_max_volume_ratio)
                if volume_ratio > 2.0:
                    oversold_score += 20
                    components['volume'] = 20
                elif volume_ratio > 1.5:
                    oversold_score += 15
                    components['volume'] = 15
                elif volume_ratio > 1.3:
                    oversold_score += 10
                    components['volume'] = 10
                elif volume_ratio > 1.1:
                    oversold_score += 5
                    components['volume'] = 5
                else:
                    components['volume'] = 0
            else:
                avg_volume_10d = df['Volume'].tail(10).mean()
                current_volume = df['Volume'].iloc[-1]
                volume_ratio = current_volume / avg_volume_10d if avg_volume_10d > 0 else 1.0
                if volume_ratio > 1.5:
                    oversold_score += 15
                    components['volume'] = 15
                elif volume_ratio > 1.2:
                    oversold_score += 8
                    components['volume'] = 8
                else:
                    components['volume'] = 0

            components['rsi_current'] = float(rsi_current) if rsi_current is not None else None
            components['bb_position'] = float(bb_current) if bb_current is not None else None
            components['volume_ratio'] = round(volume_ratio, 2)

            oversold_score = min(100.0, oversold_score)
            return oversold_score, components

        except Exception as e:
            logger.warning(f"Oversold calculation failed: {e}")
            return 0.0, {}

    def evaluate_fundamentals(
        self,
        ticker: str,
        fundamental_data: Optional[Dict] = None
    ) -> Tuple[float, Dict[str, Optional[float]]]:
        """
        LAYER 4: Evaluate fundamental health (0-100).
        Earnings, debt, profitability, cash position.
        Returns score and component breakdown.
        """
        breakdown: Dict[str, Optional[float]] = {
            'data_source': None,
            'earnings_growth_yoy': None,
            'is_profitable': None,
            'debt_to_equity': None,
            'current_ratio': None,
            'net_worth_positive': None,
            'has_shareholder_rewards': False,
            'score_components': {}
        }

        try:
            fundamental_confidence = 0.0
            score_components: Dict[str, float] = {}

            def _apply_score(component: str, points: float) -> None:
                if points > 0:
                    score_components[component] = points

            # Use provided data when available; otherwise fall back to yfinance info
            data_used = 'fundamental_data_fetcher'

            earnings_growth = None
            is_profitable = None
            debt_to_equity = None
            current_ratio = None
            net_worth_positive = None
            has_shareholder_rewards = False

            if fundamental_data and isinstance(fundamental_data, dict) and fundamental_data.get('data_available'):
                quarterly = fundamental_data.get('quarterly') or {}
                annual = fundamental_data.get('annual') or {}
                health = fundamental_data.get('financial_health') or {}

                earnings_growth = quarterly.get('earnings_yoy_growth_pct')
                if earnings_growth is None:
                    earnings_growth = annual.get('earnings_yoy_growth_pct')

                is_profitable = health.get('is_profitable')
                debt_to_equity = health.get('debt_to_equity')
                current_ratio = health.get('current_ratio')
                net_worth_positive = health.get('net_worth_positive')

                corporate_actions = fundamental_data.get('corporate_actions') or []
                has_shareholder_rewards = self._detect_shareholder_rewards(corporate_actions, health)
            else:
                data_used = 'yfinance_info'
                info = yf.Ticker(self._normalize_symbol(ticker)).info
                earnings_growth = info.get('earningsQuarterlyGrowth')
                if earnings_growth is not None:
                    earnings_growth *= 100  # Convert to %
                else:
                    eps_growth = info.get('earningsGrowth')
                    if eps_growth is not None:
                        earnings_growth = eps_growth * 100

                is_profitable = info.get('profitMargins', 0) is not None and info.get('profitMargins', 0) > 0
                debt_to_equity = info.get('debtToEquity')
                current_ratio = info.get('currentRatio') or info.get('quickRatio')
                net_worth_positive = None  # Not directly available reliably
                dividend_yield = info.get('dividendYield')
                if dividend_yield:
                    has_shareholder_rewards = dividend_yield > 0

            # Earnings growth (0-25 points)
            breakdown['earnings_growth_yoy'] = earnings_growth
            if isinstance(earnings_growth, (int, float)):
                if earnings_growth > 15:
                    fundamental_confidence += 25
                    _apply_score('earnings_growth', 25)
                elif earnings_growth > 5:
                    fundamental_confidence += 15
                    _apply_score('earnings_growth', 15)
                elif earnings_growth > 0:
                    fundamental_confidence += 10
                    _apply_score('earnings_growth', 10)

            # Profitability (0-10 points)
            breakdown['is_profitable'] = bool(is_profitable) if is_profitable is not None else None
            if is_profitable:
                fundamental_confidence += 10
                _apply_score('profitability', 10)

            # Debt levels (0-15 points)
            breakdown['debt_to_equity'] = debt_to_equity
            if isinstance(debt_to_equity, (int, float)):
                if debt_to_equity < 0.5:
                    fundamental_confidence += 15
                    _apply_score('debt_to_equity', 15)
                elif debt_to_equity < 1.0:
                    fundamental_confidence += 8
                    _apply_score('debt_to_equity', 8)

            # Liquidity (current ratio proxy)
            breakdown['current_ratio'] = current_ratio
            if isinstance(current_ratio, (int, float)) and current_ratio >= 0.8:
                fundamental_confidence += 5
                _apply_score('liquidity', 5)

            # Net worth positive (0-5 points)
            breakdown['net_worth_positive'] = net_worth_positive
            if net_worth_positive:
                fundamental_confidence += 5
                _apply_score('net_worth', 5)

            # Shareholder rewards (dividend/buyback) (0-10 points)
            breakdown['has_shareholder_rewards'] = bool(has_shareholder_rewards)
            if has_shareholder_rewards:
                fundamental_confidence += 10
                _apply_score('shareholder_rewards', 10)

            breakdown['score_components'] = score_components
            breakdown['data_source'] = data_used

            return min(100.0, fundamental_confidence), breakdown

        except Exception as e:
            logger.warning(f"Fundamental evaluation failed for {ticker}: {e}")
            breakdown['error'] = str(e)
            return 0.0, breakdown

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
        details: Dict[str, Optional[float]] = {}
        violations: List[str] = []
        missing_metrics: List[str] = []

        def _sanitize(value: Optional[float]) -> Optional[float]:
            if value is None:
                return None
            if isinstance(value, float) and np.isnan(value):
                return None
            return value

        # Debt check
        debt_to_equity = _sanitize(stock_data.get('debt_to_equity'))
        details['debt_to_equity'] = debt_to_equity
        if debt_to_equity is None:
            missing_metrics.append('debt_to_equity')
        elif debt_to_equity > self.max_debt_to_equity:
            failures.append(f"High debt ({debt_to_equity:.1f} > {self.max_debt_to_equity})")
            violations.append('debt_to_equity')

        # Liquidity check
        current_ratio = _sanitize(stock_data.get('current_ratio'))
        details['current_ratio'] = current_ratio
        if current_ratio is None:
            missing_metrics.append('current_ratio')
        elif current_ratio < self.min_current_ratio:
            failures.append(f"Low liquidity ({current_ratio:.2f} < {self.min_current_ratio})")
            violations.append('current_ratio')

        # Market cap check
        market_cap_cr = _sanitize(stock_data.get('market_cap_cr'))
        details['market_cap_cr'] = market_cap_cr
        if market_cap_cr is None:
            missing_metrics.append('market_cap_cr')
        elif market_cap_cr < self.min_market_cap_cr:
            failures.append(f"Small cap (₹{market_cap_cr:.0f}Cr < ₹{self.min_market_cap_cr}Cr)")
            violations.append('market_cap')

        # Volume check
        daily_volume = _sanitize(stock_data.get('daily_volume'))
        details['daily_volume'] = daily_volume
        if daily_volume is None:
            missing_metrics.append('daily_volume')
        elif daily_volume < self.min_daily_volume:
            failures.append(f"Low volume ({daily_volume:.0f} < {self.min_daily_volume})")
            violations.append('liquidity')

        avg_volume_30d = _sanitize(stock_data.get('avg_volume_30d'))
        details['avg_volume_30d'] = avg_volume_30d
        if avg_volume_30d is None:
            missing_metrics.append('avg_volume_30d')

        # Beta check
        beta = _sanitize(stock_data.get('beta'))
        correction_confidence = stock_data.get('correction_confidence', 0.5)
        details['beta'] = beta
        if beta is None:
            missing_metrics.append('beta')
        elif beta > self.max_beta_strict and correction_confidence < 0.5:
            failures.append(f"High volatility (beta {beta:.1f}) + low confidence")
            violations.append('volatility')

        # IPO age check
        listed_months = _sanitize(stock_data.get('listed_months'))
        details['listed_months'] = listed_months
        if listed_months is None:
            missing_metrics.append('listed_months')
        elif listed_months < self.min_listing_months:
            failures.append(f"Too new ({listed_months}m < {self.min_listing_months}m)")
            violations.append('listing_age')

        if missing_metrics:
            details['missing_metrics'] = list(dict.fromkeys(missing_metrics))

        return {
            'passed': len(failures) == 0,
            'failures': failures,
            'details': {**details, 'violations': violations}
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
            adjusted_confidence = min(1.0, adjusted_confidence * 1.05)
            adjustments.append(f"Bull market → threshold {confidence_threshold}, confidence +5%, boost +10%")

        elif regime == 'bear':
            confidence_threshold = self.confidence_threshold_bear
            boost_multiplier = 0.8
            adjusted_confidence = max(0.0, adjusted_confidence * 0.9)
            adjustments.append(f"Bear market → threshold {confidence_threshold}, confidence -10%, boost -20%")

        else:
            adjustments.append("Uncertain market → neutral adjustments")

        # VOLATILITY ADJUSTMENT
        if vix_level > 30:
            confidence_threshold = min(0.40, confidence_threshold + 0.05)
            boost_multiplier *= 0.8
            adjusted_confidence = max(0.0, adjusted_confidence * 0.9)
            adjustments.append(f"High VIX ({vix_level:.1f}) → confidence -10%, threshold raised, boost reduced")

        return {
            'adjusted_confidence': round(adjusted_confidence, 3),
            'confidence_threshold': round(confidence_threshold, 3),
            'boost_factor_multiplier': round(boost_multiplier, 2),
            'adjustment_reason': ' | '.join(adjustments)
        }

    def check_emergency_safeguards(
        self,
        ticker: str,
        market_context: Dict,
        fundamental_data: Optional[Dict] = None
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

            # SECTOR CRISIS CHECK (7-day sector drop > 10%)
            sector_info = self._get_sector_context(ticker, fundamental_data)
            sector_perf = sector_info.get('performance') if sector_info else None
            if sector_perf and isinstance(sector_perf.get('7_day_return'), (int, float)):
                if sector_perf['7_day_return'] < -0.10:
                    sym = sector_info.get('symbol') or 'SECTOR'
                    triggered.append(f"Sector crisis: {sym} -{sector_perf['7_day_return']*100:.1f}% (7d)")

            # COMPANY CRISIS CHECK (earnings miss >20% or high-severity news)
            if isinstance(fundamental_data, dict):
                # Try multiple common keys for earnings surprise
                earnings = fundamental_data.get('earnings') or fundamental_data.get('quarterly') or {}
                surprise = earnings.get('surprise_pct') or earnings.get('earnings_surprise_pct')
                if isinstance(surprise, (int, float)) and surprise < -20:
                    triggered.append(f"Company crisis: earnings surprise {surprise:.1f}%")
                # News severity / scandal flags
                news = fundamental_data.get('news') or {}
                severity = news.get('severity') or fundamental_data.get('news_severity')
                scandal = news.get('has_scandal') or fundamental_data.get('has_scandal') or fundamental_data.get('major_scandal_detected')
                if isinstance(severity, (int, float)) and severity > 80:
                    triggered.append("Company crisis: high-severity negative news")
                if scandal:
                    triggered.append("Company crisis: scandal/regulatory issue")

        except Exception as e:
            logger.warning(f"Emergency safeguard check failed: {e}")

        safe_to_boost = emergency_level != 'critical' and len(triggered) == 0

        return {
            'safe_to_boost': safe_to_boost,
            'triggered_safeguards': triggered,
            'emergency_level': emergency_level
        }

    # ==================== SECTOR CONTEXT & ADJUSTMENTS ====================

    def _infer_sector(self, ticker: str, fundamental_data: Optional[Dict]) -> Optional[str]:
        """Infer sector from provided data or yfinance info."""
        # Try provided data
        if isinstance(fundamental_data, dict):
            for k in ('sector', 'industry', 'sector_name'):
                v = fundamental_data.get(k) or (
                    (fundamental_data.get('financial_health') or {}).get(k)
                )
                if isinstance(v, str) and v:
                    return v
        # Fallback to yfinance info
        try:
            info = yf.Ticker(self._normalize_symbol(ticker)).info
            sector = info.get('sector') or info.get('industry')
            if isinstance(sector, str) and sector:
                return sector
        except Exception:
            pass
        return None

    def _map_sector_to_symbols(self, sector: str) -> List[str]:
        """Return a list of candidate Yahoo Finance symbols for a given sector."""
        s = (sector or '').upper()
        mapping: Dict[str, List[str]] = {
            'BANK': ['BANKBEES.NS', '^NSEBANK', '^NIFTYBANK', '^BANK'],
            'BANKING': ['BANKBEES.NS', '^NSEBANK', '^NIFTYBANK'],
            'FINANCIAL SERVICES': ['^CNXFINANCE', '^NIFTYFIN', 'FINNIFTY.NS'],
            'FINANCE': ['^CNXFINANCE', '^NIFTYFIN', 'FINNIFTY.NS'],
            'TECHNOLOGY': ['ITBEES.NS', '^CNXIT', '^NIFTYIT'],
            'SOFTWARE': ['ITBEES.NS', '^CNXIT', '^NIFTYIT'],
            'IT': ['ITBEES.NS', '^CNXIT', '^NIFTYIT'],
            'PHARMACEUTICALS': ['PHARMABEES.NS', '^CNXPHARMA', '^NIFTYPHARMA'],
            'PHARMACEUTICAL': ['PHARMABEES.NS', '^CNXPHARMA', '^NIFTYPHARMA'],
            'PHARMA': ['PHARMABEES.NS', '^CNXPHARMA', '^NIFTYPHARMA'],
            'AUTOMOBILE': ['^CNXAUTO', '^NIFTYAUTO'],
            'AUTO': ['^CNXAUTO', '^NIFTYAUTO'],
            'FMCG': ['^CNXFMCG', '^NIFTYFMCG'],
            'CONSUMER GOODS': ['^CNXFMCG', '^NIFTYFMCG'],
            'METAL': ['^CNXMETAL', '^NIFTYMETAL'],
            'METALS': ['^CNXMETAL', '^NIFTYMETAL'],
            'ENERGY': ['^CNXENERGY', '^NIFTYENERGY'],
            'OIL': ['^CNXENERGY', '^NIFTYENERGY'],
            'REAL ESTATE': ['^CNXREALTY', '^NIFTYREALTY'],
            'REALTY': ['^CNXREALTY', '^NIFTYREALTY'],
        }
        # Default fallback to headline index if sector unmapped
        return mapping.get(s, ['^NSEI'])

    def _get_sector_performance_data(self, symbols: List[str]) -> Optional[Dict[str, float]]:
        """Fetch sector performance snapshot for the first symbol with data."""
        now = datetime.now()
        for sym in symbols:
            # Cache check
            cached = self._sector_cache.get(sym)
            if cached and (now - cached['ts']).total_seconds() < self.cache_ttl:
                return cached['data']
            try:
                hist = yf.Ticker(sym).history(period='1mo')
                if hist is None or hist.empty:
                    continue
                current_price = float(hist['Close'].iloc[-1])
                # 7-day return (or first/last if <7)
                idx_ref = -7 if len(hist) >= 7 else 0
                week_ago_price = float(hist['Close'].iloc[idx_ref])
                week_return = (current_price - week_ago_price) / week_ago_price if week_ago_price else 0.0
                # vs 20-DMA momentum
                ma_20 = hist['Close'].rolling(20).mean().iloc[-1] if len(hist) >= 20 else current_price
                vs_20ma = (current_price - ma_20) / ma_20 if ma_20 else 0.0
                data = {
                    'symbol': sym,
                    '7_day_return': float(week_return),
                    'vs_20ma': float(vs_20ma),
                    'current_price': current_price
                }
                # Cache
                self._sector_cache[sym] = {'ts': now, 'data': data}
                return data
            except Exception:
                continue
        return None

    def apply_sector_adjustment(
        self,
        ticker: str,
        correction_confidence: float,
        fundamental_data: Optional[Dict] = None
    ) -> Dict:
        """
        Adjust correction confidence ±10% based on sector momentum vs 20-DMA.
        Returns dict with adjusted_confidence, factor, and context details.
        """
        sector = self._infer_sector(ticker, fundamental_data)
        if not sector:
            return {
                'adjusted_confidence': round(correction_confidence, 3),
                'factor': 1.0,
                'sector': None,
                'symbol': None,
                'vs_20ma': None,
                '7_day_return': None,
                'reason': 'Sector unknown - no adjustment'
            }

        symbols = self._map_sector_to_symbols(sector)
        perf = self._get_sector_performance_data(symbols)
        if not perf:
            return {
                'adjusted_confidence': round(correction_confidence, 3),
                'factor': 1.0,
                'sector': sector,
                'symbol': None,
                'vs_20ma': None,
                '7_day_return': None,
                'reason': 'Sector data unavailable'
            }

        vs_20 = perf.get('vs_20ma', 0.0)
        if vs_20 < -0.05:
            factor = 0.9
            reason = f"Sector weak vs 20MA ({vs_20:.2%}) → -10% confidence"
        elif vs_20 > 0.05:
            factor = 1.1
            reason = f"Sector strong vs 20MA ({vs_20:.2%}) → +10% confidence"
        else:
            factor = 1.0
            reason = 'Sector neutral - no adjustment'

        adjusted = max(0.0, min(1.0, correction_confidence * factor))
        return {
            'adjusted_confidence': round(adjusted, 3),
            'factor': factor,
            'sector': sector,
            'symbol': perf.get('symbol'),
            'vs_20ma': round(vs_20, 4),
            '7_day_return': round(perf.get('7_day_return', 0.0), 4),
            'reason': reason
        }

    def _get_sector_context(self, ticker: str, fundamental_data: Optional[Dict]) -> Dict:
        """Return sector symbol and performance metrics for a ticker."""
        sector = self._infer_sector(ticker, fundamental_data)
        if not sector:
            return {'sector': None, 'symbol': None, 'performance': None}
        symbols = self._map_sector_to_symbols(sector)
        perf = self._get_sector_performance_data(symbols)
        symbol = perf.get('symbol') if perf else None
        return {'sector': sector, 'symbol': symbol, 'performance': perf}

    def apply_boost(
        self,
        hybrid_score: float,
        correction_confidence: float,
        market_context: Dict,
        safe_to_boost: bool,
        context_adjustment: Optional[Dict] = None
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

        # Get adjusted confidence (reuse adjustment if provided)
        if context_adjustment is not None:
            adjusted_result = context_adjustment
        else:
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
                'reasoning': f'Confidence {adjusted_confidence:.2f} < threshold {threshold:.2f}',
                'context_adjustment': adjusted_result
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
            'reasoning': f'{tier} confidence ({adjusted_confidence:.2f}) → +{confidence_boost:.1f}pt boost',
            'context_adjustment': adjusted_result
        }

    # ==================== HELPER METHODS ====================

    def _normalize_symbol(self, ticker: str) -> str:
        """Normalize ticker for yfinance (default NSE suffix if missing)."""
        if not ticker:
            return ticker
        ticker = ticker.strip()
        if '.' in ticker:
            return ticker
        return f"{ticker}.NS"

    def _count_longest_decline_streak(self, prices: pd.Series) -> int:
        """Count longest consecutive decline streak within provided series."""
        if prices is None or len(prices) < 2:
            return 0

        longest = 0
        current = 0
        values = prices.values

        for idx in range(1, len(values)):
            if values[idx] < values[idx - 1]:
                current += 1
                longest = max(longest, current)
            else:
                current = 0

        return longest

    def _detect_shareholder_rewards(
        self,
        corporate_actions: Optional[List],
        financial_health: Optional[Dict]
    ) -> bool:
        """Detect recent dividends or buybacks from provided data."""
        if corporate_actions:
            for action in corporate_actions:
                text = str(action).lower()
                if any(keyword in text for keyword in ['dividend', 'buyback', 'buy-back', 'repurchase']):
                    return True

        if isinstance(financial_health, dict):
            if financial_health.get('has_recent_dividend') or financial_health.get('recent_dividend'):
                return True
            if financial_health.get('share_buyback_announced'):
                return True

        return False

    def _get_stock_metadata(
        self,
        ticker: str,
        df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Optional[float]]:
        """Fetch stock metadata required for risk filters with caching."""
        key = ('meta', ticker.upper())
        now = datetime.now()
        cached = self.cache.get(key)

        if cached and (now - cached['timestamp']).total_seconds() < self.cache_ttl:
            metadata = cached['data'].copy()
        else:
            metadata: Dict[str, Optional[float]] = {
                'market_cap_cr': None,
                'avg_volume_30d': None,
                'beta': None,
                'listed_months': None,
                'daily_volume': None
            }

            try:
                info = yf.Ticker(self._normalize_symbol(ticker)).info

                market_cap = info.get('marketCap')
                if isinstance(market_cap, (int, float)) and market_cap > 0:
                    metadata['market_cap_cr'] = market_cap / 10_000_000  # Convert to ₹ Crore

                avg_vol = info.get('averageDailyVolume10Day') or info.get('averageVolume') or info.get('averageVolume10days')
                if isinstance(avg_vol, (int, float)) and avg_vol > 0:
                    metadata['avg_volume_30d'] = float(avg_vol)

                beta = info.get('beta') or info.get('beta3Year')
                if isinstance(beta, (int, float)):
                    metadata['beta'] = float(beta)

                first_trade = info.get('firstTradeDateEpochUtc') or info.get('firstTradeDate') or info.get('ipoDate')
                listed_months = None
                if isinstance(first_trade, (int, float)) and first_trade > 0:
                    first_trade_dt = datetime.utcfromtimestamp(first_trade)
                    listed_months = max(0, (datetime.now() - first_trade_dt).days // 30)
                elif isinstance(first_trade, str):
                    try:
                        if len(first_trade) == 10:
                            first_trade_dt = datetime.strptime(first_trade, "%Y-%m-%d")
                        else:
                            first_trade_dt = datetime.fromisoformat(first_trade)
                        listed_months = max(0, (datetime.now() - first_trade_dt).days // 30)
                    except Exception:
                        listed_months = None
                metadata['listed_months'] = listed_months

            except Exception as exc:
                logger.debug(f"Metadata fetch failed for {ticker}: {exc}")

            self.cache[key] = {'timestamp': now, 'data': metadata.copy()}
            metadata = metadata.copy()

        # Update with fresh volume data if dataframe provided
        if df is not None and not df.empty:
            metadata = metadata.copy()
            try:
                metadata['daily_volume'] = float(df['Volume'].iloc[-1])
                rolling_avg = df['Volume'].tail(30).mean()
                if not np.isnan(rolling_avg):
                    metadata['avg_volume_30d'] = float(rolling_avg)
            except Exception:
                pass

        if metadata.get('daily_volume') is None and metadata.get('avg_volume_30d') is not None:
            metadata['daily_volume'] = metadata['avg_volume_30d']

        return metadata

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
