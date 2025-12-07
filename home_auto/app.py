# from flask import Flask, request, jsonify
# import joblib
# import concurrent.futures
# import traceback
# import logging
# import time
# from datetime import datetime
# import requests   

# app = Flask(__name__)

# ESP_IP = "10.168.187.212"      
# ESP_TIMEOUT = 2               



# class OnlyTimeFormatter(logging.Formatter):
#     def formatTime(self, record, datefmt=None):
#         return datetime.now().strftime("%H:%M:%S")

# formatter = OnlyTimeFormatter("%(asctime)s | %(levelname)s | %(message)s")

# error_handler = logging.FileHandler("error.log")
# error_handler.setLevel(logging.ERROR)
# error_handler.setFormatter(formatter)

# logger = logging.getLogger()
# logger.setLevel(logging.ERROR)
# logger.addHandler(error_handler)


# def log_error(msg, **details):
#     detail_str = " | ".join([f"{k}={v}" for k, v in details.items()])
#     logging.error(f"{msg} | {detail_str}")



# try:
#     model = joblib.load("intent_model.pkl")
# except Exception as e:
#     log_error("MODEL LOAD FAILED", error=str(e))
#     model = None



# def predict_model(text):
#     if not model:
#         raise ValueError("Model not loaded")
#     return model.predict([text])[0]


# def call_esp_send_cmd(cmd):
#     try:
#         url = f"http://{ESP_IP}/setcmd/{cmd}"
#         resp = requests.get(url, timeout=ESP_TIMEOUT)

#         if resp.status_code == 200:
#             return True      # ESP SUCCESS
#         else:
#             log_error("ESP NON-200 RESPONSE", cmd=cmd, status=resp.status_code)
#             return False
#     except Exception as e:
#         log_error("ESP CALL FAILED", cmd=cmd, error=str(e))
#         return False



# @app.route("/", methods=["POST"])
# def predict():
#     data = request.json or {}
#     text = data.get("text", "")

#     if text.strip() == "":
#         log_error("EMPTY INPUT RECEIVED", input=text)
#         return jsonify({"prediction": ""})

#     with concurrent.futures.ThreadPoolExecutor() as executor:
#         future = executor.submit(predict_model, text)

#         try:
#             prediction = future.result(timeout=5)

#             if prediction is None or str(prediction).strip() == "" or str(prediction).lower() == "null":
#                 log_error("NULL / EMPTY PREDICTION", input=text, output=str(prediction))
#                 return jsonify({"prediction": ""})

#             cmd = str(prediction).strip()

           
#             esp_ok = call_esp_send_cmd(cmd)

#             if esp_ok:
#                 return jsonify({"prediction": cmd})
#             else:
#                 return jsonify({"prediction": ""})

#         except concurrent.futures.TimeoutError:
#             log_error("MODEL TIMEOUT", input=text, timeout="5s")
#             return jsonify({"prediction": ""})

#         except Exception as model_error:
#             log_error("MODEL ERROR",
#                       input=text,
#                       error=str(model_error),
#                       traceback=traceback.format_exc())
#             return jsonify({"prediction": ""})



# if __name__ == "__main__":
#     print("Flask server running on http://127.0.0.1:5000")
#     app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)

from flask import Flask, request, jsonify
import joblib
import concurrent.futures
import traceback
import time
from datetime import datetime
import requests
import socket    # NEW

app = Flask(__name__, static_url_path='', static_folder='.')

ESP_IP = "10.168.187.212"
ESP_TIMEOUT = 2


# --------------------------------------------------
# NEW : Find LAN IP (Windows / Linux automatically)
# --------------------------------------------------
def get_lan_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "0.0.0.0"


# --------------------------------------------------
# NEW : Post IP to your Config Server
# --------------------------------------------------
def send_device_config():
    device_ip = get_lan_ip()

    payload = {
        "deviceName": "rasPi",
        "wifiName": "Sorry",
        "wifiPassword": "aaaaaaaa",
        "deviceIp": device_ip
    }

    try:
        res = requests.post(
            "https://internetprotocal.onrender.com/config",
            json=payload,
            timeout=5
        )
        print("CONFIG POST RESPONSE:", res.status_code, res.text)
    except Exception as e:
        print("CONFIG POST FAILED:", e)


# --------------------------------------------------
# REAL MODEL CODE (present but unused)
# --------------------------------------------------
try:
    model = joblib.load("intent_model.pkl")
except:
    model = None

def predict_model(text):
    try:
        return model.predict([text])[0] if model else ""
    except:
        return ""

def call_esp_send_cmd(cmd):
    try:
        requests.get(f"http://{ESP_IP}/setcmd/{cmd}", timeout=ESP_TIMEOUT)
    except:
        pass
    return False


# --------------------------------------------------
# MIMIC ROUTE — ALWAYS SAFE
# --------------------------------------------------
@app.route("/pridict", methods=["POST"])
def mimic_predict():

    try:
        data = request.json or {}
        text = data.get("text", "")
        print(f"Incoming text: {text}")

    except:
        pass

    return jsonify({})


# --------------------------------------------------
# STATIC SITE SUPPORT
# --------------------------------------------------
@app.route("/")
def serve_index():
    return app.send_static_file("index.html")


if __name__ == "__main__":
    print("Mimic Flask server running on http://127.0.0.1:5000")

    # ------------------------
    # NEW : Send config at startup
    # ------------------------
    send_device_config()

    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
