#!/usr/bin/env python3
"""
Continuous Optimized AutoScout24 Scraper
=========================================

This script runs a continuous scraper with optimized proxy usage
to maintain 10,000+ vehicles/hour throughput.

Strategy:
- Multiple parallel scrapers with different search strategies
- Optimized proxy rotation for maximum concurrency
- Continuous monitoring and adjustment
- Focus on finding NEW vehicles, not duplicates
"""

import os
import sys
import time
import threading
import logging
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List, Dict, Any

# Add the project root to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'vehicle_data-main 2'))

from scrapper.autoscout24_recent import AutoScout24HourlyScraper
from proxies.webshare_optimized import WEBSHARE
from database.db import VehicleDatabase
from logger.logger_setup import LoggerSetup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/continuous_scraper.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class ScraperConfig:
    """Configuration for continuous scraping"""
    max_pages: int = 1000  # Pages per scraper instance
    max_retries: int = 1   # Minimal retries for speed
    delay_between_requests: float = 0.01  # Ultra-minimal delay
    thread_count: int = 50  # Threads per scraper instance
    timeout: int = 5        # Request timeout in seconds

class ContinuousScraper:
    """Continuous scraper with optimized proxy usage"""
    
    def __init__(self):
        self.config = ScraperConfig()
        self.webshare = WEBSHARE()
        self.db = VehicleDatabase(logger=logger)
        self.running = False
        self.scrapers = []
        
    def create_scraper_instance(self, instance_id: int, strategy: str) -> AutoScout24HourlyScraper:
        """Create a scraper instance with specific strategy"""
        scraper = AutoScout24HourlyScraper()
        
        # Configure scraper
        scraper.config.max_pages = self.config.max_pages
        scraper.config.max_retries = self.config.max_retries
        scraper.config.delay_between_requests = self.config.delay_between_requests
        
        # Set unique thread ID for proxy session
        scraper.thread_id = instance_id
        
        logger.info(f"Created scraper instance {instance_id} with strategy: {strategy}")
        return scraper
    
    def run_scraper_instance(self, instance_id: int, strategy: str) -> Dict[str, Any]:
        """Run a single scraper instance"""
        try:
            scraper = self.create_scraper_instance(instance_id, strategy)
            
            logger.info(f"🚀 Starting scraper instance {instance_id} with strategy: {strategy}")
            start_time = time.time()
            
            # Run the scraper
            result = scraper.run()
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(f"✅ Scraper instance {instance_id} completed in {duration:.2f} seconds")
            
            return {
                'instance_id': instance_id,
                'strategy': strategy,
                'duration': duration,
                'result': result,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"❌ Scraper instance {instance_id} failed: {e}")
            return {
                'instance_id': instance_id,
                'strategy': strategy,
                'error': str(e),
                'success': False
            }
    
    def run_parallel_scrapers(self, num_instances: int = 5) -> List[Dict[str, Any]]:
        """Run multiple scraper instances in parallel"""
        strategies = [
            "recent_listings",
            "price_range_0_20k",
            "price_range_20k_40k", 
            "price_range_40k_60k",
            "price_range_60k_100k"
        ]
        
        results = []
        
        with ThreadPoolExecutor(max_workers=num_instances) as executor:
            # Submit all scraper instances
            futures = []
            for i in range(num_instances):
                strategy = strategies[i % len(strategies)]
                future = executor.submit(self.run_scraper_instance, i + 1, strategy)
                futures.append(future)
            
            # Collect results as they complete
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                if result['success']:
                    logger.info(f"✅ Instance {result['instance_id']} completed successfully")
                else:
                    logger.error(f"❌ Instance {result['instance_id']} failed: {result['error']}")
        
        return results
    
    def monitor_performance(self) -> Dict[str, Any]:
        """Monitor scraper performance"""
        try:
            # Get recent vehicle count
            conn = self.db.get_connection()
            cursor = conn.cursor()
            
            # Count vehicles from last hour
            one_hour_ago = datetime.now() - timedelta(hours=1)
            cursor.execute('''
                SELECT COUNT(*) 
                FROM vehicle_marketplace.vehicle_data 
                WHERE created_at >= %s AND listing_url LIKE '%autoscout24%'
            ''', (one_hour_ago,))
            
            recent_count = cursor.fetchone()[0]
            
            # Count vehicles from last 30 minutes
            thirty_min_ago = datetime.now() - timedelta(minutes=30)
            cursor.execute('''
                SELECT COUNT(*) 
                FROM vehicle_marketplace.vehicle_data 
                WHERE created_at >= %s AND listing_url LIKE '%autoscout24%'
            ''', (thirty_min_ago,))
            
            very_recent_count = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            return {
                'last_hour': recent_count,
                'last_30_min': very_recent_count,
                'rate_per_hour': recent_count,
                'rate_per_minute': very_recent_count / 30 if very_recent_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error monitoring performance: {e}")
            return {'error': str(e)}
    
    def run_continuous(self, cycle_duration: int = 300):  # 5 minutes per cycle
        """Run continuous scraping with performance monitoring"""
        logger.info("🚀 Starting CONTINUOUS OPTIMIZED AutoScout24 Scraper")
        logger.info("=" * 60)
        logger.info(f"⏰ Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"🎯 TARGET: 10,000+ vehicles/hour")
        logger.info(f"🎯 STRATEGY: Continuous parallel scraping with optimized proxy")
        logger.info(f"✅ CONTINUOUS OPTIMIZATION SETTINGS:")
        logger.info(f"   • Proxy service: WebShare rotating with unique sessions")
        logger.info(f"   • Thread count: {self.config.thread_count} per instance")
        logger.info(f"   • Request timeout: {self.config.timeout} seconds")
        logger.info(f"   • Retry attempts: {self.config.max_retries}")
        logger.info(f"   • Request delay: {self.config.delay_between_requests} seconds")
        logger.info(f"   • Cycle duration: {cycle_duration} seconds")
        logger.info(f"   • Strategy: Multiple parallel scrapers with different approaches")
        logger.info("=" * 60)
        
        self.running = True
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                cycle_start = time.time()
                
                logger.info(f"🔄 Starting cycle {cycle_count}")
                
                # Run parallel scrapers
                results = self.run_parallel_scrapers(num_instances=5)
                
                # Monitor performance
                performance = self.monitor_performance()
                
                cycle_end = time.time()
                cycle_duration_actual = cycle_end - cycle_start
                
                # Log cycle results
                logger.info(f"📊 Cycle {cycle_count} Results:")
                logger.info(f"   • Duration: {cycle_duration_actual:.2f} seconds")
                logger.info(f"   • Success rate: {sum(1 for r in results if r['success'])}/{len(results)}")
                logger.info(f"   • Last hour: {performance.get('last_hour', 0)} vehicles")
                logger.info(f"   • Last 30 min: {performance.get('last_30_min', 0)} vehicles")
                logger.info(f"   • Rate: {performance.get('rate_per_hour', 0)} vehicles/hour")
                
                # Check if we need to adjust strategy
                if performance.get('rate_per_hour', 0) < 1000:
                    logger.warning("⚠️  Low performance detected - adjusting strategy")
                    # Increase concurrency
                    self.config.thread_count = min(self.config.thread_count + 10, 100)
                    self.config.delay_between_requests = max(self.config.delay_between_requests - 0.001, 0.001)
                elif performance.get('rate_per_hour', 0) > 15000:
                    logger.info("✅ High performance detected - maintaining current settings")
                
                # Wait before next cycle
                if cycle_duration_actual < cycle_duration:
                    wait_time = cycle_duration - cycle_duration_actual
                    logger.info(f"⏳ Waiting {wait_time:.2f} seconds before next cycle...")
                    time.sleep(wait_time)
                
        except KeyboardInterrupt:
            logger.info("🛑 Stopping continuous scraper...")
            self.running = False
        except Exception as e:
            logger.error(f"❌ Continuous scraper error: {e}")
            self.running = False
        
        logger.info("✅ Continuous scraper stopped")

def main():
    """Main function"""
    scraper = ContinuousScraper()
    
    try:
        scraper.run_continuous(cycle_duration=300)  # 5 minutes per cycle
    except KeyboardInterrupt:
        logger.info("🛑 Scraper stopped by user")
    except Exception as e:
        logger.error(f"❌ Scraper failed: {e}")

if __name__ == "__main__":
    main()
