import os
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
    data = request.get_json()
    email    = (data.get("email")    or "").strip().lower()
    password =  data.get("password") or ""

    res = db.table("usuarios").select("*").eq("email", email).execute()
    if not res.data or not check_password_hash(res.data[0]["password_hash"], password):
        return jsonify({"ok": False, "error": "Email o contraseña incorrectos"}), 401

    user = res.data[0]
    session.permanent = True
    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    return jsonify({"ok": True})

@app.route("/api/finanzas/register", methods=["POST"])
def register():
    data = request.get_json()
    email    = (data.get("email")    or "").strip().lower()
    username = (data.get("username") or "").strip()
    password =  data.get("password") or ""

    if not email or not username or not password:
        return jsonify({"ok": False, "error": "Completá todos los campos"}), 400

    if db.table("usuarios").select("id").eq("email", email).execute().data:
        return jsonify({"ok": False, "error": "Ese email ya está registrado"}), 400

    if db.table("usuarios").select("id").eq("username", username).execute().data:
        return jsonify({"ok": False, "error": "Ese nombre de usuario ya está en uso"}), 400

    res = db.table("usuarios").insert({
        "email":        email,
        "username":     username,
        "password_hash": generate_password_hash(password),
        "verificado":   True,
    }).execute()

    user = res.data[0]
    db.table("transacciones").update({"user_id": user["id"]}).is_("user_id", "null").execute()

    session.permanent = True
    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    return jsonify({"ok": True}), 201

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
