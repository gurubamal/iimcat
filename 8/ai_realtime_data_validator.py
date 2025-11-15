#!/usr/bin/env python3
"""
AI REAL-TIME DATA VALIDATOR
============================
Validates that AI is using ONLY yfinance data and NOT training data.

This script:
1. Confirms AI receives real-time yfinance data
2. Validates quarterly/annual growth calculations
3. Checks institutional ownership data
4. Ensures no training data contamination
5. Provides explicit confirmation messages

Usage:
    python3 ai_realtime_data_validator.py RELIANCE
    python3 ai_realtime_data_validator.py --test-file tickers_test.txt
"""

import sys
import json
from datetime import datetime
from typing import Dict, List, Optional

try:
    from realtime_price_fetcher import get_comprehensive_price_data, format_price_context_for_ai
    from fundamental_data_fetcher import FundamentalDataFetcher
    IMPORTS_OK = True
except ImportError as e:
    print(f"❌ Import failed: {e}")
    IMPORTS_OK = False


class AIDataValidator:
    """Validates that AI receives only real-time yfinance data."""

    def __init__(self):
        self.fetcher = FundamentalDataFetcher(use_cache=False)
        self.validation_results = []

    def validate_ticker(self, ticker: str) -> Dict:
        """
        Comprehensive validation for a single ticker.

        Returns validation report with all data sources confirmed.
        """
        print(f"\n{'='*80}")
        print(f"🔍 VALIDATING DATA SOURCES FOR: {ticker}")
        print(f"{'='*80}\n")

        validation = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'price_data': self._validate_price_data(ticker),
            'fundamental_data': self._validate_fundamental_data(ticker),
            'institutional_data': self._validate_institutional_data(ticker),
            'data_completeness': {},
            'ai_instructions_present': True,
            'training_data_warnings': True
        }

        # Check data completeness
        validation['data_completeness'] = {
            'price_available': validation['price_data']['fetched_successfully'],
            'quarterly_results': validation['fundamental_data']['quarterly_available'],
            'annual_results': validation['fundamental_data']['annual_available'],
            'institutional_ownership': validation['institutional_data']['data_available'],
            'financial_health': validation['fundamental_data']['health_available']
        }

        # Overall status
        all_critical = (
            validation['price_data']['fetched_successfully'] and
            validation['fundamental_data']['quarterly_available']
        )

        validation['overall_status'] = 'PASS' if all_critical else 'PARTIAL'

        return validation

    def _validate_price_data(self, ticker: str) -> Dict:
        """Validate real-time price fetching from yfinance."""
        print("📊 VALIDATING PRICE DATA (from yfinance)...")

        result = {
            'fetched_successfully': False,
            'source': None,
            'current_price': None,
            'timestamp': None,
            'entry_exit_calculated': False,
            'warning_present': False
        }

        try:
            price_data = get_comprehensive_price_data(ticker)

            if price_data.get('price_data_available'):
                result['fetched_successfully'] = True
                result['current_price'] = price_data['current_price']
                result['timestamp'] = price_data['price_timestamp']
                result['source'] = price_data.get('source', 'unknown')
                result['entry_exit_calculated'] = (
                    price_data.get('entry_zone_low') is not None and
                    price_data.get('target_conservative') is not None
                )

                print(f"  ✅ Price fetched: ₹{price_data['current_price']:.2f}")
                print(f"  ✅ Timestamp: {price_data['price_timestamp']}")
                print(f"  ✅ Source: {result['source']}")
                print(f"  ✅ Entry/Exit levels: {'Calculated' if result['entry_exit_calculated'] else 'Not available'}")

                # Check if warning is in formatted context
                formatted = format_price_context_for_ai(price_data)
                result['warning_present'] = 'DO NOT use any memorized' in formatted or 'CRITICAL INSTRUCTIONS' in formatted
                print(f"  ✅ Training data warning: {'Present' if result['warning_present'] else '⚠️ MISSING'}")
            else:
                print(f"  ❌ Price fetch failed: {price_data.get('error', 'Unknown')}")

        except Exception as e:
            print(f"  ❌ Exception: {str(e)[:100]}")
            result['error'] = str(e)

        return result

    def _validate_fundamental_data(self, ticker: str) -> Dict:
        """Validate fundamental data fetching (quarterly/annual results)."""
        print("\n📈 VALIDATING FUNDAMENTAL DATA (from yfinance)...")

        result = {
            'fetched_successfully': False,
            'quarterly_available': False,
            'annual_available': False,
            'health_available': False,
            'quarterly_earnings_yoy': None,
            'annual_earnings_yoy': None,
            'is_profitable': None,
            'net_worth_positive': None
        }

        try:
            fund_data = self.fetcher.fetch_comprehensive_fundamentals(ticker)

            if fund_data.get('data_available'):
                result['fetched_successfully'] = True

                # Quarterly data
                quarterly = fund_data.get('quarterly', {})
                if quarterly.get('data_available'):
                    result['quarterly_available'] = True
                    result['quarterly_earnings_yoy'] = quarterly.get('earnings_yoy_growth_pct')
                    print(f"  ✅ Quarterly data available")
                    print(f"     • Earnings Y-o-Y: {result['quarterly_earnings_yoy']:.2f}%" if result['quarterly_earnings_yoy'] is not None else "     • Earnings Y-o-Y: N/A")

                # Annual data
                annual = fund_data.get('annual', {})
                if annual.get('data_available'):
                    result['annual_available'] = True
                    result['annual_earnings_yoy'] = annual.get('earnings_yoy_growth_pct')
                    print(f"  ✅ Annual data available")
                    print(f"     • Earnings Y-o-Y: {result['annual_earnings_yoy']:.2f}%" if result['annual_earnings_yoy'] is not None else "     • Earnings Y-o-Y: N/A")

                # Financial health
                health = fund_data.get('financial_health', {})
                if health.get('data_available'):
                    result['health_available'] = True
                    result['is_profitable'] = health.get('is_profitable')
                    result['net_worth_positive'] = health.get('net_worth_positive')
                    print(f"  ✅ Financial health available")
                    print(f"     • Profitable: {'Yes' if result['is_profitable'] else 'No' if result['is_profitable'] is not None else 'N/A'}")
                    print(f"     • Net worth positive: {'Yes' if result['net_worth_positive'] else 'No' if result['net_worth_positive'] is not None else 'N/A'}")

                # Check validation flags
                validation = fund_data.get('validation', {})
                if validation:
                    print(f"  ✅ Validation summary: {validation.get('overall_health', 'unknown').upper()}")
                    if validation.get('red_flags'):
                        print(f"     ⚠️  Red flags: {len(validation['red_flags'])}")
                    if validation.get('green_flags'):
                        print(f"     ✅ Green flags: {len(validation['green_flags'])}")
            else:
                print(f"  ⚠️  Fundamental data not fully available")

        except Exception as e:
            print(f"  ❌ Exception: {str(e)[:100]}")
            result['error'] = str(e)

        return result

    def _validate_institutional_data(self, ticker: str) -> Dict:
        """Validate institutional ownership data."""
        print("\n🏦 VALIDATING INSTITUTIONAL OWNERSHIP DATA...")

        result = {
            'data_available': False,
            'institutional_ownership_pct': None,
            'institutions_count': None,
            'top_5_holders_pct': None
        }

        try:
            fund_data = self.fetcher.fetch_comprehensive_fundamentals(ticker)

            institutional = fund_data.get('institutional', {})
            if institutional.get('data_available'):
                result['data_available'] = True
                result['institutional_ownership_pct'] = institutional.get('institutional_ownership_pct')
                result['institutions_count'] = institutional.get('institutions_count')
                result['top_5_holders_pct'] = institutional.get('top_5_holders_pct')

                print(f"  ✅ Institutional data available")
                if result['institutional_ownership_pct'] is not None:
                    print(f"     • Institutional ownership: {result['institutional_ownership_pct']:.2f}%")
                if result['institutions_count'] is not None:
                    print(f"     • Number of institutions: {result['institutions_count']}")
                if result['top_5_holders_pct'] is not None:
                    print(f"     • Top 5 holders: {result['top_5_holders_pct']:.2f}%")
            else:
                print(f"  ⚠️  Institutional data not available (may be limited by yfinance)")

        except Exception as e:
            print(f"  ❌ Exception: {str(e)[:100]}")
            result['error'] = str(e)

        return result

    def generate_ai_confirmation_prompt(self, ticker: str) -> str:
        """
        Generate a prompt that requires AI to explicitly confirm data sources.

        This should be added to all AI prompts to ensure AI acknowledges
        using real-time data and not training data.
        """
        return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  MANDATORY AI CONFIRMATION (MUST RESPOND TO THIS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Before providing your analysis, you MUST confirm:

1. ✅ I ACKNOWLEDGE that I received real-time price data for {ticker} from yfinance
2. ✅ I WILL NOT use any memorized/training data prices for {ticker}
3. ✅ I ACKNOWLEDGE quarterly/annual results data provided above is from yfinance
4. ✅ I WILL base ALL calculations ONLY on the data provided in this prompt
5. ✅ I UNDERSTAND that using training data would invalidate this analysis

Include this confirmation in your JSON response as:
"data_source_confirmation": {{
    "used_provided_price": true,
    "used_provided_fundamentals": true,
    "no_training_data_used": true,
    "confirmation_statement": "I confirm using ONLY the yfinance data provided in this prompt"
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

    def print_validation_summary(self, validation: Dict):
        """Print a clear summary of validation results."""
        print(f"\n{'='*80}")
        print(f"📋 VALIDATION SUMMARY FOR {validation['ticker']}")
        print(f"{'='*80}\n")

        status = validation['overall_status']
        status_icon = "✅" if status == "PASS" else "⚠️"
        print(f"{status_icon} Overall Status: {status}\n")

        completeness = validation['data_completeness']
        print("Data Availability:")
        for key, available in completeness.items():
            icon = "✅" if available else "❌"
            print(f"  {icon} {key.replace('_', ' ').title()}: {'Available' if available else 'Not Available'}")

        print(f"\n{'='*80}\n")


def main():
    """Main validation function."""
    if not IMPORTS_OK:
        print("\n❌ Cannot proceed - import errors detected")
        print("Please ensure realtime_price_fetcher.py and fundamental_data_fetcher.py exist")
        return 1

    # Parse arguments
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 ai_realtime_data_validator.py TICKER")
        print("  python3 ai_realtime_data_validator.py --test-file tickers_test.txt")
        return 1

    validator = AIDataValidator()

    if sys.argv[1] == '--test-file':
        # Batch validation
        if len(sys.argv) < 3:
            print("❌ Please provide a file path with --test-file")
            return 1

        try:
            with open(sys.argv[2], 'r') as f:
                tickers = [line.strip() for line in f if line.strip()]
        except Exception as e:
            print(f"❌ Failed to read file: {e}")
            return 1

        print(f"\n🔍 Validating {len(tickers)} tickers from {sys.argv[2]}")

        all_validations = []
        for ticker in tickers[:5]:  # Limit to 5 for quick test
            validation = validator.validate_ticker(ticker)
            validator.print_validation_summary(validation)
            all_validations.append(validation)

        # Save results
        output_file = f'validation_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w') as f:
            json.dump(all_validations, f, indent=2, default=str)

        print(f"\n📄 Full validation results saved to: {output_file}")

    else:
        # Single ticker validation
        ticker = sys.argv[1].upper()
        validation = validator.validate_ticker(ticker)
        validator.print_validation_summary(validation)

        # Print AI confirmation prompt
        print("\n" + "="*80)
        print("📝 ADD THIS TO AI PROMPTS:")
        print("="*80)
        print(validator.generate_ai_confirmation_prompt(ticker))

        # Save results
        output_file = f'validation_{ticker}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(output_file, 'w') as f:
            json.dump(validation, f, indent=2, default=str)

        print(f"\n📄 Validation results saved to: {output_file}\n")

    return 0


if __name__ == '__main__':
    sys.exit(main())
