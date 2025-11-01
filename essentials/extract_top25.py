#!/usr/bin/env python3
"""
Extract Top-25 from existing analysis and prepare for frontier-AI processing.
"""

import pandas as pd
import sys
from pathlib import Path

def extract_top25():
    """Extract Top-25 from latest analysis output."""
    
    # Find latest AI analysis
    output_dir = Path('outputs')
    csv_files = sorted(output_dir.glob('ai_adjusted_top50_*.csv'), reverse=True)
    
    if not csv_files:
        print("[ERROR] No ai_adjusted_top50_*.csv files found in outputs/")
        sys.exit(1)
    
    latest_file = csv_files[0]
    print(f"[INFO] Loading latest analysis: {latest_file}")
    
    df = pd.read_csv(latest_file)
    
    # Take top 25
    top25 = df.head(25).copy()
    
    # Ensure required columns
    if 'ticker' not in top25.columns:
        top25 = top25.rename(columns={df.columns[0]: 'ticker'})
    
    # Add marketcap_cr (estimate if not present)
    if 'marketcap_cr' not in top25.columns:
        top25['marketcap_cr'] = 50000.0  # Default estimate
    
    if 'existing_rank' not in top25.columns:
        top25['existing_rank'] = range(1, len(top25) + 1)
    
    # Keep minimal columns
    top25 = top25[['ticker', 'marketcap_cr', 'existing_rank']].reset_index(drop=True)
    
    # Save
    output_file = 'top25_for_frontier_ai.csv'
    top25.to_csv(output_file, index=False)
    
    print(f"[SUCCESS] Top-25 extracted to {output_file}")
    print(f"\nTop 25 Tickers:")
    print(top25.to_string(index=False))
    
    return output_file

if __name__ == '__main__':
    extract_top25()
