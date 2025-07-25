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
    repository_context: Optional[Dict[str, Any]] = None,
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
        # 入力検証とコンテンツ自動取得
        if not document_content or not document_content.strip():
            # Try to get document content from repository context
            if repository_context and repository_context.get("current_path"):
                try:
                    from doc_ai_helper_backend.services.git.factory import GitServiceFactory
                    
                    # Create git service
                    service_type = repository_context.get("service", "github")
                    git_service = GitServiceFactory.create(service_type)
                    
                    # Get document content
                    owner = repository_context.get("owner")
                    repo = repository_context.get("repo")
                    path = repository_context.get("current_path")
                    ref = repository_context.get("ref", "main")
                    
                    if owner and repo and path:
                        document_content = await git_service.get_file_content(owner, repo, path, ref)
                        logger.info(f"Auto-retrieved document content for summarization from {owner}/{repo}/{path}: {len(document_content)} chars")
                except Exception as e:
                    logger.warning(f"Failed to auto-retrieve document content for summarization: {e}")            
            
            # Still no content available
            if not document_content or not document_content.strip():
                return json.dumps({
                    "success": False,
                    "error": "Document content cannot be empty"
                }, ensure_ascii=False)
        
        # 日本語文書用の専用プロンプトを構築
        prompt = _build_japanese_summarization_prompt(
            document_content, summary_length, focus_area, context
        )
        
        # 設定から適切なモデルを取得
        from doc_ai_helper_backend.core.config import settings
        model = settings.default_openai_model or "gpt-3.5-turbo"
        
        # 内部LLM APIエンドポイントへの呼び出し
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/llm/query",
                json={
                    "prompt": prompt,
                    "provider": "openai",
                    "enable_tools": False,  # 循環呼び出し防止
                    "options": {
                        "model": model,
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
            
            # Calculate metrics for Japanese document processing
            original_length = len(document_content)
            summary_length_chars = len(summary_text)
            compression_ratio = summary_length_chars / original_length if original_length > 0 else 0
            processing_time = time.time() - start_time
            
            # Extract key points from Japanese document
            key_points = _extract_japanese_key_points(summary_text)
            
            result = {
                "success": True,
                "original_length": original_length,
                "summary": summary_text,
                "summary_length": summary_length_chars,
                "compression_ratio": round(compression_ratio, 3),
                "key_points": key_points,
                "focus_area": _translate_focus_area(focus_area),
                "length_type": _translate_length_type(summary_length),
                "processing_time_seconds": round(processing_time, 2),
                "metadata": {
                    "model_used": "gpt-3.5-turbo",
                    "temperature": 0.3,
                    "prompt_type": "japanese_document_summary",
                    "language": "japanese"
                }
            }
            
            logger.info(f"Japanese document summary completed in {processing_time:.2f} seconds")
            return json.dumps(result, indent=2, ensure_ascii=False)
            
    except httpx.TimeoutException:
        logger.error("LLM API timeout during summary processing")
        return json.dumps({
            "success": False,
            "error": "LLM processing timeout - please retry",
            "processing_time_seconds": round(time.time() - start_time, 2)
        }, ensure_ascii=False)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API HTTP error: {e.response.status_code}")
        return json.dumps({
            "success": False,
            "error": f"LLM API error occurred: {e.response.status_code}",
            "processing_time_seconds": round(time.time() - start_time, 2)
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Unexpected error during summary processing: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Unexpected error occurred: {str(e)}",
            "processing_time_seconds": round(time.time() - start_time, 2)
        }, ensure_ascii=False)


async def create_improvement_recommendations_with_llm(
    document_content: str,
    summary_context: str = "",
    improvement_type: str = "comprehensive",
    target_audience: str = "general",
    feedback_data: str = "",
    repository_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    専門レベルのLLM分析による日本語文書の詳細な改善提案を作成します。
    
    文書分析やフィードバックデータに基づいて、優先度別に分類された改善提案と
    実装ガイダンスを含む包括的な推奨事項を生成します。
    従来の create_improvement_proposal 機能も統合。
    
    Args:
        document_content: 分析対象の日本語文書内容
        summary_context: 事前分析の要約コンテキスト (オプション)
        improvement_type: 改善タイプ ("structure"=構造, "content"=内容, "readability"=読みやすさ, "comprehensive"=包括的)
        target_audience: 対象読者 ("general"=一般, "technical"=技術者, "beginner"=初心者, "expert"=専門家)
        feedback_data: フィードバック分析データ（JSON文字列、オプション）
        repository_context: リポジトリコンテキスト（自動注入）
        
    Returns:
        分類された推奨事項、優先度レベル、実装ガイダンスを含むJSON文字列
    """
    start_time = time.time()
    
    try:
        # 入力検証とコンテンツ自動取得
        if not document_content or not document_content.strip():
            # Try to get document content from repository context
            if repository_context and repository_context.get("current_path"):
                try:
                    from doc_ai_helper_backend.services.git.factory import GitServiceFactory
                    
                    # Create git service
                    service_type = repository_context.get("service", "github")
                    git_service = GitServiceFactory.create(service_type)
                    
                    # Get document content
                    owner = repository_context.get("owner")
                    repo = repository_context.get("repo")
                    path = repository_context.get("current_path")
                    ref = repository_context.get("ref", "main")
                    
                    if owner and repo and path:
                        document_content = await git_service.get_file_content(owner, repo, path, ref)
                        logger.info(f"Auto-retrieved document content for improvement analysis from {owner}/{repo}/{path}: {len(document_content)} chars")
                except Exception as e:
                    logger.warning(f"Failed to auto-retrieve document content for improvement analysis: {e}")            
            
            # Still no content available
            if not document_content or not document_content.strip():
                return json.dumps({
                    "success": False,
                    "error": "Document content cannot be empty"
                }, ensure_ascii=False)
        
        # 日本語文書改善用の専用プロンプトを構築
        prompt = _build_japanese_improvement_prompt(
            document_content, summary_context, improvement_type, target_audience
        )
        
        logger.info(f"Improvement analysis prompt: {prompt[:500]}...")  # Log prompt for debugging
        
        # 設定から適切なモデルを取得
        from doc_ai_helper_backend.core.config import settings
        model = settings.default_openai_model or "gpt-4"
        
        # 内部LLM APIエンドポイントへの呼び出し
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/v1/llm/query",
                json={
                    "prompt": prompt,
                    "provider": "openai",
                    "enable_tools": False,  # 循環呼び出し防止
                    "options": {
                        "model": model,
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
            logger.info(f"Raw LLM recommendations response: {recommendations_text[:500]}...")  # Log response for debugging
            
            # Parse and structure Japanese improvement recommendations
            structured_recommendations = _parse_japanese_improvement_recommendations(recommendations_text)
            logger.info(f"Parsed recommendations structure: {structured_recommendations}")  # Log parsed structure
            
            # Calculate processing metrics
            processing_time = time.time() - start_time
            
            result = {
                "success": True,
                "improvement_type": _translate_improvement_type(improvement_type),
                "target_audience": _translate_target_audience(target_audience),
                "recommendations": structured_recommendations,
                "overall_assessment": _generate_japanese_overall_assessment(structured_recommendations),
                "processing_time_seconds": round(processing_time, 2),
                "metadata": {
                    "model_used": "gpt-4",
                    "temperature": 0.4,
                    "prompt_type": "japanese_document_improvement_analysis",
                    "has_summary_context": bool(summary_context),
                    "language": "japanese"
                }
            }
            
            logger.info(f"Japanese document improvement recommendations generated in {processing_time:.2f} seconds")
            return json.dumps(result, indent=2, ensure_ascii=False)
            
    except httpx.TimeoutException:
        logger.error("LLM API timeout during improvement analysis")
        return json.dumps({
            "success": False,
            "error": "LLM processing timeout - please retry",
            "processing_time_seconds": round(time.time() - start_time, 2)
        }, ensure_ascii=False)
        
    except httpx.HTTPStatusError as e:
        logger.error(f"LLM API HTTP error: {e.response.status_code}")
        return json.dumps({
            "success": False,
            "error": f"LLM API error occurred: {e.response.status_code}",
            "processing_time_seconds": round(time.time() - start_time, 2)
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Unexpected error during improvement analysis: {str(e)}")
        return json.dumps({
            "success": False,
            "error": f"Unexpected error occurred: {str(e)}",
            "processing_time_seconds": round(time.time() - start_time, 2)
        }, ensure_ascii=False)


def _build_japanese_summarization_prompt(
    content: str, length: str, focus: str, context: Optional[str] = None
) -> str:
    """Build specialized prompt for Japanese document summarization."""
    
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
    """Build specialized prompt for Japanese document improvement."""
    
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

**重要**: 必ず以下の正確な形式で詳細な改善提案を日本語で提供してください：

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
・期待効果: [低/中/高]

各優先度レベルで最低1つの改善提案を提供し、■と・記号を正確に使用してください。"""
    
    return prompt


def _get_max_tokens_for_length(length: str) -> int:
    """Get appropriate max_tokens based on summary length."""
    token_limits = {
        "brief": 200,
        "detailed": 500,
        "comprehensive": 800
    }
    return token_limits.get(length, 800)


def _extract_japanese_key_points(summary_text: str) -> list:
    """Extract key points from Japanese summary text."""
    points = []
    
    # 文による分割とフィルタリング
    sentences = [s.strip() for s in summary_text.split('。') if s.strip()]
    
    # 実質的な内容を持つ文を重要ポイントとして取得
    for sentence in sentences[:5]:
        if len(sentence) > 10:  # 最小文字数
            points.append(sentence + '。')
    
    return points


def _parse_japanese_improvement_recommendations(recommendations_text: str) -> Dict[str, Any]:
    """Parse and structure improvement recommendations from LLM response."""
    # Structure Japanese improvement recommendations
    structured = {
        "高優先度": [],
        "中優先度": [],
        "低優先度": []
    }
    
    current_priority = None
    current_recommendation = None
    lines = recommendations_text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect priority sections with various formats
        if ('高優先度' in line or '■ 高優先度' in line or 
            'High Priority' in line or 'HIGH PRIORITY' in line):
            current_priority = '高優先度'
            continue
        elif ('中優先度' in line or '■ 中優先度' in line or 
              'Medium Priority' in line or 'MEDIUM PRIORITY' in line):
            current_priority = '中優先度'
            continue
        elif ('低優先度' in line or '■ 低優先度' in line or 
              'Low Priority' in line or 'LOW PRIORITY' in line):
            current_priority = '低優先度'
            continue
        
        # Extract improvement recommendations
        if (line.startswith('・') or line.startswith('-') or line.startswith('*') or 
            line.startswith('1.') or line.startswith('2.') or line.startswith('3.')):
            if current_priority:
                # Parse category if present
                category = "general"
                if 'カテゴリ:' in line or 'Category:' in line:
                    if '構造' in line or 'structure' in line.lower():
                        category = "structure"
                    elif '内容' in line or 'content' in line.lower():
                        category = "content"
                    elif '読みやすさ' in line or 'readability' in line.lower():
                        category = "readability"
                
                # Extract effort and impact
                effort = "medium"
                impact = "medium"
                if '実装労力:' in line or 'Implementation Effort:' in line.lower():
                    if '低' in line or 'low' in line.lower():
                        effort = "low"
                    elif '高' in line or 'high' in line.lower():
                        effort = "high"
                
                if '期待効果:' in line or 'Expected Impact:' in line.lower():
                    if '低' in line or 'low' in line.lower():
                        impact = "low"
                    elif '高' in line or 'high' in line.lower():
                        impact = "high"
                
                # Extract title and description
                clean_line = line.lstrip('・-*123. ')
                title = clean_line.split('：')[0] if '：' in clean_line else clean_line.split(':')[0] if ':' in clean_line else clean_line
                description = clean_line
                
                recommendation = {
                    "カテゴリ": category,
                    "タイトル": title[:100] if len(title) > 100 else title,  # Limit title length
                    "説明": description,
                    "実装労力": effort,
                    "期待効果": impact
                }
                structured[current_priority].append(recommendation)
        
        # Also check for multi-line recommendations
        elif current_priority and current_recommendation is None and line and not line.startswith('#'):
            # This might be a continuation or a simple recommendation
            recommendation = {
                "カテゴリ": "general",
                "タイトル": line[:50] + "..." if len(line) > 50 else line,
                "説明": line,
                "実装労力": "medium",
                "期待効果": "medium"
            }
            structured[current_priority].append(recommendation)
    
    # If no structured parsing worked, try to extract general recommendations
    if not any(structured.values()):
        # Split by sentences or paragraphs for general recommendations
        sentences = [s.strip() for s in recommendations_text.replace('。', '.').split('.') if s.strip() and len(s.strip()) > 10]
        
        for i, sentence in enumerate(sentences[:6]):  # Limit to 6 recommendations
            priority = "高優先度" if i < 2 else "中優先度" if i < 4 else "低優先度"
            recommendation = {
                "カテゴリ": "general",
                "タイトル": sentence[:50] + "..." if len(sentence) > 50 else sentence,
                "説明": sentence,
                "実装労力": "medium",
                "期待効果": "medium"
            }
            structured[priority].append(recommendation)
        
        # If still nothing, create a default recommendation
        if not any(structured.values()):
            structured["高優先度"] = [{
                "カテゴリ": "general",
                "タイトル": "文書改善提案",
                "説明": recommendations_text[:200] + "..." if len(recommendations_text) > 200 else recommendations_text,
                "実装労力": "medium",
                "期待効果": "medium"
            }]
    
    return structured


def _generate_japanese_overall_assessment(recommendations: Dict[str, Any]) -> Dict[str, Any]:
    """Generate overall assessment based on improvement recommendations."""
    total_high = len(recommendations.get("高優先度", []))
    total_medium = len(recommendations.get("中優先度", []))
    total_low = len(recommendations.get("低優先度", []))
    total_recommendations = total_high + total_medium + total_low
    
    if total_high > 3:
        quality = "要改善"
        effort = "4-6時間"
        potential = "非常に高い"
    elif total_high >= 1:
        quality = "良好"  
        effort = "2-3時間"
        potential = "高"
    else:
        quality = "優秀"
        effort = "1-2時間"
        potential = "低"
    
    return {
        "現在の品質": quality,
        "総提案数": total_recommendations,
        "高優先度数": total_high,
        "改善可能性": potential,
        "予想作業時間": effort
    }


def _translate_focus_area(focus_area: str) -> str:
    """Translate focus area to Japanese."""
    translations = {
        "general": "一般向け",
        "technical": "技術的",
        "business": "ビジネス向け"
    }
    return translations.get(focus_area, focus_area)


def _translate_length_type(length_type: str) -> str:
    """Translate length type to Japanese."""
    translations = {
        "brief": "簡潔",
        "detailed": "詳細",
        "comprehensive": "包括的"
    }
    return translations.get(length_type, length_type)


def _translate_improvement_type(improvement_type: str) -> str:
    """Translate improvement type to Japanese."""
    translations = {
        "structure": "構造",
        "content": "内容",
        "readability": "読みやすさ",
        "comprehensive": "包括的"
    }
    return translations.get(improvement_type, improvement_type)


def _translate_target_audience(target_audience: str) -> str:
    """Translate target audience to Japanese."""
    translations = {
        "general": "一般",
        "technical": "技術者",
        "beginner": "初心者",
        "expert": "専門家"
    }
    return translations.get(target_audience, target_audience)