"""
フロントエンドからForgejoサービスへのAPIアクセス例

このスクリプトでは、フロントエンドからバックエンドのForgejoサービスを
使用してドキュメント取得とリポジトリ構造取得を行う例を示します。
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional

import httpx
from dotenv import load_dotenv


class ForgejoAPIClient:
    """ForgejoサービスのAPIクライアント（フロントエンド想定）"""

    def __init__(self, backend_url: str = "http://localhost:8000"):
        """
        クライアントを初期化

        Args:
            backend_url: バックエンドサーバーのURL
        """
        self.backend_url = backend_url.rstrip("/")
        self.api_prefix = "/api/v1/documents"

    async def get_document(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str = "main",
        transform_links: bool = True,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Forgejoサービスからドキュメントを取得

        Args:
            owner: リポジトリオーナー
            repo: リポジトリ名
            path: ドキュメントパス
            ref: ブランチまたはタグ名
            transform_links: リンク変換を行うか
            base_url: リンク変換用のベースURL

        Returns:
            ドキュメント情報の辞書

        Raises:
            httpx.HTTPStatusError: HTTPエラーが発生した場合
        """
        url = f"{self.backend_url}{self.api_prefix}/contents/forgejo/{owner}/{repo}/{path}"

        params = {"ref": ref, "transform_links": transform_links}
        if base_url:
            params["base_url"] = base_url

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_repository_structure(
        self,
        owner: str,
        repo: str,
        ref: str = "main",
        path: str = "",
    ) -> Dict[str, Any]:
        """
        Forgejoサービスからリポジトリ構造を取得

        Args:
            owner: リポジトリオーナー
            repo: リポジトリ名
            ref: ブランチまたはタグ名
            path: パス フィルター

        Returns:
            リポジトリ構造の辞書

        Raises:
            httpx.HTTPStatusError: HTTPエラーが発生した場合
        """
        url = f"{self.backend_url}{self.api_prefix}/structure/forgejo/{owner}/{repo}"

        params = {"ref": ref}
        if path:
            params["path"] = path

        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def test_connection(self) -> bool:
        """
        バックエンドサーバーへの接続をテスト

        Returns:
            接続成功の場合True
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.backend_url}/health")
                return response.status_code == 200
        except Exception:
            return False


async def demo_forgejo_api_access():
    """ForgejoサービスのAPI使用デモ"""

    # 環境変数を読み込み
    load_dotenv()

    # APIクライアントを作成
    client = ForgejoAPIClient()

    print("=== Forgejo API Client Demo ===\n")

    # 接続テスト
    print("1. バックエンドサーバーへの接続テスト...")
    if await client.test_connection():
        print("   ✅ 接続成功")
    else:
        print(
            "   ❌ 接続失敗 - バックエンドサーバーが起動していることを確認してください"
        )
        return

    # 環境変数からリポジトリ情報を取得
    owner = os.getenv("FORGEJO_OWNER", "test-owner")
    repo = os.getenv("FORGEJO_REPO", "test-repo")
    base_url = os.getenv("FORGEJO_BASE_URL", "http://localhost:3000")

    print(f"\n2. リポジトリ構造取得テスト...")
    print(f"   対象: {owner}/{repo}")

    try:
        structure = await client.get_repository_structure(owner, repo)
        print(f"   ✅ 構造取得成功")
        print(f"   - サービス: {structure['service']}")
        print(f"   - リポジトリ: {structure['owner']}/{structure['repository']}")
        print(f"   - ブランチ: {structure['ref']}")
        print(f"   - ファイル数: {len(structure['structure'])}")

        # 最初の数個のファイルを表示
        print("   - ファイル一覧（最初の5個）:")
        for item in structure["structure"][:5]:
            print(f"     - {item['name']} ({item['type']})")

        if len(structure["structure"]) > 5:
            print(f"     ... 他 {len(structure['structure']) - 5} 個")

    except httpx.HTTPStatusError as e:
        print(f"   ❌ 構造取得失敗: HTTP {e.response.status_code}")
        print(f"   エラー詳細: {e.response.text}")
        return
    except Exception as e:
        print(f"   ❌ 構造取得失敗: {e}")
        return

    # README.mdファイルの取得を試す
    print(f"\n3. ドキュメント取得テスト...")
    readme_candidates = ["README.md", "readme.md", "README.rst", "index.md"]

    for readme_file in readme_candidates:
        # 構造からファイルを探す
        found = any(
            item["name"].lower() == readme_file.lower()
            for item in structure["structure"]
        )
        if found:
            print(f"   対象ファイル: {readme_file}")
            try:
                document = await client.get_document(
                    owner, repo, readme_file, transform_links=True, base_url=base_url
                )
                print(f"   ✅ ドキュメント取得成功")
                print(f"   - パス: {document['path']}")
                print(f"   - タイプ: {document['type']}")
                print(f"   - サイズ: {document['content']['size']} bytes")
                print(f"   - エンコーディング: {document['content']['encoding']}")

                # フロントマター情報
                if document["metadata"]["frontmatter"]:
                    print(
                        f"   - フロントマター: {len(document['metadata']['frontmatter'])} 項目"
                    )

                # リンク情報
                if document["links"]:
                    print(f"   - リンク数: {len(document['links'])}")
                    for link in document["links"][:3]:  # 最初の3個のリンクを表示
                        print(f"     - {link['text']}: {link['url']}")

                # コンテンツのプレビュー
                content = document["content"]["raw"]
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"   - コンテンツプレビュー:")
                print(f"     {preview}")
                break

            except httpx.HTTPStatusError as e:
                print(f"   ❌ ドキュメント取得失敗: HTTP {e.response.status_code}")
                if e.response.status_code == 404:
                    print(f"   ファイル '{readme_file}' が見つかりません")
                    continue
                else:
                    print(f"   エラー詳細: {e.response.text}")
                    break
            except Exception as e:
                print(f"   ❌ ドキュメント取得失敗: {e}")
                break
    else:
        print("   ⚠️  READMEファイルが見つかりませんでした")

    print("\n=== デモ完了 ===")


def print_curl_examples():
    """curl でのAPI呼び出し例を表示"""
    print("\n=== curl でのAPI呼び出し例 ===")

    # 環境変数を読み込み
    load_dotenv()
    owner = os.getenv("FORGEJO_OWNER", "test-owner")
    repo = os.getenv("FORGEJO_REPO", "test-repo")

    print(f"\n1. リポジトリ構造取得:")
    print(
        f"curl -X GET 'http://localhost:8000/api/v1/documents/structure/forgejo/{owner}/{repo}?ref=main'"
    )

    print(f"\n2. ドキュメント取得:")
    print(
        f"curl -X GET 'http://localhost:8000/api/v1/documents/contents/forgejo/{owner}/{repo}/README.md?ref=main&transform_links=true'"
    )

    print(f"\n3. パス フィルター付き構造取得:")
    print(
        f"curl -X GET 'http://localhost:8000/api/v1/documents/structure/forgejo/{owner}/{repo}?ref=main&path=docs/'"
    )


async def main():
    """メイン関数"""
    print("ForgejoサービスのフロントエンドAPI使用例\n")

    # デモ実行
    await demo_forgejo_api_access()

    # curl例の表示
    print_curl_examples()

    print("\n注意:")
    print(
        "- バックエンドサーバーが localhost:8000 で起動していることを確認してください"
    )
    print(
        "- .env ファイルでFORGEJO_OWNER, FORGEJO_REPO, FORGEJO_BASE_URL を設定してください"
    )
    print("- 実際のForgejoサーバーに接続可能であることを確認してください")


if __name__ == "__main__":
    asyncio.run(main())
