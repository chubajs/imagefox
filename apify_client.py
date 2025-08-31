#!/usr/bin/env python3
"""
Apify Google Images Scraper API client for ImageFox.

This module provides a robust client for interacting with Apify's
Google Images Scraper API to perform image searches.
"""

import os
import time
import hashlib
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import sentry_sdk
from sentry_sdk import capture_exception

logger = logging.getLogger(__name__)


class ApifyClient:
    """Client for Apify Google Images Scraper API."""
    
    DEFAULT_ACTOR_ID = "hooli~google-images-scraper"
    API_BASE_URL = "https://api.apify.com/v2"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Apify client.
        
        Args:
            api_key: Apify API key. If not provided, reads from environment.
        
        Raises:
            ValueError: If API key is not provided or found in environment.
        """
        self.api_key = api_key or os.getenv('APIFY_API_KEY')
        if not self.api_key:
            raise ValueError("APIFY_API_KEY not provided or found in environment")
        
        # Rate limiting configuration
        self.rate_limit = int(os.getenv('APIFY_RATE_LIMIT', '100'))
        self.requests_per_minute = []
        
        # Cache configuration
        self.cache_ttl = int(os.getenv('CACHE_TTL', '3600'))  # 1 hour default
        self.cache = {}
        
        # Setup session with retry strategy
        self.session = self._create_session()
        
        logger.info("Apify client initialized")
    
    def _create_session(self) -> requests.Session:
        """Create HTTP session with retry strategy."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=int(os.getenv('RETRY_ATTEMPTS', '3')),
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        return session
    
    def _enforce_rate_limit(self):
        """Enforce rate limiting to prevent API throttling."""
        current_time = time.time()
        minute_ago = current_time - 60
        
        # Remove requests older than 1 minute
        self.requests_per_minute = [
            req_time for req_time in self.requests_per_minute 
            if req_time > minute_ago
        ]
        
        # Check if we've hit the rate limit
        if len(self.requests_per_minute) >= self.rate_limit:
            # Calculate sleep time
            oldest_request = min(self.requests_per_minute)
            sleep_time = 60 - (current_time - oldest_request) + 0.1
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
        
        # Record this request
        self.requests_per_minute.append(current_time)
    
    def _get_cache_key(self, query: str, **params) -> str:
        """Generate cache key for search results."""
        cache_data = {'query': query, **params}
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Retrieve results from cache if valid."""
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() < cached_data['expires']:
                logger.info(f"Cache hit for key {cache_key}")
                return cached_data['data']
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """Save results to cache."""
        self.cache[cache_key] = {
            'data': data,
            'expires': datetime.now() + timedelta(seconds=self.cache_ttl)
        }
        logger.info(f"Cached results for key {cache_key}")
    
    def validate_api_key(self) -> bool:
        """
        Test API connectivity and validate API key.
        
        Returns:
            True if API key is valid, False otherwise.
        """
        try:
            url = f"{self.API_BASE_URL}/users/me"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"API key validated for user: {user_data.get('username')}")
                return True
            else:
                logger.error(f"API key validation failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            capture_exception(e)
            return False
    
    def search_images(
        self,
        query: str,
        limit: int = 20,
        safe_search: bool = True,
        country_code: str = "US",
        language_code: str = "en",
        use_cache: bool = True,
        **kwargs
    ) -> List[Dict]:
        """
        Search for images using Apify Google Images Scraper.
        
        Args:
            query: Search query string
            limit: Maximum number of results to return
            safe_search: Enable safe search filtering
            country_code: Country code for search localization
            language_code: Language code for search
            use_cache: Whether to use cached results
            **kwargs: Additional parameters for the API
        
        Returns:
            List of image results with metadata
        
        Raises:
            requests.RequestException: If API request fails
        """
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(
                query, limit=limit, safe_search=safe_search,
                country_code=country_code, language_code=language_code
            )
            cached_results = self._get_from_cache(cache_key)
            if cached_results:
                return cached_results
        
        # Enforce rate limiting
        self._enforce_rate_limit()
        
        # Prepare request - using correct endpoint for hooli/google-images-scraper
        actor_url = f"{self.API_BASE_URL}/acts/{self.DEFAULT_ACTOR_ID}/runs"
        
        # Build payload for hooli/google-images-scraper
        payload = {
            "queries": [query],  # Actor expects array of queries
            "maxResults": limit,
            "countryCode": country_code,
            "languageCode": language_code,
            "safeSearch": "moderate" if safe_search else "off",
            **kwargs
        }
        
        try:
            logger.info(f"Searching for images: '{query}' (limit={limit})")
            
            # Make API request with token
            response = self.session.post(
                actor_url,
                json=payload,
                params={"token": self.api_key},
                timeout=int(os.getenv('REQUEST_TIMEOUT', '60'))
            )
            
            # Handle response
            if response.status_code in [200, 201]:
                # For /runs endpoint, we need to wait for completion and get dataset
                run_data = response.json()
                run_id = run_data.get('data', {}).get('id')
                
                if run_id:
                    # Wait for run to complete and get dataset
                    dataset_url = f"{self.API_BASE_URL}/actor-runs/{run_id}/dataset/items"
                    
                    # Poll for completion (max 60 seconds)
                    import time
                    for _ in range(30):  # 30 * 2 = 60 seconds max
                        time.sleep(2)
                        status_response = self.session.get(
                            f"{self.API_BASE_URL}/actor-runs/{run_id}",
                            params={"token": self.api_key}
                        )
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            if status_data.get('data', {}).get('status') in ['SUCCEEDED', 'FAILED', 'ABORTED']:
                                break
                    
                    # Get dataset items
                    dataset_response = self.session.get(
                        dataset_url,
                        params={"token": self.api_key}
                    )
                    
                    if dataset_response.status_code == 200:
                        data = dataset_response.json()
                        logger.info(f"Dataset response type: {type(data)}, keys: {list(data.keys()) if isinstance(data, dict) else 'list'}")
                        if isinstance(data, list) and len(data) > 0:
                            logger.info(f"First item keys: {list(data[0].keys())}")
                            logger.info(f"First item sample: {json.dumps(data[0], indent=2)[:500]}")
                        results = self._parse_search_results(data, limit)
                        
                        # Cache results
                        if use_cache:
                            self._save_to_cache(cache_key, results)
                        
                        logger.info(f"Found {len(results)} images for query '{query}'")
                        return results
                    else:
                        raise Exception(f"Failed to get dataset: {dataset_response.text}")
                else:
                    raise Exception(f"No run ID in response: {run_data}")
                    
            elif response.status_code == 402:
                raise Exception("Insufficient Apify credits")
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded")
            else:
                response.raise_for_status()
                
        except requests.RequestException as e:
            logger.error(f"Error searching images: {e}")
            capture_exception(e)
            raise
    
    def _parse_search_results(self, data: Union[List[Dict], Dict], limit: int) -> List[Dict]:
        """
        Parse and format search results from hooli/google-images-scraper response.
        
        Args:
            data: Raw response data from Apify
            limit: Maximum number of results to return
        
        Returns:
            Formatted list of image results
        """
        results = []
        seen_urls = set()
        
        # Handle different response formats
        items = data if isinstance(data, list) else data.get('items', [])
        
        for item in items:
            # hooli/google-images-scraper actual format
            image_url = item.get('imageUrl')
            
            if not image_url or image_url in seen_urls:
                continue
            
            seen_urls.add(image_url)
            
            # Format result with actual field names from hooli/google-images-scraper
            formatted_result = {
                'image_url': image_url,
                'thumbnail_url': item.get('thumbnailUrl', image_url),
                'source_url': item.get('contentUrl', ''),  # contentUrl is the source page
                'title': item.get('title', ''),
                'description': item.get('description', ''),
                'displayed_url': item.get('origin', ''),  # origin is the domain
                'width': item.get('imageWidth', 0),
                'height': item.get('imageHeight', 0),
                'search_query': item.get('query', ''),
                'timestamp': datetime.now().isoformat()
            }
            
            results.append(formatted_result)
            
            # Check limit
            if len(results) >= limit:
                return results
        
        return results
    
    def get_actor_runs(self, limit: int = 10) -> List[Dict]:
        """
        Get recent actor runs for monitoring.
        
        Args:
            limit: Number of runs to retrieve
        
        Returns:
            List of recent actor runs with status
        """
        try:
            url = f"{self.API_BASE_URL}/actor-runs"
            params = {'limit': limit}
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('items', [])
            else:
                logger.error(f"Failed to get actor runs: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting actor runs: {e}")
            capture_exception(e)
            return []
    
    def clear_cache(self):
        """Clear all cached search results."""
        self.cache.clear()
        logger.info("Cache cleared")
    
    def get_usage_stats(self) -> Dict:
        """
        Get API usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        try:
            url = f"{self.API_BASE_URL}/users/me/usage"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get usage stats: {response.status_code}")
                return {}
                
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            capture_exception(e)
            return {}


def main():
    """Test the Apify client."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Initialize client
        client = ApifyClient()
        
        # Validate API key
        if not client.validate_api_key():
            print("API key validation failed")
            return 1
        
        # Test search
        results = client.search_images("modern office space", limit=5)
        
        # Display results
        print(f"\nFound {len(results)} images:")
        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   URL: {result['image_url'][:80]}...")
            print(f"   Source: {result['source_url'][:80]}...")
        
        # Get usage stats
        stats = client.get_usage_stats()
        if stats:
            print(f"\nAPI Usage: {json.dumps(stats, indent=2)}")
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())