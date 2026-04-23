"""
Test script to fetch traces from Langfuse using the MCP server tools.
This demonstrates the tool working with real Langfuse data.
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

# Add src to path
sys.path.insert(0, str(__file__).replace("test_live.py", "src"))

from langfuse_traces_mcp.server import (
    fetch_langfuse_traces,
    get_langfuse_trace_detail,
    list_langfuse_trace_filters,
)


async def test_tools():
    """Test the MCP server tools with real Langfuse data."""
    
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host_url = os.getenv("LANGFUSE_BASE_URL")
    
    print("🚀 Testing Langfuse Traces MCP Server Tools\n")
    print("=" * 70)
    
    # Test 1: List available filters
    print("\n📋 Test 1: List Available Filters")
    print("-" * 70)
    filters_result = await list_langfuse_trace_filters()
    print(filters_result[:500] + "...\n")
    
    # Test 2: Fetch traces with 'test' tag
    print("\n📊 Test 2: Fetch Traces with 'test' Tag")
    print("-" * 70)
    fetch_result = await fetch_langfuse_traces(
        public_key=public_key,
        secret_key=secret_key,
        host_url=host_url,
        tags=["test"],
        limit=10,
    )
    print(fetch_result)
    
    # Test 3: Fetch traces with chatbot name
    print("\n🤖 Test 3: Fetch 'simple-chatbot' Traces")
    print("-" * 70)
    chatbot_result = await fetch_langfuse_traces(
        public_key=public_key,
        secret_key=secret_key,
        host_url=host_url,
        name="simple-chatbot",
        limit=5,
    )
    print(chatbot_result)
    
    # Test 4: Get detail of a specific trace (if any exist)
    print("\n🔍 Test 4: Fetch Trace Details")
    print("-" * 70)
    print("Looking for a trace to fetch details...")
    
    # Try to get the first trace found
    list_result = await fetch_langfuse_traces(
        public_key=public_key,
        secret_key=secret_key,
        host_url=host_url,
        limit=1,
    )
    
    # Extract trace ID from the result if available
    if "ID:" in list_result:
        # Simple extraction - find the trace ID
        import re
        trace_id_match = re.search(r"ID: (\S+)\)", list_result)
        if trace_id_match:
            trace_id = trace_id_match.group(1)
            print(f"\n✅ Found trace: {trace_id}")
            print("Fetching full details...\n")
            
            detail_result = await get_langfuse_trace_detail(
                public_key=public_key,
                secret_key=secret_key,
                host_url=host_url,
                trace_id=trace_id,
            )
            print(detail_result)
        else:
            print("Could not extract trace ID from results")
    else:
        print("No traces found yet. Run demo_chatbot.py first to create traces!")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_tools())
