#!/usr/bin/env python3
"""Run key experiments - the predicted top performers."""

import asyncio
from execute_imagefox_pipeline import ImageFoxPipeline

# Key experiments based on our earlier analysis
KEY_EXPERIMENTS = [
    {
        "id": "EXP-13",
        "name": "Risk Assessment",
        "query": "risk assessment matrix corporate risk management operational safety"
    },
    {
        "id": "EXP-15",
        "name": "Brand Management",
        "query": "brand reputation management corporate image crisis protection"
    },
    {
        "id": "EXP-03",
        "name": "Media & Communication Strategy",
        "query": "corporate crisis communication public relations PR media management"
    },
    {
        "id": "EXP-09",
        "name": "Crisis Management",
        "query": "crisis management emergency response incident handling business continuity"
    },
    {
        "id": "EXP-02",
        "name": "Corporate Trust & Leadership",
        "query": "corporate leadership executive management business integrity trust governance"
    }
]

async def run_key_experiments():
    """Run just the key experiments."""
    print("🎯 Running Top 5 Key Experiments")
    print("="*60)
    
    async with ImageFoxPipeline() as pipeline:
        results = []
        
        for exp in KEY_EXPERIMENTS:
            result = await pipeline.run_experiment(exp)
            results.append(result)
            await asyncio.sleep(1)  # Small delay between experiments
        
        print("\n" + "="*60)
        print("📊 RESULTS SUMMARY")
        print("="*60)
        
        # Sort by score
        sorted_results = sorted(
            results,
            key=lambda x: x["best_image"]["analysis"]["total_score"] if x.get("best_image") else 0,
            reverse=True
        )
        
        for i, result in enumerate(sorted_results, 1):
            if result.get("best_image"):
                print(f"\n{i}. {result['experiment_name']}")
                print(f"   Score: {result['best_image']['analysis']['total_score']}")
                print(f"   Image: {result['best_image']['title'][:50]}...")
                print(f"   Relevance: {result['best_image']['analysis']['relevance_to_article']}")
                print(f"   URL: {result['best_image']['url'][:80]}...")
        
        # Find winner
        if sorted_results and sorted_results[0].get("best_image"):
            winner = sorted_results[0]
            print("\n" + "="*60)
            print("🏆 WINNER: " + winner['experiment_name'])
            print(f"🎯 Score: {winner['best_image']['analysis']['total_score']}")
            print(f"📸 Image: {winner['best_image']['title']}")
            print("="*60)

if __name__ == "__main__":
    asyncio.run(run_key_experiments())