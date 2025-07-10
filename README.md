# doc_ai_helper_backend

GitサービスでホストされたMarkdownドキュメントを取得し、フロントエンドに提供するバックエンドAPI。LLM統合機能とMCP（Model Context Protocol）対応を含む。

## プロジェクト概要

このプロジェクトは、GitサービスでホストされたMarkdownドキュメントを取得し、フロントエンドに提供するバックエンドAPIです。様々なGitサービス（GitHub, GitLabなど）からドキュメントを取得し、統一されたインターフェースを通じて提供し、LLM（Large Language Model）との統合機能を提供します。

**現在の実装状況**: Markdownドキュメント対応とLLM統合機能が完了済み。将来的にはQuartoドキュメントプロジェクトもサポート予定。

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

### 主なメリット

1. **セキュリティの強化**
   - API キーをフロントエンドに露出させない
   - バックエンドでユーザー認証と権限チェックを一元管理
   - センシティブ情報のフィルタリング

2. **抽象化と柔軟性**
   - 複数LLMプロバイダ（OpenAI, Anthropic, Gemini等）を抽象化し、切り替え可能に
   - プロンプトテンプレートの一元管理
   - LLM APIの変更にフロントエンド側の変更なしで対応可能

3. **パフォーマンスと機能最適化**
   - レスポンスのキャッシュによるAPI利用コスト削減
   - コンテキスト最適化
   - レート制限の一元管理

4. **Model Context Protocol (MCP) との連携**
   - 異なるLLMプロバイダー間でのコンテキスト管理標準化
   - Markdownドキュメントから抽出した情報を構造化された形式でLLMに提供
   - 既存の処理パイプライン（MarkdownProcessor, LinkTransformer）の活用

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
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
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

## MCP（Model Context Protocol）統合機能

プロジェクトでは、Model Context Protocol（MCP）の完全な実装が完了しています。MCPは、LLMアプリケーションが外部データソースやツールとやり取りするための標準化されたプロトコルです。

### 実装済みMCP機能

#### 1. GitHubツール統合
- **リポジトリ操作**: GitHub APIを通じたリポジトリの情報取得、ファイル内容の取得
- **セキュアアクセス**: GitHubトークンを使用した認証機能
- **日本語対応**: エラーメッセージやレスポンスの日本語ローカライゼーション
- **コンテンツ処理**: Markdownファイルの取得と処理機能

#### 2. MCPアダプター機能
- **コンテキスト変換**: ドキュメントデータをMCP標準形式に変換
- **トークン最適化**: LLMのトークン制限に応じたコンテキストの最適化
- **構造化データ**: メタデータ、リンク情報、フロントマターの構造化

#### 3. ツール関数の実装
以下のMCPツール関数が完全に実装され、テスト済みです：

```python
# 実装済みのGitHubツール関数
- get_repository_info: リポジトリの基本情報を取得
- get_file_content: ファイル内容を取得
- list_repository_files: リポジトリのファイル一覧を取得
- search_repository_content: リポジトリ内のコンテンツ検索
- get_repository_structure: リポジトリの構造を取得
```

#### 4. エラーハンドリングと国際化
- **包括的なエラー処理**: GitHub API、ネットワーク、認証エラーに対する適切な処理
- **日本語エラーメッセージ**: 開発者向けの分かりやすい日本語エラーメッセージ
- **ログ出力**: デバッグとトラブルシューティングのための詳細なログ

### テスト状況
- **単体テスト**: 全329テストが通過、包括的なカバレッジを実現
- **統合テスト**: GitHubツールとMCPアダプターの完全な統合テスト
- **エラーケーステスト**: 様々なエラー条件下での動作確認

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
- Forgejo対応とGitホストサービス抽象化の強化 [✅完了]
- HTML対応機能（Quarto準備段階）の実装 [🔄次期優先]
- データベース層はモックで実装（APIの仕様が定まりつつある段階）
- Quarto対応は将来の拡張として位置付け

**テスト戦略**:
- 単体テストとAPIテスト: Mockサービスを活用した外部依存なしテスト
- 統合テスト: 実際の外部API（GitHub、OpenAI等）を使用したテスト
- 明確な分離により、開発効率と信頼性を両立
- MCPサーバー・ツール・Function Callingのユニットテスト（29件全てPASSED）

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
   - GitHubツール統合機能の実装 [✅完了]
   - セキュアなGitHubアクセス機能の実装 [✅完了]
   - 包括的なテストスイートの実装 [✅完了]
   - 追加のLLMプロバイダー実装（Ollama等） [⏱️将来実装予定]
   - MCPアダプターの拡張機能 [⏱️将来実装予定]

6. **Gitサービス抽象化の強化とForgejo対応** [🔄次期優先実装]
   - Gitサービス抽象化レイヤーの強化（`services/git/base.py`）
   - Forgejoサービスの実装（`services/git/forgejo_service.py`）
   - 認証方式の統一化と複数ホスト対応
   - サービス自動検出機能の追加

7. **HTML対応機能（Quarto準備段階）** [🔄次期優先実装]
   - HTMLプロセッサーの実装（`services/document_processors/html_processor.py`）
   - ファイル関連付け機能の基本実装
   - HTMLメタデータ抽出とリンク解析機能
   - API拡張（HTML取得、関連ファイル情報の提供）

8. **APIの拡張（Quarto対応を見据えた機能）** [🔄計画中]
   - Quartoプロジェクト検出機能の追加
   - ソースファイルと出力ファイルの関連付けエンドポイント
   - リンク変換オプションの追加
   - フロントマター解析とメタデータ提供機能の拡張
   - リポジトリ設定モデルとAPIの追加

9. **データベース層の実装** [🔄進行予定]
   - SQLAlchemyのBaseクラスとデータベース接続の設定（`db/database.py`）
   - モデル定義（`db/models.py`）
   - リポジトリパターンによるデータアクセス層の実装（`db/repositories/`）
   - Alembicによるマイグレーション設定
   - リポジトリ設定・マッピング機能の追加

10. **Quartoドキュメント対応の追加** [⏱️未着手]
   - Quartoプロジェクト設定（_quarto.yml）の解析
   - ソースファイル(.qmd)と出力ファイル(.html)の関連付け
   - リポジトリ構造分析とパスマッピング
   - サイト構造情報の提供

11. **テストの充実** [✅大部分完了]
   - APIエンドポイントのテスト（ドキュメント取得、構造取得）[✅完了]
   - LLMサービスの包括的なテスト [✅完了]
   - MCPアダプターとGitHubツールのテスト [✅完了]
   - ストリーミング機能のテスト [✅完了]
   - モックを使った外部サービスのテスト [✅完了]
   - Markdownドキュメント機能の拡張テスト [✅完了]
   - エラーハンドリングとエッジケースのテスト [✅完了]
11. **テストの充実** [✅大部分完了]
   - APIエンドポイントのテスト（ドキュメント取得、構造取得）[✅完了]
   - LLMサービスの包括的なテスト [✅完了]
   - MCPアダプターとGitHubツールのテスト [✅完了]
   - ストリーミング機能のテスト [✅完了]
   - モックを使った外部サービスのテスト [✅完了]
   - Markdownドキュメント機能の拡張テスト [✅完了]
   - エラーハンドリングとエッジケースのテスト [✅完了]
   - Forgejoサービスのテスト [🔄次期実装予定]
   - HTML処理機能のテスト [🔄次期実装予定]
   - 統合テスト（実際のDBを使った全体的なフロー確認） [🔄将来実装予定]
   - 将来的なQuartoプロジェクト対応のテスト [⏱️未着手]

12. **リファクタリングとコード品質向上** [✅大部分完了]
    - モックサービスをテスト用からプロダクションコードへ移行 [✅完了]
    - APIパスの整理（`/contents`と`/structure`の明確な分離）[✅完了]
    - Markdownドキュメント処理の強化 [✅完了]
    - LLMサービスのエラーハンドリング強化 [✅完了]
    - 包括的なテストカバレッジの実装 [✅完了]
    - コードの抽象化とモジュール化の改善 [✅完了]
    - ログ出力の強化 [🔄計画中]
    - パフォーマンス最適化 [🔄計画中]
    - セキュリティ対策の強化 [🔄計画中]

13. **本番環境準備** [未着手]
    - Docker Composeの調整
    - 環境変数の設定
    - 監視やバックアップなどの運用機能の実装

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
   - GitHubツール統合機能 [✅完了]
   - セキュアなGitHubアクセス機能 [✅完了]
   - 包括的なテストスイート [✅完了]
   - 追加のプロバイダー実装（Ollama等） [⏱️将来実装予定]
   - MCPアダプターの拡張機能 [⏱️将来実装予定]

4. **検索API** [🔄実装予定]
   - リポジトリ内のファイル検索
   - テキスト検索とメタデータ検索
   - ドキュメントタイプや属性によるフィルタリング

5. **キャッシュ機能** [✅完了]
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

## セットアップ手順

### 開発環境

1. リポジトリのクローン
```bash
git clone [リポジトリURL]
cd doc_ai_helper_backend
```

2. 仮想環境の作成と有効化
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows PowerShell
```

3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

4. 環境変数の設定
```bash
cp .env.example .env
# .envファイルを編集して必要な環境変数を設定
```

5. アプリケーションの実行
```bash
uvicorn doc_ai_helper_backend.main:app --reload
```

### Docker環境

```bash
docker-compose up -d
```

## APIドキュメント

アプリケーション実行後、以下のURLでSwagger UIベースのAPIドキュメントにアクセスできます。

```
http://localhost:8000/docs
```

## API概要

### ドキュメント関連エンドポイント
- `GET /api/v1/documents/contents/{service}/{owner}/{repo}/{path}` - 特定ドキュメントの取得
  - クエリパラメータ:
    - `ref`: ブランチまたはタグ名（デフォルト: main）
    - `transform_links`: リンクを変換するかどうか（デフォルト: true）
    - `base_url`: リンク変換に使用するベースURL（オプション）
    - `include_source`: HTMLの場合、ソースファイル情報も含めるか（デフォルト: false、将来機能）
    - `include_rendered`: Markdown/Quartoの場合、レンダリング済みファイル情報も含めるか（デフォルト: false、将来機能）

- `GET /api/v1/documents/structure/{service}/{owner}/{repo}` - リポジトリ構造の取得
  - クエリパラメータ:
    - `ref`: ブランチまたはタグ名（デフォルト: main）
    - `path`: フィルタリングするパス（デフォルト: ""）
    - `include_mappings`: ソース・出力ファイルのマッピングを含めるか（デフォルト: false、将来機能）

### LLM連携エンドポイント
- `POST /api/v1/llm/query` - LLMへの問い合わせ
  - ボディパラメータ:
    - `prompt`: ユーザーからのプロンプト
    - `documents`: コンテキストとして使用するドキュメント情報
    - `options`: LLM固有のオプション（モデル、温度等）
    - `provider`: 使用するLLMプロバイダー（デフォルト: システム設定値）

- `POST /api/v1/llm/stream` - ストリーミングモードでLLMからのレスポンスを取得
  - ボディパラメータ: （`/query`と同じ）
  - レスポンス: SSE（Server-Sent Events）形式のストリーミングレスポンス
  - 形式: `data: {"text": "チャンクテキスト"}\n\n`
  - 完了時: `data: {"done": true}\n\n`
  - エラー時: `data: {"error": "エラーメッセージ"}\n\n`

- `GET /api/v1/llm/providers` - 利用可能なLLMプロバイダー一覧の取得
- `GET /api/v1/llm/capabilities` - 選択されたプロバイダーの機能情報取得
- `GET /api/v1/llm/templates` - プロンプトテンプレート一覧の取得
- `POST /api/v1/llm/format-prompt` - プロンプトテンプレートのフォーマット

### 会話履歴管理エンドポイント
- `POST /api/v1/llm/conversations` - 新しい会話セッションの作成
- `GET /api/v1/llm/conversations/{conversation_id}` - 会話履歴の取得
- `POST /api/v1/llm/conversations/{conversation_id}/messages` - 会話への新しいメッセージ追加
- `DELETE /api/v1/llm/conversations/{conversation_id}` - 会話セッションの削除
- `GET /api/v1/llm/conversations` - 会話セッション一覧の取得

### リポジトリ管理エンドポイント（計画中）
- `GET /api/v1/repositories` - リポジトリ一覧の取得
- `POST /api/v1/repositories` - リポジトリの登録
- `GET /api/v1/repositories/{id}` - リポジトリ詳細の取得
- `PUT /api/v1/repositories/{id}` - リポジトリの更新
- `DELETE /api/v1/repositories/{id}` - リポジトリの削除
- `PUT /api/v1/repositories/{id}/settings` - リポジトリ設定の更新（Markdown設定と将来的なQuarto設定）

### サポートされているサービス
- `github` - GitHub API経由でのドキュメント取得
- `mock` - モックデータを返すテスト・デモ用サービス
- `forgejo` - Forgejo API経由でのドキュメント取得（次期実装予定）
- `gitlab` - GitLab API経由でのドキュメント取得（計画中）

## テスト実行

### 基本的なテスト実行

```bash
# 全テスト実行
pytest

# 層別テスト実行
pytest tests/unit/          # 単体テスト
pytest tests/integration/   # 統合テスト  
pytest tests/e2e/           # E2Eテスト
```

### 層別テスト実行

```bash
# Git層統合テスト
pytest tests/integration/git/ -v

# LLM層統合テスト
pytest tests/integration/llm/ -v

# MCP層統合テスト
pytest tests/integration/mcp/ -v
```

### マーカー別テスト実行

```bash
# Git関連テスト
pytest -m git -v

# LLM関連テスト
pytest -m llm -v

# MCP関連テスト
pytest -m mcp -v

# ストリーミング機能テスト
pytest -m streaming -v

# 外部API不要テスト（単体テスト）
pytest -m "not (github or forgejo or openai)" -v
```

### テスト戦略

このプロジェクトでは、3層のテスト戦略を採用しています：

1. **単体テスト** (`tests/unit/`)
   - 外部依存関係を排除したテスト
   - Mockサービスを活用した高速テスト
   - 開発中の継続的な実行に適している

2. **統合テスト** (`tests/integration/`)
   - 実際の外部API（GitHub、Forgejo、OpenAI等）を使用
   - サービス層の実際の動作の検証
   - 環境変数による設定が必要

3. **E2Eテスト** (`tests/e2e/`)
   - API経由のエンドツーエンド動作確認
   - ワークフローシナリオのテスト
   - 実際のユーザー利用シナリオの検証

#### 統合テスト実行の要件

統合テストの実行には以下の環境変数が必要です：

```bash
# GitHub統合テスト
export GITHUB_TOKEN="your_github_token"

# OpenAI統合テスト  
export OPENAI_API_KEY="your_openai_api_key"

# Forgejo統合テスト（オプション）
export FORGEJO_BASE_URL="https://your-forgejo-instance.com"
export FORGEJO_TOKEN="your_forgejo_token"
# または
export FORGEJO_USERNAME="your_username"
export FORGEJO_PASSWORD="your_password"
```

## ブランチ戦略

このプロジェクトでは以下のシンプルなブランチ戦略を採用しています：

### メインブランチ

- **main**: 本番環境にデプロイ可能な安定版コード

### 開発ブランチ

- **feature/\***: 新機能の開発用（例: `feature/github-integration`）
  - mainから分岐し、mainにマージ
  - 命名規則: `feature/[機能名]`

- **fix/\***: バグ修正用（例: `fix/auth-error`）
  - mainから分岐し、mainにマージ
  - 命名規則: `fix/[バグ内容]`

### ワークフロー

1. 新機能開発やバグ修正は常に最新の `main` から新しいブランチを作成
2. 作業完了後、プルリクエストを作成
3. コードレビュー、自動テスト通過後に `main` にマージ
4. `main` へのマージ後、必要に応じてデプロイを実施

このシンプルなワークフローにより、開発の複雑さを減らしながらも、コードの品質を保つことができます。

## ライセンス

[ライセンス情報]

## データモデル設計

システムは以下の主要データモデルに基づいて構築されています。

### リポジトリモデル

```python
# リポジトリ基本モデル
class RepositoryBase(BaseModel):
    name: str                   # リポジトリ名
    owner: str                  # リポジトリオーナー
    service_type: GitServiceType  # Gitサービスタイプ（github, gitlab等）
    url: HttpUrl                # リポジトリURL
    branch: str = "main"        # デフォルトブランチ
    description: Optional[str]  # リポジトリ説明
    is_public: bool = True      # 公開リポジトリかどうか
    settings: Optional[RepositorySettings]  # ドキュメント設定（計画中）
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
    index_file: str = "index.html"  # インデックスファイル
```

### ドキュメントモデル

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
    # relations: Optional[DocumentRelations]  # 関連ドキュメント情報（将来実装予定）
```

### LLMデータモデル

```python
# LLMクエリリクエストモデル
class LLMQueryRequest(BaseModel):
    prompt: str                 # ユーザープロンプト
    documents: Optional[List[DocumentReference]] = None  # コンテキストとして使用するドキュメント
    options: Optional[Dict[str, Any]] = None  # LLM固有のオプション
    provider: Optional[str] = None  # LLMプロバイダー

# LLMレスポンスモデル
class LLMResponse(BaseModel):
    text: str                   # LLMからのレスポンステキスト
    usage: LLMUsage             # トークン使用量
    model: str                  # 使用されたモデル
    provider: str               # LLMプロバイダー
    processed_at: datetime      # 処理時間
    elapsed_time: float         # 処理に要した時間（秒）
    cached: bool = False        # キャッシュからの応答かどうか
    raw_response: Optional[Any] = None  # 生のレスポンスデータ（デバッグ用）

# トークン使用量モデル
class LLMUsage(BaseModel):
    prompt_tokens: int          # プロンプトのトークン数
    completion_tokens: int      # 応答のトークン数
    total_tokens: int           # 合計トークン数
    
# ドキュメント参照モデル
class DocumentReference(BaseModel):
    service: str                # Gitサービス
    owner: str                  # リポジトリオーナー
    repository: str             # リポジトリ名
    path: str                   # ドキュメントパス
    ref: Optional[str] = None   # ブランチまたはタグ
    content: Optional[str] = None  # 直接コンテンツを提供する場合

# 会話履歴関連モデル
class ConversationMessage(BaseModel):
    role: str                   # メッセージの役割（user, assistant, system）
    content: str                # メッセージ内容
    timestamp: datetime         # メッセージ作成時刻
    metadata: Optional[Dict[str, Any]] = None  # 追加メタデータ

class Conversation(BaseModel):
    id: str                     # 会話ID
    title: Optional[str] = None # 会話タイトル
    created_at: datetime        # 作成時刻
    updated_at: datetime        # 最終更新時刻
    messages: List[ConversationMessage]  # メッセージ履歴
    metadata: Optional[Dict[str, Any]] = None  # 追加メタデータ

class ConversationCreateRequest(BaseModel):
    title: Optional[str] = None # 初期タイトル
    initial_message: Optional[str] = None  # 初期メッセージ

class ConversationResponse(BaseModel):
    conversation: Conversation  # 会話データ
    message_count: int          # メッセージ数
    last_activity: datetime     # 最終活動時刻
```

## ユースケース

このAPIは以下の主要ユースケースをサポートします：

1. **Markdownコンテンツのレンダリング** [現在の主要ターゲット]
   - リポジトリからのMarkdownファイル取得
   - フロントエンドでのレンダリング処理
   - リンクの適切な変換と処理

2. **LLMコンテキストの提供** [現在の主要ターゲット]
   - Markdownファイルの取得
   - バックエンド経由のLLM問い合わせ（OpenAI）
   - ストリーミングレスポンスによるリアルタイム表示
   - メタデータと併せたコンテキスト提供
   - 会話履歴管理による継続的な対話サポート

3. **HTMLドキュメントの表示** [将来的に拡張]
   - QuartoでビルドされたリポジトリからのHTML取得
   - フロントエンドでの直接表示
   - 対応するソースファイル（.qmd）の参照

## フロントエンド連携

バックエンドAPIはフロントエンドと以下のように連携します：

1. **Markdownレンダリング連携** [現在の主要ターゲット]
   - バックエンド側: Markdownコンテンツの提供、メタデータの解析と提供
   - フロントエンド側: Markdownのレンダリング、メタデータの表示

2. **リンク処理** [✅完了]
   - バックエンド側: 相対リンクのAPI URL変換、リンク情報の提供
   - フロントエンド側: 内部ナビゲーションへの変換、リンクの適切な表示

3. **メタデータ活用** [✅完了]
   - バックエンド側: フロントマター解析、メタデータ提供
   - フロントエンド側: タイトル、説明、タグなどの表示

4. **LLM連携** [✅完了]
   - バックエンド側: 
     - LLM APIへのプロキシ（OpenAI） [✅完了]
     - コンテキスト最適化とMCPサポート [✅基本実装完了]
     - ストリーミングレスポンスのサポート [✅完了]
     - SSE（Server-Sent Events）エンドポイント [✅完了]
     - テンプレート管理とレスポンスキャッシュ [✅完了]
     - 会話履歴管理機能 [✅完了]
   - フロントエンド側: 
     - ユーザーインターフェース [🔄進行中]
     - ストリーミングレスポンスの表示 [✅完了]
     - SSEクライアント実装 [✅完了]
     - 会話履歴の表示と管理 [🔄進行中]

5. **ファイル関連付け** [将来的に拡張]
   - バックエンド側: ソースファイルと出力ファイルのマッピング提供
   - フロントエンド側: ユーザーへのソース/出力切り替えUI提供

## Markdownドキュメント処理機能

Markdownドキュメント処理機能は完全に実装されています。以下の機能を提供します：

### フロントマター解析
- Markdownファイルからのフロントマター（YAML/JSON形式）の抽出
- タイトル、説明、著者、日付、タグなどの標準メタデータの解析
- カスタムフロントマターデータのサポート

### リンク変換と解析
- Markdownファイル内のリンク（通常のリンクと画像リンク）の検出
- 相対リンクの絶対パスへの変換
- 外部リンクと内部リンクの区別
- リンク情報（テキスト、URL、位置情報など）の抽出と提供

### 拡張メタデータの提供
- 基本的なファイル情報（ファイル名、拡張子、パスなど）
- フロントマターから抽出したメタデータ
- ドキュメント内のリンク情報
- Git情報（コミットID、最終更新日など）

### 文書処理アーキテクチャ
処理は以下のモジュールで構成されています：
- `MarkdownProcessor`: Markdownファイルの処理を担当
- `LinkTransformer`: リンクの検出と変換を担当
- `parse_frontmatter`: フロントマーターの解析を担当
- `DocumentProcessorFactory`: ドキュメントタイプに応じたプロセッサーを生成

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

## 📋 次期実装計画（フェーズ3: GitHub MCP統合）

### 🎯 実装目標
MCP経由でのGitHub Issue/PR作成機能を実装し、LLMとの対話からダイレクトにGitHubへフィードバック投稿できる仕組みを構築します。

### 📅 実装スケジュール（2週間）
- **Week 1**: GitHub APIクライアント基盤 + MCPツール実装
- **Week 2**: Function Calling統合 + テスト実装 + 最適化

### 🔧 実装予定機能

#### **GitHub MCPツール**
```python
# 実装予定のMCPツール
async def create_github_issue(
    repository: str,        # "owner/repo" 形式
    title: str,            # Issue タイトル
    description: str,      # Issue 本文
    labels: List[str] = None,      # ラベル
    assignees: List[str] = None    # アサイニー
) -> Dict[str, Any]:
    """GitHub Issue を作成し、結果を返す"""

async def create_github_pr(
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

### 🎯 実装の利点
1. **最小実装**: 既存MCP基盤（29テスト通過済み）をフル活用
2. **即座に動作**: フロントエンド不要でLLM対話テスト可能
3. **段階的拡張**: 安定した基盤から順次機能追加
4. **実装量削減**: 既存インフラ活用により効率的な開発

---

*最終更新: 2025年7月4日 - Forgejo対応とGitサービス抽象化完了*
