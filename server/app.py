#!/bin/python

from flask import Flask, render_template, request
import subprocess

app = Flask(__name__)

slider_position = 50

ESP32_IP = "192.168.18.131"  

@app.route("/", methods=["GET", "POST"])
def index():
    global slider_position
    if request.method == "POST":
        slider_position = int(request.form.get("value", slider_position))
        cmd = ["curl", f"http://{ESP32_IP}/goto?pos={slider_position}"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print("Curl output:", result.stdout)
        except subprocess.CalledProcessError as e:
            print("Curl failed:", e)
    return render_template("index.html", slider_position=slider_position)

app.run(host="0.0.0.0", port=5000)
