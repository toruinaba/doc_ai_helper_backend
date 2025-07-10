"""
日本語文書対応 LLM強化ツール for MCP server.

このモジュールは内部LLM APIエンドポイントを活用して、
日本語文書の高度な分析機能を提供します。
"""

import json
import logging
import time
from typing import Dict, Any, Optional

import httpx

logger = logging.getLogger(__name__)


async def summarize_document_with_llm(
    document_content: str,
    summary_length: str = "comprehensive",
    focus_area: str = "general",
    context: Optional[str] = None,
) -> str:
    """
    内部LLM APIを使用して日本語文書の高品質な要約を生成します。
    
    専用の日本語プロンプトと処理機能を使用して、
    日本語文書に最適化された要約を提供します。
    
    Args:
        document_content: 要約対象の日本語文書内容
        summary_length: 要約の長さ ("brief"=簡潔, "detailed"=詳細, "comprehensive"=包括的)
        focus_area: 焦点領域 ("general"=一般向け, "technical"=技術的, "business"=ビジネス向け)
        context: 追加コンテキスト (オプション)
        
    Returns:
        要約、メタデータ、分析指標を含むJSON文字列
    """
    start_time = time.time()
    
    try:
        # 入力検証
        if not document_content or not document_content.strip():
            return json.dumps({
                "success": False,
                "error": "文書内容が空です",
                "error_en": "Document content cannot be empty"
            }, ensure_ascii=False)
        
        # 日本語文書用の専用プロンプトを構築
        prompt = _build_japanese_summarization_prompt(
            document_content, summary_length, focus_area, context
        )
        
        # 内部LLM APIエンドポイントへの呼び出し
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/llm/query",
                json={
                    "prompt": prompt,
                    "provider": "openai",
                    "enable_tools": False,  # 循環呼び出し防止
                    "options": {
                        "model": "gpt-3.5-turbo",
                        "temperature": 0.3,
                        "max_tokens": _get_max_tokens_for_length(summary_length),
                    }
                },
                timeout=30.0
            )
            response.raise_for_status()
            
            llm_response = response.json()
            
            # LLM応答から要約を抽出
            summary_text = llm_response.get("response", "")
            
            # 日本語文書用メトリクス計算
            original_length = len(document_content)
            summary_length_chars = len(summary_text)
            compression_ratio = summary_length_chars / original_length if original_length > 0 else 0
            processing_time = time.time() - start_time
            
            # 日本語文書から重要ポイントを抽出
            key_points = _extract_japanese_key_points(summary_text)
            
            result = {
                "success": True,
                "元文書文字数": original_length,
                "要約": summary_text,
                "要約文字数": summary_length_chars,
                "圧縮率": round(compression_ratio, 3),
                "重要ポイント": key_points,
                "焦点領域": _translate_focus_area(focus_area),
                "長さタイプ": _translate_length_type(summary_length),
                "処理時間秒": round(processing_time, 2),
                "メタデータ": {
                    "使用モデル": "gpt-3.5-turbo",
                    "温度パラメータ": 0.3,
                    "プロンプトタイプ": "日本語専用要約",
                    "言語": "日本語"
                }
            }
            
            logger.info(f"日本語文書要約が {processing_time:.2f}秒で完了しました")
            return json.dumps(result, indent=2, ensure_ascii=False)
            
    except httpx.TimeoutException:
        logger.error("LLM API要約処理中にタイムアウトが発生しました")
        return json.dumps({
            "success": False,
            "error": "LLM処理がタイムアウトしました - 再試行してください",
            "error_en": "LLM processing timeout",
            "処理時間秒": round(time.time() - start_time, 2)
        }, ensure_ascii=False)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API HTTPエラー: {e.response.status_code}")
        return json.dumps({
            "success": False,
            "error": f"LLM APIエラーが発生しました: {e.response.status_code}",
            "error_en": f"LLM API error: {e.response.status_code}",
            "処理時間秒": round(time.time() - start_time, 2)
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"要約処理中に予期しないエラーが発生しました: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"予期しないエラーが発生しました: {str(e)}",
            "error_en": f"Unexpected error: {str(e)}",
            "処理時間秒": round(time.time() - start_time, 2)
        }, ensure_ascii=False)


async def create_improvement_recommendations_with_llm(
    document_content: str,
    summary_context: str = "",
    improvement_type: str = "comprehensive",
    target_audience: str = "general",
) -> str:
    """
    専門レベルのLLM分析による日本語文書の詳細な改善提案を作成します。
    
    文書分析に基づいて、優先度別に分類された改善提案と
    実装ガイダンスを含む包括的な推奨事項を生成します。
    
    Args:
        document_content: 分析対象の日本語文書内容
        summary_context: 事前分析の要約コンテキスト (オプション)
        improvement_type: 改善タイプ ("structure"=構造, "content"=内容, "readability"=読みやすさ, "comprehensive"=包括的)
        target_audience: 対象読者 ("general"=一般, "technical"=技術者, "beginner"=初心者, "expert"=専門家)
        
    Returns:
        分類された推奨事項、優先度レベル、実装ガイダンスを含むJSON文字列
    """
    start_time = time.time()
    
    try:
        # 入力検証
        if not document_content or not document_content.strip():
            return json.dumps({
                "success": False,
                "error": "文書内容が空です",
                "error_en": "Document content cannot be empty"
            }, ensure_ascii=False)
        
        # 日本語文書改善用の専用プロンプトを構築
        prompt = _build_japanese_improvement_prompt(
            document_content, summary_context, improvement_type, target_audience
        )
        
        # 内部LLM APIエンドポイントへの呼び出し
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/llm/query",
                json={
                    "prompt": prompt,
                    "provider": "openai",
                    "enable_tools": False,  # 循環呼び出し防止
                    "options": {
                        "model": "gpt-4",  # より高度な分析にGPT-4を使用
                        "temperature": 0.4,
                        "max_tokens": 1500,
                    }
                },
                timeout=45.0
            )
            response.raise_for_status()
            
            llm_response = response.json()
            
            # LLM応答から改善提案を抽出
            recommendations_text = llm_response.get("response", "")
            
            # 日本語改善提案の解析と構造化
            structured_recommendations = _parse_japanese_improvement_recommendations(recommendations_text)
            
            # 処理メトリクス計算
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "改善タイプ": _translate_improvement_type(improvement_type),
                "対象読者": _translate_target_audience(target_audience),
                "改善提案": structured_recommendations,
                "総合評価": _generate_japanese_overall_assessment(structured_recommendations),
                "処理時間秒": round(processing_time, 2),
                "メタデータ": {
                    "使用モデル": "gpt-4",
                    "温度パラメータ": 0.4,
                    "プロンプトタイプ": "日本語文書改善分析",
                    "要約コンテキスト有": bool(summary_context),
                    "言語": "日本語"
                }
            }
            
            logger.info(f"日本語文書改善提案が {processing_time:.2f}秒で生成されました")
            return json.dumps(result, indent=2, ensure_ascii=False)
            
    except httpx.TimeoutException:
        logger.error("LLM API改善分析中にタイムアウトが発生しました")
        return json.dumps({
            "success": False,
            "error": "LLM処理がタイムアウトしました - 再試行してください",
            "error_en": "LLM processing timeout",
            "処理時間秒": round(time.time() - start_time, 2)
        }, ensure_ascii=False)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API HTTPエラー: {e.response.status_code}")
        return json.dumps({
            "success": False,
            "error": f"LLM APIエラーが発生しました: {e.response.status_code}",
            "error_en": f"LLM API error: {e.response.status_code}",
            "処理時間秒": round(time.time() - start_time, 2)
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"改善分析中に予期しないエラーが発生しました: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"予期しないエラーが発生しました: {str(e)}",
            "error_en": f"Unexpected error: {str(e)}",
            "処理時間秒": round(time.time() - start_time, 2)
        }, ensure_ascii=False)


def _build_japanese_summarization_prompt(
    content: str, length: str, focus: str, context: Optional[str] = None
) -> str:
    """日本語文書要約用の専用プロンプトを構築します。"""
    
    # 長さ別の日本語指示
    length_instructions = {
        "brief": "重要なポイントを2-3文で簡潔にまとめてください。",
        "detailed": "主要な内容を1-2段落で詳細にまとめ、重要な詳細も含めてください。",
        "comprehensive": "全体の要点、重要な詳細、構造の概要、重要な示唆を含む包括的な要約を作成してください。"
    }
    
    # 焦点別の日本語指示
    focus_instructions = {
        "general": "一般読者向けに、主要なアイデアと全体的なメッセージに焦点を当ててください。",
        "technical": "技術的な詳細、方法論、実装の側面を重視してください。",
        "business": "ビジネス価値、成果、戦略的な影響を強調してください。"
    }
    
    prompt = f"""あなたは専門的な日本語文書分析の専門家です。以下の日本語文書を分析し、高品質な要約を作成してください。

要約の要件：
- 長さ: {length_instructions.get(length, length_instructions['comprehensive'])}
- 焦点: {focus_instructions.get(focus, focus_instructions['general'])}
- 重要なポイントを明確に抽出し、自然な日本語で表現してください
- 元の文書の意図と文脈を正確に保持してください
- 読みやすく、理解しやすい構造にしてください

{f"追加コンテキスト: {context}" if context else ""}

分析対象文書：
{content}

指定された要件に従って、構造化された日本語要約を提供してください。"""
    
    return prompt


def _build_japanese_improvement_prompt(
    content: str, summary_context: str, improvement_type: str, audience: str
) -> str:
    """日本語文書改善用の専用プロンプトを構築します。"""
    
    # 改善タイプ別の日本語指示
    improvement_instructions = {
        "structure": "文書の構成、見出し階層、論理的な流れに焦点を当ててください。",
        "content": "内容の品質、明確性、完全性、正確性に焦点を当ててください。",
        "readability": "文章スタイル、文の構造、読みやすさ、アクセシビリティに焦点を当ててください。",
        "comprehensive": "構造、内容、読みやすさ、全体的な効果性のすべての側面を分析してください。"
    }
    
    # 対象読者別の日本語指示
    audience_instructions = {
        "general": "様々な背景を持つ幅広い読者に対するアクセシビリティを考慮してください。",
        "technical": "技術的正確性、詳細レベル、専門的標準に焦点を当ててください。",
        "beginner": "明確性、説明、学習の進行を重視してください。",
        "expert": "深さ、正確性、高度な考慮事項に焦点を当ててください。"
    }
    
    prompt = f"""あなたは日本語技術文書の専門コンサルタントです。以下の日本語文書を分析し、詳細な改善提案を作成してください。

分析要件：
- 改善焦点: {improvement_instructions.get(improvement_type, improvement_instructions['comprehensive'])}
- 対象読者: {audience_instructions.get(audience, audience_instructions['general'])}
- 優先度別の改善提案を作成してください（高優先度/中優先度/低優先度）
- 具体的で実行可能な提案を提供してください
- 実装労力と期待効果を評価してください

日本語文書特有の評価項目：
- 文章の自然さと読みやすさ
- 専門用語の説明の適切性
- 構造の論理性と明確性
- 対象読者に適した敬語レベルと表現
- 日本語の文書構成（起承転結など）

{f"要約コンテキスト: {summary_context}" if summary_context else ""}

分析対象文書：
{content}

以下の形式で詳細な改善提案を日本語で提供してください：

■ 高優先度: [最も影響の大きい改善点]
・カテゴリ: [構造/内容/読みやすさ]
・具体的な改善内容
・実装労力: [低/中/高]
・期待効果: [低/中/高]

■ 中優先度: [中程度の影響がある改善点]
・カテゴリ: [構造/内容/読みやすさ]
・具体的な改善内容
・実装労力: [低/中/高]
・期待効果: [低/中/高]

■ 低優先度: [あればよい改善点]
・カテゴリ: [構造/内容/読みやすさ]
・具体的な改善内容
・実装労力: [低/中/高]
・期待効果: [低/中/高]"""
    
    return prompt


def _get_max_tokens_for_length(length: str) -> int:
    """要約長さに基づく適切なmax_tokensを取得します。"""
    token_limits = {
        "brief": 200,
        "detailed": 500,
        "comprehensive": 800
    }
    return token_limits.get(length, 800)


def _extract_japanese_key_points(summary_text: str) -> list:
    """日本語要約テキストから重要ポイントを抽出します。"""
    points = []
    
    # 文による分割とフィルタリング
    sentences = [s.strip() for s in summary_text.split('。') if s.strip()]
    
    # 実質的な内容を持つ文を重要ポイントとして取得
    for sentence in sentences[:5]:
        if len(sentence) > 10:  # 最小文字数
            points.append(sentence + '。')
    
    return points


def _parse_japanese_improvement_recommendations(recommendations_text: str) -> Dict[str, Any]:
    """LLM応答から日本語改善提案を解析し構造化します。"""
    # 日本語の改善提案を構造化
    structured = {
        "高優先度": [],
        "中優先度": [],
        "低優先度": []
    }
    
    current_priority = None
    lines = recommendations_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 優先度セクションを検出
        if '高優先度' in line:
            current_priority = '高優先度'
            continue
        elif '中優先度' in line:
            current_priority = '中優先度'
            continue
        elif '低優先度' in line:
            current_priority = '低優先度'
            continue
        
        # 改善提案を抽出
        if line.startswith('・') or line.startswith('-') or line.startswith('*'):
            if current_priority:
                recommendation = {
                    "カテゴリ": "一般",
                    "タイトル": line.lstrip('・-* ').split('：')[0] if '：' in line else line.lstrip('・-* '),
                    "説明": line.lstrip('・-* '),
                    "実装労力": "中",
                    "期待効果": "中"
                }
                structured[current_priority].append(recommendation)
    
    # 構造化された解析ができなかった場合の一般的な推奨事項
    if not any(structured.values()):
        structured["高優先度"] = [{
            "カテゴリ": "一般",
            "タイトル": "一般的な改善",
            "説明": recommendations_text,
            "実装労力": "中",
            "期待効果": "中"
        }]
    
    return structured


def _generate_japanese_overall_assessment(recommendations: Dict[str, Any]) -> Dict[str, Any]:
    """改善提案に基づく日本語総合評価を生成します。"""
    total_high = len(recommendations.get("高優先度", []))
    total_medium = len(recommendations.get("中優先度", []))
    total_low = len(recommendations.get("低優先度", []))
    total_recommendations = total_high + total_medium + total_low
    
    if total_high > 3:
        quality = "改善が必要"
        effort = "4-6時間"
    elif total_high > 1:
        quality = "良好"
        effort = "2-3時間"
    else:
        quality = "優秀"
        effort = "1-2時間"
    
    return {
        "現在の品質": quality,
        "総提案数": total_recommendations,
        "高優先度数": total_high,
        "改善可能性": "高" if total_high > 2 else "中" if total_high > 0 else "低",
        "予想作業時間": effort
    }


def _translate_focus_area(focus_area: str) -> str:
    """焦点領域を日本語に翻訳します。"""
    translations = {
        "general": "一般向け",
        "technical": "技術的",
        "business": "ビジネス向け"
    }
    return translations.get(focus_area, focus_area)


def _translate_length_type(length_type: str) -> str:
    """長さタイプを日本語に翻訳します。"""
    translations = {
        "brief": "簡潔",
        "detailed": "詳細",
        "comprehensive": "包括的"
    }
    return translations.get(length_type, length_type)


def _translate_improvement_type(improvement_type: str) -> str:
    """改善タイプを日本語に翻訳します。"""
    translations = {
        "structure": "構造",
        "content": "内容",
        "readability": "読みやすさ",
        "comprehensive": "包括的"
    }
    return translations.get(improvement_type, improvement_type)


def _translate_target_audience(target_audience: str) -> str:
    """対象読者を日本語に翻訳します。"""
    translations = {
        "general": "一般",
        "technical": "技術者",
        "beginner": "初心者",
        "expert": "専門家"
    }
    return translations.get(target_audience, target_audience)