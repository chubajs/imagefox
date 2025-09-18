#!/usr/bin/env python3
"""
Quick test to verify DataImpulse proxy configuration.
"""
import requests
import time
from proxy_config import DataImpulseConfig

def test_proxy():
    """Test DataImpulse proxy with simple HTTP request."""
    config = DataImpulseConfig()
    
    print(f"Testing DataImpulse proxy...")
    print(f"Username: {config.username}")
    print(f"Gateway: {config.gateway}")
    print(f"HTTP Port: {config.http_rotating_port}")
    
    # Test rotating proxy
    try:
        proxy_url = config.get_rotating_http_url('us')
        print(f"Rotating proxy URL: {proxy_url}")
        
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        # Simple IP check
        print("Testing with rotating proxy...")
        response = requests.get('http://httpbin.org/ip', 
                               proxies=proxies, 
                               timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
    except Exception as e:
        print(f"Rotating proxy test failed: {e}")
    
    # Test sticky session
    try:
        time.sleep(1)  # Brief delay
        session_id = config.get_next_session_id()
        proxy_url = config.get_sticky_session_url(session_id, 'us')
        print(f"\nSticky session URL: {proxy_url}")
        
        proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        
        print("Testing with sticky session...")
        response = requests.get('http://httpbin.org/ip', 
                               proxies=proxies, 
                               timeout=30)
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.text}")
        
    except Exception as e:
        print(f"Sticky session test failed: {e}")

if __name__ == "__main__":
    test_proxy()