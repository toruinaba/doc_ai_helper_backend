# Git Services Legacy Tests

このディレクトリには、OptionA（1:1対応）原則に違反していたため移動されたレガシーテストファイルが含まれています。

## 移動されたファイル

### `test_factory_forgejo.py`
- **理由**: ファクトリーとForgejoサービスの複数機能をテスト（1:1対応違反）
- **新しい場所**: 
  - 一般的なファクトリーテスト → `../test_factory.py`
  - Forgejo固有のテスト → `../test_forgejo_service.py`

### `test_forgejo_api_integration.py`
- **理由**: 統合テストのため単体テストディレクトリに不適切
- **推奨場所**: `tests/integration/` ディレクトリ

### `github/` ディレクトリ
- **理由**: 対応するソースファイルが存在しない空のテストファイル
- **状況**: GitHubクライアントや認証マネージャーが独立したファイルとして実装されていない

## レガシーテストの処理

すべてのレガシーテストには `pytest.mark.skip` マーカーが追加されており、テスト実行時には自動的にスキップされます。

## 新しいテスト構造

現在のgitサービステストは以下の1:1対応に従っています：

```
services/git/                  → tests/unit/services/git/
├── base.py                   → test_base.py
├── factory.py                → test_factory.py
├── forgejo_service.py        → test_forgejo_service.py
├── github_service.py         → test_github_service.py
├── mock_data.py              → test_mock_data.py
└── mock_service.py           → test_mock_service.py
```

このレガシーディレクトリは将来的には削除される予定です。
