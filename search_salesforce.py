#!/usr/bin/env python3
"""
Search for the best image for Salesforce Winter '26 article.
"""

import asyncio
import json
from imagefox import ImageFox, SearchRequest

async def search_salesforce_image():
    """Search for Salesforce AI Winter '26 image."""
    
    print("\n" + "="*80)
    print("🔍 SEARCHING FOR SALESFORCE WINTER '26 AI IMAGE")
    print("="*80)
    
    # Initialize ImageFox
    imagefox = ImageFox()
    
    # Create search request
    request = SearchRequest(
        query="Salesforce AI artificial intelligence sales transformation innovation technology",
        max_results=1,  # Get the single best image
        enable_processing=False,  # Skip processing for demo
        enable_upload=False,  # Skip upload for demo
        enable_storage=False  # Skip storage for demo
    )
    
    print(f"\n📋 Search Parameters:")
    print(f"  Query: {request.query}")
    print(f"  Max Results: {request.max_results}")
    print(f"  Article: Salesforce Winter '26: AI-Powered Sales Transformation & Ukrainian Innovation")
    
    try:
        # Run the search
        print("\n⏳ Starting search and analysis...")
        result = await imagefox.search_and_select(request)
        
        print("\n" + "="*80)
        print("✅ SEARCH COMPLETE")
        print("="*80)
        
        print(f"\n📊 Search Statistics:")
        print(f"  Total Images Found: {result.total_found}")
        print(f"  Images Analyzed: {result.processed_count}")
        print(f"  Images Selected: {result.selected_count}")
        print(f"  Processing Time: {result.processing_time:.2f} seconds")
        
        print(f"\n💰 Cost Breakdown:")
        print(f"  Total Cost: ${result.total_cost:.4f}")
        if result.statistics:
            if 'apify' in result.statistics:
                print(f"  - Apify Search: ${result.statistics['apify'].get('estimated_cost', 0):.4f}")
            if 'openrouter' in result.statistics:
                print(f"  - Vision Analysis: ${result.statistics['openrouter'].get('total_cost', 0):.4f}")
                print(f"    • Tokens Used: {result.statistics['openrouter'].get('total_tokens', 0):,}")
                if 'model_usage' in result.statistics['openrouter']:
                    for model, usage in result.statistics['openrouter']['model_usage'].items():
                        print(f"    • {model}: ${usage.get('cost', 0):.4f}")
        
        if result.selected_images:
            print(f"\n🏆 BEST IMAGE SELECTED:")
            print("-" * 40)
            
            for img in result.selected_images:
                print(f"\n📸 Image Details:")
                print(f"  Title: {img.title}")
                print(f"  URL: {img.url}")
                print(f"  Source: {img.source_url}")
                print(f"  Dimensions: {img.dimensions}")
                print(f"  Selection Score: {img.selection_score:.3f}")
                
                if img.analysis:
                    print(f"\n  🔍 Analysis:")
                    print(f"    Description: {img.analysis.get('description', 'N/A')[:200]}...")
                    print(f"    Quality Score: {img.analysis.get('quality_score', 0):.2f}")
                    print(f"    Relevance Score: {img.analysis.get('relevance_score', 0):.2f}")
                    print(f"    Confidence: {img.analysis.get('confidence_score', 0):.2f}")
                    
                    if 'objects' in img.analysis:
                        print(f"    Detected Objects: {', '.join(img.analysis['objects'][:5])}")
                    if 'colors' in img.analysis:
                        print(f"    Main Colors: {', '.join(img.analysis['colors'][:5])}")
                    if 'scene_type' in img.analysis:
                        print(f"    Scene Type: {img.analysis['scene_type']}")
                
                if img.ai_selection_explanation:
                    try:
                        explanation = json.loads(img.ai_selection_explanation)
                        print(f"\n  🤖 AI Selection Reasoning:")
                        print(f"    {explanation.get('detailed_explanation', 'No explanation available')}")
                        
                        if 'selection_criteria_used' in explanation:
                            print(f"\n  📌 Selection Criteria:")
                            for criterion in explanation['selection_criteria_used']:
                                print(f"    • {criterion}")
                    except:
                        pass
                
                print(f"\n  🔗 Direct Image URL:")
                print(f"    {img.url}")
                
        else:
            print("\n❌ No images were selected")
            if result.errors:
                print("\n⚠️ Errors encountered:")
                for error in result.errors:
                    print(f"  - {error}")
        
        # Save results to file
        with open('salesforce_image_result.json', 'w') as f:
            json.dump({
                'search_query': result.search_query,
                'total_cost': result.total_cost,
                'processing_time': result.processing_time,
                'selected_image': {
                    'url': result.selected_images[0].url if result.selected_images else None,
                    'title': result.selected_images[0].title if result.selected_images else None,
                    'source': result.selected_images[0].source_url if result.selected_images else None,
                    'analysis': result.selected_images[0].analysis if result.selected_images else None
                } if result.selected_images else None,
                'statistics': result.statistics
            }, f, indent=2)
            print(f"\n💾 Results saved to salesforce_image_result.json")
            
    except Exception as e:
        print(f"\n❌ Error during search: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(search_salesforce_image())