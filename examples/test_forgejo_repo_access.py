#!/usr/bin/env python3
"""
Test Forgejo repository content access with current token.
"""

import os
import asyncio
import httpx
import json


async def test_repo_access(client: httpx.AsyncClient, base_url: str, token: str):
    """Test repository access with current token."""
    headers = {"Authorization": f"token {token}"}

    print("🔍 Testing repository access...")

    # First, get list of available repositories
    print("\n1. Getting repository list...")
    try:
        search_url = f"{base_url}/api/v1/repos/search"
        response = await client.get(search_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            repos = data.get("data", [])
            print(f"   ✅ Found {len(repos)} repositories")

            if repos:
                # Show first few repositories
                print("   📋 Available repositories:")
                for i, repo in enumerate(repos[:5]):  # Show first 5
                    print(
                        f"      {i+1}. {repo.get('owner', {}).get('login', 'unknown')}/{repo.get('name', 'unknown')}"
                    )

                # Test access to first repository
                if repos:
                    first_repo = repos[0]
                    owner = first_repo.get("owner", {}).get("login", "")
                    repo_name = first_repo.get("name", "")

                    if owner and repo_name:
                        await test_specific_repo(
                            client, base_url, token, owner, repo_name
                        )
            else:
                print("   ⚠️  No repositories found")
        else:
            print(f"   ❌ Failed to get repository list: {response.status_code}")
            print(f"      {response.text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")


async def test_specific_repo(
    client: httpx.AsyncClient, base_url: str, token: str, owner: str, repo_name: str
):
    """Test access to a specific repository."""
    headers = {"Authorization": f"token {token}"}

    print(f"\n2. Testing repository: {owner}/{repo_name}")

    # Test repository info
    try:
        repo_url = f"{base_url}/api/v1/repos/{owner}/{repo_name}"
        response = await client.get(repo_url, headers=headers)
        if response.status_code == 200:
            print("   ✅ Repository info accessible")
            repo_data = response.json()
            print(f"      Name: {repo_data.get('name')}")
            print(
                f"      Description: {repo_data.get('description', 'No description')}"
            )
            print(f"      Private: {repo_data.get('private', False)}")
        else:
            print(f"   ❌ Repository info failed: {response.status_code}")
            print(f"      {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Error getting repository info: {e}")
        return

    # Test repository contents (root directory)
    try:
        contents_url = f"{base_url}/api/v1/repos/{owner}/{repo_name}/contents"
        response = await client.get(contents_url, headers=headers)
        if response.status_code == 200:
            print("   ✅ Repository contents accessible")
            contents = response.json()
            print(f"      Found {len(contents)} items in root directory:")
            for item in contents[:10]:  # Show first 10 items
                item_type = "📁" if item.get("type") == "dir" else "📄"
                print(f"         {item_type} {item.get('name')}")

            # Try to get a markdown file if available
            md_files = [
                item for item in contents if item.get("name", "").endswith(".md")
            ]
            if md_files:
                md_file = md_files[0]
                await test_file_content(
                    client, base_url, token, owner, repo_name, md_file.get("name", "")
                )

        else:
            print(f"   ❌ Repository contents failed: {response.status_code}")
            print(f"      {response.text}")
    except Exception as e:
        print(f"   ❌ Error getting repository contents: {e}")


async def test_file_content(
    client: httpx.AsyncClient,
    base_url: str,
    token: str,
    owner: str,
    repo_name: str,
    file_path: str,
):
    """Test access to a specific file."""
    headers = {"Authorization": f"token {token}"}

    print(f"\n3. Testing file access: {file_path}")

    try:
        file_url = f"{base_url}/api/v1/repos/{owner}/{repo_name}/contents/{file_path}"
        response = await client.get(file_url, headers=headers)
        if response.status_code == 200:
            print("   ✅ File content accessible")
            file_data = response.json()
            print(f"      Name: {file_data.get('name')}")
            print(f"      Size: {file_data.get('size')} bytes")
            print(f"      Encoding: {file_data.get('encoding')}")

            # Try to decode content if it's base64
            if file_data.get("encoding") == "base64":
                import base64

                try:
                    content = base64.b64decode(file_data.get("content", "")).decode(
                        "utf-8"
                    )
                    print(f"      Content preview (first 200 chars):")
                    print(f"      {content[:200]}...")
                except Exception as decode_error:
                    print(f"      ⚠️  Could not decode content: {decode_error}")
        else:
            print(f"   ❌ File access failed: {response.status_code}")
            print(f"      {response.text}")
    except Exception as e:
        print(f"   ❌ Error getting file content: {e}")


async def main():
    """Main function."""
    base_url = os.getenv("FORGEJO_BASE_URL", "").rstrip("/")
    token = os.getenv("FORGEJO_TOKEN", "")

    if not base_url or not token:
        print("❌ Please set FORGEJO_BASE_URL and FORGEJO_TOKEN environment variables")
        return

    print(f"🎯 Testing Forgejo repository access: {base_url}")
    print(f"🔑 Token: {token[:10]}..." if len(token) > 10 else f"🔑 Token: {token}")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=15.0) as client:
        await test_repo_access(client, base_url, token)

    print("\n" + "=" * 60)
    print("🎉 Repository access test completed!")


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    asyncio.run(main())
