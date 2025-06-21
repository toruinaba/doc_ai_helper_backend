# OpenAIService 単体テスト実行方法

このドキュメントでは、OpenAIServiceの単体テストの実行方法について説明します。

## 前提条件

- Python 3.9以上
- pytest、pytest-asyncio、unittest.mockがインストールされていること

## 単体テストの特徴

OpenAIServiceの単体テストには以下の特徴があります：

1. **外部依存のモック化**:
   - OpenAI APIとの通信を完全にモック化
   - ネットワーク接続なしで実行可能
   - APIキーなどの認証情報不要

2. **テスト対象**:
   - OpenAIServiceの内部ロジック
   - メッセージ構築処理
   - オプション処理
   - キャッシュ機能
   - エラーハンドリング
   - トークン推定機能

## テスト実行方法

### 基本的な実行方法

```powershell
# プロジェクトのルートディレクトリから実行
pytest tests/unit/services/llm/test_openai_service.py -v
```

### 特定のテストケースのみを実行

```powershell
# 例: 基本的なクエリのテストのみ実行
pytest tests/unit/services/llm/test_openai_service.py::TestOpenAIService::test_query_basic -v
```

### すべての単体テストを実行

```powershell
pytest tests/unit/ -v
```

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
