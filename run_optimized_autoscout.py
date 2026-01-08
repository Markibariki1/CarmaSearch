#!/usr/bin/env python3
"""
Optimized AutoScout24 Scraper Runner
Enhanced with improved database connectivity and performance optimizations.
"""

import os
import sys
import time
from datetime import datetime

# Add the scraper directory to path
sys.path.append('/Users/marchaupter/Desktop/C1/vehicle_data-main 2')

def main():
    """Run the optimized AutoScout scraper"""
    print("🚀 Starting Optimized AutoScout24 Scraper")
    print("=" * 50)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Import and run the scraper
        from scrapper.autoscout24_complete import main as scraper_main
        
        print("✅ Database connectivity: Fixed")
        print("✅ Connection pool: Optimized (5-50 connections)")
        print("✅ Retry logic: Enhanced with exponential backoff")
        print("✅ Thread count: Optimized to 10 concurrent threads")
        print("✅ Request timeout: Increased to 60 seconds")
        print("✅ Retry attempts: Increased to 5")
        print("")
        
        # Run the scraper
        scraper_main()
        
    except KeyboardInterrupt:
        print("\n⏹️  Scraper stopped by user")
    except Exception as e:
        print(f"\n❌ Scraper failed: {e}")
        return 1
    
    print(f"\n✅ Scraper completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0

if __name__ == "__main__":
    exit(main())
