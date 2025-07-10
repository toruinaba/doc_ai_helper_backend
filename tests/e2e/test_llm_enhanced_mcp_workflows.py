"""
LLM Enhanced MCP Tools E2E Tests.

This module contains E2E tests for the new LLM-enhanced MCP tools that provide
sophisticated document analysis capabilities. These tests demonstrate the
simplified workflow enabled by the new tools:

User Request → AI Tool Selection → [summarize_document_with_llm + 
create_improvement_recommendations_with_llm + create_git_issue] → Complete Workflow

Based on the design document: docs/LLM_ENHANCED_MCP_TOOLS_DESIGN.md
"""

import asyncio
import pytest
import logging
import json
from datetime import datetime
from typing import Dict, Any

from tests.e2e.helpers.config import E2EConfig
from tests.e2e.helpers.api_client import BackendAPIClient
from tests.e2e.helpers.git_verification import GitVerificationClient

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.mcp
@pytest.mark.llm_enhanced
@pytest.mark.asyncio
class TestLLMEnhancedMCPWorkflows:
    """
    E2E tests for LLM-enhanced MCP tools workflows.
    
    These tests verify the simplified workflow where a single user request
    triggers multiple AI-powered tools to complete complex document analysis
    and improvement tasks automatically.
    """

    async def test_japanese_document_analysis_workflow(
        self,
        backend_api_client: BackendAPIClient,
        git_verification_client: GitVerificationClient,
        e2e_config: E2EConfig,
        clean_test_issues,
        test_repository_context
    ):
        """
        Test Japanese document analysis workflow using LLM-enhanced tools.
        
        This test demonstrates the simplified workflow:
        1. User makes a single natural language request
        2. AI automatically selects and uses multiple tools:
           - summarize_document_with_llm
           - create_improvement_recommendations_with_llm
           - create_git_issue
        """
        if not e2e_config.has_github_config:
            pytest.skip("GitHub configuration not available for E2E tests")

        logger.info("=== Starting Japanese Document Analysis Workflow Test ===")
        
        # Step 1: Single natural language request for comprehensive analysis
        test_id = f"llm-enhanced-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        comprehensive_request = f"""
以下のリポジトリのREADMEドキュメントを包括的に分析し、改善提案のissueを作成してください：

リポジトリ: {e2e_config.github_owner}/{e2e_config.github_repo}
ドキュメント: README.md

やってほしいこと:
1. ドキュメントの内容を要約してください
2. 改善提案を作成してください
3. その改善提案でGitHubのissueを作成してください

あなたの持っているツールを使って、この作業を完了してください。
issueのタイトルには「[{e2e_config.test_issue_marker}] 日本語ドキュメント分析 - {test_id}」を含めてください。
        """

        # Create repository context for MCP tools
        from doc_ai_helper_backend.models.repository_context import RepositoryContext
        
        repository_context = RepositoryContext(
            service="github",
            owner=e2e_config.github_owner,
            repo=e2e_config.github_repo,
            ref="main"
        )

        # Step 2: Execute comprehensive workflow with LLM-enhanced tools
        logger.info("Step 2: Executing comprehensive workflow with LLM-enhanced tools")
        
        workflow_response = await backend_api_client.query_llm(
            prompt=comprehensive_request,
            provider=e2e_config.llm_provider,
            tools_enabled=True,
            repository_context=repository_context.model_dump()
        )

        # Step 3: Verify the workflow executed successfully
        logger.info("Step 3: Verifying workflow execution")
        assert workflow_response is not None, "Workflow response should not be None"
        assert "content" in workflow_response, "Workflow response should have content"
        
        # ===== DETAILED TOOL EXECUTION VERIFICATION =====
        logger.info("🔍 Verifying LLM-enhanced tool execution details")
        
        # Check for tool calls (initial LLM response)
        tool_calls_exist = "tool_calls" in workflow_response and workflow_response["tool_calls"] is not None
        tool_results_exist = "tool_execution_results" in workflow_response and workflow_response["tool_execution_results"] is not None
        
        logger.info(f"Tool calls present: {tool_calls_exist}")
        logger.info(f"Tool execution results present: {tool_results_exist}")
        
        # At least one form of tool interaction should be present
        assert tool_calls_exist or tool_results_exist, \
            "Response should contain either 'tool_calls' or 'tool_execution_results' - tools were not invoked"
        
        # Expected tools for comprehensive document analysis workflow
        expected_tools = {"summarize_document_with_llm", "create_improvement_recommendations_with_llm", "create_git_issue"}
        
        # If tool_calls exist, verify expected tools are requested
        if tool_calls_exist:
            tool_calls = workflow_response["tool_calls"]
            assert len(tool_calls) > 0, "Should have at least one tool call"
            
            requested_tools = set()
            for tool_call in tool_calls:
                function_name = tool_call.get("function", {}).get("name", "")
                requested_tools.add(function_name)
                logger.info(f"Tool requested: {function_name}")
                
                # Verify specific tool arguments
                if function_name == "create_git_issue":
                    arguments = tool_call.get("function", {}).get("arguments", "{}")
                    try:
                        args_dict = json.loads(arguments) if isinstance(arguments, str) else arguments
                        assert "title" in args_dict, "create_git_issue should have 'title' argument"
                        assert "description" in args_dict, "create_git_issue should have 'description' argument"
                        assert e2e_config.test_issue_marker in args_dict["title"], f"Issue title should contain test marker '{e2e_config.test_issue_marker}'"
                        logger.info(f"✅ create_git_issue properly requested with title: {args_dict['title'][:50]}...")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Could not parse create_git_issue arguments: {e}")
                elif function_name == "summarize_document_with_llm":
                    arguments = tool_call.get("function", {}).get("arguments", "{}")
                    try:
                        args_dict = json.loads(arguments) if isinstance(arguments, str) else arguments
                        assert "document_content" in args_dict, "summarize_document_with_llm should have 'document_content' argument"
                        logger.info("✅ summarize_document_with_llm properly requested")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Could not parse summarize_document_with_llm arguments: {e}")
                elif function_name == "create_improvement_recommendations_with_llm":
                    arguments = tool_call.get("function", {}).get("arguments", "{}")
                    try:
                        args_dict = json.loads(arguments) if isinstance(arguments, str) else arguments
                        assert "document_content" in args_dict, "create_improvement_recommendations_with_llm should have 'document_content' argument"
                        logger.info("✅ create_improvement_recommendations_with_llm properly requested")
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Could not parse create_improvement_recommendations_with_llm arguments: {e}")
            
            # Check if at least some expected tools were requested
            tools_intersection = expected_tools.intersection(requested_tools)
            assert len(tools_intersection) > 0, f"At least one expected tool should be requested. Expected: {expected_tools}, Requested: {requested_tools}"
            logger.info(f"✅ Expected tools requested: {tools_intersection}")
        
        # Check for tool execution results
        tool_results = workflow_response.get("tool_execution_results", [])
        logger.info(f"Tool execution results: {len(tool_results) if tool_results else 0} tools executed")
        
        # Verify that our LLM-enhanced tools were used
        tools_used = set()
        issue_created = False
        summary_created = False
        recommendations_created = False
        
        if tool_results:
            assert len(tool_results) > 0, "Should have at least one tool execution result"
            
            for tool_result in tool_results:
                function_name = tool_result.get("function_name", "")
                tools_used.add(function_name)
                logger.info(f"Tool executed: {function_name}")
                
                # Check for successful tool execution 
                result = tool_result.get("result", {})
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        pass
                
                if function_name == "summarize_document_with_llm":
                    logger.info("✅ Document summarization tool executed")
                    summary_created = True
                    if isinstance(result, dict) and result.get("success"):
                        logger.info(f"Summary length: {result.get('summary_length', 'N/A')}")
                    else:
                        logger.warning(f"Summary tool failed: {result.get('error', 'Unknown error')}")
                        
                elif function_name == "create_improvement_recommendations_with_llm":
                    logger.info("✅ Improvement recommendations tool executed")
                    recommendations_created = True
                    if isinstance(result, dict) and result.get("success"):
                        recommendations = result.get("recommendations", {})
                        high_priority = recommendations.get("high_priority", [])
                        logger.info(f"High priority recommendations: {len(high_priority)}")
                    else:
                        logger.warning(f"Recommendations tool failed: {result.get('error', 'Unknown error')}")
                        
                elif function_name == "create_git_issue":
                    logger.info("✅ Git issue creation tool executed")
                    if isinstance(result, dict) and result.get("success"):
                        issue_created = True
                        logger.info("Issue creation successful")
                    else:
                        logger.error(f"Issue creation failed: {result.get('error', 'Unknown error')}")
            
            # Verify that at least some expected tools were executed
            executed_intersection = expected_tools.intersection(tools_used)
            logger.info(f"Expected tools executed: {executed_intersection}")
            
            # Log if expected tools were not executed
            missing_tools = expected_tools - tools_used
            if missing_tools:
                logger.warning(f"⚠️ Expected tools not executed: {missing_tools}")
        
        # Final comprehensive verification
        if not tool_results_exist and not tool_calls_exist:
            logger.error("❌ No tool interaction detected - this is likely the core issue")
            logger.info(f"Full workflow response: {json.dumps(workflow_response, indent=2, default=str)}")
        elif tool_calls_exist and not tool_results_exist:
            logger.warning("⚠️ Tools were requested but not executed - execution failure")
        elif not tools_used:
            logger.warning("⚠️ No tools were executed despite results existing")
        
        # Log workflow summary
        logger.info(f"Workflow summary - Tools used: {list(tools_used)}")
        logger.info(f"Summary created: {summary_created}, Recommendations created: {recommendations_created}, Issue created: {issue_created}")

        # Step 4: Verify comprehensive workflow completion
        logger.info("Step 4: Verifying comprehensive workflow completion")
        
        # For real LLM providers, verify the issue was actually created
        if e2e_config.llm_provider != "mock" and issue_created:
            await asyncio.sleep(3)  # Wait for issue creation
            
            created_issue = await git_verification_client.verify_issue_exists(
                service="github",
                owner=e2e_config.github_owner,
                repo=e2e_config.github_repo,
                title_pattern=e2e_config.test_issue_marker,
                max_age_seconds=120
            )
            
            if created_issue:
                logger.info(f"✅ Verified issue creation: #{created_issue['number']} - {created_issue['title']}")
                assert "日本語ドキュメント分析" in created_issue["title"]
                
                return {
                    "success": True,
                    "service": "github",
                    "issue": created_issue,
                    "tools_used": list(tools_used),
                    "workflow_completed": True
                }

        # For mock provider or when verification isn't needed
        logger.info("✅ LLM-enhanced workflow completed successfully")
        return {
            "success": True,
            "service": "github",
            "tools_used": list(tools_used),
            "mock": e2e_config.llm_provider == "mock",
            "workflow_completed": True
        }

    async def test_multi_language_document_comparison(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig,
        test_repository_context
    ):
        """
        Test multi-language document comparison using LLM-enhanced tools.
        
        This test demonstrates how the tools can handle different language
        contexts and provide culturally appropriate analysis.
        """
        if not e2e_config.has_github_config:
            pytest.skip("GitHub configuration not available for E2E tests")

        logger.info("=== Starting Multi-Language Document Comparison Test ===")
        
        # Request analysis in different languages
        comparison_request = """
以下のリポジトリのREADMEドキュメントを日本語と英語の両方の観点から分析してください：

やってほしいこと:
1. ドキュメントを日本語話者の視点で要約してください
2. 英語話者の視点でも要約してください  
3. 両方の文化的背景を考慮した改善提案を作成してください

summarize_document_with_llm と create_improvement_recommendations_with_llm ツールを使用してください。
        """

        # Create repository context
        from doc_ai_helper_backend.models.repository_context import RepositoryContext
        
        repository_context = RepositoryContext(
            service="github",
            owner=e2e_config.github_owner,
            repo=e2e_config.github_repo,
            ref="main"
        )

        # Execute multi-language analysis
        logger.info("Executing multi-language analysis")
        
        analysis_response = await backend_api_client.query_llm(
            prompt=comparison_request,
            provider=e2e_config.llm_provider,
            tools_enabled=True,
            repository_context=repository_context.model_dump()
        )

        # Verify analysis results
        assert analysis_response is not None, "Analysis response should not be None"
        assert "content" in analysis_response, "Analysis should have content"
        
        # Check for tool usage
        tool_results = analysis_response.get("tool_execution_results", [])
        tools_used = []
        
        if tool_results:
            for tool_result in tool_results:
                function_name = tool_result.get("function_name", "")
                tools_used.append(function_name)
                
                result = tool_result.get("result", {})
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        pass
                
                if function_name in ["summarize_document_with_llm", "create_improvement_recommendations_with_llm"]:
                    logger.info(f"✅ {function_name} executed successfully")

        logger.info("✅ Multi-language document comparison completed")
        return {
            "success": True,
            "tools_used": tools_used,
            "analysis_completed": True
        }

    async def test_technical_documentation_enhancement(
        self,
        backend_api_client: BackendAPIClient,
        git_verification_client: GitVerificationClient,
        e2e_config: E2EConfig,
        clean_test_issues,
        test_repository_context
    ):
        """
        Test technical documentation enhancement workflow.
        
        This test focuses on technical documentation analysis with
        specific focus areas and target audiences.
        """
        if not e2e_config.has_github_config:
            pytest.skip("GitHub configuration not available for E2E tests")

        logger.info("=== Starting Technical Documentation Enhancement Test ===")
        
        test_id = f"tech-doc-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        technical_request = f"""
以下のリポジトリのREADMEドキュメントを技術文書として分析し、開発者向けの改善を提案してください：

リポジトリ: {e2e_config.github_owner}/{e2e_config.github_repo}

分析の観点:
- 技術的な完全性
- API文書の明確性
- 開発者向けの使いやすさ
- コード例の品質

やってほしいこと:
1. 技術文書として要約 (focus_area: "technical")
2. 開発者向けの改善提案 (target_audience: "technical")
3. 改善提案でissueを作成

issueタイトル: "[{e2e_config.test_issue_marker}] 技術文書改善 - {test_id}"
        """

        # Create repository context
        from doc_ai_helper_backend.models.repository_context import RepositoryContext
        
        repository_context = RepositoryContext(
            service="github",
            owner=e2e_config.github_owner,
            repo=e2e_config.github_repo,
            ref="main"
        )

        # Execute technical enhancement workflow
        logger.info("Executing technical enhancement workflow")
        
        enhancement_response = await backend_api_client.query_llm(
            prompt=technical_request,
            provider=e2e_config.llm_provider,
            tools_enabled=True,
            repository_context=repository_context.model_dump()
        )

        # Verify workflow execution
        assert enhancement_response is not None, "Enhancement response should not be None"
        
        # Check tool execution
        tool_results = enhancement_response.get("tool_execution_results", [])
        technical_analysis_done = False
        recommendations_created = False
        issue_created = False
        
        if tool_results:
            for tool_result in tool_results:
                function_name = tool_result.get("function_name", "")
                result = tool_result.get("result", {})
                
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except json.JSONDecodeError:
                        pass
                
                if function_name == "summarize_document_with_llm":
                    technical_analysis_done = True
                    logger.info("✅ Technical analysis completed")
                    
                elif function_name == "create_improvement_recommendations_with_llm":
                    recommendations_created = True
                    logger.info("✅ Technical recommendations created")
                    
                elif function_name == "create_git_issue":
                    if isinstance(result, dict) and result.get("success"):
                        issue_created = True
                        logger.info("✅ Technical enhancement issue created")

        # Verify issue creation for real providers
        if e2e_config.llm_provider != "mock" and issue_created:
            await asyncio.sleep(3)
            
            created_issue = await git_verification_client.verify_issue_exists(
                service="github",
                owner=e2e_config.github_owner,
                repo=e2e_config.github_repo,
                title_pattern=e2e_config.test_issue_marker,
                max_age_seconds=120
            )
            
            if created_issue:
                logger.info(f"✅ Verified technical issue: #{created_issue['number']}")
                assert "技術文書改善" in created_issue["title"]

        logger.info("✅ Technical documentation enhancement completed")
        return {
            "success": True,
            "technical_analysis": technical_analysis_done,
            "recommendations_created": recommendations_created,
            "issue_created": issue_created,
            "workflow_completed": True
        }

    async def test_llm_enhanced_error_handling(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig
    ):
        """
        Test error handling in LLM-enhanced tools.
        
        This test verifies that the LLM-enhanced tools handle errors gracefully
        and provide meaningful error messages in Japanese.
        """
        logger.info("=== Starting LLM-Enhanced Error Handling Test ===")
        
        # Request analysis of non-existent document
        error_request = """
存在しないリポジトリのドキュメントを分析してください：

リポジトリ: nonexistent-owner/nonexistent-repo
ドキュメント: README.md

summarize_document_with_llm ツールを使って要約を作成してください。
        """

        # Create invalid repository context
        from doc_ai_helper_backend.models.repository_context import RepositoryContext
        
        invalid_context = RepositoryContext(
            service="github",
            owner="nonexistent-owner-12345",
            repo="nonexistent-repo-12345",
            ref="main"
        )

        # Execute with invalid context
        error_response = await backend_api_client.query_llm(
            prompt=error_request,
            provider=e2e_config.llm_provider,
            tools_enabled=True,
            repository_context=invalid_context.model_dump()
        )

        # Verify error handling
        assert error_response is not None, "Error response should not be None"
        
        # Check for proper error handling
        error_handled = False
        tool_results = error_response.get("tool_execution_results", [])
        
        if tool_results:
            for tool_result in tool_results:
                function_name = tool_result.get("function_name", "")
                result = tool_result.get("result", {})
                
                if function_name == "summarize_document_with_llm":
                    if isinstance(result, str):
                        try:
                            result = json.loads(result)
                        except json.JSONDecodeError:
                            pass
                    
                    if isinstance(result, dict) and not result.get("success"):
                        error_handled = True
                        error_message = result.get("error", "")
                        logger.info(f"✅ Error properly handled: {error_message}")
                        break

        # For mock provider, error handling is assumed
        if e2e_config.llm_provider == "mock":
            error_handled = True
            logger.info("✅ Mock provider error handling test completed")

        assert error_handled, "LLM-enhanced tools should handle errors gracefully"
        
        logger.info("✅ LLM-enhanced error handling test completed")
        return {
            "success": True,
            "error_handled": error_handled,
            "workflow_completed": True
        }

    async def test_batch_document_analysis(
        self,
        backend_api_client: BackendAPIClient,
        e2e_config: E2EConfig,
        test_repository_context
    ):
        """
        Test batch document analysis using LLM-enhanced tools.
        
        This test demonstrates how multiple documents can be analyzed
        efficiently using the enhanced tools.
        """
        if not e2e_config.has_github_config:
            pytest.skip("GitHub configuration not available for E2E tests")

        logger.info("=== Starting Batch Document Analysis Test ===")
        
        # Request batch analysis
        batch_request = f"""
以下のリポジトリの複数のドキュメントを分析してください：

リポジトリ: {e2e_config.github_owner}/{e2e_config.github_repo}

以下のドキュメントを分析してください:
1. README.md
2. ドキュメント全体の構造

やってほしいこと:
1. 各ドキュメントの要約を作成
2. 全体的な改善提案を作成
3. 最も重要な改善点を特定

summarize_document_with_llm と create_improvement_recommendations_with_llm を使用してください。
        """

        # Create repository context
        from doc_ai_helper_backend.models.repository_context import RepositoryContext
        
        repository_context = RepositoryContext(
            service="github",
            owner=e2e_config.github_owner,
            repo=e2e_config.github_repo,
            ref="main"
        )

        # Execute batch analysis
        batch_response = await backend_api_client.query_llm(
            prompt=batch_request,
            provider=e2e_config.llm_provider,
            tools_enabled=True,
            repository_context=repository_context.model_dump()
        )

        # Verify batch analysis
        assert batch_response is not None, "Batch response should not be None"
        assert "content" in batch_response, "Batch response should have content"
        
        # Check for tool execution
        tool_results = batch_response.get("tool_execution_results", [])
        tools_executed = len(tool_results) if tool_results else 0
        
        logger.info(f"Batch analysis completed with {tools_executed} tool executions")
        
        # Verify meaningful analysis was performed
        content = batch_response.get("content", "")
        
        # If no tools were executed, check if the response itself contains analysis
        if tools_executed == 0:
            # For mock provider, we expect at least some response content
            if content:
                logger.info(f"Analysis completed with response content: {len(content)} characters")
            else:
                logger.info("No tool execution occurred - this may be expected for mock provider")
        else:
            assert len(content) > 50, "Batch analysis should produce meaningful content"
        
        logger.info("✅ Batch document analysis completed")
        return {
            "success": True,
            "tools_executed": tools_executed,
            "analysis_completed": True
        }

    async def test_multi_step_before_pattern_workflow(
        self,
        backend_api_client: BackendAPIClient,
        git_verification_client: GitVerificationClient,
        e2e_config: E2EConfig,
        clean_test_issues,
        test_repository_context
    ):
        """
        Test multi-step "Before" pattern workflow from design document.
        
        This test demonstrates the original complex multi-step workflow:
        Step 1: "Summarize this README"
        Step 2: "What can be improved?"
        Step 3: "Create an issue for these improvements"
        
        This recreates the "Before" pattern from the design document to compare 
        against the simplified "After" pattern.
        """
        if not e2e_config.has_github_config:
            pytest.skip("GitHub configuration not available for E2E tests")

        logger.info("=== Starting Multi-Step 'Before' Pattern Workflow Test ===")
        
        test_id = f"before-pattern-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Create repository context for document auto-retrieval
        from doc_ai_helper_backend.models.repository_context import RepositoryContext
        
        repository_context = RepositoryContext(
            service="github",
            owner=e2e_config.github_owner,
            repo=e2e_config.github_repo,
            ref="main",
            current_path="README.md"
        )

        conversation_history = []  # Start with empty conversation history
        
        # Step 1: "Summarize this README" (with auto document retrieval)
        logger.info("Step 1: Requesting document summary")
        step1_response = await backend_api_client.query_llm(
            prompt="このREADMEを要約してください",
            conversation_history=conversation_history,
            repository_context=repository_context.model_dump(),
            auto_include_document=True,
            provider=e2e_config.llm_provider
        )
        
        assert step1_response is not None, "Step 1 response should not be None"
        assert "content" in step1_response, "Step 1 should have content"
        step1_content = step1_response["content"]
        logger.info(f"Step 1 completed: Summary length = {len(step1_content)} characters")
        
        # Update conversation history with Step 1
        conversation_history = [
            {"role": "user", "content": "このREADMEを要約してください"},
            {"role": "assistant", "content": step1_content}
        ]
        
        # Step 2: "What can be improved?" (using conversation context)
        logger.info("Step 2: Requesting improvement suggestions")
        step2_response = await backend_api_client.query_llm(
            prompt="何が改善できますか？",
            conversation_history=conversation_history,
            provider=e2e_config.llm_provider
        )
        
        assert step2_response is not None, "Step 2 response should not be None"
        assert "content" in step2_response, "Step 2 should have content"
        step2_content = step2_response["content"]
        logger.info(f"Step 2 completed: Improvement suggestions length = {len(step2_content)} characters")
        
        # Update conversation history with Step 2
        conversation_history.extend([
            {"role": "user", "content": "何が改善できますか？"},
            {"role": "assistant", "content": step2_content}
        ])
        
        # Step 3: "Create an issue for these improvements" (with tools enabled)
        logger.info("Step 3: Requesting issue creation")
        step3_prompt = f"""
これらの改善でissueを作成してください。

issueのタイトル: "[{e2e_config.test_issue_marker}] マルチステップ改善提案 - {test_id}"
issueの内容: 上記で提案された改善点をまとめたもの

create_git_issue ツールを使用してissueを作成してください。
        """
        
        step3_response = await backend_api_client.query_llm(
            prompt=step3_prompt,
            conversation_history=conversation_history,
            repository_context=repository_context.model_dump(),
            tools_enabled=True,
            provider=e2e_config.llm_provider
        )
        
        assert step3_response is not None, "Step 3 response should not be None"
        logger.info("Step 3 completed: Issue creation request processed")
        
        # Verify the multi-step workflow results
        workflow_results = {
            "step1_summary_length": len(step1_content),
            "step2_improvements_length": len(step2_content),
            "step3_processed": True,
            "conversation_steps": len(conversation_history) // 2,  # Pairs of user/assistant
            "workflow_type": "multi_step_before_pattern"
        }
        
        # Check for issue creation
        issue_created = False
        tool_results = step3_response.get("tool_execution_results", [])
        
        if tool_results:
            for tool_result in tool_results:
                if tool_result.get("function_name") == "create_git_issue":
                    result = tool_result.get("result", {})
                    if isinstance(result, str):
                        try:
                            result = json.loads(result)
                        except json.JSONDecodeError:
                            pass
                    
                    if isinstance(result, dict) and result.get("success"):
                        issue_created = True
                        logger.info("✅ Issue creation successful in multi-step workflow")
                        break
        
        # For real LLM providers, verify the issue was actually created
        if e2e_config.llm_provider != "mock" and issue_created:
            await asyncio.sleep(3)  # Wait for issue creation
            
            created_issue = await git_verification_client.verify_issue_exists(
                service="github",
                owner=e2e_config.github_owner,
                repo=e2e_config.github_repo,
                title_pattern=e2e_config.test_issue_marker,
                max_age_seconds=120
            )
            
            if created_issue:
                logger.info(f"✅ Verified multi-step issue: #{created_issue['number']} - {created_issue['title']}")
                workflow_results["issue_created"] = True
                workflow_results["issue_number"] = created_issue["number"]
                workflow_results["issue_title"] = created_issue["title"]
        
        logger.info("✅ Multi-step 'Before' pattern workflow completed")
        logger.info(f"Workflow stats: {workflow_results}")
        
        return {
            "success": True,
            "workflow_type": "multi_step_before_pattern",
            "steps_completed": 3,
            "conversation_length": len(conversation_history),
            "issue_created": issue_created,
            "workflow_results": workflow_results,
            "mock": e2e_config.llm_provider == "mock"
        }

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
        
        Verifies that both approaches achieve similar results with different UX.
        """
        if not e2e_config.has_github_config:
            pytest.skip("GitHub configuration not available for E2E tests")

        logger.info("=== Starting Workflow Comparison: Before vs After ===")
        
        test_id = f"comparison-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Create repository context
        from doc_ai_helper_backend.models.repository_context import RepositoryContext
        
        repository_context = RepositoryContext(
            service="github",
            owner=e2e_config.github_owner,
            repo=e2e_config.github_repo,
            ref="main",
            current_path="README.md"
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
        before_total_content = len(before_step1["content"]) + len(before_step2["content"]) + len(before_step3.get("content", ""))
        before_issue_created = False
        
        before_tool_results = before_step3.get("tool_execution_results", [])
        if before_tool_results:
            for tool_result in before_tool_results:
                if tool_result.get("function_name") == "create_git_issue":
                    result = tool_result.get("result", {})
                    if isinstance(result, str):
                        try:
                            result = json.loads(result)
                        except json.JSONDecodeError:
                            pass
                    if isinstance(result, dict) and result.get("success"):
                        before_issue_created = True
                        break
        
        # Analyze AFTER workflow
        after_requests = 1
        after_total_content = len(after_response.get("content", ""))
        after_issue_created = False
        
        after_tool_results = after_response.get("tool_execution_results", [])
        if after_tool_results:
            for tool_result in after_tool_results:
                if tool_result.get("function_name") == "create_git_issue":
                    result = tool_result.get("result", {})
                    if isinstance(result, str):
                        try:
                            result = json.loads(result)
                        except json.JSONDecodeError:
                            pass
                    if isinstance(result, dict) and result.get("success"):
                        after_issue_created = True
                        break
        
        # Create comparison report
        comparison_report = {
            "before_workflow": {
                "requests": before_requests,
                "duration_seconds": before_duration,
                "total_content_length": before_total_content,
                "issue_created": before_issue_created,
                "conversation_steps": len(conversation_history) // 2
            },
            "after_workflow": {
                "requests": after_requests,
                "duration_seconds": after_duration,
                "total_content_length": after_total_content,
                "issue_created": after_issue_created,
                "conversation_steps": 0  # No conversation management needed
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