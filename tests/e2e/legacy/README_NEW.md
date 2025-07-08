# User Story-Based E2E Tests

このディレクトリには、Document AI Helper Backendのユーザーストーリーベースのエンド・ツー・エンド（E2E）テストが含まれています。

## 概要

これらのテストは、実際のユーザーの視点から始まって、フロントエンドとバックエンドの統合フローを検証します。従来のAPI中心のテストとは異なり、ユーザージャーニーと実際の使用パターンに焦点を当てています。

## アーキテクチャ

### ディレクトリ構造

```
tests/e2e/
├── user_stories/           # ユーザーストーリーベースのテストケース
│   ├── test_onboarding_journey.py
│   ├── test_document_exploration_journey.py
│   ├── test_ai_assisted_improvement_journey.py
│   └── test_team_collaboration_journey.py
├── helpers/                # テストヘルパーモジュール
│   ├── __init__.py
│   ├── frontend_simulator.py      # フロントエンドシミュレーター
│   ├── user_journey_tracker.py    # ユーザージャーニー追跡
│   ├── story_assertions.py        # ストーリー固有のアサーション
│   ├── scenario_runner.py         # シナリオランナー
│   ├── performance_monitor.py     # パフォーマンス監視
│   ├── data_validator.py          # データバリデーター
│   └── test_data_generator.py     # テストデータ生成器
├── fixtures/               # テストフィクスチャー
│   ├── user_personas.json         # ユーザーペルソナ定義
│   ├── story_scenarios.json       # ストーリーシナリオ設定
│   ├── sample_documents/          # サンプルドキュメント
│   └── schemas/                   # バリデーション用JSONスキーマ
├── conftest.py            # Pytest設定とフィクスチャー
├── pytest.ini            # Pytest設定（マーカー定義）
└── README.md             # このファイル
```

### 主要なヘルパークラス

#### ScenarioRunner
テストシナリオの実行を管理し、セットアップ、実行、ティアダウンを処理します。

```python
async with scenario_runner.run_scenario(
    "onboarding_basic",
    "new_user", 
    client
) as context:
    # テストロジック
    pass
```

#### FrontendSimulator
フロントエンドユーザーの操作をシミュレートし、実際のユーザー体験を再現します。

```python
simulator = FrontendSimulator(backend_api_client)
session = simulator.start_session("new_user")
result = await simulator.connect_to_repository("github", "owner", "repo", user_context)
```

#### UserJourneyTracker
ユーザーのアクション、エラー、達成を追跡し、ジャーニー分析を提供します。

```python
tracker = UserJourneyTracker(persona)
tracker.log_action("ドキュメント閲覧", {"path": "/README.md"})
tracker.add_achievement("初回ドキュメント閲覧完了")
summary = tracker.get_journey_summary()
```

#### PerformanceMonitor
テスト実行中のパフォーマンスメトリクスを監視します。

```python
monitor = PerformanceMonitor()
await monitor.start_monitoring()
# ... テスト実行 ...
metrics = await monitor.get_metrics()
await monitor.stop_monitoring()
```

#### DataValidator
APIレスポンス、ドキュメント内容、その他のデータを検証します。

```python
validator = DataValidator()
result = validator.validate_custom(document, "document_content")
assert result.is_valid, f"Validation failed: {result.errors}"
```

#### TestDataGenerator
テスト用のリアルなデータを生成します。

```python
generator = TestDataGenerator(seed=42)
repo_config = generator.generate_repository_config()
markdown_content = generator.generate_markdown_content()
```

## ユーザーストーリーテスト

### 1. オンボーディングジャーニー
新規ユーザーが初めてシステムを使用する体験をテストします。

**テストケース:**
- `test_complete_onboarding_flow` - 完全なオンボーディングフロー
- `test_error_recovery_during_onboarding` - エラー発生時のリカバリー
- `test_comprehensive_onboarding_with_ai` - AI機能を含む包括的オンボーディング

### 2. ドキュメント探索ジャーニー
ユーザーがドキュメントを探索し、情報を見つける体験をテストします。

### 3. AI支援改善ジャーニー
AI機能を使ってドキュメントを分析し、改善する体験をテストします。

### 4. チーム協力ジャーニー
チームメンバーが協力してドキュメントを作業する体験をテストします。

## 設定とマーカー

### Pytestマーカー

```ini
# pytest.ini
[tool:pytest]
markers = 
    e2e_user_story: User story-based end-to-end tests
    onboarding: Onboarding journey tests
    document_exploration: Document exploration tests
    ai_assistance: AI assistance feature tests
    team_collaboration: Team collaboration tests
    slow: Tests that may take longer to execute
    requires_external_api: Tests requiring external API access
```

### フィクスチャー

```python
# conftest.py で提供される主要なフィクスチャー
@pytest.fixture
def scenario_runner(fixtures_path: Path) -> ScenarioRunner

@pytest.fixture
def performance_monitor() -> PerformanceMonitor

@pytest.fixture
def data_validator(fixtures_path: Path) -> DataValidator

@pytest.fixture
def test_data_generator() -> TestDataGenerator
```

## 実行方法

### 全てのユーザーストーリーテストを実行
```bash
pytest tests/e2e/user_stories/ -v
```

### 特定のジャーニーをテスト
```bash
# オンボーディングジャーニーのみ
pytest tests/e2e/user_stories/ -m onboarding -v

# AI機能を含むテストのみ
pytest tests/e2e/user_stories/ -m ai_assistance -v

# 時間のかかるテストを除外
pytest tests/e2e/user_stories/ -m "not slow" -v
```

### 詳細ログ付きで実行
```bash
pytest tests/e2e/user_stories/ -v -s --log-cli-level=INFO
```

## テストの設計原則

### 1. ユーザー中心設計
- 実際のユーザーペルソナに基づいたテスト
- ユーザーの目標と動機を反映
- 実際の使用パターンをシミュレート

### 2. ジャーニーベース
- エンド・ツー・エンドのユーザージャーニーをテスト
- 複数のAPIエンドポイントをまたがるフロー
- 実際のユーザー体験を再現

### 3. コンテキスト保持
- テスト間でのコンテキストと状態の管理
- ユーザーセッションの追跡
- 累積的な学習と改善の検証

### 4. パフォーマンス統合
- ユーザー体験に影響するパフォーマンスの測定
- レスポンス時間とリソース使用量の監視
- 実際の使用条件でのテスト

### 5. エラー回復力
- エラー発生時のユーザー体験
- 適切なエラーメッセージと回復ガイダンス
- システムの堅牢性検証

## ベストプラクティス

### テスト作成
1. **明確なユーザーストーリー定義** - 誰が、何を、なぜを明確にする
2. **リアルなテストデータ** - 実際の使用パターンを反映したデータを使用
3. **段階的な検証** - 各ステップでの適切な検証を実装
4. **意味のあるアサーション** - 技術的な詳細よりユーザー価値に焦点

### デバッグとトラブルシューティング
1. **詳細なログ** - ユーザーアクションと系統の追跡
2. **コンテキスト保存** - 失敗時の状態情報を保存
3. **再現可能性** - 固定シードを使用した一貫したテスト
4. **段階的実行** - 複雑なジャーニーを小さなステップに分割

### メンテナンス
1. **モジュラー設計** - 再利用可能なヘルパーとユーティリティ
2. **設定の外部化** - ハードコードされた値の回避
3. **定期的な更新** - ユーザーニーズの変化に応じた更新
4. **ドキュメント保守** - テストの意図と期待される動作の明確化

## 拡張性

### 新しいユーザーストーリーの追加
1. `user_stories/` ディレクトリに新しいテストファイルを作成
2. 適切なマーカーを追加
3. 必要に応じて新しいペルソナやシナリオを定義
4. ヘルパーメソッドを拡張

### 新しいヘルパーの追加
1. `helpers/` ディレクトリに新しいモジュールを作成
2. `__init__.py` でエクスポート
3. `conftest.py` でフィクスチャーとして提供
4. 適切なドキュメントを追加

この構造により、ユーザー中心のE2Eテストが maintainable で scalable な方法で実装できます。
