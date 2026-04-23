"""Integration tests for MCP tools — verifies tool registration and response formatting."""

from __future__ import annotations

import httpx
import pytest
import respx

from langfuse_traces_mcp.server import (
    fetch_langfuse_traces,
    get_langfuse_trace_detail,
    list_langfuse_trace_filters,
)

from .conftest import (
    SAMPLE_EMPTY_RESPONSE,
    SAMPLE_TRACE_DETAIL,
    SAMPLE_TRACES_LIST_RESPONSE,
    TEST_HOST_URL,
    TEST_PUBLIC_KEY,
    TEST_SECRET_KEY,
)


# ===================================================================
# fetch_langfuse_traces
# ===================================================================


class TestFetchLangfuseTraces:
    """Test the fetch_langfuse_traces tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_successful_fetch(self) -> None:
        """Should return formatted trace summaries."""
        respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRACES_LIST_RESPONSE)
        )

        result = await fetch_langfuse_traces(
            public_key=TEST_PUBLIC_KEY,
            secret_key=TEST_SECRET_KEY,
            host_url=TEST_HOST_URL,
        )

        assert "trace-abc-123" in result
        assert "agent-run-pediatrician" in result
        assert "Page 1" in result
        assert "1 of 1 total traces" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_with_filters(self) -> None:
        """Should show active filters in output."""
        respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRACES_LIST_RESPONSE)
        )

        result = await fetch_langfuse_traces(
            public_key=TEST_PUBLIC_KEY,
            secret_key=TEST_SECRET_KEY,
            host_url=TEST_HOST_URL,
            name="agent-run-pediatrician",
            environment="production",
        )

        assert "Active filters" in result
        assert "name=agent-run-pediatrician" in result
        assert "environment=production" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_empty_results(self) -> None:
        """Should return a friendly message when no traces match."""
        respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(200, json=SAMPLE_EMPTY_RESPONSE)
        )

        result = await fetch_langfuse_traces(
            public_key=TEST_PUBLIC_KEY,
            secret_key=TEST_SECRET_KEY,
            host_url=TEST_HOST_URL,
            name="nonexistent",
        )

        assert "No traces matched" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_api_error_formatted(self) -> None:
        """Should return a readable error message on API failure."""
        respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(401, json={"message": "Unauthorized"})
        )

        result = await fetch_langfuse_traces(
            public_key=TEST_PUBLIC_KEY,
            secret_key=TEST_SECRET_KEY,
            host_url=TEST_HOST_URL,
        )

        assert "❌" in result
        assert "401" in result
        assert "Unauthorized" in result

    @pytest.mark.asyncio
    async def test_invalid_credentials_formatted(self) -> None:
        """Should return validation error for empty credentials."""
        result = await fetch_langfuse_traces(
            public_key="",
            secret_key="sk",
            host_url="https://example.com",
        )

        assert "❌" in result
        assert "Validation error" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_trace_metadata_shown(self) -> None:
        """Should include metadata fields in the output."""
        respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRACES_LIST_RESPONSE)
        )

        result = await fetch_langfuse_traces(
            public_key=TEST_PUBLIC_KEY,
            secret_key=TEST_SECRET_KEY,
            host_url=TEST_HOST_URL,
        )

        assert "user-42" in result
        assert "production" in result
        assert "2.1.0" in result


# ===================================================================
# get_langfuse_trace_detail
# ===================================================================


class TestGetLangfuseTraceDetail:
    """Test the get_langfuse_trace_detail tool."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_successful_detail(self) -> None:
        """Should return full trace detail with observations and scores."""
        trace_id = "trace-abc-123"
        respx.get(f"{TEST_HOST_URL}/api/public/traces/{trace_id}").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRACE_DETAIL)
        )

        result = await get_langfuse_trace_detail(
            public_key=TEST_PUBLIC_KEY,
            secret_key=TEST_SECRET_KEY,
            host_url=TEST_HOST_URL,
            trace_id=trace_id,
        )

        # Trace info
        assert "trace-abc-123" in result
        assert "agent-run-pediatrician" in result

        # Observations
        assert "Observations" in result
        assert "GENERATION" in result
        assert "llm-call" in result
        assert "gemini-2.5-pro" in result
        assert "SPAN" in result
        assert "memory-retrieval" in result

        # Scores
        assert "Scores" in result
        assert "relevance" in result
        assert "0.95" in result
        assert "accuracy" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_404_error(self) -> None:
        """Should return error for missing trace."""
        trace_id = "nonexistent"
        respx.get(f"{TEST_HOST_URL}/api/public/traces/{trace_id}").mock(
            return_value=httpx.Response(404, json={"message": "Trace not found"})
        )

        result = await get_langfuse_trace_detail(
            public_key=TEST_PUBLIC_KEY,
            secret_key=TEST_SECRET_KEY,
            host_url=TEST_HOST_URL,
            trace_id=trace_id,
        )

        assert "❌" in result
        assert "404" in result


# ===================================================================
# list_langfuse_trace_filters
# ===================================================================


class TestListLangfuseTraceFilters:
    """Test the list_langfuse_trace_filters help tool."""

    @pytest.mark.asyncio
    async def test_returns_filter_reference(self) -> None:
        """Should return a reference table of all filters."""
        result = await list_langfuse_trace_filters()

        # Check key filter names are documented
        assert "name" in result
        assert "user_id" in result
        assert "session_id" in result
        assert "tags" in result
        assert "version" in result
        assert "release" in result
        assert "environment" in result
        assert "from_timestamp" in result
        assert "to_timestamp" in result
        assert "limit" in result
        assert "page" in result

        # Check credentials section
        assert "public_key" in result
        assert "secret_key" in result
        assert "host_url" in result

        # Check example
        assert "fetch_langfuse_traces" in result
