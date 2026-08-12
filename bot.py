import json
import os
from datetime import datetime

LOG_FILE = "logs.json"

def record_successful_login():
    # Load existing logs or fallback to default structure
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                data = json.load(f)
        except Exception:
            data = {"streak": 0, "history": []}
    else:
        data = {"streak": 0, "history": []}

    # Increment streak
    data["streak"] = data.get("streak", 0) + 1

    # Format current UTC time
    current_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    # Success entry
    new_entry = {
        "timestamp": current_time,
        "status": "Daily login successful",
        "passed": True
    }

    # Add to beginning of history array
    data["history"].insert(0, new_entry)

    # Write back to file
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print("Logged successful login to logs.json")

# --- Inside your Playwright logic ---
# async def main():
#     ...
#     if login_successful:
#         record_successful_login()
#         await page.screenshot(path="dashboard.png")
