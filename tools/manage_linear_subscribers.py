#!/usr/bin/env python3
"""Manage Linear issue subscribers - add or remove subscribers from issues."""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Optional
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

# Known user IDs (can be extended)
KNOWN_USERS = {
    'claude': '64a87888-93a6-4c13-bdac-d3bec9cc7f5d',
    'sbulaev': 'f6869754-5429-4298-a825-ae506cf4e71e',
    'serge': 'f6869754-5429-4298-a825-ae506cf4e71e'  # alias
}

def get_user_id_by_email(email: str) -> Optional[str]:
    """Get Linear user ID by email address."""
    query = """
    query GetUsers {
        users {
            nodes {
                id
                email
                name
            }
        }
    }
    """
    
    response = requests.post(
        LINEAR_API_URL,
        headers=headers,
        json={'query': query}
    )
    
    if response.status_code == 200:
        data = response.json()
        users = data.get('data', {}).get('users', {}).get('nodes', [])
        for user in users:
            if user['email'] == email:
                return user['id']
    return None

def get_project_issues(project_id: str) -> List[Dict]:
    """Get all issues in a project."""
    query = """
    query GetProjectIssues($projectId: String!) {
        project(id: $projectId) {
            issues {
                nodes {
                    id
                    identifier
                    title
                    subscribers {
                        nodes {
                            id
                            name
                            email
                        }
                    }
                }
            }
        }
    }
    """
    
    variables = {"projectId": project_id}
    
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
        
        project = data.get('data', {}).get('project', {})
        return project.get('issues', {}).get('nodes', [])
    else:
        print(f"{Fore.RED}API Error: {response.status_code}")
        print(response.text)
        return []

def add_subscriber_to_issue(issue_id: str, user_id: str, existing_subscriber_ids: List[str] = None) -> bool:
    """Add a subscriber to an issue."""
    # Build the subscriber list (existing + new)
    subscriber_ids = existing_subscriber_ids or []
    if user_id not in subscriber_ids:
        subscriber_ids.append(user_id)
    
    mutation = """
    mutation AddSubscriber($issueId: String!, $subscriberIds: [String!]!) {
        issueUpdate(id: $issueId, input: { subscriberIds: $subscriberIds }) {
            success
            issue {
                id
                identifier
                title
            }
        }
    }
    """
    
    variables = {
        "issueId": issue_id,
        "subscriberIds": subscriber_ids
    }
    
    response = requests.post(
        LINEAR_API_URL,
        headers=headers,
        json={'query': mutation, 'variables': variables}
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"{Fore.RED}Error adding subscriber: {data['errors']}")
            return False
        
        result = data.get('data', {}).get('issueUpdate', {})
        return result.get('success', False)
    else:
        print(f"{Fore.RED}API Error: {response.status_code}")
        return False

def remove_subscriber_from_issue(issue_id: str, user_id: str) -> bool:
    """Remove a subscriber from an issue."""
    mutation = """
    mutation RemoveSubscriber($issueId: String!, $userId: String!) {
        issueRemoveSubscriber(id: $issueId, userId: $userId) {
            success
            issue {
                id
                identifier
                title
            }
        }
    }
    """
    
    variables = {
        "issueId": issue_id,
        "userId": user_id
    }
    
    response = requests.post(
        LINEAR_API_URL,
        headers=headers,
        json={'query': mutation, 'variables': variables}
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'errors' in data:
            print(f"{Fore.RED}Error removing subscriber from {issue_id}: {data['errors']}")
            return False
        
        result = data.get('data', {}).get('issueRemoveSubscriber', {})
        return result.get('success', False)
    else:
        print(f"{Fore.RED}API Error: {response.status_code}")
        return False

def get_team_issues_by_pattern(team_id: str, title_pattern: Optional[str] = None, identifiers: Optional[List[str]] = None) -> List[Dict]:
    """Get team issues by title pattern or specific identifiers."""
    filter_str = ""
    if title_pattern:
        filter_str = f', filter: {{ title: {{ contains: "{title_pattern}" }} }}'
    
    query = f"""
    query GetTeamIssues($teamId: String!) {{
        team(id: $teamId) {{
            issues(first: 100{filter_str}) {{
                nodes {{
                    id
                    identifier
                    title
                    subscribers {{
                        nodes {{
                            id
                            name
                            email
                        }}
                    }}
                }}
            }}
        }}
    }}
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
        return []

def bulk_manage_subscribers(project_id: str, user_id: str, action: str = 'add') -> None:
    """Add or remove a subscriber from all issues in a project."""
    print(f"{Fore.CYAN}Fetching issues from project {project_id}...")
    issues = get_project_issues(project_id)
    
    if not issues:
        print(f"{Fore.YELLOW}No issues found in project")
        print(f"{Fore.CYAN}Trying to fetch by team and pattern instead...")
        # For ImageFox project, use known team ID and issue identifiers
        if project_id == 'a84c6a45-1304-45d5-8d46-d9c926248ec1':
            # ImageFox issues are SER-33 through SER-50
            identifiers = [f'SER-{i}' for i in range(33, 51)]
            issues = get_team_issues_by_pattern('a168f90b-ba6c-41d9-87ed-4db05ba428a7', identifiers=identifiers)
        else:
            return
    
    print(f"{Fore.GREEN}Found {len(issues)} issues")
    print(f"{Fore.CYAN}{'Adding' if action == 'add' else 'Removing'} subscriber...")
    
    results = []
    for issue in issues:
        issue_id = issue['id']
        identifier = issue['identifier']
        title = issue['title'][:50] + ('...' if len(issue['title']) > 50 else '')
        
        # Check if user is already subscribed
        current_subscribers = [sub['id'] for sub in issue.get('subscribers', {}).get('nodes', [])]
        is_subscribed = user_id in current_subscribers
        
        if action == 'add':
            if is_subscribed:
                results.append([identifier, title, '✓ Already subscribed'])
                continue
            
            success = add_subscriber_to_issue(issue_id, user_id, current_subscribers)
            status = '✓ Added' if success else '✗ Failed'
        else:  # remove
            if not is_subscribed:
                results.append([identifier, title, '- Not subscribed'])
                continue
            
            success = remove_subscriber_from_issue(issue_id, user_id)
            status = '✓ Removed' if success else '✗ Failed'
        
        results.append([identifier, title, status])
    
    # Display results
    print("\n" + "=" * 80)
    print(tabulate(results, headers=['Issue', 'Title', 'Status'], tablefmt='grid'))
    print("=" * 80)
    
    # Summary
    success_count = sum(1 for r in results if '✓' in r[2])
    failed_count = sum(1 for r in results if '✗' in r[2])
    skipped_count = sum(1 for r in results if 'Already' in r[2] or 'Not subscribed' in r[2])
    
    print(f"\n{Fore.GREEN}Summary:")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Skipped: {skipped_count}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Manage Linear issue subscribers')
    parser.add_argument('action', choices=['add', 'remove'], help='Action to perform')
    parser.add_argument('--project-id', '-p', required=True, help='Linear project ID')
    parser.add_argument('--user', '-u', help='User identifier (email, known name, or ID)')
    parser.add_argument('--user-id', help='Direct Linear user ID')
    parser.add_argument('--list-users', action='store_true', help='List known users')
    
    args = parser.parse_args()
    
    if args.list_users:
        print(f"{Fore.CYAN}Known users:")
        for name, user_id in KNOWN_USERS.items():
            print(f"  {name}: {user_id}")
        return 0
    
    # Determine user ID
    user_id = None
    if args.user_id:
        user_id = args.user_id
    elif args.user:
        # Check if it's a known user
        if args.user.lower() in KNOWN_USERS:
            user_id = KNOWN_USERS[args.user.lower()]
            print(f"{Fore.GREEN}Using known user: {args.user}")
        # Check if it's an email
        elif '@' in args.user:
            print(f"{Fore.CYAN}Looking up user by email: {args.user}")
            user_id = get_user_id_by_email(args.user)
            if user_id:
                print(f"{Fore.GREEN}Found user ID: {user_id}")
            else:
                print(f"{Fore.RED}User not found with email: {args.user}")
                return 1
        # Assume it's a user ID
        else:
            user_id = args.user
    else:
        print(f"{Fore.RED}Error: Must provide --user or --user-id")
        return 1
    
    # Perform the action
    bulk_manage_subscribers(args.project_id, user_id, args.action)
    return 0

if __name__ == "__main__":
    sys.exit(main())