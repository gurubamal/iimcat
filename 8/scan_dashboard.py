#!/usr/bin/env python3
"""Real-time scan dashboard"""

import time
import subprocess
import os

def get_scan_status():
    """Get current scan status"""
    try:
        # Check if process is running
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        running_scans = []
        for line in lines:
            if 'enhanced_india' in line and 'grep' not in line:
                parts = line.split()
                if len(parts) >= 3:
                    pid = parts[1]
                    cpu = parts[2]
                    running_scans.append(f"PID {pid} - CPU {cpu}%")
        
        return running_scans
    except:
        return []

def get_latest_aggregated():
    """Get latest aggregated file info"""
    try:
        result = subprocess.run(['ls', '-t', 'aggregated_full_articles_48h_*.txt'], 
                               capture_output=True, text=True)
        if result.stdout:
            latest = result.stdout.strip().split('\n')[0]
            
            # Get file size
            size_result = subprocess.run(['du', '-h', latest], capture_output=True, text=True)
            size = size_result.stdout.split()[0] if size_result.stdout else "Unknown"
            
            # Count tickers and articles
            tickers = subprocess.run(['grep', '-c', 'Full Article Fetch Test', latest], 
                                   capture_output=True, text=True)
            articles = subprocess.run(['grep', '-c', 'Title   :', latest], 
                                    capture_output=True, text=True)
            
            ticker_count = tickers.stdout.strip() if tickers.returncode == 0 else "0"
            article_count = articles.stdout.strip() if articles.returncode == 0 else "0"
            
            return {
                'file': latest,
                'size': size,
                'tickers': ticker_count,
                'articles': article_count
            }
    except:
        pass
    return None

print("🚀 ENHANCED SCAN DASHBOARD")
print("=" * 80)

running = get_scan_status()
if running:
    print("✅ Status: RUNNING")
    for scan in running:
        print(f"   {scan}")
else:
    print("⏸️  Status: NO ACTIVE SCANS")

print()

# Check latest file
latest = get_latest_aggregated()
if latest:
    print(f"📊 Latest Progress:")
    print(f"   File: {latest['file']}")
    print(f"   Size: {latest['size']}")
    print(f"   Tickers: {latest['tickers']}/2993")
    if latest['tickers'].isdigit():
        progress = int(latest['tickers']) * 100 / 2993
        print(f"   Progress: {progress:.1f}%")
    print(f"   Articles: {latest['articles']}")

print()
print("📁 Monitor Commands:")
print("   tail -f copilot_run_*.log        # Real-time log")
print("   python3 copilot_agent.py run monitor  # Agent monitor")
print("   ./monitor_scan.sh                # Detailed monitor")

print()
print("⏱️  Estimated completion: 15-25 minutes")
print("=" * 80)

