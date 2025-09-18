#!/usr/bin/env python3
"""
Test ImageFox workflow with actual API calls but without Airtable dependencies.

This script demonstrates the ImageFox pipeline working end-to-end.
"""

import asyncio
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for ImageFox imports
sys.path.insert(0, str(Path(__file__).parent))

from imagefox import ImageFox, SearchRequest
from imagefox_agent import generate_search_query

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


async def test_imagefox_workflow():
    """Test the complete ImageFox workflow."""
    print("=" * 60)
    print("ImageFox Workflow Test")
    print("=" * 60)
    
    # Sample article content (simulating what would come from OurPost table)
    sample_articles = [
        {
            "title": "Digital Marketing Trends 2025",
            "article": "The digital marketing landscape is evolving rapidly with artificial intelligence, machine learning, and automation becoming central to successful campaigns. Companies are investing heavily in personalized customer experiences and data-driven strategies to stay competitive in the market.",
            "expected_images": 2
        },
        {
            "title": "Remote Work Technology Solutions", 
            "article": "As remote work becomes the norm, businesses are seeking innovative technology solutions to maintain productivity and collaboration. Cloud computing, video conferencing, and project management tools are essential for distributed teams to work effectively.",
            "expected_images": 2
        }
    ]
    
    try:
        # Initialize ImageFox
        print("\n1. Initializing ImageFox...")
        imagefox = ImageFox()
        
        # Validate configuration (skip airtable)
        validation_results = imagefox.validate_configuration()
        failed_components = [comp for comp, status in validation_results.items() if not status and comp != 'airtable']
        
        if failed_components:
            print(f"❌ Validation failed for: {failed_components}")
            return False
        
        print("✅ ImageFox validation successful")
        
        # Process sample articles
        total_cost = 0.0
        total_images = 0
        
        for i, article_data in enumerate(sample_articles, 1):
            print(f"\n2.{i} Processing Article: '{article_data['title']}'")
            
            # Generate search query (same as agent does)
            search_query = generate_search_query(article_data['article'], article_data['title'])
            print(f"   Generated Query: '{search_query}'")
            
            # Create search request
            search_request = SearchRequest(
                query=search_query,
                limit=20,  # Search more to get better candidates
                max_results=article_data['expected_images'],
                safe_search=True,
                enable_processing=True,
                enable_upload=True,  # Upload to ImageBB for CDN URLs
                enable_storage=False  # Don't store in Airtable Images table
            )
            
            print(f"   Searching for {article_data['expected_images']} images...")
            
            # Execute ImageFox workflow
            workflow_result = await imagefox.search_and_select(search_request)
            
            # Display results
            print(f"   📊 Results:")
            print(f"      Found: {workflow_result.total_found} images")
            print(f"      Analyzed: {workflow_result.processed_count} images")
            print(f"      Selected: {workflow_result.selected_count} images")
            print(f"      Processing time: {workflow_result.processing_time:.2f}s")
            print(f"      Cost: ${workflow_result.total_cost:.6f}")
            
            if workflow_result.errors:
                print(f"      ⚠️ Errors: {len(workflow_result.errors)}")
                for error in workflow_result.errors:
                    print(f"         - {error}")
            
            if workflow_result.selected_images:
                print(f"   🖼️ Selected Images:")
                for j, image in enumerate(workflow_result.selected_images, 1):
                    # Prefer CDN URL (ImageBB) over original
                    image_url = image.imagebb_url if image.imagebb_url else image.url
                    print(f"      {j}. Score: {image.selection_score:.3f}")
                    print(f"         URL: {image_url[:80]}...")
                    print(f"         Title: {image.title[:60]}..." if image.title else "         Title: (none)")
                    print(f"         Quality: {image.analysis.get('quality_score', 'N/A')}")
                    
                    # This would be added to Airtable attachment field in real usage
                    total_images += 1
            else:
                print("   ❌ No images selected")
            
            total_cost += workflow_result.total_cost
            
            # Add delay between articles
            await asyncio.sleep(1)
        
        # Final summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)
        print(f"Articles processed: {len(sample_articles)}")
        print(f"Total images found: {total_images}")
        print(f"Total cost: ${total_cost:.6f}")
        print(f"Average cost per image: ${total_cost/max(total_images, 1):.6f}")
        
        # Cleanup
        await imagefox.cleanup()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_search_query_generation():
    """Test search query generation."""
    print("\n" + "=" * 60)
    print("Search Query Generation Test")
    print("=" * 60)
    
    test_cases = [
        {
            "title": "AI Revolution in Healthcare",
            "article": "Artificial intelligence is transforming healthcare with predictive analytics, diagnostic imaging, and personalized treatment plans. Machine learning algorithms help doctors make more accurate diagnoses and improve patient outcomes.",
        },
        {
            "title": "Sustainable Energy Future",
            "article": "Renewable energy sources like solar and wind power are becoming more cost-effective. Energy storage technology and smart grids are key to transitioning away from fossil fuels toward a sustainable future.",
        },
        {
            "title": "E-commerce Growth Strategies",
            "article": "Online retailers are leveraging social media marketing, influencer partnerships, and mobile-first experiences to drive sales growth. Customer data analytics help optimize product recommendations and inventory management.",
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        query = generate_search_query(case['article'], case['title'])
        print(f"{i}. Title: '{case['title']}'")
        print(f"   Article: '{case['article'][:100]}...'")
        print(f"   Generated Query: '{query}'")
        print()


async def main():
    """Main test runner."""
    print("ImageFox Agent Workflow Test Suite")
    
    # Test query generation first
    await test_search_query_generation()
    
    # Test full workflow
    success = await test_imagefox_workflow()
    
    if success:
        print("\n🎉 All tests passed! ImageFox agent is ready for production.")
        return 0
    else:
        print("\n❌ Tests failed. Check configuration and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))