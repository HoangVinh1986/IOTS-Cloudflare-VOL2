import requests
import time
import os
import datetime
from ..history_manager import save_history

ESP8266_HOST = os.getenv("ESP8266_HOST", "10.141.235.134")
REQUEST_TIMEOUT = 5
MAX_RETRY = 3


def _send_request(url):
    print(f"Sending request to: {url}")
    for attempt in range(MAX_RETRY):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                print(f"Request successful: {response.text}")
                return response.text
        except Exception as e:
            print(f"Request failed (attempt {attempt+1}): {e}")
        time.sleep(1)
    print("All attempts failed")
    return None


def toggle_led(led):
    # Get current status
    url = f"https://{ESP8266_HOST}/led{led}/status"
    current_status = "off"
    for attempt in range(MAX_RETRY):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                lines = response.text.strip().split("\n")
                for line in lines:
                    if line.startswith(f"LED{led}="):
                        current_status = line.split("=")[1].lower()
                        print(f"Current status for LED{led}: {current_status}")
                        break
            break
        except Exception as e:
            print(f"Error getting status for LED{led}: {e}")
            time.sleep(1)
    # Toggle
    new_status = "on" if current_status == "off" else "off"
    print(f"Toggling LED{led} from {current_status} to {new_status}")
    _send_request(f"https://{ESP8266_HOST}/led{led}/{new_status}")
    return new_status


def format_response(action, led_statuses):
    if action.startswith("toggle"):
        led = action.split("_")[1]
        status = led_statuses[led]
        return f"Đèn {led} đã chuyển sang trạng thái {status.upper()}"
    elif action in ["on_all", "off_all"]:
        status = "ON" if "on" in action else "OFF"
        return f"Tất cả đèn đã {status.lower()}"
    return "Hành động hoàn thành"


def light_control(status, led):
    try:
        if status == "toggle":
            if led in ["1", "2"]:
                new_status = toggle_led(led)
                led_statuses = {led: new_status}
                response_content = f"Đèn {led} đã chuyển sang trạng thái {new_status.upper()}"
            else:
                return {"content": "Đèn không hợp lệ", "image": []}
        elif status in ["on", "off"]:
            if led == "all":
                _send_request(f"https://{ESP8266_HOST}/ledall/{status}")
                response_content = f"Tất cả đèn đã {status.upper()}"
            elif led in ["1", "2"]:
                _send_request(f"https://{ESP8266_HOST}/led{led}/{status}")
                response_content = f"Đèn {led} đã {status.upper()}"
            else:
                return {"content": "Đèn không hợp lệ", "image": []}
        else:
            return {"content": "Hành động không hợp lệ", "image": []}

        return {"content": response_content, "image": []}
    except Exception as e:
        return {"content": f"Lỗi điều khiển đèn: {str(e)}", "image": []}


def get_led_status():
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
        statuses[led] = status
    return statuses


def light_control_old(action):
    """
    action:
    - toggle_1
    - toggle_2
    - on_all
    - off_all
    """

    led_statuses = {}
    error_message = ""

    try:
        if action == "toggle_1":
            led_statuses["1"] = toggle_led("1")

        elif action == "toggle_2":
            led_statuses["2"] = toggle_led("2")

        elif action == "on_all":
            _send_request(f"https://{ESP8266_HOST}/ledall/on")
            led_statuses = {"1": "on", "2": "on"}

        elif action == "off_all":
            _send_request(f"https://{ESP8266_HOST}/ledall/off")
            led_statuses = {"1": "off", "2": "off"}

        else:
            return {"content": "Hành động không hợp lệ", "image": []}

        response_content = format_response(action, led_statuses)

        save_history({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "light_control",
            "action": action,
            "result": led_statuses
        })

        return {"content": response_content, "image": []}

    except Exception as e:
        error_message = str(e)
        return {"content": f"Lỗi điều khiển đèn: {error_message}", "image": []}
