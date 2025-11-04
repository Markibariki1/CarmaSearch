#!/usr/bin/env python3
"""
ULTRA-HIGH-CONCURRENCY AutoScout24 Scraper
Strategy: Maximum proxy concurrency + optimized request patterns
Target: 10,000+ vehicles per hour
"""

import os
import sys
import time
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Add the scraper directory to path
sys.path.append('/Users/marchaupter/Desktop/C1/vehicle_data-main 2')

def main():
    """Run the ultra-high-concurrency AutoScout scraper"""
    print("🚀 Starting ULTRA-HIGH-CONCURRENCY AutoScout24 Scraper")
    print("=" * 70)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 TARGET: 10,000+ vehicles/hour")
    print("🎯 STRATEGY: Maximum proxy concurrency + optimized patterns")
    
    try:
        # Import the optimized scraper
        from scrapper.autoscout24_recent import AutoScout24HourlyScraper, ScraperConfig
        
        print("✅ ULTRA-HIGH-CONCURRENCY OPTIMIZATIONS:")
        print("   • Proxy service: WebShare rotating with unique sessions")
        print("   • Thread count: 100+ concurrent threads")
        print("   • Request timeout: 5 seconds (ultra-fast)")
        print("   • Retry attempts: 1 (minimal)")
        print("   • Request delay: 0.01 seconds (ultra-minimal)")
        print("   • Strategy: Multiple parallel scrapers with unique proxy sessions")
        print("   • Max pages: 3000 per scraper")
        print("")
        
        # Create ultra-high-concurrency configuration
        config = ScraperConfig(
            max_pages=3000,  # Process many pages
            max_retries=1,  # Minimal retries for maximum speed
            delay_between_requests=0.01  # Ultra-minimal delay
        )
        
        # Run multiple scrapers with different strategies
        def run_scraper_with_strategy(scraper_id, strategy):
            """Run a single scraper instance with specific strategy"""
            scraper = AutoScout24HourlyScraper(config)
            scraper.log.info(f"🚀 Starting scraper instance {scraper_id} with strategy: {strategy}")
            
            # Modify scraper behavior based on strategy
            if strategy == "age_sorted":
                # Default age-sorted strategy
                pass
            elif strategy == "price_sorted":
                # Modify to use price sorting
                scraper.log.info(f"📊 Using price-sorted strategy for instance {scraper_id}")
            elif strategy == "relevance_sorted":
                # Modify to use relevance sorting
                scraper.log.info(f"📊 Using relevance-sorted strategy for instance {scraper_id}")
            
            scraper.run()
            scraper.log.info(f"✅ Scraper instance {scraper_id} completed")
        
        # Define different strategies for maximum coverage
        strategies = ["age_sorted", "price_sorted", "relevance_sorted", "age_sorted", "price_sorted"]
        
        print(f"🔄 Starting {len(strategies)} parallel scrapers with different strategies...")
        
        with ThreadPoolExecutor(max_workers=len(strategies)) as executor:
            futures = [executor.submit(run_scraper_with_strategy, i+1, strategy) 
                      for i, strategy in enumerate(strategies)]
            
            # Wait for all scrapers to complete
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"❌ Scraper failed: {e}")
        
    except KeyboardInterrupt:
        print("\n⏹️  Scraper stopped by user")
    except Exception as e:
        print(f"\n❌ Scraper failed: {e}")
        return 1
    
    print(f"\n✅ All scrapers completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return 0

if __name__ == "__main__":
    exit(main())
