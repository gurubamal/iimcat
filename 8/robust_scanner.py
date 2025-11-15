#!/usr/bin/env python3
"""
ROBUST SCANNER - Entity-Validated Stock Assessment System
Foundation-first approach: Perfect entity validation → Business impact scoring
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime
from collections import defaultdict

class RobustEntityValidator:
    """
    Foundation-level entity validation with zero-tolerance for mismatches
    """

    def __init__(self):
        # Known problematic ticker mappings (company vs news entity mismatches)
        self.entity_blacklist = {
            'GLOBAL': {
                'company_pattern': r'education',
                'exclude_news_patterns': [r'energy alliance', r'energy group', r'alliance plans']
            },
            'TI': {
                'company_pattern': r'tilaknagar',
                'exclude_news_patterns': [r'tide.*fintech', r'tide raises', r'tide.*tpg']
            },
            'IT': {
                'company_pattern': r'kotak.*nifty.*it.*etf',
                'exclude_news_patterns': [r'italy.*banking', r'italian.*deals']
            }
        }

        # Sector classification for validation
        self.sector_keywords = {
            'education': ['education', 'learning', 'school', 'university', 'training'],
            'energy': ['energy', 'power', 'renewable', 'solar', 'wind', 'oil', 'gas'],
            'finance': ['financial', 'bank', 'insurance', 'credit', 'loan', 'fund'],
            'pharma': ['pharmaceutical', 'drug', 'medicine', 'healthcare', 'biotech'],
            'it': ['software', 'technology', 'digital', 'computing', 'data'],
            'manufacturing': ['manufacturing', 'production', 'factory', 'industrial'],
            'real_estate': ['real estate', 'property', 'construction', 'housing'],
            'retail': ['retail', 'consumer', 'shopping', 'commerce']
        }

    def validate_entity_match(self, ticker, company_name, news_title):
        """
        Core validation: Does the news actually relate to this company?
        Returns: (is_valid: bool, confidence: float, reason: str)
        """
        ticker = ticker.upper()
        company_lower = company_name.lower()
        title_lower = news_title.lower()

        # Check blacklist first (known bad matches)
        if ticker in self.entity_blacklist:
            blacklist_rule = self.entity_blacklist[ticker]

            # Check if company matches expected pattern
            if not re.search(blacklist_rule['company_pattern'], company_lower):
                return False, 0.0, f"Company pattern mismatch for {ticker}"

            # Check if news contains excluded patterns
            for exclude_pattern in blacklist_rule['exclude_news_patterns']:
                if re.search(exclude_pattern, title_lower):
                    return False, 0.0, f"News about different entity: {exclude_pattern}"

        # Sector consistency check
        company_sector = self._classify_sector(company_lower)
        news_sector = self._classify_sector(title_lower)

        if company_sector and news_sector and company_sector != news_sector:
            return False, 0.1, f"Sector mismatch: {company_sector} vs {news_sector}"

        # Positive validation checks
        validation_score = 0.0
        validation_reasons = []

        # 1. Exact ticker mention in title
        if ticker.lower() in title_lower:
            validation_score += 0.4
            validation_reasons.append("exact_ticker_match")

        # 2. Company name components in title
        company_words = [w for w in company_lower.split()
                        if len(w) > 4 and w not in ['limited', 'ltd', 'india', 'private', 'company']]

        word_matches = sum(1 for word in company_words if word in title_lower)
        if word_matches > 0:
            word_score = min(0.4, word_matches * 0.2)
            validation_score += word_score
            validation_reasons.append(f"company_words_{word_matches}")

        # 3. Context validation (surrounding words make sense)
        if validation_score > 0.3:
            context_valid = self._validate_context(ticker, company_lower, title_lower)
            if context_valid:
                validation_score += 0.2
                validation_reasons.append("context_valid")

        # Minimum threshold for acceptance
        if validation_score >= 0.5:
            return True, validation_score, "|".join(validation_reasons)
        else:
            return False, validation_score, f"Low_confidence_{validation_score:.2f}"

    def _classify_sector(self, text):
        """Classify text into business sector"""
        for sector, keywords in self.sector_keywords.items():
            if any(keyword in text for keyword in keywords):
                return sector
        return None

    def _validate_context(self, ticker, company, title):
        """Additional context validation for ambiguous cases"""
        # For short tickers, require stronger context validation
        if len(ticker) <= 3:
            # Check if surrounding words in title make sense with company
            title_words = title.split()
            for i, word in enumerate(title_words):
                if ticker.lower() in word:
                    # Check context window around ticker mention
                    start = max(0, i-2)
                    end = min(len(title_words), i+3)
                    context = " ".join(title_words[start:end])

                    # If context mentions different organizations, it's likely wrong
                    if any(org in context for org in ['alliance', 'group', 'association', 'foundation']):
                        return False

        return True

class RobustBusinessAssessment:
    """
    Business impact assessment - only runs AFTER entity validation passes
    """

    def __init__(self, data_df):
        self.df = data_df
        self._learn_patterns()

    def _learn_patterns(self):
        """Learn patterns from validated data only"""
        amounts = [row['amt_cr'] for _, row in self.df.iterrows() if row['amt_cr'] > 0]

        if amounts:
            self.financial_percentiles = np.percentile(amounts, [50, 75, 90, 95])
        else:
            self.financial_percentiles = [0, 0, 0, 0]

    def assess_business_impact(self, row, validation_confidence):
        """
        Assess business impact - only for validated entities
        """
        title = str(row['top_title']).lower()
        amount = float(row['amt_cr']) if row['amt_cr'] > 0 else 0

        impact_score = 0.0
        components = {}

        # 1. FINANCIAL MATERIALITY (0-40 points)
        if amount > 0:
            if amount >= self.financial_percentiles[3]:  # 95th percentile
                components['financial'] = 40
            elif amount >= self.financial_percentiles[2]:  # 90th percentile
                components['financial'] = 30
            elif amount >= self.financial_percentiles[1]:  # 75th percentile
                components['financial'] = 20
            elif amount >= self.financial_percentiles[0]:  # 50th percentile
                components['financial'] = 10
            else:
                components['financial'] = 5
        else:
            # Look for large value mentions in text
            if any(term in title for term in ['billion', 'bn']):
                components['financial'] = 25
            elif any(term in title for term in ['crore', 'million']):
                components['financial'] = 10
            else:
                components['financial'] = 0

        # 2. BUSINESS ACTION TYPE (0-30 points)
        high_impact = ['acquisition', 'merger', 'ipo', 'contract', 'order', 'deal', 'partnership']
        medium_impact = ['launch', 'expansion', 'facility', 'investment', 'approval']
        low_impact = ['results', 'profit', 'revenue']

        if any(action in title for action in high_impact):
            components['business_action'] = 30
        elif any(action in title for action in medium_impact):
            components['business_action'] = 20
        elif any(action in title for action in low_impact):
            components['business_action'] = 10
        else:
            components['business_action'] = 0

        # 3. MARKET IMPACT (0-20 points)
        positive_signals = ['surge', 'rally', 'jump', 'soar', 'beat', 'strong', 'growth']
        negative_signals = ['plunge', 'fall', 'drop', 'weak', 'loss', 'miss']

        pos_count = sum(1 for signal in positive_signals if signal in title)
        neg_count = sum(1 for signal in negative_signals if signal in title)

        if pos_count > neg_count:
            components['market_impact'] = min(20, pos_count * 7)
        elif neg_count > pos_count:
            components['market_impact'] = max(-20, -neg_count * 7)
        else:
            components['market_impact'] = 0

        # 4. ENTITY VALIDATION BONUS (0-10 points)
        components['validation_bonus'] = min(10, validation_confidence * 10)

        # Calculate total impact
        total_score = sum(components.values())
        normalized_score = max(0.0, min(100.0, total_score)) / 100.0

        return normalized_score, components

def run_robust_scan():
    """
    Run complete robust scan with entity validation first
    """
    print("🔧 INITIALIZING ROBUST SCANNER WITH ENTITY VALIDATION")
    print("=" * 60)

    # Load latest data
    try:
        df = pd.read_csv('outputs/ai_adjusted_top50_20250925_001820.csv')
        print(f"📊 Loaded {len(df)} opportunities from latest scan")
    except:
        print("❌ No recent scan data found. Run a fresh scan first.")
        return

    # Initialize robust systems
    validator = RobustEntityValidator()
    assessor = RobustBusinessAssessment(df)

    # Process each stock with robust validation
    robust_results = []
    validation_stats = {'passed': 0, 'failed': 0, 'reasons': defaultdict(int)}

    print("\n🔍 ENTITY VALIDATION PHASE")
    print("-" * 30)

    for _, row in df.iterrows():
        ticker = row['ticker']
        company = row['company_name']
        title = row['top_title']

        # PHASE 1: Entity Validation (Zero Tolerance)
        is_valid, confidence, reason = validator.validate_entity_match(ticker, company, title)

        if is_valid:
            validation_stats['passed'] += 1
            validation_stats['reasons'][reason] += 1

            # PHASE 2: Business Assessment (Only for validated entities)
            impact_score, impact_components = assessor.assess_business_impact(row, confidence)

            robust_results.append({
                'ticker': ticker,
                'company': company,
                'title': title[:80],
                'amount': row['amt_cr'],
                'validation_confidence': confidence,
                'validation_reason': reason,
                'impact_score': impact_score,
                'financial_pts': impact_components['financial'],
                'action_pts': impact_components['business_action'],
                'market_pts': impact_components['market_impact'],
                'validation_pts': impact_components['validation_bonus'],
                'original_score': row['adj_score']
            })

            print(f"✅ {ticker:8} ({confidence:.2f}) - {title[:50]}...")
        else:
            validation_stats['failed'] += 1
            validation_stats['reasons'][reason] += 1
            print(f"❌ {ticker:8} REJECTED - {reason}")

    # Sort by robust impact score
    robust_results.sort(key=lambda x: x['impact_score'], reverse=True)

    # Save robust results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'outputs/robust_validated_{timestamp}.csv'

    robust_df = pd.DataFrame(robust_results)
    if len(robust_df) > 0:
        robust_df.to_csv(output_file, index=False)

    # Print results
    print(f"\n🏆 ROBUST SCAN RESULTS")
    print("=" * 50)
    print(f"📊 Validation Stats:")
    print(f"   ✅ Passed: {validation_stats['passed']}")
    print(f"   ❌ Failed: {validation_stats['failed']}")
    print(f"   🎯 Success Rate: {validation_stats['passed']/(validation_stats['passed']+validation_stats['failed'])*100:.1f}%")

    print(f"\n🚀 TOP 10 ROBUST OPPORTUNITIES:")
    print("-" * 50)

    for i, stock in enumerate(robust_results[:10], 1):
        ticker = stock['ticker']
        score = stock['impact_score']
        amount = stock['amount']
        title = stock['title']

        amount_str = f" | ₹{amount:.0f}Cr" if amount > 0 else ""
        print(f"{i:2d}. **{ticker}** ({score:.3f}){amount_str}")
        print(f"    {title}...")
        print(f"    [F:{stock['financial_pts']} A:{stock['action_pts']} M:{stock['market_pts']} V:{stock['validation_pts']}]")
        print()

    print(f"💾 Robust results saved to: {output_file}")
    print(f"🔧 Entity validation applied with zero tolerance")
    print(f"📈 Business assessment only on validated entities")

    return output_file

if __name__ == "__main__":
    run_robust_scan()