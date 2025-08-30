import requests

def ask_ollama(prompt):
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    })
    return response.json()["response"]

response = ask_ollama("What's 23 x 57?")
