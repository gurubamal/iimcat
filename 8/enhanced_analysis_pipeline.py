#!/usr/bin/env python3
"""
ENHANCED ANALYSIS PIPELINE
Integrates all verification, validation, and verdict engines

Workflow:
1. Get initial analysis from realtime_ai_news_analyzer
2. Run WebSearchVerificationEngine to verify claims
3. Run TemporalContextValidator for timeliness check
4. Run AIVerdictEngine for intelligent final verdict
5. Generate complete audit trail and reports
6. Output final results with full transparency

Features:
- No training data bias (uses only web-verified facts)
- Temporal awareness (flags stale data)
- Complete transparency (audit trails)
- Intelligent verdicts (Claude AI based)
- Risk management (conservative approach)
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import asdict

# Import all components
from web_search_verification_layer import WebSearchVerificationEngine
from ai_verdict_engine import AIVerdictEngine
from temporal_context_validator import create_temporal_validator_for_analysis
from data_audit_trail import DataAuditTrail, AuditReport

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedAnalysisPipeline:
    """
    Complete pipeline for enhanced stock analysis with verification, validation, and verdicts.
    """

    def __init__(self, enable_web_search: bool = True, enable_ai_verdict: bool = True,
                 enable_temporal_check: bool = True, enable_audit_trail: bool = True,
                 ai_provider: str = "unknown"):
        """Initialize pipeline components"""
        self.enable_web_search = enable_web_search
        self.enable_ai_verdict = enable_ai_verdict
        self.enable_temporal_check = enable_temporal_check
        self.enable_audit_trail = enable_audit_trail
        # Track which AI provider produced the original CSV so we can adapt
        # verdict behavior for shell/CLI providers like codex without
        # disturbing Claude API/CLI flows.
        self.ai_provider = (ai_provider or "unknown")

        self.verification_engine = WebSearchVerificationEngine() if enable_web_search else None
        self.verdict_engine = AIVerdictEngine(ai_provider=self.ai_provider) if enable_ai_verdict else None
        self.audit_trails: Dict[str, DataAuditTrail] = {}

        logger.info(f"✅ Enhanced Analysis Pipeline initialized")
        logger.info(f"   Web Search Verification: {'✅' if enable_web_search else '❌'}")
        logger.info(f"   AI Verdict Engine: {'✅' if enable_ai_verdict else '❌'} (provider={self.ai_provider})")
        logger.info(f"   Temporal Validation: {'✅' if enable_temporal_check else '❌'}")
        logger.info(f"   Audit Trail: {'✅' if enable_audit_trail else '❌'}")

    def process_analysis(self, ticker: str, initial_analysis: Dict) -> Dict:
        """
        Process analysis through complete pipeline

        Args:
            ticker: Stock ticker
            initial_analysis: Initial analysis from realtime_ai_news_analyzer

        Returns:
            Enhanced analysis with verification, validation, and final verdict
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 Processing: {ticker}")
        logger.info(f"{'='*80}")

        # Step 1: Verify data through web search
        verification_results = self._verify_data(ticker, initial_analysis)
        logger.info(f"✅ Verification complete: {verification_results.get('verified_count')}/{verification_results.get('verification_count')} verified")

        # Step 2: Validate temporal context
        temporal_results = self._validate_temporal(ticker, initial_analysis, verification_results)
        logger.info(f"✅ Temporal check complete: {temporal_results.get('freshness_status')} data")

        # Step 3: Generate intelligent verdict
        final_verdict = self._generate_verdict(ticker, initial_analysis, verification_results)
        logger.info(f"✅ Verdict generated: {final_verdict.get('final_recommendation')} (Score: {final_verdict.get('final_score'):.1f})")

        # Step 4: Create audit trail
        audit_report = self._create_audit_report(
            ticker, initial_analysis, final_verdict, verification_results, temporal_results
        )

        # Compile final results
        enhanced_analysis = {
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),

            # Original analysis
            'initial_analysis': {
                'score': initial_analysis.get('ai_score'),
                'sentiment': initial_analysis.get('sentiment'),
                'recommendation': initial_analysis.get('recommendation'),
                'catalysts': initial_analysis.get('catalysts'),
            },

            # Verification results
            'verification': {
                'status': verification_results.get('overall_assessment'),
                'verified_count': verification_results.get('verified_count'),
                'unverified_count': verification_results.get('unverified_count'),
                'conflicting_count': verification_results.get('conflicting_count'),
                'confidence': f"{verification_results.get('confidence_score'):.0%}",
                'details': verification_results.get('verifications', [])[:3]  # Top 3 for summary
            },

            # Temporal validation
            'temporal': {
                'freshness': temporal_results.get('freshness_status'),
                'critical_issues': len(
                    temporal_results.get('temporal_assessment', {}).get('critical_issues', [])
                ) if isinstance(
                    temporal_results.get('temporal_assessment', {}).get('critical_issues', []), (list, tuple)
                ) else 0,
                'warnings': len(
                    temporal_results.get('temporal_assessment', {}).get('warning_issues', [])
                ) if isinstance(
                    temporal_results.get('temporal_assessment', {}).get('warning_issues', []), (list, tuple)
                ) else 0,
                'stale_fields': temporal_results.get('stale_fields', []),
            },

            # Final verdict
            'final_verdict': {
                'score': final_verdict.get('final_score'),
                'sentiment': final_verdict.get('final_sentiment'),
                'recommendation': final_verdict.get('final_recommendation'),
                'summary': final_verdict.get('verdict_summary'),
                'reasoning': final_verdict.get('reasoning'),
                'confidence': final_verdict.get('confidence_level'),
                'data_basis': final_verdict.get('data_basis'),
                'unverified_claims': final_verdict.get('unverified_claims'),
                'temporal_notes': final_verdict.get('temporal_currency'),
            },

            # Risk flags
            'flags': final_verdict.get('flagged_issues', []),

            # Audit trail
            'audit': {
                'report_summary': {
                    'data_quality': f"{audit_report.data_quality_score:.0f}%",
                    'verified_fields': audit_report.verified_count,
                    'total_fields': audit_report.total_data_points,
                    'critical_issues': len(audit_report.critical_issues),
                    'warnings': len(audit_report.warnings),
                },
                'sources_consulted': list(set(audit_report.sources_consulted)),
                'verifiers_used': audit_report.verifiers_used,
            },

            # Recommendations
            'recommendations': self._compile_recommendations(
                verification_results, temporal_results, final_verdict
            ),

            # Meta
            'pipeline_info': {
                'version': '2.0',
                'components': ['WebSearchVerification', 'AIVerdictEngine', 'TemporalValidator', 'AuditTrail'],
                'grounding': 'NO TRAINING DATA USED - All decisions based on real-time web-verified facts',
                'temporal_grounding': f"Analysis timestamp: {datetime.now().isoformat()}",
            }
        }

        # Export audit trail if enabled
        if self.enable_audit_trail:
            self._export_audit_trail(ticker, audit_report)

        logger.info(f"\n{'='*80}")
        logger.info(f"✅ Analysis complete for {ticker}")
        logger.info(f"{'='*80}\n")

        return enhanced_analysis

    def _verify_data(self, ticker: str, analysis_data: Dict) -> Dict:
        """Verify all claims through web search"""
        if not self.enable_web_search:
            logger.warning("Web search verification DISABLED")
            return {
                'overall_assessment': 'VERIFICATION_DISABLED',
                'verified_count': 0,
                'unverified_count': 0,
                'conflicting_count': 0,
                'verification_count': 0,
                'confidence_score': 0.5,
                'verifications': []
            }

        logger.info(f"🔍 Verifying data through web search...")
        try:
            result = self.verification_engine.verify_stock_analysis(ticker, analysis_data)
            logger.info(f"   {result['verified_count']} verified, {result['unverified_count']} unverified, "
                       f"{result['conflicting_count']} conflicting")
            return result
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {
                'overall_assessment': 'VERIFICATION_FAILED',
                'verified_count': 0,
                'unverified_count': 0,
                'conflicting_count': 0,
                'verification_count': 0,
                'confidence_score': 0.3,
                'verifications': []
            }

    def _validate_temporal(self, ticker: str, analysis_data: Dict, verification_results: Dict) -> Dict:
        """Validate temporal context"""
        if not self.enable_temporal_check:
            logger.warning("Temporal validation DISABLED")
            return {
                'freshness_status': 'UNCHECKED',
                'temporal_assessment': {
                    'critical_issues': [],
                    'warning_issues': [],
                }
            }

        logger.info(f"⏰ Validating temporal context...")
        try:
            result = create_temporal_validator_for_analysis(ticker, analysis_data, verification_results)
            temporal_assessment = result.get('temporal_assessment', {})
            logger.info(f"   Freshness: {result.get('freshness_status')} "
                       f"({temporal_assessment.get('critical_issues', [])} critical, "
                       f"{temporal_assessment.get('warning_issues', [])} warnings)")
            return result
        except Exception as e:
            logger.error(f"Temporal validation failed: {e}")
            return {
                'freshness_status': 'VALIDATION_FAILED',
                'temporal_assessment': {
                    'critical_issues': [],
                    'warning_issues': [],
                }
            }

    def _generate_verdict(self, ticker: str, analysis_data: Dict, verification_results: Dict) -> Dict:
        """Generate AI verdict based on verified data"""
        if not self.enable_ai_verdict:
            logger.warning("AI verdict DISABLED - using original analysis")
            return {
                'final_score': analysis_data.get('ai_score', 50),
                'final_sentiment': analysis_data.get('sentiment', 'neutral'),
                'final_recommendation': analysis_data.get('recommendation', 'HOLD'),
                'verdict_summary': 'Verdict engine disabled',
                'reasoning': 'Using original analysis',
                'confidence_level': 0.5,
                'data_basis': [],
                'unverified_claims': [],
                'temporal_currency': 'Unknown',
                'flagged_issues': ['Verdict engine disabled']
            }

        logger.info(f"🤖 Generating AI verdict based on verified facts...")
        try:
            verdict = self.verdict_engine.generate_verdict(ticker, analysis_data, verification_results)
            logger.info(f"   Verdict: {verdict.final_recommendation} "
                       f"(Score: {verdict.final_score:.1f}, Confidence: {verdict.confidence_level:.0%})")
            return asdict(verdict)
        except Exception as e:
            logger.error(f"Verdict generation failed: {e}")
            return {
                'final_score': analysis_data.get('ai_score', 50),
                'final_sentiment': analysis_data.get('sentiment', 'neutral'),
                'final_recommendation': 'HOLD',
                'verdict_summary': 'Verdict generation failed',
                'reasoning': str(e),
                'confidence_level': 0.2,
                'data_basis': [],
                'unverified_claims': ['Verdict engine error'],
                'temporal_currency': 'Unknown',
                'flagged_issues': [f'Verdict generation failed: {e}']
            }

    def _create_audit_report(self, ticker: str, initial_analysis: Dict, final_verdict: Dict,
                            verification_results: Dict, temporal_results: Dict) -> AuditReport:
        """Create complete audit report"""
        if not self.enable_audit_trail:
            logger.warning("Audit trail DISABLED")
            return AuditReport(
                ticker=ticker,
                analysis_timestamp=datetime.now().isoformat(),
                initial_score=0,
                final_score=0,
                initial_sentiment='',
                final_sentiment='',
                initial_recommendation='',
                final_recommendation='',
                total_data_points=0,
                verified_count=0,
                unverified_count=0,
                conflicting_count=0,
                stale_count=0
            )

        logger.info(f"📋 Creating audit report...")
        try:
            trail = DataAuditTrail(ticker)
            self.audit_trails[ticker] = trail

            # Log verification results
            for verification in verification_results.get('verifications', []):
                trail.log_data_point(
                    field_name=verification.get('field_name'),
                    claimed_value=verification.get('claimed_value'),
                    verification_status=verification.get('verification_status'),
                    verified_value=verification.get('verified_value'),
                    source_urls=verification.get('sources', []),
                    publication_dates=verification.get('publication_dates', []),
                    confidence=verification.get('confidence', 0),
                    reasoning=verification.get('reasoning', '')
                )

            # Log any temporal issues as warnings
            temporal_assessment = temporal_results.get('temporal_assessment', {})
            critical_list = temporal_assessment.get('critical_issues', [])
            warning_list = temporal_assessment.get('warning_issues', [])
            if not isinstance(critical_list, (list, tuple)):
                critical_list = []
            if not isinstance(warning_list, (list, tuple)):
                warning_list = []
            for issue in critical_list:
                trail.add_issue(issue.get('description', '') if isinstance(issue, dict) else str(issue))
            for issue in warning_list:
                trail.add_warning(issue.get('description', '') if isinstance(issue, dict) else str(issue))

            # Generate report
            report = trail.generate_report(initial_analysis, final_verdict, verification_results, temporal_results)
            logger.info(f"   Report generated: {report.data_quality_score:.0f}% data quality")
            return report

        except Exception as e:
            logger.error(f"Audit report creation failed: {e}")
            return AuditReport(
                ticker=ticker,
                analysis_timestamp=datetime.now().isoformat(),
                initial_score=initial_analysis.get('ai_score', 0),
                final_score=final_verdict.get('final_score', 0),
                initial_sentiment=initial_analysis.get('sentiment', ''),
                final_sentiment=final_verdict.get('final_sentiment', ''),
                initial_recommendation=initial_analysis.get('recommendation', ''),
                final_recommendation=final_verdict.get('final_recommendation', ''),
                total_data_points=0,
                verified_count=0,
                unverified_count=0,
                conflicting_count=0,
                stale_count=0
            )

    def _compile_recommendations(self, verification_results: Dict, temporal_results: Dict,
                                final_verdict: Dict) -> List[str]:
        """Compile actionable recommendations"""
        recommendations = []

        # From verification
        recommendations.extend(verification_results.get('recommendations', []))

        # From temporal
        recommendations.extend(temporal_results.get('actions_needed', []))

        # From verdict
        recommendations.extend(final_verdict.get('flagged_issues', []))

        return list(set(recommendations))  # Remove duplicates

    def _export_audit_trail(self, ticker: str, audit_report: AuditReport) -> None:
        """Export audit trail to files"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_path = Path(f'audit_trails/{ticker}_{timestamp}')
            base_path.mkdir(parents=True, exist_ok=True)

            trail = self.audit_trails.get(ticker)
            if trail:
                # CSV export
                trail.export_audit_trail_csv(str(base_path / 'data_points.csv'))

                # JSON export
                trail.export_audit_report_json(str(base_path / 'report.json'), audit_report)

                # HTML export
                trail.export_audit_report_html(str(base_path / 'report.html'), audit_report)

                logger.info(f"✅ Audit trail exported to {base_path}")
        except Exception as e:
            logger.error(f"Failed to export audit trail: {e}")

    def process_multiple_stocks(self, analyses: List[Dict]) -> List[Dict]:
        """Process multiple stock analyses"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🚀 Processing {len(analyses)} stocks through enhanced pipeline")
        logger.info(f"{'='*80}\n")

        results = []
        for analysis in analyses:
            ticker = analysis.get('ticker', 'UNKNOWN')
            try:
                result = self.process_analysis(ticker, analysis)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {ticker}: {e}")
                results.append({
                    'ticker': ticker,
                    'error': str(e),
                    'status': 'FAILED'
                })

        return results


# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = EnhancedAnalysisPipeline(
        enable_web_search=True,
        enable_ai_verdict=True,
        enable_temporal_check=True,
        enable_audit_trail=True
    )

    # Sample analysis
    sample_analysis = {
        'ticker': 'SIEMENS',
        'ai_score': 48.8,
        'sentiment': 'bearish',
        'recommendation': 'HOLD',
        'catalysts': ['Q2 earnings', 'Digital Industries weak'],
        'current_price': 3084.20,
        'price_timestamp': '2025-11-15T01:43:20',
        'rsi': 40.1,
        'momentum_10d': -1.38,
        'q2_profit_cr': 485,
        'revenue_cr': 5171,
        'yoy_growth_pct': -7
    }

    # Process
    result = pipeline.process_analysis('SIEMENS', sample_analysis)

    # Print summary
    print("\n" + "="*80)
    print("📊 FINAL ENHANCED ANALYSIS SUMMARY")
    print("="*80)
    print(json.dumps({
        'ticker': result['ticker'],
        'initial_score': result['initial_analysis']['score'],
        'final_score': result['final_verdict']['score'],
        'final_recommendation': result['final_verdict']['recommendation'],
        'data_quality': result['audit']['report_summary']['data_quality'],
        'verified_fields': f"{result['audit']['report_summary']['verified_fields']}/{result['audit']['report_summary']['total_fields']}",
    }, indent=2))
    print("="*80 + "\n")
