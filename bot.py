import os
import glob
import json
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright

LOG_FILE = "logs.json"
TARGET_URL = "https://dashboard.interschoolscoding.com/home/dashboard/student"
LOGIN_URL = "https://dashboard.interschoolscoding.com"

def cleanup_old_screenshots():
    """Deletes old step screenshots from the workspace before taking new ones."""
    screenshots = glob.glob("step_*.png") + ["dashboard.png"]
    for img in screenshots:
        if os.path.exists(img):
            try:
                os.remove(img)
                print(f"Removed old screenshot: {img}")
            except Exception as e:
                print(f"Error removing {img}: {e}")

def record_log(passed, status_message, steps_captured):
    """Appends workflow status and metadata to logs.json."""
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {"streak": 0, "history": []}
    else:
        data = {"streak": 0, "history": []}

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
        context = await browser.new_context(viewport={"width": 1280, "height": 720})
        page = await context.new_page()

        try:
            # Step 1: Open Login Page
            print("Step 1: Navigating to portal...")
            await page.goto(LOGIN_URL, wait_until="networkidle")
            await page.screenshot(path="step_1.png")
            steps_taken.append({"step": 1, "label": "Login Page Loaded", "file": "step_1.png"})

            # Step 2: Fill Credentials
            print("Step 2: Entering login credentials...")
            await page.fill("input[name='email']", username) if await page.query_selector("input[name='email']") else await page.fill("input[type='text']", username)
            await page.fill("input[type='password']", password)
            await page.screenshot(path="step_2.png")
            steps_taken.append({"step": 2, "label": "Credentials Filled", "file": "step_2.png"})

            # Step 3: Click Submit / Login Button
            print("Step 3: Submitting login form...")
            submit_btn = await page.query_selector("button[type='submit']") or await page.query_selector("button")
            if submit_btn:
                await submit_btn.click()
            await page.wait_for_timeout(3000)
            await page.screenshot(path="step_3.png")
            steps_taken.append({"step": 3, "label": "Authentication Submitted", "file": "step_3.png"})

            # Step 4: Navigate to Final Target Page (Student Dashboard)
            print("Step 4: Accessing Student Dashboard...")
            await page.goto(TARGET_URL, wait_until="networkidle")
            await page.screenshot(path="dashboard.png")
            steps_taken.append({"step": 4, "label": "Student Dashboard Active", "file": "dashboard.png"})

            print("All 4 steps completed successfully!")
            record_log(True, "Daily login and student dashboard verify successful", steps_taken)

        except Exception as e:
            print(f"Error during execution: {e}")
            record_log(False, f"Execution failed: {str(e)}", steps_taken)
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run_bot())
