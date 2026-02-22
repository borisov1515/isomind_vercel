from fastapi import FastAPI
from pydantic import BaseModel
import subprocess
import base64

app = FastAPI(title="IsoMind Agent API")

class Coordinates(BaseModel):
    x: int
    y: int

@app.get("/v1/health/status")
def health_check():
    return {"status": "ok", "environment": "sandbox"}

@app.get("/v1/perception/screenshot")
def capture_screenshot():
    # Simple scrot capture as placeholder; will move to native Playwright/MSS later
    try:
        subprocess.run(["scrot", "-z", "/tmp/screen.png"], check=True)
        with open("/tmp/screen.png", "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode('utf-8')
        return {"image_base64": encoded}
    except Exception as e:
        return {"error": str(e)}

@app.post("/v1/action/browser/navigate")
async def browser_navigate(url: str):
    # TODO: Implement actual playwright connection
    return {"status": "simulated_navigation", "url": url}

@app.post("/v1/action/mouse/click")
async def mouse_click(coords: Coordinates):
    # TODO: Implement xdotool or playwright click
    return {"status": "simulated_click", "x": coords.x, "y": coords.y}
