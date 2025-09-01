#!/usr/bin/env python3
"""
Demonstration of ImageFox output data structure.

This script shows exactly what data ImageFox returns when processing a search query.
"""

import json
from datetime import datetime
from dataclasses import asdict

# Import the data structures
from imagefox import WorkflowResult, ImageResult

# Create sample image results that would be returned
sample_images = [
    ImageResult(
        url="https://images.example.com/mountain-sunset-1.jpg",
        source_url="https://photography-site.com/gallery/mountain-sunset",
        title="Majestic Mountain Sunset Over Alpine Valley",
        dimensions="3840x2160",
        analysis={
            "description": "A breathtaking sunset scene featuring snow-capped mountain peaks with golden and orange hues painting the sky. The foreground shows an alpine valley with scattered pine trees.",
            "objects": ["mountain", "sunset", "sky", "clouds", "pine trees", "valley", "snow"],
            "scene_type": "landscape",
            "colors": ["orange", "pink", "purple", "blue", "white", "green"],
            "composition": "Rule of thirds with mountain peaks in upper third, dramatic sky filling two-thirds of frame",
            "quality_score": 0.92,
            "relevance_score": 0.95,
            "technical_details": {
                "lighting": "Golden hour lighting with warm sunset tones",
                "perspective": "Wide angle landscape view from elevated position",
                "focus": "Sharp focus throughout with good depth of field",
                "exposure": "Well-balanced exposure capturing detail in highlights and shadows"
            },
            "confidence_score": 0.88,
            "models_used": ["openai/gpt-4-vision-preview", "anthropic/claude-3-opus"],
            "processing_time": 2.3,
            "cost_estimate": 0.045
        },
        selection_score=0.94,
        processed_path="/tmp/imagefox/processed/mountain-sunset-1_optimized.jpg",
        thumbnail_path="/tmp/imagefox/thumbnails/mountain-sunset-1_thumb.jpg",
        imagebb_url="https://i.ibb.co/X8Km9Lp/mountain-sunset-1.jpg",
        airtable_id="recXYZ123456"
    ),
    ImageResult(
        url="https://images.example.com/alpine-glow-2.jpg",
        source_url="https://nature-photos.com/landscapes/alpine-glow",
        title="Alpine Glow on Mountain Range at Dusk",
        dimensions="4096x2731",
        analysis={
            "description": "Stunning alpenglow effect on a mountain range during the blue hour after sunset. The peaks are illuminated with a soft pink glow while the valleys are in deep shadow.",
            "objects": ["mountain range", "alpenglow", "peaks", "valleys", "sky", "clouds"],
            "scene_type": "landscape",
            "colors": ["pink", "purple", "blue", "indigo", "gray"],
            "composition": "Panoramic composition with layered mountain ridges creating depth",
            "quality_score": 0.89,
            "relevance_score": 0.91,
            "technical_details": {
                "lighting": "Post-sunset alpenglow with soft, diffused light",
                "perspective": "Distant panoramic view showing multiple mountain layers",
                "focus": "Excellent sharpness with atmospheric perspective",
                "exposure": "Slightly underexposed to preserve color saturation"
            },
            "confidence_score": 0.85,
            "models_used": ["openai/gpt-4-vision-preview", "anthropic/claude-3-sonnet"],
            "processing_time": 1.8,
            "cost_estimate": 0.038
        },
        selection_score=0.88,
        processed_path="/tmp/imagefox/processed/alpine-glow-2_optimized.jpg",
        thumbnail_path="/tmp/imagefox/thumbnails/alpine-glow-2_thumb.jpg",
        imagebb_url="https://i.ibb.co/7NjkM8Q/alpine-glow-2.jpg",
        airtable_id="recABC789012"
    )
]

# Create the complete workflow result
workflow_result = WorkflowResult(
    search_query="mountain landscape sunset",
    total_found=47,  # Total images found by Apify search
    processed_count=5,  # Number of images analyzed
    selected_count=2,  # Number of images selected
    selected_images=sample_images,
    processing_time=12.5,
    total_cost=0.127,  # Total cost in USD
    errors=[],  # No errors in this successful run
    statistics={
        "apify": {
            "requests": 1,
            "cached_hits": 0,
            "estimated_cost": 0.002
        },
        "openrouter": {
            "total_requests": 5,
            "total_tokens": 8543,
            "total_cost": 0.095,
            "model_usage": {
                "openai/gpt-4-vision-preview": {"requests": 3, "tokens": 5200, "cost": 0.065},
                "anthropic/claude-3-opus": {"requests": 1, "tokens": 2343, "cost": 0.025},
                "anthropic/claude-3-sonnet": {"requests": 1, "tokens": 1000, "cost": 0.005}
            }
        },
        "image_processor": {
            "downloads_attempted": 5,
            "downloads_successful": 5,
            "images_optimized": 2,
            "thumbnails_generated": 2,
            "total_size_saved_mb": 3.2,
            "average_processing_time": 1.8
        },
        "image_selector": {
            "total_selections": 1,
            "total_candidates_evaluated": 5,
            "cache_hits": 0,
            "average_selection_time": 0.3
        }
    },
    created_at=datetime.now().isoformat()
)

# Print the structured output
print("\n" + "="*80)
print("IMAGEFOX WORKFLOW RESULT - DATA STRUCTURE")
print("="*80)

# Convert to dictionary for JSON display
result_dict = asdict(workflow_result)

# Pretty print the JSON structure
print("\n📋 Complete Result Structure (JSON):")
print(json.dumps(result_dict, indent=2))

print("\n" + "="*80)
print("KEY DATA POINTS EXTRACTED:")
print("="*80)

print(f"\n🔍 Search Query: '{workflow_result.search_query}'")
print(f"📊 Images Found: {workflow_result.total_found}")
print(f"🔬 Images Analyzed: {workflow_result.processed_count}")
print(f"✅ Images Selected: {workflow_result.selected_count}")
print(f"⏱️  Processing Time: {workflow_result.processing_time:.2f} seconds")
print(f"💰 Total Cost: ${workflow_result.total_cost:.4f}")

print("\n📸 SELECTED IMAGES DETAILS:")
print("-" * 40)

for i, img in enumerate(workflow_result.selected_images, 1):
    print(f"\n🖼️  Image {i}:")
    print(f"  Title: {img.title}")
    print(f"  URL: {img.url}")
    print(f"  Dimensions: {img.dimensions}")
    print(f"  Selection Score: {img.selection_score:.3f}")
    print(f"  Quality Score: {img.analysis['quality_score']:.2f}")
    print(f"  Relevance Score: {img.analysis['relevance_score']:.2f}")
    print(f"  Confidence: {img.analysis['confidence_score']:.2f}")
    print(f"  CDN URL: {img.imagebb_url}")
    print(f"  Airtable ID: {img.airtable_id}")
    print(f"\n  📝 Description:")
    print(f"    {img.analysis['description'][:150]}...")
    print(f"\n  🎨 Detected Objects:")
    print(f"    {', '.join(img.analysis['objects'])}")
    print(f"\n  🎭 Scene Type: {img.analysis['scene_type']}")
    print(f"  🌈 Colors: {', '.join(img.analysis['colors'][:5])}")

print("\n" + "="*80)
print("API USAGE STATISTICS:")
print("="*80)

stats = workflow_result.statistics
print(f"\n📡 Apify: {stats['apify']['requests']} requests, ${stats['apify']['estimated_cost']:.4f}")
print(f"🤖 OpenRouter: {stats['openrouter']['total_requests']} requests, {stats['openrouter']['total_tokens']} tokens, ${stats['openrouter']['total_cost']:.4f}")
print(f"💾 Image Processor: {stats['image_processor']['downloads_successful']}/{stats['image_processor']['downloads_attempted']} downloaded")
print(f"   Saved {stats['image_processor']['total_size_saved_mb']:.1f} MB through optimization")
print(f"🎯 Image Selector: Evaluated {stats['image_selector']['total_candidates_evaluated']} candidates in {stats['image_selector']['average_selection_time']:.2f}s")

print("\n" + "="*80)
print("This is the complete data structure returned by ImageFox.search_and_select()")
print("="*80)