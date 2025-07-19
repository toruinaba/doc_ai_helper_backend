"""
Comprehensive MCP tools for the core workflow.

This module provides consolidated, high-quality tools for the essential workflow:
1. Document content questions
2. Improvement recommendation summary  
3. Issue creation

These tools replace multiple redundant tools with focused, comprehensive functionality.
"""

from typing import Dict, Any, Optional, List
import json
import logging

logger = logging.getLogger(__name__)


async def analyze_document_comprehensive(
    document_content: str,
    analysis_type: str = "full",
    focus_area: str = "general"
) -> Dict[str, Any]:
    """
    Comprehensive document analysis combining structure, quality, and content analysis.
    
    This tool consolidates multiple analysis functions to provide complete document insights
    including structure, quality metrics, topics, completeness, and contextual information.
    
    Args:
        document_content: The document content to analyze
        analysis_type: Type of analysis - "full", "structure", "quality", "topics", "completeness"
        focus_area: Focus area for analysis - "general", "technical", "readability", "completeness"
        
    Returns:
        Comprehensive analysis results including structure, quality, topics, and recommendations
    """
    try:
        if not document_content.strip():
            return {
                "success": False,
                "error": "Document content is required for analysis",
                "analysis_type": analysis_type,
                "focus_area": focus_area
            }
        
        # Initialize result structure
        result = {
            "success": True,
            "analysis_type": analysis_type,
            "focus_area": focus_area,
            "document_length": len(document_content),
            "word_count": len(document_content.split()),
            "line_count": len(document_content.split('\n')),
        }
        
        # Document structure analysis
        if analysis_type in ["full", "structure"]:
            result["structure_analysis"] = _analyze_document_structure(document_content)
        
        # Document quality analysis
        if analysis_type in ["full", "quality"]:
            result["quality_analysis"] = _analyze_document_quality(document_content, focus_area)
        
        # Topic extraction
        if analysis_type in ["full", "topics"]:
            result["topic_analysis"] = _extract_document_topics(document_content)
        
        # Completeness check
        if analysis_type in ["full", "completeness"]:
            result["completeness_analysis"] = _check_document_completeness(document_content, focus_area)
        
        # Context extraction
        if analysis_type in ["full"]:
            result["context_summary"] = _extract_document_context(document_content)
        
        # Generate overall recommendations
        result["recommendations"] = _generate_analysis_recommendations(result, focus_area)
        
        logger.info(f"Document comprehensive analysis completed: {analysis_type} focus on {focus_area}")
        return result
        
    except Exception as e:
        logger.error(f"Error in comprehensive document analysis: {e}")
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}",
            "analysis_type": analysis_type,
            "focus_area": focus_area
        }


def _analyze_document_structure(content: str) -> Dict[str, Any]:
    """Analyze document structure including headings, sections, and hierarchy."""
    lines = content.split('\n')
    
    # Find headings (markdown style)
    headings = []
    heading_levels = {}
    
    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            heading_text = line.lstrip('#').strip()
            headings.append({
                "level": level,
                "text": heading_text,
                "line_number": i + 1
            })
            heading_levels[level] = heading_levels.get(level, 0) + 1
    
    # Analyze paragraph structure
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    
    return {
        "headings": headings,
        "heading_hierarchy": heading_levels,
        "total_headings": len(headings),
        "paragraph_count": len(paragraphs),
        "average_paragraph_length": sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0,
        "structure_score": _calculate_structure_score(headings, paragraphs)
    }


def _analyze_document_quality(content: str, focus_area: str) -> Dict[str, Any]:
    """Analyze document quality based on various criteria."""
    words = content.split()
    sentences = content.split('.')
    
    # Basic readability metrics
    avg_sentence_length = len(words) / len(sentences) if sentences else 0
    avg_word_length = sum(len(word.strip('.,!?;:')) for word in words) / len(words) if words else 0
    
    # Quality scoring
    quality_scores = {
        "readability": _calculate_readability_score(avg_sentence_length, avg_word_length),
        "clarity": _calculate_clarity_score(content),
        "completeness": _calculate_completeness_score(content),
        "technical_accuracy": _calculate_technical_score(content, focus_area)
    }
    
    overall_score = sum(quality_scores.values()) / len(quality_scores)
    
    return {
        "quality_scores": quality_scores,
        "overall_score": overall_score,
        "avg_sentence_length": avg_sentence_length,
        "avg_word_length": avg_word_length,
        "readability_level": _get_readability_level(overall_score),
        "improvement_areas": _identify_improvement_areas(quality_scores)
    }


def _extract_document_topics(content: str) -> Dict[str, Any]:
    """Extract main topics and themes from document content."""
    # Simple keyword-based topic extraction
    words = content.lower().split()
    word_freq = {}
    
    # Filter out common words and count frequencies
    common_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'a', 'an', 'this', 'that', 'these', 'those'}
    
    for word in words:
        word = word.strip('.,!?;:()[]{}"\'-').lower()
        if len(word) > 3 and word not in common_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Get top topics
    top_topics = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Identify themes based on word patterns
    themes = _identify_themes(content)
    
    return {
        "top_keywords": [{"word": word, "frequency": freq} for word, freq in top_topics],
        "identified_themes": themes,
        "topic_diversity": len(word_freq),
        "content_focus": _determine_content_focus(top_topics)
    }


def _check_document_completeness(content: str, focus_area: str) -> Dict[str, Any]:
    """Check document completeness against specified criteria."""
    completeness_checks = {
        "has_introduction": _has_introduction(content),
        "has_conclusion": _has_conclusion(content),
        "has_examples": _has_examples(content),
        "has_headings": _has_proper_headings(content),
        "has_structured_content": _has_structured_content(content)
    }
    
    if focus_area == "technical":
        completeness_checks.update({
            "has_code_examples": _has_code_examples(content),
            "has_installation_guide": _has_installation_guide(content),
            "has_usage_examples": _has_usage_examples(content)
        })
    
    completed_items = sum(1 for check in completeness_checks.values() if check)
    total_items = len(completeness_checks)
    completeness_score = completed_items / total_items if total_items > 0 else 0
    
    return {
        "completeness_checks": completeness_checks,
        "completeness_score": completeness_score,
        "completed_items": completed_items,
        "total_items": total_items,
        "missing_elements": [key for key, value in completeness_checks.items() if not value]
    }


def _extract_document_context(content: str) -> Dict[str, Any]:
    """Extract structured context from document content."""
    return {
        "document_type": _determine_document_type(content),
        "primary_purpose": _determine_primary_purpose(content),
        "target_audience": _determine_target_audience(content),
        "key_concepts": _extract_key_concepts(content),
        "summary": _generate_brief_summary(content)
    }


def _generate_analysis_recommendations(result: Dict[str, Any], focus_area: str) -> List[str]:
    """Generate recommendations based on analysis results."""
    recommendations = []
    
    # Structure recommendations
    if "structure_analysis" in result:
        structure = result["structure_analysis"]
        if structure["total_headings"] == 0:
            recommendations.append("Add section headings to improve document structure")
        if structure["structure_score"] < 0.7:
            recommendations.append("Improve document organization with clearer section hierarchy")
    
    # Quality recommendations
    if "quality_analysis" in result:
        quality = result["quality_analysis"]
        if quality["overall_score"] < 0.7:
            recommendations.append("Enhance overall document quality focusing on clarity and readability")
        for area in quality["improvement_areas"]:
            recommendations.append(f"Improve {area} for better document quality")
    
    # Completeness recommendations
    if "completeness_analysis" in result:
        completeness = result["completeness_analysis"]
        if completeness["completeness_score"] < 0.8:
            for missing in completeness["missing_elements"]:
                recommendations.append(f"Add {missing.replace('_', ' ')} to improve completeness")
    
    return recommendations


# Helper functions for analysis
def _calculate_structure_score(headings: List[Dict], paragraphs: List[str]) -> float:
    """Calculate structure quality score."""
    if not headings:
        return 0.3
    
    # Check heading hierarchy
    hierarchy_score = 0.5
    levels = [h["level"] for h in headings]
    if len(set(levels)) > 1:  # Multiple levels
        hierarchy_score = 0.8
    
    # Check paragraph distribution
    paragraph_score = min(len(paragraphs) / 10, 1.0)  # Ideal 10+ paragraphs
    
    return (hierarchy_score + paragraph_score) / 2


def _calculate_readability_score(avg_sentence_length: float, avg_word_length: float) -> float:
    """Calculate readability score."""
    # Ideal: 15-20 words per sentence, 4-5 letters per word
    sentence_score = max(0, 1 - abs(avg_sentence_length - 17.5) / 17.5)
    word_score = max(0, 1 - abs(avg_word_length - 4.5) / 4.5)
    return (sentence_score + word_score) / 2


def _calculate_clarity_score(content: str) -> float:
    """Calculate content clarity score."""
    # Simple heuristics for clarity
    sentences = content.split('.')
    questions = content.count('?')
    explanations = content.lower().count('because') + content.lower().count('therefore')
    
    clarity_indicators = min(explanations / len(sentences) * 10, 1.0) if sentences else 0
    return min(clarity_indicators + 0.3, 1.0)


def _calculate_completeness_score(content: str) -> float:
    """Calculate content completeness score."""
    # Check for various content indicators
    has_intro = any(word in content.lower() for word in ['introduction', 'overview', 'について'])
    has_examples = any(word in content.lower() for word in ['example', 'for example', '例'])
    has_conclusion = any(word in content.lower() for word in ['conclusion', 'summary', 'まとめ'])
    
    indicators = [has_intro, has_examples, has_conclusion]
    return sum(indicators) / len(indicators)


def _calculate_technical_score(content: str, focus_area: str) -> float:
    """Calculate technical accuracy score."""
    if focus_area != "technical":
        return 0.8  # Default score for non-technical content
    
    # Check for technical indicators
    has_code = '```' in content or '`' in content
    has_technical_terms = any(term in content.lower() for term in ['api', 'function', 'class', 'method', 'install'])
    
    return 0.5 + (0.25 if has_code else 0) + (0.25 if has_technical_terms else 0)


def _get_readability_level(score: float) -> str:
    """Get readability level description."""
    if score >= 0.8:
        return "Excellent"
    elif score >= 0.6:
        return "Good"
    elif score >= 0.4:
        return "Fair"
    else:
        return "Needs Improvement"


def _identify_improvement_areas(quality_scores: Dict[str, float]) -> List[str]:
    """Identify areas needing improvement."""
    threshold = 0.6
    return [area for area, score in quality_scores.items() if score < threshold]


def _identify_themes(content: str) -> List[str]:
    """Identify main themes in content."""
    themes = []
    content_lower = content.lower()
    
    # Technical themes
    if any(term in content_lower for term in ['api', 'code', 'function', 'development']):
        themes.append("Technical/Programming")
    
    # Documentation themes
    if any(term in content_lower for term in ['guide', 'tutorial', 'how to', 'installation']):
        themes.append("Documentation/Guide")
    
    # Business themes
    if any(term in content_lower for term in ['business', 'strategy', 'market', 'customer']):
        themes.append("Business/Strategy")
    
    return themes or ["General"]


def _determine_content_focus(top_topics: List[tuple]) -> str:
    """Determine the main focus of content."""
    if not top_topics:
        return "General"
    
    top_words = [word for word, _ in top_topics[:3]]
    
    technical_words = ['api', 'code', 'function', 'system', 'data', 'server']
    business_words = ['business', 'market', 'customer', 'strategy', 'revenue']
    
    if any(word in technical_words for word in top_words):
        return "Technical"
    elif any(word in business_words for word in top_words):
        return "Business"
    else:
        return "General"


# Document completeness check helper functions
def _has_introduction(content: str) -> bool:
    """Check if document has introduction."""
    content_lower = content.lower()
    return any(term in content_lower for term in ['introduction', 'overview', 'はじめに', 'について'])


def _has_conclusion(content: str) -> bool:
    """Check if document has conclusion."""
    content_lower = content.lower()
    return any(term in content_lower for term in ['conclusion', 'summary', 'まとめ', '結論'])


def _has_examples(content: str) -> bool:
    """Check if document has examples."""
    content_lower = content.lower()
    return any(term in content_lower for term in ['example', 'for example', '例', 'サンプル'])


def _has_proper_headings(content: str) -> bool:
    """Check if document has proper headings."""
    return content.count('#') > 0


def _has_structured_content(content: str) -> bool:
    """Check if document has structured content."""
    paragraphs = content.split('\n\n')
    return len(paragraphs) > 3


def _has_code_examples(content: str) -> bool:
    """Check if document has code examples."""
    return '```' in content or content.count('`') > 5


def _has_installation_guide(content: str) -> bool:
    """Check if document has installation guide."""
    content_lower = content.lower()
    return any(term in content_lower for term in ['install', 'setup', 'インストール', 'セットアップ'])


def _has_usage_examples(content: str) -> bool:
    """Check if document has usage examples."""
    content_lower = content.lower()
    return any(term in content_lower for term in ['usage', 'how to use', '使い方', '使用方法'])


# Context extraction helper functions
def _determine_document_type(content: str) -> str:
    """Determine document type."""
    content_lower = content.lower()
    
    if any(term in content_lower for term in ['readme', 'getting started', 'quick start']):
        return "README/Guide"
    elif any(term in content_lower for term in ['api', 'reference', 'documentation']):
        return "API Documentation"
    elif any(term in content_lower for term in ['tutorial', 'how to', 'step by step']):
        return "Tutorial"
    elif any(term in content_lower for term in ['specification', 'spec', 'requirements']):
        return "Specification"
    else:
        return "General Document"


def _determine_primary_purpose(content: str) -> str:
    """Determine primary purpose of document."""
    content_lower = content.lower()
    
    if any(term in content_lower for term in ['explain', 'describe', 'what is']):
        return "Explanation"
    elif any(term in content_lower for term in ['how to', 'tutorial', 'guide']):
        return "Instruction"
    elif any(term in content_lower for term in ['reference', 'api', 'documentation']):
        return "Reference"
    else:
        return "Information"


def _determine_target_audience(content: str) -> str:
    """Determine target audience."""
    content_lower = content.lower()
    
    if any(term in content_lower for term in ['beginner', 'getting started', 'basic']):
        return "Beginners"
    elif any(term in content_lower for term in ['advanced', 'expert', 'professional']):
        return "Advanced Users"
    elif any(term in content_lower for term in ['developer', 'programmer', 'coding']):
        return "Developers"
    else:
        return "General Users"


def _extract_key_concepts(content: str) -> List[str]:
    """Extract key concepts from content."""
    # Simple extraction based on capitalized terms and frequent words
    words = content.split()
    concepts = []
    
    for word in words:
        word = word.strip('.,!?;:()[]{}"\'-')
        if len(word) > 3 and word[0].isupper():
            concepts.append(word)
    
    # Return top 5 most frequent concepts
    from collections import Counter
    concept_counts = Counter(concepts)
    return [concept for concept, _ in concept_counts.most_common(5)]


def _generate_brief_summary(content: str) -> str:
    """Generate a brief summary of the content."""
    sentences = content.split('.')[:3]  # First 3 sentences
    summary = '. '.join(sentences).strip()
    return summary[:200] + "..." if len(summary) > 200 else summary


__all__ = [
    "analyze_document_comprehensive",
]