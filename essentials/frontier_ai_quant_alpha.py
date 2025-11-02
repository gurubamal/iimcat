#!/usr/bin/env python3
"""
FRONTIER-AI QUANT ALPHA - MAIN ORCHESTRATOR
Compute alpha signals for top-25 tickers + news integration.
Output: 22-column CSV + gate analysis + risk metrics.
"""

import pandas as pd
import numpy as np
import sys
import os
from datetime import datetime
import logging
from pathlib import Path
from frontier_ai_quant_alpha_core import (
    QuantFeatureEngine, LLMNewsScorer, AlphaCalculator, RiskManager
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FrontierAIOrchestrator:
    """Orchestrate end-to-end alpha computation."""
    
    def __init__(self, top25_file: str = 'top25_for_frontier_ai.csv', news_file: str = None, demo: bool = False):
        self.top25_file = top25_file
        self.news_file = news_file
        self.results_df = None
        self.demo = demo
        
    def load_top25(self) -> pd.DataFrame:
        """Load top-25 ticker list."""
        if not os.path.exists(self.top25_file):
            logger.error(f"Top-25 file not found: {self.top25_file}")
            return pd.DataFrame()
        
        df = pd.read_csv(self.top25_file)
        required_cols = ['ticker', 'marketcap_cr', 'existing_rank']
        if not all(col in df.columns for col in required_cols):
            logger.warning(f"Expected columns {required_cols}, found {df.columns.tolist()}")
        return df
    
    def load_news_for_ticker(self, ticker: str) -> list:
        """Load news headlines for a ticker from aggregated file."""
        if not self.news_file or not os.path.exists(self.news_file):
            return []
        
        headlines = []
        try:
            with open(self.news_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Simple heuristic: look for ticker mentions
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if ticker.upper() in line.upper() or ticker.split('.')[0].upper() in line.upper():
                        headlines.append(line.strip())
                        # Get context (next 2 lines)
                        if i + 1 < len(lines):
                            headlines.append(lines[i + 1].strip())
        except Exception as e:
            logger.warning(f"Failed to load news for {ticker}: {e}")
        
        return headlines[:10]  # Max 10 headlines
    
    def process_ticker(self, ticker: str, row: pd.Series) -> dict:
        """Process a single ticker through full pipeline."""
        result = {
            'ticker': ticker,
            'marketcap_cr': row.get('marketcap_cr', 0),
            'existing_rank': row.get('existing_rank', -1),
        }
        
        # Step 1: Compute quant features
        engine = QuantFeatureEngine(use_demo=self.demo)
        quant = engine.compute_features(ticker)
        
        if quant is None:
            logger.warning(f"Failed to compute features for {ticker}")
            return None
        
        result.update({
            'close': quant.close,
            'atr20': quant.atr20,
            'momentum_3': quant.momentum_3,
            'momentum_20': quant.momentum_20,
            'momentum_60': quant.momentum_60,
            'rvol': quant.rvol,
            'squeeze': int(quant.squeeze),
            'bb_width': quant.squeeze_bb_width,
            'breakout': quant.breakout,
            'pbz': quant.pbz,
            'trend_sma50': int(quant.trend_sma50),
            'trend_sma200': int(quant.trend_sma200),
            'rsi14': quant.rsi_14,
        })
        
        # Step 2: Score news
        scorer = LLMNewsScorer()
        news_headlines = self.load_news_for_ticker(ticker)
        news = scorer.score_news(news_headlines, ticker)
        
        result.update({
            'catalyst_type': news.catalyst_type,
            'catalyst_count': news.catalyst_count,
            'deal_value_cr': news.deal_value_cr,
            'sentiment': news.sentiment,
            'certainty': news.certainty,
            'headline_text': news.headline_text[:80] if news.headline_text else 'N/A',
            'headline_count': len(news_headlines),
        })
        
        # Step 3: Compute alpha + gates
        alpha_calc = AlphaCalculator()
        alpha, metrics = alpha_calc.compute_alpha(quant, news)
        
        result.update({
            'mom20_norm': metrics['mom20_norm'],
            'mom60_norm': metrics['mom60_norm'],
            'rvol_norm': metrics['rvol_norm'],
            'squeeze_bo_score': metrics['squeeze_bo'],
            'pbz_norm': metrics['pbz_norm'],
            'news_score': metrics['news_score'],
            'alpha': alpha,
            'gate_flags': metrics['gate_flags'],
            'final_pick': int(metrics['final_pick']),
        })
        
        # Step 4: Compute risk levels
        risk = RiskManager.compute_levels(quant.close, quant.atr20)
        result.update({
            'stop_loss': risk['stop'],
            'tp1': risk['tp1'],
            'tp2': risk['tp2'],
            'trail_stop': risk['trail_stop'],
            'impact_pct': (risk['tp1'] - quant.close) / quant.close * 100 if quant.close > 0 else 0,
        })
        
        return result
    
    def run(self, news_file: str = None) -> pd.DataFrame:
        """Run full pipeline."""
        self.news_file = news_file
        
        logger.info("Loading top-25 tickers...")
        top25 = self.load_top25()
        
        if top25.empty:
            logger.error("No tickers to process")
            return pd.DataFrame()
        
        logger.info(f"Processing {len(top25)} tickers...")
        results = []
        
        for idx, row in top25.iterrows():
            ticker = row['ticker']
            logger.info(f"[{idx+1}/{len(top25)}] Processing {ticker}...")
            
            result = self.process_ticker(ticker, row)
            if result:
                results.append(result)
        
        self.results_df = pd.DataFrame(results)
        
        if not self.results_df.empty:
            # Sort by alpha descending
            self.results_df = self.results_df.sort_values('alpha', ascending=False)
            logger.info(f"Processed {len(self.results_df)} tickers successfully")
        
        return self.results_df
    
    def save_results(self, output_file: str = None) -> str:
        """Save results to CSV."""
        if self.results_df is None or self.results_df.empty:
            logger.error("No results to save")
            return None
        
        if output_file is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f'frontier_ai_alpha_results_{timestamp}.csv'
        
        # Column order
        columns = [
            'ticker', 'close', 'alpha', 'final_pick', 'marketcap_cr', 'existing_rank',
            'momentum_20', 'momentum_60', 'momentum_3',
            'rvol', 'rvol_norm', 'pbz', 'pbz_norm',
            'squeeze', 'breakout', 'squeeze_bo_score', 'bb_width',
            'trend_sma50', 'trend_sma200', 'rsi14',
            'catalyst_type', 'catalyst_count', 'deal_value_cr', 'sentiment', 'certainty',
            'news_score', 'mom20_norm', 'mom60_norm',
            'atr20', 'stop_loss', 'tp1', 'tp2', 'trail_stop', 'impact_pct',
            'gate_flags', 'headline_text', 'headline_count'
        ]
        
        # Reorder columns
        available_cols = [c for c in columns if c in self.results_df.columns]
        output_df = self.results_df[available_cols]
        
        output_df.to_csv(output_file, index=False)
        logger.info(f"Results saved to {output_file}")
        
        return output_file

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Frontier-AI Quant Alpha System')
    parser.add_argument('--top25', default='top25_for_frontier_ai.csv', help='Top-25 ticker file')
    parser.add_argument('--news', default=None, help='Aggregated news file')
    parser.add_argument('--output', default=None, help='Output CSV file')
    parser.add_argument('--demo', action='store_true', help='Use demo/synthetic data (no network)')
    
    args = parser.parse_args()
    
    orchestrator = FrontierAIOrchestrator(top25_file=args.top25, demo=args.demo)
    results_df = orchestrator.run(news_file=args.news)
    
    if not results_df.empty:
        output_file = orchestrator.save_results(args.output)
        
        # Print summary
        logger.info("\n" + "="*80)
        logger.info("SUMMARY")
        logger.info("="*80)
        logger.info(f"Total tickers processed: {len(results_df)}")
        logger.info(f"Final picks (gates passed): {results_df['final_pick'].sum()}")
        logger.info(f"Average alpha: {results_df['alpha'].mean():.2f}")
        logger.info(f"Top 5 picks by alpha:")
        for idx, row in results_df.head(5).iterrows():
            flag = "✓ PICK" if row['final_pick'] else "✗ filtered"
            logger.info(f"  {row['ticker']:12} | Alpha: {row['alpha']:6.2f} | {flag} | {row['headline_text']}")

if __name__ == '__main__':
    main()
