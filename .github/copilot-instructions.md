# Copilot Instructions for doc_ai_helper_backend

このドキュメントはGitHub Copilotが`doc_ai_helper_backend`プロジェクトをより良く理解し、適切な提案を行うための指示書です。

## プロジェクト概要

`doc_ai_helper_backend`は、GitサービスでホストされたMarkdownドキュメントを取得し、フロントエンドに提供するバックエンドAPIです。名前は`doc_ai_helper_backend`です。将来的にはQuartoドキュメントもサポートする予定です。

### 主なユースケース

1. **Markdownレンダリング**: フロントエンド側でレンダリングするためのMarkdownコンテンツの提供
2. **LLMコンテキスト**: フロントエンドからLLMに問い合わせるための元ファイル（.md）を提供
3. **HTMLドキュメント表示**: （将来機能）QuartoでビルドされたHTMLファイルをフロントエンドに提供

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
- バックエンド経由LLM API連携を優先的に実装

### 進行中の機能
- バックエンド経由LLM API連携の実装 [🔄優先実装項目]
- リポジトリ管理機能の実装
- 検索機能の実装
- APIの拡張（Quarto対応を見据えた機能）

### 未着手の機能
- データベース層の本格的な実装
- Quartoドキュメント対応の追加
- 本番環境準備

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
│   │       └── llm.py             # LLM API（計画中）
│   ├── core/                      # コア機能
│   │   ├── __init__.py
│   │   ├── config.py              # 設定管理
│   │   ├── exceptions.py          # カスタム例外
│   │   └── logging.py             # ロギング設定
│   ├── db/                        # データベース層
│   │   ├── __init__.py
│   │   └── repositories/          # リポジトリパターン
│   │       └── __pycache__/
│   ├── models/                    # データモデル
│   │   ├── __init__.py
│   │   ├── document.py            # ドキュメントモデル
│   │   ├── frontmatter.py         # フロントマターモデル
│   │   ├── link_info.py           # リンク情報モデル
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
│   │   └── git/                   # Gitサービス
│   │       ├── __init__.py
│   │       ├── base.py            # Git基本サービス
│   │       ├── factory.py         # Gitサービスファクトリ
│   │       ├── github_service.py  # GitHub実装
│   │       └── mock_service.py    # モック実装
│   └── utils/                     # ユーティリティ
│       ├── __init__.py
│       └── errors.py              # エラーユーティリティ
│   ├── services/llm/              # LLMサービス（計画中）
│   │   ├── __init__.py
│   │   ├── base.py                # LLM基本サービス
│   │   ├── factory.py             # LLMサービスファクトリ
│   │   ├── openai_service.py      # OpenAI実装
│   │   ├── anthropic_service.py   # Anthropic実装
│   │   └── mcp_adapter.py         # Model Context Protocol アダプター
├── tests/                         # テスト
│   ├── __init__.py
│   ├── conftest.py                # テスト設定
│   ├── api/                       # APIテスト
│   │   ├── __init__.py
│   │   ├── test_documents.py      # ドキュメントAPIテスト
│   │   └── test_health.py         # ヘルスチェックAPIテスト
│   ├── integration/               # 統合テスト
│   │   └── __init__.py
│   └── unit/                      # ユニットテスト
│       └── __init__.py
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
   - バックエンド経由LLM API連携を優先的に実装 [🔄優先実装項目]
   - リポジトリ管理機能の実装を進める
   - 検索機能の実装を進める
   - キャッシュ機能を強化する
   - Quarto対応は将来の拡張として位置付ける
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

LLM API連携は以下のモジュールで構成される予定です：

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
    _services: Dict[str, Type[LLMServiceBase]] = {
        "openai": OpenAIService,
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