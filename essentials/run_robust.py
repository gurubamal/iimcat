import pandas as pd
import numpy as np
import re
from datetime import datetime
from collections import defaultdict

# Load latest data from today
try:
    df = pd.read_csv('outputs/ai_adjusted_top50_20250926_132945.csv')
    print(f'ROBUST SCANNER: Loaded {len(df)} opportunities from TODAY')
except Exception as e:
    print(f'ERROR loading data: {e}')
    exit()

# Entity blacklist for known bad matches (ZERO TOLERANCE)
entity_blacklist = {
    'GLOBAL': {
        'company_pattern': r'education',
        'exclude_patterns': [r'energy alliance', r'energy group', r'alliance plans']
    },
    'TI': {
        'company_pattern': r'tilaknagar',
        'exclude_patterns': [r'tide.*fintech', r'tide raises', r'tide.*tpg']
    },
    'IT': {
        'company_pattern': r'kotak.*nifty.*it.*etf',
        'exclude_patterns': [r'italy.*banking', r'italian.*deals', r'banking.*italy']
    },
    'SCI': {
        'company_pattern': r'shipping corporation',
        'exclude_patterns': [r'scientists', r'science', r'scientific']
    }
}

def validate_entity(ticker, company_name, news_title):
    ticker = ticker.upper()
    company_lower = company_name.lower()
    title_lower = news_title.lower()

    # ZERO TOLERANCE: Check blacklist first
    if ticker in entity_blacklist:
        rule = entity_blacklist[ticker]

        # Company must match expected pattern
        if not re.search(rule['company_pattern'], company_lower):
            return False, 0.0, f'COMPANY_MISMATCH_{ticker}'

        # News must NOT match exclude patterns (different entities)
        for exclude in rule['exclude_patterns']:
            if re.search(exclude, title_lower):
                return False, 0.0, f'ENTITY_MISMATCH_{exclude.replace(".*", "_")}'

    # Positive validation scoring
    validation_score = 0.0
    validation_reasons = []

    # 1. Exact ticker mention in title (strong signal)
    if ticker.lower() in title_lower:
        validation_score += 0.5
        validation_reasons.append('exact_ticker')

    # 2. Company name components in title
    company_words = [w for w in company_lower.split()
                    if len(w) > 4 and w not in ['limited', 'ltd', 'india', 'private', 'company']]

    word_matches = sum(1 for word in company_words if word in title_lower)
    if word_matches > 0:
        word_score = min(0.4, word_matches * 0.2)
        validation_score += word_score
        validation_reasons.append(f'company_words_{word_matches}')

    # MINIMUM THRESHOLD: Must meet minimum confidence
    min_threshold = 0.4
    if validation_score >= min_threshold:
        return True, validation_score, '|'.join(validation_reasons)
    else:
        return False, validation_score, f'LOW_CONFIDENCE_{validation_score:.2f}'

def assess_business_impact(row, validation_confidence):
    title = str(row['top_title']).lower()
    amount = float(row['amt_cr']) if row['amt_cr'] > 0 else 0

    impact_breakdown = {}

    # 1. FINANCIAL MATERIALITY (0-40 points)
    if amount > 1000:
        impact_breakdown['financial'] = 40
    elif amount > 500:
        impact_breakdown['financial'] = 35
    elif amount > 100:
        impact_breakdown['financial'] = 25
    elif amount > 50:
        impact_breakdown['financial'] = 15
    elif amount > 10:
        impact_breakdown['financial'] = 10
    else:
        # Text-based financial indicators
        if any(term in title for term in ['billion', 'bn']):
            impact_breakdown['financial'] = 30
        elif any(term in title for term in ['crore', 'million']):
            impact_breakdown['financial'] = 15
        else:
            impact_breakdown['financial'] = 0

    # 2. BUSINESS ACTION TYPE (0-30 points)
    high_impact_actions = ['acquisition', 'merger', 'ipo', 'contract', 'order', 'deal', 'partnership']
    medium_impact_actions = ['launch', 'expansion', 'facility', 'investment', 'approval']
    results_actions = ['results', 'profit', 'revenue', 'earnings']

    if any(action in title for action in high_impact_actions):
        impact_breakdown['business_action'] = 30
    elif any(action in title for action in medium_impact_actions):
        impact_breakdown['business_action'] = 20
    elif any(action in title for action in results_actions):
        impact_breakdown['business_action'] = 15
    else:
        impact_breakdown['business_action'] = 0

    # 3. MARKET MOMENTUM (0-20 points, can be negative)
    positive_signals = ['surge', 'rally', 'jump', 'soar', 'beat', 'strong', 'growth', 'rise']
    negative_signals = ['plunge', 'fall', 'drop', 'weak', 'loss', 'miss', 'disappoint', 'concern']

    pos_count = sum(1 for signal in positive_signals if signal in title)
    neg_count = sum(1 for signal in negative_signals if signal in title)

    if pos_count > neg_count:
        impact_breakdown['market_momentum'] = min(20, pos_count * 8)
    elif neg_count > pos_count:
        impact_breakdown['market_momentum'] = max(-20, -neg_count * 8)
    else:
        impact_breakdown['market_momentum'] = 0

    # 4. VALIDATION CONFIDENCE BONUS (0-10 points)
    impact_breakdown['validation_bonus'] = min(10, validation_confidence * 12)

    # Calculate total impact score
    total_impact = sum(impact_breakdown.values())
    normalized_score = max(0.0, min(100.0, total_impact)) / 100.0

    return normalized_score, impact_breakdown

# Process all stocks with robust validation
print('\nROBUST ENTITY VALIDATION PHASE:')
print('=' * 50)

robust_results = []
validation_stats = {'passed': 0, 'failed': 0, 'reasons': defaultdict(int)}

for _, row in df.iterrows():
    ticker = row['ticker']
    company = row['company_name']
    title = row['top_title']

    # PHASE 1: ZERO-TOLERANCE ENTITY VALIDATION
    is_valid, confidence, reason = validate_entity(ticker, company, title)

    if is_valid:
        validation_stats['passed'] += 1
        validation_stats['reasons'][reason] += 1

        # PHASE 2: BUSINESS IMPACT ASSESSMENT (only for validated entities)
        impact_score, impact_breakdown = assess_business_impact(row, confidence)

        robust_results.append({
            'ticker': ticker,
            'company': company,
            'title': title[:75],
            'amount': row['amt_cr'],
            'validation_confidence': confidence,
            'validation_reason': reason,
            'impact_score': impact_score,
            'financial_pts': impact_breakdown['financial'],
            'action_pts': impact_breakdown['business_action'],
            'momentum_pts': impact_breakdown['market_momentum'],
            'validation_pts': impact_breakdown['validation_bonus'],
            'original_score': row['adj_score']
        })

        print(f'PASS {ticker:8} ({confidence:.2f}) - {title[:45]}...')
    else:
        validation_stats['failed'] += 1
        validation_stats['reasons'][reason] += 1
        print(f'FAIL {ticker:8} - {reason}')

# Sort by robust impact score
robust_results.sort(key=lambda x: x['impact_score'], reverse=True)

# Save robust results
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
output_file = f'outputs/robust_validated_{timestamp}.csv'

if robust_results:
    pd.DataFrame(robust_results).to_csv(output_file, index=False)

# Display results
print(f'\nROBUST SCAN COMPLETED:')
print('=' * 50)
print(f'Validation Statistics:')
print(f'  PASSED: {validation_stats["passed"]} stocks')
print(f'  FAILED: {validation_stats["failed"]} stocks')
print(f'  SUCCESS RATE: {validation_stats["passed"]/(validation_stats["passed"]+validation_stats["failed"])*100:.1f}%')

print(f'\nFAILURE REASONS:')
for reason, count in validation_stats["reasons"].items():
    if 'MISMATCH' in reason or 'LOW_CONFIDENCE' in reason:
        print(f'  {reason}: {count}')

print(f'\nTOP 10 ROBUST OPPORTUNITIES (VALIDATED):')
print('=' * 50)

for i, stock in enumerate(robust_results[:10], 1):
    ticker = stock['ticker']
    score = stock['impact_score']
    amount = stock['amount']
    title = stock['title']

    amount_str = f' | Rs{amount:.0f}Cr' if amount > 0 else ''
    print(f'{i:2d}. {ticker:8} ({score:.3f}){amount_str}')
    print(f'    {title}...')
    print(f'    [F:{stock["financial_pts"]} A:{stock["action_pts"]} M:{stock["momentum_pts"]} V:{stock["validation_pts"]}]')
    print()

print(f'ROBUST RESULTS SAVED: {output_file}')
print('SYSTEM: Zero-tolerance entity validation + Business impact assessment')