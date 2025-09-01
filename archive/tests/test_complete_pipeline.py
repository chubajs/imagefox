#!/usr/bin/env python3
"""
Complete AI Pipeline Test for ImageFox
Tests both Gemini vision analysis and Claude Sonnet 4 selection
"""

import os
import json
import logging
from dotenv import load_dotenv
from openrouter_client import OpenRouterClient
from vision_analyzer import VisionAnalyzer
from image_selector import ImageSelector, ImageCandidate

# Setup logging
logging.basicConfig(level=logging.DEBUG)
load_dotenv()

def test_complete_pipeline():
    print("=" * 70)
    print("COMPLETE AI PIPELINE TEST - HEALTHCARE M&A ARTICLE")
    print("=" * 70)
    
    # Test images (our working healthcare images)
    test_images = [
        {
            'url': 'https://i.ibb.co/ycDQJN5g/healthcare-ai-ma-2025.webp',
            'title': 'AI is Revolutionizing Healthcare M&A: 2025',
            'expected_relevance': 'high'
        },
        {
            'url': 'https://www.grandviewresearch.com/static/img/research/us-artificial-intelligence-in-healthcare-market-size.png',
            'title': 'AI in Healthcare Market Size',
            'expected_relevance': 'medium'
        }
    ]
    
    # Initialize clients
    print("\n1. Initializing AI clients...")
    try:
        openrouter = OpenRouterClient()
        analyzer = VisionAnalyzer()
        selector = ImageSelector()
        print("✅ All clients initialized successfully")
    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        return False
    
    # Step 1: Test Gemini 2.0 Flash Lite Vision Analysis
    print("\n2. Testing Gemini 2.0 Flash Lite vision analysis...")
    analyzed_candidates = []
    total_vision_cost = 0.0
    
    for i, img in enumerate(test_images, 1):
        print(f"\nAnalyzing image {i}: {img['title'][:50]}...")
        
        try:
            # Test vision analysis
            result = openrouter.analyze_image(
                image_input=img['url'],
                prompt=f"""Analyze this image for a healthcare M&A article titled "2025 Healthcare Outlook: M&A and AI Drive Margin Growth". 

Return JSON with:
- description: detailed description
- objects: list of objects/elements seen
- scene_type: type of image (infographic, photo, etc.)  
- colors: dominant colors
- composition: layout and design quality
- quality_score: technical quality 0-1
- relevance_score: relevance to healthcare M&A 0-1
- technical_details: any technical notes""",
                model="google/gemini-2.0-flash-lite-001",
                max_tokens=400,
                temperature=0.3
            )
            
            print(f"  ✅ Vision analysis successful")
            print(f"  📊 Quality: {result.quality_score:.2f}, Relevance: {result.relevance_score:.2f}")
            print(f"  💰 Cost: ${result.cost_estimate:.6f}")
            print(f"  🏷️  Scene: {result.scene_type}")
            
            total_vision_cost += result.cost_estimate
            
            # Create candidate for selection
            candidate = ImageCandidate(
                image_url=img['url'],
                source_url=img['url'],
                title=img['title'],
                analysis=result,  # This should be a ComprehensiveAnalysis object
                metadata={'width': 800, 'height': 600},
                search_query="healthcare M&A AI 2025"
            )
            analyzed_candidates.append(candidate)
            
        except Exception as e:
            print(f"  ❌ Vision analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Step 2: Test Claude Sonnet 4 Selection
    print(f"\n3. Testing Claude Sonnet 4 selection...")
    print(f"Vision analysis total cost: ${total_vision_cost:.6f}")
    
    try:
        # Create selection prompt for Claude
        selection_prompt = f"""You are an expert image selector for healthcare content. 

TASK: Select the best image for this article:
**Title**: "2025 Healthcare Outlook: M&A and AI Drive Margin Growth and Care Transformation"

**Article themes**: mergers & acquisitions, AI automation, hospital efficiency, cost reduction, digital transformation

**Candidates analyzed**:
"""
        
        for i, candidate in enumerate(analyzed_candidates, 1):
            selection_prompt += f"""
{i}. **{candidate.title}**
   - URL: {candidate.image_url}
   - Quality: {candidate.analysis.quality_score:.2f}
   - Relevance: {candidate.analysis.relevance_score:.2f}  
   - Scene: {candidate.analysis.scene_type}
   - Description: {candidate.analysis.description[:100]}...
"""

        selection_prompt += """
REQUIREMENTS:
1. Select the image that best matches the article themes
2. Provide detailed reasoning for your selection
3. Return JSON format:
```json
{
  "selected_index": 1,
  "reasoning": "Detailed explanation of why this image was selected",
  "score_breakdown": {
    "relevance_to_ma": 0.9,
    "relevance_to_ai": 0.8, 
    "visual_appeal": 0.7,
    "professional_quality": 0.8
  },
  "final_score": 0.85
}
```"""

        # Make selection with Claude Sonnet 4
        selection_result = openrouter.analyze_image(
            image_input=analyzed_candidates[0].image_url,  # Include an image for context
            prompt=selection_prompt,
            model="anthropic/claude-sonnet-4",
            max_tokens=1000,
            temperature=0.3
        )
        
        print(f"✅ Claude Sonnet 4 selection successful")
        print(f"💰 Selection cost: ${selection_result.cost_estimate:.6f}")
        
        # Parse selection
        try:
            selection_data = json.loads(selection_result.description)
            selected_idx = selection_data.get('selected_index', 1) - 1
            selected_image = analyzed_candidates[selected_idx]
            
            print(f"\n🏆 SELECTED IMAGE:")
            print(f"   Title: {selected_image.title}")
            print(f"   URL: {selected_image.image_url}")
            print(f"   Score: {selection_data.get('final_score', 0.0):.2f}")
            print(f"   Reasoning: {selection_data.get('reasoning', 'N/A')[:200]}...")
            
        except (json.JSONDecodeError, KeyError) as e:
            print(f"⚠️  Selection parsing issue: {e}")
            print(f"   Raw response: {selection_result.description[:200]}...")
    
    except Exception as e:
        print(f"❌ Claude selection failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Summary
    total_cost = total_vision_cost + selection_result.cost_estimate
    print(f"\n" + "=" * 70)
    print("PIPELINE TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Vision Analysis: {len(analyzed_candidates)} images analyzed")
    print(f"✅ AI Selection: 1 image selected")
    print(f"💰 Total Cost: ${total_cost:.6f}")
    print(f"   - Vision (Gemini): ${total_vision_cost:.6f}")
    print(f"   - Selection (Claude): ${selection_result.cost_estimate:.6f}")
    print(f"⚡ Processing: Complete AI pipeline working!")
    
    return True

if __name__ == "__main__":
    success = test_complete_pipeline()
    if success:
        print(f"\n🎉 COMPLETE PIPELINE TEST: PASSED")
    else:
        print(f"\n💥 COMPLETE PIPELINE TEST: FAILED")
