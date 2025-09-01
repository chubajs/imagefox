#!/usr/bin/env python3
"""
Test single image analysis with configured models.
"""

import asyncio
import os
from dotenv import load_dotenv
from openrouter_client import OpenRouterClient
from vision_analyzer import VisionAnalyzer, ImageMetadata

# Load environment variables
load_dotenv()

def test_image_analysis():
    """Test analyzing a single Salesforce image."""
    
    # The best image URL from our search
    image_url = "https://d3nqfz2gm66yqg.cloudfront.net/images/20250730093517/BlogFeatured-Templates-Character-A_708x428px.png"
    
    print("="*80)
    print("🔍 TESTING IMAGE ANALYSIS WITH CONFIGURED MODELS")
    print("="*80)
    
    # Create metadata
    metadata = ImageMetadata(
        url=image_url,
        title="Admin Release Countdown: Get Ready for Winter '26 - Salesforce Admins",
        source_url="https://admin.salesforce.com",
        width=708,
        height=428,
        format="png"
    )
    
    print(f"\n📸 Image: {metadata.title}")
    print(f"   URL: {metadata.url}")
    print(f"   Dimensions: {metadata.width}x{metadata.height}")
    
    # Initialize components
    try:
        client = OpenRouterClient()
        analyzer = VisionAnalyzer(client)
        
        print(f"\n🤖 Models Configuration:")
        print(f"   Primary: {analyzer.primary_models}")
        print(f"   Fallback: {analyzer.fallback_models}")
        
        print(f"\n⏳ Analyzing image...")
        
        # Analyze the image
        result = analyzer.analyze_image(
            metadata,
            search_query="Salesforce Winter 26 AI artificial intelligence"
        )
        
        print(f"\n✅ Analysis Complete!")
        print(f"   Description: {result.description[:150]}...")
        print(f"   Scene Type: {result.scene_type}")
        print(f"   Objects: {', '.join(result.objects[:5])}")
        print(f"   Colors: {', '.join(result.colors[:5])}")
        print(f"   Quality Score: {result.quality_metrics.overall_score:.2f}")
        print(f"   Relevance Score: {result.relevance_score:.2f}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Models Used: {', '.join(result.models_used)}")
        print(f"   Processing Time: {result.processing_time:.2f}s")
        print(f"   Cost Estimate: ${result.cost_estimate:.6f}")
        
        if hasattr(result, 'raw_model_responses') and result.raw_model_responses:
            print(f"\n📝 Raw Model Responses:")
            for resp in result.raw_model_responses:
                print(f"   - {resp.get('model', 'Unknown')}: {resp.get('tokens_used', 0)} tokens")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_image_analysis()