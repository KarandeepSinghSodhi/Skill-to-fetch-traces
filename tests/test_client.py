"""Tests for the Langfuse REST API client using mocked HTTP responses."""

from __future__ import annotations

import httpx
import pytest
import respx

from langfuse_traces_mcp.client import LangfuseAPIError, LangfuseClient
from langfuse_traces_mcp.models import LangfuseCredentials, TraceFilters

from .conftest import (
    SAMPLE_TRACE_DETAIL,
    SAMPLE_TRACES_LIST_RESPONSE,
    TEST_HOST_URL,
    TEST_PUBLIC_KEY,
    TEST_SECRET_KEY,
)


@pytest.fixture
def credentials() -> LangfuseCredentials:
    return LangfuseCredentials(
        public_key=TEST_PUBLIC_KEY,
        secret_key=TEST_SECRET_KEY,
        host_url=TEST_HOST_URL,
    )


# ===================================================================
# list_traces
# ===================================================================


class TestListTraces:
    """Test the list_traces method."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_basic_list(self, credentials: LangfuseCredentials) -> None:
        """Should fetch traces with default filters."""
        route = respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRACES_LIST_RESPONSE)
        )

        async with LangfuseClient(credentials) as client:
            result = await client.list_traces()

        assert route.called
        assert len(result["data"]) == 1
        assert result["data"][0]["id"] == "trace-abc-123"
        assert result["meta"]["totalItems"] == 1

    @respx.mock
    @pytest.mark.asyncio
    async def test_with_filters(self, credentials: LangfuseCredentials) -> None:
        """Should pass filter query params to the API."""
        route = respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRACES_LIST_RESPONSE)
        )

        filters = TraceFilters(
            name="agent-run",
            user_id="user-42",
            tags=["production"],
            limit=5,
        )
        async with LangfuseClient(credentials) as client:
            await client.list_traces(filters)

        # Verify the query parameters were sent
        request = route.calls[0].request
        assert "name=agent-run" in str(request.url)
        assert "userId=user-42" in str(request.url)
        assert "limit=5" in str(request.url)

    @respx.mock
    @pytest.mark.asyncio
    async def test_auth_header(self, credentials: LangfuseCredentials) -> None:
        """Should send Basic Auth with public_key:secret_key."""
        route = respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRACES_LIST_RESPONSE)
        )

        async with LangfuseClient(credentials) as client:
            await client.list_traces()

        request = route.calls[0].request
        auth_header = request.headers.get("authorization", "")
        assert auth_header.startswith("Basic ")
        assert auth_header != "Basic "  # Not empty credentials

    @respx.mock
    @pytest.mark.asyncio
    async def test_401_unauthorized(self, credentials: LangfuseCredentials) -> None:
        """Should raise LangfuseAPIError on 401."""
        respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(401, json={"message": "Invalid API keys"})
        )

        async with LangfuseClient(credentials) as client:
            with pytest.raises(LangfuseAPIError) as exc_info:
                await client.list_traces()

        assert exc_info.value.status_code == 401
        assert "Invalid API keys" in exc_info.value.detail

    @respx.mock
    @pytest.mark.asyncio
    async def test_500_server_error(self, credentials: LangfuseCredentials) -> None:
        """Should raise LangfuseAPIError on 500."""
        respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(500, json={"error": "Internal Server Error"})
        )

        async with LangfuseClient(credentials) as client:
            with pytest.raises(LangfuseAPIError) as exc_info:
                await client.list_traces()

        assert exc_info.value.status_code == 500

    @respx.mock
    @pytest.mark.asyncio
    async def test_non_json_error_body(self, credentials: LangfuseCredentials) -> None:
        """Should handle non-JSON error response gracefully."""
        respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(502, text="Bad Gateway")
        )

        async with LangfuseClient(credentials) as client:
            with pytest.raises(LangfuseAPIError) as exc_info:
                await client.list_traces()

        assert exc_info.value.status_code == 502
        assert "Bad Gateway" in exc_info.value.detail


# ===================================================================
# get_trace
# ===================================================================


class TestGetTrace:
    """Test the get_trace method."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_basic_get(self, credentials: LangfuseCredentials) -> None:
        """Should fetch a single trace by ID."""
        trace_id = "trace-abc-123"
        route = respx.get(f"{TEST_HOST_URL}/api/public/traces/{trace_id}").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRACE_DETAIL)
        )

        async with LangfuseClient(credentials) as client:
            result = await client.get_trace(trace_id)

        assert route.called
        assert result["id"] == trace_id
        assert "observations" in result
        assert "scores" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_404_not_found(self, credentials: LangfuseCredentials) -> None:
        """Should raise LangfuseAPIError on 404."""
        trace_id = "nonexistent-trace"
        respx.get(f"{TEST_HOST_URL}/api/public/traces/{trace_id}").mock(
            return_value=httpx.Response(404, json={"message": "Trace not found"})
        )

        async with LangfuseClient(credentials) as client:
            with pytest.raises(LangfuseAPIError) as exc_info:
                await client.get_trace(trace_id)

        assert exc_info.value.status_code == 404


# ===================================================================
# Client lifecycle
# ===================================================================


class TestClientLifecycle:
    """Test context manager and user-agent header."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_user_agent_header(self, credentials: LangfuseCredentials) -> None:
        """Should send custom User-Agent header."""
        route = respx.get(f"{TEST_HOST_URL}/api/public/traces").mock(
            return_value=httpx.Response(200, json=SAMPLE_TRACES_LIST_RESPONSE)
        )

        async with LangfuseClient(credentials) as client:
            await client.list_traces()

        request = route.calls[0].request
        assert "langfuse-traces-mcp" in request.headers.get("user-agent", "")
