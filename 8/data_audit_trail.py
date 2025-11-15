#!/usr/bin/env python3
"""
DATA AUDIT TRAIL
Complete transparency and traceability for all analysis decisions

Features:
- Track every data point from source to decision
- Document verification process
- Show confidence calculations
- Explain score adjustments
- Create audit reports
- Enable retrospective analysis

Design Principles:
1. COMPLETE TRACEABILITY: Everything can be traced back to source
2. DECISION LOGGING: Every decision is recorded with reasoning
3. CONFIDENCE TRACKING: Know exactly how confident we are
4. SOURCE DOCUMENTATION: Know where every data point came from
5. REVISION HISTORY: Track data changes and updates
"""

import logging
import json
import csv
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DataPoint:
    """Single data point with full provenance"""
    field_name: str
    claimed_value: Any
    verified_value: Optional[Any] = None
    verification_status: str = "UNVERIFIED"  # VERIFIED, CONFLICTING, UNVERIFIED
    source_urls: List[str] = field(default_factory=list)
    publication_dates: List[str] = field(default_factory=list)
    confidence: float = 0.0
    data_age_hours: Optional[float] = None
    is_stale: bool = False
    has_conflict: bool = False
    reasoning: str = ""


@dataclass
class DecisionRecord:
    """Record of a decision made during analysis"""
    decision_type: str  # "SCORE_ADJUSTMENT", "VERDICT_OVERRIDE", "CONFIDENCE_CHANGE"
    timestamp: str
    ticker: str
    original_value: Any
    new_value: Any
    reasoning: str
    confidence_before: float
    confidence_after: float
    data_points_involved: List[str]  # Field names used for decision


@dataclass
class AuditReport:
    """Complete audit report for a stock analysis"""
    ticker: str
    analysis_timestamp: str
    initial_score: float
    final_score: float
    initial_sentiment: str
    final_sentiment: str
    initial_recommendation: str
    final_recommendation: str

    # Data tracking
    total_data_points: int
    verified_count: int
    unverified_count: int
    conflicting_count: int
    stale_count: int

    # Decisions made
    decisions_log: List[DecisionRecord] = field(default_factory=list)
    data_points: List[DataPoint] = field(default_factory=list)

    # Issues and flags
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    # Summary
    overall_confidence: float = 0.0
    data_quality_score: float = 0.0
    recommendation_confidence: float = 0.0

    # Metadata
    verifiers_used: List[str] = field(default_factory=list)
    sources_consulted: List[str] = field(default_factory=list)
    final_verdict_summary: str = ""


class DataAuditTrail:
    """Maintains complete audit trail of analysis"""

    def __init__(self, ticker: str):
        """Initialize audit trail for a ticker"""
        self.ticker = ticker
        self.start_time = datetime.now()
        self.data_points: Dict[str, DataPoint] = {}
        self.decisions: List[DecisionRecord] = []
        self.issues: List[str] = []
        self.warnings: List[str] = []

    def log_data_point(self, field_name: str, claimed_value: Any,
                      verification_status: str = "UNVERIFIED",
                      verified_value: Optional[Any] = None,
                      source_urls: Optional[List[str]] = None,
                      publication_dates: Optional[List[str]] = None,
                      confidence: float = 0.0,
                      reasoning: str = "") -> None:
        """Log a data point with its verification status"""

        # Calculate data age
        data_age = None
        is_stale = False
        if publication_dates:
            try:
                latest_date = max(publication_dates)
                pub_datetime = datetime.fromisoformat(latest_date)
                age_hours = (datetime.now() - pub_datetime).total_seconds() / 3600
                data_age = age_hours
                is_stale = age_hours > 48  # More than 2 days old
            except:
                pass

        # Check for conflicts
        has_conflict = verification_status == "CONFLICTING"

        # Create data point record
        point = DataPoint(
            field_name=field_name,
            claimed_value=claimed_value,
            verified_value=verified_value,
            verification_status=verification_status,
            source_urls=source_urls or [],
            publication_dates=publication_dates or [],
            confidence=confidence,
            data_age_hours=data_age,
            is_stale=is_stale,
            has_conflict=has_conflict,
            reasoning=reasoning
        )

        self.data_points[field_name] = point

        # Log issues if found
        if has_conflict:
            self.issues.append(f"🚨 CONFLICT in {field_name}: {reasoning}")
        if is_stale:
            self.warnings.append(f"⚠️  STALE DATA: {field_name} is {data_age:.1f} hours old")
        if confidence < 0.5:
            self.warnings.append(f"⚠️  LOW CONFIDENCE: {field_name} (confidence: {confidence:.0%})")

    def log_decision(self, decision_type: str, original_value: Any, new_value: Any,
                    reasoning: str, confidence_before: float = 0.0,
                    confidence_after: float = 0.0, data_points_involved: Optional[List[str]] = None) -> None:
        """Log a decision that was made during analysis"""
        record = DecisionRecord(
            decision_type=decision_type,
            timestamp=datetime.now().isoformat(),
            ticker=self.ticker,
            original_value=original_value,
            new_value=new_value,
            reasoning=reasoning,
            confidence_before=confidence_before,
            confidence_after=confidence_after,
            data_points_involved=data_points_involved or []
        )
        self.decisions.append(record)

    def add_issue(self, issue: str) -> None:
        """Add a critical issue"""
        if issue not in self.issues:
            self.issues.append(issue)

    def add_warning(self, warning: str) -> None:
        """Add a warning"""
        if warning not in self.warnings:
            self.warnings.append(warning)

    def generate_report(self, initial_analysis: Dict, final_analysis: Dict,
                       verification_results: Dict, temporal_results: Dict) -> AuditReport:
        """Generate complete audit report"""

        # Count data points
        verified = sum(1 for dp in self.data_points.values() if dp.verification_status == "VERIFIED")
        unverified = sum(1 for dp in self.data_points.values() if dp.verification_status == "UNVERIFIED")
        conflicting = sum(1 for dp in self.data_points.values() if dp.has_conflict)
        stale = sum(1 for dp in self.data_points.values() if dp.is_stale)

        # Calculate quality scores
        total_points = len(self.data_points)
        data_quality = (verified / max(total_points, 1)) * 100

        # Gather sources
        all_sources = set()
        for dp in self.data_points.values():
            all_sources.update(dp.source_urls)

        # Calculate final confidence
        overall_confidence = sum(dp.confidence for dp in self.data_points.values()) / max(total_points, 1)

        # Create report
        report = AuditReport(
            ticker=self.ticker,
            analysis_timestamp=datetime.now().isoformat(),
            initial_score=initial_analysis.get('ai_score', 0),
            final_score=final_analysis.get('final_score', 0),
            initial_sentiment=initial_analysis.get('sentiment', ''),
            final_sentiment=final_analysis.get('final_sentiment', ''),
            initial_recommendation=initial_analysis.get('recommendation', ''),
            final_recommendation=final_analysis.get('final_recommendation', ''),
            total_data_points=total_points,
            verified_count=verified,
            unverified_count=unverified,
            conflicting_count=conflicting,
            stale_count=stale,
            decisions_log=self.decisions,
            data_points=list(self.data_points.values()),
            critical_issues=self.issues,
            warnings=self.warnings,
            overall_confidence=overall_confidence,
            data_quality_score=data_quality,
            recommendation_confidence=min(1.0, overall_confidence * (verified / max(total_points, 1))),
            verifiers_used=["WebSearchVerification", "AIVerdictEngine", "TemporalValidator"],
            sources_consulted=list(all_sources),
            final_verdict_summary=f"{final_analysis.get('final_recommendation')} - {final_analysis.get('verdict_summary', '')}"
        )

        return report

    def export_audit_trail_csv(self, output_file: str) -> None:
        """Export audit trail as CSV"""
        rows = []
        for field_name, point in self.data_points.items():
            rows.append({
                'ticker': self.ticker,
                'field_name': field_name,
                'claimed_value': point.claimed_value,
                'verified_value': point.verified_value,
                'status': point.verification_status,
                'confidence': f"{point.confidence:.0%}",
                'data_age_hours': f"{point.data_age_hours:.1f}" if point.data_age_hours else "N/A",
                'is_stale': point.is_stale,
                'has_conflict': point.has_conflict,
                'sources': "|".join(point.source_urls),
                'dates': "|".join(point.publication_dates),
                'reasoning': point.reasoning
            })

        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys() if rows else [])
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"✅ Audit trail exported to {output_file}")

    def export_audit_report_json(self, output_file: str, report: AuditReport) -> None:
        """Export audit report as JSON"""
        report_dict = asdict(report)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, default=str)

        logger.info(f"✅ Audit report exported to {output_file}")

    def export_audit_report_html(self, output_file: str, report: AuditReport) -> None:
        """Export audit report as HTML for easy viewing"""
        html = self._generate_html_report(report)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"✅ HTML audit report exported to {output_file}")

    def _generate_html_report(self, report: AuditReport) -> str:
        """Generate HTML version of audit report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Audit Report - {report.ticker}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border-left: 4px solid #0066cc; }}
        .critical {{ border-left-color: #cc0000; background-color: #ffe6e6; }}
        .warning {{ border-left-color: #ff9900; background-color: #fff3e6; }}
        .verified {{ color: #00aa00; }}
        .unverified {{ color: #ff6600; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background-color: #f9f9f9; font-weight: bold; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Audit Report - {report.ticker}</h1>
        <p>Generated: {report.analysis_timestamp}</p>
    </div>

    <div class="section">
        <h2>Summary</h2>
        <div class="metric">
            <strong>Initial Score:</strong> {report.initial_score}/100
        </div>
        <div class="metric">
            <strong>Final Score:</strong> {report.final_score}/100
        </div>
        <div class="metric">
            <strong>Recommendation:</strong> {report.final_recommendation}
        </div>
        <div class="metric">
            <strong>Data Quality:</strong> {report.data_quality_score:.0f}%
        </div>
    </div>

    <div class="section">
        <h2>Data Verification Summary</h2>
        <div class="metric verified">
            ✅ Verified: {report.verified_count}/{report.total_data_points}
        </div>
        <div class="metric unverified">
            ⚠️ Unverified: {report.unverified_count}/{report.total_data_points}
        </div>
        <div class="metric critical" style="margin: 0;">
            🚨 Conflicting: {report.conflicting_count}/{report.total_data_points}
        </div>
    </div>

    <div class="section">
        <h2>Data Points</h2>
        <table>
            <thead>
                <tr>
                    <th>Field</th>
                    <th>Claimed</th>
                    <th>Verified</th>
                    <th>Status</th>
                    <th>Confidence</th>
                </tr>
            </thead>
            <tbody>
"""
        for point in report.data_points:
            status_class = 'verified' if point.verification_status == 'VERIFIED' else 'unverified'
            html += f"""
                <tr>
                    <td>{point.field_name}</td>
                    <td>{point.claimed_value}</td>
                    <td>{point.verified_value or '-'}</td>
                    <td><span class="{status_class}">{point.verification_status}</span></td>
                    <td>{point.confidence:.0%}</td>
                </tr>
"""
        html += """
            </tbody>
        </table>
    </div>
"""

        if report.critical_issues:
            html += f"""
    <div class="section critical">
        <h2>🚨 Critical Issues ({len(report.critical_issues)})</h2>
        <ul>
"""
            for issue in report.critical_issues:
                html += f"<li>{issue}</li>\n"
            html += "</ul>\n</div>\n"

        if report.warnings:
            html += f"""
    <div class="section warning">
        <h2>⚠️ Warnings ({len(report.warnings)})</h2>
        <ul>
"""
            for warning in report.warnings:
                html += f"<li>{warning}</li>\n"
            html += "</ul>\n</div>\n"

        html += """
</body>
</html>
"""
        return html


# Helper function
def create_audit_trail(ticker: str) -> DataAuditTrail:
    """Factory function to create audit trail"""
    return DataAuditTrail(ticker)


if __name__ == "__main__":
    # Example usage
    trail = DataAuditTrail('SIEMENS')

    trail.log_data_point(
        'Q2_profit',
        claimed_value=485,
        verification_status='VERIFIED',
        verified_value=485,
        source_urls=['https://business-standard.com'],
        publication_dates=['2025-11-15'],
        confidence=0.98,
        reasoning='Verified against official results'
    )

    trail.log_decision(
        'SCORE_ADJUSTMENT',
        original_value=50,
        new_value=48.8,
        reasoning='Adjusted for revenue growth weighting',
        confidence_before=0.7,
        confidence_after=0.75,
        data_points_involved=['Q2_profit', 'revenue']
    )

    print("✅ Audit trail created successfully")
    print(f"Data points logged: {len(trail.data_points)}")
    print(f"Decisions recorded: {len(trail.decisions)}")
