````instructions
# Copilot Instructions for doc_ai_helper_backend

このドキュメントはGitHub Copilotが`doc_ai_helper_backend`プロジェクトをより良く理解し、適切な提案を行うための指示書です。

## プロジェクト概要

`doc_ai_helper_backend`は、GitサービスでホストされたMarkdownドキュメントを取得し、フロントエンドに提供するバックエンドAPIです。名前は`doc_ai_helper_backend`です。将来的にはQuartoドキュメントもサポートする予定です。

### 主な用途

1. **Markdownレンダリング**: フロントエンド側でレンダリングするためのMarkdownコンテンツの提供
2. **LLMコンテキスト**: フロントエンドからLLMに問い合わせるための元ファイル（.md）を提供
3. **HTMLドキュメント表示**: HTMLファイルの取得と提供（次期実装予定、Quarto対応の準備段階）

### 実装アプローチ

段階的な実装アプローチを採用しています：

1. **Markdownサポート（フェーズ1）**: まずMarkdownファイルの取得・処理機能を完全に実装 [✅完了]
   - 基本的なMarkdownファイル取得とコンテンツ提供
   - フロントマター解析とメタデータ抽出
   - リンク情報の抽出と変換
   - 拡張ドキュメントメタデータの提供

2. **拡張機能（フェーズ2）**: その他の機能拡張 [✅完了]
   - バックエンド経由LLM API連携の実装 [✅完了]
   - MCP（Model Context Protocol）機能の実装 [✅完了]
   - GitHubツール統合機能の実装 [✅完了]
   - LLMレスポンスキャッシュ機能の実装 [✅完了]
   - ストリーミングレスポンス機能の実装 [✅完了]
   - Forgejo対応とGitホストサービス抽象化の強化 [✅完了]

3. **次期実装予定（フェーズ3）**: 高度な機能拡張 [🔄計画中]
   - HTML対応機能（Quarto準備段階）の実装 [🔄次期優先実装]
   - リポジトリ管理機能の実装 [🔄計画中]
   - 検索機能の実装 [🔄計画中]
   - パフォーマンスとセキュリティの最適化 [🔄計画中]

5. **Quartoサポート（フェーズ5）**: Quartoドキュメントプロジェクトの特殊機能（ソースと出力ファイルの関連付けなど）を追加 [⏱️将来対応]

このアプローチにより、基本機能を早期に提供しながら、徐々に高度な機能を追加していくことが可能になります。

## バックエンド経由LLM API連携

プロジェクトの拡張として、外部LLM APIとの連携をバックエンド経由で実装します。これにより以下の利点が得られます：

### LLMサービス実装概要

LLMサービス層は、クリーンな抽象化レイヤーを通じて様々なLLMプロバイダー（OpenAI、Anthropicなど）と対話するための統一インターフェースを提供します。実装は関心事の明確な分離を持つモジュラー設計に従っています：

#### コンポーネント

1. **ベースLLMサービス（`base.py`）**
   - すべてのLLMサービス実装に共通するインターフェースを定義
   - `query()`：LLMプロバイダーにプロンプトを送信
   - `stream_query()`：ストリーミングモードでLLMプロバイダーにプロンプトを送信
   - `get_capabilities()`：プロバイダーの機能を取得
   - `format_prompt()`：変数を使用してプロンプトテンプレートをフォーマット
   - `estimate_tokens()`：価格/制限のためのトークン数を推定

2. **LLMサービスファクトリー（`factory.py`）**
   - 適切なLLMサービスインスタンスを作成するためのファクトリーパターン
   - プロバイダーの動的登録をサポート
   - プロバイダー設定を管理

3. **OpenAIサービス（`openai_service.py`）**
   - OpenAI APIとの通信を実装
   - Chat Completions APIを使用した標準的なクエリ処理
   - ストリーミングレスポンスのサポート
   - キャッシュ機能によるAPI呼び出しの最適化
   - カスタムベースURLのサポート（LiteLLMプロキシサーバーなどと連携可能）
   - トークン見積もりのためのtiktokenライブラリ統合
   - エラー処理とロギング機能
   - ユーザーとシステムインストラクションを含む複雑なメッセージ構造のサポート

4. **キャッシュサービス（`cache_service.py`）**
   - LLMレスポンスのためのインメモリキャッシュを実装
   - プロンプトとオプションから決定論的なキャッシュキーを生成
   - キャッシュアイテムのTTL（Time-To-Live）を実装
   - キャッシュと期限切れアイテムをクリアするためのメソッドを提供

5. **MCPアダプター（`mcp_adapter.py`）**
   - Model Context Protocolに従ってコンテキストのフォーマットを処理
   - ドキュメントを標準化されたコンテキスト形式に変換
   - トークン制限内に収まるようにコンテキストを最適化
   - 関連性に基づいてコンテンツの優先順位付け

6. **テンプレートマネージャー（`template_manager.py`）**
   - プロンプトテンプレートを管理するシステムを提供
   - JSONファイルからテンプレートを読み込み
   - 変数置換によるテンプレートのフォーマット
   - 必須変数の検証

7. **会話履歴管理（`conversation_history.py`）**
   - LLM問い合わせの会話履歴を管理
   - セッション単位での会話フローの保持
   - 過去のコンテキストを考慮した問い合わせ処理
   - 履歴データの構造化と効率的なアクセス

#### 実装状況

- ✅ LLMサービス基本アーキテクチャの設計と実装
- ✅ 抽象基底クラス（`LLMServiceBase`）の実装
- ✅ サービスファクトリー（`LLMServiceFactory`）の実装
- ✅ キャッシュサービス（`LLMCacheService`）の実装
- ✅ テンプレート管理システム（`PromptTemplateManager`）の実装
- ✅ モックサービス（`MockLLMService`）の実装
- ✅ OpenAIサービス（`OpenAIService`）の実装と単体テスト完了
- ✅ ストリーミングレスポンスの完全サポート
- ✅ SSE（Server-Sent Events）エンドポイントの実装
- ✅ MCPアダプター（`MCPAdapter`）の完全実装
- ✅ GitHubツール統合機能（`GitHubTools`）の実装
- ✅ セキュアなGitHubアクセス機能の実装
- ✅ Forgejo対応とGitホストサービス抽象化の強化（完了）
- ✅ 包括的なテストスイート（230+の単体テストが通過）
- 🔄 HTML対応機能（Quarto準備段階）- 次期優先実装
- ⏱️ 追加のLLMプロバイダー実装（Ollama等）- 将来実装予定
- ⏱️ MCPアダプターの拡張機能（後続フェーズ）

#### GitHubツール統合機能

GitHubとの統合機能は完全に実装され、テスト済みです。実装には以下の要素が含まれています：

1. **セキュアアクセス機能**
   - GitHubアクセストークンの安全な管理
   - リポジトリアクセス権限の検証
   - エラーハンドリングとログ出力

2. **MCPツール実装**
   - GitHubリポジトリの検索機能
   - ファイルコンテンツの取得機能
   - イシューとプルリクエストの管理機能
   - セキュリティ制限の実装

3. **APIエンドポイント実装**
   - RESTful APIエンドポイントの完全実装
   - 包括的なテストカバレッジ

#### ストリーミング実装状況

ストリーミングレスポンスのサポートは完全に実装され、テスト済みです。実装には以下の要素が含まれています：

1. **基本インターフェースの拡張**
   - `LLMServiceBase`クラスに`stream_query`メソッドを追加
   - AsyncGeneratorを返す非同期メソッドの実装
   - 全ての実装（OpenAI、Mock）でのストリーミングサポート

2. **OpenAIサービス実装**
   - OpenAI APIのストリーミングモード完全対応
   - パラメータ重複バグの修正（`model`と`stream`パラメータの重複を回避）
   - チャンク処理とジェネレーター実装の最適化
   - 包括的なエラーハンドリングの追加

3. **APIエンドポイント実装**
   - SSE（Server-Sent Events）エンドポイントの完全実装
   - フロントエンドとの連携テスト完了

OpenAIサービスのストリーミング実装例:

```python
async def stream_query(
    self, prompt: str, options: Optional[Dict[str, Any]] = None
) -> AsyncGenerator[str, None]:
    """ストリーミングモードでOpenAI APIにクエリを送信する"""
    options = options or {}
    query_options = self._prepare_options(prompt, options)
    model = query_options.get("model", self.default_model)
    
    try:
        # OpenAI APIにリクエスト
        messages = query_options.pop("messages")
        # modelキーとstreamキーをquery_optionsから削除して重複を防ぐ
        query_options.pop("model", None)
        query_options.pop("stream", None)
        
        # ストリーミングレスポンスを取得
        stream = await self.async_client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            **query_options
        )
        
        # チャンクを順次生成
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:                yield chunk.choices[0].delta.content
                
    except Exception as e:
        logger.error(f"Error in streaming query: {str(e)}")
        raise LLMServiceException(f"Streaming error: {str(e)}")
```

#### Forgejo対応完了報告

Forgejoサービスの実装が完了しました。Forgejoは軽量なGitホスティングサービスであり、以下の特徴を持ちます：

1. **セルフホスト対応**: プライベート環境での Git ホスティング
2. **GitLab/GitHub互換**: 既存のAPIパターンを活用可能
3. **オープンソース**: カスタマイズ性と透明性

完了した実装：

1. **Gitサービス抽象化の強化**
   - `GitServiceBase` の機能拡張完了
   - 認証方式の統一化（トークン、基本認証等）
   - エラーハンドリングの標準化

2. **Forgejoサービス実装**
   - `ForgejoService` クラスの完全実装（`GitServiceBase` を継承）
   - Forgejo APIとの通信実装（httpxを使用）
   - リポジトリ操作、ファイル取得機能の実装

3. **設定管理の拡張**
   - 複数ホストの設定管理
   - ホスト固有の認証情報管理
   - サービス自動検出機能

4. **テスト完了**
   - 54個のユニットテストが全て通過
   - GitHub、Forgejo、Mockサービスの統合テスト完了
   - API互換性の確認完了

1. **Gitサービス抽象化の強化**
   - `GitServiceBase` の機能拡張
   - 認証方式の統一化（トークン、基本認証等）
   - エラーハンドリングの標準化

2. **Forgejoサービス実装**
   - `ForgejoService` クラスの作成（`GitServiceBase` を継承）
   - Forgejo APIとの通信実装（httpxを使用）
   - リポジトリ操作、ファイル取得機能の実装

3. **設定管理の拡張**
   - 複数ホストの設定管理
   - ホスト固有の認証情報管理
   - サービス自動検出機能

#### HTML対応機能実装計画（Quarto準備段階）

HTML対応機能は、将来のQuarto完全サポートに向けた準備段階として実装されます：

1. **HTML処理基盤**
   - `HTMLProcessor` クラスの実装
   - HTMLメタデータ抽出機能
   - HTMLリンク解析と変換機能

2. **ファイル関連付け機能**
   - ソースファイル（.md/.qmd）と出力ファイル（.html）の関連付け
   - パスマッピング機能の基本実装
   - メタデータ連携機能

3. **API拡張**
   - HTML取得エンドポイントの拡張
   - 関連ファイル情報の提供
   - コンテンツタイプ判定の強化

## 現在の達成状況（プロジェクト概要）

本プロジェクトは**フェーズ1（Markdownサポート）とフェーズ2の主要部分（LLM API連携・MCP統合）が完了**した状態です。

### 完了済みの主要機能

#### 1. 基盤システム
- ✅ FastAPI ベースのRESTful APIアーキテクチャ
- ✅ 抽象化されたサービス層設計（GitサービスとLLMサービス）
- ✅ ファクトリーパターンによる拡張可能な設計
- ✅ 包括的なエラーハンドリングとログ機能

#### 2. ドキュメント処理システム
- ✅ Markdownファイルの完全処理（取得、解析、変換）
- ✅ フロントマター解析とメタデータ抽出
- ✅ 相対リンクの絶対パス変換
- ✅ リンク情報の抽出と構造化

#### 3. LLM統合システム
- ✅ OpenAI APIとの完全統合
- ✅ ストリーミングレスポンス機能
- ✅ SSE（Server-Sent Events）によるリアルタイム通信
- ✅ プロンプトテンプレート管理システム
- ✅ インメモリキャッシュによるパフォーマンス最適化

#### 4. MCP（Model Context Protocol）システム
- ✅ GitHubツール統合機能（リポジトリ操作、ファイル取得等）
- ✅ セキュアなGitHubアクセス機能
- ✅ MCPアダプターによるコンテキスト変換
- ✅ 日本語ローカライゼーション対応

#### 5. 品質保証
- ✅ 329の単体テストが全通過
- ✅ APIエンドポイントの包括的テスト
- ✅ エラーケースとエッジケースのテスト
- ✅ モックサービスを活用したテスト駆動開発

### 次期優先実装予定の機能

- 🔄 Forgejo対応とGitホストサービスの抽象化強化（最優先）
- 🔄 HTML対応機能（Quarto対応の準備段階）
- 🔄 データベース層の本格実装（現在はモック）
- 🔄 検索API機能
- 🔄 リポジトリ管理API

### 将来実装予定の機能

- ⏱️ Quartoドキュメントサポート（フェーズ3）
- ⏱️ 追加のLLMプロバイダー実装（Ollama等）

## 実装計画

### 現在の状況
- 環境構築完了
- エントリーポイント作成済み
- 基本的なAPIルーティングの設定完了
- ヘルスチェックAPIの実装完了
- ドキュメント取得APIの基本機能実装完了
- リポジトリ構造取得APIの基本機能実装完了
- Mockサービスの実装完了（開発・デモ・テスト用）
- LLMサービス層の完全実装（OpenAI、ストリーミング、MCP、キャッシュ等）
- GitHubツール統合機能の実装完了
- 包括的なテストスイート完了（329の単体テストが通過）

**実装方針の明確化**:
- Markdownドキュメント対応を最優先で実装 [✅完了]
- LLM API連携の基本機能実装 [✅完了]
- MCP（Model Context Protocol）機能実装 [✅完了]
- GitHubツール統合機能実装 [✅完了]
- Forgejo対応とGitホストサービス抽象化の強化 [🔄次期最優先]
- HTML対応機能（Quarto準備段階）の実装 [🔄次期優先]
- データベース層はモックで実装（APIの仕様が定まりつつある段階）
- Quarto対応は将来の拡張として位置付け

## 実装計画

### 現在の状況
- 環境構築完了
- エントリーポイント作成済み
- 基本的なAPIルーティングの設定完了
- ヘルスチェックAPIの実装完了
- ドキュメント取得APIの基本機能実装完了
- リポジトリ構造取得APIの基本機能実装完了
- Mockサービスの実装完了（開発・デモ・テスト用）

### 開発ステップ
1. **基本API定義の完了** [✅完了]
   - RESTful APIのエンドポイント定義
   - リクエスト/レスポンスのPydanticモデル定義
   - エラーハンドリングの実装

2. **サービス層の実装** [✅完了]
   - 抽象Gitサービスの実装（`services/git/base.py`）
   - GitHub実装（`services/git/github_service.py`）
   - Mock実装（`services/git/mock_service.py`）   - ドキュメント処理サービス（`services/document_service.py`）
   - キャッシュサービス（基本実装）
   - LLMサービス実装（`services/llm/`）

3. **モックを用いたAPIの動作確認** [✅完了]
   - 実際のデータベースなしでサービス層をモックしてAPIの動作を確認
   - テスト駆動開発の手法を活用し、APIの期待する動作をテストで定義

4. **Markdownドキュメント対応の拡張** [✅完了]
   - Markdownファイルのフロントマター解析
   - 相対リンクの絶対パス変換機能
   - リンク情報の抽出と提供
   - ドキュメントメタデータの拡充
   
5. **LLM API連携の実装** [✅完了]
   - LLMサービス抽象化レイヤーの実装（`services/llm/base.py`） [✅完了]
   - プロバイダー固有の実装（OpenAI, モックサービス） [✅完了]
   - `LLMServiceFactory` の実装（`services/llm/factory.py`） [✅完了]
   - MCPアダプターの実装（`services/llm/mcp_adapter.py`） [✅完了]
   - LLM問い合わせ用エンドポイントの追加（`api/endpoints/llm.py`） [✅完了]
   - プロンプトテンプレート管理機能の実装 [✅完了]
   - レスポンスキャッシュの実装 [✅完了]
   - ストリーミングレスポンスのサポート [✅完了]
   - SSE（Server-Sent Events）エンドポイントの実装 [✅完了]
   - 会話履歴管理機能の実装 [✅完了]
   - MCPサーバー（FastMCPベース）の実装 [✅完了]
   - Function Calling/ツール実行機能の実装 [✅完了]
   - フィードバック分析エンジンの実装 [✅完了]
   - MCPツール（document/feedback/analysis）の実装 [✅完了]
   - ユニットテスト完全実装（29件全てPASSED）[✅完了]

6. **GitHub MCP統合の実装** [🔄次期実装予定]
   - GitHub APIクライアント基盤の実装
   - `create_github_issue` MCPツールの実装
   - `create_github_pr` MCPツールの実装
   - GitHub認証・権限管理機能の実装
   - MCPサーバーへのGitHubツール登録
   - Function Calling統合とエラーハンドリング
   - ユニットテスト・統合テスト実装

7. **APIの拡張（将来機能）** [⏱️将来対応]
   - Quartoプロジェクト検出機能の追加
   - ソースファイルと出力ファイルの関連付けエンドポイント
   - リンク変換オプションの追加
   - フロントマター解析とメタデータ提供機能の拡張
   - リポジトリ設定モデルとAPIの追加

8. **データベース層の実装** [🔄進行予定]
   - SQLAlchemyのBaseクラスとデータベース接続の設定（`db/database.py`）
   - モデル定義（`db/models.py`）
   - リポジトリパターンによるデータアクセス層の実装（`db/repositories/`）
   - Alembicによるマイグレーション設定
   - リポジトリ設定・マッピング機能の追加

9. **Quartoドキュメント対応の追加** [⏱️未着手]
   - Quartoプロジェクト設定（_quarto.yml）の解析
   - ソースファイル(.qmd)と出力ファイル(.html)の関連付け
   - リポジトリ構造分析とパスマッピング
   - サイト構造情報の提供

10. **テストの充実** [✅完了]
   - APIエンドポイントのテスト（ドキュメント取得、構造取得）[✅完了]
   - 単体テスト：Mockサービスを使った外部依存なしテスト [✅完了]
   - 統合テスト：実際の外部API（GitHub、OpenAI等）を使用したテスト [✅完了]
   - Markdownドキュメント機能のテスト [✅完了]
   - LLMサービスのテスト [✅完了]
   - 会話履歴管理機能のテスト [✅完了]
   - 将来的なQuartoプロジェクト対応のテスト [⏱️未着手]

11. **リファクタリングとコード品質向上** [🔄部分的に完了]
    - モックサービスをテスト用からプロダクションコードへ移行 [✅完了]
    - APIパスの整理（`/contents`と`/structure`の明確な分離）[✅完了]
    - Markdownドキュメント処理の強化 [✅完了]
    - LLMサービスのエラーハンドリング強化 [✅完了]
    - ログ出力の強化 [🔄計画中]
    - パフォーマンス最適化 [🔄計画中]
    - セキュリティ対策の強化 [🔄計画中]

## 主要機能

1. **ドキュメント取得API** [✅基本実装済み]
   - 様々なGitサービス（GitHub, Mock等）からのドキュメント取得
   - Markdownファイルの取得と提供
   - リポジトリ構造の取得
   - ドキュメント内リンクの解析と変換 [✅完了]
   - フロントマターの解析とメタデータ提供 [✅完了]
   - HTMLファイルの取得と提供（基本実装済み）
   - Quarto/HTMLファイルのソースと出力ファイルの関連付け（将来対応）

2. **リポジトリ管理API** [🔄実装予定]
   - リポジトリ情報のCRUD操作
   - リポジトリメタデータの管理
   - Markdownドキュメント設定の管理
   - 将来的にはQuartoドキュメント設定（パスマッピング、出力ディレクトリなど）の管理
   - リポジトリタイプ（Markdown/Quarto）の検出と管理

3. **LLM API連携** [✅完了]
   - 外部LLMサービス（OpenAI）との統合 [✅完了]
   - ストリーミングレスポンスのサポート [✅完了]
   - SSE（Server-Sent Events）によるリアルタイム応答 [✅完了]
   - Model Context Protocol (MCP) 対応 [✅完了]
   - ドキュメントコンテキストを活用したLLM問い合わせ [✅完了]
   - プロンプトテンプレート管理 [✅完了]
   - レスポンスキャッシュ [✅完了]
   - 会話履歴管理 [✅完了]
   - MCPサーバー（FastMCPベース）の実装 [✅完了]
   - Function Calling/ツール実行機能 [✅完了]
   - フィードバック分析エンジン [✅完了]
   - MCPツール（document/feedback/analysis）[✅完了]

4. **GitHub統合** [🔄次期実装予定]
   - GitHub MCPツール（Issue/PR作成）[🔄実装予定]
   - GitHub認証・権限管理 [🔄実装予定]
   - Function Calling経由GitHub操作 [🔄実装予定]
   - GitHub統合テスト [🔄実装予定]

5. **検索API** [🔄実装予定]
   - リポジトリ内のファイル検索
   - テキスト検索とメタデータ検索
   - ドキュメントタイプや属性によるフィルタリング

6. **キャッシュ機能** [基本実装済み]
   - 頻繁にアクセスされるドキュメントのキャッシュ
   - リポジトリ構造のキャッシュ
   - 設定情報のキャッシュ
   - LLMレスポンスのキャッシュ [✅完了]

## 技術スタック

- **フレームワーク**: FastAPI
- **データベース**: SQLite（開発・本番共通）
- **ORM**: SQLAlchemy
- **マイグレーション**: Alembic
- **HTTP クライアント**: httpx
- **キャッシュ**: Redis または in-memory
- **テスト**: pytest
- **コンテナ化**: Docker
- **フォーマッター**: black

3. **パフォーマンスと機能最適化**
   - レスポンスのキャッシュによるAPI利用コスト削減
   - コンテキスト最適化
   - レート制限の一元管理

4. **Model Context Protocol (MCP) との連携**
   - 異なるLLMプロバイダー間でのコンテキスト管理標準化
   - Markdownドキュメントから抽出した情報を構造化された形式でLLMに提供
   - 既存の処理パイプライン（MarkdownProcessor, LinkTransformer）の活用

### 実装アプローチ

1. **LLMサービス抽象化レイヤーの追加**
   - 基底クラス `LLMServiceBase` の実装
   - プロバイダー固有の実装（OpenAI, Anthropic等）
   - `LLMServiceFactory` によるサービスの抽象化

2. **MCPアダプターの実装**
   - ドキュメントデータをMCPフォーマットに変換
   - コンテキストの最適化と構造化

3. **APIエンドポイントの拡張**
   - LLM問い合わせ用エンドポイントの追加
   - コンテキスト管理APIの実装

この拡張は既存のプロジェクトアーキテクチャ（特にサービス抽象化とファクトリーパターン）と自然に統合され、将来的なLLM統合の基盤となります。

## 現在の開発状況

### 実装済み機能
- 環境構築完了
- エントリーポイント作成済み
- 基本的なAPIルーティングの設定完了
- ヘルスチェックAPIの実装完了
- ドキュメント取得APIの基本機能実装完了
- リポジトリ構造取得APIの基本機能実装完了
- Mockサービスの実装完了（開発・デモ・テスト用）
- Markdownドキュメント処理機能の完全実装（フロントマター解析、リンク変換など）

### 実装方針の明確化
- Markdownドキュメント対応を最優先で実装（✅完了）
- データベース層はモックで実装（APIの仕様が定まった段階でモデル定義を行う）
- Quarto対応は将来の拡張として位置付け

### 開発ステップ
1. **基本API定義の完了** [✅完了]
   - RESTful APIのエンドポイント定義
   - リクエスト/レスポンスのPydanticモデル定義
   - エラーハンドリングの実装

2. **サービス層の実装** [✅完了]
   - 抽象Gitサービスの実装（`services/git/base.py`）
   - GitHub実装（`services/git/github_service.py`）
   - Mock実装（`services/git/mock_service.py`）
   - ドキュメント処理サービス（`services/document_service.py`）
   - キャッシュサービス（基本実装）

3. **モックを用いたAPIの動作確認** [✅完了]
   - 実際のデータベースなしでサービス層をモックしてAPIの動作を確認
   - テスト駆動開発の手法を活用し、APIの期待する動作をテストで定義

4. **Markdownドキュメント対応の拡張** [✅完了]
   - Markdownファイルのフロントマター解析
   - 相対リンクの絶対パス変換機能
   - リンク情報の抽出と提供
   - ドキュメントメタデータの拡充
   
5. **APIの拡張（Quarto対応を見据えた機能）** [🔄計画中]
   - Quartoプロジェクト検出機能の追加
   - ソースファイルと出力ファイルの関連付けエンドポイント
   - リンク変換オプションの追加
   - フロントマター解析とメタデータ提供機能の拡張
   - リポジトリ設定モデルとAPIの追加

6. **LLM API連携の実装** [🔄優先実装予定]
   - LLMサービス抽象化レイヤーの実装（`services/llm/base.py`）
   - プロバイダー固有の実装（OpenAI, Anthropic等）
   - `LLMServiceFactory` の実装（`services/llm/factory.py`）
   - MCPアダプターの実装（`services/llm/mcp_adapter.py`）
   - LLM問い合わせ用エンドポイントの追加（`api/endpoints/llm.py`）
   - プロンプトテンプレート管理機能の実装
   - レスポンスキャッシュの実装

7. **データベース層の実装** [🔄進行予定]
   - SQLAlchemyのBaseクラスとデータベース接続の設定（`db/database.py`）
   - モデル定義（`db/models.py`）
   - リポジトリパターンによるデータアクセス層の実装（`db/repositories/`）
   - Alembicによるマイグレーション設定
   - リポジトリ設定・マッピング機能の追加

8. **Quartoドキュメント対応の追加** [⏱️未着手]
   - Quartoプロジェクト設定（_quarto.yml）の解析
   - ソースファイル(.qmd)と出力ファイル(.html)の関連付け
   - リポジトリ構造分析とパスマッピング
   - サイト構造情報の提供

## 技術スタック

- **フレームワーク**: FastAPI
- **データベース**: SQLite（開発・本番共通）
- **ORM**: SQLAlchemy
- **マイグレーション**: Alembic
- **HTTP クライアント**: httpx
- **キャッシュ**: Redis または in-memory
- **テスト**: pytest
- **コンテナ化**: Docker
- **フォーマッター**: black

## ディレクトリ構造

現在のプロジェクト構造は以下の通りです：

```
doc_ai_helper_backend/
├── doc_ai_helper_backend/         # メインパッケージ
│   ├── __init__.py
│   ├── main.py                    # アプリケーションエントリーポイント
│   ├── api/                       # API層
│   │   ├── __init__.py
│   │   ├── api.py                 # APIルーティング設定
│   │   ├── dependencies.py        # 依存関係注入
│   │   ├── error_handlers.py      # エラーハンドラー
│   │   └── endpoints/             # エンドポイント定義
│   │       ├── __init__.py
│   │       ├── documents.py       # ドキュメント取得API
│   │       ├── health.py          # ヘルスチェックAPI
│   │       ├── repositories.py    # リポジトリ管理API
│   │       ├── search.py          # 検索API
│   │       └── llm.py             # LLM API（完了）
│   ├── core/                      # コア機能
│   │   ├── __init__.py
│   │   ├── config.py              # 設定管理
│   │   ├── exceptions.py          # カスタム例外
│   │   └── logging.py             # ロギング設定
│   ├── db/                        # データベース層
│   │   ├── __init__.py
│   │   └── database.py            # データベース接続
│   ├── models/                    # データモデル
│   │   ├── __init__.py
│   │   ├── document.py            # ドキュメントモデル
│   │   ├── frontmatter.py         # フロントマターモデル
│   │   ├── link_info.py           # リンク情報モデル
│   │   ├── llm.py                 # LLMモデル
│   │   ├── repository_context.py  # リポジトリコンテキスト
│   │   ├── repository.py          # リポジトリモデル
│   │   └── search.py              # 検索モデル
│   ├── services/                  # サービス層
│   │   ├── __init__.py
│   │   ├── document_service.py    # ドキュメント処理サービス
│   │   ├── document_processors/   # ドキュメントプロセッサー
│   │   │   ├── __init__.py
│   │   │   ├── base_processor.py   # 基底プロセッサー
│   │   │   ├── factory.py          # プロセッサーファクトリ
│   │   │   ├── frontmatter_parser.py # フロントマター解析
│   │   │   ├── link_transformer.py   # リンク変換
│   │   │   └── markdown_processor.py # Markdown処理
│   │   ├── git/                   # Gitサービス
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Git基本サービス
│   │   │   ├── factory.py         # Gitサービスファクトリ
│   │   │   ├── github_service.py  # GitHub実装
│   │   │   ├── forgejo_service.py # Forgejo実装（完了）
│   │   │   └── mock_service.py    # モック実装
│   │   ├── github/                # GitHub統合サービス
│   │   │   ├── __init__.py
│   │   │   ├── client.py          # GitHubクライアント
│   │   │   └── auth.py            # GitHub認証
│   │   ├── llm/                   # LLMサービス（完了）
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # LLM基本サービス
│   │   │   ├── factory.py         # LLMサービスファクトリ
│   │   │   ├── openai_service.py  # OpenAI実装
│   │   │   ├── mock_service.py    # モック実装
│   │   │   ├── cache_service.py   # キャッシュサービス
│   │   │   ├── template_manager.py # テンプレート管理
│   │   │   ├── conversation_history.py # 会話履歴管理
│   │   │   ├── function_manager.py # Function Calling管理
│   │   │   └── templates/         # プロンプトテンプレート
│   │   │       └── prompts.json
│   │   └── mcp/                   # MCP統合（完了）
│   │       ├── __init__.py
│   │       ├── server.py          # MCPサーバー
│   │       ├── config.py          # MCP設定
│   │       ├── function_adapter.py # Function Calling アダプター
│   │       └── tools/             # MCPツール群
│   │           ├── __init__.py
│   │           ├── document_tools.py   # ドキュメントツール
│   │           ├── feedback_tools.py   # フィードバックツール
│   │           ├── analysis_tools.py   # 分析ツール
│   │           ├── git_tools.py        # Gitツール
│   │           └── git/               # Git統合ツール詳細
│   │               ├── __init__.py
│   │               ├── factory.py
│   │               ├── service_resolver.py
│   │               ├── forgejo_adapter.py
│   │               ├── adapters/
│   │               │   ├── __init__.py
│   │               │   ├── base_adapter.py
│   │               │   ├── github_adapter.py
│   │               │   └── forgejo_adapter.py
│   │               ├── context/
│   │               │   ├── __init__.py
│   │               │   └── repository_context.py
│   │               ├── operations/
│   │               │   ├── __init__.py
│   │               │   └── git_operations.py
│   │               └── tools/
│   │                   ├── __init__.py
│   │                   └── git_mcp_tools.py
│   └── utils/                     # ユーティリティ
│       ├── __init__.py
│       └── errors.py              # エラーユーティリティ
├── tests/                         # テスト
│   ├── __init__.py
│   ├── conftest.py                # テスト設定
│   ├── api/                       # APIテスト
│   │   ├── __init__.py
│   │   ├── test_documents.py      # ドキュメントAPIテスト
│   │   └── test_health.py         # ヘルスチェックAPIテスト
│   ├── integration/               # 統合テスト
│   │   └── __init__.py
│   ├── unit/                      # ユニットテスト
│   │   └── __init__.py
│   └── e2e/                       # E2Eテスト
│       └── __init__.py
├── docs/                          # ドキュメント
│   ├── API_REFERENCE.md
│   ├── ARCHITECTURE.md
│   ├── DEVELOPMENT.md
│   ├── FORGEJO_SETUP_GUIDE.md
│   ├── PROJECT_HISTORY.md
│   └── SETUP_GUIDE.md
├── examples/                      # サンプルコード
│   ├── demo_multi_git_mcp.py
│   ├── frontend_api_demo.py
│   └── test_api_mcp_tools.py
├── data/                          # データディレクトリ
├── docker-compose.yml             # Docker Compose設定
├── Dockerfile                     # Docker設定
├── README.md                      # プロジェクト説明
├── requirements.lock              # 固定依存関係
├── requirements.txt               # 依存関係
└── setup.py                       # セットアップスクリプト
```

## 実装アプローチの詳細

### アプリケーションエントリポイント

プロジェクトのエントリポイントは `main.py` であり、FastAPIアプリケーションの初期化、CORSミドルウェアの設定、APIルーターのマウント、エラーハンドラーの設定を行っています。

```python
# main.py
app = FastAPI(
    title="Document AI Helper API",
    description="API for Document AI Helper",
    version=settings.app_version,
    debug=settings.debug,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router)
```

### APIルーティング

APIルーティングは `api.py` で定義され、各エンドポイントのルーターをメインルーターに統合しています。

```python
# api.py
router = APIRouter(prefix=settings.api_prefix)

# Include routers for different endpoints
router.include_router(health_router, prefix="/health")
router.include_router(documents_router, prefix="/documents")
router.include_router(repositories_router, prefix="/repositories")
router.include_router(search_router, prefix="/search")
router.include_router(llm_router, prefix="/llm")  # 計画中のLLM APIルーター
```

### 依存関係注入

依存関係の注入は `dependencies.py` で行われ、サービスインスタンスの生成と提供を行っています。これにより、テスト時にモックサービスを注入することが容易になります。

### Gitサービス抽象化

Gitサービスは抽象基底クラス `GitServiceBase` を実装しており、ファクトリパターンを使用して具体的な実装を生成します。

```python
# factory.py
class GitServiceFactory:
    """Factory for creating Git service instances."""

    # Registry of available Git services
    _services: Dict[str, Type[GitServiceBase]] = {
        "github": GitHubService,
        "mock": MockGitService,
    }

    @classmethod
    def create(
        cls, service_type: str, access_token: Optional[str] = None
    ) -> GitServiceBase:
        # 実装
```

### エンドポイント

各エンドポイントは `/api/endpoints/` ディレクトリにモジュールとして実装されています。例えば、ドキュメント取得APIは以下のように実装されています：

```python
# documents.py
@router.get(
    "/contents/{service}/{owner}/{repo}/{path:path}",
    response_model=DocumentResponse,
    summary="Get document",
    description="Get document from a Git repository",
)
async def get_document(
    service: str = Path(..., description="Git service (github, gitlab, etc.)"),
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    path: str = Path(..., description="Document path"),
    ref: Optional[str] = Query(default="main", description="Branch or tag name"),
    transform_links: bool = Query(
        default=True, description="Transform relative links to absolute"
    ),
    base_url: Optional[str] = Query(
        default=None, description="Base URL for link transformation"
    ),
    document_service: DocumentService = Depends(get_document_service),
):
    # 実装
```

## ドキュメントモデル

```python
# ドキュメントレスポンスモデル
class DocumentResponse(BaseModel):
    path: str                   # ファイルパス
    name: str                   # ファイル名
    type: DocumentType          # ドキュメントタイプ
    content: DocumentContent    # ドキュメントコンテンツ
    metadata: DocumentMetadata  # ドキュメントメタデータ
    repository: str             # リポジトリ名
    owner: str                  # リポジトリオーナー
    service: str                # Gitサービス
    ref: str                    # ブランチまたはタグ
    links: List[LinkInfo]       # リンク情報
    transformed_content: Optional[str]  # リンク変換済みコンテンツ
    # 計画中の拡張フィールド
    # relations: Optional[DocumentRelations]  # 関連ドキュメント情報（将来実装予定）
```

### リンク情報モデル

```python
# リンク情報モデル
class LinkInfo(BaseModel):
    text: str                  # リンクテキスト
    url: str                   # リンクURL
    is_image: bool             # 画像リンクかどうか
    position: Tuple[int, int]  # リンクの位置（開始,終了）
    is_external: bool          # 外部リンクかどうか
```

### 拡張ドキュメントメタデータモデル

```python
# 拡張ドキュメントメタデータモデル
class ExtendedDocumentMetadata(BaseModel):
    filename: str              # ファイル名
    extension: str             # ファイル拡張子
    frontmatter: Dict[str, Any] # フロントマターデータ
    title: Optional[str]       # タイトル
    description: Optional[str] # 説明
    author: Optional[str]      # 著者
    date: Optional[str]        # 日付
    tags: List[str]            # タグ
```

### ドキュメント設定モデル（計画中）

```python
# パスマッピングモデル（将来的なQuartoサポートで使用）
class PathMapping(BaseModel):
    source_dir: str             # ソースディレクトリ（例: 'src'）
    output_dir: str             # 出力ディレクトリ（例: '_site'）
    source_ext: List[str]       # ソースファイル拡張子（例: ['qmd', 'md']）
    output_ext: str = "html"    # 出力ファイル拡張子

# リポジトリ設定モデル
class RepositorySettings(BaseModel):
    document_type: DocumentType  # ドキュメントタイプ（markdown, quarto等）
    # Markdownのみの場合は以下は不要
    config_file: Optional[str] = None  # 設定ファイル（_quarto.yml等）
    path_mappings: Optional[List[PathMapping]] = None  # パスマッピング設定（Quarto用）
    ## コーディングガイドライン

1. **FastAPIベストプラクティス**
   - エンドポイントには適切な`response_model`を設定する
   - Path, Query, Bodyパラメータにはすべて説明を付与する
   - 依存関係の注入を積極的に活用する

2. **タイプヒント**
   - すべての関数とメソッドには適切なタイプヒントを付与する
   - 複雑な型は`typing`モジュールを活用する

3. **エラーハンドリング**
   - カスタム例外を適切に使用する
   - APIレスポンスでは適切なHTTPステータスコードを返す
   - 明確なエラーメッセージを提供する

4. **テスト駆動開発**
   - 新機能を追加する前にテストを書く
   - モックを活用して外部依存関係を分離する
   - 単体テストと統合テストの両方を作成する

5. **ドキュメンテーション**
   - コードにはDocstringを付与する
   - APIエンドポイントには適切な説明を付与する
   - README.mdは最新の状態を維持する

6. **コードスタイル**
   - blackフォーマッターに従う
   - 一貫性のある命名規則を使用する
   - 適切な関数/メソッドの分割を行う

7. **開発優先順位**
   - Markdownドキュメント対応を最優先で実装 [✅完了]
   - バックエンド経由LLM API連携を優先的に実装 [✅完了]
   - Forgejo対応とGitサービス抽象化の強化 [✅完了]
   - 会話履歴管理機能の実装 [✅完了]
   - MCP統合とFunction Calling機能の実装 [✅完了]
   - HTML対応機能（Quarto準備段階）の実装を進める [🔄次期優先]
   - リポジトリ管理機能の実装を進める [🔄計画中]
   - 検索機能の実装を進める [🔄計画中]
   - キャッシュ機能を強化する [🔄計画中]
   - Quarto対応は将来の拡張として位置付ける [⏱️将来対応]
```

## ドキュメント処理アーキテクチャ

ドキュメント処理は以下のモジュールで構成されています：

### 基底プロセッサー (BaseProcessor)

すべてのドキュメントプロセッサーの基底クラスとして機能し、共通インターフェースを定義します。

```python
class DocumentProcessorBase(ABC):
    @abstractmethod
    def process_content(self, content: str, path: str) -> "DocumentContent":
        """ドキュメントコンテンツを処理する"""
        pass
        
    @abstractmethod
    def extract_metadata(self, content: str, path: str) -> "DocumentMetadata":
        """ドキュメントからメタデータを抽出する"""
        pass
        
    @abstractmethod
    def extract_links(self, content: str, base_path: str) -> List["LinkInfo"]:
        """ドキュメントからリンク情報を抽出する"""
        pass
        
    @abstractmethod
    def transform_links(self, content: str, links: List["LinkInfo"], base_url: str) -> str:
        """ドキュメント内のリンクを変換する"""
        pass
```

### Markdownプロセッサー (MarkdownProcessor)

Markdownドキュメントに特化した処理を行うプロセッサーです。

```python
class MarkdownProcessor(DocumentProcessorBase):
    """Markdownドキュメント処理クラス"""
    
    # 実装メソッド
    def process_content(self, content: str, path: str) -> DocumentContent:
        # Markdownの処理ロジック
        
    def extract_metadata(self, content: str, path: str) -> DocumentMetadata:
        # フロントマターの解析とメタデータ抽出
        
    def extract_links(self, content: str, base_path: str) -> List[LinkInfo]:
        # Markdownリンクの検出と情報抽出
        
    def transform_links(self, content: str, links: List[LinkInfo], base_url: str) -> str:
        # 相対リンクの絶対パス変換
```

### フロントマターパーサー (FrontmatterParser)

Markdownファイルからフロントマターを解析するユーティリティです。

```python
def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Markdownコンテンツからフロントマターを解析する。
    
    Returns:
        (フロントマター辞書, フロントマー除去済みコンテンツ)のタプル
    """
    # python-frontmatterを使用した実装
```

### リンク変換 (LinkTransformer)

ドキュメント内のリンクを検出し、変換するユーティリティです。

```python
class LinkTransformer:
    """Markdownドキュメント内のリンクを変換するユーティリティクラス。"""
    
    @staticmethod
    def transform_relative_links(content: str, base_url: str, base_path: str) -> str:
        """相対リンクを絶対パスに変換する"""
        
    @staticmethod
    def extract_links(content: str, is_markdown: bool = True) -> List[LinkInfo]:
        """ドキュメントからリンク情報を抽出する"""
```

### プロセッサーファクトリー (ProcessorFactory)

ドキュメントタイプに応じた適切なプロセッサーを生成するファクトリークラスです。

```python
class DocumentProcessorFactory:
    """ドキュメントタイプに応じたプロセッサーを生成するファクトリークラス。"""
    
    # 利用可能なプロセッサー
    _processors: Dict[DocumentType, Type[DocumentProcessorBase]] = {
        DocumentType.MARKDOWN: MarkdownProcessor,
        # 将来的にQuartoやHTMLを追加
    }
    
    @classmethod
    def create(cls, document_type: DocumentType) -> DocumentProcessorBase:
        """ドキュメントタイプに応じたプロセッサーを生成する"""
```

## LLM API連携アーキテクチャ

LLM API連携は以下のモジュールで構成されています（完了済み）：

### 基底LLMサービス (LLMServiceBase)

すべてのLLMサービスの基底クラスとして機能し、共通インターフェースを定義します。

```python
class LLMServiceBase(ABC):
    @abstractmethod
    async def query(self, prompt: str, options: Dict[str, Any] = None) -> LLMResponse:
        """LLMへの問い合わせを行う"""
        pass
        
    @abstractmethod
    async def get_capabilities(self) -> Dict[str, Any]:
        """LLMの機能と制限を取得する"""
        pass
        
    @abstractmethod
    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """プロンプトテンプレートをフォーマットする"""
        pass
```

### LLMサービス実装 (OpenAIService, AnthropicService など)

各LLMプロバイダーに特化したサービス実装です。

```python
class OpenAIService(LLMServiceBase):
    """OpenAI API実装"""
    
    def __init__(self, api_key: str, default_model: str = "gpt-4", **kwargs):
        self.client = OpenAI(api_key=api_key)
        self.default_model = default_model
        self.default_options = kwargs
    
    async def query(self, prompt: str, options: Dict[str, Any] = None) -> LLMResponse:
        # OpenAI固有の実装
        
    async def get_capabilities(self) -> Dict[str, Any]:
        # OpenAI固有の機能と制限
        
    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        # プロンプトテンプレートの処理
```

### LLMサービスファクトリー (LLMServiceFactory)

LLMプロバイダーに応じた適切なサービスを生成するファクトリークラスです。

```python
class LLMServiceFactory:
    """LLMプロバイダーに応じたサービスを生成するファクトリークラス。"""
    
    # 利用可能なサービス
    _services: Dict[str, Type[LLMServiceBase]] = {        "openai": OpenAIService,
        "anthropic": AnthropicService,
        "gemini": GeminiService,
        # 将来的に他のプロバイダーを追加
    }
    
    @classmethod
    def create(cls, provider: str, **config) -> LLMServiceBase:
        """プロバイダーに応じたLLMサービスを生成する"""
```

### MCPアダプター (MCPAdapter)

Model Context Protocol に準拠したコンテキスト管理を行うアダプターです。

```python
class MCPAdapter:
    """Model Context Protocol アダプター"""
    
    @staticmethod
    def convert_document_to_context(document: DocumentResponse) -> Dict[str, Any]:
        """ドキュメントをMCPコンテキストに変換する"""
        
    @staticmethod
    def optimize_context(context: List[Dict[str, Any]], max_tokens: int) -> List[Dict[str, Any]]:
        """コンテキストを最適化する"""
```

### LLM APIエンドポイント

LLM API連携のためのエンドポイントです。

```python
# llm.py
@router.post(
    "/query",
    response_model=LLMQueryResponse,
    summary="Query LLM",
    description="Send a query to LLM with document context",
)
async def query_llm(
    request: LLMQueryRequest,
    llm_service: LLMService = Depends(get_llm_service),
):
    # 実装
```

## 進捗サマリー（2025年7月4日現在）

### フェーズ2完了 - Forgejo対応とGitサービス抽象化完了
- ✅ **Gitサービス抽象化**: GitHub、Forgejo、Mockサービス統合完了
- ✅ **Forgejoサービス**: 完全実装・54個のテスト全通過
- ✅ **MCPサーバー（FastMCPベース）**: 完全実装・テスト済み
- ✅ **Function Calling/ツール実行機能**: 完全実装・テスト済み
- ✅ **フィードバック分析エンジン**: 完全実装・テスト済み
- ✅ **MCPツール群**: document_tools/feedback_tools/analysis_tools全て実装済み
- ✅ **LLMサービス**: 99個のテスト全通過
- ✅ **API統合**: 基本エンドポイント27個中25個通過

### 主要実装コンポーネント
- **Gitサービス**: `doc_ai_helper_backend/services/git/` (GitHub、Forgejo、Mock)
- **MCPサーバー**: `doc_ai_helper_backend/services/mcp/server.py`
- **Function Registry**: `doc_ai_helper_backend/services/llm/function_manager.py`
- **MCPアダプター**: `doc_ai_helper_backend/services/mcp/function_adapter.py`
- **ツール群**: 
  - document_tools: ドキュメント解析・最適化
  - feedback_tools: フィードバック収集・分析
  - analysis_tools: テキスト分析・感情分析
  - git_tools: Git統合機能
- **設定管理**: `doc_ai_helper_backend/services/mcp/config.py`

### 完了した実装項目（フェーズ1-2）
- ✅ Markdownドキュメント取得・処理（フロントマター解析、リンク変換）
- ✅ Gitサービス抽象化とForgejo対応
- ✅ LLMサービス基本アーキテクチャ（OpenAI、ストリーミング、キャッシュ）
- ✅ 会話履歴管理サービス
- ✅ MCPサーバー（FastMCPベース）とツール群
- ✅ Function Calling/ツール実行機能
- ✅ フィードバック分析エンジン
- ✅ 包括的ユニットテスト（230+件通過）

### 次期計画（フェーズ3）
- HTML対応機能（Quarto準備段階）の実装
- データベース層の本格実装
- 検索機能の実装
- リポジトリ管理機能の実装
- パフォーマンス最適化とセキュリティ強化

## � 次期実装計画（フェーズ3: 高度な機能拡張）

### 🎯 実装目標
現在の安定した基盤を活用して、高度な機能拡張を実装します。

### 📅 実装スケジュール
- **Phase 3.1**: HTML対応機能（Quarto準備段階）
- **Phase 3.2**: データベース層本格実装
- **Phase 3.3**: 検索機能・リポジトリ管理機能

### 🔧 実装予定機能

#### HTML対応機能（優先度: 高）
```python
# HTML処理基盤の実装
async def get_html_document(
    repository: str,
    path: str,
    include_source: bool = False
) -> Dict[str, Any]:
    """HTMLドキュメントとソースファイルの関連付け取得"""

async def analyze_quarto_project(
    repository: str
) -> Dict[str, Any]:
    """Quartoプロジェクト設定の解析"""
```
    repository: str,        # "owner/repo" 形式
    title: str,            # PR タイトル
    description: str,      # PR 説明
    file_path: str,        # 変更するファイルパス
    file_content: str,     # 新しいファイル内容
    branch_name: str = None,       # ブランチ名
    base_branch: str = "main"      # ベースブランチ
) -> Dict[str, Any]:
    """GitHub Pull Request を作成し、結果を返す"""
```

#### **実装計画（2週間）**
**Week 1**: GitHub基盤・MCPツール実装
- GitHub APIクライアント基盤（認証・基本API）
- MCPツール実装（Issue/PR作成）
- MCPサーバー統合

**Week 2**: 統合・テスト・最適化
- Function Calling統合
- ユニット・統合テスト実装
- エラーハンドリング・リトライ機能
- ドキュメント・デプロイ準備

#### **実装の利点**
1. **最小実装**: 既存MCP基盤（29テスト通過）をフル活用
2. **即座に動作**: フロントエンド不要でLLM対話テスト可能
3. **段階的拡張**: 基本機能確立後、フィードバックAPI等を追加可能
4. **実装量削減**: 約250行の実装でコア機能完成

#### **使用例**
```python
# LLMとの対話例
ユーザー: "この README.md の構造が分かりにくいので、改善提案をGitHubのIssueとして投稿してください"

LLM: analyze_document_structure() で分析
     ↓
     generate_feedback_from_conversation() でフィードバック生成
     ↓
     create_github_issue() でIssue作成
     ↓
     "GitHub Issue #123 を作成しました: https://github.com/owner/repo/issues/123"
```

#### 実装の利点
1. **段階的拡張**: 既存基盤（230+テスト通過済み）をフル活用
2. **モジュラー設計**: 既存アーキテクチャとシームレス統合
3. **実装量削減**: 既存インフラ活用により効率的な開発

---

*最終更新: 2025年7月4日 - Forgejo対応とGitサービス抽象化完了*
`````