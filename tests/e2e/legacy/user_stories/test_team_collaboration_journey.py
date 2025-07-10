"""
チーム連携・協働ドキュメント管理ジャーニーのE2Eテスト

このテストは複数のチームメンバーが連携してドキュメントを
管理・改善する際の典型的なフローをシミュレートします。

User Story:
- チームメンバーとして、他のメンバーと連携してドキュメントを管理する
- レビュープロセスを通じて品質を向上させる
- ナレッジ共有と継続的改善を実現する
"""

import pytest
import asyncio
from typing import Dict, Any, List

from tests.e2e.helpers.frontend_simulator import FrontendSimulator
from tests.e2e.fixtures.user_personas import get_user_persona
from tests.e2e.fixtures.story_scenarios import get_story_scenario


class TestTeamCollaborationJourney:
    """チーム連携ジャーニーE2Eテスト"""

    @pytest.fixture
    def team_lead_simulator(self) -> FrontendSimulator:
        """チームリーダー向けのフロントエンドシミュレーターを作成"""
        persona = get_user_persona("team_lead")
        return FrontendSimulator(user_persona=persona)

    @pytest.fixture
    def team_member_simulator(self) -> FrontendSimulator:
        """チームメンバー向けのフロントエンドシミュレーターを作成"""
        persona = get_user_persona("team_member")
        return FrontendSimulator(user_persona=persona)

    @pytest.fixture
    def collaboration_scenario(self) -> Dict[str, Any]:
        """チーム連携シナリオデータを取得"""
        return get_story_scenario("team_collaboration")

    @pytest.mark.e2e_user_story
    @pytest.mark.team_collaboration
    @pytest.mark.document_review
    @pytest.mark.asyncio
    async def test_collaborative_document_review_process(
        self,
        team_lead_simulator: FrontendSimulator,
        team_member_simulator: FrontendSimulator,
        collaboration_scenario: Dict[str, Any],
    ):
        """協働ドキュメントレビュープロセステスト"""

        # Step 1: チームリーダーによる初期セットアップ
        repository_info = collaboration_scenario["target_repository"]

        lead_discovery = await team_lead_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )

        assert lead_discovery["success"] is True
        team_lead_simulator.log_user_action("チームリーダーがリポジトリアクセス")

        # レビュー対象ドキュメントの特定
        structure = lead_discovery["structure"]
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]
        review_targets = markdown_files[:2]  # 最大2つのドキュメントをレビュー対象

        team_lead_simulator.log_user_action(
            f"{len(review_targets)}個のドキュメントをレビュー対象に選定"
        )

        # Step 2: チームリーダーによる初期レビュー
        lead_review_results = []

        for doc_info in review_targets:
            doc_result = await team_lead_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=doc_info["path"],
            )

            if doc_result["success"]:
                # リーダーレビュー観点
                lead_review_query = f"""
                チームリーダーとして、このドキュメント「{doc_info['name']}」を
                以下の観点でレビューしてください：
                1. チーム標準への準拠
                2. 情報の一貫性
                3. 保守性
                4. チームメンバーへのレビュー指示
                """

                lead_review_response = (
                    await team_lead_simulator.query_ai_about_document(
                        query=lead_review_query, document_context=doc_result["content"]
                    )
                )

                if lead_review_response["success"]:
                    lead_review_results.append(
                        {
                            "document": doc_info["name"],
                            "path": doc_info["path"],
                            "leader_reviewed": True,
                            "content_length": len(doc_result["content"]),
                        }
                    )

                    team_lead_simulator.log_user_action(
                        f"リーダーレビュー完了: {doc_info['name']}"
                    )

        # Step 3: チームメンバーによる並行レビュー
        member_review_results = []

        # チームメンバーも同じリポジトリにアクセス
        member_discovery = await team_member_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )

        assert member_discovery["success"] is True
        team_member_simulator.log_user_action("チームメンバーがリポジトリアクセス")

        for review_target in lead_review_results:
            doc_result = await team_member_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=review_target["path"],
            )

            if doc_result["success"]:
                # メンバーレビュー観点
                member_review_query = f"""
                チームメンバーとして、このドキュメント「{review_target['document']}」を
                以下の観点でレビューしてください：
                1. 技術的正確性
                2. 実用性と使いやすさ
                3. 具体的改善提案
                4. 疑問点や不明な箇所
                """

                member_review_response = (
                    await team_member_simulator.query_ai_about_document(
                        query=member_review_query,
                        document_context=doc_result["content"],
                    )
                )

                if member_review_response["success"]:
                    member_review_results.append(
                        {
                            "document": review_target["document"],
                            "path": review_target["path"],
                            "member_reviewed": True,
                        }
                    )

                    team_member_simulator.log_user_action(
                        f"メンバーレビュー完了: {review_target['document']}"
                    )

        # Step 4: レビュー結果の統合と討議シミュレーション
        if lead_review_results and member_review_results:
            # 統合レビュー会議シミュレーション
            integration_query = f"""
            チームレビュー会議として、以下のドキュメントレビュー結果を統合し、
            最終的な改善計画を策定してください：
            - レビュー対象: {len(lead_review_results)}個のドキュメント
            - チームリーダーレビュー完了
            - チームメンバーレビュー完了
            
            統合的な改善優先順位と実行計画を提案してください。
            """

            # 最初のドキュメントをコンテキストとして使用
            first_doc = review_targets[0]
            doc_result = await team_lead_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=first_doc["path"],
            )

            if doc_result["success"]:
                integration_response = (
                    await team_lead_simulator.query_ai_about_document(
                        query=integration_query, document_context=doc_result["content"]
                    )
                )

                if integration_response["success"]:
                    team_lead_simulator.log_user_action(
                        "レビュー結果統合と改善計画策定"
                    )

        # Step 5: 協働レビュー結果の検証
        assert len(lead_review_results) > 0, "リーダーレビューが実行されていない"
        assert len(member_review_results) > 0, "メンバーレビューが実行されていない"

        # 両方のレビューが同じドキュメントをカバーしていることを確認
        reviewed_docs = set([r["document"] for r in lead_review_results])
        member_reviewed_docs = set([r["document"] for r in member_review_results])
        common_reviewed = reviewed_docs.intersection(member_reviewed_docs)

        assert (
            len(common_reviewed) > 0
        ), "共通してレビューされたドキュメントが存在しない"

        team_lead_simulator.log_user_action(
            f"協働レビュー完了: {len(common_reviewed)}個のドキュメント"
        )

    @pytest.mark.e2e_user_story
    @pytest.mark.team_collaboration
    @pytest.mark.knowledge_sharing
    @pytest.mark.asyncio
    async def test_team_knowledge_sharing_workflow(
        self,
        team_lead_simulator: FrontendSimulator,
        team_member_simulator: FrontendSimulator,
        collaboration_scenario: Dict[str, Any],
    ):
        """チームナレッジ共有ワークフローテスト"""

        # Step 1: ナレッジ共有対象の特定
        repository_info = collaboration_scenario["target_repository"]

        discovery_result = await team_lead_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )

        assert discovery_result["success"] is True

        structure = discovery_result["structure"]
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]

        # ナレッジ共有価値の高いドキュメントを特定
        knowledge_candidates = []

        for doc_info in markdown_files[:3]:  # 最大3つを評価
            doc_result = await team_lead_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=doc_info["path"],
            )

            if doc_result["success"]:
                knowledge_value_query = f"""
                このドキュメント「{doc_info['name']}」について、
                チーム内でのナレッジ共有価値を評価してください：
                1. 新メンバーのオンボーディング価値
                2. 専門知識の共有価値
                3. ベストプラクティスの学習価値
                4. 具体的な共有方法の提案
                """

                value_response = await team_lead_simulator.query_ai_about_document(
                    query=knowledge_value_query, document_context=doc_result["content"]
                )

                if value_response["success"]:
                    knowledge_candidates.append(
                        {
                            "document": doc_info["name"],
                            "path": doc_info["path"],
                            "knowledge_value_assessed": True,
                        }
                    )

                    team_lead_simulator.log_user_action(
                        f"ナレッジ価値評価: {doc_info['name']}"
                    )

        # Step 2: チームメンバーによるナレッジ習得
        learning_results = []

        for candidate in knowledge_candidates:
            doc_result = await team_member_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=candidate["path"],
            )

            if doc_result["success"]:
                learning_query = f"""
                新しいチームメンバーとして、このドキュメント「{candidate['document']}」から
                学習すべき重要なポイントを抽出してください：
                1. 必須知識
                2. 実践的なスキル
                3. 注意すべき点
                4. さらに学習が必要な領域
                """

                learning_response = await team_member_simulator.query_ai_about_document(
                    query=learning_query, document_context=doc_result["content"]
                )

                if learning_response["success"]:
                    learning_results.append(
                        {"document": candidate["document"], "learning_completed": True}
                    )

                    team_member_simulator.log_user_action(
                        f"ナレッジ学習完了: {candidate['document']}"
                    )

        # Step 3: ナレッジギャップの特定
        if learning_results:
            gap_analysis_query = f"""
            {len(learning_results)}個のドキュメントを学習した結果として、
            チーム内で不足しているナレッジや文書化されていない知識を特定してください。
            新メンバーが困る可能性のある領域と、その解決策を提案してください。
            """

            # 最初の学習ドキュメントをコンテキストとして使用
            first_candidate = knowledge_candidates[0]
            doc_result = await team_member_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=first_candidate["path"],
            )

            if doc_result["success"]:
                gap_response = await team_member_simulator.query_ai_about_document(
                    query=gap_analysis_query, document_context=doc_result["content"]
                )

                if gap_response["success"]:
                    team_member_simulator.log_user_action("ナレッジギャップ分析完了")

        # Step 4: ナレッジ改善提案の協働作成
        if knowledge_candidates and learning_results:
            improvement_proposal_query = f"""
            チームリーダーとして、ナレッジ共有の改善提案を作成してください：
            1. 現在のナレッジ共有の評価
            2. 改善が必要な領域
            3. 具体的な実施計画
            4. 成果測定方法
            """

            proposal_response = await team_lead_simulator.query_ai_about_document(
                query=improvement_proposal_query, document_context=doc_result["content"]
            )

            if proposal_response["success"]:
                team_lead_simulator.log_user_action("ナレッジ共有改善提案作成")

        # Step 5: ナレッジ共有結果の検証
        assert len(knowledge_candidates) > 0, "ナレッジ価値評価が実行されていない"
        assert len(learning_results) > 0, "ナレッジ学習が実行されていない"

        team_lead_simulator.log_user_action(
            f"ナレッジ共有完了: {len(learning_results)}個のドキュメント"
        )

    @pytest.mark.e2e_user_story
    @pytest.mark.team_collaboration
    @pytest.mark.process_improvement
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_continuous_improvement_process(
        self,
        team_lead_simulator: FrontendSimulator,
        team_member_simulator: FrontendSimulator,
        collaboration_scenario: Dict[str, Any],
    ):
        """継続的改善プロセステスト"""

        # Step 1: 現状のプロセス評価
        repository_info = collaboration_scenario["target_repository"]

        discovery_result = await team_lead_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )

        assert discovery_result["success"] is True

        # プロセス評価のためのベースライン設定
        structure = discovery_result["structure"]
        total_docs = len([f for f in structure["files"] if f["name"].endswith(".md")])

        baseline_query = f"""
        このリポジトリの{total_docs}個のドキュメントについて、
        現在のドキュメント管理プロセスを評価してください：
        1. 品質の一貫性
        2. 保守性
        3. チーム間の連携状況
        4. 改善の機会
        """

        # 代表的なドキュメントを選択
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]
        baseline_doc = markdown_files[0] if markdown_files else None

        if baseline_doc:
            doc_result = await team_lead_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=baseline_doc["path"],
            )

            if doc_result["success"]:
                baseline_response = await team_lead_simulator.query_ai_about_document(
                    query=baseline_query, document_context=doc_result["content"]
                )

                if baseline_response["success"]:
                    team_lead_simulator.log_user_action("プロセス現状評価完了")

        # Step 2: チームメンバーからのフィードバック収集
        feedback_results = []

        for doc_info in markdown_files[:2]:  # 最大2つのドキュメントでフィードバック
            doc_result = await team_member_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=doc_info["path"],
            )

            if doc_result["success"]:
                feedback_query = f"""
                実際の利用者として、このドキュメント「{doc_info['name']}」と
                関連するプロセスについてフィードバックをお願いします：
                1. 使いやすさ
                2. 情報の見つけやすさ
                3. 作業効率への影響
                4. 改善提案
                """

                feedback_response = await team_member_simulator.query_ai_about_document(
                    query=feedback_query, document_context=doc_result["content"]
                )

                if feedback_response["success"]:
                    feedback_results.append(
                        {"document": doc_info["name"], "feedback_collected": True}
                    )

                    team_member_simulator.log_user_action(
                        f"フィードバック提供: {doc_info['name']}"
                    )

        # Step 3: 改善計画の策定
        if feedback_results:
            improvement_plan_query = f"""
            {len(feedback_results)}件のフィードバックを踏まえて、
            チーム全体のドキュメント管理プロセス改善計画を策定してください：
            1. 優先改善項目
            2. 実施スケジュール
            3. 責任者とリソース
            4. 成果指標
            5. リスク管理
            """

            plan_response = await team_lead_simulator.query_ai_about_document(
                query=improvement_plan_query, document_context=doc_result["content"]
            )

            if plan_response["success"]:
                team_lead_simulator.log_user_action("改善計画策定完了")

        # Step 4: 改善実施シミュレーション
        improvement_implementations = []

        implementation_phases = [
            "Phase 1: 即座に実施可能な改善",
            "Phase 2: 中期的な構造改善",
            "Phase 3: 長期的な文化改善",
        ]

        for i, phase in enumerate(implementation_phases):
            if i < len(feedback_results):  # フィードバック数に応じて調整
                implementation_query = f"""
                {phase}として、具体的な改善アクションを実施してください。
                実施内容と期待される効果を詳細に説明してください。
                """

                implementation_response = (
                    await team_lead_simulator.query_ai_about_document(
                        query=implementation_query,
                        document_context=doc_result["content"],
                    )
                )

                if implementation_response["success"]:
                    improvement_implementations.append(
                        {"phase": phase, "implemented": True}
                    )

                    team_lead_simulator.log_user_action(f"改善実施: {phase}")

        # Step 5: 改善効果の測定
        if improvement_implementations:
            measurement_query = f"""
            {len(improvement_implementations)}フェーズの改善実施後の効果測定を行ってください：
            1. 目標達成度
            2. 予期しない効果
            3. 残存課題
            4. 次期改善サイクルへの提言
            """

            measurement_response = await team_lead_simulator.query_ai_about_document(
                query=measurement_query, document_context=doc_result["content"]
            )

            if measurement_response["success"]:
                team_lead_simulator.log_user_action("改善効果測定完了")

        # Step 6: 継続的改善結果の検証
        assert len(feedback_results) > 0, "フィードバック収集が実行されていない"
        assert len(improvement_implementations) > 0, "改善実施が実行されていない"

        # 両方のシミュレーターでアクションが実行されたことを確認
        lead_summary = team_lead_simulator.get_journey_summary()
        member_summary = team_member_simulator.get_journey_summary()

        lead_improvement_actions = [a for a in lead_summary["actions"] if "改善" in a]
        member_feedback_actions = [
            a for a in member_summary["actions"] if "フィードバック" in a
        ]

        assert len(lead_improvement_actions) >= 2, "リーダーの改善アクションが不十分"
        assert (
            len(member_feedback_actions) >= 1
        ), "メンバーのフィードバックアクションが不十分"

        team_lead_simulator.log_user_action(
            f"継続的改善プロセス完了: {len(improvement_implementations)}フェーズ実施"
        )

    @pytest.mark.e2e_user_story
    @pytest.mark.team_collaboration
    @pytest.mark.cross_functional
    @pytest.mark.asyncio
    async def test_cross_functional_collaboration(
        self,
        team_lead_simulator: FrontendSimulator,
        team_member_simulator: FrontendSimulator,
        collaboration_scenario: Dict[str, Any],
    ):
        """機能横断的協働テスト"""

        # Step 1: 機能横断プロジェクトの開始
        repository_info = collaboration_scenario["target_repository"]

        # チームリーダーによるプロジェクト初期化
        discovery_result = await team_lead_simulator.discover_repository(
            service=repository_info["service"],
            owner=repository_info["owner"],
            repo=repository_info["repo"],
        )

        assert discovery_result["success"] is True

        structure = discovery_result["structure"]
        markdown_files = [f for f in structure["files"] if f["name"].endswith(".md")]

        project_planning_query = f"""
        機能横断的なドキュメント改善プロジェクトを開始します。
        {len(markdown_files)}個のドキュメントについて、以下の観点で計画を立ててください：
        1. 技術チーム担当領域
        2. デザインチーム担当領域
        3. プロダクトチーム担当領域
        4. 協働が必要な領域
        5. 統合スケジュール
        """

        if markdown_files:
            first_doc = markdown_files[0]
            doc_result = await team_lead_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=first_doc["path"],
            )

            if doc_result["success"]:
                planning_response = await team_lead_simulator.query_ai_about_document(
                    query=project_planning_query, document_context=doc_result["content"]
                )

                if planning_response["success"]:
                    team_lead_simulator.log_user_action("機能横断プロジェクト計画策定")

        # Step 2: 各機能チームの専門分析
        functional_analyses = []

        # 技術チーム視点（チームメンバーが担当）
        for doc_info in markdown_files[:2]:  # 最大2つのドキュメント
            doc_result = await team_member_simulator.view_document(
                service=repository_info["service"],
                owner=repository_info["owner"],
                repo=repository_info["repo"],
                path=doc_info["path"],
            )

            if doc_result["success"]:
                tech_analysis_query = f"""
                技術チームメンバーとして、このドキュメント「{doc_info['name']}」を
                以下の技術的観点で分析してください：
                1. 技術的正確性
                2. API/インターフェース仕様
                3. パフォーマンス考慮事項
                4. セキュリティ観点
                5. 他チームとの技術連携ポイント
                """

                tech_response = await team_member_simulator.query_ai_about_document(
                    query=tech_analysis_query, document_context=doc_result["content"]
                )

                if tech_response["success"]:
                    functional_analyses.append(
                        {
                            "document": doc_info["name"],
                            "team": "技術",
                            "analysis_completed": True,
                        }
                    )

                    team_member_simulator.log_user_action(
                        f"技術チーム分析: {doc_info['name']}"
                    )

        # Step 3: 統合的品質保証（チームリーダー）
        if functional_analyses:
            integration_query = f"""
            機能横断的な観点から、以下の分析結果を統合してください：
            - {len(functional_analyses)}個のドキュメントの技術分析完了
            
            統合的な品質保証として：
            1. 機能間の整合性確認
            2. 情報の重複や矛盾の特定
            3. ユーザーエクスペリエンスの統一性
            4. 全体最適化の提案
            """

            integration_response = await team_lead_simulator.query_ai_about_document(
                query=integration_query, document_context=doc_result["content"]
            )

            if integration_response["success"]:
                team_lead_simulator.log_user_action("機能横断統合品質保証実施")

        # Step 4: 協働改善アクションの実行
        collaborative_actions = []

        action_types = [
            "技術仕様の統一化",
            "ユーザビリティの向上",
            "情報アーキテクチャの最適化",
        ]

        for i, action_type in enumerate(action_types):
            if i < len(functional_analyses):
                action_query = f"""
                機能横断チームで「{action_type}」を実行してください。
                各チームの専門性を活かした具体的なアクションプランと
                期待される統合効果を説明してください。
                """

                # 交互にリーダーとメンバーが実行
                simulator = team_lead_simulator if i % 2 == 0 else team_member_simulator

                action_response = await simulator.query_ai_about_document(
                    query=action_query, document_context=doc_result["content"]
                )

                if action_response["success"]:
                    collaborative_actions.append(
                        {
                            "action_type": action_type,
                            "executor": "リーダー" if i % 2 == 0 else "メンバー",
                            "completed": True,
                        }
                    )

                    simulator.log_user_action(f"協働アクション実行: {action_type}")

        # Step 5: 機能横断成果の評価
        if collaborative_actions:
            evaluation_query = f"""
            機能横断的協働プロジェクトの成果を評価してください：
            - 実行アクション数: {len(collaborative_actions)}
            - 機能分析数: {len(functional_analyses)}
            
            以下の観点で総合評価をお願いします：
            1. チーム間協働の効果
            2. 品質向上の達成度
            3. プロセス改善の成果
            4. 今後の機能横断協働への提言
            """

            evaluation_response = await team_lead_simulator.query_ai_about_document(
                query=evaluation_query, document_context=doc_result["content"]
            )

            if evaluation_response["success"]:
                team_lead_simulator.log_user_action("機能横断成果評価完了")

        # Step 6: 機能横断協働結果の検証
        assert len(functional_analyses) > 0, "機能分析が実行されていない"
        assert len(collaborative_actions) > 0, "協働アクションが実行されていない"

        # 両方のシミュレーターで機能横断アクションが実行されたことを確認
        lead_summary = team_lead_simulator.get_journey_summary()
        member_summary = team_member_simulator.get_journey_summary()

        lead_cross_actions = [
            a for a in lead_summary["actions"] if "機能横断" in a or "統合" in a
        ]
        member_cross_actions = [
            a for a in member_summary["actions"] if "技術" in a or "協働" in a
        ]

        assert len(lead_cross_actions) >= 2, "リーダーの機能横断アクションが不十分"
        assert len(member_cross_actions) >= 1, "メンバーの機能横断アクションが不十分"

        team_lead_simulator.log_user_action(
            f"機能横断協働完了: {len(collaborative_actions)}アクション実行"
        )
