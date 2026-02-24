import os
import requests
import base64
import math
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:8002")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing Supabase credentials in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def cosine_similarity(v1, v2):
    if isinstance(v1, str):
        import json
        v1 = json.loads(v1)
    if isinstance(v2, str):
        import json
        v2 = json.loads(v2)
    
    dot_product = sum(float(a) * float(b) for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(float(a) * float(a) for a in v1))
    norm_v2 = math.sqrt(sum(float(b) * float(b) for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def get_screenshot_and_marks():
    print("📸 Capturing browser state for analysis...")
    res = requests.get(f"{AGENT_API_URL}/v1/perception/screenshot?marks=true")
    if res.status_code != 200:
        print(f"❌ Failed to get screenshot: {res.text}")
        return None, None
    data = res.json()
    return data["image_base64"], data["marks_mapping"]

def get_embedding(image_base64: str):
    res = requests.post(f"{EMBEDDING_API_URL}/v1/embed/image", json={"image_base64": image_base64})
    if res.status_code != 200:
        print(f"❌ Failed to generate embedding: {res.text}")
        return None
    return res.json()["embedding"]

def crop_image_around_mark(image_base64: str, mark_info: dict, crop_size=100):
    img_data = base64.b64decode(image_base64)
    img = Image.open(BytesIO(img_data))
    
    x = mark_info["x"]
    y = mark_info["y"]
    
    left = max(0, x - crop_size//2)
    top = max(0, y - crop_size//2)
    right = min(img.width, x + crop_size//2)
    bottom = min(img.height, y + crop_size//2)
    
    cropped = img.crop((left, top, right, bottom))
    
    buffered = BytesIO()
    cropped.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")

def execute_action(action: str, payload: dict):
    print(f"🛠️ Executing {action}...")
    res = requests.post(f"{AGENT_API_URL}/v1/action/{action}", json=payload)
    if res.status_code != 200:
        print(f"❌ Action failed: {res.text}")
    return res.status_code == 200

def run_blueprint(blueprint_id: str, start_url: str):
    yield f"[SYSTEM] 📥 Loading Blueprint {blueprint_id} from Memory..."
    res = supabase.table("blueprints").select("state_graph_json").eq("id", blueprint_id).execute()
    if not res.data:
        yield "[ERROR] ❌ Blueprint not found"
        return
        
    state_graph = res.data[0].get("state_graph_json", {}).get("steps", [])
    if not state_graph:
        yield "[ERROR] ❌ Blueprint is empty"
        return
        
    yield f"[SYSTEM] 🚀 Starting Execution Pipeline ({len(state_graph)} steps)"
    execute_action("browser/navigate", {"url": start_url})
    
    for step in state_graph:
        yield f"\n[SYSTEM] --- STEP {step['step']}: {step['action'].upper()} ---"
        
        if step['action'] == 'type':
            execute_action("keyboard/type", {"text": step['text']})
            continue
            
        elif step['action'] == 'click':
            target_label = step['semantic_target']
            yield f"[AGENT] 🔍 Searching for visual anchor: '{target_label}'"
            
            # Fetch anchor vector from Supabase
            anchor_res = supabase.table("visual_anchors").select("embedding").eq("blueprint_id", blueprint_id).eq("semantic_label", target_label).limit(1).execute()
            if not anchor_res.data:
                yield f"[ERROR] ❌ Memory Error: Visual Anchor for '{target_label}' is missing from DB."
                break
                
            original_vector = anchor_res.data[0]['embedding']
            
            # Get current screen state
            img_b64, marks = get_screenshot_and_marks()
            if not img_b64 or not marks:
                yield "[ERROR] ❌ Failed to get screen context"
                break
                
            yield f"[AGENT] 👁️ Analyzing {len(marks)} interactive elements on screen..."
            
            best_mark_id = None
            best_sim = -1.0
            
            for mark_id, mark_info in marks.items():
                crop_b64 = crop_image_around_mark(img_b64, mark_info)
                curr_vector = get_embedding(crop_b64)
                if curr_vector:
                    sim = cosine_similarity(original_vector, curr_vector)
                    if sim > best_sim:
                        best_sim = sim
                        best_mark_id = mark_id
                        
            yield f"[MEMORY] 📊 Best match: Mark ID {best_mark_id} with similarity {best_sim:.2f}"
            
            if best_sim > 0.85: # Strict visual threshold mapping
                yield f"[AGENT] 🎯 Target Acquired! Clicking {best_mark_id}"
                execute_action("mouse/click", {"x": marks[best_mark_id]['x'], "y": marks[best_mark_id]['y']})
            else:
                yield f"[ERROR] ❌ Visual drift detected. No element matched above threshold (0.85). Execution halted."
                break
                
    yield "\n[SYSTEM] ✅ Blueprint Execution Completed"

def main():
    print("🤖 Welcome to the IsoMind Autonomous Executor")
    blueprint_id = input("Enter Blueprint UUID to execute: ").strip()
    start_url = input("Enter starting URL: ").strip()
    
    if blueprint_id and start_url:
        run_blueprint(blueprint_id, start_url)

if __name__ == "__main__":
    main()
