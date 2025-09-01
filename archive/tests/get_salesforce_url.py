#!/usr/bin/env python3
"""
Get the best image URL for Salesforce article.
"""

from apify_client import ApifyClient

# Initialize client and search
client = ApifyClient()
print("🔍 Searching for: 'Salesforce AI artificial intelligence Winter 26'")
print("-" * 60)

results = client.search_images(
    "Salesforce AI artificial intelligence Winter 26", 
    limit=5
)

if results:
    print(f"✅ Found {len(results)} images\n")
    
    # Show the best (first) result
    best = results[0]
    print("🏆 BEST IMAGE:")
    print(f"URL: {best.get('image_url')}")
    print(f"Title: {best.get('title')}")
    print(f"Source: {best.get('displayed_url')}")
    print(f"Dimensions: {best.get('width')}x{best.get('height')}")
    
    print("\n📊 All Results:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r.get('title', 'No title')[:60]}...")
        print(f"   {r.get('image_url')}")
        
    # Cost estimate
    print("\n💰 Cost: ~$0.002 (Apify search only, no AI analysis)")
else:
    print("❌ No results found")