import os
import requests as req
from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect
from flask_cors import CORS
from supabase import create_client
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ["SECRET_KEY"]
app.permanent_session_lifetime = timedelta(days=30)

db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/finanzas/login")
        return f(*args, **kwargs)
    return decorated

# ── Páginas ───────────────────────────────────────────────────────────────────

@app.route("/finanzas")
@login_required
def index():
    return render_template("finanzas.html", username=session["username"])

@app.route("/finanzas/login")
def login_page():
    if "user_id" in session:
        return redirect("/finanzas")
    return render_template("auth.html")

@app.route("/finanzas/logout")
def logout():
    session.clear()
    return redirect("/finanzas/login")

@app.route("/finanzas/manifest.json")
def manifest():
    return send_from_directory("static", "finanzas_manifest.json", mimetype="application/manifest+json")

@app.route("/finanzas/sw.js")
def sw():
    return send_from_directory("static", "finanzas_sw.js", mimetype="application/javascript")

# ── Auth API ──────────────────────────────────────────────────────────────────

@app.route("/api/finanzas/login", methods=["POST"])
def login():
    data     = request.get_json()
    username = (data.get("username") or "").strip()
    password =  data.get("password") or ""

    res = db.table("usuarios").select("*").eq("username", username).execute()
    if not res.data or not check_password_hash(res.data[0]["password_hash"], password):
        return jsonify({"ok": False, "error": "Usuario o contraseña incorrectos"}), 401

    user = res.data[0]
    session.permanent = True
    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    return jsonify({"ok": True})

@app.route("/api/finanzas/register", methods=["POST"])
def register():
    data     = request.get_json()
    username = (data.get("username") or "").strip()
    password =  data.get("password") or ""

    if not username or not password:
        return jsonify({"ok": False, "error": "Completá todos los campos"}), 400

    if db.table("usuarios").select("id").eq("username", username).execute().data:
        return jsonify({"ok": False, "error": "Ese nombre de usuario ya está en uso"}), 400

    email = f"{username}@finanzas.local"
    res = db.table("usuarios").insert({
        "email":         email,
        "username":      username,
        "password_hash": generate_password_hash(password),
        "verificado":    True,
    }).execute()

    user = res.data[0]
    db.table("transacciones").update({"user_id": user["id"]}).is_("user_id", "null").execute()

    session.permanent = True
    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    return jsonify({"ok": True}), 201

# ── Cotizaciones API ──────────────────────────────────────────────────────────

@app.route("/api/finanzas/cotizaciones")
def cotizaciones():
    try:
        r = req.get("https://api.bluelytics.com.ar/v2/latest", timeout=5)
        data = r.json()
        return jsonify({
            "USD": round(data["oficial"]["value_sell"], 2),
            "EUR": round(data["oficial_euro"]["value_sell"], 2),
        })
    except Exception as e:
        return jsonify({"USD": None, "EUR": None}), 200

# ── Transacciones API ─────────────────────────────────────────────────────────

@app.route("/api/finanzas", methods=["GET"])
@login_required
def listar():
    res = db.table("transacciones").select("*").eq("user_id", session["user_id"]).order("fecha", desc=True).execute()
    return jsonify(res.data)

@app.route("/api/finanzas", methods=["POST"])
@login_required
def agregar():
    t = request.get_json()
    payload = {
        "tipo":        t["tipo"],
        "monto":       float(t["monto"]),
        "fecha":       t["fecha"],
        "categoria":   t.get("categoria", ""),
        "descripcion": t.get("descripcion", ""),
        "moneda":      t.get("moneda", "ARS"),
        "user_id":     session["user_id"],
    }
    res = db.table("transacciones").insert(payload).execute()
    return jsonify(res.data[0]), 201

@app.route("/api/finanzas/<int:tid>", methods=["DELETE"])
@login_required
def eliminar(tid):
    db.table("transacciones").delete().eq("id", tid).eq("user_id", session["user_id"]).execute()
    return jsonify({"ok": True})

if __name__ == "__main__":
    import socket
    port = int(os.environ.get("PORT", 5001))
    ip = socket.gethostbyname(socket.gethostname())
    print(f"\n  Local:  http://localhost:{port}/finanzas\n")
    app.run(host="0.0.0.0", port=port, debug=False)
