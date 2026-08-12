import json
import os
from datetime import date, datetime, timedelta
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

LOGS_FILE = "logs.json"
LOGIN_URL = "https://dashboard.interschoolscoding.com/"
DASHBOARD_TARGET = (
    "https://dashboard.interschoolscoding.com/home/dashboard/student"
)


def load_data():
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f:
            return json.load(f)
    return {"streak": 0, "last_login": "", "history": []}


def save_data(data):
    with open(LOGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def perform_browser_login():
    username = os.getenv("PORTAL_USERNAME", "holdae")
    password = os.getenv("PORTAL_PASSWORD", "Holdae@18")

    login_successful = False
    details = ""

    with sync_playwright() as p:
        # Launch headless browser (no GUI window, runs in cloud)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        try:
            print(f"Navigating to {LOGIN_URL}...")
            page.goto(LOGIN_URL, wait_until="networkidle", timeout=30000)

            # Locate input fields dynamically by common selectors
            print("Filling login credentials...")
            page.fill(
                "input[type='text'], input[type='email'], input[name='username']",
                username,
            )
            page.fill("input[type='password']", password)

            # Submit the form
            page.click(
                "button[type='submit'], input[type='submit'], form button"
            )

            # Wait for navigation to complete and verify target dashboard URL
            print(f"Waiting for redirection to {DASHBOARD_TARGET}...")
            page.wait_for_url(
                lambda url: "dashboard/student" in url or url == DASHBOARD_TARGET,
                timeout=30000,
            )

            current_url = page.url
            if "dashboard/student" in current_url:
                login_successful = True
                details = f"Verified landing on student dashboard ({current_url})."
            else:
                details = (
                    f"Logged in, but landed on unexpected page: {current_url}"
                )

        except PlaywrightTimeoutError:
            details = "Login timed out or failed to reach dashboard URL."
        except Exception as e:
            details = f"Browser automation error: {str(e)}"
        finally:
            # Ensure browser context is strictly closed after reading the page
            print("Closing browser session...")
            context.close()
            browser.close()

    return login_successful, details


def run_automated_login():
    data = load_data()
    today = date.today()
    today_str = today.isoformat()
    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Perform browser verification
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
        status_msg = f"Login check failed: {details}"

    # Record log entry
    log_entry = {
        "timestamp": now_timestamp,
        "status": status_msg,
        "current_streak": data["streak"],
    }
    data["history"].insert(0, log_entry)

    save_data(data)
    print(status_msg)


if __name__ == "__main__":
    run_automated_login()
