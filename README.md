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

1. **Markdownサポート（フェーズ1）**: まずMarkdownファイルの取得・処理機能を完全に実装
2. **拡張機能（フェーズ2）**: フロントマター解析、リンク変換などの機能を追加
3. **Quartoサポート（フェーズ3）**: Quartoドキュメントプロジェクトの特殊機能（ソースと出力ファイルの関連付けなど）を追加

このアプローチにより、基本機能を早期に提供しながら、徐々に高度な機能を追加していくことが可能になります。

## 実装計画

### 現在の状況
- 環境構築完了
- エントリーポイント作成済み
- 基本的なAPIルーティングの設定完了
- ヘルスチェックAPIの実装完了
- ドキュメント取得APIの基本機能実装完了
- リポジトリ構造取得APIの基本機能実装完了
- Mockサービスの実装完了（開発・デモ・テスト用）

**実装方針の明確化**:
- Markdownドキュメント対応を最優先で実装
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

4. **Markdownドキュメント対応の拡張** [🔄実装中]
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

6. **データベース層の実装** [🔄進行予定]
   - SQLAlchemyのBaseクラスとデータベース接続の設定（`db/database.py`）
   - モデル定義（`db/models.py`）
   - リポジトリパターンによるデータアクセス層の実装（`db/repositories/`）
   - Alembicによるマイグレーション設定
   - リポジトリ設定・マッピング機能の追加

7. **Quartoドキュメント対応の追加** [⏱️未着手]
   - Quartoプロジェクト設定（_quarto.yml）の解析
   - ソースファイル(.qmd)と出力ファイル(.html)の関連付け
   - リポジトリ構造分析とパスマッピング
   - サイト構造情報の提供

8. **テストの充実** [🔄部分的に完了]
   - APIエンドポイントのテスト（ドキュメント取得、構造取得）[✅完了]
   - 統合テスト（実際のDBを使った全体的なフロー確認）
   - モックを使った外部サービスのテスト [✅完了]
   - Markdownドキュメント機能の拡張テスト [🔄実装予定]
   - 将来的なQuartoプロジェクト対応のテスト [⏱️未着手]

9. **リファクタリングとコード品質向上** [🔄部分的に完了]
   - モックサービスをテスト用からプロダクションコードへ移行 [✅完了]
   - APIパスの整理（`/contents`と`/structure`の明確な分離）[✅完了]
   - Markdownドキュメント処理の強化 [🔄実装中]
   - ログ出力の強化 [🔄計画中]
   - エラーハンドリングの改善 [🔄計画中]
   - パフォーマンス最適化 [🔄計画中]
   - セキュリティ対策の強化 [🔄計画中]

10. **本番環境準備** [未着手]
    - Docker Composeの調整
    - 環境変数の設定
    - 監視やバックアップなどの運用機能の実装

## 主要機能

1. **ドキュメント取得API** [✅基本実装済み]
   - 様々なGitサービス（GitHub, Mock等）からのドキュメント取得
   - Markdownファイルの取得と提供
   - リポジトリ構造の取得
   - ドキュメント内リンクの解析と変換（実装中）
   - フロントマターの解析とメタデータ提供（実装中）
   - HTMLファイルの取得と提供（基本実装済み）
   - Quarto/HTMLファイルのソースと出力ファイルの関連付け（将来対応）

2. **リポジトリ管理API** [🔄実装予定]
   - リポジトリ情報のCRUD操作
   - リポジトリメタデータの管理
   - Markdownドキュメント設定の管理
   - 将来的にはQuartoドキュメント設定（パスマッピング、出力ディレクトリなど）の管理
   - リポジトリタイプ（Markdown/Quarto）の検出と管理

3. **検索API** [🔄実装予定]
   - リポジトリ内のファイル検索
   - テキスト検索とメタデータ検索
   - ドキュメントタイプや属性によるフィルタリング

4. **キャッシュ機能** [基本実装済み]
   - 頻繁にアクセスされるドキュメントのキャッシュ
   - リポジトリ構造のキャッシュ
   - 設定情報のキャッシュ

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
    - `transform_links`: リンクを変換するかどうか（デフォルト: true、実装中）
    - `include_source`: HTMLの場合、ソースファイル情報も含めるか（デフォルト: false、将来機能）
    - `include_rendered`: Markdown/Quartoの場合、レンダリング済みファイル情報も含めるか（デフォルト: false、将来機能）

- `GET /api/v1/documents/structure/{service}/{owner}/{repo}` - リポジトリ構造の取得
  - クエリパラメータ:
    - `ref`: ブランチまたはタグ名（デフォルト: main）
    - `path`: フィルタリングするパス（デフォルト: ""）
    - `include_mappings`: ソース・出力ファイルのマッピングを含めるか（デフォルト: false、将来機能）

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
    # 実装中/計画中の拡張フィールド
    # links: List[LinkInfo]       # リンク情報（実装中）
    # transformed_content: Optional[str]  # リンク変換済みコンテンツ（実装中）
    # relations: Optional[DocumentRelations]  # 関連ドキュメント情報（将来実装予定）
```

## ユースケース

このAPIは以下の主要ユースケースをサポートします：

1. **Markdownコンテンツのレンダリング** [現在の主要ターゲット]
   - リポジトリからのMarkdownファイル取得
   - フロントエンドでのレンダリング処理
   - リンクの適切な変換と処理

2. **LLMコンテキストの提供** [現在の主要ターゲット]
   - Markdownファイルの取得
   - フロントエンド側からLLMへの問い合わせ用コンテキスト提供
   - メタデータと併せたコンテンツ提供

3. **HTMLドキュメントの表示** [将来的に拡張]
   - QuartoでビルドされたリポジトリからのHTML取得
   - フロントエンドでの直接表示
   - 対応するソースファイル（.qmd）の参照

## フロントエンド連携

バックエンドAPIはフロントエンドと以下のように連携します：

1. **Markdownレンダリング連携** [現在の主要ターゲット]
   - バックエンド側: Markdownコンテンツの提供、メタデータの解析と提供
   - フロントエンド側: Markdownのレンダリング、メタデータの表示

2. **リンク処理** [実装中]
   - バックエンド側: 相対リンクのAPI URL変換、リンク情報の提供
   - フロントエンド側: 内部ナビゲーションへの変換、リンクの適切な表示

3. **メタデータ活用** [実装中]
   - バックエンド側: フロントマター解析、メタデータ提供
   - フロントエンド側: タイトル、説明、タグなどの表示

4. **ファイル関連付け** [将来的に拡張]
   - バックエンド側: ソースファイルと出力ファイルのマッピング提供
   - フロントエンド側: ユーザーへのソース/出力切り替えUI提供
