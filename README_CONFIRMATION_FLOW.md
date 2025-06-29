# README改善確認フロー付きE2Eテスト

## 概要

このドキュメントでは、LLM経由でGitHub Issueを作成する際の確認フロー付きE2Eテストについて説明します。

## 実装した改善点

### 1. 日本語出力の確実性向上

**問題**: LLMが英語でIssueを作成することがある

**解決策**:
- システムプロンプトの強化
- 具体的な日本語出力例の提示
- 「必ず日本語で」という強い指示の追加
- OpenAI APIの正しい使用（system_instructionの修正）

```python
system_prompt = f"""
あなたは日本人のドキュメント改善専門家です。必ず日本語で応答してください。

【重要指示】
- すべての応答は日本語で行ってください
- Issue作成時も日本語でタイトルと説明を作成してください
- 英語は一切使用しないでください

【出力例】
タイトル: 📚 README改善提案: プロジェクト概要と詳細な導入手順の追加
説明: 
## 改善提案
現在のREADMEには以下の情報が不足しています：
...以下日本語で詳細に記述
"""
```

### 2. Issue投稿前の確認フロー

**実装した機能**:
- 2段階のフロー実装
- ユーザー確認機能
- インタラクティブモードとテストモードの分離

#### フロー図

```
1. LLMがIssue内容を生成（JSON形式）
   ↓
2. 内容をユーザーに表示
   ↓
3. ユーザー確認
   [1] はい → Issue投稿実行
   [2] いいえ → キャンセル
   [3] 修正 → 今後実装予定
   ↓
4. 確認された内容でGitHub Issue作成
```

## テスト関数

### 1. `test_readme_improvement_with_confirmation()`
- 自動実行版（テスト用）
- ユーザー選択は自動で「はい」を選択

### 2. `test_readme_improvement_interactive_confirmation()`
- インタラクティブ版（実際のユーザー入力）
- input()を使用した実際の確認

## 実行方法

### Python直接実行

```bash
# 自動モード
python run_confirmation_test.py

# インタラクティブモード
python run_confirmation_test.py --interactive
```

### PowerShell実行

```powershell
# 自動モード
.\run_confirmation_test.ps1

# インタラクティブモード
.\run_confirmation_test.ps1 -Interactive

# リポジトリ指定
.\run_confirmation_test.ps1 -Interactive -Repository "your-user/your-repo"
```

### メインテストスイート実行

```bash
python test_llm_github_e2e_fixed.py
```

## 環境変数

必要な環境変数:

```powershell
$env:OPENAI_API_KEY='sk-your-openai-key-here'
$env:GITHUB_TOKEN='ghp-your-github-token-here'
$env:TEST_GITHUB_REPOSITORY='your-username/your-test-repo'
```

## 使用例

### インタラクティブモードでの実行例

```
📖 README改善インタラクティブ確認フロー E2Eテスト
=======================================================

🔧 E2E テスト設定確認:
   OpenAI API Key: ✅ 設定済み
   GitHub Token: ✅ 設定済み
   テストリポジトリ: your-user/test-repo

1️⃣ LLMサービス初期化...
   ✅ LLMサービス初期化完了

2️⃣ Function Registry & MCP設定...
   ✅ Function Registry & MCP設定完了

...（中略）...

6️⃣ ユーザー確認...
============================================================
📋 生成されたGitHub Issue内容:
============================================================
リポジトリ: your-user/test-repo
タイトル: 📝 README改善提案: プロジェクト概要と詳細な導入手順の追加

本文:
## 改善提案

現在のREADMEには以下の情報が不足しています：

1. **プロジェクトの目的と概要**
   - このプロジェクトが何を解決するのかが不明
   - 対象ユーザーが分からない

2. **前提条件の記載**
   - Node.jsのバージョン要件
   - 必要なシステム要件

...（詳細な提案内容）...

ラベル: documentation, improvement, readme
============================================================

❓ この内容でGitHub Issueを投稿しますか？
   [1] はい - Issueを投稿
   [2] いいえ - キャンセル
   [3] 修正 - 内容を修正して再生成

選択してください (1/2/3): 1

7️⃣ GitHub Issue投稿実行...
   📤 LLM応答: 確認済みの内容でGitHub Issueを作成しました。

   🔧 Function Call検出: 1個
   📞 関数呼び出し: create_github_issue
   ✅ Issue投稿成功
   📋 Issue #123 が作成されました
   🔗 URL: https://github.com/your-user/test-repo/issues/123
   🏷️ ラベル: ['documentation', 'improvement', 'readme']
   🎉 確認フロー付きIssue作成が完了しました！

🎉 インタラクティブ確認フロー付きE2Eテスト完了
```

## 特徴

### 日本語出力の改善

1. **強化されたプロンプト**: より明確で強い日本語出力指示
2. **具体例の提示**: 期待する出力の具体例を示す
3. **繰り返し強調**: 複数箇所で日本語出力を要求

### 確認フローの利点

1. **ユーザーコントロール**: Issue投稿前に内容を確認可能
2. **誤投稿防止**: 意図しないIssue作成を防止
3. **内容確認**: 生成されたIssue内容の品質を事前チェック
4. **柔軟性**: テスト用自動実行と実際のユーザー確認の両方に対応

### テスト分離

1. **自動テスト**: CI/CDで実行可能な自動テスト
2. **インタラクティブテスト**: 実際の使用シナリオに近いテスト
3. **スクリプト化**: 簡単に実行できるコマンド提供

## 今後の改善予定

1. **内容修正機能**: ユーザーが内容を修正して再生成する機能
2. **テンプレート機能**: 定型的なIssue作成用のテンプレート
3. **フィードバック機能**: 投稿後のIssue品質フィードバック
4. **エラーハンドリング**: より詳細なエラー処理と回復機能

## トラブルシューティング

### よくある問題

#### 1. `system_instruction`エラー
```
TypeError: AsyncCompletions.create() got an unexpected keyword argument 'system_instruction'
```

**解決済み**: OpenAI APIでは`system_instruction`パラメータは存在しません。`messages`配列にシステムメッセージを含める実装に修正済み。

#### 2. 英語でIssueが作成される

**解決策**: プロンプトの強化により改善。さらに日本語出力を確実にしたい場合は、temperature値を下げる（0.1-0.3）ことも有効。

#### 3. Function Callingが実行されない

**確認点**:
- 関数定義が正しく登録されているか
- OpenAI APIキーが有効か
- モデルがFunction Callingに対応しているか（gpt-4, gpt-3.5-turbo等）

## 関連ファイル

- `test_llm_github_e2e_fixed.py`: メインテストファイル
- `run_confirmation_test.py`: Python実行スクリプト
- `run_confirmation_test.ps1`: PowerShell実行スクリプト
- `README_CONFIRMATION_FLOW.md`: このドキュメント
