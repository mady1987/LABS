import os
import json
import requests
from langchain.agents import Tool, initialize_agent, AgentType
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

try:
    # LangGraph prebuilt ReAct agent (optional)
    from langgraph.prebuilt import create_react_agent as _create_react_agent
except Exception:
    _create_react_agent = None


import os
from openai import OpenAI
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

    # llm = _TextModel(
    #     model="llama3.2:3b-instruct-q4_K_M",
    #     temperature=0.6,
    #     num_ctx=2048,
    #     num_predict=400,
    # )


    # Fetch API key from environment variable
    client = OpenAI() 

    tools = load_tools_from_mcp()
    agent = initialize_agent(
        tools=tools,
        llm=client,
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
    # Orchestrated mode: execute external workflow JSON step-by-step (no LLM decisions)
    if os.getenv("ORCHESTRATED_MODE", "0").strip() in {"1", "true", "True"}:
        from .orchestrated_runner import OrchestratedRunner
        runner = OrchestratedRunner.load_from_env()
        results = runner.run()
        # Print concise summary
        ok = all(item.get("ok") for item in results) if results else True
        print({
            "mode": "orchestrated",
            "ok": ok,
            "results": results,
        })
        return

    # Default: LLM-driven agent with MCP tools
    query = os.getenv(
        "AGENT_QUERY",
        "Trigger an alert 'Server room temp high' then create a task 'Investigate temperature spike'.",
    )

    # If a workflow file/url is provided (but not in orchestrated mode),
    # load it and include as context for the LLM to follow.
    wf_data = None
    wf_url = os.getenv("WORKFLOW_URL")
    wf_file = os.getenv("WORKFLOW_FILE")
    if wf_url or wf_file:
        try:
            if wf_url:
                r = requests.get(wf_url)
                r.raise_for_status()
                wf_data = r.json()
            elif wf_file and os.path.exists(wf_file):
                with open(wf_file, "r", encoding="utf-8") as f:
                    wf_data = json.load(f)
        except Exception as e:
            # Do not hard fail; continue without workflow context
            wf_data = None

    if wf_data is not None:
        # Provide explicit guidance for the agent on how to use tools
        wf_blob = json.dumps(wf_data, ensure_ascii=False)
        query = (
            "You are given a workflow orchestration system in JSON. "
            "Follow it step-by-step. For manual tasks, summarize the step. "
            "When automation is implied or tools are named, use the available tools exactly once per unique input.\n\n"
            f"Workflow JSON:\n{wf_blob}\n\n"
            f"User Task/Goal: {query}"
        )

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
