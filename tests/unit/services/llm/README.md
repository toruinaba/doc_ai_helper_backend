# LLM Services Unit Tests

このドキュメントでは、LLMサービスの単体テストの構造と実行方法について説明します。

## テスト構造 - 1:1対応原則

すべてのソースファイルは対応するテストファイルと厳密な1:1対応を維持しています：

### メインLLMサービス
```
doc_ai_helper_backend/services/llm/    <->    tests/unit/services/llm/
├── base.py                           <->    ├── test_base.py
├── common.py                         <->    ├── test_common.py  
├── factory.py                        <->    ├── test_factory.py
├── mock_service.py                   <->    ├── test_mock_service.py
└── openai_service.py                 <->    └── test_openai_service.py
```

### ユーティリティモジュール
```
doc_ai_helper_backend/services/llm/utils/    <->    tests/unit/services/llm/utils/
├── caching.py                               <->    ├── test_caching.py
├── functions.py                             <->    ├── test_functions.py
├── helpers.py                               <->    ├── test_helpers.py
├── messaging.py                             <->    ├── test_messaging.py
├── templating.py                            <->    ├── test_templating.py
└── tokens.py                                <->    └── test_tokens.py
```

## 前提条件

- Python 3.9以上
- pytest、pytest-asyncio、unittest.mockがインストールされていること

## 単体テストの特徴

LLMサービスの単体テストには以下の特徴があります：

1. **外部依存のモック化**:
   - OpenAI APIとの通信を完全にモック化
   - ネットワーク接続なしで実行可能
   - APIキーなどの認証情報不要

2. **テスト対象**:
   - LLMサービスの内部ロジック
   - メッセージ構築処理
   - オプション処理
   - キャッシュ機能
   - エラーハンドリング
   - トークン推定機能
   - コンポジション設計の正確性

## テスト実行方法

### 1:1対応テストのみ実行（推奨）

```bash
# プロジェクトのルートディレクトリから実行
pytest tests/unit/services/llm/ --ignore=tests/unit/services/llm/legacy/ -v
```

### 特定のサービステスト実行

```bash
# OpenAIサービスのテストのみ実行
pytest tests/unit/services/llm/test_openai_service.py -v

# ファクトリーのテストのみ実行
pytest tests/unit/services/llm/test_factory.py -v

# ユーティリティのテストのみ実行
pytest tests/unit/services/llm/utils/ -v
```

### 特定のテストケースのみを実行

```bash
# 例: 基本的なクエリのテストのみ実行
pytest tests/unit/services/llm/test_openai_service.py::TestOpenAIService::test_query_basic -v
```

### すべての単体テスト（legacy含む）を実行

```bash
pytest tests/unit/services/llm/ -v
```

## レガシーテストについて

`tests/unit/services/llm/legacy/` ディレクトリには古いアーキテクチャ用のテストが含まれています：

- **自動スキップ**: pytest.mark.skipが設定済み
- **参考用**: 旧実装の参考として保持
- **実行除外**: 通常のテスト実行からは除外推奨

詳細は [legacy/README.md](legacy/README.md) を参照してください。

## テスト結果の確認

テスト実行後、pytest は以下のような結果を表示します：

```
============================= test session starts =============================
...
collected 12 items

tests/unit/services/llm/test_openai_service.py::TestOpenAIService::test_initialization PASSED
tests/unit/services/llm/test_openai_service.py::TestOpenAIService::test_query_basic PASSED
tests/unit/services/llm/test_openai_service.py::TestOpenAIService::test_query_with_custom_options PASSED
...

============================= 12 passed in 0.54s =============================
```

## テスト実装の主なポイント

1. **依存関係のモック化**:
   - `AsyncOpenAI`、`OpenAI`、`tiktoken`をモック化して外部依存を排除
   - フィクスチャを使用してモックをテスト間で共有

2. **テストの網羅性**:
   - 基本機能（クエリ、機能取得など）のテスト
   - オプション処理のテスト（カスタムモデル、温度、最大トークン数など）
   - メッセージ形式のテスト
   - カスタムベースURLのテスト
   - キャッシュ機能のテスト
   - エラーハンドリングのテスト
   - 内部メソッドのテスト（`_prepare_options`、`_convert_to_llm_response`など）

3. **アサーション戦略**:
   - API呼び出しパラメータが正しいことを確認
   - 戻り値の型と内容を検証
   - キャッシュヒット時にAPI呼び出しがないことを確認

## 統合テストとの違い

1. **モック化の範囲**:
   - 単体テスト: すべての外部依存をモック化
   - 統合テスト: 実際のAPIを呼び出し、エンドツーエンドの動作を確認

2. **テスト速度**:
   - 単体テスト: 高速（ネットワーク通信なし）
   - 統合テスト: 低速（実際のAPI呼び出しを含む）

3. **テスト安定性**:
   - 単体テスト: 高い（外部要因に依存しない）
   - 統合テスト: 低い（API可用性、レート制限などに影響される）

4. **必要な設定**:
   - 単体テスト: なし（APIキー不要）
   - 統合テスト: APIキーやベースURLなどの設定が必要

## トラブルシューティング

### モックが正しく動作しない

単体テストでモックが期待通りに動作しない場合は、以下を確認してください：

1. パッチが正しい場所に適用されているか
2. モックオブジェクトの設定が正しいか
3. テスト対象のクラスがモックの代わりに実際のオブジェクトを使用していないか

### テストが失敗する

1. **OpenAIServiceの実装変更**: クラスの実装が変更された場合、テストを更新する必要があります。
2. **Python/ライブラリのバージョン**: 使用しているPythonやライブラリのバージョンによって動作が異なる場合があります。
3. **モックの不足**: テスト対象のコードが使用する外部依存がすべてモック化されていることを確認してください。
