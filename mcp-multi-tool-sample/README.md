# MCP Multi-Tool Sample — Agentic AI Use Case (Zip)

This is a **minimal MCP server** exposing **multiple tools** you can wire into an agentic AI stack.
It uses **Python**, **FastMCP** (HTTP/STDIO MCP), and demonstrates how an LLM can call tools via MCP.

## Tools included
1. **get_weather** — mock weather lookup (safe for offline demos).
2. **orian_start_process** — POST a JSON workflow payload to your **Orian** (or any HTTP) endpoint.
3. **create_github_issue** — open an issue in a GitHub repo (requires a token).

## Project layout
```
mcp-multi-tool-sample/
├─ server.py                 # MCP server (HTTP + STDIO)
├─ tools/                    # Tool modules
│  ├─ __init__.py
│  ├─ weather.py             # Mock weather tool
│  ├─ orian.py               # Orian/HTTP orchestration tool
│  └─ github.py              # GitHub issue creation tool
├─ agent_demo_openai.py      # (Optional) simple agent loop using OpenAI function-calling to pick tools
├─ requirements.txt
├─ .env.sample               # Example env vars
└─ README.md
```

## Quick start

> Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.sample .env  # edit values as needed
```

### Run the MCP server (HTTP)
```bash
python server.py --http :1284
```
This starts the MCP server at `http://localhost:1284/`. You can register it with any MCP-aware client (e.g., Claude Desktop, LangGraph MCP client, etc.).

### Run the MCP server (STDIO)
```bash
# Set transport to stdio; useful for editors/LLM hosts that spawn the process.
$env:MCP_TRANSPORT="stdio"    # PowerShell
export MCP_TRANSPORT=stdio    # bash/zsh
python server.py
```

### Configure in a typical MCP client
Most MCP clients accept a **server command** and optional **transport**:
- **HTTP**: `http://localhost:1284`
- **STDIO**: `python server.py`

### Test the tools (without an MCP client)
You can call the tool functions directly to sanity-check behavior:
```bash
python -c "from tools.weather import get_weather_sync; print(get_weather_sync('Hyderabad'))"
```
or
```bash
python -c "from tools.orian import orian_start_process_sync; print(orian_start_process_sync('http://127.0.0.1:8000/admin/configure_workflow', {'workflowName':'Sample','tasks':[]}))"
```

### Agent demo using OpenAI (optional)
`agent_demo_openai.py` shows a tiny **function-calling** loop with the OpenAI API. The LLM selects a tool and the Python code **bridges to the MCP tool** by calling the same underlying Python functions. This is a simple shim so you can compare a traditional tools flow vs. MCP.

> Set `OPENAI_API_KEY` in your environment before running.

```bash
python agent_demo_openai.py
```

## Environment variables
- `GITHUB_TOKEN` — a token with `repo` scope for `create_github_issue`.
- `ORIAN_DEFAULT_ENDPOINT` — default Orian endpoint (e.g., `http://localhost:8000/admin/configure_workflow`).
- `MCP_TRANSPORT` — set to `stdio` to run via stdio; omit to run HTTP.
- `OPENAI_API_KEY` — only for the `agent_demo_openai.py` demo.

## Notes
- The **weather tool is mocked** for offline demos; replace with your preferred API if needed.
- `orian_start_process` is generic for **any HTTP JSON endpoint**. It returns the full JSON response or an error with status code.
- The MCP server name is **"multi-tools"**; you can change it in `server.py`.

Enjoy!
