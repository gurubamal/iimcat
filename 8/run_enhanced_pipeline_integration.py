#!/usr/bin/env python3
"""
ENHANCED PIPELINE INTEGRATION
Takes existing realtime_ai_news_analyzer results and enhances them with:
- Web search verification
- Temporal context validation
- AI verdict generation
- Audit trail creation

Usage:
    python3 run_enhanced_pipeline_integration.py --input realtime_ai_results.csv --output enhanced_results.csv
"""

import json
import logging
import argparse
import sys
import csv
import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Import enhanced pipeline
try:
    from enhanced_analysis_pipeline import EnhancedAnalysisPipeline
except ImportError as e:
    print(f"❌ Error: enhanced_analysis_pipeline not found: {e}")
    print("   Please ensure all modules are in the same directory")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header():
    """Print integration header"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║     ENHANCED PIPELINE INTEGRATION                           ║
║                                                              ║
║  Taking existing analysis results and enhancing with:       ║
║  ✅ Web Search Verification                                 ║
║  ✅ Temporal Context Validation                             ║
║  ✅ AI Verdict Generation                                   ║
║  ✅ Audit Trail Creation                                    ║
║  ✅ Confidence Calibration                                  ║
╚══════════════════════════════════════════════════════════════╝
""")


def read_csv_results(input_file: str) -> List[Dict]:
    """Read CSV results from analyzer"""
    logger.info(f"📖 Reading CSV results from: {input_file}")

    if not Path(input_file).exists():
        logger.error(f"❌ File not found: {input_file}")
        return []

    results = []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                results.append(row)
        logger.info(f"✅ Loaded {len(results)} stocks from CSV")
        return results
    except Exception as e:
        logger.error(f"❌ Failed to read CSV: {e}")
        return []


def convert_csv_row_to_analysis(row: Dict) -> Dict:
    """Convert CSV row to analysis dictionary for pipeline"""
    try:
        analysis = {
            'ticker': row.get('ticker', ''),
            'ai_score': float(row.get('ai_score', 50)),
            'sentiment': row.get('sentiment', 'neutral'),
            'recommendation': row.get('recommendation', 'HOLD'),
            'catalysts': [c.strip() for c in (row.get('catalysts', '') or '').split(',') if c.strip()],
            'risks': [r.strip() for r in (row.get('risks', '') or '').split(',') if r.strip()],
            'certainty': float(row.get('certainty', 50)),
            'articles_count': int(row.get('articles_count', 0)),
            'current_price': float(row.get('current_price', 0)) if row.get('current_price') else None,
            'price_timestamp': row.get('price_timestamp', datetime.now().isoformat()),
            'company_name': row.get('company_name', ''),
        }

        # Try to extract financial, holdings, and target data if available so that the
        # web verification layer can operate on the same metrics that the CSV
        # exposes (growth, margins, health, holdings, targets, sentiment).
        try:
            # Quarterly YoY earnings growth
            if row.get('quarterly_earnings_growth_yoy'):
                analysis['quarterly_earnings_growth_yoy'] = float(row.get('quarterly_earnings_growth_yoy', 0))
        except (ValueError, TypeError):
            pass

        try:
            # Annual YoY earnings growth
            if row.get('annual_earnings_growth_yoy'):
                analysis['annual_earnings_growth_yoy'] = float(row.get('annual_earnings_growth_yoy', 0))
        except (ValueError, TypeError):
            pass

        try:
            # Profit margin percentage
            if row.get('profit_margin_pct'):
                analysis['profit_margin_pct'] = float(row.get('profit_margin_pct', 0))
        except (ValueError, TypeError):
            pass

        # Financial health status (string field)
        if row.get('financial_health_status'):
            analysis['financial_health_status'] = row.get('financial_health_status')

        # Institutional holdings (FII/DII) – used by InstitutionalHoldingVerifier
        try:
            if row.get('fii_holding_pct'):
                analysis['fii_holding_pct'] = float(row.get('fii_holding_pct', 0))
        except (ValueError, TypeError):
            pass

        try:
            if row.get('dii_holding_pct'):
                analysis['dii_holding_pct'] = float(row.get('dii_holding_pct', 0))
        except (ValueError, TypeError):
            pass

        try:
            # Conservative and aggressive targets (if present)
            if row.get('target_conservative'):
                analysis['target_conservative'] = float(row.get('target_conservative', 0))
        except (ValueError, TypeError):
            pass

        try:
            if row.get('target_aggressive'):
                analysis['target_aggressive'] = float(row.get('target_aggressive', 0))
        except (ValueError, TypeError):
            pass

        return analysis
    except Exception as e:
        logger.error(f"Failed to convert CSV row: {e}")
        return None


def enhance_results(csv_results: List[Dict], pipeline: EnhancedAnalysisPipeline) -> List[Dict]:
    """Run each result through enhanced pipeline"""
    logger.info(f"\n{'='*80}")
    logger.info(f"🚀 Enhancing {len(csv_results)} stock analyses through enhanced pipeline")
    logger.info(f"{'='*80}\n")

    enhanced_results = []

    for idx, row in enumerate(csv_results, 1):
        ticker = row.get('ticker', 'UNKNOWN')

        # Convert CSV row to analysis format
        analysis = convert_csv_row_to_analysis(row)
        if not analysis:
            logger.warning(f"⚠️  Skipping {ticker} - failed to convert data")
            enhanced_results.append({
                'ticker': ticker,
                'error': 'Failed to convert CSV data',
                'original_score': row.get('ai_score', ''),
                'original_sentiment': row.get('sentiment', '')
            })
            continue

        try:
            # Process through enhanced pipeline
            logger.info(f"\n[{idx}/{len(csv_results)}] Processing {ticker}...")
            enhanced = pipeline.process_analysis(ticker, analysis)
            enhanced_results.append(enhanced)

            # Print brief summary
            original_score = enhanced['initial_analysis']['score']
            final_score = enhanced['final_verdict']['score']
            verification = enhanced['verification']

            print(f"\n📊 {ticker}")
            print(f"   Score: {original_score:.1f} → {final_score:.1f}")
            print(f"   Verification: {verification['verified_count']}/{verification['verified_count'] + verification['unverified_count']} verified")
            print(f"   Temporal: {enhanced['temporal']['freshness']}")
            print(f"   Final Verdict: {enhanced['final_verdict']['recommendation']} (Confidence: {enhanced['final_verdict']['confidence']:.0%})")

        except Exception as e:
            logger.error(f"❌ Error processing {ticker}: {e}")
            enhanced_results.append({
                'ticker': ticker,
                'error': str(e),
                'original_score': row.get('ai_score', ''),
                'original_sentiment': row.get('sentiment', '')
            })

    return enhanced_results


def save_enhanced_results(enhanced_results: List[Dict], output_file: str, ai_provider: str = "unknown"):
    """Save enhanced results to JSON"""
    logger.info(f"\n{'='*80}")
    logger.info(f"💾 Saving enhanced results to: {output_file}")
    logger.info(f"{'='*80}\n")

    try:
        output_dir = Path('enhanced_results')
        output_dir.mkdir(exist_ok=True)

        # Build timestamped filename with AI provider suffix, e.g.:
        # enhanced_results_2025-11-15_05-51-08_codex-shell.json
        timestamp_str = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        base_stem = Path(output_file).stem or 'enhanced_results'
        safe_provider = (ai_provider or 'unknown').replace('/', '-')
        timestamped_name = f"{base_stem}_{timestamp_str}_{safe_provider}.json"

        timestamped_path = output_dir / timestamped_name
        # Canonical path (for tools/docs): enhanced_results/enhanced_results.json
        canonical_path = output_dir / output_file

        with open(timestamped_path, 'w') as f:
            json.dump(enhanced_results, f, indent=2, default=str)

        # Also copy to canonical output name for convenience
        try:
            shutil.copyfile(timestamped_path, canonical_path)
        except Exception as copy_exc:
            logger.warning(f"⚠️  Unable to copy enhanced results to canonical path {canonical_path}: {copy_exc}")

        logger.info(f"✅ Results saved to: {timestamped_path}")
        logger.info(f"✅ Canonical copy: {canonical_path}")

        # Print summary statistics
        successful = [r for r in enhanced_results if 'error' not in r]
        failed = [r for r in enhanced_results if 'error' in r]

        print(f"\n{'='*80}")
        print(f"📊 ENHANCEMENT SUMMARY")
        print(f"{'='*80}")
        print(f"Total processed: {len(enhanced_results)}")
        print(f"Successful: {len(successful)} ✅")
        print(f"Failed: {len(failed)} ❌")
        print(f"Success rate: {len(successful)/len(enhanced_results)*100:.1f}%")

        # Show top 5 by confidence
        if successful:
            top_by_confidence = sorted(
                successful,
                key=lambda x: x.get('final_verdict', {}).get('confidence', 0),
                reverse=True
            )[:5]

            print(f"\nTop 5 by Confidence:")
            for result in top_by_confidence:
                ticker = result['ticker']
                score = result['final_verdict']['score']
                confidence = result['final_verdict']['confidence']
                recommendation = result['final_verdict']['recommendation']
                print(f"  {ticker}: {score:.1f} → {recommendation} (Confidence: {confidence:.0%})")

        print(f"\n{'='*80}\n")

    except Exception as e:
        logger.error(f"❌ Failed to save results: {e}")


def _infer_ai_provider_from_input(input_path: str) -> str:
    """
    Infer AI provider name from the input CSV filename.

    Expected patterns:
      - realtime_ai_results_YYYY-MM-DD_HH-MM-SS_provider.csv
      - realtime_ai_results.csv (in which case we look for the latest timestamped file)
    """
    try:
        p = Path(input_path)
        name = p.name

        # Direct timestamped input
        if name.startswith("realtime_ai_results_") and name.endswith(".csv"):
            middle = name[len("realtime_ai_results_"):-len(".csv")]
            if "_" in middle:
                _, provider = middle.rsplit("_", 1)
                return provider or "unknown"

        # Canonical input: try to discover latest timestamped file
        if name == "realtime_ai_results.csv":
            candidates = sorted(Path(p.parent or ".").glob("realtime_ai_results_*_*.csv"))
            if candidates:
                latest = candidates[-1].name
                middle = latest[len("realtime_ai_results_"):-len(".csv")]
                if "_" in middle:
                    _, provider = middle.rsplit("_", 1)
                    return provider or "unknown"
    except Exception:
        pass
    return "unknown"


def main():
    """Main function"""
    print_header()

    parser = argparse.ArgumentParser(
        description='Enhanced Pipeline Integration',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enhance existing results
  python3 run_enhanced_pipeline_integration.py --input realtime_ai_results.csv

  # Specify custom output
  python3 run_enhanced_pipeline_integration.py --input realtime_ai_results.csv --output enhanced_20251115.json
"""
    )

    parser.add_argument(
        '--input',
        type=str,
        default='realtime_ai_results.csv',
        help='Input CSV file from analyzer (default: realtime_ai_results.csv)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='enhanced_results.json',
        help='Output JSON file (default: enhanced_results.json)'
    )
    parser.add_argument(
        '--skip-verification',
        action='store_true',
        help='Skip web search verification (faster processing)'
    )
    parser.add_argument(
        '--skip-temporal',
        action='store_true',
        help='Skip temporal validation (faster processing)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )

    args = parser.parse_args()

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Read existing results
    csv_results = read_csv_results(args.input)
    if not csv_results:
        logger.error("No results to enhance")
        sys.exit(1)

    # Infer AI provider from input filename so the enhanced pipeline and
    # verdict engine know whether this came from codex-shell, claude, etc.
    ai_provider = _infer_ai_provider_from_input(args.input)

    # Initialize enhanced pipeline
    logger.info("🚀 Initializing Enhanced Analysis Pipeline...")
    pipeline = EnhancedAnalysisPipeline(
        enable_web_search=not args.skip_verification,
        enable_ai_verdict=True,
        enable_temporal_check=not args.skip_temporal,
        enable_audit_trail=True,
        ai_provider=ai_provider
    )

    # Enhance results
    enhanced = enhance_results(csv_results, pipeline)

    # Save results (both timestamped + canonical)
    save_enhanced_results(enhanced, args.output, ai_provider)


if __name__ == "__main__":
    main()
