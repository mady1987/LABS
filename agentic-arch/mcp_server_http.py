from fastapi import FastAPI, Body
from pydantic import BaseModel
from tools.common_tools import trigger_alert, create_task

app = FastAPI(title="MCP HTTP Bridge")

# A tiny registry so the agent can call tools by name over HTTP
TOOL_REGISTRY = {
    "trigger_alert": trigger_alert,
    "create_task": create_task,
}

class InvokeRequest(BaseModel):
    tool: str
    input: str

@app.get("/tools")
def list_tools():
    return {"tools": list(TOOL_REGISTRY.keys())}

@app.post("/invoke")
def invoke(req: InvokeRequest):
    fn = TOOL_REGISTRY.get(req.tool)
    if not fn:
        return {"ok": False, "error": f"unknown tool '{req.tool}'"}
    try:
        result = fn(req.input)
        return {"ok": True, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print("🌐 MCP HTTP bridge on http://127.0.0.1:8765")
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")
