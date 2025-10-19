Auto-Blinds:
    firmware for ESP32 and a Flask server providing a web UI + REST API to control blinds. 
    Server will expose endpoints for open/close/position and persist last-known position to a SQLite DB.


# Server quick start

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python run.py

