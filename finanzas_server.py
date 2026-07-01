import os
import csv
import io
import calendar
import hmac
import hashlib
import requests as req
from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect
from flask_cors import CORS
from supabase import create_client
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date, timedelta, datetime, timezone
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

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/finanzas")
@login_required
def index():
    user = db.table("usuarios").select("plan,trial_expira").eq("id", session["user_id"]).execute().data
    is_pro = False
    is_trial = False
    trial_dias = 0
    if user:
        plan = user[0].get("plan")
        trial_expira = user[0].get("trial_expira")
        if plan == "pro":
            is_pro = True
        elif plan == "trial" and trial_expira:
            expira = datetime.fromisoformat(trial_expira.replace("Z", "+00:00"))
            if expira > datetime.now(timezone.utc):
                is_pro = True
                is_trial = True
                trial_dias = max(1, (expira - datetime.now(timezone.utc)).days + 1)
    return render_template("finanzas.html", username=session["username"], is_pro=is_pro, is_trial=is_trial, trial_dias=trial_dias)

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
        "plan":          "trial",
        "trial_expira":  (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
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

# ── Plan helpers ─────────────────────────────────────────────────────────────

def _es_pro(user_id):
    res = db.table("usuarios").select("plan,trial_expira").eq("id", user_id).execute()
    if not res.data:
        return False
    u = res.data[0]
    if u.get("plan") == "pro":
        return True
    if u.get("plan") == "trial" and u.get("trial_expira"):
        expira = datetime.fromisoformat(u["trial_expira"].replace("Z", "+00:00"))
        return expira > datetime.now(timezone.utc)
    return False

# ── Recurrentes helpers ───────────────────────────────────────────────────────

def _siguiente_fecha(fecha_str, frecuencia):
    d = date.fromisoformat(fecha_str)
    if frecuencia == "semanal":
        return (d + timedelta(weeks=1)).isoformat()
    mes  = d.month + 1 if d.month < 12 else 1
    anio = d.year      if d.month < 12 else d.year + 1
    return date(anio, mes, min(d.day, calendar.monthrange(anio, mes)[1])).isoformat()

def _procesar_recurrentes(user_id):
    hoy = date.today().isoformat()
    pendientes = db.table("recurrentes").select("*").eq("user_id", user_id).eq("activo", True).lte("proxima_fecha", hoy).execute().data
    for r in pendientes:
        prox = r["proxima_fecha"]
        while prox <= hoy:
            db.table("transacciones").insert({
                "tipo": r["tipo"], "monto": r["monto"], "fecha": prox,
                "categoria": r["categoria"], "descripcion": r["descripcion"],
                "moneda": r["moneda"], "user_id": user_id,
            }).execute()
            prox = _siguiente_fecha(prox, r["frecuencia"])
        db.table("recurrentes").update({"proxima_fecha": prox}).eq("id", r["id"]).execute()

# ── Transacciones API ─────────────────────────────────────────────────────────

@app.route("/api/finanzas", methods=["GET"])
@login_required
def listar():
    try:
        _procesar_recurrentes(session["user_id"])
    except Exception:
        pass
    es_pro = _es_pro(session["user_id"])
    query = db.table("transacciones").select("*").eq("user_id", session["user_id"])
    if not es_pro:
        desde = (date.today() - timedelta(days=90)).isoformat()
        query = query.gte("fecha", desde)
    res = query.order("fecha", desc=True).execute()
    return jsonify(res.data)

@app.route("/api/finanzas", methods=["POST"])
@login_required
def agregar():
    if not _es_pro(session["user_id"]):
        inicio_mes = date.today().replace(day=1).isoformat()
        count = len(db.table("transacciones").select("id").eq("user_id", session["user_id"]).gte("fecha", inicio_mes).execute().data)
        if count >= 50:
            return jsonify({"ok": False, "error": "limite_pro"}), 403
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

@app.route("/api/finanzas/export", methods=["GET"])
@login_required
def exportar():
    if not _es_pro(session["user_id"]):
        return jsonify({"error": "Pro requerido"}), 403
    res = db.table("transacciones").select("*").eq("user_id", session["user_id"]).order("fecha", desc=True).execute()
    output = io.StringIO()
    output.write("sep=;\n")
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["Fecha", "Tipo", "Monto", "Moneda", "Categoria", "Descripcion"])
    for t in res.data:
        writer.writerow([
            t["fecha"], t["tipo"], t["monto"],
            t.get("moneda","ARS"), t.get("categoria",""), t.get("descripcion",""),
        ])
    from flask import Response
    encoded = output.getvalue().encode("utf-8-sig")
    return Response(encoded, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=finanzas.csv"})

@app.route("/api/finanzas/stats")
@login_required
def stats():
    from collections import defaultdict
    hoy = date.today()
    inicio_mes = hoy.replace(day=1).isoformat()
    inicio_mes_ant = date(hoy.year if hoy.month > 1 else hoy.year - 1,
                          hoy.month - 1 if hoy.month > 1 else 12, 1).isoformat()
    res_act = db.table("transacciones").select("tipo,monto,categoria").eq("user_id", session["user_id"]).gte("fecha", inicio_mes).execute()
    res_ant = db.table("transacciones").select("tipo,monto").eq("user_id", session["user_id"]).gte("fecha", inicio_mes_ant).lt("fecha", inicio_mes).execute()
    cats = defaultdict(float)
    gas_act = ing_act = 0.0
    for t in res_act.data:
        m = float(t["monto"])
        if t["tipo"] == "Gasto":
            cats[t.get("categoria") or "Otros"] += m
            gas_act += m
        else:
            ing_act += m
    gas_ant = sum(float(t["monto"]) for t in res_ant.data if t["tipo"] == "Gasto")
    ing_ant  = sum(float(t["monto"]) for t in res_ant.data if t["tipo"] == "Ingreso")
    meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    return jsonify({
        "categorias": [{"nombre": k, "total": v} for k, v in sorted(cats.items(), key=lambda x: -x[1])],
        "resumen": {
            "gastos_actual": gas_act, "ingresos_actual": ing_act,
            "gastos_anterior": gas_ant, "ingresos_anterior": ing_ant,
            "mes_actual": meses[hoy.month - 1], "mes_anterior": meses[(hoy.month - 2) % 12],
        },
        "count_mes": len(res_act.data),
    })

@app.route("/api/finanzas/recurrentes", methods=["GET"])
@login_required
def listar_recurrentes():
    res = db.table("recurrentes").select("*").eq("user_id", session["user_id"]).eq("activo", True).order("creado_en", desc=True).execute()
    return jsonify(res.data)

@app.route("/api/finanzas/recurrentes", methods=["POST"])
@login_required
def crear_recurrente():
    if not _es_pro(session["user_id"]):
        return jsonify({"ok": False, "error": "pro_requerido"}), 403
    try:
        t = request.get_json()
        payload = {
            "tipo":          t["tipo"],
            "monto":         float(t["monto"]),
            "categoria":     t.get("categoria") or "",
            "descripcion":   t.get("descripcion") or "",
            "moneda":        t.get("moneda") or "ARS",
            "frecuencia":    t["frecuencia"],
            "proxima_fecha": t["fecha"],
            "user_id":       session["user_id"],
        }
        res = db.table("recurrentes").insert(payload).execute()
        return jsonify(res.data[0]), 201
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/finanzas/recurrentes/<int:rid>", methods=["DELETE"])
@login_required
def eliminar_recurrente(rid):
    db.table("recurrentes").update({"activo": False}).eq("id", rid).eq("user_id", session["user_id"]).execute()
    return jsonify({"ok": True})

@app.route("/api/finanzas/<int:tid>", methods=["PUT"])
@login_required
def editar(tid):
    t = request.get_json()
    payload = {
        "tipo":        t["tipo"],
        "monto":       float(t["monto"]),
        "fecha":       t["fecha"],
        "categoria":   t.get("categoria", ""),
        "descripcion": t.get("descripcion", ""),
        "moneda":      t.get("moneda", "ARS"),
    }
    res = db.table("transacciones").update(payload).eq("id", tid).eq("user_id", session["user_id"]).execute()
    return jsonify(res.data[0])

@app.route("/api/finanzas/<int:tid>", methods=["DELETE"])
@login_required
def eliminar(tid):
    db.table("transacciones").delete().eq("id", tid).eq("user_id", session["user_id"]).execute()
    return jsonify({"ok": True})

@app.route("/api/finanzas/suscribir")
@login_required
def suscribir():
    mp_token = os.environ.get("MP_ACCESS_TOKEN", "")
    r = req.post(
        "https://api.mercadopago.com/preapproval",
        headers={"Authorization": f"Bearer {mp_token}"},
        json={
            "reason": "Finanzas Pro",
            "external_reference": session["user_id"],
            "payer_email": f"{session['username']}@finanzas.local",
            "auto_recurring": {
                "frequency": 1,
                "frequency_type": "months",
                "transaction_amount": 1999,
                "currency_id": "ARS",
            },
            "back_url": "https://web-production-d822b.up.railway.app/finanzas",
            "notification_url": "https://web-production-d822b.up.railway.app/api/finanzas/webhook/mercadopago",
        }
    )
    data = r.json()
    init_point = data.get("init_point")
    if not init_point:
        return jsonify({"error": "No se pudo crear la suscripción", "detalle": data}), 500
    return redirect(init_point)

@app.route("/api/finanzas/webhook/mercadopago", methods=["POST"])
def webhook_mp():
    data = request.get_json(silent=True) or {}
    topic = data.get("type") or request.args.get("topic", "")
    resource_id = data.get("data", {}).get("id") or request.args.get("id", "")

    if topic in ("subscription_preapproval", "preapproval") and resource_id:
        mp_token = os.environ.get("MP_ACCESS_TOKEN", "")
        r = req.get(
            f"https://api.mercadopago.com/preapproval/{resource_id}",
            headers={"Authorization": f"Bearer {mp_token}"}
        )
        preapproval = r.json()
        if preapproval.get("status") == "authorized":
            user_id = preapproval.get("external_reference")
            if user_id:
                db.table("usuarios").update({"plan": "pro"}).eq("id", user_id).execute()

    return jsonify({"ok": True})

if __name__ == "__main__":
    import socket
    port = int(os.environ.get("PORT", 5001))
    ip = socket.gethostbyname(socket.gethostname())
    print(f"\n  Local:  http://localhost:{port}/finanzas\n")
    app.run(host="0.0.0.0", port=port, debug=False)
