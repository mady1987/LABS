import os
import asyncio
import httpx

async def create_issue_async(repo: str, title: str, body: str = "", token_env: str = "GITHUB_TOKEN"):
    token = os.getenv(token_env)
    if not token:
        return {"ok": False, "error": f"Missing token in env var {token_env}"}
    url = f"https://api.github.com/repos/{repo}/issues"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }
    payload = {"title": title, "body": body}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            ok = 200 <= resp.status_code < 300
            return {"ok": ok, "status": resp.status_code, "response": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def create_issue_sync(repo: str, title: str, body: str = "", token_env: str = "GITHUB_TOKEN"):
    return asyncio.get_event_loop().run_until_complete(create_issue_async(repo, title, body, token_env))
