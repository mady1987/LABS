import requests

def trigger_alert(message: str) -> str:
    res = requests.post("http://localhost:5000/alert", json={"msg": message})
    return res.text

# def create_task(task_name: str) -> str:
#     res = requests.post("http://localhost:5000/create-task", json={"task": task_name})
#     return res.text

# Placeholder functions for workflow management
def configure_workflow(payload: str) -> str:
    """
    This MCP tool wraps the Orian API running on port 8000
     {
        "workflowName": "SampleWorkflow2",
        "description": "Sample workflow for demonstration",
        "app": "Agent Orc",
        "contexts": [
            {
            "key": "REQUESTER",
            "description": "Person who requested the workflow",
            "dataType": "STRING"
            }
        ],
        "tasks": [
            {
            "name": "SUBMIT_REQUEST",
            "description": "Submit initial request",
            "taskType": "MANUAL",
            "assignmentType": "USER",
            "sequence": 1,
            "outcomes": [
                {
                "name": "SUBMITTED",
                "description": "Request has been submitted",
                "nextTask": "REVIEW_REQUEST"
                }
            ]
            },
            {
            "name": "REVIEW_REQUEST",
            "description": "Review the submitted request",
            "taskType": "MANUAL",
            "assignmentType": "GROUP",
            "sequence": 2,
            "outcomes": [
                {
                "name": "APPROVED",
                "nextTask": null
                },
                {
                "name": "NEEDS_INFO",
                "nextTask": "SUBMIT_REQUEST"
                }
            ]
            }
        ],
        "startInstance": false,
        "initialContext": {
            "REQUESTER": "alice@example.com"
        }
        }
    """
    try:
        print("Configuring workflow with payload:", payload)
        res = requests.post("http://localhost:8000/admin/configure_workflow", json=payload)
        return {
            "status": res.status_code,
            "response": res.json() if res.content else {}
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# def run_workflow(workflow_id: str) -> str:
#     res = requests.post("http://localhost:8000/run-workflow", json={"workflow_id": workflow_id})
#     return res.text

def complete_task(task_id: str, outcome: str) -> str:
    res = requests.post(f"http://localhost:8000/{task_id}/complete", json={"outcome": outcome})
    return res.text

# def delete_workflow(workflow_id: str) -> str:
#     res = requests.post("http://localhost:8000/delete-workflow", json={"workflow_id": workflow_id})
#     return res.text

# def complete_workflow(workflow_id: str) -> str:
#     res = requests.post("http://localhost:8000/complete-workflow", json={"workflow_id": workflow_id})
#     return res.text