#!/usr/bin/env python3
"""
Ultra-High-Performance AutoScout24 Scraper
Strategy: Focus on finding NEW vehicles using multiple search approaches
Target: 10,000+ vehicles per hour
"""

import os
import sys
import time
from datetime import datetime
import random

# Add the scraper directory to path
sys.path.append('/Users/marchaupter/Desktop/C1/vehicle_data-main 2')

def main():
    """Run the ultra-high-performance AutoScout scraper"""
    print("🚀 Starting ULTRA-HIGH-PERFORMANCE AutoScout24 Scraper")
    print("=" * 70)
    print(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 TARGET: 10,000+ vehicles/hour")
    print("🎯 STRATEGY: Find NEW vehicles using multiple approaches")
    
    try:
        # Import the scraper
        from scrapper.autoscout24_complete import AutoScout24Scraper, ScraperConfig
        
        print("✅ ULTRA-HIGH-PERFORMANCE OPTIMIZATIONS:")
        print("   • Thread count: 50 concurrent threads")
        print("   • Request timeout: 10 seconds (ultra-fast)")
        print("   • Retry attempts: 2 (minimal)")
        print("   • Request delay: 0.05 seconds (minimal)")
        print("   • Chunk size: 25 (maximum parallel processing)")
        print("   • Strategy: Multiple search approaches for NEW vehicles")
        print("")
        
        # Create ultra-high-performance configuration
        config = ScraperConfig(
            price_start=0,
            price_end=100000,
            initial_chunk_size=25,  # Smaller chunks for more parallel processing
            max_retries=2,  # Minimal retries for speed
            delay_between_requests=0.05,  # Ultra-minimal delay
            max_results_per_range=4000
        )
        
        # Initialize scraper
        scraper = AutoScout24Scraper(config)
        
        # Override the run method to use multiple strategies
        original_run = scraper.run
        
        def ultra_high_performance_run():
            """Ultra-high-performance run with multiple strategies"""
            scraper.log.info("🚀 Starting ULTRA-HIGH-PERFORMANCE scraping...")
            scraper.log.info("🎯 Strategy: Multiple approaches to find NEW vehicles")
            
            start_time = time.time()
            
            # Strategy 1: Process price ranges with smaller chunks for more coverage
            scraper.log.info("📊 Strategy 1: High-frequency price range scanning")
            price_ranges = []
            
            # Generate more price ranges with smaller chunks
            for start in range(0, 100000, 25):  # Every 25 euros
                end = min(start + 25, 100000)
                price_ranges.append((start, end))
            
            # Shuffle ranges to avoid patterns
            random.shuffle(price_ranges)
            
            # Process ranges in parallel batches
            batch_size = 50  # Process 50 ranges simultaneously
            for i in range(0, len(price_ranges), batch_size):
                batch = price_ranges[i:i + batch_size]
                scraper.log.info(f"🔄 Processing batch {i//batch_size + 1}/{(len(price_ranges) + batch_size - 1)//batch_size}")
                
                # Process batch in parallel
                with scraper.thread_limit:
                    # Use ThreadPoolExecutor for the batch
                    from concurrent.futures import ThreadPoolExecutor
                    with ThreadPoolExecutor(max_workers=50) as executor:
                        futures = [executor.submit(scraper.process_price_range, price_range) for price_range in batch]
                        for future in futures:
                            try:
                                future.result(timeout=300)  # 5 minute timeout per range
                            except Exception as e:
                                scraper.log.error(f"❌ Range processing failed: {e}")
                
                # Brief pause between batches
                time.sleep(0.1)
            
            # Log final stats
            elapsed_time = time.time() - start_time
            scraper.log.info(f"⚡ Ultra-high-performance run completed in {elapsed_time:.2f} seconds")
            scraper.log.info(f"📊 Total listings processed: {scraper.stats.total_listings}")
            if elapsed_time > 0:
                scraper.log.info(f"⚡ Rate: {scraper.stats.total_listings / elapsed_time:.2f} listings/sec")
                scraper.log.info(f"⚡ Hourly rate: {scraper.stats.total_listings / elapsed_time * 3600:.0f} listings/hour")
        
        # Replace the run method
        scraper.run = ultra_high_performance_run
        
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
