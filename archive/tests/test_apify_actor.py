#!/usr/bin/env python3
"""
Test different Apify actor endpoint formats for hooli/google-images-scraper.
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('APIFY_API_KEY')
if not api_key:
    print("❌ No APIFY_API_KEY found")
    exit(1)

print(f"✓ API Key found: {api_key[:10]}...")

# Test different actor ID formats and endpoints
tests = [
    {
        "name": "Direct actor ID with runs",
        "url": "https://api.apify.com/v2/acts/hooli~google-images-scraper/runs",
        "actor_id": "hooli~google-images-scraper"
    },
    {
        "name": "Slash format with runs", 
        "url": "https://api.apify.com/v2/acts/hooli/google-images-scraper/runs",
        "actor_id": "hooli/google-images-scraper"
    },
    {
        "name": "Actor ID only",
        "url": "https://api.apify.com/v2/acts/Hooli/google-images-scraper/runs",
        "actor_id": "Hooli/google-images-scraper"
    },
    {
        "name": "Using run-sync",
        "url": "https://api.apify.com/v2/acts/hooli~google-images-scraper/run-sync",
        "actor_id": "hooli~google-images-scraper"
    }
]

payload = {
    "queries": ["Salesforce AI"],
    "maxResults": 2
}

headers = {
    "Content-Type": "application/json"
}

print("\n" + "="*60)
print("Testing Apify Actor Endpoints")
print("="*60)

for test in tests:
    print(f"\n📋 Test: {test['name']}")
    print(f"   URL: {test['url']}")
    print(f"   Actor ID: {test['actor_id']}")
    
    try:
        response = requests.post(
            test['url'],
            json=payload,
            headers=headers,
            params={"token": api_key},
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code in [200, 201]:
            print("   ✅ SUCCESS!")
            data = response.json()
            print(f"   Response keys: {list(data.keys())[:5]}")
            if 'data' in data:
                print(f"   Data keys: {list(data['data'].keys())[:5]}")
                if 'id' in data['data']:
                    print(f"   Run ID: {data['data']['id']}")
            break
        else:
            error_text = response.text[:200]
            print(f"   ❌ Failed: {error_text}")
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:200]}")

print("\n" + "="*60)