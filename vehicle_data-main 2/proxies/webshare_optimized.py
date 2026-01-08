from configuration.config import Config
import random
import time
from typing import List, Dict, Any


class WEBSHARE:
    user = Config.WEBSHARE_PROXY_USER
    password = Config.WEBSHARE_PROXY_PASSWORD
    host = Config.WEBSHARE_PROXY_HOST
    port = Config.WEBSHARE_PROXY_PORT
    
    def __init__(self):
        """Initialize WebShare proxy with rotation support"""
        self.proxy_pool = []
        self.current_proxy_index = 0
        self.last_rotation_time = time.time()
        self.rotation_interval = 30  # Rotate every 30 seconds for fresh IPs
        
    def get_proxy(self, force_rotation: bool = False) -> Dict[str, str]:
        """
        Returns a proxy object with rotation support for high concurrency.
        
        Args:
            force_rotation: Force immediate proxy rotation
            
        Returns:
            Dict containing http and https proxy configurations
        """
        current_time = time.time()
        
        # Force rotation if requested or if enough time has passed
        if force_rotation or (current_time - self.last_rotation_time) > self.rotation_interval:
            self._rotate_proxy()
            self.last_rotation_time = current_time
        
        # Use rotating proxy with session ID for better distribution
        session_id = random.randint(100000, 999999)
        
        proxy = {
            'http': f"http://{self.user}-session-{session_id}:{self.password}@{self.host}:{self.port}",
            'https': f"http://{self.user}-session-{session_id}:{self.password}@{self.host}:{self.port}",
        }
        
        return proxy
    
    def _rotate_proxy(self):
        """Rotate to next proxy in pool (for future multi-proxy support)"""
        self.current_proxy_index = (self.current_proxy_index + 1) % max(1, len(self.proxy_pool))
    
    def get_multiple_proxies(self, count: int = 10) -> List[Dict[str, str]]:
        """
        Get multiple proxy configurations for parallel requests.
        
        Args:
            count: Number of proxy configurations to return
            
        Returns:
            List of proxy configurations
        """
        proxies = []
        for i in range(count):
            # Create unique session IDs for each proxy
            session_id = random.randint(100000, 999999)
            proxy = {
                'http': f"http://{self.user}-session-{session_id}:{self.password}@{self.host}:{self.port}",
                'https': f"http://{self.user}-session-{session_id}:{self.password}@{self.host}:{self.port}",
            }
            proxies.append(proxy)
            time.sleep(0.01)  # Small delay to ensure different sessions
        
        return proxies
    
    def get_high_concurrency_proxy(self, thread_id: int = 0) -> Dict[str, str]:
        """
        Get proxy optimized for high concurrency with unique session per thread.
        
        Args:
            thread_id: Unique identifier for the thread/request
            
        Returns:
            Proxy configuration optimized for concurrent use
        """
        # Create unique session based on thread ID and timestamp
        session_id = f"{thread_id}-{int(time.time() * 1000) % 100000}"
        
        proxy = {
            'http': f"http://{self.user}-session-{session_id}:{self.password}@{self.host}:{self.port}",
            'https': f"http://{self.user}-session-{session_id}:{self.password}@{self.host}:{self.port}",
        }
        
        return proxy
