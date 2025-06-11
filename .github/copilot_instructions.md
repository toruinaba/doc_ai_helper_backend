# Copilot instruction
## Doc_ai_helper(backend)
### プロジェクト概要

このプロジェクトは、GitサービスでホストされたMarkdown/Quartoドキュメントを取得し、フロントエンドに提供するバックエンドAPIを実装します。名前は`doc_ai_helper_backend`です。

### 技術スタック

- **フレームワーク**: FastAPI
- **データベース**: SQLite（開発・本番共通）
- **ORM**: SQLAlchemy
- **マイグレーション**: Alembic
- **HTTP クライアント**: httpx
- **キャッシュ**: Redis または in-memory
- **テスト**: pytest
- **コンテナ化**: Docker
- **フォーマッター**: black

### ディレクトリ構成

```
doc_ai_helper_backend/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py       # ドキュメント取得API
│   │   │   ├── repositories.py    # リポジトリ管理API
│   │   │   ├── search.py          # 検索API
│   │   │   └── health.py          # ヘルスチェックAPI
│   │   ├── dependencies.py        # 依存関係注入
│   │   └── error_handlers.py      # エラーハンドラー
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # 設定管理
│   │   ├── security.py            # 認証・認可
│   │   └── exceptions.py          # カスタム例外
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py            # データベース接続
│   │   ├── models.py              # SQLAlchemyモデル
│   │   └── repositories/          # リポジトリパターン
│   │       ├── __init__.py
│   │       ├── base.py            # ベースリポジトリ
│   │       └── repository_repo.py # リポジトリ情報のCRUD
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py            # ドキュメントモデル
│   │   ├── repository.py          # リポジトリモデル
│   │   └── search.py              # 検索モデル
│   ├── services/
│   │   ├── __init__.py
│   │   ├── git/
│   │   │   ├── __init__.py
│   │   │   ├── base.py            # Git基本サービス
│   │   │   ├── github_service.py  # GitHub実装
│   │   │   ├── gitlab_service.py  # GitLab実装
│   │   │   └── factory.py         # Gitサービスファクトリ
│   │   ├── document_service.py    # ドキュメント処理
│   │   ├── cache_service.py       # キャッシュ
│   │   └── search_service.py      # 検索サービス
│   └── utils/
│       ├── __init__.py
│       ├── logging.py             # ロギング
│       └── helpers.py             # ヘルパー関数
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # テスト設定
│   ├── test_api/                  # APIテスト
│   │   ├── __init__.py
│   │   ├── test_documents.py
│   │   └── test_repositories.py
│   └── test_services/             # サービステスト
│       ├── __init__.py
│       ├── test_git_services.py
│       └── test_document_service.py
├── alembic/                       # マイグレーション
│   ├── versions/
│   ├── env.py
│   └── alembic.ini
├── scripts/
│   ├── create_db.py               # DB初期化
│   └── index_repositories.py      # 検索インデックス作成
├── data/                          # データディレクトリ
│   └── app.db                     # SQLiteデータベースファイル
├── main.py                        # アプリケーションエントリポイント
├── requirements.txt               # 依存関係
├── Dockerfile                     # Docker設定
├── docker-compose.yml             # Docker Compose設定
├── .env.example                   # 環境変数例
├── pyproject.toml                 # Black設定
└── README.md                      # プロジェクト説明
```

### ドキュメント方針

- **スタイル**: Googleスタイルのdocstringsを使用
- **簡潔さ**: 端的で明確な記述を心がける
- **必須要素**: 関数の説明、引数、戻り値、例外を必ず記述

**例**:
```python

def get_document(service: str, owner: str, repo: str, path: str, ref: str = "main") -> Dict[str, Any]:
    """指定されたリポジトリからドキュメントを取得する。

    Args:
        service: Gitサービスタイプ（github, gitlab等）
        owner: リポジトリオーナー
        repo: リポジトリ名
        path: ファイルパス
        ref: ブランチまたはタグ名。デフォルトは"main"

    Returns:
        ドキュメント情報を含む辞書

    Raises:
        FileNotFoundError: ドキュメントが見つからない場合
        GitServiceError: Gitサービスとの通信に問題がある場合
    """
    # 実装
```

### コード整形
- **フォーマッター**: Black
- **設定**: pyproject.tomlで設定
- **行の長さ**: 88文字（Blackのデフォルト）
- **適用方法**: コミット前に自動適用

```toml 

# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py39']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''
```

### 主要機能
#### 1. ドキュメント取得API
- 様々なGitサービス（GitHub, GitLab等）からのドキュメント取得
- Markdown/Quarto/HTMLファイルの取得と提供
- リポジトリ構造の取得

#### 2. リポジトリ管理API

リポジトリ情報のCRUD操作
リポジトリメタデータの管理

#### 3. 検索API

リポジトリ内のファイル検索
テキスト検索とメタデータ検索

#### 4. キャッシュ機能

頻繁にアクセスされるドキュメントのキャッシュ
リポジトリ構造のキャッシュ

### アーキテクチャ設計
#### レイヤードアーキテクチャ:

- API層（エンドポイント定義）
- サービス層（ビジネスロジック）
- リポジトリ層（データアクセス）
- モデル層（データモデル）

#### Gitサービス抽象化:

- 共通インターフェースを持つ抽象基底クラス
- サービス固有の実装クラス
- ファクトリパターンによるインスタンス生成
 
### コーディング規約
- PEP 8に準拠したコーディングスタイル
- 型ヒントの積極的な使用
- Googleスタイルのdocstringsで関数とクラスを文書化
- 例外処理は明示的に行い、適切なHTTPステータスコードを返す
- 非同期処理（async/await）を適切に活用
- Blackによる自動フォーマット

### API設計
#### ドキュメント取得API
```
GET /api/documents/{service}/{owner}/{repo}/{path:path}
```
- **service:** Gitサービスタイプ（github, gitlab等）
- **owner**: リポジトリオーナー
- **repo**: リポジトリ名
- **path**: ファイルパス
- **クエリパラメータ**:
  - ref: ブランチまたはタグ（デフォルト: main）

#### リポジトリ構造取得API
```
GET /api/structure/{service}/{owner}/{repo}
```
- **service**: Gitサービスタイプ
- **owner**: リポジトリオーナー
- **repo**: リポジトリ名
- **クエリパラメータ**:
  - ref: ブランチまたはタグ（デフォルト: main）

#### リポジトリ管理API
```
GET /api/repositories
POST /api/repositories
GET /api/repositories/{id}
PUT /api/repositories/{id}
DELETE /api/repositories/{id}
```

#### 検索API
```
POST /api/search/{service}/{owner}/{repo}
```

- **service**: Gitサービスタイプ
- **owner**: リポジトリオーナー
- **repo**: リポジトリ名
- **リクエストボディ**:
- query: 検索クエリ
- limit: 結果の最大数（デフォルト: 10）

### データモデル
#### Repository

```python 

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    service_type = Column(String, nullable=False)  # 'github', 'gitlab', etc.
    url = Column(String, nullable=False)
    branch = Column(String, default='main')
    access_token = Column(String, nullable=True)
    description = Column(String, nullable=True)
    is_public = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    metadata = Column(JSON, default={})
```

### SQLite設定
- データベースファイルは`data/app.db`に配置
- 開発環境と本番環境で同じSQLiteを使用
- データベース接続文字列: `sqlite:///./data/app.db`
- SQLiteの同時接続制限に注意（`check_same_thread=False`オプションを使用）
- 定期的なバックアップを実装

```python 

# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

## 開発手順
1. プロジェクト構造の作成
2. 基本的なFastAPIアプリケーションの設定
3. データベースモデルとマイグレーションの実装
4. Gitサービス抽象化レイヤーの実装
5. ドキュメント取得APIの実装
6. リポジトリ管理APIの実装
7. キャッシュ機能の実装
8. 検索APIの実装
9. テストの作成
10. Dockerファイルの作成

## 実装の注意点
- エラーハンドリングを適切に行い、わかりやすいエラーメッセージを返す
- レート制限などのGitサービス固有の制約に対応する
- 大きなファイルの処理を効率的に行う
- キャッシュ戦略を適切に実装し、パフォーマンスを最適化する
- セキュリティを考慮し、アクセストークンなどの機密情報を適切に管理する
- CORSを適切に設定し、フロントエンドからのアクセスを許可する
- SQLiteの制約（同時書き込み等）に注意し、適切に対応する

## テスト戦略
- ユニットテスト: サービスとリポジトリクラスの個別テスト
- 統合テスト: APIエンドポイントの動作確認
- モック: 外部サービス（GitHubなど）の呼び出しをモック化

## デプロイ
- Docker Composeを使用した開発環境の構築
- 本番環境用のDockerfile作成
- 環境変数による設定の外部化
- SQLiteデータベースファイルのボリュームマウント

```yaml 

# docker-compose.yml
version: '3'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data  # SQLiteデータベースのマウント
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
      - GITHUB_TOKEN=${GITHUB_TOKEN}
```

## 拡張性
- 新しいGitサービスを追加できるプラグイン的な設計
- 将来的な機能拡張（認証、高度な検索など）を考慮した設計

## 備考
- 日本語で回答すること