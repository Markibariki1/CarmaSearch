#!/usr/bin/env python3
"""
NEW Vehicle Discovery Scraper
Strategy: Focus on finding NEW vehicles by sorting by age and processing recent listings
Target: 10,000+ vehicles per hour
"""

import os
import sys
import time
from datetime import datetime

# Add the scraper directory to path
sys.path.append('/Users/marchaupter/Desktop/C1/vehicle_data-main 2')

def main():
    """Run the NEW vehicle discovery scraper"""
    print("🚀 Starting NEW Vehicle Discovery Scraper")
    print("=" * 50)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 TARGET: 10,000+ vehicles/hour")
    print("🎯 STRATEGY: Find NEW vehicles by sorting by age")
    
    try:
        # Import the recent scraper which sorts by age
        from scrapper.autoscout24_recent import AutoScout24HourlyScraper, ScraperConfig
        
        print("✅ NEW VEHICLE DISCOVERY OPTIMIZATIONS:")
        print("   • Thread count: 50 concurrent threads")
        print("   • Request timeout: 10 seconds")
        print("   • Retry attempts: 2 (minimal)")
        print("   • Request delay: 0.05 seconds (minimal)")
        print("   • Strategy: Sort by AGE to find newest listings")
        print("   • Max pages: 1000 (aggressive)")
        print("")
        
        # Create configuration optimized for finding new vehicles
        config = ScraperConfig(
            max_pages=1000,  # Process many pages to find new vehicles
            max_retries=2,  # Minimal retries for speed
            delay_between_requests=0.05  # Ultra-minimal delay
        )
        
        # Initialize scraper
        scraper = AutoScout24HourlyScraper(config)
        
        # Run the scraper
        scraper.run()
        
    except KeyboardInterrupt:
        print("\n⏹️  Scraper stopped by user")
    except Exception as e:
        print(f"\n❌ Scraper failed: {e}")
        return 1
    
    print(f"\n✅ Scraper completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0

if __name__ == "__main__":
    exit(main())
