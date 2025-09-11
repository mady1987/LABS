import os
import json
from typing import Any, Dict, List
from dotenv import load_dotenv
from openai import OpenAI

# Local tool implementations (same ones the MCP server exposes)
from tools.weather import get_weather_sync
from tools.orian import orian_start_process_sync, get_default_orian_endpoint
from tools.github import create_issue_sync

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define function/tool specs for OpenAI
functions = [
    {
        "name": "get_weather",
        "description": "Return a mock weather reading for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string"}
            },
            "required": ["city"]
        }
    },
    {
        "name": "orian_start_process",
        "description": "POST a JSON payload to an Orian (or generic HTTP) endpoint.",
        "parameters": {
            "type": "object",
            "properties": {
                "endpoint": {"type": "string", "description": "HTTP endpoint to POST to."},
                "payload": {"type": "object"}
            },
            "required": ["endpoint", "payload"]
        }
    },
    {
        "name": "create_github_issue",
        "description": "Create a GitHub issue in the given repository.",
        "parameters": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "org/repo"},
                "title": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["repo", "title"]
        }
    }
]

def call_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name == "get_weather":
        return get_weather_sync(args["city"])
    if name == "orian_start_process":
        return orian_start_process_sync(args["endpoint"], args["payload"])
    if name == "create_github_issue":
        return create_issue_sync(args["repo"], args["title"], args.get("body",""))
    return {"error": f"Unknown tool {name}"}

def run_agentic_dialog(prompt: str) -> Dict[str, Any]:
    # Single-turn demo with function calling
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that may call tools when useful."},
            {"role": "user", "content": prompt},
        ],
        tools=[{"type":"function", "function": f} for f in functions],
        tool_choice="auto",
        temperature=0.2
    )

    msg = resp.choices[0].message
    if msg.tool_calls:
        # Execute the first tool call (demo)
        tc = msg.tool_calls[0]
        tool_name = tc.function.name
        tool_args = json.loads(tc.function.arguments or "{}")
        result = call_tool(tool_name, tool_args)

        # Return tool result to the model for a final answer
        follow = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that may call tools when useful."},
                {"role": "user", "content": prompt},
                {"role": "tool", "tool_call_id": tc.id, "name": tool_name, "content": json.dumps(result)}
            ],
            temperature=0.2
        )
        return {"tool": tool_name, "args": tool_args, "result": result, "final": follow.choices[0].message.content}
    else:
        return {"final": msg.content}

if __name__ == "__main__":
    # Example prompts:
    examples = [
        "What's the weather in Hyderabad?",
        "Trigger the onboarding workflow in Orian with process name 'Sample' and no tasks.",
        "Create a GitHub issue in owner/repo titled 'Bug: login 500' with body 'Stacktrace attached.'"
    ]
    for p in examples:
        print(f"\n### Prompt: {p}")
        out = run_agentic_dialog(p)
        print(json.dumps(out, indent=2))
