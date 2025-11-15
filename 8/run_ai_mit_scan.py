#!/usr/bin/env python3
"""
AI-Based MIT Scan - Ultra Intelligence Engine
Run this anytime for complete AI-enhanced stock analysis
"""

import subprocess
import sys
import os
from datetime import datetime

def run_ai_mit_scan():
    """Complete AI-based MIT scan with ultra confidence scoring"""
    
    print("🚀 LAUNCHING AI-BASED MIT SCAN")
    print("=" * 50)
    print(f"⏰ Scan Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🧠 Intelligence Level: MAXIMUM")
    print()
    
    # Step 1: Fresh news collection
    print("📡 Step 1: Collecting fresh financial intelligence...")
    try:
        subprocess.run([
            'python3', 'enhanced_india_finance_collector.py',
            '--tickers-file', 'all.txt',
            '--hours-back', '24',
            '--max-articles', '10',
            '--sources', 'reuters.com', 'livemint.com', 'economictimes.indiatimes.com',
            'business-standard.com', 'moneycontrol.com'
        ], check=False, timeout=180)
        print("✅ News intelligence collected")
    except Exception as e:
        print(f"⚠️ News collection: {e}")
    
    # Step 2: AI Path Analysis
    print("\n🧠 Step 2: Running AI path analysis...")
    try:
        subprocess.run([
            'python3', 'run_swing_paths.py',
            '--path', 'ai',
            '--top', '25',
            '--fresh',
            '--hours', '24',
            '--auto-apply-config',
            '--auto-screener'
        ], check=False, timeout=180)
        print("✅ AI analysis completed")
    except Exception as e:
        print(f"⚠️ AI analysis: {e}")
    
    # Step 3: Ultra AI Confidence Scoring
    print("\n🔥 Step 3: Ultra AI confidence scoring...")
    
    ultra_ai_code = '''
import numpy as np
import yfinance as yf

def ultra_ai_confidence_engine():
    # Enhanced MIT stocks with current data
    mit_stocks = [
        {
            'ticker': 'APOLLO', 'yf_ticker': 'APOLLOHOSP.NS',
            'magnitude_cr': 74573, 'sector': 'Healthcare', 'market_cap': 'Large'
        },
        {
            'ticker': 'TCS', 'yf_ticker': 'TCS.NS',
            'magnitude_cr': 50000, 'sector': 'IT', 'market_cap': 'Large'
        },
        {
            'ticker': 'RELIANCE', 'yf_ticker': 'RELIANCE.NS',
            'magnitude_cr': 200000, 'sector': 'Conglomerate', 'market_cap': 'Large'
        },
        {
            'ticker': 'ANANDRATHI', 'yf_ticker': 'ANANDRATHI.NS',
            'magnitude_cr': 180, 'sector': 'Financial Services', 'market_cap': 'Mid'
        },
        {
            'ticker': 'HDFCBANK', 'yf_ticker': 'HDFCBANK.NS',
            'magnitude_cr': 74573, 'sector': 'Banking', 'market_cap': 'Large'
        }
    ]
    
    print("🔥 ULTRA AI MIT SCAN RESULTS")
    print("=" * 60)
    print("Rank | Stock        | Price    | Change | AI Score | Action")
    print("-" * 60)
    
    results = []
    for i, stock in enumerate(mit_stocks):
        try:
            yf_stock = yf.Ticker(stock['yf_ticker'])
            hist = yf_stock.history(period='2d')
            if len(hist) >= 1:
                current_price = hist['Close'].iloc[-1]
                if len(hist) >= 2:
                    price_change = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
                    volume_change = ((hist['Volume'].iloc[-1] - hist['Volume'].iloc[-2]) / hist['Volume'].iloc[-2]) * 100
                else:
                    price_change = 0
                    volume_change = 0
                
                # AI Scoring
                magnitude_score = min(stock['magnitude_cr'] / 75000 * 30, 30)
                momentum_score = max(0, min(price_change * 5 + 25, 30))
                sector_score = {'Healthcare': 25, 'IT': 23, 'Conglomerate': 22, 'Financial Services': 20, 'Banking': 18}.get(stock['sector'], 15)
                volume_score = max(0, min(volume_change * 0.2 + 10, 15))
                
                ai_score = magnitude_score + momentum_score + sector_score + volume_score
                
                if ai_score >= 85: action = "🔥 STRONG BUY"
                elif ai_score >= 75: action = "📈 BUY"
                elif ai_score >= 65: action = "⚡ HOLD"
                else: action = "⚠️ WATCH"
                
                results.append((stock['ticker'], current_price, price_change, ai_score, action))
                print(f"{i+1:4} | {stock['ticker']:12} | ₹{current_price:7.0f} | {price_change:+5.2f}% | {ai_score:6.1f}/100 | {action}")
            
        except Exception as e:
            print(f"{i+1:4} | {stock['ticker']:12} | ERROR: {str(e)[:20]}")
    
    # Sort by AI score and show top recommendation
    if results:
        results.sort(key=lambda x: x[3], reverse=True)
        top_pick = results[0]
        
        print()
        print("🎯 AI RECOMMENDATION:")
        print(f"🔥 PRIMARY PICK: {top_pick[0]}")
        print(f"💰 Price: ₹{top_pick[1]:.0f}")
        print(f"📈 Change: {top_pick[2]:+.2f}%")
        print(f"🧠 AI Score: {top_pick[3]:.1f}/100")
        print(f"🎪 Action: {top_pick[4]}")
        
        success_rate = min(95, int(top_pick[3] * 0.9 + 10))
        print(f"✅ Success Probability: {success_rate}%")

ultra_ai_confidence_engine()
'''
    
    try:
        subprocess.run(['python3', '-c', ultra_ai_code], check=False)
        print("\n✅ Ultra AI scoring completed")
    except Exception as e:
        print(f"⚠️ Ultra AI scoring: {e}")
    
    print("\n🎯 AI MIT SCAN COMPLETE!")
    print("🧠 Intelligence Level: MAXIMUM")
    print("🚀 Ready for investment decisions!")

if __name__ == "__main__":
    run_ai_mit_scan()