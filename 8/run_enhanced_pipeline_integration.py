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

        # Try to extract financial data if available
        try:
            if row.get('quarterly_earnings_growth_yoy'):
                analysis['yoy_growth_pct'] = float(row.get('quarterly_earnings_growth_yoy', 0))
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


def save_enhanced_results(enhanced_results: List[Dict], output_file: str):
    """Save enhanced results to JSON"""
    logger.info(f"\n{'='*80}")
    logger.info(f"💾 Saving enhanced results to: {output_file}")
    logger.info(f"{'='*80}\n")

    try:
        Path('enhanced_results').mkdir(exist_ok=True)
        output_path = Path('enhanced_results') / output_file

        with open(output_path, 'w') as f:
            json.dump(enhanced_results, f, indent=2, default=str)

        logger.info(f"✅ Results saved to: {output_path}")

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

    # Initialize enhanced pipeline
    logger.info("🚀 Initializing Enhanced Analysis Pipeline...")
    pipeline = EnhancedAnalysisPipeline(
        enable_web_search=not args.skip_verification,
        enable_ai_verdict=True,
        enable_temporal_check=not args.skip_temporal,
        enable_audit_trail=True
    )

    # Enhance results
    enhanced = enhance_results(csv_results, pipeline)

    # Save results
    save_enhanced_results(enhanced, args.output)


if __name__ == "__main__":
    main()
