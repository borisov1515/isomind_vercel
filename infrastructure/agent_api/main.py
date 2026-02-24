import base64
import random
import math
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from playwright.async_api import async_playwright, Browser, Page
from playwright_stealth import stealth_async

# --- Global Playwright State ---
playwright_instance = None
browser: Browser = None
page: Page = None
current_mouse_x = 0
current_mouse_y = 0

async def move_mouse_humanly(target_page: Page, start_x: int, start_y: int, end_x: int, end_y: int):
    global current_mouse_x, current_mouse_y
    steps = random.randint(15, 30)
    
    dx = end_x - start_x
    dy = end_y - start_y
    dist = math.hypot(dx, dy)
    
    if dist < 5:
        await target_page.mouse.move(end_x, end_y, steps=2)
        current_mouse_x, current_mouse_y = end_x, end_y
        return
        
    dev = max(10, dist * 0.15)
    cp1_x = start_x + dx * 0.33 + random.uniform(-dev, dev)
    cp1_y = start_y + dy * 0.33 + random.uniform(-dev, dev)
    cp2_x = start_x + dx * 0.66 + random.uniform(-dev, dev)
    cp2_y = start_y + dy * 0.66 + random.uniform(-dev, dev)
    
    for i in range(1, steps + 1):
        t = i / steps
        inv_t = 1.0 - t
        x = (inv_t**3 * start_x) + (3 * inv_t**2 * t * cp1_x) + (3 * inv_t * t**2 * cp2_x) + (t**3 * end_x)
        y = (inv_t**3 * start_y) + (3 * inv_t**2 * t * cp1_y) + (3 * inv_t * t**2 * cp2_y) + (t**3 * end_y)
        
        await target_page.mouse.move(x + random.uniform(-1, 1), y + random.uniform(-1, 1))
        await asyncio.sleep(random.uniform(0.005, 0.015))
        
    await target_page.mouse.move(end_x, end_y)
    current_mouse_x, current_mouse_y = end_x, end_y
    await asyncio.sleep(random.uniform(0.05, 0.15))

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch Playwright browser
    global playwright_instance, browser, page
    playwright_instance = await async_playwright().start()
    
    # Launch Chromium in headed mode (we have a virtual display :99 via Xvfb)
    browser = await playwright_instance.chromium.launch(
        headless=False,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--start-maximized",
            "--disable-blink-features=AutomationControlled"
        ]
    )
    
    # Create a persistent context with a fixed viewport matching our Xvfb screen
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080},
        device_scale_factor=1,
    )
    
    # Inject custom stealth scripts that playwright-stealth might miss
    await context.add_init_script("""
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {
                    0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                    description: "Portable Document Format",
                    filename: "internal-pdf-viewer",
                    length: 1,
                    name: "Chrome PDF Plugin"
                }
            ],
        });
    """)
    
    page = await context.new_page()
    await stealth_async(page)
    
    yield
    
    # Shutdown: Clean up resources
    await browser.close()
    await playwright_instance.stop()

app = FastAPI(title="IsoMind Agent API", lifespan=lifespan)

# --- Schemas ---
class NavigateRequest(BaseModel):
    url: str

class Coordinates(BaseModel):
    x: int
    y: int

class TypeRequest(BaseModel):
    text: str

class EvaluateRequest(BaseModel):
    js_code: str

# --- Endpoints ---
@app.get("/v1/health/status")
async def health_check():
    if not page:
        raise HTTPException(status_code=503, detail="Browser not initialized")
    return {"status": "ok", "environment": "sandbox"}

@app.get("/v1/perception/screenshot")
async def capture_screenshot(marks: bool = True):
    if not page:
        raise HTTPException(status_code=503, detail="Browser not initialized")
    try:
        marks_mapping = {}
        if marks:
            js_payload = """
            () => {
                // Remove existing marks
                document.querySelectorAll('.isomind-mark').forEach(e => e.remove());
                
                let interactives = document.querySelectorAll('a, button, input, textarea, select, details, [tabindex]:not([tabindex="-1"]), [role="button"], [role="link"], [role="checkbox"], [role="menuitem"], [role="tab"]');
                let marks = {};
                let counter = 1;
                
                interactives.forEach(el => {
                    let rect = el.getBoundingClientRect();
                    // Check if visible
                    if (rect.width > 5 && rect.height > 5 && rect.top >= 0 && rect.left >= 0 && 
                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) && 
                        rect.right <= (window.innerWidth || document.documentElement.clientWidth)) {
                        
                        let style = window.getComputedStyle(el);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && style.opacity !== '0') {
                            let id = counter++;
                            let mark = document.createElement('div');
                            mark.className = 'isomind-mark';
                            mark.innerText = id;
                            mark.style.position = 'fixed';
                            mark.style.top = Math.max(0, rect.top - 10) + 'px';
                            mark.style.left = Math.max(0, rect.left - 10) + 'px';
                            mark.style.backgroundColor = 'red';
                            mark.style.color = 'white';
                            mark.style.border = '1px solid black';
                            mark.style.borderRadius = '3px';
                            mark.style.padding = '1px 3px';
                            mark.style.fontSize = '12px';
                            mark.style.fontWeight = 'bold';
                            mark.style.zIndex = '999999';
                            mark.style.pointerEvents = 'none';
                            document.body.appendChild(mark);
                            
                            marks[id] = {
                                x: Math.round(rect.left + (rect.width / 2)),
                                y: Math.round(rect.top + (rect.height / 2)),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                top: Math.round(rect.top),
                                left: Math.round(rect.left)
                            };
                        }
                    }
                });
                return marks;
            }
            """
            marks_mapping = await page.evaluate(js_payload)
            # Small sleep to ensure render
            await asyncio.sleep(0.1)

        # Capture a 1920x1080 screenshot directly from the DOM state
        screenshot_bytes = await page.screenshot()
        encoded = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        # Cleanup marks after screenshot so they don't break functionality
        if marks:
            await page.evaluate("() => { document.querySelectorAll('.isomind-mark').forEach(e => e.remove()); }")
            
        return {
            "image_base64": encoded,
            "marks_mapping": marks_mapping
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/action/browser/navigate")
async def browser_navigate(req: NavigateRequest):
    if not page:
        raise HTTPException(status_code=503, detail="Browser not initialized")
    try:
        await page.goto(req.url, wait_until="domcontentloaded")
        return {"status": "simulated_navigation", "url": req.url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/action/browser/evaluate")
async def browser_evaluate(req: EvaluateRequest):
    if not page:
        raise HTTPException(status_code=503, detail="Browser not initialized")
    try:
        result = await page.evaluate(req.js_code)
        return {"status": "evaluated", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/action/mouse/click")
async def mouse_click(coords: Coordinates):
    global current_mouse_x, current_mouse_y
    if not page:
        raise HTTPException(status_code=503, detail="Browser not initialized")
    try:
        await move_mouse_humanly(page, current_mouse_x, current_mouse_y, coords.x, coords.y)
        await asyncio.sleep(random.uniform(0.1, 0.3))
        await page.mouse.down()
        await asyncio.sleep(random.uniform(0.05, 0.15))
        await page.mouse.up()
        return {"status": "simulated_human_click", "x": coords.x, "y": coords.y}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/action/keyboard/type")
async def keyboard_type(req: TypeRequest):
    if not page:
        raise HTTPException(status_code=503, detail="Browser not initialized")
    try:
        await page.keyboard.type(req.text, delay=random.randint(50, 150))
        return {"status": "simulated_human_type", "text": req.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
