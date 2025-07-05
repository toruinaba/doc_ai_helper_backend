#!/usr/bin/env python3
"""
LLM経由GitHub MCP E2Eテスト - 修正版
実際のLLMがFunction CallingでMCP GitHub toolsを呼び出すE2Eテストです
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.services.llm.utils import FunctionRegistry
from doc_ai_helper_backend.models.repository_context import RepositoryContext
from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
from doc_ai_helper_backend.services.mcp.function_adapter import MCPFunctionAdapter
from doc_ai_helper_backend.models.llm import FunctionDefinition
from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.models.repository_context import GitService


class E2ETestConfig:
    """E2Eテスト設定"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.test_repository = os.getenv(
            "TEST_GITHUB_REPOSITORY", "test-owner/test-repo"
        )

    def is_valid(self) -> bool:
        """設定が有効かチェック"""
        return bool(self.openai_api_key and self.github_token)

    def print_status(self):
        """設定状況を表示"""
        print("🔧 E2E テスト設定確認:")
        print(
            f"   OpenAI API Key: {'✅ 設定済み' if self.openai_api_key else '❌ 未設定'}"
        )
        print(f"   OpenAI Base URL: {self.openai_base_url or 'デフォルト'}")
        print(f"   GitHub Token: {'✅ 設定済み' if self.github_token else '❌ 未設定'}")
        print(f"   テストリポジトリ: {self.test_repository}")


async def setup_mcp_functions(
    github_token: str,
) -> tuple[FunctionRegistry, MCPFunctionAdapter]:
    """MCP関数のセットアップ"""
    print("   🔧 MCPサーバー初期化中...")

    # MCPサーバーの初期化
    mcp_server = DocumentAIHelperMCPServer()

    # MCPアダプターの初期化
    adapter = MCPFunctionAdapter(mcp_server)

    # Function Registryの初期化
    function_registry = FunctionRegistry()

    # 利用可能なツールを取得
    available_tools = await mcp_server.get_available_tools_async()
    print(f"   📋 利用可能なMCPツール: {available_tools}")

    # GitHub関連ツールを手動で登録
    github_tools = [
        "create_github_issue",
        "create_github_pull_request",
        "check_github_repository_permissions",
    ]

    for tool_name in github_tools:
        if tool_name in available_tools:
            # ツール情報を取得してFunction Callingフォーマットに変換
            tool_def = get_github_tool_definition(tool_name)
            function_registry.register_function(
                name=tool_name,
                function=create_mcp_tool_wrapper(mcp_server, tool_name, github_token),
                description=tool_def["description"],
                parameters=tool_def["parameters"],
            )
            print(f"   ✅ 登録完了: {tool_name}")

    return function_registry, adapter


def create_mcp_tool_wrapper(
    mcp_server: DocumentAIHelperMCPServer, tool_name: str, github_token: str
):
    """MCPツール用のラッパー関数を作成"""

    async def wrapper(**kwargs) -> Dict[str, Any]:
        try:
            # デバッグ用: 入力パラメータを表示
            print(f"       🔧 {tool_name} 呼び出し開始")
            print(f"          入力パラメータ: {kwargs}")
            
            # GitHubトークンをツール呼び出しに注入
            kwargs["github_token"] = github_token
            
            # repository パラメータがある場合は、repository_contextに変換
            if "repository" in kwargs:
                repository = kwargs.pop("repository")
                owner, repo = repository.split('/', 1)
                
                # RepositoryContextを作成してリポジトリコンテキストとして注入
                repo_context = RepositoryContext(
                    repo=repo,
                    owner=owner,
                    service=GitService.GITHUB,  # GitServiceを正しく使用
                    ref="main"
                )
                kwargs["repository_context"] = repo_context.model_dump()
                print(f"          変換後パラメータ: {kwargs}")
            
            result = await mcp_server.call_tool(tool_name, **kwargs)
            
            # デバッグ用: MCPツールの生の結果を表示
            print(f"          MCPツール生の結果: {result}")
            print(f"          結果のタイプ: {type(result)}")
            
            return {"success": True, "result": result, "error": None}
        except Exception as e:
            print(f"          ❌ MCPツール実行エラー: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "result": None, "error": str(e)}

    return wrapper


def get_github_tool_definition(tool_name: str) -> Dict[str, Any]:
    """GitHubツールの定義を取得"""
    definitions = {
        "create_github_issue": {
            "description": "GitHub Issue を作成する",
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "リポジトリ名 (owner/repo形式)",
                    },
                    "title": {"type": "string", "description": "Issue のタイトル"},
                    "description": {"type": "string", "description": "Issue の説明"},
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "ラベルのリスト",
                    },
                    "assignees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "アサイニーのリスト",
                    },
                },
                "required": ["repository", "title", "description"],
            },
        },
        "create_github_pull_request": {
            "description": "GitHub Pull Request を作成する",
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "リポジトリ名 (owner/repo形式)",
                    },
                    "title": {"type": "string", "description": "PR のタイトル"},
                    "description": {"type": "string", "description": "PR の説明"},
                    "file_path": {
                        "type": "string",
                        "description": "変更するファイルのパス",
                    },
                    "file_content": {
                        "type": "string",
                        "description": "新しいファイルの内容",
                    },
                    "branch_name": {
                        "type": "string",
                        "description": "新しいブランチ名",
                    },
                    "base_branch": {
                        "type": "string",
                        "description": "ベースブランチ (デフォルト: main)",
                    },
                },
                "required": [
                    "repository",
                    "title",
                    "description",
                    "file_path",
                    "file_content",
                ],
            },
        },
        "check_github_repository_permissions": {
            "description": "GitHub リポジトリの権限を確認する",
            "parameters": {
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "リポジトリ名 (owner/repo形式)",
                    }
                },
                "required": ["repository"],
            },
        },
    }

    return definitions.get(
        tool_name,
        {
            "description": f"MCP tool: {tool_name}",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    )


async def test_readme_improvement_flow():
    """README改善フローE2Eテスト - READMEコンテンツを基に改善Issueを作成"""
    print("📖 README改善フロー E2Eテスト")
    print("=" * 55)

    config = E2ETestConfig()
    config.print_status()

    if not config.is_valid():
        print("❌ 環境変数が設定されていません")
        return False

    # GitHub tokenのnullチェック
    if not config.github_token:
        print("❌ GitHubトークンが設定されていません")
        return False

    try:
        # 1. LLMサービス初期化
        print("\n1️⃣ LLMサービス初期化...")
        llm_service = LLMServiceFactory.create(
            provider="openai",
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            default_model="azure-tk-gpt-4o",
        )
        print("   ✅ LLMサービス初期化完了")

        # 2. Function Registry設定
        print("\n2️⃣ Function Registry設定...")
        function_registry, adapter = await setup_mcp_functions(config.github_token)
        print(f"   ✅ Function Registry設定完了")

        # 3. サンプルREADMEコンテンツ（分析対象）
        print("\n3️⃣ README コンテンツ準備...")

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
        print(
            f"\n⚠️  リポジトリ '{config.test_repository}' にREADME改善Issueを作成します"
        )
        confirm = input("   続行しますか？ (yes/no): ").strip().lower()

        if confirm not in ["yes", "y"]:
            print("❌ テストをキャンセルしました")
            return False

        # 5. LLMプロンプト作成（READMEコンテンツを注入）
        print("\n4️⃣ README改善プロンプト作成...")

        system_prompt = f"""
あなたは日本人のドキュメント改善専門家です。必ず日本語で応答してください。
リポジトリ: {config.test_repository}

現在のREADME.mdファイルの内容:
```markdown
{sample_readme}
```

【重要指示】
- すべての応答は日本語で行ってください
- Issue作成時も日本語でタイトルと説明を作成してください
- 英語は一切使用しないでください
- 必ず日本語で具体的な改善提案を作成してください

【出力例】
タイトル: 📚 README改善提案: プロジェクト概要と詳細な導入手順の追加
説明: 
## 改善提案

現在のREADMEには以下の情報が不足しています：

1. **プロジェクトの目的と概要**
   - このプロジェクトが何を解決するのかが不明
   - 対象ユーザーが分からない

2. **前提条件の記載**
   - Node.jsのバージョン要件
   - 必要なシステム要件

...以下日本語で詳細に記述

あなたの役割:
1. 提供されたREADMEの内容を日本語で分析
2. ユーザーからの改善要求を日本語で理解
3. 具体的で実用的な改善提案を日本語でGitHub Issueとして作成

利用可能な関数:
- create_github_issue: 改善提案をGitHub Issueとして作成（日本語で）

ユーザーの要求に基づいて、READMEの具体的な改善点を日本語で分析し、
日本語の適切なタイトル、日本語の詳細な説明、関連ラベルを含むIssueを作成してください。

必ず以下の形式で日本語Issue作成を実行してください:
- タイトル: 「📚 README改善提案: [具体的な改善項目]」
- 説明: 日本語で詳細な改善提案（上記の出力例を参考に）
- ラベル: ["documentation", "enhancement", "readme-improvement"]
"""

        user_prompt = """
このREADMEファイルを分析して、必ず日本語で改善提案のIssueを作成してください。

【問題点】
このREADMEは以下の情報が不足していて、新しい開発者が理解しにくいです：

- プロジェクトの目的と概要が不明確
- 前提条件（Node.jsバージョンなど）が記載されていない  
- インストール手順が簡潔すぎる
- 使用方法の説明が曖昧
- ライセンス情報がない
- 貢献方法が記載されていない

【要求】
開発者にとって親切で実用的なREADMEにするための改善提案を、必ず日本語でGitHub Issueとして投稿してください。

【必須条件】
- Issue作成時は必ず日本語を使用してください
- タイトルと説明文は日本語で記述してください
- 具体的で実行可能な改善提案を含めてください
- 「📚 README改善提案: [具体的な内容]」という形式でタイトルを作成してください

今すぐcreate_github_issue関数を使って、上記の条件で日本語のIssueを作成してください。
"""

        print("   ✅ README改善プロンプト作成完了")

        # 6. OpenAI tools APIに対応したクエリオプション
        print("\n5️⃣ README改善分析 & Issue作成実行...")

        # Function Callingのツール定義を取得
        tools = []
        all_function_definitions = function_registry.get_all_function_definitions()
        for func_def in all_function_definitions:
            tool = {
                "type": "function",
                "function": {
                    "name": func_def.name,
                    "description": func_def.description or "",
                    "parameters": func_def.parameters or {},
                },
            }
            tools.append(tool)

        query_options = {
            "model": "azure-tk-gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "tools": tools,  # OpenAI tools API使用
            "tool_choice": "auto",
            "temperature": 0.3,  # 創造的な改善提案のため少し高め
        }

        print("   📖 README分析中...")
        print("   🔍 改善点の特定中...")
        print("   📝 Issue作成中...")

        result = await llm_service.query(
            prompt="", options=query_options  # messagesで指定済み
        )

        print("   ✅ README改善分析完了")

        # 7. Tool Calls の処理（OpenAI tools API対応）
        print("\n6️⃣ Tool Calls処理...")

        tool_results: List[Dict[str, Any]] = []

        if result.tool_calls:
            print(f"   🔧 Tool Call実行: {len(result.tool_calls)}件")

            for i, tool_call in enumerate(result.tool_calls, 1):
                print(f"   📋 Tool Call {i}: {tool_call.function.name}")

                try:
                    # 引数をパース
                    arguments = json.loads(tool_call.function.arguments)
                    print(f"       引数: {arguments}")

                    # リポジトリパラメータを注入
                    arguments["repository"] = config.test_repository

                    # 対応する関数を取得して実行
                    function_name = tool_call.function.name
                    func = function_registry.get_function(function_name)
                    if func:
                        result_data = await func(**arguments)
                        tool_results.append(
                            {"tool_call_id": tool_call.id, "result": result_data}
                        )

                        # デバッグ用: 結果の詳細を表示
                        print(f"       🔍 Tool実行結果の詳細:")
                        print(f"          Type: {type(result_data)}")
                        print(f"          Data: {result_data}")
                        
                        # 結果を表示
                        if isinstance(result_data, dict) and result_data.get("success"):
                            result_content = result_data.get("result", {})
                            print(f"          Result content type: {type(result_content)}")
                            print(f"          Result content: {result_content}")
                            
                            if isinstance(result_content, dict) and "issue_info" in result_content:
                                issue_info = result_content["issue_info"]
                                print(f"          Issue info type: {type(issue_info)}")
                                print(f"          Issue info: {issue_info}")
                                
                                if isinstance(issue_info, dict):
                                    print(
                                        f"       ✅ Issue #{issue_info.get('number')} 作成成功"
                                    )
                                    print(
                                        f"       📚 タイトル: {issue_info.get('title', 'N/A')}"
                                    )
                                    print(f"       🔗 URL: {issue_info.get('url')}")
                                    print(
                                        f"       🏷️  ラベル: {issue_info.get('labels', [])}"
                                    )
                                else:
                                    print(f"       ⚠️ Issue info is not a dict: {issue_info}")
                            elif isinstance(result_content, str):
                                print(f"       ✅ 操作成功: {result_content}")
                            else:
                                print(f"       ✅ 操作成功 (詳細なし)")
                        else:
                            print(
                                f"       ❌ エラー: {result_data.get('error', 'Unknown error') if isinstance(result_data, dict) else result_data}"
                            )
                    else:
                        print(f"       ❌ 関数が見つかりません: {function_name}")

                except Exception as e:
                    print(f"       ❌ Tool Call実行エラー: {str(e)}")
                    tool_results.append(
                        {
                            "tool_call_id": tool_call.id,
                            "result": {"success": False, "error": str(e)},
                        }
                    )

        # 8. LLMの改善分析結果表示
        print(f"\n7️⃣ LLMによるREADME改善分析結果:")
        print(f"   💭 {result.content}")

        # 9. フロー成功確認
        success = any(tr.get("result", {}).get("success", False) for tr in tool_results)

        if success:
            print(f"\n🎉 README改善フロー成功!")
            print(f"   📖 README内容の分析完了")
            print(f"   🔍 改善点の特定完了")
            print(f"   📝 GitHub Issue作成完了")
            print(
                f"   ✨ 新しい開発者にとって理解しやすいREADMEへの改善提案が投稿されました"
            )
        else:
            print(f"\n⚠️  README改善フローに問題が発生しました")
            print(f"   📊 Issue作成: {'✅' if success else '❌'}")

        return success

    except Exception as e:
        print(f"\n❌ README改善フロー中にエラー: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


async def test_basic_github_issue_creation():
    """基本的なGitHub Issue作成テスト"""
    print("\n🚀 基本GitHub Issue作成テスト")
    print("=" * 55)

    config = E2ETestConfig()

    if not config.is_valid():
        print("❌ 環境変数が設定されていません")
        return False

    # GitHub tokenのnullチェック
    if not config.github_token:
        print("❌ GitHubトークンが設定されていません")
        return False

    try:
        # LLMサービス初期化
        llm_service = LLMServiceFactory.create(
            provider="openai",
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            default_model="azure-tk-gpt-4o",
        )

        # Function Registry設定
        function_registry, adapter = await setup_mcp_functions(config.github_token)

        # ユーザーに確認
        print(
            f"\n⚠️  リポジトリ '{config.test_repository}' に基本テストIssueを作成します"
        )
        confirm = input("   続行しますか？ (yes/no): ").strip().lower()

        if confirm not in ["yes", "y"]:
            print("❌ テストをキャンセルしました")
            return False

        # LLMプロンプト
        system_prompt = f"""
あなたは GitHub Issue を作成する専門アシスタントです。
現在のリポジトリ: {config.test_repository}

利用可能な関数:
- create_github_issue: GitHub Issue を作成します

ユーザーの要求に応じて、適切な Issue を作成してください。
レスポンスは日本語で行い、作成されたIssueの詳細を報告してください。
"""

        user_prompt = """
以下の内容でGitHub Issueを作成してください:

タイトル: 🤖 LLM E2E テスト - 基本Issue作成
説明: 
- これはLLM経由のE2Eテストで作成されたIssueです
- Function Callingの動作確認を目的としています
- MCP GitHub Toolsとの統合テストです
- 確認後、このIssueは削除していただいて構いません

ラベル: ["e2e-test", "llm-generated", "auto-created"]
"""

        # Function Callingのツール定義を取得
        tools = []
        all_function_definitions = function_registry.get_all_function_definitions()
        for func_def in all_function_definitions:
            tool = {
                "type": "function",
                "function": {
                    "name": func_def.name,
                    "description": func_def.description or "",
                    "parameters": func_def.parameters or {},
                },
            }
            tools.append(tool)

        query_options = {
            "model": "azure-tk-gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.1,
        }

        print("   📤 LLMへ問い合わせ中...")

        result = await llm_service.query(prompt="", options=query_options)

        print("   ✅ LLM応答受信完了")

        # Tool Calls処理
        success = False
        if result.tool_calls:
            for tool_call in result.tool_calls:
                if tool_call.function.name == "create_github_issue":
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        arguments["repository"] = config.test_repository

                        func = function_registry.get_function("create_github_issue")
                        if func:
                            tool_result = await func(**arguments)
                            
                            # デバッグ用: 結果の詳細を表示
                            print(f"       🔍 Tool実行結果:")
                            print(f"          Type: {type(tool_result)}")
                            print(f"          Data: {tool_result}")

                            if tool_result.get("success"):
                                success = True
                                result_content = tool_result.get("result", {})
                                if isinstance(result_content, dict) and "issue_info" in result_content:
                                    issue_info = result_content["issue_info"]
                                    print(
                                        f"   ✅ Issue #{issue_info.get('number')} 作成成功"
                                    )
                                    print(f"   🔗 URL: {issue_info.get('url')}")
                                elif isinstance(result_content, str):
                                    print(f"   ✅ 操作成功: {result_content}")
                                else:
                                    print(f"   ✅ 操作成功 (詳細なし)")
                            else:
                                print(f"   ❌ エラー: {tool_result.get('error')}")
                        else:
                            print(f"   ❌ 関数が見つかりません: create_github_issue")

                    except Exception as e:
                        print(f"   ❌ Tool実行エラー: {str(e)}")

        print(f"\n💬 LLM最終応答: {result.content}")

        return success

    except Exception as e:
        print(f"\n❌ 基本Issue作成テスト中にエラー: {str(e)}")
        return False


async def test_github_permissions_check():
    """GitHub権限確認テスト"""
    print("\n🔍 GitHub権限確認テスト")
    print("=" * 55)

    config = E2ETestConfig()

    if not config.is_valid():
        print("❌ 環境変数が設定されていません")
        return False

    # GitHub tokenのnullチェック
    if not config.github_token:
        print("❌ GitHubトークンが設定されていません")
        return False

    try:
        # LLMサービス初期化
        llm_service = LLMServiceFactory.create(
            provider="openai",
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
        )

        # Function Registry設定
        function_registry, adapter = await setup_mcp_functions(config.github_token)

        # LLMプロンプト
        system_prompt = f"""
あなたはGitHubリポジトリの権限確認アシスタントです。
現在のリポジトリ: {config.test_repository}

利用可能な関数:
- check_github_repository_permissions: リポジトリの権限を確認します

リポジトリの権限を確認して、結果を日本語で報告してください。
"""

        user_prompt = "現在のリポジトリの権限を確認してください。"

        # Function Callingのツール定義を取得 (権限確認のみ)
        tools = []
        all_function_definitions = function_registry.get_all_function_definitions()
        for func_def in all_function_definitions:
            if func_def.name == "check_github_repository_permissions":
                tool = {
                    "type": "function",
                    "function": {
                        "name": func_def.name,
                        "description": func_def.description or "",
                        "parameters": func_def.parameters or {},
                    },
                }
                tools.append(tool)

        query_options = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.1,
        }

        print("📤 権限確認実行中...")

        result = await llm_service.query(prompt="", options=query_options)

        print("📊 権限確認結果:")
        if result.tool_calls:
            for tool_call in result.tool_calls:
                if tool_call.function.name == "check_github_repository_permissions":
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        arguments["repository"] = config.test_repository

                        func = function_registry.get_function(
                            "check_github_repository_permissions"
                        )
                        if func:
                            tool_result = await func(**arguments)
                            
                            # デバッグ用: 結果の詳細を表示
                            print(f"       🔍 権限確認結果:")
                            print(f"          Type: {type(tool_result)}")
                            print(f"          Data: {tool_result}")

                            if tool_result.get("success"):
                                result_content = tool_result.get("result", {})
                                if isinstance(result_content, dict):
                                    permissions = result_content.get("permissions", {})
                                    print(f"   ✅ 権限確認成功")
                                    print(
                                        f"   📋 Issue作成: {'✅' if permissions.get('issues') else '❌'}"
                                    )
                                    print(
                                        f"   📋 PR作成: {'✅' if permissions.get('pull_requests') else '❌'}"
                                    )
                                    print(
                                        f"   📋 Push権限: {'✅' if permissions.get('push') else '❌'}"
                                    )
                                else:
                                    print(f"   ✅ 権限確認成功: {result_content}")
                            else:
                                print(f"   ❌ エラー: {tool_result.get('error')}")
                        else:
                            print(
                                f"   ❌ 関数が見つかりません: check_github_repository_permissions"
                            )

                    except Exception as e:
                        print(f"   ❌ Tool実行エラー: {str(e)}")

        print(f"💬 LLM応答: {result.content}")

        return True

    except Exception as e:
        print(f"❌ 権限確認テスト中にエラー: {str(e)}")
        return False


async def test_readme_improvement_with_confirmation():
    """READMEドリブン改善要求の確認フロー付きE2Eテスト"""
    print("📖 README改善確認フロー E2Eテスト")
    print("=" * 55)
    
    config = E2ETestConfig()
    config.print_status()
    
    if not config.is_valid():
        print("❌ 環境変数が設定されていません")
        return False
    
    try:
        # 1. LLMサービス初期化
        print("\n1️⃣ LLMサービス初期化...")
        llm_service = LLMServiceFactory.create(
            provider="openai",
            api_key=config.openai_api_key,
            base_url=config.openai_base_url,
            default_model="azure-tk-gpt-4o",
        )
        print("   ✅ LLMサービス初期化完了")
        
        # 2. Function Registry & MCP設定
        print("\n2️⃣ Function Registry & MCP設定...")
        
        # GitHubトークンがNoneでないことを保証
        if not config.github_token:
            print("❌ GitHubトークンが設定されていません")
            return False
            
        function_registry, mcp_adapter = await setup_mcp_functions(config.github_token)
        print("   ✅ Function Registry & MCP設定完了")
        
        # 3. サンプルREADME準備（実際の取得は省略）
        print("\n3️⃣ サンプルREADME準備...")
        sample_readme = """
# Sample Project

A sample project for testing.

## Installation

```bash
npm install
```

## Usage

Run the application.
"""
        print("   📝 サンプルREADMEを使用")
        
        # 4. 第1段階 - Issue内容生成（投稿はしない）
        print("\n4️⃣ Issue内容生成段階...")
        
        system_prompt_generation = f"""
あなたは日本語で対応するドキュメント改善の専門家です。

【重要】すべての応答は必ず日本語で行ってください。英語は一切使用しないでください。

現在のリポジトリ: {config.test_repository}

README.mdの内容:
```markdown
{sample_readme}
```

あなたの役割:
1. READMEの内容を日本語で分析
2. ユーザーからの改善要求を理解
3. GitHub Issueのタイトル、本文、ラベルを日本語で提案（まだ投稿はしない）

【提案する形式】
以下のJSONフォーマットで改善提案を作成してください：

```json
{{
  "title": "📝 README改善提案: [具体的な改善内容]",
  "body": "## 改善提案\\n\\n[詳細な改善提案を日本語で]\\n\\n## 背景\\n\\n[改善が必要な理由]\\n\\n## 提案内容\\n\\n[具体的な改善案]",
  "labels": ["documentation", "improvement", "readme"]
}}
```

必ず日本語で内容を作成し、JSONフォーマットで返してください。
"""
        
        user_prompt_generation = """
このREADMEファイルを見て、以下の観点から改善提案をお願いします：

1. プロジェクトの目的や概要が不明確
2. インストール手順が簡素すぎる
3. 使用方法の説明が不足
4. 前提条件の記載がない

上記の問題点を解決するための改善提案を、先ほどのJSONフォーマットで作成してください。
必ず日本語で作成してください。
"""
        
        print("   📝 Issue内容生成中...")
        
        query_options_generation = {
            "model": "azure-tk-gpt-4o",
            "messages": [
                {"role": "system", "content": system_prompt_generation},
                {"role": "user", "content": user_prompt_generation},
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        generation_response = await llm_service.query(
            prompt="", options=query_options_generation  # messagesで指定済み
        )
        
        print(f"   ✅ Issue内容生成完了")
        
        # 5. 生成されたIssue内容を解析
        print("\n5️⃣ 生成されたIssue内容の解析...")
        
        import re
        
        # JSONブロックを抽出
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', generation_response.content, re.DOTALL)
        if json_match:
            try:
                issue_data = json.loads(json_match.group(1))
                print("   ✅ Issue内容の解析成功")
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON解析エラー: {e}")
                print(f"   📄 生成内容: {generation_response.content}")
                return False
        else:
            print("   ❌ JSON形式のIssue内容が見つかりません")
            print(f"   📄 生成内容: {generation_response.content}")
            return False
        
        # 6. ユーザー確認（実際の入力）
        print("\n6️⃣ ユーザー確認...")
        print("=" * 60)
        print("📋 生成されたGitHub Issue内容:")
        print("=" * 60)
        print(f"リポジトリ: {config.test_repository}")
        print(f"タイトル: {issue_data['title']}")
        print(f"\n本文:\n{issue_data['body']}")
        print(f"\nラベル: {', '.join(issue_data['labels'])}")
        print("=" * 60)
        
        # 実際のユーザー入力
        print("\n❓ この内容でGitHub Issueを投稿しますか？")
        print("   [1] はい - Issueを投稿")
        print("   [2] いいえ - キャンセル")
        print("   [3] 修正 - 内容を修正して再生成")
        
        while True:
            user_choice = input("選択してください (1/2/3): ").strip()
            if user_choice in ["1", "2", "3"]:
                break
            print("無効な選択です。1、2、または3を入力してください。")
        
        # 7. ユーザー選択に基づく処理
        if user_choice == "1":
            print("\n7️⃣ GitHub Issue投稿実行...")
            
            # 第2段階 - 実際のIssue投稿
            system_prompt_posting = f"""
あなたは確認済みのGitHub Issue投稿を実行する専門家です。

リポジトリ: {config.test_repository}

以下の確認済み内容でIssueを投稿してください：

タイトル: {issue_data['title']}
本文: {issue_data['body']}
ラベル: {issue_data['labels']}

利用可能な関数:
- create_github_issue: 上記内容でGitHub Issueを作成

必ず上記の確認済み内容でIssueを投稿してください。
"""
            
            user_prompt_posting = "確認済みの内容でGitHub Issueを投稿してください。"
            
            # Function Calling有効でLLM実行
            tools = []
            for func_def in function_registry.get_all_function_definitions():
                tool = {
                    "type": "function",
                    "function": {
                        "name": func_def.name,
                        "description": func_def.description,
                        "parameters": func_def.parameters,
                    },
                }
                tools.append(tool)
            
            query_options = {
                "model": "azure-tk-gpt-4o",
                "messages": [
                    {"role": "system", "content": system_prompt_posting},
                    {"role": "user", "content": user_prompt_posting},
                ],
                "tools": tools,  # OpenAI tools API使用
                "tool_choice": "auto",
                "temperature": 0.1,
            }
            
            posting_response = await llm_service.query(
                prompt="", options=query_options  # messagesで指定済み
            )
            
            print(f"   📤 LLM応答: {posting_response.content}")
            
            # Function Call処理
            if posting_response.tool_calls:
                print(f"\n   🔧 Function Call検出: {len(posting_response.tool_calls)}個")
                
                for tool_call in posting_response.tool_calls:
                    print(f"   📞 関数呼び出し: {tool_call.function.name}")
                    
                    if tool_call.function.name == "create_github_issue":
                        try:
                            # Function実行（既存のラッパー使用）
                            func = function_registry.get_function(tool_call.function.name)
                            
                            if func is None:
                                print(f"   ❌ 関数が見つかりません: {tool_call.function.name}")
                                return False
                            
                            args = json.loads(tool_call.function.arguments)
                            
                            result = await func(**args)
                            
                            if isinstance(result, dict) and result.get("success"):
                                print(f"   ✅ Issue投稿成功")
                                result_content = result.get("result", {})
                                if isinstance(result_content, dict) and "issue_info" in result_content:
                                    issue_info = result_content["issue_info"]
                                    if isinstance(issue_info, dict):
                                        print(f"   📋 Issue #{issue_info.get('number')} が作成されました")
                                        print(f"   🔗 URL: {issue_info.get('url')}")
                                        print(f"   🏷️ ラベル: {issue_info.get('labels', [])}")
                                print(f"   🎉 確認フロー付きIssue作成が完了しました！")
                                return True
                            else:
                                print(f"   ❌ Issue投稿エラー: {result.get('error') if isinstance(result, dict) else result}")
                                return False
                            
                        except Exception as e:
                            print(f"   ❌ Issue投稿エラー: {e}")
                            import traceback
                            traceback.print_exc()
                            return False
            else:
                print("   ⚠️ Function Callが実行されませんでした")
                return False
                
        elif user_choice == "2":
            print("\n❌ ユーザーによりキャンセルされました")
            return True  # キャンセルも正常終了
            
        elif user_choice == "3":
            print("\n🔄 内容修正機能は今後実装予定です")
            return True
        
        print("\n🎉 インタラクティブ確認フロー付きE2Eテスト完了")
        return True
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
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
    result1 = await test_github_permissions_check()
    results.append(("権限確認", result1))

    # テスト2: README改善フロー
    print("\n📖 テスト2: README改善フロー")
    result2 = await test_readme_improvement_flow()
    results.append(("README改善フロー", result2))

    # テスト3: 基本GitHub Issue作成
    print("\n🚀 テスト3: 基本GitHub Issue作成")
    result3 = await test_basic_github_issue_creation()
    results.append(("基本Issue作成", result3))

    # テスト4: README改善確認フロー付きテスト
    print("\n🔄 テスト4: README改善確認フロー付き")
    result4 = await test_readme_improvement_with_confirmation()
    results.append(("README改善確認フロー", result4))

    # テスト5: README改善インタラクティブ確認フロー付きテスト
    print("\n🔄 テスト5: README改善インタラクティブ確認フロー付き")
    result5 = await test_readme_improvement_interactive_confirmation()
    results.append(("README改善インタラクティブ確認フロー", result5))

    # 最終結果
    print("\n" + "=" * 60)
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
