import requests

def trigger_alert(message: str) -> str:
    res = requests.post("http://localhost:5000/alert", json={"msg": message})
    return res.text

def create_task(task_name: str) -> str:
    res = requests.post("http://localhost:5000/create-task", json={"task": task_name})
    return res.text
