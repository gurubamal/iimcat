#!/usr/bin/env python3
"""
Enhanced Entity Resolution Engine for Maximum Intelligence Scanning

Critical component addressing the 50% entity mismatch rate discovered in system analysis.
Implements zero-tolerance policy for entity validation with sector-aware matching.
"""

import json
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class EntityProfile:
    ticker: str
    full_name: str
    sector: str
    business_type: str
    keywords: List[str]
    exclusion_keywords: List[str]
    aliases: List[str]

class EntityResolutionEngine:
    """
    Zero-tolerance entity validation system

    Addresses critical failures:
    - TI (Tilaknagar) vs Tide fintech
    - GLOBAL Education vs GLOBAL Energy Alliance
    - ACC Ltd vs "accelerator" programs
    """

    def __init__(self, config_path: str = "configs/entities.json"):
        self.config_path = config_path
        self.entity_db: Dict[str, EntityProfile] = {}
        self.sector_keywords: Dict[str, List[str]] = {}
        self.wrong_sector_indicators: Dict[str, List[str]] = {}
        self.load_entity_database()

    def load_entity_database(self):
        """Load and build comprehensive entity database"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Build entity profiles
            for ticker, data in config.get('entities', {}).items():
                self.entity_db[ticker] = EntityProfile(
                    ticker=ticker,
                    full_name=data['full_name'],
                    sector=data['sector'],
                    business_type=data['business_type'],
                    keywords=data['keywords'],
                    exclusion_keywords=data.get('exclusion_keywords', []),
                    aliases=data.get('aliases', [])
                )

            # Build sector classification
            self.sector_keywords = config.get('sector_keywords', {})
            self.wrong_sector_indicators = config.get('wrong_sector_indicators', {})

        except FileNotFoundError:
            logging.warning(f"Entity config not found: {self.config_path}. Using minimal defaults.")
            self._build_minimal_database()

    def _build_minimal_database(self):
        """Build minimal database for critical mismatches"""
        critical_entities = {
            'TI': EntityProfile(
                ticker='TI',
                full_name='Tilaknagar Industries Limited',
                sector='Alcobev',
                business_type='Manufacturing',
                keywords=['tilaknagar', 'liquor', 'alcobev', 'alcohol', 'spirits'],
                exclusion_keywords=['fintech', 'tide', 'banking', 'digital', 'payment'],
                aliases=['Tilaknagar Industries']
            ),
            'GLOBAL': EntityProfile(
                ticker='GLOBAL',
                full_name='Global Education Limited',
                sector='Education',
                business_type='Services',
                keywords=['education', 'learning', 'school', 'training', 'academic'],
                exclusion_keywords=['energy', 'alliance', 'fund', 'investment', 'petroleum'],
                aliases=['Global Education']
            ),
            'ACC': EntityProfile(
                ticker='ACC',
                full_name='ACC Limited',
                sector='Cement',
                business_type='Manufacturing',
                keywords=['cement', 'concrete', 'construction', 'building'],
                exclusion_keywords=['accelerator', 'startup', 'incubator', 'venture'],
                aliases=['ACC Limited', 'ACC Cement']
            )
        }
        self.entity_db.update(critical_entities)

    def validate_entity_match(self, ticker: str, title: str, content: str) -> Tuple[float, str]:
        """
        Core validation function with zero-tolerance policy

        Returns:
            (confidence_score, reason)
            - 0.0: Entity mismatch detected (ZERO TOLERANCE)
            - 0.5: Uncertain match, needs review
            - 1.0: High confidence match
        """
        if ticker not in self.entity_db:
            return 0.0, f"Unknown ticker: {ticker}"

        entity = self.entity_db[ticker]
        combined_text = (title + " " + content).lower()

        # Step 1: Check for exclusion keywords (ZERO TOLERANCE)
        for exclusion in entity.exclusion_keywords:
            if exclusion.lower() in combined_text:
                return 0.0, f"Exclusion detected: {exclusion} (wrong entity)"

        # Step 2: Check for wrong sector indicators
        wrong_sectors = self.wrong_sector_indicators.get(entity.sector, [])
        for wrong_indicator in wrong_sectors:
            if wrong_indicator.lower() in combined_text:
                return 0.0, f"Wrong sector indicator: {wrong_indicator}"

        # Step 3: Positive entity validation
        positive_matches = 0
        total_keywords = len(entity.keywords)

        for keyword in entity.keywords:
            if keyword.lower() in combined_text:
                positive_matches += 1

        # Step 4: Check for company name variations
        name_match = False
        for name_variant in [entity.full_name] + entity.aliases:
            if name_variant.lower() in combined_text:
                name_match = True
                break

        # Step 5: Calculate confidence score
        if name_match and positive_matches > 0:
            return 1.0, f"Strong match: name + {positive_matches} keywords"
        elif name_match:
            return 0.8, f"Name match only"
        elif positive_matches >= total_keywords // 2:
            return 0.6, f"Keyword match: {positive_matches}/{total_keywords}"
        elif positive_matches > 0:
            return 0.3, f"Weak keyword match: {positive_matches}/{total_keywords}"
        else:
            return 0.0, f"No entity indicators found"

    def extract_financial_amount(self, text: str) -> float:
        """Extract financial amounts in crores"""
        patterns = [
            r'₹\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*cr',
            r'rs\.?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*crore',
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*crore',
            r'\$\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*million',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    # Clean and convert
                    amount_str = matches[0].replace(',', '')
                    amount = float(amount_str)

                    # Convert to crores if needed
                    if 'million' in pattern:
                        amount = amount * 7.5  # Rough USD to INR crore conversion

                    return amount
                except ValueError:
                    continue

        return 0.0

    def classify_event_type(self, text: str) -> Tuple[str, float]:
        """Classify event type and assign impact score"""
        text_lower = text.lower()

        # High-impact events
        if any(keyword in text_lower for keyword in ['ipo', 'listing', 'public offering']):
            return 'IPO/listing', 0.9
        elif any(keyword in text_lower for keyword in ['acquisition', 'm&a', 'merger', 'takeover']):
            return 'M&A/acquisition', 0.8
        elif any(keyword in text_lower for keyword in ['block deal', 'bulk deal', 'stake sale']):
            return 'Block/bulk deal', 0.7

        # Medium-impact events
        elif any(keyword in text_lower for keyword in ['contract', 'order', 'award']):
            return 'Contract/order', 0.6
        elif any(keyword in text_lower for keyword in ['partnership', 'joint venture', 'collaboration']):
            return 'Partnership/JV', 0.5
        elif any(keyword in text_lower for keyword in ['expansion', 'facility', 'plant']):
            return 'Expansion', 0.4

        # Low-impact events
        elif any(keyword in text_lower for keyword in ['results', 'quarterly', 'earnings']):
            return 'Results/earnings', 0.3
        elif any(keyword in text_lower for keyword in ['appointment', 'resignation', 'management']):
            return 'Management', 0.2
        else:
            return 'General', 0.1

    def generate_validation_report(self, ticker: str, articles: List[dict]) -> dict:
        """Generate comprehensive validation report"""
        report = {
            'ticker': ticker,
            'total_articles': len(articles),
            'validated_articles': 0,
            'rejected_articles': 0,
            'validation_details': [],
            'average_confidence': 0.0,
            'event_distribution': {},
            'total_financial_value': 0.0
        }

        confidence_scores = []
        event_counts = {}

        for article in articles:
            confidence, reason = self.validate_entity_match(
                ticker, article.get('title', ''), article.get('content', '')
            )

            financial_amount = self.extract_financial_amount(article.get('content', ''))
            event_type, impact_score = self.classify_event_type(article.get('content', ''))

            validation_detail = {
                'title': article.get('title', '')[:100],
                'confidence': confidence,
                'reason': reason,
                'financial_amount_cr': financial_amount,
                'event_type': event_type,
                'impact_score': impact_score
            }

            report['validation_details'].append(validation_detail)
            confidence_scores.append(confidence)

            if confidence > 0.0:
                report['validated_articles'] += 1
                report['total_financial_value'] += financial_amount
            else:
                report['rejected_articles'] += 1

            event_counts[event_type] = event_counts.get(event_type, 0) + 1

        report['average_confidence'] = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        report['event_distribution'] = event_counts

        return report

def main():
    """Test the entity resolution engine"""
    resolver = EntityResolutionEngine()

    # Test critical mismatch cases
    test_cases = [
        ('TI', 'Tide fintech raises $120 million', 'fintech startup digital payments'),
        ('TI', 'Tilaknagar Industries Q2 results', 'alcohol beverage sales revenue'),
        ('GLOBAL', 'Global Energy Alliance summit', 'energy sector petroleum alliance'),
        ('GLOBAL', 'Global Education Limited expansion', 'education learning schools'),
        ('ACC', 'India Accelerator acquires MySOHO', 'startup accelerator incubator'),
        ('ACC', 'ACC Limited cement sales growth', 'cement concrete building materials')
    ]

    print("🔍 Entity Resolution Engine Test Results")
    print("=" * 50)

    for ticker, title, content in test_cases:
        confidence, reason = resolver.validate_entity_match(ticker, title, content)
        status = "✅ PASS" if confidence > 0.0 else "❌ REJECT"
        print(f"{status} {ticker}: {confidence:.2f} - {reason}")
        print(f"   Title: {title}")
        print(f"   Content: {content}")
        print()

if __name__ == "__main__":
    main()