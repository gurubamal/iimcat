#!/usr/bin/env python3
"""
YFINANCE DATA VALIDATOR
=======================
Comprehensive validation of yfinance data to ensure:
1. Data is fetched correctly
2. Data is legitimate and current
3. All fields are populated
4. Calculations are accurate
5. Timestamps are recent

Usage:
    python3 validate_yfinance_data.py RELIANCE
    python3 validate_yfinance_data.py TCS
"""

import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json

try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    DEPENDENCIES_OK = True
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install: pip3 install yfinance pandas numpy")
    DEPENDENCIES_OK = False
    sys.exit(1)


class YFinanceValidator:
    """Validate yfinance data for a ticker."""

    def __init__(self, ticker: str):
        self.ticker = ticker.upper().replace('.NS', '')
        self.symbol_ns = f"{self.ticker}.NS"
        self.symbol_bo = f"{self.ticker}.BO"
        self.validation_time = datetime.now()
        self.issues = []
        self.warnings = []
        self.data = {}

    def run_full_validation(self) -> Dict:
        """Run complete validation suite."""

        print("=" * 80)
        print(f"🔍 YFINANCE DATA VALIDATION: {self.ticker}")
        print("=" * 80)
        print(f"Validation Time: {self.validation_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Step 1: Fetch ticker object
        print("📥 STEP 1: Fetching Ticker Object...")
        ticker_obj = self._fetch_ticker()
        if not ticker_obj:
            return self._validation_failed("Could not fetch ticker object")

        # Step 2: Fetch fast_info (current price)
        print("\n📊 STEP 2: Fetching Fast Info (Current Price)...")
        fast_info = self._validate_fast_info(ticker_obj)

        # Step 3: Fetch historical data
        print("\n📈 STEP 3: Fetching Historical Data (6 months)...")
        hist_data = self._validate_historical_data(ticker_obj)

        # Step 4: Validate price data
        print("\n💰 STEP 4: Validating Price Data...")
        price_data = self._validate_price_data(fast_info, hist_data)

        # Step 5: Calculate and validate technical indicators
        print("\n📉 STEP 5: Calculating Technical Indicators...")
        technical_data = self._validate_technical_indicators(hist_data)

        # Step 6: Fetch and validate info (fundamentals)
        print("\n📋 STEP 6: Fetching Company Info...")
        info_data = self._validate_info(ticker_obj)

        # Step 7: Cross-validate data consistency
        print("\n✅ STEP 7: Cross-Validating Data Consistency...")
        self._cross_validate(price_data, technical_data, hist_data)

        # Step 8: Generate report
        print("\n" + "=" * 80)
        print("📊 VALIDATION REPORT")
        print("=" * 80)

        return self._generate_report(price_data, technical_data, info_data, hist_data)

    def _fetch_ticker(self) -> yf.Ticker:
        """Fetch ticker object with fallback."""

        # Try NSE first
        try:
            ticker = yf.Ticker(self.symbol_ns)
            # Test if it works by accessing info
            _ = ticker.fast_info
            print(f"✅ Ticker object created: {self.symbol_ns}")
            return ticker
        except Exception as e:
            self.warnings.append(f"NSE symbol failed: {e}")
            print(f"⚠️  NSE ({self.symbol_ns}) failed, trying BSE...")

        # Try BSE
        try:
            ticker = yf.Ticker(self.symbol_bo)
            _ = ticker.fast_info
            print(f"✅ Ticker object created: {self.symbol_bo}")
            return ticker
        except Exception as e:
            self.issues.append(f"Both NSE and BSE failed: {e}")
            print(f"❌ Both exchanges failed!")
            return None

    def _validate_fast_info(self, ticker: yf.Ticker) -> Dict:
        """Validate fast_info (real-time price data)."""

        try:
            fast_info = ticker.fast_info

            # Check available fields
            price_fields = {}

            # Last price
            try:
                last_price = fast_info.get('lastPrice') or fast_info.get('regularMarketPrice')
                if last_price and last_price > 0:
                    price_fields['last_price'] = float(last_price)
                    print(f"   Last Price: ₹{last_price:,.2f}")
                else:
                    self.warnings.append("Last price not available in fast_info")
            except Exception as e:
                self.warnings.append(f"Could not get last price: {e}")

            # Previous close
            try:
                prev_close = fast_info.get('previousClose')
                if prev_close and prev_close > 0:
                    price_fields['previous_close'] = float(prev_close)
                    print(f"   Previous Close: ₹{prev_close:,.2f}")
            except Exception as e:
                self.warnings.append(f"Could not get previous close: {e}")

            # Day range
            try:
                day_high = fast_info.get('dayHigh')
                day_low = fast_info.get('dayLow')
                if day_high and day_low:
                    price_fields['day_high'] = float(day_high)
                    price_fields['day_low'] = float(day_low)
                    print(f"   Day Range: ₹{day_low:,.2f} - ₹{day_high:,.2f}")
            except Exception as e:
                self.warnings.append(f"Could not get day range: {e}")

            # Market cap
            try:
                market_cap = fast_info.get('marketCap')
                if market_cap:
                    price_fields['market_cap'] = market_cap
                    print(f"   Market Cap: ₹{market_cap:,.0f}")
            except Exception as e:
                self.warnings.append(f"Could not get market cap: {e}")

            if not price_fields:
                self.issues.append("No price data available from fast_info")
                print("   ❌ No price data available")
            else:
                print(f"   ✅ {len(price_fields)} price fields fetched")

            return price_fields

        except Exception as e:
            self.issues.append(f"fast_info failed: {e}")
            print(f"   ❌ fast_info failed: {e}")
            return {}

    def _validate_historical_data(self, ticker: yf.Ticker) -> pd.DataFrame:
        """Validate historical data fetch."""

        try:
            # Fetch 6 months of data
            hist = ticker.history(period='6mo')

            if hist is None or hist.empty:
                self.issues.append("Historical data is empty")
                print("   ❌ No historical data")
                return pd.DataFrame()

            print(f"   ✅ Fetched {len(hist)} days of data")
            print(f"   Date Range: {hist.index[0].date()} to {hist.index[-1].date()}")

            # Check how recent the data is
            last_date = hist.index[-1]
            # Handle timezone-aware datetimes
            if hasattr(last_date, 'tz') and last_date.tz is not None:
                last_date_naive = last_date.replace(tzinfo=None)
            else:
                last_date_naive = last_date
            days_old = (datetime.now() - last_date_naive).days

            if days_old > 5:
                self.warnings.append(f"Data is {days_old} days old (last: {last_date.date()})")
                print(f"   ⚠️  Data is {days_old} days old")
            else:
                print(f"   ✅ Data is recent ({days_old} days old)")

            # Check columns
            expected_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
            missing_cols = [col for col in expected_cols if col not in hist.columns]

            if missing_cols:
                self.issues.append(f"Missing columns: {missing_cols}")
                print(f"   ❌ Missing columns: {missing_cols}")
            else:
                print(f"   ✅ All expected columns present")

            # Check for data quality
            null_counts = hist[expected_cols].isnull().sum()
            if null_counts.any():
                self.warnings.append(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
                print(f"   ⚠️  Null values: {null_counts[null_counts > 0].to_dict()}")

            return hist

        except Exception as e:
            self.issues.append(f"Historical data fetch failed: {e}")
            print(f"   ❌ Failed: {e}")
            return pd.DataFrame()

    def _validate_price_data(self, fast_info: Dict, hist: pd.DataFrame) -> Dict:
        """Validate and combine price data."""

        price_data = {}

        # Current price (prefer fast_info, fallback to history)
        if 'last_price' in fast_info:
            price_data['current'] = fast_info['last_price']
            price_data['source'] = 'fast_info'
            print(f"   ✅ Current Price: ₹{price_data['current']:,.2f} (from fast_info)")
        elif not hist.empty:
            price_data['current'] = float(hist['Close'].iloc[-1])
            price_data['source'] = 'history'
            print(f"   ⚠️  Current Price: ₹{price_data['current']:,.2f} (from history)")
        else:
            self.issues.append("No current price available")
            print("   ❌ No current price available")
            return {}

        # Previous close
        if 'previous_close' in fast_info:
            price_data['previous_close'] = fast_info['previous_close']
        elif not hist.empty and len(hist) > 1:
            price_data['previous_close'] = float(hist['Close'].iloc[-2])

        # Day range
        if 'day_high' in fast_info:
            price_data['day_high'] = fast_info['day_high']
            price_data['day_low'] = fast_info['day_low']
        elif not hist.empty:
            price_data['day_high'] = float(hist['High'].iloc[-1])
            price_data['day_low'] = float(hist['Low'].iloc[-1])

        # Calculate change
        if 'previous_close' in price_data and price_data['previous_close'] > 0:
            change = price_data['current'] - price_data['previous_close']
            change_pct = (change / price_data['previous_close']) * 100
            price_data['change'] = change
            price_data['change_pct'] = change_pct
            print(f"   Change: ₹{change:+,.2f} ({change_pct:+.2f}%)")

        price_data['timestamp'] = datetime.now().isoformat()

        return price_data

    def _validate_technical_indicators(self, hist: pd.DataFrame) -> Dict:
        """Calculate and validate technical indicators."""

        if hist.empty:
            print("   ⚠️  No historical data for indicators")
            return {}

        tech = {}

        try:
            # Current price
            current_price = float(hist['Close'].iloc[-1])
            tech['current_price'] = current_price

            # RSI (14-period)
            if len(hist) >= 14:
                delta = hist['Close'].diff()
                gain = delta.where(delta > 0, 0).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                tech['rsi_14'] = float(rsi.iloc[-1])
                print(f"   RSI(14): {tech['rsi_14']:.2f}")

                # Validate RSI is in valid range
                if not (0 <= tech['rsi_14'] <= 100):
                    self.issues.append(f"Invalid RSI value: {tech['rsi_14']}")
            else:
                self.warnings.append("Not enough data for RSI (need 14+ days)")

            # Moving Averages
            if len(hist) >= 20:
                sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
                tech['sma_20'] = float(sma_20)
                tech['price_vs_sma20_pct'] = ((current_price - sma_20) / sma_20) * 100
                print(f"   SMA(20): ₹{tech['sma_20']:,.2f} ({tech['price_vs_sma20_pct']:+.2f}%)")

            if len(hist) >= 50:
                sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
                tech['sma_50'] = float(sma_50)
                tech['price_vs_sma50_pct'] = ((current_price - sma_50) / sma_50) * 100
                print(f"   SMA(50): ₹{tech['sma_50']:,.2f} ({tech['price_vs_sma50_pct']:+.2f}%)")

            # Volume analysis
            if 'Volume' in hist.columns and len(hist) >= 20:
                current_vol = hist['Volume'].iloc[-1]
                avg_vol_20 = hist['Volume'].rolling(window=20).mean().iloc[-1]
                tech['volume_current'] = int(current_vol)
                tech['volume_avg_20d'] = int(avg_vol_20)
                tech['volume_ratio'] = float(current_vol / avg_vol_20) if avg_vol_20 > 0 else 0
                print(f"   Volume: {current_vol:,.0f} (Avg: {avg_vol_20:,.0f}, Ratio: {tech['volume_ratio']:.2f}x)")

            # Momentum
            if len(hist) >= 10:
                price_10d_ago = hist['Close'].iloc[-10]
                momentum_10d_pct = ((current_price - price_10d_ago) / price_10d_ago) * 100
                tech['momentum_10d_pct'] = float(momentum_10d_pct)
                print(f"   10-day Momentum: {tech['momentum_10d_pct']:+.2f}%")

            # 52-week high/low
            if len(hist) >= 252:
                week_52_high = hist['Close'].iloc[-252:].max()
                week_52_low = hist['Close'].iloc[-252:].min()
                tech['week_52_high'] = float(week_52_high)
                tech['week_52_low'] = float(week_52_low)
                tech['distance_from_52w_high_pct'] = ((current_price - week_52_high) / week_52_high) * 100
                tech['distance_from_52w_low_pct'] = ((current_price - week_52_low) / week_52_low) * 100
                print(f"   52W Range: ₹{week_52_low:,.2f} - ₹{week_52_high:,.2f}")

            print(f"   ✅ {len(tech)} technical indicators calculated")

        except Exception as e:
            self.issues.append(f"Technical indicator calculation failed: {e}")
            print(f"   ❌ Calculation failed: {e}")

        return tech

    def _validate_info(self, ticker: yf.Ticker) -> Dict:
        """Validate company info/fundamentals."""

        try:
            info = ticker.info

            if not info:
                self.warnings.append("Company info not available")
                print("   ⚠️  Info not available")
                return {}

            info_data = {}

            # Basic info
            fields_to_check = [
                ('longName', 'Company Name'),
                ('sector', 'Sector'),
                ('industry', 'Industry'),
                ('marketCap', 'Market Cap'),
                ('trailingPE', 'P/E Ratio'),
                ('dividendYield', 'Dividend Yield'),
            ]

            for field, label in fields_to_check:
                if field in info and info[field]:
                    info_data[field] = info[field]
                    value = info[field]
                    if isinstance(value, (int, float)) and field == 'marketCap':
                        print(f"   {label}: ₹{value:,.0f}")
                    elif isinstance(value, float) and field in ['trailingPE', 'dividendYield']:
                        print(f"   {label}: {value:.2f}")
                    else:
                        print(f"   {label}: {value}")

            if info_data:
                print(f"   ✅ {len(info_data)} info fields fetched")
            else:
                self.warnings.append("No company info fields available")

            return info_data

        except Exception as e:
            self.warnings.append(f"Info fetch failed: {e}")
            print(f"   ⚠️  Info fetch failed: {e}")
            return {}

    def _cross_validate(self, price_data: Dict, tech: Dict, hist: pd.DataFrame):
        """Cross-validate data for consistency."""

        issues_found = 0

        # Check price consistency
        if 'current' in price_data and 'current_price' in tech:
            if abs(price_data['current'] - tech['current_price']) > 0.01:
                self.issues.append(
                    f"Price mismatch: price_data={price_data['current']}, tech={tech['current_price']}"
                )
                issues_found += 1

        # Check if current price is within day range
        if all(k in price_data for k in ['current', 'day_low', 'day_high']):
            if not (price_data['day_low'] <= price_data['current'] <= price_data['day_high']):
                self.warnings.append(
                    f"Current price (₹{price_data['current']}) outside day range "
                    f"(₹{price_data['day_low']} - ₹{price_data['day_high']})"
                )
                issues_found += 1

        # Check volume is positive
        if 'volume_current' in tech and tech['volume_current'] <= 0:
            self.warnings.append("Volume is zero or negative")
            issues_found += 1

        if issues_found == 0:
            print("   ✅ All cross-validation checks passed")
        else:
            print(f"   ⚠️  {issues_found} consistency issues found")

    def _generate_report(self, price_data: Dict, tech: Dict, info: Dict, hist: pd.DataFrame) -> Dict:
        """Generate validation report."""

        report = {
            'ticker': self.ticker,
            'validation_time': self.validation_time.isoformat(),
            'status': 'PASS' if not self.issues else 'FAIL',
            'issues_count': len(self.issues),
            'warnings_count': len(self.warnings),
            'issues': self.issues,
            'warnings': self.warnings,
            'data': {
                'price': price_data,
                'technical': tech,
                'info': info,
                'historical_data_points': len(hist) if not hist.empty else 0,
            }
        }

        # Print summary
        print()
        if report['status'] == 'PASS':
            print("✅ VALIDATION: PASSED")
        else:
            print("❌ VALIDATION: FAILED")

        print(f"   Issues: {report['issues_count']}")
        print(f"   Warnings: {report['warnings_count']}")

        if self.issues:
            print("\n❌ ISSUES:")
            for issue in self.issues:
                print(f"   - {issue}")

        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   - {warning}")

        # Data completeness score
        total_fields = len(price_data) + len(tech) + len(info)
        print(f"\n📊 DATA COMPLETENESS: {total_fields} fields fetched")

        if hist is not None and not hist.empty:
            print(f"   Historical Data: {len(hist)} days")
            print(f"   Latest Data: {hist.index[-1].date()}")

        return report

    def _validation_failed(self, reason: str) -> Dict:
        """Return failed validation report."""
        return {
            'ticker': self.ticker,
            'status': 'FAIL',
            'reason': reason,
            'issues': self.issues,
            'warnings': self.warnings
        }


def main():
    """Main validation function."""

    if len(sys.argv) < 2:
        print("Usage: python3 validate_yfinance_data.py <TICKER>")
        print("Example: python3 validate_yfinance_data.py RELIANCE")
        sys.exit(1)

    ticker = sys.argv[1]

    validator = YFinanceValidator(ticker)
    report = validator.run_full_validation()

    # Save report
    report_file = f"yfinance_validation_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    print("\n" + "=" * 80)
    print(f"💾 Saving report to: {report_file}")

    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"✅ Report saved!")
    print("=" * 80)

    # Return exit code based on validation status
    sys.exit(0 if report['status'] == 'PASS' else 1)


if __name__ == '__main__':
    main()
