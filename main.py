from flask import Flask, request, jsonify, render_template, redirect
from app import generate_Content
from app.services.call_esp8266 import light_control, get_led_status
from app.history_manager import save_history
import logging
import json
import datetime

_app = Flask(__name__)
_app.logger.setLevel(logging.INFO)
_app.template_folder = "templates"
_app.static_folder = "static"

@_app.route("/", methods = ["GET"])
def home():
    return render_template("home.html")

@_app.route("/introduction", methods = ["GET"])
def introduction():
    return render_template("introduction.html")

@_app.route("/history", methods=["GET"])
def history():
    try:
        with open("history.json", "r", encoding="utf-8") as f:
            history_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history_data = []
    return render_template("history.html", history=history_data)

@_app.route("/toggle_led1", methods=["GET", "POST"])
def toggle_led1():
    print("Toggle LED1 called")
    result = light_control(status="toggle", led="1")
    print(f"Result: {result}")
    # Lưu lịch sử
    save_history({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "light_control",
        "action": "toggle",
        "led": "1",
        "result": result
    })
    return jsonify({"message": result["content"]})

@_app.route("/toggle_led2", methods=["GET", "POST"])
def toggle_led2():
    print("Toggle LED2 called")
    result = light_control(status="toggle", led="2")
    print(f"Result: {result}")
    # Lưu lịch sử
    save_history({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "light_control",
        "action": "toggle",
        "led": "2",
        "result": result
    })
    return jsonify({"message": result["content"]})

@_app.route("/control_all", methods=["GET", "POST"])
def control_all():
    action = request.args.get("action", "off")
    print(f"Control all called with action: {action}")
    if action not in ["on", "off"]:
        action = "off"
    
    # Control each LED individually
    result1 = light_control(status=action, led="1")
    result2 = light_control(status=action, led="2")
    
    # Combine messages
    messages = []
    if result1["content"]:
        messages.append(f"Đèn 1: {result1['content']}")
    if result2["content"]:
        messages.append(f"Đèn 2: {result2['content']}")
    
    combined_message = " | ".join(messages) if messages else "Lỗi điều khiển tất cả đèn"
    
    print(f"Results: LED1 - {result1}, LED2 - {result2}")
    
    # Lưu lịch sử
    save_history({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "light_control",
        "action": action,
        "led": "all",
        "result": {
            "led1": result1,
            "led2": result2,
            "combined": combined_message
        }
    })
    
    return jsonify({"message": combined_message})

@_app.route("/get_status", methods=["GET"])
def get_status():
    statuses = get_led_status()
    return jsonify({"led1": statuses.get("1", "unknown"), "led2": statuses.get("2", "unknown")})
def botController():
    req: dict = request.get_json()
    message = req.get("message", None)
    attchment = req.get('attchment', None)

    response:str = generate_Content(prompt=message, attchment=attchment) or "Xảy ra lỗi. Tôi là CHATBOT."
    _app.logger.info("model message")
    # Lưu lịch sử chat
    save_history({
        "timestamp": datetime.datetime.now().isoformat(),
        "type": "chat",
        "user_message": message,
        "bot_response": response,
        "attachment": attchment is not None
    })
    return jsonify({
        "model": response
    }), 200


if __name__ == "__main__":
    _app.run(host="0.0.0.0", port=8080, debug=True)
    