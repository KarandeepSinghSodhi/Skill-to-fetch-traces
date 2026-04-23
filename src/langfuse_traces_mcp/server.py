"""FastMCP server exposing Langfuse trace-fetching tools for VS Code agent mode."""

from __future__ import annotations

import json
from typing import Optional

from fastmcp import FastMCP

try:
    from .client import LangfuseAPIError, LangfuseClient
    from .models import LangfuseCredentials, TraceFilters
except ImportError:
    from langfuse_traces_mcp.client import LangfuseAPIError, LangfuseClient
    from langfuse_traces_mcp.models import LangfuseCredentials, TraceFilters

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

mcp = FastMCP("Langfuse Trace Fetcher")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_trace_summary(trace: dict) -> str:
    """Format a single trace dict into a concise, readable text block."""
    lines: list[str] = []
    lines.append(f"### Trace: {trace.get('name', 'unnamed')}  (ID: {trace.get('id', '?')})")
    lines.append(f"- **Timestamp:** {trace.get('timestamp', 'N/A')}")

    if user_id := trace.get("userId"):
        lines.append(f"- **User ID:** {user_id}")
    if session_id := trace.get("sessionId"):
        lines.append(f"- **Session ID:** {session_id}")
    if tags := trace.get("tags"):
        lines.append(f"- **Tags:** {', '.join(tags)}")
    if version := trace.get("version"):
        lines.append(f"- **Version:** {version}")
    if release := trace.get("release"):
        lines.append(f"- **Release:** {release}")
    if environment := trace.get("environment"):
        lines.append(f"- **Environment:** {environment}")
    if metadata := trace.get("metadata"):
        lines.append(f"- **Metadata:** {json.dumps(metadata, indent=2)}")

    # Input/output (may be present on detailed trace fetches)
    if input_data := trace.get("input"):
        input_str = json.dumps(input_data, indent=2) if isinstance(input_data, (dict, list)) else str(input_data)
        lines.append(f"- **Input:**\n```json\n{input_str}\n```")
    if output_data := trace.get("output"):
        output_str = json.dumps(output_data, indent=2) if isinstance(output_data, (dict, list)) else str(output_data)
        lines.append(f"- **Output:**\n```json\n{output_str}\n```")

    return "\n".join(lines)


def _format_observations(observations: list[dict]) -> str:
    """Format a list of observations (spans/generations) into readable text."""
    if not observations:
        return "_No observations._"

    sections: list[str] = []
    for obs in observations:
        lines: list[str] = []
        obs_type = obs.get("type", "UNKNOWN")
        obs_name = obs.get("name", "unnamed")
        lines.append(f"#### {obs_type}: {obs_name}  (ID: {obs.get('id', '?')})")
        lines.append(f"- **Start:** {obs.get('startTime', 'N/A')}")
        if end_time := obs.get("endTime"):
            lines.append(f"- **End:** {end_time}")
        if model := obs.get("model"):
            lines.append(f"- **Model:** {model}")
        if usage := obs.get("usage"):
            lines.append(f"- **Usage:** {json.dumps(usage)}")
        if obs_input := obs.get("input"):
            input_str = json.dumps(obs_input, indent=2) if isinstance(obs_input, (dict, list)) else str(obs_input)
            lines.append(f"- **Input:**\n```json\n{input_str}\n```")
        if obs_output := obs.get("output"):
            output_str = json.dumps(obs_output, indent=2) if isinstance(obs_output, (dict, list)) else str(obs_output)
            lines.append(f"- **Output:**\n```json\n{output_str}\n```")
        if status_msg := obs.get("statusMessage"):
            lines.append(f"- **Status Message:** {status_msg}")
        if level := obs.get("level"):
            lines.append(f"- **Level:** {level}")

        sections.append("\n".join(lines))

    return "\n\n---\n\n".join(sections)


def _trace_matches_tags(trace: dict, required_tags: list[str]) -> bool:
    """Check whether a trace matches tags from top-level or metadata tags."""
    top_level_tags = trace.get("tags") or []
    metadata_tags = (trace.get("metadata") or {}).get("tags") or []
    merged = set(top_level_tags) | set(metadata_tags)
    return all(tag in merged for tag in required_tags)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool
async def fetch_langfuse_traces(
    public_key: str,
    secret_key: str,
    host_url: str,
    name: Optional[str] = None,
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    tags: Optional[list[str]] = None,
    version: Optional[str] = None,
    release: Optional[str] = None,
    environment: Optional[str] = None,
    from_timestamp: Optional[str] = None,
    to_timestamp: Optional[str] = None,
    limit: int = 20,
    page: int = 1,
) -> str:
    """Fetch a filtered list of traces from a Langfuse instance.

    Connects to the specified Langfuse host using the provided credentials
    and returns matching traces formatted as readable context.

    Args:
        public_key: Langfuse public API key.
        secret_key: Langfuse secret API key.
        host_url: Langfuse host URL (e.g. https://cloud.langfuse.com or http://localhost:3000).
        name: Filter by trace name.
        user_id: Filter by user ID.
        session_id: Filter by session ID.
        tags: Filter by tags (traces must have ALL specified tags).
        version: Filter by application version.
        release: Filter by release identifier.
        environment: Filter by environment (e.g. production, staging).
        from_timestamp: ISO 8601 start time — only return traces at or after this time.
        to_timestamp: ISO 8601 end time — only return traces before this time.
        limit: Max number of traces to return (1–100, default 20).
        page: Page number for pagination (default 1).

    Returns:
        Formatted text with trace summaries and pagination info.
    """
    try:
        credentials = LangfuseCredentials(
            public_key=public_key,
            secret_key=secret_key,
            host_url=host_url,
        )
        filters = TraceFilters(
            name=name,
            user_id=user_id,
            session_id=session_id,
            tags=tags,
            version=version,
            release=release,
            environment=environment,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit,
            page=page,
        )
    except Exception as e:
        return f"❌ **Validation error:** {e}"

    used_metadata_tag_fallback = False

    try:
        async with LangfuseClient(credentials) as client:
            result = await client.list_traces(filters)
            traces = result.get("data", [])

            # Fallback path: some SDK paths store tags in metadata only.
            # If API tag filtering returns no traces, re-fetch without tags
            # and filter locally against metadata.tags as well.
            if tags and not traces:
                fallback_filters = filters.model_copy(update={"tags": None})
                fallback_result = await client.list_traces(fallback_filters)
                fallback_traces = fallback_result.get("data", [])
                filtered_traces = [t for t in fallback_traces if _trace_matches_tags(t, tags)]

                result = fallback_result
                result["data"] = filtered_traces
                used_metadata_tag_fallback = True
    except LangfuseAPIError as e:
        return f"❌ **Langfuse API error ({e.status_code}):** {e.detail}"
    except Exception as e:
        return f"❌ **Connection error:** {e}"

    traces = result.get("data", [])
    meta = result.get("meta", {})

    if not traces:
        return "ℹ️ No traces matched the given filters."

    # Build output
    output_parts: list[str] = []
    output_parts.append(f"## Langfuse Traces — Page {meta.get('page', page)} of {meta.get('totalPages', '?')}")
    output_parts.append(f"_Showing {len(traces)} of {meta.get('totalItems', '?')} total traces._\n")

    # Active filters summary
    active_filters = {k: v for k, v in filters.model_dump().items() if v is not None and k not in ("limit", "page")}
    if active_filters:
        filter_strs = [f"`{k}={v}`" for k, v in active_filters.items()]
        output_parts.append(f"**Active filters:** {', '.join(filter_strs)}\n")
    if used_metadata_tag_fallback:
        output_parts.append(
            "_Note: tag matching used metadata fallback (`metadata.tags`) "
            "because API tag filtering returned no rows._\n"
        )

    for trace in traces:
        output_parts.append(_format_trace_summary(trace))
        output_parts.append("")  # blank line between traces

    return "\n".join(output_parts)


@mcp.tool
async def get_langfuse_trace_detail(
    public_key: str,
    secret_key: str,
    host_url: str,
    trace_id: str,
) -> str:
    """Fetch full detail for a single Langfuse trace by its ID.

    Returns the complete trace including input/output data, observations
    (spans, generations), scores, and metadata.

    Args:
        public_key: Langfuse public API key.
        secret_key: Langfuse secret API key.
        host_url: Langfuse host URL (e.g. https://cloud.langfuse.com or http://localhost:3000).
        trace_id: The ID of the trace to fetch.

    Returns:
        Formatted text with full trace detail.
    """
    try:
        credentials = LangfuseCredentials(
            public_key=public_key,
            secret_key=secret_key,
            host_url=host_url,
        )
    except Exception as e:
        return f"❌ **Validation error:** {e}"

    try:
        async with LangfuseClient(credentials) as client:
            trace = await client.get_trace(trace_id)
    except LangfuseAPIError as e:
        return f"❌ **Langfuse API error ({e.status_code}):** {e.detail}"
    except Exception as e:
        return f"❌ **Connection error:** {e}"

    # Build output
    output_parts: list[str] = []
    output_parts.append("## Langfuse Trace Detail\n")
    output_parts.append(_format_trace_summary(trace))

    # Observations
    observations = trace.get("observations", [])
    if observations:
        output_parts.append("\n## Observations\n")
        output_parts.append(_format_observations(observations))

    # Scores
    scores = trace.get("scores", [])
    if scores:
        output_parts.append("\n## Scores\n")
        for score in scores:
            score_name = score.get("name", "unnamed")
            score_value = score.get("value", "N/A")
            score_comment = score.get("comment")
            line = f"- **{score_name}:** {score_value}"
            if score_comment:
                line += f" — _{score_comment}_"
            output_parts.append(line)

    return "\n".join(output_parts)


@mcp.tool
async def list_langfuse_trace_filters() -> str:
    """List all available filter fields for fetching Langfuse traces.

    This is a help/reference tool — it does not make any API calls.
    Use these filter names as parameters when calling fetch_langfuse_traces.

    Returns:
        A formatted reference table of available filters.
    """
    return """## Available Filters for `fetch_langfuse_traces`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | string | — | Filter by trace name (exact match) |
| `user_id` | string | — | Filter by user ID |
| `session_id` | string | — | Filter by session ID |
| `tags` | list[string] | — | Filter by tags (traces must have ALL tags) |
| `version` | string | — | Filter by application version |
| `release` | string | — | Filter by release identifier |
| `environment` | string | — | Filter by environment (e.g. `production`, `staging`) |
| `from_timestamp` | string | — | ISO 8601 start time (inclusive) |
| `to_timestamp` | string | — | ISO 8601 end time (exclusive) |
| `limit` | int | 20 | Max traces to return (1–100) |
| `page` | int | 1 | Page number for pagination |

### Required Credentials (all tools)

| Parameter | Description |
|-----------|-------------|
| `public_key` | Langfuse public API key |
| `secret_key` | Langfuse secret API key |
| `host_url` | Langfuse instance URL (e.g. `https://cloud.langfuse.com` or `http://localhost:3000`) |

### Example Usage
```
fetch_langfuse_traces(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host_url="https://cloud.langfuse.com",
    name="my-agent-run",
    tags=["production"],
    environment="production",
    from_timestamp="2026-04-01T00:00:00Z",
    limit=10
)
```
"""


# ---------------------------------------------------------------------------
# Entry point — run via stdio for MCP
# ---------------------------------------------------------------------------

def main():
    """Entry point for running the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
