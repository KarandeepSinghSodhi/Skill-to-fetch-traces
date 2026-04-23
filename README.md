# Langfuse Trace Fetcher — MCP Server for VS Code

> **Version 0.1.0** · Fetch Langfuse observability traces directly into your coding agent's context.

## What It Does

This is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that connects your VS Code coding agent (Gemini Code Assist) to a [Langfuse](https://langfuse.com) instance. It exposes three tools:

| Tool | Description |
|------|-------------|
| `fetch_langfuse_traces` | Fetch a filtered, paginated list of traces |
| `get_langfuse_trace_detail` | Fetch full detail for a single trace (including observations, scores) |
| `list_langfuse_trace_filters` | Show available filter fields and usage examples |

## Installation

### From PyPI (Recommended)

```bash
pip install langfuse-traces-mcp
```

### From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/langfuse-traces-mcp.git
cd langfuse-traces-mcp

# Install in development mode (includes test dependencies)
pip install -e ".[dev]"
```

## Prerequisites

- **Python 3.10+**
- **VS Code** with Gemini Code Assist extension (Agent Mode enabled)
- **Langfuse instance** — cloud ([cloud.langfuse.com](https://cloud.langfuse.com)) or self-hosted

## VS Code Setup

1. Install the package: `pip install langfuse-traces-mcp`

2. Add the MCP server configuration to your VS Code settings. Open VS Code settings (Ctrl/Cmd + ,) and search for "Gemini Code Assist". In the settings JSON, add:

```json
{
  "mcpServers": {
    "langfuse-traces": {
      "command": "langfuse-traces-mcp"
    }
  }
}
```

3. **Reload VS Code** after configuration.
4. Open Gemini Code Assist chat and **toggle Agent Mode ON**.
5. The `langfuse-traces` tools should now be available.

## Usage

Once configured, you can ask your coding agent questions like:

- "Show me traces from production in the last hour"
- "Get details for trace ID abc-123-xyz"
- "List traces with errors tagged as 'critical'"
- "Show me traces from user 'john.doe' in the staging environment"

The agent will fetch and display formatted trace data directly in the conversation.

## Available Filters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | string | — | Filter by trace name |
| `user_id` | string | — | Filter by user ID |
| `session_id` | string | — | Filter by session ID |
| `tags` | list | — | Filter by tags |
| `version` | string | — | Filter by app version |
| `release` | string | — | Filter by release |
| `environment` | string | — | Filter by environment |
| `from_timestamp` | string | — | ISO 8601 start time |
| `to_timestamp` | string | — | ISO 8601 end time |
| `limit` | int | 20 | Max traces (1–100) |
| `page` | int | 1 | Page number |

## Example Chat Usage

In VS Code Gemini Code Assist chat (with Agent Mode on):

```
Fetch the last 5 production traces from my Langfuse instance:
- Public key: pk-lf-abc123
- Secret key: sk-lf-xyz789
- Host: https://cloud.langfuse.com
- Environment: production
- Limit: 5
```

The agent will call `fetch_langfuse_traces` with those parameters and return formatted trace data.

## Running Tests

```bash
# Install dev dependencies (if not already)
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run a specific test file
pytest tests/test_models.py -v
pytest tests/test_client.py -v
pytest tests/test_server.py -v
```

## Project Structure

```
├── pyproject.toml                  # Project metadata & dependencies (v0.1.0)
├── README.md                       # This file
├── .gemini/
│   └── settings.json               # MCP server registration for VS Code
├── src/
│   └── langfuse_traces_mcp/
│       ├── __init__.py              # Version export
│       ├── server.py                # FastMCP server + 3 tool definitions
│       ├── client.py                # Async HTTP client for Langfuse API
│       └── models.py                # Pydantic models (filters, credentials)
└── tests/
    ├── conftest.py                  # Shared test fixtures & mock data
    ├── test_models.py               # Filter & credential validation tests
    ├── test_client.py               # REST client tests (mocked HTTP)
    └── test_server.py               # MCP tool integration tests
```

## Versioning

This project follows [Semantic Versioning 2.0](https://semver.org/):

- **PATCH** (0.1.x) — Bug fixes
- **MINOR** (0.x.0) — New filters, tools, or features
- **MAJOR** (x.0.0) — Breaking changes

## License

MIT
