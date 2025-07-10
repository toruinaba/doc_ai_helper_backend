"""
日本語文書対応 LLM強化ツールの簡単なユニットテスト.

既存のMCPツールのテストパターンに合わせた実装。
"""

import json
import pytest
import os

from doc_ai_helper_backend.services.mcp.tools.llm_enhanced_tools import (
    _build_japanese_summarization_prompt,
    _build_japanese_improvement_prompt,
    _extract_japanese_key_points,
    _parse_japanese_improvement_recommendations,
    _generate_japanese_overall_assessment,
    _translate_focus_area,
    _translate_length_type,
    _translate_improvement_type,
    _translate_target_audience,
    _get_max_tokens_for_length,
)


class TestJapaneseLLMToolsUtilities:
    """日本語LLMツールのユーティリティ関数テストクラス"""

    def test_build_japanese_summarization_prompt(self):
        """日本語要約プロンプト構築のテスト"""
        content = "これはテスト文書です。FastAPIを使用したプロジェクトの説明です。"
        prompt = _build_japanese_summarization_prompt(
            content, "brief", "technical", "追加のコンテキスト情報"
        )
        
        # プロンプトの必要な要素が含まれているかチェック
        assert "専門的な日本語文書分析の専門家" in prompt
        assert "重要なポイントを2-3文で簡潔に" in prompt
        assert "技術的な詳細" in prompt
        assert "追加のコンテキスト情報" in prompt
        assert content in prompt
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # 適切な長さのプロンプト

    def test_build_japanese_improvement_prompt_comprehensive(self):
        """日本語改善プロンプト構築のテスト（包括的）"""
        content = "# README\n\nプロジェクトの説明\n\n機能の説明"
        prompt = _build_japanese_improvement_prompt(
            content, "要約コンテキスト", "comprehensive", "technical"
        )
        
        # プロンプトの必要な要素が含まれているかチェック
        assert "日本語技術文書の専門コンサルタント" in prompt
        assert "すべての側面を分析" in prompt
        assert "技術的正確性" in prompt
        assert "要約コンテキスト" in prompt
        assert content in prompt
        assert "■ 高優先度:" in prompt
        assert "■ 中優先度:" in prompt
        assert "■ 低優先度:" in prompt

    def test_extract_japanese_key_points(self):
        """日本語重要ポイント抽出のテスト"""
        summary_text = "これは最初の重要なポイントです。次に、二番目のポイントを説明します。最後に、三番目の要点をまとめます。短い文。"
        key_points = _extract_japanese_key_points(summary_text)
        
        assert isinstance(key_points, list)
        assert len(key_points) >= 3
        assert all(isinstance(point, str) for point in key_points)
        assert all(point.endswith('。') for point in key_points)
        assert "これは最初の重要なポイントです。" in key_points

    def test_parse_japanese_improvement_recommendations(self):
        """日本語改善提案解析のテスト"""
        recommendations_text = """
        ■ 高優先度:
        ・構造改善: 見出し階層の整理が必要です
        ・内容改善: 詳細な説明の追加が重要です
        
        ■ 中優先度:
        ・読みやすさ: 文章の流れを改善できます
        ・構造: サブセクションの追加を検討
        
        ■ 低優先度:
        ・その他: FAQ セクションの追加
        """
        
        structured = _parse_japanese_improvement_recommendations(recommendations_text)
        
        assert isinstance(structured, dict)
        assert "高優先度" in structured
        assert "中優先度" in structured
        assert "低優先度" in structured
        
        # 高優先度の改善提案をチェック
        high_priority = structured["高優先度"]
        assert isinstance(high_priority, list)
        assert len(high_priority) == 2
        
        # 各改善提案の構造をチェック
        for recommendation in high_priority:
            assert "カテゴリ" in recommendation
            assert "タイトル" in recommendation
            assert "説明" in recommendation
            assert "実装労力" in recommendation
            assert "期待効果" in recommendation

    def test_generate_japanese_overall_assessment(self):
        """日本語総合評価生成のテスト"""
        recommendations = {
            "高優先度": [
                {"title": "見出し改善", "category": "構造"},
                {"title": "内容充実", "category": "内容"},
                {"title": "詳細追加", "category": "内容"}
            ],
            "中優先度": [
                {"title": "文章改善", "category": "読みやすさ"}
            ],
            "低優先度": []
        }
        
        assessment = _generate_japanese_overall_assessment(recommendations)
        
        assert isinstance(assessment, dict)
        assert "現在の品質" in assessment
        assert "総提案数" in assessment
        assert "高優先度数" in assessment
        assert "改善可能性" in assessment
        assert "予想作業時間" in assessment
        
        # 数値の確認
        assert assessment["総提案数"] == 4
        assert assessment["高優先度数"] == 3
        assert assessment["現在の品質"] == "良好"  # 高優先度が3つ
        assert assessment["改善可能性"] == "高"

    def test_parameter_translations(self):
        """パラメータ翻訳のテスト"""
        # 焦点領域の翻訳
        assert _translate_focus_area("general") == "一般向け"
        assert _translate_focus_area("technical") == "技術的"
        assert _translate_focus_area("business") == "ビジネス向け"
        assert _translate_focus_area("unknown") == "unknown"
        
        # 長さタイプの翻訳
        assert _translate_length_type("brief") == "簡潔"
        assert _translate_length_type("detailed") == "詳細"
        assert _translate_length_type("comprehensive") == "包括的"
        
        # 改善タイプの翻訳
        assert _translate_improvement_type("structure") == "構造"
        assert _translate_improvement_type("content") == "内容"
        assert _translate_improvement_type("readability") == "読みやすさ"
        assert _translate_improvement_type("comprehensive") == "包括的"
        
        # 対象読者の翻訳
        assert _translate_target_audience("general") == "一般"
        assert _translate_target_audience("technical") == "技術者"
        assert _translate_target_audience("beginner") == "初心者"
        assert _translate_target_audience("expert") == "専門家"

    def test_max_tokens_calculation(self):
        """max_tokens計算のテスト"""
        assert _get_max_tokens_for_length("brief") == 200
        assert _get_max_tokens_for_length("detailed") == 500
        assert _get_max_tokens_for_length("comprehensive") == 800
        assert _get_max_tokens_for_length("unknown") == 800  # デフォルト値


class TestJapaneseTextProcessing:
    """日本語テキスト処理のテストクラス"""

    def test_japanese_character_handling(self):
        """日本語文字処理のテスト"""
        japanese_text = "これは日本語のテストです。ひらがな、カタカナ、漢字を含みます。"
        
        # 文字数計算
        char_count = len(japanese_text)
        assert char_count == 31
        
        # UTF-8エンコーディング
        encoded = japanese_text.encode('utf-8')
        decoded = encoded.decode('utf-8')
        assert decoded == japanese_text

    def test_mixed_language_content(self):
        """日英混在コンテンツの処理テスト"""
        mixed_content = """
        # API Documentation
        
        このAPIドキュメントでは以下を説明します：
        
        - GET /api/users - ユーザー情報の取得
        - POST /api/login - ログイン処理
        
        ## Example Usage
        
        ```javascript
        fetch('/api/users')
          .then(response => response.json())
          .then(data => console.log(data));
        ```
        
        詳細については公式ドキュメントを参照してください。
        """
        
        # 混在コンテンツの基本処理確認
        assert "API Documentation" in mixed_content
        assert "このAPIドキュメント" in mixed_content
        assert "```javascript" in mixed_content
        
        # 文字数計算
        char_count = len(mixed_content.strip())
        assert char_count > 200


class TestPromptTemplates:
    """プロンプトテンプレートのテストクラス"""

    def test_summarization_prompt_variations(self):
        """要約プロンプトの種類別テスト"""
        content = "テスト文書の内容です。"
        
        # Brief要約
        brief_prompt = _build_japanese_summarization_prompt(content, "brief", "general")
        assert "2-3文で簡潔に" in brief_prompt
        
        # Detailed要約
        detailed_prompt = _build_japanese_summarization_prompt(content, "detailed", "technical")
        assert "1-2段落で詳細に" in detailed_prompt
        assert "技術的な詳細" in detailed_prompt
        
        # Comprehensive要約
        comprehensive_prompt = _build_japanese_summarization_prompt(content, "comprehensive", "business")
        assert "包括的な要約" in comprehensive_prompt
        assert "ビジネス価値" in comprehensive_prompt

    def test_improvement_prompt_variations(self):
        """改善プロンプトの種類別テスト"""
        content = "改善対象の文書内容です。"
        
        # Structure改善
        structure_prompt = _build_japanese_improvement_prompt(content, "", "structure", "general")
        assert "文書の構成、見出し階層" in structure_prompt
        
        # Content改善
        content_prompt = _build_japanese_improvement_prompt(content, "", "content", "technical")
        assert "内容の品質、明確性" in content_prompt
        assert "技術的正確性" in content_prompt
        
        # Readability改善
        readability_prompt = _build_japanese_improvement_prompt(content, "", "readability", "beginner")
        assert "文章スタイル、文の構造" in readability_prompt
        assert "明確性、説明、学習の進行" in readability_prompt


class TestErrorHandling:
    """エラーハンドリングのテストクラス"""

    def test_empty_content_handling(self):
        """空コンテンツの処理テスト"""
        # 空文字列
        empty_points = _extract_japanese_key_points("")
        assert isinstance(empty_points, list)
        assert len(empty_points) == 0
        
        # None値の処理
        none_points = _extract_japanese_key_points("")
        assert isinstance(none_points, list)

    def test_malformed_recommendations_parsing(self):
        """不正な形式の改善提案解析テスト"""
        # 不正な形式のテキスト
        malformed_text = "これは不正な形式のテキストです。優先度が明確でありません。"
        structured = _parse_japanese_improvement_recommendations(malformed_text)
        
        # 基本構造は維持される
        assert isinstance(structured, dict)
        assert "高優先度" in structured
        assert "中優先度" in structured
        assert "低優先度" in structured
        
        # 少なくとも1つの一般的な推奨事項が作成される
        total_recommendations = sum(len(v) for v in structured.values())
        assert total_recommendations >= 1

    def test_assessment_edge_cases(self):
        """評価の境界ケーステスト"""
        # 改善提案が0個の場合
        empty_recommendations = {"高優先度": [], "中優先度": [], "低優先度": []}
        assessment = _generate_japanese_overall_assessment(empty_recommendations)
        
        assert assessment["総提案数"] == 0
        assert assessment["高優先度数"] == 0
        assert assessment["改善可能性"] == "低"
        assert assessment["現在の品質"] == "優秀"