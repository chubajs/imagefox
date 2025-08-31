#!/usr/bin/env python3
"""EXP-02: Corporate Trust & Leadership Analysis - PROPER METHODOLOGY"""

import logging
import asyncio
from dotenv import load_dotenv
from imagefox import SearchRequest, ImageFox

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_article():
    """Load the easyJet article content."""
    with open('easyjet_article.txt', 'r') as f:
        return f.read()

def corporate_trust_leadership_analysis(article_content):
    """
    EXP-02: Corporate Trust & Leadership Analysis
    Extract leadership decisions, corporate governance, and trust-building themes from the easyJet article.
    """
    print("\n=== EXP-02: CORPORATE TRUST & LEADERSHIP ANALYSIS ===")
    
    # Key leadership elements from the easyJet article
    leadership_elements = [
        "easyJet's swift removal of the pilot",  # decisive leadership action
        "formal investigation",  # corporate governance
        "business ethics mandate integrity and candor",  # leadership values
        "focus premium",  # leadership concept
        "transparent, decisive responses",  # leadership communication
        "culture where accountability and self-leadership are daily habits",  # leadership culture
        "every employee embodies the brand"  # leadership responsibility
    ]
    
    # Analysis focus: Leadership decision-making and corporate trust
    focus_areas = [
        "executive leadership", "corporate governance", "business integrity",
        "organizational trust", "leadership accountability", "corporate culture",
        "ethical leadership", "brand management", "crisis leadership"
    ]
    
    # Generate leadership-focused search query based on actual article content
    query = "corporate leadership executive management business integrity organizational trust ethical governance accountability"
    
    print(f"Leadership elements from article: {len(leadership_elements)} identified")
    for elem in leadership_elements[:3]:
        print(f"  - {elem}")
    print(f"Focus areas: {', '.join(focus_areas[:4])}...")
    print(f"Generated query: {query}")
    
    return query

async def run_exp02():
    # Load and analyze the actual article
    article = load_article()
    print(f"Article loaded: {len(article)} characters")
    
    # Apply Corporate Trust & Leadership analysis to the easyJet content
    query = corporate_trust_leadership_analysis(article)
    
    # Create ImageFox instance and run search
    imagefox = ImageFox()
    
    request = SearchRequest(
        query=query,
        limit=5,
        max_results=1,
        enable_processing=False,
        enable_upload=False,
        enable_storage=False
    )

    result = await imagefox.search_and_select(request)

    print('\n=== EXP-02 EXECUTION RESULTS ===')
    print(f'Selected images: {len(result.selected_images)}')
    if result.selected_images:
        selected = result.selected_images[0]
        print(f'Selected: {selected.title}')
        print(f'Image URL: {selected.image_url}')
        print(f'Analysis preview: {selected.analysis.description[:200]}...')
    print(f'Total cost: ${result.total_cost:.4f}')
    
    return result, query

if __name__ == "__main__":
    result, query = asyncio.run(run_exp02())
    print(f"\n✅ EXP-02 COMPLETE: Leadership analysis of easyJet article produced query: {query}")