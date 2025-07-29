"""
Tool Execution and Followup

ツール実行とフォローアップレスポンス生成機能を提供します。
"""

import json
import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING

# Forward references for repository context models
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.repository_context import RepositoryContext
    from doc_ai_helper_backend.services.llm.base import LLMServiceBase

from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    MessageItem,
    MessageRole,
    FunctionDefinition,
)

logger = logging.getLogger(__name__)


async def handle_tool_execution_and_followup(
    service: "LLMServiceBase",
    llm_response: LLMResponse,
    tools: List[FunctionDefinition],
    repository_context: Optional["RepositoryContext"],
    original_prompt: str,
    conversation_history: Optional[List[MessageItem]],
    system_prompt: Optional[str],
    options: Optional[Dict[str, Any]],
):
    """ツール実行とフォローアップレスポンス生成を処理"""
    logger.info(f"Tool calls detected: {len(llm_response.tool_calls)}, executing tools and generating followup response")
    
    # 全ツール呼び出しを実行
    executed_results = []
    for tool_call in llm_response.tool_calls:
        try:
            # リポジトリコンテキストを辞書に変換
            repo_context_dict = convert_repository_context_to_dict(repository_context)
            
            # 利用可能な関数のマッピング取得
            available_functions = {func.name: func for func in tools}
            
            # ツール呼び出し実行
            result = await service.execute_function_call(
                tool_call.function,
                available_functions,
                repository_context=repo_context_dict,
            )
            
            executed_results.append({
                "tool_call_id": tool_call.id,
                "function_name": tool_call.function.name,
                "result": result,
            })
            
            logger.info(f"Tool '{tool_call.function.name}' executed successfully")
            
        except Exception as e:
            executed_results.append({
                "tool_call_id": tool_call.id,  
                "function_name": tool_call.function.name,
                "error": str(e),
            })
            logger.error(f"Tool '{tool_call.function.name}' execution failed: {e}")

    # 実行結果をレスポンスに追加
    llm_response.tool_execution_results = executed_results
    
    # ツール実行結果に基づくフォローアップレスポンス生成
    followup_response = await generate_followup_response(
        service=service,
        original_prompt=original_prompt,
        tool_calls=llm_response.tool_calls,
        tool_results=executed_results,
        conversation_history=conversation_history,
        system_prompt=system_prompt,
        options=options or {},
    )
    
    # フォローアップでメインレスポンス内容を更新
    if followup_response and followup_response.content:
        llm_response.content = followup_response.content
        
        # 使用量統計を更新
        if followup_response.usage and llm_response.usage:
            llm_response.usage.prompt_tokens += followup_response.usage.prompt_tokens
            llm_response.usage.completion_tokens += followup_response.usage.completion_tokens
            llm_response.usage.total_tokens += followup_response.usage.total_tokens
        
        # 会話履歴の最適化情報も転送（重要：これが抜けていた）
        if hasattr(followup_response, 'optimized_conversation_history'):
            llm_response.optimized_conversation_history = followup_response.optimized_conversation_history
        if hasattr(followup_response, 'history_optimization_info'):
            llm_response.history_optimization_info = followup_response.history_optimization_info
        
        content_len = len(llm_response.content) if llm_response.content is not None else 0
        logger.info(f"Followup response generated: {content_len} characters")
        
        # 会話履歴の転送状況をログ出力（安全にチェック）
        history = getattr(llm_response, 'optimized_conversation_history', None)
        history_count = len(history) if history is not None else 0
        logger.info(f"Conversation history transferred: {history_count} messages")
    else:
        logger.warning("Followup response generation failed or returned empty content")


def convert_repository_context_to_dict(
    repository_context: Optional["RepositoryContext"]
) -> Optional[Dict[str, Any]]:
    """リポジトリコンテキストを辞書形式に変換"""
    if not repository_context:
        logger.warning("No repository context available for tool execution")
        return None
        
    repo_context_dict = {
        "service": repository_context.service.value if hasattr(repository_context.service, 'value') else repository_context.service,
        "owner": repository_context.owner,
        "repo": repository_context.repo,
        "ref": repository_context.ref,
        "current_path": repository_context.current_path,
        "base_url": repository_context.base_url,
    }
    logger.debug(f"Repository context converted to dict: {repo_context_dict}")
    return repo_context_dict


async def generate_followup_response(
    service: "LLMServiceBase",
    original_prompt: str,
    tool_calls: List,
    tool_results: List[Dict[str, Any]],
    conversation_history: Optional[List[MessageItem]] = None,
    system_prompt: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Optional[LLMResponse]:
    """
    ツール実行結果に基づくフォローアップレスポンス生成
    """
    try:
        logger.info("Generating followup response based on tool execution results")
        
        # フォローアップ会話履歴構築
        followup_history = []
        
        # 元の会話履歴を追加
        if conversation_history:
            followup_history.extend(conversation_history)
        
        # 元のユーザープロンプトを追加
        followup_history.append(MessageItem(
            role=MessageRole.USER,
            content=original_prompt
        ))
        
        # ツール呼び出しのアシスタントレスポンス（簡略版）
        tool_call_summary = []
        for i, tool_call in enumerate(tool_calls):
            tool_call_summary.append(f"{i+1}. {tool_call.function.name}を実行しました")
        
        followup_history.append(MessageItem(
            role=MessageRole.ASSISTANT,
            content=f"以下のツールを実行しました：\n" + "\n".join(tool_call_summary)
        ))
        
        # ツール結果サマリーを構築
        tool_results_summary = build_tool_results_summary(tool_results)
        
        # フォローアッププロンプト作成
        followup_prompt = f"""上記のツール実行結果を踏まえて、以下の内容で包括的な回答を日本語で提供してください：

ツール実行結果：
{chr(10).join(tool_results_summary)}

元のリクエストに対する完全な回答を、ツール実行結果を統合して作成してください。具体的で実用的な内容を含め、ユーザーに価値のある情報を提供してください。"""
        
        followup_history.append(MessageItem(
            role=MessageRole.USER,
            content=followup_prompt
        ))
        
        # フォローアップオプション準備（再帰を防ぐためツールなし）
        followup_options = (options or {}).copy()
        followup_options["temperature"] = 0.7  # 合成により創造性を加える
        
        # ツールなしでフォローアップレスポンス生成
        followup_provider_options = await service._prepare_provider_options(
            prompt=followup_prompt,
            conversation_history=followup_history[:-1],  # フォローアッププロンプトは別途追加済み
            options=followup_options,
            system_prompt=system_prompt,
            tools=None,  # 再帰防止のためツールなし
            tool_choice=None,
        )
        
        # フォローアップ用プロバイダーAPI呼び出し
        followup_raw_response = await service._call_provider_api(followup_provider_options)
        
        # フォローアップレスポンス変換
        followup_response = await service._convert_provider_response(
            followup_raw_response, followup_provider_options
        )
        
        # フォローアップレスポンスに会話履歴最適化情報を設定
        if hasattr(service, '_set_conversation_optimization_info'):
            service._set_conversation_optimization_info(followup_response, followup_history)
        
        logger.info(f"Followup response generated successfully: {len(followup_response.content) if followup_response.content else 0} characters")
        return followup_response
        
    except Exception as e:
        logger.error(f"Error generating followup response: {str(e)}")
        return None


def build_tool_results_summary(tool_results: List[Dict[str, Any]]) -> List[str]:
    """ツール実行結果のサマリーを構築"""
    tool_results_summary = []
    for result in tool_results:
        function_name = result.get("function_name", "不明なツール")
        if "error" in result:
            tool_results_summary.append(f"❌ {function_name}: エラーが発生しました - {result['error']}")
        else:
            # 結果から意味のある内容を抽出
            result_data = result.get("result", {})
            if isinstance(result_data, dict):
                if result_data.get("success"):
                    if "result" in result_data and isinstance(result_data["result"], str):
                        # JSON結果をパースしてみる
                        try:
                            parsed_result = json.loads(result_data["result"])
                            if isinstance(parsed_result, dict):
                                if "summary" in parsed_result:
                                    tool_results_summary.append(f"✅ {function_name}: 要約が生成されました")
                                elif "recommendations" in parsed_result:
                                    tool_results_summary.append(f"✅ {function_name}: 改善提案が生成されました")
                                else:
                                    tool_results_summary.append(f"✅ {function_name}: 分析が完了しました")
                            else:
                                tool_results_summary.append(f"✅ {function_name}: 処理が完了しました")
                        except json.JSONDecodeError:
                            tool_results_summary.append(f"✅ {function_name}: 結果を取得しました")
                    else:
                        tool_results_summary.append(f"✅ {function_name}: 実行完了")
                else:
                    tool_results_summary.append(f"❌ {function_name}: {result_data.get('error', '実行に失敗しました')}")
            else:
                tool_results_summary.append(f"✅ {function_name}: 実行完了")
    return tool_results_summary