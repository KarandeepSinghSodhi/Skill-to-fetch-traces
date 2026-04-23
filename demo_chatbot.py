"""
Simple chatbot that logs traces to Langfuse and chats via tool calls.
This allows testing trace creation plus tool-based fetching from
langfuse-traces-mcp.
"""

import asyncio
import os
import re
import sys
import uuid
from datetime import UTC, datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Try to use Langfuse SDK to log traces
if hasattr(sys.stdout, "reconfigure"):
    # Avoid Windows cp1252 crashes on emoji/log output.
    sys.stdout.reconfigure(encoding="utf-8")

try:
    from langfuse import Langfuse
except ImportError:
    print("Installing langfuse SDK...")
    import subprocess
    subprocess.check_call(["pip", "install", "langfuse"])
    from langfuse import Langfuse

try:
    from langfuse_traces_mcp.server import (
        fetch_langfuse_traces,
        get_langfuse_trace_detail,
        list_langfuse_trace_filters,
    )
except ImportError:
    print("Installing langfuse-traces-mcp...")
    import subprocess
    subprocess.check_call(["pip", "install", "langfuse-traces-mcp"])
    from langfuse_traces_mcp.server import (
        fetch_langfuse_traces,
        get_langfuse_trace_detail,
        list_langfuse_trace_filters,
    )


def create_sample_traces():
    """Create sample traces in Langfuse for testing."""
    
    # Initialize Langfuse client
    langfuse = Langfuse(
        secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
        public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
        base_url=os.getenv("LANGFUSE_BASE_URL"),
    )
    
    print("📝 Creating sample traces in Langfuse...\n")
    
    run_id = f"demo-run-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    # Create a simple trace with observations.
    trace_id_1 = uuid.uuid4().hex
    if hasattr(langfuse, "trace"):
        trace_1 = langfuse.trace(
            id=trace_id_1,
            name="simple-chatbot",
            userId="test-user-001",
            sessionId="session-001",
            tags=["test", "chatbot"],
            metadata={"bot_version": "1.0", "environment": "test", "run_id": run_id},
            input={"message": "Hello, what's the weather today?"},
            output={"response": "I don't have access to real-time weather data, but you can check weather.com!"},
        )
        trace_1.generation(
            name="chat-response",
            model="gpt-4",
            input={"message": "Hello, what's the weather today?"},
            output={"response": "I don't have access to real-time weather data, but you can check weather.com!"},
            usage={"input": 12, "output": 20},
        )
        trace_1.span(
            name="text-processing",
            input={"raw_text": "Hello, what's the weather today?"},
            output={"processed": "weather inquiry"},
        )
    else:
        # Langfuse v4+ compatibility path (no Langfuse.trace API).
        root_1 = langfuse.start_observation(
            trace_context={"trace_id": trace_id_1},
            name="simple-chatbot",
            as_type="span",
            input={"message": "Hello, what's the weather today?"},
            output={"response": "I don't have access to real-time weather data, but you can check weather.com!"},
            metadata={
                "bot_version": "1.0",
                "environment": "test",
                "user_id": "test-user-001",
                "session_id": "session-001",
                "tags": ["test", "chatbot"],
                "run_id": run_id,
            },
        )
        root_1.end()
        gen_1 = langfuse.start_observation(
            trace_context={"trace_id": trace_id_1},
            name="chat-response",
            as_type="generation",
            model="gpt-4",
            input={"message": "Hello, what's the weather today?"},
            output={"response": "I don't have access to real-time weather data, but you can check weather.com!"},
            usage_details={"input": 12, "output": 20},
        )
        gen_1.end()
        span_1 = langfuse.start_observation(
            trace_context={"trace_id": trace_id_1},
            name="text-processing",
            as_type="span",
            input={"raw_text": "Hello, what's the weather today?"},
            output={"processed": "weather inquiry"},
        )
        span_1.end()
    
    print("✅ Trace 1 created:")
    print(f"   - Trace ID: {trace_id_1}")
    print(f"   - Name: simple-chatbot")
    print(f"   - User: test-user-001")
    print()
    
    # Create another trace
    trace_id_2 = uuid.uuid4().hex
    if hasattr(langfuse, "trace"):
        trace_2 = langfuse.trace(
            id=trace_id_2,
            name="follow-up-chatbot",
            userId="test-user-002",
            sessionId="session-002",
            tags=["test", "chatbot", "follow-up"],
            metadata={"bot_version": "1.0", "environment": "test", "run_id": run_id},
            input={"message": "Tell me a joke"},
            output={"response": "Why did the python go to the gym? To get more reps!"},
        )
        trace_2.generation(
            name="chat-response",
            model="gpt-3.5-turbo",
            input={"message": "Tell me a joke"},
            output={"response": "Why did the python go to the gym? To get more reps!"},
            usage={"input": 5, "output": 15},
        )
    else:
        root_2 = langfuse.start_observation(
            trace_context={"trace_id": trace_id_2},
            name="follow-up-chatbot",
            as_type="span",
            input={"message": "Tell me a joke"},
            output={"response": "Why did the python go to the gym? To get more reps!"},
            metadata={
                "bot_version": "1.0",
                "environment": "test",
                "user_id": "test-user-002",
                "session_id": "session-002",
                "tags": ["test", "chatbot", "follow-up"],
                "run_id": run_id,
            },
        )
        root_2.end()
        gen_2 = langfuse.start_observation(
            trace_context={"trace_id": trace_id_2},
            name="chat-response",
            as_type="generation",
            model="gpt-3.5-turbo",
            input={"message": "Tell me a joke"},
            output={"response": "Why did the python go to the gym? To get more reps!"},
            usage_details={"input": 5, "output": 15},
        )
        gen_2.end()
    
    print("✅ Trace 2 created:")
    print(f"   - Trace ID: {trace_id_2}")
    print(f"   - Name: follow-up-chatbot")
    print(f"   - User: test-user-002")
    print()
    
    # Flush to make sure all traces are sent
    langfuse.flush()
    
    print("🌐 All traces flushed to Langfuse!")
    print(f"✨ Traces created at: {datetime.now().isoformat()}")
    print("\n📊 Next, run the MCP server fetch tool to retrieve these traces.")
    
    return {
        "trace_1_id": trace_id_1,
        "trace_2_id": trace_id_2,
        "run_id": run_id,
        "public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
        "secret_key": os.getenv("LANGFUSE_SECRET_KEY"),
        "host_url": os.getenv("LANGFUSE_BASE_URL"),
    }


def _extract_name_filter(user_message: str) -> str | None:
    match = re.search(r"name\s+([a-zA-Z0-9_\-]+)", user_message.lower())
    return match.group(1) if match else None


def _extract_user_filter(user_message: str) -> str | None:
    match = re.search(r"user\s+([a-zA-Z0-9_\-]+)", user_message.lower())
    return match.group(1) if match else None


def _extract_trace_id(user_message: str, trace_info: dict[str, str]) -> str | None:
    for key in ("trace_1_id", "trace_2_id"):
        trace_id = trace_info.get(key, "")
        if trace_id and trace_id in user_message:
            return trace_id

    explicit = re.search(r"\b[a-f0-9]{32}\b", user_message.lower())
    if explicit:
        return explicit.group(0)

    explicit = re.search(r"trace[-\w]*-\d+", user_message.lower())
    if explicit:
        return explicit.group(0)
    return None


def _extract_tag_filter(user_message: str) -> list[str] | None:
    normalized = user_message.lower()
    # "tag test", "tags test chatbot", "with tag test"
    match = re.search(r"\btags?\s+([a-z0-9_\-\s,]+)", normalized)
    if not match:
        return None

    tail = match.group(1).strip()
    # Stop at likely clause separators.
    tail = re.split(r"\b(from|to|since|before|after|limit|page|name|user)\b", tail)[0].strip()
    if not tail:
        return None

    raw = re.split(r"[,\s]+", tail)
    tags = [t for t in raw if t]
    return tags or None


def _extract_limit(user_message: str, default: int = 5) -> int:
    match = re.search(r"\blimit\s+(\d+)\b", user_message.lower())
    if not match:
        return default
    return max(1, min(100, int(match.group(1))))


def _extract_time_filters(user_message: str) -> tuple[str | None, str | None]:
    from_match = re.search(r"\bfrom\s+([0-9T:\-\.Zz\+]+)", user_message, flags=re.IGNORECASE)
    to_match = re.search(r"\bto\s+([0-9T:\-\.Zz\+]+)", user_message, flags=re.IGNORECASE)
    from_ts = from_match.group(1) if from_match else None
    to_ts = to_match.group(1) if to_match else None
    if from_ts:
        from_ts = from_ts.replace("z", "Z")
    if to_ts:
        to_ts = to_ts.replace("z", "Z")
    return from_ts, to_ts


def _is_not_found_response(text: str) -> bool:
    lowered = text.lower()
    return "api error (404)" in lowered or "not found" in lowered


def _is_empty_list_response(text: str) -> bool:
    return "No traces matched the given filters." in text


async def _retry_get_trace_detail(
    *,
    public_key: str,
    secret_key: str,
    host_url: str,
    trace_id: str,
    retries: int = 6,
    delay_seconds: float = 1.5,
) -> str:
    response = ""
    for attempt in range(retries):
        response = await get_langfuse_trace_detail(
            public_key=public_key,
            secret_key=secret_key,
            host_url=host_url,
            trace_id=trace_id,
        )
        if not _is_not_found_response(response):
            return response
        if attempt < retries - 1:
            await asyncio.sleep(delay_seconds)
    return response


async def _retry_fetch_traces(
    *,
    public_key: str,
    secret_key: str,
    host_url: str,
    name: str | None,
    user_id: str | None,
    tags: list[str] | None,
    from_timestamp: str | None,
    to_timestamp: str | None,
    limit: int,
    page: int = 1,
    retries: int = 6,
    delay_seconds: float = 1.5,
) -> str:
    response = ""
    for attempt in range(retries):
        response = await fetch_langfuse_traces(
            public_key=public_key,
            secret_key=secret_key,
            host_url=host_url,
            name=name,
            user_id=user_id,
            tags=tags,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit,
            page=page,
        )
        if not _is_empty_list_response(response):
            return response
        if attempt < retries - 1:
            await asyncio.sleep(delay_seconds)
    return response


async def agent_chat_turn(user_message: str, trace_info: dict[str, str]) -> str:
    """Simple agent router that calls langfuse-traces-mcp tools."""
    public_key = trace_info["public_key"]
    secret_key = trace_info["secret_key"]
    host_url = trace_info["host_url"]

    normalized = user_message.lower().strip()

    if "filter" in normalized or "help" in normalized:
        return await list_langfuse_trace_filters()

    trace_id = _extract_trace_id(user_message, trace_info)
    if trace_id and ("detail" in normalized or "trace" in normalized or "show" in normalized):
        return await _retry_get_trace_detail(
            public_key=public_key,
            secret_key=secret_key,
            host_url=host_url,
            trace_id=trace_id,
        )

    name_filter = _extract_name_filter(user_message)
    user_filter = _extract_user_filter(user_message)
    from_timestamp, to_timestamp = _extract_time_filters(user_message)
    tags = _extract_tag_filter(user_message)
    if tags is None and "test" in normalized:
        tags = ["test"]
    limit = _extract_limit(user_message, default=5)

    filtered_response = await _retry_fetch_traces(
        public_key=public_key,
        secret_key=secret_key,
        host_url=host_url,
        name=name_filter,
        user_id=user_filter,
        tags=tags,
        from_timestamp=from_timestamp,
        to_timestamp=to_timestamp,
        limit=limit,
        page=1,
    )
    if tags and _is_empty_list_response(filtered_response):
        fallback = await _retry_fetch_traces(
            public_key=public_key,
            secret_key=secret_key,
            host_url=host_url,
            name=name_filter,
            user_id=user_filter,
            tags=None,
            from_timestamp=from_timestamp,
            to_timestamp=to_timestamp,
            limit=limit,
            page=1,
            retries=2,
            delay_seconds=1.0,
        )
        return (
            "ℹ️ Tag-filtered result was empty (common right after ingestion or when tags are only in metadata).\n"
            "Showing unfiltered latest traces instead.\n\n"
            f"{fallback}"
        )

    return filtered_response


async def run_agent_chat(trace_info: dict[str, str]) -> None:
    """Interactive chatbot that fetches responses from langfuse-traces-mcp tools."""
    print("\n" + "=" * 60)
    print("🤖 Langfuse Tool Agent Chat")
    print("=" * 60)
    print("Ask things like:")
    print("  - show traces with tag test")
    print("  - show trace detail <trace_id>")
    print("  - help filters")
    print("Type 'exit' to quit.\n")

    while True:
        user_message = input("You: ").strip()
        if user_message.lower() in {"exit", "quit"}:
            print("Agent: Goodbye!")
            return
        if not user_message:
            continue

        tool_response = await agent_chat_turn(user_message, trace_info)
        print("\nAgent (tool response):")
        print(tool_response)
        print()


def _mask_secret(secret: str | None, keep: int = 6) -> str:
    if not secret:
        return ""
    if len(secret) <= keep:
        return "*" * len(secret)
    return f"{secret[:keep]}{'*' * (len(secret) - keep)}"


if __name__ == "__main__":
    trace_info = create_sample_traces()
    
    print("\n" + "="*60)
    print("🔑 Use these credentials with the MCP server tools:")
    print("="*60)
    print(f"Public Key:  {trace_info['public_key']}")
    print(f"Secret Key:  {_mask_secret(trace_info['secret_key'])}")
    print(f"Host URL:    {trace_info['host_url']}")
    print("\n📝 Starting interactive chat agent...")
    asyncio.run(run_agent_chat(trace_info))
