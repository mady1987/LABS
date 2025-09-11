import os
import argparse
from fastmcp import FastMCP, tool
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load env
load_dotenv()

# Create the MCP app
app = FastMCP(
    name="multi-tools",
    version="0.1.0",
    description="Sample MCP server exposing multiple tools for agentic AI demos."
)

# ----- Tool Schemas -----
class WeatherInput(BaseModel):
    city: str = Field(..., description="City name to look up weather for.")

class OrchestrationInput(BaseModel):
    endpoint: str = Field(..., description="HTTP endpoint to POST the workflow payload to.")
    payload: dict = Field(..., description="Arbitrary JSON payload to send.")

class GitHubIssueInput(BaseModel):
    repo: str = Field(..., description="org/repo, e.g. 'owner/name'.")
    title: str
    body: str = ""
    token_env: str = Field("GITHUB_TOKEN", description="Environment variable that contains the token.")

# ----- Tools -----
from tools.weather import get_weather_async
from tools.orian import orian_start_process_async, get_default_orian_endpoint
from tools.github import create_issue_async

@tool
async def get_weather(input: WeatherInput):
    """Return a mock weather reading (replace with a real provider if desired)."""
    return await get_weather_async(input.city)

@tool
async def orian_start_process(input: OrchestrationInput):
    """POST a JSON workflow payload to an Orian (or generic HTTP) endpoint."""
    return await orian_start_process_async(input.endpoint, input.payload)

@tool
async def create_github_issue(input: GitHubIssueInput):
    """Open a GitHub issue in the given repo using a personal access token."""
    return await create_issue_async(input.repo, input.title, input.body, input.token_env)

def main():
    parser = argparse.ArgumentParser(description="MCP Multi-Tool Server")
    parser.add_argument("--http", help="Bind as HTTP MCP server, e.g. ':1284' or '0.0.0.0:1284'")
    args = parser.parse_args()

    # Prefer explicit transport
    if args.http:
        host, port = "127.0.0.1", 1284
        if ":" in args.http:
            host, port_str = args.http.split(":", 1)
            host = host or "0.0.0.0"
            port = int(port_str)
        print(f"Starting MCP HTTP server on http://{host}:{port}")
        app.run_http(host=host, port=port)
        return

    transport = os.getenv("MCP_TRANSPORT", "").lower()
    if transport == "stdio":
        print("Starting MCP STDIO server...")
        app.run_stdio()
    else:
        # Default to HTTP on 127.0.0.1:1284
        print("Starting MCP HTTP server on http://127.0.0.1:1284")
        app.run_http(host="127.0.0.1", port=1284)

if __name__ == "__main__":
    main()
