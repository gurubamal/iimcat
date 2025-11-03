#!/usr/bin/env python3
"""
PATCH: Add AI Confirmation Validation to realtime_ai_news_analyzer.py

This patch adds explicit validation of the data_source_confirmation field
that AI must include in its response.
"""

import json
import logging

logger = logging.getLogger(__name__)


def validate_ai_confirmation(ai_analysis: dict, ticker: str) -> dict:
    """
    Validate that AI included data_source_confirmation and used real-time data.

    Returns validation result dict with:
      - is_valid: bool
      - warnings: list of warning messages
      - confirmation_data: the confirmation dict from AI (if present)
    """

    validation = {
        'is_valid': True,
        'warnings': [],
        'confirmation_data': None
    }

    # Check if confirmation field exists
    confirmation = ai_analysis.get('data_source_confirmation')

    if not confirmation:
        validation['is_valid'] = False
        validation['warnings'].append(
            f"⚠️  {ticker}: AI did not include data_source_confirmation field"
        )
        return validation

    validation['confirmation_data'] = confirmation

    # Check individual boolean fields
    used_price = confirmation.get('used_provided_price')
    used_fundamentals = confirmation.get('used_provided_fundamentals')
    no_training = confirmation.get('no_training_data_used')
    statement = confirmation.get('confirmation_statement')

    if used_price is not True:
        validation['warnings'].append(
            f"⚠️  {ticker}: AI did not confirm using provided price (value: {used_price})"
        )
        validation['is_valid'] = False

    if used_fundamentals is not True:
        validation['warnings'].append(
            f"⚠️  {ticker}: AI did not confirm using provided fundamentals (value: {used_fundamentals})"
        )
        validation['is_valid'] = False

    if no_training is not True:
        validation['warnings'].append(
            f"⚠️  {ticker}: AI did not confirm avoiding training data (value: {no_training})"
        )
        validation['is_valid'] = False

    if not statement or not isinstance(statement, str) or len(statement) < 10:
        validation['warnings'].append(
            f"⚠️  {ticker}: AI confirmation statement is missing or invalid"
        )
        validation['is_valid'] = False

    # Check if ticker is mentioned in statement
    if statement and ticker.upper() not in statement.upper():
        validation['warnings'].append(
            f"⚠️  {ticker}: AI confirmation statement doesn't mention ticker"
        )
        validation['is_valid'] = False

    # Log results
    if validation['is_valid']:
        logger.info(f"   ✅ {ticker}: AI confirmed using real-time data")
        logger.debug(f"      Confirmation: {statement[:80]}...")
    else:
        for warning in validation['warnings']:
            logger.warning(warning)

    return validation


def log_full_ai_response(ticker: str, ai_analysis: dict, save_to_file: bool = False):
    """
    Log the full AI response for debugging/verification purposes.

    Args:
        ticker: Stock ticker
        ai_analysis: Full AI response dict
        save_to_file: If True, save to logs/ai_response_<ticker>.json
    """

    logger.debug(f"\n{'='*80}")
    logger.debug(f"Full AI Response for {ticker}:")
    logger.debug(f"{'='*80}")
    logger.debug(json.dumps(ai_analysis, indent=2, default=str)[:500])
    logger.debug(f"{'='*80}\n")

    if save_to_file:
        import os
        from datetime import datetime

        os.makedirs('logs', exist_ok=True)
        filename = f"logs/ai_response_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        try:
            with open(filename, 'w') as f:
                json.dump(ai_analysis, f, indent=2, default=str)
            logger.info(f"   📝 Full AI response saved to: {filename}")
        except Exception as e:
            logger.warning(f"   ⚠️  Could not save AI response: {e}")


# Example usage (to be integrated into realtime_ai_news_analyzer.py):
"""
# After line 960 in realtime_ai_news_analyzer.py:
ai_analysis, data_bundle = self._call_copilot_ai(ticker, headline, full_text, url)

# Add these lines:
from validate_ai_confirmation_patch import validate_ai_confirmation, log_full_ai_response

# Log full response for debugging (optional - set DEBUG_AI_RESPONSES=1)
if os.getenv('DEBUG_AI_RESPONSES', '0') == '1':
    log_full_ai_response(ticker, ai_analysis, save_to_file=True)

# Validate confirmation
confirmation_result = validate_ai_confirmation(ai_analysis, ticker)
if not confirmation_result['is_valid']:
    # Warnings were already logged, but you can optionally fail here
    pass
"""


if __name__ == '__main__':
    # Test with sample AI responses

    print("Testing validation with GOOD response:")
    good_response = {
        'score': 75,
        'sentiment': 'bullish',
        'data_source_confirmation': {
            'used_provided_price': True,
            'used_provided_fundamentals': True,
            'no_training_data_used': True,
            'confirmation_statement': 'I confirm using ONLY yfinance data for RELIANCE'
        }
    }
    result = validate_ai_confirmation(good_response, 'RELIANCE')
    print(f"Valid: {result['is_valid']}")
    print(f"Warnings: {result['warnings']}")
    print()

    print("Testing validation with BAD response (missing confirmation):")
    bad_response = {
        'score': 75,
        'sentiment': 'bullish'
        # Missing data_source_confirmation
    }
    result = validate_ai_confirmation(bad_response, 'RELIANCE')
    print(f"Valid: {result['is_valid']}")
    print(f"Warnings: {result['warnings']}")
    print()

    print("Testing validation with PARTIAL response (false values):")
    partial_response = {
        'score': 75,
        'sentiment': 'bullish',
        'data_source_confirmation': {
            'used_provided_price': False,  # ❌
            'used_provided_fundamentals': True,
            'no_training_data_used': True,
            'confirmation_statement': 'I confirm...'
        }
    }
    result = validate_ai_confirmation(partial_response, 'RELIANCE')
    print(f"Valid: {result['is_valid']}")
    print(f"Warnings: {result['warnings']}")
