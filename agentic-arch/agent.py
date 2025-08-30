from langchain.agents import Tool, initialize_agent, AgentType
from langchain_community.llms import Ollama
import requests

MCP_HTTP = "http://127.0.0.1:8765"

# ---- Anti-repeat guard ------------------------------------------------------
_last_call = {"name": None, "arg": None}

def mcp_invoke(tool: str, inp: str) -> str:
    # prevent repeated identical tool calls
    if _last_call["name"] == tool and _last_call["arg"] == inp:
        return f"(skipped duplicate call to {tool} with same input)"
    _last_call["name"], _last_call["arg"] = tool, inp

    r = requests.post(f"{MCP_HTTP}/invoke", json={"tool": tool, "input": inp})
    try:
        j = r.json()
    except Exception:
        return f"Error: MCP bridge returned non-JSON: {r.text}"
    if j.get("ok"):
        return j["result"]
    return f"Error: {j.get('error')}"

def load_tools_from_mcp():
    resp = requests.get(f"{MCP_HTTP}/tools").json()
    tools = []
    for name in resp.get("tools", []):
        tools.append(
            Tool(
                name=name,
                func=lambda arg, _name=name: mcp_invoke(_name, arg),
                description=(
                    f"Remote MCP tool '{name}'. Call at most once per unique input. "
                    "Return value is final; do not re-call with the same arguments."
                ),
            )
        )
    return tools

SYSTEM_RULES = (
    "You may call tools to complete the task. Rules: "
    "1) Use a tool ONLY if needed and ONLY ONCE per unique input. "
    "2) If the observation answers the task, STOP and produce the final answer. "
    "3) Do not repeat the same tool with the same arguments. "
    "4) If a tool fails twice or returns an error, explain the failure and stop."
)

def main():
    llm = Ollama(model="llama3.1")
    tools = load_tools_from_mcp()

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=4,                     # hard stop to avoid loops
        early_stopping_method="generate",     # produce best answer on stop
        agent_kwargs={"system_message": SYSTEM_RULES},
    )

    query = "Trigger an alert 'Server room temp high' then create a task 'Investigate temperature spike'."
    result = agent.run(query)
    print("\nFinal Result:\n", result)

if __name__ == "__main__":
    main()
