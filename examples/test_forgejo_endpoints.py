#!/usr/bin/env python3
"""
Test Forgejo with different endpoints to find what works with current token.
"""

import os
import asyncio
import httpx
from typing import List, Tuple


async def test_endpoint(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    endpoint: str,
    description: str,
) -> Tuple[bool, str]:
    """Test a specific endpoint with token authentication."""
    headers = {"Authorization": f"token {token}"}
    url = f"{base_url}/api/v1{endpoint}"

    try:
        print(f"\n🔍 Testing {description}")
        print(f"   URL: {url}")

        response = await client.get(url, headers=headers)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            print(f"   ✅ SUCCESS!")
            data = response.json()
            if isinstance(data, list):
                print(f"   📊 Found {len(data)} items")
            elif isinstance(data, dict):
                print(f"   📊 Response keys: {list(data.keys())}")
            return True, "Success"
        elif response.status_code == 404:
            print(f"   ⚠️  Endpoint not found")
            return False, "Not found"
        elif response.status_code == 403:
            error_msg = response.text
            print(f"   ❌ Forbidden: {error_msg}")
            return False, f"Forbidden: {error_msg}"
        else:
            print(f"   ❌ Error: {response.text}")
            return False, f"Error {response.status_code}: {response.text}"

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False, f"Exception: {e}"


async def main():
    """Test various endpoints to find what works."""
    base_url = os.getenv("FORGEJO_BASE_URL", "").rstrip("/")
    token = os.getenv("FORGEJO_TOKEN", "")

    if not base_url or not token:
        print("❌ Please set FORGEJO_BASE_URL and FORGEJO_TOKEN environment variables")
        return

    print(f"🎯 Testing Forgejo endpoints: {base_url}")
    print(f"🔑 Token: {token[:10]}..." if len(token) > 10 else f"🔑 Token: {token}")

    # Test various endpoints from least to most privileged
    endpoints = [
        ("/version", "Server version (public)"),
        ("/repos/search", "Repository search (may be public)"),
        ("/user", "Current user info (needs read:user)"),
        ("/user/repos", "User repositories (needs read:repository)"),
        ("/orgs", "Organizations (needs read:organization)"),
    ]

    successful_endpoints = []

    async with httpx.AsyncClient(timeout=10.0) as client:
        print("\n" + "=" * 60)
        print("Testing endpoints with current token...")
        print("=" * 60)

        for endpoint, description in endpoints:
            success, message = await test_endpoint(
                client, base_url, token, endpoint, description
            )
            if success:
                successful_endpoints.append((endpoint, description))

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)

        if successful_endpoints:
            print("✅ Working endpoints:")
            for endpoint, description in successful_endpoints:
                print(f"   - {endpoint}: {description}")
        else:
            print("❌ No endpoints worked with current token!")

        print("\n💡 Recommendations:")
        if not successful_endpoints:
            print("   1. Create a new token with broader permissions")
            print("   2. Include at least: read:user, read:repository")
            print("   3. Check token expiration date")
        elif len(successful_endpoints) < 3:
            print("   1. Token works but has limited permissions")
            print("   2. Consider adding more scopes for full functionality")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(main())
