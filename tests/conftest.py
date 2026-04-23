"""Shared test fixtures and mock data for Langfuse Traces MCP tests."""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Sample Langfuse API response data
# ---------------------------------------------------------------------------

SAMPLE_TRACE_SUMMARY = {
    "id": "trace-abc-123",
    "name": "agent-run-pediatrician",
    "timestamp": "2026-04-22T18:30:00.000Z",
    "userId": "user-42",
    "sessionId": "session-xyz",
    "tags": ["production", "v2"],
    "version": "2.1.0",
    "release": "2026-04-22",
    "environment": "production",
    "metadata": {"agent": "pediatrician", "priority": "high"},
    "public": False,
}

SAMPLE_TRACE_DETAIL = {
    **SAMPLE_TRACE_SUMMARY,
    "input": {"message": "What vaccines does a 6-month-old need?"},
    "output": {"response": "At 6 months, the recommended vaccines include..."},
    "observations": [
        {
            "id": "obs-001",
            "type": "GENERATION",
            "name": "llm-call",
            "startTime": "2026-04-22T18:30:01.000Z",
            "endTime": "2026-04-22T18:30:03.500Z",
            "model": "gemini-2.5-pro",
            "input": {"prompt": "You are a pediatrician..."},
            "output": {"text": "At 6 months, the recommended vaccines include..."},
            "usage": {"input": 150, "output": 280, "total": 430},
            "level": "DEFAULT",
        },
        {
            "id": "obs-002",
            "type": "SPAN",
            "name": "memory-retrieval",
            "startTime": "2026-04-22T18:30:00.500Z",
            "endTime": "2026-04-22T18:30:01.000Z",
            "input": {"query": "vaccine schedule infant"},
            "output": {"docs_found": 3},
        },
    ],
    "scores": [
        {
            "name": "relevance",
            "value": 0.95,
            "comment": "Highly relevant response",
        },
        {
            "name": "accuracy",
            "value": 0.88,
        },
    ],
}

SAMPLE_TRACES_LIST_RESPONSE = {
    "data": [SAMPLE_TRACE_SUMMARY],
    "meta": {
        "page": 1,
        "limit": 20,
        "totalItems": 1,
        "totalPages": 1,
    },
}

SAMPLE_EMPTY_RESPONSE = {
    "data": [],
    "meta": {
        "page": 1,
        "limit": 20,
        "totalItems": 0,
        "totalPages": 0,
    },
}


# ---------------------------------------------------------------------------
# Credential fixtures
# ---------------------------------------------------------------------------

TEST_PUBLIC_KEY = "pk-lf-test-123456"
TEST_SECRET_KEY = "sk-lf-test-abcdef"
TEST_HOST_URL = "https://test.langfuse.example.com"


@pytest.fixture
def credentials_dict() -> dict[str, str]:
    """Return test credential dict for direct use in tool calls."""
    return {
        "public_key": TEST_PUBLIC_KEY,
        "secret_key": TEST_SECRET_KEY,
        "host_url": TEST_HOST_URL,
    }
