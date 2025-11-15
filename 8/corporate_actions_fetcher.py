#!/usr/bin/env python3
"""
CORPORATE ACTIONS FETCHER - Dividend & Bonus Catalyst Scoring
=============================================================
Fetches upcoming corporate actions (dividends, bonuses, splits) from NSE
and provides catalyst scoring for decision-making.

Key Features:
- Scrapes NSE website for corporate actions (polite, rate-limited)
- Identifies upcoming dividends (ex-dates in future)
- Identifies recent bonus issues (within last 6 months)
- Provides scoring: +5 points for dividends, +10 points for bonuses
- Smart caching (6-hour TTL)

Usage:
    from corporate_actions_fetcher import get_corporate_action_score

    result = get_corporate_action_score('RELIANCE')
    # Returns: {
    #   'catalyst_score': 15,  # +5 for dividend, +10 for bonus
    #   'has_upcoming_dividend': True,
    #   'dividend_amount': 10.0,
    #   'dividend_ex_date': '2025-08-19',
    #   'has_recent_bonus': True,
    #   'bonus_ratio': '1:1',
    #   'bonus_ex_date': '2024-10-28',
    #   'catalysts': ['Dividend ₹10', 'Bonus 1:1']
    # }
"""

import requests
from bs4 import BeautifulSoup
import json
import hashlib
import time
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Lock

# Cache directory
CACHE_DIR = Path('.scraper_cache')
CACHE_DIR.mkdir(exist_ok=True)
CACHE_TTL = 21600  # 6 hours (corporate actions don't change frequently)

# Rate limiter
class RateLimiter:
    def __init__(self, min_interval: float = 2.0):
        self.min_interval = min_interval
        self.last_request_time = {}
        self.lock = Lock()

    def wait(self, key: str = 'default'):
        with self.lock:
            elapsed = time.time() - self.last_request_time.get(key, 0)
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed + random.uniform(0, 0.5))
            self.last_request_time[key] = time.time()

_rate_limiter = RateLimiter(min_interval=2.0)

# User agents for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
]

def _get_cache_key(ticker: str) -> str:
    """Generate cache key for corporate actions"""
    return hashlib.md5(f"corporate_actions_{ticker}".encode()).hexdigest()

def _get_cached(ticker: str) -> Optional[Dict]:
    """Get cached corporate actions"""
    cache_file = CACHE_DIR / f"{_get_cache_key(ticker)}.json"
    if cache_file.exists():
        age = time.time() - cache_file.stat().st_mtime
        if age < CACHE_TTL:
            try:
                return json.loads(cache_file.read_text())
            except:
                pass
    return None

def _set_cache(ticker: str, data: Dict):
    """Cache corporate actions"""
    cache_file = CACHE_DIR / f"{_get_cache_key(ticker)}.json"
    cache_file.write_text(json.dumps(data, indent=2))

def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse date string to datetime"""
    if not date_str or date_str.strip() == '-':
        return None

    try:
        # Try different date formats
        for fmt in ['%d-%b-%Y', '%d/%m/%Y', '%Y-%m-%d']:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
    except:
        pass

    return None

def _scrape_nse_corporate_actions(ticker: str) -> Dict:
    """Scrape corporate actions from NSE website"""

    result = {
        'ticker': ticker,
        'fetch_time': datetime.now().isoformat(),
        'dividends': [],
        'bonuses': [],
        'splits': [],
        'data_available': False
    }

    # NSE requires session with cookies
    session = requests.Session()
    session.headers.update({
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    try:
        # Get homepage first to set cookies
        _rate_limiter.wait('nseindia.com')
        session.get('https://www.nseindia.com', timeout=10)
        time.sleep(1)  # Wait for cookies

        # Get corporate actions
        url = f"https://www.nseindia.com/api/corporates-corporateActions?index=equities&symbol={ticker}"
        _rate_limiter.wait('nseindia.com')
        response = session.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # Handle both list and dict responses
            actions_list = data if isinstance(data, list) else data.get('data', [])

            # Parse corporate actions
            for action in actions_list:
                subject = action.get('subject', '').lower()
                ex_date_str = action.get('exDate', '')

                # Parse ex-date
                ex_date = _parse_date(ex_date_str)

                # Dividend
                if 'dividend' in subject:
                    # Extract amount
                    amount = None
                    if 'rs' in subject or '₹' in subject:
                        import re
                        match = re.search(r'(?:rs|₹)\s*(\d+(?:\.\d+)?)', subject, re.IGNORECASE)
                        if match:
                            amount = float(match.group(1))

                    result['dividends'].append({
                        'description': action.get('subject', ''),
                        'ex_date': ex_date_str,
                        'ex_date_parsed': ex_date.isoformat() if ex_date else None,
                        'amount': amount
                    })

                # Bonus
                elif 'bonus' in subject:
                    # Extract ratio
                    ratio = None
                    import re
                    match = re.search(r'(\d+)\s*:\s*(\d+)', subject)
                    if match:
                        ratio = f"{match.group(1)}:{match.group(2)}"

                    result['bonuses'].append({
                        'description': action.get('subject', ''),
                        'ex_date': ex_date_str,
                        'ex_date_parsed': ex_date.isoformat() if ex_date else None,
                        'ratio': ratio
                    })

                # Split
                elif 'split' in subject:
                    result['splits'].append({
                        'description': action.get('subject', ''),
                        'ex_date': ex_date_str,
                        'ex_date_parsed': ex_date.isoformat() if ex_date else None
                    })

            result['data_available'] = True

    except Exception as e:
        print(f"  Warning: Failed to fetch corporate actions for {ticker}: {e}")
        result['error'] = str(e)

    return result

def get_corporate_actions(ticker: str) -> Dict:
    """
    Get corporate actions for a ticker (cached)

    Returns:
        Dict with dividends, bonuses, splits
    """
    # Check cache first
    cached = _get_cached(ticker)
    if cached:
        return cached

    # Fetch from NSE
    data = _scrape_nse_corporate_actions(ticker)

    # Cache result
    if data['data_available']:
        _set_cache(ticker, data)

    return data

def get_corporate_action_score(ticker: str) -> Dict:
    """
    Calculate catalyst score based on corporate actions

    Scoring:
    - Recent dividend (within 6 months): +5 points
    - Recent bonus (within 12 months): +10 points
    - Recent split (within 12 months): +3 points

    Returns:
        Dict with:
        - catalyst_score: int (0-18 max)
        - has_recent_dividend: bool
        - dividend_amount: float or None
        - dividend_ex_date: str or None
        - has_recent_bonus: bool
        - bonus_ratio: str or None
        - bonus_ex_date: str or None
        - has_recent_split: bool
        - catalysts: List[str] (human-readable)
    """

    result = {
        'catalyst_score': 0,
        'has_recent_dividend': False,
        'dividend_amount': None,
        'dividend_ex_date': None,
        'has_recent_bonus': False,
        'bonus_ratio': None,
        'bonus_ex_date': None,
        'has_recent_split': False,
        'split_ratio': None,
        'split_ex_date': None,
        'catalysts': [],
        'data_available': False
    }

    # Get corporate actions
    data = get_corporate_actions(ticker)

    if not data['data_available']:
        return result

    result['data_available'] = True
    now = datetime.now()
    six_months_ago = now - timedelta(days=180)
    twelve_months_ago = now - timedelta(days=365)

    # Check dividends (recent = within 6 months)
    for dividend in data['dividends']:
        ex_date = dividend['ex_date_parsed']
        if ex_date:
            ex_datetime = datetime.fromisoformat(ex_date)

            # Recent dividend (within 6 months)
            if ex_datetime > six_months_ago:
                result['catalyst_score'] += 5
                result['has_recent_dividend'] = True
                result['dividend_amount'] = dividend['amount']
                result['dividend_ex_date'] = dividend['ex_date']

                # Add to catalysts list
                if dividend['amount']:
                    result['catalysts'].append(f"Dividend ₹{dividend['amount']}")
                else:
                    result['catalysts'].append("Dividend announced")
                break  # Only count most recent dividend

    # Check bonuses (recent = within 12 months)
    for bonus in data['bonuses']:
        ex_date = bonus['ex_date_parsed']
        if ex_date:
            ex_datetime = datetime.fromisoformat(ex_date)

            # Recent bonus (within 12 months)
            if ex_datetime > twelve_months_ago:
                result['catalyst_score'] += 10
                result['has_recent_bonus'] = True
                result['bonus_ratio'] = bonus['ratio']
                result['bonus_ex_date'] = bonus['ex_date']

                # Add to catalysts list
                if bonus['ratio']:
                    result['catalysts'].append(f"Bonus {bonus['ratio']}")
                else:
                    result['catalysts'].append("Bonus issue")
                break  # Only count most recent bonus

    # Check splits (recent = within 12 months)
    for split in data['splits']:
        ex_date = split['ex_date_parsed']
        if ex_date:
            ex_datetime = datetime.fromisoformat(ex_date)

            # Recent split (within 12 months)
            if ex_datetime > twelve_months_ago:
                result['catalyst_score'] += 3
                result['has_recent_split'] = True
                result['split_ex_date'] = split['ex_date']

                result['catalysts'].append("Stock split")
                break  # Only count most recent split

    return result

def format_catalyst_summary(score_data: Dict) -> str:
    """
    Format catalyst data for display

    Returns:
        Human-readable string like "Dividend ₹10 (+5), Bonus 1:1 (+10)"
    """
    if not score_data.get('catalysts'):
        return "None"

    parts = []

    if score_data['has_recent_dividend']:
        if score_data['dividend_amount']:
            parts.append(f"Dividend ₹{score_data['dividend_amount']} (+5)")
        else:
            parts.append("Dividend (+5)")

    if score_data['has_recent_bonus']:
        if score_data['bonus_ratio']:
            parts.append(f"Bonus {score_data['bonus_ratio']} (+10)")
        else:
            parts.append("Bonus (+10)")

    if score_data['has_recent_split']:
        parts.append("Split (+3)")

    return ", ".join(parts) if parts else "None"


# Quick test
if __name__ == '__main__':
    print("="*80)
    print("CORPORATE ACTIONS CATALYST SCORING TEST")
    print("="*80)
    print()

    tickers = ['RELIANCE', 'TRENT', 'INFY']

    for ticker in tickers:
        print(f"Testing: {ticker}")
        print("-" * 80)

        # Get corporate actions
        actions = get_corporate_actions(ticker)

        if actions['data_available']:
            print(f"  ✅ Corporate actions found")
            print(f"     Dividends: {len(actions['dividends'])}")
            print(f"     Bonuses: {len(actions['bonuses'])}")
            print(f"     Splits: {len(actions['splits'])}")

            # Get catalyst score
            score = get_corporate_action_score(ticker)
            print()
            print(f"  📊 CATALYST SCORING:")
            print(f"     Total Score: +{score['catalyst_score']} points")
            print(f"     Recent Dividend (6mo): {'Yes' if score['has_recent_dividend'] else 'No'}")
            if score['has_recent_dividend']:
                print(f"       Amount: ₹{score['dividend_amount']}")
                print(f"       Ex-Date: {score['dividend_ex_date']}")
            print(f"     Recent Bonus (12mo): {'Yes' if score['has_recent_bonus'] else 'No'}")
            if score['has_recent_bonus']:
                print(f"       Ratio: {score['bonus_ratio']}")
                print(f"       Ex-Date: {score['bonus_ex_date']}")
            print(f"     Recent Split (12mo): {'Yes' if score['has_recent_split'] else 'No'}")
            print()
            print(f"  📋 Catalysts: {format_catalyst_summary(score)}")
        else:
            print(f"  ⚠️  No corporate actions data available")

        print()

    print("="*80)
    print("TEST COMPLETE")
    print("="*80)
    print()
    print("Scoring Summary:")
    print("  - Recent Dividend (6 months): +5 points")
    print("  - Recent Bonus (12 months): +10 points")
    print("  - Recent Split (12 months): +3 points")
    print("  - Maximum catalyst score: +18 points")
