#!/bin/python

from flask import Flask, render_template, request, redirect
from apscheduler.schedulers.background import BackgroundScheduler
import subprocess
import sqlite3

app = Flask(__name__)

ESP32_IP = "192.168.18.131"  

def curl_get(path):
    result = subprocess.run(
        ["curl", "-s", f"http://{ESP32_IP}/{path}"],
        capture_output=True,
        text=True
    )
    try:
        result = int(result.stdout.strip())
    except:
        result = 0
    return result

def schedule_blind(hour, minute, position, job_id):
    scheduler.add_job(
        func=move_to,
        trigger='cron',
        hour=hour,
        minute=minute,
        args=[position],
        id=job_id,
        replace_existing=True  # replace if job with same id exists
    )

# Load all jobs from DB on startup
def load_schedules():
    conn = sqlite3.connect("roller_blinds.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, hour, minute, position FROM schedules")
    rows = cursor.fetchall()
    conn.close()
    for row in rows:
        schedule_blind(row[1], row[2], row[3], str(row[0]))

def move_to(position)
    cmd = ["curl", f"http://{ESP32_IP}/goto?pos={position}"]
    result = subprocess.run(cmd, capture_output=False, text=True, check=True)

slider_position = curl_get("get_current_pos") 
max_pos = curl_get("get_max_pos")
set_up_status = curl_get("get_set_up_status")

@app.route("/", methods=["GET", "POST"])
def index():
    global slider_position
    slider_position = int(curl_get("get_current_pos") / max_pos * 100)
    if request.method == "POST":
        if request.form.get("action") == "Move":
            slider_position = int(request.form.get("value", slider_position))
            cmd = ["curl", f"http://{ESP32_IP}/goto?pos={slider_position * max_pos / 100}"]
            result = subprocess.run(cmd, capture_output=False, text=True, check=True)
        elif request.form.get("action") == "Schedule":
            hour = int(request.form.get("hour"))
            minute = int(request.form.get("minute"))
            position = int(request.form.get("position"))
            print(hour, minute, position)

            conn = sqlite3.connect("roller_blinds.db")
            cursor = conn.cursor()
            cursor.execute("INSERT INTO schedules (hour, minute, position) VALUES (?, ?, ?)",
                           (hour, minute, position))
            conn.commit()
            conn.close()
        elif request.form.get("action") == "Delete":
            conn = sqlite3.connect("roller_blinds.db")
            cursor = conn.cursor()
            schedule_id = int(request.form.get("id"))
            cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
            conn.commit()
            conn.close()
            return redirect("/")

    conn = sqlite3.connect("roller_blinds.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM schedules")
    all_schedules = cursor.fetchall()
    conn.close()
    return render_template("index.html", slider_position=slider_position, schedules=all_schedules)

app.run(host="0.0.0.0", port=5000)
