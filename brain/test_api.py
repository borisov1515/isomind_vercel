import pytest
import requests
import base64

API_URL = "http://localhost:8000"

def test_health_status():
    res = requests.get(f"{API_URL}/v1/health/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["environment"] == "sandbox"

def test_screenshot_with_marks():
    res = requests.get(f"{API_URL}/v1/perception/screenshot?marks=true")
    assert res.status_code == 200
    data = res.json()
    assert "image_base64" in data
    assert "marks_mapping" in data
    
    # decode base64 to ensure it's valid
    img_bytes = base64.b64decode(data["image_base64"])
    assert len(img_bytes) > 1000  # Should be a decent sized image
    
    # Check that marks mapping is a dict
    assert isinstance(data["marks_mapping"], dict)

def test_screenshot_without_marks():
    res = requests.get(f"{API_URL}/v1/perception/screenshot?marks=false")
    assert res.status_code == 200
    data = res.json()
    assert "image_base64" in data
    assert "marks_mapping" in data
    assert len(data["marks_mapping"]) == 0  # Should be empty when marks=false

def test_navigate_validation():
    # Test missing payload
    res = requests.post(f"{API_URL}/v1/action/browser/navigate")
    assert res.status_code == 422  # Unprocessable Entity
    
    # Test invalid payload
    res = requests.post(f"{API_URL}/v1/action/browser/navigate", json={"bad_key": "http://example.com"})
    assert res.status_code == 422
    
def test_click_validation():
    # Test missing payload
    res = requests.post(f"{API_URL}/v1/action/mouse/click")
    assert res.status_code == 422
    
    # Test invalid coordinates (strings instead of ints)
    res = requests.post(f"{API_URL}/v1/action/mouse/click", json={"x": "abc", "y": "def"})
    assert res.status_code == 422
    
def test_type_validation():
    # Test missing payload
    res = requests.post(f"{API_URL}/v1/action/keyboard/type")
    assert res.status_code == 422

# Functional tests
def test_navigate_success():
    res = requests.post(f"{API_URL}/v1/action/browser/navigate", json={"url": "https://example.com"})
    assert res.status_code == 200
    assert res.json() == {"status": "simulated_navigation", "url": "https://example.com"}

def test_click_success():
    res = requests.post(f"{API_URL}/v1/action/mouse/click", json={"x": 100, "y": 100})
    assert res.status_code == 200
    assert res.json() == {"status": "simulated_human_click", "x": 100, "y": 100}

def test_type_success():
    res = requests.post(f"{API_URL}/v1/action/keyboard/type", json={"text": "hello test"})
    assert res.status_code == 200
    assert res.json() == {"status": "simulated_human_type", "text": "hello test"}
