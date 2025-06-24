#!/usr/bin/env python3
"""
MCP統合テスト実行スクリプト

使用方法:
    python scripts/run_mcp_integration_tests.py [options]

オプション:
    --basic      基本的なMCPテストのみ実行
    --full       全てのMCPテストを実行（GitHub API含む）
    --performance パフォーマンステストを実行
    --e2e        E2Eシナリオテストを実行
    --verbose    詳細出力
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


def setup_environment():
    """テスト環境の設定"""
    # プロジェクトルートを環境変数に追加
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))

    # 必要な環境変数の確認
    env_vars = {"PYTHONPATH": str(project_root), "TEST_ENV": "integration"}

    for key, value in env_vars.items():
        os.environ[key] = value

    print(f"Environment setup complete. Project root: {project_root}")


def run_pytest_command(test_args: list, verbose: bool = False):
    """pytestコマンドを実行"""
    cmd = ["python", "-m", "pytest"]

    if verbose:
        cmd.extend(["-v", "-s"])

    cmd.extend(test_args)

    print(f"Running: {' '.join(cmd)}")
    print("-" * 60)

    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def run_basic_mcp_tests(verbose: bool = False):
    """基本的なMCPテストを実行（外部API不要）"""
    print("🔧 Running basic MCP tests (no external APIs required)")

    test_args = [
        "tests/integration/mcp/test_mcp_server.py",
        "tests/integration/mcp/test_mcp_tools.py",
        "-m",
        "mcp and not github and not slow",
        "--tb=short",
    ]

    return run_pytest_command(test_args, verbose)


def run_function_calling_tests(verbose: bool = False):
    """Function Callingテストを実行"""
    print("🛠️ Running MCP Function Calling tests")

    test_args = [
        "tests/integration/mcp/test_mcp_function_calling.py",
        "-m",
        "function_calling",
        "--tb=short",
    ]

    return run_pytest_command(test_args, verbose)


def run_e2e_tests(verbose: bool = False):
    """E2Eシナリオテストを実行"""
    print("🔄 Running MCP E2E scenario tests")

    test_args = [
        "tests/integration/mcp/test_mcp_e2e_scenarios.py",
        "-m",
        "e2e and not github",
        "--tb=short",
    ]

    return run_pytest_command(test_args, verbose)


def run_performance_tests(verbose: bool = False):
    """パフォーマンステストを実行"""
    print("⚡ Running MCP performance tests")

    test_args = [
        "tests/integration/mcp/test_mcp_performance.py",
        "-m",
        "performance",
        "--tb=short",
    ]

    return run_pytest_command(test_args, verbose)


def run_github_tests(verbose: bool = False):
    """GitHubテストを実行（環境変数必要）"""
    if not os.getenv("GITHUB_TOKEN"):
        print("⚠️ GITHUB_TOKEN not set. Skipping GitHub tests.")
        return 0

    print("🐙 Running GitHub integration tests")

    test_args = ["tests/integration/mcp/", "-m", "github", "--tb=short"]

    return run_pytest_command(test_args, verbose)


def run_all_mcp_tests(verbose: bool = False):
    """全てのMCPテストを実行"""
    print("🚀 Running ALL MCP integration tests")

    test_args = ["tests/integration/mcp/", "-m", "mcp", "--tb=short"]

    return run_pytest_command(test_args, verbose)


def check_prerequisites():
    """前提条件のチェック"""
    print("Checking prerequisites...")

    # 必須パッケージの確認
    required_packages = ["pytest", "fastmcp", "httpx", "psutil"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print(f"❌ Missing required packages: {', '.join(missing_packages)}")
        print("Please install them with: pip install -r requirements.txt")
        return False

    # テストディレクトリの確認
    test_dir = Path("tests/integration/mcp")
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        return False

    print("✅ Prerequisites check passed")
    return True


def main():
    parser = argparse.ArgumentParser(description="MCP統合テスト実行スクリプト")
    parser.add_argument(
        "--basic", action="store_true", help="基本的なMCPテストのみ実行"
    )
    parser.add_argument(
        "--full", action="store_true", help="全てのMCPテストを実行（GitHub API含む）"
    )
    parser.add_argument(
        "--function-calling", action="store_true", help="Function Callingテストを実行"
    )
    parser.add_argument("--e2e", action="store_true", help="E2Eシナリオテストを実行")
    parser.add_argument(
        "--performance", action="store_true", help="パフォーマンステストを実行"
    )
    parser.add_argument("--github", action="store_true", help="GitHubテストを実行")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")

    args = parser.parse_args()

    # 前提条件チェック
    if not check_prerequisites():
        return 1

    # 環境設定
    setup_environment()

    # テスト実行
    exit_code = 0

    if args.basic:
        exit_code = max(exit_code, run_basic_mcp_tests(args.verbose))
    elif args.full:
        exit_code = max(exit_code, run_all_mcp_tests(args.verbose))
    elif args.function_calling:
        exit_code = max(exit_code, run_function_calling_tests(args.verbose))
    elif args.e2e:
        exit_code = max(exit_code, run_e2e_tests(args.verbose))
    elif args.performance:
        exit_code = max(exit_code, run_performance_tests(args.verbose))
    elif args.github:
        exit_code = max(exit_code, run_github_tests(args.verbose))
    else:
        # デフォルトは基本テスト
        print("No specific test type specified. Running basic MCP tests.")
        exit_code = run_basic_mcp_tests(args.verbose)

    if exit_code == 0:
        print("\n✅ All MCP integration tests passed!")
    else:
        print(f"\n❌ Some tests failed (exit code: {exit_code})")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
