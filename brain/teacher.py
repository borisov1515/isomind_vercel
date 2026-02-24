import os
import requests
import base64
import json
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:8002")
VLLM_API_URL = os.getenv("VLLM_API_URL", "http://localhost:8001/v1")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing Supabase credentials in .env")
    exit(1)

print(f"🔌 Connecting to Supabase at {SUPABASE_URL}...")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_screenshot_and_marks():
    print("📸 Capturing browser state...")
    try:
        res = requests.get(f"{AGENT_API_URL}/v1/perception/screenshot?marks=true")
        if res.status_code != 200:
            print(f"❌ Failed to get screenshot: {res.text}")
            return None, None
        data = res.json()
        return data["image_base64"], data["marks_mapping"]
    except Exception as e:
        print(f"❌ Connection error to Agent API: {e}")
        return None, None

def get_embedding(image_base64: str):
    print("🧠 Generating CLIP embedding vector...")
    try:
        res = requests.post(f"{EMBEDDING_API_URL}/v1/embed/image", json={"image_base64": image_base64})
        if res.status_code != 200:
            print(f"❌ Failed to generate embedding: {res.text}")
            return None
        return res.json()["embedding"]
    except Exception as e:
        print(f"❌ Connection error to Embedding API: {e}")
        return None

def crop_image_around_mark(image_base64: str, mark_info: dict, crop_size=100):
    img_data = base64.b64decode(image_base64)
    img = Image.open(BytesIO(img_data))
    
    x = mark_info["x"]
    y = mark_info["y"]
    
    # Simple centered crop constrained to image bounds
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
    try:
        res = requests.post(f"{AGENT_API_URL}/v1/action/{action}", json=payload)
        if res.status_code != 200:
            print(f"❌ Action failed: {res.text}")
        return res.status_code == 200
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    print("🎓 Welcome to the IsoMind Teacher CLI")
    
    # Verify DB connection with a simple query
    try:
        test = supabase.table("blueprints").select("id").limit(1).execute()
        print("✅ Supabase connection verified.")
    except Exception as e:
        print(f"❌ Supabase connection failed: {e}")
        return
        
    blueprint_name = input("Enter a name for this Blueprint (e.g. 'Wikipedia Search'): ").strip()
    if not blueprint_name:
        print("Name required. Exiting.")
        return
        
    try:
        res = supabase.table("blueprints").insert({"name": blueprint_name}).execute()
        blueprint_id = res.data[0]['id']
        print(f"✅ Created Blueprint ID: {blueprint_id}")
    except Exception as e:
        print(f"❌ Failed to create blueprint: {e}")
        return
        
    start_url = input("Enter starting URL: ").strip()
    if start_url:
        execute_action("browser/navigate", {"url": start_url})
    
    step_num = 1
    state_graph = []
    
    while True:
        print(f"\n--- Blueprint Step {step_num} ---")
        img_b64, marks = get_screenshot_and_marks()
        if not img_b64:
            break
            
        with open("teacher_view.png", "wb") as f:
            f.write(base64.b64decode(img_b64))
        print("🖼️ Saved current view to teacher_view.png. Please open it to see Mark IDs.")
        
        action = input("Enter action ('click', 'type', or 'done'): ").strip().lower()
        
        if action == "done":
            break
            
        elif action == "click":
            mark_id = input("Enter Mark ID to click: ").strip()
            if mark_id not in marks and str(mark_id) not in marks:
                print("❌ Invalid Mark ID")
                continue
                
            # Dictionary keys from JSON might be strings
            mark = marks.get(mark_id) or marks.get(str(mark_id))
            
            semantic_label = input(f"Enter semantic label for Mark ID {mark_id} (e.g. 'Search Bar'): ").strip()
            
            # Crop, Embed, Store
            crop_b64 = crop_image_around_mark(img_b64, mark)
            with open("last_crop.png", "wb") as f:
                f.write(base64.b64decode(crop_b64))
                
            vector = get_embedding(crop_b64)
            if not vector:
                continue
                
            rel_box = {
                "width_pct": mark["width"] / 1920,
                "height_pct": mark["height"] / 1080
            }
            
            try:
                supabase.table("visual_anchors").insert({
                    "blueprint_id": blueprint_id,
                    "semantic_label": semantic_label,
                    "embedding": vector,
                    "bounding_box_relative": rel_box
                }).execute()
                print(f"✅ Saved Visual Anchor '{semantic_label}' to DB.")
            except Exception as e:
                print(f"❌ Supabase store error: {e}")
                
            state_graph.append({
                "step": step_num,
                "action": "click",
                "semantic_target": semantic_label
            })
            
            execute_action("mouse/click", {"x": mark["x"], "y": mark["y"]})
            
        elif action == "type":
            text_to_type = input("Enter text to type: ")
            state_graph.append({
                "step": step_num,
                "action": "type",
                "text": text_to_type
            })
            execute_action("keyboard/type", {"text": text_to_type})
            
        else:
            print("❌ Unknown action.")
            continue
            
        step_num += 1
        
    print("\n💾 Saving final Blueprint state graph...")
    try:
        supabase.table("blueprints").update({"state_graph_json": {"steps": state_graph}}).eq("id", blueprint_id).execute()
        print("✅ Blueprint saved completely!")
    except Exception as e:
        print(f"❌ Supabase update error: {e}")

if __name__ == "__main__":
    main()
