#!/usr/bin/env python3
"""
TEMPORAL CONTEXT VALIDATOR
Handles temporal awareness to prevent stale data and temporal bias issues

Features:
- Track data recency and freshness
- Identify temporal conflicts (old data vs current)
- Flag stale analyst targets
- Monitor news timeliness
- Warn about year-end/quarter-end anomalies
- Prevent using outdated comparisons

Design Principles:
1. EXPLICIT DATES: Everything has publication/verification dates
2. FRESHNESS TRACKING: Flag data older than threshold
3. CONFLICT RESOLUTION: Alert when data from different periods contradict
4. CONTEXT AWARENESS: Understand quarter/year cycles
5. TRANSPARENCY: Show exactly what data is stale
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
CRITICAL_FRESHNESS_HOURS = 48  # Data older than 48h is critical
WARNING_FRESHNESS_HOURS = 168  # Data older than 7d needs warning
ANALYST_TARGET_VALIDITY_DAYS = 90  # Analyst targets valid for ~90 days
EARNINGS_VALIDITY_DAYS = 365  # Earnings data valid for 1 year
FII_DATA_VALIDITY_HOURS = 24  # FII data should be fresh


@dataclass
class TemporalIssue:
    """Issue related to data timeliness"""
    field_name: str  # e.g., "analyst_target", "FII_holding"
    issue_type: str  # "STALE", "CONFLICT", "OUTDATED", "UNCLEAR_TIMING"
    severity: str  # CRITICAL, WARNING, INFO
    description: str  # What the issue is
    data_age_days: Optional[float]  # How old is the data?
    recommendation: str  # What to do about it


@dataclass
class TemporalAssessment:
    """Complete temporal assessment of stock data"""
    ticker: str
    assessment_timestamp: str
    total_issues: int
    critical_issues: int
    warning_issues: int
    issues: List[TemporalIssue]
    overall_freshness: str  # "FRESH", "ACCEPTABLE", "STALE", "CRITICAL"
    stale_data_fields: List[str]  # Fields that are too old
    conflict_alerts: List[str]  # Temporal conflicts found
    recommendations: List[str]  # Actions needed


class TemporalContextValidator:
    """
    Validates temporal context of all stock data.
    Ensures we're not using stale or conflicting data.
    """

    def __init__(self):
        """Initialize validator"""
        self.current_time = datetime.now()
        self.current_quarter = self._get_current_quarter()
        self.current_year = datetime.now().year

    def validate_temporal_context(self, ticker: str, analysis_data: Dict,
                                 verification_results: Dict) -> TemporalAssessment:
        """
        Validate all temporal aspects of the data

        Args:
            ticker: Stock ticker
            analysis_data: Original analysis data
            verification_results: Web verification results

        Returns:
            TemporalAssessment with all temporal issues identified
        """
        timestamp = datetime.now().isoformat()
        issues = []

        # Check earnings data freshness
        earnings_issues = self._validate_earnings_timeliness(ticker, analysis_data, verification_results)
        issues.extend(earnings_issues)

        # Check analyst target validity
        analyst_issues = self._validate_analyst_data(ticker, analysis_data)
        issues.extend(analyst_issues)

        # Check FII/DII data freshness
        institutional_issues = self._validate_institutional_data(ticker, analysis_data)
        issues.extend(institutional_issues)

        # Check for temporal conflicts
        conflict_issues = self._check_temporal_conflicts(ticker, analysis_data)
        issues.extend(conflict_issues)

        # Check price data freshness
        price_issues = self._validate_price_data(ticker, analysis_data)
        issues.extend(price_issues)

        # Categorize issues
        critical_issues = [i for i in issues if i.severity == "CRITICAL"]
        warning_issues = [i for i in issues if i.severity == "WARNING"]

        # Assess overall freshness
        overall_freshness = self._assess_overall_freshness(issues)

        # Generate recommendations
        recommendations = self._generate_temporal_recommendations(issues)

        return TemporalAssessment(
            ticker=ticker,
            assessment_timestamp=timestamp,
            total_issues=len(issues),
            critical_issues=len(critical_issues),
            warning_issues=len(warning_issues),
            issues=issues,
            overall_freshness=overall_freshness,
            stale_data_fields=[i.field_name for i in issues if i.issue_type == "STALE"],
            conflict_alerts=[i.description for i in issues if i.issue_type == "CONFLICT"],
            recommendations=recommendations
        )

    def _validate_earnings_timeliness(self, ticker: str, analysis_data: Dict,
                                      verification_results: Dict) -> List[TemporalIssue]:
        """Check if earnings data is fresh and current"""
        issues = []

        # Get earnings publication date
        verifications = verification_results.get('verifications', [])
        earnings_verification = next(
            (v for v in verifications if 'profit' in v.get('field_name', '').lower()),
            None
        )

        if earnings_verification:
            pub_dates = earnings_verification.get('publication_dates', [])
            if pub_dates:
                latest_date = max(pub_dates)
                try:
                    pub_datetime = datetime.fromisoformat(latest_date)
                    age_hours = (self.current_time - pub_datetime).total_seconds() / 3600
                    age_days = age_hours / 24

                    if age_hours > 48:  # More than 2 days old
                        issues.append(TemporalIssue(
                            field_name="earnings_date",
                            issue_type="STALE",
                            severity="CRITICAL" if age_days > 7 else "WARNING",
                            description=f"Earnings data is {age_days:.1f} days old (published {pub_dates[0]})",
                            data_age_days=age_days,
                            recommendation="Verify earnings haven't been revised or withdrawn"
                        ))
                except:
                    pass

        # Check earnings quarter consistency
        quarter_info = analysis_data.get('quarter_end_date', '')
        if quarter_info:
            try:
                quarter_datetime = datetime.fromisoformat(quarter_info)
                days_since_quarter = (self.current_time - quarter_datetime).days
                if days_since_quarter > 365:
                    issues.append(TemporalIssue(
                        field_name="earnings_quarter",
                        issue_type="OUTDATED",
                        severity="WARNING",
                        description=f"Using earnings from {days_since_quarter} days ago, need more recent quarter",
                        data_age_days=days_since_quarter,
                        recommendation="Wait for current quarter earnings or use latest available"
                    ))
            except:
                pass

        return issues

    def _validate_analyst_data(self, ticker: str, analysis_data: Dict) -> List[TemporalIssue]:
        """Check if analyst targets and ratings are still valid"""
        issues = []

        analyst_target = analysis_data.get('analyst_target')
        analyst_date = analysis_data.get('analyst_target_date')

        if analyst_target and analyst_date:
            try:
                target_datetime = datetime.fromisoformat(analyst_date)
                age_days = (self.current_time - target_datetime).days

                if age_days > ANALYST_TARGET_VALIDITY_DAYS:
                    issues.append(TemporalIssue(
                        field_name="analyst_target",
                        issue_type="OUTDATED",
                        severity="WARNING",
                        description=f"Analyst target is {age_days} days old (from {analyst_date})",
                        data_age_days=age_days,
                        recommendation="Target may not reflect current market conditions. Verify with latest analyst report"
                    ))

                current_price = analysis_data.get('current_price', 0)
                if current_price > analyst_target * 1.1:
                    issues.append(TemporalIssue(
                        field_name="analyst_target",
                        issue_type="CONFLICT",
                        severity="CRITICAL",
                        description=f"Current price ₹{current_price} > analyst target ₹{analyst_target} by 10%+",
                        data_age_days=age_days,
                        recommendation="Target is outdated or market expectations have changed significantly"
                    ))
            except:
                pass

        return issues

    def _validate_institutional_data(self, ticker: str, analysis_data: Dict) -> List[TemporalIssue]:
        """Check if FII/DII data is fresh"""
        issues = []

        fii_date = analysis_data.get('fii_update_date')
        dii_date = analysis_data.get('dii_update_date')

        for holding_type, date in [("FII", fii_date), ("DII", dii_date)]:
            if date:
                try:
                    holding_datetime = datetime.fromisoformat(date)
                    age_hours = (self.current_time - holding_datetime).total_seconds() / 3600
                    age_days = age_hours / 24

                    if age_hours > FII_DATA_VALIDITY_HOURS:
                        severity = "CRITICAL" if age_days > 7 else "WARNING"
                        issues.append(TemporalIssue(
                            field_name=f"{holding_type}_holding",
                            issue_type="STALE",
                            severity=severity,
                            description=f"{holding_type} data is {age_days:.1f} days old",
                            data_age_days=age_days,
                            recommendation=f"Get latest {holding_type} shareholding from NSE"
                        ))
                except:
                    pass

        return issues

    def _check_temporal_conflicts(self, ticker: str, analysis_data: Dict) -> List[TemporalIssue]:
        """Check for temporal conflicts between different data sources"""
        issues = []

        # Compare quarter-end earnings with current date
        quarter_end = analysis_data.get('quarter_end_date')
        if quarter_end:
            try:
                quarter_datetime = datetime.fromisoformat(quarter_end)
                if quarter_datetime > self.current_time:
                    issues.append(TemporalIssue(
                        field_name="quarter_date",
                        issue_type="CONFLICT",
                        severity="CRITICAL",
                        description=f"Quarter end date {quarter_end} is in the FUTURE (impossible)",
                        data_age_days=None,
                        recommendation="Fix quarter end date - appears to be incorrect"
                    ))
            except:
                pass

        # Check if analyst target newer than earnings
        analyst_date = analysis_data.get('analyst_target_date')
        earnings_date = analysis_data.get('earnings_announcement_date')

        if analyst_date and earnings_date:
            try:
                analyst_dt = datetime.fromisoformat(analyst_date)
                earnings_dt = datetime.fromisoformat(earnings_date)

                if analyst_dt < earnings_dt:
                    issues.append(TemporalIssue(
                        field_name="analyst_vs_earnings",
                        issue_type="CONFLICT",
                        severity="WARNING",
                        description=f"Analyst target ({analyst_date}) is older than earnings ({earnings_date})",
                        data_age_days=(self.current_time - analyst_dt).days,
                        recommendation="Analyst target may not include latest earnings data"
                    ))
            except:
                pass

        return issues

    def _validate_price_data(self, ticker: str, analysis_data: Dict) -> List[TemporalIssue]:
        """Check if price data is fresh"""
        issues = []

        price_timestamp = analysis_data.get('price_timestamp')
        current_price = analysis_data.get('current_price')

        if price_timestamp and current_price:
            try:
                price_datetime = datetime.fromisoformat(price_timestamp)
                age_hours = (self.current_time - price_datetime).total_seconds() / 3600

                if age_hours > 24:
                    issues.append(TemporalIssue(
                        field_name="current_price",
                        issue_type="STALE",
                        severity="CRITICAL" if age_hours > 72 else "WARNING",
                        description=f"Price data is {age_hours:.1f} hours old (from {price_timestamp})",
                        data_age_days=age_hours / 24,
                        recommendation="Refresh price data from yfinance for current market conditions"
                    ))
            except:
                pass

        return issues

    def _assess_overall_freshness(self, issues: List[TemporalIssue]) -> str:
        """Assess overall data freshness"""
        if not issues:
            return "FRESH"

        critical = sum(1 for i in issues if i.severity == "CRITICAL")
        if critical > 0:
            return "CRITICAL"

        warning = sum(1 for i in issues if i.severity == "WARNING")
        if warning > 3:
            return "STALE"
        elif warning > 0:
            return "ACCEPTABLE"
        else:
            return "FRESH"

    def _generate_temporal_recommendations(self, issues: List[TemporalIssue]) -> List[str]:
        """Generate recommendations based on temporal issues"""
        recommendations = []

        for issue in issues:
            if issue.severity in ["CRITICAL", "WARNING"]:
                recommendations.append(issue.recommendation)

        if not recommendations:
            recommendations.append("✅ Data is temporally sound and current")

        return list(set(recommendations))  # Remove duplicates

    def _get_current_quarter(self) -> str:
        """Get current quarter"""
        month = self.current_time.month
        quarter = (month - 1) // 3 + 1
        return f"Q{quarter} FY{self.current_time.year}"


# Integration helper
def create_temporal_validator_for_analysis(ticker: str, analysis_data: Dict,
                                           verification_results: Dict) -> Dict:
    """
    Helper function to create temporal validation for stock analysis

    Returns combined assessment with all temporal insights
    """
    validator = TemporalContextValidator()
    assessment = validator.validate_temporal_context(ticker, analysis_data, verification_results)

    return {
        'ticker': ticker,
        'temporal_assessment': asdict(assessment),
        'freshness_status': assessment.overall_freshness,
        'temporal_ok': assessment.critical_issues == 0,
        'stale_fields': assessment.stale_data_fields,
        'conflicts': assessment.conflict_alerts,
        'actions_needed': assessment.recommendations
    }


if __name__ == "__main__":
    validator = TemporalContextValidator()

    test_data = {
        'ticker': 'SIEMENS',
        'current_price': 3084.20,
        'price_timestamp': '2025-11-15T01:43:20',
        'analyst_target': 885,
        'analyst_target_date': '2025-11-01',
        'quarter_end_date': '2025-09-30',
        'fii_update_date': '2025-11-15T10:00:00'
    }

    test_verification = {
        'verifications': [
            {
                'field_name': 'Q2_profit',
                'publication_dates': ['2025-11-15']
            }
        ]
    }

    result = create_temporal_validator_for_analysis('SIEMENS', test_data, test_verification)
    print(json.dumps(result, indent=2, default=str))
