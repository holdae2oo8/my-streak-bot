import os
import glob
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

LOG_FILE = "logs.json"
LOGIN_URL = "https://dashboard.interschoolscoding.com"
TARGET_URL = "https://dashboard.interschoolscoding.com/home/dashboard/student"

def cleanup_old_screenshots():
    """Deletes existing daily screenshots before running the current run."""
    screenshots = glob.glob("step_*.png") + ["dashboard.png"]
    for img in screenshots:
        if os.path.exists(img):
            try:
                os.remove(img)
                print(f"Removed old capture: {img}")
            except Exception as e:
                print(f"Error removing {img}: {e}")

def record_log(passed, status_message, steps_captured):
    """Appends workflow status and metadata to logs.json."""
    data = {"streak": 0, "history": []}
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            pass

    if passed:
        data["streak"] = data.get("streak", 0) + 1

    current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    new_entry = {
        "timestamp": current_time,
        "status": status_message,
        "passed": passed,
        "steps": steps_captured
    }

    if "history" not in data:
        data["history"] = []
    
    data["history"].insert(0, new_entry)

    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("Updated logs.json successfully.")

async def run_bot():
    cleanup_old_screenshots()
    
    username = os.getenv("BOT_USERNAME")
    password = os.getenv("BOT_PASSWORD")
    
    steps_taken = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        try:
            # ----------------------------------------------------
            # STEP 1: Login Page
            # ----------------------------------------------------
            print("Step 1: Navigating to login page...")
            await page.goto(LOGIN_URL, wait_until="networkidle")
            await page.screenshot(path="step_1.png")
            steps_taken.append({"step": 1, "label": "Login Page", "file": "step_1.png"})

            # ----------------------------------------------------
            # STEP 2: Input Credentials
            # ----------------------------------------------------
            print("Step 2: Entering login credentials...")
            await page.fill("input[placeholder='Enter username']", username)
            await page.fill("input[placeholder='Enter your password']", password)
            await page.screenshot(path="step_2.png")
            steps_taken.append({"step": 2, "label": "Credentials Entered", "file": "step_2.png"})

            # ----------------------------------------------------
            # STEP 3: Click Sign In & Capture Toast Notification
            # ----------------------------------------------------
            print("Step 3: Submitting login & capturing success notification...")
            await page.click("button:has-text('Sign in')")
            
            # Wait for the toast popup ("Login successful")
            try:
                await page.wait_for_selector("text=Login successful", timeout=5000)
            except Exception:
                await page.wait_for_timeout(1000) # Fallback timing if toast disappears fast
                
            await page.screenshot(path="step_3.png")
            steps_taken.append({"step": 3, "label": "Successful Login Notification", "file": "step_3.png"})

            # ----------------------------------------------------
            # STEP 4: Navigate / Wait for Final Student Dashboard
            # ----------------------------------------------------
            print("Step 4: Navigating to Student Dashboard...")
            await page.wait_for_url("**/home/dashboard/student**", timeout=10000)
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path="dashboard.png")
            steps_taken.append({"step": 4, "label": "Student Dashboard", "file": "dashboard.png"})

            print("All 4 captures taken successfully!")
            record_log(True, "Daily authentication and dashboard verification completed.", steps_taken)

        except Exception as e:
            print(f"Workflow interrupted: {e}")
            record_log(False, f"Execution failed: {str(e)}", steps_taken)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
