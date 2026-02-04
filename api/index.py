from flask import Flask, request, jsonify, render_template, redirect
from app import generate_Content
from app.services.call_esp8266 import light_control
from app.history_manager import save_history
import logging
import os
import json
import datetime

app = Flask(__name__)
app.logger.setLevel(logging.INFO)
app.template_folder = os.path.join(os.path.dirname(__file__), "../templates")
app.static_folder = os.path.join(os.path.dirname(__file__), "../static")

@app.route("/", methods=["GET"])
def home():
    return render_template("home.html")

@app.route("/introduction", methods=["GET"])
def introduction():
    return render_template("introduction.html")

@app.route("/history", methods=["GET"])
def history():
    from app.history_manager import get_history
    history_data = get_history()
    return render_template("history.html", history=history_data)

@app.route("/bot", methods=["POST"])
def botController():
    req: dict = request.get_json()
    message = req.get("message", None)
    attchment = req.get('attchment', None)

    response = generate_Content(prompt=message, attchment=attchment) or "Xảy ra lỗi. Tôi là CHATBOT."
    app.logger.info("model message")
    return jsonify({
        "model": response
    }), 200

@app.route("/toggle_led1", methods=["GET", "POST"])
def toggle_led1():
    result = light_control(status="toggle", led="1")
    save_history({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "light_control",
        "action": "toggle",
        "led": "1",
        "result": result
    })
    return jsonify({"message": result["content"]})

@app.route("/toggle_led2", methods=["GET", "POST"])
def toggle_led2():
    result = light_control(status="toggle", led="2")
    save_history({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "light_control",
        "action": "toggle",
        "led": "2",
        "result": result
    })
    return jsonify({"message": result["content"]})

@app.route("/control_all", methods=["GET", "POST"])
def control_all():
    action = request.args.get("action", "off")
    if action not in ["on", "off"]:
        action = "off"
    result = light_control(status=action, led="all")
    save_history({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "light_control",
        "action": action,
        "led": "all",
        "result": result
    })
    return jsonify({"message": result["content"]})

@app.route("/get_status", methods=["GET"])
def get_status():
    # Get status for LED1 and LED2
    status1 = light_control(status="status", led="1")  # Need to modify light_control for status
    status2 = light_control(status="status", led="2")
    # But light_control returns content, need to parse or modify
    # For simplicity, assume we call directly
    # Actually, better to add a separate function or modify
    # For now, let's add a simple get_status function
    # But to keep simple, let's modify light_control to handle "status"
    # Wait, in code, for toggle it gets status first
    # Perhaps add a new function get_led_status(led)
    # But to save time, let's add route that calls light_control with toggle but doesn't change, just get status
    # Wait, better: add a new route that fetches status without changing
    # Since ESP8266 has /led1/status, we can call it directly
    import requests
    from app.services.call_esp8266 import ESP8266_HOST, REQUEST_TIMEOUT, MAX_RETRY
    statuses = {}
    for led in ["1", "2"]:
        url = f"https://{ESP8266_HOST}/led{led}/status"
        status = "unknown"
        for attempt in range(MAX_RETRY):
            try:
                response = requests.get(url, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    lines = response.text.strip().split("\n")
                    for line in lines:
                        if line.startswith(f"LED{led}="):
                            status = line.split("=")[1].upper()
                            break
                break
            except:
                pass
        statuses[f"led{led}"] = status
    return jsonify(statuses)

# Vercel expects the Flask app to be named 'app'