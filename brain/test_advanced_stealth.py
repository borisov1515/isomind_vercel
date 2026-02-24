import requests
import json
import time

API_URL = "http://localhost:8000"

def test_stealth_flags():
    print("🚦 STARTING ADVANCED STEALTH QA")
    
    # 1. Navigate to a blank page to test base environment
    print("\nNavigating to about:blank to verify base stealth...")
    res = requests.post(f"{API_URL}/v1/action/browser/navigate", json={"url": "about:blank"})
    assert res.status_code == 200
    time.sleep(1)

    # 2. Assert navigator.webdriver is False (Critical detection vector)
    print("Testing navigator.webdriver (Should be undefined or false)...")
    res = requests.post(f"{API_URL}/v1/action/browser/evaluate", json={"js_code": "() => navigator.webdriver"})
    assert res.status_code == 200
    data = res.json()
    assert data["result"] in [False, None, 'undefined'], f"WebDriver flag detected! Value: {data['result']}"
    print("✅ navigator.webdriver is masked.")

    # 3. Assert window.chrome exists (headless browsers often lack it)
    print("Testing window.chrome presence...")
    res = requests.post(f"{API_URL}/v1/action/browser/evaluate", json={"js_code": "() => typeof window.chrome"})
    assert res.status_code == 200
    assert res.json()["result"] == "object", "window.chrome is missing!"
    print("✅ window.chrome is present.")
    
    # 4. Assert navigator.plugins is not completely empty (fingerprinting)
    print("Testing navigator.plugins length...")
    res = requests.post(f"{API_URL}/v1/action/browser/evaluate", json={"js_code": "() => navigator.plugins.length"})
    assert res.status_code == 200
    assert res.json()["result"] > 0, "navigator.plugins is empty! Clear sign of headless browser."
    print("✅ navigator.plugins is mock populated.")

    # 5. Connect to Cloudflare Turnstile explicitly
    # print("\nNavigating to SannySoft (Advanced Bot Detection)...")
    # res = requests.post(f"{API_URL}/v1/action/browser/navigate", json={"url": "https://bot.sannysoft.com/"})
    # assert res.status_code == 200
    
    print("\n✅ All Stealth Asserts Passed Successfully!")

if __name__ == "__main__":
    test_stealth_flags()
