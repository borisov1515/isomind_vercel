import requests
import base64
import time
import os
import json

AGENT_API_URL = "http://localhost:8000"
ARTIFACT_DIR = "/Users/andrewborysov/.gemini/antigravity/brain/01979c5a-780b-40fa-9875-e0de1ede6b73"

def main():
    print("Testing Set-of-Marks Layer...")
    res = requests.post(f"{AGENT_API_URL}/v1/action/browser/navigate", json={"url": "https://wikipedia.org"})
    print("Navigate Response:", res.status_code, res.text)
    
    print("Waiting 2 seconds...")
    time.sleep(2)

    print("Taking screenshot with marks=true ...")
    res = requests.get(f"{AGENT_API_URL}/v1/perception/screenshot?marks=true")
    if res.status_code == 200:
        data = res.json()
        b64 = data["image_base64"]
        marks = data["marks_mapping"]
        
        img_data = base64.b64decode(b64)
        path = os.path.join(ARTIFACT_DIR, "marks_test.png")
        with open(path, "wb") as f:
            f.write(img_data)
        print(f"Screenshot saved to {path}!")
        print(f"Extracted {len(marks)} Interactive Marks via Javascript!")
        
        if len(marks) > 0:
            first_key = list(marks.keys())[0]
            print(f"Example Mark ID {first_key}:", marks[first_key])
    else:
        print("Screenshot failed:", res.status_code, res.text)

if __name__ == "__main__":
    main()
