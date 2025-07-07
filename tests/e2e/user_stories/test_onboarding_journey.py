"""
新規ユーザーのオンボーディングジャーニーのE2Eテスト

このテストは実際のユーザーが初めてシステムを使用する際の
典型的なフローをシミュレートします。

User Story:
- 新規ユーザーとして、ドキュメントAIヘルパーを初めて使用する
- 基本的な機能を理解し、最初のリポジトリを追加する
- サンプルドキュメントを閲覧し、AI機能を試用する
"""

import pytest
import asyncio
from pathlib import Path
from typing import Dict, Any, List

from tests.e2e.helpers import (
    FrontendSimulator,
    ScenarioRunner,
    PerformanceMonitor,
    DataValidator,
    TestDataGenerator,
    StoryAssertions,
    UserJourneyTracker,
)


class TestOnboardingJourney:
    """新規ユーザーのオンボーディングジャーニーE2Eテスト"""

    @pytest.fixture
    def scenario_runner(self) -> ScenarioRunner:
        """シナリオランナーを作成"""
        fixtures_path = Path(__file__).parent.parent / "fixtures"
        return ScenarioRunner(fixtures_path)

    @pytest.fixture
    def test_data_generator(self) -> TestDataGenerator:
        """テストデータジェネレーターを作成"""
        return TestDataGenerator(seed=42)  # 再現可能なテスト用

    @pytest.fixture
    def new_user_simulator(self, scenario_runner: ScenarioRunner) -> FrontendSimulator:
        """新規ユーザー向けのフロントエンドシミュレーターを作成"""
        # APIクライアントの作成（必要に応じて実装）
        from tests.e2e.helpers.api_client import BackendAPIClient

        api_client = BackendAPIClient()
        return FrontendSimulator(backend_api_client=api_client)

    @pytest.mark.e2e_user_story
    @pytest.mark.onboarding
    @pytest.mark.asyncio
    async def test_complete_onboarding_flow(
        self,
        new_user_simulator: FrontendSimulator,
        scenario_runner: ScenarioRunner,
        test_data_generator: TestDataGenerator,
    ):
        """完全なオンボーディングフローのテスト"""

        # ユーザーペルソナを取得
        persona = scenario_runner.get_persona("new_user") or {
            "id": "new_user",
            "name": "New User",
            "role": "developer",
            "experience_level": "beginner",
        }

        # ジャーニートラッカーを作成
        journey_tracker = UserJourneyTracker(persona)

        # ユーザーセッションを開始
        session = new_user_simulator.start_session(persona["id"], {"first_visit": True})
        journey_tracker.log_action("ユーザーセッション開始")

        async with scenario_runner.run_scenario(
            "onboarding_basic",
            "new_user",
            new_user_simulator.api_client.client,
        ) as context:
            # Step 1: システムヘルスチェック（フロントエンドの初期化として）
            health_response = await new_user_simulator.api_client.health_check()
            journey_tracker.log_action(
                "システムアクセス",
                {"health_status": "healthy" if health_response else "unhealthy"},
            )

            # バリデーション
            health_validation = context.data_validator.validate_custom(
                health_response, "api_response", expected_status=200
            )
            assert (
                health_validation.is_valid
            ), f"Health check failed: {health_validation.errors}"

            # Step 2: リポジトリ設定とテストデータ生成
            repo_config = test_data_generator.generate_repository_config(
                service="github", owner="microsoft", repo="vscode"
            )
            context.set_test_data("repository", repo_config)
            journey_tracker.log_action("リポジトリ設定", repo_config)

            # Step 3: リポジトリ接続（フロントエンドシミュレーション）
            connection_result = await new_user_simulator.connect_to_repository(
                service=repo_config["service"],
                owner=repo_config["owner"],
                repo=repo_config["repo"],
                user_context={"is_first_time": True, "skill_level": "beginner"},
            )
            journey_tracker.log_action(
                "リポジトリ接続完了",
                {
                    "status": connection_result["status"],
                    "recommendations_count": len(
                        connection_result.get("recommended_first_steps", [])
                    ),
                },
            )

            # バリデーション：リポジトリ接続成功
            assert connection_result["status"] == "connected"
            assert "repository_info" in connection_result
            assert "recommended_first_steps" in connection_result

            # Step 4: 初心者向けガイダンス取得
            guidance = await new_user_simulator.get_beginner_guidance(
                connection_result["repository_info"]
            )
            journey_tracker.log_action(
                "初心者ガイダンス取得",
                {"guidance_items": len(guidance.get("guidance_items", []))},
            )

            # Step 5: 推奨されたドキュメントの閲覧
            first_steps = connection_result.get("recommended_first_steps", [])
            if first_steps:
                first_doc = first_steps[0]
                if "path" in first_doc:
                    document_response = (
                        await new_user_simulator.api_client.get_document(
                            service=repo_config["service"],
                            owner=repo_config["owner"],
                            repo=repo_config["repo"],
                            path=first_doc["path"],
                        )
                    )
                    journey_tracker.log_action(
                        "推奨ドキュメント閲覧",
                        {
                            "document_path": first_doc["path"],
                            "content_length": len(
                                document_response.get("content", {}).get("raw", "")
                            ),
                        },
                    )

                    # ドキュメント内容のバリデーション
                    doc_validation = context.data_validator.validate_custom(
                        document_response, "document_content"
                    )
                    assert (
                        doc_validation.is_valid
                    ), f"Document validation failed: {doc_validation.errors}"

            # Step 6: AI機能の初回試用（オプション）
            if len(journey_tracker.actions) >= 3:  # 一定のアクションを完了した場合
                try:
                    ai_query = "このプロジェクトの概要を教えてください"
                    ai_response = await new_user_simulator.api_client.query_llm(
                        prompt=ai_query, context={"repository": repo_config}
                    )
                    journey_tracker.log_action(
                        "AI機能初回試用",
                        {
                            "query": ai_query,
                            "response_length": len(ai_response.get("content", "")),
                        },
                    )
                    journey_tracker.add_achievement("AI機能試用完了")
                except Exception as e:
                    journey_tracker.log_error(f"AI機能試用エラー: {str(e)}", "ai_query")

            # ジャーニー完了の評価
            journey_summary = journey_tracker.get_journey_summary()

            # アサーション：オンボーディングの成功基準
            assert (
                journey_summary["total_actions"] >= 4
            ), "最低限のアクションが実行されていない"
            assert journey_summary["error_rate"] < 0.5, "エラー率が高すぎる"
            assert len(journey_summary["achievements"]) > 0, "達成項目がない"

            # パフォーマンス評価
            performance_summary = await context.performance_monitor.get_metrics()
            assert (
                performance_summary.get("avg_api_response_time_ms", 0) < 2000
            ), "レスポンス時間が遅すぎる"

    @pytest.mark.e2e_user_story
    @pytest.mark.onboarding
    @pytest.mark.asyncio
    async def test_error_recovery_during_onboarding(
        self,
        new_user_simulator: FrontendSimulator,
        scenario_runner: ScenarioRunner,
        test_data_generator: TestDataGenerator,
    ):
        """エラー発生時のリカバリー能力をテスト"""

        persona = {
            "id": "error_prone_user",
            "name": "Error Prone User",
            "role": "beginner",
        }
        journey_tracker = UserJourneyTracker(persona)
        session = new_user_simulator.start_session(persona["id"])

        async with scenario_runner.run_scenario(
            "onboarding_error_recovery",
            "error_prone_user",
            (
                new_user_simulator.api_client.client
                if hasattr(new_user_simulator.api_client, "client")
                else None
            ),
        ) as context:

            # Step 1: システムヘルスチェック（正常）
            health_response = await new_user_simulator.api_client.get_health()
            journey_tracker.log_action(
                "システムアクセス", {"health_status": health_response.get("status")}
            )

            # Step 2: 存在しないリポジトリへのアクセス試行（エラーケース）
            try:
                invalid_repo_result = await new_user_simulator.connect_to_repository(
                    service="github",
                    owner="nonexistent",
                    repo="nonexistent",
                    user_context={"is_first_time": True},
                )
                journey_tracker.log_error(
                    "存在しないリポジトリ", "repository_not_found"
                )
            except Exception as e:
                journey_tracker.log_error(
                    f"リポジトリ接続エラー: {str(e)}", "connection_error"
                )

            # Step 3: 有効なリポジトリでのリカバリー
            valid_repo_config = test_data_generator.generate_repository_config()
            connection_result = await new_user_simulator.connect_to_repository(
                service=valid_repo_config["service"],
                owner=valid_repo_config["owner"],
                repo=valid_repo_config["repo"],
                user_context={"is_first_time": True, "had_previous_error": True},
            )
            journey_tracker.log_action(
                "リカバリー成功", {"status": connection_result["status"]}
            )

            # エラー回復の評価
            journey_summary = journey_tracker.get_journey_summary()
            assert journey_summary["total_errors"] > 0, "エラーが発生していない"
            assert journey_summary[
                "recovered_from_errors"
            ], "エラーからの回復ができていない"

    @pytest.mark.e2e_user_story
    @pytest.mark.onboarding
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_comprehensive_onboarding_with_ai(
        self,
        new_user_simulator: FrontendSimulator,
        scenario_runner: ScenarioRunner,
        test_data_generator: TestDataGenerator,
    ):
        """AI機能を含む包括的なオンボーディングテスト"""

        persona = scenario_runner.get_persona("tech_writer") or {
            "id": "tech_writer",
            "name": "Technical Writer",
            "role": "tech_writer",
            "experience_level": "intermediate",
        }

        journey_tracker = UserJourneyTracker(persona)
        session = new_user_simulator.start_session(
            persona["id"], {"wants_ai_help": True}
        )

        async with scenario_runner.run_scenario(
            "comprehensive_onboarding",
            "tech_writer",
            (
                new_user_simulator.api_client.client
                if hasattr(new_user_simulator.api_client, "client")
                else None
            ),
        ) as context:

            # Step 1: システム接続
            health_response = await new_user_simulator.api_client.get_health()
            journey_tracker.log_action("システム接続")

            # Step 2: ドキュメント豊富なリポジトリに接続
            repo_config = {
                "service": "github",
                "owner": "microsoft",
                "repo": "vscode-docs",  # ドキュメントが豊富なリポジトリ
                "ref": "main",
            }

            connection_result = await new_user_simulator.connect_to_repository(
                **repo_config,
                user_context={"role": "tech_writer", "wants_comprehensive_tour": True},
            )
            journey_tracker.log_action("ドキュメントリポジトリ接続")

            # Step 3: AI機能での文書分析
            if connection_result.get("recommended_first_steps"):
                first_doc = connection_result["recommended_first_steps"][0]
                if "path" in first_doc:
                    # ドキュメント取得
                    document_response = (
                        await new_user_simulator.api_client.get_document(
                            **repo_config, path=first_doc["path"]
                        )
                    )
                    journey_tracker.log_action("ドキュメント取得")

                    # AI分析クエリ
                    ai_queries = [
                        "このドキュメントの構造を分析してください",
                        "改善点を提案してください",
                        "関連するドキュメントを推奨してください",
                    ]

                    for query in ai_queries:
                        try:
                            ai_response = await new_user_simulator.api_client.query_llm(
                                prompt=query,
                                context={
                                    "document": document_response,
                                    "repository": repo_config,
                                },
                            )
                            journey_tracker.log_action(f"AI分析: {query[:20]}...")
                            journey_tracker.add_achievement("AI分析機能習得")
                        except Exception as e:
                            journey_tracker.log_error(
                                f"AI分析エラー: {str(e)}", "ai_analysis"
                            )

            # Step 4: 高度な機能の発見
            guidance = await new_user_simulator.get_beginner_guidance(
                connection_result["repository_info"]
            )
            if guidance.get("advanced_features"):
                journey_tracker.add_achievement("高度な機能発見")

            # 包括的評価
            journey_summary = journey_tracker.get_journey_summary()
            performance_summary = await context.performance_monitor.get_metrics()

            # アサーション
            assert (
                journey_summary["total_actions"] >= 6
            ), "十分なアクションが実行されていない"
            assert len(journey_summary["achievements"]) >= 2, "十分な達成項目がない"
            assert journey_summary["error_rate"] < 0.3, "エラー率が高すぎる"

            # パフォーマンス評価（AI機能使用により時間は長めでも許容）
            assert (
                performance_summary.get("avg_api_response_time_ms", 0) < 5000
            ), "AI含むレスポンス時間が遅すぎる"

            # 成功の記録
            context.set_test_data(
                "final_summary",
                {
                    "journey_summary": journey_summary,
                    "performance_summary": performance_summary,
                    "test_completed": True,
                },
            )
