"""
Test data generator for E2E tests.

This module provides utilities to generate test data for user story-based E2E tests.
"""

import random
import string
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path


class TestDataGenerator:
    """Generator for test data used in E2E tests."""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_repository_config(
        self,
        service: str = "github",
        owner: Optional[str] = None,
        repo: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generate repository configuration for testing."""
        return {
            "service": service,
            "owner": owner or self._generate_username(),
            "repo": repo or self._generate_repo_name(),
            "ref": "main",
        }

    def generate_document_path(
        self,
        extension: str = "md",
        nested: bool = True,
    ) -> str:
        """Generate a document path for testing."""
        if nested:
            directories = [self._generate_word() for _ in range(random.randint(1, 3))]
            filename = f"{self._generate_word()}.{extension}"
            return "/".join(directories + [filename])
        else:
            return f"{self._generate_word()}.{extension}"

    def generate_markdown_content(
        self,
        title: Optional[str] = None,
        sections: int = 3,
        include_frontmatter: bool = True,
        include_links: bool = True,
    ) -> str:
        """Generate Markdown content for testing."""
        content_parts = []

        # Add frontmatter
        if include_frontmatter:
            frontmatter = self.generate_frontmatter(title=title)
            content_parts.append("---")
            for key, value in frontmatter.items():
                if isinstance(value, list):
                    value_str = json.dumps(value)
                elif isinstance(value, str):
                    value_str = f'"{value}"'
                else:
                    value_str = str(value)
                content_parts.append(f"{key}: {value_str}")
            content_parts.append("---")
            content_parts.append("")

        # Add main title
        if title:
            content_parts.append(f"# {title}")
        else:
            content_parts.append(f"# {self._generate_title()}")
        content_parts.append("")

        # Add introduction
        content_parts.append(self._generate_paragraph())
        content_parts.append("")

        # Add sections
        for i in range(sections):
            section_title = self._generate_title()
            content_parts.append(f"## {section_title}")
            content_parts.append("")

            # Add section content
            for _ in range(random.randint(1, 3)):
                content_parts.append(self._generate_paragraph())
                content_parts.append("")

            # Add links if requested
            if include_links and random.choice([True, False]):
                link_text = self._generate_word().title()
                link_url = self._generate_url()
                content_parts.append(
                    f"For more information, see [{link_text}]({link_url})."
                )
                content_parts.append("")

        return "\n".join(content_parts)

    def generate_frontmatter(
        self,
        title: Optional[str] = None,
        author: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate frontmatter for testing."""
        return {
            "title": title or self._generate_title(),
            "description": self._generate_sentence(),
            "author": author or self._generate_full_name(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "tags": [self._generate_word() for _ in range(random.randint(2, 5))],
            "category": random.choice(
                ["documentation", "tutorial", "guide", "reference"]
            ),
        }

    def generate_user_persona(
        self,
        role: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate a user persona for testing."""
        roles = [
            "developer",
            "tech_writer",
            "project_manager",
            "student",
            "researcher",
        ]

        selected_role = role or random.choice(roles)

        persona = {
            "id": f"test_{selected_role}_{random.randint(1000, 9999)}",
            "name": self._generate_full_name(),
            "role": selected_role,
            "experience_level": random.choice(["beginner", "intermediate", "advanced"]),
            "goals": [self._generate_goal() for _ in range(random.randint(2, 4))],
            "pain_points": [
                self._generate_pain_point() for _ in range(random.randint(1, 3))
            ],
            "preferred_tools": [
                random.choice(["VS Code", "GitHub", "Notion", "Slack", "Discord"])
                for _ in range(random.randint(2, 4))
            ],
        }

        return persona

    def generate_test_scenario(
        self,
        scenario_type: str = "document_exploration",
    ) -> Dict[str, Any]:
        """Generate a test scenario configuration."""
        scenarios = {
            "document_exploration": self._generate_exploration_scenario,
            "ai_assistance": self._generate_ai_scenario,
            "team_collaboration": self._generate_collaboration_scenario,
            "onboarding": self._generate_onboarding_scenario,
        }

        generator = scenarios.get(scenario_type, self._generate_exploration_scenario)
        return generator()

    def generate_api_test_data(
        self,
        endpoint_type: str,
    ) -> Dict[str, Any]:
        """Generate test data for API endpoints."""
        if endpoint_type == "document":
            return {
                "service": "github",
                "owner": self._generate_username(),
                "repo": self._generate_repo_name(),
                "path": self.generate_document_path(),
                "ref": "main",
                "transform_links": True,
            }
        elif endpoint_type == "llm_query":
            return {
                "prompt": self._generate_question(),
                "context": {
                    "documents": [
                        {
                            "path": self.generate_document_path(),
                            "content": self._generate_paragraph(),
                        }
                    ]
                },
                "options": {
                    "model": "gpt-4",
                    "max_tokens": 500,
                    "temperature": 0.7,
                },
            }
        else:
            return {}

    def _generate_username(self) -> str:
        """Generate a random username."""
        prefixes = ["dev", "user", "team", "org", "project"]
        suffixes = [str(random.randint(100, 999)), self._generate_word()]
        return f"{random.choice(prefixes)}{random.choice(suffixes)}"

    def _generate_repo_name(self) -> str:
        """Generate a random repository name."""
        adjectives = ["awesome", "simple", "modern", "fast", "clean"]
        nouns = ["docs", "guide", "tutorial", "project", "tool"]
        return f"{random.choice(adjectives)}-{random.choice(nouns)}"

    def _generate_word(self) -> str:
        """Generate a random word."""
        words = [
            "documentation",
            "guide",
            "tutorial",
            "reference",
            "manual",
            "overview",
            "introduction",
            "getting",
            "started",
            "advanced",
            "configuration",
            "setup",
            "installation",
            "deployment",
            "usage",
            "examples",
            "samples",
            "troubleshooting",
            "faq",
            "best",
            "practices",
            "patterns",
            "architecture",
            "design",
            "development",
        ]
        return random.choice(words)

    def _generate_title(self) -> str:
        """Generate a random title."""
        templates = [
            "{action} {noun}",
            "{adjective} {noun} {action}",
            "How to {action} {noun}",
            "{noun} {action} Guide",
            "Understanding {noun}",
        ]

        actions = ["Getting Started with", "Building", "Creating", "Managing", "Using"]
        adjectives = ["Advanced", "Complete", "Essential", "Practical", "Modern"]
        nouns = ["Documentation", "API", "System", "Framework", "Tool"]

        template = random.choice(templates)
        return template.format(
            action=random.choice(actions),
            adjective=random.choice(adjectives),
            noun=random.choice(nouns),
        )

    def _generate_sentence(self) -> str:
        """Generate a random sentence."""
        templates = [
            "This {noun} provides {description} for {audience}.",
            "Learn how to {action} {object} with this {resource}.",
            "A {adjective} guide to {topic} and {related_topic}.",
            "Discover the {quality} of {technology} in this {resource}.",
        ]

        template = random.choice(templates)
        return template.format(
            noun=random.choice(["document", "guide", "tutorial", "resource"]),
            description=random.choice(
                [
                    "comprehensive information",
                    "detailed instructions",
                    "practical examples",
                ]
            ),
            audience=random.choice(["developers", "users", "teams", "beginners"]),
            action=random.choice(["implement", "configure", "optimize", "understand"]),
            object=random.choice(["features", "systems", "workflows", "processes"]),
            resource=random.choice(["guide", "tutorial", "documentation", "manual"]),
            adjective=random.choice(
                ["comprehensive", "practical", "detailed", "complete"]
            ),
            topic=random.choice(
                ["development", "configuration", "deployment", "testing"]
            ),
            related_topic=random.choice(
                ["best practices", "troubleshooting", "optimization", "security"]
            ),
            quality=random.choice(
                ["power", "flexibility", "simplicity", "effectiveness"]
            ),
            technology=random.choice(
                ["this tool", "modern frameworks", "cloud platforms", "automation"]
            ),
        )

    def _generate_paragraph(self) -> str:
        """Generate a random paragraph."""
        sentences = [self._generate_sentence() for _ in range(random.randint(3, 6))]
        return " ".join(sentences)

    def _generate_full_name(self) -> str:
        """Generate a random full name."""
        first_names = [
            "Alex",
            "Jordan",
            "Casey",
            "Morgan",
            "Taylor",
            "Riley",
            "Avery",
            "Quinn",
        ]
        last_names = [
            "Smith",
            "Johnson",
            "Brown",
            "Wilson",
            "Davis",
            "Miller",
            "Jones",
            "Garcia",
        ]
        return f"{random.choice(first_names)} {random.choice(last_names)}"

    def _generate_url(self) -> str:
        """Generate a random URL."""
        domains = ["example.com", "test.org", "demo.net", "sample.io"]
        paths = ["docs", "guide", "help", "tutorial", "reference"]
        return f"https://{random.choice(domains)}/{random.choice(paths)}"

    def _generate_goal(self) -> str:
        """Generate a user goal."""
        goals = [
            "Find relevant documentation quickly",
            "Understand complex technical concepts",
            "Get help with implementation details",
            "Learn best practices and patterns",
            "Collaborate effectively with team members",
            "Stay updated with latest changes",
            "Troubleshoot common issues",
            "Improve development workflow",
        ]
        return random.choice(goals)

    def _generate_pain_point(self) -> str:
        """Generate a user pain point."""
        pain_points = [
            "Documentation is hard to find",
            "Information is outdated or incomplete",
            "Too much technical jargon",
            "Lack of practical examples",
            "Difficulty navigating complex structures",
            "Inconsistent formatting and style",
            "Missing context and background information",
            "Poor search functionality",
        ]
        return random.choice(pain_points)

    def _generate_question(self) -> str:
        """Generate a random question."""
        questions = [
            "How do I get started with this project?",
            "What are the best practices for configuration?",
            "Can you explain the main concepts?",
            "How do I troubleshoot common issues?",
            "What are the key features and capabilities?",
            "How does this compare to other solutions?",
            "What are the requirements and prerequisites?",
            "Can you provide some practical examples?",
        ]
        return random.choice(questions)

    def _generate_exploration_scenario(self) -> Dict[str, Any]:
        """Generate a document exploration scenario."""
        return {
            "id": f"exploration_{random.randint(1000, 9999)}",
            "name": "Document Exploration Journey",
            "description": "User explores documentation to find specific information",
            "steps": [
                {
                    "action": "browse_repository",
                    "expected_outcome": "Repository structure is displayed",
                },
                {
                    "action": "search_documents",
                    "query": self._generate_word(),
                    "expected_outcome": "Relevant documents are found",
                },
                {
                    "action": "view_document",
                    "expected_outcome": "Document content is properly formatted",
                },
                {
                    "action": "follow_links",
                    "expected_outcome": "Links navigate to correct destinations",
                },
            ],
            "success_criteria": [
                "All documents load successfully",
                "Links are properly transformed",
                "Content is well-formatted",
                "Navigation is intuitive",
            ],
        }

    def _generate_ai_scenario(self) -> Dict[str, Any]:
        """Generate an AI assistance scenario."""
        return {
            "id": f"ai_assistance_{random.randint(1000, 9999)}",
            "name": "AI-Assisted Documentation Journey",
            "description": "User gets AI help to understand and improve documentation",
            "steps": [
                {
                    "action": "ask_question",
                    "question": self._generate_question(),
                    "expected_outcome": "AI provides helpful response",
                },
                {
                    "action": "request_summary",
                    "expected_outcome": "AI generates document summary",
                },
                {
                    "action": "get_suggestions",
                    "expected_outcome": "AI suggests improvements",
                },
            ],
            "success_criteria": [
                "AI responses are relevant and helpful",
                "Suggestions are actionable",
                "Response time is acceptable",
                "Context is properly understood",
            ],
        }

    def _generate_collaboration_scenario(self) -> Dict[str, Any]:
        """Generate a team collaboration scenario."""
        return {
            "id": f"collaboration_{random.randint(1000, 9999)}",
            "name": "Team Collaboration Journey",
            "description": "Team members collaborate on documentation improvements",
            "steps": [
                {
                    "action": "review_document",
                    "expected_outcome": "Document is analyzed for quality",
                },
                {
                    "action": "provide_feedback",
                    "expected_outcome": "Feedback is recorded and categorized",
                },
                {
                    "action": "suggest_improvements",
                    "expected_outcome": "Improvement suggestions are generated",
                },
                {
                    "action": "track_changes",
                    "expected_outcome": "Changes are monitored and reported",
                },
            ],
            "success_criteria": [
                "Feedback is properly captured",
                "Suggestions are relevant",
                "Collaboration is seamless",
                "Progress is trackable",
            ],
        }

    def _generate_onboarding_scenario(self) -> Dict[str, Any]:
        """Generate an onboarding scenario."""
        return {
            "id": f"onboarding_{random.randint(1000, 9999)}",
            "name": "New User Onboarding Journey",
            "description": "New user discovers and learns the system",
            "steps": [
                {
                    "action": "discover_features",
                    "expected_outcome": "Available features are presented",
                },
                {
                    "action": "guided_tour",
                    "expected_outcome": "User is guided through main functionality",
                },
                {
                    "action": "try_examples",
                    "expected_outcome": "User successfully completes examples",
                },
                {
                    "action": "access_help",
                    "expected_outcome": "Help resources are easily accessible",
                },
            ],
            "success_criteria": [
                "User understands main features",
                "Examples work as expected",
                "Help is comprehensive and accessible",
                "Experience is intuitive",
            ],
        }
