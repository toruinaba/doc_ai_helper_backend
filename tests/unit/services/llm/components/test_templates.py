"""
Tests for the template management component.
"""

import pytest
import os
import json
import tempfile
from pathlib import Path

from doc_ai_helper_backend.services.llm.components.templates import (
    PromptTemplateManager,
)
from doc_ai_helper_backend.models.llm import PromptTemplate, TemplateVariable
from doc_ai_helper_backend.core.exceptions import (
    TemplateNotFoundError,
    TemplateSyntaxError,
)


class TestPromptTemplateManager:
    """Tests for the PromptTemplateManager."""

    @pytest.fixture
    def temp_templates_dir(self):
        """Create a temporary directory for templates."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a sample template
            sample_template = {
                "id": "test_template",
                "name": "Test Template",
                "description": "A template for testing",
                "template": "Hello, {{name}}! This is a {{type}} template.",
                "variables": [
                    {"name": "name", "description": "Your name", "required": True},
                    {
                        "name": "type",
                        "description": "Template type",
                        "required": False,
                        "default": "test",
                    },
                ],
            }

            template_path = Path(tmp_dir) / "test_template.json"
            with open(template_path, "w") as f:
                json.dump(sample_template, f)

            yield tmp_dir

    @pytest.fixture
    def template_manager(self, temp_templates_dir):
        """Create a template manager with the temporary directory."""
        return PromptTemplateManager(templates_dir=temp_templates_dir)

    def test_load_templates(self, template_manager):
        """Test loading templates."""
        templates = template_manager.list_templates()
        assert "test_template" in templates

    def test_get_template(self, template_manager):
        """Test getting a template."""
        template = template_manager.get_template("test_template")
        assert isinstance(template, PromptTemplate)
        assert template.id == "test_template"
        assert template.name == "Test Template"
        assert "{{name}}" in template.template

    def test_get_nonexistent_template(self, template_manager):
        """Test getting a non-existent template."""
        with pytest.raises(TemplateNotFoundError):
            template_manager.get_template("nonexistent")

    def test_format_template(self, template_manager):
        """Test formatting a template."""
        formatted = template_manager.format_template("test_template", {"name": "John"})
        assert "Hello, John!" in formatted
        assert "test template" in formatted  # Default value

    def test_format_with_all_variables(self, template_manager):
        """Test formatting with all variables provided."""
        formatted = template_manager.format_template(
            "test_template", {"name": "Jane", "type": "custom"}
        )
        assert "Hello, Jane!" in formatted
        assert "custom template" in formatted

    def test_format_missing_required(self, template_manager):
        """Test formatting with missing required variable."""
        with pytest.raises(TemplateSyntaxError):
            template_manager.format_template("test_template", {})

    def test_save_template(self, template_manager, temp_templates_dir):
        """Test saving a template."""
        new_template = PromptTemplate(
            id="new_template",
            name="New Template",
            description="A new test template",
            template="This is a {{adjective}} new template!",
            variables=[
                TemplateVariable(
                    name="adjective",
                    description="Descriptive adjective",
                    required=True,
                    default="fantastic",
                )
            ],
        )

        template_manager.save_template(new_template)

        # Check file was created
        template_path = Path(temp_templates_dir) / "new_template.json"
        assert template_path.exists()

        # Check template was added to cache
        assert "new_template" in template_manager.list_templates()

        # Check template can be loaded
        loaded = template_manager.get_template("new_template")
        assert loaded.name == "New Template"
