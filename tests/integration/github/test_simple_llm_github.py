#!/usr/bin/env python3
"""
シンプルなLLM経由GitHub MCP E2Eテスト
基本的なFunction Callingの動作確認用
"""

import asyncio
import json
import os
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory


async def simple_llm_github_test():
    """シンプルなLLM GitHub Function Callingテスト"""
    print("🤖 シンプル LLM GitHub テスト")
    print("=" * 40)
    
    # 環境変数チェック
    openai_key = os.getenv('OPENAI_API_KEY')
    github_token = os.getenv('GITHUB_TOKEN')
    
    print(f"OpenAI API Key: {'✅' if openai_key else '❌'}")
    print(f"GitHub Token: {'✅' if github_token else '❌'}")
    
    if not openai_key:
        print("\n❌ OPENAI_API_KEYが設定されていません")
        return
    
    try:
        # LLMサービス初期化
        print("\n🔄 LLMサービス初期化...")
        llm_service = LLMServiceFactory.create(
            provider='openai',
            api_key=openai_key,
            base_url=os.getenv('OPENAI_BASE_URL'),
            default_model='azure-tk-gpt-4o'
        )
        
        # GitHubツール関数定義（tools形式）
        github_tool = {
            "type": "function",
            "function": {
                "name": "create_github_issue",
                "description": "GitHubリポジトリにIssueを作成します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Issueのタイトル"
                        },
                        "description": {
                            "type": "string", 
                            "description": "Issueの詳細説明"
                        },
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "ラベルのリスト"
                        }
                    },
                    "required": ["title", "description"]
                }
            }
        }
        
        # テスト用プロンプト
        system_prompt = """
あなたはGitHub Issue作成アシスタントです。
ユーザーの要求に応じてIssueを作成してください。
利用可能な関数: create_github_issue
"""
        
        user_prompt = """
テスト用のGitHub Issueを作成してください。
タイトル: 🧪 LLM Function Calling テスト
内容: このIssueはLLMのFunction Calling機能をテストするために作成されました。
ラベル: ["test", "llm", "function-calling"]
"""
        
        # LLM問い合わせ（Function Calling使用）
        print("📤 LLMに問い合わせ中...")
        
        query_options = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "tools": [github_tool],
            "tool_choice": "auto",
            "temperature": 0.1
        }
        
        result = await llm_service.query(
            prompt="",
            options=query_options
        )
        
        print("📥 LLM応答受信")
        
        # 結果表示
        print("\n📊 結果:")
        print(f"Content: {result.content}")
        
        if hasattr(result, 'tool_calls') and result.tool_calls:
            print(f"Tool Calls: {len(result.tool_calls)}件")
            for i, call in enumerate(result.tool_calls, 1):
                print(f"  Call {i}:")
                print(f"    ID: {call.id}")
                print(f"    関数名: {call.function.name}")
                print(f"    引数: {call.function.arguments}")
                
                # 実際のGitHubトークンがある場合は実行
                if github_token and call.function.name == 'create_github_issue':
                    print("    🚀 実際のGitHub Issue作成を実行中...")
                    
                    # ここで実際のMCPツールを呼び出し
                    from doc_ai_helper_backend.services.mcp.tools.github_tools import create_github_issue
                    
                    # テスト用リポジトリコンテキスト
                    test_repo = os.getenv('TEST_GITHUB_REPOSITORY', 'test-owner/test-repo')
                    owner, repo = test_repo.split('/', 1)
                    
                    repository_context = {
                        "repo": repo,
                        "owner": owner,
                        "service": "github",
                        "ref": "main"
                    }
                    
                    # 引数をJSONからパース
                    import json
                    try:
                        args = json.loads(call.function.arguments)
                    except json.JSONDecodeError:
                        args = {}
                    
                    issue_result = await create_github_issue(
                        title=args.get('title', 'テストIssue'),
                        description=args.get('description', 'テストです'),
                        labels=args.get('labels', []),
                        github_token=github_token,
                        repository_context=repository_context
                    )
                    
                    print("    📋 Issue作成結果:")
                    result_data = json.loads(issue_result)
                    if result_data.get('success'):
                        issue_info = result_data.get('issue_info', {})
                        print(f"       ✅ Issue #{issue_info.get('number')} 作成成功")
                        print(f"       🔗 URL: {issue_info.get('url')}")
                    else:
                        print(f"       ❌ エラー: {result_data.get('error')}")
                else:
                    print("    ⏭️  GitHub Token未設定のため、実際の作成はスキップ")
        else:
            print("Tool Callsなし")
        
        print("\n✅ テスト完了")
        
    except Exception as e:
        print(f"\n❌ エラー: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(simple_llm_github_test())
