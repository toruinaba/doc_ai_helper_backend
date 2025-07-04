#!/usr/bin/env python3
"""
E2E Test Runner Script

This script helps run E2E tests with proper setup and validation.
"""
import os
import sys
import asyncio
import subprocess
import time
import signal
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.e2e.helpers.test_data import E2ETestData
from tests.e2e.helpers.api_client import BackendAPIClient
from tests.e2e.helpers.forgejo_client import ForgejoVerificationClient


class E2ETestRunner:
    """E2E test runner with environment validation and server management."""

    def __init__(self):
        self.backend_process = None
        self.project_root = project_root

    def validate_environment(self):
        """Validate environment configuration."""
        print("🔍 Validating environment configuration...")

        errors = E2ETestData.validate_environment()
        if errors:
            print("❌ Environment validation failed:")
            for error in errors:
                print(f"   - {error}")
            return False

        print("✅ Environment validation passed")
        return True

    async def check_backend_server(self):
        """Check if backend server is running."""
        print("🔍 Checking backend server availability...")

        async with BackendAPIClient() as client:
            if await client.health_check():
                print("✅ Backend server is running")
                return True
            else:
                print("❌ Backend server is not available")
                return False

    async def check_forgejo_connection(self):
        """Check Forgejo connection."""
        print("🔍 Checking Forgejo connection...")

        config = E2ETestData.get_forgejo_config()
        async with ForgejoVerificationClient(
            base_url=config.base_url,
            token=config.token,
            username=config.username,
            password=config.password,
            verify_ssl=config.verify_ssl,
        ) as client:
            if await client.check_connection():
                print(f"✅ Forgejo connection successful: {config.base_url}")

                # Check test repository
                repo_info = await client.get_repository_info(config.owner, config.repo)
                if repo_info:
                    print(
                        f"✅ Test repository accessible: {config.owner}/{config.repo}"
                    )
                    return True
                else:
                    print(f"❌ Test repository not found: {config.owner}/{config.repo}")
                    return False
            else:
                print(f"❌ Forgejo connection failed: {config.base_url}")
                return False

    def start_backend_server(self):
        """Start backend server in background."""
        print("🚀 Starting backend server...")

        try:
            # Change to project directory
            os.chdir(self.project_root)

            # Start server process
            self.backend_process = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "doc_ai_helper_backend.main:app",
                    "--host",
                    "0.0.0.0",
                    "--port",
                    "8000",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait for server to start
            print("⏳ Waiting for server to start...")
            time.sleep(5)

            # Check if process is still running
            if self.backend_process.poll() is not None:
                stdout, stderr = self.backend_process.communicate()
                print(f"❌ Server failed to start:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False

            print("✅ Backend server started successfully")
            return True

        except Exception as e:
            print(f"❌ Failed to start backend server: {e}")
            return False

    def stop_backend_server(self):
        """Stop backend server."""
        if self.backend_process:
            print("🛑 Stopping backend server...")
            self.backend_process.terminate()

            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print("⚠️ Server didn't stop gracefully, killing...")
                self.backend_process.kill()
                self.backend_process.wait()

            print("✅ Backend server stopped")
            self.backend_process = None

    def run_tests(self, test_args=None):
        """Run E2E tests."""
        print("🧪 Running E2E tests...")

        # Default test arguments
        if test_args is None:
            test_args = ["tests/e2e/", "--run-e2e", "-v", "--tb=short", "--maxfail=3"]

        # Add project root to command
        cmd = [sys.executable, "-m", "pytest"] + test_args

        print(f"📋 Test command: {' '.join(cmd)}")

        try:
            # Change to project directory
            os.chdir(self.project_root)

            # Run tests
            result = subprocess.run(cmd, capture_output=False, text=True)
            return result.returncode == 0

        except Exception as e:
            print(f"❌ Failed to run tests: {e}")
            return False

    async def run_quick_validation(self):
        """Run quick validation of all components."""
        print("🏃‍♂️ Running quick validation...")

        # Check backend
        backend_ok = await self.check_backend_server()

        # Check Forgejo
        forgejo_ok = await self.check_forgejo_connection()

        return backend_ok and forgejo_ok

    def cleanup(self):
        """Cleanup resources."""
        self.stop_backend_server()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run E2E tests for Document AI Helper Backend"
    )
    parser.add_argument(
        "--start-server", action="store_true", help="Start backend server automatically"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate environment and connections",
    )
    parser.add_argument(
        "--quick-test", action="store_true", help="Run only basic tests"
    )
    parser.add_argument(
        "--test-args", nargs="*", help="Additional arguments to pass to pytest"
    )

    args = parser.parse_args()

    runner = E2ETestRunner()

    try:
        # Signal handler for cleanup
        def signal_handler(signum, frame):
            print("\n🛑 Received interrupt signal, cleaning up...")
            runner.cleanup()
            sys.exit(1)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # Validate environment
        if not runner.validate_environment():
            sys.exit(1)

        # Start server if requested
        if args.start_server:
            if not runner.start_backend_server():
                sys.exit(1)

        # Run validation
        validation_ok = await runner.run_quick_validation()

        if args.validate_only:
            if validation_ok:
                print("✅ All validations passed")
                sys.exit(0)
            else:
                print("❌ Validation failed")
                sys.exit(1)

        if not validation_ok:
            print("❌ Pre-test validation failed")
            sys.exit(1)

        # Prepare test arguments
        test_args = ["tests/e2e/", "--run-e2e", "-v"]

        if args.quick_test:
            test_args.extend(["-m", "not slow", "--maxfail=1"])

        if args.test_args:
            test_args.extend(args.test_args)

        # Run tests
        success = runner.run_tests(test_args)

        if success:
            print("✅ All E2E tests passed!")
            sys.exit(0)
        else:
            print("❌ Some E2E tests failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

    finally:
        runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
