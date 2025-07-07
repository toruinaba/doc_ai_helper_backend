"""
キャッシュサービス (Cache Service)

LLMレスポンスのインメモリキャッシュを提供します。
元ファイル: utils/caching.py

このコンポーネントは純粋な委譲パターンで使用され、mixin継承は使用しません。
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional, Tuple

from doc_ai_helper_backend.models.llm import LLMResponse
from doc_ai_helper_backend.core.config import settings


class LLMCacheService:
    """
    LLMレスポンスのキャッシュサービス

    LLMレスポンスをキャッシュしてAPI呼び出しを削減し、パフォーマンスを向上させます。
    """

    def __init__(self, ttl_seconds: int = None):
        """
        キャッシュサービスの初期化

        Args:
            ttl_seconds: キャッシュのTTL（秒）、デフォルトは設定値を使用
        """
        self._cache: Dict[str, Tuple[LLMResponse, float]] = {}
        self.ttl_seconds = ttl_seconds or settings.llm_cache_ttl

    def generate_key(self, prompt: str, options: Dict[str, Any]) -> str:
        """
        プロンプトとオプションからキャッシュキーを生成

        Args:
            prompt: プロンプトテキスト
            options: クエリオプション

        Returns:
            str: キャッシュ用のハッシュキー
        """
        # 入力の決定論的な表現を作成
        key_data = {
            "prompt": prompt,
            "options": self._serialize_options(options),
        }

        # JSONに変換してハッシュ化
        serialized = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()

    def _serialize_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """
        キャッシュキー生成用にオプションをシリアライズ

        Args:
            options: クエリオプション

        Returns:
            Dict: シリアライズ可能な値を持つ辞書
        """
        serialized = {}
        for k, v in sorted(options.items()):
            if k == "stream":
                continue  # ストリームオプションはキャッシュでは無視
            elif k == "functions" and isinstance(v, list):
                # 関数定義をシリアライズ
                serialized[k] = [
                    {
                        "name": func.name if hasattr(func, "name") else str(func),
                        "description": (
                            func.description if hasattr(func, "description") else ""
                        ),
                        "parameters": (
                            func.parameters if hasattr(func, "parameters") else {}
                        ),
                    }
                    for func in v
                ]
            elif hasattr(v, "dict"):
                # Pydanticモデル
                serialized[k] = v.dict()
            elif hasattr(v, "__dict__"):
                # 属性を持つ通常のオブジェクト
                serialized[k] = str(v)
            else:
                serialized[k] = v
        return serialized

    def get(self, key: str) -> Optional[LLMResponse]:
        """
        キャッシュからアイテムを取得

        Args:
            key: キャッシュキー

        Returns:
            Optional[LLMResponse]: キャッシュされたレスポンス、見つからないか期限切れの場合はNone
        """
        if key not in self._cache:
            return None

        response, expiry_time = self._cache[key]

        # 期限切れチェック
        if time.time() > expiry_time:
            del self._cache[key]
            return None

        return response

    def set(self, key: str, response: LLMResponse) -> None:
        """
        キャッシュにアイテムを保存

        Args:
            key: キャッシュキー
            response: キャッシュするLLMレスポンス
        """
        expiry_time = time.time() + self.ttl_seconds
        self._cache[key] = (response, expiry_time)

    def clear(self) -> None:
        """
        キャッシュの全アイテムをクリア
        """
        self._cache.clear()

    def clear_expired(self) -> int:
        """
        期限切れアイテムをキャッシュからクリア

        Returns:
            int: クリアされたアイテム数
        """
        now = time.time()
        expired_keys = [
            key for key, (_, expiry_time) in self._cache.items() if now > expiry_time
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def size(self) -> int:
        """
        現在のキャッシュサイズを取得

        Returns:
            int: キャッシュされているアイテム数
        """
        return len(self._cache)

    def stats(self) -> Dict[str, Any]:
        """
        キャッシュ統計情報を取得

        Returns:
            Dict: キャッシュ統計情報
        """
        now = time.time()
        expired_count = sum(
            1 for _, expiry_time in self._cache.values() if now > expiry_time
        )

        return {
            "total_items": len(self._cache),
            "expired_items": expired_count,
            "active_items": len(self._cache) - expired_count,
            "ttl_seconds": self.ttl_seconds,
        }
