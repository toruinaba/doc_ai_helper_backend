# LLMサービス層リファクタリング実装計画

## 概要

DEVELOPMENT_PLAN.mdに基づき、LLMサービス層をmixin-based継承から純粋な委譲（composition）パターンに移行します。

## 現在の構造分析

### 現在のディレクトリ構造
```
services/llm/
├── base.py                    # 現在の基底サービス
├── openai_service.py          # OpenAIサービス実装
├── mock_service.py            # モックサービス実装  
├── factory.py                 # ファクトリー
├── common.py                  # 共通機能
├── utils/                     # ユーティリティ（移動対象）
│   ├── caching.py
│   ├── functions.py
│   ├── helpers.py
│   ├── messaging.py
│   ├── mixins.py              # 削除対象
│   ├── query_orchestrator.py
│   ├── response_builder.py
│   ├── streaming.py
│   ├── templating.py
│   └── tokens.py
├── legacy/                    # 削除対象
└── mock/                      # 再構成対象
    ├── constants.py
    ├── response_generator.py
    └── test_utilities.py
```

### 目標構造
```
services/llm/
├── base.py                    # 純粋委譲パターンの基底サービス
├── openai_service.py          # リファクタリング後OpenAIサービス
├── mock_service.py            # リファクタリング後モックサービス
├── factory.py                 # 更新されたファクトリー
├── components/                # 新しいコンポーネントディレクトリ
│   ├── cache.py              # utils/caching.py から移動
│   ├── templates.py          # utils/templating.py から移動
│   ├── messaging.py          # utils/messaging.py から移動
│   ├── functions.py          # utils/functions.py から移動
│   ├── response_builder.py   # utils/response_builder.py から移動
│   ├── tokens.py             # utils/tokens.py から移動
│   ├── streaming_utils.py    # utils/streaming.py から移動（リネーム）
│   └── query_manager.py      # utils/query_orchestrator.py から移動（リネーム）
├── mock/                     # 再構成されたモックディレクトリ
│   ├── generator.py          # response_generator.py から移動（リネーム）
│   ├── helpers.py            # test_utilities.py から移動（リネーム）
│   └── constants.py          # そのまま
└── templates/
    └── prompts.json
```

## 実装フェーズ

### Phase 1: ディレクトリ構造準備 (Day 1)

#### 1.1 新しいディレクトリ作成
- `components/` ディレクトリ作成
- 各ディレクトリに `__init__.py` 作成

#### 1.2 現在のテスト実行状況確認
- 既存テストスイートの実行
- ベースライン確立

### Phase 2: コンポーネントファイル移動 (Day 1-2)

#### 2.1 Utilsファイルの移動とリネーム
- `utils/caching.py` → `components/cache.py`
- `utils/templating.py` → `components/templates.py`
- `utils/messaging.py` → `components/messaging.py`
- `utils/functions.py` → `components/functions.py`
- `utils/response_builder.py` → `components/response_builder.py`
- `utils/tokens.py` → `components/tokens.py`
- `utils/streaming.py` → `components/streaming_utils.py`
- `utils/query_orchestrator.py` → `components/query_manager.py`

#### 2.2 Mockファイルの再構成
- `mock/response_generator.py` → `mock/generator.py`
- `mock/test_utilities.py` → `mock/helpers.py`

#### 2.3 各移動後ファイルの内容調整
- インポート文の更新
- クラス名・関数名の必要に応じた調整

### Phase 3: 委譲パターン実装 (Day 2-3)

#### 3.1 新しい基底クラスの実装
- `base.py` を純粋な委譲パターンに変更
- mixin継承の完全除去
- コンポーネントの直接インスタンス化

#### 3.2 OpenAIServiceの更新
- `openai_service.py` を新しい基底クラスに適合
- 委譲パターンの適用

#### 3.3 MockServiceの更新
- `mock_service.py` を新しい基底クラスに適合
- 委譲パターンの適用

### Phase 4: インポート文とテスト更新 (Day 3-4)

#### 4.1 全ファイルのインポート文更新
- APIエンドポイント
- 他のサービス
- テストファイル

#### 4.2 テストスイートの修正
- 段階的なテスト修正
- 基本機能から高度機能の順序

#### 4.3 Factory更新
- 新しい構造に対応したファクトリーの更新

### Phase 5: クリーンアップ (Day 4-5)

#### 5.1 不要ファイル削除
- `utils/` ディレクトリ削除
- `legacy/` ディレクトリ削除
- `common.py` 削除（必要に応じて）

#### 5.2 最終テスト実行
- 全テストスイートの実行
- パフォーマンステスト
- 統合テスト

## 詳細実装計画

### Phase 1: ディレクトリ構造準備

```bash
# 新しいディレクトリ作成
mkdir -p doc_ai_helper_backend/services/llm/components
```

#### components/__init__.py の作成
```python
"""LLMサービスの機能コンポーネント"""

from .cache import LLMCacheService
from .templates import PromptTemplateManager
from .messaging import MessageBuilder
from .functions import FunctionService
from .response_builder import ResponseBuilder
from .tokens import TokenCounter
from .streaming_utils import StreamingUtils
from .query_manager import QueryManager

__all__ = [
    'LLMCacheService',
    'PromptTemplateManager', 
    'MessageBuilder',
    'FunctionService',
    'ResponseBuilder',
    'TokenCounter',
    'StreamingUtils',
    'QueryManager'
]
```

### Phase 2: ファイル移動戦略

#### 移動手順
1. **ファイルコピー**: 元ファイルをコピーして新しい場所に配置
2. **内容調整**: インポート文とクラス名の調整
3. **段階的テスト**: 各移動後にテストを実行
4. **元ファイル削除**: 全て正常動作確認後に削除

#### 例: caching.py → cache.py
```python
# components/cache.py
"""LLMレスポンスキャッシュサービス"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

class LLMCacheService:
    """LLMレスポンスのキャッシュサービス"""
    
    def __init__(self, ttl_minutes: int = 60):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._ttl = timedelta(minutes=ttl_minutes)
    
    # 既存メソッドをそのまま移動
```

### Phase 3: 新しい基底クラス実装

#### 委譲パターンの基底クラス
```python
# base.py (リファクタリング後)
"""Pure delegation pattern base service"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
from .components import (
    LLMCacheService, PromptTemplateManager, MessageBuilder,
    FunctionService, ResponseBuilder, TokenCounter,
    StreamingUtils, QueryManager
)

class LLMServiceBase(ABC):
    """LLMサービスの基底クラス（純粋委譲パターン）"""
    
    def __init__(self, api_key: str, default_model: str, 
                 base_url: Optional[str] = None, **kwargs):
        # Configuration
        self._api_key = api_key
        self._default_model = default_model
        self._base_url = base_url
        self._default_options = kwargs
        
        # Component composition (no inheritance)
        self.cache_service = LLMCacheService()
        self.template_manager = PromptTemplateManager()
        self.message_builder = MessageBuilder()
        self.function_service = FunctionService()
        self.response_builder = ResponseBuilder()
        self.token_counter = TokenCounter()
        self.streaming_utils = StreamingUtils()
        self.query_manager = QueryManager(
            cache_service=self.cache_service,
            template_manager=self.template_manager,
            message_builder=self.message_builder
        )
    
    # 共通インターフェース（委譲）
    async def query(self, prompt: str, **kwargs) -> 'LLMResponse':
        """LLMへのクエリ実行（委譲）"""
        return await self.query_manager.orchestrate_query(
            service=self, prompt=prompt, **kwargs
        )
    
    async def stream_query(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """ストリーミングクエリ実行（委譲）"""
        async for chunk in self.query_manager.orchestrate_streaming_query(
            service=self, prompt=prompt, **kwargs
        ):
            yield chunk
    
    # プロバイダー固有の抽象メソッド
    @abstractmethod
    async def _call_provider_api(self, options: Dict[str, Any]):
        """プロバイダー固有のAPI呼び出し"""
        pass
    
    @abstractmethod  
    async def _stream_provider_api(self, options: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """プロバイダー固有のストリーミングAPI呼び出し"""
        pass
```

### Phase 4: テスト更新戦略

#### 段階的テスト修正
```python
# 1. 基本インポートテスト
def test_imports():
    """新しい構造でのインポートテスト"""
    from doc_ai_helper_backend.services.llm.components import (
        LLMCacheService, PromptTemplateManager
    )
    
# 2. 基本機能テスト
def test_basic_functionality():
    """基本機能の動作確認"""
    
# 3. 統合テスト
def test_integration():
    """全体統合テスト"""
```

## リスク管理

### 主要リスク
1. **破壊的変更**: 段階的実装で最小化
2. **テスト失敗**: 各フェーズでテスト実行
3. **パフォーマンス低下**: ベンチマーク比較
4. **インポートエラー**: 自動検索・置換ツール使用

### 緊急時対応
- **ロールバック計画**: Gitブランチでの作業
- **ホットフィックス**: 最小限の修正で動作復旧
- **段階的復旧**: フェーズ単位での復旧

## 成功指標

### 定量的指標
- [ ] 全テスト通過率 100%
- [ ] コードカバレッジ維持（現在の95%以上）
- [ ] パフォーマンス低下なし（±5%以内）

### 定性的指標
- [ ] mixin継承完全除去
- [ ] ディレクトリ階層1階層以下
- [ ] コンポーネント責任明確化
- [ ] 可読性・保守性向上

## 実装スケジュール

| フェーズ | 期間 | 主要タスク | 成果物 |
|---------|------|-----------|--------|
| Phase 1 | Day 1 | ディレクトリ準備・テスト確認 | 新構造準備完了 |
| Phase 2 | Day 1-2 | ファイル移動・内容調整 | コンポーネント移動完了 |
| Phase 3 | Day 2-3 | 委譲パターン実装 | 新アーキテクチャ完了 |
| Phase 4 | Day 3-4 | インポート・テスト更新 | 全機能動作確認 |
| Phase 5 | Day 4-5 | クリーンアップ・最終テスト | リファクタリング完了 |

## 次のステップ

1. **Phase 1実行**: ディレクトリ構造準備の開始
2. **ベースライン確立**: 現在のテスト実行状況記録
3. **実装開始**: 段階的な移行作業開始

このリファクタリングにより、LLMサービス層がより保守しやすく、拡張しやすい構造になります。
