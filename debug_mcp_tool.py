#!/usr/bin/env python3
"""
簡単なデバッグ用テストスクリプト
問題の特定を行います
"""

import asyncio
import os
from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
from doc_ai_helper_backend.models.repository_context import RepositoryContext, GitService


async def debug_mcp_tool():
    """MCPツールの直接テスト"""
    print("🔍 MCP GitHub Tool デバッグテスト")
    print("=" * 50)
    
    # 環境変数チェック
    github_token = os.getenv('GITHUB_TOKEN')
    test_repo = os.getenv('TEST_GITHUB_REPOSITORY', 'test-owner/test-repo')
    
    if not github_token:
        print("⚠️ GITHUB_TOKEN環境変数が設定されていません")
        print("   MCPサーバーの初期化のみテストします...")
        github_token = "dummy-token-for-debug"
    
    print(f"📋 GitHub Token: {'✅ 設定済み' if github_token else '❌ 未設定'}")
    print(f"📋 テストリポジトリ: {test_repo}")
    
    try:
        # MCPサーバー初期化
        print("\n1️⃣ MCPサーバー初期化...")
        mcp_server = DocumentAIHelperMCPServer()
        
        # 利用可能なツールを確認
        available_tools = await mcp_server.get_available_tools_async()
        print(f"   利用可能なツール: {available_tools}")
        
        # RepositoryContextを作成
        owner, repo = test_repo.split('/', 1)
        repo_context = RepositoryContext(
            repo=repo,
            owner=owner,
            service=GitService.GITHUB,
            ref="main"
        )
        
        print(f"\n2️⃣ リポジトリコンテキスト作成:")
        print(f"   Owner: {owner}")
        print(f"   Repo: {repo}")
        print(f"   Service: {repo_context.service}")
        print(f"   Context Dict: {repo_context.model_dump()}")
        
        # GitHub Issue作成テスト
        if "create_github_issue" in available_tools:
            print(f"\n3️⃣ GitHub Issue作成テスト...")
            
            issue_params = {
                "title": "🔍 MCP Debug Test Issue",
                "description": "これはMCPツールのデバッグテストで作成されたIssueです。削除して構いません。",
                "labels": ["debug", "test"],
                "github_token": github_token,
                "repository_context": repo_context.model_dump()
            }
            
            print(f"   パラメータ: {issue_params}")
            
            # 実際にツールを呼び出し
            print(f"   MCPツール呼び出し中...")
            result = await mcp_server.call_tool("create_github_issue", **issue_params)
            
            print(f"   結果タイプ: {type(result)}")
            print(f"   結果内容: {result}")
            
            # 結果の詳細解析
            if isinstance(result, dict):
                print(f"   ✅ 辞書型の結果")
                for key, value in result.items():
                    print(f"      {key}: {value} (type: {type(value)})")
            elif isinstance(result, str):
                print(f"   📝 文字列型の結果: {result}")
            else:
                print(f"   ⚠️ 予期しない型: {type(result)}")
        
        else:
            print("❌ create_github_issue ツールが利用できません")
        
    except Exception as e:
        print(f"❌ デバッグテスト中にエラー: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_mcp_tool())
