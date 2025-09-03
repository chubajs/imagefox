#!/usr/bin/env python3
"""
Proxy configuration for ImageFox image downloads using DataImpulse.
Credentials extracted from telefragment project.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DataImpulseConfig:
    """DataImpulse proxy configuration for ImageFox."""
    
    # DataImpulse credentials from telefragment
    username: str = "c7d6a835276a77adae72"
    password: str = "48394739639fed3c"
    gateway: str = "gw.dataimpulse.com"
    http_port: int = 823
    socks5_port: int = 824
    sticky_port_range: tuple = (10000, 20000)
    
    # Override from environment if available
    def __post_init__(self):
        self.username = os.getenv('DATAIMPULSE_USERNAME', self.username)
        self.password = os.getenv('DATAIMPULSE_PASSWORD', self.password)
        self.gateway = os.getenv('DATAIMPULSE_GATEWAY', self.gateway)
        self.http_port = int(os.getenv('DATAIMPULSE_HTTP_PORT', str(self.http_port)))
        self.socks5_port = int(os.getenv('DATAIMPULSE_SOCKS5_PORT', str(self.socks5_port)))
    
    def get_rotating_http_url(self, country: Optional[str] = None) -> str:
        """
        Get rotating HTTP proxy URL.
        Each request gets a new IP address.
        
        Args:
            country: Optional country code (e.g., 'us', 'uk', 'de')
            
        Returns:
            Proxy URL with authentication
        """
        if country:
            username = f"{self.username}__cr.{country}"
        else:
            username = self.username
        return f"http://{username}:{self.password}@{self.gateway}:{self.http_port}"
    
    def get_sticky_http_url(self, session_id: Optional[int] = None, port: Optional[int] = None) -> str:
        """
        Get sticky HTTP proxy URL (same IP for session).
        Useful for maintaining session across multiple requests.
        
        Args:
            session_id: Optional session ID for sticky session
            port: Optional specific port (10000-20000)
            
        Returns:
            Proxy URL with sticky session
        """
        if port is None:
            port = self.sticky_port_range[0]  # Default to 10000
            
        username = self.username
        if session_id:
            username = f"{self.username}__sessid.{session_id}"
        return f"http://{username}:{self.password}@{self.gateway}:{port}"
    
    def get_socks5_url(self, rotating: bool = True) -> str:
        """
        Get SOCKS5 proxy URL.
        
        Args:
            rotating: Whether to use rotating proxy (default True)
            
        Returns:
            SOCKS5 proxy URL
        """
        port = self.socks5_port if rotating else 10001
        return f"socks5://{self.username}:{self.password}@{self.gateway}:{port}"
    
    def test_credentials(self) -> bool:
        """
        Test if credentials are valid.
        
        Returns:
            True if credentials appear valid (basic check)
        """
        return bool(self.username and self.password and self.gateway)
    
    def __repr__(self) -> str:
        return f"DataImpulseConfig(gateway={self.gateway}, port={self.http_port})"


# Default instance
default_proxy = DataImpulseConfig()