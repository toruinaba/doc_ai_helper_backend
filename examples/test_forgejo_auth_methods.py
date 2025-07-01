#!/usr/bin/env python3
"""
Forgejo authentication methods test script.
Tests different authentication methods to find the correct one.
"""

import os
import asyncio
import httpx
from typing import Dict, Optional


class ForgejoAuthTester:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.client = httpx.AsyncClient(timeout=10.0)

    async def test_auth_method_1_token(self) -> bool:
        """Test method 1: Authorization: token XXXXX"""
        headers = {"Authorization": f"token {self.token}"}
        return await self._test_auth(headers, "Method 1: token header")

    async def test_auth_method_2_bearer(self) -> bool:
        """Test method 2: Authorization: Bearer XXXXX"""
        headers = {"Authorization": f"Bearer {self.token}"}
        return await self._test_auth(headers, "Method 2: Bearer header")

    async def test_auth_method_3_query_param(self) -> bool:
        """Test method 3: URL query parameter ?token=XXXXX"""
        url = f"{self.base_url}/api/v1/user?token={self.token}"
        return await self._test_auth_with_url(url, "Method 3: query parameter")

    async def test_auth_method_4_custom_header(self) -> bool:
        """Test method 4: Custom token header"""
        headers = {"token": self.token}
        return await self._test_auth(headers, "Method 4: custom token header")

    async def test_auth_method_5_x_token(self) -> bool:
        """Test method 5: X-Token header"""
        headers = {"X-Token": self.token}
        return await self._test_auth(headers, "Method 5: X-Token header")

    async def _test_auth(self, headers: Dict[str, str], method_name: str) -> bool:
        """Test authentication with given headers."""
        try:
            print(f"\n🔐 Testing {method_name}")
            print(f"   Headers: {headers}")

            response = await self.client.get(
                f"{self.base_url}/api/v1/user", headers=headers
            )

            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                user_data = response.json()
                print(f"   ✅ SUCCESS! User: {user_data.get('login', 'unknown')}")
                return True
            else:
                print(f"   ❌ Failed: {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    async def _test_auth_with_url(self, url: str, method_name: str) -> bool:
        """Test authentication with URL parameters."""
        try:
            print(f"\n🔐 Testing {method_name}")
            print(f"   URL: {url}")

            response = await self.client.get(url)

            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                user_data = response.json()
                print(f"   ✅ SUCCESS! User: {user_data.get('login', 'unknown')}")
                return True
            else:
                print(f"   ❌ Failed: {response.text}")
                return False

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False

    async def test_all_methods(self):
        """Test all authentication methods."""
        print("🔐 Testing Forgejo Authentication Methods")
        print("=" * 50)

        methods = [
            self.test_auth_method_1_token,
            self.test_auth_method_2_bearer,
            self.test_auth_method_3_query_param,
            self.test_auth_method_4_custom_header,
            self.test_auth_method_5_x_token,
        ]

        successful_methods = []

        for method in methods:
            success = await method()
            if success:
                successful_methods.append(method.__name__)

        print("\n" + "=" * 50)
        if successful_methods:
            print(f"✅ Successful authentication methods:")
            for method in successful_methods:
                print(f"   - {method}")
        else:
            print("❌ No authentication methods worked!")
            print("   Please check:")
            print("   1. Token is valid and not expired")
            print("   2. Token has appropriate permissions")
            print("   3. Forgejo server configuration")

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()


async def main():
    """Main function."""
    # Load configuration from environment
    base_url = os.getenv("FORGEJO_BASE_URL")
    token = os.getenv("FORGEJO_TOKEN")

    if not base_url or not token:
        print("❌ Please set FORGEJO_BASE_URL and FORGEJO_TOKEN environment variables")
        return

    print(f"🎯 Testing Forgejo server: {base_url}")
    print(f"🔑 Token: {token[:10]}..." if len(token) > 10 else f"🔑 Token: {token}")

    tester = ForgejoAuthTester(base_url, token)
    try:
        await tester.test_all_methods()
    finally:
        await tester.close()


if __name__ == "__main__":
    # Load environment variables from .env file
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(main())
