#!/usr/bin/env python3
"""
LLM経由GitHub MCP E2Eテスト
実際のLLMがFunction CallingでMCP GitHub toolsを呼び出すE2Eテストです
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.services.llm.utils import FunctionRegistry
from doc_ai_helper_backend.models.repository_context import RepositoryContext
from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
from doc_ai_helper_backend.services.mcp.function_adapter import MCPFunctionAdapter


class E2ETestConfig:
    """E2Eテスト設定"""
    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_base_url = os.getenv('OPENAI_BASE_URL')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.test_repository = os.getenv('TEST_GITHUB_REPOSITORY', 'test-owner/test-repo')
        
    def is_valid(self) -> bool:
        """設定が有効かチェック"""
        return bool(self.openai_api_key and self.github_token)
    
    def print_status(self):
        """設定状況を表示"""
        print("🔧 E2E テスト設定確認:")
        print(f"   OpenAI API Key: {'✅ 設定済み' if self.openai_api_key else '❌ 未設定'}")
        print(f"   OpenAI Base URL: {self.openai_base_url or 'デフォルト'}")
        print(f"   GitHub Token: {'✅ 設定済み' if self.github_token else '❌ 未設定'}")
        print(f"   テストリポジトリ: {self.test_repository}")


async def test_llm_github_issue_creation():
    """LLM経由でのGitHub Issue作成E2Eテスト"""
    print("🚀 LLM経由 GitHub Issue作成 E2Eテスト")
    print("=" * 55)
    
    config = E2ETestConfig()
    config.print_status()
    
    if not config.is_valid():
        print("\n❌ 必要な環境変数が設定されていません")
        print("   必要な環境変数:")
        print("   - OPENAI_API_KEY: OpenAI APIキー")
        print("   - GITHUB_TOKEN: GitHub Personal Access Token")
        print("   - TEST_GITHUB_REPOSITORY: テスト対象リポジトリ (オプション)")
        return False
    
    print("\n" + "="*55)
    
    try:
        # 1. LLMサービスの初期化
        print("1️⃣ LLMサービス初期化...")
        llm_service = LLMServiceFactory.create(
            provider='openai',
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            default_model='azure-tk-gpt-4o'  # .envから取得
        )
        print("   ✅ LLMサービス初期化完了")
        
        # 2. Function Registryの設定
        print("\n2️⃣ Function Registry設定...")
        function_registry = FunctionRegistry()
        
        # リポジトリコンテキストの作成
        owner, repo = config.test_repository.split('/', 1)
        repository_context = RepositoryContext(
            repo=repo,
            owner=owner,
            service="github",
            ref="main"
        )
        
        # GitHub toolsを登録
        from doc_ai_helper_backend.services.mcp.function_adapter import MCPFunctionAdapter
        adapter = MCPFunctionAdapter()
        
        # GitHub関数を登録
        github_functions = await adapter.get_available_functions()
        github_tool_functions = [f for f in github_functions if f.get('name', '').startswith('create_github')]
        
        for func in github_tool_functions:
            function_registry.register_function(func)
        
        print(f"   ✅ {len(github_tool_functions)}個のGitHub関数を登録")
        
        # 3. ユーザーに確認
        print(f"\n⚠️  リポジトリ '{config.test_repository}' に実際にIssueを作成します")
        confirm = input("   続行しますか？ (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("❌ テストをキャンセルしました")
            return False
        
        # 4. LLMへのプロンプト作成
        print("\n3️⃣ LLMプロンプト作成...")
        
        system_prompt = f"""
あなたは GitHub Issue を作成する専門アシスタントです。
現在のリポジトリコンテキスト: {config.test_repository}

利用可能な関数:
- create_github_issue: GitHub Issue を作成します

ユーザーの要求に応じて、適切な Issue を作成してください。
レスポンスは日本語で行い、作成されたIssueの詳細を報告してください。
"""
        
        user_prompt = """
以下の内容でGitHub Issueを作成してください:

タイトル: 🤖 LLM E2E テスト - 自動作成Issue
説明: 
- これはLLM経由のE2Eテストで作成されたIssueです
- Function Callingの動作確認を目的としています
- MCP GitHub Toolsとの統合テストです
- 確認後、このIssueは削除していただいて構いません

ラベル: ["e2e-test", "llm-generated", "auto-created"]
"""
        
        print("   ✅ プロンプト作成完了")
        
        # 5. LLMへの問い合わせ（Function Calling付き）
        print("\n4️⃣ LLM Function Calling実行...")
        
        # コンテキスト情報をLLMに注入
        context_data = {
            "repository_context": repository_context.model_dump(),
            "github_token": config.github_token
        }
        
        query_options = {
            "model": "azure-tk-gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "functions": function_registry.get_all_functions(),
            "function_call": "auto",
            "context": context_data,
            "temperature": 0.1
        }
        
        print("   📤 LLMへ問い合わせ中...")
        
        result = await llm_service.query(
            prompt="",  # messagesで指定済み
            options=query_options
        )
        
        print("   ✅ LLM応答受信完了")
        
        # 6. 結果の解析と表示
        print("\n5️⃣ 結果解析...")
        
        if hasattr(result, 'function_calls') and result.function_calls:
            print(f"   🔧 Function Call実行: {len(result.function_calls)}件")
            
            for i, call in enumerate(result.function_calls, 1):
                print(f"   📋 Call {i}: {call.get('name', 'unknown')}")
                if call.get('result'):
                    try:
                        call_result = json.loads(call['result'])
                        if call_result.get('success'):
                            if 'issue_info' in call_result:
                                issue_info = call_result['issue_info']
                                print(f"      ✅ Issue #{issue_info.get('number')} 作成成功")
                                print(f"      🔗 URL: {issue_info.get('url')}")
                            print(f"      💬 メッセージ: {call_result.get('message', 'N/A')}")
                        else:
                            print(f"      ❌ エラー: {call_result.get('error', 'Unknown error')}")
                    except json.JSONDecodeError:
                        print(f"      📄 Raw result: {call['result'][:100]}...")
        
        # LLMの最終応答
        print(f"\n6️⃣ LLM最終応答:")
        print(f"   💬 {result.content}")
        
        print(f"\n🎉 E2Eテスト完了!")
        return True
        
    except Exception as e:
        print(f"\n❌ E2Eテスト中にエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_github_permissions_check():
    """LLM経由でのGitHub権限確認テスト"""
    print("\n" + "="*55)
    print("🔍 LLM経由 GitHub権限確認テスト")
    print("=" * 55)
    
    config = E2ETestConfig()
    
    if not config.is_valid():
        print("❌ 環境変数が設定されていません")
        return False
    
    try:
        # LLMサービス初期化
        llm_service = LLMServiceFactory.create(
            provider='openai',
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        
        # Function Registry設定
        function_registry = FunctionRegistry()
        
        # リポジトリコンテキスト
        owner, repo = config.test_repository.split('/', 1)
        repository_context = RepositoryContext(
            repo=repo,
            owner=owner,
            service="github",
            ref="main"
        )
        
        # GitHub権限確認関数を登録
        from doc_ai_helper_backend.services.mcp.function_adapter import MCPFunctionAdapter
        adapter = MCPFunctionAdapter()
        
        github_functions = await adapter.get_available_functions()
        permissions_function = [f for f in github_functions if f.get('name') == 'check_github_repository_permissions']
        
        for func in permissions_function:
            function_registry.register_function(func)
        
        # LLMプロンプト
        system_prompt = f"""
あなたはGitHubリポジトリの権限確認アシスタントです。
現在のリポジトリコンテキスト: {config.test_repository}

利用可能な関数:
- check_github_repository_permissions: リポジトリの権限を確認します

リポジトリの権限を確認して、結果を日本語で報告してください。
"""
        
        user_prompt = "現在のリポジトリの権限を確認してください。"
        
        # コンテキスト情報
        context_data = {
            "repository_context": repository_context.model_dump(),
            "github_token": config.github_token
        }
        
        query_options = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "functions": function_registry.get_all_functions(),
            "function_call": "auto",
            "context": context_data,
            "temperature": 0.1
        }
        
        print("📤 権限確認実行中...")
        
        result = await llm_service.query(
            prompt="",
            options=query_options
        )
        
        print("📊 権限確認結果:")
        if hasattr(result, 'function_calls') and result.function_calls:
            for call in result.function_calls:
                if call.get('result'):
                    try:
                        call_result = json.loads(call['result'])
                        if call_result.get('success'):
                            permissions = call_result.get('permissions', {})
                            print(f"   ✅ 権限確認成功")
                            print(f"   📋 Issue作成: {'✅' if permissions.get('issues') else '❌'}")
                            print(f"   📋 PR作成: {'✅' if permissions.get('pull_requests') else '❌'}")
                            print(f"   📋 Push権限: {'✅' if permissions.get('push') else '❌'}")
                        else:
                            print(f"   ❌ エラー: {call_result.get('error')}")
                    except json.JSONDecodeError:
                        print(f"   📄 Raw: {call['result'][:100]}...")
        
        print(f"💬 LLM応答: {result.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ 権限確認テスト中にエラー: {str(e)}")
        return False


async def test_readme_improvement_flow():
    """README改善フローE2Eテスト - READMEコンテンツを基に改善Issueを作成"""
    print("\n" + "="*55)
    print("📖 README改善フロー E2Eテスト")
    print("=" * 55)
    
    config = E2ETestConfig()
    
    if not config.is_valid():
        print("❌ 環境変数が設定されていません")
        return False
    
    try:
        # 1. LLMサービス初期化
        print("1️⃣ LLMサービス初期化...")
        llm_service = LLMServiceFactory.create(
            provider='openai',
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            default_model='azure-tk-gpt-4o'
        )
        print("   ✅ LLMサービス初期化完了")
        
        # 2. Function Registry設定
        print("2️⃣ Function Registry設定...")
        function_registry = FunctionRegistry()
        
        # リポジトリコンテキスト
        owner, repo = config.test_repository.split('/', 1)
        repository_context = RepositoryContext(
            repo=repo,
            owner=owner,
            service="github",
            ref="main"
        )
        
        # GitHub関数を登録
        from doc_ai_helper_backend.services.mcp.function_adapter import MCPFunctionAdapter
        adapter = MCPFunctionAdapter()
        
        github_functions = await adapter.get_available_functions()
        github_tool_functions = [f for f in github_functions if f.get('name', '').startswith('create_github')]
        
        for func in github_tool_functions:
            function_registry.register_function(func)
        
        print(f"   ✅ {len(github_tool_functions)}個のGitHub関数を登録")
        
        # 3. サンプルREADMEコンテンツ（分析対象）
        print("3️⃣ README コンテンツ準備...")
        
        sample_readme = """# My Project

This is a simple project.

## Setup

Run the following commands:

```bash
npm install
npm start
```

## Usage

Use the application.

Contact: email@example.com
"""
        
        print("   ✅ サンプルREADMEコンテンツ準備完了")
        
        # 4. ユーザーに確認
        print(f"\n⚠️  リポジトリ '{config.test_repository}' にREADME改善Issueを作成します")
        confirm = input("   続行しますか？ (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("❌ テストをキャンセルしました")
            return False
        
        # 5. LLMプロンプト作成（READMEコンテンツを注入）
        print("4️⃣ README改善プロンプト作成...")
        
        system_prompt = f"""
あなたはドキュメント改善の専門家です。
リポジトリ: {config.test_repository}

現在のREADME.mdファイルの内容:
```markdown
{sample_readme}
```

あなたの役割:
1. 提供されたREADMEの内容を分析
2. ユーザーからの改善要求を理解
3. 具体的で実用的な改善提案をGitHub Issueとして作成

利用可能な関数:
- create_github_issue: 改善提案をGitHub Issueとして作成

ユーザーの要求に基づいて、READMEの具体的な改善点を分析し、
適切なタイトル、詳細な説明、関連ラベルを含むIssueを作成してください。
"""
        
        user_prompt = """
このREADMEは情報が不足していて、新しい開発者が理解しにくいと思います。
以下の改善点を含むGitHub Issueを作成してください:

- プロジェクトの目的と概要が不明
- 前提条件（Node.jsバージョンなど）が記載されていない  
- インストール手順が簡潔すぎる
- 使用方法の説明が曖昧
- ライセンス情報がない
- 貢献方法が記載されていない

開発者にとって親切で実用的なREADMEにするための改善提案をIssueとして投稿してください。
"""
        
        print("   ✅ README改善プロンプト作成完了")
        
        # 6. LLM Function Calling実行
        print("5️⃣ README改善分析 & Issue作成実行...")
        
        context_data = {
            "repository_context": repository_context.model_dump(),
            "github_token": config.github_token,
            "readme_content": sample_readme
        }
        
        query_options = {
            "model": "azure-tk-gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "functions": function_registry.get_all_functions(),
            "function_call": "auto",
            "context": context_data,
            "temperature": 0.3  # 創造的な改善提案のため少し高め
        }
        
        print("   📖 README分析中...")
        print("   🔍 改善点の特定中...")
        print("   📝 Issue作成中...")
        
        result = await llm_service.query(
            prompt="",  # messagesで指定済み
            options=query_options
        )
        
        print("   ✅ README改善分析完了")
        
        # 7. 結果解析と表示
        print("6️⃣ README改善フロー結果解析...")
        
        success = False
        issue_url = None
        
        if hasattr(result, 'function_calls') and result.function_calls:
            print(f"   🔧 Function Call実行: {len(result.function_calls)}件")
            
            for i, call in enumerate(result.function_calls, 1):
                print(f"   📋 Call {i}: {call.get('name', 'unknown')}")
                if call.get('result'):
                    try:
                        call_result = json.loads(call['result'])
                        if call_result.get('success'):
                            success = True
                            if 'issue_info' in call_result:
                                issue_info = call_result['issue_info']
                                issue_url = issue_info.get('url')
                                print(f"      ✅ README改善Issue #{issue_info.get('number')} 作成成功")
                                print(f"      📚 タイトル: {issue_info.get('title', 'N/A')}")
                                print(f"      🔗 URL: {issue_url}")
                                print(f"      🏷️  ラベル: {issue_info.get('labels', [])}")
                            print(f"      💬 メッセージ: {call_result.get('message', 'N/A')}")
                        else:
                            print(f"      ❌ エラー: {call_result.get('error', 'Unknown error')}")
                    except json.JSONDecodeError:
                        print(f"      📄 Raw result: {call['result'][:100]}...")
        
        # 8. LLMの改善分析結果表示
        print(f"\n7️⃣ LLMによるREADME改善分析結果:")
        print(f"   💭 {result.content}")
        
        # 9. フロー成功確認
        if success and issue_url:
            print(f"\n🎉 README改善フロー成功!")
            print(f"   📖 README内容の分析完了")
            print(f"   🔍 改善点の特定完了")  
            print(f"   📝 GitHub Issue作成完了")
            print(f"   🔗 作成されたIssue: {issue_url}")
            print(f"   ✨ 新しい開発者にとって理解しやすいREADMEへの改善提案が投稿されました")
        else:
            print(f"\n⚠️  README改善フローに問題が発生しました")
            print(f"   📊 Issue作成: {'✅' if success else '❌'}")
        
        return success
        
    except Exception as e:
        print(f"\n❌ README改善フロー中にエラー: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """メインE2Eテスト実行"""
    print("🧪 LLM経由 GitHub MCP E2Eテストスイート")
    print("=" * 60)
    
    # 環境確認
    config = E2ETestConfig()
    if not config.is_valid():
        print("\n📝 環境変数設定例:")
        print("   PowerShell:")
        print("   $env:OPENAI_API_KEY='sk-your-key-here'")
        print("   $env:GITHUB_TOKEN='ghp-your-token-here'")
        print("   $env:TEST_GITHUB_REPOSITORY='your-username/your-test-repo'")
        return
    
    results = []
    
    # テスト1: GitHub権限確認
    print("\n🔍 テスト1: GitHub権限確認")
    result1 = await test_llm_github_permissions_check()
    results.append(("権限確認", result1))
    
    # テスト2: README改善フロー
    print("\n📖 テスト2: README改善フロー")
    result2 = await test_readme_improvement_flow()
    results.append(("README改善フロー", result2))
    
    # テスト3: 基本GitHub Issue作成
    print("\n🚀 テスト3: 基本GitHub Issue作成")
    result3 = await test_llm_github_issue_creation()
    results.append(("基本Issue作成", result3))
    
    # 最終結果
    print("\n" + "="*60)
    print("📊 E2Eテスト結果サマリー")
    print("=" * 60)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n🎯 総合結果: {passed}/{total} テスト成功")
    
    if passed == total:
        print("🎉 全テストが成功しました！")
        print("   LLM経由でのMCP GitHub tools統合が正常に動作しています")
    else:
        print("⚠️  一部テストが失敗しました")
        print("   ログを確認して問題を解決してください")


if __name__ == "__main__":
    asyncio.run(main())
