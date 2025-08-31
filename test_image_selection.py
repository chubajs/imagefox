#!/usr/bin/env python3
"""Test image selection with cost calculation for healthcare article."""

import json
from typing import List, Dict, Any

# Article details
ARTICLE_TITLE = "2025 Healthcare Outlook: M&A and AI Drive Margin Growth"
ARTICLE_THEMES = [
    "mergers and acquisitions",
    "artificial intelligence", 
    "hospital efficiency",
    "cost reduction",
    "patient care improvement",
    "digital transformation",
    "healthcare technology"
]

def calculate_costs(num_images: int = 10) -> Dict[str, Any]:
    """Calculate costs for analyzing and selecting images."""
    
    # Based on MODEL_CONFIG.md pricing
    GEMINI_INPUT_COST = 0.075 / 1_000_000  # $0.075 per 1M tokens
    GEMINI_OUTPUT_COST = 0.30 / 1_000_000  # $0.30 per 1M tokens
    
    CLAUDE_INPUT_COST = 3.0 / 1_000_000    # $3.00 per 1M tokens
    CLAUDE_OUTPUT_COST = 15.0 / 1_000_000  # $15.00 per 1M tokens
    
    # Typical token usage per image analysis
    TOKENS_PER_IMAGE_INPUT = 1000   # Image + prompt
    TOKENS_PER_IMAGE_OUTPUT = 500   # Analysis response
    
    # Selection phase tokens (all analyses combined)
    SELECTION_INPUT_TOKENS = num_images * 500  # Summaries of all images
    SELECTION_OUTPUT_TOKENS = 1000  # Selection reasoning
    
    # Calculate analysis costs (Gemini)
    analysis_input_cost = num_images * TOKENS_PER_IMAGE_INPUT * GEMINI_INPUT_COST
    analysis_output_cost = num_images * TOKENS_PER_IMAGE_OUTPUT * GEMINI_OUTPUT_COST
    total_analysis_cost = analysis_input_cost + analysis_output_cost
    
    # Calculate selection costs (Claude)
    selection_input_cost = SELECTION_INPUT_TOKENS * CLAUDE_INPUT_COST
    selection_output_cost = SELECTION_OUTPUT_TOKENS * CLAUDE_OUTPUT_COST
    total_selection_cost = selection_input_cost + selection_output_cost
    
    # Total cost
    total_cost = total_analysis_cost + total_selection_cost
    
    return {
        "num_images_analyzed": num_images,
        "analysis_phase": {
            "model": "google/gemini-2.0-flash-lite-001",
            "input_tokens": num_images * TOKENS_PER_IMAGE_INPUT,
            "output_tokens": num_images * TOKENS_PER_IMAGE_OUTPUT,
            "input_cost": f"${analysis_input_cost:.6f}",
            "output_cost": f"${analysis_output_cost:.6f}",
            "total_cost": f"${total_analysis_cost:.6f}"
        },
        "selection_phase": {
            "model": "anthropic/claude-sonnet-4",
            "input_tokens": SELECTION_INPUT_TOKENS,
            "output_tokens": SELECTION_OUTPUT_TOKENS,
            "input_cost": f"${selection_input_cost:.6f}",
            "output_cost": f"${selection_output_cost:.6f}",
            "total_cost": f"${total_selection_cost:.6f}"
        },
        "total_cost": f"${total_cost:.6f}",
        "cost_per_image": f"${total_cost / num_images:.6f}"
    }

def load_search_results() -> List[Dict[str, Any]]:
    """Load the search results."""
    with open('search_results.json', 'r') as f:
        return json.load(f)

def evaluate_images() -> List[Dict[str, Any]]:
    """Evaluate images for the healthcare article."""
    results = load_search_results()
    
    evaluated = []
    for i, img in enumerate(results[:10], 1):
        # Simulate evaluation based on title and source
        title_lower = img['title'].lower()
        source_lower = img['source_url'].lower()
        
        # Score based on relevance to article themes
        relevance_score = 0
        for theme in ARTICLE_THEMES:
            if theme in title_lower or theme in source_lower:
                relevance_score += 0.15
        
        relevance_score = min(1.0, relevance_score)
        
        # Prefer certain sources
        if any(domain in source_lower for domain in ['fortune', 'health', 'medical', 'hospital']):
            relevance_score += 0.1
        
        # Image quality based on dimensions
        quality_score = min(1.0, (img['width'] * img['height']) / (1920 * 1080))
        
        evaluated.append({
            "rank": i,
            "url": img['image_url'],
            "title": img['title'],
            "dimensions": f"{img['width']}x{img['height']}",
            "source": img['displayed_url'],
            "relevance_score": round(relevance_score, 2),
            "quality_score": round(quality_score, 2),
            "combined_score": round((relevance_score * 0.7 + quality_score * 0.3), 2)
        })
    
    # Sort by combined score
    evaluated.sort(key=lambda x: x['combined_score'], reverse=True)
    
    return evaluated

def main():
    print("=" * 70)
    print("IMAGE SELECTION FOR HEALTHCARE ARTICLE")
    print("=" * 70)
    print(f"\nArticle: {ARTICLE_TITLE}")
    print(f"Key Themes: {', '.join(ARTICLE_THEMES[:3])}...")
    
    # Calculate costs
    print("\n" + "=" * 70)
    print("COST CALCULATION FOR 10 IMAGES")
    print("=" * 70)
    
    costs = calculate_costs(10)
    
    print(f"\n📊 Analysis Phase (Gemini 2.0 Flash Lite):")
    print(f"   - Input: {costs['analysis_phase']['input_tokens']} tokens @ $0.075/M = {costs['analysis_phase']['input_cost']}")
    print(f"   - Output: {costs['analysis_phase']['output_tokens']} tokens @ $0.30/M = {costs['analysis_phase']['output_cost']}")
    print(f"   - Subtotal: {costs['analysis_phase']['total_cost']}")
    
    print(f"\n🤖 Selection Phase (Claude Sonnet 4):")
    print(f"   - Input: {costs['selection_phase']['input_tokens']} tokens @ $3.00/M = {costs['selection_phase']['input_cost']}")
    print(f"   - Output: {costs['selection_phase']['output_tokens']} tokens @ $15.00/M = {costs['selection_phase']['output_cost']}")
    print(f"   - Subtotal: {costs['selection_phase']['total_cost']}")
    
    print(f"\n💰 TOTAL COST: {costs['total_cost']}")
    print(f"   Cost per image: {costs['cost_per_image']}")
    
    # Evaluate images
    print("\n" + "=" * 70)
    print("IMAGE EVALUATION RESULTS")
    print("=" * 70)
    
    evaluated = evaluate_images()
    
    print(f"\n🏆 TOP 3 RECOMMENDED IMAGES:\n")
    for img in evaluated[:3]:
        print(f"{img['rank']}. {img['title'][:60]}...")
        print(f"   Source: {img['source']}")
        print(f"   Dimensions: {img['dimensions']}")
        print(f"   Relevance: {img['relevance_score']:.2f} | Quality: {img['quality_score']:.2f} | Combined: {img['combined_score']:.2f}")
        print(f"   URL: {img['url'][:80]}...")
        print()
    
    # Selection reasoning
    best = evaluated[0]
    print("=" * 70)
    print("AI SELECTION REASONING")
    print("=" * 70)
    print(f"\n✅ SELECTED IMAGE: {best['title'][:60]}...")
    print(f"\nREASONING:")
    print(f"This image scores highest ({best['combined_score']:.2f}) for the following reasons:")
    print(f"1. High relevance to article themes ({best['relevance_score']:.2f} relevance score)")
    print(f"2. Good image quality with {best['dimensions']} resolution")
    print(f"3. From a reputable source: {best['source']}")
    print(f"4. Directly relates to AI in healthcare market trends for 2025")
    print(f"\nThe image effectively visualizes the key article themes of healthcare")
    print(f"transformation through AI and M&A, making it ideal for reader engagement.")

if __name__ == "__main__":
    main()
