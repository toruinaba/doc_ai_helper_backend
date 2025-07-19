"""
Document analysis tools for MCP server.

This module provides advanced analysis tools for document quality,
topic extraction, and completeness checking.
"""

import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


async def analyze_document_quality(
    document_content: str, quality_metrics: List[str] = None
) -> Dict[str, Any]:
    """
    Analyze document quality across multiple dimensions.

    Args:
        document_content: Document content to analyze
        quality_metrics: List of specific quality metrics to evaluate

    Returns:
        Dict containing comprehensive quality analysis
    """
    try:
        # Default quality metrics if none specified
        if quality_metrics is None:
            quality_metrics = [
                "readability",
                "structure",
                "completeness",
                "consistency",
                "accessibility",
            ]

        # Initialize quality metrics
        metrics_results = {}

        if "readability" in quality_metrics:
            metrics_results["readability"] = analyze_readability_score(document_content)
        if "structure" in quality_metrics:
            metrics_results["structure"] = analyze_structure_quality(document_content)
        if "completeness" in quality_metrics:
            metrics_results["completeness"] = analyze_completeness_score(
                document_content
            )
        if "consistency" in quality_metrics:
            metrics_results["consistency"] = analyze_consistency_score(document_content)
        if "accessibility" in quality_metrics:
            metrics_results["accessibility"] = analyze_accessibility_score(
                document_content
            )

        # Calculate overall quality score
        overall_score = (
            sum(metrics_results.values()) / len(metrics_results)
            if metrics_results
            else 0
        )

        # Generate quality insights
        insights = generate_quality_insights(metrics_results, document_content)

        # Identify specific issues
        issues = identify_quality_issues(document_content, metrics_results)

        quality_analysis = {
            "overall_score": round(overall_score, 2),
            "metrics": metrics_results,
            "grade": calculate_quality_grade(overall_score),
            "insights": insights,
            "issues": issues,
            "recommendations": generate_quality_recommendations(
                metrics_results, issues
            ),
            "strengths": identify_strengths(metrics_results),
            "improvement_priority": prioritize_improvements(issues),
        }

        logger.info(
            f"Document quality analysis completed with score: {overall_score:.2f}"
        )
        return quality_analysis

    except Exception as e:
        logger.error(f"Error analyzing document quality: {e}")
        return {"error": str(e)}


async def extract_document_topics(
    document_content: str, topic_count: int = 5
) -> List[Dict[str, Any]]:
    """
    Extract main topics and themes from document content.

    Args:
        document_content: Document content to analyze
        topic_count: Number of topics to extract

    Returns:
        List of dictionaries containing extracted topics and analysis
    """
    try:
        # Simple keyword extraction (in real implementation, would use NLP libraries)
        words = extract_meaningful_words(document_content)

        # Count word frequencies
        word_frequencies = count_word_frequencies(words)

        # Extract potential topics
        topics = extract_topics_from_frequencies(word_frequencies, topic_count)

        # Identify semantic clusters
        semantic_clusters = identify_semantic_clusters(topics)

        # Extract section topics
        section_topics = extract_section_topics(document_content)

        # Convert to list format for FastMCP
        topics_list = []
        for i, topic in enumerate(topics[:topic_count]):
            topics_list.append(
                {
                    "rank": i + 1,
                    "topic": topic,
                    "weight": calculate_topic_weight(topic, document_content),
                    "section_coverage": get_section_coverage(topic, section_topics),
                }
            )

        logger.info(f"Extracted {len(topics_list)} topics from document")
        return topics_list

    except Exception as e:
        logger.error(f"Error extracting document topics: {e}")
        return [{"error": str(e)}]


async def check_document_completeness(
    document_content: str, template_type: str = "general"
) -> Dict[str, Any]:
    """
    Check document completeness against standard sections and best practices.

    Args:
        document_content: Document content to check
        template_type: Type of template (general, api, tutorial, reference, etc.)

    Returns:
        Dict containing completeness analysis
    """
    try:
        # Define standard sections for different document types
        standard_sections = get_standard_sections(template_type)

        # Extract actual sections from content
        actual_sections = extract_document_sections(document_content)

        # Check for missing sections
        missing_sections = find_missing_sections(standard_sections, actual_sections)

        # Check for empty sections
        empty_sections = find_empty_sections(actual_sections, document_content)

        # Analyze section quality
        section_quality = analyze_section_quality(actual_sections, document_content)

        # Check for essential elements
        essential_elements = check_essential_elements(document_content, template_type)

        # Calculate completeness score
        completeness_score = calculate_completeness_score(
            standard_sections, actual_sections, essential_elements
        )

        completeness_analysis = {
            "completeness_score": completeness_score,
            "grade": calculate_completeness_grade(completeness_score),
            "expected_sections": standard_sections,
            "actual_sections": [s["name"] for s in actual_sections],
            "missing_sections": missing_sections,
            "empty_sections": empty_sections,
            "section_quality": section_quality,
            "essential_elements": essential_elements,
            "recommendations": generate_completeness_recommendations(
                missing_sections, empty_sections, essential_elements
            ),
            "next_steps": suggest_next_steps(missing_sections, completeness_score),
        }

        logger.info(
            f"Document completeness analysis completed with score: {completeness_score:.2f}"
        )
        return completeness_analysis

    except Exception as e:
        logger.error(f"Error checking document completeness: {e}")
        return {"error": str(e)}


# Helper functions for quality analysis


def analyze_readability_score(content: str) -> float:
    """Calculate readability score based on sentence and word complexity."""
    if not content.strip():
        return 0.0

    # Simple readability metrics
    sentences = content.split(".")
    words = content.split()

    avg_sentence_length = len(words) / max(len(sentences), 1)
    avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

    # Simple scoring (inverse of complexity)
    readability = max(0, min(1, 1.0 - (avg_sentence_length + avg_word_length) / 50))
    return round(readability, 2)


def analyze_structure_quality(content: str) -> float:
    """Analyze document structure quality."""
    if not content.strip():
        return 0.0

    lines = content.split("\n")
    headings = [line for line in lines if line.strip().startswith("#")]

    # Score based on heading hierarchy and distribution
    has_main_title = any(line.strip().startswith("# ") for line in lines)
    has_subsections = any(line.strip().startswith("## ") for line in lines)
    heading_distribution = len(headings) / max(len(lines), 1)

    structure_score = 0.3  # Base score
    if has_main_title:
        structure_score += 0.3
    if has_subsections:
        structure_score += 0.2
    if 0.01 <= heading_distribution <= 0.1:  # Good heading ratio
        structure_score += 0.2

    return round(min(1.0, structure_score), 2)


def analyze_completeness_score(content: str) -> float:
    """Analyze document completeness."""
    if not content.strip():
        return 0.0

    # Check for common document elements
    has_intro = any(
        word in content.lower() for word in ["introduction", "overview", "about"]
    )
    has_examples = any(
        word in content.lower() for word in ["example", "for example", "```"]
    )
    has_conclusion = any(
        word in content.lower() for word in ["conclusion", "summary", "next steps"]
    )

    completeness = 0.4  # Base score for having content
    if has_intro:
        completeness += 0.2
    if has_examples:
        completeness += 0.2
    if has_conclusion:
        completeness += 0.2

    return round(completeness, 2)


def analyze_consistency_score(content: str) -> float:
    """Analyze document consistency."""
    if not content.strip():
        return 0.0

    # Simple consistency checks
    lines = content.split("\n")
    headings = [line for line in lines if line.strip().startswith("#")]

    # Check heading format consistency
    heading_formats = set()
    for heading in headings:
        # Count # symbols
        level = len(heading) - len(heading.lstrip("#"))
        heading_formats.add(level)

    # More consistent headings = higher score
    consistency = max(0.5, 1.0 - len(heading_formats) / 10)
    return round(consistency, 2)


def analyze_accessibility_score(content: str) -> float:
    """Analyze document accessibility."""
    if not content.strip():
        return 0.0

    # Check for accessibility features
    has_alt_text = "![" in content and "](" in content  # Basic image alt text check
    has_clear_headings = any(
        line.strip().startswith("#") for line in content.split("\n")
    )
    has_good_contrast = True  # Placeholder - would need color analysis

    accessibility = 0.5  # Base score
    if has_alt_text:
        accessibility += 0.2
    if has_clear_headings:
        accessibility += 0.2
    if has_good_contrast:
        accessibility += 0.1

    return round(accessibility, 2)


def generate_quality_insights(metrics: Dict[str, float], content: str) -> List[str]:
    """Generate insights based on quality metrics."""
    insights = []

    if metrics["readability"] < 0.6:
        insights.append(
            "Document may be difficult to read - consider simplifying language"
        )

    if metrics["structure"] < 0.6:
        insights.append("Document structure could be improved with better headings")

    if metrics["completeness"] < 0.6:
        insights.append("Document appears incomplete - missing key sections")

    return insights


def identify_quality_issues(
    content: str, metrics: Dict[str, float]
) -> List[Dict[str, Any]]:
    """Identify specific quality issues."""
    issues = []

    if metrics["readability"] < 0.5:
        issues.append(
            {
                "type": "readability",
                "severity": "high",
                "description": "Content is difficult to read",
                "suggestions": ["Use shorter sentences", "Simplify vocabulary"],
            }
        )

    if metrics["structure"] < 0.5:
        issues.append(
            {
                "type": "structure",
                "severity": "medium",
                "description": "Poor document structure",
                "suggestions": [
                    "Add clear headings",
                    "Organize content hierarchically",
                ],
            }
        )

    return issues


def calculate_quality_grade(score: float) -> str:
    """Calculate letter grade based on quality score."""
    if score >= 0.9:
        return "A"
    elif score >= 0.8:
        return "B"
    elif score >= 0.7:
        return "C"
    elif score >= 0.6:
        return "D"
    else:
        return "F"


def generate_quality_recommendations(
    metrics: Dict[str, float], issues: List[Dict[str, Any]]
) -> List[str]:
    """Generate quality improvement recommendations."""
    recommendations = []

    for issue in issues:
        recommendations.extend(issue.get("suggestions", []))

    return list(set(recommendations))  # Remove duplicates


def identify_strengths(metrics: Dict[str, float]) -> List[str]:
    """Identify document strengths."""
    strengths = []

    if metrics["readability"] >= 0.8:
        strengths.append("Excellent readability")
    if metrics["structure"] >= 0.8:
        strengths.append("Well-structured content")
    if metrics["completeness"] >= 0.8:
        strengths.append("Comprehensive coverage")

    return strengths


def prioritize_improvements(issues: List[Dict[str, Any]]) -> List[str]:
    """Prioritize improvement areas."""
    high_priority = [issue["type"] for issue in issues if issue["severity"] == "high"]
    medium_priority = [
        issue["type"] for issue in issues if issue["severity"] == "medium"
    ]

    return high_priority + medium_priority


# Helper functions for topic extraction


def extract_meaningful_words(content: str) -> List[str]:
    """Extract meaningful words from content."""
    # Simple word extraction (would use NLP in real implementation)
    words = re.findall(r"\b[a-zA-Z]{3,}\b", content.lower())

    # Filter out common stop words
    stop_words = {
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
    }
    return [word for word in words if word not in stop_words]


def count_word_frequencies(words: List[str]) -> Dict[str, int]:
    """Count word frequencies."""
    frequencies = {}
    for word in words:
        frequencies[word] = frequencies.get(word, 0) + 1
    return frequencies


def extract_topics_from_frequencies(
    frequencies: Dict[str, int], max_topics: int
) -> List[Dict[str, Any]]:
    """Extract topics from word frequencies."""
    sorted_words = sorted(frequencies.items(), key=lambda x: x[1], reverse=True)

    topics = []
    for word, count in sorted_words[:max_topics]:
        topics.append(
            {
                "topic": word,
                "frequency": count,
                "weight": count / sum(frequencies.values()),
            }
        )

    return topics


def identify_semantic_clusters(topics: List[Dict[str, Any]]) -> List[List[str]]:
    """Identify semantic clusters of topics."""
    # Simple clustering placeholder
    return [["development", "programming"], ["documentation", "writing"]]


def extract_section_topics(content: str) -> Dict[str, List[str]]:
    """Extract topics for each section."""
    sections = {}
    current_section = "Introduction"

    for line in content.split("\n"):
        if line.strip().startswith("#"):
            current_section = line.strip("#").strip()
            sections[current_section] = []
        else:
            # Extract words from line
            words = extract_meaningful_words(line)
            sections.setdefault(current_section, []).extend(
                words[:3]
            )  # Top 3 words per line

    return sections


def calculate_topic_distribution(topics: List[Dict[str, Any]]) -> Dict[str, float]:
    """Calculate topic distribution."""
    total_weight = sum(topic["weight"] for topic in topics)
    return {topic["topic"]: topic["weight"] / total_weight for topic in topics}


def analyze_topic_coverage(
    content: str, topics: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Analyze how well topics are covered."""
    return {
        "coverage_score": 0.8,
        "balanced_coverage": True,
        "underrepresented_topics": [],
    }


def calculate_keyword_density(
    content: str, topics: List[Dict[str, Any]]
) -> Dict[str, float]:
    """Calculate keyword density for topics."""
    total_words = len(content.split())
    densities = {}

    for topic in topics[:5]:  # Top 5 topics
        topic_name = topic["topic"]
        frequency = topic["frequency"]
        densities[topic_name] = frequency / total_words

    return densities


def calculate_topic_coherence(topics: List[Dict[str, Any]], content: str) -> float:
    """Calculate topic coherence score."""
    return 0.75  # Placeholder


# Helper functions for completeness analysis


def get_standard_sections(document_type: str) -> List[str]:
    """Get standard sections for different document types."""
    sections_map = {
        "api": [
            "Introduction",
            "Authentication",
            "Endpoints",
            "Examples",
            "Error Codes",
        ],
        "tutorial": [
            "Introduction",
            "Prerequisites",
            "Steps",
            "Examples",
            "Conclusion",
        ],
        "reference": ["Overview", "Syntax", "Parameters", "Return Values", "Examples"],
        "general": ["Introduction", "Content", "Conclusion"],
    }
    return sections_map.get(document_type, sections_map["general"])


def extract_document_sections(content: str) -> List[Dict[str, Any]]:
    """Extract sections from document content."""
    sections = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        if line.strip().startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            name = line.strip("#").strip()
            sections.append({"name": name, "level": level, "line_number": i + 1})

    return sections


def find_missing_sections(
    expected: List[str], actual: List[Dict[str, Any]]
) -> List[str]:
    """Find missing sections."""
    actual_names = [section["name"].lower() for section in actual]
    return [section for section in expected if section.lower() not in actual_names]


def find_empty_sections(sections: List[Dict[str, Any]], content: str) -> List[str]:
    """Find sections with little or no content."""
    # Simplified implementation
    return []


def analyze_section_quality(
    sections: List[Dict[str, Any]], content: str
) -> Dict[str, Any]:
    """Analyze the quality of document sections."""
    return {
        "average_section_length": 100,
        "well_structured": True,
        "consistent_formatting": True,
    }


def check_essential_elements(content: str, document_type: str) -> Dict[str, bool]:
    """Check for essential document elements."""
    return {
        "has_title": content.strip().startswith("#"),
        "has_introduction": "introduction" in content.lower(),
        "has_examples": "example" in content.lower(),
        "has_conclusion": any(
            word in content.lower() for word in ["conclusion", "summary"]
        ),
    }


def calculate_completeness_score(
    expected: List[str], actual: List[Dict[str, Any]], elements: Dict[str, bool]
) -> float:
    """Calculate completeness score."""
    section_score = len(actual) / max(len(expected), 1)
    element_score = sum(elements.values()) / max(len(elements), 1)

    return round(min(1.0, (section_score + element_score) / 2), 2)


def calculate_completeness_grade(score: float) -> str:
    """Calculate completeness grade."""
    return calculate_quality_grade(score)


def generate_completeness_recommendations(
    missing: List[str], empty: List[str], elements: Dict[str, bool]
) -> List[str]:
    """Generate completeness recommendations."""
    recommendations = []

    if missing:
        recommendations.append(f"Add missing sections: {', '.join(missing)}")

    if empty:
        recommendations.append(f"Add content to empty sections: {', '.join(empty)}")

    for element, present in elements.items():
        if not present:
            recommendations.append(
                f"Add {element.replace('has_', '').replace('_', ' ')}"
            )

    return recommendations


def suggest_next_steps(
    missing_sections: List[str], completeness_score: float
) -> List[str]:
    """Suggest next steps for improvement."""
    steps = []

    if completeness_score < 0.5:
        steps.append("Focus on adding missing essential sections")

    if missing_sections:
        steps.append(
            f"Prioritize adding: {missing_sections[0] if missing_sections else 'content'}"
        )

    steps.append("Review and expand existing content")

    return steps


def calculate_topic_weight(topic: str, content: str) -> float:
    """Calculate weight/importance of a topic in the content."""
    return min(1.0, content.lower().count(topic.lower()) / 100.0)


def get_section_coverage(topic: str, section_topics: List[str]) -> str:
    """Get section coverage information for a topic."""
    for section in section_topics:
        if topic.lower() in section.lower():
            return section
    return "general"


def get_standard_sections(template_type: str) -> List[str]:
    """Get standard sections for different template types."""
    templates = {
        "general": ["Introduction", "Content", "Conclusion"],
        "api": ["Overview", "Authentication", "Endpoints", "Examples", "Error Codes"],
        "tutorial": [
            "Introduction",
            "Prerequisites",
            "Steps",
            "Examples",
            "Next Steps",
        ],
        "reference": ["Overview", "Syntax", "Parameters", "Examples", "See Also"],
    }
    return templates.get(template_type, templates["general"])
