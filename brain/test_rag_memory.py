import os
import requests
import base64
import time
from io import BytesIO
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client, Client
from executor import cosine_similarity, get_embedding, crop_image_around_mark
import uuid

load_dotenv()
AGENT_API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_visual_rag():
    print("🚦 STARTING E2E RAG MEMORY VALIDATION")
    
    # 1. Setup Dummy Blueprint
    test_id = str(uuid.uuid4())
    print(f"\n1. Creating Dummy Blueprint for Test ({test_id})...")
    res = supabase.table("blueprints").insert({"name": f"Validation Test {test_id}"}).execute()
    blueprint_id = res.data[0]['id']
    
    # 2. Navigate to a known static page
    print("\n2. Navigating to example.com...")
    requests.post(f"{AGENT_API_URL}/v1/action/browser/navigate", json={"url": "https://example.com"})
    time.sleep(1) # Let DOM settle
    
    # 3. Get Screenshot & Marks (The "Teacher" phase)
    print("\n3. Capturing marks for 'Teacher' phase...")
    res = requests.get(f"{AGENT_API_URL}/v1/perception/screenshot?marks=true")
    assert res.status_code == 200
    data = res.json()
    img_b64 = data["image_base64"]
    marks = data["marks_mapping"]
    
    # example.com usually has one 'More information...' link. Find it.
    assert len(marks) > 0, "No interactive elements found on example.com"
    target_mark_id = list(marks.keys())[0]
    target_mark = marks[target_mark_id]
    
    # 4. Crop, Embed, and save to DB
    print(f"\n4. Embedding Element {target_mark_id} ('More info link')...")
    crop_b64 = crop_image_around_mark(img_b64, target_mark)
    original_vector = get_embedding(crop_b64)
    assert original_vector is not None
    assert len(original_vector) == 512
    
    supabase.table("visual_anchors").insert({
        "blueprint_id": blueprint_id,
        "semantic_label": "More Info Link",
        "embedding": original_vector,
        "bounding_box_relative": {"width_pct": 0.1, "height_pct": 0.1}
    }).execute()
    print("✅ Saved Anchor to Supabase.")
    
    # 5. The "Executor" phase - Reload page to change mark IDs (simulating drift)
    print("\n5. Reloading page (Simulating Executor Phase)...")
    requests.post(f"{AGENT_API_URL}/v1/action/browser/navigate", json={"url": "https://example.com"})
    time.sleep(1)
    
    # 6. Retrieve Memory & Match
    print("\n6. Fetching Memory and Scanning Screen...")
    anchor_res = supabase.table("visual_anchors").select("embedding").eq("blueprint_id", blueprint_id).eq("semantic_label", "More Info Link").execute()
    memory_vector = anchor_res.data[0]['embedding']
    
    res = requests.get(f"{AGENT_API_URL}/v1/perception/screenshot?marks=true")
    new_img_b64 = res.json()["image_base64"]
    new_marks = res.json()["marks_mapping"]
    
    best_id = None
    best_sim = -1
    
    print("\n7. Calculating Cosine Similarities against Memory:")
    for mark_id, mark_info in new_marks.items():
        new_crop = crop_image_around_mark(new_img_b64, mark_info)
        new_vector = get_embedding(new_crop)
        sim = cosine_similarity(memory_vector, new_vector)
        print(f" -> Mark {mark_id}: {sim:.4f}")
        if sim > best_sim:
            best_sim = sim
            best_id = mark_id
            
    assert best_sim > 0.95, f"Expected near-perfect match, got {best_sim}"
    print(f"\n✅ SUCCESS: Vector Engine successfully found target with score {best_sim:.4f}")
    
    # 7. Cleanup
    print("\n8. Cleaning up Test DB entries...")
    supabase.table("blueprints").delete().eq("id", blueprint_id).execute()
    print("🧹 Cleanup complete.")

if __name__ == "__main__":
    test_visual_rag()
