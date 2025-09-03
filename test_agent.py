#!/usr/bin/env python3
"""
Test script for ImageFox Agent

This script tests the ImageFox agent functionality without running the full agent.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path for ImageFox imports
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from pyairtable import Table

# Load environment variables
load_dotenv()

# Import from our agent
from imagefox_agent import (
    parse_imagefox_config,
    generate_search_query,
    check_agent_status,
    AIRTABLE_API_KEY,
    PROJECTS_BASE,
    projects_table
)

# Setup logging for testing
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_parse_imagefox_config():
    """Test the imagefox config parsing function."""
    print("\n=== Testing parse_imagefox_config ===")
    
    test_cases = [
        "OurPost->google_images",
        "OurPost->google_images:3", 
        "NewsTable->photos:1",
        "Invalid",
        "Missing->",
        "->MissingTable"
    ]
    
    for test_case in test_cases:
        result = parse_imagefox_config(test_case)
        print(f"Input: '{test_case}' -> {result}")


def test_generate_search_query():
    """Test the search query generation function."""
    print("\n=== Testing generate_search_query ===")
    
    test_cases = [
        {
            "title": "Breaking News: Market Crash",
            "article": "The stock market experienced a significant downturn today as investors panic over economic uncertainty...",
            "expected_keywords": ["market", "crash", "stock"]
        },
        {
            "title": "Tech Innovation",
            "article": "A new artificial intelligence breakthrough has been announced by researchers at leading universities. The technology promises to revolutionize healthcare...",
            "expected_keywords": ["tech", "innovation", "artificial", "intelligence"]
        },
        {
            "title": "",
            "article": "Climate change continues to affect weather patterns globally. Scientists report increasing temperatures and extreme weather events.",
            "expected_keywords": ["climate", "change", "weather"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        query = generate_search_query(test_case["article"], test_case["title"])
        print(f"Test {i}:")
        print(f"  Title: '{test_case['title']}'")
        print(f"  Article: '{test_case['article'][:50]}...'")
        print(f"  Generated Query: '{query}'")
        print(f"  Expected Keywords: {test_case['expected_keywords']}")
        
        # Check if any expected keywords are in the query
        found_keywords = [kw for kw in test_case['expected_keywords'] if kw.lower() in query.lower()]
        print(f"  Found Keywords: {found_keywords}")
        print()


def test_agent_status():
    """Test agent status checking."""
    print("\n=== Testing check_agent_status ===")
    
    try:
        status = check_agent_status()
        print(f"Agent status: {'ENABLED' if status else 'DISABLED'}")
    except Exception as e:
        print(f"Error checking agent status: {e}")


def test_projects_query():
    """Test querying projects with imagefox field."""
    print("\n=== Testing projects query ===")
    
    try:
        # Query projects with imagefox field
        projects = projects_table.all(formula="AND({imagefox}, {turnedOn})")
        print(f"Found {len(projects)} projects with imagefox configuration")
        
        for project in projects:
            fields = project["fields"]
            print(f"Project: {fields.get('project', 'Unknown')}")
            print(f"  ImageFox Config: {fields.get('imagefox', 'None')}")
            print(f"  Base ID: {fields.get('baseID', 'None')}")
            print(f"  Turned On: {fields.get('turnedOn', False)}")
            print()
            
    except Exception as e:
        print(f"Error querying projects: {e}")


def test_customertimes_records():
    """Test querying records from customertimes project."""
    print("\n=== Testing customertimes records ===")
    
    try:
        # First find the customertimes project
        projects = projects_table.all(formula="AND({project}='customertimes', {imagefox})")
        
        if not projects:
            print("No customertimes project found with imagefox configuration")
            return
        
        project = projects[0]
        fields = project["fields"]
        print(f"Found customertimes project:")
        print(f"  ImageFox Config: {fields.get('imagefox', 'None')}")
        
        # Parse the configuration
        imagefox_config = parse_imagefox_config(fields.get('imagefox', ''))
        if not imagefox_config:
            print("Invalid imagefox configuration")
            return
            
        print(f"  Parsed Config: {imagefox_config}")
        
        # Connect to target table
        base_id = fields["baseID"]
        table_name = imagefox_config["table_name"]
        field_name = imagefox_config["field_name"]
        
        target_table = Table(AIRTABLE_API_KEY, base_id, table_name)
        
        # Query records that need images
        formula = f"AND({{Status}}='In Pipeline', NOT({{{field_name}}}), {{errors}} < 3)"
        print(f"Query formula: {formula}")
        
        records = target_table.all(formula=formula)
        print(f"Found {len(records)} records needing images")
        
        # Show first few records
        for i, record in enumerate(records[:3], 1):
            record_fields = record["fields"]
            print(f"\nRecord {i}:")
            print(f"  ID: {record_fields.get('id', 'None')}")
            print(f"  Title: {record_fields.get('title', 'None')[:50]}...")
            print(f"  Status: {record_fields.get('Status', 'None')}")
            print(f"  Has Article: {'Yes' if record_fields.get('article') else 'No'}")
            print(f"  Article Preview: {record_fields.get('article', '')[:100]}...")
            
            # Generate search query for this record
            if record_fields.get('article'):
                search_query = generate_search_query(
                    record_fields.get('article', ''), 
                    record_fields.get('title', '')
                )
                print(f"  Generated Query: '{search_query}'")
        
    except Exception as e:
        print(f"Error testing customertimes records: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests."""
    print("ImageFox Agent Test Suite")
    print("=" * 50)
    
    # Test individual functions
    test_parse_imagefox_config()
    test_generate_search_query()
    test_agent_status()
    test_projects_query()
    test_customertimes_records()
    
    print("\n" + "=" * 50)
    print("Test suite completed")


if __name__ == "__main__":
    asyncio.run(main())