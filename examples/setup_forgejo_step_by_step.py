#!/usr/bin/env python3
"""
Step-by-step Forgejo Configuration Guide

This script guides you through setting up Forgejo connectivity step by step.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def step1_check_environment():
    """Step 1: Check if .env file exists and has required settings."""

    print("=" * 60)
    print("📋 STEP 1: Environment Configuration Check")
    print("=" * 60)

    env_file = project_root / ".env"

    if not env_file.exists():
        print("❌ .env file not found!")
        print("\n💡 Solution:")
        print("   1. Copy the example file:")
        print("      cp .env.example .env")
        print("   2. Edit .env with your Forgejo server details")
        return False

    print("✅ .env file found")

    # Check required environment variables
    required_vars = {
        "FORGEJO_BASE_URL": "Forgejo server base URL",
        "FORGEJO_TOKEN": "Forgejo access token (OR username/password)",
    }

    print("\n🔍 Checking required variables:")

    missing_vars = []
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Hide sensitive values
            if "TOKEN" in var or "PASSWORD" in var:
                display_value = (
                    f"{'*' * min(len(value), 8)}...{value[-4:]}"
                    if len(value) > 8
                    else "***"
                )
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: NOT SET ({description})")
            missing_vars.append(var)

    # Check alternative authentication
    if "FORGEJO_TOKEN" in missing_vars:
        username = os.getenv("FORGEJO_USERNAME")
        password = os.getenv("FORGEJO_PASSWORD")

        if username and password:
            print(f"  ✅ Alternative: Basic auth configured (username: {username})")
            missing_vars.remove("FORGEJO_TOKEN")
        else:
            print("  ❌ Neither token nor username/password configured")

    if missing_vars:
        print(f"\n❌ Missing required variables: {', '.join(missing_vars)}")
        return False

    print("\n✅ All required environment variables are set")
    return True


async def step2_test_basic_connection():
    """Step 2: Test basic connection to Forgejo server."""

    print("\n" + "=" * 60)
    print("🌐 STEP 2: Basic Connection Test")
    print("=" * 60)

    try:
        from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService
        from doc_ai_helper_backend.core.config import settings

        print(f"📍 Testing connection to: {settings.forgejo_base_url}")

        # Create service instance
        service = ForgejoService(
            base_url=settings.forgejo_base_url,
            access_token=settings.forgejo_token,
            username=settings.forgejo_username,
            password=settings.forgejo_password,
        )

        print("✅ Service instance created")
        print(f"🔐 Supported auth methods: {service.get_supported_auth_methods()}")

        # Test connection
        print("\n🔌 Testing connection...")
        connection_result = await service.test_connection()

        if connection_result.get("status") == "success":
            print("✅ Connection successful!")
            return True
        else:
            print(
                f"❌ Connection failed: {connection_result.get('error', 'Unknown error')}"
            )
            return False

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False


async def step3_test_authentication():
    """Step 3: Test authentication with Forgejo server."""

    print("\n" + "=" * 60)
    print("🔐 STEP 3: Authentication Test")
    print("=" * 60)

    try:
        from doc_ai_helper_backend.services.git.factory import GitServiceFactory

        # Create service through factory
        service = GitServiceFactory.create("forgejo")

        print("🔍 Testing authentication...")
        auth_result = await service.authenticate()

        if auth_result:
            print("✅ Authentication successful!")

            # Get rate limit info to verify API access
            try:
                rate_info = await service.get_rate_limit_info()
                print(f"📊 API access confirmed. Rate limit info: {rate_info}")
            except Exception as e:
                print(f"⚠️  Note: Rate limit info unavailable: {e}")

            return True
        else:
            print("❌ Authentication failed!")
            print("\n💡 Troubleshooting:")
            print("   1. Check if your access token is valid")
            print("   2. Verify token has required permissions (repository:read)")
            print("   3. Try regenerating the token in Forgejo")
            return False

    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return False


async def step4_test_repository_access():
    """Step 4: Test repository access."""

    print("\n" + "=" * 60)
    print("📚 STEP 4: Repository Access Test")
    print("=" * 60)

    try:
        from doc_ai_helper_backend.services.git.factory import GitServiceFactory

        service = GitServiceFactory.create("forgejo")

        # Test with a common repository name (or ask user)
        test_repos = [
            ("gitea", "gitea"),  # Common public repo
            ("forgejo", "forgejo"),  # Common public repo
        ]

        print("🔍 Testing repository access...")

        for owner, repo in test_repos:
            try:
                exists = await service.check_repository_exists(owner, repo)
                print(
                    f"  📂 {owner}/{repo}: {'✅ Accessible' if exists else '❌ Not found'}"
                )

                if exists:
                    print("✅ Repository access confirmed!")
                    return True

            except Exception as e:
                print(f"  📂 {owner}/{repo}: ❌ Error: {e}")

        print("\n💡 Repository access test completed.")
        print("   No test repositories were accessible, but this might be normal")
        print("   depending on your Forgejo server configuration.")

        return True

    except Exception as e:
        print(f"❌ Repository access error: {e}")
        return False


async def main():
    """Main function to run all setup steps."""

    print("🚀 Forgejo Setup & Connection Test")
    print("This tool will guide you through setting up Forgejo connectivity.")
    print("\nPress Ctrl+C at any time to exit.")

    try:
        # Step 1: Environment check
        if not step1_check_environment():
            print("\n❌ Setup incomplete. Please fix environment configuration.")
            return False

        input("\nPress Enter to continue to connection test...")

        # Step 2: Basic connection
        if not await step2_test_basic_connection():
            print("\n❌ Connection failed. Check your FORGEJO_BASE_URL.")
            return False

        input("\nPress Enter to continue to authentication test...")

        # Step 3: Authentication
        if not await step3_test_authentication():
            print("\n❌ Authentication failed. Check your credentials.")
            return False

        input("\nPress Enter to continue to repository access test...")

        # Step 4: Repository access
        await step4_test_repository_access()

        print("\n" + "=" * 60)
        print("🎉 SETUP COMPLETE!")
        print("=" * 60)
        print("✅ Your Forgejo server is properly configured and accessible.")
        print("✅ You can now use the Forgejo service in your application.")

        print("\n📚 Next steps:")
        print("   1. Test with your actual repositories")
        print("   2. Integrate into your application workflow")
        print("   3. Check the API documentation for advanced features")

        return True

    except KeyboardInterrupt:
        print("\n\n👋 Setup interrupted by user. Run again when ready.")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(main())
