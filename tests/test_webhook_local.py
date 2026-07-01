#!/usr/bin/env python3
"""Local webhook testing script - simulates GitHub webhook payloads."""

import json
import requests
import time
import subprocess
import signal
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
WEBHOOK_ENDPOINT = f"{BASE_URL}/webhook"

# Mock GitHub webhook payloads
def mock_issue_opened_webhook(issue_number=42, repo="owner/repo"):
    """Create a mock 'issue opened' webhook payload."""
    return {
        "action": "opened",
        "issue": {
            "number": issue_number,
            "title": "Test issue title",
            "body": "This is a test issue body"
        },
        "repository": {
            "full_name": repo
        }
    }


def test_health_endpoint():
    """Test the /health endpoint."""
    print("\n✓ Testing GET /health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "ok", f"Expected status=ok, got {data}"
        print(f"  ✓ Response: {data}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_root_endpoint():
    """Test the root / endpoint."""
    print("\n✓ Testing GET /...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "status" in data, "Missing 'status' in response"
        assert "repo" in data, "Missing 'repo' in response"
        print(f"  ✓ Response: {data}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_webhook_correct_repo():
    """Test webhook with correct repo."""
    print("\n✓ Testing POST /webhook (correct repo, 'opened' action)...")
    try:
        payload = mock_issue_opened_webhook(issue_number=123)
        # Override repo to match config (you'll need to adjust this)
        payload["repository"]["full_name"] = os.getenv("REPO_FULL_NAME", "owner/repo")

        response = requests.post(
            WEBHOOK_ENDPOINT,
            json=payload,
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "webhook received", f"Expected 'webhook received', got {data}"
        print(f"  ✓ Response: {data}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_webhook_wrong_repo():
    """Test webhook with wrong repo (should be ignored)."""
    print("\n✓ Testing POST /webhook (wrong repo)...")
    try:
        payload = mock_issue_opened_webhook(issue_number=124, repo="different/repo")
        response = requests.post(
            WEBHOOK_ENDPOINT,
            json=payload,
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "ignored", f"Expected 'ignored', got {data}"
        print(f"  ✓ Response: {data}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def test_webhook_wrong_action():
    """Test webhook with wrong action (should be ignored)."""
    print("\n✓ Testing POST /webhook (wrong action)...")
    try:
        payload = mock_issue_opened_webhook(issue_number=125)
        payload["action"] = "closed"  # Not 'opened'
        payload["repository"]["full_name"] = os.getenv("REPO_FULL_NAME", "owner/repo")

        response = requests.post(
            WEBHOOK_ENDPOINT,
            json=payload,
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data["status"] == "ignored", f"Expected 'ignored', got {data}"
        print(f"  ✓ Response: {data}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return False


def wait_for_server(max_retries=10, delay=1):
    """Wait for server to start."""
    print(f"Waiting for server to start on {BASE_URL}...")
    for i in range(max_retries):
        try:
            requests.get(f"{BASE_URL}/health", timeout=2)
            print("✓ Server is running!")
            return True
        except:
            if i < max_retries - 1:
                print(f"  Attempt {i+1}/{max_retries}... waiting {delay}s")
                time.sleep(delay)
    print("✗ Server failed to start")
    return False


def main():
    """Run all webhook tests."""
    print("=" * 60)
    print("GitHub Issue Triage Agent - Local Webhook Test")
    print("=" * 60)

    # Wait for server
    if not wait_for_server():
        print("\nMake sure to start the server first:")
        print("  python main.py")
        sys.exit(1)

    # Run tests
    results = []
    results.append(("Health check", test_health_endpoint()))
    results.append(("Root endpoint", test_root_endpoint()))
    results.append(("Webhook (correct repo)", test_webhook_correct_repo()))
    results.append(("Webhook (wrong repo)", test_webhook_wrong_repo()))
    results.append(("Webhook (wrong action)", test_webhook_wrong_action()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
