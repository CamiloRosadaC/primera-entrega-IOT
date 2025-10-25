from flask import Flask, request, jsonify, send_file, Response, redirect, url_for
import os, csv, time
from datetime import datetime

app = Flask(__name__)

CSV_PATH = "data.csv"
API_TOKEN = "esp32-clima-12345"  # igual que en el ESP32

# --- crear CSV si no existe ---
def ensure_csv():
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
            f.write("sep=;\n")
            writer = csv.writer(f, delimiter=';')
            writer.writerow(["ts_epoch","device","temp_c","hum_pct"])
ensure_csv()

@app.get("/")
def home():
    return redirect(url_for("dashboard"))

@app.get("/dashboard")
def dashboard():
    try:
        n = int(request.args.get("n", 20))
    except ValueError:
        n = 20

    rows = []
    header = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter=';')
        first = next(reader, None)
        if first and first[0].lower().startswith("sep="):
            header = next(reader, [])
        else:
            header = first or []
        for r in reader:
            rows.append(r)

    last_rows = rows[-n:] if n > 0 else rows

    def fmt_row(r):
        try:
            ts = int(float(r[0]))
            human = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            human = "—"
        device = r[1] if len(r) > 1 else "—"
        temp = r[2] if len(r) > 2 else "—"
        hum  = r[3] if len(r) > 3 else "—"
        return [human, device, temp, hum]

    table_rows = [fmt_row(r) for r in last_rows]

    html = f"""
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Dashboard ESP32</title>
  <meta http-equiv="refresh" content="5">
  <style>
    body{{font-family:system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;margin:24px;color:#111}}
    h1{{margin:0 0 6px}}
    .muted{{color:#666;margin:0 0 18px}}
    .actions{{display:flex;gap:12px;margin:12px 0 20px;flex-wrap:wrap}}
    a.btn, button.btn{{display:inline-block;padding:10px 14px;border-radius:10px;border:1px solid #ddd;
      text-decoration:none;color:#111;background:#fafafa;cursor:pointer}}
    a.btn:hover, button.btn:hover{{background:#f0f0f0}}
    table{{border-collapse:collapse;width:100%;max-width:960px}}
    th,td{{border:1px solid #e5e5e5;padding:8px 10px;text-align:left}}
    th{{background:#f7f7f7}}
    .right{{text-align:right}}
    .note{{font-size:12px;color:#666;margin-top:6px}}
    .inputs{{display:flex;align-items:center;gap:8px}}
    input[type=number]{{width:80px;padding:6px 8px;border:1px solid #ccc;border-radius:8px}}
  </style>
</head>
<body>
  <h1>Dashboard ESP32</h1>
  <p class="muted">Lecturas de temperatura y humedad (actualiza cada 5 s)</p>

  <div class="actions">
    <a class="btn" href="/data.csv" download>⬇️ Descargar CSV</a>
    <form class="inputs" action="/dashboard" method="get">
      <label>Mostrar últimas</label>
      <input type="number" name="n" value="{n}" min="1" step="1">
      <button class="btn" type="submit">Actualizar</button>
    </form>
  </div>

  <table>
    <thead>
      <tr><th>Fecha/Hora</th><th>Dispositivo</th><th class="right">Temperatura (°C)</th><th class="right">Humedad (%)</th></tr>
    </thead>
    <tbody>
"""
    for hr, dev, t, h in table_rows:
        html += f"<tr><td>{hr}</td><td>{dev}</td><td class='right'>{t}</td><td class='right'>{h}</td></tr>\n"

    html += """
    </tbody>
  </table>
  <p class="note">TIP: cambia ?n=50 en la URL para ver más filas (ej: /dashboard?n=50)</p>
</body>
</html>
"""
    return Response(html, mimetype="text/html; charset=utf-8")

@app.post("/ingest")
def ingest():
    if request.headers.get("X-API-KEY") != API_TOKEN:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    j = request.get_json(silent=True)
    if not j:
        return jsonify({"ok": False, "error": "invalid json"}), 400

    try:
        ts  = int(j.get("ts_epoch", time.time()))
        dev = str(j.get("device", "esp32"))
        t   = float(j["temp_c"])
        h   = float(j["hum_pct"])
    except Exception:
        return jsonify({"ok": False, "error": "bad fields"}), 400

    ensure_csv()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=';').writerow([ts, dev, t, h])

    return jsonify({"ok": True})

@app.get("/data.csv")
def data_csv():
    ensure_csv()
    return send_file(CSV_PATH, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

