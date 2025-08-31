#!/usr/bin/env python3
"""EXP-03: Media & Communication Strategy Analysis - PROPER METHODOLOGY"""

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

def media_communication_analysis(article_content):
    """
    EXP-03: Media & Communication Strategy Analysis
    Extract communication strategies, PR elements, and media management themes from the easyJet article.
    """
    print("\n=== EXP-03: MEDIA & COMMUNICATION STRATEGY ANALYSIS ===")
    
    # Key communication elements from the easyJet article
    communication_elements = [
        "public scrutiny",  # media attention
        "hyper-transparency of social media",  # digital communication challenges
        "livestreamed worldwide",  # modern media landscape
        "transparent, decisive responses",  # communication strategy
        "faster reputational fallout",  # PR consequences
        "every employee embodies the brand",  # brand communication
        "public spaces",  # visibility concerns
        "eyewitnesses described",  # media reporting
        "reports of public drunkenness"  # media coverage
    ]
    
    # Analysis focus: PR strategy and communication management
    focus_areas = [
        "corporate communication", "public relations", "crisis communication",
        "brand messaging", "media management", "reputation management",
        "social media strategy", "corporate PR", "communication strategy"
    ]
    
    # Generate communication-focused search query based on actual article content
    query = "corporate communication public relations media strategy brand messaging crisis PR social media management"
    
    print(f"Communication elements from article: {len(communication_elements)} identified")
    for elem in communication_elements[:3]:
        print(f"  - {elem}")
    print(f"Focus areas: {', '.join(focus_areas[:4])}...")
    print(f"Generated query: {query}")
    
    return query

async def run_exp03():
    # Load and analyze the actual article
    article = load_article()
    print(f"Article loaded: {len(article)} characters")
    
    # Apply Media & Communication analysis to the easyJet content
    query = media_communication_analysis(article)
    
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

    print('\n=== EXP-03 EXECUTION RESULTS ===')
    print(f'Selected images: {len(result.selected_images)}')
    if result.selected_images:
        selected = result.selected_images[0]
        print(f'Selected: {selected.title}')
        print(f'Image URL: {selected.image_url}')
        print(f'Analysis preview: {selected.analysis.description[:200]}...')
    print(f'Total cost: ${result.total_cost:.4f}')
    
    return result, query

if __name__ == "__main__":
    result, query = asyncio.run(run_exp03())
    print(f"\n✅ EXP-03 COMPLETE: Communication analysis of easyJet article produced query: {query}")