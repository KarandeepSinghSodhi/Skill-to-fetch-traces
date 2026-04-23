"""Pydantic models for Langfuse trace filters and response formatting."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class TraceFilters(BaseModel):
    """Filters for querying Langfuse traces via GET /api/public/traces."""

    name: Optional[str] = Field(
        default=None,
        description="Filter traces by name (exact match).",
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Filter traces by user ID.",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Filter traces by session ID.",
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Filter traces by tags. Traces must have ALL specified tags.",
    )
    version: Optional[str] = Field(
        default=None,
        description="Filter traces by application version.",
    )
    release: Optional[str] = Field(
        default=None,
        description="Filter traces by release identifier.",
    )
    environment: Optional[str] = Field(
        default=None,
        description="Filter traces by environment (e.g. 'production', 'staging', 'development').",
    )
    from_timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp — only return traces created at or after this time.",
    )
    to_timestamp: Optional[str] = Field(
        default=None,
        description="ISO 8601 timestamp — only return traces created before this time.",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of traces to return (1–100).",
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Page number for pagination.",
    )

    @field_validator("tags", mode="before")
    @classmethod
    def coerce_tags(cls, v: object) -> object:
        """Accept a single tag string and wrap it in a list."""
        if isinstance(v, str):
            return [v]
        return v

    def to_query_params(self) -> dict[str, str | int | list[str]]:
        """Convert filters to query parameters for the Langfuse API.

        Only includes non-None values. Field names are mapped to the API's
        expected camelCase / snake_case parameter names.
        """
        param_map: dict[str, str] = {
            "name": "name",
            "user_id": "userId",
            "session_id": "sessionId",
            "tags": "tags",
            "version": "version",
            "release": "release",
            "environment": "environment",
            "from_timestamp": "fromTimestamp",
            "to_timestamp": "toTimestamp",
            "limit": "limit",
            "page": "page",
        }
        params: dict[str, str | int | list[str]] = {}
        for field_name, api_name in param_map.items():
            value = getattr(self, field_name)
            if value is not None:
                params[api_name] = value
        return params


class LangfuseCredentials(BaseModel):
    """Credentials required to authenticate with a Langfuse instance."""

    public_key: str = Field(
        ...,
        min_length=1,
        description="Langfuse public key (used as HTTP Basic Auth username).",
    )
    secret_key: str = Field(
        ...,
        min_length=1,
        description="Langfuse secret key (used as HTTP Basic Auth password).",
    )
    host_url: str = Field(
        ...,
        min_length=1,
        description="Langfuse host URL (e.g. 'https://cloud.langfuse.com' or 'http://localhost:3000').",
    )

    @field_validator("host_url", mode="after")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        """Normalize host URL by stripping trailing slashes."""
        return v.rstrip("/")
