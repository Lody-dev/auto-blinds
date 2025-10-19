#!/bin/python

from flask import Flask, render_template, request
import subprocess

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

slider_position = curl_get("get_current_pos")
max_pos = curl_get("get_max_pos")
set_up_status = curl_get("get_set_up_status")

@app.route("/", methods=["GET", "POST"])
def index():
    global slider_position
    slider_position = int(request.form.get("value", slider_position))
    sent_goto = (slider_position * max_pos) / 100;
    if request.method == "POST":
        cmd = ["curl", f"http://{ESP32_IP}/goto?pos={sent_goto}"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("Curl output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Curl failed:", e)
    return render_template("index.html", slider_position=slider_position)


app.run(host="0.0.0.0", port=5000)
