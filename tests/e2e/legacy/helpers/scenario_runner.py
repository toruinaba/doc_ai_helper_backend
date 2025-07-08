"""
Scenario runner for user story-based E2E tests.

This module provides utilities for running test scenarios with proper setup,
teardown, and error handling for user story tests.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
from contextlib import asynccontextmanager

import pytest
from httpx import AsyncClient

from .user_journey_tracker import UserJourneyTracker
from .performance_monitor import PerformanceMonitor
from .data_validator import DataValidator

logger = logging.getLogger(__name__)


class ScenarioContext:
    """Context for running a test scenario."""

    def __init__(
        self,
        scenario_id: str,
        user_persona: str,
        client: AsyncClient,
        journey_tracker: UserJourneyTracker,
        performance_monitor: PerformanceMonitor,
        data_validator: DataValidator,
    ):
        self.scenario_id = scenario_id
        self.user_persona = user_persona
        self.client = client
        self.journey_tracker = journey_tracker
        self.performance_monitor = performance_monitor
        self.data_validator = data_validator
        self.start_time = datetime.now()
        self.test_data: Dict[str, Any] = {}

    def set_test_data(self, key: str, value: Any) -> None:
        """Set test data for the scenario."""
        self.test_data[key] = value

    def get_test_data(self, key: str, default: Any = None) -> Any:
        """Get test data for the scenario."""
        return self.test_data.get(key, default)


class ScenarioRunner:
    """Runner for executing user story test scenarios."""

    def __init__(self, fixtures_path: Path):
        self.fixtures_path = fixtures_path
        self.scenarios: Dict[str, Dict[str, Any]] = {}
        self.personas: Dict[str, Dict[str, Any]] = {}
        self._load_fixtures()

    def _load_fixtures(self) -> None:
        """Load test fixtures from JSON files."""
        try:
            # Load user personas
            personas_file = self.fixtures_path / "user_personas.json"
            if personas_file.exists():
                with open(personas_file, "r", encoding="utf-8") as f:
                    self.personas = json.load(f)

            # Load story scenarios
            scenarios_file = self.fixtures_path / "story_scenarios.json"
            if scenarios_file.exists():
                with open(scenarios_file, "r", encoding="utf-8") as f:
                    self.scenarios = json.load(f)

        except Exception as e:
            logger.error(f"Failed to load fixtures: {e}")

    def get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get scenario configuration by ID."""
        return self.scenarios.get(scenario_id)

    def get_persona(self, persona_id: str) -> Optional[Dict[str, Any]]:
        """Get user persona by ID."""
        return self.personas.get(persona_id)

    @asynccontextmanager
    async def run_scenario(
        self,
        scenario_id: str,
        user_persona: str,
        client: AsyncClient,
        setup_hooks: Optional[List[Callable]] = None,
        teardown_hooks: Optional[List[Callable]] = None,
    ) -> AsyncGenerator[ScenarioContext, None]:
        """
        Run a test scenario with proper setup and teardown.

        Args:
            scenario_id: ID of the scenario to run
            user_persona: User persona to use for the test
            client: HTTP client for API calls
            setup_hooks: Optional setup functions to run before the scenario
            teardown_hooks: Optional teardown functions to run after the scenario

        Yields:
            ScenarioContext: Context object for the running scenario
        """
        # Get persona data
        persona_data = self.get_persona(user_persona) or {
            "id": user_persona,
            "name": f"Test User ({user_persona})",
            "role": "tester",
        }

        # Initialize components
        journey_tracker = UserJourneyTracker(persona_data)
        performance_monitor = PerformanceMonitor()
        data_validator = DataValidator()

        # Create scenario context
        context = ScenarioContext(
            scenario_id=scenario_id,
            user_persona=user_persona,
            client=client,
            journey_tracker=journey_tracker,
            performance_monitor=performance_monitor,
            data_validator=data_validator,
        )

        try:
            # Run setup hooks
            if setup_hooks:
                for hook in setup_hooks:
                    if asyncio.iscoroutinefunction(hook):
                        await hook(context)
                    else:
                        hook(context)

            # Start monitoring
            await performance_monitor.start_monitoring()
            journey_tracker.start_journey(scenario_id, user_persona)

            logger.info(
                f"Starting scenario: {scenario_id} with persona: {user_persona}"
            )

            yield context

        except Exception as e:
            logger.error(f"Error in scenario {scenario_id}: {e}")
            # Log the error for analysis
            journey_tracker.add_error(str(e))
            raise

        finally:
            # Stop monitoring
            await performance_monitor.stop_monitoring()
            journey_tracker.end_journey()

            # Run teardown hooks
            if teardown_hooks:
                for hook in teardown_hooks:
                    try:
                        if asyncio.iscoroutinefunction(hook):
                            await hook(context)
                        else:
                            hook(context)
                    except Exception as e:
                        logger.error(f"Error in teardown hook: {e}")

            # Generate test report
            await self._generate_test_report(context)

            logger.info(f"Completed scenario: {scenario_id}")

    async def _generate_test_report(self, context: ScenarioContext) -> None:
        """Generate a test report for the scenario."""
        try:
            report = {
                "scenario_id": context.scenario_id,
                "user_persona": context.user_persona,
                "start_time": context.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "duration": (datetime.now() - context.start_time).total_seconds(),
                "journey_summary": context.journey_tracker.get_summary(),
                "performance_metrics": await context.performance_monitor.get_metrics(),
                "test_data": context.test_data,
            }

            # Log the report
            logger.info(
                f"Test report for {context.scenario_id}: {json.dumps(report, indent=2)}"
            )

        except Exception as e:
            logger.error(f"Failed to generate test report: {e}")

    async def run_multiple_scenarios(
        self,
        scenario_ids: List[str],
        user_persona: str,
        client: AsyncClient,
        parallel: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Run multiple scenarios in sequence or parallel.

        Args:
            scenario_ids: List of scenario IDs to run
            user_persona: User persona to use for all scenarios
            client: HTTP client for API calls
            parallel: Whether to run scenarios in parallel

        Returns:
            List of scenario results
        """
        results = []

        if parallel:
            # Run scenarios in parallel
            tasks = []
            for scenario_id in scenario_ids:
                task = self._run_single_scenario(scenario_id, user_persona, client)
                tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            # Run scenarios sequentially
            for scenario_id in scenario_ids:
                try:
                    result = await self._run_single_scenario(
                        scenario_id, user_persona, client
                    )
                    results.append(result)
                except Exception as e:
                    results.append({"error": str(e), "scenario_id": scenario_id})

        return results

    async def _run_single_scenario(
        self,
        scenario_id: str,
        user_persona: str,
        client: AsyncClient,
    ) -> Dict[str, Any]:
        """Run a single scenario and return the result."""
        async with self.run_scenario(scenario_id, user_persona, client) as context:
            scenario_config = self.get_scenario(scenario_id)
            if not scenario_config:
                raise ValueError(f"Scenario not found: {scenario_id}")

            # Execute scenario steps (this would be implemented by specific test methods)
            result = {
                "scenario_id": scenario_id,
                "status": "completed",
                "duration": (datetime.now() - context.start_time).total_seconds(),
            }

            return result


class ScenarioStep:
    """Represents a single step in a test scenario."""

    def __init__(
        self,
        name: str,
        action: Callable,
        expected_result: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ):
        self.name = name
        self.action = action
        self.expected_result = expected_result
        self.timeout = timeout

    async def execute(self, context: ScenarioContext) -> Dict[str, Any]:
        """Execute the scenario step."""
        start_time = datetime.now()

        try:
            # Execute the action
            if asyncio.iscoroutinefunction(self.action):
                result = await asyncio.wait_for(
                    self.action(context), timeout=self.timeout
                )
            else:
                result = self.action(context)

            # Record the step
            context.journey_tracker.add_step(
                self.name, "success", (datetime.now() - start_time).total_seconds()
            )

            return {"status": "success", "result": result}

        except Exception as e:
            # Record the error
            context.journey_tracker.add_step(
                self.name,
                "error",
                (datetime.now() - start_time).total_seconds(),
                str(e),
            )
            raise


class ScenarioBuilder:
    """Builder for creating test scenarios with steps."""

    def __init__(self, scenario_id: str):
        self.scenario_id = scenario_id
        self.steps: List[ScenarioStep] = []

    def add_step(
        self,
        name: str,
        action: Callable,
        expected_result: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
    ) -> "ScenarioBuilder":
        """Add a step to the scenario."""
        step = ScenarioStep(name, action, expected_result, timeout)
        self.steps.append(step)
        return self

    async def execute(self, context: ScenarioContext) -> List[Dict[str, Any]]:
        """Execute all steps in the scenario."""
        results = []

        for step in self.steps:
            try:
                result = await step.execute(context)
                results.append(result)
            except Exception as e:
                results.append({"status": "error", "error": str(e), "step": step.name})
                # Stop execution on error
                break

        return results
