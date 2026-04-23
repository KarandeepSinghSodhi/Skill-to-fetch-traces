# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-04-23

### Added
- Initial release of Langfuse Traces MCP Server
- `fetch_langfuse_traces` tool for listing traces with filtering and pagination
- `get_langfuse_trace_detail` tool for retrieving full trace details including observations and scores
- `list_langfuse_trace_filters` tool for displaying available filter options
- Comprehensive error handling for authentication and connection issues
- Rich markdown formatting for trace data display
- Support for all major Langfuse trace filters (name, user_id, session_id, tags, environment, timestamps, etc.)
- VS Code Gemini Code Assist integration via MCP protocol