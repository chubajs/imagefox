#!/usr/bin/env python3
"""Link Linear issues to a project."""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict
import argparse
from tabulate import tabulate
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored output
init(autoreset=True)

# Load environment variables from parent directory
parent_dir = Path(__file__).parent.parent
env_path = parent_dir / '.env'
load_dotenv(env_path)

# Linear API configuration
LINEAR_API_KEY = os.getenv('LINEAR_API_KEY')
LINEAR_API_URL = 'https://api.linear.app/graphql'

if not LINEAR_API_KEY:
    print(f"{Fore.RED}Error: LINEAR_API_KEY not found in environment variables")
    sys.exit(1)

headers = {
    'Authorization': LINEAR_API_KEY,
    'Content-Type': 'application/json'
}

def get_team_issues(team_id: str, identifiers: List[str] = None) -> List[Dict]:
    """Get team issues, optionally filtered by identifiers."""
    query = """
    query GetTeamIssues($teamId: String!) {
        team(id: $teamId) {
            issues(first: 100) {
                nodes {
                    id
                    identifier
                    title
                    project {
                        id
                        name
                    }
                }
            }
        }
    }
    """
    
    variables = {"teamId": team_id}
    
    response = requests.post(
        LINEAR_API_URL,
        headers=headers,
        json={'query': query, 'variables': variables}
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"{Fore.RED}GraphQL Errors: {data['errors']}")
            return []
        
        issues = data.get('data', {}).get('team', {}).get('issues', {}).get('nodes', [])
        
        # Filter by identifiers if provided
        if identifiers:
            issues = [i for i in issues if i['identifier'] in identifiers]
        
        return issues
    else:
        print(f"{Fore.RED}API Error: {response.status_code}")
        print(response.text)
        return []

def link_issue_to_project(issue_id: str, project_id: str) -> bool:
    """Link an issue to a project."""
    mutation = """
    mutation LinkIssueToProject($issueId: String!, $projectId: String!) {
        issueUpdate(id: $issueId, input: { projectId: $projectId }) {
            success
            issue {
                id
                identifier
                title
                project {
                    id
                    name
                }
            }
        }
    }
    """
    
    variables = {
        "issueId": issue_id,
        "projectId": project_id
    }
    
    response = requests.post(
        LINEAR_API_URL,
        headers=headers,
        json={'query': mutation, 'variables': variables}
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"{Fore.RED}Error linking issue: {data['errors']}")
            return False
        
        result = data.get('data', {}).get('issueUpdate', {})
        if result.get('success'):
            issue = result.get('issue', {})
            project = issue.get('project', {})
            if project and project.get('id') == project_id:
                return True
        return False
    else:
        print(f"{Fore.RED}API Error: {response.status_code}")
        return False

def bulk_link_issues(team_id: str, project_id: str, identifiers: List[str] = None) -> None:
    """Link multiple issues to a project."""
    print(f"{Fore.CYAN}Fetching issues from team...")
    issues = get_team_issues(team_id, identifiers)
    
    if not issues:
        print(f"{Fore.YELLOW}No issues found")
        return
    
    print(f"{Fore.GREEN}Found {len(issues)} issues")
    print(f"{Fore.CYAN}Linking issues to project {project_id}...")
    
    results = []
    for issue in issues:
        issue_id = issue['id']
        identifier = issue['identifier']
        title = issue['title'][:50] + ('...' if len(issue['title']) > 50 else '')
        
        # Check current project
        current_project = issue.get('project', {})
        if current_project and current_project.get('id') == project_id:
            results.append([identifier, title, '✓ Already linked'])
            continue
        
        # Link to project
        success = link_issue_to_project(issue_id, project_id)
        status = '✓ Linked' if success else '✗ Failed'
        results.append([identifier, title, status])
    
    # Display results
    print("\n" + "=" * 80)
    print(tabulate(results, headers=['Issue', 'Title', 'Status'], tablefmt='grid'))
    print("=" * 80)
    
    # Summary
    success_count = sum(1 for r in results if '✓ Linked' in r[2])
    failed_count = sum(1 for r in results if '✗' in r[2])
    skipped_count = sum(1 for r in results if 'Already' in r[2])
    
    print(f"\n{Fore.GREEN}Summary:")
    print(f"  Linked: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Already linked: {skipped_count}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Link Linear issues to a project')
    parser.add_argument('--team-id', '-t', required=True, help='Linear team ID')
    parser.add_argument('--project-id', '-p', required=True, help='Linear project ID')
    parser.add_argument('--issues', '-i', nargs='+', help='Specific issue identifiers (e.g., SER-33 SER-34)')
    parser.add_argument('--range', '-r', help='Issue range (e.g., "SER-33:SER-50")')
    
    args = parser.parse_args()
    
    # Determine which issues to link
    identifiers = None
    if args.issues:
        identifiers = args.issues
    elif args.range and ':' in args.range:
        # Parse range like "SER-33:SER-50"
        start, end = args.range.split(':')
        prefix = start.rsplit('-', 1)[0]
        start_num = int(start.rsplit('-', 1)[1])
        end_num = int(end.rsplit('-', 1)[1])
        identifiers = [f"{prefix}-{i}" for i in range(start_num, end_num + 1)]
        print(f"{Fore.CYAN}Processing range: {identifiers[0]} to {identifiers[-1]}")
    
    # Link the issues
    bulk_link_issues(args.team_id, args.project_id, identifiers)
    return 0

if __name__ == "__main__":
    sys.exit(main())