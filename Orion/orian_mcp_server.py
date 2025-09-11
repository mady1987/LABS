"""
Orian MCP Server (Python SDK)

Implements MCP tools that let an LLM configure and run Orian workflows
using a strict JSON schema. Designed to run over stdio (JSON‑RPC),
so it can be used as a sidecar MCP server.

Environment variables:
  ORIAN_BASE_URL   e.g. https://orian.mycorp.internal
  ORIAN_API_KEY    bearer/API key if required by your gateway

Run (stdio):
  python orian_mcp_server.py

NOTE: Depending on your MCP SDK version, import paths may differ slightly.
This sample uses the canonical "mcp" Python SDK layout.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any, Dict, Optional, List

import requests
from requests import Response

# === MCP SDK imports (adjust to the SDK version you use) ===
try:
    from mcp.server import Server, Tool
    from mcp.server.stdio import stdio_transport
except Exception as e:  # pragma: no cover
    print("[WARN] Could not import MCP SDK. Make sure 'mcp' package is installed.", file=sys.stderr)
    raise

# === Optional: JSON Schema validation (strong guardrails for LLM) ===
try:
    from jsonschema import validate, Draft7Validator
except Exception:
    validate = None
    Draft7Validator = None


ORIAN_WORKFLOW_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "OrianWorkflowConfig",
    "description": "Schema for configuring and triggering an Orian workflow",
    "type": "object",
    "properties": {
        "workflowName": {"type": "string", "description": "Unique name of the workflow"},
        "description": {"type": "string"},
        "app": {"type": "string"},
        "contexts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "description": {"type": "string"},
                    "dataType": {
                        "type": "string",
                        "enum": ["STRING", "NUMBER", "BOOLEAN", "DATE", "OBJECT"],
                    },
                },
                "required": ["key", "dataType"],
            },
        },
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "taskType": {"type": "string", "enum": ["MANUAL", "AUTOMATED"]},
                    "assignmentType": {"type": "string", "enum": ["USER", "GROUP", "SYSTEM"]},
                    "sequence": {"type": "integer", "minimum": 1},
                    "outcomes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "nextTask": {"type": ["string", "null"]},
                            },
                            "required": ["name"],
                        },
                    },
                },
                "required": ["name", "taskType", "assignmentType", "sequence"],
            },
        },
        "startInstance": {"type": "boolean"},
        "initialContext": {
            "type": "object",
            "additionalProperties": {"type": ["string", "number", "boolean", "null"]},
        },
    },
    "required": ["workflowName", "tasks", "startInstance"],
}


# === Utility: HTTP helpers ===
class OrianClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def create_or_update_workflow(self, payload: Dict[str, Any]) -> Response:
        url = f"{self.base_url}/workflows"  # adjust to your Orian route
        return requests.post(url, headers=self._headers(), data=json.dumps(payload), timeout=30)

    def start_instance(self, workflow_name: str, initial_context: Optional[Dict[str, Any]] = None) -> Response:
        url = f"{self.base_url}/instances"
        body = {"workflowName": workflow_name, "initialContext": initial_context or {}}
        return requests.post(url, headers=self._headers(), data=json.dumps(body), timeout=30)

    def complete_task(self, instance_id: str, task_name: str, outcome: str, context_updates: Optional[Dict[str, Any]] = None) -> Response:
        url = f"{self.base_url}/instances/{instance_id}/tasks/{task_name}:complete"
        body = {"outcome": outcome, "context": context_updates or {}}
        return requests.post(url, headers=self._headers(), data=json.dumps(body), timeout=30)

    def complete_workflow(self, instance_id: str) -> Response:
        url = f"{self.base_url}/instances/{instance_id}:complete"
        return requests.post(url, headers=self._headers(), timeout=30)


# === MCP Server setup ===
server = Server("orian-mcp")


def _env_or_fail(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return val


def _validate_schema(schema: Dict[str, Any], data: Dict[str, Any]) -> None:
    if Draft7Validator is None:
        return
    Draft7Validator(schema).validate(data)


# === Tool: create_orian_workflow ===
@server.tool(
    Tool(
        name="create_orian_workflow",
        description=(
            "Configure (and optionally start) an Orian workflow. "
            "If startInstance=true, also creates a workflow instance."
        ),
        input_schema=ORIAN_WORKFLOW_SCHEMA,
    )
)
def create_orian_workflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Create or update a workflow definition in Orian, and optionally start it."""
    try:
        _validate_schema(ORIAN_WORKFLOW_SCHEMA, payload)
        base_url = _env_or_fail("ORIAN_BASE_URL")
        api_key = os.getenv("ORIAN_API_KEY")
        client = OrianClient(base_url, api_key)

        # 1) Create/Update workflow
        resp = client.create_or_update_workflow(payload)
        if not resp.ok:
            return {
                "ok": False,
                "step": "create_or_update_workflow",
                "status": resp.status_code,
                "error": safe_text(resp),
            }
        result: Dict[str, Any] = {
            "ok": True,
            "workflow": resp.json() if _is_json(resp) else resp.text,
        }

        # 2) Optionally start instance
        if payload.get("startInstance"):
            wf_name = payload["workflowName"]
            init_ctx = payload.get("initialContext", {})
            start_resp = client.start_instance(wf_name, init_ctx)
            if not start_resp.ok:
                result.update({
                    "instanceStart": {
                        "ok": False,
                        "status": start_resp.status_code,
                        "error": safe_text(start_resp),
                    }
                })
            else:
                result.update({
                    "instanceStart": {
                        "ok": True,
                        "instance": start_resp.json() if _is_json(start_resp) else start_resp.text,
                    }
                })

        return result

    except Exception as e:  # capture stack for the LLM
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


# === Tool: complete_orian_task ===
COMPLETE_TASK_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "instanceId": {"type": "string"},
        "taskName": {"type": "string"},
        "outcome": {"type": "string"},
        "contextUpdates": {
            "type": "object",
            "additionalProperties": {"type": ["string", "number", "boolean", "null"]},
        },
    },
    "required": ["instanceId", "taskName", "outcome"],
}


@server.tool(
    Tool(
        name="complete_orian_task",
        description="Complete a task in an Orian workflow instance with an outcome and optional context updates.",
        input_schema=COMPLETE_TASK_SCHEMA,
    )
)
def complete_orian_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if Draft7Validator is not None:
            Draft7Validator(COMPLETE_TASK_SCHEMA).validate(payload)
        base_url = _env_or_fail("ORIAN_BASE_URL")
        api_key = os.getenv("ORIAN_API_KEY")
        client = OrianClient(base_url, api_key)
        r = client.complete_task(
            instance_id=payload["instanceId"],
            task_name=payload["taskName"],
            outcome=payload["outcome"],
            context_updates=payload.get("contextUpdates"),
        )
        if not r.ok:
            return {"ok": False, "status": r.status_code, "error": safe_text(r)}
        return {"ok": True, "result": r.json() if _is_json(r) else r.text}
    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


# === Tool: complete_orian_workflow ===
COMPLETE_WORKFLOW_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {"instanceId": {"type": "string"}},
    "required": ["instanceId"],
}


@server.tool(
    Tool(
        name="complete_orian_workflow",
        description="Mark an Orian workflow instance as complete.",
        input_schema=COMPLETE_WORKFLOW_SCHEMA,
    )
)
def complete_orian_workflow(payload: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if Draft7Validator is not None:
            Draft7Validator(COMPLETE_WORKFLOW_SCHEMA).validate(payload)
        base_url = _env_or_fail("ORIAN_BASE_URL")
        api_key = os.getenv("ORIAN_API_KEY")
        client = OrianClient(base_url, api_key)
        r = client.complete_workflow(instance_id=payload["instanceId"])
        if not r.ok:
            return {"ok": False, "status": r.status_code, "error": safe_text(r)}
        return {"ok": True, "result": r.json() if _is_json(r) else r.text}
    except Exception as e:
        return {"ok": False, "error": str(e), "trace": traceback.format_exc()}


# === Helpers ===

def _is_json(resp: Response) -> bool:
    ctype = resp.headers.get("Content-Type", "")
    return "json" in ctype.lower()


def safe_text(resp: Response) -> str:
    try:
        return resp.text
    except Exception:
        return f"<non-text response: {resp.status_code}>"


# === Entry point (STDIO JSON‑RPC) ===
if __name__ == "__main__":
    # The MCP stdio transport wires the server to stdin/stdout as per the MCP spec.
    transport = stdio_transport()
    try:
        server.run(transport)
    except KeyboardInterrupt:
        pass
