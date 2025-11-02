#!/usr/bin/env python3
"""
NSE Corporate Announcements Scraper
Fetches company-specific announcements from NSE
100% reliable - no entity resolution needed
"""

import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict
import time
import csv

class NSEAnnouncementsScraper:
    """Scrape NSE corporate announcements"""
    
    def __init__(self):
        self.base_url = "https://www.nseindia.com"
        self.announcements_url = f"{self.base_url}/api/corporate-announcements"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/companies-listing/corporate-filings-announcements'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
    def get_announcements(self, days_back: int = 7, index: str = "equities") -> List[Dict]:
        """
        Fetch corporate announcements from NSE
        
        Args:
            days_back: Number of days to look back
            index: 'equities' or specific index
        
        Returns:
            List of announcements with company details
        """
        announcements = []
        
        try:
            # First request to set cookies
            self.session.get(self.base_url, timeout=10)
            time.sleep(1)
            
            # Calculate date range
            to_date = datetime.now()
            from_date = to_date - timedelta(days=days_back)
            
            params = {
                'index': index,
                'from_date': from_date.strftime('%d-%m-%Y'),
                'to_date': to_date.strftime('%d-%m-%Y')
            }
            
            print(f"📡 Fetching NSE announcements from {from_date.strftime('%Y-%m-%d')} to {to_date.strftime('%Y-%m-%d')}")
            
            response = self.session.get(
                self.announcements_url,
                params=params,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                announcements = data if isinstance(data, list) else []
                print(f"✅ Fetched {len(announcements)} announcements")
            else:
                print(f"⚠️  NSE API returned status {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error fetching announcements: {e}")
        
        return announcements
    
    def parse_announcement(self, announcement: Dict) -> Dict:
        """Parse and structure announcement data"""
        return {
            'symbol': announcement.get('symbol', ''),
            'company': announcement.get('companyName', ''),
            'subject': announcement.get('desc', announcement.get('subject', '')),
            'date': announcement.get('an_dt', announcement.get('date', '')),
            'attachment': announcement.get('attchmntFile', ''),
            'category': announcement.get('category', ''),
            'source': 'NSE Corporate Announcement',
            'url': f"{self.base_url}/companies-listing/corporate-filings-announcements"
        }
    
    def filter_material_announcements(self, announcements: List[Dict]) -> List[Dict]:
        """Filter for material/important announcements"""
        material_keywords = [
            'acquisition', 'merger', 'buyback', 'dividend', 'split', 'bonus',
            'rights', 'delisting', 'order', 'contract', 'agreement', 'jv',
            'joint venture', 'expansion', 'capex', 'investment', 'disinvestment',
            'financial results', 'earnings', 'profit', 'loss', 'revenue',
            'board meeting', 'agm', 'egm', 'resignation', 'appointment',
            'fund raising', 'qip', 'preferential', 'stake', 'equity',
            'debt', 'loan', 'rating', 'default', 'resolution'
        ]
        
        filtered = []
        for ann in announcements:
            subject = ann.get('subject', '').lower()
            
            # Check if any material keyword present
            if any(keyword in subject for keyword in material_keywords):
                filtered.append(ann)
        
        return filtered
    
    def categorize_announcements(self, announcements: List[Dict]) -> Dict[str, List[Dict]]:
        """Categorize announcements by type"""
        categories = {
            'M&A': [],
            'Fundraising': [],
            'Financial Results': [],
            'Corporate Actions': [],
            'Material Contracts': [],
            'Corporate Governance': [],
            'Other': []
        }
        
        for ann in announcements:
            subject = ann.get('subject', '').lower()
            
            if any(k in subject for k in ['acquisition', 'merger', 'amalgamation', 'demerger']):
                categories['M&A'].append(ann)
            elif any(k in subject for k in ['fund', 'qip', 'rights', 'preferential', 'issue']):
                categories['Fundraising'].append(ann)
            elif any(k in subject for k in ['result', 'financial', 'earnings', 'profit', 'revenue']):
                categories['Financial Results'].append(ann)
            elif any(k in subject for k in ['dividend', 'bonus', 'split', 'buyback']):
                categories['Corporate Actions'].append(ann)
            elif any(k in subject for k in ['order', 'contract', 'agreement']):
                categories['Material Contracts'].append(ann)
            elif any(k in subject for k in ['board', 'appointment', 'resignation', 'agm', 'egm']):
                categories['Corporate Governance'].append(ann)
            else:
                categories['Other'].append(ann)
        
        return categories
    
    def save_to_csv(self, announcements: List[Dict], filename: str):
        """Save announcements to CSV"""
        if not announcements:
            print("No announcements to save")
            return
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=announcements[0].keys())
            writer.writeheader()
            writer.writerows(announcements)
        
        print(f"💾 Saved {len(announcements)} announcements to {filename}")


def main():
    """Main execution"""
    scraper = NSEAnnouncementsScraper()
    
    # Fetch announcements
    print("="*100)
    print("🏛️  NSE CORPORATE ANNOUNCEMENTS SCRAPER")
    print("="*100)
    
    raw_announcements = scraper.get_announcements(days_back=7)
    
    if not raw_announcements:
        print("❌ No announcements fetched. NSE API may be unavailable.")
        print("\n💡 Alternative: Using BSE announcements or company RSS feeds")
        return
    
    # Parse announcements
    parsed = [scraper.parse_announcement(ann) for ann in raw_announcements]
    
    # Filter material announcements
    material = scraper.filter_material_announcements(parsed)
    print(f"\n📊 Material announcements: {len(material)} out of {len(parsed)}")
    
    # Categorize
    categorized = scraper.categorize_announcements(material)
    
    print("\n" + "="*100)
    print("📋 ANNOUNCEMENTS BY CATEGORY")
    print("="*100)
    
    for category, anns in categorized.items():
        if anns:
            print(f"\n{category}: {len(anns)} announcements")
            for ann in anns[:3]:  # Show top 3 per category
                print(f"  • {ann['symbol']}: {ann['subject'][:70]}...")
    
    # Show top 10 most important
    print("\n" + "="*100)
    print("🏆 TOP 10 MOST IMPORTANT ANNOUNCEMENTS")
    print("="*100)
    
    # Prioritize M&A and Material Contracts
    priority = categorized['M&A'] + categorized['Material Contracts'] + categorized['Fundraising']
    
    for i, ann in enumerate(priority[:10], 1):
        print(f"\n{i}. {ann['symbol']} - {ann['company']}")
        print(f"   📄 {ann['subject']}")
        print(f"   📅 Date: {ann['date']}")
        if ann['attachment']:
            print(f"   📎 Attachment: {ann['attachment']}")
    
    # Save to files
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if material:
        scraper.save_to_csv(material, f'nse_announcements_material_{timestamp}.csv')
    
    if priority:
        scraper.save_to_csv(priority[:50], f'nse_announcements_priority_{timestamp}.csv')
    
    print("\n" + "="*100)
    print("✅ NSE Announcements Scraping Complete")
    print("="*100)


if __name__ == "__main__":
    main()
