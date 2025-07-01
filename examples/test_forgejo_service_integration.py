#!/usr/bin/env python3
"""
Test Forgejo service integration with actual document retrieval.
"""

import os
import asyncio
from dotenv import load_dotenv

# Add the project root to the path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doc_ai_helper_backend.services.git.factory import GitServiceFactory


async def test_forgejo_service():
    """Test Forgejo service with actual document retrieval."""

    print("🚀 Testing Forgejo Service Integration")
    print("=" * 50)

    # Load configuration
    base_url = os.getenv("FORGEJO_BASE_URL")
    token = os.getenv("FORGEJO_TOKEN")

    if not base_url or not token:
        print("❌ Please set FORGEJO_BASE_URL and FORGEJO_TOKEN")
        return

    print(f"🎯 Server: {base_url}")
    print(f"🔑 Token: {token[:10]}...")

    try:
        # Create Forgejo service via factory
        print("\n1️⃣ Creating Forgejo service...")
        service = GitServiceFactory.create(
            "forgejo", base_url=base_url, access_token=token
        )
        print("   ✅ Service created successfully")

        # Test connection
        print("\n2️⃣ Testing connection...")
        connection_result = await service.test_connection()
        print(f"   📊 Connection result: {connection_result}")

        if not connection_result.get("authenticated"):
            print("   ❌ Authentication failed")
            return

        print("   ✅ Connection and authentication successful")

        # Test repository listing (from previous manual test we know there's a repo)
        print("\n3️⃣ Testing repository discovery...")

        # We know from manual test that there's a repo: toruinaba/gikenDocGen
        owner = "toruinaba"
        repo = "gikenDocGen"

        # Check if repository exists
        exists = await service.check_repository_exists(owner, repo)
        print(f"   📋 Repository {owner}/{repo} exists: {exists}")

        if not exists:
            print("   ❌ Repository not found")
            return

        # Test document retrieval
        print("\n4️⃣ Testing document retrieval...")

        try:
            document = await service.get_document(
                owner=owner, repo=repo, path="README.md", ref="main"
            )

            print("   ✅ Document retrieved successfully!")
            print(f"   📄 File: {document.name}")
            print(f"   📏 Size: {document.metadata.size} bytes")
            print(f"   📝 Content preview: {document.content.content[:100]}...")

        except Exception as e:
            print(f"   ❌ Document retrieval failed: {e}")

        # Test repository structure
        print("\n5️⃣ Testing repository structure...")

        try:
            structure = await service.get_repository_structure(
                owner=owner, repo=repo, ref="main"
            )

            print("   ✅ Repository structure retrieved!")
            print(f"   📁 Found {len(structure.tree)} files")
            for file in structure.tree[:5]:  # Show first 5
                print(f"      - {file.name} ({file.type})")

        except Exception as e:
            print(f"   ❌ Structure retrieval failed: {e}")

        print("\n" + "=" * 50)
        print("🎉 Forgejo service integration test completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_forgejo_service())
