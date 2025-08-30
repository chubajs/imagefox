#!/usr/bin/env python3
"""Create Linear project for ImageFox."""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from parent directory
parent_dir = Path(__file__).parent.parent
env_path = parent_dir / '.env'
load_dotenv(env_path)

# Also try loading from storyteller if not found
if not os.getenv('LINEAR_API_KEY'):
    storyteller_env = Path('/home/sbulaev/storyteller/.env')
    if storyteller_env.exists():
        load_dotenv(storyteller_env, override=True)

# Linear API configuration
LINEAR_API_KEY = os.getenv('LINEAR_API_KEY')
LINEAR_API_URL = 'https://api.linear.app/graphql'

if not LINEAR_API_KEY:
    print("Error: LINEAR_API_KEY not found in environment variables")
    sys.exit(1)

headers = {
    'Authorization': LINEAR_API_KEY,
    'Content-Type': 'application/json'
}

def create_project():
    """Create ImageFox project in Linear."""
    
    # GraphQL mutation to create project
    mutation = """
    mutation CreateProject($name: String!, $teamIds: [String!]!, $description: String!) {
        projectCreate(input: {
            name: $name,
            teamIds: $teamIds,
            description: $description,
            color: "#FF6B35",
            state: "started"
        }) {
            success
            project {
                id
                name
                description
                url
            }
        }
    }
    """
    
    variables = {
        "name": "Co.Actor Scale (ImageFox)",
        "teamIds": ["a168f90b-ba6c-41d9-87ed-4db05ba428a7"],  # Serge & Agents team ID
        "description": "AI-powered intelligent image search and selection agent using Apify for Google image search, OpenRouter LLMs for vision analysis, and Airtable/ImageBB for storage. Part of the Co.Actor Scale content generation ecosystem."
    }
    
    response = requests.post(
        LINEAR_API_URL,
        headers=headers,
        json={'query': mutation, 'variables': variables}
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"GraphQL Errors: {data['errors']}")
            return None
        
        if data.get('data', {}).get('projectCreate', {}).get('success'):
            project = data['data']['projectCreate']['project']
            print(f"✓ Project created successfully!")
            print(f"  Name: {project['name']}")
            print(f"  ID: {project['id']}")
            print(f"  URL: {project['url']}")
            print(f"  Description: {project['description']}")
            return project
        else:
            print("Failed to create project")
            return None
    else:
        print(f"API Error: {response.status_code}")
        print(response.text)
        return None

def main():
    """Main function."""
    print("Creating Linear project for ImageFox...")
    print("-" * 50)
    
    project = create_project()
    
    if project:
        print("\n" + "=" * 50)
        print("Project created! Add this to ImageFox CLAUDE.md:")
        print(f"- **Project Name**: {project['name']}")
        print(f"- **Project ID**: `{project['id']}`")
        print(f"- **Team**: Serge & Agents (ID: `a168f90b-ba6c-41d9-87ed-4db05ba428a7`)")
        print(f"- **URL**: {project['url']}")
        print("=" * 50)
        return 0
    else:
        print("Failed to create project")
        return 1

if __name__ == "__main__":
    sys.exit(main())