"""
Prompt template utilities.

This module provides utilities for managing and formatting prompt templates.
"""

import os
import json
from typing import Dict, Any, List, Optional
import re
from pathlib import Path

from doc_ai_helper_backend.models.llm import PromptTemplate, TemplateVariable
from doc_ai_helper_backend.core.exceptions import (
    TemplateNotFoundError,
    TemplateSyntaxError,
)


class PromptTemplateManager:
    """
    Manager for prompt templates.

    This class handles loading, storing, and formatting prompt templates.
    """

    def __init__(self, templates_dir: Optional[str] = None):
        """
        Initialize the template manager.

        Args:
            templates_dir: Directory containing template files (default: 'templates' in the current module directory)
        """
        if templates_dir is None:
            # Default to a 'templates' directory in the same directory as this file
            self.templates_dir = os.path.join(os.path.dirname(__file__), "templates")
        else:
            self.templates_dir = templates_dir

        # Create templates directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)

        # Cache for loaded templates
        self._templates: Dict[str, PromptTemplate] = {}

        # Load templates
        self._load_templates()

    def _load_templates(self) -> None:
        """
        Load templates from the templates directory.
        """
        if not os.path.exists(self.templates_dir):
            return

        for file_path in Path(self.templates_dir).glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    template_data = json.load(f)

                # Convert to PromptTemplate model
                template = PromptTemplate(
                    id=template_data.get("id", file_path.stem),
                    name=template_data.get("name", file_path.stem),
                    description=template_data.get("description", ""),
                    template=template_data.get("template", ""),
                    variables=(
                        [
                            TemplateVariable(**var)
                            for var in template_data.get("variables", [])
                        ]
                        if "variables" in template_data
                        else []
                    ),
                )

                self._templates[template.id] = template

            except Exception as e:
                # Log error but continue loading other templates
                print(f"Error loading template {file_path}: {str(e)}")

    def get_template(self, template_id: str) -> PromptTemplate:
        """
        Get a template by ID.

        Args:
            template_id: The ID of the template

        Returns:
            PromptTemplate: The requested template

        Raises:
            TemplateNotFoundError: If the template is not found
        """
        if template_id not in self._templates:
            raise TemplateNotFoundError(f"Template '{template_id}' not found")

        return self._templates[template_id]

    def list_templates(self) -> List[str]:
        """
        Get a list of available template IDs.

        Returns:
            List[str]: List of template IDs
        """
        return list(self._templates.keys())

    def format_template(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Format a template with the provided variables.

        Args:
            template_id: The ID of the template
            variables: The variables to substitute in the template

        Returns:
            str: The formatted prompt

        Raises:
            TemplateNotFoundError: If the template is not found
            TemplateSyntaxError: If there's an error formatting the template
        """
        template = self.get_template(template_id)

        # Check required variables
        for var in template.variables:
            if var.required and var.name not in variables and var.default is None:
                raise TemplateSyntaxError(
                    f"Required variable '{var.name}' not provided"
                )

        # Apply default values for missing variables
        for var in template.variables:
            if var.name not in variables and var.default is not None:
                variables[var.name] = var.default

        # Format the template
        formatted = template.template

        # Replace {{variable}} placeholders
        var_pattern = r"{{([^{}]+)}}"

        def replace_var(match):
            var_name = match.group(1).strip()
            if var_name not in variables:
                raise TemplateSyntaxError(
                    f"Variable '{var_name}' used in template but not provided"
                )
            return str(variables[var_name])

        try:
            formatted = re.sub(var_pattern, replace_var, formatted)
            return formatted
        except Exception as e:
            raise TemplateSyntaxError(f"Error formatting template: {str(e)}")

    def save_template(self, template: PromptTemplate) -> None:
        """
        Save a template to the templates directory.

        Args:
            template: The template to save
        """
        file_path = os.path.join(self.templates_dir, f"{template.id}.json")

        # Convert to dictionary
        template_dict = template.model_dump()

        # Save to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(template_dict, f, indent=2)

        # Update cache
        self._templates[template.id] = template
