#!/usr/bin/env python3
"""
テストファイルリファクタリングスクリプト
ルートディレクトリのテストファイルを適切なディレクトリに移動します
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List


# 移動対象ファイルとその移動先のマッピング
FILE_MAPPING: Dict[str, str] = {
    # GitHub統合テスト
    "test_github_issue_creation.py": "tests/integration/github/",
    "test_real_github_issue.py": "tests/integration/github/",
    "test_llm_github_e2e.py": "tests/integration/github/",
    "test_llm_github_e2e_fixed.py": "tests/integration/github/",
    "test_simple_llm_github.py": "tests/integration/github/",
    # Function Calling APIテスト
    "test_api_function_calling.py": "tests/api/function_calling/",
    "test_complete_function_calling_api.py": "tests/api/function_calling/",
    "test_openai_function_calling.py": "tests/api/function_calling/",
    "test_single_function_calling.py": "tests/api/function_calling/",
    "test_utility_function_calling.py": "tests/api/function_calling/",
    "test_utility_function_calling_simple.py": "tests/api/function_calling/",
    "test_japanese_function_calling.py": "tests/api/function_calling/",
    "test_explicit_tool_call.py": "tests/api/function_calling/",
    # コンテキスト関連APIテスト
    "test_api_context_integration.py": "tests/api/context/",
    "test_context_aware_llm.py": "tests/api/context/",
    # システムプロンプト関連APIテスト
    "test_api_system_prompt.py": "tests/api/system_prompt/",
    "test_function_calling_system_prompt.py": "tests/api/system_prompt/",
    "test_streaming_system_prompt.py": "tests/api/system_prompt/",
    # ストリーミング統合テスト
    "test_sse_streaming.py": "tests/integration/streaming/",
    "test_streaming_verification.py": "tests/integration/streaming/",
    # デモ・デバッグスクリプト
    "test_natural_response_demo.py": "tests/demo/examples/",
    "test_openai_detailed_debug.py": "tests/demo/debug/",
    "test_japanese_mock.py": "tests/demo/examples/",
    "test_japanese_responses.py": "tests/demo/examples/",
    "test_tool_flow_comparison.py": "tests/demo/examples/",
    "test_utility_tools.py": "tests/demo/utility/",
}


def move_test_files(dry_run: bool = True) -> None:
    """テストファイルを移動する

    Args:
        dry_run: Trueの場合は実際の移動は行わず、実行予定のアクションを表示
    """
    project_root = Path(__file__).parent

    print(f"🏠 プロジェクトルート: {project_root}")
    print(f"{'🔍 DRY RUN MODE' if dry_run else '🚀 EXECUTION MODE'}")
    print("=" * 60)

    moved_count = 0
    error_count = 0

    for filename, target_dir in FILE_MAPPING.items():
        source_path = project_root / filename
        target_path = project_root / target_dir / filename

        if not source_path.exists():
            print(f"⚠️  SKIP: {filename} (ファイルが存在しません)")
            continue

        if target_path.exists():
            print(f"⚠️  SKIP: {filename} (移動先に既に存在します)")
            continue

        try:
            if dry_run:
                print(f"📋 PLAN: {filename} → {target_dir}")
            else:
                # ディレクトリが存在しない場合は作成
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source_path), str(target_path))
                print(f"✅ MOVED: {filename} → {target_dir}")

            moved_count += 1

        except Exception as e:
            print(f"❌ ERROR: {filename} - {str(e)}")
            error_count += 1

    print("=" * 60)
    print(f"📊 SUMMARY:")
    print(f"   移動対象: {moved_count}件")
    print(f"   エラー: {error_count}件")

    if dry_run:
        print(f"\n💡 実際に移動するには以下を実行してください:")
        print(f"   python {__file__} --execute")


def main():
    """メイン実行関数"""
    import sys

    # コマンドライン引数をチェック
    dry_run = "--execute" not in sys.argv

    if dry_run:
        print("🔍 DRY RUN: 実行計画を表示します（実際の移動は行いません）\n")
    else:
        print("🚀 EXECUTE: ファイルを実際に移動します\n")

    move_test_files(dry_run=dry_run)


if __name__ == "__main__":
    main()
