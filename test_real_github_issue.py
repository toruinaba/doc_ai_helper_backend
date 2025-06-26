#!/usr/bin/env python3
"""
GitHub Issue投稿の実際のテスト用簡易スクリプト
使用方法:
1. 環境変数 GITHUB_TOKEN を設定
2. python test_real_github_issue.py
3. 画面の指示に従ってテスト実行
"""

import asyncio
import json
import os
from doc_ai_helper_backend.services.mcp.tools.github_tools import create_github_issue


async def main():
    """実際のGitHub Issue作成テスト"""
    print("🐙 GitHub Issue実作成テスト")
    print("=" * 40)
    
    # 環境変数チェック
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN環境変数が設定されていません")
        print("   PowerShellで設定例:")
        print("   $env:GITHUB_TOKEN='ghp_your_token_here'")
        print("   その後、このスクリプトを再実行してください")
        return
    
    print(f"✅ GitHubトークン: {github_token[:10]}...")
    
    # リポジトリ指定
    print("\n📁 テスト対象リポジトリ:")
    print("   注意: 書き込み権限があるリポジトリを指定してください")
    repo_input = input("   リポジトリ (owner/repo): ").strip()
    
    if not repo_input or '/' not in repo_input:
        print("❌ 無効な形式です")
        return
    
    owner, repo = repo_input.split('/', 1)
    
    # 実行確認
    print(f"\n⚠️  リポジトリ '{repo_input}' に実際にIssueを作成します")
    confirm = input("   続行しますか？ (yes/no): ").strip().lower()
    
    if confirm not in ['yes', 'y']:
        print("❌ キャンセルしました")
        return
    
    # Issue作成
    repository_context = {
        "repo": repo,
        "owner": owner,
        "service": "github", 
        "ref": "main"
    }
    
    print("\n🚀 Issue作成中...")
    
    try:
        result = await create_github_issue(
            title="🤖 MCP Tools テスト Issue",
            description="""
## 📋 概要
このIssueはMCP GitHub Toolsのテストとして作成されました。

## ✅ 確認事項
- [x] MCP経由でのIssue作成
- [x] 日本語レスポンス
- [x] リポジトリコンテキスト検証

## 🗑️ 削除について
このIssueはテスト用のため、確認後に削除してください。

---
*MCP GitHub Tools による自動作成*
            """.strip(),
            labels=["test", "mcp", "自動作成"],
            github_token=github_token,
            repository_context=repository_context
        )
        
        # 結果表示
        result_data = json.loads(result)
        print(f"\n📊 結果:")
        print(f"   成功: {result_data.get('success')}")
        
        if result_data.get('success'):
            issue_info = result_data.get('issue_info', {})
            print(f"   Issue番号: #{issue_info.get('number')}")
            print(f"   URL: {issue_info.get('url')}")
            print(f"   🎉 Issue作成成功!")
        else:
            print(f"   エラー: {result_data.get('error')}")
            print(f"   エラータイプ: {result_data.get('error_type')}")
    
    except Exception as e:
        print(f"❌ エラー: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
