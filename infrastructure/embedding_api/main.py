from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import base64
import io

app = FastAPI(title="IsoMind Visual Embedding API")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_ID = "openai/clip-vit-base-patch32"

print(f"Loading CLIP model {MODEL_ID} on {DEVICE}...")
model = CLIPModel.from_pretrained(MODEL_ID).to(DEVICE)
processor = CLIPProcessor.from_pretrained(MODEL_ID)
print("Model loaded successfully.")

class EmbedRequest(BaseModel):
    image_base64: str
    
class TextEmbedRequest(BaseModel):
    text: str

@app.post("/v1/embed/image")
async def embed_image(req: EmbedRequest):
    try:
        # Decode base64 image
        image_bytes = base64.b64decode(req.image_base64)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        
        # Process and generate embedding
        inputs = processor(images=image, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
            
        # Normalize vector (cosine similarity standard)
        image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
        embedding = image_features.squeeze(0).cpu().tolist()
        
        return {"status": "success", "embedding": embedding, "dimensions": len(embedding)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embed/text")
async def embed_text(req: TextEmbedRequest):
    try:
        inputs = processor(text=req.text, return_tensors="pt", padding=True).to(DEVICE)
        with torch.no_grad():
            text_features = model.get_text_features(**inputs)
            
        # Normalize vector
        text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
        embedding = text_features.squeeze(0).cpu().tolist()
        
        return {"status": "success", "embedding": embedding, "dimensions": len(embedding)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/v1/health")
async def health_check():
    return {"status": "ok", "device": DEVICE, "model": MODEL_ID}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
