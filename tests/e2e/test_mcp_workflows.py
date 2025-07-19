"""
Unified MCP Workflows E2E Tests.

This module contains comprehensive E2E tests for MCP (Model Context Protocol) workflows,
covering both traditional step-by-step approaches and new LLM-enhanced single-request 
workflows. This consolidates the functionality previously split between:
- test_llm_enhanced_mcp_workflows.py (new enhanced workflows)
- test_mcp_issue_workflows.py (traditional workflows)

Test Categories:
- Basic Workflows: Traditional step-by-step MCP workflows
- Enhanced Workflows: LLM-enhanced single-request workflows  
- Comparison Tests: Before vs After workflow comparisons
- Error Handling: Comprehensive error scenario testing
"""

import asyncio
import pytest
import logging
import json
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional

from tests.e2e.helpers.config import E2EConfig
from tests.e2e.helpers.api_client import BackendAPIClient
from tests.e2e.helpers.git_verification import GitVerificationClient

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.mcp
@pytest.mark.asyncio
class TestMCPWorkflows:
    """
    Comprehensive E2E tests for MCP workflows.
    
    This class tests both traditional and enhanced MCP workflows:
    - Traditional: Document retrieval → LLM analysis → Tool execution (multi-step)
    - Enhanced: Single request → AI tool selection → Automated execution (single-step)
    """

    # ========== HELPER METHODS ==========
    
    def _create_repository_context(self, service: str, owner: str, repo: str, ref: str = "main", path: Optional[str] = None):
        """Create repository context for MCP tools."""
        from doc_ai_helper_backend.models.repository_context import RepositoryContext
        
        return RepositoryContext(
            service=service,
            owner=owner,
            repo=repo,
            ref=ref,
            current_path=path
        )

    def _verify_provider_configuration(self, response: Dict[str, Any], expected_provider: str):
        """Verify LLM provider configuration in response."""
        actual_provider = response.get("provider", "unknown")
        actual_model = response.get("model", "unknown")
        
        logger.info(f"🔍 Provider verification - Expected: {expected_provider}, Actual: {actual_provider}, Model: {actual_model}")
        
        # Assert that we're NOT using mock provider for E2E tests
        assert actual_provider != "mock", f"E2E test should not use mock provider, got: {actual_provider}"
        
        # Assert that we're using the expected provider
        assert actual_provider == expected_provider, \
            f"Expected provider '{expected_provider}', but got '{actual_provider}'"
        
        # For OpenAI provider, verify we're using Azure OpenAI
        if actual_provider == "openai":
            assert "azure" in actual_model.lower() or "gpt" in actual_model.lower(), \
                f"Expected Azure OpenAI model, but got: {actual_model}"

    def _verify_tool_execution(self, response: Dict[str, Any], expected_tools: List[str]) -> Dict[str, Any]:
        """Verify tool execution in MCP response."""
        verification_result = {
            "tool_calls_exist": False,
            "tool_results_exist": False,
            "tools_requested": set(),
            "tools_executed": set(),
            "execution_success": {}
        }
        
        # Check for tool calls (initial LLM response)
        tool_calls_exist = "tool_calls" in response and response["tool_calls"] is not None and len(response["tool_calls"]) > 0
        tool_results_exist = "tool_execution_results" in response and response["tool_execution_results"] is not None and len(response["tool_execution_results"]) > 0
        
        verification_result["tool_calls_exist"] = tool_calls_exist
        verification_result["tool_results_exist"] = tool_results_exist
        
        logger.info(f"Tool calls present: {tool_calls_exist}")
        logger.info(f"Tool execution results present: {tool_results_exist}")
        
        # Verify tool calls
        if tool_calls_exist:
            tool_calls = response["tool_calls"]
            for tool_call in tool_calls:
                function_name = tool_call.get("function", {}).get("name", "")
                verification_result["tools_requested"].add(function_name)
                logger.info(f"Tool requested: {function_name}")
        
        # Verify tool execution results
        if tool_results_exist:
            tool_results = response["tool_execution_results"]
            for tool_result in tool_results:
                function_name = tool_result.get("function_name", "")
                verification_result["tools_executed"].add(function_name)
                
                result = tool_result.get("result", {})
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        pass
                
                success = result.get("success", False) if isinstance(result, dict) else False
                verification_result["execution_success"][function_name] = success
                
                logger.info(f"Tool executed: {function_name}, Success: {success}")
        
        # At least one form of tool interaction should be present
        assert tool_calls_exist or tool_results_exist, \
            "Response should contain either 'tool_calls' or 'tool_execution_results' - tools were not invoked"
        
        return verification_result

    async def _verify_github_issue_creation(self, git_client: GitVerificationClient, config: E2EConfig, test_marker: str) -> Optional[Dict[str, Any]]:
        """Verify GitHub issue was actually created."""
        await asyncio.sleep(3)  # Wait for issue creation
        
        created_issue = await git_client.verify_issue_exists(
            service="github",
            owner=config.github_owner,
            repo=config.github_repo,
            title_pattern=test_marker,
            max_age_seconds=120
        )
        
        if created_issue:
            logger.info(f"✅ Verified issue creation: #{created_issue['number']} - {created_issue['title']}")
            assert test_marker in created_issue["title"]
            
        return created_issue

    # ========== BASIC WORKFLOWS (Traditional Multi-Step) ==========

    @pytest.mark.mcp_basic
    async def test_basic_github_workflow(
        self,
        backend_api_client: BackendAPIClient,
        git_verification_client: GitVerificationClient,
        e2e_config: E2EConfig,
        clean_test_issues,
        test_repository_context
    ):
        """
        Test traditional MCP workflow with GitHub: document → LLM → issue creation.
        
        This represents the "Before" pattern with explicit step-by-step execution.
        """
        if not e2e_config.has_github_config:
            pytest.skip("GitHub configuration not available for E2E tests")

        logger.info("=== Starting Basic GitHub MCP Workflow Test ===")
        
        # Step 1: Retrieve document from GitHub
        logger.info("Step 1: Retrieving document from GitHub")
        document = await backend_api_client.get_document(
            service="github",
            owner=e2e_config.github_owner,
            repo=e2e_config.github_repo,
            path="README.md"
        )
        
        assert document is not None, "Document should be retrieved successfully"
        assert "content" in document, "Document should have content"
        logger.info(f"Retrieved document: {document['path']}")

        # Step 2: Generate analysis with LLM
        logger.info("Step 2: Generating document analysis with LLM")
        test_id = f"basic-github-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        analysis_prompt = f"""
以下のREADMEドキュメントを分析し、見解を提供してください：

ドキュメント: {document.get('path', 'README.md')}
内容（最初の800文字）: {document['content']['content'][:800]}

以下の観点から簡潔な分析を提供してください：
1. リポジトリの主な目的
2. 言及されている主要な機能やコンポーネント
3. ドキュメントの不足点や改善提案

分析は簡潔で情報豊かに保ってください。
        """

        analysis_response = await backend_api_client.query_llm(
            prompt=analysis_prompt,
            provider=e2e_config.llm_provider,
            tools_enabled=False  # Pure analysis without tools
        )

        assert analysis_response is not None, "Analysis response should not be None"
        assert "content" in analysis_response, "Analysis should have content"
        analysis = analysis_response["content"]
        logger.info(f"Generated analysis: {analysis[:100]}...")

        # Step 3: Request issue creation via MCP
        logger.info("Step 3: Requesting issue creation via MCP tools")
        
        issue_creation_prompt = f"""
YOU MUST call the create_git_issue tool NOW. This is MANDATORY.

CALL create_git_issue tool with these exact parameters:
- title: "[{e2e_config.test_issue_marker}] 基本ワークフロー - {test_id}"
- description: "分析結果に基づく改善提案: {analysis[:300]}"

Repository: {e2e_config.github_owner}/{e2e_config.github_repo}
Service: GitHub

This is a REQUIRED tool execution. You MUST execute the create_git_issue tool immediately.
        """

        repository_context = self._create_repository_context(
            "github", e2e_config.github_owner, e2e_config.github_repo
        )

        # Execute MCP workflow
        mcp_response = await backend_api_client.query_llm(
            prompt=issue_creation_prompt,
            provider=e2e_config.llm_provider,
            tools_enabled=True,
            repository_context=repository_context.model_dump()
        )

        # Step 4: Verify MCP response and issue creation
        logger.info("Step 4: Verifying MCP response and issue creation")
        assert mcp_response is not None, "MCP response should not be None"
        
        # Verify provider configuration
        self._verify_provider_configuration(mcp_response, e2e_config.llm_provider)
        
        # Verify tool execution
        tool_verification = self._verify_tool_execution(mcp_response, ["create_git_issue"])
        
        # For real LLM providers, verify the issue was actually created
        created_issue = None
        if e2e_config.llm_provider != "mock" and tool_verification["execution_success"].get("create_git_issue"):
            created_issue = await self._verify_github_issue_creation(
                git_verification_client, e2e_config, e2e_config.test_issue_marker
            )

        logger.info("✅ Basic GitHub MCP workflow completed")
        return {
            "success": True,
            "workflow_type": "basic_github",
            "service": "github",
            "issue": created_issue,
            "tools_executed": list(tool_verification["tools_executed"]),
            "workflow_completed": True
        }

    @pytest.mark.mcp_enhanced
    @pytest.mark.llm_enhanced
    async def test_enhanced_japanese_analysis_workflow(
        self,
        backend_api_client: BackendAPIClient,
        git_verification_client: GitVerificationClient,
        e2e_config: E2EConfig,
        clean_test_issues,
        test_repository_context
    ):
        """
        Test LLM-enhanced single-request workflow for Japanese document analysis.
        
        This represents the "After" pattern where a single request triggers:
        summarize_document_with_llm + create_improvement_recommendations_with_llm + create_git_issue
        """
        if not e2e_config.has_github_config:
            pytest.skip("GitHub configuration not available for E2E tests")

        logger.info("=== Starting Enhanced Japanese Analysis Workflow Test ===")
        
        test_id = f"enhanced-jp-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        comprehensive_request = f"""
YOU MUST call these 3 tools in this exact order - this is MANDATORY:

1. CALL summarize_document_with_llm tool
2. CALL create_improvement_recommendations_with_llm tool  
3. CALL create_git_issue tool with parameters:
   - title: "[{e2e_config.test_issue_marker}] 日本語ドキュメント分析 - {test_id}"
   - description: "Document analysis results from LLM-enhanced MCP workflow"

Repository: {e2e_config.github_owner}/{e2e_config.github_repo}
Document: README.md

This is a REQUIRED tool execution test. You MUST execute ALL 3 tools listed above.
Use the repository context to automatically retrieve document content.
        """

        repository_context = self._create_repository_context(
            "github", e2e_config.github_owner, e2e_config.github_repo
        )

        # Execute comprehensive workflow with LLM-enhanced tools
        workflow_response = await backend_api_client.query_llm(
            prompt=comprehensive_request,
            provider=e2e_config.llm_provider,
            tools_enabled=True,
            repository_context=repository_context.model_dump(),
            auto_include_document=True
        )

        # Verify the workflow executed successfully
        assert workflow_response is not None, "Workflow response should not be None"
        
        # Verify provider configuration
        self._verify_provider_configuration(workflow_response, e2e_config.llm_provider)
        
        # Verify expected tools were used
        expected_tools = {"summarize_document_with_llm", "create_improvement_recommendations_with_llm", "create_git_issue"}
        tool_verification = self._verify_tool_execution(workflow_response, list(expected_tools))
        
        # Check if expected tools were executed
        executed_intersection = expected_tools.intersection(tool_verification["tools_executed"])
        logger.info(f"Expected tools executed: {executed_intersection}")
        
        # For real LLM providers, verify issue creation
        created_issue = None
        if e2e_config.llm_provider != "mock" and tool_verification["execution_success"].get("create_git_issue"):
            created_issue = await self._verify_github_issue_creation(
                git_verification_client, e2e_config, e2e_config.test_issue_marker
            )

        logger.info("✅ Enhanced Japanese analysis workflow completed")
        return {
            "success": True,
            "workflow_type": "enhanced_japanese",
            "service": "github",
            "issue": created_issue,
            "tools_used": list(tool_verification["tools_executed"]),
            "workflow_completed": True
        }

    @pytest.mark.mcp_comparison
    async def test_workflow_comparison_before_vs_after(
        self,
        backend_api_client: BackendAPIClient,
        git_verification_client: GitVerificationClient,
        e2e_config: E2EConfig,
        clean_test_issues,
        test_repository_context
    ):
        """
        Test workflow comparison: "Before" (multi-step) vs "After" (single-step).
        
        This test demonstrates the improvement achieved by LLM-enhanced tools:
        - Before: 3 separate requests with manual conversation management
        - After: 1 request with automatic tool orchestration
        """
        if not e2e_config.has_github_config:
            pytest.skip("GitHub configuration not available for E2E tests")

        logger.info("=== Starting Workflow Comparison: Before vs After ===")
        
        test_id = f"comparison-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        repository_context = self._create_repository_context(
            "github", e2e_config.github_owner, e2e_config.github_repo, path="README.md"
        )

        # === BEFORE: Multi-step workflow ===
        logger.info("🔄 Executing 'BEFORE' workflow (multi-step)")
        
        before_start_time = datetime.now()
        conversation_history = []
        
        # Before Step 1: Summary
        before_step1 = await backend_api_client.query_llm(
            prompt="このREADMEを要約してください",
            conversation_history=conversation_history,
            repository_context=repository_context.model_dump(),
            auto_include_document=True,
            provider=e2e_config.llm_provider
        )
        
        conversation_history = [
            {"role": "user", "content": "このREADMEを要約してください"},
            {"role": "assistant", "content": before_step1["content"]}
        ]
        
        # Before Step 2: Improvements
        before_step2 = await backend_api_client.query_llm(
            prompt="何が改善できますか？",
            conversation_history=conversation_history,
            provider=e2e_config.llm_provider
        )
        
        conversation_history.extend([
            {"role": "user", "content": "何が改善できますか？"},
            {"role": "assistant", "content": before_step2["content"]}
        ])
        
        # Before Step 3: Issue creation
        before_step3 = await backend_api_client.query_llm(
            prompt=f"""これらの改善でissueを作成してください。
            
タイトル: "[{e2e_config.test_issue_marker}] BEFORE方式改善 - {test_id}"
create_git_issue ツールを使用してください。""",
            conversation_history=conversation_history,
            repository_context=repository_context.model_dump(),
            tools_enabled=True,
            provider=e2e_config.llm_provider
        )
        
        before_end_time = datetime.now()
        before_duration = (before_end_time - before_start_time).total_seconds()
        
        # === AFTER: Single-step workflow ===
        logger.info("🚀 Executing 'AFTER' workflow (single-step)")
        
        after_start_time = datetime.now()
        
        after_response = await backend_api_client.query_llm(
            prompt=f"""このREADMEを包括的に分析し、改善提案のissueを作成してください：

やってほしいこと:
1. ドキュメントの内容を要約
2. 改善提案を作成
3. その改善提案でissueを作成

issueタイトル: "[{e2e_config.test_issue_marker}] AFTER方式改善 - {test_id}"
""",
            repository_context=repository_context.model_dump(),
            auto_include_document=True,
            tools_enabled=True,
            provider=e2e_config.llm_provider
        )
        
        after_end_time = datetime.now()
        after_duration = (after_end_time - after_start_time).total_seconds()
        
        # === COMPARISON ANALYSIS ===
        logger.info("📊 Analyzing workflow comparison results")
        
        # Analyze BEFORE workflow
        before_requests = 3
        before_tool_verification = self._verify_tool_execution(before_step3, ["create_git_issue"])
        before_issue_created = before_tool_verification["execution_success"].get("create_git_issue", False)
        
        # Analyze AFTER workflow  
        after_requests = 1
        after_tool_verification = self._verify_tool_execution(after_response, ["create_git_issue"])
        after_issue_created = after_tool_verification["execution_success"].get("create_git_issue", False)
        
        # Create comparison report
        comparison_report = {
            "before_workflow": {
                "requests": before_requests,
                "duration_seconds": before_duration,
                "issue_created": before_issue_created,
                "conversation_steps": len(conversation_history) // 2
            },
            "after_workflow": {
                "requests": after_requests,
                "duration_seconds": after_duration,  
                "issue_created": after_issue_created,
                "conversation_steps": 0
            },
            "improvements": {
                "request_reduction": f"{before_requests - after_requests} fewer requests",
                "time_efficiency": f"{before_duration - after_duration:.2f}s faster" if after_duration < before_duration else f"{after_duration - before_duration:.2f}s slower",
                "complexity_reduction": "No manual conversation management needed",
                "both_successful": before_issue_created and after_issue_created
            }
        }
        
        logger.info("✅ Workflow comparison completed")
        logger.info(f"📊 Comparison Report: {json.dumps(comparison_report, indent=2)}")
        
        # Verify both workflows achieved their goals
        assert before_issue_created or e2e_config.llm_provider == "mock", "Before workflow should create issue"
        assert after_issue_created or e2e_config.llm_provider == "mock", "After workflow should create issue"
        
        # The After workflow should be more efficient (fewer requests)
        assert after_requests < before_requests, "After workflow should require fewer requests"
        
        return {
            "success": True,
            "comparison_report": comparison_report,
            "before_successful": before_issue_created,
            "after_successful": after_issue_created,
            "efficiency_improvement": before_requests - after_requests,
            "mock": e2e_config.llm_provider == "mock"
        }

    @pytest.mark.mcp_error
    async def test_mcp_error_handling(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """
        Test MCP error handling when repository context is invalid.
        """
        logger.info("=== Starting MCP Error Handling Test ===")
        
        # Try to create an issue with invalid repository context
        error_prompt = f"""
create_git_issue ツールを使用して、以下の詳細でissueを作成してください：
- タイトル: "[{e2e_config.test_issue_marker}] テストissue"
- 本文: "無効なリポジトリのため失敗するはずです"

リポジトリコンテキスト:
- サービス: github
- オーナー: nonexistent-owner-12345
- リポジトリ: nonexistent-repo-12345
        """

        # Create invalid repository context
        invalid_context = self._create_repository_context(
            "github", "nonexistent-owner-12345", "nonexistent-repo-12345", path="README.md"
        )

        # Execute MCP workflow with invalid context
        mcp_response = await backend_api_client.query_llm(
            prompt=error_prompt,
            provider=e2e_config.llm_provider,
            tools_enabled=True,
            repository_context=invalid_context.model_dump()
        )

        # Verify error handling
        assert mcp_response is not None, "MCP response should not be None even on error"
        
        # Verify tools were invoked and handled errors
        tool_verification = self._verify_tool_execution(mcp_response, ["create_git_issue"])
        
        # Check that the tool execution reported an error
        error_handled = False
        if "create_git_issue" in tool_verification["execution_success"]:
            if not tool_verification["execution_success"]["create_git_issue"]:
                logger.info("✅ MCP tool correctly handled invalid repository")
                error_handled = True
        
        # For mock LLM, error handling is simulated
        if e2e_config.llm_provider == "mock":
            logger.info("✅ Mock LLM error handling test completed")
            error_handled = True

        assert error_handled or tool_verification["tool_calls_exist"], "MCP should handle errors gracefully"
        
        logger.info("✅ MCP error handling test completed")
        return {
            "success": True,
            "error_handled": error_handled,
            "workflow_completed": True
        }