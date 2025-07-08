"""
Helper modules for E2E tests.

This package contains helper modules and utilities for user story-based E2E tests:
- frontend_simulator: Simulates frontend user interactions
- user_journey_tracker: Tracks and analyzes user journeys
- story_assertions: User story-specific assertion functions
- scenario_runner: Runs test scenarios with proper setup/teardown
- performance_monitor: Monitors performance during E2E tests
- data_validator: Validates test data and responses
- test_data_generator: Generates test data for scenarios
- api_client: Backend API client for E2E communication
"""

from .frontend_simulator import FrontendSimulator
from .user_journey_tracker import UserJourneyTracker
from .story_assertions import StoryAssertions
from .scenario_runner import ScenarioRunner
from .performance_monitor import PerformanceMonitor
from .data_validator import DataValidator
from .test_data_generator import TestDataGenerator
from .api_client import BackendAPIClient

__all__ = [
    "FrontendSimulator",
    "UserJourneyTracker",
    "StoryAssertions",
    "ScenarioRunner",
    "PerformanceMonitor",
    "DataValidator",
    "TestDataGenerator",
]
