"""
LLM Orchestrator

LLMサービスの統合オーケストレータ。
クエリ実行制御を中心とし、各機能は専門モジュールに委譲します。
"""

import asyncio
import hashlib
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, TYPE_CHECKING

# Forward references for repository context models
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.repository_context import (
        RepositoryContext,
        DocumentMetadata,
    )
    from doc_ai_helper_backend.services.llm.base import LLMServiceBase

from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMQueryRequest,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ToolChoice,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException, ServiceNotFoundError
from doc_ai_helper_backend.core.config import settings

# 分割されたモジュールからの関数インポート
from .conversation_optimizer import (
    optimize_conversation_history,
    build_conversation_messages,
)
from .system_prompt_generator import generate_system_prompt
from .tool_executor import handle_tool_execution_and_followup

logger = logging.getLogger(__name__)




class LLMOrchestrator:
    """
    LLM処理の統合オーケストレータ
    
    以前のQueryManagerの機能を統合し、より整理された単一のエントリーポイントを提供します。
    システムプロンプト生成、キャッシング、ツール実行、レスポンス処理を統一して管理します。
    """

    def __init__(self, cache_service):
        """
        オーケストレータの初期化

        Args:
            cache_service: レスポンスキャッシュサービス
        """
        self.cache_service = cache_service
        self.document_service = None  # DocumentServiceは依存関係注入で設定される

    # === 新しい構造化リクエスト処理メソッド ===
    
    async def execute_query(self, request: LLMQueryRequest) -> LLMResponse:
        """
        構造化されたLLMQueryRequestを処理
        
        Args:
            request: 構造化されたLLMクエリリクエスト
            
        Returns:
            LLMResponse: LLMからのレスポンス
        """
        from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
        
        logger.info(f"Starting query execution with prompt length: {len(request.query.prompt or '')}")
        
        try:
            # プロンプト検証
            if not request.query.prompt or not request.query.prompt.strip():
                raise LLMServiceException("Prompt cannot be empty")

            # サービスインスタンスを作成
            service_config = {"model": request.query.model}
            
            # プロバイダー固有の設定を追加
            if request.query.provider.lower() == "openai":
                service_config.update({
                    "api_key": settings.openai_api_key,
                    "base_url": settings.openai_base_url,
                    "default_model": request.query.model or settings.default_openai_model
                })
            
            service = LLMServiceFactory.create_with_mcp(
                request.query.provider,
                enable_mcp=True,
                **service_config
            )
            
            # 処理オプションを準備
            options = {}
            if request.processing and request.processing.options:
                options.update(request.processing.options)
            
            # リポジトリコンテキストの準備
            repository_context = None
            document_metadata = None
            document_content = None
            
            if request.document and request.document.repository_context:
                repository_context = request.document.repository_context
                logger.info(f"Repository context received: service={repository_context.service}, owner={repository_context.owner}, repo={repository_context.repo}, current_path={repository_context.current_path}")
                
                # ドキュメントコンテキストがある場合、必要に応じて文書取得
                if request.document.auto_include_document:
                    document_content, document_metadata = await self._retrieve_document_content(repository_context)
            
            # ツールが有効な場合は、ツール付きクエリを実行
            if request.tools and request.tools.enable_tools:
                # 利用可能なツールを取得
                tools = await service.get_available_functions()
                logger.info(f"Available MCP tools count: {len(tools)}")
                for tool in tools:
                    logger.debug(f"Available tool: {tool.name} - {tool.description[:100]}...")
                
                tool_choice = None
                if request.tools.tool_choice:
                    from doc_ai_helper_backend.models.llm import ToolChoice
                    tool_choice = ToolChoice(type=request.tools.tool_choice)
                
                return await self._execute_query_with_tools_internal(
                    service=service,
                    prompt=request.query.prompt,
                    tools=tools,
                    conversation_history=request.query.conversation_history,
                    tool_choice=tool_choice,
                    options=options,
                    repository_context=repository_context,
                    document_metadata=document_metadata,
                    document_content=document_content
                )
            
            # 標準クエリの実行（直接実装）
            # 1. キャッシュチェック
            cache_key = self._generate_cache_key(
                request.query.prompt, request.query.conversation_history, options, repository_context,
                document_metadata, document_content
            )

            if cached_response := self.cache_service.get(cache_key):
                logger.info("Returning cached response")
                return cached_response

            # 2. システムプロンプト生成
            system_prompt = generate_system_prompt(
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content=document_content,
                include_document_in_system_prompt=request.document.auto_include_document,
            )

            # 3. プロバイダー固有オプション準備
            provider_options = await service._prepare_provider_options(
                prompt=request.query.prompt,
                conversation_history=request.query.conversation_history,
                options=options,
                system_prompt=system_prompt,
            )

            # 4. プロバイダーAPI呼び出し
            raw_response = await service._call_provider_api(provider_options)

            # 5. レスポンス変換
            llm_response = await service._convert_provider_response(
                raw_response, provider_options
            )

            # 6. 会話履歴最適化情報設定（現在のやり取りを含む）
            updated_history = self._build_updated_conversation_history(
                request.query.conversation_history, 
                request.query.prompt, 
                llm_response.content
            )
            self._set_conversation_optimization_info(llm_response, updated_history)

            # 7. レスポンスキャッシュ
            self.cache_service[cache_key] = llm_response

            logger.info(f"Query execution completed successfully, model: {llm_response.model}")
            return llm_response

        except ServiceNotFoundError:
            # ServiceNotFoundErrorをそのまま再raise（APIレイヤーで適切に処理される）
            raise
        except Exception as e:
            logger.error(f"Error in query execution: {str(e)}")
            raise LLMServiceException(f"Query execution failed: {str(e)}")
    
    async def execute_streaming_query(self, request: LLMQueryRequest) -> AsyncGenerator[Dict[str, Any], None]:
        """
        構造化されたLLMQueryRequestでストリーミングクエリを処理
        
        Args:
            request: 構造化されたLLMクエリリクエスト
            
        Yields:
            Dict[str, Any]: ストリーミングレスポンスチャンク
        """
        from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
        
        logger.info(f"Starting streaming query execution with prompt length: {len(request.query.prompt or '')}")
        
        try:
            # プロンプト検証
            if not request.query.prompt or not request.query.prompt.strip():
                raise LLMServiceException("Prompt cannot be empty")

            # サービスインスタンスを作成
            service_config = {"model": request.query.model}
            
            # プロバイダー固有の設定を追加
            if request.query.provider.lower() == "openai":
                service_config.update({
                    "api_key": settings.openai_api_key,
                    "base_url": settings.openai_base_url,
                    "default_model": request.query.model or settings.default_openai_model
                })
            
            service = LLMServiceFactory.create_with_mcp(
                request.query.provider,
                enable_mcp=True,
                **service_config
            )
            
            # 処理オプションを準備
            options = {}
            if request.processing and request.processing.options:
                options.update(request.processing.options)

            # リポジトリコンテキストの準備
            repository_context = None
            document_metadata = None
            document_content = None
            
            if request.document and request.document.repository_context:
                repository_context = request.document.repository_context
                logger.info(f"Repository context received: service={repository_context.service}, owner={repository_context.owner}, repo={repository_context.repo}, current_path={repository_context.current_path}")
                
                # ドキュメントコンテキストがある場合、必要に応じて文書取得
                if request.document.auto_include_document:
                    document_content, document_metadata = await self._retrieve_document_content(repository_context)
                
            # 1. システムプロンプト生成
            system_prompt = generate_system_prompt(
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content=document_content,
                include_document_in_system_prompt=request.document.auto_include_document,
            )

            # 2. プロバイダー固有オプション準備
            provider_options = await service._prepare_provider_options(
                prompt=request.query.prompt,
                conversation_history=request.query.conversation_history,
                options=options,
                system_prompt=system_prompt,
            )

            # 3. プロバイダーAPIからのストリーミング
            async for chunk in service._stream_provider_api(provider_options):
                # ストリーミングチャンクを構造化データとして返す
                yield {"content": chunk, "done": False}
            
            # ストリーミング完了を示す
            yield {"content": "", "done": True}

            logger.info("Streaming query execution completed successfully")

        except Exception as e:
            logger.error(f"Error in streaming query execution: {str(e)}")
            raise LLMServiceException(f"Streaming query execution failed: {str(e)}")

    # === 内部実装メソッド ===

    async def _execute_query_with_tools_internal(
        self,
        service: "LLMServiceBase",
        prompt: str,
        tools: List[FunctionDefinition],
        conversation_history: Optional[List[MessageItem]] = None,
        tool_choice: Optional[ToolChoice] = None,
        options: Optional[Dict[str, Any]] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        include_document_in_system_prompt: bool = True,
    ) -> LLMResponse:
        """
        ツール付きLLMクエリを実行
        """
        logger.info(f"Starting query with tools execution, tools count: {len(tools)}")
        
        # リポジトリコンテキストのログ
        if repository_context:
            logger.info(f"Repository context - service: {repository_context.service}, owner: {repository_context.owner}, repo: {repository_context.repo}")
        else:
            logger.warning("No repository context provided")

        try:
            # 1. システムプロンプト生成
            system_prompt = generate_system_prompt(
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content=document_content,
                include_document_in_system_prompt=include_document_in_system_prompt,
            )

            # 2. ツール付きプロバイダーオプション準備
            provider_options = await service._prepare_provider_options(
                prompt=prompt,
                conversation_history=conversation_history,
                options=options or {},
                system_prompt=system_prompt,
                tools=tools,
                tool_choice=tool_choice,
            )

            # 3. プロバイダーAPI呼び出し
            raw_response = await service._call_provider_api(provider_options)

            # 4. レスポンス変換
            llm_response = await service._convert_provider_response(
                raw_response, provider_options
            )

            # 5. ツール実行とフォローアップ処理
            if llm_response.tool_calls and len(llm_response.tool_calls) > 0:
                await handle_tool_execution_and_followup(
                    service, llm_response, tools, repository_context,
                    prompt, conversation_history, system_prompt, options
                )
            else:
                logger.info("No tool calls detected in LLM response")
                llm_response.tool_execution_results = []

            # 6. 会話履歴最適化情報設定（現在のやり取りを含む）
            updated_history = self._build_updated_conversation_history(
                conversation_history, 
                prompt, 
                llm_response.content
            )
            self._set_conversation_optimization_info(llm_response, updated_history)

            logger.info(f"Query with tools execution completed successfully, model: {llm_response.model}")
            return llm_response

        except Exception as e:
            logger.error(f"Error in query with tools execution: {str(e)}")
            raise LLMServiceException(f"Query with tools execution failed: {str(e)}")

    # === ユーティリティメソッド ===

    def _generate_cache_key(
        self,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        include_document_in_system_prompt: bool = True,
    ) -> Optional[str]:
        """
        統合されたシステムプロンプト生成
        
        以前のSystemPromptBuilderの機能を簡素化して統合。
        実際には1種類のプロンプトタイプしか使われていないため、
        テンプレートシステムを簡素化してここに統合。
        """
        try:
            if not include_document_in_system_prompt:
                return None

            prompt_parts = []

            # バイリンガルツールシステムプロンプト（常に有効）
            prompt_parts.append("""=== BILINGUAL TOOL EXECUTION SYSTEM ===

IMPORTANT: You have access to tools for document analysis and repository management. When the user requests tool execution in Japanese, you MUST:

1. **TOOL SELECTION**: Interpret Japanese tool requests as English tool execution instructions
   - When user says "summarize_document_with_llm ツールを呼び出してください" → Execute summarize_document_with_llm tool
   - When user says "create_improvement_recommendations_with_llm ツールを呼び出してください" → Execute create_improvement_recommendations_with_llm tool  
   - When user says "create_git_issue ツールを呼び出してください" → Execute create_git_issue tool
   - When user requests multiple tools → Execute ALL requested tools

2. **TOOL EXECUTION**: Always execute tools when explicitly requested by the user
   - Use auto_include_document=True to automatically retrieve document content
   - Pass appropriate parameters to each tool
   - Execute multiple tools if requested

3. **RESPONSE LANGUAGE**: Always respond to the user in Japanese (日本語)
   - Tool execution results should be summarized in Japanese
   - Maintain natural Japanese conversation flow
   - Provide helpful explanations in Japanese

4. **PRIORITY**: Tool execution takes priority over conversation
   - If user requests tools, execute them immediately
   - Don't ask for confirmation - execute the requested tools
   - Provide results and summary in Japanese""")

            # リポジトリコンテキスト情報
            if repository_context:
                prompt_parts.append(f"リポジトリ: {repository_context.owner}/{repository_context.repo}")
                
                if repository_context.current_path:
                    prompt_parts.append(f"現在のファイル: {repository_context.current_path}")

            # ドキュメントメタデータ情報
            if document_metadata:
                # content_typeを使用してファイルタイプを判定
                content_type = getattr(document_metadata, 'content_type', '').lower()
                if any(code_type in content_type for code_type in ['python', 'javascript', 'json', 'yaml']):
                    prompt_parts.append("このファイルはコードファイルです。")
                elif 'markdown' in content_type or 'html' in content_type or (
                    'text' in content_type and not any(x in content_type for x in ['python', 'javascript', 'json', 'yaml'])
                ):
                    prompt_parts.append("このファイルはドキュメントファイルです。")
                elif content_type:
                    prompt_parts.append(f"ファイルタイプ: {content_type}")
                    
                # ファイルサイズ情報も追加
                if hasattr(document_metadata, 'size') and document_metadata.size:
                    prompt_parts.append(f"ファイルサイズ: {document_metadata.size} bytes")

            # ドキュメント内容埋め込み（新機能）
            if document_content:
                prompt_parts.append("=== 現在のドキュメント内容 ===")
                
                # 長すぎる場合は切り詰め（トークン制限を考慮）
                max_content_length = 8000  # 約2000トークンに相当
                if len(document_content) > max_content_length:
                    truncated_content = document_content[:max_content_length] + "\n...(内容が長いため省略されました)"
                    prompt_parts.append(truncated_content)
                    logger.info(f"Document content truncated from {len(document_content)} to {max_content_length} characters")
                else:
                    prompt_parts.append(document_content)
                    logger.info(f"Full document content included: {len(document_content)} characters")
                
                prompt_parts.append("=== ドキュメント内容ここまで ===")
                prompt_parts.append("上記のドキュメント内容を参考にして、コンテキストに基づいた回答を提供してください。")

            return "\n".join(prompt_parts)

        except Exception as e:
            logger.warning(f"Failed to generate system prompt: {str(e)}, continuing without system prompt")
            return None

    # === ツール実行処理 ===

    async def _handle_tool_execution_and_followup(
        self,
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
                repo_context_dict = self._convert_repository_context_to_dict(repository_context)
                
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
        followup_response = await self._generate_followup_response(
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
            
            content_len = len(llm_response.content) if llm_response.content is not None else 0
            logger.info(f"Followup response generated: {content_len} characters")
        else:
            logger.warning("Followup response generation failed or returned empty content")

    def _convert_repository_context_to_dict(
        self, repository_context: Optional["RepositoryContext"]
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

    async def _generate_followup_response(
        self,
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
            tool_results_summary = self._build_tool_results_summary(tool_results)
            
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
            
            logger.info(f"Followup response generated successfully: {len(followup_response.content) if followup_response.content else 0} characters")
            return followup_response
            
        except Exception as e:
            logger.error(f"Error generating followup response: {str(e)}")
            return None

    def _build_tool_results_summary(self, tool_results: List[Dict[str, Any]]) -> List[str]:
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
                                import json
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

    # === ユーティリティメソッド ===

    def build_conversation_messages(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        system_prompt: Optional[str] = None,
    ) -> List[MessageItem]:
        """
        標準フォーマットで会話メッセージを構築
        
        全プロバイダーで共通だが、最終フォーマットは各プロバイダーで変換される。
        """
        messages = []

        # システムプロンプト追加
        if system_prompt:
            messages.append(MessageItem(role=MessageRole.SYSTEM, content=system_prompt))

        # 会話履歴追加
        if conversation_history:
            messages.extend(conversation_history)

        # 現在のプロンプト追加（空でない場合のみ）
        if prompt.strip():
            messages.append(MessageItem(role=MessageRole.USER, content=prompt))

        return messages

    def _build_updated_conversation_history(
        self, 
        original_history: Optional[List[MessageItem]], 
        user_prompt: str, 
        assistant_response: Optional[str]
    ) -> List[MessageItem]:
        """Build updated conversation history including current exchange"""
        from doc_ai_helper_backend.models.llm import MessageItem, MessageRole
        
        # Start with original history or empty list
        updated_history = original_history.copy() if original_history else []
        
        # Add current user message
        updated_history.append(MessageItem(
            role=MessageRole.USER,
            content=user_prompt
        ))
        
        # Add current assistant response if available
        if assistant_response:
            updated_history.append(MessageItem(
                role=MessageRole.ASSISTANT,
                content=assistant_response
            ))
        
        return updated_history

    def _set_conversation_optimization_info(
        self, llm_response: LLMResponse, conversation_history: Optional[List[MessageItem]]
    ):
        """Set conversation history optimization information"""
        if conversation_history:
            optimized_history, optimization_info = optimize_conversation_history(
                conversation_history, max_tokens=4000
            )
            llm_response.optimized_conversation_history = optimized_history
            llm_response.history_optimization_info = optimization_info
        else:
            llm_response.optimized_conversation_history = []
            llm_response.history_optimization_info = {
                "was_optimized": False,
                "reason": "No conversation history provided",
            }

    def _generate_cache_key(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
    ) -> str:
        """クエリ用のキャッシュキーを生成"""
        key_data = {
            "prompt": prompt,
            "conversation_history": (
                [msg.model_dump() for msg in conversation_history]
                if conversation_history
                else None
            ),
            "options": options,
            "repository_context": (
                repository_context.model_dump() if repository_context else None
            ),
            "document_metadata": (
                document_metadata.model_dump() if document_metadata else None
            ),
            "document_content": document_content,
        }

        key_string = str(sorted(key_data.items()))
        return hashlib.md5(key_string.encode()).hexdigest()

    async def _retrieve_document_content(
        self, 
        repository_context: "RepositoryContext"
    ) -> tuple[Optional[str], Optional["DocumentMetadata"]]:
        """
        DocumentServiceを使用してドキュメント内容を取得
        
        Args:
            repository_context: リポジトリコンテキスト
            
        Returns:
            tuple: (document_content, document_metadata)
        """
        if not repository_context or not repository_context.current_path:
            logger.warning("Repository context or current_path is missing for document retrieval")
            return None, None
            
        try:
            # DocumentServiceが設定されていない場合は初期化
            if not self.document_service:
                from doc_ai_helper_backend.services.document import DocumentService
                self.document_service = DocumentService()
                logger.info("DocumentService initialized for document retrieval")
            
            # ドキュメント取得
            document_response = await self.document_service.get_document(
                service=repository_context.service,
                owner=repository_context.owner,
                repo=repository_context.repo,
                path=repository_context.current_path,
                ref=repository_context.ref or "main",
                transform_links=True,
            )
            
            logger.info(f"Document content retrieved: {len(document_response.content.content)} characters")
            return document_response.content.content, document_response.metadata
            
        except Exception as e:
            logger.warning(f"Failed to retrieve document content: {e}")
            return None, None


# 後方互換性のためのエイリアス
QueryManager = LLMOrchestrator
QueryOrchestrator = LLMOrchestrator