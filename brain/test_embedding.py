import requests
import json
import base64
import os

API_URL = "http://localhost:8002"

def test_embedding_api():
    print("🚦 TESTING LOCAL VISUAL EMBEDDING SERVICE")
    
    # 1. Health check
    print("\n1. Checking Health Status...")
    res = requests.get(f"{API_URL}/v1/health")
    assert res.status_code == 200
    print(f"✅ API is healthy: {res.json()}")

    # 2. Text Embedding
    print("\n2. Testing Text Embedding...")
    res = requests.post(f"{API_URL}/v1/embed/text", json={"text": "Login Button"})
    assert res.status_code == 200
    data = res.json()
    assert "embedding" in data
    print(f"✅ Text embedded. Dimensions: {data['dimensions']}")
    
    # 3. Image Embedding (Create a tiny dummy red 100x100 square)
    print("\n3. Testing Visual (Image) Embedding...")
    from PIL import Image
    import io
    dummy_img = Image.new('RGB', (100, 100), color = 'red')
    buffered = io.BytesIO()
    dummy_img.save(buffered, format="JPEG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    
    res = requests.post(f"{API_URL}/v1/embed/image", json={"image_base64": img_b64})
    assert res.status_code == 200
    data = res.json()
    assert "embedding" in data
    print(f"✅ Visual crop embedded. Dimensions: {data['dimensions']}")
    
    print("\n✅ All Embedding API endpoints work correctly!")

if __name__ == "__main__":
    test_embedding_api()
