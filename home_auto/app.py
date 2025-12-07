from flask import Flask, request, jsonify
import joblib
import concurrent.futures
import traceback
import logging
import time
from datetime import datetime
import requests   

app = Flask(__name__)

ESP_IP = "10.168.187.212"      
ESP_TIMEOUT = 2               



class OnlyTimeFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        return datetime.now().strftime("%H:%M:%S")

formatter = OnlyTimeFormatter("%(asctime)s | %(levelname)s | %(message)s")

error_handler = logging.FileHandler("error.log")
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.setLevel(logging.ERROR)
logger.addHandler(error_handler)


def log_error(msg, **details):
    detail_str = " | ".join([f"{k}={v}" for k, v in details.items()])
    logging.error(f"{msg} | {detail_str}")



try:
    model = joblib.load("intent_model.pkl")
except Exception as e:
    log_error("MODEL LOAD FAILED", error=str(e))
    model = None



def predict_model(text):
    if not model:
        raise ValueError("Model not loaded")
    return model.predict([text])[0]


def call_esp_send_cmd(cmd):
    try:
        url = f"http://{ESP_IP}/setcmd/{cmd}"
        resp = requests.get(url, timeout=ESP_TIMEOUT)

        if resp.status_code == 200:
            return True      # ESP SUCCESS
        else:
            log_error("ESP NON-200 RESPONSE", cmd=cmd, status=resp.status_code)
            return False
    except Exception as e:
        log_error("ESP CALL FAILED", cmd=cmd, error=str(e))
        return False



@app.route("/", methods=["POST"])
def predict():
    data = request.json or {}
    text = data.get("text", "")

    if text.strip() == "":
        log_error("EMPTY INPUT RECEIVED", input=text)
        return jsonify({"prediction": ""})

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(predict_model, text)

        try:
            prediction = future.result(timeout=5)

            if prediction is None or str(prediction).strip() == "" or str(prediction).lower() == "null":
                log_error("NULL / EMPTY PREDICTION", input=text, output=str(prediction))
                return jsonify({"prediction": ""})

            cmd = str(prediction).strip()

           
            esp_ok = call_esp_send_cmd(cmd)

            if esp_ok:
                return jsonify({"prediction": cmd})
            else:
                return jsonify({"prediction": ""})

        except concurrent.futures.TimeoutError:
            log_error("MODEL TIMEOUT", input=text, timeout="5s")
            return jsonify({"prediction": ""})

        except Exception as model_error:
            log_error("MODEL ERROR",
                      input=text,
                      error=str(model_error),
                      traceback=traceback.format_exc())
            return jsonify({"prediction": ""})



if __name__ == "__main__":
    print("Flask server running on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
