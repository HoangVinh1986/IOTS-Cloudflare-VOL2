import requests
import time
import os
import datetime
from ..history_manager import save_history

# ESP8266 Configuration (Cloudflare Tunnel or Local IP)
ESP8266_HOST = os.getenv("ESP8266_HOST", "10.141.235.134")  # Default to local IP; set to domain for production
REQUEST_TIMEOUT = 5
MAX_RETRY = 3

def light_control(status="off", led="all"):
    try:
        status = status.lower().strip()
        led = led.lower().strip()

        if status not in ["on", "off", "toggle"]:
            status = "off"

        if led not in ["1", "2", "all"]:
            led = "all"

        leds_to_control = ["1", "2"] if led == "all" else [led]

        led_statuses = {}
        error_message = ""

        if led == "all":
            # For all, use /ledall/
            url = f"https://{ESP8266_HOST}/ledall/{status}"
            led_status = None
            for attempt in range(MAX_RETRY):
                try:
                    print(f"[light_control] Attempt {attempt+1}: {url}")
                    response = requests.get(url, timeout=REQUEST_TIMEOUT)

                    if response.status_code == 200:
                        lines = response.text.strip().split("\n")
                        for line in lines:
                            if "LED1=" in line:
                                led_status = "OK"  # Assume success
                                break

                except requests.exceptions.Timeout:
                    error_message = "Timeout"
                except requests.exceptions.ConnectionError:
                    error_message = "Không kết nối được ESP qua Cloudflare"
                except Exception as e:
                    error_message = str(e)

                time.sleep(1)

            led_statuses["1"] = led_status
            led_statuses["2"] = led_status
        else:
            # For individual LEDs
            for l in leds_to_control:
                if status == "toggle":
                    # First get current status
                    url_get = f"https://{ESP8266_HOST}/led{l}/status"
                    current_status = None
                    for attempt in range(MAX_RETRY):
                        try:
                            response = requests.get(url_get, timeout=REQUEST_TIMEOUT)
                            if response.status_code == 200:
                                lines = response.text.strip().split("\n")
                                for line in lines:
                                    if line.startswith(f"LED{l}="):
                                        current_status = line.split("=")[1].lower()
                                        break
                            break
                        except:
                            pass
                    if current_status == "on":
                        new_status = "off"
                    elif current_status == "off":
                        new_status = "on"
                    else:
                        new_status = "off"  # default
                else:
                    new_status = status

                url = f"https://{ESP8266_HOST}/led{l}/{new_status}"
                led_status = None

                for attempt in range(MAX_RETRY):
                    try:
                        print(f"[light_control] Attempt {attempt+1}: {url}")
                        response = requests.get(url, timeout=REQUEST_TIMEOUT)

                        if response.status_code == 200:
                            lines = response.text.strip().split("\n")
                            for line in lines:
                                if line.startswith(f"LED{l}="):
                                    led_status = line.split("=")[1]
                                    break
                            break

                    except requests.exceptions.Timeout:
                        error_message = "Timeout"
                    except requests.exceptions.ConnectionError:
                        error_message = "Không kết nối được ESP qua Cloudflare"
                    except Exception as e:
                        error_message = str(e)

                    time.sleep(1)

                led_statuses[l] = led_status

        if all(led_statuses.values()):
            if status == "toggle":
                action_text = "chuyển đổi"
            else:
                action_text = "bật" if status == "on" else "tắt"
            led_text = "tất cả đèn" if led == "all" else f"đèn {led}"
            statuses_text = ", ".join([f"đèn {k}: {v}" for k, v in led_statuses.items()])
            response_content = f"Đã {action_text} {led_text}. Trạng thái: {statuses_text}."
        else:
            response_content = f"Lỗi điều khiển đèn: {error_message}"

        # Lưu lịch sử
        save_history({
            "timestamp": datetime.datetime.now().isoformat(),
            "type": "light_control",
            "action": status,
            "led": led,
            "result": {
                "content": response_content,
                "statuses": led_statuses,
                "error": error_message
            }
        })

        return {
            "content": response_content,
            "image": []
        }
    except Exception as e:
        print(f"Unexpected error in light_control: {e}")
def get_led_status(led="all"):
    try:
        led = led.lower().strip()

        if led not in ["1", "2", "all"]:
            led = "all"

        leds_to_check = ["1", "2"] if led == "all" else [led]

        led_statuses = {}

        for l in leds_to_check:
            url_get = f"https://{ESP8266_HOST}/led{l}/status"
            current_status = "unknown"
            for attempt in range(MAX_RETRY):
                try:
                    response = requests.get(url_get, timeout=REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        lines = response.text.strip().split("\n")
                        for line in lines:
                            if line.startswith(f"LED{l}="):
                                current_status = line.split("=")[1].lower()
                                break
                    break
                except:
                    pass
            led_statuses[l] = current_status

        return led_statuses
    except Exception as e:
        print(f"Error getting LED status: {e}")
        return {"1": "unknown", "2": "unknown"}
