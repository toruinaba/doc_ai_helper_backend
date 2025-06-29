"""
Document processing tools for MCP server.

This module provides tools for document analysis, context extraction,
and content optimization.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


async def extract_document_context(
    document_content: str,
    repository: str = "",
    path: str = "",
    title: str = "",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Extract structured context from document content.

    Args:
        document_content: Document content text
        repository: Repository identifier
        path: Document file path
        title: Document title (optional)
        metadata: Additional metadata (optional)

    Returns:
        JSON string containing structured document context
    """
    try:
        # Basic document analysis
        word_count = len(document_content.split())
        line_count = len(document_content.split("\n"))

        # Extract headings (simple markdown heading detection)
        headings = []
        for line in document_content.split("\n"):
            if line.strip().startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                heading_text = line.lstrip("#").strip()
                if heading_text:
                    headings.append({"level": level, "text": heading_text})

        # Basic structure analysis
        has_code_blocks = "```" in document_content
        has_links = "[" in document_content and "](" in document_content
        has_images = "![" in document_content

        context = {
            "title": title or "Untitled Document",
            "content": document_content,
            "path": path,
            "repository": repository,
            "metadata": metadata or {},
            "analysis": {
                "word_count": word_count,
                "line_count": line_count,
                "headings": headings,
                "has_code_blocks": has_code_blocks,
                "has_links": has_links,
                "has_images": has_images,
                "structure_score": min(1.0, len(headings) / 5.0),  # Basic scoring
            },
        }

        logger.info(f"Extracted context for document: {title or path}")

        # FastMCPではJSON文字列として返す
        import json

        return json.dumps(context, indent=2)

    except Exception as e:
        logger.error(f"Error extracting document context: {e}")
        import json

        return json.dumps(
            {
                "title": title,
                "content": document_content,
                "path": path,
                "repository": repository,
                "error": str(e),
            }
        )


async def analyze_document_structure(
    document_content: str, document_type: str = "markdown"
) -> Dict[str, Any]:
    """
    Analyze the structure and organization of a document.

    Args:
        document_content: Document content to analyze
        document_type: Type of document (markdown, html, etc.)

    Returns:
        Dict containing structure analysis
    """
    try:
        lines = document_content.split("\n")

        # Count different elements
        heading_levels = {}
        code_blocks = 0
        lists = 0
        links = 0
        images = 0

        in_code_block = False

        for line in lines:
            stripped = line.strip()

            # Track code blocks
            if stripped.startswith("```"):
                if in_code_block:
                    code_blocks += 1
                in_code_block = not in_code_block
                continue

            if in_code_block:
                continue

            # Count headings by level
            if stripped.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                heading_levels[level] = heading_levels.get(level, 0) + 1

            # Count lists
            if (
                stripped.startswith("-")
                or stripped.startswith("*")
                or stripped.startswith("+")
            ):
                lists += 1

            # Count links and images
            links += line.count("](")
            images += line.count("![")

        # Calculate structure metrics
        total_headings = sum(heading_levels.values())
        has_proper_hierarchy = len(heading_levels) > 1

        structure_analysis = {
            "heading_levels": heading_levels,
            "total_headings": total_headings,
            "code_blocks": code_blocks,
            "lists": lists,
            "links": links,
            "images": images,
            "has_proper_hierarchy": has_proper_hierarchy,
            "structure_quality": calculate_structure_quality(
                heading_levels, code_blocks, lists
            ),
            "recommendations": generate_structure_recommendations(
                heading_levels, code_blocks, lists
            ),
        }

        logger.info("Document structure analysis completed")
        return structure_analysis

    except Exception as e:
        logger.error(f"Error analyzing document structure: {e}")
        return {"error": str(e)}


async def optimize_document_content(
    document_content: str, optimization_type: str = "readability"
) -> str:
    """
    Optimize document content for better readability or structure.

    Args:
        document_content: Document content to optimize
        optimization_type: Type of optimization (readability, structure, seo)    Returns:
        JSON string containing optimization suggestions
    """
    try:
        suggestions = []

        if optimization_type == "readability":
            suggestions = analyze_readability(document_content)
        elif optimization_type == "structure":
            suggestions = analyze_structure_improvements(document_content)
        elif optimization_type == "seo":
            suggestions = analyze_seo_improvements(document_content)
        else:
            suggestions = ["Unknown optimization type"]

        optimization_result = {
            "original_content": document_content,
            "optimization_type": optimization_type,
            "suggestions": suggestions,
            "priority": "medium",  # Could be calculated based on suggestions
            "estimated_improvement": "15-25%",  # Placeholder
        }

        logger.info(f"Content optimization completed for type: {optimization_type}")

        # FastMCPではJSON文字列として返す
        import json

        return json.dumps(optimization_result, indent=2)

    except Exception as e:
        logger.error(f"Error optimizing document content: {e}")
        import json

        return json.dumps({"error": str(e)})


def calculate_structure_quality(
    heading_levels: Dict[int, int], code_blocks: int, lists: int
) -> float:
    """Calculate a quality score for document structure."""
    score = 0.5  # Base score

    # Good heading hierarchy
    if heading_levels.get(1, 0) > 0:  # Has main title
        score += 0.2
    if len(heading_levels) > 1:  # Has multiple levels
        score += 0.2
    if heading_levels.get(2, 0) > 0:  # Has subsections
        score += 0.1

    return min(1.0, score)


def generate_structure_recommendations(
    heading_levels: Dict[int, int], code_blocks: int, lists: int
) -> List[str]:
    """Generate recommendations for improving document structure."""
    recommendations = []

    if not heading_levels.get(1, 0):
        recommendations.append("Consider adding a main title (# Title)")

    if len(heading_levels) == 1:
        recommendations.append("Consider adding subsections with ## headings")

    if code_blocks == 0 and lists == 0:
        recommendations.append(
            "Consider adding examples or bullet points for better readability"
        )

    return recommendations


def analyze_readability(content: str) -> List[str]:
    """Analyze content for readability improvements."""
    suggestions = []

    # Check paragraph length
    paragraphs = content.split("\n\n")
    long_paragraphs = [p for p in paragraphs if len(p.split()) > 100]

    if long_paragraphs:
        suggestions.append(
            "Consider breaking up long paragraphs for better readability"
        )

    # Check sentence length (simple approximation)
    sentences = content.split(".")
    long_sentences = [s for s in sentences if len(s.split()) > 25]

    if long_sentences:
        suggestions.append("Consider shortening complex sentences")

    return suggestions


def analyze_structure_improvements(content: str) -> List[str]:
    """Analyze content for structure improvements."""
    suggestions = []

    # Check for introduction and conclusion
    if not content.lower().startswith(("introduction", "overview", "about")):
        suggestions.append("Consider adding an introduction section")

    if not any(
        word in content.lower() for word in ["conclusion", "summary", "next steps"]
    ):
        suggestions.append("Consider adding a conclusion or summary section")

    return suggestions


def analyze_seo_improvements(content: str) -> List[str]:
    """Analyze content for SEO improvements."""
    suggestions = []

    # Check for meta information
    if "title:" not in content.lower() and "# " not in content:
        suggestions.append("Consider adding a clear title")

    if "description:" not in content.lower():
        suggestions.append("Consider adding a description for better discoverability")

    return suggestions
