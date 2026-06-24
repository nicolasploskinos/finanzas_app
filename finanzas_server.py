import os
from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

db = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route("/finanzas")
def index():
    return render_template("finanzas.html")

@app.route("/finanzas/manifest.json")
def manifest():
    return send_from_directory("static", "finanzas_manifest.json", mimetype="application/manifest+json")

@app.route("/finanzas/sw.js")
def sw():
    return send_from_directory("static", "finanzas_sw.js", mimetype="application/javascript")

@app.route("/api/finanzas", methods=["GET"])
def listar():
    res = db.table("transacciones").select("*").order("fecha", desc=True).execute()
    return jsonify(res.data)

@app.route("/api/finanzas", methods=["POST"])
def agregar():
    t = request.get_json()
    payload = {
        "tipo":        t["tipo"],
        "monto":       float(t["monto"]),
        "fecha":       t["fecha"],
        "categoria":   t.get("categoria", ""),
        "descripcion": t.get("descripcion", ""),
    }
    res = db.table("transacciones").insert(payload).execute()
    return jsonify(res.data[0]), 201

@app.route("/api/finanzas/<int:tid>", methods=["DELETE"])
def eliminar(tid):
    db.table("transacciones").delete().eq("id", tid).execute()
    return jsonify({"ok": True})

if __name__ == "__main__":
    import socket
    ip = socket.gethostbyname(socket.gethostname())
    print(f"\n  Local:  http://localhost:5001/finanzas")
    print(f"  Celular (WiFi): http://{ip}:5001/finanzas\n")
    app.run(host="0.0.0.0", port=5001, debug=False)
