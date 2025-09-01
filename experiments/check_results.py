#!/usr/bin/env python3
"""Check experiment results."""

import json
from pathlib import Path

results_dir = Path("experiment_results")
all_results = []

for json_file in sorted(results_dir.glob("*.json")):
    with open(json_file) as f:
        data = json.load(f)
        
    if data.get("best_image"):
        score = data["best_image"]["analysis"]["total_score"]
        url = data["best_image"]["url"]
        all_results.append({
            "id": data["experiment_id"],
            "name": data["experiment_name"],
            "score": score,
            "url": url,
            "relevance": data["best_image"]["analysis"]["relevance_to_article"]
        })
        print(f"✅ {data['experiment_id']}: {data['experiment_name']}")
        print(f"   Score: {score}")
        print(f"   Relevance: {data['best_image']['analysis']['relevance_to_article']}")
        print(f"   URL: {url[:80]}...")
    else:
        print(f"❌ {data['experiment_id']}: No images analyzed")
    print()

# Show ranking
if all_results:
    print("="*60)
    print("🏆 RANKING BY SCORE")
    print("="*60)
    
    sorted_results = sorted(all_results, key=lambda x: x["score"], reverse=True)
    
    for i, result in enumerate(sorted_results, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        print(f"{medal} {result['name']}")
        print(f"   Score: {result['score']}")
        print(f"   Relevance: {result['relevance']}")
        print()
    
    print("="*60)
    print(f"🏆 WINNER: {sorted_results[0]['name']}")
    print(f"🎯 Score: {sorted_results[0]['score']}")
    print(f"📸 Image URL: {sorted_results[0]['url']}")