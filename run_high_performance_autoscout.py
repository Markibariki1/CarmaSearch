#!/usr/bin/env python3
"""
High-Performance AutoScout24 Scraper Runner
Optimized for 10,000+ vehicles per hour throughput.
"""

import os
import sys
import time
from datetime import datetime

# Add the scraper directory to path
sys.path.append('/Users/marchaupter/Desktop/C1/vehicle_data-main 2')

def main():
    """Run the high-performance AutoScout scraper"""
    print("🚀 Starting HIGH-PERFORMANCE AutoScout24 Scraper")
    print("=" * 60)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 TARGET: 10,000+ vehicles/hour")
    
    try:
        # Import and run the scraper
        from scrapper.autoscout24_complete import main as scraper_main
        
        print("✅ HIGH-PERFORMANCE OPTIMIZATIONS:")
        print("   • Thread count: 50 concurrent threads")
        print("   • Request timeout: 15 seconds (faster)")
        print("   • Retry attempts: 3 (faster recovery)")
        print("   • Request delay: 0.1 seconds (minimal)")
        print("   • Chunk size: 50 (more parallel processing)")
        print("   • Retry backoff: 0.5s exponential (faster)")
        print("   • Database pool: 5-50 connections")
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
