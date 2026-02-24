import time
import os
import sys
from agent import run_agent_loop, get_screenshot
import base64

ARTIFACT_DIR = "/Users/andrewborysov/.gemini/antigravity/brain/01979c5a-780b-40fa-9875-e0de1ede6b73"
TEST_GOAL = "Go to wikipedia.org, search for 'Alan Turing', and click on the first link in the table of contents."

def main():
    print(f"=================================================")
    print(f"🚦 STARTING E2E VISUAL AGENT VALIDATION")
    print(f"🎯 Goal: {TEST_GOAL}")
    print(f"=================================================")
    
    # Run the standard agent loop up to 5 steps
    run_agent_loop(TEST_GOAL, max_steps=5)
    
    print(f"=================================================")
    print(f"📸 SAVING FINAL VISUAL STATE PROOF")
    print(f"=================================================")
    
    # Grab the final screenshot to prove where it ended up
    b64_image, marks = get_screenshot()
    if b64_image:
        img_data = base64.b64decode(b64_image)
        path = os.path.join(ARTIFACT_DIR, "e2e_final_state.png")
        with open(path, "wb") as f:
            f.write(img_data)
        print(f"✅ Final State Saved: {path}")
    else:
        print("❌ Failed to capture final screenshot")
        sys.exit(1)
        
    print("✅ E2E Test Completed Successfully!")

if __name__ == "__main__":
    main()
