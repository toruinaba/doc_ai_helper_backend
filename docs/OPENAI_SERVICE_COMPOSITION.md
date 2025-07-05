# OpenAI LLM Service Composition Architecture

## 概要

OpenAI LLMサービスは、マルチプル継承の問題を解決するためにComposition（構成）パターンを使用してリファクタリングされました。

## アーキテクチャ構成

### 主要コンポーネント

#### 1. LLMServiceBase (`base.py`)
- 抽象基底クラス（Composition-based アーキテクチャ）
- すべてのLLMサービスが実装すべきインターフェースを定義
- 最小限の抽象メソッドのみ含む（プロバイダー固有の実装）

#### 2. LLMServiceCommon (`common.py`)
- 共通機能の実装
- テンプレート管理、キャッシュ機能、システムプロンプト構築など
- 複数のLLMサービスで共有されるロジック

#### 3. OpenAIService (`openai_service.py`)
- OpenAI固有の実装
- LLMServiceBaseを継承
- LLMServiceCommonのインスタンスを内部に保持（コンポジション）
- 共通機能は_commonインスタンスに委譲

## 利点

### 1. マルチプル継承の回避
- 複雑な継承階層を避け、単純な構成パターンを使用
- 依存関係が明確で理解しやすい

### 2. テスタビリティの向上
- 各コンポーネントを独立してテスト可能
- モック化が容易

### 3. 拡張性
- 新しいLLMプロバイダーを簡単に追加可能
- 共通機能の再利用が容易

### 4. 保守性
- 責任の分離が明確
- バグの特定と修正が容易

## 使用例

```python
from doc_ai_helper_backend.services.llm import OpenAIService

# サービスインスタンスの作成
service = OpenAIService(
    api_key="your-api-key",
    default_model="gpt-4",
    base_url="https://api.openai.com/v1"  # オプション
)

# 基本的なクエリ
response = await service.query("Hello, world!")

# ストリーミングクエリ
async for chunk in service.stream_query("Tell me a story"):
    print(chunk, end="")
```

## コンポジションパターンの実装

```python
class OpenAIService(LLMServiceBase):
    """OpenAI LLM service using composition pattern."""
    
    def __init__(self, api_key: str, **kwargs):
        # 共通機能をコンポジションで組み込み
        self._common = LLMServiceCommon()
        
        # OpenAI固有の初期化
        self.client = OpenAI(api_key=api_key)
        # ...
    
    async def query(self, prompt: str, options: Optional[Dict[str, Any]] = None) -> LLMResponse:
        # 共通機能への委譲
        formatted_prompt = self._common.format_prompt(prompt, options)
        
        # OpenAI固有の処理
        # ...
    
    @property
    def cache_service(self):
        """キャッシュサービスへのアクセス"""
        return self._common.cache_service
    
    @property 
    def template_manager(self):
        """テンプレートマネージャーへのアクセス"""
        return self._common.template_manager
```

## テスト戦略

### アクティブテスト
- `tests/unit/services/llm/test_openai_service.py`: 新しいComposition-basedの実装をテスト

### レガシーテスト（スキップ）
- `tests/unit/services/llm/legacy/`: 古いモジュラーアーキテクチャのテスト
- pytest.mark.skipマーカーで明示的にスキップ
- 開発者への説明付きREADME.md

## マイグレーション

### 完了済み
- ✅ LLMServiceCommonの実装
- ✅ 新しいOpenAIServiceの実装
- ✅ テストの移行とレガシーテストのスキップ化
- ✅ 重複ファイルの削除（openai_service_composition.py）
- ✅ ドキュメントの更新

### 今後の計画
- 他のLLMプロバイダー（Anthropic等）も同様のパターンで実装
- レガシーファイルの段階的な削除

## 推奨事項

1. **新機能の開発**: 必ずComposition-basedアーキテクチャを使用
2. **テスト**: `test_openai_service.py`のテストパターンに従う
3. **レガシーコード**: 緊急時以外は変更しない
4. **ドキュメント**: 変更時はこの文書も更新

## 関連ファイル

- `doc_ai_helper_backend/services/llm/openai_service.py` - メインの実装
- `doc_ai_helper_backend/services/llm/base.py` - 抽象基底クラス（Composition-based）
- `doc_ai_helper_backend/services/llm/common.py` - 共通機能
- `doc_ai_helper_backend/services/llm/legacy/base_legacy.py` - レガシー抽象基底クラス
- `tests/unit/services/llm/test_openai_service.py` - アクティブテスト
- `tests/unit/services/llm/legacy/README.md` - レガシーテストの説明
