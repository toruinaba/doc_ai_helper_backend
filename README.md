# doc_ai_helper_backend

GitサービスでホストされたMarkdown/Quartoドキュメントを取得し、フロントエンドに提供するバックエンドAPI

## プロジェクト概要

このプロジェクトは、GitサービスでホストされたMarkdown/Quartoドキュメントを取得し、フロントエンドに提供するバックエンドAPIを実装します。様々なGitサービス（GitHub, GitLabなど）からドキュメントを取得し、統一されたインターフェースを通じて提供します。

## 実装計画

### 現在の状況
- 環境構築完了
- エントリーポイント作成済み
- 基本的なAPIルーティングの設定完了
- ヘルスチェックAPIの実装完了
- データベース層はモックで実装予定（APIの仕様が定まった段階でモデル定義を行う）

### 開発ステップ
1. **API定義の完了** [進行中]
   - RESTful APIのエンドポイント定義
   - リクエスト/レスポンスのPydanticモデル定義
   - エラーハンドリングの実装

2. **サービス層の実装**
   - 抽象Gitサービスの実装（`services/git/base.py`）
   - GitHub実装（`services/git/github_service.py`）
   - GitLab実装（`services/git/gitlab_service.py`）
   - ドキュメント処理サービス（`services/document_service.py`）
   - キャッシュサービス（`services/cache_service.py`）

3. **モックを用いたAPIの動作確認**
   - 実際のデータベースなしでサービス層をモックしてAPIの動作を確認
   - テスト駆動開発の手法を活用し、APIの期待する動作をテストで定義

4. **データベース層の実装**
   - SQLAlchemyのBaseクラスとデータベース接続の設定（`db/database.py`）
   - モデル定義（`db/models.py`）
   - リポジトリパターンによるデータアクセス層の実装（`db/repositories/`）
   - Alembicによるマイグレーション設定

5. **テストの充実**
   - ユニットテスト（サービス層、リポジトリ層の個別テスト）
   - 統合テスト（実際のDBを使った全体的なフロー確認）
   - モックを使った外部サービスのテスト

6. **リファクタリングとコード品質向上**
   - ログ出力の強化
   - エラーハンドリングの改善
   - パフォーマンス最適化
   - セキュリティ対策の強化

7. **本番環境準備**
   - Docker Composeの調整
   - 環境変数の設定
   - 監視やバックアップなどの運用機能の実装

## 主要機能

1. **ドキュメント取得API**
   - 様々なGitサービス（GitHub, GitLab等）からのドキュメント取得
   - Markdown/Quarto/HTMLファイルの取得と提供
   - リポジトリ構造の取得

2. **リポジトリ管理API**
   - リポジトリ情報のCRUD操作
   - リポジトリメタデータの管理

3. **検索API**
   - リポジトリ内のファイル検索
   - テキスト検索とメタデータ検索

4. **キャッシュ機能**
   - 頻繁にアクセスされるドキュメントのキャッシュ
   - リポジトリ構造のキャッシュ

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
