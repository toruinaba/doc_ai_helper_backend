#!/usr/bin/env python3
"""
README改善確認フロー付きテスト実行スクリプト

使用方法:
python run_confirmation_test.py [--interactive]

オプション:
--interactive: 実際のユーザー入力を使用（デフォルトは自動実行）
"""

import asyncio
import sys
import argparse
from test_llm_github_e2e_fixed import (
    test_readme_improvement_with_confirmation,
    test_readme_improvement_interactive_confirmation,
    E2ETestConfig
)


async def main():
    """確認フロー付きテスト実行"""
    parser = argparse.ArgumentParser(description="README改善確認フロー付きテスト")
    parser.add_argument(
        "--interactive", 
        action="store_true", 
        help="実際のユーザー入力を使用（デフォルトは自動実行）"
    )
    
    args = parser.parse_args()
    
    print("🔄 README改善確認フロー付きテスト")
    print("=" * 50)
    
    # 環境確認
    config = E2ETestConfig()
    config.print_status()
    
    if not config.is_valid():
        print("\n❌ 環境変数が設定されていません")
        print("\n📝 環境変数設定例:")
        print("   PowerShell:")
        print("   $env:OPENAI_API_KEY='sk-your-key-here'")
        print("   $env:GITHUB_TOKEN='ghp-your-token-here'")
        print("   $env:TEST_GITHUB_REPOSITORY='your-username/your-test-repo'")
        return 1
    
    # テスト実行
    try:
        if args.interactive:
            print("\n🎮 インタラクティブモード（ユーザー入力あり）")
            success = await test_readme_improvement_interactive_confirmation()
        else:
            print("\n🤖 自動モード（テスト用）")
            success = await test_readme_improvement_with_confirmation()
        
        if success:
            print("\n✅ テスト成功！")
            return 0
        else:
            print("\n❌ テスト失敗")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによって中断されました")
        return 1
    except Exception as e:
        print(f"\n❌ テスト実行エラー: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
