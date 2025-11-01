#!/usr/bin/env python3
"""
INTELLIGENCE ENHANCER - Advanced Pattern Learning & Adaptive Intelligence
Next-level AI pattern recognition with market context awareness
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime, time
from collections import defaultdict, Counter
import re

class AdvancedIntelligenceEngine:
    """
    Advanced AI engine that learns from patterns and enhances intelligence
    """

    def __init__(self):
        self.intelligence_patterns = {
            'mega_deal_indicators': [
                r'(\d+)\s*crore.*deal',
                r'(\d+)\s*billion.*agreement',
                r'stake.*worth.*(\d+)',
                r'acquisition.*(\d+)',
                r'merger.*worth.*(\d+)'
            ],
            'strategic_action_patterns': [
                r'partnership.*with',
                r'joint.*venture',
                r'strategic.*alliance',
                r'collaboration.*agreement',
                r'licensing.*deal'
            ],
            'mega_action_patterns': [
                r'ipo.*subscription',
                r'merger.*approval',
                r'nclt.*approves',
                r'facility.*expansion',
                r'manufacturing.*plant'
            ],
            'market_timing_patterns': {
                'pre_market': (9, 15),      # 9:00-9:15 AM
                'opening_bell': (9, 16),    # 9:15-9:30 AM
                'morning_session': (9, 30), # 9:30-12:00 PM
                'afternoon_session': (13, 15), # 1:00-3:30 PM
                'closing_bell': (15, 16)     # 3:30-4:00 PM
            }
        }

        self.sector_intelligence = {
            'pharma': {
                'high_value_keywords': ['drug', 'patent', 'clinical', 'fda', 'approval'],
                'multiplier': 1.3
            },
            'energy': {
                'high_value_keywords': ['renewable', 'solar', 'wind', 'oil', 'gas'],
                'multiplier': 1.2
            },
            'finance': {
                'high_value_keywords': ['ncd', 'bond', 'loan', 'credit', 'fundraise'],
                'multiplier': 1.1
            },
            'technology': {
                'high_value_keywords': ['ai', 'digital', 'software', 'platform', 'tech'],
                'multiplier': 1.4
            }
        }

        self.learned_patterns = self._load_learned_patterns()

    def _load_learned_patterns(self):
        """Load previously learned patterns"""
        try:
            with open('learning/intelligence_patterns.json', 'r') as f:
                return json.load(f)
        except:
            return {
                'success_patterns': defaultdict(int),
                'failure_patterns': defaultdict(int),
                'sector_performance': defaultdict(dict),
                'timing_analysis': defaultdict(list)
            }

    def enhance_intelligence_multipliers(self, ticker, company, title, base_score, validation_confidence):
        """
        Advanced intelligence enhancement with pattern learning
        """
        intelligence_multipliers = {}
        enhanced_score = base_score

        title_lower = title.lower()
        company_lower = company.lower()

        # 1. MEGA DEAL DETECTION (Advanced Pattern Recognition)
        mega_deal_score = self._detect_mega_deal(title_lower)
        if mega_deal_score > 0:
            intelligence_multipliers['mega_deal'] = mega_deal_score
            enhanced_score *= (1.0 + mega_deal_score * 0.5)

        # 2. STRATEGIC ACTION INTELLIGENCE
        strategic_score = self._detect_strategic_action(title_lower)
        if strategic_score > 0:
            intelligence_multipliers['strategic_action'] = strategic_score
            enhanced_score *= (1.0 + strategic_score * 0.3)

        # 3. MARKET TIMING INTELLIGENCE
        timing_multiplier = self._assess_market_timing()
        if timing_multiplier > 1.0:
            intelligence_multipliers['market_timing'] = timing_multiplier
            enhanced_score *= timing_multiplier

        # 4. SECTOR-SPECIFIC INTELLIGENCE
        sector_multiplier = self._apply_sector_intelligence(company_lower, title_lower)
        if sector_multiplier > 1.0:
            intelligence_multipliers['sector_boost'] = sector_multiplier
            enhanced_score *= sector_multiplier

        # 5. LEARNED PATTERN INTELLIGENCE (Adaptive)
        pattern_multiplier = self._apply_learned_patterns(ticker, title_lower)
        if pattern_multiplier != 1.0:
            intelligence_multipliers['pattern_learned'] = pattern_multiplier
            enhanced_score *= pattern_multiplier

        # 6. BILLION MENTION DETECTION
        if any(term in title_lower for term in ['billion', 'bn']):
            intelligence_multipliers['billion_mention'] = 1.2
            enhanced_score *= 1.2

        # 7. IPO/LISTING INTELLIGENCE
        if any(term in title_lower for term in ['ipo', 'listing', 'public offer']):
            intelligence_multipliers['ipo_event'] = 1.3
            enhanced_score *= 1.3

        # 8. REGULATORY APPROVAL INTELLIGENCE
        if any(term in title_lower for term in ['nclt', 'approval', 'regulatory', 'clearance']):
            intelligence_multipliers['regulatory_approval'] = 1.1
            enhanced_score *= 1.1

        return enhanced_score, intelligence_multipliers

    def _detect_mega_deal(self, title):
        """Detect mega deals with financial magnitude assessment"""
        for pattern in self.intelligence_patterns['mega_deal_indicators']:
            match = re.search(pattern, title)
            if match:
                try:
                    amount = float(match.group(1))
                    if amount > 1000:  # > 1000 crores
                        return 1.0
                    elif amount > 500:  # > 500 crores
                        return 0.8
                    elif amount > 100:  # > 100 crores
                        return 0.6
                    else:
                        return 0.3
                except:
                    return 0.5  # Pattern matched but amount unclear
        return 0

    def _detect_strategic_action(self, title):
        """Detect strategic business actions"""
        for pattern in self.intelligence_patterns['strategic_action_patterns']:
            if re.search(pattern, title):
                return 1.0

        # Additional strategic keywords
        strategic_keywords = ['expansion', 'acquisition', 'merger', 'partnership', 'jv']
        strategic_count = sum(1 for keyword in strategic_keywords if keyword in title)

        return min(1.0, strategic_count * 0.5)

    def _assess_market_timing(self):
        """Market session timing intelligence"""
        current_time = datetime.now().time()
        current_hour = current_time.hour
        current_minute = current_time.minute

        # Pre-market intelligence boost
        if 7 <= current_hour <= 9:
            return 1.1  # Pre-market news gets boost

        # Market hours boost
        elif 9 <= current_hour <= 15:
            return 1.05  # Market hours slight boost

        # After-market processing
        elif 16 <= current_hour <= 20:
            return 1.0  # Normal processing

        return 1.0

    def _apply_sector_intelligence(self, company, title):
        """Apply sector-specific intelligence multipliers"""
        for sector, config in self.sector_intelligence.items():
            sector_keywords = config['high_value_keywords']
            if any(keyword in company or keyword in title for keyword in sector_keywords):
                return config['multiplier']
        return 1.0

    def _apply_learned_patterns(self, ticker, title):
        """Apply intelligence learned from historical patterns"""
        # Check if ticker has historically performed well
        if ticker in self.learned_patterns.get('success_patterns', {}):
            success_count = self.learned_patterns['success_patterns'][ticker]
            if success_count > 3:  # Historically successful ticker
                return 1.1

        # Check for failure patterns
        if ticker in self.learned_patterns.get('failure_patterns', {}):
            failure_count = self.learned_patterns['failure_patterns'][ticker]
            if failure_count > 3:  # Historically problematic ticker
                return 0.9

        return 1.0

    def learn_from_results(self, results_data):
        """Learn from scan results to improve future intelligence"""
        for result in results_data:
            ticker = result['ticker']
            score = result.get('enhanced_score', result.get('impact_score', 0))
            multipliers_str = result.get('intelligence_multipliers', '')
            multipliers = multipliers_str.split(', ') if isinstance(multipliers_str, str) else []

            # Learn success patterns
            if score > 0.5:  # High score = success
                self.learned_patterns['success_patterns'][ticker] += 1

                # Learn successful multiplier patterns
                for multiplier_type in multipliers:
                    if multiplier_type not in self.learned_patterns['sector_performance']:
                        self.learned_patterns['sector_performance'][multiplier_type] = {'success': 0, 'total': 0}
                    self.learned_patterns['sector_performance'][multiplier_type]['success'] += 1
                    self.learned_patterns['sector_performance'][multiplier_type]['total'] += 1

            # Learn failure patterns
            elif score < 0.2:  # Low score = failure
                self.learned_patterns['failure_patterns'][ticker] += 1

        # Save learned patterns
        self._save_learned_patterns()

    def _save_learned_patterns(self):
        """Save learned patterns for future use"""
        try:
            with open('learning/intelligence_patterns.json', 'w') as f:
                # Convert defaultdict to regular dict for JSON serialization
                patterns_to_save = {
                    'success_patterns': dict(self.learned_patterns['success_patterns']),
                    'failure_patterns': dict(self.learned_patterns['failure_patterns']),
                    'sector_performance': dict(self.learned_patterns['sector_performance']),
                    'timing_analysis': dict(self.learned_patterns['timing_analysis'])
                }
                json.dump(patterns_to_save, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save learned patterns: {e}")

    def generate_intelligence_report(self, scan_results):
        """Generate intelligence analysis report"""
        report = {
            'scan_timestamp': datetime.now().isoformat(),
            'total_opportunities': len(scan_results),
            'intelligence_distribution': Counter(),
            'top_patterns': [],
            'sector_analysis': {},
            'timing_analysis': {},
            'recommendations': []
        }

        # Analyze intelligence multiplier distribution
        for result in scan_results:
            multipliers = result.get('intelligence_multipliers', {})
            for multiplier_type in multipliers:
                report['intelligence_distribution'][multiplier_type] += 1

        # Generate recommendations
        if report['intelligence_distribution']['mega_deal'] > 3:
            report['recommendations'].append("HIGH MEGA-DEAL ACTIVITY: Multiple large transactions detected")

        if report['intelligence_distribution']['strategic_action'] > 5:
            report['recommendations'].append("STRATEGIC CONSOLIDATION: Increased partnership/alliance activity")

        return report

def enhance_existing_results(input_file, output_file):
    """Enhance existing scan results with advanced intelligence"""
    print("ENHANCING RESULTS WITH ADVANCED INTELLIGENCE")
    print("=" * 55)

    # Load existing results
    try:
        df = pd.read_csv(input_file)
        print(f"Loaded {len(df)} existing results")
    except Exception as e:
        print(f"Error loading {input_file}: {e}")
        return

    # Initialize intelligence engine
    intelligence_engine = AdvancedIntelligenceEngine()

    enhanced_results = []
    intelligence_stats = Counter()

    for _, row in df.iterrows():
        ticker = row['ticker']
        company = row['company']
        title = row['title']
        base_score = row['impact_score']
        validation_confidence = row['validation_confidence']

        # Apply advanced intelligence enhancement
        enhanced_score, new_multipliers = intelligence_engine.enhance_intelligence_multipliers(
            ticker, company, title, base_score, validation_confidence)

        # Combine with existing multipliers
        existing_multipliers = str(row.get('intelligence_multipliers', '')).split(', ')
        existing_multipliers = [m for m in existing_multipliers if m and m != 'nan']

        combined_multipliers = list(set(existing_multipliers + list(new_multipliers.keys())))

        # Update intelligence stats
        for multiplier in new_multipliers:
            intelligence_stats[multiplier] += 1

        enhanced_results.append({
            'ticker': ticker,
            'company': company,
            'title': title,
            'amount': row['amount'],
            'validation_confidence': validation_confidence,
            'base_score': base_score,
            'enhanced_score': enhanced_score,
            'intelligence_boost': enhanced_score / base_score if base_score > 0 else 1.0,
            'intelligence_multipliers': ', '.join(combined_multipliers),
            'new_intelligence': ', '.join(new_multipliers.keys())
        })

        print(f"BOOST {ticker:8} ({base_score:.3f} -> {enhanced_score:.3f}) {list(new_multipliers.keys())}")

    # Sort by enhanced score
    enhanced_results.sort(key=lambda x: x['enhanced_score'], reverse=True)

    # Save enhanced results
    pd.DataFrame(enhanced_results).to_csv(output_file, index=False)

    # Learn from results
    intelligence_engine.learn_from_results(enhanced_results)

    # Generate intelligence report
    intelligence_report = intelligence_engine.generate_intelligence_report(enhanced_results)

    print(f"\nADVANCED INTELLIGENCE ENHANCEMENT COMPLETED")
    print("=" * 55)
    print(f"Enhancement Statistics:")
    for multiplier, count in intelligence_stats.most_common(5):
        print(f"   {multiplier}: {count} stocks")

    print(f"\nTOP 10 ENHANCED OPPORTUNITIES:")
    print("-" * 40)
    for i, stock in enumerate(enhanced_results[:10], 1):
        boost = stock['intelligence_boost']
        boost_str = f" ({boost:.2f}x)" if boost > 1.1 else ""
        print(f"{i:2d}. {stock['ticker']:8} {stock['enhanced_score']:.3f}{boost_str}")
        if stock['new_intelligence']:
            print(f"    NEW: [{stock['new_intelligence']}]")

    print(f"\nEnhanced results saved: {output_file}")
    return output_file

if __name__ == "__main__":
    # Enhance the latest intelligent scan results
    input_file = 'outputs/intelligent_scan_20250927_172159.csv'
    output_file = f'outputs/enhanced_intelligence_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

    enhance_existing_results(input_file, output_file)