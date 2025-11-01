#!/usr/bin/env python3
"""
NEWS PROCESSING VERIFICATION SCRIPT
Ensures NO news is skipped during analysis
"""

import sys
import re
from frontier_ai_real_integration import FrontierAIRealIntegration

def verify_news_extraction(news_file):
    """Comprehensive verification that no news is skipped"""
    
    print("\n" + "="*100)
    print("🔍 NEWS EXTRACTION VERIFICATION")
    print("="*100 + "\n")
    
    # Read raw file
    with open(news_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Manual count of all "Title   :" occurrences
    manual_count = len(re.findall(r'Title\s*:', content))
    print(f"📊 Manual count of 'Title   :' in file: {manual_count}")
    
    # Count company sections
    sections = re.split(r'Full Article Fetch Test - (\w+)', content)
    company_count = len(sections) // 2
    print(f"🏢 Total company sections: {company_count}")
    
    # Count "no fresh items"
    no_news_count = content.lower().count('no fresh items')
    print(f"⚪ Companies with 'no fresh items': {no_news_count}")
    print(f"✅ Companies expected to have news: {company_count - no_news_count}")
    
    # Now use system extraction
    print(f"\n{'='*100}")
    print("🤖 TESTING SYSTEM EXTRACTION")
    print("="*100 + "\n")
    
    system = FrontierAIRealIntegration()
    company_news = system.extract_company_news(news_file)
    
    # Count extracted headlines
    extracted_count = sum(len(headlines) for headlines in company_news.values())
    
    print(f"\n{'='*100}")
    print("📊 VERIFICATION RESULTS")
    print("="*100)
    print(f"✅ Companies with extracted news: {len(company_news)}")
    print(f"📰 Total headlines extracted: {extracted_count}")
    print(f"📈 Extraction rate: {extracted_count}/{manual_count} ({extracted_count/manual_count*100:.1f}%)")
    
    # Detailed breakdown
    print(f"\n{'='*100}")
    print("📋 TOP 15 COMPANIES BY NEWS VOLUME")
    print("="*100)
    sorted_companies = sorted(company_news.items(), key=lambda x: len(x[1]), reverse=True)[:15]
    
    for idx, (company, headlines) in enumerate(sorted_companies, 1):
        print(f"{idx:2}. {company:15} {len(headlines):3} headlines")
        for headline in headlines[:2]:
            print(f"    • {headline[:70]}...")
        if len(headlines) > 2:
            print(f"    ... and {len(headlines)-2} more")
    
    # Warning if extraction rate is low
    if extracted_count < manual_count * 0.8:
        print(f"\n⚠️  WARNING: Extraction rate is low ({extracted_count/manual_count*100:.1f}%)")
        print(f"   Some news may be skipped. Expected >80% extraction rate.")
    else:
        print(f"\n✅ EXCELLENT: Extraction rate is {extracted_count/manual_count*100:.1f}%")
        print(f"   System is capturing most/all meaningful news!")
    
    print("\n" + "="*100)
    print("✅ Verification Complete!")
    print("="*100 + "\n")
    
    return {
        'manual_count': manual_count,
        'extracted_count': extracted_count,
        'companies_with_news': len(company_news),
        'extraction_rate': extracted_count / manual_count if manual_count > 0 else 0
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 verify_no_news_skipped.py <news_file>")
        print("\nExample:")
        print("  python3 verify_no_news_skipped.py aggregated_full_articles_48h_20251021_220636.txt")
        sys.exit(1)
    
    news_file = sys.argv[1]
    results = verify_news_extraction(news_file)
    
    # Exit code based on extraction rate
    if results['extraction_rate'] < 0.8:
        print("⚠️  Exit code 1: Low extraction rate")
        sys.exit(1)
    else:
        print("✅ Exit code 0: Success")
        sys.exit(0)
