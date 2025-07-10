"""
ストリーミングユーティリティ (Streaming Utilities)

LLMサービス向けのストリーミングレスポンス処理ユーティリティを提供します。
元ファイル: utils/streaming.py

このコンポーネントは純粋な委譲パターンで使用され、mixin継承は使用しません。

主要機能:
- ストリーミングレスポンスの処理
- チャンクベースのコンテンツ配信
- ストリームのバッファリング
"""

import asyncio
import logging
from typing import AsyncGenerator, Union, List

logger = logging.getLogger(__name__)


class StreamingUtils:
    """
    LLMサービスでのストリーミング操作を処理するユーティリティクラス

    異なるLLMサービス実装間で再利用可能な共通ストリーミング機能を提供します。
    """

    def __init__(self):
        """ストリーミングユーティリティの初期化"""
        self.logger = logger

    async def chunk_content(
        self,
        content: str,
        chunk_size: int = 15,
        delay_per_chunk: float = 0.1,
        total_delay: float = 0.0,
    ) -> AsyncGenerator[str, None]:
        """
        コンテンツをチャンクに分割し、遅延を設けて配信

        ストリーミングレスポンスのシミュレーションやコンテンツ配信レートの制御に便利です。

        Args:
            content: チャンク化するコンテンツ
            chunk_size: 各チャンクのサイズ（文字数）
            delay_per_chunk: チャンク間の遅延（秒）
            total_delay: 全チャンクに分散する総遅延

        Yields:
            str: コンテンツチャンク
        """
        if not content:
            return

        # total_delayが指定されている場合は動的な遅延を計算
        if total_delay > 0 and len(content) > 0:
            num_chunks = max(1, len(content) // chunk_size)
            delay_per_chunk = total_delay / num_chunks

        for i in range(0, len(content), chunk_size):
            chunk = content[i : i + chunk_size]

            if delay_per_chunk > 0:
                await asyncio.sleep(delay_per_chunk)

            yield chunk

        self.logger.debug(
            f"Completed chunking {len(content)} characters into {len(content) // chunk_size + 1} chunks"
        )

    async def buffer_stream(
        self,
        stream: AsyncGenerator[str, None],
        buffer_size: int = 100,
        flush_on_newline: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        ストリームをバッファリングし、バッファが満杯または改行時に配信

        小さな配信の数を減らすことでストリーミングパフォーマンスを向上させます。

        Args:
            stream: バッファリングする入力ストリーム
            buffer_size: フラッシュ前の最大バッファサイズ
            flush_on_newline: 改行文字でバッファをフラッシュするかどうか

        Yields:
            str: バッファリングされたコンテンツ
        """
        buffer = ""

        async for chunk in stream:
            buffer += chunk

            # バッファをフラッシュすべきかチェック
            should_flush = len(buffer) >= buffer_size or (
                flush_on_newline and "\n" in buffer
            )

            if should_flush:
                yield buffer
                buffer = ""

        # バッファに残っているコンテンツがあれば配信
        if buffer:
            yield buffer

    async def aggregate_stream(
        self,
        stream: AsyncGenerator[str, None],
        max_content_length: int = 50000,
    ) -> str:
        """
        ストリーム全体を集約して単一の文字列として返す

        Args:
            stream: 集約するストリーム
            max_content_length: 最大コンテンツ長（制限として）

        Returns:
            str: 集約されたコンテンツ

        Raises:
            ValueError: コンテンツが最大長を超えた場合
        """
        aggregated_content = ""

        async for chunk in stream:
            aggregated_content += chunk

            if len(aggregated_content) > max_content_length:
                raise ValueError(
                    f"Content length exceeded maximum: {max_content_length}"
                )

        return aggregated_content

    async def throttle_stream(
        self,
        stream: AsyncGenerator[str, None],
        max_chunks_per_second: float = 10.0,
    ) -> AsyncGenerator[str, None]:
        """
        ストリームをスロットリングして配信レートを制御

        Args:
            stream: スロットリングするストリーム
            max_chunks_per_second: 秒間の最大チャンク数

        Yields:
            str: スロットリングされたチャンク
        """
        if max_chunks_per_second <= 0:
            # スロットリングなし
            async for chunk in stream:
                yield chunk
            return

        interval = 1.0 / max_chunks_per_second
        last_yield_time = 0.0

        async for chunk in stream:
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - last_yield_time

            if time_since_last < interval:
                await asyncio.sleep(interval - time_since_last)

            yield chunk
            last_yield_time = asyncio.get_event_loop().time()

    async def filter_stream(
        self,
        stream: AsyncGenerator[str, None],
        filter_func: callable = None,
    ) -> AsyncGenerator[str, None]:
        """
        ストリームにフィルタを適用

        Args:
            stream: フィルタリングするストリーム
            filter_func: フィルタ関数（文字列を受け取って bool を返す）

        Yields:
            str: フィルタリングされたチャンク
        """
        if filter_func is None:
            # フィルタなし
            async for chunk in stream:
                yield chunk
            return

        async for chunk in stream:
            if filter_func(chunk):
                yield chunk

    async def transform_stream(
        self,
        stream: AsyncGenerator[str, None],
        transform_func: callable = None,
    ) -> AsyncGenerator[str, None]:
        """
        ストリームに変換を適用

        Args:
            stream: 変換するストリーム
            transform_func: 変換関数（文字列を受け取って文字列を返す）

        Yields:
            str: 変換されたチャンク
        """
        if transform_func is None:
            # 変換なし
            async for chunk in stream:
                yield chunk
            return

        async for chunk in stream:
            try:
                transformed_chunk = transform_func(chunk)
                if transformed_chunk:  # 空でない場合のみ配信
                    yield transformed_chunk
            except Exception as e:
                self.logger.warning(f"Error transforming chunk: {e}")
                # エラーの場合は元のチャンクを配信
                yield chunk

    @staticmethod
    async def create_mock_stream(
        content: str,
        chunk_size: int = 10,
        delay: float = 0.05,
    ) -> AsyncGenerator[str, None]:
        """
        モックストリームを作成（テスト用）

        Args:
            content: ストリーミングするコンテンツ
            chunk_size: チャンクサイズ
            delay: チャンク間の遅延

        Yields:
            str: コンテンツチャンク
        """
        utils = StreamingUtils()
        async for chunk in utils.chunk_content(content, chunk_size, delay):
            yield chunk

    async def join_streams(
        self, *streams: AsyncGenerator[str, None]
    ) -> AsyncGenerator[str, None]:
        """
        複数のストリームを結合

        Args:
            streams: 結合するストリーム

        Yields:
            str: 結合されたチャンク
        """
        for stream in streams:
            async for chunk in stream:
                yield chunk
