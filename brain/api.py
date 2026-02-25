import os
import subprocess
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
from executor import run_blueprint
from contextlib import asynccontextmanager

# Read Vast.ai connection details
SSH_HOST = os.getenv("VAST_IP", "217.171.200.22")
SSH_PORT = os.getenv("VAST_PORT", "43097")
SSH_KEY_PATH = "/tmp/isomind_key"

tunnels = []
ssh_logs = []
startup_info = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch SSH Tunnels
    print(f"🚀 Booting IsoMind Orchestrator... connecting to {SSH_HOST}:{SSH_PORT}...")
    
    env_key = os.getenv("VAST_SSH_KEY")
    env_key_b64 = os.getenv("VAST_SSH_KEY_B64")
    
    startup_info["env_key_present"] = bool(env_key)
    startup_info["env_key_b64_present"] = bool(env_key_b64)
    
    if env_key_b64:
        import base64
        with open(SSH_KEY_PATH, "w") as f:
            f.write(base64.b64decode(env_key_b64).decode('utf-8'))
        os.chmod(SSH_KEY_PATH, 0o600)
        startup_info["key_written"] = True
        print("🔑 Loaded SSH Key from Base64 Environment Variable!")
    elif env_key:
        with open(SSH_KEY_PATH, "w") as f:
            env_key = env_key.replace("\\n", "\n")
            
            # If the user pasted the key into a single-line input field on Render, 
            # it loses its vital newline formatting which causes libcrypto errors.
            if env_key.count("\n") < 2:
                print("⚠️ Formatting corrupted single-line SSH key string...")
                body = env_key.replace("-----BEGIN OPENSSH PRIVATE KEY-----", "").replace("-----END OPENSSH PRIVATE KEY-----", "").strip()
                # body might have spaces separating the base64 chunks
                body_lines = body.replace(" ", "\n")
                env_key = f"-----BEGIN OPENSSH PRIVATE KEY-----\n{body_lines}\n-----END OPENSSH PRIVATE KEY-----\n"

            f.write(env_key)
        # SSH requires strict permissions on the private key
        os.chmod(SSH_KEY_PATH, 0o600)
        startup_info["key_written"] = True
        print("🔑 Loaded SSH Key from Environment Variable into /tmp/.")
    else:
        startup_info["key_written"] = False
        print("⚠️ VAST_SSH_KEY not found in environment variables!")
    
    # We need to forward Agent API (8000), vLLM (8001), Embedding API (8002), and WebRTC/VNC (8080)
    ports = [8000, 8001, 8002, 8080]
    for port in ports:
        cmd = [
            "ssh", "-N",
            "-L", f"{port}:localhost:{port}",
            "-p", SSH_PORT,
            "-i", SSH_KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            "-v", # Add verbose logging
            f"root@{SSH_HOST}"
        ]
        print(f"🔗 Establishing tunnel for port {port}...")
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        tunnels.append(proc)
        
        # Async task to read stderr without blocking the main event loop
        async def read_stderr(p, pt: int):
            while True:
                line = await p.stderr.readline()
                if not line: break
                ssh_logs.append(f"[Port {pt}] {line.decode().strip()}")
                
        asyncio.create_task(read_stderr(proc, port))
        
    # Give tunnels a moment to bind
    await asyncio.sleep(2)
    print("✅ All Sandbox connections established.")
    
    yield
    
    # Shutdown: Clean up tunnels
    print("🛑 Shutting down Orchestrator... closing tunnels...")
    for proc in tunnels:
        proc.terminate()
        try:
            await asyncio.wait_for(proc.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            proc.kill()
    print("🧹 Tunnels closed.")

from datetime import datetime
from fastapi import Request

LAST_ACTIVITY_TIME = datetime.utcnow()

app = FastAPI(title="IsoMind Orchestration API", lifespan=lifespan)

@app.get("/v1/debug/ssh")
async def get_ssh_logs():
    return {
        "startup_info": startup_info,
        "logs": ssh_logs[-100:]
    }

@app.middleware("http")
async def track_activity(request: Request, call_next):
    global LAST_ACTIVITY_TIME
    if request.url.path != "/v1/health":
        LAST_ACTIVITY_TIME = datetime.utcnow()
    response = await call_next(request)
    return response

@app.get("/v1/health")
async def health_check():
    global LAST_ACTIVITY_TIME
    inactive_seconds = (datetime.utcnow() - LAST_ACTIVITY_TIME).total_seconds()
    return {"status": "ok", "inactive_seconds": inactive_seconds}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://isomind-platform.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.responses import HTMLResponse

@app.get("/v1/dashboard/vnc", response_class=HTMLResponse)
async def get_vnc_player():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>IsoMind VNC Stream</title>
        <meta charset="utf-8">
        <style>
            body { margin: 0; background-color: #09090b; overflow: hidden; display: flex; align-items: center; justify-content: center; height: 100vh; }
            iframe { width: 100%; height: 100%; border: none; }
        </style>
    </head>
    <body>
        <iframe src="/vnc/vnc.html?autoconnect=true&resize=scale"></iframe>
    </body>
    </html>
    """
    return html_content

import httpx
import websockets
import asyncio
from fastapi import Request, WebSocket, WebSocketDisconnect
from starlette.responses import StreamingResponse

@app.websocket("/vnc/websockify")
async def websocket_proxy(websocket: WebSocket):
    await websocket.accept()
    
    # The local SSH tunnel to the Vast.ai container's noVNC
    target_ws_url = "ws://localhost:8080/websockify"
    
    try:
        async with websockets.connect(target_ws_url) as target_ws:
            async def forward_to_target():
                try:
                    while True:
                        data = await websocket.receive()
                        if 'bytes' in data:
                            await target_ws.send(data['bytes'])
                        elif 'text' in data:
                            await target_ws.send(data['text'])
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    print(f"WS Error forwarding client to target: {e}")

            async def forward_to_client():
                try:
                    while True:
                        message = await target_ws.recv()
                        if isinstance(message, bytes):
                            await websocket.send_bytes(message)
                        else:
                            await websocket.send_text(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception as e:
                    print(f"WS Error forwarding target to client: {e}")

            await asyncio.gather(
                forward_to_target(),
                forward_to_client()
            )
            
    except Exception as e:
        print(f"WebSocket Proxy Connection Error to local port 8080: {e}")
        try:
            await websocket.close()
        except:
            pass

from fastapi.staticfiles import StaticFiles

# Mount the noVNC client statically
app.mount("/vnc", StaticFiles(directory="novnc", html=True), name="vnc")
class ExecuteRequest(BaseModel):
    blueprint_id: str
    start_url: str

@app.get("/v1/perception/screenshot")
async def get_screenshot(marks: bool = False):
    import requests
    PROXY_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")
    try:
        # Proxy the request to the Vast.ai container over the SSH tunnel
        resp = requests.get(f"{PROXY_URL}/v1/perception/screenshot?marks={str(marks).lower()}", timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

class NavigateRequest(BaseModel):
    url: str

@app.post("/v1/action/browser/navigate")
async def browser_navigate(req: NavigateRequest):
    import requests
    PROXY_URL = "http://localhost:8000"
    try:
        resp = requests.post(f"{PROXY_URL}/v1/action/browser/navigate", json={"url": req.url}, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy navigate error: {str(e)}")

class TeachRequest(BaseModel):
    blueprint_id: str
    action: str # "click" or "type"
    label: str
    x: float
    y: float
    text: str = ""

@app.post("/v1/teach/action")
async def teach_action(req: TeachRequest):
    import traceback
    try:
        # This endpoint replaces the CLI teacher.py
        # 1. Ask Vast.ai browser for current DOM state
        from executor import get_screenshot_and_marks, crop_image_around_mark, get_embedding, supabase
        
        img_b64, marks = get_screenshot_and_marks()
        if not img_b64 or not marks:
            raise HTTPException(status_code=500, detail="Failed to get screen context")
            
        best_mark_id = None
        min_dist = float('inf')
        
        # Logic: Find which DOM element 'mark' contains the user's (x, y) click
        for m_id, m in marks.items():
            # Safely get bounding box falling back to center point coords
            m_left = m.get('left', m.get('x', 0) - m.get('width', 10)/2)
            m_top = m.get('top', m.get('y', 0) - m.get('height', 10)/2)
            m_width = m.get('width', 10)
            m_height = m.get('height', 10)
            
            # Check if point inside bounding box
            if m_left <= req.x <= (m_left + m_width) and m_top <= req.y <= (m_top + m_height):
                best_mark_id = m_id
                break
                
        # Fallback to closest center distance if exact box not found
        if not best_mark_id:
            for m_id, m in marks.items():
                m_x = m.get('x', 0)
                m_y = m.get('y', 0)
                dist = ((m_x - req.x)**2 + (m_y - req.y)**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    best_mark_id = m_id
                    
        if not best_mark_id:
            raise HTTPException(status_code=400, detail="Could not find an interactive element near click")
            
        target_mark = marks[best_mark_id]
        print(f"✅ Web Teacher matched click ({req.x}, {req.y}) to Mark {best_mark_id}")
        
        # 2. Crop & Embed Visual Anchor
        crop_b64 = crop_image_around_mark(img_b64, target_mark)
        vector = get_embedding(crop_b64)
        if not vector:
            raise HTTPException(status_code=500, detail="Failed to embed Visual Anchor")
            
        # 3. Save Memory to Supabase
        width_pct = target_mark.get('width', 10) / 1920
        height_pct = target_mark.get('height', 10) / 1080
        supabase.table("visual_anchors").insert({
            "blueprint_id": req.blueprint_id,
            "semantic_label": req.label,
            "embedding": vector,
            "bounding_box_relative": {
                "width_pct": width_pct,
                "height_pct": height_pct
            }
        }).execute()
        
        # 4. Update the Blueprint DAG
        res = supabase.table("blueprints").select("state_graph_json").eq("id", req.blueprint_id).execute()
        
        graph = res.data[0].get("state_graph_json") if res.data else None
        if not graph or not isinstance(graph, dict):
            graph = {"steps": []}
        if "steps" not in graph:
            graph["steps"] = []
            
        step_num = len(graph["steps"]) + 1
        new_step = {
            "step": step_num,
            "action": req.action,
            "semantic_target": req.label
        }
        if req.action == "type":
            new_step["text"] = req.text
            
        graph["steps"].append(new_step)
        supabase.table("blueprints").update({"state_graph_json": graph}).eq("id", req.blueprint_id).execute()
        
        # 5. Execute the click in the browser so the stream advances
        import requests
        PROXY_URL = "http://localhost:8000"
        t_x = target_mark.get('x', 0)
        t_y = target_mark.get('y', 0)
        
        if req.action == "click":
            requests.post(f"{PROXY_URL}/v1/action/mouse/click", json={"x": t_x, "y": t_y}, timeout=30)
        elif req.action == "type":
            requests.post(f"{PROXY_URL}/v1/action/mouse/click", json={"x": t_x, "y": t_y}, timeout=30)
            requests.post(f"{PROXY_URL}/v1/action/keyboard/type", json={"text": req.text}, timeout=30)
            
        return {"status": "success", "mark_id": best_mark_id, "step_added": new_step}
    except Exception as e:
        print("💥 FATAL ERROR IN TEACH_ACTION:")
        err_str = traceback.format_exc()
        print(err_str)
        raise HTTPException(status_code=500, detail=err_str)

@app.post("/v1/execute")
async def execute_task(req: ExecuteRequest):
    async def event_stream():
        # run_blueprint is currently a synchronous generator. 
        # For a truly async stream we loop through it.
        try:
            for log_line in run_blueprint(req.blueprint_id, req.start_url):
                yield f"data: {log_line}\n\n"
                await asyncio.sleep(0.01) # Small yield to event loop
        except Exception as e:
            yield f"data: [ERROR] Fatal exception: {str(e)}\n\n"
            
    return StreamingResponse(event_stream(), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    # Run on 8003 to not conflict with Agent API (8000), vLLM (8001), Embedding API (8002)
    uvicorn.run(app, host="0.0.0.0", port=8003)
