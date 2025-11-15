#!/usr/bin/env python3
"""Pytest unit tests for Correction Boost core logic (offline, synthetic data)."""

import pandas as pd
import numpy as np
import pytest
import sys, os

# Ensure project root is on sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from enhanced_correction_analyzer import EnhancedCorrectionAnalyzer


def _make_ohlcv(close_prices, volumes):
    n = len(close_prices)
    # Build simple OHLC around Close with tiny ranges
    close = pd.Series(close_prices, name='Close')
    open_ = close.shift(1).fillna(close.iloc[0])
    high = pd.concat([open_, close], axis=1).max(axis=1) * 1.005
    low = pd.concat([open_, close], axis=1).min(axis=1) * 0.995
    vol = pd.Series(volumes, name='Volume')
    df = pd.DataFrame({
        'Open': open_.values,
        'High': high.values,
        'Low': low.values,
        'Close': close.values,
        'Volume': vol.values,
    })
    # Add a DatetimeIndex
    df.index = pd.date_range(end=pd.Timestamp.today().normalize(), periods=n, freq='D')
    return df


def test_detect_correction_decline_window_volume():
    analyzer = EnhancedCorrectionAnalyzer()

    # Construct 25 days: stable up to day 15, then 6-day decline >10% with a volume spike
    prices = [100.0] * 15 + [98.0, 96.0, 94.0, 92.0, 90.0, 88.0, 88.0, 88.2, 88.1, 88.0]
    # Base vol 100k, one spike to 200k during decline window
    volumes = [100_000] * 16 + [200_000] + [110_000] * (len(prices) - 17)
    df = _make_ohlcv(prices, volumes)

    result = analyzer.detect_correction('TEST.NS', df)

    assert result['detected'] is True
    assert 10 <= result['correction_pct'] <= 35
    # Confirm enhanced confirmation logic: longest decline streak >= 5 and spike seen in decline
    assert result['decline_days'] >= analyzer.min_decline_days
    assert result['volume_ratio_decline_max'] >= analyzer.min_volume_spike
    assert result['confirmed']


def test_sector_adjustment_neutral_when_unknown():
    analyzer = EnhancedCorrectionAnalyzer()
    # No sector info provided; should be neutral
    base_conf = 0.6
    adj = analyzer.apply_sector_adjustment('TEST.NS', base_conf, fundamental_data={})
    assert pytest.approx(adj['adjusted_confidence'], 1e-6) == base_conf
    assert adj['factor'] == 1.0


def test_correction_confidence_weights():
    analyzer = EnhancedCorrectionAnalyzer()
    oversold, fundamental, catalyst = 80.0, 70.0, 60.0
    conf = analyzer.calculate_correction_confidence(oversold, fundamental, catalyst)
    expected = (0.3 * oversold + 0.3 * fundamental + 0.4 * catalyst) / 100.0
    assert pytest.approx(conf, 1e-6) == expected


def test_risk_filters_pass_simple():
    analyzer = EnhancedCorrectionAnalyzer()
    data = {
        'debt_to_equity': 0.8,
        'current_ratio': 1.2,
        'market_cap_cr': 1000.0,
        'daily_volume': 500_000,
        'avg_volume_30d': 450_000,
        'beta': 1.2,
        'listed_months': 24,
        'correction_confidence': 0.6,
    }
    res = analyzer.apply_risk_filters(data)
    assert res['passed'] is True
