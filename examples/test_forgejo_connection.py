#!/usr/bin/env python3
"""
Forgejo Server Connection Test

This script tests the connection to your Forgejo server with the configured settings.
Run this after setting up your .env file to verify connectivity.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from doc_ai_helper_backend.services.git.factory import GitServiceFactory
    from doc_ai_helper_backend.core.config import settings
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this script from the project root directory.")
    sys.exit(1)


async def test_forgejo_connection():
    """Test Forgejo server connection with current settings."""

    print("=" * 60)
    print("🔧 Forgejo Server Connection Test")
    print("=" * 60)

    # 1. Check configuration
    print("\n📋 Configuration Check:")
    print(f"  Base URL: {settings.forgejo_base_url or '❌ NOT SET'}")
    print(f"  Token: {'✅ SET' if settings.forgejo_token else '❌ NOT SET'}")
    print(f"  Username: {'✅ SET' if settings.forgejo_username else '❌ NOT SET'}")
    print(f"  Password: {'✅ SET' if settings.forgejo_password else '❌ NOT SET'}")

    if not settings.forgejo_base_url:
        print("\n❌ FORGEJO_BASE_URL is required. Please set it in your .env file.")
        return False

    # 2. Test service creation
    print("\n🏗️  Service Creation Test:")
    try:
        service = GitServiceFactory.create("forgejo")
        print("  ✅ Forgejo service created successfully")
        print(f"  📍 Service URL: {service.base_url}")
        print(f"  🔐 Auth methods: {service.get_supported_auth_methods()}")
    except Exception as e:
        print(f"  ❌ Failed to create service: {e}")
        return False

    # 3. Test authentication
    print("\n🔐 Authentication Test:")
    try:
        auth_result = await service.authenticate()
        if auth_result:
            print("  ✅ Authentication successful")
        else:
            print("  ❌ Authentication failed")
            return False
    except Exception as e:
        print(f"  ❌ Authentication error: {e}")
        return False

    # 4. Test connection
    print("\n🌐 Connection Test:")
    try:
        connection_result = await service.test_connection()
        if connection_result.get("status") == "success":
            print("  ✅ Connection test passed")
            print(f"  📊 Rate limit info: {connection_result.get('rate_limit', {})}")
        else:
            print(
                f"  ❌ Connection test failed: {connection_result.get('error', 'Unknown error')}"
            )
            return False
    except Exception as e:
        print(f"  ❌ Connection error: {e}")
        return False

    # 5. Test basic API call (optional)
    print("\n📡 API Test (Repository List):")
    try:
        # Try to check if a test repository exists
        exists = await service.check_repository_exists("test", "test")
        print(f"  ✅ API call successful (test/test exists: {exists})")
    except Exception as e:
        print(f"  ⚠️  API test failed (this may be normal): {e}")

    print("\n🎉 All tests completed successfully!")
    return True


def print_setup_instructions():
    """Print setup instructions for Forgejo configuration."""

    print("\n" + "=" * 60)
    print("📖 SETUP INSTRUCTIONS")
    print("=" * 60)

    print("\n1. 📁 Create .env file:")
    print("   Copy .env.forgejo.example to .env")
    print("   cp .env.forgejo.example .env")

    print("\n2. 🔧 Configure Forgejo settings in .env:")
    print("   FORGEJO_BASE_URL=https://your-forgejo-server.com")
    print("   FORGEJO_TOKEN=your_access_token_here")

    print("\n3. 🔑 Create Forgejo access token:")
    print("   - Log into your Forgejo server")
    print("   - Go to Settings → Applications → Access Tokens")
    print("   - Create new token with 'repository' scope")
    print("   - Copy the token to FORGEJO_TOKEN in .env")

    print("\n4. 🧪 Run this test again:")
    print("   python examples/test_forgejo_connection.py")


if __name__ == "__main__":
    # Check if .env file exists
    env_file = project_root / ".env"

    if not env_file.exists():
        print("❌ .env file not found!")
        print_setup_instructions()
        sys.exit(1)

    # Run the test
    try:
        result = asyncio.run(test_forgejo_connection())
        if not result:
            print("\n💡 Check your configuration and try again.")
            print_setup_instructions()
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)
