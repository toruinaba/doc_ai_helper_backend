#!/usr/bin/env python3
"""
Debug script to see actual tool execution response
"""
import asyncio
import json
import sys
import os

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

from tests.e2e.helpers.config import E2EConfig
from tests.e2e.helpers.api_client import BackendAPIClient
from doc_ai_helper_backend.models.repository_context import RepositoryContext

async def debug_batch_analysis():
    """Debug batch document analysis response"""
    print("=== Debug Batch Document Analysis ===")
    
    # Setup
    e2e_config = E2EConfig()
    client = BackendAPIClient(e2e_config.api_base_url)
    
    # Request
    batch_request = f"""
以下のリポジトリの複数のドキュメントを分析してください：

リポジトリ: {e2e_config.github_owner}/{e2e_config.github_repo}

以下のドキュメントを分析してください:
1. README.md
2. ドキュメント全体の構造

やってほしいこと:
1. 各ドキュメントの要約を作成
2. 全体的な改善提案を作成
3. 最も重要な改善点を特定

summarize_document_with_llm と create_improvement_recommendations_with_llm を使用してください。
    """
    
    # Repository context
    repository_context = RepositoryContext(
        service="github",
        owner=e2e_config.github_owner,
        repo=e2e_config.github_repo,
        ref="main",
        current_path="README.md"
    )
    
    print(f"Sending request to: {e2e_config.api_base_url}")
    print(f"Repository: {e2e_config.github_owner}/{e2e_config.github_repo}")  
    print(f"LLM Provider: {e2e_config.llm_provider}")
    print(f"Repository Context: {repository_context}")
    print(f"Repository Context Dict: {repository_context.model_dump()}")
    
    # Execute
    response = await client.query_llm(
        prompt=batch_request,
        provider=e2e_config.llm_provider,
        tools_enabled=True,
        repository_context=repository_context.model_dump()
    )
    
    print("\n=== RESPONSE ANALYSIS ===")
    print(f"Response type: {type(response)}")
    print(f"Response keys: {list(response.keys()) if isinstance(response, dict) else 'Not a dict'}")
    
    if isinstance(response, dict):
        print(f"Content length: {len(response.get('content', ''))}")
        print(f"Content value: '{response.get('content', '')}'")
        print(f"Provider: {response.get('provider', 'N/A')}")
        print(f"Model: {response.get('model', 'N/A')}")
        
        # Tool calls
        tool_calls = response.get('tool_calls', [])
        print(f"Tool calls count: {len(tool_calls) if tool_calls else 0}")
        if tool_calls:
            for i, call in enumerate(tool_calls):
                func_name = call.get('function', {}).get('name', 'Unknown')
                print(f"  Tool {i+1}: {func_name}")
        
        # Tool execution results
        tool_results = response.get('tool_execution_results', [])
        print(f"Tool execution results count: {len(tool_results) if tool_results else 0}")
        if tool_results:
            for i, result in enumerate(tool_results):
                func_name = result.get('function_name', 'Unknown')
                result_data = result.get('result', {})
                print(f"  Result {i+1}: {func_name}")
                print(f"    Result type: {type(result_data)}")
                if isinstance(result_data, dict):
                    print(f"    Result keys: {list(result_data.keys())}")
                    print(f"    Success: {result_data.get('success', 'N/A')}")
                elif isinstance(result_data, str):
                    print(f"    Result string length: {len(result_data)}")
                    print(f"    Result preview: {result_data[:100]}...")
    
    print(f"\n=== FULL RESPONSE ===")
    print(json.dumps(response, indent=2, default=str, ensure_ascii=False))
    
    return response

if __name__ == "__main__":
    asyncio.run(debug_batch_analysis())