# doc_ai_helper_backend 開発計画

最終更新: 2025年6月22日

## プロジェクト概要

このプロジェクトは、一般ユーザーがリポジトリに格納されたドキュメントをカジュアルな形式で確認しながらLLMと対話し、理解を深めるためのアプリケーションです。

### 主要機能
1. ドキュメントを見ながらLLMとの質問・対話による理解促進
2. LLMとの対話から文書改善点を発見し、MCPを用いてリポジトリにIssue/PRを投稿
3. リポジトリ管理者によるフィードバックを受けた文書のアップデート
4. GitHub、GitLab、Gitea等の複数Gitサービス対応

## テスト戦略の明確化

### Unit Tests（単体テスト）
```
tests/unit/
├── api/                    # API層の単体テスト（Mock LLM使用）
│   ├── test_llm.py        # ✅ LLM APIエンドポイントテスト
│   ├── test_llm_endpoints.py  # ✅ 詳細なエンドポイントテスト
│   ├── test_llm_streaming.py  # ✅ ストリーミングテスト
│   └── test_documents.py     # ✅ ドキュメントAPIテスト
├── services/              # サービス層の単体テスト
│   ├── llm/              # ✅ LLMサービステスト（Mock含む）
│   └── git/              # ✅ Gitサービステスト
└── document_processors/   # ✅ ドキュメント処理テスト
```

### Integration Tests（統合テスト）
```
tests/integration/
├── git/                   # 実際のGitサービス統合テスト
│   └── test_github_service.py  # 実際のGitHub API使用
└── llm/                   # 実際のLLMサービス統合テスト
    └── test_openai_service.py   # 実際のOpenAI API使用
```

**統合テストの実行条件:**
- 環境変数で実際のAPIキーが設定されている場合のみ実行
- ローカル開発では基本的にスキップ
- CI/CDの特定のブランチ・環境での実行

## 実装計画

### フェーズ1: テスト基盤の整理（優先度: 最高）

#### 1.1 統合テストの削除・再編成
- [ ] 既存の統合テストからMockモード削除
- [ ] 統合テストを実際のAPI使用時のみ実行に変更
- [ ] CI/CDで統合テストをオプション実行に設定
- [ ] ローカル開発では統合テストをスキップ

#### 1.2 Unit APIテストの強化
現状: ✅ Mock LLMを使用したAPIテスト完備

拡張予定:
- [ ] エラーケースのテスト強化
- [ ] レスポンス形式の詳細検証
- [ ] パフォーマンステストの追加
- [ ] 境界値テストの追加

#### 1.3 開発ワークフローの明確化
**開発時のテスト実行:**
1. Unit Tests のみ実行（高速、依存なし）
2. 統合テストは本番前のみ実行
3. Mock環境での完全な機能検証

### フェーズ2: コア機能開発（優先度: 高）

#### 2.1 Function Calling機能の実装
- [ ] OpenAIサービスのFunction Calling対応
- [ ] MockサービスのFunction Calling対応
- [ ] APIエンドポイントでのツール呼び出し
- [ ] Unit APIテストでの検証完了

#### 2.2 MCP基盤実装
**カスタムMCPサーバー:**
- [ ] 文書分析ツール実装
- [ ] フィードバック生成ツール実装
- [ ] 改善提案ツール実装
- [ ] Unit テストでの完全検証

#### 2.3 フィードバック分析エンジン
**新しいサービス層:**
- [ ] 対話履歴分析サービス
- [ ] 文書品質評価サービス
- [ ] 改善提案生成サービス
- [ ] Mock データでのUnit テスト

### フェーズ3: 外部統合とフィードバック投稿（優先度: 高）

#### 3.1 GitHub統合（実装優先）
- [ ] GitHub MCP Server統合
- [ ] Issue作成機能
- [ ] PR作成機能
- [ ] Unit テストでMock GitHub API使用
- [ ] 統合テストで実際のGitHub API使用（オプション）

#### 3.2 フィードバック投稿API
**新しいAPIエンドポイント:**
- [ ] `POST /api/v1/feedback/analyze` - 対話分析
- [ ] `POST /api/v1/feedback/generate` - 改善提案生成
- [ ] `POST /api/v1/feedback/submit` - フィードバック投稿
- [ ] `GET /api/v1/mcp/tools` - 利用可能ツール

### フェーズ4: UX向上機能（優先度: 中）

#### 4.1 文書理解支援
- [ ] 文書構造分析
- [ ] 専門用語解説
- [ ] 関連セクション推薦
- [ ] 理解度評価

#### 4.2 検索・発見機能
- [ ] 文書内容検索
- [ ] 関連文書推薦
- [ ] 質問候補提示
- [ ] 学習パス提案

## 実装スケジュール

### Week 1: テスト基盤整理
- [ ] 統合テストからMockモード削除
- [ ] CI/CD設定更新
- [ ] Unit APIテストの拡充
- [ ] 開発ワークフロー文書化

### Week 2: Function Calling実装
- [ ] OpenAI Function Calling実装
- [ ] Mock Function Calling実装
- [ ] Unit テストでの完全検証
- [ ] APIエンドポイントの拡張

### Week 3-4: MCP基盤とフィードバック機能
- [ ] カスタムMCPサーバー実装
- [ ] フィードバック分析エンジン
- [ ] GitHub統合の基礎
- [ ] Unit テストでの検証

### Week 5-6: 外部統合とAPI完成
- [ ] GitHub MCP統合完了
- [ ] フィードバック投稿API完成
- [ ] 統合テスト（実API使用）の実装
- [ ] エンドツーエンドテスト

## テスト実行戦略

### 開発時（ローカル環境）
```bash
# 高速で依存のないテストのみ実行
pytest tests/unit/ -v

# 特定のAPI機能テスト
pytest tests/unit/api/ -v

# 特定のサービステスト
pytest tests/unit/services/llm/ -v
```

### CI/CD（継続的統合）
```yaml
# .github/workflows/test.yml
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Run Unit Tests
        run: pytest tests/unit/ -v --cov
    
  integration-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || contains(github.event.pull_request.labels.*.name, 'integration-test')
    steps:
      - name: Run Integration Tests
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: pytest tests/integration/ -v
```

### 本番前検証
```bash
# 実際のAPI使用した統合テスト
OPENAI_API_KEY=xxx GITHUB_TOKEN=xxx pytest tests/integration/ -v

# パフォーマンステスト
pytest tests/performance/ -v

# セキュリティテスト
pytest tests/security/ -v
```

## 成功メトリクス

### 開発効率
- ✅ Unit テスト実行時間 < 30秒
- ✅ ローカル開発でのテスト成功率 > 98%
- ✅ 外部依存なしでの完全機能検証

### 品質保証
- ✅ Unit テストカバレッジ > 90%
- ✅ API契約の完全検証
- ✅ エラーハンドリングの網羅

### 統合品質
- ✅ 実API統合テスト成功率 > 95%（実行時）
- ✅ パフォーマンス要件の達成
- ✅ セキュリティ要件の満足

## アーキテクチャ上の利点

### 開発速度向上
- 外部API依存なしでの迅速な開発
- 高速なテストフィードバックループ
- 確実な機能検証

### 品質保証
- Mock環境での完全な機能テスト
- 実環境での統合テスト分離
- 段階的な検証プロセス

### 運用安定性
- 外部API障害の影響最小化
- 予測可能なテスト実行
- 明確な責任分界

## 技術スタック

### コア技術
- **フレームワーク**: FastAPI
- **LLMプロバイダー**: OpenAI (+ Mock for development)
- **MCPプロトコル**: Model Context Protocol
- **テスト**: pytest
- **HTTP クライアント**: httpx

### 対応サービス
- **Gitサービス**: GitHub, GitLab, Gitea
- **LLMサービス**: OpenAI (実装済み), Mock (開発用)
- **MCPサーバー**: GitHub MCP, カスタムMCP

## 注意事項

### 開発環境制約
- OpenAIへの直接アクセス不可のため、Mock環境での開発
- 統合テストは実際のAPI利用可能時のみ実行
- CI/CDでの統合テストはオプション実行

### 設計方針
- 会話履歴の永続化は対象外（インメモリ管理のみ）
- Ollamaサービスは優先度低により除外
- 段階的実装によるリスク最小化

---

この計画に基づいて、文書理解支援とフィードバック機能を核とした価値提供を着実に実現していきます。
