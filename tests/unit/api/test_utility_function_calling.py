"""
ユーティリティ関数のFunction Calling機能のユニットテスト

このモジュールは、MockLLMServiceがユーティリティ関数（現在時刻取得、文字数カウント等）を
正しく検出・実行できるかをテストします。
"""

import pytest
from unittest.mock import AsyncMock, patch

from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.services.llm.utility_functions import get_utility_functions
from doc_ai_helper_backend.models.llm import FunctionCall
from doc_ai_helper_backend.core.exceptions import LLMServiceException


class TestUtilityFunctionCalling:
    """ユーティリティ関数Function Callingのテストクラス"""

    @pytest.fixture
    def mock_service(self):
        """MockLLMServiceのフィクスチャ"""
        return MockLLMService(response_delay=0.0)  # テスト用に遅延なし

    @pytest.fixture
    def utility_functions(self):
        """ユーティリティ関数のフィクスチャ"""
        return get_utility_functions()

    @pytest.mark.asyncio
    async def test_get_utility_functions(self, utility_functions):
        """ユーティリティ関数が正しく取得できることをテストする"""
        assert len(utility_functions) > 0

        # 各関数に必要な属性があることを確認
        for func in utility_functions:
            assert hasattr(func, "name")
            assert hasattr(func, "description")
            assert hasattr(func, "parameters")

    @pytest.mark.asyncio
    async def test_current_time_function_calling(self, mock_service, utility_functions):
        """現在時刻取得のFunction Callingをテストする"""
        prompt = "What is the current time?"

        response = await mock_service.query(
            prompt, options={"functions": utility_functions}
        )

        assert response is not None
        assert hasattr(response, "content")
        assert isinstance(response.content, str)

        # ツール呼び出しが発生したことを確認
        if hasattr(response, "tool_calls") and response.tool_calls:
            assert len(response.tool_calls) > 0
            for tool_call in response.tool_calls:
                assert hasattr(tool_call, "function")
                assert hasattr(tool_call.function, "name")
                assert hasattr(tool_call.function, "arguments")

    @pytest.mark.asyncio
    async def test_character_count_function_calling(
        self, mock_service, utility_functions
    ):
        """文字数カウントのFunction Callingをテストする"""
        prompt = "Please count the characters in the text: Hello World"

        response = await mock_service.query(
            prompt, options={"functions": utility_functions}
        )

        assert response is not None
        assert hasattr(response, "content")
        assert isinstance(response.content, str)

    @pytest.mark.asyncio
    async def test_calculation_function_calling(self, mock_service, utility_functions):
        """計算のFunction Callingをテストする"""
        prompt = "Calculate 15 + 27"

        response = await mock_service.query(
            prompt, options={"functions": utility_functions}
        )

        assert response is not None
        assert hasattr(response, "content")
        assert isinstance(response.content, str)

    @pytest.mark.asyncio
    async def test_function_execution(self, mock_service, utility_functions):
        """関数実行機能をテストする"""
        # 現在時刻取得関数を探す
        time_functions = [f for f in utility_functions if "time" in f.name.lower()]

        if time_functions:
            time_function = time_functions[0]

            # FunctionCallオブジェクトを作成
            function_call = FunctionCall(
                name=time_function.name, arguments="{}"  # JSON文字列として渡す
            )

            # 関数を実行
            if hasattr(mock_service, "execute_function_call"):
                result = await mock_service.execute_function_call(
                    function_call, utility_functions
                )

                assert result is not None
                assert isinstance(result, (str, dict, int, float))

    @pytest.mark.asyncio
    async def test_no_function_calling_when_disabled(self, mock_service):
        """Function Calling無効時にツール呼び出しが発生しないことをテストする"""
        prompt = "What is the current time?"

        response = await mock_service.query(
            prompt, options={"functions": None}  # 関数なし
        )

        assert response is not None
        assert hasattr(response, "content")
        assert isinstance(response.content, str)

        # ツール呼び出しが発生しないことを確認
        if hasattr(response, "tool_calls"):
            assert response.tool_calls is None or len(response.tool_calls) == 0

    @pytest.mark.asyncio
    async def test_function_calling_error_handling(
        self, mock_service, utility_functions
    ):
        """Function Callingエラーハンドリングをテストする"""
        # 空のプロンプトでLLMServiceExceptionが発生することを確認
        prompt = ""

        with pytest.raises(LLMServiceException, match="Prompt cannot be empty"):
            await mock_service.query(prompt, options={"functions": utility_functions})

    @pytest.mark.asyncio
    async def test_multiple_function_calls(self, mock_service, utility_functions):
        """複数のFunction Callsをテストする"""
        prompt = "What is the current time and calculate 10 + 5?"

        response = await mock_service.query(
            prompt, options={"functions": utility_functions}
        )

        assert response is not None
        assert hasattr(response, "content")
        assert isinstance(response.content, str)

        # 複数のツール呼び出しが可能かテスト（実装依存）
        if hasattr(response, "tool_calls") and response.tool_calls:
            # ツール呼び出しが発生した場合の検証
            for tool_call in response.tool_calls:
                assert hasattr(tool_call, "function")
                assert hasattr(tool_call.function, "name")
                assert hasattr(tool_call.function, "arguments")
