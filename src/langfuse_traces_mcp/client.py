"""Async HTTP client for the Langfuse public REST API."""

from __future__ import annotations

import httpx

from .models import LangfuseCredentials, TraceFilters


class LangfuseAPIError(Exception):
    """Raised when the Langfuse API returns an unexpected response."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Langfuse API error {status_code}: {detail}")


class LangfuseClient:
    """Lightweight async client for Langfuse trace endpoints.

    Uses HTTP Basic Auth (public_key as username, secret_key as password)
    and communicates with Langfuse's public REST API.
    """

    TRACES_ENDPOINT = "/api/public/traces"
    DEFAULT_TIMEOUT = 30.0  # seconds

    def __init__(self, credentials: LangfuseCredentials) -> None:
        self._base_url = credentials.host_url
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            auth=(credentials.public_key, credentials.secret_key),
            timeout=self.DEFAULT_TIMEOUT,
            headers={
                "Accept": "application/json",
                "User-Agent": "langfuse-traces-mcp/0.1.0",
            },
        )

    async def list_traces(self, filters: TraceFilters | None = None) -> dict:
        """Fetch a paginated list of traces from Langfuse.

        Args:
            filters: Optional trace filters. Uses defaults if not provided.

        Returns:
            Raw JSON response dict with 'data' (list of traces) and 'meta'
            (pagination info).

        Raises:
            LangfuseAPIError: If the API returns a non-2xx status.
            httpx.TimeoutException: If the request times out.
        """
        if filters is None:
            filters = TraceFilters()

        params = filters.to_query_params()
        response = await self._client.get(self.TRACES_ENDPOINT, params=params)
        self._raise_for_status(response)
        return response.json()

    async def get_trace(self, trace_id: str) -> dict:
        """Fetch full detail for a single trace by ID.

        Args:
            trace_id: The Langfuse trace ID.

        Returns:
            Raw JSON response dict with full trace data including
            observations, scores, and metadata.

        Raises:
            LangfuseAPIError: If the API returns a non-2xx status.
            httpx.TimeoutException: If the request times out.
        """
        url = f"{self.TRACES_ENDPOINT}/{trace_id}"
        response = await self._client.get(url)
        self._raise_for_status(response)
        return response.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> LangfuseClient:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        """Raise LangfuseAPIError for non-2xx responses with a helpful message."""
        if response.is_success:
            return

        # Try to extract a useful error message from the response body
        try:
            body = response.json()
            detail = body.get("message") or body.get("error") or str(body)
        except Exception:
            detail = response.text[:500] if response.text else "No response body"

        raise LangfuseAPIError(
            status_code=response.status_code,
            detail=detail,
        )
