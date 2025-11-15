#!/usr/bin/env python3
"""
DEEP VALIDATION CHECK - Independent Data Verification
======================================================
Investigates data deviations and validates legitimacy with multiple cross-checks.
"""

import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json
import sys

def deep_validate_ticker(ticker: str) -> dict:
    """
    Performs deep validation with multiple independent checks.
    """

    print(f"\n{'='*80}")
    print(f"DEEP VALIDATION: {ticker}")
    print(f"{'='*80}\n")

    result = {
        'ticker': ticker,
        'validation_time': datetime.now().isoformat(),
        'checks': {},
        'issues': [],
        'corrections': []
    }

    try:
        ticker_obj = yf.Ticker(f"{ticker}.NS")

        # ================================================================
        # CHECK 1: Price History Trend (1 year)
        # ================================================================
        print("📊 CHECK 1: Price History Trend (1 Year)")
        print("-" * 80)

        hist_1y = ticker_obj.history(period='1y')

        if not hist_1y.empty:
            current_price = ticker_obj.fast_info.get('lastPrice', hist_1y['Close'].iloc[-1])

            # Get key historical prices
            price_1m_ago = hist_1y['Close'].iloc[-22] if len(hist_1y) >= 22 else None
            price_3m_ago = hist_1y['Close'].iloc[-66] if len(hist_1y) >= 66 else None
            price_6m_ago = hist_1y['Close'].iloc[-132] if len(hist_1y) >= 132 else None
            price_1y_ago = hist_1y['Close'].iloc[0]

            year_high = hist_1y['High'].max()
            year_low = hist_1y['Low'].min()

            trend_data = {
                'current_price': float(current_price),
                'price_1m_ago': float(price_1m_ago) if price_1m_ago is not None else None,
                'price_3m_ago': float(price_3m_ago) if price_3m_ago is not None else None,
                'price_6m_ago': float(price_6m_ago) if price_6m_ago is not None else None,
                'price_1y_ago': float(price_1y_ago),
                '52w_high': float(year_high),
                '52w_low': float(year_low),
                'change_1m_pct': ((current_price - price_1m_ago) / price_1m_ago * 100) if price_1m_ago else None,
                'change_3m_pct': ((current_price - price_3m_ago) / price_3m_ago * 100) if price_3m_ago else None,
                'change_6m_pct': ((current_price - price_6m_ago) / price_6m_ago * 100) if price_6m_ago else None,
                'change_1y_pct': ((current_price - price_1y_ago) / price_1y_ago * 100),
                'position_in_52w_range_pct': ((current_price - year_low) / (year_high - year_low) * 100)
            }

            result['checks']['price_trend'] = trend_data

            print(f"  Current Price:      ₹{current_price:,.2f}")
            print(f"  52-Week High:       ₹{year_high:,.2f}")
            print(f"  52-Week Low:        ₹{year_low:,.2f}")
            print(f"  Position in Range:  {trend_data['position_in_52w_range_pct']:.1f}%")
            print(f"\n  Price Changes:")
            if trend_data['change_1m_pct']:
                print(f"    1 Month:  {trend_data['change_1m_pct']:+.2f}%")
            if trend_data['change_3m_pct']:
                print(f"    3 Months: {trend_data['change_3m_pct']:+.2f}%")
            if trend_data['change_6m_pct']:
                print(f"    6 Months: {trend_data['change_6m_pct']:+.2f}%")
            print(f"    1 Year:   {trend_data['change_1y_pct']:+.2f}%")

            # Check for major drops (possible split indicator)
            if trend_data['change_1m_pct'] and trend_data['change_1m_pct'] < -40:
                result['issues'].append({
                    'type': 'sudden_price_drop',
                    'severity': 'high',
                    'description': f"Price dropped {trend_data['change_1m_pct']:.1f}% in 1 month - possible split/adjustment",
                    'current_price': current_price,
                    'previous_price': price_1m_ago
                })
                print(f"\n  ⚠️  ALERT: Major 1-month drop detected ({trend_data['change_1m_pct']:.1f}%)")

        # ================================================================
        # CHECK 2: Corporate Actions (Splits, Bonuses, Dividends)
        # ================================================================
        print(f"\n📋 CHECK 2: Corporate Actions")
        print("-" * 80)

        # Check for splits
        actions = ticker_obj.actions
        if not actions.empty:
            # Handle timezone-aware index
            cutoff_date = datetime.now() - timedelta(days=365)
            if hasattr(actions.index, 'tz') and actions.index.tz is not None:
                # Make cutoff_date timezone-aware to match the index
                import pytz
                cutoff_date = pytz.UTC.localize(cutoff_date)
            recent_actions = actions[actions.index > cutoff_date]

            splits = recent_actions[recent_actions['Stock Splits'] != 0]
            dividends = recent_actions[recent_actions['Dividends'] != 0]

            if not splits.empty:
                print(f"  Stock Splits Found: {len(splits)}")
                for date, row in splits.iterrows():
                    split_ratio = row['Stock Splits']
                    print(f"    - {date.strftime('%Y-%m-%d')}: {split_ratio}:1 split")
                    result['checks']['stock_splits'] = {
                        'count': len(splits),
                        'latest_date': splits.index[-1].strftime('%Y-%m-%d'),
                        'latest_ratio': float(splits['Stock Splits'].iloc[-1])
                    }

                    # This explains price differences!
                    result['corrections'].append({
                        'type': 'stock_split_adjustment',
                        'date': splits.index[-1].strftime('%Y-%m-%d'),
                        'ratio': float(split_ratio),
                        'explanation': f"Stock split {split_ratio}:1 adjusts historical prices"
                    })
            else:
                print(f"  No stock splits in past year")
                result['checks']['stock_splits'] = {'count': 0}

            if not dividends.empty:
                total_dividend = dividends['Dividends'].sum()
                print(f"  Dividends Found: {len(dividends)} payments, Total: ₹{total_dividend:.2f}")
                result['checks']['dividends'] = {
                    'count': len(dividends),
                    'total_amount': float(total_dividend)
                }
            else:
                print(f"  No dividends in past year")
        else:
            print(f"  No corporate actions data available")

        # ================================================================
        # CHECK 3: Volume Validation (Detect Unusual Activity)
        # ================================================================
        print(f"\n📈 CHECK 3: Volume Validation")
        print("-" * 80)

        if not hist_1y.empty:
            avg_volume_3m = hist_1y['Volume'].tail(66).mean()
            avg_volume_1y = hist_1y['Volume'].mean()
            current_volume = hist_1y['Volume'].iloc[-1]
            max_volume_1y = hist_1y['Volume'].max()

            volume_data = {
                'current_volume': int(current_volume),
                'avg_volume_3m': int(avg_volume_3m),
                'avg_volume_1y': int(avg_volume_1y),
                'max_volume_1y': int(max_volume_1y),
                'current_vs_avg_3m': float(current_volume / avg_volume_3m) if avg_volume_3m > 0 else 0
            }

            result['checks']['volume'] = volume_data

            print(f"  Current Volume:     {current_volume:,}")
            print(f"  3-Month Avg:        {avg_volume_3m:,.0f}")
            print(f"  1-Year Avg:         {avg_volume_1y:,.0f}")
            print(f"  Current vs 3M Avg:  {volume_data['current_vs_avg_3m']:.2f}x")

            if volume_data['current_vs_avg_3m'] > 3:
                result['issues'].append({
                    'type': 'unusual_volume',
                    'severity': 'medium',
                    'description': f"Volume {volume_data['current_vs_avg_3m']:.1f}x above 3-month average"
                })
                print(f"\n  ⚠️  ALERT: Unusual high volume detected")

        # ================================================================
        # CHECK 4: Market Cap Consistency (Independent Validation)
        # ================================================================
        print(f"\n💰 CHECK 4: Market Cap Consistency")
        print("-" * 80)

        fast_info = ticker_obj.fast_info
        market_cap_fast = fast_info.get('marketCap', 0)
        shares_outstanding = fast_info.get('sharesOutstanding', 0)

        info = ticker_obj.info
        market_cap_info = info.get('marketCap', 0)
        shares_info = info.get('sharesOutstanding', 0)

        # Calculate market cap independently
        current_price = fast_info.get('lastPrice', 0)
        if shares_outstanding > 0 and current_price > 0:
            calculated_market_cap = current_price * shares_outstanding
        else:
            calculated_market_cap = 0

        market_cap_data = {
            'market_cap_fast_info': market_cap_fast,
            'market_cap_info': market_cap_info,
            'calculated_market_cap': calculated_market_cap,
            'shares_outstanding_fast': shares_outstanding,
            'shares_outstanding_info': shares_info,
            'current_price': current_price
        }

        result['checks']['market_cap'] = market_cap_data

        print(f"  Market Cap (fast_info): ₹{market_cap_fast / 10000000:,.0f} crore")
        print(f"  Market Cap (info):      ₹{market_cap_info / 10000000:,.0f} crore")
        print(f"  Calculated Market Cap:  ₹{calculated_market_cap / 10000000:,.0f} crore")
        print(f"  Shares Outstanding:     {shares_outstanding / 10000000:,.2f} crore")

        # Check consistency
        if market_cap_fast > 0 and calculated_market_cap > 0:
            deviation_pct = abs(market_cap_fast - calculated_market_cap) / market_cap_fast * 100
            if deviation_pct > 5:
                result['issues'].append({
                    'type': 'market_cap_inconsistency',
                    'severity': 'high',
                    'description': f"Market cap values deviate by {deviation_pct:.1f}%",
                    'deviation_pct': deviation_pct
                })
                print(f"\n  ⚠️  ALERT: Market cap inconsistency detected ({deviation_pct:.1f}% deviation)")
            else:
                print(f"  ✅ Market cap consistent (deviation: {deviation_pct:.2f}%)")

        # ================================================================
        # CHECK 5: Data Freshness
        # ================================================================
        print(f"\n🕐 CHECK 5: Data Freshness")
        print("-" * 80)

        last_trade_date = hist_1y.index[-1]
        if hasattr(last_trade_date, 'tz') and last_trade_date.tz is not None:
            last_trade_date = last_trade_date.replace(tzinfo=None)

        days_old = (datetime.now() - last_trade_date).days

        freshness_data = {
            'last_trade_date': last_trade_date.strftime('%Y-%m-%d'),
            'days_old': days_old,
            'data_status': 'current' if days_old <= 5 else 'stale'
        }

        result['checks']['freshness'] = freshness_data

        print(f"  Last Trade Date: {last_trade_date.strftime('%Y-%m-%d')}")
        print(f"  Days Old:        {days_old}")
        print(f"  Status:          {'✅ Current' if days_old <= 5 else '⚠️ Stale'}")

        if days_old > 7:
            result['issues'].append({
                'type': 'stale_data',
                'severity': 'medium',
                'description': f"Data is {days_old} days old",
                'days_old': days_old
            })

        # ================================================================
        # CHECK 6: Historical Price Level Comparison
        # ================================================================
        print(f"\n📉 CHECK 6: Historical Price Level Analysis")
        print("-" * 80)

        # Get data for different periods
        hist_2y = ticker_obj.history(period='2y')
        hist_5y = ticker_obj.history(period='5y')

        price_levels = {
            'current': float(current_price),
            'avg_1y': float(hist_1y['Close'].mean()) if not hist_1y.empty else None,
            'avg_2y': float(hist_2y['Close'].mean()) if not hist_2y.empty else None,
            'avg_5y': float(hist_5y['Close'].mean()) if not hist_5y.empty else None,
            'max_5y': float(hist_5y['High'].max()) if not hist_5y.empty else None,
            'min_5y': float(hist_5y['Low'].min()) if not hist_5y.empty else None,
        }

        result['checks']['historical_price_levels'] = price_levels

        print(f"  Current Price:  ₹{price_levels['current']:,.2f}")
        if price_levels['avg_1y']:
            print(f"  1-Year Avg:     ₹{price_levels['avg_1y']:,.2f} (current is {(current_price/price_levels['avg_1y']-1)*100:+.1f}%)")
        if price_levels['avg_2y']:
            print(f"  2-Year Avg:     ₹{price_levels['avg_2y']:,.2f} (current is {(current_price/price_levels['avg_2y']-1)*100:+.1f}%)")
        if price_levels['avg_5y']:
            print(f"  5-Year Avg:     ₹{price_levels['avg_5y']:,.2f} (current is {(current_price/price_levels['avg_5y']-1)*100:+.1f}%)")
        if price_levels['max_5y']:
            print(f"  5-Year High:    ₹{price_levels['max_5y']:,.2f}")
        if price_levels['min_5y']:
            print(f"  5-Year Low:     ₹{price_levels['min_5y']:,.2f}")

        # Check if current price is way below historical averages
        if price_levels['avg_2y']:
            deviation_from_avg = (current_price / price_levels['avg_2y'] - 1) * 100
            if deviation_from_avg < -30:
                result['issues'].append({
                    'type': 'significant_price_deviation',
                    'severity': 'medium',
                    'description': f"Current price {abs(deviation_from_avg):.1f}% below 2-year average",
                    'deviation_pct': deviation_from_avg,
                    'possible_causes': ['Market correction', 'Stock split', 'Company fundamentals change']
                })
                print(f"\n  ⚠️  NOTE: Price significantly below 2-year average ({deviation_from_avg:.1f}%)")

    except Exception as e:
        result['error'] = str(e)
        print(f"\n❌ ERROR: {e}")

    # ================================================================
    # FINAL VERDICT
    # ================================================================
    print(f"\n{'='*80}")
    print(f"VALIDATION SUMMARY")
    print(f"{'='*80}\n")

    if len(result['issues']) == 0:
        print("✅ ALL CHECKS PASSED - Data is legitimate and consistent")
        result['verdict'] = 'PASSED'
    else:
        print(f"⚠️  {len(result['issues'])} issue(s) detected:")
        for i, issue in enumerate(result['issues'], 1):
            print(f"  {i}. [{issue['severity'].upper()}] {issue['description']}")

        # Determine if issues are explainable
        has_split = any(c['type'] == 'stock_split_adjustment' for c in result['corrections'])
        has_price_drop = any(i['type'] == 'sudden_price_drop' for i in result['issues'])

        if has_split and has_price_drop:
            print(f"\n✅ VERDICT: Issues explained by stock split - Data is LEGITIMATE")
            result['verdict'] = 'PASSED_WITH_EXPLANATION'
        else:
            print(f"\n⚠️  VERDICT: Data requires manual review")
            result['verdict'] = 'REVIEW_REQUIRED'

    if len(result['corrections']) > 0:
        print(f"\n📋 Corrections Applied:")
        for correction in result['corrections']:
            print(f"  - {correction['explanation']}")

    return result


def compare_multiple_tickers(tickers: list):
    """
    Compare multiple tickers to identify systematic issues vs individual anomalies.
    """

    print(f"\n{'='*80}")
    print(f"COMPARATIVE ANALYSIS: {len(tickers)} Tickers")
    print(f"{'='*80}\n")

    results = []

    for ticker in tickers:
        result = deep_validate_ticker(ticker)
        results.append(result)
        print("\n")

    # Save results
    output_file = f"deep_validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"COMPARATIVE SUMMARY")
    print(f"{'='*80}\n")

    for result in results:
        ticker = result['ticker']
        verdict = result['verdict']
        issues_count = len(result['issues'])

        status_icon = '✅' if verdict == 'PASSED' else ('⚠️' if verdict == 'PASSED_WITH_EXPLANATION' else '❌')
        print(f"{status_icon} {ticker:15} | Verdict: {verdict:25} | Issues: {issues_count}")

    print(f"\n📄 Detailed results saved to: {output_file}")

    return results


if __name__ == '__main__':
    # Test with the tickers we've been analyzing + a few more for comparison
    test_tickers = [
        'RELIANCE',  # The one with potential deviation
        'CDSL',      # The one that matched perfectly
        'TCS',       # Large cap IT
        'INFY',      # Large cap IT
        'HDFCBANK',  # Large cap banking
    ]

    if len(sys.argv) > 1:
        # Single ticker mode
        ticker = sys.argv[1]
        result = deep_validate_ticker(ticker)

        # Save result
        output_file = f"deep_validation_{ticker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"\n📄 Results saved to: {output_file}")
    else:
        # Comparative mode
        results = compare_multiple_tickers(test_tickers)
