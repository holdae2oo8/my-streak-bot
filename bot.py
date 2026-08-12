from datetime import datetime, date, timedelta
import json
import os

LOGS_FILE = "logs.json"


def load_data():
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "r") as f:
            return json.load(f)
    return {"streak": 0, "last_login": "", "history": []}


def save_data(data):
    with open(LOGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def run_automated_login():
    data = load_data()

    today = date.today()
    today_str = today.isoformat()
    now_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    last_login_str = data.get("last_login", "")

    if last_login_str:
        last_login_date = datetime.strptime(last_login_str, "%Y-%m-%d").date()

        if last_login_date == today:
            # Already logged in today
            status_msg = "Automated login check run (already logged in today)."
        elif last_login_date == today - timedelta(days=1):
            # Consecutive day -> increment streak
            data["streak"] += 1
            data["last_login"] = today_str
            status_msg = (
                f"Automated login successful! Streak incremented to {data['streak']}."
            )
        else:
            # Missed a day -> reset streak to 1
            data["streak"] = 1
            data["last_login"] = today_str
            status_msg = "Streak reset due to missed day. New streak started at 1."
    else:
        # First-time run
        data["streak"] = 1
        data["last_login"] = today_str
        status_msg = "First automated login recorded! Streak started at 1."

    # Record log entry
    log_entry = {
        "timestamp": now_timestamp,
        "status": status_msg,
        "current_streak": data["streak"],
    }
    data["history"].insert(0, log_entry)  # Latest logs first

    save_data(data)
    print(status_msg)


if __name__ == "__main__":
    run_automated_login()