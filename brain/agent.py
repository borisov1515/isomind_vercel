import requests
import json
import base64
import time
from openai import OpenAI

# Configuration
AGENT_API_URL = "http://localhost:8000"
VLLM_API_URL = "http://localhost:8001/v1"
MODEL_NAME = "Qwen/Qwen2-VL-7B-Instruct"

# Initialize OpenAI Client (pointing to local vLLM)
client = OpenAI(
    api_key="EMPTY", # vLLM doesn't require an API key by default
    base_url=VLLM_API_URL,
)

SYSTEM_PROMPT = """You are an autonomous web browser agent. 
You are given a screenshot of the current browser state, the screen resolution is 1920x1080.
Interactive elements in the screenshot are highlighted with red numbered tags (e.g. 1, 2, 3).
Your task is to reach the user's goal by navigating, clicking, or typing.

You MUST respond in pure JSON format containing your next action. No markdown formatting or extra text.
Available actions and JSON formats:

1. Navigate to a URL:
{"action": "navigate", "url": "https://example.com"}

2. Click a numbered tag:
{"action": "click", "mark_id": "5"}

3. Click at raw coordinates (if no tag exists):
{"action": "click", "x": 500, "y": 200}

4. Type text (assuming input is already focused, or you just clicked a tag/coordinate to focus it):
{"action": "type", "text": "my search query"}

5. Finish the task:
{"action": "done", "result": "The answer to the user's question..."}

Take it step by step. Output ONLY valid JSON.
"""

def get_screenshot():
    # Attempt to grab a screenshot from our Agent API
    print("📸 Taking screenshot...")
    try:
        response = requests.get(f"{AGENT_API_URL}/v1/perception/screenshot")
        response.raise_for_status()
        data = response.json()
        return data.get("image_base64"), data.get("marks_mapping", {})
    except Exception as e:
        print(f"❌ Failed to get screenshot: {e}")
        return None, {}

def execute_action(action_data, marks_mapping):
    # Sends the parsed JSON action to the FastAPI agent backend
    action_type = action_data.get("action")
    print(f"🛠️ Executing action: {action_type}")
    
    try:
        if action_type == "navigate":
            url = action_data.get("url")
            print(f"   -> Nagivating to: {url}")
            requests.post(f"{AGENT_API_URL}/v1/action/browser/navigate", json={"url": url})
        
        elif action_type == "click":
            # Check if mark_id is provided
            if "mark_id" in action_data:
                mark_id = str(action_data["mark_id"])
                if mark_id in marks_mapping:
                    x = marks_mapping[mark_id]["x"]
                    y = marks_mapping[mark_id]["y"]
                    print(f"   -> Clicking Mark ID [{mark_id}] at: ({x}, {y})")
                else:
                    print(f"❌ Mark ID [{mark_id}] not found in mapping.")
                    return False
            else:
                x, y = action_data.get("x"), action_data.get("y")
                print(f"   -> Clicking at: ({x}, {y})")
                
            requests.post(f"{AGENT_API_URL}/v1/action/mouse/click", json={"x": x, "y": y})
            
        elif action_type == "type":
            text = action_data.get("text")
            print(f"   -> Typing: '{text}'")
            requests.post(f"{AGENT_API_URL}/v1/action/keyboard/type", json={"text": text})
            
        elif action_type == "done":
            result = action_data.get("result")
            print(f"✅ Goal Achieved: {result}")
            return True
            
        else:
            print(f"⚠️ Unknown action type: {action_type}")
            
    except Exception as e:
        print(f"❌ Action execution failed: {e}")
        
    return False

def decide_next_action(goal, b64_image, history):
    print("🧠 Asking VLM for the next move...", flush=True)
    
    # Format message history
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]
    
    # Append past history so it knows what it already did
    if history:
        messages.extend(history)
        
    # Build the current turn query
    content = [
        {"type": "text", "text": f"Goal: {goal}\nWhat is your next action based on this screenshot?"},
        {
            "type": "image_url", 
            "image_url": {"url": f"data:image/png;base64,{b64_image}"}
        }
    ]
    messages.append({"role": "user", "content": content})
    
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=256,
            temperature=0.1
        )
        response_text = completion.choices[0].message.content.strip()
        
        # Remove any Markdown code block backticks if the model ignores the core prompt
        if response_text.startswith("```json"):
            response_text = response_text[7:-3]
        elif response_text.startswith("```"):
            response_text = response_text[3:-3]
            
        return json.loads(response_text), messages
    except json.JSONDecodeError as e:
        print(f"❌ VLM returned invalid JSON: {response_text}", flush=True)
        return None, messages
    except BaseException as e:
        import traceback
        with open("crash.log", "w") as f:
            f.write(traceback.format_exc())
        print(f"❌ VLM request FATAL ERROR: {e}", flush=True)
        return None, messages

def run_agent_loop(goal, max_steps=10):
    print(f"🚀 Starting Agent Loop. Goal: '{goal}'")
    history = []
    
    for step in range(1, max_steps + 1):
        print(f"\n--- Step {step}/{max_steps} ---")
        
        # 1. Grab Screenshot
        b64_image, marks_mapping = get_screenshot()
        if not b64_image:
            print("Aborting loop due to missing screenshot.")
            break
            
        # 2. Decide Next Action Using Vision LLM
        action_data, messages = decide_next_action(goal, b64_image, history)
        if not action_data:
            print("Aborting loop due to VLM failure.")
            break
            
        print(f"🤖 VLM Response: {json.dumps(action_data, indent=2)}")
        
        # 3. Add to History
        # We append the original query (user) and the model's response (assistant)
        # to the history so it can reason over multiple steps
        # We omit the raw base64 string from history to save context tokens, 
        # replacing it with a placeholder note.
        clean_user_message = {
            "role": "user", 
            "content": f"Goal: {goal}\n[Screenshot submitted previously]"
        }
        history.append(clean_user_message)
        history.append({"role": "assistant", "content": json.dumps(action_data)})
        
        # 4. Execute Action
        is_done = execute_action(action_data, marks_mapping)
        if is_done:
            break
            
        # Sleep briefly to let the DOM settle before the next screenshot
        time.sleep(2)
        
    print("\n🛑 Agent loop finished.")

if __name__ == "__main__":
    task = input("Enter a goal for the agent (e.g., 'Go to wikipedia.org and search for Quantum Mechanics'): ")
    run_agent_loop(task)
