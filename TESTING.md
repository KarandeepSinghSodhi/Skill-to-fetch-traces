## 🧪 Live Testing Setup

This directory contains scripts to test the Langfuse Traces MCP Server with real Langfuse data.

### Files

- **`.env.local`** - Your Langfuse API credentials (keep private!)
- **`demo_chatbot.py`** - Simple chatbot that creates sample traces in Langfuse
- **`test_live.py`** - Tests the MCP server tools by fetching those traces

### Quick Start

#### 1️⃣ Create Sample Traces

```bash
python demo_chatbot.py
```

This will:
- Connect to your Langfuse instance
- Create 2 sample traces with observations (generations and spans)
- Display trace IDs for verification

#### 2️⃣ Fetch Traces with MCP Server Tools

```bash
python test_live.py
```

This will:
- List available trace filters
- Fetch traces with the 'test' tag
- Fetch traces by name
- Get full details of a specific trace

### What Gets Created

The `demo_chatbot.py` script creates:

**Trace 1: simple-chatbot**
- User ID: test-user-001
- Session ID: session-001
- Tags: test, chatbot
- Contains: 1 generation (LLM call) + 1 span (text processing)

**Trace 2: follow-up-chatbot**
- User ID: test-user-002
- Session ID: session-002
- Tags: test, chatbot, follow-up
- Contains: 1 generation (LLM call)

### Verify in Langfuse UI

1. Go to https://us.cloud.langfuse.com
2. Sign in with your account
3. Navigate to **Traces** to see the created traces
4. Click on a trace to see its observations and details

### Using with VS Code

You can also test directly in VS Code Gemini Code Assist:

1. Ensure the MCP server is configured
2. Ask: "Show me traces with tag 'test'"
3. Ask: "Get details for the simple-chatbot trace"
4. Ask: "List all traces from test-user-001"

### Security

- `.env.local` is in `.gitignore` and won't be committed
- Never share your API keys
- Regenerate keys if they're exposed
