#!/usr/bin/env python3
"""EXP-13: Risk Assessment Pattern Analysis"""

import logging
import json
import asyncio
from dotenv import load_dotenv
from imagefox import SearchRequest, ImageFox

# Load environment first
load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def run_exp13():
    # Create ImageFox instance
    imagefox = ImageFox()
    
    # EXP-13: Risk Assessment Pattern Analysis - simplified for testing
    request = SearchRequest(
        query='airline industry financial risk market volatility assessment aviation sector analysis economic uncertainty',
        limit=5,
        max_results=1,
        enable_processing=False,
        enable_upload=False,
        enable_storage=False
    )

    result = await imagefox.search_and_select(request)

    print('EXP-13 COMPLETED')
    print(f'Selected images: {len(result.selected_images)}')
    if result.selected_images:
        selected = result.selected_images[0]
        print(f'Selected: {selected.title}')
        print(f'URL: {selected.uploaded_url}')
    print(f'Total cost: ${result.total_cost:.4f}')
    return result

if __name__ == "__main__":
    result = asyncio.run(run_exp13())