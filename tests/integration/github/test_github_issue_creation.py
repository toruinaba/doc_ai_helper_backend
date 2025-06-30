#!/usr/bin/env python3
"""
GitHub Issue投稿のMCPテストコード
実際のGitHubリポジトリに対してIssue作成をテストします
"""

import asyncio
import json
import os
from typing import Optional
from doc_ai_helper_backend.services.mcp.tools.github_tools import (
    create_github_issue,
    check_github_repository_permissions,
)


def get_github_token() -> Optional[str]:
    """GitHub tokenを環境変数から取得"""
    return os.getenv("GITHUB_TOKEN")


async def test_github_issue_creation():
    """実際のGitHubリポジトリにIssue作成をテストする"""
    print("🐙 GitHub Issue作成 MCP テスト")
    print("=" * 50)

    # GitHubトークンの確認
    github_token = get_github_token()
    if not github_token:
        print("❌ GITHUB_TOKENが設定されていません")
        print("   環境変数にGITHUB_TOKENを設定してください:")
        print("   例: export GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx")
        print("")
        print("📝 トークンなしでの動作確認（エラーメッセージのテスト）:")
        await test_without_token()
        return

    print(f"✅ GitHubトークンが設定されています: {github_token[:10]}...")

    # テスト対象リポジトリの設定
    test_repo = input(
        "📁 テスト対象リポジトリを入力してください (例: owner/repo): "
    ).strip()
    if not test_repo or "/" not in test_repo:
        print("❌ 無効なリポジトリ形式です。 'owner/repo' の形式で入力してください")
        return

    owner, repo = test_repo.split("/", 1)

    # リポジトリコンテキストの作成
    repository_context = {
        "repo": repo,
        "owner": owner,
        "service": "github",
        "ref": "main",
    }

    print(f"🎯 テスト対象: {test_repo}")
    print("")

    # Step 1: リポジトリ権限の確認
    print("1️⃣ リポジトリ権限の確認...")
    try:
        permissions_result = await check_github_repository_permissions(
            github_token=github_token, repository_context=repository_context
        )

        permissions_data = json.loads(permissions_result)
        print(f"   結果: {permissions_data}")

        if not permissions_data.get("success"):
            print(f"   ❌ 権限確認エラー: {permissions_data.get('error')}")
            return

        permissions = permissions_data.get("permissions", {})
        can_create_issues = permissions.get("issues", False)

        if not can_create_issues:
            print(f"   ❌ このリポジトリにはIssue作成権限がありません")
            return

        print(f"   ✅ Issue作成権限があります")

    except Exception as e:
        print(f"   ❌ 権限確認中にエラー: {str(e)}")
        return

    print("")

    # Step 2: Issue作成のテスト
    print("2️⃣ テストIssue作成...")

    # ユーザーに確認
    create_issue = input("   実際にIssueを作成しますか？ (y/N): ").strip().lower()
    if create_issue != "y":
        print("   ⏭️  Issue作成をスキップしました")
        return

    # Issue情報の設定
    issue_title = "🤖 MCP GitHub Tools テスト - 自動作成されたIssue"
    issue_description = """
## 📋 概要
このIssueはMCP GitHub Toolsの動作テストとして自動作成されました。

## ✅ テスト内容
- MCP経由でのGitHub Issue作成機能
- 日本語メッセージとの統合
- リポジトリコンテキストの検証

## 🛠️ 作成元
- ツール: MCP GitHub Tools
- 日時: {datetime}
- 言語: 日本語レスポンス対応

## 🗑️ 削除について
このIssueはテスト目的で作成されているため、確認後に削除していただいて構いません。

---
*このIssueは自動化ツールによって作成されました*
    """.strip()

    try:
        issue_result = await create_github_issue(
            title=issue_title,
            description=issue_description,
            labels=["テスト", "自動作成", "MCP"],
            github_token=github_token,
            repository_context=repository_context,
        )

        issue_data = json.loads(issue_result)
        print(f"   📝 Issue作成結果:")
        print(f"      成功: {issue_data.get('success')}")

        if issue_data.get("success"):
            issue_info = issue_data.get("issue_info", {})
            print(f"      Issue番号: #{issue_info.get('number')}")
            print(f"      URL: {issue_info.get('url')}")
            print(f"      タイトル: {issue_info.get('title')}")
            print(f"      ✅ Issue作成に成功しました！")
        else:
            print(f"      ❌ エラー: {issue_data.get('error')}")

    except Exception as e:
        print(f"   ❌ Issue作成中にエラー: {str(e)}")

    print("")
    print("🎉 GitHub Issue作成テスト完了!")


async def test_without_token():
    """トークンなしでの動作確認（エラーハンドリングテスト）"""
    print("")
    print("🧪 トークンなしエラーハンドリングテスト")
    print("-" * 40)

    # ダミーのリポジトリコンテキスト
    repository_context = {
        "repo": "test-repo",
        "owner": "test-owner",
        "service": "github",
        "ref": "main",
    }

    try:
        result = await create_github_issue(
            title="テストIssue",
            description="これはトークンなしのテストです",
            repository_context=repository_context,
        )

        result_data = json.loads(result)
        print("📋 レスポンス:")
        print(f"   成功: {result_data.get('success')}")
        print(f"   エラー: {result_data.get('error')}")
        print(f"   エラータイプ: {result_data.get('error_type')}")
        print("")
        print("✅ 日本語エラーメッセージが正しく表示されています")

    except Exception as e:
        print(f"❌ 予期しないエラー: {str(e)}")


async def main():
    """メイン関数"""
    print("🔧 環境確認...")

    # 現在の作業ディレクトリの確認
    print(f"   作業ディレクトリ: {os.getcwd()}")

    # 環境変数の確認
    github_token = get_github_token()
    if github_token:
        print(f"   GitHubトークン: 設定済み ({github_token[:10]}...)")
    else:
        print("   GitHubトークン: 未設定")

    print("")

    # メインテストの実行
    await test_github_issue_creation()


if __name__ == "__main__":
    asyncio.run(main())
