import os
import sys
import asyncio
from typing import Optional
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

PORT = int(os.environ.get("PORT", "8010"))
UZCHESS_BACKEND = "http://127.0.0.1:7878"
IBRAT_BACKEND = "http://127.0.0.1:8015"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="Mega Automation Hub", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Persistent HTTP client with connection pooling
http_client = httpx.AsyncClient(timeout=120.0)

@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()


# Generic reverse proxy helper
async def forward_request(target_url: str, request: Request) -> Response:
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    body = await request.body()
    try:
        resp = await http_client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            params=dict(request.query_params),
            content=body,
            follow_redirects=True
        )
        
        response_headers = dict(resp.headers)
        # Remove hop-by-hop and encoding headers
        for h in ["content-encoding", "transfer-encoding", "content-length"]:
            response_headers.pop(h, None)
            
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=response_headers,
            media_type=resp.headers.get("content-type")
        )
    except Exception as e:
        return JSONResponse({"ok": False, "error": f"Backend aloqa xatoligi: {str(e)}"}, status_code=502)


# ==============================================================================
# 1. BOSH SAHIFA VA PROXY PAGES
# ==============================================================================

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def hub_home():
    html_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return HTMLResponse("<h1>Multi-Bot Mega Hub</h1>")

# Panel 1: UzChess
@app.api_route("/view/uzchess", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def view_uzchess(request: Request):
    return await forward_request(f"{UZCHESS_BACKEND}/", request)

# Panel 2: IF-Online
@app.api_route("/view/ifonline", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def view_ifonline(request: Request):
    return await forward_request(f"{UZCHESS_BACKEND}/ifonline", request)

# Panel 3: Ibrat Academy
@app.api_route("/view/ibrat", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def view_ibrat(request: Request):
    return await forward_request(f"{IBRAT_BACKEND}/", request)


# ==============================================================================
# 2. HUB AGGREGATED TELEMETRY & CONTROLS
# ==============================================================================

@app.get("/api/hub/stats")
async def hub_stats():
    """Barcha 3 ta bot tizimidan real-vaqt statistikasini parallel yig'ib beradi"""
    async def get_uzchess():
        try:
            r = await http_client.get(f"{UZCHESS_BACKEND}/api/status", timeout=3.0)
            return r.json() if r.status_code == 200 else {"_error": True}
        except Exception:
            return {"_error": True}

    async def get_ifonline():
        try:
            r = await http_client.get(f"{UZCHESS_BACKEND}/api/ifonline/status", timeout=3.0)
            return r.json() if r.status_code == 200 else {"_error": True}
        except Exception:
            return {"_error": True}

    async def get_ibrat():
        try:
            r = await http_client.get(f"{IBRAT_BACKEND}/api/status", timeout=3.0)
            p = await http_client.get(f"{IBRAT_BACKEND}/api/pool/stats", timeout=3.0)
            res = r.json() if r.status_code == 200 else {"_error": True}
            pool = p.json() if p.status_code == 200 else {}
            res["pool"] = pool
            return res
        except Exception:
            return {"_error": True}

    u_res, if_res, ib_res = await asyncio.gather(get_uzchess(), get_ifonline(), get_ibrat())

    return {
        "uzchess": {
            "online": "_error" not in u_res,
            "is_running": u_res.get("is_running", False),
            "sessions": u_res.get("sessions_count", 0),
            "registered": u_res.get("registered_count", 0),
            "mode": u_res.get("mode", ""),
            "task": u_res.get("current_task", "")
        },
        "ifonline": {
            "online": "_error" not in if_res,
            "is_running": if_res.get("is_running", False),
            "sessions": if_res.get("sessions_count", 0),
            "registered": if_res.get("registered_count", 0),
            "task": if_res.get("current_task", "")
        },
        "ibrat": {
            "online": "_error" not in ib_res,
            "is_running": ib_res.get("is_running", False),
            "total": ib_res.get("total", 0),
            "success": ib_res.get("success", 0),
            "processed": ib_res.get("processed", 0),
            "pool_available": ib_res.get("pool", {}).get("available", 0),
            "pool_total": ib_res.get("pool", {}).get("total", 0)
        }
    }


@app.post("/api/hub/stop-all")
async def hub_stop_all():
    """Barcha faol tizimlarni darhol favqulodda to'xtatish"""
    results = {}
    try:
        r1 = await http_client.post(f"{UZCHESS_BACKEND}/api/stop", timeout=5.0)
        results["uzchess"] = r1.status_code == 200
    except Exception as e:
        results["uzchess"] = False

    try:
        r2 = await http_client.post(f"{UZCHESS_BACKEND}/api/ifonline/stop", timeout=5.0)
        results["ifonline"] = r2.status_code == 200
    except Exception as e:
        results["ifonline"] = False

    try:
        r3 = await http_client.post(f"{IBRAT_BACKEND}/api/stop", timeout=5.0)
        results["ibrat"] = r3.status_code == 200
    except Exception as e:
        results["ibrat"] = False

    return {"ok": True, "stopped": results}


# ==============================================================================
# 3. STREAMING VA STATIC RESURSLAR PROXY
# ==============================================================================

# UzChess SSE Stream
@app.get("/api/live/stream")
async def stream_uzchess(request: Request):
    async def sse_generator():
        try:
            async with http_client.stream("GET", f"{UZCHESS_BACKEND}/api/live/stream") as resp:
                async for chunk in resp.aiter_bytes():
                    yield chunk
        except Exception:
            yield b"data: {\"event\": \"disconnected\"}\n\n"

    return StreamingResponse(sse_generator(), media_type="text/event-stream")

# Static assets proxy
@app.get("/static/{path:path}")
async def proxy_static(path: str, request: Request):
    # Check if file exists in our local static first
    local_file = os.path.join(STATIC_DIR, path)
    if os.path.exists(local_file) and not os.path.isdir(local_file):
        from fastapi.responses import FileResponse
        return FileResponse(local_file)
    return await forward_request(f"{UZCHESS_BACKEND}/static/{path}", request)


# ==============================================================================
# 4. DISPATCHING API PROXIES (UZCHESS, IF-ONLINE, IBRAT)
# ==============================================================================

# Explicit Dedicated Routes to isolate each bot's telemetry & logs
@app.api_route("/api/uzchess/{path:path}", methods=["GET", "POST", "DELETE", "PUT"])
async def proxy_uzchess_explicit(path: str, request: Request):
    return await forward_request(f"{UZCHESS_BACKEND}/api/{path}", request)

@app.api_route("/api/ibrat/{path:path}", methods=["GET", "POST", "DELETE", "PUT"])
async def proxy_ibrat_explicit(path: str, request: Request):
    return await forward_request(f"{IBRAT_BACKEND}/api/{path}", request)

# IF-Online APIs
@app.api_route("/api/ifonline/{path:path}", methods=["GET", "POST", "DELETE", "PUT"])
async def proxy_ifonline(path: str, request: Request):
    return await forward_request(f"{UZCHESS_BACKEND}/api/ifonline/{path}", request)

# Ibrat Specific APIs
@app.api_route("/api/pool/{path:path}", methods=["GET", "POST", "DELETE", "PUT"])
async def proxy_ibrat_pool(path: str, request: Request):
    return await forward_request(f"{IBRAT_BACKEND}/api/pool/{path}", request)

@app.api_route("/api/checker/{path:path}", methods=["GET", "POST", "DELETE", "PUT"])
async def proxy_ibrat_checker(path: str, request: Request):
    return await forward_request(f"{IBRAT_BACKEND}/api/checker/{path}", request)

@app.api_route("/api/regions", methods=["GET"])
async def proxy_ibrat_regions(request: Request):
    return await forward_request(f"{IBRAT_BACKEND}/api/regions", request)

@app.api_route("/api/districts/{path:path}", methods=["GET"])
async def proxy_ibrat_districts(path: str, request: Request):
    return await forward_request(f"{IBRAT_BACKEND}/api/districts/{path}", request)

@app.api_route("/api/localities/{path:path}", methods=["GET"])
async def proxy_ibrat_localities(path: str, request: Request):
    return await forward_request(f"{IBRAT_BACKEND}/api/localities/{path}", request)

@app.api_route("/api/history", methods=["GET"])
@app.api_route("/api/history/{path:path}", methods=["GET"])
async def proxy_ibrat_history(request: Request, path: str = ""):
    target = f"{IBRAT_BACKEND}/api/history" if not path else f"{IBRAT_BACKEND}/api/history/{path}"
    return await forward_request(target, request)

@app.api_route("/api/reset", methods=["POST"])
async def proxy_ibrat_reset(request: Request):
    return await forward_request(f"{IBRAT_BACKEND}/api/reset", request)

@app.api_route("/api/start-process", methods=["POST"])
async def proxy_ibrat_start(request: Request):
    return await forward_request(f"{IBRAT_BACKEND}/api/start-process", request)

@app.api_route("/api/logs", methods=["GET"])
@app.api_route("/api/logs/clear", methods=["POST"])
async def proxy_ibrat_logs(request: Request):
    return await forward_request(f"{IBRAT_BACKEND}{request.url.path}", request)

@app.api_route("/api/download/{path:path}", methods=["GET"])
async def proxy_ibrat_download(path: str, request: Request):
    return await forward_request(f"{IBRAT_BACKEND}/api/download/{path}", request)

@app.get("/hisobot.pdf")
@app.get("/hisobot.xlsx")
async def proxy_ibrat_reports(request: Request):
    return await forward_request(f"{IBRAT_BACKEND}{request.url.path}", request)

# UzChess Specific APIs
@app.api_route("/api/geo", methods=["GET"])
@app.api_route("/api/geo/neighborhoods", methods=["GET"])
async def proxy_uzchess_geo(request: Request):
    return await forward_request(f"{UZCHESS_BACKEND}{request.url.path}", request)

@app.api_route("/api/sessions", methods=["GET"])
@app.api_route("/api/sessions/{path:path}", methods=["GET", "POST"])
async def proxy_uzchess_sessions(request: Request, path: str = ""):
    target = f"{UZCHESS_BACKEND}/api/sessions" if not path else f"{UZCHESS_BACKEND}/api/sessions/{path}"
    return await forward_request(target, request)

@app.post("/api/upload")
async def proxy_uzchess_upload(request: Request):
    return await forward_request(f"{UZCHESS_BACKEND}/api/upload", request)

@app.post("/api/start")
@app.post("/api/stop")
@app.post("/api/clear-logs")
@app.post("/api/import-existing")
async def proxy_uzchess_controls(request: Request):
    return await forward_request(f"{UZCHESS_BACKEND}{request.url.path}", request)

@app.api_route("/api/accounts", methods=["GET"])
@app.api_route("/api/account/{phone}", methods=["DELETE"])
@app.api_route("/api/vault/stats", methods=["GET"])
@app.api_route("/api/export/{path:path}", methods=["GET"])
async def proxy_uzchess_account_ops(request: Request, path: str = "", phone: str = ""):
    return await forward_request(f"{UZCHESS_BACKEND}{request.url.path}", request)

# General Fallback Proxy
@app.api_route("/7878/{path:path}", methods=["GET", "POST", "DELETE", "PUT"])
async def proxy_7878_fallback(path: str, request: Request):
    return await forward_request(f"{UZCHESS_BACKEND}/{path}", request)


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("👑 MEGA AUTOMATION HUB: 3-in-1 Control Center")
    print(f"🌐 Brauzerda oching: http://localhost:{PORT}")
    print(f"🔗 UzChess: {UZCHESS_BACKEND} | IF-Online: {UZCHESS_BACKEND}/ifonline | Ibrat: {IBRAT_BACKEND}")
    print("="*70 + "\n")
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, reload=False)
