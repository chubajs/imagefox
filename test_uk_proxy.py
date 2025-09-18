#!/usr/bin/env python3
"""
Test DataImpulse with UK country code specifically (seen in logs).
"""
import asyncio
import aiohttp
from proxy_config import DataImpulseConfig

async def test_uk_proxy():
    """Test aiohttp with UK DataImpulse proxy."""
    config = DataImpulseConfig()
    
    print("Testing aiohttp with UK DataImpulse proxy...")
    
    # Test sticky session with UK (same as in logs)
    try:
        session_id = config.get_next_session_id()
        proxy_url = config.get_sticky_session_url(session_id, 'uk')
        print(f"UK sticky session URL: {proxy_url}")
        
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get('https://httpbin.org/ip', 
                                 proxy=proxy_url, 
                                 headers=headers) as response:
                print(f"UK Response status: {response.status}")
                text = await response.text()
                print(f"UK Response body: {text}")
                
        # Test multiple requests in sequence to simulate our usage
        print("\nTesting multiple sequential requests...")
        for i in range(3):
            await asyncio.sleep(0.5)  # Similar to our rate limiting
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get('https://httpbin.org/headers', 
                                         proxy=proxy_url, 
                                         headers=headers) as response:
                        print(f"Request {i+1} status: {response.status}")
                        
            except Exception as e:
                print(f"Request {i+1} failed: {e}")
                
    except Exception as e:
        print(f"UK proxy test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_uk_proxy())