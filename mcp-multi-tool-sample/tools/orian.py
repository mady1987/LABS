import os
import asyncio
import httpx

def get_default_orian_endpoint() -> str:
    return os.getenv("ORIAN_DEFAULT_ENDPOINT", "http://127.0.0.1:8000/admin/configure_workflow")

async def orian_start_process_async(endpoint: str, payload: dict):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(endpoint, json=payload)
            content_type = resp.headers.get("content-type", "")
            try:
                data = resp.json()
            except Exception:
                data = {"raw": resp.text}
            if resp.status_code >= 400:
                return {
                    "ok": False,
                    "status": resp.status_code,
                    "endpoint": endpoint,
                    "response": data
                }
            return {
                "ok": True,
                "status": resp.status_code,
                "endpoint": endpoint,
                "response": data
            }
    except Exception as e:
        return {"ok": False, "error": str(e), "endpoint": endpoint}

def orian_start_process_sync(endpoint: str, payload: dict):
    return asyncio.get_event_loop().run_until_complete(orian_start_process_async(endpoint, payload))
