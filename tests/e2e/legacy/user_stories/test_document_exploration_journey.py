"""
ドキュメント探索・発見ジャーニーのE2Eテスト

このテストは既存ユーザーがリポジトリ内のドキュメントを
探索し、関連情報を発見する際の典型的なフローをシミュレートします。

User Story:
- 既存ユーザーとして、特定の情報を探すためにドキュメントを探索する
- リンクを辿り、関連ドキュメントを発見する
- フロントマターやメタデータを活用して効率的に情報を見つける
"""

import pytest
import asyncio
from typing import Dict, Any, List

from tests.e2e.helpers.frontend_simulator import FrontendSimulator
from tests.e2e.fixtures.user_personas import get_user_persona
from tests.e2e.fixtures.story_scenarios import get_story_scenario


class TestDocumentExplorationJourney:
    """ドキュメント探索ジャーニーE2Eテスト"""

    @pytest.fixture
    def explorer_user_simulator(self) -> FrontendSimulator:
        """探索ユーザー向けのフロントエンドシミュレーターを作成"""
        persona = get_user_persona("document_explorer")
        return FrontendSimulator(user_persona=persona)

    @pytest.fixture
    def exploration_scenario(self) -> Dict[str, Any]:
        """ドキュメント探索シナリオデータを取得"""
        return get_story_scenario("document_exploration")

    @pytest.mark.e2e_user_story
    @pytest.mark.document_exploration
    @pytest.mark.asyncio
    async def test_structured_document_discovery(
        self,
        explorer_user_simulator: FrontendSimulator,
        exploration_scenario: Dict[str, Any],
    ):
        """構造化されたドキュメント発見フローのテスト"""

        # Step 1: システムアクセスとリポジトリ選択
        repository_info = exploration_scenario["target_repository"]
        discovery_result = await explorer_user_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )

        assert discovery_result["success"] is True
        explorer_user_simulator.log_user_action("探索対象リポジトリにアクセス")

        # Step 2: リポジトリ構造の分析
        structure = discovery_result["structure"]
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]
        assert len(markdown_files) > 0, "Markdownファイルが見つからない"

        # ディレクトリ構造から重要なファイルを特定
        important_files = []
        for file_info in markdown_files:
            if any(
                keyword in file_info["name"].lower()
                for keyword in ["readme", "index", "getting-started", "introduction"]
            ):
                important_files.append(file_info)

        explorer_user_simulator.log_user_action(
            f"{len(important_files)}個の重要ファイルを特定"
        )

        # Step 3: 階層的ドキュメント探索
        explored_documents = []

        for file_info in important_files[:3]:  # 最大3つまで探索
            doc_result = await explorer_user_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=file_info["path"],
            )

            if doc_result["success"]:
                # ドキュメントメタデータの確認
                document_content = doc_result["content"]
                metadata = doc_result.get("metadata", {})

                explored_documents.append(
                    {
                        "path": file_info["path"],
                        "name": file_info["name"],
                        "content_length": len(document_content),
                        "has_frontmatter": bool(metadata.get("frontmatter")),
                        "links_found": len(doc_result.get("links", [])),
                    }
                )

                explorer_user_simulator.log_user_action(
                    f"ドキュメント {file_info['name']} を探索"
                )

        # Step 4: リンク辿り探索
        if explored_documents:
            # 最初のドキュメントからリンクを辿る
            first_doc = explored_documents[0]
            links_result = await explorer_user_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=first_doc["path"],
            )

            if links_result["success"] and "links" in links_result:
                internal_links = [
                    link
                    for link in links_result["links"]
                    if not link.get("is_external", False)
                ]

                # 内部リンクを1つ辿る
                if internal_links:
                    target_link = internal_links[0]
                    linked_doc_result = (
                        await explorer_user_simulator.follow_document_link(
                            service=repository_info["service"],
                            owner=repository_info["owner"],
                            repo=repository_info["repo"],
                            link_url=target_link["url"],
                        )
                    )

                    if linked_doc_result["success"]:
                        explorer_user_simulator.log_user_action(
                            "内部リンクを辿って関連ドキュメントを発見"
                        )

        # Step 5: 探索結果の検証
        assert len(explored_documents) > 0, "ドキュメント探索が失敗"

        # フロントマターを持つドキュメントが存在することを確認
        docs_with_frontmatter = [
            doc for doc in explored_documents if doc["has_frontmatter"]
        ]
        explorer_user_simulator.log_user_action(
            f"{len(docs_with_frontmatter)}個のドキュメントでメタデータを発見"
        )

        # 探索ジャーニーの完了
        journey_summary = explorer_user_simulator.get_journey_summary()
        assert (
            len(journey_summary["actions"]) >= 5
        ), "十分な探索アクションが実行されていない"

    @pytest.mark.e2e_user_story
    @pytest.mark.document_exploration
    @pytest.mark.search_functionality
    @pytest.mark.asyncio
    async def test_content_based_exploration(
        self,
        explorer_user_simulator: FrontendSimulator,
        exploration_scenario: Dict[str, Any],
    ):
        """コンテンツベースのドキュメント探索テスト"""

        # Step 1: 基本セットアップ
        repository_info = exploration_scenario["target_repository"]
        discovery_result = await explorer_user_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )
        assert discovery_result["success"] is True

        # Step 2: 特定のキーワードでドキュメント検索
        search_keywords = exploration_scenario["search_keywords"]
        found_documents = []

        structure = discovery_result["structure"]
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]

        for keyword in search_keywords:
            # ファイル名ベースの検索
            matching_files = [
                f for f in markdown_files if keyword.lower() in f["name"].lower()
            ]

            for file_info in matching_files[:2]:  # 各キーワードで最大2ファイル
                doc_result = await explorer_user_simulator.view_document(
                    service=repository_info["service"],
                    owner=repository_info["owner"],
                    repo=repository_info["repo"],
                    path=file_info["path"],
                )

                if doc_result["success"]:
                    found_documents.append(
                        {
                            "keyword": keyword,
                            "file": file_info["name"],
                            "path": file_info["path"],
                            "content_length": len(doc_result["content"]),
                        }
                    )

                    explorer_user_simulator.log_user_action(
                        f"キーワード '{keyword}' でドキュメント発見"
                    )

        # Step 3: コンテンツ内キーワード検索
        if found_documents:
            content_matches = []

            for doc_info in found_documents[:3]:  # 最大3つのドキュメントで検索
                # コンテンツを再取得して検索
                doc_result = await explorer_user_simulator.view_document(
                    service=repository_info["service"],
                    owner=repository_info["owner"],
                    repo=repository_info["repo"],
                    path=doc_info["path"],
                )

                if doc_result["success"]:
                    content = doc_result["content"].lower()

                    # 各検索キーワードの出現回数をカウント
                    for keyword in search_keywords:
                        count = content.count(keyword.lower())
                        if count > 0:
                            content_matches.append(
                                {
                                    "document": doc_info["file"],
                                    "keyword": keyword,
                                    "occurrences": count,
                                }
                            )

            explorer_user_simulator.log_user_action(
                f"コンテンツ内で {len(content_matches)} 件のキーワードマッチを発見"
            )

        # Step 4: AIを使った関連ドキュメント発見
        if found_documents:
            ai_discovery_query = (
                f"'{search_keywords[0]}' に関連する他のドキュメントや情報はありますか？"
            )

            # 最初に見つかったドキュメントのコンテキストでAIに問い合わせ
            first_doc = found_documents[0]
            doc_result = await explorer_user_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=first_doc["path"],
            )

            if doc_result["success"]:
                ai_response = await explorer_user_simulator.query_ai_about_document(
                    query=ai_discovery_query, document_context=doc_result["content"]
                )

                if ai_response["success"]:
                    explorer_user_simulator.log_user_action(
                        "AIを活用して関連ドキュメントを発見"
                    )

        # Step 5: 探索結果の検証
        assert (
            len(found_documents) > 0 or len(content_matches) > 0
        ), "検索ベースの探索が失敗"

        journey_summary = explorer_user_simulator.get_journey_summary()
        search_actions = [
            action
            for action in journey_summary["actions"]
            if "検索" in action or "キーワード" in action or "発見" in action
        ]
        assert len(search_actions) >= 2, "十分な検索アクションが実行されていない"

    @pytest.mark.e2e_user_story
    @pytest.mark.document_exploration
    @pytest.mark.metadata_analysis
    @pytest.mark.asyncio
    async def test_metadata_driven_exploration(
        self,
        explorer_user_simulator: FrontendSimulator,
        exploration_scenario: Dict[str, Any],
    ):
        """メタデータドリブンなドキュメント探索テスト"""

        # Step 1: セットアップ
        repository_info = exploration_scenario["target_repository"]
        discovery_result = await explorer_user_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )
        assert discovery_result["success"] is True

        # Step 2: フロントマター付きドキュメントの特定
        structure = discovery_result["structure"]
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]

        frontmatter_documents = []

        for file_info in markdown_files[:5]:  # 最大5ファイルをチェック
            doc_result = await explorer_user_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=file_info["path"],
            )

            if doc_result["success"]:
                metadata = doc_result.get("metadata", {})
                frontmatter = metadata.get("frontmatter", {})

                if frontmatter:
                    frontmatter_documents.append(
                        {
                            "path": file_info["path"],
                            "name": file_info["name"],
                            "frontmatter": frontmatter,
                            "metadata": metadata,
                        }
                    )

                    explorer_user_simulator.log_user_action(
                        f"フロントマター付きドキュメント {file_info['name']} を発見"
                    )

        # Step 3: メタデータによる分類と探索
        if frontmatter_documents:
            # タグベースの分類
            tag_groups = {}
            for doc in frontmatter_documents:
                tags = doc["frontmatter"].get("tags", [])
                for tag in tags:
                    if tag not in tag_groups:
                        tag_groups[tag] = []
                    tag_groups[tag].append(doc)

            explorer_user_simulator.log_user_action(
                f"{len(tag_groups)}個のタググループを特定"
            )

            # 日付ベースの分類
            dated_documents = [
                doc for doc in frontmatter_documents if "date" in doc["frontmatter"]
            ]

            if dated_documents:
                explorer_user_simulator.log_user_action(
                    f"{len(dated_documents)}個の日付付きドキュメントを特定"
                )

            # 著者ベースの分類
            author_groups = {}
            for doc in frontmatter_documents:
                author = doc["frontmatter"].get("author", "unknown")
                if author not in author_groups:
                    author_groups[author] = []
                author_groups[author].append(doc)

            explorer_user_simulator.log_user_action(
                f"{len(author_groups)}人の著者を特定"
            )

        # Step 4: メタデータベースのAI分析
        if frontmatter_documents:
            # メタデータサマリーの作成
            metadata_summary = {
                "total_documents": len(frontmatter_documents),
                "unique_tags": len(tag_groups),
                "unique_authors": len(author_groups),
                "dated_documents": len(dated_documents),
            }

            ai_analysis_query = f"このリポジトリのドキュメントメタデータから、どのような情報構造や傾向が読み取れますか？"

            # 最初のフロントマター付きドキュメントをコンテキストとして使用
            first_doc = frontmatter_documents[0]
            doc_result = await explorer_user_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=first_doc["path"],
            )

            if doc_result["success"]:
                ai_response = await explorer_user_simulator.query_ai_about_document(
                    query=ai_analysis_query, document_context=doc_result["content"]
                )

                if ai_response["success"]:
                    explorer_user_simulator.log_user_action(
                        "AIによるメタデータ分析を実行"
                    )

        # Step 5: 探索結果の検証
        journey_summary = explorer_user_simulator.get_journey_summary()

        metadata_actions = [
            action
            for action in journey_summary["actions"]
            if "メタデータ" in action or "フロントマター" in action or "タグ" in action
        ]

        # メタデータベースの探索が実行されたことを確認
        if frontmatter_documents:
            assert len(metadata_actions) >= 3, "十分なメタデータ探索が実行されていない"
            assert (
                len(frontmatter_documents) > 0
            ), "フロントマター付きドキュメントが見つからない"

        explorer_user_simulator.log_user_action("メタデータドリブン探索完了")

    @pytest.mark.e2e_user_story
    @pytest.mark.document_exploration
    @pytest.mark.link_analysis
    @pytest.mark.asyncio
    async def test_link_based_navigation_exploration(
        self,
        explorer_user_simulator: FrontendSimulator,
        exploration_scenario: Dict[str, Any],
    ):
        """リンクベースのナビゲーション探索テスト"""

        # Step 1: セットアップ
        repository_info = exploration_scenario["target_repository"]
        discovery_result = await explorer_user_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )
        assert discovery_result["success"] is True

        # Step 2: エントリーポイントドキュメントの特定
        structure = discovery_result["structure"]
        entry_point_files = [
            f
            for f in structure["files"]
            if f["name"].lower() in ["readme.md", "index.md", "home.md"]
        ]

        if not entry_point_files:
            # フォールバック: 最初のマークダウンファイル
            markdown_files = [
                f for f in structure["files"] if f["name"].endswith(".md")
            ]
            entry_point_files = markdown_files[:1]

        assert (
            len(entry_point_files) > 0
        ), "エントリーポイントドキュメントが見つからない"

        entry_point = entry_point_files[0]
        explorer_user_simulator.log_user_action(
            f"エントリーポイント {entry_point['name']} を特定"
        )

        # Step 3: リンク分析
        doc_result = await explorer_user_simulator.view_document(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
            path=entry_point["path"],
        )

        assert doc_result["success"] is True
        links = doc_result.get("links", [])

        # リンクタイプの分類
        internal_links = [link for link in links if not link.get("is_external", False)]
        external_links = [link for link in links if link.get("is_external", False)]
        image_links = [link for link in links if link.get("is_image", False)]

        explorer_user_simulator.log_user_action(
            f"リンク分析完了: 内部{len(internal_links)}, 外部{len(external_links)}, 画像{len(image_links)}"
        )

        # Step 4: 内部リンクナビゲーション
        visited_documents = [entry_point["path"]]
        navigation_path = []

        for link in internal_links[:3]:  # 最大3つの内部リンクを辿る
            linked_doc_result = await explorer_user_simulator.follow_document_link(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                link_url=link["url"],
            )

            if linked_doc_result["success"]:
                linked_path = linked_doc_result.get("document_path", link["url"])
                if linked_path not in visited_documents:
                    visited_documents.append(linked_path)
                    navigation_path.append(
                        {
                            "from": entry_point["path"],
                            "to": linked_path,
                            "link_text": link["text"],
                        }
                    )

                    explorer_user_simulator.log_user_action(
                        f"リンク '{link['text']}' を辿ってナビゲーション"
                    )

        # Step 5: リンクグラフの構築
        if len(navigation_path) > 1:
            # 二次リンクの探索
            second_level_links = []

            for nav in navigation_path[:2]:  # 最大2つの二次ドキュメントから
                second_doc_result = await explorer_user_simulator.view_document(
                    service=repository_info["service"],
                    owner=repository_info["owner"],
                    repo=repository_info["repo"],
                    path=nav["to"],
                )

                if second_doc_result["success"]:
                    second_links = second_doc_result.get("links", [])
                    second_internal = [
                        link
                        for link in second_links
                        if not link.get("is_external", False)
                    ]

                    second_level_links.extend(
                        second_internal[:2]
                    )  # 各ドキュメントから最大2リンク

            explorer_user_simulator.log_user_action(
                f"二次リンク {len(second_level_links)} 個を発見"
            )

        # Step 6: ナビゲーション結果の検証
        assert len(visited_documents) > 1, "リンクナビゲーションが実行されていない"

        journey_summary = explorer_user_simulator.get_journey_summary()
        navigation_actions = [
            action
            for action in journey_summary["actions"]
            if "リンク" in action or "ナビゲーション" in action
        ]

        assert (
            len(navigation_actions) >= 2
        ), "十分なナビゲーションアクションが実行されていない"

        explorer_user_simulator.log_user_action(
            f"リンクベース探索完了: {len(visited_documents)}個のドキュメントを探索"
        )
