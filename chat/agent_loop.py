# pip install requests
import json, subprocess, requests, sys

MODEL = "llama3.1"
CHAT_URL = "http://localhost:11434/api/chat"

SYSTEM = """You can ask to use a tool by replying with pure JSON:
{"tool":"search_repo","query":"<text>","root":"."}
If you use the tool, wait for results; then write a final, concrete answer with code or diffs.
"""

def stream_chat(messages):
    r = requests.post(CHAT_URL, json={"model": MODEL, "messages": messages, "stream": True}, stream=True)
    full = ""
    for line in r.iter_lines():
        if not line: continue
        data = json.loads(line.decode())
        chunk = data.get("message", {}).get("content")
        if chunk:
            full += chunk
        if data.get("done"):
            break
    return full

user = sys.argv[1] if len(sys.argv) > 1 else "Find where 'retry policy' is implemented and propose a safer version."
messages = [{"role":"system","content":SYSTEM},{"role":"user","content":user}]
reply = stream_chat(messages).strip()

# tool call?
if reply.startswith("{"):
    try:
        req = json.loads(reply)
        if req.get("tool") == "search_repo":
            tool_out = subprocess.check_output(
                ["python","repo_tool.py"], input=json.dumps(req), text=True
            )
            result = json.loads(tool_out)["result"]
            messages += [{"role":"assistant","content":reply},
                         {"role":"user","content":"Tool result:\n" + result}]
            final = stream_chat(messages)
            print(final)
        else:
            print(reply)
    except Exception:
        print(reply)
else:
    print(reply)
