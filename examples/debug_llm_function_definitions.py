#!/usr/bin/env python3
"""
LLMが受け取る関数定義をデバッグするスクリプト
"""

import asyncio
import sys

sys.path.append(".")

from doc_ai_helper_backend.services.llm import LLMServiceFactory


async def debug_llm_function_definitions():
    """LLMサービスが受け取る関数定義をデバッグ"""
    print("🔍 LLM Function Definitions Debug")
    print("=" * 50)

    # MockLLMサービスを作成
    llm_service = LLMServiceFactory.create("mock")

    # 利用可能な関数を取得
    functions = await llm_service.get_available_functions()

    print(f"📋 Total functions available: {len(functions)}")

    # calculate_simple_mathとextract_document_contextの詳細を確認
    target_functions = [
        "calculate_simple_math",
        "extract_document_context",
        "optimize_document_content",
    ]

    for target in target_functions:
        print(f"\n🔍 Function: {target}")
        print("-" * 30)

        matching_functions = [f for f in functions if f.name == target]
        if matching_functions:
            func = matching_functions[0]
            print(f"Name: {func.name}")
            print(f"Description: {func.description}")
            print(f"Parameters: {func.parameters}")
        else:
            print(f"❌ Function '{target}' not found!")


if __name__ == "__main__":
    asyncio.run(debug_llm_function_definitions())
