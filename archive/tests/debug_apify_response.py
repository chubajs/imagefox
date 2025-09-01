#!/usr/bin/env python3
"""
Debug Apify response to see what data format we're getting.
"""

import os
import json
from apify_client import ApifyClient

# Initialize client
client = ApifyClient()

# Search for images
print("🔍 Searching for images...")
results = client.search_images("Salesforce AI", limit=3)

print(f"\n📊 Got {len(results)} results")

# Print first result in detail
if results:
    print("\n📋 First result structure:")
    print(json.dumps(results[0], indent=2))
    
    print("\n🔑 All keys in results:")
    for i, result in enumerate(results, 1):
        print(f"\nResult {i} keys: {list(result.keys())}")
        print(f"  image_url: '{result.get('image_url', 'MISSING')}'")
        print(f"  title: '{result.get('title', 'MISSING')}'")
        print(f"  source_url: '{result.get('source_url', 'MISSING')}'")
        print(f"  width: {result.get('width', 'MISSING')}")
        print(f"  height: {result.get('height', 'MISSING')}")
else:
    print("\n❌ No results returned")