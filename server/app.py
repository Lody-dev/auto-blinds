from flask import Flask, render_template, request, redirect
from flask_apscheduler import APScheduler
import subprocess
from datetime import datetime
import sqlite3

app = Flask(__name__)
scheduler = APScheduler()

ESP32_IP = "Your esp32 local IP"

def curl_get(path):
    result = subprocess.run(
        ["curl", "-s", f"http://{ESP32_IP}/{path}"],
        capture_output=True,
        text=True
    )
    try:
        return int(result.stdout.strip())
    except:
        return 0

#def move_to(position):
#    """Actual job executed by the scheduler"""
#    print(f"[{datetime.now()}] Moving blinds to {position}")
#    subprocess.run(["curl", f"http://{ESP32_IP}/goto?pos={position}"],
#                   capture_output=False, text=True, check=False)
def move_to(position):
    """Actual job executed by the scheduler"""
    max_pos = curl_get("get_max_pos") or 1
    raw_position = int(position * max_pos / 100)  # scale only here
    print(f"[{datetime.now()}] Moving blinds to {position}% -> raw {raw_position}")
    subprocess.run(["curl", f"http://{ESP32_IP}/goto?pos={raw_position}"],
                   capture_output=False, text=True, check=False)



def add_schedule_to_scheduler(job_id, hour, minute, position):
    """Registers job in APScheduler"""
    job_name = f"job_{job_id}"
    scheduler.add_job(
        id=job_name,
        func=move_to,
        trigger="cron",
        hour=hour,
        minute=minute,
        args=[position],
        replace_existing=True
    )
    print(f"Scheduled job {job_name} at {hour:02d}:{minute:02d} -> {position}")


def load_schedules_from_db():
    """Reload all jobs when the app starts"""
    conn = sqlite3.connect("roller_blinds.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS schedules (id INTEGER PRIMARY KEY AUTOINCREMENT, hour INT, minute INT, position INT)")
    for row in cursor.execute("SELECT id, hour, minute, position FROM schedules"):
        add_schedule_to_scheduler(*row)
    conn.close()


@app.route("/", methods=["GET", "POST"])
def index():
    conn = sqlite3.connect("roller_blinds.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS schedules (id INTEGER PRIMARY KEY AUTOINCREMENT, hour INT, minute INT, position INT)")

    max_pos = curl_get("get_max_pos") or 1
    slider_position = int(curl_get("get_current_pos") / max_pos * 100)

    if request.method == "POST":
        action = request.form.get("action")

        if action == "Move":
            slider_position = int(request.form.get("value", slider_position))
            move_to(int(slider_position))

        elif action == "Schedule":
            hour = int(request.form.get("hour"))
            minute = int(request.form.get("minute"))
            position = int(request.form.get("position"))

            cursor.execute("INSERT INTO schedules (hour, minute, position) VALUES (?, ?, ?)",
                           (hour, minute, position))
            conn.commit()
            job_id = cursor.lastrowid
            add_schedule_to_scheduler(job_id, hour, minute, position)

        elif action == "Delete":
            schedule_id = int(request.form.get("id"))
            cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
            conn.commit()

            # remove from APScheduler too
            job_name = f"job_{schedule_id}"
            if scheduler.get_job(job_name):
                scheduler.remove_job(job_name)

            return redirect("/")

    cursor.execute("SELECT * FROM schedules")
    all_schedules = cursor.fetchall()
    conn.close()
    return render_template("index.html", slider_position=slider_position, schedules=all_schedules)


if __name__ == "__main__":
    scheduler.init_app(app)
    scheduler.start()
    load_schedules_from_db()  # load existing jobs
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=False)
