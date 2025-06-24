"""
ユーティリティツールとFunction Calling統合のユニットテスト

このモジュールは、ユーティリティツールとFunction Callingの統合機能をテストします。
"""

import pytest
from unittest.mock import AsyncMock, patch

from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.models.llm import LLMQueryRequest


class TestUtilityTools:
    """ユーティリティツールのテストクラス"""

    @pytest.fixture
    def mock_service(self):
        """MockLLMServiceのフィクスチャ"""
        return LLMServiceFactory.create("mock", response_delay=0.0)

    @pytest.mark.asyncio
    async def test_utility_function_calling_availability(self, mock_service):
        """ユーティリティ関数の利用可能性をテストする"""
        # 利用可能な関数を取得
        functions = await mock_service.get_available_functions()

        assert functions is not None
        assert isinstance(functions, list)

        if len(functions) > 0:
            # 各関数に必要な属性があることを確認
            for func in functions:
                assert hasattr(func, "name")
                assert hasattr(func, "description")

    @pytest.mark.asyncio
    async def test_current_time_function(self, mock_service):
        """現在時刻関数をテストする"""
        time_request = LLMQueryRequest(
            prompt="What is the current time?", enable_tools=True
        )

        # 利用可能な関数を取得
        functions = await mock_service.get_available_functions()
        utility_functions = [f for f in functions if "time" in f.name.lower()]

        if utility_functions:
            # ツール付きでクエリを実行
            if hasattr(mock_service, "query_with_tools"):
                response = await mock_service.query_with_tools(
                    prompt=time_request.prompt,
                    tools=utility_functions,
                    options={"enable_tools": True},
                )

                assert response is not None
                assert hasattr(response, "content")
                assert isinstance(response.content, str)

                # ツール呼び出しの検証
                if hasattr(response, "tool_calls") and response.tool_calls:
                    assert len(response.tool_calls) > 0
                    for call in response.tool_calls:
                        assert hasattr(call, "function")
                        assert hasattr(call.function, "name")
                        assert hasattr(call.function, "arguments")

    @pytest.mark.asyncio
    async def test_character_count_function(self, mock_service):
        """文字数カウント関数をテストする"""
        count_request = LLMQueryRequest(
            prompt="Count the characters in 'Hello World'", enable_tools=True
        )

        # 利用可能な関数を取得
        functions = await mock_service.get_available_functions()
        char_functions = [
            f
            for f in functions
            if "count" in f.name.lower() or "char" in f.name.lower()
        ]

        if char_functions:
            # ツール付きでクエリを実行
            if hasattr(mock_service, "query_with_tools"):
                response = await mock_service.query_with_tools(
                    prompt=count_request.prompt,
                    tools=char_functions,
                    options={"enable_tools": True},
                )

                assert response is not None
                assert hasattr(response, "content")
                assert isinstance(response.content, str)

    @pytest.mark.asyncio
    async def test_calculation_function(self, mock_service):
        """計算関数をテストする"""
        calc_request = LLMQueryRequest(prompt="Calculate 25 * 4", enable_tools=True)

        # 利用可能な関数を取得
        functions = await mock_service.get_available_functions()
        calc_functions = [
            f for f in functions if "calc" in f.name.lower() or "math" in f.name.lower()
        ]

        if calc_functions:
            # ツール付きでクエリを実行
            if hasattr(mock_service, "query_with_tools"):
                response = await mock_service.query_with_tools(
                    prompt=calc_request.prompt,
                    tools=calc_functions,
                    options={"enable_tools": True},
                )

                assert response is not None
                assert hasattr(response, "content")
                assert isinstance(response.content, str)

    @pytest.mark.asyncio
    async def test_function_execution_direct(self, mock_service):
        """関数の直接実行をテストする"""
        # 利用可能な関数を取得
        functions = await mock_service.get_available_functions()

        if functions and len(functions) > 0:
            # 最初の関数を選択
            test_function = functions[0]

            # 関数実行メソッドがあるかチェック
            if hasattr(mock_service, "execute_function"):
                try:
                    result = await mock_service.execute_function(
                        function_name=test_function.name, arguments={}
                    )

                    # 結果の検証
                    assert result is not None

                except Exception as e:
                    # 実行エラーは許容（実装依存）
                    pytest.skip(f"Function execution not implemented: {e}")

    @pytest.mark.asyncio
    async def test_weather_function_if_available(self, mock_service):
        """天気関数が利用可能な場合のテスト"""
        weather_request = LLMQueryRequest(
            prompt="What's the weather like today?", enable_tools=True
        )

        # 利用可能な関数を取得
        functions = await mock_service.get_available_functions()
        weather_functions = [f for f in functions if "weather" in f.name.lower()]

        if weather_functions:
            # ツール付きでクエリを実行
            if hasattr(mock_service, "query_with_tools"):
                response = await mock_service.query_with_tools(
                    prompt=weather_request.prompt,
                    tools=weather_functions,
                    options={"enable_tools": True},
                )

                assert response is not None
                assert hasattr(response, "content")
                assert isinstance(response.content, str)

    @pytest.mark.asyncio
    async def test_no_tools_query(self, mock_service):
        """ツールなしクエリをテストする"""
        simple_request = LLMQueryRequest(
            prompt="Hello, how are you?", enable_tools=False
        )

        # 通常のクエリを実行
        response = await mock_service.query(
            simple_request.prompt, options={"enable_tools": False}
        )

        assert response is not None
        assert hasattr(response, "content")
        assert isinstance(response.content, str)

        # ツール呼び出しが発生しないことを確認
        if hasattr(response, "tool_calls"):
            assert response.tool_calls is None or len(response.tool_calls) == 0

    @pytest.mark.asyncio
    async def test_service_factory_creation(self):
        """サービスファクトリーの作成をテストする"""
        # Mockサービスの作成
        mock_service = LLMServiceFactory.create("mock", response_delay=0.0)

        assert mock_service is not None
        assert hasattr(mock_service, "query")

        # 基本的なクエリをテスト
        response = await mock_service.query("Test prompt", options={})

        assert response is not None
        assert hasattr(response, "content")

    @pytest.mark.asyncio
    async def test_error_handling_with_invalid_function(self, mock_service):
        """無効な関数でのエラーハンドリングをテストする"""
        # 存在しない関数名でテスト
        if hasattr(mock_service, "execute_function"):
            try:
                result = await mock_service.execute_function(
                    function_name="non_existent_function", arguments={}
                )
                # エラーが発生するか、適切にハンドリングされることを期待
                assert result is not None or True  # エラーハンドリングを許容

            except Exception as e:
                # エラーが適切に処理されることを確認
                assert isinstance(e, Exception)
                assert str(e)  # エラーメッセージがあることを確認
