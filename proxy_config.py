#!/usr/bin/env python3
"""
Proxy configuration for ImageFox image downloads using DataImpulse.
Credentials extracted from telefragment project.
"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, Any
import threading
import time
import random
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DataImpulseConfig:
    """DataImpulse proxy configuration with proper thread and session management."""
    
    # DataImpulse credentials from telefragment
    username: str = "c7d6a835276a77adae72"
    password: str = "48394739639fed3c"
    gateway: str = "gw.dataimpulse.com"
    
    # Proper port configuration per DataImpulse docs
    http_rotating_port: int = 823  # For rotating IPs
    socks5_rotating_port: int = 824  # For SOCKS5 rotating
    sticky_port_range: tuple = (10000, 20000)  # For sticky sessions
    
    # Thread and rate limiting per DataImpulse best practices
    max_concurrent_threads: int = 50  # Well below 2000 limit
    request_delay: float = 0.3  # 300ms between requests to avoid rate limits
    session_ttl_minutes: int = 30  # IP rotation interval for sticky sessions
    
    # Override from environment if available
    def __post_init__(self):
        self.username = os.getenv('DATAIMPULSE_USERNAME', self.username)
        self.password = os.getenv('DATAIMPULSE_PASSWORD', self.password)
        self.gateway = os.getenv('DATAIMPULSE_GATEWAY', self.gateway)
        self.http_rotating_port = int(os.getenv('DATAIMPULSE_HTTP_PORT', str(self.http_rotating_port)))
        self.socks5_rotating_port = int(os.getenv('DATAIMPULSE_SOCKS5_PORT', str(self.socks5_rotating_port)))
        
        # Initialize thread management
        self._active_threads = 0
        self._thread_lock = threading.Lock()
        self._last_request_time = 0
        self._session_counter = 0
    
    def _wait_for_rate_limit(self):
        """Implement proper rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self._last_request_time = time.time()
    
    def acquire_thread(self) -> bool:
        """Acquire a thread slot, respecting the concurrent limit."""
        with self._thread_lock:
            if self._active_threads >= self.max_concurrent_threads:
                return False
            self._active_threads += 1
            return True
    
    def release_thread(self):
        """Release a thread slot."""
        with self._thread_lock:
            if self._active_threads > 0:
                self._active_threads -= 1
    
    def get_sticky_session_url(self, session_id: str, country: Optional[str] = None) -> str:
        """
        Get sticky HTTP proxy URL with session ID for ~30min IP persistence.
        Best practice for maintaining same IP across multiple requests.
        
        Args:
            session_id: Unique session identifier
            country: Optional country code (e.g., 'us', 'uk', 'de')
            
        Returns:
            Proxy URL with sticky session
        """
        self._wait_for_rate_limit()
        
        user_params = self.username
        if country:
            user_params += f"__cr.{country}"
        user_params += f";sessid.{session_id}"
        
        port = random.randint(self.sticky_port_range[0], self.sticky_port_range[1])
        return f"http://{user_params}:{self.password}@{self.gateway}:{port}"
    
    def get_rotating_http_url(self, country: Optional[str] = None) -> str:
        """
        Get rotating HTTP proxy URL (new IP per request).
        Uses port 823 per DataImpulse docs.
        
        Args:
            country: Optional country code (e.g., 'us', 'uk', 'de')
            
        Returns:
            Proxy URL with authentication
        """
        self._wait_for_rate_limit()
        
        user_params = self.username
        if country:
            user_params += f"__cr.{country}"
        return f"http://{user_params}:{self.password}@{self.gateway}:{self.http_rotating_port}"
    
    def get_sticky_ttl_url(self, ttl_minutes: Optional[int] = None, country: Optional[str] = None) -> str:
        """
        Get sticky HTTP proxy URL with time-based rotation.
        IP rotates every ttl_minutes (default 30min per DataImpulse best practices).
        
        Args:
            ttl_minutes: Minutes between IP rotations (default 30)
            country: Optional country code
            
        Returns:
            Proxy URL with time-based sticky session
        """
        self._wait_for_rate_limit()
        
        ttl = ttl_minutes or self.session_ttl_minutes
        user_params = self.username
        if country:
            user_params += f"__cr.{country}"
        user_params += f";sessttl.{ttl}"
        
        port = random.randint(self.sticky_port_range[0], self.sticky_port_range[1])
        return f"http://{user_params}:{self.password}@{self.gateway}:{port}"
    
    def get_next_session_id(self) -> str:
        """Generate a unique session ID for sticky sessions."""
        self._session_counter += 1
        return f"img_{int(time.time())}_{self._session_counter}"
    
    def get_thread_stats(self) -> Dict[str, Any]:
        """Get current thread usage statistics."""
        with self._thread_lock:
            return {
                'active_threads': self._active_threads,
                'max_threads': self.max_concurrent_threads,
                'utilization_pct': (self._active_threads / self.max_concurrent_threads) * 100
            }
    
    def test_credentials(self) -> bool:
        """
        Test if credentials are valid.
        
        Returns:
            True if credentials appear valid (basic check)
        """
        return bool(self.username and self.password and self.gateway)
    
    def __repr__(self) -> str:
        return f"DataImpulseConfig(gateway={self.gateway}, port={self.http_rotating_port})"


# Default instance
default_proxy = DataImpulseConfig()