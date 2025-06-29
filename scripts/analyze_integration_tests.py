#!/usr/bin/env python3
"""
統合テストファイルを分析し、削除・移行すべき要素を特定するスクリプト
"""

import os
import ast
import re
from typing import List, Dict, Any
from pathlib import Path


class IntegrationTestAnalyzer:
    """統合テストファイルの分析クラス"""

    def __init__(self, integration_dir: str = "tests/integration"):
        self.integration_dir = Path(integration_dir)
        self.analysis_report = {}

    def analyze_all_tests(self) -> Dict[str, Any]:
        """全ての統合テストファイルを分析"""

        if not self.integration_dir.exists():
            print(f"統合テストディレクトリが見つかりません: {self.integration_dir}")
            return {}

        print(f"統合テストディレクトリを分析中: {self.integration_dir}")
        print("=" * 50)

        for py_file in self.integration_dir.rglob("test_*.py"):
            if py_file.is_file():
                analysis = self.analyze_file(py_file)
                relative_path = py_file.relative_to(self.integration_dir)
                self.analysis_report[str(relative_path)] = analysis

        return self.analysis_report

    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """個別ファイルの分析"""
        analysis = {
            "file_size": 0,
            "line_count": 0,
            "has_mock_mode": False,
            "has_real_api_calls": False,
            "environment_variables": [],
            "test_methods": [],
            "imports": [],
            "pytest_marks": [],
            "fixtures": [],
            "should_migrate_to_unit": [],
            "should_keep_as_integration": [],
            "recommendations": [],
        }

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            if not content.strip():
                analysis["recommendations"].append("Empty file - consider deletion")
                return analysis

            analysis["file_size"] = len(content)
            analysis["line_count"] = len(content.splitlines())

            # AST解析
            try:
                tree = ast.parse(content)
                self._analyze_ast(tree, analysis)
            except SyntaxError as e:
                analysis["recommendations"].append(f"Syntax error in file: {e}")
                return analysis

            # テキストベースの解析
            self._analyze_text_patterns(content, analysis)

            # 推奨事項の生成
            self._generate_recommendations(analysis, file_path)

        except Exception as e:
            analysis["error"] = str(e)
            analysis["recommendations"].append(f"Failed to analyze file: {e}")

        return analysis

    def _analyze_ast(self, tree: ast.AST, analysis: Dict[str, Any]):
        """AST解析によるコード構造の分析"""

        for node in ast.walk(tree):
            # インポート文の分析
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        analysis["imports"].append(alias.name)
                else:
                    module = node.module or ""
                    for alias in node.names:
                        analysis["imports"].append(f"{module}.{alias.name}")

            # クラス定義の分析
            elif isinstance(node, ast.ClassDef):
                for method in node.body:
                    if isinstance(method, ast.FunctionDef):
                        analysis["test_methods"].append(
                            {
                                "class": node.name,
                                "method": method.name,
                                "is_async": isinstance(method, ast.AsyncFunctionDef),
                            }
                        )

            # 関数定義の分析（クラス外のテスト関数）
            elif isinstance(node, ast.FunctionDef):
                if node.name.startswith("test_"):
                    analysis["test_methods"].append(
                        {
                            "class": None,
                            "method": node.name,
                            "is_async": isinstance(node, ast.AsyncFunctionDef),
                        }
                    )

    def _analyze_text_patterns(self, content: str, analysis: Dict[str, Any]):
        """テキストパターンによる解析"""

        # 環境変数の検出
        env_pattern = r'os\.environ\.get\(["\']([^"\']+)["\']'
        env_vars = re.findall(env_pattern, content)
        analysis["environment_variables"] = list(set(env_vars))

        # Mockモードの検出
        mock_patterns = [
            r"TEST_MODE.*mock",
            r"mock.*service",
            r'LLMServiceFactory\.create\(["\']mock["\']',
            r"MockLLMService",
            r"pytest\.skip.*mock",
        ]

        for pattern in mock_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                analysis["has_mock_mode"] = True
                break

        # 実API呼び出しの検出
        real_api_patterns = [
            r"OPENAI_API_KEY",
            r"GITHUB_TOKEN",
            r"ANTHROPIC_API_KEY",
            r"OpenAI\(",
            r"openai\.",
            r"github\.com",
            r"api\.openai\.com",
        ]

        for pattern in real_api_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                analysis["has_real_api_calls"] = True
                break

        # pytest マークの検出
        pytest_marks = re.findall(r"@pytest\.mark\.(\w+)", content)
        analysis["pytest_marks"] = list(set(pytest_marks))

        # fixture の検出
        fixtures = re.findall(r"@pytest\.fixture[^)]*\)\s*def\s+(\w+)", content)
        analysis["fixtures"] = fixtures

    def _generate_recommendations(self, analysis: Dict[str, Any], file_path: Path):
        """分析結果に基づく推奨事項の生成"""

        recommendations = []

        # 空ファイルの処理
        if analysis["line_count"] == 0:
            recommendations.append("🗑️  Delete empty file")
            analysis["recommendations"] = recommendations
            return

        # Mockモードと実APIの混在チェック
        if analysis["has_mock_mode"] and analysis["has_real_api_calls"]:
            recommendations.append("⚠️  Mixed mock and real API modes detected")
            recommendations.append(
                "🔄 Split into unit tests (mock) and integration tests (real API)"
            )

        # Mock専用ファイルの場合
        elif analysis["has_mock_mode"] and not analysis["has_real_api_calls"]:
            recommendations.append("📦 Move to unit tests - this file only uses mocks")
            analysis["should_migrate_to_unit"] = analysis["test_methods"]

        # 実API専用ファイルの場合
        elif not analysis["has_mock_mode"] and analysis["has_real_api_calls"]:
            recommendations.append("✅ Keep as integration test - uses real APIs")
            recommendations.append(
                "🔧 Add environment variable checks and skip conditions"
            )
            analysis["should_keep_as_integration"] = analysis["test_methods"]

        # 環境変数が多い場合
        if len(analysis["environment_variables"]) > 3:
            recommendations.append(
                "🔐 Consider consolidating environment variable usage"
            )

        # 必須の環境変数チェック
        required_env_vars = ["OPENAI_API_KEY", "GITHUB_TOKEN", "ANTHROPIC_API_KEY"]
        missing_checks = []

        for env_var in required_env_vars:
            if env_var in analysis["environment_variables"]:
                # スキップ条件があるかチェック
                skip_pattern = f"pytest\.skip.*{env_var}"
                with open(file_path, "r") as f:
                    content = f.read()
                if not re.search(skip_pattern, content):
                    missing_checks.append(env_var)

        if missing_checks:
            recommendations.append(
                f"🚨 Add pytest.skip for missing env vars: {', '.join(missing_checks)}"
            )

        analysis["recommendations"] = recommendations

    def print_report(self):
        """分析レポートの出力"""

        if not self.analysis_report:
            print("分析対象のファイルが見つかりませんでした。")
            return

        print("\n📊 統合テスト分析レポート")
        print("=" * 50)

        total_files = len(self.analysis_report)
        files_with_mock = sum(
            1
            for analysis in self.analysis_report.values()
            if analysis.get("has_mock_mode")
        )
        files_with_real_api = sum(
            1
            for analysis in self.analysis_report.values()
            if analysis.get("has_real_api_calls")
        )

        print(f"📁 総ファイル数: {total_files}")
        print(f"🎭 Mockモード使用: {files_with_mock}")
        print(f"🌐 実API使用: {files_with_real_api}")
        print()

        for file_path, analysis in self.analysis_report.items():
            print(f"📄 {file_path}")
            print(f"   行数: {analysis['line_count']}")
            print(f"   テストメソッド数: {len(analysis['test_methods'])}")
            print(f"   環境変数: {len(analysis['environment_variables'])}")
            print(f"   Mockモード: {'✓' if analysis['has_mock_mode'] else '✗'}")
            print(f"   実API: {'✓' if analysis['has_real_api_calls'] else '✗'}")

            if analysis["recommendations"]:
                print("   推奨事項:")
                for rec in analysis["recommendations"]:
                    print(f"     {rec}")

            print()

    def generate_migration_plan(self) -> Dict[str, List[str]]:
        """マイグレーション計画の生成"""

        plan = {
            "delete_files": [],
            "migrate_to_unit": [],
            "keep_as_integration": [],
            "need_splitting": [],
        }

        for file_path, analysis in self.analysis_report.items():
            if analysis["line_count"] == 0:
                plan["delete_files"].append(file_path)
            elif analysis["should_migrate_to_unit"]:
                plan["migrate_to_unit"].append(file_path)
            elif analysis["should_keep_as_integration"]:
                plan["keep_as_integration"].append(file_path)
            elif analysis["has_mock_mode"] and analysis["has_real_api_calls"]:
                plan["need_splitting"].append(file_path)

        return plan


def main():
    """メイン実行関数"""
    print("🔍 統合テスト分析ツール")
    print("=" * 50)

    # 現在のディレクトリから実行する想定
    analyzer = IntegrationTestAnalyzer()

    # 分析実行
    analysis_report = analyzer.analyze_all_tests()

    if not analysis_report:
        print("❌ 分析対象のファイルが見つかりませんでした。")
        return

    # レポート出力
    analyzer.print_report()

    # マイグレーション計画生成
    migration_plan = analyzer.generate_migration_plan()

    print("\n🚀 マイグレーション計画")
    print("=" * 50)

    if migration_plan["delete_files"]:
        print("🗑️  削除対象ファイル:")
        for file_path in migration_plan["delete_files"]:
            print(f"   - {file_path}")

    if migration_plan["migrate_to_unit"]:
        print("\n📦 ユニットテストに移行:")
        for file_path in migration_plan["migrate_to_unit"]:
            print(f"   - {file_path}")

    if migration_plan["keep_as_integration"]:
        print("\n✅ 統合テストとして保持:")
        for file_path in migration_plan["keep_as_integration"]:
            print(f"   - {file_path}")

    if migration_plan["need_splitting"]:
        print("\n🔄 分割が必要:")
        for file_path in migration_plan["need_splitting"]:
            print(f"   - {file_path}")

    print("\n💡 次のステップ:")
    print("1. 削除対象ファイルの確認と削除")
    print("2. Mock専用テストをユニットテストディレクトリに移行")
    print("3. 実API統合テストの環境変数チェック強化")
    print("4. 分割が必要なファイルの手動分割")


if __name__ == "__main__":
    main()
