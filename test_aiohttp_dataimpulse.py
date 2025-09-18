#!/usr/bin/env python3
"""
Test aiohttp with DataImpulse proxy to debug NO_RAY errors.
"""
import asyncio
import aiohttp
from proxy_config import DataImpulseConfig

async def test_aiohttp_proxy():
    """Test aiohttp with DataImpulse proxy."""
    config = DataImpulseConfig()
    
    print("Testing aiohttp with DataImpulse proxy...")
    
    # Test rotating proxy
    try:
        proxy_url = config.get_rotating_http_url('us')
        print(f"Rotating proxy URL: {proxy_url}")
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get('http://httpbin.org/ip', proxy=proxy_url) as response:
                print(f"Response status: {response.status}")
                text = await response.text()
                print(f"Response body: {text}")
                
    except Exception as e:
        print(f"Rotating proxy test failed: {e}")
    
    # Test sticky session
    try:
        await asyncio.sleep(1)  # Brief delay
        session_id = config.get_next_session_id()
        proxy_url = config.get_sticky_session_url(session_id, 'us')
        print(f"\nSticky session URL: {proxy_url}")
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get('http://httpbin.org/ip', proxy=proxy_url) as response:
                print(f"Response status: {response.status}")
                text = await response.text()
                print(f"Response body: {text}")
                
    except Exception as e:
        print(f"Sticky session test failed: {e}")
    
    # Test with HTTPS URL (like our image downloads)
    try:
        await asyncio.sleep(1)
        session_id = config.get_next_session_id()
        proxy_url = config.get_sticky_session_url(session_id, 'us')
        print(f"\nTesting HTTPS with proxy: {proxy_url}")
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get('https://httpbin.org/ip', 
                                 proxy=proxy_url, 
                                 headers=headers) as response:
                print(f"HTTPS Response status: {response.status}")
                text = await response.text()
                print(f"HTTPS Response body: {text}")
                
    except Exception as e:
        print(f"HTTPS test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_aiohttp_proxy())