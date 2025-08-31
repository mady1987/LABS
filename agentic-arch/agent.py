import os
import requests
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
try:
    # Prefer chat model for LangGraph
    from langchain_ollama import ChatOllama as _ChatModel
except Exception:
    _ChatModel = None
try:
    # Fallback text LLM for legacy LangChain agent path
    from langchain_ollama import OllamaLLM as _TextModel
except Exception:
    _TextModel = None
try:
    # LangGraph prebuilt ReAct agent (optional)
    from langgraph.prebuilt import create_react_agent as _create_react_agent
except Exception:
    _create_react_agent = None

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

def _run_with_langgraph(query: str) -> str:
    if _create_react_agent is None or _ChatModel is None:
        raise RuntimeError("LangGraph or ChatOllama not available")

    model = _ChatModel(
        model="llama3.2:3b-instruct-q4_K_M",
        temperature=0.6,
        num_ctx=2048,
        num_predict=400,
    )

    tools = load_tools_from_mcp()
    app = _create_react_agent(model, tools)

    res = app.invoke({
        "messages": [
            SystemMessage(content=SYSTEM_RULES),
            HumanMessage(content=query),
        ]
    })
    msgs = res.get("messages", [])
    # Grab the last AI response
    for m in reversed(msgs):
        if isinstance(m, AIMessage):
            return m.content or ""
    # Fallback to stringifying last message
    return str(msgs[-1].content) if msgs else ""


def _run_with_langchain_agent(query: str) -> str:
    if _TextModel is None:
        raise RuntimeError("Ollama text model not available for legacy agent path")

    llm = _TextModel(
        model="llama3.2:3b-instruct-q4_K_M",
        temperature=0.6,
        num_ctx=2048,
        num_predict=400,
    )

    tools = load_tools_from_mcp()
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=4,
        early_stopping_method="generate",
        agent_kwargs={"system_message": SYSTEM_RULES},
    )
    result = agent.invoke({"input": query})
    return result.get("output", "")


def main():
    query = "Trigger an alert 'Server room temp high' then create a task 'Investigate temperature spike'."

    use_langgraph = os.getenv("USE_LANGGRAPH", "1").strip() not in {"0", "false", "False"}
    try:
        if use_langgraph:
            output = _run_with_langgraph(query)
        else:
            output = _run_with_langchain_agent(query)
    except Exception as e:
        # Fallback: if LangGraph path fails, try legacy agent once
        if use_langgraph:
            try:
                output = _run_with_langchain_agent(query)
            except Exception:
                raise e
        else:
            raise e
    print(output)

if __name__ == "__main__":
    main()
