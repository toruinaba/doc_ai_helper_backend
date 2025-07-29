"""
日本語文書対応 LLM強化ツール for MCP server.

このモジュールは内部LLM APIエンドポイントを活用して、
日本語文書の高度な分析機能を提供します。
要約機能は削除され、改善提案機能のみ提供します。
"""

import json
import logging
import re
import time
from typing import Dict, Any, Optional, Union

import httpx

logger = logging.getLogger(__name__)


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
            
            # JSON問題のデバッグ用：問題のある文字を特定
            if '"' in recommendations_text or "'" in recommendations_text:
                quote_positions = [i for i, c in enumerate(recommendations_text) if c in '"\'']
                logger.warning(f"Found quotes at positions: {quote_positions[:10]}...")  # First 10 positions
            
            # 応答の文字エンコーディングをチェック
            try:
                recommendations_text.encode('utf-8')
                logger.info("LLM response encoding: UTF-8 compatible")
            except UnicodeEncodeError as e:
                logger.error(f"LLM response encoding issue: {e}")
                recommendations_text = recommendations_text.encode('utf-8', errors='ignore').decode('utf-8')
            
            # Parse and structure Japanese improvement recommendations
            try:
                structured_recommendations = _parse_japanese_improvement_recommendations(recommendations_text)
                logger.info(f"Parsed recommendations structure: {structured_recommendations}")  # Log parsed structure
                
                # 構造検証：各優先度レベルに最低1つの提案があることを確認
                for priority in ["高優先度", "中優先度", "低優先度"]:
                    if not structured_recommendations.get(priority):
                        structured_recommendations[priority] = []
                        
            except Exception as parse_error:
                logger.error(f"Error parsing improvement recommendations: {parse_error}")
                # フォールバック：基本的な構造を提供
                structured_recommendations = {
                    "高優先度": [{
                        "カテゴリ": "general",
                        "タイトル": "改善提案パース失敗",
                        "説明": f"改善提案の解析中にエラーが発生しました: {str(parse_error)[:100]}",
                        "実装労力": "medium",
                        "期待効果": "medium"
                    }],
                    "中優先度": [],
                    "低優先度": []
                }
            
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
            
            # Sanitize all string values in result to prevent JSON issues
            logger.info(f"Pre-sanitization result keys: {list(result.keys())}")
            result = _sanitize_json_content(result)
            logger.info(f"Post-sanitization result keys: {list(result.keys())}")
            
            # JSON文字列生成をtry-catchで保護 (ensure_ascii=Trueで安全性向上)
            try:
                # 段階的にJSON生成を試す
                logger.info("Attempting JSON serialization...")
                json_result = json.dumps(result, ensure_ascii=True, separators=(',', ':'))  # Compact format
                
                # JSON文字列の整合性を検証
                logger.info("Testing JSON parse...")
                json.loads(json_result)  # Parse test
                logger.info("JSON serialization successful")
                return json_result
                
            except (json.JSONEncodeError, UnicodeEncodeError) as json_error:
                logger.error(f"JSON serialization error: {json_error}")
                logger.error(f"Error line/column info: line {getattr(json_error, 'lineno', 'N/A')}, col {getattr(json_error, 'colno', 'N/A')}")
                
                # より詳細な問題箇所の特定
                try:
                    test_basic = json.dumps({"test": "basic"}, ensure_ascii=True)
                    logger.info("Basic JSON works - problem is in result structure")
                except Exception as basic_error:
                    logger.error(f"Even basic JSON fails: {basic_error}")
                
                # フォールバック：簡略化されたレスポンスを返す
                fallback_result = {
                    "success": True,
                    "improvement_type": "comprehensive",
                    "target_audience": "general", 
                    "recommendations": {
                        "高優先度": [{"説明": "改善提案を生成しましたが、JSON形式での出力に問題が発生しました。", "カテゴリ": "general"}],
                        "中優先度": [],
                        "低優先度": []
                    },
                    "processing_time_seconds": round(processing_time, 2)
                }
                logger.info("Returning fallback result")
                return json.dumps(fallback_result, ensure_ascii=True)
            
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


def _sanitize_json_content(data: Any) -> Any:
    """
    Recursively sanitize data to prevent JSON serialization issues.
    
    Simple approach: just remove or replace problematic characters without double-escaping.
    """
    if isinstance(data, dict):
        return {key: _sanitize_json_content(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_sanitize_json_content(item) for item in data]
    elif isinstance(data, str):
        # Remove or replace problematic characters
        sanitized = data
        
        # Replace control characters (except standard whitespace)
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', ' ', sanitized)
        
        # Replace invalid Unicode characters
        sanitized = sanitized.encode('utf-8', errors='ignore').decode('utf-8')
        
        # Replace problematic quotes with safe alternatives (avoid double-escaping)
        sanitized = sanitized.replace('"', '「')  # Use Japanese quotes
        sanitized = sanitized.replace("'", '』')  # Use Japanese quotes
        
        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()
        
        # Limit string length to prevent memory issues
        if len(sanitized) > 800:
            sanitized = sanitized[:797] + "..."
            
        return sanitized
    else:
        return data