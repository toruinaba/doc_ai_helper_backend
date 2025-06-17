# LLMサービス実装概要

このドキュメントは、2025年6月17日時点の`doc_ai_helper_backend`プロジェクトにおけるLLM（大規模言語モデル）サービス層の実装について概要をまとめたものです。

## 概要

LLMサービス層は、クリーンな抽象化レイヤーを通じて様々なLLMプロバイダー（OpenAI、Anthropicなど）と対話するための統一インターフェースを提供します。実装は関心事の明確な分離を持つモジュラー設計に従っています：

1. **抽象化**：プロバイダー選択のための基本インターフェースとファクトリーパターン
2. **キャッシュ**：API呼び出しを削減するためのLLMレスポンスキャッシュ
3. **コンテキスト管理**：標準化されたコンテキスト処理のためのModel Context Protocol（MCP）アダプター
4. **テンプレート**：プロンプトテンプレート管理システム
5. **API統合**：LLM機能を公開するFastAPIエンドポイント

## コンポーネント

### 1. ベースLLMサービス（`base.py`）

`LLMServiceBase`抽象クラスは、すべてのLLMサービス実装に共通するインターフェースを以下の主要メソッドで定義しています：
- `query()`：LLMプロバイダーにプロンプトを送信
- `get_capabilities()`：プロバイダーの機能を取得
- `format_prompt()`：変数を使用してプロンプトテンプレートをフォーマット
- `estimate_tokens()`：価格/制限のためのトークン数を推定

### 2. LLMサービスファクトリー（`factory.py`）

`LLMServiceFactory`は適切なLLMサービスインスタンスを作成するためのファクトリーパターンを実装しています：
- プロバイダーの動的登録をサポート
- プロバイダー設定を管理
- サービス検出を提供

### 3. モックLLMサービス（`mock_service.py`）

`MockLLMService`はテスト用の実装を提供します：
- テスト用の予測可能なレスポンスを返す
- API呼び出しなしでプロバイダーの動作をシミュレート
- エッジケースをテストするための設定可能な遅延とエラーを含む

### 4. OpenAIサービス（`openai_service.py`）

`OpenAIService`はOpenAI APIとの通信を実装しています：
- Chat Completions APIを使用した標準的なクエリ処理
- キャッシュ機能によるAPI呼び出しの最適化
- カスタムベースURLのサポート（LiteLLMプロキシサーバーなどと連携可能）
- トークン見積もりのためのtiktokenライブラリ統合
- エラー処理とロギング機能
- ユーザーとシステムインストラクションを含む複雑なメッセージ構造のサポート

### 5. キャッシュサービス（`cache_service.py`）

`LLMCacheService`はLLMレスポンスのためのインメモリキャッシュを実装しています：
- プロンプトとオプションから決定論的なキャッシュキーを生成
- キャッシュアイテムのTTL（Time-To-Live）を実装
- キャッシュと期限切れアイテムをクリアするためのメソッドを提供

### 6. MCPアダプター（`mcp_adapter.py`）

`MCPAdapter`はModel Context Protocolに従ってコンテキストのフォーマットを処理します：
- ドキュメントを標準化されたコンテキスト形式に変換
- トークン制限内に収まるようにコンテキストを最適化
- 関連性に基づいてコンテンツの優先順位付け

### 7. テンプレートマネージャー（`template_manager.py`）

`PromptTemplateManager`はプロンプトテンプレートを管理するシステムを提供します：
- JSONファイルからテンプレートを読み込み
- 変数置換によるテンプレートのフォーマット
- 必須変数の検証

### 8. APIエンドポイント（`llm.py`）

APIエンドポイントはRESTfulインターフェースを通じてLLM機能を公開します：
- `/query`：コンテキスト付きでLLMにクエリを送信
- `/capabilities`：プロバイダーの機能を取得
- `/templates`：利用可能なテンプレートをリスト
- `/format-prompt`：プロンプトテンプレートをフォーマット

## データモデル

LLMサービスの主要なデータモデルには以下が含まれます：
- `LLMQueryRequest`：LLMクエリのリクエストモデル
- `LLMResponse`：標準化された構造を持つレスポンスモデル
- `LLMUsage`：課金/モニタリングのためのトークン使用情報
- `PromptTemplate`：変数を持つテンプレート定義

## 実装状況

### 完了した実装
- LLMサービス基本アーキテクチャの設計と実装
- 抽象基底クラス（`LLMServiceBase`）の実装
- サービスファクトリー（`LLMServiceFactory`）の実装
- キャッシュサービス（`LLMCacheService`）の実装
- テンプレート管理システム（`PromptTemplateManager`）の実装
- モックサービス（`MockLLMService`）の実装
- OpenAIサービス（`OpenAIService`）の実装と単体テスト完了
  - 基本機能（初期化、クエリ、カスタムオプション）
  - メッセージフォーマット処理
  - キャッシュ機能
  - カスタムベースURL設定
  - エラーハンドリング
  - トークン推定機能
- MCPアダプター（`MCPAdapter`）の基本実装
- 依存関係注入システムの構築

### 開発中の機能
- ストリーミングレスポンスのサポート（最優先）
- 追加のLLMプロバイダー実装（Ollama）
- MCPアダプターの拡張機能（後続フェーズ）

### 実装詳細

#### OpenAIサービスの特記事項
OpenAIサービスは以下の機能を備えています：
- 標準的なOpenAI APIだけでなく、LiteLLMプロキシサーバーなどとの連携をサポート
- カスタムベースURLの設定により柔軟な接続先変更が可能
- 非同期クライアント（AsyncOpenAI）を使用したパフォーマンス最適化
- キャッシュによるAPI呼び出しコストの削減（完全実装済み）
- トークン使用量の正確な追跡と報告
- 様々なモデル設定のサポート（温度、最大トークン数など）
- ユーザーメッセージとシステムインストラクションを含む複雑なメッセージ構造の完全サポート
- エラーのキャプチャと意味のある例外への変換

#### 設定とセキュリティ
- 環境変数による設定（`OPENAI_API_KEY`、`OPENAI_BASE_URL`など）
- 開発/テスト環境での自動モックサービス切り替え
- 異なるプロバイダーとモデルのための設定パラメータ

## 今後の機能拡張

1. **追加プロバイダー実装**
   - Ollamaサービスの実装
   - プロバイダー固有のエラーに対する適切なエラーハンドリングの追加
   - ローカルモデルとの効率的な連携

2. **ストリーミングサポート**
   - 互換性のあるプロバイダーのストリーミングレスポンスサポートの追加
   - SSE（Server-Sent Events）エンドポイントの実装
   - ストリーミングキャッシュ対応

### ストリーミング実装計画
ストリーミングレスポンスサポートは、最優先で実装する機能として位置づけられています。以下の手順で実装を進めます：

1. **基本インターフェースの拡張**
   - `LLMServiceBase`クラスに`stream_query`メソッドを追加
   - AsyncGeneratorを返す非同期メソッドの実装
   - 新しいレスポンスモデル`LLMStreamChunk`の定義

2. **OpenAIサービス実装**
   - OpenAI APIのストリーミングモード対応
   - チャンク処理とジェネレーター実装
   - エラーハンドリングの強化

3. **FastAPIエンドポイント**
   - `/stream`エンドポイントの追加
   - SSE（Server-Sent Events）形式でのレスポンス実装
   - タイムアウト処理と接続管理

4. **モックサービス対応**
   - テスト用ストリーミングレスポンスのモック実装
   - 遅延シミュレーション機能

5. **テストスイート**
   - 単体テスト（ストリーミングジェネレーターの動作確認）
   - 統合テスト（APIエンドポイントからのストリーミングレスポンス検証）
   - 異常系テスト（エラーハンドリング、タイムアウト処理）

6. **クライアントサンプル**
   - フロントエンドでのSSE受信サンプル実装
   - 段階的表示のデモ

3. **コンテキスト最適化**
   - 大きなドキュメントのセマンティックチャンキングの改善
   - コンテキスト優先順位付けのための関連性スコアリングの実装

4. **モニタリングと可観測性**
   - トークン使用量の詳細なロギングの追加
   - パフォーマンスメトリクスの実装

5. **セキュリティ強化**
   - コンテンツフィルタリングとモデレーション
   - レート制限とクォータ

## 結論

LLMサービス実装は、ドキュメントAIヘルパーバックエンドにLLM機能を統合するための堅固な基盤を提供します。モジュラー設計により、新しいプロバイダーや機能の簡単な拡張が可能です。

OpenAIサービスの実装と単体テストの完了により、プロジェクトは主要なLLMプロバイダーとの統合を達成し、実際のプロダクション環境で使用できる状態になりました。全12件の単体テストがすべて成功し、以下の機能が確認されています：

1. サービスの基本初期化
2. 基本的なクエリ機能
3. カスタムオプションの処理
4. 複雑なメッセージ構造の処理
5. キャッシュ機能
6. 異なるオプションでのキャッシュ動作
7. カスタムベースURL設定
8. 機能情報取得
9. トークン数推定
10. エラーハンドリング
11. オプション準備ロジック
12. レスポンス変換

また、LiteLLMプロキシとの連携によって、将来的に異なるLLMプロバイダーを簡単に切り替えたり、同時に複数のプロバイダーを利用したりすることも可能です。

残りのタスクとしては、ストリーミングサポートの追加を最優先で実装し、その後Ollamaサービスの追加を行う予定です。MCPアダプターの拡張については、後続フェーズで対応します。

## 実装ロードマップ

以下の順序で機能実装を進めます：

### フェーズ1（現在進行中）
1. **ストリーミングサポート実装**（2023年7月末完了予定）
   - 基本ストリーミングインターフェース
   - OpenAIサービスのストリーミング対応
   - SSEエンドポイント実装
   - テストとドキュメント

2. **Ollamaサービス実装**（2023年8月中旬完了予定）
   - 基本機能（クエリ、機能情報取得）
   - ストリーミング対応
   - エラーハンドリング
   
### フェーズ2（2023年9月以降）
1. **モニタリングと可観測性強化**
   - 詳細なトークン使用量ロギング
   - パフォーマンスメトリクス

2. **MCPアダプター拡張**
   - コンテキスト最適化
   - GitHub MCP Serverとの連携

3. **セキュリティ強化**
   - コンテンツフィルタリング
   - レート制限とクォータ

## コード例

### ストリーミングサポート実装例

#### 1. LLMServiceBaseの拡張
```python
# services/llm/base.py
class LLMServiceBase(ABC):
    # 既存のメソッド...
    
    @abstractmethod
    async def stream_query(
        self, prompt: str, options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        ストリーミングモードでLLMにクエリを送信する。
        
        Args:
            prompt: プロンプト
            options: オプション
            
        Returns:
            AsyncGenerator: レスポンスチャンクを生成するジェネレーター
        """
        pass
```

#### 2. OpenAIサービスのストリーミング実装
```python
# services/llm/openai_service.py
class OpenAIService(LLMServiceBase):
    # 既存のメソッド...
    
    async def stream_query(
        self, prompt: str, options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """ストリーミングモードでOpenAI APIにクエリを送信する"""
        options = options or {}
        query_options = self._prepare_options(prompt, options)
        model = query_options.get("model", self.default_model)
        
        try:
            # ストリーミングパラメータを設定
            query_options["stream"] = True
            
            # OpenAI APIにリクエスト
            messages = query_options.pop("messages")
            
            # ストリーミングレスポンスを取得
            stream = await self.async_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **query_options
            )
            
            # チャンクを順次生成
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error in streaming query: {str(e)}")
            raise LLMServiceException(f"Streaming error: {str(e)}")
```

#### 3. SSEエンドポイント
```python
# api/endpoints/llm.py
@router.post(
    "/stream",
    response_model=None,
    summary="Stream LLM response",
    description="Stream response from LLM in real-time"
)
async def stream_llm_response(
    request: LLMQueryRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    """ストリーミングモードでLLMからのレスポンスを返す"""
    
    async def event_generator():
        try:
            # ストリーミングクエリを実行
            async for text_chunk in llm_service.stream_query(
                request.prompt, request.options
            ):
                # SSEフォーマットでチャンクを送信
                yield f"data: {json.dumps({'text': text_chunk})}\n\n"
                
            # ストリーム終了を示す
            yield f"data: {json.dumps({'done': True})}\n\n"
            
        except Exception as e:
            # エラーイベントを送信
            error_msg = str(e)
            yield f"data: {json.dumps({'error': error_msg})}\n\n"
    
    # SSEレスポンスを返す
    return EventSourceResponse(event_generator())
```
