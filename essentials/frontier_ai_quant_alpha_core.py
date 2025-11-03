#!/usr/bin/env python3
"""
FRONTIER-AI QUANT ALPHA CORE ENGINE
HFT-Inspired swing-trading signal generation with LLM-based news scoring.

Features: 20+ quant metrics, news parsing, risk management, gate filters.
Formula: Alpha = 25×MOM20 + 15×MOM60 + 10×RVOL + 10×SqueezeBO + 10×PBZ + 20×NewsScore + 5×TrendBonus
"""

import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta
import warnings
import json
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import os

ALLOW_OFFLINE_OHLCV_CACHE = os.getenv('ALLOW_OFFLINE_OHLCV_CACHE', '0').strip() == '1'

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class QuantFeatures:
    """Container for computed quant metrics."""
    ticker: str
    close: float
    atr20: float
    momentum_3: float
    momentum_20: float
    momentum_60: float
    rvol: float
    squeeze: bool
    squeeze_bb_width: float
    breakout: int
    pbz: float
    trend_sma50: bool
    trend_sma200: bool
    rsi_14: float
    macd_signal: float
    ema20: float
    setup_earnings_gap_high_rvol: bool
    setup_base_breakout_squeeze: bool
    setup_pullback_20ema: bool
    
    def to_dict(self) -> Dict:
        return self.__dict__

@dataclass
class NewsMetrics:
    """Container for news-based metrics."""
    catalyst_type: str
    catalyst_count: int
    deal_value_cr: float
    sentiment: str
    certainty: int
    source_quality: str
    headline_text: str
    
    def to_dict(self) -> Dict:
        return self.__dict__

class QuantFeatureEngine:
    """Compute 20+ HFT-style quant features."""
    
    def __init__(self, lookback_days: int = 180, use_demo: bool = False):
        self.lookback_days = lookback_days
        self.use_demo = use_demo
        self.config = self._load_config()
        self.allow_offline_cache = ALLOW_OFFLINE_OHLCV_CACHE
        self.offline_dir = Path(os.getenv('OFFLINE_OHLCV_DIR', 'offline_ohlcv_cache'))
        if self.allow_offline_cache:
            self.offline_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self) -> Dict:
        try:
            import json, os
            path = os.getenv('EXPERT_PLAYBOOK_PATH', 'expert_playbook.json')
            if path and os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
        
    def _generate_demo_data(self, ticker: str) -> pd.DataFrame:
        """Generate REALISTIC synthetic OHLCV data that mimics market behavior."""
        np.random.seed(hash(ticker) % 2**32)
        base_prices = {
            'RELIANCE.NS': 2850, 'TCS.NS': 3800, 'INFY.NS': 2450,
            'HCLTECH.NS': 1800, 'WIPRO.NS': 450, 'ICICIBANK.NS': 950,
            'HDFC.NS': 2500, 'AXISBANK.NS': 1100, 'BAJAJFINSV.NS': 1500,
            'MARUTI.NS': 11000, 'NESTLEIND.NS': 25000, 'SUNPHARMA.NS': 800,
        }
        base = base_prices.get(ticker, 500)
        periods = self.lookback_days
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='D')
        
        # Create realistic trending market (some winners, some losers)
        trend_type = hash(ticker) % 3
        if trend_type == 0:
            # Strong uptrend (like earnings winners)
            trend = np.linspace(1.0, 1.45, periods)  # +45% trend
            momentum_boost = 0.8
        elif trend_type == 1:
            # Downtrend (like selloffs)
            trend = np.linspace(1.0, 0.85, periods)  # -15% trend
            momentum_boost = -0.4
        else:
            # Consolidation with micro trends
            trend = 1.0 + 0.15 * np.sin(np.linspace(0, 4*np.pi, periods))
            momentum_boost = 0.2
        
        # Generate price with trend + volatility + momentum
        returns = np.random.normal(0.008 + momentum_boost * 0.01, 0.028, periods)
        close = base * trend * np.exp(np.cumsum(returns))
        
        # Realistic OHLC: higher volatility on trending days
        trend_strength = np.abs(np.diff(np.concatenate([[0], trend])))
        intraday_vol = 0.015 + trend_strength[1:] * 0.05  # Higher vol on trend days
        intraday_vol = np.concatenate([[intraday_vol[0]], intraday_vol])
        
        high = close * (1 + intraday_vol)
        low = close * (1 - intraday_vol * 0.7)
        
        # Volume spikes on strong moves
        base_vol = np.random.uniform(8e6, 25e7, periods)
        
        # Create volume surge on breakout candles
        close_pct_change = np.concatenate([[0], (close[1:] - close[:-1]) / close[:-1]])
        vol_multiplier = np.where(np.abs(close_pct_change) > 0.02, 2.5, 1.0)  # +2.5x on big moves
        volume = base_vol * vol_multiplier
        
        # Realistic open (small gaps)
        opens = []
        for i in range(periods):
            if i == 0:
                opens.append(base)
            else:
                gap = np.random.uniform(-0.8, 1.2) / 100  # -0.8% to +1.2% gap
                opens.append(close[i-1] * (1 + gap))
        
        df = pd.DataFrame({
            'Date': dates, 'Open': opens,
            'High': high, 'Low': low, 'Close': close, 'Volume': volume,
            'Adj Close': close
        }).set_index('Date')
        return df

    def _offline_path(self, ticker: str) -> Path:
        safe = ticker.replace('/', '_')
        return self.offline_dir / f"{safe}.csv"

    def _save_offline_data(self, ticker: str, df: pd.DataFrame) -> None:
        if not self.allow_offline_cache:
            return
        try:
            path = self._offline_path(ticker)
            df.to_csv(path, index=True, index_label='Date')
        except Exception as exc:
            logger.warning(f"⚠️  Unable to persist OHLCV cache for %s: %s", ticker, exc)

    def _load_offline_data(self, ticker: str) -> Optional[pd.DataFrame]:
        if not self.allow_offline_cache:
            return None
        path = self._offline_path(ticker)
        if not path.exists():
            return None
        try:
            df = pd.read_csv(path, parse_dates=['Date'], index_col='Date')
            return df
        except Exception as exc:
            logger.warning(f"⚠️  Failed to load cached OHLCV for %s: %s", ticker, exc)
            return None

    def fetch_data(self, ticker: str) -> Optional[pd.DataFrame]:
        """Fetch OHLCV data from yfinance with offline cache fallback."""
        if self.use_demo:
            try:
                return self._generate_demo_data(ticker)
            except Exception as e:
                logger.warning(f"Demo data generation failed for {ticker}: {e}")
                return None

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=self.lookback_days)
            df = yf.download(ticker, start=start_date, end=end_date, progress=False, timeout=10)
            if df is None or len(df) < 60 or len(df.columns) == 0:
                logger.warning(f"{ticker}: Insufficient live data ({len(df) if df is not None else 0} bars)")
                return self._load_offline_data(ticker)

            # Flatten multi-index columns produced by some yfinance versions
            try:
                import pandas as _pd
                if isinstance(df.columns, _pd.MultiIndex):
                    cols = {}
                    for name in ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']:
                        try:
                            cols[name] = df[(name, ticker)]
                        except Exception:
                            try:
                                cols[name] = df[name]
                            except Exception:
                                pass
                    if cols:
                        df = _pd.DataFrame(cols, index=df.index)
            except Exception:
                pass

            df['ticker'] = ticker
            self._save_offline_data(ticker, df)
            return df
        except Exception as e:
            logger.warning(f"Failed to fetch {ticker} live data ({type(e).__name__}); using cached OHLCV if available")
            cached = self._load_offline_data(ticker)
            if cached is not None:
                return cached
            if self.use_demo:
                try:
                    return self._generate_demo_data(ticker)
                except Exception:
                    return None
            return None
    
    def compute_atr(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Average True Range (volatility)."""
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        # Create DataFrame and take max per row
        tr_df = pd.DataFrame({'hl': high_low, 'hc': high_close, 'lc': low_close})
        tr = tr_df.max(axis=1)
        return tr.rolling(period).mean()
    
    def compute_momentum(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Rate of change momentum (0-100 scale)."""
        roc = ((df['Close'] - df['Close'].shift(period)) / df['Close'].shift(period)) * 100
        # Normalize to 0-100 using tanh
        normalized = np.tanh(roc / 20) * 50 + 50
        return pd.Series(normalized.values, index=df.index)  # Explicitly create Series with index
    
    def compute_rvol(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Relative Volume (current / average)."""
        vol_avg = df['Volume'].rolling(period).mean()
        return df['Volume'] / vol_avg
    
    def compute_squeeze(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """Bollinger Band + Keltner squeeze detection."""
        # BB: 20-SMA ± 2×StdDev
        sma = df['Close'].rolling(20).mean()
        std = df['Close'].rolling(20).std()
        bb_upper = sma + 2 * std
        bb_lower = sma - 2 * std
        bb_width = bb_upper - bb_lower
        
        # Keltner: SMA ± 1.5×ATR (simplified)
        atr = self.compute_atr(df, 20)
        kc_upper = sma + 1.5 * atr
        kc_lower = sma - 1.5 * atr
        
        # Squeeze: BB inside KC
        squeeze = (bb_upper < kc_upper) & (bb_lower > kc_lower)
        return squeeze, bb_width
    
    def compute_breakout(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Breakout signal: 1=up, -1=down, 0=none."""
        high_20 = df['High'].rolling(period).max()
        low_20 = df['Low'].rolling(period).min()
        breakout = pd.Series(0, index=df.index)
        breakout[df['Close'] > high_20.shift(1)] = 1
        breakout[df['Close'] < low_20.shift(1)] = -1
        return breakout
    
    def compute_pbz(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Price-to-Bollinger-Zone (0-100, 50=middle)."""
        sma = df['Close'].rolling(period).mean()
        std = df['Close'].rolling(period).std()
        upper = sma + 2 * std
        lower = sma - 2 * std
        pbz = 50 + 50 * (df['Close'] - sma) / (upper - lower)
        return pbz.clip(0, 100)
    
    def compute_rsi(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Relative Strength Index."""
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def compute_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series]:
        """MACD and Signal line."""
        ema_fast = df['Close'].ewm(span=fast).mean()
        ema_slow = df['Close'].ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        return macd, signal_line
    
    def compute_ema(self, df: pd.DataFrame, span: int = 20) -> pd.Series:
        return df['Close'].ewm(span=span).mean()
    
    def compute_gap_pct(self, df: pd.DataFrame) -> pd.Series:
        prev_close = df['Close'].shift(1)
        gap = (df['Open'] - prev_close) / prev_close
        return gap
    
    def compute_features(self, ticker: str) -> Optional[QuantFeatures]:
        """Compute all features for a ticker."""
        df = self.fetch_data(ticker)
        if df is None or len(df) < 60:
            return None
        
        try:
            current = df.iloc[-1]
            close = current['Close']
            ema20_series = self.compute_ema(df, 20)
            ema20 = float(ema20_series.iloc[-1])
            
            # Volatility
            atr20 = self.compute_atr(df, 20).iloc[-1]
            
            # Momentum (3 timeframes)
            mom3 = self.compute_momentum(df, 3).iloc[-1]
            mom20 = self.compute_momentum(df, 20).iloc[-1]
            mom60 = self.compute_momentum(df, 60).iloc[-1]
            
            # Volume
            rvol = self.compute_rvol(df, 20).iloc[-1]
            
            # Squeeze
            squeeze_series, bb_width = self.compute_squeeze(df)
            squeeze = squeeze_series.iloc[-1]
            bb_width_val = bb_width.iloc[-1]
            
            # Breakout
            breakout = self.compute_breakout(df, 20).iloc[-1]
            
            # Price-to-BB-Zone
            pbz = self.compute_pbz(df, 20).iloc[-1]
            
            # Trends
            sma50 = df['Close'].rolling(50).mean().iloc[-1]
            sma200 = df['Close'].rolling(200).mean().iloc[-1]
            trend_sma50 = close > sma50
            trend_sma200 = close > sma200
            
            # RSI, MACD
            rsi = self.compute_rsi(df, 14).iloc[-1]
            _, signal = self.compute_macd(df)
            macd_signal = signal.iloc[-1]

            # Expert setups thresholds from config
            setups_cfg = (self.config.get('setups') or {})
            egap_cfg = setups_cfg.get('earnings_gap_rvol', {})
            gap_thr = float(egap_cfg.get('gap_up_threshold_pct', 2.0)) / 100.0
            rvol_thr = float(egap_cfg.get('rvol_threshold', 1.8))
            pb_cfg = setups_cfg.get('pullback_20ema', {})
            ema_tol = float(pb_cfg.get('tolerance_pct', 1.5)) / 100.0

            # Compute setups
            gap_pct_series = self.compute_gap_pct(df)
            gap_pct = float(gap_pct_series.iloc[-1]) if not pd.isna(gap_pct_series.iloc[-1]) else 0.0
            setup_earnings_gap_high_rvol = bool((gap_pct >= gap_thr) and (rvol >= rvol_thr))
            setup_base_breakout_squeeze = bool(squeeze and (int(breakout) > 0))
            near_ema = abs(close - ema20) / max(1e-6, ema20) <= ema_tol
            setup_pullback_20ema = bool(trend_sma50 and near_ema)
            
            return QuantFeatures(
                ticker=ticker,
                close=close,
                atr20=atr20,
                momentum_3=mom3,
                momentum_20=mom20,
                momentum_60=mom60,
                rvol=rvol,
                squeeze=squeeze,
                squeeze_bb_width=bb_width_val,
                breakout=int(breakout),
                pbz=pbz,
                trend_sma50=trend_sma50,
                trend_sma200=trend_sma200,
                rsi_14=rsi,
                macd_signal=macd_signal,
                ema20=ema20,
                setup_earnings_gap_high_rvol=setup_earnings_gap_high_rvol,
                setup_base_breakout_squeeze=setup_base_breakout_squeeze,
                setup_pullback_20ema=setup_pullback_20ema,
            )
        except Exception as e:
            logger.error(f"Error computing features for {ticker}: {e}")
            return None

class LLMNewsScorer:
    """Extract catalysts from news and score sentiment/certainty."""
    
    CATALYST_TYPES = {
        'earnings': r'(earnings|result|profit|revenue|net income|ebitda)',
        'acquisition': r'(acquire|acquisition|merger|deal|buyout|takeover)',
        'investment': r'(invest|investment|fund|funding|stake|capital)',
        'expansion': r'(expand|expansion|new factory|capacity|facility)',
        'contract': r'(contract|order|supply|partnership|joint venture)',
        'product': r'(launch|product|service|feature|new offering)',
        'dividend': r'(dividend|buyback|shareholder return)',
        'strategic': r'(strategic|board change|ceo|leadership|restructure)',
        'regulatory': r'(approval|license|permit|regulatory|compliance)',
        'ipo': r'(ipo|listing|stock|public offering|float)'
    }
    
    SENTIMENT_WORDS = {
        'positive': ['surge', 'soar', 'jump', 'rally', 'boom', 'growth', 'profit', 'beat', 'strong', 'gain', 'rise'],
        'negative': ['fall', 'drop', 'crash', 'decline', 'miss', 'loss', 'weak', 'down', 'down', 'struggle', 'risk'],
        'neutral': ['announce', 'report', 'file', 'update', 'begin', 'plan']
    }
    
    def parse_deal_value(self, text: str) -> float:
        """Extract deal value in crores."""
        patterns = [
            r'₹\s*([0-9,]+(?:\.[0-9]+)?)\s*(?:cr|crore)',
            r'\$\s*([0-9,]+(?:\.[0-9]+)?)\s*(?:mn|million)',
            r'€\s*([0-9,]+(?:\.[0-9]+)?)\s*(?:mn|million)',
            r'([0-9,]+(?:\.[0-9]+)?)\s*(?:cr|crore)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1):  # Check group exists and is not empty
                try:
                    val = float(match.group(1).replace(',', ''))
                    # Convert USD/EUR to INR at 1:83, 1:90 respectively
                    if '$' in text[:match.start()]:
                        val *= 83 / 100  # Million to Crore
                    elif '€' in text[:match.start()]:
                        val *= 90 / 100
                    return val
                except ValueError:
                    continue
        return 0.0
    
    def score_news(self, headlines: List[str], ticker: str = '') -> NewsMetrics:
        """Score news headlines for catalysts, sentiment, and certainty."""
        if not headlines:
            return NewsMetrics('none', 0, 0, 'neutral', 0, 'no_news', '')
        
        combined_text = ' '.join(headlines).lower()
        
        # Detect catalysts
        catalyst_counts = {cat: len(re.findall(pat, combined_text)) for cat, pat in self.CATALYST_TYPES.items()}
        primary_catalyst = max(catalyst_counts.items(), key=lambda x: x[1])
        
        # Sentiment
        pos_count = sum(combined_text.count(w) for w in self.SENTIMENT_WORDS['positive'])
        neg_count = sum(combined_text.count(w) for w in self.SENTIMENT_WORDS['negative'])
        sentiment = 'positive' if pos_count > neg_count else ('negative' if neg_count > pos_count else 'neutral')
        
        # Deal value
        deal_value = self.parse_deal_value(combined_text)
        
        # IMPROVED CERTAINTY CALCULATION
        certainty_score = 0
        
        # 1. Base score (20 points) - Has news at all
        certainty_score += 20
        
        # 2. Specificity (up to 25 points) - Numbers, percentages, amounts
        numbers = len(re.findall(r'\d{1,4}[,\d]*(?:\.\d+)?', combined_text))
        percentages = len(re.findall(r'\d+(?:\.\d+)?%', combined_text))
        amounts = len(re.findall(r'[₹$€]\s*\d+', combined_text))
        specificity_score = min(25, numbers * 2 + percentages * 3 + amounts * 5)
        certainty_score += specificity_score
        
        # 3. Temporal markers (up to 15 points) - Dates, quarters, years
        dates = len(re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2}', combined_text))
        quarters = len(re.findall(r'\bq[1-4]\b|\bfirst quarter\b|\bsecond quarter\b|\bthird quarter\b|\bfourth quarter\b', combined_text))
        years = len(re.findall(r'\b20\d{2}\b|\bfy\d{2}\b', combined_text))
        temporal_score = min(15, dates * 5 + quarters * 3 + years * 2)
        certainty_score += temporal_score
        
        # 4. Action verbs (up to 15 points) - Confirmed actions vs speculation
        confirmed_actions = len(re.findall(r'\b(?:announced|approved|signed|launched|completed|reported|filed|declared|awarded|acquired)\b', combined_text))
        speculation_words = len(re.findall(r'\b(?:may|might|could|possibly|potentially|expects|plans|considering|exploring)\b', combined_text))
        action_score = min(15, confirmed_actions * 3 - speculation_words * 2)
        action_score = max(0, action_score)  # Don't go negative
        certainty_score += action_score
        
        # 5. Catalyst strength (up to 15 points) - Multiple mentions = stronger
        catalyst_strength = primary_catalyst[1]
        catalyst_score = min(15, catalyst_strength * 5)
        certainty_score += catalyst_score
        
        # 6. Deal/financial specificity (up to 10 points) - Real numbers vs vague
        if deal_value > 0:
            certainty_score += 10  # Has actual deal value
        elif any(word in combined_text for word in ['crore', 'million', 'billion', 'lakh']):
            certainty_score += 5   # Mentions amounts but not parsed
        
        # Normalize to 0-100
        certainty = min(100, certainty_score)
        
        # Penalty for test/dummy data
        if 'full article fetch test' in combined_text:
            certainty = max(20, certainty - 40)  # Reduce by 40 for test data
        
        # Source quality (weighted by headline count and content quality)
        source_quality = 'premium' if len(headlines) > 5 else 'standard'
        
        headline_text = headlines[0] if headlines else ''
        
        return NewsMetrics(
            catalyst_type=primary_catalyst[0],
            catalyst_count=primary_catalyst[1],
            deal_value_cr=deal_value,
            sentiment=sentiment,
            certainty=int(certainty),
            source_quality=source_quality,
            headline_text=headline_text
        )

class AlphaCalculator:
    """Compute final alpha score and gate filters."""
    
    def __init__(self):
        self.config = self._load_config()
        self.weights = {
            'mom20': 25,
            'mom60': 15,
            'rvol': 10,
            'squeeze_bo': 10,
            'pbz': 10,
            'news': 20,
            'trend_bonus': 5
        }
        self.gate_thresholds = {
            'alpha': 70,
            'rvol': 1.5,
            'trend': True,
            'volatility_setup': True
        }
        # Setup bonuses (points added into trend_bonus bucket before weighting)
        self.setup_bonuses = {
            'earnings_gap_rvol': 12,
            'base_breakout_squeeze': 10,
            'pullback_20ema': 8,
        }
        # Override from config if present
        try:
            cfg_w = (self.config.get('alpha') or {}).get('weights') or {}
            for k, v in cfg_w.items():
                if k in self.weights:
                    self.weights[k] = float(v)
        except Exception:
            pass
        try:
            cfg_g = (self.config.get('alpha') or {}).get('gate_thresholds') or {}
            for k, v in cfg_g.items():
                self.gate_thresholds[k] = v
        except Exception:
            pass
        try:
            cfg_s = (self.config.get('setups') or {})
            if 'earnings_gap_rvol' in cfg_s and 'bonus' in cfg_s['earnings_gap_rvol']:
                self.setup_bonuses['earnings_gap_rvol'] = float(cfg_s['earnings_gap_rvol']['bonus'])
            if 'base_breakout_squeeze' in cfg_s and 'bonus' in cfg_s['base_breakout_squeeze']:
                self.setup_bonuses['base_breakout_squeeze'] = float(cfg_s['base_breakout_squeeze']['bonus'])
            if 'pullback_20ema' in cfg_s and 'bonus' in cfg_s['pullback_20ema']:
                self.setup_bonuses['pullback_20ema'] = float(cfg_s['pullback_20ema']['bonus'])
        except Exception:
            pass

    def _load_config(self) -> Dict:
        try:
            import json, os
            path = os.getenv('EXPERT_PLAYBOOK_PATH', 'expert_playbook.json')
            if path and os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return {}
    
    def normalize_feature(self, value: float, min_val: float = 0, max_val: float = 100) -> float:
        """Normalize feature to 0-100 range."""
        return np.clip((value - min_val) / (max_val - min_val) * 100, 0, 100)
    
    def compute_squeeze_bo_score(self, squeeze: bool, breakout: int, pb_zone: float) -> float:
        """Score volatility setup."""
        score = 0
        if squeeze:
            score += 50  # Compressed volatility
        if breakout > 0:
            score += 30  # Upside breakout
        if pb_zone > 60:
            score += 20  # Upper half of BB
        return min(score, 100)
    
    def compute_news_score(self, news: NewsMetrics) -> float:
        """Score news impact on trading."""
        base_score = news.certainty
        
        # Catalyst multiplier
        catalyst_boost = {
            'earnings': 1.5, 'acquisition': 1.4, 'investment': 1.3,
            'expansion': 1.2, 'contract': 1.2, 'ipo': 1.5,
            'dividend': 1.1, 'strategic': 1.1, 'regulatory': 1.1,
            'product': 1.0, 'none': 0.5
        }
        
        boost = catalyst_boost.get(news.catalyst_type, 1.0)
        
        # Deal value impact (larger deals = higher confidence)
        deal_factor = min(news.deal_value_cr / 500, 1.0) if news.deal_value_cr > 0 else 0.3
        
        # Sentiment boost
        sentiment_factor = 1.2 if news.sentiment == 'positive' else (0.8 if news.sentiment == 'negative' else 1.0)
        
        return min(100, base_score * boost * sentiment_factor)
    
    def compute_alpha(self, quant: QuantFeatures, news: NewsMetrics) -> Tuple[float, Dict]:
        """
        Compute final alpha score and gate flags.
        Alpha = 25×MOM20 + 15×MOM60 + 10×RVOL + 10×SqueezeBO + 10×PBZ + 20×NewsScore + 5×TrendBonus
        """
        # Normalize components
        mom20_norm = self.normalize_feature(quant.momentum_20, 0, 100)
        mom60_norm = self.normalize_feature(quant.momentum_60, 0, 100)
        rvol_norm = self.normalize_feature(quant.rvol, 0, 3)  # Typical 0-3x range
        squeeze_bo = self.compute_squeeze_bo_score(quant.squeeze, quant.breakout, quant.pbz)
        pbz_norm = quant.pbz  # Already 0-100
        news_score = self.compute_news_score(news)
        trend_bonus = 20 if (quant.trend_sma50 and quant.trend_sma200) else (10 if quant.trend_sma50 else 0)
        # Setup-derived bonus
        setup_bonus = 0.0
        setup_flags = []
        if getattr(quant, 'setup_earnings_gap_high_rvol', False):
            setup_bonus += self.setup_bonuses.get('earnings_gap_rvol', 12)
            setup_flags.append('egap_rvol')
        if getattr(quant, 'setup_base_breakout_squeeze', False):
            setup_bonus += self.setup_bonuses.get('base_breakout_squeeze', 10)
            setup_flags.append('bo_squeeze')
        if getattr(quant, 'setup_pullback_20ema', False):
            setup_bonus += self.setup_bonuses.get('pullback_20ema', 8)
            setup_flags.append('pb_ema20')
        trend_bonus = min(30, trend_bonus + setup_bonus)
        
        # Alpha formula (weights must sum to 100)
        alpha = (
            (mom20_norm * self.weights['mom20'] +
             mom60_norm * self.weights['mom60'] +
             rvol_norm * self.weights['rvol'] +
             squeeze_bo * self.weights['squeeze_bo'] +
             pbz_norm * self.weights['pbz'] +
             news_score * self.weights['news'] +
             trend_bonus * self.weights['trend_bonus']) / 95  # Normalize
        )
        
        # Apply smooth saturation (tanh)
        alpha_saturated = 50 + 50 * np.tanh(alpha / 50 - 1)
        alpha_final = np.clip(alpha_saturated, 0, 100)
        
        # Gate filters
        gate_flags = {}
        gate_flags['alpha_pass'] = alpha_final >= self.gate_thresholds['alpha']
        gate_flags['rvol_pass'] = quant.rvol >= self.gate_thresholds['rvol']
        gate_flags['trend_pass'] = quant.trend_sma50
        volatility_setup = quant.squeeze or quant.breakout > 0
        gate_flags['volatility_pass'] = volatility_setup
        
        gate_flags['all_pass'] = all(gate_flags.values())
        gate_flags_str = '|'.join([f"{k.replace('_pass', '')}:{v}" for k, v in gate_flags.items() if k.endswith('_pass')])
        
        metrics = {
            'mom20_norm': mom20_norm,
            'mom60_norm': mom60_norm,
            'rvol_norm': rvol_norm,
            'squeeze_bo': squeeze_bo,
            'pbz_norm': pbz_norm,
            'news_score': news_score,
            'trend_bonus': trend_bonus,
            'alpha': alpha_final,
            'gate_flags': gate_flags_str,
            'setup_flags': ','.join(setup_flags),
            'final_pick': gate_flags['all_pass']
        }
        
        return alpha_final, metrics

class RiskManager:
    """ATR-based position sizing and stop/target levels."""
    
    @staticmethod
    def compute_levels(entry_price: float, atr20: float) -> Dict[str, float]:
        """Compute stop, TP1, TP2, and trailing stop."""
        stop = entry_price - 1.5 * atr20
        tp1 = entry_price + 1.5 * atr20
        tp2 = entry_price + 3.0 * atr20
        trail_start = entry_price - 2.5 * atr20
        
        return {
            'entry': entry_price,
            'stop': max(stop, entry_price * 0.95),  # Hard floor at 5% below entry
            'tp1': tp1,
            'tp2': tp2,
            'tp1_sell_pct': 50,  # Sell 50% at TP1
            'tp2_sell_pct': 25,  # Sell 25% at TP2
            'trail_stop': trail_start,
            'trail_update': entry_price  # Current highest close
        }

def main():
    """Example usage."""
    logger.info("Frontier-AI Quant Alpha Core loaded successfully")
    
    # Test with a single ticker
    engine = QuantFeatureEngine()
    quant = engine.compute_features('RELIANCE.NS')
    
    if quant:
        logger.info(f"Quant features for RELIANCE:\n{json.dumps(quant.to_dict(), indent=2)}")
        
        scorer = LLMNewsScorer()
        sample_news = [
            "RELIANCE surges on strong Q3 earnings beat ₹50,000 crore profit",
            "Jio expansion gains momentum with new facilities"
        ]
        news = scorer.score_news(sample_news)
        logger.info(f"News metrics:\n{json.dumps(news.to_dict(), indent=2)}")
        
        alpha_calc = AlphaCalculator()
        alpha, metrics = alpha_calc.compute_alpha(quant, news)
        logger.info(f"Alpha score: {alpha:.2f}")
        logger.info(f"Metrics: {json.dumps(metrics, indent=2)}")
        
        risk = RiskManager.compute_levels(quant.close, quant.atr20)
        logger.info(f"Risk levels: {json.dumps(risk, indent=2)}")

if __name__ == '__main__':
    main()
