from flask import Flask, request, jsonify, send_file
import os, csv, time

app = Flask(__name__)

CSV_PATH = "data.csv"
API_TOKEN = "esp32-clima-12345"  # pon algo aleatorio

# crea el CSV si no existe
if not os.path.exists(CSV_PATH):
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(["ts_epoch","device","temp_c","hum_pct"])

@app.get("/")
def home():
    return "API ESP32 OK → POST /ingest   |   Descarga: /data.csv"

@app.post("/ingest")
def ingest():
    # seguridad simple por encabezado
    if request.headers.get("X-API-KEY") != API_TOKEN:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    j = request.get_json(silent=True)
    if not j: 
        return jsonify({"ok": False, "error": "invalid json"}), 400

    try:
        ts = int(j.get("ts_epoch", time.time()))
        dev = str(j.get("device","esp32"))
        t  = float(j["temp_c"])
        h  = float(j["hum_pct"])
    except Exception:
        return jsonify({"ok": False, "error": "bad fields"}), 400

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=';').writerow([ts, dev, t, h])

    return jsonify({"ok": True})

@app.get("/data.csv")
def data_csv():
    return send_file(CSV_PATH, as_attachment=True)

# para correr local
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
