"""
End-to-End tests for Forgejo workflow.

This module contains comprehensive E2E tests that verify the complete workflow:
1. Document retrieval from Forgejo
2. LLM processing with document content
3. MCP tool execution to create issues

These tests require:
- Backend API server running
- Forgejo instance accessible
- Proper environment configuration
"""

import asyncio
import json
import pytest
import logging
from datetime import datetime
from typing import Dict, Any

from .helpers.api_client import BackendAPIClient
from .helpers.forgejo_client import ForgejoVerificationClient
from .helpers.test_data import E2ETestData

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.forgejo
@pytest.mark.asyncio
class TestForgejoE2EWorkflow:
    """
    End-to-end test class for Forgejo workflow.
    """

    async def test_basic_document_retrieval(
        self, backend_api_client: BackendAPIClient, test_config, test_data: E2ETestData
    ):
        """
        Test basic document retrieval from Forgejo via backend API.

        This test verifies that the backend can successfully retrieve
        documents from a Forgejo repository.
        """
        logger.info("Testing basic document retrieval from Forgejo")

        # Test retrieving README.md
        document = await backend_api_client.get_document(
            service="forgejo",
            owner=test_config.owner,
            repo=test_config.repo,
            path="README.md",
        )

        # Verify document structure
        assert document is not None, "Document should not be None"
        assert "content" in document, "Document should have content"
        assert "metadata" in document, "Document should have metadata"
        assert "path" in document, "Document should have path"
        assert document["path"] == "README.md", "Path should match requested path"
        assert document["service"] == "forgejo", "Service should be forgejo"
        assert document["owner"] == test_config.owner, "Owner should match"
        assert document["repository"] == test_config.repo, "Repository should match"

        # Verify content is not empty
        content = document["content"]
        assert "content" in content, "Content should have content field"
        assert len(content["content"]) > 0, "Content should not be empty"

        logger.info(f"Successfully retrieved document: {document['path']}")
        logger.info(f"Content length: {len(content['content'])} characters")

    async def test_repository_structure_retrieval(
        self, backend_api_client: BackendAPIClient, test_config
    ):
        """
        Test repository structure retrieval from Forgejo.
        """
        logger.info("Testing repository structure retrieval")

        structure = await backend_api_client.get_repository_structure(
            service="forgejo", owner=test_config.owner, repo=test_config.repo
        )

        # Verify structure
        assert structure is not None, "Structure should not be None"
        assert "tree" in structure, "Structure should have tree"
        assert isinstance(structure["tree"], list), "Tree should be a list"

        # Check that at least some items exist
        assert len(structure["tree"]) > 0, "Repository should have some items"

        # Separate files and directories
        files = [item for item in structure["tree"] if item.get("type") == "file"]
        directories = [
            item for item in structure["tree"] if item.get("type") == "directory"
        ]

        # Verify we have some files and directories
        assert len(files) > 0, "Repository should have some files"

        logger.info(
            f"Repository structure: {len(files)} files, {len(directories)} directories"
        )

    async def test_llm_document_summarization(
        self, backend_api_client: BackendAPIClient, test_config, test_data: E2ETestData
    ):
        """
        Test LLM document summarization via backend API.

        This test verifies that the LLM can process document content
        and generate appropriate summaries.
        """
        logger.info("Testing LLM document summarization")

        # First, get a document
        document = await backend_api_client.get_document(
            service="forgejo",
            owner=test_config.owner,
            repo=test_config.repo,
            path="README.md",
        )

        # Create summarization prompt
        prompt = test_data.get_test_prompt(
            "document_summary",
            title=document.get("metadata", {}).get("title", "README"),
            path=document["path"],
            content=document["content"]["content"][:1000],  # Limit content length
        )

        # Query LLM for summarization
        response = await backend_api_client.query_llm(
            prompt=prompt,
            provider=test_data.TEST_LLM_PROVIDER,
            tools_enabled=False,  # Disable tools for pure summarization
        )

        # Verify response
        assert response is not None, "LLM response should not be None"
        assert "content" in response, "Response should have content field"
        assert len(response["content"]) > 0, "Response should not be empty"

        # Basic quality checks
        summary = response["content"]
        assert len(summary) > 50, "Summary should be substantial"
        assert len(summary) < 1000, "Summary should be concise"

        logger.info(f"Generated summary ({len(summary)} chars): {summary[:100]}...")

        return summary

    async def test_streaming_llm_response(
        self, backend_api_client: BackendAPIClient, test_config, test_data: E2ETestData
    ):
        """
        Test streaming LLM response functionality.
        """
        logger.info("Testing streaming LLM response")

        # Get a document
        document = await backend_api_client.get_document(
            service="forgejo",
            owner=test_config.owner,
            repo=test_config.repo,
            path="README.md",
        )

        # Create a simple prompt
        prompt = f"以下の内容を簡潔に要約してください：{document['content']['content'][:500]}"

        # Test streaming response
        chunks = []
        async for chunk in backend_api_client.stream_llm_query(
            prompt=prompt, provider=test_data.TEST_LLM_PROVIDER
        ):
            chunks.append(chunk)
            logger.debug(f"Received chunk: {chunk}")

        # Verify streaming worked
        assert len(chunks) > 0, "Should receive at least one chunk"

        full_response = "".join(chunks)
        assert len(full_response) > 0, "Combined response should not be empty"

        logger.info(
            f"Streaming response completed: {len(chunks)} chunks, {len(full_response)} total chars"
        )

    @pytest.mark.mcp
    async def test_llm_with_mcp_issue_creation(
        self,
        backend_api_client: BackendAPIClient,
        forgejo_client: ForgejoVerificationClient,
        test_config,
        test_data: E2ETestData,
        clean_test_issues,
    ):
        """
        Test complete workflow: document retrieval -> LLM processing -> MCP issue creation.

        This is the main E2E test that verifies the entire workflow.
        """
        logger.info("Testing complete workflow with MCP issue creation")

        # Step 1: Retrieve document
        logger.info("Step 1: Retrieving document")
        document = await backend_api_client.get_document(
            service="forgejo",
            owner=test_config.owner,
            repo=test_config.repo,
            path="README.md",
        )

        # Step 2: Generate summary with LLM
        logger.info("Step 2: Generating document summary")
        summary_prompt = test_data.get_test_prompt(
            "document_summary",
            title=document.get("metadata", {}).get("title", "README"),
            path=document["path"],
            content=document["content"]["content"][:1000],
        )

        summary_response = await backend_api_client.query_llm(
            prompt=summary_prompt,
            provider=test_data.TEST_LLM_PROVIDER,
            tools_enabled=False,
        )

        summary = summary_response["content"]
        logger.info(f"Generated summary: {summary[:100]}...")

        # Step 3: Request issue creation with MCP tools
        logger.info("Step 3: Requesting issue creation via MCP")

        test_id = f"e2e-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        issue_prompt = test_data.get_test_prompt(
            "issue_creation_request",
            summary=summary,
            owner=test_config.owner,
            repo=test_config.repo,
            marker=test_data.TEST_ISSUE_MARKER,
        )

        # Enable MCP tools for issue creation
        from doc_ai_helper_backend.models.repository_context import RepositoryContext

        repository_context = RepositoryContext(
            service="forgejo",
            owner=test_config.owner,
            repo=test_config.repo,
            ref="main",
        )

        mcp_response = await backend_api_client.query_llm(
            prompt=issue_prompt,
            context={"document": document, "summary": summary, "test_id": test_id},
            provider=test_data.TEST_LLM_PROVIDER,
            tools_enabled=True,
            repository_context=repository_context.model_dump(),  # RepositoryContextを辞書形式で渡す
        )

        # Verify MCP response
        assert mcp_response is not None, "MCP response should not be None"
        logger.info(f"MCP response: {mcp_response}")

        # Check if issue was actually created by looking at tool execution results
        if "tool_execution_results" in mcp_response:
            tool_results = mcp_response["tool_execution_results"]
            for tool_result in tool_results:
                if tool_result.get("function_name") == "create_git_issue":
                    result = tool_result.get("result", {})
                    if result.get("success"):
                        logger.info("✅ Issue creation successful - parsing result")

                        # Parse the result to get issue information
                        result_data = json.loads(result.get("result", "{}"))
                        if result_data.get("success"):
                            issue_data = result_data.get("data", {})
                            logger.info(
                                f"📝 Created issue #{issue_data.get('issue_number')} - {issue_data.get('title')}"
                            )
                            logger.info(f"🔗 Issue URL: {issue_data.get('issue_url')}")

                            # Verify issue content
                            assert test_data.TEST_ISSUE_MARKER in issue_data.get(
                                "title", ""
                            ), "Issue title should contain test marker"

                            return {
                                "success": True,
                                "issue_number": issue_data.get("issue_number"),
                                "issue_url": issue_data.get("issue_url"),
                                "title": issue_data.get("title"),
                                "state": issue_data.get("state"),
                                "created_at": issue_data.get("created_at"),
                            }
                    else:
                        logger.error(f"❌ Issue creation failed: {result}")
                        assert (
                            False
                        ), f"Issue creation failed: {result.get('result', 'Unknown error')}"

        # Check if function calls were made (fallback for older formats)
        if "function_calls" in mcp_response:
            function_calls = mcp_response["function_calls"]
            logger.info(
                f"Function calls made: {[call.get('name') for call in function_calls]}"
            )

            # Look for issue creation calls
            issue_creation_calls = [
                call
                for call in function_calls
                if call.get("name") in ["create_git_issue"]
            ]

            if issue_creation_calls:
                logger.info(f"Issue creation calls found: {len(issue_creation_calls)}")

                # Step 4: Verify issue was actually created in Forgejo
                logger.info("Step 4: Verifying issue creation in Forgejo")

                # Wait a bit for the issue to be created
                await asyncio.sleep(2)

                # Look for the created issue
                created_issue = await forgejo_client.verify_issue_exists(
                    owner=test_config.owner,
                    repo=test_config.repo,
                    title_pattern=test_data.TEST_ISSUE_MARKER,
                    max_age_seconds=60,  # Look for issues created in the last minute
                )

                if created_issue:
                    logger.info(
                        f"✅ Issue successfully created: #{created_issue['number']} - {created_issue['title']}"
                    )

                    # Verify issue content
                    assert (
                        test_data.TEST_ISSUE_MARKER in created_issue["title"]
                    ), "Issue title should contain test marker"

                    # Additional verification
                    issue_body = created_issue.get("body", "")
                    assert len(issue_body) > 0, "Issue should have content"

                    return created_issue
                else:
                    logger.warning(
                        "⚠️ Issue creation was requested but no matching issue found in Forgejo"
                    )
                    # This might be expected if using mock LLM
                    if test_data.TEST_LLM_PROVIDER == "mock":
                        logger.info(
                            "Using mock LLM - issue creation simulation completed"
                        )
                        return {"mock": True, "status": "simulated"}
            else:
                logger.info("No issue creation function calls found in response")
        else:
            logger.info("No function calls found in MCP response")

        # If we reach here with mock provider, that's expected
        if test_data.TEST_LLM_PROVIDER == "mock":
            logger.info("Mock LLM workflow completed successfully")
            return {"mock": True, "status": "completed"}

        # For real LLM providers, we should have gotten some result
        assert (
            False
        ), "Expected either issue creation or clear explanation of why it didn't happen"

    @pytest.mark.slow
    async def test_multiple_document_analysis(
        self, backend_api_client: BackendAPIClient, test_config, test_data: E2ETestData
    ):
        """
        Test analysis of multiple documents from the repository.

        This test verifies that the system can handle multiple documents
        and provide comprehensive analysis.
        """
        logger.info("Testing multiple document analysis")

        # Get repository structure first
        structure = await backend_api_client.get_repository_structure(
            service="forgejo", owner=test_config.owner, repo=test_config.repo
        )

        # Find markdown files
        markdown_files = [
            f
            for f in structure["tree"]
            if f.get("name", "").endswith((".md", ".markdown"))
            and f.get("type") == "file"
        ][
            :3
        ]  # Limit to first 3 files

        logger.info(f"Found {len(markdown_files)} markdown files to analyze")

        analyses = []
        for file_info in markdown_files:
            file_path = file_info.get("path", file_info.get("name"))
            logger.info(f"Analyzing file: {file_path}")

            try:
                # Get document
                document = await backend_api_client.get_document(
                    service="forgejo",
                    owner=test_config.owner,
                    repo=test_config.repo,
                    path=file_path,
                )

                # Analyze with LLM
                analysis_prompt = test_data.get_test_prompt(
                    "analysis_request",
                    content=document["content"]["content"][:800],  # Limit content
                )

                analysis_response = await backend_api_client.query_llm(
                    prompt=analysis_prompt,
                    provider=test_data.TEST_LLM_PROVIDER,
                    tools_enabled=False,
                )

                analyses.append(
                    {
                        "file": file_path,
                        "analysis": analysis_response["content"],
                        "document": document,
                    }
                )

                logger.info(f"Analysis completed for {file_path}")

            except Exception as e:
                logger.warning(f"Failed to analyze {file_path}: {e}")
                continue

        # Verify we got some analyses
        assert len(analyses) > 0, "Should have analyzed at least one document"

        logger.info(f"Successfully analyzed {len(analyses)} documents")

        # Verify analysis quality
        for analysis in analyses:
            assert (
                len(analysis["analysis"]) > 100
            ), f"Analysis for {analysis['file']} should be substantial"

        return analyses

    async def test_error_handling_invalid_repository(
        self, backend_api_client: BackendAPIClient, test_config
    ):
        """
        Test error handling for invalid repository access.
        """
        logger.info("Testing error handling for invalid repository")

        # Try to access non-existent repository
        with pytest.raises(Exception) as exc_info:
            await backend_api_client.get_document(
                service="forgejo",
                owner=test_config.owner,
                repo="non-existent-repo-12345",
                path="README.md",
            )

        logger.info(f"Expected error occurred: {exc_info.value}")

    async def test_error_handling_invalid_file(
        self, backend_api_client: BackendAPIClient, test_config
    ):
        """
        Test error handling for invalid file access.
        """
        logger.info("Testing error handling for invalid file")

        # Try to access non-existent file
        with pytest.raises(Exception) as exc_info:
            await backend_api_client.get_document(
                service="forgejo",
                owner=test_config.owner,
                repo=test_config.repo,
                path="non-existent-file-12345.md",
            )

        logger.info(f"Expected error occurred: {exc_info.value}")


@pytest.mark.e2e
@pytest.mark.forgejo
@pytest.mark.llm
@pytest.mark.asyncio
class TestForgejoAdvancedWorkflows:
    """
    Advanced E2E workflow tests for complex scenarios.
    """

    async def test_document_comparison_workflow(
        self, backend_api_client: BackendAPIClient, test_config, test_data: E2ETestData
    ):
        """
        Test workflow for comparing multiple documents.
        """
        logger.info("Testing document comparison workflow")

        # Get multiple documents
        documents = []
        for file_path in ["README.md", "docs/guide.md"][:2]:  # Limit to 2 files
            try:
                doc = await backend_api_client.get_document(
                    service="forgejo",
                    owner=test_config.owner,
                    repo=test_config.repo,
                    path=file_path,
                )
                documents.append(doc)
            except Exception as e:
                logger.warning(f"Could not fetch {file_path}: {e}")

        if len(documents) < 2:
            pytest.skip("Need at least 2 documents for comparison test")

        # Create comparison prompt
        comparison_prompt = f"""
以下の2つのドキュメントを比較し、相違点と改善提案を行ってください：

ドキュメント1: {documents[0]['path']}
内容: {documents[0]['content']['raw'][:500]}

ドキュメント2: {documents[1]['path']}
内容: {documents[1]['content']['raw'][:500]}

比較結果として以下を含めてください：
1. 内容の重複度
2. 構造の違い
3. 品質の比較
4. 統合または改善の提案
        """

        # Query LLM for comparison
        response = await backend_api_client.query_llm(
            prompt=comparison_prompt,
            provider=test_data.TEST_LLM_PROVIDER,
            tools_enabled=False,
        )

        # Verify comparison result
        assert response is not None, "Comparison response should not be None"
        comparison_result = response["content"]
        assert len(comparison_result) > 200, "Comparison should be detailed"

        logger.info(
            f"Document comparison completed: {len(comparison_result)} characters"
        )

        return {"documents": documents, "comparison": comparison_result}
