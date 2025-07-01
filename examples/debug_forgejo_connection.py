#!/usr/bin/env python3
"""
Forgejo Connection Debug Tool

This script provides detailed debugging information for Forgejo connection issues.
It will help identify the specific cause of "Unknown error" messages.
"""

import asyncio
import sys
import traceback
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Set httpx logging to DEBUG to see network details
logging.getLogger("httpx").setLevel(logging.DEBUG)


async def debug_forgejo_connection():
    """Debug Forgejo connection with detailed error reporting."""

    print("🔧 Forgejo Connection Debug Tool")
    print("=" * 60)

    try:
        # Import with error handling
        from doc_ai_helper_backend.core.config import settings
        from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService

        print(f"📋 Configuration:")
        print(f"  Base URL: {settings.forgejo_base_url}")
        print(f"  Token: {'SET' if settings.forgejo_token else 'NOT SET'}")
        print(f"  Username: {'SET' if settings.forgejo_username else 'NOT SET'}")
        print(f"  Password: {'SET' if settings.forgejo_password else 'NOT SET'}")

        if not settings.forgejo_base_url:
            print("❌ FORGEJO_BASE_URL is not set!")
            return False

        print(f"\n🏗️  Creating service instance...")
        service = ForgejoService(
            base_url=settings.forgejo_base_url,
            access_token=settings.forgejo_token,
            username=settings.forgejo_username,
            password=settings.forgejo_password,
        )

        print(f"✅ Service created")
        print(f"  Final base URL: {service.base_url}")
        print(f"  API URL: {service.api_base_url}")
        print(f"  Auth methods: {service.get_supported_auth_methods()}")

        print(f"\n🌐 Testing basic connectivity...")

        # Test 1: Basic URL validation
        print(f"📍 Step 1: URL validation")
        try:
            import httpx

            # Test basic connectivity to the base URL
            async with httpx.AsyncClient(timeout=10.0) as client:
                print(f"  Testing base URL: {service.base_url}")
                response = await client.get(service.base_url)
                print(f"  ✅ Base URL accessible (Status: {response.status_code})")
        except Exception as e:
            print(f"  ❌ Base URL test failed: {type(e).__name__}: {str(e)}")
            return False

        # Test 2: API endpoint accessibility
        print(f"\n📍 Step 2: API endpoint test")
        try:
            version_url = f"{service.api_base_url}/version"
            async with httpx.AsyncClient(timeout=10.0) as client:
                print(f"  Testing API URL: {version_url}")
                response = await client.get(version_url)
                print(f"  ✅ API endpoint accessible (Status: {response.status_code})")
                if response.status_code == 200:
                    try:
                        version_data = response.json()
                        print(f"  📊 Server version: {version_data}")
                    except:
                        print(f"  📊 Response text: {response.text[:200]}...")
        except Exception as e:
            print(f"  ❌ API endpoint test failed: {type(e).__name__}: {str(e)}")
            print(f"      Full error: {traceback.format_exc()}")

        # Test 3: Authentication test
        print(f"\n📍 Step 3: Authentication test")
        try:
            auth_result = await service.authenticate()
            print(f"  Authentication result: {auth_result}")
            if auth_result:
                print(f"  ✅ Authentication successful")
            else:
                print(f"  ❌ Authentication failed")
        except Exception as e:
            print(f"  ❌ Authentication test failed: {type(e).__name__}: {str(e)}")
            print(f"      Full error: {traceback.format_exc()}")

        # Test 4: Connection test (the failing one)
        print(f"\n📍 Step 4: Service connection test")
        try:
            connection_result = await service.test_connection()
            print(f"  Connection result: {connection_result}")

            if connection_result.get("status") == "success":
                print(f"  ✅ Connection test successful")
                return True
            else:
                print(f"  ❌ Connection test failed")
                print(f"      Error: {connection_result.get('error', 'Unknown')}")
                return False

        except Exception as e:
            print(f"  ❌ Connection test exception: {type(e).__name__}: {str(e)}")
            print(f"      Full traceback:")
            print(f"      {traceback.format_exc()}")
            return False

    except ImportError as e:
        print(f"❌ Import error: {e}")
        print(f"   Make sure you're running from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {str(e)}")
        print(f"   Full traceback:")
        print(f"   {traceback.format_exc()}")
        return False


async def test_manual_connection():
    """Test connection with manual configuration (bypass settings)."""

    print("\n" + "=" * 60)
    print("🔧 Manual Connection Test")
    print("=" * 60)

    # Get configuration from user
    base_url = input("Enter Forgejo base URL (e.g., http://localhost:3000): ").strip()
    if not base_url:
        print("❌ Base URL is required")
        return False

    token = input("Enter Forgejo token (or press Enter to skip): ").strip()

    username = None
    password = None

    if not token:
        username = input("Enter username (or press Enter to skip): ").strip()
        if username:
            password = input("Enter password: ").strip()

    if not token and not (username and password):
        print("❌ Either token or username/password is required")
        return False

    try:
        from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService

        print(f"\n🏗️  Creating manual service instance...")
        service = ForgejoService(
            base_url=base_url,
            access_token=token if token else None,
            username=username if username else None,
            password=password if password else None,
        )

        print(f"✅ Manual service created")
        print(f"  Base URL: {service.base_url}")
        print(f"  API URL: {service.api_base_url}")

        print(f"\n🧪 Testing manual connection...")
        connection_result = await service.test_connection()

        print(f"📊 Manual connection result: {connection_result}")

        if connection_result.get("status") == "success":
            print(f"✅ Manual connection successful!")
            return True
        else:
            print(
                f"❌ Manual connection failed: {connection_result.get('error', 'Unknown')}"
            )
            return False

    except Exception as e:
        print(f"❌ Manual connection error: {type(e).__name__}: {str(e)}")
        print(f"   Full traceback:")
        print(f"   {traceback.format_exc()}")
        return False


async def main():
    """Main debugging function."""

    print("🚀 Starting Forgejo connection debugging...")

    try:
        # Test 1: Configuration-based connection
        print("\n📋 Testing with configuration...")
        success = await debug_forgejo_connection()

        if success:
            print("\n🎉 Configuration-based connection successful!")
            return

        # Test 2: Manual connection
        print("\n🔧 Configuration failed. Trying manual connection...")
        choice = (
            input("\nWould you like to try manual connection? (y/n): ").lower().strip()
        )

        if choice in ["y", "yes"]:
            manual_success = await test_manual_connection()

            if manual_success:
                print("\n🎉 Manual connection successful!")
                print(
                    "💡 Check your .env configuration against the working manual settings."
                )
            else:
                print("\n❌ Both configuration and manual connections failed.")
                print("💡 Check:")
                print("   1. Forgejo server is running and accessible")
                print("   2. URL format is correct (no trailing slash)")
                print("   3. Token/credentials are valid")
                print("   4. Network connectivity")
        else:
            print("\n👋 Debugging session ended.")

    except KeyboardInterrupt:
        print("\n\n👋 Debugging interrupted by user.")
    except Exception as e:
        print(f"\n💥 Unexpected error in main: {e}")
        print(f"   {traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(main())
