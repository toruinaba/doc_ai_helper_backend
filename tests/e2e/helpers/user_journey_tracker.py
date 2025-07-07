"""
ユーザージャーニー追跡ヘルパー

このモジュールはE2Eテストでのユーザージャーニーを
追跡・分析するためのヘルパークラスを提供します。
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json


class UserJourneyTracker:
    """ユーザージャーニーを追跡するヘルパークラス"""

    def __init__(self, user_persona: Dict[str, Any]):
        self.user_persona = user_persona
        self.journey_start = datetime.now()
        self.actions: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []
        self.achievements: List[str] = []
        self.current_context: Dict[str, Any] = {}

    def log_action(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None,
        success: bool = True,
        duration: Optional[float] = None,
    ) -> None:
        """アクションをログに記録する"""
        action_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "success": success,
            "context": context or {},
            "duration": duration,
            "cumulative_actions": len(self.actions) + 1,
        }

        self.actions.append(action_entry)

        if not success:
            self.errors.append(action_entry)

    def log_error(
        self,
        error: str,
        error_type: str = "general",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """エラーをログに記録する"""
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "error": error,
            "error_type": error_type,
            "context": context or {},
            "action_count_at_error": len(self.actions),
        }

        self.errors.append(error_entry)
        self.log_action(f"エラー発生: {error}", context, success=False)

    def add_achievement(self, achievement: str) -> None:
        """達成項目を追加する"""
        if achievement not in self.achievements:
            self.achievements.append(achievement)
            self.log_action(f"Achievement unlocked: {achievement}")

    def start_journey(self, scenario_id: str, user_persona: str) -> None:
        """ジャーニーを開始する"""
        self.log_action(f"Journey started: {scenario_id} for {user_persona}")
        self.update_context("scenario_id", scenario_id)
        self.update_context("journey_started", True)

    def end_journey(self) -> None:
        """ジャーニーを終了する"""
        journey_duration = (datetime.now() - self.journey_start).total_seconds()
        self.log_action("Journey completed", {"total_duration": journey_duration})
        self.update_context("journey_completed", True)

    def add_error(self, error: str, context: Optional[Dict[str, Any]] = None) -> None:
        """エラーを追加する（log_errorの別名）"""
        self.log_error(error, context=context)

    def add_step(
        self,
        step_name: str,
        success: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """ステップを追加する（log_actionの別名）"""
        self.log_action(step_name, context=context, success=success)

    def get_summary(self) -> Dict[str, Any]:
        """サマリーを取得する（get_journey_summaryの別名）"""
        return self.get_journey_summary()

    def update_context(self, key: str, value: Any) -> None:
        """現在のコンテキストを更新する"""
        self.current_context[key] = value

    def get_journey_summary(self) -> Dict[str, Any]:
        """ジャーニーの要約を取得する"""
        journey_duration = (datetime.now() - self.journey_start).total_seconds()

        return {
            "user_persona": self.user_persona,
            "journey_duration_seconds": journey_duration,
            "total_actions": len(self.actions),
            "successful_actions": len([a for a in self.actions if a["success"]]),
            "failed_actions": len([a for a in self.actions if not a["success"]]),
            "total_errors": len(self.errors),
            "achievements": self.achievements,
            "actions": [a["action"] for a in self.actions],
            "error_rate": len(self.errors) / max(len(self.actions), 1),
            "recovered_from_errors": len(self.errors) > 0
            and len(self.achievements) > 0,
            "current_context": self.current_context,
        }

    def get_action_timeline(self) -> List[Dict[str, Any]]:
        """アクションのタイムラインを取得する"""
        return self.actions.copy()

    def get_error_analysis(self) -> Dict[str, Any]:
        """エラー分析を取得する"""
        if not self.errors:
            return {"has_errors": False}

        error_types = {}
        for error in self.errors:
            error_type = error.get("error_type", "unknown")
            if error_type not in error_types:
                error_types[error_type] = 0
            error_types[error_type] += 1

        return {
            "has_errors": True,
            "total_errors": len(self.errors),
            "error_types": error_types,
            "first_error": self.errors[0] if self.errors else None,
            "last_error": self.errors[-1] if self.errors else None,
            "error_recovery_rate": len(self.achievements) / max(len(self.errors), 1),
        }

    def check_journey_completeness(self, required_actions: List[str]) -> Dict[str, Any]:
        """ジャーニーの完全性をチェックする"""
        completed_actions = [a["action"] for a in self.actions if a["success"]]

        missing_actions = []
        for required in required_actions:
            if not any(
                required.lower() in action.lower() for action in completed_actions
            ):
                missing_actions.append(required)

        return {
            "is_complete": len(missing_actions) == 0,
            "completion_rate": (len(required_actions) - len(missing_actions))
            / len(required_actions),
            "missing_actions": missing_actions,
            "completed_required_actions": len(required_actions) - len(missing_actions),
        }

    def export_journey(self, file_path: Optional[str] = None) -> str:
        """ジャーニーをJSONとしてエクスポートする"""
        journey_data = {
            "summary": self.get_journey_summary(),
            "timeline": self.get_action_timeline(),
            "error_analysis": self.get_error_analysis(),
        }

        json_data = json.dumps(journey_data, indent=2, ensure_ascii=False)

        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(json_data)

        return json_data


class JourneyComparator:
    """複数のユーザージャーニーを比較するヘルパークラス"""

    @staticmethod
    def compare_journeys(
        journey1: UserJourneyTracker, journey2: UserJourneyTracker
    ) -> Dict[str, Any]:
        """2つのジャーニーを比較する"""
        summary1 = journey1.get_journey_summary()
        summary2 = journey2.get_journey_summary()

        return {
            "persona_comparison": {
                "journey1_persona": summary1["user_persona"]["name"],
                "journey2_persona": summary2["user_persona"]["name"],
            },
            "performance_comparison": {
                "duration_difference": summary2["journey_duration_seconds"]
                - summary1["journey_duration_seconds"],
                "action_count_difference": summary2["total_actions"]
                - summary1["total_actions"],
                "success_rate_1": summary1["successful_actions"]
                / max(summary1["total_actions"], 1),
                "success_rate_2": summary2["successful_actions"]
                / max(summary2["total_actions"], 1),
                "error_rate_difference": summary2["error_rate"]
                - summary1["error_rate"],
            },
            "achievement_comparison": {
                "common_achievements": list(
                    set(summary1["achievements"]) & set(summary2["achievements"])
                ),
                "unique_to_journey1": list(
                    set(summary1["achievements"]) - set(summary2["achievements"])
                ),
                "unique_to_journey2": list(
                    set(summary2["achievements"]) - set(summary1["achievements"])
                ),
            },
        }

    @staticmethod
    def analyze_journey_patterns(journeys: List[UserJourneyTracker]) -> Dict[str, Any]:
        """複数のジャーニーのパターンを分析する"""
        if not journeys:
            return {"error": "No journeys provided"}

        summaries = [j.get_journey_summary() for j in journeys]

        # 共通アクションの特定
        all_actions = []
        for summary in summaries:
            all_actions.extend(summary["actions"])

        action_frequency = {}
        for action in all_actions:
            if action not in action_frequency:
                action_frequency[action] = 0
            action_frequency[action] += 1

        common_actions = [
            action
            for action, freq in action_frequency.items()
            if freq >= len(journeys) * 0.5
        ]  # 50%以上で実行されるアクション

        # 成功パターンの分析
        successful_journeys = [s for s in summaries if s["error_rate"] < 0.2]
        failed_journeys = [s for s in summaries if s["error_rate"] >= 0.5]

        return {
            "total_journeys": len(journeys),
            "common_actions": common_actions,
            "action_frequency": action_frequency,
            "success_patterns": {
                "successful_journey_count": len(successful_journeys),
                "failed_journey_count": len(failed_journeys),
                "average_success_rate": sum(
                    s["successful_actions"] / max(s["total_actions"], 1)
                    for s in summaries
                )
                / len(summaries),
                "average_error_rate": sum(s["error_rate"] for s in summaries)
                / len(summaries),
            },
            "persona_performance": {
                persona["user_persona"]["name"]: {
                    "success_rate": persona["successful_actions"]
                    / max(persona["total_actions"], 1),
                    "error_rate": persona["error_rate"],
                    "achievements": len(persona["achievements"]),
                }
                for persona in summaries
            },
        }


class StoryScenarioValidator:
    """ストーリーシナリオの妥当性を検証するヘルパークラス"""

    @staticmethod
    def validate_user_story_completion(
        journey: UserJourneyTracker, story_scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ユーザーストーリーの完了を検証する"""
        required_steps = story_scenario.get("required_steps", [])
        optional_steps = story_scenario.get("optional_steps", [])
        success_criteria = story_scenario.get("success_criteria", [])

        journey_summary = journey.get_journey_summary()
        completed_actions = journey_summary["actions"]

        # 必須ステップの確認
        completed_required = []
        missing_required = []

        for step in required_steps:
            if any(step.lower() in action.lower() for action in completed_actions):
                completed_required.append(step)
            else:
                missing_required.append(step)

        # オプションステップの確認
        completed_optional = []
        for step in optional_steps:
            if any(step.lower() in action.lower() for action in completed_actions):
                completed_optional.append(step)

        # 成功基準の確認
        met_criteria = []
        unmet_criteria = []

        for criterion in success_criteria:
            if StoryScenarioValidator._check_success_criterion(
                journey_summary, criterion
            ):
                met_criteria.append(criterion)
            else:
                unmet_criteria.append(criterion)

        story_completion_rate = len(completed_required) / max(len(required_steps), 1)

        return {
            "story_completed": len(missing_required) == 0 and len(unmet_criteria) == 0,
            "completion_rate": story_completion_rate,
            "required_steps": {
                "total": len(required_steps),
                "completed": completed_required,
                "missing": missing_required,
            },
            "optional_steps": {
                "total": len(optional_steps),
                "completed": completed_optional,
            },
            "success_criteria": {
                "total": len(success_criteria),
                "met": met_criteria,
                "unmet": unmet_criteria,
            },
            "overall_assessment": StoryScenarioValidator._get_overall_assessment(
                story_completion_rate,
                len(unmet_criteria),
                journey_summary["error_rate"],
            ),
        }

    @staticmethod
    def _check_success_criterion(
        journey_summary: Dict[str, Any], criterion: str
    ) -> bool:
        """成功基準をチェックする"""
        if "エラー率" in criterion:
            # エラー率基準（例: "エラー率20%以下"）
            threshold = float(criterion.split("率")[1].split("%")[0]) / 100
            return journey_summary["error_rate"] <= threshold

        if "アクション数" in criterion:
            # アクション数基準（例: "アクション数5以上"）
            threshold = int(criterion.split("数")[1].split("以上")[0])
            return journey_summary["total_actions"] >= threshold

        if "達成" in criterion:
            # 達成基準（例: "3つ以上の達成"）
            if "以上" in criterion:
                threshold = int(criterion.split("つ以上")[0])
                return len(journey_summary["achievements"]) >= threshold

        # デフォルト: アクション名での検索
        return any(
            criterion.lower() in action.lower() for action in journey_summary["actions"]
        )

    @staticmethod
    def _get_overall_assessment(
        completion_rate: float, unmet_criteria_count: int, error_rate: float
    ) -> str:
        """総合評価を取得する"""
        if completion_rate >= 0.9 and unmet_criteria_count == 0 and error_rate < 0.1:
            return "優秀"
        elif completion_rate >= 0.7 and unmet_criteria_count <= 1 and error_rate < 0.3:
            return "良好"
        elif completion_rate >= 0.5 and error_rate < 0.5:
            return "改善の余地あり"
        else:
            return "要改善"


class PerformanceMetrics:
    """パフォーマンスメトリクス計算ヘルパークラス"""

    @staticmethod
    def calculate_user_experience_score(journey: UserJourneyTracker) -> Dict[str, Any]:
        """ユーザーエクスペリエンススコアを計算する"""
        summary = journey.get_journey_summary()

        # 基本スコア要素
        success_rate = summary["successful_actions"] / max(summary["total_actions"], 1)
        error_recovery_rate = 1.0 if summary["recovered_from_errors"] else 0.0
        achievement_rate = len(summary["achievements"]) / max(
            summary["total_actions"] * 0.3, 1
        )

        # 効率性スコア
        efficiency_score = min(1.0, 10.0 / max(summary["journey_duration_seconds"], 1))

        # 総合UXスコア（100点満点）
        ux_score = (
            success_rate * 40  # 成功率（40点）
            + (1 - summary["error_rate"]) * 30  # エラー率の逆（30点）
            + achievement_rate * 20  # 達成率（20点）
            + efficiency_score * 10  # 効率性（10点）
        )

        return {
            "ux_score": round(ux_score, 2),
            "components": {
                "success_rate": round(success_rate * 100, 1),
                "error_rate": round(summary["error_rate"] * 100, 1),
                "achievement_rate": round(achievement_rate * 100, 1),
                "efficiency_score": round(efficiency_score * 100, 1),
            },
            "grade": PerformanceMetrics._get_ux_grade(ux_score),
            "recommendations": PerformanceMetrics._get_ux_recommendations(
                success_rate, summary["error_rate"], achievement_rate, efficiency_score
            ),
        }

    @staticmethod
    def _get_ux_grade(score: float) -> str:
        """UXスコアから評価グレードを取得する"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    @staticmethod
    def _get_ux_recommendations(
        success_rate: float,
        error_rate: float,
        achievement_rate: float,
        efficiency_score: float,
    ) -> List[str]:
        """UX改善の推奨事項を生成する"""
        recommendations = []

        if success_rate < 0.8:
            recommendations.append("成功率向上のためのプロセス改善が必要")

        if error_rate > 0.2:
            recommendations.append("エラー処理とユーザーガイダンスの改善が必要")

        if achievement_rate < 0.5:
            recommendations.append("達成感を向上させる機能の追加を検討")

        if efficiency_score < 0.3:
            recommendations.append("操作効率の改善とワークフローの最適化が必要")

        if not recommendations:
            recommendations.append("優秀なユーザーエクスペリエンスを維持")

        return recommendations
