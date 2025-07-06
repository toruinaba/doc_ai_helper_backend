"""
Tests for simulation utilities.

This module tests the simulation utilities used for testing and development
across different LLM service implementations.
"""

import pytest
import asyncio
from unittest.mock import patch

from doc_ai_helper_backend.services.llm.utils.simulation import SimulationUtils
from doc_ai_helper_backend.core.exceptions import LLMServiceException


class TestSimulationUtils:
    """Test the SimulationUtils class."""

    @pytest.mark.asyncio
    async def test_simulate_delay_positive(self):
        """Test simulating delay with positive values."""
        # Test with small delay
        start_time = asyncio.get_event_loop().time()
        await SimulationUtils.simulate_delay(0.1)
        end_time = asyncio.get_event_loop().time()

        # Allow for some timing variance
        assert end_time - start_time >= 0.05

    @pytest.mark.asyncio
    async def test_simulate_delay_zero(self):
        """Test simulating delay with zero value."""
        start_time = asyncio.get_event_loop().time()
        await SimulationUtils.simulate_delay(0)
        end_time = asyncio.get_event_loop().time()

        # Should complete almost immediately
        assert end_time - start_time < 0.01

    @pytest.mark.asyncio
    async def test_simulate_delay_negative(self):
        """Test simulating delay with negative value."""
        start_time = asyncio.get_event_loop().time()
        await SimulationUtils.simulate_delay(-1.0)
        end_time = asyncio.get_event_loop().time()

        # Should complete almost immediately
        assert end_time - start_time < 0.01

    def test_should_simulate_error_default_keywords(self):
        """Test error simulation detection with default keywords."""
        # Test default error keywords
        assert SimulationUtils.should_simulate_error("Please simulate_error")
        assert SimulationUtils.should_simulate_error("Force_Error now")
        assert SimulationUtils.should_simulate_error("TEST_ERROR case")

        # Test non-error prompts
        assert not SimulationUtils.should_simulate_error("Normal prompt")
        assert not SimulationUtils.should_simulate_error("Hello world")

    def test_should_simulate_error_custom_keywords(self):
        """Test error simulation detection with custom keywords."""
        custom_keywords = ["crash", "fail", "boom"]

        assert SimulationUtils.should_simulate_error("Make it crash", custom_keywords)
        assert SimulationUtils.should_simulate_error("Please fail", custom_keywords)
        assert SimulationUtils.should_simulate_error("BOOM!", custom_keywords)

        # Default keywords shouldn't work with custom list
        assert not SimulationUtils.should_simulate_error(
            "simulate_error", custom_keywords
        )

        # Non-error prompts
        assert not SimulationUtils.should_simulate_error(
            "Normal prompt", custom_keywords
        )

    def test_should_simulate_error_empty_keywords(self):
        """Test error simulation detection with empty keyword list."""
        assert not SimulationUtils.should_simulate_error("simulate_error", [])
        assert not SimulationUtils.should_simulate_error("any prompt", [])

    def test_raise_simulated_error_default_message(self):
        """Test raising simulated error with default message."""
        with pytest.raises(LLMServiceException) as exc_info:
            SimulationUtils.raise_simulated_error()

        assert "Simulated error for testing purposes" in str(exc_info.value)

    def test_raise_simulated_error_custom_message(self):
        """Test raising simulated error with custom message."""
        custom_message = "Custom test error message"

        with pytest.raises(LLMServiceException) as exc_info:
            SimulationUtils.raise_simulated_error(custom_message)

        assert custom_message in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_check_and_raise_error_if_needed_no_error(self):
        """Test check and raise when no error should be simulated."""
        # Should not raise any exception
        await SimulationUtils.check_and_raise_error_if_needed("Normal prompt")
        await SimulationUtils.check_and_raise_error_if_needed("Hello world")

    @pytest.mark.asyncio
    async def test_check_and_raise_error_if_needed_with_error(self):
        """Test check and raise when error should be simulated."""
        with pytest.raises(LLMServiceException):
            await SimulationUtils.check_and_raise_error_if_needed("simulate_error")

        with pytest.raises(LLMServiceException):
            await SimulationUtils.check_and_raise_error_if_needed("force_error please")

    @pytest.mark.asyncio
    async def test_check_and_raise_error_if_needed_custom_keywords(self):
        """Test check and raise with custom error keywords."""
        custom_keywords = ["crash", "boom"]

        # Should raise with custom keywords
        with pytest.raises(LLMServiceException):
            await SimulationUtils.check_and_raise_error_if_needed(
                "crash now", custom_keywords
            )

        # Should not raise with default keywords when custom list is provided
        await SimulationUtils.check_and_raise_error_if_needed(
            "simulate_error", custom_keywords
        )
