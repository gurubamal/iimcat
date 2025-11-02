#!/usr/bin/env python3
"""
Fundamental Screener
Screen stocks by fundamental metrics before news analysis
"""

import yfinance as yf
import pandas as pd
import csv
from typing import List, Dict
from datetime import datetime
import concurrent.futures
from tqdm import tqdm

class FundamentalScreener:
    """Screen stocks by fundamental criteria"""
    
    def __init__(self, ticker_file: str = 'sec_list.csv'):
        self.ticker_file = ticker_file
        self.tickers = self.load_tickers()
        
    def load_tickers(self) -> List[Dict]:
        """Load tickers from CSV"""
        tickers = []
        try:
            with open(self.ticker_file, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    tickers.append({
                        'ticker': row.get('Symbol', row.get('symbol', '')),
                        'company': row.get('Name', row.get('company', ''))
                    })
        except Exception as e:
            print(f"Error loading tickers: {e}")
        
        return tickers
    
    def get_stock_fundamentals(self, ticker: str) -> Dict:
        """Fetch fundamental data for a stock"""
        try:
            stock = yf.Ticker(f"{ticker}.NS")
            info = stock.info
            
            # Extract key metrics
            fundamentals = {
                'ticker': ticker,
                'company': info.get('longName', ticker),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'roe': info.get('returnOnEquity', 0),
                'profit_margin': info.get('profitMargins', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'earnings_growth': info.get('earningsGrowth', 0),
                'current_price': info.get('currentPrice', 0),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                'beta': info.get('beta', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'volume': info.get('volume', 0),
                'avg_volume': info.get('averageVolume', 0)
            }
            
            return fundamentals
            
        except Exception as e:
            return None
    
    def screen_by_criteria(self, 
                          min_market_cap: float = 100e7,  # 100 crore
                          max_pe: float = 30,
                          max_pb: float = 5,
                          max_debt_to_equity: float = 2,
                          min_roe: float = 0.10,
                          min_profit_margin: float = 0.05,
                          min_revenue_growth: float = 0.10) -> pd.DataFrame:
        """
        Screen stocks by fundamental criteria
        
        Default criteria (conservative):
        - Market cap > 100 crore (avoid penny stocks)
        - P/E < 30 (not overvalued)
        - P/B < 5 (reasonable book value)
        - Debt/Equity < 2 (manageable debt)
        - ROE > 10% (profitable)
        - Profit Margin > 5% (sustainable)
        - Revenue Growth > 10% (growing)
        """
        print("="*100)
        print("📊 FUNDAMENTAL SCREENER")
        print("="*100)
        print(f"Total tickers to screen: {len(self.tickers)}")
        print(f"\nCriteria:")
        print(f"  Market Cap > ₹{min_market_cap/1e7:.0f} crore")
        print(f"  P/E Ratio < {max_pe}")
        print(f"  P/B Ratio < {max_pb}")
        print(f"  Debt/Equity < {max_debt_to_equity}")
        print(f"  ROE > {min_roe*100:.0f}%")
        print(f"  Profit Margin > {min_profit_margin*100:.0f}%")
        print(f"  Revenue Growth > {min_revenue_growth*100:.0f}%")
        print()
        
        results = []
        
        # Use concurrent fetching for speed
        def fetch_wrapper(ticker_dict):
            return self.get_stock_fundamentals(ticker_dict['ticker'])
        
        print("🔍 Fetching fundamental data...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(fetch_wrapper, t) for t in self.tickers[:500]]  # Limit for speed
            
            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
                result = future.result()
                if result:
                    results.append(result)
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        if df.empty:
            print("❌ No data fetched")
            return df
        
        print(f"\n✅ Fetched data for {len(df)} stocks")
        
        # Apply filters
        filtered = df[
            (df['market_cap'] > min_market_cap) &
            (df['pe_ratio'] > 0) & (df['pe_ratio'] < max_pe) &
            (df['pb_ratio'] > 0) & (df['pb_ratio'] < max_pb) &
            (df['debt_to_equity'] < max_debt_to_equity) &
            (df['roe'] > min_roe) &
            (df['profit_margin'] > min_profit_margin) &
            (df['revenue_growth'] > min_revenue_growth)
        ]
        
        print(f"\n📊 Qualified stocks: {len(filtered)}")
        
        # Calculate score
        filtered = self.calculate_quality_score(filtered)
        
        # Sort by score
        filtered = filtered.sort_values('quality_score', ascending=False)
        
        return filtered
    
    def calculate_quality_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate quality score for each stock"""
        df = df.copy()
        
        # Normalize metrics (0-100 scale)
        df['pe_score'] = ((30 - df['pe_ratio']) / 30 * 100).clip(0, 100)
        df['pb_score'] = ((5 - df['pb_ratio']) / 5 * 100).clip(0, 100)
        df['debt_score'] = ((2 - df['debt_to_equity']) / 2 * 100).clip(0, 100)
        df['roe_score'] = (df['roe'] * 100).clip(0, 100)
        df['margin_score'] = (df['profit_margin'] * 200).clip(0, 100)
        df['growth_score'] = (df['revenue_growth'] * 100).clip(0, 100)
        
        # Weighted average
        df['quality_score'] = (
            df['pe_score'] * 0.15 +
            df['pb_score'] * 0.10 +
            df['debt_score'] * 0.15 +
            df['roe_score'] * 0.20 +
            df['margin_score'] * 0.20 +
            df['growth_score'] * 0.20
        )
        
        return df
    
    def generate_report(self, df: pd.DataFrame, top_n: int = 50) -> str:
        """Generate screening report"""
        if df.empty:
            return "No stocks qualified based on screening criteria"
        
        report = []
        report.append("="*120)
        report.append("🏆 TOP STOCKS BY FUNDAMENTAL SCREENING")
        report.append("="*120)
        report.append(f"Qualified Stocks: {len(df)} | Showing Top {top_n}")
        report.append("")
        
        for i, (_, stock) in enumerate(df.head(top_n).iterrows(), 1):
            report.append(f"\n{i}. {stock['ticker']} - {stock['company']}")
            report.append("─" * 120)
            report.append(f"   Quality Score: {stock['quality_score']:.1f}/100")
            report.append(f"   Sector: {stock['sector']} | Industry: {stock['industry']}")
            report.append(f"   Market Cap: ₹{stock['market_cap']/1e7:.0f} crore | Price: ₹{stock['current_price']:.2f}")
            report.append(f"   P/E: {stock['pe_ratio']:.2f} | P/B: {stock['pb_ratio']:.2f} | D/E: {stock['debt_to_equity']:.2f}")
            report.append(f"   ROE: {stock['roe']*100:.1f}% | Profit Margin: {stock['profit_margin']*100:.1f}%")
            report.append(f"   Revenue Growth: {stock['revenue_growth']*100:.1f}% | Beta: {stock['beta']:.2f}")
        
        report.append("\n" + "="*120)
        report.append("📊 SECTOR BREAKDOWN")
        report.append("="*120)
        
        sector_counts = df['sector'].value_counts().head(10)
        for sector, count in sector_counts.items():
            report.append(f"  {sector}: {count} stocks")
        
        return "\n".join(report)


def main():
    """Main execution"""
    screener = FundamentalScreener()
    
    # Run screening with conservative criteria
    qualified = screener.screen_by_criteria(
        min_market_cap=100e7,  # 100 crore
        max_pe=25,
        max_pb=4,
        max_debt_to_equity=1.5,
        min_roe=0.12,
        min_profit_margin=0.08,
        min_revenue_growth=0.15
    )
    
    if not qualified.empty:
        # Generate report
        report = screener.generate_report(qualified, top_n=50)
        print("\n" + report)
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_file = f'screened_stocks_{timestamp}.csv'
        qualified.to_csv(csv_file, index=False)
        print(f"\n💾 Saved {len(qualified)} stocks to {csv_file}")
        
        # Save top 50 tickers for news analysis
        top_50 = qualified.head(50)['ticker'].tolist()
        with open(f'top_50_tickers_{timestamp}.txt', 'w') as f:
            f.write('\n'.join(top_50))
        print(f"💾 Saved top 50 tickers to top_50_tickers_{timestamp}.txt")
        
        print("\n✅ Use these 50 tickers for focused news analysis!")
    else:
        print("\n❌ No stocks qualified. Consider relaxing criteria.")


if __name__ == "__main__":
    main()
