#!/usr/bin/env python3
"""
Test direct API call to see actual token usage and costs.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    print("❌ No OPENROUTER_API_KEY found")
    exit(1)

# Test image
image_url = "https://d3nqfz2gm66yqg.cloudfront.net/images/20250730093517/BlogFeatured-Templates-Character-A_708x428px.png"

print("="*80)
print("🔍 DIRECT OPENROUTER API TEST")
print("="*80)

# Prepare request
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://imagefox.ai",
    "X-Title": "ImageFox Test"
}

payload = {
    "model": "google/gemini-2.0-flash-lite-001",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Analyze this image for a Salesforce Winter '26 article. Describe what you see."
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": image_url
                    }
                }
            ]
        }
    ],
    "max_tokens": 500,
    "temperature": 0.3
}

print(f"\n📸 Testing with model: {payload['model']}")
print(f"   Image: {image_url[:80]}...")
print(f"\n⏳ Making API call...")

try:
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    data = response.json()
    
    # Extract response
    if 'choices' in data and len(data['choices']) > 0:
        content = data['choices'][0]['message']['content']
        print(f"\n✅ Response received!")
        print(f"   Content: {content[:200]}...")
    
    # Check usage
    if 'usage' in data:
        usage = data['usage']
        print(f"\n📊 Token Usage:")
        print(f"   Prompt tokens: {usage.get('prompt_tokens', 0)}")
        print(f"   Completion tokens: {usage.get('completion_tokens', 0)}")
        print(f"   Total tokens: {usage.get('total_tokens', 0)}")
        
        # Calculate cost
        prompt_tokens = usage.get('prompt_tokens', 0)
        completion_tokens = usage.get('completion_tokens', 0)
        
        # Gemini 2.0 Flash Lite pricing
        input_cost = (prompt_tokens / 1_000_000) * 0.075
        output_cost = (completion_tokens / 1_000_000) * 0.30
        total_cost = input_cost + output_cost
        
        print(f"\n💰 Cost Calculation:")
        print(f"   Input cost: ${input_cost:.8f}")
        print(f"   Output cost: ${output_cost:.8f}")
        print(f"   Total cost: ${total_cost:.8f}")
    
    # Save full response for debugging
    with open('api_response.json', 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n💾 Full response saved to api_response.json")
    
except requests.exceptions.RequestException as e:
    print(f"\n❌ API Error: {e}")
    if hasattr(e.response, 'text'):
        print(f"   Response: {e.response.text[:500]}")
except Exception as e:
    print(f"\n❌ Error: {e}")