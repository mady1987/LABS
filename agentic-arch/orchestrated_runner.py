import json
import os
from typing import Any, Dict, List, Optional

import requests

# Local tool implementations
from .tools import common_tools


class OrchestratedRunner:
    """
    Executes a workflow defined in JSON, step-by-step, without LLM planning.

    JSON schema (minimal):
    {
      "steps": [
        {"tool": "trigger_alert", "input": "..."},
        {"tool": "create_task", "input": "..."}
      ]
    }

    Configuration:
    - WORKFLOW_URL: if set, fetch JSON from URL.
    - WORKFLOW_FILE: if set, read JSON from local file.
    If both set, WORKFLOW_URL takes precedence.
    """

    def __init__(self, workflow: Dict[str, Any]):
        self.workflow = workflow
        self.results: List[Dict[str, Any]] = []

        # Map tool names to callables
        self.tool_map = {
            "trigger_alert": common_tools.trigger_alert,
            "create_task": common_tools.create_task,
        }

    @staticmethod
    def _normalize_to_steps(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Accept either the simple {"steps": [{tool,input}, ...]} schema or a
        richer workflow schema containing tasks/contexts and convert it into
        a {"steps": [...]} payload OrchestratedRunner understands.

        Supported alt schema (example):
        {
          "workflowName": "...",
          "contexts": [...],
          "tasks": [
            {"name": "...", "description": "...", "taskType": "MANUAL", "sequence": 1},
            ...
          ],
          "initialContext": { ... }
        }
        """
        if isinstance(data, dict) and isinstance(data.get("steps"), list):
            return {"steps": data["steps"]}

        # Attempt to convert a tasks-based workflow into actionable steps
        steps: List[Dict[str, Any]] = []

        wf_name = data.get("workflowName") or data.get("name") or "Workflow"
        init_ctx = data.get("initialContext") or {}
        requester = init_ctx.get("REQUESTER") or init_ctx.get("requester")

        # Optional: Trigger a starting alert if we have a requester
        if requester:
            steps.append({
                "tool": "trigger_alert",
                "input": f"Starting {wf_name} for {requester}",
            })

        tasks = data.get("tasks") or []
        if isinstance(tasks, list) and tasks:
            # Sort by sequence if present
            def _seq(x: Dict[str, Any]) -> Any:
                return x.get("sequence", 0)

            for t in sorted(tasks, key=_seq):
                tname = (t.get("name") or "").strip()
                tdesc = (t.get("description") or "").strip()

                # Future: if tasks declare explicit automation, honor it.
                automation = t.get("automation") if isinstance(t, dict) else None
                if isinstance(automation, dict) and automation.get("tool"):
                    steps.append({
                        "tool": str(automation.get("tool")),
                        "input": str(automation.get("input", tdesc or tname)),
                    })
                else:
                    # Default behavior: create a task entry for manual steps
                    label = f"{tname}: {tdesc}" if tdesc else tname or "Unnamed Task"
                    steps.append({
                        "tool": "create_task",
                        "input": label,
                    })

        if not steps:
            raise ValueError("Invalid workflow JSON: expected 'steps' or non-empty 'tasks'")

        return {"steps": steps}

    @staticmethod
    def load_from_env() -> "OrchestratedRunner":
        url = os.getenv("WORKFLOW_URL")
        file_path = os.getenv("WORKFLOW_FILE")

        data: Optional[Dict[str, Any]] = None

        if url:
            r = requests.get(url)
            r.raise_for_status()
            data = r.json()
        elif file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            raise RuntimeError("No workflow source provided. Set WORKFLOW_URL or WORKFLOW_FILE.")

        if not isinstance(data, dict):
            raise ValueError("Invalid workflow JSON: expected an object")

        normalized = OrchestratedRunner._normalize_to_steps(data)
        return OrchestratedRunner(workflow=normalized)

    def run(self) -> List[Dict[str, Any]]:
        steps = self.workflow.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError("workflow.steps must be a list")

        for idx, step in enumerate(steps, start=1):
            tool_name = (step.get("tool") or "").strip()
            inp = step.get("input")
            if not tool_name:
                self.results.append({
                    "step": idx,
                    "ok": False,
                    "error": "Missing tool name",
                })
                break

            func = self.tool_map.get(tool_name)

            try:
                # Tools here accept a single string input
                arg = "" if inp is None else str(inp)

                if func is not None:
                    out = func(arg)
                else:
                    # Fallback: try calling local MCP HTTP bridge by tool name
                    mcp_base = os.getenv("MCP_HTTP", "http://127.0.0.1:8765").rstrip("/")
                    r = requests.post(f"{mcp_base}/invoke", json={"tool": tool_name, "input": arg})
                    jr = r.json()
                    if not jr.get("ok"):
                        raise RuntimeError(jr.get("error") or f"MCP call to {tool_name} failed")
                    out = jr.get("result")
                self.results.append({
                    "step": idx,
                    "tool": tool_name,
                    "input": arg,
                    "ok": True,
                    "output": out,
                })
            except Exception as e:
                self.results.append({
                    "step": idx,
                    "tool": tool_name,
                    "input": inp,
                    "ok": False,
                    "error": str(e),
                })
                break

        return self.results


def main() -> None:
    runner = OrchestratedRunner.load_from_env()
    res = runner.run()
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
