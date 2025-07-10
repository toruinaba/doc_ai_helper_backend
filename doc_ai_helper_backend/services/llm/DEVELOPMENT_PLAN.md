# LLM Service Layer Refactoring Plan

## 目的

LLMサービス層をmixin-based継承から純粋な委譲（composition）パターンに移行し、コードベースの明確性と保守性を向上させる。

## 現在の問題点

1. **複雑なmixin継承**: 複数のmixinクラスによる継承チェーンが複雑
2. **深い階層**: `utils/`、`core/`、`mock/`、`legacy/`などの深いディレクトリ構造
3. **責任の重複**: `delegation.py`、`common.py`、各コンポーネントの役割が重複
4. **冗長な構造**: `services/llm/services/`のような冗長なディレクトリ名

## 新しいディレクトリ構造

```
services/llm/
├── __init__.py
├── factory.py
├── DEVELOPMENT_PLAN.md           # このファイル
│
# === サービス実装（直接配置） ===
├── base.py                       # 基底サービス（直接委譲パターン）
├── openai_service.py             # OpenAIサービス
├── mock_service.py               # モックサービス
│
# === 機能コンポーネント ===
├── components/
│   ├── __init__.py
│   ├── cache.py                  # キャッシュサービス
│   ├── templates.py              # テンプレート管理
│   ├── messaging.py              # メッセージ処理
│   ├── functions.py              # Function Calling
│   ├── response_builder.py       # レスポンス構築
│   ├── tokens.py                 # トークン計算
│   ├── streaming_utils.py        # ストリーミングユーティリティ
│   └── query_manager.py          # クエリ管理（query_orchestrator改名）
│
# === モック・テスト支援 ===
├── mock/
│   ├── __init__.py
│   ├── generator.py              # モック応答生成
│   ├── helpers.py                # テストヘルパー
│   └── constants.py              # テスト定数
│
└── templates/
    └── prompts.json
```

## ファイル移行計画

### Phase 1: ディレクトリ構造の準備

1. **新しいディレクトリ作成**
   - `components/`
   - `mock/` (既存のmockディレクトリを再構成)

2. **削除予定ディレクトリの特定**
   - `utils/` (全ファイルを移動後削除)
   - `legacy/` (アーカイブまたは削除)

### Phase 2: ファイル移動とリネーム

#### サービス実装（llm直下に移動）
- `base.py` → 既存位置のまま（内容をリファクタリング）
- `openai_service.py` → 既存位置のまま（内容をリファクタリング）
- `mock_service.py` → 既存位置のまま（内容をリファクタリング）

#### コンポーネント移動
- `utils/caching.py` → `components/cache.py`
- `utils/templating.py` → `components/templates.py`
- `utils/functions.py` → `components/functions.py`
- `utils/response_builder.py` → `components/response_builder.py`
- `utils/tokens.py` → `components/tokens.py`
- `utils/streaming.py` → `components/streaming_utils.py`
- `utils/query_orchestrator.py` → `components/query_manager.py`
- `messaging.py` → `components/messaging.py`

#### モック関連統合
- `mock/response_generator.py` → `mock/generator.py`
- `mock/test_utilities.py` → `mock/helpers.py`
- `mock/constants.py` → `mock/constants.py` (既存位置)

### Phase 3: 委譲パターンの実装

#### 新しい基底クラス
```python
# base.py (リファクタリング後)
from abc import ABC, abstractmethod
from .components import (
    CacheService, TemplateService, FunctionService,
    ResponseBuilder, TokenCounter, StreamingUtils,
    QueryManager, MessageBuilder
)

class LLMServiceBase(ABC):
    def __init__(self, api_key: str, default_model: str, base_url: Optional[str] = None, **kwargs):
        # Direct composition - no mixins
        self.cache = CacheService()
        self.template_service = TemplateService()
        self.function_service = FunctionService()
        self.response_builder = ResponseBuilder()
        self.token_counter = TokenCounter()
        self.streaming_utils = StreamingUtils()
        self.query_manager = QueryManager()
        self.message_builder = MessageBuilder()
        
        # Store configuration directly
        self._api_key = api_key
        self._default_model = default_model
        self._base_url = base_url
        self._default_options = kwargs
        # 直接コンポーネントをインスタンス化（純粋な委譲）
        self.cache_service = LLMCacheService()
        self.template_manager = PromptTemplateManager()
        # ... その他のコンポーネント
        
        self.query_manager = QueryManager(
            cache_service=self.cache_service,
            system_prompt_builder=self.system_prompt_builder
        )
    
    # 共通インターフェース（コンポーネントに委譲）
    async def query(self, prompt: str, **kwargs) -> LLMResponse:
        return await self.query_manager.orchestrate_query(
            service=self, prompt=prompt, **kwargs
        )
    
    async def stream_query(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        async for chunk in self.query_manager.orchestrate_streaming_query(
            service=self, prompt=prompt, **kwargs
        ):
            yield chunk
    
    # プロバイダー固有の抽象メソッド
    @abstractmethod
    async def _call_provider_api(self, options: Dict[str, Any]):
        """各プロバイダー固有のAPI呼び出し実装"""
        pass
    
    @abstractmethod
    async def _stream_provider_api(self, options: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """各プロバイダー固有のストリーミングAPI呼び出し実装"""
        pass
```

### Phase 4: インポート文とテストの更新

1. **全ファイルのインポート文更新**
   - `from doc_ai_helper_backend.services.llm.utils.*` → `from doc_ai_helper_backend.services.llm.components.*`
   - 移動されたファイルへの参照を全て更新

2. **テストファイルの更新**
   - テストでのインポート文更新
   - モックオブジェクトのパス更新

3. **`__init__.py`ファイルの更新**
   - 各ディレクトリの`__init__.py`で適切なエクスポートを設定

## 実装の利点

### 1. **シンプルさ**
- 直接的な所有と委譲によりコードが理解しやすい
- 複雑な抽象化層が不要

### 2. **明確性**
- 各コンポーネントの責任が明確
- ファイルの役割が名前から理解しやすい

### 3. **保守性**
- 依存関係が追跡しやすい
- テストが書きやすい

### 4. **拡張性**
- 新しいプロバイダーの追加が容易
- コンポーネントの独立した拡張が可能

## 実装手順

1. **Phase 1**: ディレクトリ構造準備
2. **Phase 2**: ファイル移動（破壊的変更なし）
3. **Phase 3**: Mixin → Delegation変換
4. **Phase 4**: インポート文更新・テスト修正
5. **Phase 5**: 不要ファイル削除・クリーンアップ

## 注意事項

- **段階的実装**: 各フェーズで動作確認を行い、破壊的変更を最小限に抑制
- **テスト優先**: 各変更後にテストスイートを実行し、回帰を防止
- **後方互換性**: 可能な限り既存APIとの互換性を維持

## 成功指標

- [ ] 全テストが通過する
- [ ] mixin継承が完全に除去される
- [ ] ディレクトリ階層が1階層以下になる
- [ ] 各コンポーネントの責任が明確になる
- [ ] コードの可読性と保守性が向上する

### 実装成果

1. **Pure Composition Pattern導入**: mixin継承を完全に除去し、直接委譲パターンに移行
2. **フラットディレクトリ構造**: 1階層以下の明確な構造に整理
3. **コンポーネント責任分離**: 各機能コンポーネントの役割を明確化
4. **保守性向上**: 依存関係が追跡しやすく、テストが容易な構造
5. **拡張性向上**: 新しいプロバイダーやコンポーネントの追加が容易

### 新しいアーキテクチャ

```
services/llm/
├── base.py                       # 基底サービス（純粋な委譲）
├── openai_service.py             # OpenAIサービス実装
├── mock_service.py               # モックサービス実装
├── factory.py                    # サービスファクトリー
├── components/                   # 機能コンポーネント
│   ├── cache.py                  # キャッシュサービス
│   ├── templates.py              # テンプレート管理
│   ├── messaging.py              # メッセージ処理
│   ├── functions.py              # Function Calling
│   ├── response_builder.py       # レスポンス構築
│   ├── tokens.py                 # トークン計算
│   ├── streaming_utils.py        # ストリーミング
│   └── query_manager.py          # クエリ管理
├── mock/                         # モック・テスト支援
│   ├── generator.py              # モック応答生成
│   ├── helpers.py                # テストヘルパー
│   └── constants.py              # テスト定数
└── templates/                    # プロンプトテンプレート
    └── prompts.json
```


### 主要な修正タスク
1. **コアメソッド実装**: `QueryManager.prepare_query()`, `MockLLMService.format_prompt()` 等
2. **プロパティ追加**: `default_model`, backward compatibility layer
3. **メソッドシグネチャ統一**: `query()`, `stream_query()` の引数互換性
4. **テスト段階的修正**: 基本機能 → 高度機能の順序で修正
