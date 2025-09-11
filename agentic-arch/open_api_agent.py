from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from typing import Dict, Any, Optional, List
from openai import OpenAI
import json
import os
from langchain.agents import Tool, initialize_agent, AgentType

# Initialize FastAPI app
app = FastAPI(title="OpenAPI MCP Agent")

# Configuration
MCP_HTTP = "http://127.0.0.1:8765"
client = OpenAI()  # Make sure OPENAI_API_KEY is set in environment variables

# Request Models
class WorkflowRequest(BaseModel):
    query: str
    workflow_data: Optional[Dict[str, Any]] = None

class TaskRequest(BaseModel):
    query: str
    task_data: Optional[Dict[str, Any]] = None

# Anti-repeat guard for tool calls
_last_call = {"name": None, "arg": None}

def mcp_invoke(tool: str, inp: str) -> str:
    """
    Invoke an MCP tool with anti-repeat protection
    """
    # Prevent repeated identical tool calls
    if _last_call["name"] == tool and _last_call["arg"] == inp:
        return f"(skipped duplicate call to {tool} with same input)"
    _last_call["name"], _last_call["arg"] = tool, inp

    try:
        r = requests.post(f"{MCP_HTTP}/invoke", json={"tool": tool, "input": inp})
        r.raise_for_status()
        response = r.json()
        
        if response.get("ok"):
            return response["result"]
        return f"Error: {response.get('error')}"
    except Exception as e:
        return f"Error invoking MCP tool: {str(e)}"

def load_tools_from_mcp() -> List[Tool]:
    """
    Load available tools from MCP server
    """
    try:
        resp = requests.get(f"{MCP_HTTP}/tools")
        resp.raise_for_status()
        tools = []
        
        for name in resp.json().get("tools", []):
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load MCP tools: {str(e)}")

def create_agent():
    """
    Create a LangChain agent with MCP tools
    """

    print('Loading tools from MCP...')
    tools = load_tools_from_mcp()
    
    system_message = (
        "You are an AI assistant that helps configure workflows and complete tasks. "
        "Available tools can be used to implement the workflow and execute tasks. Rules:\n"
        "1. Analyze the user query carefully to understand the workflow or task requirements\n"
        "2. Use appropriate tools to implement the solution\n"
        "3. Use each tool only once per unique input\n"
        "4. Provide clear feedback about what was done"
    )
    # initialize the open api agent
    graph = create_react_agent(
        llm=llm,
        tools=tools,
        state_modifier="You are an API assistant. Prefer calling tools defined by the OpenAPI spec."
    )


@app.get("/configure-workflow")
async def configure_workflow():
    """
    Configure a workflow based on user query and optional workflow data
    """
    agent = create_agent()
    
    print('Preparing to configure workflow...')
    # Prepare the input for the agent
    query = "create a workflow with 2 tasks, onboarding and offboarding. Once onboarding completed offboard should be the next task" 
    
    # Convert natural language query into workflow configuration
    try:
        # First, let the LLM understand and structure the workflow
        structuring_prompt = f"""
        Convert this natural language request into a workflow configuration JSON:
        {query}
        
        The configuration should include:
        - workflow_name: Name of the workflow
        - steps: Array of workflow steps
        - triggers: What triggers this workflow
        - conditions: Any conditions for the workflow

        
        """
        
        result = agent.invoke({"input": structuring_prompt})
        print(result)
        workflow_config = result.get("output", "")
        print(workflow_config)
        # If additional workflow_data was provided, merge it with the generated config
        # if request.workflow_data:
        #     workflow_json = json.dumps(request.workflow_data, ensure_ascii=False)
        #     merging_prompt = f"""
        #     Merge these two workflow configurations into one cohesive workflow:
            
        #     Generated config:
        #     {workflow_config}
            
        #     Provided config:
        #     {workflow_json}
            
        #     Return the merged configuration as valid JSON.
        #     """
        #     result = agent.invoke({"input": merging_prompt})
        #     workflow_config = result.get("output", "")
        
        # Use the MCP tool to configure the workflow
        final_result = mcp_invoke("configure_workflow", workflow_config)
        return {"status": "success", "result": final_result, "generated_config": workflow_config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/complete-task")
async def complete_task(request: TaskRequest):
    """
    Complete a task based on user query and optional task data
    """
    agent = create_agent()
    
    # Prepare the input for the agent
    query = request.query
    if request.task_data:
        task_json = json.dumps(request.task_data, ensure_ascii=False)
        query = f"{query}\nTask data:\n{task_json}"
    
    try:
        result = agent.invoke({"input": query})
        return {"status": "success", "result": result.get("output", "")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        # Check MCP server connectivity
        requests.get(f"{MCP_HTTP}/tools").raise_for_status()
        return {"status": "healthy", "mcp_connection": "ok"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🚀 OpenAPI MCP Agent starting on http://127.0.0.1:8001")
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
