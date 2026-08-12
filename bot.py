import json
import os
import sys
import time
from datetime import date, datetime, timedelta
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

LOGS_FILE = "logs.json"
SCREENSHOT_FILE = "dashboard.png"
LOGIN_URL = "https://dashboard.interschoolscoding.com/"
DASHBOARD_TARGET = (
    "https://dashboard.interschoolscoding.com/home/dashboard/student"
)


def load_data():
    """Loads existing streak data and history from logs.json with corruption fallbacks."""
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"Warning: Failed to read {LOGS_FILE} ({e}). Initializing clean state.")
            
    return {"streak": 0, "last_login": "", "history": []}


def save_data(data):
    """Safely saves updated streak data and history to logs.json."""
    try:
        with open(LOGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        print(f"Error: Could not write to {LOGS_FILE}: {e}")


def perform_browser_login(max_retries=3, delay_between_retries=5):
    """Robust browser login automation with fallback selectors, retries, and screenshot safeguards."""
    # Pull credentials from environment variables (fallback to local defaults if missing)
    username = os.getenv("PORTAL_USERNAME", "holdae")
    password = os.getenv("PORTAL_PASSWORD", "Holdae@18")

    login_successful = False
    details = ""

    for attempt in range(1, max_retries + 1):
        print(f"\n--- [Attempt {attempt}/{max_retries}] Starting Playwright Browser Context ---")

        try:
            with sync_playwright() as p:
                # Launch Chromium with anti-detection args
                browser = p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-dev-shm-usage"]
                )
                context = browser.new_context(
                    viewport={"width": 1280, "height": 800},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()

                print(f"Navigating to {LOGIN_URL}...")
                page.goto(LOGIN_URL, wait_until="domcontentloaded", timeout=45000)

                # Wait for form elements to become interactive
                username_selector = "input[type='text'], input[type='email'], input[name='username'], input[id='username']"
                password_selector = "input[type='password'], input[name='password']"
                submit_selector = "button[type='submit'], input[type='submit'], form button"

                page.wait_for_selector(username_selector, timeout=15000)
                
                print("Injecting login credentials...")
                page.fill(username_selector, username)
                page.fill(password_selector, password)

                print("Submitting authentication form...")
                page.click(submit_selector)

                print(f"Waiting for student dashboard redirection...")
                page.wait_for_url(
                    lambda url: "dashboard" in url or "student" in url or url == DASHBOARD_TARGET,
                    timeout=30000
                )

                current_url = page.url
                if "dashboard" in current_url or "student" in current_url:
                    login_successful = True
                    details = f"Successfully landed on dashboard URL: {current_url} (Attempt {attempt})"

                    # Capture fresh dashboard screenshot for home.html
                    page.wait_for_timeout(2000) # Ensure full rendering
                    page.screenshot(path=SCREENSHOT_FILE, full_page=False)
                    print(f"Saved dashboard preview to {SCREENSHOT_FILE}")

                    context.close()
                    browser.close()
                    break  # Success! Break retry loop
                else:
                    details = f"Landed on unexpected URL: {current_url}"

        except PlaywrightTimeoutError:
            details = f"Attempt {attempt} timed out waiting for portal response/redirect."
            print(details)
        except Exception as e:
            details = f"Attempt {attempt} failed due to unexpected error: {str(e)}"
            print(details)

        if not login_successful and attempt < max_retries:
            print(f"Retrying in {delay_between_retries} seconds...")
            time.sleep(delay_between_retries)

    return login_successful, details


def run_automated_login():
    """Manages streak state calculation and commits updates to execution history."""
    data = load_data()
    today = date.today()
    today_str = today.isoformat()
    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    success, details = perform_browser_login()

    if success:
        last_login_str = data.get("last_login", "")

        if last_login_str:
            last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()
            if last_login_date == today:
                status_msg = f"Dashboard login verified. Streak active! ({details})"
            elif last_login_date == today - timedelta(days=1):
                data["streak"] += 1
                data["last_login"] = today_str
                status_msg = f"Login verified! Streak increased to {data['streak']}. ({details})"
            else:
                data["streak"] = 1
                data["last_login"] = today_str
                status_msg = f"Login verified! Streak reset to 1. ({details})"
        else:
            data["streak"] = 1
            data["last_login"] = today_str
            status_msg = f"First login verified! Streak started at 1. ({details})"
    else:
        status_msg = f"Login check failed after retries: {details}"

    log_entry = {
        "timestamp": now_timestamp,
        "status": status_msg,
        "current_streak": data["streak"],
        "passed": success,
    }
    
    # Prepend latest execution log
    data["history"].insert(0, log_entry)

    # Save output to disk
    save_data(data)
    print(f"\n[Execution Summary] {status_msg}")

    # Exit cleanly
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    run_automated_login()
