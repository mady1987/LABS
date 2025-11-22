import os
import json
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
load_dotenv()

import httpx
from pydantic import BaseModel, Field, ValidationError

from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# -----------------------------
# LLM
# -----------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",   # swap to "gpt-4o" for higher quality
    temperature=0.2,
)

# -----------------------------
# Shared HTTP client(s)
# -----------------------------
ORIAN_BASE = os.getenv("ORIAN_BASE_URL", "http://localhost:8080").rstrip("/")
ORIAN_TOKEN = os.getenv("ORIAN_AUTH_TOKEN", "")

GH_TOKEN = os.getenv("GITHUB_TOKEN", "")
GH_OWNER = os.getenv("GITHUB_OWNER", "")
GH_REPO  = os.getenv("GITHUB_REPO", "")

ori_headers = {"Authorization": f"Bearer {ORIAN_TOKEN}"} if ORIAN_TOKEN else {}
gh_headers  = {"Authorization": f"Bearer {GH_TOKEN}",
               "Accept": "application/vnd.github+json"} if GH_TOKEN else {}

http_timeout = httpx.Timeout(30.0)

# -----------------------------
# Tool Schemas (Pydantic)
# -----------------------------
class GetProcessInstanceInput(BaseModel):
    """Fetch an Orian process instance and its current tasks."""
    instance_id: int = Field(..., description="Orian process instance id")

class CompleteTaskInput(BaseModel):
    """Complete an Orian task instance with an outcome string."""
    task_instance_id: int = Field(..., description="Orian task_instance id")
    outcome: str = Field(..., description="Outcome label, e.g., 'SUCCESS' or 'RETRY' or 'ESCALATE'")

class CreateGithubIssueInput(BaseModel):
    """Create a GitHub issue in the configured repo."""
    title: str = Field(..., description="Issue title")
    body: Optional[str] = Field("", description="Issue description")
    labels: Optional[List[str]] = Field(default_factory=list, description="Optional labels")

# -----------------------------
# Orian Tools
# -----------------------------
@tool("orian_get_instance", args_schema=GetProcessInstanceInput)
def orian_get_instance(instance_id: int) -> Dict[str, Any]:
    """
    Get Orian process instance (state + active tasks).
    The agent can use this to understand which task(s) are currently active.
    """
    if not ORIAN_BASE:
        return {"error": "ORIAN_BASE_URL not set"}

    url = f"{ORIAN_BASE}/instances/{instance_id}"
    try:
        with httpx.Client(timeout=http_timeout) as client:
            r = client.get(url, headers=ori_headers)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        return {"error": f"HTTP error calling Orian: {e}", "url": url}

@tool("orian_complete_task", args_schema=CompleteTaskInput)
def orian_complete_task(task_instance_id: int, outcome: str) -> Dict[str, Any]:
    """
    Complete a specific Orian task instance by posting an outcome.
    Returns the updated instance/task state from Orian.
    """
    if not ORIAN_BASE:
        return {"error": "ORIAN_BASE_URL not set"}

    url = f"{ORIAN_BASE}/tasks/{task_instance_id}/complete"
    payload = {"outcome": outcome}
    try:
        with httpx.Client(timeout=http_timeout) as client:
            r = client.post(url, json=payload, headers=ori_headers)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        return {"error": f"HTTP error completing task: {e}", "url": url, "payload": payload}

# -----------------------------
# GitHub Tool
# -----------------------------
@tool("github_create_issue", args_schema=CreateGithubIssueInput)
def github_create_issue(title: str, body: str = "", labels: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Create an issue in the configured GitHub repository.
    Requires GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO.
    """
    if not (GH_TOKEN and GH_OWNER and GH_REPO):
        return {"error": "GitHub env vars missing: GITHUB_TOKEN / GITHUB_OWNER / GITHUB_REPO"}

    url = f"https://api.github.com/repos/{GH_OWNER}/{GH_REPO}/issues"
    payload = {"title": title, "body": body}
    if labels:
        payload["labels"] = labels
    try:
        with httpx.Client(timeout=http_timeout) as client:
            r = client.post(url, headers=gh_headers, json=payload)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPError as e:
        return {"error": f"HTTP error creating GitHub issue: {e}", "url": url, "payload": payload}

# -----------------------------
# Build LangGraph ReAct Agent
# -----------------------------
tools = [orian_get_instance, orian_complete_task, github_create_issue]

app = create_react_agent(
    llm=llm,
    tools=tools,
    # Optional: you can pass 'state_modifier' to pin system instructions
    state_modifier="You are a pragmatic assistant that manages Orian workflows and files GitHub issues when needed."
)

# -----------------------------
# Example runs
# -----------------------------
def run_examples():
    # 1) Inspect an Orian instance
    messages = [
        ("user", "Check Orian process instance 1 and tell me which tasks are active.")
    ]
    res = app.invoke({"messages": messages})
    print("\n--- Agent Response (inspect instance) ---\n")
    print(res["messages"][-1].content)

    # 2) Complete a task and then create a GH issue
    # NOTE: Adjust IDs/outcomes to real ones in your Orian.
    messages2 = [
        ("user", "Complete task_instance_id=42 with outcome=SUCCESS, then create a GitHub issue titled 'Onboarding finished' with a short summary.")
    ]
    res2 = app.invoke({"messages": messages2})
    print("\n--- Agent Response (complete + GH issue) ---\n")
    print(res2["messages"][-1].content)

if __name__ == "__main__":
    run_examples()
