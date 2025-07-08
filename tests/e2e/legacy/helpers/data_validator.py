"""
Data validation utilities for E2E tests.

This module provides tools to validate test data, API responses,
and document content in user story-based E2E tests.
"""

import json
import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from pathlib import Path

import jsonschema
from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation operation."""

    is_valid: bool
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class DataValidator:
    """Validator for test data and API responses."""

    def __init__(self, schemas_path: Optional[Path] = None):
        self.schemas_path = schemas_path
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.custom_validators: Dict[str, Callable] = {}
        self._load_schemas()
        self._register_default_validators()

    def _load_schemas(self) -> None:
        """Load JSON schemas from files."""
        if not self.schemas_path or not self.schemas_path.exists():
            logger.info("No schemas path provided or path doesn't exist")
            return

        try:
            for schema_file in self.schemas_path.glob("*.json"):
                schema_name = schema_file.stem
                with open(schema_file, "r", encoding="utf-8") as f:
                    self.schemas[schema_name] = json.load(f)

            logger.info(f"Loaded {len(self.schemas)} validation schemas")

        except Exception as e:
            logger.error(f"Failed to load schemas: {e}")

    def _register_default_validators(self) -> None:
        """Register default custom validators."""
        self.custom_validators.update(
            {
                "document_content": self._validate_document_content,
                "api_response": self._validate_api_response,
                "markdown_format": self._validate_markdown_format,
                "frontmatter": self._validate_frontmatter,
                "link_structure": self._validate_link_structure,
                "llm_response": self._validate_llm_response,
            }
        )

    def validate_json_schema(
        self,
        data: Any,
        schema_name: str,
    ) -> ValidationResult:
        """
        Validate data against a JSON schema.

        Args:
            data: Data to validate
            schema_name: Name of the schema to use

        Returns:
            ValidationResult with validation outcome
        """
        if schema_name not in self.schemas:
            return ValidationResult(
                is_valid=False,
                errors=[f"Schema '{schema_name}' not found"],
                warnings=[],
                metadata={"schema_name": schema_name},
            )

        try:
            validate(instance=data, schema=self.schemas[schema_name])
            return ValidationResult(
                is_valid=True,
                errors=[],
                warnings=[],
                metadata={"schema_name": schema_name},
            )

        except ValidationError as e:
            return ValidationResult(
                is_valid=False,
                errors=[str(e)],
                warnings=[],
                metadata={
                    "schema_name": schema_name,
                    "validation_path": list(e.path),
                    "failed_value": e.instance,
                },
            )

    def validate_custom(
        self,
        data: Any,
        validator_name: str,
        **kwargs,
    ) -> ValidationResult:
        """
        Validate data using a custom validator.

        Args:
            data: Data to validate
            validator_name: Name of the custom validator
            **kwargs: Additional arguments for the validator

        Returns:
            ValidationResult with validation outcome
        """
        if validator_name not in self.custom_validators:
            return ValidationResult(
                is_valid=False,
                errors=[f"Custom validator '{validator_name}' not found"],
                warnings=[],
                metadata={"validator_name": validator_name},
            )

        try:
            return self.custom_validators[validator_name](data, **kwargs)

        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=[],
                metadata={"validator_name": validator_name, "exception": str(e)},
            )

    def _validate_document_content(
        self,
        document: Dict[str, Any],
        **kwargs,
    ) -> ValidationResult:
        """Validate document content structure."""
        errors = []
        warnings = []

        # Required fields
        required_fields = ["path", "name", "type", "content", "metadata"]
        for field in required_fields:
            if field not in document:
                errors.append(f"Missing required field: {field}")

        # Content validation
        if "content" in document:
            content = document["content"]
            if isinstance(content, dict):
                if "raw" not in content:
                    errors.append("Document content missing 'raw' field")

                # Check content length
                raw_content = content.get("raw", "")
                if len(raw_content) == 0:
                    warnings.append("Document content is empty")
                elif len(raw_content) > 1_000_000:  # 1MB
                    warnings.append("Document content is very large (>1MB)")

        # Metadata validation
        if "metadata" in document:
            metadata = document["metadata"]
            if not isinstance(metadata, dict):
                errors.append("Document metadata must be a dictionary")
            else:
                # Check for common metadata fields
                expected_metadata = ["filename", "extension", "size"]
                missing_metadata = [f for f in expected_metadata if f not in metadata]
                if missing_metadata:
                    warnings.append(
                        f"Missing common metadata fields: {missing_metadata}"
                    )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={"document_path": document.get("path", "unknown")},
        )

    def _validate_api_response(
        self,
        response: Dict[str, Any],
        expected_status: int = 200,
        **kwargs,
    ) -> ValidationResult:
        """Validate API response structure."""
        errors = []
        warnings = []

        # Check status code if provided
        if "status_code" in response:
            status_code = response["status_code"]
            if status_code != expected_status:
                if status_code >= 400:
                    errors.append(f"API error: status {status_code}")
                else:
                    warnings.append(
                        f"Unexpected status code: {status_code} (expected {expected_status})"
                    )

        # Check response time
        if "response_time" in response:
            response_time = response["response_time"]
            if response_time > 5.0:  # 5 seconds
                warnings.append(f"Slow response time: {response_time:.2f}s")

        # Check for error fields
        if "error" in response or "errors" in response:
            error_msg = response.get("error", response.get("errors", "Unknown error"))
            errors.append(f"API returned error: {error_msg}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={
                "status_code": response.get("status_code"),
                "response_time": response.get("response_time"),
            },
        )

    def _validate_markdown_format(
        self,
        content: str,
        **kwargs,
    ) -> ValidationResult:
        """Validate Markdown format and structure."""
        errors = []
        warnings = []

        if not isinstance(content, str):
            errors.append("Markdown content must be a string")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata={},
            )

        # Check for common Markdown patterns
        lines = content.split("\n")

        # Check for headers
        headers = [line for line in lines if line.strip().startswith("#")]
        if not headers:
            warnings.append("No Markdown headers found")

        # Check for proper header hierarchy
        header_levels = []
        for line in lines:
            if line.strip().startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                header_levels.append(level)

        if header_levels:
            # Check if first header is H1
            if header_levels[0] != 1:
                warnings.append("First header is not H1")

            # Check for proper nesting
            for i in range(1, len(header_levels)):
                if header_levels[i] > header_levels[i - 1] + 1:
                    warnings.append(
                        f"Header level jumps from H{header_levels[i-1]} to H{header_levels[i]}"
                    )

        # Check for links
        link_pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        links = re.findall(link_pattern, content)
        if links:
            # Validate link URLs
            for link_text, link_url in links:
                if not link_url.strip():
                    errors.append(f"Empty link URL for text: {link_text}")
                elif link_url.startswith("http"):
                    # External link - basic validation
                    if not re.match(r"https?://[^\s]+", link_url):
                        warnings.append(
                            f"Potentially invalid external link: {link_url}"
                        )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={
                "header_count": len(headers),
                "link_count": len(links),
                "line_count": len(lines),
                "character_count": len(content),
            },
        )

    def _validate_frontmatter(
        self,
        frontmatter: Dict[str, Any],
        **kwargs,
    ) -> ValidationResult:
        """Validate frontmatter structure."""
        errors = []
        warnings = []

        if not isinstance(frontmatter, dict):
            errors.append("Frontmatter must be a dictionary")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata={},
            )

        # Check for common frontmatter fields
        common_fields = ["title", "description", "author", "date"]
        present_fields = [f for f in common_fields if f in frontmatter]

        if not present_fields:
            warnings.append("No common frontmatter fields found")

        # Validate specific fields
        if "title" in frontmatter:
            title = frontmatter["title"]
            if not isinstance(title, str) or not title.strip():
                errors.append("Title must be a non-empty string")

        if "date" in frontmatter:
            date = frontmatter["date"]
            if isinstance(date, str):
                # Try to parse as ISO date
                try:
                    datetime.fromisoformat(date.replace("Z", "+00:00"))
                except ValueError:
                    warnings.append(f"Date format may not be standard: {date}")

        if "tags" in frontmatter:
            tags = frontmatter["tags"]
            if not isinstance(tags, list):
                warnings.append("Tags should be a list")
            elif not all(isinstance(tag, str) for tag in tags):
                warnings.append("All tags should be strings")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={
                "field_count": len(frontmatter),
                "present_common_fields": present_fields,
            },
        )

    def _validate_link_structure(
        self,
        links: List[Dict[str, Any]],
        **kwargs,
    ) -> ValidationResult:
        """Validate link structure."""
        errors = []
        warnings = []

        if not isinstance(links, list):
            errors.append("Links must be a list")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                metadata={},
            )

        required_link_fields = ["text", "url", "is_image", "is_external"]

        for i, link in enumerate(links):
            if not isinstance(link, dict):
                errors.append(f"Link {i} must be a dictionary")
                continue

            # Check required fields
            for field in required_link_fields:
                if field not in link:
                    errors.append(f"Link {i} missing required field: {field}")

            # Validate URL
            if "url" in link:
                url = link["url"]
                if not isinstance(url, str) or not url.strip():
                    errors.append(f"Link {i} has invalid URL")
                elif url.startswith("http"):
                    # Basic URL validation
                    if not re.match(r"https?://[^\s]+", url):
                        warnings.append(f"Link {i} may have invalid URL format: {url}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={
                "link_count": len(links),
                "external_links": len(
                    [l for l in links if l.get("is_external", False)]
                ),
                "image_links": len([l for l in links if l.get("is_image", False)]),
            },
        )

    def _validate_llm_response(
        self,
        response: Dict[str, Any],
        **kwargs,
    ) -> ValidationResult:
        """Validate LLM response structure."""
        errors = []
        warnings = []

        # Check for required fields
        if "content" not in response:
            errors.append("LLM response missing 'content' field")

        if "usage" in response:
            usage = response["usage"]
            if not isinstance(usage, dict):
                errors.append("Usage field must be a dictionary")
            else:
                # Check token usage
                total_tokens = usage.get("total_tokens", 0)
                if total_tokens > 8000:  # High token usage
                    warnings.append(f"High token usage: {total_tokens}")

        # Check response quality indicators
        if "content" in response:
            content = response["content"]
            if isinstance(content, str):
                if len(content.strip()) == 0:
                    errors.append("LLM response content is empty")
                elif len(content) < 10:
                    warnings.append("LLM response content is very short")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            metadata={
                "content_length": len(response.get("content", "")),
                "has_usage": "usage" in response,
            },
        )

    def register_custom_validator(
        self,
        name: str,
        validator_func: Callable,
    ) -> None:
        """Register a custom validator function."""
        self.custom_validators[name] = validator_func
        logger.info(f"Registered custom validator: {name}")

    def validate_multiple(
        self,
        validations: List[Dict[str, Any]],
    ) -> List[ValidationResult]:
        """
        Run multiple validations.

        Args:
            validations: List of validation configs, each containing:
                - type: "schema" or "custom"
                - data: Data to validate
                - validator: Schema name or custom validator name
                - kwargs: Additional arguments (optional)

        Returns:
            List of ValidationResult objects
        """
        results = []

        for validation in validations:
            validation_type = validation.get("type")
            data = validation.get("data")
            validator = validation.get("validator")
            kwargs = validation.get("kwargs", {})

            if validation_type == "schema":
                result = self.validate_json_schema(data, validator)
            elif validation_type == "custom":
                result = self.validate_custom(data, validator, **kwargs)
            else:
                result = ValidationResult(
                    is_valid=False,
                    errors=[f"Unknown validation type: {validation_type}"],
                    warnings=[],
                    metadata={"validation_config": validation},
                )

            results.append(result)

        return results

    def get_validation_summary(
        self,
        results: List[ValidationResult],
    ) -> Dict[str, Any]:
        """Get a summary of validation results."""
        total_validations = len(results)
        passed_validations = len([r for r in results if r.is_valid])
        failed_validations = total_validations - passed_validations

        all_errors = []
        all_warnings = []

        for result in results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)

        return {
            "total_validations": total_validations,
            "passed_validations": passed_validations,
            "failed_validations": failed_validations,
            "success_rate": (
                passed_validations / total_validations if total_validations > 0 else 0
            ),
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
            "errors": all_errors,
            "warnings": all_warnings,
        }
