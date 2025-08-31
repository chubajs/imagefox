#!/usr/bin/env python3
"""EXP-20: Wellness Integration Pattern Analysis"""

import logging
import json
import asyncio
from dotenv import load_dotenv
from imagefox import SearchRequest, ImageFox

# Load environment first
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def run_exp20():
    # Create ImageFox instance
    imagefox = ImageFox()
    
    # EXP-20: Wellness Integration Pattern Analysis
    request = SearchRequest(
        query='workplace wellness mental health stress management aviation industry employee wellbeing support programs',
        limit=5,
        max_results=1,
        enable_processing=False,
        enable_upload=False, 
        enable_storage=False
    )

    result = await imagefox.search_and_select(request)

    print('EXP-20 COMPLETED')
    print(f'Selected images: {len(result.selected_images)}')
    if result.selected_images:
        selected = result.selected_images[0]
        print(f'Selected: {selected.title}')
        print(f'Analysis: {selected.analysis.description[:200]}...')
    print(f'Total cost: ${result.total_cost:.4f}')
    return result

if __name__ == "__main__":
    result = asyncio.run(run_exp20())