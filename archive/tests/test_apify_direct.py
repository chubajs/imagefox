#!/usr/bin/env python3
"""
Test Apify Google Images Scraper directly to find the correct input format.
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_apify_google_images():
    """Test direct Apify API call."""
    
    api_key = os.getenv('APIFY_API_KEY')
    if not api_key:
        print("❌ APIFY_API_KEY not found in environment")
        return
    
    # Try the hooli/google-images-scraper actor
    actor_id = "hooli/google-images-scraper"
    
    # Apify API endpoint - try different formats
    urls_to_try = [
        f"https://api.apify.com/v2/acts/{actor_id}/run-sync-get-dataset-items",
        f"https://api.apify.com/v2/acts/{actor_id}/runs",
        f"https://api.apify.com/v2/actor-tasks/{actor_id}/run-sync-get-dataset-items"
    ]
    
    # Try different input formats
    inputs_to_try = [
        {
            # Format 1: Simple query
            "query": "Salesforce AI artificial intelligence",
            "maxResults": 5
        },
        {
            # Format 2: search parameter
            "search": "Salesforce AI artificial intelligence",
            "maxResults": 5
        },
        {
            # Format 3: searchQuery parameter
            "searchQuery": "Salesforce AI artificial intelligence",
            "maxResults": 5
        },
        {
            # Format 4: queries parameter (like current implementation)
            "queries": "Salesforce AI artificial intelligence",
            "maxPagesPerQuery": 1,
            "resultsPerPage": 5
        }
    ]
    
    headers = {
        "Content-Type": "application/json"
    }
    
    params = {
        "token": api_key,
        "timeout": 60
    }
    
    print(f"🔍 Testing Apify Actor: {actor_id}")
    print("="*60)
    
    # Just test with the first input format across different URLs
    test_input = {
        "query": "Salesforce AI artificial intelligence",
        "maxResults": 5
    }
    
    for url in urls_to_try:
        print(f"\n📋 Testing URL: {url.split('/v2/')[-1]}")
        
        try:
            response = requests.post(
                url,
                headers=headers,
                params=params,
                json=test_input,
                timeout=30
            )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("  ✅ Success!")
                data = response.json()
                print(f"  Response type: {type(data).__name__}")
                if isinstance(data, dict):
                    print(f"  Response keys: {list(data.keys())[:5]}")
                elif isinstance(data, list):
                    print(f"  Results: {len(data)} items")
                    if len(data) > 0:
                        print(f"  Sample result keys: {list(data[0].keys())[:5]}")
                return url, test_input
            else:
                print(f"  ❌ Failed: {response.text[:200]}")
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:200]}")
    
    print("\n" + "="*60)
    print("📝 Summary: Unable to find correct input format")
    print("Consider checking:")
    print("1. Actor documentation at https://apify.com/hooli/google-images-scraper")
    print("2. Actor input schema in Apify console")
    print("3. Different actor like 'devisty/google-image-search'")

if __name__ == "__main__":
    test_apify_google_images()