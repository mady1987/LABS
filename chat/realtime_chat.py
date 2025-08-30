# pip install requests
import json, requests

BASE = "http://localhost:11434/api/chat"
MODEL = "llama3.1"
messages = [{"role":"system","content":"You are a concise coding assistant."}]

while True:
    try:
        user = input("\nYou: ")
    except (EOFError, KeyboardInterrupt):
        break
    messages.append({"role":"user","content":user})

    r = requests.post(BASE, json={"model": MODEL, "messages": messages, "stream": True}, stream=True)
    print("Assistant: ", end="", flush=True)
    full = ""
    for line in r.iter_lines():
        if not line:
            continue
        data = json.loads(line.decode("utf-8"))
        chunk = data.get("message", {}).get("content")
        if chunk:
            full += chunk
            print(chunk, end="", flush=True)
        if data.get("done"):
            break
    print()
    messages.append({"role":"assistant","content":full})
