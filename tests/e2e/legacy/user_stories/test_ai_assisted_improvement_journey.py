"""
AI支援によるドキュメント改善ジャーニーのE2Eテスト

このテストはユーザーがAI機能を活用してドキュメントの
品質改善や理解向上を図る際の典型的なフローをシミュレートします。

User Story:
- ドキュメント作成者として、AIの支援を受けてコンテンツを改善する
- AI分析を通じてドキュメントの問題点や改善点を発見する
- AI提案に基づいて具体的な改善アクションを実行する
"""

import pytest
import asyncio
from typing import Dict, Any, List

from tests.e2e.helpers.frontend_simulator import FrontendSimulator
from tests.e2e.fixtures.user_personas import get_user_persona
from tests.e2e.fixtures.story_scenarios import get_story_scenario


class TestAIAssistedImprovementJourney:
    """AI支援による改善ジャーニーE2Eテスト"""

    @pytest.fixture
    def content_creator_simulator(self) -> FrontendSimulator:
        """コンテンツ作成者向けのフロントエンドシミュレーターを作成"""
        persona = get_user_persona("content_creator")
        return FrontendSimulator(user_persona=persona)

    @pytest.fixture
    def improvement_scenario(self) -> Dict[str, Any]:
        """ドキュメント改善シナリオデータを取得"""
        return get_story_scenario("ai_assisted_improvement")

    @pytest.mark.e2e_user_story
    @pytest.mark.ai_assistance
    @pytest.mark.content_improvement
    @pytest.mark.asyncio
    async def test_comprehensive_document_analysis(
        self,
        content_creator_simulator: FrontendSimulator,
        improvement_scenario: Dict[str, Any],
    ):
        """包括的なドキュメント分析と改善提案テスト"""

        # Step 1: 改善対象ドキュメントの選択
        repository_info = improvement_scenario["target_repository"]
        discovery_result = await content_creator_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )

        assert discovery_result["success"] is True
        content_creator_simulator.log_user_action("改善対象リポジトリにアクセス")

        # 改善対象ドキュメントを特定
        structure = discovery_result["structure"]
        target_files = improvement_scenario.get("target_documents", ["README.md"])

        found_target = None
        for file_info in structure["files"]:
            if any(target in file_info["name"] for target in target_files):
                found_target = file_info
                break

        if not found_target:
            # フォールバック: 最初のマークダウンファイル
            markdown_files = [
                f for f in structure["files"] if f["name"].endswith(".md")
            ]
            found_target = markdown_files[0] if markdown_files else None

        assert found_target is not None, "改善対象ドキュメントが見つからない"

        content_creator_simulator.log_user_action(
            f"改善対象ドキュメント {found_target['name']} を選択"
        )

        # Step 2: ドキュメント内容の取得と初期分析
        doc_result = await content_creator_simulator.view_document(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
            path=found_target["path"],
        )

        assert doc_result["success"] is True
        document_content = doc_result["content"]

        # 基本統計の収集
        content_stats = {
            "length": len(document_content),
            "lines": len(document_content.split("\n")),
            "words": len(document_content.split()),
            "links": len(doc_result.get("links", [])),
            "has_frontmatter": bool(doc_result.get("metadata", {}).get("frontmatter")),
        }

        content_creator_simulator.log_user_action(
            f"ドキュメント分析完了: {content_stats['words']}語, {content_stats['links']}リンク"
        )

        # Step 3: AI による構造分析
        structure_analysis_query = """
        このドキュメントの構造と組織化について分析してください。
        以下の観点で評価をお願いします：
        1. 情報の論理的な流れ
        2. 見出しの階層構造
        3. 読みやすさ
        4. 改善可能な点
        """

        structure_response = await content_creator_simulator.query_ai_about_document(
            query=structure_analysis_query, document_context=document_content
        )

        assert structure_response["success"] is True
        content_creator_simulator.log_user_action("AI構造分析を実行")

        # Step 4: AI による内容品質分析
        quality_analysis_query = """
        このドキュメントの内容品質について分析してください。
        以下の観点で評価をお願いします：
        1. 情報の完全性
        2. 技術的正確性
        3. 対象読者への適切性
        4. 具体的改善提案
        """

        quality_response = await content_creator_simulator.query_ai_about_document(
            query=quality_analysis_query, document_context=document_content
        )

        assert quality_response["success"] is True
        content_creator_simulator.log_user_action("AI品質分析を実行")

        # Step 5: AI による具体的改善提案
        improvement_query = """
        このドキュメントを改善するための具体的な提案をしてください。
        優先度の高い順に、実行可能な改善案を提示してください。
        """

        improvement_response = await content_creator_simulator.query_ai_about_document(
            query=improvement_query, document_context=document_content
        )

        assert improvement_response["success"] is True
        content_creator_simulator.log_user_action("AI改善提案を取得")

        # Step 6: 改善分析結果の統合
        analysis_summary = {
            "document": found_target["name"],
            "content_stats": content_stats,
            "ai_analyses": [
                {"type": "structure", "completed": structure_response["success"]},
                {"type": "quality", "completed": quality_response["success"]},
                {"type": "improvement", "completed": improvement_response["success"]},
            ],
        }

        # 全ての分析が完了したことを確認
        completed_analyses = [
            a for a in analysis_summary["ai_analyses"] if a["completed"]
        ]
        assert len(completed_analyses) == 3, "全てのAI分析が完了していない"

        content_creator_simulator.log_user_action("包括的ドキュメント分析完了")

        # Journey完了確認
        journey_summary = content_creator_simulator.get_journey_summary()
        ai_actions = [action for action in journey_summary["actions"] if "AI" in action]
        assert len(ai_actions) >= 3, "十分なAI分析が実行されていない"

    @pytest.mark.e2e_user_story
    @pytest.mark.ai_assistance
    @pytest.mark.content_optimization
    @pytest.mark.asyncio
    async def test_targeted_content_optimization(
        self,
        content_creator_simulator: FrontendSimulator,
        improvement_scenario: Dict[str, Any],
    ):
        """ターゲット指向のコンテンツ最適化テスト"""

        # Step 1: セットアップ
        repository_info = improvement_scenario["target_repository"]
        discovery_result = await content_creator_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )
        assert discovery_result["success"] is True

        # 複数のドキュメントを対象とした最適化
        structure = discovery_result["structure"]
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]
        target_docs = markdown_files[:3]  # 最大3つのドキュメント

        optimization_results = []

        # Step 2: 各ドキュメントに対する特定目的の最適化
        optimization_goals = [
            "初心者向けの理解しやすさ",
            "SEO最適化",
            "技術的正確性の向上",
        ]

        for i, doc_info in enumerate(target_docs):
            goal = optimization_goals[i % len(optimization_goals)]

            doc_result = await content_creator_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=doc_info["path"],
            )

            if doc_result["success"]:
                optimization_query = f"""
                このドキュメントを「{goal}」の観点で最適化してください。
                具体的な改善点と実装方法を提案してください。
                """

                optimization_response = (
                    await content_creator_simulator.query_ai_about_document(
                        query=optimization_query, document_context=doc_result["content"]
                    )
                )

                if optimization_response["success"]:
                    optimization_results.append(
                        {
                            "document": doc_info["name"],
                            "goal": goal,
                            "content_length": len(doc_result["content"]),
                            "optimized": True,
                        }
                    )

                    content_creator_simulator.log_user_action(
                        f"ドキュメント {doc_info['name']} を {goal} で最適化"
                    )

        # Step 3: 統合的な改善提案
        if optimization_results:
            integration_query = f"""
            以下の{len(optimization_results)}個のドキュメントの最適化結果を踏まえて、
            リポジトリ全体のドキュメント品質向上のための統合的な改善戦略を提案してください。
            """

            # 最初のドキュメントをコンテキストとして使用
            first_doc = target_docs[0]
            doc_result = await content_creator_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=first_doc["path"],
            )

            if doc_result["success"]:
                integration_response = (
                    await content_creator_simulator.query_ai_about_document(
                        query=integration_query, document_context=doc_result["content"]
                    )
                )

                if integration_response["success"]:
                    content_creator_simulator.log_user_action("統合的改善戦略を取得")

        # Step 4: 最適化結果の検証
        assert len(optimization_results) > 0, "コンテンツ最適化が実行されていない"

        successful_optimizations = [r for r in optimization_results if r["optimized"]]
        assert len(successful_optimizations) > 0, "成功した最適化が存在しない"

        content_creator_simulator.log_user_action(
            f"ターゲット最適化完了: {len(successful_optimizations)}個のドキュメントを最適化"
        )

    @pytest.mark.e2e_user_story
    @pytest.mark.ai_assistance
    @pytest.mark.accessibility_improvement
    @pytest.mark.asyncio
    async def test_accessibility_focused_improvement(
        self,
        content_creator_simulator: FrontendSimulator,
        improvement_scenario: Dict[str, Any],
    ):
        """アクセシビリティ重視の改善テスト"""

        # Step 1: セットアップ
        repository_info = improvement_scenario["target_repository"]
        discovery_result = await content_creator_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )
        assert discovery_result["success"] is True

        # Step 2: アクセシビリティ評価対象の選択
        structure = discovery_result["structure"]
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]

        accessibility_results = []

        for doc_info in markdown_files[:2]:  # 最大2つのドキュメントを評価
            doc_result = await content_creator_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=doc_info["path"],
            )

            if doc_result["success"]:
                # リンク分析（画像のalt属性など）
                links = doc_result.get("links", [])
                image_links = [link for link in links if link.get("is_image", False)]

                # Step 3: アクセシビリティ分析
                accessibility_query = """
                このドキュメントのアクセシビリティについて評価してください。
                以下の観点で分析をお願いします：
                1. 見出し構造の適切性
                2. 画像のalt属性
                3. リンクの説明文
                4. 色に依存しない情報伝達
                5. スクリーンリーダー対応
                具体的な改善提案も含めてください。
                """

                accessibility_response = (
                    await content_creator_simulator.query_ai_about_document(
                        query=accessibility_query,
                        document_context=doc_result["content"],
                    )
                )

                if accessibility_response["success"]:
                    accessibility_results.append(
                        {
                            "document": doc_info["name"],
                            "image_count": len(image_links),
                            "total_links": len(links),
                            "accessibility_analyzed": True,
                        }
                    )

                    content_creator_simulator.log_user_action(
                        f"ドキュメント {doc_info['name']} のアクセシビリティを分析"
                    )

        # Step 4: 包括的アクセシビリティ改善提案
        if accessibility_results:
            comprehensive_query = """
            アクセシビリティの観点から、このリポジトリのドキュメント全体を
            改善するための包括的なガイドラインと具体的なアクションプランを提案してください。
            WCAG 2.1準拠を目指した改善案をお願いします。
            """

            # 最初のドキュメントをコンテキストとして使用
            first_doc = markdown_files[0]
            doc_result = await content_creator_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=first_doc["path"],
            )

            if doc_result["success"]:
                comprehensive_response = (
                    await content_creator_simulator.query_ai_about_document(
                        query=comprehensive_query,
                        document_context=doc_result["content"],
                    )
                )

                if comprehensive_response["success"]:
                    content_creator_simulator.log_user_action(
                        "包括的アクセシビリティ改善提案を取得"
                    )

        # Step 5: 結果検証
        assert len(accessibility_results) > 0, "アクセシビリティ分析が実行されていない"

        analyzed_docs = [
            r for r in accessibility_results if r["accessibility_analyzed"]
        ]
        assert len(analyzed_docs) > 0, "成功したアクセシビリティ分析が存在しない"

        content_creator_simulator.log_user_action(
            f"アクセシビリティ改善完了: {len(analyzed_docs)}個のドキュメントを分析"
        )

    @pytest.mark.e2e_user_story
    @pytest.mark.ai_assistance
    @pytest.mark.iterative_improvement
    @pytest.mark.asyncio
    async def test_iterative_improvement_cycle(
        self,
        content_creator_simulator: FrontendSimulator,
        improvement_scenario: Dict[str, Any],
    ):
        """反復的改善サイクルテスト"""

        # Step 1: セットアップ
        repository_info = improvement_scenario["target_repository"]
        discovery_result = await content_creator_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )
        assert discovery_result["success"] is True

        # Step 2: 改善対象ドキュメントの選択
        structure = discovery_result["structure"]
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]
        target_doc = markdown_files[0]  # 最初のドキュメントで反復改善

        improvement_cycles = []

        # Step 3: 反復改善サイクル（3回実行）
        for cycle in range(3):
            cycle_name = f"改善サイクル{cycle + 1}"

            doc_result = await content_creator_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=target_doc["path"],
            )

            if doc_result["success"]:
                # 各サイクルで異なる観点から分析
                analysis_focuses = [
                    "初回評価: 全体的な品質と構造",
                    "第2回評価: 具体性と実用性",
                    "第3回評価: 最終確認と残課題",
                ]

                focus = analysis_focuses[cycle]
                cycle_query = f"""
                {focus}の観点から、このドキュメントを評価してください。
                前回の改善提案を踏まえて、さらなる改善点があれば具体的に提案してください。
                """

                cycle_response = (
                    await content_creator_simulator.query_ai_about_document(
                        query=cycle_query, document_context=doc_result["content"]
                    )
                )

                if cycle_response["success"]:
                    improvement_cycles.append(
                        {
                            "cycle": cycle + 1,
                            "focus": focus,
                            "content_length": len(doc_result["content"]),
                            "completed": True,
                        }
                    )

                    content_creator_simulator.log_user_action(
                        f"{cycle_name}を実行: {focus}"
                    )

        # Step 4: 改善進捗の統合分析
        if len(improvement_cycles) >= 2:
            progress_query = f"""
            {len(improvement_cycles)}回の改善サイクルを通じて、
            このドキュメントの品質向上の進捗と最終的な改善成果を評価してください。
            まだ残っている課題があれば、優先順位と共に提示してください。
            """

            doc_result = await content_creator_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=target_doc["path"],
            )

            if doc_result["success"]:
                progress_response = (
                    await content_creator_simulator.query_ai_about_document(
                        query=progress_query, document_context=doc_result["content"]
                    )
                )

                if progress_response["success"]:
                    content_creator_simulator.log_user_action(
                        "改善進捗の統合分析を実行"
                    )

        # Step 5: 反復改善結果の検証
        assert len(improvement_cycles) >= 2, "十分な反復改善サイクルが実行されていない"

        completed_cycles = [c for c in improvement_cycles if c["completed"]]
        assert len(completed_cycles) >= 2, "成功した改善サイクルが不十分"

        content_creator_simulator.log_user_action(
            f"反復改善完了: {len(completed_cycles)}回のサイクルを実行"
        )

        # Journey完了確認
        journey_summary = content_creator_simulator.get_journey_summary()
        cycle_actions = [
            action for action in journey_summary["actions"] if "サイクル" in action
        ]
        assert len(cycle_actions) >= 2, "十分な反復改善アクションが実行されていない"

    @pytest.mark.e2e_user_story
    @pytest.mark.ai_assistance
    @pytest.mark.collaborative_improvement
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_ai_collaborative_improvement_workflow(
        self,
        content_creator_simulator: FrontendSimulator,
        improvement_scenario: Dict[str, Any],
    ):
        """AI協働改善ワークフローテスト"""

        # Step 1: セットアップ
        repository_info = improvement_scenario["target_repository"]
        discovery_result = await content_creator_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )
        assert discovery_result["success"] is True

        # Step 2: チーム視点での改善計画立案
        structure = discovery_result["structure"]
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]

        planning_query = f"""
        このリポジトリの{len(markdown_files)}個のドキュメントについて、
        チーム協働での改善プロジェクトを計画してください。
        以下を含めた包括的な改善計画を提案してください：
        1. 優先順位付け
        2. 役割分担案
        3. 品質基準
        4. 進捗管理方法
        """

        # 最初のドキュメントをコンテキストとして使用
        first_doc = markdown_files[0]
        doc_result = await content_creator_simulator.view_document(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
            path=first_doc["path"],
        )

        assert doc_result["success"] is True

        planning_response = await content_creator_simulator.query_ai_about_document(
            query=planning_query, document_context=doc_result["content"]
        )

        assert planning_response["success"] is True
        content_creator_simulator.log_user_action("チーム協働改善計画を立案")

        # Step 3: 段階的改善実行シミュレーション
        improvement_phases = [
            "Phase 1: 構造改善",
            "Phase 2: 内容充実",
            "Phase 3: 品質向上",
        ]

        phase_results = []

        for i, phase in enumerate(improvement_phases):
            if i < len(markdown_files):  # ドキュメント数に応じて調整
                target_doc = markdown_files[i]

                doc_result = await content_creator_simulator.view_document(
                    service=repository_info["service"],
                    owner=repository_info["owner"],
                    repo=repository_info["repo"],
                    path=target_doc["path"],
                )

                if doc_result["success"]:
                    phase_query = f"""
                    {phase}として、このドキュメントに対して実行すべき
                    具体的な改善アクションを提案してください。
                    チームメンバーが実行可能な形で詳細に説明してください。
                    """

                    phase_response = (
                        await content_creator_simulator.query_ai_about_document(
                            query=phase_query, document_context=doc_result["content"]
                        )
                    )

                    if phase_response["success"]:
                        phase_results.append(
                            {
                                "phase": phase,
                                "document": target_doc["name"],
                                "completed": True,
                            }
                        )

                        content_creator_simulator.log_user_action(f"{phase}を実行")

        # Step 4: 最終品質評価
        if phase_results:
            final_evaluation_query = f"""
            {len(phase_results)}フェーズの改善作業を完了しました。
            最終的な品質評価として、以下を実行してください：
            1. 改善目標の達成度評価
            2. 残存課題の特定
            3. 今後の保守計画の提案
            4. チーム改善プロセスの評価
            """

            final_response = await content_creator_simulator.query_ai_about_document(
                query=final_evaluation_query, document_context=doc_result["content"]
            )

            if final_response["success"]:
                content_creator_simulator.log_user_action("最終品質評価を実行")

        # Step 5: 協働改善結果の検証
        assert len(phase_results) >= 2, "十分な改善フェーズが実行されていない"

        completed_phases = [p for p in phase_results if p["completed"]]
        assert len(completed_phases) >= 2, "成功した改善フェーズが不十分"

        content_creator_simulator.log_user_action(
            f"AI協働改善完了: {len(completed_phases)}フェーズを実行"
        )

        # Journey完了確認
        journey_summary = content_creator_simulator.get_journey_summary()
        collaborative_actions = [
            action
            for action in journey_summary["actions"]
            if "協働" in action or "チーム" in action or "Phase" in action
        ]
        assert (
            len(collaborative_actions) >= 3
        ), "十分な協働改善アクションが実行されていない"
