import requests
import base64
import time
import os

AGENT_API_URL = "http://localhost:8000"
ARTIFACT_DIR = "/Users/andrewborysov/.gemini/antigravity/brain/01979c5a-780b-40fa-9875-e0de1ede6b73"

def main():
    print("Testing Stealth Layer...")
    res = requests.post(f"{AGENT_API_URL}/v1/action/browser/navigate", json={"url": "https://bot.sannysoft.com/"})
    print("Navigate Response:", res.status_code, res.text)
    
    print("Waiting 5 seconds for bot detection to run...")
    time.sleep(5)
    
    # Test human mouse click
    print("Testing human mouse click simulation (Bezier curves)...")
    res = requests.post(f"{AGENT_API_URL}/v1/action/mouse/click", json={"x": 500, "y": 500})
    print("Click Response:", res.status_code, res.text)
    time.sleep(1)

    print("Taking screenshot...")
    res = requests.get(f"{AGENT_API_URL}/v1/perception/screenshot")
    if res.status_code == 200:
        b64 = res.json()["image_base64"]
        img_data = base64.b64decode(b64)
        path = os.path.join(ARTIFACT_DIR, "stealth_test.png")
        with open(path, "wb") as f:
            f.write(img_data)
        print(f"Screenshot saved to {path}!")
    else:
        print("Screenshot failed:", res.status_code, res.text)

if __name__ == "__main__":
    main()
