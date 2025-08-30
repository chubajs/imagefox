#!/usr/bin/env python3
"""
Unit tests for Apify client module.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apify_client import ApifyClient


class TestApifyClient(unittest.TestCase):
    """Test cases for ApifyClient class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Set test API key
        os.environ['APIFY_API_KEY'] = 'test_api_key'
        os.environ['APIFY_RATE_LIMIT'] = '10'
        os.environ['CACHE_TTL'] = '60'
        
        # Sample API responses
        self.mock_search_response = [
            {
                'searchQuery': {
                    'term': 'test query',
                    'page': 1,
                    'type': 'SEARCH'
                },
                'organicResults': [
                    {
                        'title': 'Test Image 1',
                        'url': 'https://example.com/page1',
                        'imageUrl': 'https://example.com/image1.jpg',
                        'thumbnailUrl': 'https://example.com/thumb1.jpg',
                        'description': 'Test description 1',
                        'displayedUrl': 'example.com',
                        'width': 1920,
                        'height': 1080
                    },
                    {
                        'title': 'Test Image 2',
                        'url': 'https://example.com/page2',
                        'imageUrl': 'https://example.com/image2.jpg',
                        'thumbnailUrl': 'https://example.com/thumb2.jpg',
                        'description': 'Test description 2',
                        'displayedUrl': 'example.com',
                        'width': 1280,
                        'height': 720
                    }
                ]
            }
        ]
        
        self.mock_user_response = {
            'username': 'testuser',
            'email': 'test@example.com'
        }
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test environment variables
        if 'APIFY_API_KEY' in os.environ:
            del os.environ['APIFY_API_KEY']
    
    def test_initialization_with_api_key(self):
        """Test client initialization with API key."""
        client = ApifyClient(api_key='test_key')
        self.assertEqual(client.api_key, 'test_key')
        self.assertEqual(client.rate_limit, 10)
        self.assertEqual(client.cache_ttl, 60)
    
    def test_initialization_from_environment(self):
        """Test client initialization from environment variable."""
        client = ApifyClient()
        self.assertEqual(client.api_key, 'test_api_key')
    
    def test_initialization_without_api_key(self):
        """Test client initialization fails without API key."""
        del os.environ['APIFY_API_KEY']
        with self.assertRaises(ValueError) as context:
            ApifyClient()
        self.assertIn('APIFY_API_KEY', str(context.exception))
    
    @patch('apify_client.requests.Session')
    def test_validate_api_key_success(self, mock_session_class):
        """Test successful API key validation."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_user_response
        mock_session.get.return_value = mock_response
        
        # Test
        client = ApifyClient()
        result = client.validate_api_key()
        
        # Assertions
        self.assertTrue(result)
        mock_session.get.assert_called_once()
    
    @patch('apify_client.requests.Session')
    def test_validate_api_key_failure(self, mock_session_class):
        """Test failed API key validation."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_session.get.return_value = mock_response
        
        # Test
        client = ApifyClient()
        result = client.validate_api_key()
        
        # Assertions
        self.assertFalse(result)
    
    @patch('apify_client.requests.Session')
    def test_search_images_success(self, mock_session_class):
        """Test successful image search."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_search_response
        mock_session.post.return_value = mock_response
        
        # Test
        client = ApifyClient()
        results = client.search_images('test query', limit=2)
        
        # Assertions
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['title'], 'Test Image 1')
        self.assertEqual(results[0]['image_url'], 'https://example.com/image1.jpg')
        self.assertEqual(results[1]['title'], 'Test Image 2')
        mock_session.post.assert_called_once()
    
    @patch('apify_client.requests.Session')
    def test_search_images_with_cache(self, mock_session_class):
        """Test image search with caching."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_search_response
        mock_session.post.return_value = mock_response
        
        # Test
        client = ApifyClient()
        
        # First search - should hit API
        results1 = client.search_images('test query', limit=2)
        self.assertEqual(len(results1), 2)
        self.assertEqual(mock_session.post.call_count, 1)
        
        # Second search - should use cache
        results2 = client.search_images('test query', limit=2)
        self.assertEqual(len(results2), 2)
        self.assertEqual(mock_session.post.call_count, 1)  # Still 1, not 2
        
        # Different query - should hit API again
        results3 = client.search_images('different query', limit=2)
        self.assertEqual(mock_session.post.call_count, 2)
    
    @patch('apify_client.requests.Session')
    def test_search_images_rate_limit_error(self, mock_session_class):
        """Test handling of rate limit errors."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = Exception("Rate limit exceeded")
        mock_session.post.return_value = mock_response
        
        # Test
        client = ApifyClient()
        with self.assertRaises(Exception) as context:
            client.search_images('test query')
        self.assertIn('Rate limit exceeded', str(context.exception))
    
    @patch('apify_client.requests.Session')
    def test_search_images_insufficient_credits(self, mock_session_class):
        """Test handling of insufficient credits error."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 402
        mock_session.post.return_value = mock_response
        
        # Test
        client = ApifyClient()
        with self.assertRaises(Exception) as context:
            client.search_images('test query')
        self.assertIn('Insufficient Apify credits', str(context.exception))
    
    def test_parse_search_results(self):
        """Test parsing of search results."""
        client = ApifyClient()
        results = client._parse_search_results(self.mock_search_response, limit=10)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['image_url'], 'https://example.com/image1.jpg')
        self.assertEqual(results[0]['title'], 'Test Image 1')
        self.assertEqual(results[0]['width'], 1920)
        self.assertEqual(results[0]['height'], 1080)
        self.assertIn('timestamp', results[0])
    
    def test_parse_search_results_with_limit(self):
        """Test parsing of search results with limit."""
        client = ApifyClient()
        results = client._parse_search_results(self.mock_search_response, limit=1)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Test Image 1')
    
    def test_parse_search_results_duplicate_urls(self):
        """Test that duplicate URLs are filtered out."""
        # Create response with duplicate
        duplicate_response = [
            {
                'organicResults': [
                    {
                        'imageUrl': 'https://example.com/image1.jpg',
                        'title': 'Image 1'
                    },
                    {
                        'imageUrl': 'https://example.com/image1.jpg',  # Duplicate
                        'title': 'Image 1 Duplicate'
                    },
                    {
                        'imageUrl': 'https://example.com/image2.jpg',
                        'title': 'Image 2'
                    }
                ]
            }
        ]
        
        client = ApifyClient()
        results = client._parse_search_results(duplicate_response, limit=10)
        
        # Should only have 2 results (duplicate filtered)
        self.assertEqual(len(results), 2)
        urls = [r['image_url'] for r in results]
        self.assertEqual(len(urls), len(set(urls)))  # No duplicates
    
    def test_cache_key_generation(self):
        """Test cache key generation."""
        client = ApifyClient()
        
        # Same parameters should generate same key
        key1 = client._get_cache_key('test query', limit=10, safe_search=True)
        key2 = client._get_cache_key('test query', limit=10, safe_search=True)
        self.assertEqual(key1, key2)
        
        # Different parameters should generate different keys
        key3 = client._get_cache_key('test query', limit=20, safe_search=True)
        self.assertNotEqual(key1, key3)
        
        key4 = client._get_cache_key('different query', limit=10, safe_search=True)
        self.assertNotEqual(key1, key4)
    
    def test_cache_operations(self):
        """Test cache save and retrieve operations."""
        client = ApifyClient()
        test_data = {'test': 'data'}
        cache_key = 'test_key'
        
        # Save to cache
        client._save_to_cache(cache_key, test_data)
        self.assertIn(cache_key, client.cache)
        
        # Retrieve from cache
        retrieved = client._get_from_cache(cache_key)
        self.assertEqual(retrieved, test_data)
        
        # Test expired cache
        client.cache[cache_key]['expires'] = datetime.now() - timedelta(seconds=1)
        retrieved_expired = client._get_from_cache(cache_key)
        self.assertIsNone(retrieved_expired)
    
    @patch('apify_client.time.sleep')
    def test_rate_limiting(self, mock_sleep):
        """Test rate limiting enforcement."""
        client = ApifyClient()
        client.rate_limit = 2  # Set low limit for testing
        
        # Add requests to simulate hitting rate limit
        current_time = 1000.0
        with patch('apify_client.time.time', return_value=current_time):
            client.requests_per_minute = [current_time - 30, current_time - 20]
            client._enforce_rate_limit()
            
            # Should sleep since we're at the limit
            mock_sleep.assert_called_once()
            sleep_time = mock_sleep.call_args[0][0]
            self.assertGreater(sleep_time, 0)
    
    def test_clear_cache(self):
        """Test cache clearing."""
        client = ApifyClient()
        client.cache = {'key1': 'data1', 'key2': 'data2'}
        
        client.clear_cache()
        self.assertEqual(len(client.cache), 0)
    
    @patch('apify_client.requests.Session')
    def test_get_usage_stats(self, mock_session_class):
        """Test getting usage statistics."""
        # Setup mock
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'usage': 'stats'}
        mock_session.get.return_value = mock_response
        
        # Test
        client = ApifyClient()
        stats = client.get_usage_stats()
        
        # Assertions
        self.assertEqual(stats, {'usage': 'stats'})
        mock_session.get.assert_called()


if __name__ == '__main__':
    unittest.main()