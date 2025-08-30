import subprocess, json, sys, os

def ripgrep(query, root="."):
    try:
        out = subprocess.check_output(["rg", "-n", "-S", query, root],
                                      stderr=subprocess.DEVNULL, text=True)
        return out[:6000]
    except subprocess.CalledProcessError:
        return "No matches."

if __name__ == "__main__":
    req = json.loads(sys.stdin.read())
    if req.get("tool") == "search_repo":
        print(json.dumps({"result": ripgrep(req.get("query",""), req.get("root","."))}))
    else:
        print(json.dumps({"error":"unknown tool"}))
