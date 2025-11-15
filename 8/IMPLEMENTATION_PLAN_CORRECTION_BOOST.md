# IMPLEMENTATION PLAN: PRACTICAL CORRECTION BOOST STRATEGY
## Complete Step-by-Step Guide

**Date:** 2025-11-13
**Status:** Ready for Implementation
**Target:** Production-grade system combining proven formulas with practical safeguards

---

## 📋 IMPLEMENTATION ROADMAP

### Phase 1: Core Module Creation
**File:** `enhanced_correction_analyzer.py`
**Purpose:** Standalone module implementing the complete correction boost logic

```python
CLASS HIERARCHY:

EnhancedCorrectionAnalyzer
├── detect_correction(prices, volumes)
│   ├─ Calculate correction_pct
│   ├─ Verify 10-35% range
│   ├─ Check volume spike (> 1.3x avg)
│   └─ Confirm duration (≥ 5 decline days)
│
├── confirm_reversal(prices, indicators)
│   ├─ Check consolidation (range < 10%)
│   ├─ Detect price > MA20 signal
│   ├─ Check RSI > 50 + momentum
│   └─ Identify bullish candlestick patterns
│
├── measure_oversold(rsi, bb_position, volumes)
│   ├─ RSI scoring (0-30 points)
│   ├─ BB position scoring (0-25 points)
│   └─ Volume surge scoring (0-15 points)
│
├── evaluate_fundamentals(ticker)
│   ├─ Earnings growth scoring
│   ├─ Debt/Equity analysis
│   ├─ Profitability check
│   └─ Cash position assessment
│
├── calculate_catalyst_strength(ai_score, certainty)
│   ├─ Map AI score to catalyst strength
│   └─ Apply certainty bonus
│
├── calculate_correction_confidence(oversold, fundamentals, catalyst)
│   ├─ Weighted formula: (0.3*tech + 0.3*fund + 0.4*catalyst)/100
│   └─ Clamp to 0-1 range
│
├── apply_risk_filters(stock_data)
│   ├─ Check debt_to_equity <= 2.0
│   ├─ Check current_ratio >= 0.8
│   ├─ Check market_cap >= ₹500 Cr
│   ├─ Check daily_volume >= 100k
│   ├─ Check beta OR confidence threshold
│   └─ Check listing_age >= 6 months
│
├── detect_market_context(market_data, sector_data)
│   ├─ Determine bull/bear/uncertain regime
│   ├─ Calculate sector strength
│   └─ Return context adjustments
│
├── check_emergency_safeguards(market_data, stock_data)
│   ├─ Market crash detection (index -5%+)
│   ├─ Sector crisis (sector -10%+)
│   └─ Company crisis (earnings surprise, scandal)
│
├── apply_market_context_adjustment(confidence, context)
│   ├─ Bull market: lower threshold, higher boost
│   ├─ Bear market: higher threshold, lower boost
│   ├─ Sector strength: ±10% confidence
│   └─ Return adjusted_confidence
│
└── apply_boost(hybrid_score, correction_confidence, context)
    ├─ Determine BOOST_FACTOR based on confidence tier
    ├─ Calculate confidence_boost = confidence * BOOST_FACTOR
    └─ Return {final_score, boost_applied, reasoning}
```

### Phase 2: Integration Points

#### 2.1 Technical Scoring Wrapper (`technical_scoring_wrapper.py`)
**Changes:**
```python
# In TechnicalScorer.score_ticker():
1. Add EnhancedCorrectionAnalyzer import
2. After calculating basic technical score:
   - Call analyzer.detect_correction(df)
   - If correction detected:
     - Call analyzer.confirm_reversal(df, indicators)
     - If reversal confirmed:
       - Store correction_data in result dict
       - Pass to scoring pipeline

# New fields in output:
{
    'score': 75.0,
    'tier': 'Tier1',
    'correction': {
        'detected': True,
        'correction_pct': 18.5,
        'reversal_confirmed': True,
        'consolidation_confirmed': True
    },
    ...
}
```

#### 2.2 AI News Analyzer (`realtime_ai_news_analyzer.py`)
**Changes:**
```python
# In InstantAIAnalysis dataclass, add:
correction_detected: Optional[bool] = None
correction_pct: Optional[float] = None
reversal_confirmed: Optional[bool] = None
correction_confidence: Optional[float] = None
boost_applied: Optional[float] = None
risk_filters_passed: Optional[bool] = None
correction_notes: Optional[str] = None
market_context: Optional[str] = None
fundamental_confidence: Optional[float] = None
oversold_score: Optional[float] = None
catalyst_strength: Optional[float] = None

# In _apply_frontier_scoring() or new _apply_correction_boost():
1. Import EnhancedCorrectionAnalyzer
2. After computing base hybrid_score:
   - Initialize analyzer
   - Call detect_correction(ticker)
   - If correction:
     - Call confirm_reversal(ticker)
     - If confirmed:
       - Measure oversold_score
       - Evaluate fundamentals
       - Calculate catalyst_strength
       - Calculate correction_confidence
       - Apply risk filters
       - Detect market context
       - Check emergency safeguards
       - Apply boost if all pass
   - Populate new dataclass fields
   - Return enhanced analysis
```

#### 2.3 Output CSV Enhancement
**New columns:**
```
existing_columns...,
correction_detected,
correction_pct,
reversal_confirmed,
correction_confidence,
boost_applied,
risk_filters_passed,
fundamental_confidence,
oversold_score,
catalyst_strength,
market_context,
correction_notes
```

**Example row:**
```csv
TCS,85.2,True,15.3,True,0.68,8.2,True,62.5,75.0,28.5,bull,"15% correction, reversal at MA20, strong earnings, +8pt boost"
```

---

## 🔧 DETAILED IMPLEMENTATION: Each Method

### Method 1: `detect_correction()`
```python
def detect_correction(self, ticker: str, window_days: int = 90) -> Dict:
    """
    Detect if stock has undergone a meaningful correction.

    Returns: {
        'correction_detected': bool,
        'correction_pct': float or None,
        'recent_high': float,
        'current_price': float,
        'decline_days': int,
        'volume_spike': bool,
        'volume_ratio': float,
        'confirmed': bool  # all criteria met
    }
    """
    # Fetch price history (90 days lookback)
    df = fetch_yfinance_data(ticker, period='3mo')
    if df.empty:
        return {'correction_detected': False, 'confirmed': False}

    # Find recent high (last 90 days)
    recent_high = df['Close'].max()
    current_price = df['Close'].iloc[-1]

    # Calculate correction percentage
    correction_pct = ((recent_high - current_price) / recent_high) * 100

    # Check if in valid range: 10-35%
    if not (10 <= correction_pct <= 35):
        return {
            'correction_detected': False,
            'correction_pct': correction_pct,
            'recent_high': recent_high,
            'current_price': current_price,
            'confirmed': False,
            'reason': 'Outside 10-35% range' if correction_pct else 'No correction'
        }

    # Count consecutive decline days (last 10 trading days)
    recent_closes = df['Close'].tail(10).values
    decline_days = 0
    for i in range(len(recent_closes) - 1, 0, -1):
        if recent_closes[i] < recent_closes[i-1]:
            decline_days += 1
        else:
            break

    # Check volume spike during decline
    avg_volume_30d = df['Volume'].tail(30).mean()
    current_volume = df['Volume'].iloc[-1]
    volume_ratio = current_volume / avg_volume_30d
    volume_spike = volume_ratio > 1.3

    # Confirmation: at least 5 decline days + volume spike
    confirmed = decline_days >= 5 and volume_spike

    return {
        'correction_detected': True,
        'correction_pct': round(correction_pct, 2),
        'recent_high': round(recent_high, 2),
        'current_price': round(current_price, 2),
        'decline_days': decline_days,
        'volume_spike': volume_spike,
        'volume_ratio': round(volume_ratio, 2),
        'confirmed': confirmed,
        'reason': 'Confirmed' if confirmed else f'Decline days {decline_days}<5 or no volume spike'
    }
```

### Method 2: `confirm_reversal()`
```python
def confirm_reversal(self, ticker: str, df: pd.DataFrame = None) -> Dict:
    """
    Check if stock shows signs of reversal (consolidation + price action).

    Returns: {
        'reversal_confirmed': bool,
        'consolidation_confirmed': bool,
        'consolidation_range': float,
        'reversal_signals': int,
        'signals_detail': List[str],
        'price_above_ma20': bool,
        'rsi_bullish': bool,
        'bullish_pattern': str or None,
        'reason': str
    }
    """
    if df is None or df.empty:
        return {'reversal_confirmed': False}

    # 1. CONSOLIDATION CHECK: Trading range last 10 days
    recent_closes = df['Close'].tail(10)
    trading_range = (recent_closes.max() - recent_closes.min()) / df['Close'].iloc[-1]
    consolidation_confirmed = trading_range < 0.10  # < 10% range
    consolidation_range = round(trading_range * 100, 2)

    # 2. REVERSAL SIGNAL 1: Price > 20-day MA
    ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
    price_above_ma20 = df['Close'].iloc[-1] > ma20

    # 3. REVERSAL SIGNAL 2: RSI bullish (RSI > 50 + momentum)
    rsi = self._calculate_rsi(df['Close'])
    rsi_current = rsi.iloc[-1] if not rsi.empty else None
    rsi_bullish = rsi_current > 50 if rsi_current else False

    # Check momentum crossover (simple: RSI yesterday < 50, today > 50)
    momentum_cross = False
    if len(rsi) >= 2:
        momentum_cross = rsi.iloc[-2] < 50 and rsi.iloc[-1] > 50

    # 4. REVERSAL SIGNAL 3: Bullish candlestick patterns
    bullish_pattern = self._detect_bullish_pattern(df)

    # Count reversal signals (need at least 2 of 4 for confirmation)
    reversal_signals = sum([
        consolidation_confirmed,
        price_above_ma20,
        rsi_bullish or momentum_cross,
        bullish_pattern is not None
    ])

    signals_detail = []
    if consolidation_confirmed:
        signals_detail.append(f"Consolidation <10% range ({consolidation_range}%)")
    if price_above_ma20:
        signals_detail.append("Price above 20-day MA")
    if rsi_bullish:
        signals_detail.append(f"RSI bullish ({rsi_current:.1f} > 50)")
    if momentum_cross:
        signals_detail.append("RSI momentum crossing above 50")
    if bullish_pattern:
        signals_detail.append(f"Bullish pattern: {bullish_pattern}")

    reversal_confirmed = reversal_signals >= 2

    reason = f"{reversal_signals}/4 signals confirmed" if reversal_confirmed else "Insufficient reversal signals"

    return {
        'reversal_confirmed': reversal_confirmed,
        'consolidation_confirmed': consolidation_confirmed,
        'consolidation_range': consolidation_range,
        'reversal_signals': reversal_signals,
        'signals_detail': signals_detail,
        'price_above_ma20': price_above_ma20,
        'rsi_bullish': rsi_bullish,
        'bullish_pattern': bullish_pattern,
        'reason': reason
    }
```

### Method 3: `measure_oversold()`
```python
def measure_oversold(self, df: pd.DataFrame) -> float:
    """
    Calculate oversold score (0-100) from technical indicators.
    """
    oversold_score = 0.0

    # 1. RSI component (0-30 points)
    rsi = self._calculate_rsi(df['Close'])
    rsi_current = rsi.iloc[-1] if not rsi.empty else 50

    if rsi_current < 25:
        oversold_score += 30  # Extremely oversold
    elif rsi_current < 35:
        oversold_score += 20  # Deeply oversold
    elif rsi_current < 45:
        oversold_score += 10  # Moderately oversold

    # 2. Bollinger Band position (0-25 points)
    bb_position = self._calculate_bb_position(df['Close'])
    bb_current = bb_position.iloc[-1] if not bb_position.empty else 0.5

    if bb_current < 0.15:
        oversold_score += 25  # Touching lower band
    elif bb_current < 0.35:
        oversold_score += 15  # Lower half
    elif bb_current < 0.50:
        oversold_score += 5   # Below mid-band

    # 3. Volume anomaly (0-15 points)
    avg_volume_10d = df['Volume'].tail(10).mean()
    current_volume = df['Volume'].iloc[-1]
    volume_ratio = current_volume / avg_volume_10d if avg_volume_10d > 0 else 1.0

    if volume_ratio > 1.5:
        oversold_score += 15  # Huge volume spike
    elif volume_ratio > 1.2:
        oversold_score += 8   # Moderate volume surge

    # Cap at 100
    return min(100.0, oversold_score)
```

### Method 4: `evaluate_fundamentals()`
```python
def evaluate_fundamentals(self, ticker: str) -> float:
    """
    Calculate fundamental confidence (0-100).

    Fetches from yfinance info + financial data.
    """
    fundamental_confidence = 0.0

    try:
        # Fetch fundamental data (could use existing fundamental_data if available)
        info = get_fundamentals(ticker)  # Wrapper around yfinance

        # 1. Earnings growth (0-25 points)
        earnings_growth = info.get('quarterly_earnings_growth_yoy', 0)
        if earnings_growth > 0.15:
            fundamental_confidence += 25
        elif earnings_growth > 0.05:
            fundamental_confidence += 15
        elif earnings_growth > 0:
            fundamental_confidence += 5

        # 2. Profitability (0-10 points)
        is_profitable = info.get('is_profitable', False)
        if is_profitable:
            fundamental_confidence += 10

        # 3. Debt levels (0-15 points)
        debt_to_equity = info.get('debt_to_equity', 1.5)
        if debt_to_equity < 0.5:
            fundamental_confidence += 15
        elif debt_to_equity < 1.0:
            fundamental_confidence += 8

        # 4. Net worth (0-5 points)
        net_worth_positive = info.get('net_worth_positive', False)
        if net_worth_positive:
            fundamental_confidence += 5

        # 5. Cash returns (0-10 points)
        has_dividend = info.get('has_dividend', False)
        has_buyback = info.get('has_buyback', False)
        if has_dividend or has_buyback:
            fundamental_confidence += 10

        return min(100.0, fundamental_confidence)

    except Exception as e:
        logger.warning(f"Failed to evaluate fundamentals for {ticker}: {e}")
        return 0.0
```

### Method 5: `calculate_catalyst_strength()`
```python
def calculate_catalyst_strength(self, ai_score: float, certainty: float) -> float:
    """
    Map AI news score to catalyst strength (0-100).
    """
    catalyst_strength = 0.0

    # Base catalyst from AI score
    if ai_score >= 80:
        catalyst_strength = 25   # Extremely positive
    elif ai_score >= 70:
        catalyst_strength = 18   # Strong positive
    elif ai_score >= 60:
        catalyst_strength = 12   # Moderately positive
    else:
        catalyst_strength = 0    # No meaningful catalyst

    # Certainty bonus
    if catalyst_strength > 0:
        if certainty >= 0.8:
            catalyst_strength += 10  # Highly certain
        elif certainty >= 0.6:
            catalyst_strength += 5   # Moderately certain

    return min(100.0, catalyst_strength)
```

### Method 6: `calculate_correction_confidence()`
```python
def calculate_correction_confidence(
    self,
    oversold_score: float,
    fundamental_confidence: float,
    catalyst_strength: float
) -> float:
    """
    Combine three components into correction confidence (0-1).

    Weights:
    - 30% technical (oversold)
    - 30% fundamentals
    - 40% catalyst (catalyst is the immediate trigger)
    """
    confidence = (
        (0.3 * oversold_score) +
        (0.3 * fundamental_confidence) +
        (0.4 * catalyst_strength)
    ) / 100.0

    # Clamp to 0-1
    return max(0.0, min(1.0, confidence))
```

### Method 7: `apply_risk_filters()`
```python
def apply_risk_filters(self, stock_data: Dict) -> Dict:
    """
    Run risk checks before applying boost.

    Returns: {
        'passed': bool,
        'failures': List[str],
        'details': Dict
    }
    """
    failures = []
    details = {}

    # 1. Debt check
    debt_to_equity = stock_data.get('debt_to_equity', 2.5)
    details['debt_to_equity'] = debt_to_equity
    if debt_to_equity > 2.0:
        failures.append(f"High debt ({debt_to_equity:.1f} > 2.0)")

    # 2. Liquidity check (current ratio)
    current_ratio = stock_data.get('current_ratio', 1.0)
    details['current_ratio'] = current_ratio
    if current_ratio < 0.8:
        failures.append(f"Low liquidity ({current_ratio:.2f} < 0.8)")

    # 3. Market cap check
    market_cap_cr = stock_data.get('market_cap_cr', 0)
    details['market_cap_cr'] = market_cap_cr
    if market_cap_cr < 500:
        failures.append(f"Small cap (₹{market_cap_cr}Cr < ₹500Cr)")

    # 4. Trading volume check
    avg_daily_volume = stock_data.get('avg_daily_volume', 0)
    details['avg_daily_volume'] = avg_daily_volume
    if avg_daily_volume < 100000:
        failures.append(f"Low volume ({avg_daily_volume:.0f} < 100k)")

    # 5. Volatility check
    beta = stock_data.get('beta', 1.0)
    correction_confidence = stock_data.get('correction_confidence', 0.5)
    details['beta'] = beta
    if beta > 1.5 and correction_confidence < 0.5:
        failures.append(f"High volatility (beta {beta:.1f}) + low confidence")

    # 6. IPO age check
    listed_months = stock_data.get('listed_months', 12)
    details['listed_months'] = listed_months
    if listed_months < 6:
        failures.append(f"Too new ({listed_months} months < 6)")

    return {
        'passed': len(failures) == 0,
        'failures': failures,
        'details': details
    }
```

### Method 8: `detect_market_context()`
```python
def detect_market_context(self) -> Dict:
    """
    Detect current market regime and sector conditions.

    Returns: {
        'regime': 'bull' | 'bear' | 'uncertain',
        'index_momentum': float (-1 to 1),
        'vix_level': float,
        'sector_strength': Dict[str, float],
        'recommendation': str
    }
    """
    context = {}

    try:
        # Fetch index data (NIFTY50 for India)
        nifty_data = fetch_yfinance_data('^NSEI', period='3mo')

        # Calculate momentum (recent_price vs 50-day MA)
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

        # VIX proxy (using recent volatility)
        recent_volatility = nifty_data['Close'].pct_change().std() * 100
        vix_level = recent_volatility  # Simplified proxy

        # Sector strength (compare major sectors vs index)
        sector_strength = self._calculate_sector_strength()

        context = {
            'regime': regime,
            'index_momentum': round(index_momentum, 3),
            'vix_level': round(vix_level, 1),
            'sector_strength': sector_strength,
            'market_volatility': 'high' if vix_level > 20 else 'normal'
        }

    except Exception as e:
        logger.warning(f"Market context detection failed: {e}")
        context = {
            'regime': 'uncertain',
            'index_momentum': 0.0,
            'vix_level': 20.0,
            'sector_strength': {}
        }

    return context
```

### Method 9: `apply_market_context_adjustment()`
```python
def apply_market_context_adjustment(
    self,
    correction_confidence: float,
    market_context: Dict
) -> Dict:
    """
    Adjust thresholds and boost based on market regime.

    Returns: {
        'adjusted_confidence': float (0-1),
        'confidence_threshold': float,
        'boost_factor_multiplier': float,
        'adjustment_reason': str
    }
    """
    regime = market_context.get('regime', 'uncertain')
    vix_level = market_context.get('vix_level', 20)
    sector_strength = market_context.get('sector_strength', {})

    adjusted_confidence = correction_confidence
    confidence_threshold = 0.30  # Default
    boost_multiplier = 1.0  # Default
    adjustments = []

    # REGIME-BASED ADJUSTMENTS
    if regime == 'bull':
        # Bull market: be more aggressive
        confidence_threshold = 0.25  # Lower bar
        boost_multiplier = 1.1  # Higher boost
        adjustments.append("Bull market → Lower threshold, higher boost")

    elif regime == 'bear':
        # Bear market: be more conservative
        confidence_threshold = 0.35  # Higher bar
        boost_multiplier = 0.8  # Lower boost
        adjustments.append("Bear market → Higher threshold, lower boost")

    else:  # uncertain
        # Sideways market: stick to defaults
        adjustments.append("Uncertain market → Neutral adjustments")

    # VOLATILITY ADJUSTMENT
    if vix_level > 30:
        # High volatility (fear): even more conservative
        confidence_threshold = min(0.40, confidence_threshold + 0.05)
        boost_multiplier *= 0.8
        adjustments.append(f"High VIX ({vix_level:.1f}) → Raise threshold")

    # SECTOR ADJUSTMENT
    stock_sector = market_context.get('stock_sector', 'tech')
    sector_score = sector_strength.get(stock_sector, 0.0)

    if sector_score > 0.15:  # Sector is strong
        adjusted_confidence = min(1.0, correction_confidence * 1.08)
        adjustments.append(f"{stock_sector} sector strong → +8% confidence")
    elif sector_score < -0.15:  # Sector is weak
        adjusted_confidence = max(0.0, correction_confidence * 0.90)
        adjustments.append(f"{stock_sector} sector weak → -10% confidence")

    return {
        'adjusted_confidence': round(adjusted_confidence, 3),
        'confidence_threshold': round(confidence_threshold, 3),
        'boost_factor_multiplier': round(boost_multiplier, 2),
        'adjustment_reason': ' | '.join(adjustments) if adjustments else 'No adjustments'
    }
```

### Method 10: `check_emergency_safeguards()`
```python
def check_emergency_safeguards(self, ticker: str) -> Dict:
    """
    Check for market crashes, sector crises, or company crises.

    Returns: {
        'safe_to_boost': bool,
        'triggered_safeguards': List[str],
        'emergency_level': 'none' | 'warning' | 'critical'
    }
    """
    triggered = []
    emergency_level = 'none'

    try:
        # 1. MARKET CRASH CHECK
        nifty_data = fetch_yfinance_data('^NSEI', period='5d')
        recent_close = nifty_data['Close'].iloc[-1]
        prev_close = nifty_data['Close'].iloc[-2]
        daily_change = ((recent_close - prev_close) / prev_close) * 100

        if daily_change < -5:
            triggered.append(f"Market crash: NIFTY down {daily_change:.1f}%")
            emergency_level = 'critical'

        # 2. SECTOR CRISIS CHECK
        sector_symbol = self._get_sector_etf(ticker)
        sector_data = fetch_yfinance_data(sector_symbol, period='5d')
        sector_change_weekly = (
            (sector_data['Close'].iloc[-1] - sector_data['Close'].iloc[0]) /
            sector_data['Close'].iloc[0]
        ) * 100

        if sector_change_weekly < -10:
            triggered.append(f"Sector crisis: {sector_symbol} down {sector_change_weekly:.1f}%")
            if emergency_level != 'critical':
                emergency_level = 'warning'

        # 3. COMPANY CRISIS CHECK
        company_data = fetch_company_info(ticker)
        earnings_surprise = company_data.get('earnings_surprise_pct', 0)

        if earnings_surprise < -20:
            triggered.append(f"Earnings miss: {earnings_surprise:.1f}%")
            emergency_level = 'critical'

        # Check for major scandals/news (via news sentiment)
        recent_news = fetch_recent_news(ticker, days=1)
        scandal_keywords = ['fraud', 'insolvency', 'delisting', 'accounting scandal']
        for news in recent_news:
            if any(kw in news.lower() for kw in scandal_keywords):
                triggered.append(f"Scandal detected: {news[:50]}...")
                emergency_level = 'critical'

    except Exception as e:
        logger.warning(f"Emergency safeguard check failed: {e}")

    safe_to_boost = emergency_level != 'critical' and len(triggered) == 0

    return {
        'safe_to_boost': safe_to_boost,
        'triggered_safeguards': triggered,
        'emergency_level': emergency_level
    }
```

### Method 11: `apply_boost()`
```python
def apply_boost(
    self,
    hybrid_score: float,
    correction_confidence: float,
    market_context: Dict,
    safe_to_boost: bool
) -> Dict:
    """
    Calculate final boost to apply to hybrid score.

    Returns: {
        'final_score': float (0-100),
        'boost_applied': float (points),
        'boost_factor': float,
        'boost_tier': str,
        'reasoning': str
    }
    """
    if not safe_to_boost:
        return {
            'final_score': hybrid_score,
            'boost_applied': 0.0,
            'boost_factor': 0.0,
            'boost_tier': 'None - Emergency safeguard triggered',
            'reasoning': 'Boost cancelled due to emergency conditions'
        }

    # Get adjusted confidence (with market context)
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
            'boost_tier': f'Below threshold ({adjusted_confidence:.2f} < {threshold:.2f})',
            'reasoning': 'Insufficient correction confidence'
        }

    # Determine boost tier
    if adjusted_confidence >= 0.85:
        base_boost_factor = 20
        tier = 'Very High'
    elif adjusted_confidence >= 0.70:
        base_boost_factor = 15
        tier = 'High'
    elif adjusted_confidence >= 0.55:
        base_boost_factor = 10
        tier = 'Medium'
    elif adjusted_confidence >= 0.40:
        base_boost_factor = 5
        tier = 'Low'
    else:
        return {
            'final_score': hybrid_score,
            'boost_applied': 0.0,
            'boost_factor': 0.0,
            'boost_tier': 'Below minimum',
            'reasoning': f'Confidence {adjusted_confidence:.2f} below minimum'
        }

    # Apply market multiplier
    boost_factor = base_boost_factor * multiplier

    # Calculate boost
    confidence_boost = adjusted_confidence * boost_factor

    # Apply with safeguard: don't exceed 100
    final_score = min(100.0, hybrid_score + confidence_boost)

    # Avoid over-boosting already high scores
    if hybrid_score >= 85 and confidence_boost > 5:
        confidence_boost = 5  # Cap boost for high scores
        final_score = min(100.0, hybrid_score + confidence_boost)

    return {
        'final_score': round(final_score, 2),
        'boost_applied': round(confidence_boost, 2),
        'boost_factor': round(boost_factor, 2),
        'boost_tier': tier,
        'reasoning': f'{tier} confidence ({adjusted_confidence:.2f}) → +{confidence_boost:.1f}pt boost'
    }
```

---

## 📊 DATA FLOW DIAGRAM

```
INPUT: Ticker Symbol, AI Score, Technical Indicators
     ↓
[detect_correction] → Is there a 10-35% pullback?
     ↓
     YES → [confirm_reversal] → Signs of bottoming?
     │         ↓
     │        YES → [measure_oversold] → Calculate oversold score
     │         │       ↓
     │         │    [evaluate_fundamentals] → Calculate fundamental score
     │         │       ↓
     │         │    [calculate_catalyst_strength] → Map AI news score
     │         │       ↓
     │         │    [calculate_correction_confidence] → Combine (0.3*tech + 0.3*fund + 0.4*cat)
     │         │       ↓
     │         │    [apply_risk_filters] → Pass financial checks?
     │         │       ↓
     │         │      YES → [detect_market_context] → Bull/Bear/Sector?
     │         │         ↓
     │         │      [apply_market_context_adjustment] → Adjust thresholds
     │         │         ↓
     │         │      [check_emergency_safeguards] → Market crash/crisis?
     │         │         ↓
     │         │       NO → [apply_boost] → Add points to hybrid score
     │         │         ↓
     │         │        OUTPUT: Final Score + Boost Details
     │         │
     │        NO → OUTPUT: No boost (no reversal confirmed)
     │
     NO → OUTPUT: No boost (no meaningful correction)
```

---

## ✅ VALIDATION CHECKLIST

Before deploying, verify:

- [ ] All 11 methods implemented and tested individually
- [ ] Data fetching from yfinance works reliably
- [ ] Reversal detection catches real bottoms (not premature)
- [ ] Risk filters prevent boosting risky stocks
- [ ] Market context adjustments reflect real market conditions
- [ ] Emergency safeguards can be tested (simulate market crash)
- [ ] Output fields added to InstantAIAnalysis and CSV
- [ ] Backtest on 20+ historical correction-rebound scenarios
- [ ] Performance metrics: precision ≥80%, hit-rate ≥68%

---

## 🚀 DEPLOYMENT COMMAND

```bash
# After implementation complete:
./run_without_api.sh claude test.txt 8 10

# Expected CSV output:
# TCS,85.2,...,True,15.3,True,0.68,8.2,True,62.5,75.0,28.5,bull,"Correction boost applied"
```

---

## 📚 REFERENCE MATERIALS

- Primary: User's "Practical Correction Boost Strategy" document
- Technical: APPROACH_ANALYSIS.md (this repository)
- Historical examples: Real correction-rebound patterns (TCS, INFY, RELIANCE)
- Risk management: Position sizing based on confidence tier

