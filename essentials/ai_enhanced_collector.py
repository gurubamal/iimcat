#!/usr/bin/env python3
"""
ENHANCED NEWS COLLECTOR WITH REAL-TIME AI ANALYSIS
Hooks into the news fetching process to analyze instantly

This wrapper intercepts news articles as they're fetched and
immediately calls the AI analyzer for scoring and ranking
"""

import sys
import os
from typing import Callable, Dict, Any, List, Optional
import logging

# Import the original collector
import enhanced_india_finance_collector as base_collector

# Import real-time analyzer
from realtime_ai_news_analyzer import RealtimeAIAnalyzer

logger = logging.getLogger(__name__)


class AIAnalysisHook:
    """
    Hook that intercepts fetched articles and analyzes them instantly
    """
    
    def __init__(self, analyzer: RealtimeAIAnalyzer, enabled: bool = True):
        self.analyzer = analyzer
        self.enabled = enabled
        self.articles_processed = 0
        self.articles_analyzed = 0
    
    def on_article_fetched(self, ticker: str, article: Dict[str, Any]):
        """
        Called immediately when an article is fetched
        Triggers instant AI analysis
        """
        if not self.enabled:
            return
        
        self.articles_processed += 1
        
        try:
            # Extract article data
            headline = article.get('title', '')
            full_text = article.get('text', article.get('content', ''))
            url = article.get('url', article.get('link', ''))
            
            if not headline:
                logger.warning(f"  ⚠️  Skipping article with no headline")
                return
            
            # Instant AI analysis
            logger.info(f"  🤖 Analyzing: {headline[:60]}...")
            
            analysis = self.analyzer.analyze_news_instantly(
                ticker=ticker,
                headline=headline,
                full_text=full_text,
                url=url
            )
            
            self.articles_analyzed += 1
            
            # Log immediate result
            logger.info(f"     ✅ Score: {analysis.ai_score:.1f} | {analysis.sentiment.upper()} | {analysis.recommendation}")
            
        except Exception as e:
            logger.error(f"  ❌ Analysis failed for {ticker}: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """Get processing statistics"""
        return {
            'processed': self.articles_processed,
            'analyzed': self.articles_analyzed,
            'success_rate': (self.articles_analyzed / self.articles_processed * 100) 
                           if self.articles_processed > 0 else 0
        }


class EnhancedCollectorWithAI:
    """
    Enhanced collector that performs real-time AI analysis
    """
    
    def __init__(self, enable_ai_analysis: bool = True):
        self.ai_analyzer = RealtimeAIAnalyzer() if enable_ai_analysis else None
        self.analysis_hook = AIAnalysisHook(self.ai_analyzer, enable_ai_analysis) if self.ai_analyzer else None
        self.enable_ai = enable_ai_analysis
    
    def fetch_with_ai_analysis(self, tickers: List[str], hours_back: int = 48,
                               max_articles: int = 10, sources: List[str] = None,
                               **kwargs) -> Dict[str, Any]:
        """
        Fetch news and analyze in real-time
        Returns both raw articles and AI analysis results
        """
        logger.info(f"🚀 Starting AI-enhanced news collection")
        logger.info(f"   Tickers: {len(tickers)}")
        logger.info(f"   Hours back: {hours_back}")
        logger.info(f"   AI analysis: {'ENABLED' if self.enable_ai else 'DISABLED'}")
        
        results = {
            'articles': {},
            'ai_analysis': {},
            'stats': {}
        }
        
        # Process each ticker
        for idx, ticker in enumerate(tickers, 1):
            logger.info(f"\n[{idx}/{len(tickers)}] Processing {ticker}...")
            
            try:
                # Fetch articles using base collector
                # NOTE: This is a simplified version - actual integration depends on
                # the base collector's API
                articles = self._fetch_articles_base(
                    ticker, hours_back, max_articles, sources, **kwargs
                )
                
                results['articles'][ticker] = articles
                
                # Analyze each article in real-time
                if self.enable_ai and articles:
                    logger.info(f"  📰 Found {len(articles)} articles, analyzing...")
                    
                    for article in articles:
                        self.analysis_hook.on_article_fetched(ticker, article)
                    
                    logger.info(f"  ✅ Analysis complete for {ticker}")
                
            except Exception as e:
                logger.error(f"  ❌ Error processing {ticker}: {e}")
        
        # Get AI analysis results
        if self.enable_ai and self.ai_analyzer:
            results['ai_analysis'] = self.ai_analyzer.live_results
            results['stats'] = {
                'collection': self.analysis_hook.get_stats(),
                'rankings': self.ai_analyzer.ranked_stocks
            }
        
        return results
    
    def _fetch_articles_base(self, ticker: str, hours_back: int, 
                            max_articles: int, sources: List[str],
                            **kwargs) -> List[Dict]:
        """
        Fetch articles using base collector
        This is a placeholder - actual implementation depends on base collector API
        """
        # TODO: Integrate with actual base collector
        # For now, return mock data for demonstration
        
        # Example integration (pseudo-code):
        # return base_collector.fetch_for_ticker(ticker, hours_back, max_articles, sources)
        
        return []
    
    def save_ai_results(self, output_file: str):
        """Save AI analysis results"""
        if self.ai_analyzer:
            self.ai_analyzer.save_results(output_file)
    
    def display_rankings(self, top_n: int = 10):
        """Display live rankings"""
        if self.ai_analyzer:
            self.ai_analyzer.display_live_rankings(top_n)


def create_ai_enhanced_collector(**kwargs) -> EnhancedCollectorWithAI:
    """
    Factory function to create AI-enhanced collector
    """
    enable_ai = kwargs.pop('enable_ai_analysis', True)
    return EnhancedCollectorWithAI(enable_ai_analysis=enable_ai)


def main():
    """
    Command-line interface for AI-enhanced collection
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Enhanced news collector with real-time AI analysis'
    )
    parser.add_argument('--tickers', nargs='*', help='Tickers to analyze')
    parser.add_argument('--tickers-file', type=str, help='File with ticker list')
    parser.add_argument('--hours-back', type=int, default=48)
    parser.add_argument('--max-articles', type=int, default=10)
    parser.add_argument('--sources', nargs='*', help='News sources')
    parser.add_argument('--no-ai', action='store_true', help='Disable AI analysis')
    parser.add_argument('--output', default='ai_enhanced_results.csv')
    parser.add_argument('--top', type=int, default=25)
    
    args = parser.parse_args()
    
    # Load tickers
    if args.tickers_file:
        with open(args.tickers_file, 'r') as f:
            tickers = [line.strip() for line in f if line.strip()]
    elif args.tickers:
        tickers = args.tickers
    else:
        logger.error("❌ Must provide --tickers or --tickers-file")
        sys.exit(1)
    
    # Create AI-enhanced collector
    collector = EnhancedCollectorWithAI(enable_ai_analysis=not args.no_ai)
    
    # Run collection with AI analysis
    results = collector.fetch_with_ai_analysis(
        tickers=tickers[:args.top],
        hours_back=args.hours_back,
        max_articles=args.max_articles,
        sources=args.sources
    )
    
    # Display rankings
    collector.display_rankings(top_n=args.top)
    
    # Save results
    collector.save_ai_results(args.output)
    
    # Print stats
    if results['stats']:
        print("\n" + "="*100)
        print("📊 STATISTICS")
        print("="*100)
        stats = results['stats']['collection']
        print(f"Articles processed: {stats['processed']}")
        print(f"Articles analyzed:  {stats['analyzed']}")
        print(f"Success rate:       {stats['success_rate']:.1f}%")
        print("="*100 + "\n")


if __name__ == "__main__":
    main()
