# README改善フロー E2Eテスト実行ガイド

README改善フローを含むLLM経由GitHub MCP E2Eテストの実行方法を説明します。

## 🎯 README改善フローとは

このE2Eテストは、以下のフローを自動化してテストします：

1. **READMEコンテンツの分析**: LLMがサンプルREADMEファイルの内容を解析
2. **改善点の特定**: 新規開発者が理解しにくい部分を特定
3. **改善提案の生成**: 具体的で実用的な改善提案を作成
4. **GitHub Issue作成**: MCP経由でGitHub Issueとして改善提案を投稿

## 📋 含まれるテスト

### 1. GitHub権限確認テスト
- GitHub APIトークンの権限を確認
- Issue/PR作成権限の検証
- LLM経由での権限チェック

### 2. 📖 README改善フローE2Eテスト (メイン機能)
- サンプルREADMEコンテンツの分析
- LLMによる改善点の特定
- 新規開発者向けの親切な改善提案
- GitHub Issueとしての具体的な提案投稿

### 3. 基本GitHub Issue作成テスト
- シンプルなIssue作成の動作確認
- LLM Function Callingの基本検証

## 🚀 実行方法

### 前提条件

1. **環境変数の設定**
   ```powershell
   $env:OPENAI_API_KEY="sk-your-openai-api-key"
   $env:GITHUB_TOKEN="ghp-your-github-token"
   $env:TEST_GITHUB_REPOSITORY="your-username/test-repo"
   $env:OPENAI_BASE_URL="https://your-openai-base-url"  # オプション
   ```

2. **GitHub Token権限**
   - `repo` (リポジトリへのフルアクセス)
   - `issues:write` (Issue作成権限)
   - `pull_requests:write` (PR作成権限)

### 実行コマンド

#### 方法1: 環境変数ファイル使用
```powershell
# .env.github_test.example をコピーして設定
Copy-Item .env.github_test.example .env.github_test
# .env.github_test を編集して実際の値を設定

# テスト実行
.\run_e2e_tests_fixed.ps1 -LoadEnv
```

#### 方法2: 直接実行
```powershell
# 環境変数を直接設定
$env:OPENAI_API_KEY="your-key"
$env:GITHUB_TOKEN="your-token"
$env:TEST_GITHUB_REPOSITORY="your-repo"

# テスト実行
.\run_e2e_tests_fixed.ps1
```

#### 方法3: Pythonスクリプト直接実行
```powershell
python test_llm_github_e2e_fixed.py
```

### オプション

- `-LoadEnv`: .env.github_test から環境変数を読み込み
- `-TestOnly`: 環境確認をスキップしてテストのみ実行
- `-Repository`: テスト対象リポジトリを指定
- `-Help`: ヘルプ表示

## 📖 README改善フローの詳細

### 分析対象のサンプルREADME
```markdown
# My Project

This is a simple project.

## Setup

Run the following commands:

\`\`\`bash
npm install
npm start
\`\`\`

## Usage

Use the application.

Contact: email@example.com
```

### LLMが特定する改善点
- プロジェクトの目的と概要が不明
- 前提条件（Node.jsバージョンなど）が記載されていない
- インストール手順が簡潔すぎる
- 使用方法の説明が曖昧
- ライセンス情報がない
- 貢献方法が記載されていない

### 生成される改善提案Issue
LLMが以下の要素を含む具体的なIssueを作成します：
- **詳細なタイトル**: README改善提案として明確に識別可能
- **構造化された説明**: 各改善点の詳細と推奨内容
- **適切なラベル**: `documentation`, `enhancement`, `good first issue` など
- **実装可能な提案**: 新規開発者が実際に理解しやすい具体的な改善案

## 🎉 期待される結果

テスト成功時の出力例：
```
🎉 README改善フロー成功!
   📖 README内容の分析完了
   🔍 改善点の特定完了  
   📝 GitHub Issue作成完了
   🔗 作成されたIssue: https://github.com/owner/repo/issues/123
   ✨ 新しい開発者にとって理解しやすいREADMEへの改善提案が投稿されました
```

## 🔧 トラブルシューティング

### よくある問題

1. **GitHub Token権限不足**
   - Tokenに必要な権限（repo, issues:write）が付与されているか確認
   - 対象リポジトリへのアクセス権限を確認

2. **OpenAI API制限**
   - API使用量の上限を確認
   - ベースURLが正しく設定されているか確認

3. **ネットワーク接続**
   - GitHub APIとOpenAI APIへの接続を確認
   - プロキシ設定が必要な場合は設定

### デバッグモード

詳細なログが必要な場合：
```powershell
$env:PYTHONPATH="."
python -m pytest test_llm_github_e2e_fixed.py -v -s
```

## 🎯 このテストの意義

このE2Eテストは、単なるAPI呼び出しテストではなく、**実際のドキュメント改善業務**をLLMが理解し、実行できることを検証します：

1. **コンテンツ理解**: LLMがREADMEの品質を正しく評価
2. **問題特定**: 新規開発者の視点で改善点を発見
3. **実用的提案**: 具体的で実装可能な改善案を生成
4. **GitHub連携**: MCP経由でのシームレスなIssue作成

これにより、LLMを活用したドキュメント改善ワークフローの自動化が実現されます。

## 🚧 注意事項

- **実際のIssue作成**: テストは実際にGitHub Issueを作成します
- **API使用量**: OpenAI APIとGitHub APIの使用量に注意
- **テスト環境**: 本番環境ではなくテスト用リポジトリを使用推奨
- **Issue削除**: 作成されたテストIssueは手動で削除してください

## 📚 関連ドキュメント

- [MCP GitHub Tools実装](docs/SECURE_GITHUB_TOOLS_IMPLEMENTATION.md)
- [フェーズ3完了レポート](docs/PHASE3_WEEK2_COMPLETION_REPORT.md)
- [全体テスト設計](docs/MCP_INTEGRATION_TEST_DESIGN.md)
