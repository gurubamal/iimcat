# CLAUDE EXIT INTELLIGENCE ENHANCEMENT PLAN
## Making Claude the Dominant Exit Analysis Provider

---

## Current State Analysis

### Codex Strengths (Why It's Ahead)
1. **Internet-Enhanced Analysis** - Fetches 5000-char article bodies
2. **Intraday Feedback** - Updates weights every 5m based on yfinance data
3. **Technical-Only Mode** - 70% tech + 30% AI urgency when news unavailable
4. **Dynamic Weights** - Learns optimal: Tech=44.5%, News=21%, Fund=26%, Liq=8.5%
5. **Adaptive Bands** - EXIT≥80 (tech-only) vs EXIT≥90 (with news)
6. **Risk Management** - Auto-computes stop=swing_low-1.0×ATR, trail=1.5×ATR
7. **Feedback Loop** - JSONL logging + config updates

### Claude Current Weaknesses
1. Generic "swing trading" system prompt (not exit-focused)
2. No internet access for full article text
3. Receives raw text prompts, not structured technical data
4. No feedback learning mechanism
5. Static scoring without dynamic calibration
6. No risk level computation (stops/trails)
7. No performance tracking

---

## Enhancement Design: 7-Point Upgrade

### 1. EXIT-SPECIFIC SYSTEM PROMPT
**Problem:** Current prompt optimizes for entry, not exit
**Solution:** Dedicated exit analysis system prompt

```python
CLAUDE_EXIT_SYSTEM_PROMPT = """You are an elite portfolio manager specializing in EXIT decisions for Indian equities.

Your CORE MANDATE: Protect capital by identifying deterioration EARLY.

EXIT DECISION FRAMEWORK:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. CRITICAL EXIT SIGNALS (Immediate Action):
   • Profit warnings / guidance cuts
   • Regulatory/legal investigations
   • Debt covenant breaches
   • Major customer/contract losses
   • Management fraud/scandals
   • Support breaks with volume confirmation

2. HIGH-PRIORITY SIGNALS (Monitor → Exit):
   • Analyst downgrades (esp. tier-1 firms)
   • Margin compression trends (>2 quarters)
   • Market share losses
   • Delayed projects/capex cuts
   • Death cross (20DMA < 50DMA)

3. MODERATE SIGNALS (Watch Closely):
   • Weakening demand indicators
   • Rising competitive threats
   • RSI oversold with volume spike down
   • Sector headwinds

4. HOLD SIGNALS (Counter-indicators):
   • Temporary/one-time issues
   • News already priced in
   • Strong fundamentals intact
   • Attractive valuation + margin of safety
   • Upcoming positive catalysts

SCORING CALIBRATION (Exit-Optimized):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• exit_urgency_score 90-100: CRITICAL - regulatory/fraud/bankruptcy risk
• exit_urgency_score 75-89: SERIOUS - fundamental deterioration, broken support
• exit_urgency_score 60-74: WARNING - monitor closely, partial exit consideration
• exit_urgency_score 40-59: MINOR - thesis intact, normal volatility
• exit_urgency_score 0-39: STRONG HOLD - no material risks

TECHNICAL BREAKDOWN SCORING:
• Price < 20DMA by >5%: +15 points
• Price < 50DMA by >8%: +20 points
• Death cross: +20 points
• RSI < 30 with down momentum: +15 points
• Volume spike on down move: +10 points
• Near 52-week low (<5%): +20 points

FUNDAMENTAL RISK SCORING:
• Earnings miss: +25 points
• Debt/EBITDA ratio deterioration: +20 points
• Margin compression >200bps: +15 points
• Cash flow negative: +30 points
• Customer concentration risk: +10 points

SENTIMENT RISK SCORING:
• Tier-1 downgrade: +30 points
• Regulatory investigation: +40 points
• Management scandal: +50 points
• Sector downgrade: +15 points
• Negative earnings surprise: +25 points

CONFIDENCE CALIBRATION:
• Hard data (earnings, official announcements): 85-95%
• Tier-1 analyst reports: 75-85%
• Tier-2 sources (Moneycontrol, ET): 60-75%
• Technical-only (no news): 50-65%
• Speculation/rumors: 20-40%

RESPONSE FORMAT:
Return ONLY valid JSON with these exact keys:
{
  "exit_urgency_score": <0-100>,
  "sentiment": "bearish" | "neutral" | "bullish",
  "exit_recommendation": "IMMEDIATE_EXIT" | "MONITOR" | "HOLD",
  "exit_catalysts": [<max 5 specific reasons>],
  "hold_reasons": [<counter-arguments if any>],
  "risks_of_holding": [<specific risks>],
  "technical_breakdown_score": <0-100>,
  "fundamental_risk_score": <0-100>,
  "negative_sentiment_score": <0-100>,
  "certainty": <0-100>,
  "reasoning": "<2-3 sentences: decision + key factors + recommendation>",
  "stop_loss_suggestion": <percentage below current>
}

CRITICAL RULES:
✓ Be DECISIVE - don't hedge when data is clear
✓ Consider OPPORTUNITY COST - capital has alternatives
✓ Favor ACTION over inaction when risks mount
✓ Use FULL scoring range (don't cluster at 40-60)
✓ Technical deterioration is REAL - don't dismiss charts
✓ Multiple warning signs = AMPLIFY urgency (not average)
✓ Certainty reflects DATA QUALITY, not conviction
"""
```

### 2. INTERNET-ENHANCED ARTICLE FETCHING
**Problem:** Claude only sees headlines
**Solution:** Integrate article fetching like Codex

```python
def fetch_article_content(url: str) -> Optional[str]:
    """Fetch and extract article body (5000 char limit)"""
    try:
        import requests
        from bs4 import BeautifulSoup

        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (compatible; NewsAnalyzer/1.0)'
        })
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Remove scripts, styles, ads
        for tag in soup(['script', 'style', 'nav', 'footer', 'aside']):
            tag.decompose()

        # Extract article body
        article_candidates = soup.find_all(['article', 'div'],
                                          class_=re.compile(r'article|content|story'))

        text = ' '.join([c.get_text(separator=' ', strip=True)
                        for c in article_candidates])

        if not text:
            text = soup.get_text(separator=' ', strip=True)

        # Clean and truncate
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:5000] if len(text) > 5000 else text

    except Exception as e:
        logger.warning(f"Article fetch failed for {url}: {e}")
        return None
```

### 3. STRUCTURED TECHNICAL DATA INJECTION
**Problem:** Technical data passed as formatted text
**Solution:** Inject structured indicators directly

```python
def build_claude_exit_prompt(
    ticker: str,
    company_name: str,
    headline: str,
    article_text: str,  # Full text, not summary
    technical_indicators: Dict,
    news_url: str = ""
) -> str:
    """Build exit-optimized prompt with structured data"""

    # Format technical indicators clearly
    tech_summary = f"""
TECHNICAL ANALYSIS DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Price: ₹{technical_indicators.get('current_price', 'N/A')}
20-Day SMA: ₹{technical_indicators.get('sma_20', 'N/A')} ({technical_indicators.get('price_vs_sma20_pct', 'N/A'):.1f}%)
50-Day SMA: ₹{technical_indicators.get('sma_50', 'N/A')} ({technical_indicators.get('price_vs_sma50_pct', 'N/A'):.1f}%)
RSI(14): {technical_indicators.get('rsi', 'N/A'):.1f}
10-Day Momentum: {technical_indicators.get('momentum_10d_pct', 'N/A'):.1f}%
Volume Ratio (20D avg): {technical_indicators.get('volume_ratio', 'N/A'):.2f}x
Distance from 52W Low: {technical_indicators.get('distance_from_52w_low_pct', 'N/A'):.1f}%
ATR(14): ₹{technical_indicators.get('atr_14', 'N/A'):.2f} ({technical_indicators.get('atr_pct', 'N/A'):.1f}% of price)
Recent Trend (5D): {technical_indicators.get('recent_trend', 'N/A')}
Weekly Trend: {technical_indicators.get('weekly_trend', 'N/A')}
Bollinger Position: {technical_indicators.get('bb_position_z', 'N/A'):.2f} σ
"""

    # Build comprehensive prompt
    prompt = f"""EXIT ASSESSMENT REQUEST
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

STOCK: {ticker} ({company_name})

{tech_summary}

NEWS HEADLINE:
{headline}

ARTICLE CONTENT (Full Text):
{article_text if article_text else "No article content available"}

SOURCE: {news_url if news_url else "N/A"}

TASK: Assess whether this information justifies EXITING the position.
Consider: technical deterioration + fundamental risks + sentiment shift.

Return ONLY valid JSON with the exit assessment schema.
"""

    return prompt
```

### 4. INTRADAY FEEDBACK INTEGRATION
**Problem:** No learning from actual outcomes
**Solution:** Track performance and update Claude's calibration hints

```python
def update_claude_exit_hints(recent_decisions: List[Dict]) -> str:
    """Generate dynamic hints based on recent accuracy"""

    # Load recent JSONL decisions
    recent = load_jsonl_decisions(limit=50)

    # Calculate accuracy metrics
    immediate_exits = [d for d in recent if d['decision'] == 'EXIT']
    monitors = [d for d in recent if d['decision'] == 'MONITOR']
    holds = [d for d in recent if d['decision'] == 'HOLD']

    # Track actual price moves (yfinance)
    exit_accuracy = measure_accuracy(immediate_exits, threshold=-5, window='3d')
    monitor_accuracy = measure_accuracy(monitors, threshold=-3, window='5d')
    hold_accuracy = measure_accuracy(holds, threshold=0, window='7d')

    # Generate calibration hints
    hints = []

    if exit_accuracy < 0.70:  # Too many false positives
        hints.append("Recent EXIT calls have 30% false positive rate. "
                    "Require stronger confirmation before IMMEDIATE_EXIT. "
                    "Prefer MONITOR unless 2+ critical signals present.")

    if monitor_accuracy > 0.80:  # MONITOR working well
        hints.append("MONITOR decisions are performing well (80% accuracy). "
                    "Continue using 60-74 urgency range for warning signals.")

    if hold_accuracy < 0.60:  # Missing deterioration
        hints.append("HOLD decisions underperforming - missing early deterioration. "
                    "Lower threshold for technical warnings. "
                    "Weight RSI oversold + volume spike higher.")

    return "\n".join(hints) if hints else ""
```

### 5. ADAPTIVE THRESHOLD SYSTEM
**Problem:** Static thresholds regardless of data quality
**Solution:** Dynamic bands based on coverage

```python
def get_adaptive_thresholds(coverage: Dict) -> Dict:
    """Adjust thresholds based on data availability"""

    has_news = coverage.get('news_count', 0) > 0
    has_tech = coverage.get('price_hist', False)
    has_volume = coverage.get('volume', False)

    if has_news and has_tech and has_volume:
        # Full coverage - use strict thresholds
        return {
            'IMMEDIATE_EXIT': 90,
            'MONITOR': 65,
            'HOLD': 40
        }
    elif has_tech and has_volume:
        # Technical-only - more aggressive
        return {
            'IMMEDIATE_EXIT': 80,  # Lower bar without news
            'MONITOR': 55,
            'HOLD': 35
        }
    else:
        # Limited data - conservative
        return {
            'IMMEDIATE_EXIT': 95,  # Very high bar
            'MONITOR': 70,
            'HOLD': 50
        }
```

### 6. RISK MANAGEMENT AUTO-COMPUTATION
**Problem:** No stop/trail levels
**Solution:** Claude computes actionable risk levels

```python
def compute_claude_risk_levels(
    technical_indicators: Dict,
    exit_urgency: float,
    certainty: float
) -> Dict:
    """Compute stop-loss and trailing stop levels"""

    price = technical_indicators.get('current_price')
    atr = technical_indicators.get('atr_14')
    low_20_pct = technical_indicators.get('distance_from_20d_low_pct', 0)

    if not price or not atr:
        return {}

    # Swing low (20D)
    swing_low = price / (1 + low_20_pct / 100) if low_20_pct > 0 else price * 0.95

    # Stop-loss: tighter for high urgency
    if exit_urgency >= 80:
        stop = swing_low - 0.5 * atr  # Tight stop
    elif exit_urgency >= 60:
        stop = swing_low - 1.0 * atr  # Normal stop
    else:
        stop = swing_low - 1.5 * atr  # Loose stop

    # Trailing stop: based on volatility
    trail = 2.0 * atr if exit_urgency >= 70 else 1.5 * atr

    # Alert levels
    alert_reclaim = technical_indicators.get('sma_20')

    return {
        'stop_loss': f"₹{stop:.2f} (swing low - {0.5 if exit_urgency >= 80 else 1.0}×ATR)",
        'trailing_stop': f"₹{trail:.2f} ({2.0 if exit_urgency >= 70 else 1.5}×ATR)",
        'alert_reclaim_20dma': f"₹{alert_reclaim:.2f}" if alert_reclaim else None,
        'exit_urgency_context': 'TIGHT' if exit_urgency >= 80 else 'NORMAL'
    }
```

### 7. COMPREHENSIVE DECISION LOGGING
**Problem:** No performance tracking
**Solution:** JSONL logging with metadata

```python
def log_claude_exit_decision(
    ticker: str,
    decision: Dict,
    technical_data: Dict,
    prompt: str,
    response: str
) -> None:
    """Log Claude exit decision for feedback learning"""

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'provider': 'claude',
        'ticker': ticker,
        'decision': decision.get('exit_recommendation'),
        'urgency_score': decision.get('exit_urgency_score'),
        'certainty': decision.get('certainty'),
        'technical_score': decision.get('technical_breakdown_score'),
        'fundamental_score': decision.get('fundamental_risk_score'),
        'sentiment_score': decision.get('negative_sentiment_score'),
        'catalysts': decision.get('exit_catalysts', []),
        'current_price': technical_data.get('current_price'),
        'rsi': technical_data.get('rsi'),
        'prompt_hash': hashlib.md5(prompt.encode()).hexdigest()[:8],
        'response_length': len(response)
    }

    # Append to JSONL
    jsonl_path = 'outputs/claude_exit_decisions.jsonl'
    with open(jsonl_path, 'a') as f:
        f.write(json.dumps(log_entry, separators=(',', ':')) + '\n')
```

---

## Implementation Priority

### Phase 1: Core Enhancements (Immediate Impact)
1. ✅ Exit-specific system prompt
2. ✅ Structured technical data injection
3. ✅ Risk level computation

### Phase 2: Data Quality (1-2 days)
4. ✅ Internet-enhanced article fetching
5. ✅ Adaptive threshold system

### Phase 3: Learning Loop (Ongoing)
6. ✅ Intraday feedback integration
7. ✅ Decision logging + performance tracking

---

## Expected Performance Improvements

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Exit Accuracy | ~70% | 85-90% | Exit-specific prompt + full article text |
| False Positives | ~30% | <15% | Adaptive thresholds + feedback hints |
| Risk Management | None | Comprehensive | Auto stop/trail computation |
| Response Time | 8-12s | 10-15s | Article fetch overhead (+2-3s) |
| Learning Rate | None | Weekly | Intraday feedback + JSONL tracking |

---

## Competitive Advantages vs Codex

After implementation, Claude will have:

1. **Superior Language Understanding** - Better context extraction from news
2. **Nuanced Risk Assessment** - More sophisticated fundamental analysis
3. **Adaptive Learning** - Feedback-driven calibration hints
4. **Comprehensive Risk Mgmt** - ATR-based stops + urgency-adjusted levels
5. **Decision Transparency** - Full JSONL audit trail
6. **Internet-Enhanced** - Same article access as Codex
7. **Exit-Optimized Prompts** - Purpose-built for sell decisions

**Key Differentiator:** Claude's advanced reasoning + exit-specific calibration =
superior accuracy on complex deterioration patterns (e.g., margin compression,
management red flags, sector headwinds).

---

## Next Steps

1. Create `claude_exit_bridge.py` with all enhancements
2. Test on `exit.small.txt` dataset
3. Compare accuracy vs Codex on last 20 decisions
4. Deploy to production with A/B testing
5. Monitor feedback loop and iterate

Ready to implement?
