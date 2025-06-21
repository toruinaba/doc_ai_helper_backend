# doc_ai_helper_backend

GitサービスでホストされたMarkdownドキュメントを取得し、フロントエンドに提供するバックエンドAPI（将来的にQuartoドキュメントもサポート予定）

## プロジェクト概要

このプロジェクトは、GitサービスでホストされたMarkdownドキュメントを取得し、フロントエンドに提供するバックエンドAPIを実装します。様々なGitサービス（GitHub, GitLabなど）からドキュメントを取得し、統一されたインターフェースを通じて提供します。将来的にはQuartoドキュメントプロジェクトもサポートする予定です。

### 主な用途

1. **Markdownレンダリング**: フロントエンド側でレンダリングするためのMarkdownコンテンツの提供
2. **LLMコンテキスト**: フロントエンドからLLMに問い合わせるための元ファイル（.md）を提供
3. **HTMLドキュメント表示**: （将来機能）Quartoでビルドされたリポジトリ内のHTMLファイルをフロントエンドに提供

### 実装アプローチ

段階的な実装アプローチを採用しています：

1. **Markdownサポート（フェーズ1）**: まずMarkdownファイルの取得・処理機能を完全に実装 [✅完了]
   - 基本的なMarkdownファイル取得とコンテンツ提供
   - フロントマター解析とメタデータ抽出
   - リンク情報の抽出と変換
   - 拡張ドキュメントメタデータの提供

2. **拡張機能（フェーズ2）**: その他の機能拡張 [🔄進行中]
   - バックエンド経由LLM API連携の実装 [🔄優先実装項目]
   - リポジトリ管理機能の実装
   - 検索機能の実装
   - キャッシュ機能の強化
   - パフォーマンスとセキュリティの最適化

3. **Quartoサポート（フェーズ3）**: Quartoドキュメントプロジェクトの特殊機能（ソースと出力ファイルの関連付けなど）を追加 [⏱️将来対応]

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

#### 実装状況

- ✅ LLMサービス基本アーキテクチャの設計と実装
- ✅ 抽象基底クラス（`LLMServiceBase`）の実装
- ✅ サービスファクトリー（`LLMServiceFactory`）の実装
- ✅ キャッシュサービス（`LLMCacheService`）の実装
- ✅ テンプレート管理システム（`PromptTemplateManager`）の実装
- ✅ モックサービス（`MockLLMService`）の実装
- ✅ OpenAIサービス（`OpenAIService`）の実装と単体テスト完了
- ✅ ストリーミングレスポンスのサポート（2025年6月完了）
- ✅ SSE（Server-Sent Events）エンドポイントの実装
- ✅ MCPアダプター（`MCPAdapter`）の基本実装
- 🔄 追加のLLMプロバイダー実装（Ollama、最優先）- 2025年7月中完了予定
- 🔄 MCPアダプターの拡張機能（後続フェーズ）

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

#### Ollamaサービス実装計画

Ollamaサービスの実装は、次の優先実装項目として位置づけられています。Ollamaは、軽量なローカルLLMサーバーであり、以下の特徴があります：

1. **ローカル実行**: ネットワーク遅延の少ない高速なレスポンス
2. **カスタムモデル**: 様々なオープンソースモデルのサポート
3. **リソース効率**: 限られたリソースでの効率的な実行

実装アプローチとしては、以下を予定しています：

1. **基本クラスの実装**
   - `OllamaService` クラスの作成（`LLMServiceBase` を継承）
   - Ollama APIとの通信実装（httpxを使用）
   - 基本的なクエリ機能の実装

2. **拡張機能**
   - ストリーミングサポートの実装（Ollamaのストリーミング機能を活用）
   - モデル管理機能の追加（利用可能なモデルの取得、モデル切り替え）
   - パラメーター最適化（温度、トップP、繰り返しペナルティなど）

3. **統合テスト**
   - 単体テストと統合テストの実装
   - エッジケースの検証（エラー処理、タイムアウト、大きなコンテキスト）
   - パフォーマンス測定

## 実装計画

### 現在の状況
- 環境構築完了
- エントリーポイント作成済み
- 基本的なAPIルーティングの設定完了
- ヘルスチェックAPIの実装完了
- ドキュメント取得APIの基本機能実装完了
- リポジトリ構造取得APIの基本機能実装完了
- Mockサービスの実装完了（開発・デモ・テスト用）
- LLMサービス層の基本実装完了（OpenAI、ストリーミングサポート含む）

**実装方針の明確化**:
- Markdownドキュメント対応を最優先で実装 [✅完了]
- LLM API連携の基本機能実装 [✅完了]
- Ollamaサービス実装を次の優先項目として推進 [🔄進行中]
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
   - LLMサービス実装（`services/llm/`）

3. **モックを用いたAPIの動作確認** [✅完了]
   - 実際のデータベースなしでサービス層をモックしてAPIの動作を確認
   - テスト駆動開発の手法を活用し、APIの期待する動作をテストで定義

4. **Markdownドキュメント対応の拡張** [✅完了]
   - Markdownファイルのフロントマター解析
   - 相対リンクの絶対パス変換機能
   - リンク情報の抽出と提供
   - ドキュメントメタデータの拡充
   
5. **LLM API連携の実装** [✅部分的に完了]
   - LLMサービス抽象化レイヤーの実装（`services/llm/base.py`） [✅完了]
   - プロバイダー固有の実装（OpenAI, モックサービス） [✅完了]
   - `LLMServiceFactory` の実装（`services/llm/factory.py`） [✅完了]
   - MCPアダプターの実装（`services/llm/mcp_adapter.py`） [✅基本実装完了]
   - LLM問い合わせ用エンドポイントの追加（`api/endpoints/llm.py`） [✅完了]
   - プロンプトテンプレート管理機能の実装 [✅完了]
   - レスポンスキャッシュの実装 [✅完了]
   - ストリーミングレスポンスのサポート [✅完了]
   - SSE（Server-Sent Events）エンドポイントの実装 [✅完了]
   - 追加のLLMプロバイダー実装（Ollama） [🔄進行中]
   - MCPアダプターの拡張機能 [🔄計画中]

6. **APIの拡張（Quarto対応を見据えた機能）** [🔄計画中]
   - Quartoプロジェクト検出機能の追加
   - ソースファイルと出力ファイルの関連付けエンドポイント
   - リンク変換オプションの追加
   - フロントマター解析とメタデータ提供機能の拡張
   - リポジトリ設定モデルとAPIの追加

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

9. **テストの充実** [🔄部分的に完了]
   - APIエンドポイントのテスト（ドキュメント取得、構造取得）[✅完了]
   - 統合テスト（実際のDBを使った全体的なフロー確認）
   - モックを使った外部サービスのテスト [✅完了]
   - Markdownドキュメント機能の拡張テスト [✅完了]
   - LLMサービスのテスト [✅完了]
   - 将来的なQuartoプロジェクト対応のテスト [⏱️未着手]

10. **リファクタリングとコード品質向上** [🔄部分的に完了]
    - モックサービスをテスト用からプロダクションコードへ移行 [✅完了]
    - APIパスの整理（`/contents`と`/structure`の明確な分離）[✅完了]
    - Markdownドキュメント処理の強化 [✅完了]
    - LLMサービスのエラーハンドリング強化 [✅完了]
    - ログ出力の強化 [🔄計画中]
    - パフォーマンス最適化 [🔄計画中]
    - セキュリティ対策の強化 [🔄計画中]

11. **本番環境準備** [未着手]
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

3. **LLM API連携** [✅部分的に完了]
   - 外部LLMサービス（OpenAI）との統合 [✅完了]
   - ストリーミングレスポンスのサポート [✅完了]
   - SSE（Server-Sent Events）によるリアルタイム応答 [✅完了]
   - Model Context Protocol (MCP) 対応 [✅基本実装完了]
   - ドキュメントコンテキストを活用したLLM問い合わせ [✅完了]
   - プロンプトテンプレート管理 [✅完了]
   - レスポンスキャッシュ [✅完了]
   - 追加のプロバイダー実装（Ollama） [🔄進行中]
   - MCPアダプターの拡張機能 [🔄計画中]

4. **検索API** [🔄実装予定]
   - リポジトリ内のファイル検索
   - テキスト検索とメタデータ検索
   - ドキュメントタイプや属性によるフィルタリング

5. **キャッシュ機能** [基本実装済み]
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
- `gitlab` - GitLab API経由でのドキュメント取得（計画中）

## テスト実行

```bash
pytest
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
```

## ユースケース

このAPIは以下の主要ユースケースをサポートします：

1. **Markdownコンテンツのレンダリング** [現在の主要ターゲット]
   - リポジトリからのMarkdownファイル取得
   - フロントエンドでのレンダリング処理
   - リンクの適切な変換と処理

2. **LLMコンテキストの提供** [現在の主要ターゲット]
   - Markdownファイルの取得
   - バックエンド経由のLLM問い合わせ（OpenAI、将来的にOllamaなど）
   - ストリーミングレスポンスによるリアルタイム表示
   - メタデータと併せたコンテキスト提供

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

4. **LLM連携** [✅部分的に完了]
   - バックエンド側: 
     - LLM APIへのプロキシ（OpenAI、将来的にOllama） [✅完了]
     - コンテキスト最適化とMCPサポート [✅基本実装完了]
     - ストリーミングレスポンスのサポート [✅完了]
     - SSE（Server-Sent Events）エンドポイント [✅完了]
     - テンプレート管理とレスポンスキャッシュ [✅完了]
   - フロントエンド側: 
     - ユーザーインターフェース [🔄進行中]
     - ストリーミングレスポンスの表示 [✅完了]
     - SSEクライアント実装 [✅完了]

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
