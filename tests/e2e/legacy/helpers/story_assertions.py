"""
ユーザーストーリー用のアサーション関数

このモジュールはE2Eテストでユーザーストーリーの
成功基準を検証するための専用アサーション関数を提供します。
"""

from typing import Dict, Any, List, Optional, Union
import pytest
from tests.e2e.helpers.frontend_simulator import FrontendSimulator
from tests.e2e.helpers.user_journey_tracker import UserJourneyTracker


class StoryAssertions:
    """ユーザーストーリー用のアサーション関数集"""

    @staticmethod
    def assert_user_story_completed(
        simulator: FrontendSimulator,
        required_actions: List[str],
        story_name: str = "User Story",
    ) -> None:
        """ユーザーストーリーが完了していることをアサートする"""
        journey_summary = simulator.get_journey_summary()
        completed_actions = journey_summary["actions"]

        missing_actions = []
        for required_action in required_actions:
            if not any(
                required_action.lower() in action.lower()
                for action in completed_actions
            ):
                missing_actions.append(required_action)

        assert (
            len(missing_actions) == 0
        ), f"{story_name}が未完了: 以下のアクションが実行されていません: {missing_actions}"

    @staticmethod
    def assert_minimum_user_interactions(
        simulator: FrontendSimulator,
        min_interactions: int,
        interaction_type: str = "any",
    ) -> None:
        """最小限のユーザーインタラクションが発生していることをアサートする"""
        journey_summary = simulator.get_journey_summary()

        if interaction_type == "any":
            actual_interactions = journey_summary["total_actions"]
        elif interaction_type == "ai":
            ai_actions = [
                action
                for action in journey_summary["actions"]
                if "AI" in action or "問い合わせ" in action
            ]
            actual_interactions = len(ai_actions)
        elif interaction_type == "document":
            doc_actions = [
                action
                for action in journey_summary["actions"]
                if "ドキュメント" in action or "閲覧" in action
            ]
            actual_interactions = len(doc_actions)
        else:
            actual_interactions = journey_summary["total_actions"]

        assert (
            actual_interactions >= min_interactions
        ), f"必要な{interaction_type}インタラクション数({min_interactions})に達していません。実際: {actual_interactions}"

    @staticmethod
    def assert_error_recovery_capability(
        simulator: FrontendSimulator, max_error_rate: float = 0.3
    ) -> None:
        """エラー回復能力があることをアサートする"""
        journey_summary = simulator.get_journey_summary()

        # エラー率のチェック
        assert (
            journey_summary["error_rate"] <= max_error_rate
        ), f"エラー率が許容値({max_error_rate})を超えています。実際: {journey_summary['error_rate']:.2f}"

        # エラーがある場合は回復していることをチェック
        if journey_summary["total_errors"] > 0:
            assert journey_summary[
                "recovered_from_errors"
            ], "エラーが発生しましたが、回復していません"

    @staticmethod
    def assert_ai_interaction_quality(
        simulator: FrontendSimulator,
        min_ai_queries: int = 1,
        expect_successful_responses: bool = True,
    ) -> None:
        """AI相互作用の品質をアサートする"""
        journey_summary = simulator.get_journey_summary()

        # AI問い合わせ回数のチェック
        ai_actions = [
            action
            for action in journey_summary["actions"]
            if "AI" in action or "問い合わせ" in action
        ]

        assert (
            len(ai_actions) >= min_ai_queries
        ), f"AI問い合わせが不十分です。必要: {min_ai_queries}、実際: {len(ai_actions)}"

        if expect_successful_responses:
            # AI応答の成功率をチェック（簡単な推定）
            successful_ai_actions = [
                action
                for action in ai_actions
                if "完了" in action or "取得" in action or "実行" in action
            ]

            ai_success_rate = len(successful_ai_actions) / max(len(ai_actions), 1)
            assert (
                ai_success_rate >= 0.7
            ), f"AI相互作用の成功率が低すぎます。実際: {ai_success_rate:.2f}"

    @staticmethod
    def assert_document_exploration_depth(
        simulator: FrontendSimulator,
        min_documents: int = 1,
        expect_metadata_analysis: bool = True,
        expect_link_following: bool = False,
    ) -> None:
        """ドキュメント探索の深度をアサートする"""
        journey_summary = simulator.get_journey_summary()

        # ドキュメント閲覧数のチェック
        doc_view_actions = [
            action
            for action in journey_summary["actions"]
            if "ドキュメント" in action and "閲覧" in action
        ]

        assert (
            len(doc_view_actions) >= min_documents
        ), f"ドキュメント閲覧数が不十分です。必要: {min_documents}、実際: {len(doc_view_actions)}"

        if expect_metadata_analysis:
            metadata_actions = [
                action
                for action in journey_summary["actions"]
                if "メタデータ" in action or "フロントマター" in action
            ]
            assert len(metadata_actions) > 0, "メタデータ分析が実行されていません"

        if expect_link_following:
            link_actions = [
                action
                for action in journey_summary["actions"]
                if "リンク" in action and "辿" in action
            ]
            assert len(link_actions) > 0, "リンクの追跡が実行されていません"

    @staticmethod
    def assert_collaborative_workflow(
        lead_simulator: FrontendSimulator,
        member_simulator: FrontendSimulator,
        min_collaboration_points: int = 2,
    ) -> None:
        """協働ワークフローが実行されていることをアサートする"""
        lead_summary = lead_simulator.get_journey_summary()
        member_summary = member_simulator.get_journey_summary()

        # 両方のシミュレーターでアクションが実行されていることを確認
        assert (
            lead_summary["total_actions"] > 0
        ), "チームリーダーのアクションが実行されていません"
        assert (
            member_summary["total_actions"] > 0
        ), "チームメンバーのアクションが実行されていません"

        # 協働ポイントの確認
        lead_collab_actions = [
            action
            for action in lead_summary["actions"]
            if any(
                keyword in action for keyword in ["チーム", "協働", "統合", "レビュー"]
            )
        ]
        member_collab_actions = [
            action
            for action in member_summary["actions"]
            if any(
                keyword in action
                for keyword in ["チーム", "協働", "分析", "フィードバック"]
            )
        ]

        total_collab_points = len(lead_collab_actions) + len(member_collab_actions)

        assert (
            total_collab_points >= min_collaboration_points
        ), f"協働ポイントが不十分です。必要: {min_collaboration_points}、実際: {total_collab_points}"

    @staticmethod
    def assert_improvement_cycle_execution(
        simulator: FrontendSimulator,
        min_cycles: int = 2,
        expect_iterative_feedback: bool = True,
    ) -> None:
        """改善サイクルが実行されていることをアサートする"""
        journey_summary = simulator.get_journey_summary()

        # 改善サイクルの検出
        cycle_actions = [
            action
            for action in journey_summary["actions"]
            if "サイクル" in action or "改善" in action
        ]

        assert (
            len(cycle_actions) >= min_cycles
        ), f"改善サイクルが不十分です。必要: {min_cycles}、実際: {len(cycle_actions)}"

        if expect_iterative_feedback:
            feedback_actions = [
                action
                for action in journey_summary["actions"]
                if "フィードバック" in action or "評価" in action
            ]
            assert len(feedback_actions) > 0, "反復的フィードバックが実行されていません"

    @staticmethod
    def assert_onboarding_completion(
        simulator: FrontendSimulator,
        expect_system_access: bool = True,
        expect_first_document: bool = True,
        expect_ai_trial: bool = True,
    ) -> None:
        """オンボーディングが完了していることをアサートする"""
        journey_summary = simulator.get_journey_summary()

        if expect_system_access:
            system_actions = [
                action
                for action in journey_summary["actions"]
                if "システム" in action or "アクセス" in action
            ]
            assert len(system_actions) > 0, "システムアクセスが実行されていません"

        if expect_first_document:
            first_doc_actions = [
                action
                for action in journey_summary["actions"]
                if "最初" in action and "ドキュメント" in action
            ]
            assert (
                len(first_doc_actions) > 0
            ), "最初のドキュメント閲覧が実行されていません"

        if expect_ai_trial:
            ai_trial_actions = [
                action
                for action in journey_summary["actions"]
                if "初回" in action and "AI" in action
            ]
            assert len(ai_trial_actions) > 0, "初回AI試用が実行されていません"


class PerformanceAssertions:
    """パフォーマンス関連のアサーション関数集"""

    @staticmethod
    def assert_response_time_acceptable(
        simulator: FrontendSimulator, max_average_response_time: float = 5.0
    ) -> None:
        """レスポンス時間が許容範囲内であることをアサートする"""
        # NOTE: 実際の実装では、FrontendSimulatorでレスポンス時間を測定する必要があります
        journey_summary = simulator.get_journey_summary()

        # 簡単な推定: アクション数と時間から平均レスポンス時間を算出
        if journey_summary["total_actions"] > 0:
            avg_response_time = (
                journey_summary["journey_duration_seconds"]
                / journey_summary["total_actions"]
            )

            assert (
                avg_response_time <= max_average_response_time
            ), f"平均レスポンス時間が許容値を超えています。許容値: {max_average_response_time}s、実際: {avg_response_time:.2f}s"

    @staticmethod
    def assert_user_efficiency(
        simulator: FrontendSimulator, min_actions_per_minute: float = 2.0
    ) -> None:
        """ユーザー効率が期待値以上であることをアサートする"""
        journey_summary = simulator.get_journey_summary()

        if journey_summary["journey_duration_seconds"] > 0:
            actions_per_minute = (
                journey_summary["total_actions"]
                / journey_summary["journey_duration_seconds"]
            ) * 60

            assert (
                actions_per_minute >= min_actions_per_minute
            ), f"ユーザー効率が低すぎます。期待: {min_actions_per_minute}アクション/分、実際: {actions_per_minute:.2f}アクション/分"


class QualityAssertions:
    """品質関連のアサーション関数集"""

    @staticmethod
    def assert_content_analysis_depth(
        simulator: FrontendSimulator,
        analysis_types: List[str],
        min_analyses_per_type: int = 1,
    ) -> None:
        """コンテンツ分析の深度をアサートする"""
        journey_summary = simulator.get_journey_summary()

        for analysis_type in analysis_types:
            analysis_actions = [
                action
                for action in journey_summary["actions"]
                if analysis_type in action
            ]

            assert (
                len(analysis_actions) >= min_analyses_per_type
            ), f"{analysis_type}分析が不十分です。必要: {min_analyses_per_type}、実際: {len(analysis_actions)}"

    @staticmethod
    def assert_accessibility_consideration(
        simulator: FrontendSimulator, expect_accessibility_analysis: bool = True
    ) -> None:
        """アクセシビリティが考慮されていることをアサートする"""
        if expect_accessibility_analysis:
            journey_summary = simulator.get_journey_summary()
            accessibility_actions = [
                action
                for action in journey_summary["actions"]
                if "アクセシビリティ" in action
            ]

            assert (
                len(accessibility_actions) > 0
            ), "アクセシビリティ分析が実行されていません"

    @staticmethod
    def assert_multi_perspective_analysis(
        simulator: FrontendSimulator,
        required_perspectives: List[str],
        min_analyses_per_perspective: int = 1,
    ) -> None:
        """多角的分析が実行されていることをアサートする"""
        journey_summary = simulator.get_journey_summary()

        for perspective in required_perspectives:
            perspective_actions = [
                action for action in journey_summary["actions"] if perspective in action
            ]

            assert (
                len(perspective_actions) >= min_analyses_per_perspective
            ), f"{perspective}の観点からの分析が不十分です。必要: {min_analyses_per_perspective}、実際: {len(perspective_actions)}"


# カスタムpytestマーカー用のアサーション統合関数
def assert_user_story_success(
    simulator: FrontendSimulator, story_type: str, **kwargs
) -> None:
    """ユーザーストーリータイプに応じた成功基準をアサートする統合関数"""

    if story_type == "onboarding":
        StoryAssertions.assert_onboarding_completion(
            simulator,
            expect_system_access=kwargs.get("expect_system_access", True),
            expect_first_document=kwargs.get("expect_first_document", True),
            expect_ai_trial=kwargs.get("expect_ai_trial", True),
        )
        StoryAssertions.assert_minimum_user_interactions(
            simulator, min_interactions=kwargs.get("min_interactions", 5)
        )

    elif story_type == "document_exploration":
        StoryAssertions.assert_document_exploration_depth(
            simulator,
            min_documents=kwargs.get("min_documents", 2),
            expect_metadata_analysis=kwargs.get("expect_metadata_analysis", True),
            expect_link_following=kwargs.get("expect_link_following", False),
        )
        StoryAssertions.assert_minimum_user_interactions(
            simulator,
            min_interactions=kwargs.get("min_interactions", 3),
            interaction_type="document",
        )

    elif story_type == "ai_assistance":
        StoryAssertions.assert_ai_interaction_quality(
            simulator,
            min_ai_queries=kwargs.get("min_ai_queries", 2),
            expect_successful_responses=kwargs.get("expect_successful_responses", True),
        )
        StoryAssertions.assert_improvement_cycle_execution(
            simulator,
            min_cycles=kwargs.get("min_cycles", 1),
            expect_iterative_feedback=kwargs.get("expect_iterative_feedback", True),
        )

    elif story_type == "team_collaboration":
        # team_collaborationの場合は、複数のシミュレーターが必要
        lead_simulator = kwargs.get("lead_simulator")
        member_simulator = kwargs.get("member_simulator")

        if lead_simulator and member_simulator:
            StoryAssertions.assert_collaborative_workflow(
                lead_simulator,
                member_simulator,
                min_collaboration_points=kwargs.get("min_collaboration_points", 2),
            )

    # 共通のエラー回復能力チェック
    StoryAssertions.assert_error_recovery_capability(
        simulator, max_error_rate=kwargs.get("max_error_rate", 0.3)
    )
