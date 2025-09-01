#!/usr/bin/env python3
"""Test single experiment quickly."""

import asyncio
from execute_imagefox_pipeline import ImageFoxPipeline, EXPERIMENTS

async def test_single():
    """Test just one experiment."""
    async with ImageFoxPipeline() as pipeline:
        # Run just the first experiment
        experiment = EXPERIMENTS[0]
        result = await pipeline.run_experiment(experiment)
        
        print("\n📊 RESULT SUMMARY:")
        print(f"Experiment: {result['experiment_name']}")
        print(f"Images found: {result['images_found']}")
        print(f"Images analyzed: {result['images_analyzed']}")
        
        if result.get('best_image'):
            print(f"\n🏆 Best Image:")
            print(f"  URL: {result['best_image']['url']}")
            print(f"  Score: {result['best_image']['analysis']['total_score']}")
            print(f"  Relevance: {result['best_image']['analysis']['relevance_to_article']}")

if __name__ == "__main__":
    asyncio.run(test_single())