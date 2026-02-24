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
SSH_KEY_PATH = os.path.expanduser("~/.ssh/isomind_key")

tunnels = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch SSH Tunnels
    print(f"🚀 Booting IsoMind Orchestrator... connecting to {SSH_HOST}:{SSH_PORT}...")
    
    # We need to forward Agent API (8000), vLLM (8001), Embedding API (8002), and WebRTC/VNC (8080)
    ports = [8000, 8001, 8002, 8080]
    for port in ports:
        cmd = [
            "ssh", "-N",
            "-L", f"{port}:localhost:{port}",
            "-p", SSH_PORT,
            "-i", SSH_KEY_PATH,
            "-o", "StrictHostKeyChecking=no",
            f"root@{SSH_HOST}"
        ]
        print(f"🔗 Establishing tunnel for port {port}...")
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tunnels.append(proc)
        
    # Give tunnels a moment to bind
    await asyncio.sleep(2)
    print("✅ All Sandbox connections established.")
    
    yield
    
    # Shutdown: Clean up tunnels
    print("🛑 Shutting down Orchestrator... closing tunnels...")
    for proc in tunnels:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
    print("🧹 Tunnels closed.")

app = FastAPI(title="IsoMind Orchestration API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://isomind-platform.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ExecuteRequest(BaseModel):
    blueprint_id: str
    start_url: str

@app.get("/v1/perception/screenshot")
async def get_screenshot(marks: bool = False):
    import requests
    PROXY_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")
    try:
        # Proxy the request to the Vast.ai container over the SSH tunnel
        resp = requests.get(f"{PROXY_URL}/v1/perception/screenshot?marks={str(marks).lower()}")
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {str(e)}")

class TeachRequest(BaseModel):
    blueprint_id: str
    action: str # "click" or "type"
    label: str
    x: float
    y: float
    text: str = ""

@app.post("/v1/teach/action")
async def teach_action(req: TeachRequest):
    # This endpoint replaces the CLI teacher.py
    # 1. Ask Vast.ai browser for current DOM state
    from executor import get_screenshot_and_marks, crop_image_around_mark, get_embedding, supabase, update_blueprint_state
    
    img_b64, marks = get_screenshot_and_marks()
    if not img_b64 or not marks:
        raise HTTPException(status_code=500, detail="Failed to get screen context")
        
    best_mark_id = None
    min_dist = float('inf')
    
    # Logic: Find which DOM element 'mark' contains the user's (x, y) click
    for m_id, m in marks.items():
        # Check if point inside bounding box
        if m['left'] <= req.x <= (m['left'] + m['width']) and m['top'] <= req.y <= (m['top'] + m['height']):
            best_mark_id = m_id
            break
            
    # Fallback to closest center distance if exact box not found
    if not best_mark_id:
        for m_id, m in marks.items():
            dist = ((m['x'] - req.x)**2 + (m['y'] - req.y)**2)**0.5
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
    supabase.table("visual_anchors").insert({
        "blueprint_id": req.blueprint_id,
        "semantic_label": req.label,
        "embedding": vector,
        "bounding_box_relative": {
            "width_pct": target_mark['width'] / 1920,
            "height_pct": target_mark['height'] / 1080
        }
    }).execute()
    
    # 4. Update the Blueprint DAG
    res = supabase.table("blueprints").select("state_graph_json").eq("id", req.blueprint_id).execute()
    graph = res.data[0].get("state_graph_json", {"steps": []}) if res.data else {"steps": []}
    
    step_num = len(graph.get("steps", [])) + 1
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
    import os
    PROXY_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")
    if req.action == "click":
        requests.post(f"{PROXY_URL}/v1/action/mouse/click", json={"x": target_mark['x'], "y": target_mark['y']})
    elif req.action == "type":
        requests.post(f"{PROXY_URL}/v1/action/mouse/click", json={"x": target_mark['x'], "y": target_mark['y']})
        requests.post(f"{PROXY_URL}/v1/action/keyboard/type", json={"text": req.text})
        
    return {"status": "success", "mark_id": best_mark_id, "step_added": new_step}

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
