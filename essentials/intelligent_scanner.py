#!/usr/bin/env python3
"""
INTELLIGENT SCANNER - AI-Enhanced Stock Assessment with Advanced Intelligence
Combines zero-tolerance entity validation with intelligent pattern recognition
"""

import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import json

class IntelligentEntityValidator:
    """
    Advanced entity validation with AI pattern recognition
    """

    def __init__(self):
        # Enhanced entity blacklist with intelligent patterns
        self.entity_blacklist = {
            'GLOBAL': {
                'company_sectors': ['education', 'learning'],
                'exclude_entities': ['energy alliance', 'energy group', 'alliance plans', 'climate fund'],
                'context_validation': True
            },
            'TI': {
                'company_sectors': ['tilaknagar', 'industries', 'alcohol'],
                'exclude_entities': ['tide fintech', 'tide raises', 'tide tpg', 'fintech tide'],
                'context_validation': True
            },
            'IT': {
                'company_sectors': ['kotak', 'nifty', 'etf', 'index'],
                'exclude_entities': ['italy banking', 'italian deals', 'banking italy'],
                'context_validation': True
            },
            'SCI': {
                'company_sectors': ['shipping', 'corporation', 'maritime'],
                'exclude_entities': ['scientists', 'science', 'scientific', 'research'],
                'context_validation': True
            },
            'OIL': {
                'company_sectors': ['oil india', 'petroleum'],
                'exclude_entities': ['oil prices', 'crude oil', 'oil market', 'brent oil'],
                'require_company_context': True
            }
        }

        # Intelligent sector classification
        self.sector_intelligence = {
            'financial_services': {
                'keywords': ['bank', 'financial', 'insurance', 'fund', 'credit', 'loan', 'ncd', 'bond'],
                'patterns': [r'raises.*cr.*ncd', r'launches.*fund', r'financial.*services']
            },
            'pharmaceutical': {
                'keywords': ['drug', 'pharma', 'medicine', 'healthcare', 'biotech', 'clinical'],
                'patterns': [r'drug.*deal', r'cancer.*drug', r'pharmaceutical', r'clinical.*trial']
            },
            'technology': {
                'keywords': ['tech', 'software', 'digital', 'it', 'data', 'ai', 'automation'],
                'patterns': [r'technology.*ipo', r'tech.*platform', r'digital.*transformation']
            },
            'manufacturing': {
                'keywords': ['manufacturing', 'factory', 'production', 'industrial', 'facility'],
                'patterns': [r'manufacturing.*facility', r'production.*plant', r'factory.*expansion']
            },
            'energy': {
                'keywords': ['energy', 'power', 'renewable', 'solar', 'oil', 'gas', 'electricity'],
                'patterns': [r'energy.*alliance', r'renewable.*energy', r'power.*plant']
            }
        }

        # Pattern intelligence for business actions
        self.action_intelligence = {
            'mega_deals': {
                'patterns': [r'acquisition.*billion', r'deal.*billion', r'merger.*billion'],
                'multiplier': 2.0
            },
            'strategic_partnerships': {
                'patterns': [r'partnership.*with', r'joint.*venture', r'collaboration.*with'],
                'multiplier': 1.5
            },
            'ipo_momentum': {
                'patterns': [r'ipo.*subscribed', r'ipo.*oversubscribed', r'ipo.*response'],
                'multiplier': 1.8
            },
            'regulatory_approvals': {
                'patterns': [r'nclt.*approves', r'regulatory.*approval', r'clearance.*received'],
                'multiplier': 1.3
            }
        }

    def intelligent_entity_validation(self, ticker, company_name, news_title):
        """
        Advanced entity validation with AI intelligence
        """
        ticker = ticker.upper()
        company_lower = company_name.lower()
        title_lower = news_title.lower()

        # Phase 1: Zero-tolerance blacklist check
        if ticker in self.entity_blacklist:
            rule = self.entity_blacklist[ticker]

            # Check company sector alignment
            company_match = any(sector in company_lower for sector in rule['company_sectors'])
            if not company_match:
                return False, 0.0, f'SECTOR_MISMATCH_{ticker}', 'company_sector_fail'

            # Check for excluded entities (different organizations)
            for exclude_entity in rule['exclude_entities']:
                if exclude_entity in title_lower:
                    return False, 0.0, f'ENTITY_MISMATCH_{exclude_entity.replace(" ", "_")}', 'exclude_entity_match'

        # Phase 2: Intelligent pattern matching
        validation_score = 0.0
        validation_components = {}

        # 1. Exact ticker match (strong signal)
        if ticker.lower() in title_lower:
            validation_score += 0.4
            validation_components['exact_ticker'] = 0.4
        else:
            validation_components['exact_ticker'] = 0.0

        # 2. Company name semantic matching
        company_words = [w for w in company_lower.split()
                        if len(w) > 4 and w not in ['limited', 'ltd', 'india', 'private', 'company', 'corporation']]

        semantic_score = 0.0
        for word in company_words:
            if word in title_lower:
                # Weight longer, more specific words higher
                word_weight = min(0.2, len(word) / 20)
                semantic_score += word_weight

        validation_score += min(0.3, semantic_score)
        validation_components['semantic_match'] = min(0.3, semantic_score)

        # 3. Sector consistency intelligence
        company_sector = self._classify_intelligent_sector(company_lower)
        news_sector = self._classify_intelligent_sector(title_lower)

        if company_sector and news_sector:
            if company_sector == news_sector:
                validation_score += 0.2
                validation_components['sector_alignment'] = 0.2
            else:
                validation_score -= 0.1
                validation_components['sector_alignment'] = -0.1
        else:
            validation_components['sector_alignment'] = 0.0

        # 4. Context intelligence for ambiguous tickers
        if len(ticker) <= 3:
            context_score = self._analyze_context_intelligence(ticker, title_lower)
            validation_score += context_score
            validation_components['context_intelligence'] = context_score
        else:
            validation_components['context_intelligence'] = 0.0

        # 5. News quality intelligence
        quality_score = self._assess_news_quality(title_lower)
        validation_score += quality_score
        validation_components['news_quality'] = quality_score

        # Final validation decision
        confidence_threshold = 0.5
        if validation_score >= confidence_threshold:
            return True, validation_score, 'VALIDATED', validation_components
        else:
            return False, validation_score, f'LOW_CONFIDENCE_{validation_score:.2f}', validation_components

    def _classify_intelligent_sector(self, text):
        """Intelligent sector classification with pattern matching"""
        sector_scores = {}

        for sector, intelligence in self.sector_intelligence.items():
            score = 0.0

            # Keyword matching
            for keyword in intelligence['keywords']:
                if keyword in text:
                    score += 1.0

            # Pattern matching (more sophisticated)
            for pattern in intelligence['patterns']:
                if re.search(pattern, text):
                    score += 2.0

            if score > 0:
                sector_scores[sector] = score

        if sector_scores:
            return max(sector_scores, key=sector_scores.get)
        return None

    def _analyze_context_intelligence(self, ticker, title):
        """Advanced context analysis for short tickers"""
        context_score = 0.0

        # Check for organizational indicators that suggest different entities
        org_indicators = ['alliance', 'association', 'group', 'foundation', 'institute', 'council']
        if any(indicator in title for indicator in org_indicators):
            context_score -= 0.2

        # Check for financial action words that suggest legitimate company news
        financial_actions = ['raises', 'launches', 'issues', 'announces', 'reports', 'declares']
        if any(action in title for action in financial_actions):
            context_score += 0.1

        return context_score

    def _assess_news_quality(self, title):
        """Assess the quality and specificity of news"""
        quality_score = 0.0

        # Specific financial amounts suggest higher quality
        if re.search(r'\d+.*crore|\d+.*billion|\d+.*million', title):
            quality_score += 0.1

        # Specific company actions suggest higher quality
        specific_actions = ['acquisition', 'merger', 'ipo', 'contract', 'partnership', 'deal']
        if any(action in title for action in specific_actions):
            quality_score += 0.1

        # Vague or generic terms suggest lower quality
        vague_terms = ['expects', 'likely', 'may', 'could', 'might', 'analysis', 'view']
        if any(term in title for term in vague_terms):
            quality_score -= 0.05

        return quality_score

class IntelligentBusinessAssessment:
    """
    AI-enhanced business impact assessment with intelligent pattern recognition
    """

    def __init__(self, data_df):
        self.df = data_df
        self.intelligence_patterns = self._learn_intelligence_patterns()

    def _learn_intelligence_patterns(self):
        """Learn intelligent patterns from the dataset"""
        patterns = {
            'financial_benchmarks': self._analyze_financial_patterns(),
            'action_patterns': self._analyze_action_patterns(),
            'market_signals': self._analyze_market_signals(),
            'temporal_patterns': self._analyze_temporal_patterns()
        }
        return patterns

    def _analyze_financial_patterns(self):
        """Analyze financial amount patterns intelligently"""
        amounts = [row['amt_cr'] for _, row in self.df.iterrows() if row['amt_cr'] > 0]

        if amounts:
            amounts_array = np.array(amounts)
            return {
                'percentiles': np.percentile(amounts_array, [25, 50, 75, 90, 95, 99]).tolist(),
                'mean': np.mean(amounts_array),
                'std': np.std(amounts_array),
                'high_value_threshold': np.percentile(amounts_array, 90),
                'mega_deal_threshold': np.percentile(amounts_array, 95)
            }
        return {'percentiles': [0]*6, 'mean': 0, 'std': 0, 'high_value_threshold': 100, 'mega_deal_threshold': 500}

    def _analyze_action_patterns(self):
        """Analyze business action patterns"""
        all_titles = [str(row['top_title']).lower() for _, row in self.df.iterrows()]

        action_frequency = Counter()
        for title in all_titles:
            # Extract business actions
            actions = re.findall(r'\b(acquisition|merger|ipo|deal|contract|partnership|launch|expansion)\b', title)
            action_frequency.update(actions)

        return {
            'top_actions': action_frequency.most_common(10),
            'action_diversity': len(action_frequency),
            'total_actions': sum(action_frequency.values())
        }

    def _analyze_market_signals(self):
        """Analyze market sentiment signals"""
        all_titles = [str(row['top_title']).lower() for _, row in self.df.iterrows()]

        positive_signals = []
        negative_signals = []

        for title in all_titles:
            pos_matches = re.findall(r'\b(surge|rally|jump|soar|beat|strong|growth|rise|gain)\b', title)
            neg_matches = re.findall(r'\b(plunge|fall|drop|weak|loss|miss|decline|crash)\b', title)

            positive_signals.extend(pos_matches)
            negative_signals.extend(neg_matches)

        return {
            'positive_frequency': Counter(positive_signals),
            'negative_frequency': Counter(negative_signals),
            'sentiment_ratio': len(positive_signals) / max(1, len(negative_signals))
        }

    def _analyze_temporal_patterns(self):
        """Analyze temporal patterns in the data"""
        return {
            'scan_time': datetime.now().isoformat(),
            'data_freshness': 'current',
            'market_session': self._detect_market_session()
        }

    def _detect_market_session(self):
        """Detect if we're in market hours, pre-market, or post-market"""
        now = datetime.now()
        hour = now.hour

        if 9 <= hour <= 15:
            return 'market_hours'
        elif 6 <= hour < 9:
            return 'pre_market'
        else:
            return 'post_market'

    def intelligent_impact_assessment(self, row, validation_confidence, validation_components):
        """
        AI-enhanced business impact assessment
        """
        title = str(row['top_title']).lower()
        amount = float(row['amt_cr']) if row['amt_cr'] > 0 else 0

        impact_components = {}
        intelligence_multipliers = {}

        # 1. INTELLIGENT FINANCIAL SCORING (0-50 points)
        financial_benchmarks = self.intelligence_patterns['financial_benchmarks']

        if amount > 0:
            if amount >= financial_benchmarks['mega_deal_threshold']:
                impact_components['financial_base'] = 50
                intelligence_multipliers['mega_deal'] = 1.5
            elif amount >= financial_benchmarks['high_value_threshold']:
                impact_components['financial_base'] = 40
                intelligence_multipliers['high_value'] = 1.2
            elif amount >= financial_benchmarks['percentiles'][3]:  # 75th percentile
                impact_components['financial_base'] = 30
            elif amount >= financial_benchmarks['percentiles'][2]:  # 50th percentile
                impact_components['financial_base'] = 20
            else:
                impact_components['financial_base'] = 10
        else:
            # Intelligent text-based financial detection
            if re.search(r'billion|\d+.*bn', title):
                impact_components['financial_base'] = 40
                intelligence_multipliers['billion_mention'] = 1.3
            elif re.search(r'crore|\d+.*cr', title):
                impact_components['financial_base'] = 25
            elif any(term in title for term in ['million', 'funding', 'investment']):
                impact_components['financial_base'] = 15
            else:
                impact_components['financial_base'] = 0

        # 2. INTELLIGENT ACTION CLASSIFICATION (0-40 points)
        action_patterns = self.intelligence_patterns['action_patterns']

        # Mega actions (transformational)
        mega_actions = ['acquisition', 'merger', 'ipo']
        strategic_actions = ['partnership', 'joint venture', 'collaboration', 'deal']
        operational_actions = ['launch', 'expansion', 'facility', 'contract']
        financial_actions = ['raises', 'issues', 'funding', 'investment']

        if any(action in title for action in mega_actions):
            impact_components['action_base'] = 40
            intelligence_multipliers['mega_action'] = 1.4
        elif any(action in title for action in strategic_actions):
            impact_components['action_base'] = 30
            intelligence_multipliers['strategic_action'] = 1.2
        elif any(action in title for action in operational_actions):
            impact_components['action_base'] = 20
        elif any(action in title for action in financial_actions):
            impact_components['action_base'] = 15
        else:
            impact_components['action_base'] = 0

        # 3. INTELLIGENT MARKET MOMENTUM (0-30 points, can be negative)
        market_signals = self.intelligence_patterns['market_signals']

        positive_signals = ['surge', 'rally', 'jump', 'soar', 'beat', 'strong', 'growth', 'rise', 'gain']
        negative_signals = ['plunge', 'fall', 'drop', 'weak', 'loss', 'miss', 'decline', 'crash']

        pos_count = sum(1 for signal in positive_signals if signal in title)
        neg_count = sum(1 for signal in negative_signals if signal in title)

        if pos_count > neg_count:
            momentum_score = min(30, pos_count * 12)
            if pos_count >= 2:
                intelligence_multipliers['strong_momentum'] = 1.3
        elif neg_count > pos_count:
            momentum_score = max(-30, -neg_count * 12)
            intelligence_multipliers['negative_momentum'] = 0.7
        else:
            momentum_score = 0

        impact_components['momentum'] = momentum_score

        # 4. ENTITY VALIDATION INTELLIGENCE BONUS (0-20 points)
        validation_bonus = 0
        if validation_components:
            # Reward high-quality validation components
            if validation_components.get('exact_ticker', 0) > 0:
                validation_bonus += 8
            if validation_components.get('semantic_match', 0) > 0.2:
                validation_bonus += 6
            if validation_components.get('sector_alignment', 0) > 0:
                validation_bonus += 4
            if validation_components.get('news_quality', 0) > 0:
                validation_bonus += 2

        impact_components['validation_intelligence'] = validation_bonus

        # 5. TEMPORAL INTELLIGENCE (0-10 points)
        temporal_patterns = self.intelligence_patterns['temporal_patterns']
        market_session = temporal_patterns['market_session']

        if market_session == 'market_hours':
            impact_components['temporal'] = 10
            intelligence_multipliers['market_hours'] = 1.1
        elif market_session == 'pre_market':
            impact_components['temporal'] = 8
        else:
            impact_components['temporal'] = 5

        # Calculate base impact score
        base_score = sum(impact_components.values())

        # Apply intelligence multipliers
        final_multiplier = 1.0
        for multiplier_name, multiplier_value in intelligence_multipliers.items():
            final_multiplier *= multiplier_value

        final_score = (base_score * final_multiplier) / 150.0  # Normalize to 0-1 scale
        final_score = max(0.0, min(1.0, final_score))

        return final_score, impact_components, intelligence_multipliers

def run_intelligent_scan():
    """
    Run complete intelligent scan with AI-enhanced validation and assessment
    """
    print("INTELLIGENT SCANNER - AI-Enhanced Analysis")
    print("=" * 60)

    # Load latest data
    try:
        df = pd.read_csv('outputs/ai_adjusted_top50_20250926_132945.csv')
        print(f"Loaded {len(df)} opportunities for intelligent analysis")
    except Exception as e:
        print(f"ERROR loading data: {e}")
        return

    # Initialize intelligent systems
    validator = IntelligentEntityValidator()
    assessor = IntelligentBusinessAssessment(df)

    print("\nINTELLIGENT VALIDATION & ASSESSMENT PHASE:")
    print("-" * 50)

    intelligent_results = []
    intelligence_stats = {
        'passed': 0, 'failed': 0, 'high_confidence': 0,
        'validation_reasons': defaultdict(int),
        'intelligence_multipliers': defaultdict(int)
    }

    for _, row in df.iterrows():
        ticker = row['ticker']
        company = row['company_name']
        title = row['top_title']

        # PHASE 1: Intelligent Entity Validation
        is_valid, confidence, reason, validation_components = validator.intelligent_entity_validation(
            ticker, company, title)

        if is_valid:
            intelligence_stats['passed'] += 1
            if confidence > 0.7:
                intelligence_stats['high_confidence'] += 1

            intelligence_stats['validation_reasons'][reason] += 1

            # PHASE 2: Intelligent Business Assessment
            impact_score, impact_components, intelligence_multipliers = assessor.intelligent_impact_assessment(
                row, confidence, validation_components)

            # Track intelligence multipliers
            for multiplier_name in intelligence_multipliers:
                intelligence_stats['intelligence_multipliers'][multiplier_name] += 1

            intelligent_results.append({
                'ticker': ticker,
                'company': company,
                'title': title[:80],
                'amount': row['amt_cr'],
                'validation_confidence': confidence,
                'validation_components': validation_components,
                'impact_score': impact_score,
                'impact_components': impact_components,
                'intelligence_multipliers': intelligence_multipliers,
                'original_score': row['adj_score']
            })

            multiplier_str = ', '.join(intelligence_multipliers.keys()) if intelligence_multipliers else 'none'
            print(f"PASS {ticker:8} ({confidence:.2f}, {impact_score:.3f}) - {title[:40]}...")
            print(f"     Intelligence: {multiplier_str}")

        else:
            intelligence_stats['failed'] += 1
            intelligence_stats['validation_reasons'][reason] += 1
            print(f"FAIL {ticker:8} - {reason}")

    # Sort by intelligent impact score
    intelligent_results.sort(key=lambda x: x['impact_score'], reverse=True)

    # Save intelligent results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'outputs/intelligent_scan_{timestamp}.csv'

    if intelligent_results:
        # Prepare flattened data for CSV
        csv_data = []
        for result in intelligent_results:
            csv_row = {
                'ticker': result['ticker'],
                'company': result['company'],
                'title': result['title'],
                'amount': result['amount'],
                'validation_confidence': result['validation_confidence'],
                'impact_score': result['impact_score'],
                'original_score': result['original_score']
            }

            # Add impact components
            for comp_name, comp_value in result['impact_components'].items():
                csv_row[f'impact_{comp_name}'] = comp_value

            # Add intelligence multipliers
            csv_row['intelligence_multipliers'] = ', '.join(result['intelligence_multipliers'].keys())

            csv_data.append(csv_row)

        pd.DataFrame(csv_data).to_csv(output_file, index=False)

    # Display results
    print(f"\nINTELLIGENT SCAN COMPLETED:")
    print("=" * 60)
    print(f"Intelligence Statistics:")
    print(f"  VALIDATED: {intelligence_stats['passed']} stocks")
    print(f"  REJECTED: {intelligence_stats['failed']} stocks")
    print(f"  HIGH CONFIDENCE: {intelligence_stats['high_confidence']} stocks")
    print(f"  SUCCESS RATE: {intelligence_stats['passed']/(intelligence_stats['passed']+intelligence_stats['failed'])*100:.1f}%")

    print(f"\nTop Intelligence Multipliers Applied:")
    from collections import Counter
    multiplier_counter = Counter(intelligence_stats['intelligence_multipliers'])
    for multiplier, count in multiplier_counter.most_common(5):
        print(f"  {multiplier}: {count} stocks")

    print(f"\nTOP 15 INTELLIGENT OPPORTUNITIES:")
    print("=" * 60)

    for i, stock in enumerate(intelligent_results[:15], 1):
        ticker = stock['ticker']
        score = stock['impact_score']
        amount = stock['amount']
        title = stock['title']
        multipliers = list(stock['intelligence_multipliers'].keys())

        amount_str = f" | Rs{amount:.0f}Cr" if amount > 0 else ""
        multiplier_str = f" [{', '.join(multipliers[:2])}]" if multipliers else ""

        print(f"{i:2d}. {ticker:8} ({score:.3f}){amount_str}{multiplier_str}")
        print(f"    {title}...")
        print()

    print(f"INTELLIGENT RESULTS SAVED: {output_file}")
    print("SYSTEM: AI-Enhanced validation + Intelligent impact assessment + Pattern recognition")

    return output_file

if __name__ == "__main__":
    run_intelligent_scan()