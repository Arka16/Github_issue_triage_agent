#!/usr/bin/env python3
"""Test script for GitHub service methods."""

import asyncio
import sys
from dotenv import load_dotenv
from src.config import Settings
from src.github_service import GitHubService

# Load environment variables
load_dotenv()


async def test_github_service():
    """Test all GitHub service methods."""
    print("=" * 60)
    print("GitHub Service Test")
    print("=" * 60)

    # Load configuration
    try:
        settings = Settings.load()
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return False

    # Create service
    gh = GitHubService(
        token=settings.github_token,
        repo_full_name=settings.repo_full_name,
        fetch_limit=settings.issue_fetch_limit,
    )

    print(f"\n✓ Testing with repo: {settings.repo_full_name}")

    # Test 1: Get labels
    print("\n--- Test 1: Get Labels ---")
    labels = await gh.get_labels()
    if labels:
        print(f"✓ Found {len(labels)} labels")
        print(f"  Sample labels: {labels[:5]}")
    else:
        print("✗ No labels found (repo may have no labels)")

    # Test 2: Get open issues
    print("\n--- Test 2: Get Open Issues ---")
    issues = await gh.get_open_issues()
    if issues:
        print(f"✓ Found {len(issues)} open issues")
        if issues:
            issue = issues[0]
            print(f"  Most recent: #{issue['number']} - {issue['title']}")
            print(f"  Body preview: {issue['body'][:50]}...")
            print(f"  Labels: {issue['labels']}")
    else:
        print("✗ No open issues found (or repo has no issues)")

    # Test 3: Get specific issue (use first open issue if available)
    if issues:
        issue_number = issues[0]["number"]
        print(f"\n--- Test 3: Get Specific Issue (#{issue_number}) ---")
        issue = await gh.get_issue(issue_number)
        if issue:
            print(f"✓ Fetched issue #{issue['number']}")
            print(f"  Title: {issue['title']}")
            print(f"  Author: {issue['author']}")
            print(f"  Body length: {len(issue['body'])} chars")
            print(f"  Labels: {issue['labels']}")
        else:
            print(f"✗ Failed to fetch issue #{issue_number}")
    else:
        print("\n--- Test 3: Get Specific Issue ---")
        print("⊘ Skipped (no open issues to test with)")

    # Test 4: Check if we can apply labels (dry run - won't actually apply)
    if issues and labels:
        print("\n--- Test 4: Label Application Ready ---")
        print(f"✓ Can apply labels from available set: {labels[:3]}")
        print("  (Not actually applying to avoid modifying your repo)")
    else:
        print("\n--- Test 4: Label Application Ready ---")
        print("⊘ Skipped (need both issues and labels)")

    print("\n" + "=" * 60)
    print("GitHub Service Test Complete")
    print("=" * 60)
    return True


async def main():
    """Run async tests."""
    try:
        success = await test_github_service()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
