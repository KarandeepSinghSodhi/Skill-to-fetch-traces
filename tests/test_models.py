"""Tests for Pydantic filter and credential models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from langfuse_traces_mcp.models import LangfuseCredentials, TraceFilters


# ===================================================================
# TraceFilters
# ===================================================================


class TestTraceFiltersDefaults:
    """Test default values for TraceFilters."""

    def test_all_defaults(self) -> None:
        filters = TraceFilters()
        assert filters.limit == 20
        assert filters.page == 1
        assert filters.name is None
        assert filters.user_id is None
        assert filters.session_id is None
        assert filters.tags is None
        assert filters.version is None
        assert filters.release is None
        assert filters.environment is None
        assert filters.from_timestamp is None
        assert filters.to_timestamp is None

    def test_custom_values(self) -> None:
        filters = TraceFilters(
            name="my-trace",
            user_id="user-1",
            session_id="sess-1",
            tags=["prod", "v2"],
            version="1.0.0",
            release="2026-04-01",
            environment="production",
            from_timestamp="2026-04-01T00:00:00Z",
            to_timestamp="2026-04-22T00:00:00Z",
            limit=50,
            page=3,
        )
        assert filters.name == "my-trace"
        assert filters.user_id == "user-1"
        assert filters.tags == ["prod", "v2"]
        assert filters.limit == 50
        assert filters.page == 3


class TestTraceFiltersValidation:
    """Test validation rules for TraceFilters."""

    def test_limit_min(self) -> None:
        with pytest.raises(ValidationError, match="limit"):
            TraceFilters(limit=0)

    def test_limit_max(self) -> None:
        with pytest.raises(ValidationError, match="limit"):
            TraceFilters(limit=101)

    def test_limit_boundary_valid(self) -> None:
        assert TraceFilters(limit=1).limit == 1
        assert TraceFilters(limit=100).limit == 100

    def test_page_min(self) -> None:
        with pytest.raises(ValidationError, match="page"):
            TraceFilters(page=0)

    def test_tags_string_coercion(self) -> None:
        """A single tag string should be wrapped into a list."""
        filters = TraceFilters(tags="production")  # type: ignore[arg-type]
        assert filters.tags == ["production"]

    def test_tags_list_passthrough(self) -> None:
        filters = TraceFilters(tags=["a", "b"])
        assert filters.tags == ["a", "b"]


class TestTraceFiltersQueryParams:
    """Test conversion to API query parameters."""

    def test_defaults_only_include_limit_and_page(self) -> None:
        params = TraceFilters().to_query_params()
        assert params == {"limit": 20, "page": 1}

    def test_all_fields_mapped(self) -> None:
        filters = TraceFilters(
            name="test",
            user_id="u1",
            session_id="s1",
            tags=["a"],
            version="1.0",
            release="r1",
            environment="prod",
            from_timestamp="2026-01-01T00:00:00Z",
            to_timestamp="2026-12-31T23:59:59Z",
            limit=10,
            page=2,
        )
        params = filters.to_query_params()
        assert params["name"] == "test"
        assert params["userId"] == "u1"
        assert params["sessionId"] == "s1"
        assert params["tags"] == ["a"]
        assert params["version"] == "1.0"
        assert params["release"] == "r1"
        assert params["environment"] == "prod"
        assert params["fromTimestamp"] == "2026-01-01T00:00:00Z"
        assert params["toTimestamp"] == "2026-12-31T23:59:59Z"
        assert params["limit"] == 10
        assert params["page"] == 2

    def test_none_fields_excluded(self) -> None:
        params = TraceFilters(name="only-name").to_query_params()
        assert "name" in params
        assert "userId" not in params
        assert "sessionId" not in params


# ===================================================================
# LangfuseCredentials
# ===================================================================


class TestLangfuseCredentials:
    """Test credential validation."""

    def test_valid_credentials(self) -> None:
        creds = LangfuseCredentials(
            public_key="pk-lf-123",
            secret_key="sk-lf-456",
            host_url="https://cloud.langfuse.com",
        )
        assert creds.public_key == "pk-lf-123"
        assert creds.secret_key == "sk-lf-456"
        assert creds.host_url == "https://cloud.langfuse.com"

    def test_trailing_slash_stripped(self) -> None:
        creds = LangfuseCredentials(
            public_key="pk",
            secret_key="sk",
            host_url="http://localhost:3000///",
        )
        assert creds.host_url == "http://localhost:3000"

    def test_empty_public_key_rejected(self) -> None:
        with pytest.raises(ValidationError, match="public_key"):
            LangfuseCredentials(
                public_key="",
                secret_key="sk",
                host_url="https://example.com",
            )

    def test_empty_secret_key_rejected(self) -> None:
        with pytest.raises(ValidationError, match="secret_key"):
            LangfuseCredentials(
                public_key="pk",
                secret_key="",
                host_url="https://example.com",
            )

    def test_empty_host_url_rejected(self) -> None:
        with pytest.raises(ValidationError, match="host_url"):
            LangfuseCredentials(
                public_key="pk",
                secret_key="sk",
                host_url="",
            )
