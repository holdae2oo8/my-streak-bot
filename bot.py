import json
import os
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
    """Loads existing streak data and history from logs.json safely."""
    if os.path.exists(LOGS_FILE):
        try:
            with open(LOGS_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            pass
    return {"streak": 0, "last_login": "", "history": []}


def save_data(data):
    """Saves updated streak data and log history to logs.json."""
    with open(LOGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def perform_browser_login(max_retries=3, delay_between_retries=5):
    """Attempts login via Playwright with automatic retry logic on failure."""
    username = os.getenv("PORTAL_USERNAME", "holdae")
    password = os.getenv("PORTAL_PASSWORD", "Holdae@18")

    login_successful = False
    details = ""

    for attempt in range(1, max_retries + 1):
        print(f"\n--- Login Attempt {attempt}/{max_retries} ---")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800}
            )
            page = context.new_page()

            try:
                print(f"Navigating to {LOGIN_URL}...")
                page.goto(
                    LOGIN_URL, wait_until="domcontentloaded", timeout=30000
                )

                print("Filling credentials...")
                page.fill(
                    "input[type='text'], input[type='email'], input[name='username']",
                    username,
                )
                page.fill("input[type='password']", password)

                print("Submitting login form...")
                page.click(
                    "button[type='submit'], input[type='submit'], form button"
                )

                print(f"Waiting for redirect to {DASHBOARD_TARGET}...")
                page.wait_for_url(
                    lambda url: "dashboard/student" in url
                    or url == DASHBOARD_TARGET,
                    timeout=30000,
                )

                current_url = page.url
                if "dashboard/student" in current_url:
                    login_successful = True
                    details = f"Verified landing on student dashboard on attempt {attempt}."

                    # Capture fresh dashboard screenshot for home.html
                    page.screenshot(path=SCREENSHOT_FILE, full_page=False)
                    print(f"Saved dashboard preview to {SCREENSHOT_FILE}")

                    context.close()
                    browser.close()
                    break  # Success! Exit retry loop early
                else:
                    details = f"Landed on unexpected page: {current_url}"

            except PlaywrightTimeoutError:
                details = f"Attempt {attempt} timed out reaching dashboard."
            except Exception as e:
                details = f"Attempt {attempt} failed: {str(e)}"
            finally:
                context.close()
                browser.close()

        if not login_successful and attempt < max_retries:
            print(
                f"Attempt {attempt} failed. Retrying in {delay_between_retries}s..."
            )
            time.sleep(delay_between_retries)

    return login_successful, details


def run_automated_login():
    """Calculates streaks and appends execution status to log history."""
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
    data["history"].insert(0, log_entry)

    save_data(data)
    print(f"\nFinal Result: {status_msg}")


if __name__ == "__main__":
    run_automated_login()
