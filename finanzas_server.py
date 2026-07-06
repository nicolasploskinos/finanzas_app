import os
import csv
import io
import re
import time
import random
import unicodedata
import calendar
import hmac
import hashlib
import requests as req
from urllib.parse import quote
from flask import Flask, jsonify, request, render_template, send_from_directory, session, redirect, Response
from flask_cors import CORS
from supabase import create_client
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date, timedelta, datetime, timezone
from dotenv import load_dotenv

load_dotenv()

_inflacion_cache = {"data": None, "ts": 0}
_wa_codigos = {}       # codigo de vinculación -> (user_id, expira_ts)
_wa_procesados = set() # wamids ya procesados, para ignorar reintentos de Meta

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
    hoy = (datetime.now(timezone.utc) - timedelta(hours=3)).date().isoformat()
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

def _insertar_transaccion(user_id, tipo, monto, fecha, categoria="", descripcion="", moneda="ARS"):
    if not _es_pro(user_id):
        inicio_mes = date.today().replace(day=1).isoformat()
        count = len(db.table("transacciones").select("id").eq("user_id", user_id).gte("fecha", inicio_mes).execute().data)
        if count >= 50:
            return False, "limite_pro"
    payload = {
        "tipo": tipo, "monto": float(monto), "fecha": fecha,
        "categoria": categoria or "", "descripcion": descripcion or "",
        "moneda": moneda or "ARS", "user_id": user_id,
    }
    res = db.table("transacciones").insert(payload).execute()
    return True, res.data[0]

@app.route("/api/finanzas", methods=["POST"])
@login_required
def agregar():
    t = request.get_json()
    ok, resultado = _insertar_transaccion(
        session["user_id"], t["tipo"], t["monto"], t["fecha"],
        t.get("categoria", ""), t.get("descripcion", ""), t.get("moneda", "ARS"),
    )
    if not ok:
        return jsonify({"ok": False, "error": resultado}), 403
    return jsonify(resultado), 201

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
    encoded = output.getvalue().encode("utf-8-sig")
    return Response(encoded, mimetype="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=finanzas.csv"})

@app.route("/api/finanzas/export/excel", methods=["GET"])
@login_required
def exportar_excel():
    if not _es_pro(session["user_id"]):
        return jsonify({"error": "Pro requerido"}), 403
    res = db.table("transacciones").select("*").eq("user_id", session["user_id"]).order("fecha", desc=True).execute()

    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    ws = wb.active
    ws.title = "Transacciones"
    headers = ["Fecha", "Tipo", "Monto", "Moneda", "Categoría", "Descripción"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="16A34A", end_color="16A34A", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
    for t in res.data:
        ws.append([
            t["fecha"], t["tipo"], float(t["monto"]),
            t.get("moneda", "ARS"), t.get("categoria", ""), t.get("descripcion", ""),
        ])
    for col, width in zip("ABCDEF", (12, 10, 14, 8, 20, 34)):
        ws.column_dimensions[col].width = width

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        buf.read(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=finanzas.xlsx"},
    )

@app.route("/api/finanzas/export/pdf", methods=["GET"])
@login_required
def exportar_pdf():
    if not _es_pro(session["user_id"]):
        return jsonify({"error": "Pro requerido"}), 403
    res = db.table("transacciones").select("*").eq("user_id", session["user_id"]).order("fecha", desc=True).execute()

    from fpdf import FPDF

    def _safe(s):
        return (s or "").encode("latin-1", "replace").decode("latin-1")

    total_gastos = sum(float(t["monto"]) for t in res.data if t["tipo"] == "Gasto")
    total_ingresos = sum(float(t["monto"]) for t in res.data if t["tipo"] == "Ingreso")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, _safe("Finanzas - Historial de transacciones"), ln=1)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 6, _safe(f"Generado el {date.today().isoformat()} - Usuario: {session['username']}"), ln=1)
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, _safe(f"Total ingresos: {total_ingresos:,.2f}   Total gastos: {total_gastos:,.2f}"), ln=1)
    pdf.ln(4)

    col_widths = [22, 18, 26, 14, 40, 68]
    headers = ["Fecha", "Tipo", "Monto", "Moneda", "Categoria", "Descripcion"]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(22, 163, 74)
    pdf.set_text_color(255, 255, 255)
    for w, h in zip(col_widths, headers):
        pdf.cell(w, 7, h, border=1, fill=True)
    pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 8)
    for t in res.data:
        fila = [
            t["fecha"], t["tipo"], f'{float(t["monto"]):,.2f}',
            t.get("moneda", "ARS"), (t.get("categoria") or "")[:22], (t.get("descripcion") or "")[:45],
        ]
        for w, val in zip(col_widths, fila):
            pdf.cell(w, 6, _safe(str(val)), border=1)
        pdf.ln()
        if pdf.get_y() > 270:
            pdf.add_page()

    salida = bytes(pdf.output())
    return Response(
        salida, mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=finanzas.pdf"},
    )

# ── Importar movimientos (banco / billetera virtual) ──────────────────────────

def _norm_header(s):
    s = (s or "").strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

def _buscar_col(headers, candidatos):
    for i, h in enumerate(headers):
        if any(c in h for c in candidatos):
            return i
    return None

def _parse_fecha_import(s):
    s = (s or "").strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None

def _parse_monto_import(s):
    s = (s or "").strip()
    if not s:
        return None
    neg = s.startswith("-") or (s.startswith("(") and s.endswith(")"))
    s = re.sub(r"[^\d,.\-]", "", s).lstrip("-")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        partes = s.split(",")
        if len(partes[-1]) == 2:
            s = s.replace(",", ".")
        else:
            s = s.replace(",", "")
    if not s:
        return None
    try:
        val = float(s)
    except ValueError:
        return None
    return -val if neg else val

@app.route("/api/finanzas/import/preview", methods=["POST"])
@login_required
def import_preview():
    if not _es_pro(session["user_id"]):
        return jsonify({"ok": False, "error": "pro_requerido"}), 403

    archivo = request.files.get("archivo")
    if not archivo or not archivo.filename.lower().endswith(".csv"):
        return jsonify({"ok": False, "error": "Subí un archivo .csv"}), 400

    raw = archivo.read(2_000_000)
    texto = None
    for enc in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            texto = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if texto is None:
        return jsonify({"ok": False, "error": "No se pudo leer el archivo"}), 400

    muestra = texto[:2000]
    try:
        delim = csv.Sniffer().sniff(muestra, delimiters=",;\t").delimiter
    except csv.Error:
        delim = ";" if muestra.count(";") > muestra.count(",") else ","

    filas = list(csv.reader(io.StringIO(texto), delimiter=delim))
    if len(filas) < 2:
        return jsonify({"ok": False, "error": "El archivo está vacío"}), 400

    headers = [_norm_header(h) for h in filas[0]]
    idx_fecha = _buscar_col(headers, ["fecha", "date"])
    idx_monto = _buscar_col(headers, ["importe", "monto", "valor", "amount", "total"])
    idx_desc  = _buscar_col(headers, ["descripcion", "concepto", "detalle", "description", "glosa"])
    idx_debe  = _buscar_col(headers, ["debe", "egreso", "cargo", "debito"])
    idx_haber = _buscar_col(headers, ["haber", "ingreso", "abono", "credito"])

    if idx_fecha is None or (idx_monto is None and (idx_debe is None or idx_haber is None)):
        return jsonify({
            "ok": False,
            "error": "No reconocemos las columnas del archivo. Verificá que tenga fecha, monto y descripción.",
        }), 400

    transacciones = []
    errores = 0
    for fila in filas[1:]:
        if not fila or all(not c.strip() for c in fila):
            continue
        try:
            fecha = _parse_fecha_import(fila[idx_fecha]) if idx_fecha < len(fila) else None
            desc  = fila[idx_desc].strip() if idx_desc is not None and idx_desc < len(fila) else ""

            if idx_monto is not None:
                monto_raw = _parse_monto_import(fila[idx_monto]) if idx_monto < len(fila) else None
                if not monto_raw:
                    errores += 1
                    continue
                tipo, monto = ("Gasto" if monto_raw < 0 else "Ingreso"), abs(monto_raw)
            else:
                debe  = abs(_parse_monto_import(fila[idx_debe])  or 0) if idx_debe  < len(fila) else 0
                haber = abs(_parse_monto_import(fila[idx_haber]) or 0) if idx_haber < len(fila) else 0
                if haber > 0:
                    tipo, monto = "Ingreso", haber
                elif debe > 0:
                    tipo, monto = "Gasto", debe
                else:
                    errores += 1
                    continue

            if not fecha:
                errores += 1
                continue

            transacciones.append({
                "fecha": fecha, "tipo": tipo, "monto": round(monto, 2),
                "descripcion": desc, "categoria": "", "moneda": "ARS",
            })
        except Exception:
            errores += 1

        if len(transacciones) >= 1000:
            break

    return jsonify({"ok": True, "transacciones": transacciones, "errores": errores})

@app.route("/api/finanzas/import/confirm", methods=["POST"])
@login_required
def import_confirm():
    if not _es_pro(session["user_id"]):
        return jsonify({"ok": False, "error": "pro_requerido"}), 403

    data = request.get_json() or {}
    filas = data.get("transacciones") or []
    if not isinstance(filas, list) or not filas:
        return jsonify({"ok": False, "error": "Nada para importar"}), 400
    if len(filas) > 1000:
        return jsonify({"ok": False, "error": "Demasiadas transacciones (máx. 1000)"}), 400

    payload = []
    for t in filas:
        try:
            payload.append({
                "tipo":        "Ingreso" if t.get("tipo") == "Ingreso" else "Gasto",
                "monto":       abs(float(t["monto"])),
                "fecha":       date.fromisoformat(t["fecha"]).isoformat(),
                "categoria":   (t.get("categoria") or "").strip()[:60],
                "descripcion": (t.get("descripcion") or "").strip()[:200],
                "moneda":      t.get("moneda") if t.get("moneda") in ("ARS", "USD", "EUR") else "ARS",
                "user_id":     session["user_id"],
            })
        except (KeyError, ValueError, TypeError):
            continue

    if not payload:
        return jsonify({"ok": False, "error": "Nada válido para importar"}), 400

    insertados = 0
    for i in range(0, len(payload), 500):
        lote = payload[i:i + 500]
        db.table("transacciones").insert(lote).execute()
        insertados += len(lote)

    return jsonify({"ok": True, "insertados": insertados})

# ── Bot de WhatsApp ────────────────────────────────────────────────────────────

_WA_PALABRAS_INGRESO = {"ingreso", "cobre", "deposito"}
_WA_PALABRAS_DESCARTE = {
    "gaste", "gasto", "pague", "cobre", "ingreso", "deposito",
    "en", "de", "del", "la", "el", "los", "las",
    "usd", "dolar", "dolares", "eur", "euro", "euros",
}

def _parse_mensaje_whatsapp(texto):
    limpio = _norm_header(texto)
    if not limpio:
        return None

    match = re.search(r"\d[\d.,]*", limpio)
    if not match:
        return None
    monto = _parse_monto_import(match.group())
    if not monto:
        return None

    palabras = re.findall(r"[a-z0-9$]+", limpio)
    tipo = "Ingreso" if any(p in _WA_PALABRAS_INGRESO for p in palabras) else "Gasto"

    moneda = "ARS"
    if "usd" in palabras or "dolar" in palabras or "dolares" in palabras or "u$s" in palabras:
        moneda = "USD"
    elif "eur" in palabras or "euro" in palabras or "euros" in palabras:
        moneda = "EUR"

    resto = limpio[:match.start()] + limpio[match.end():]
    cat_palabras = [w for w in re.findall(r"[a-z]+", resto) if w not in _WA_PALABRAS_DESCARTE]
    categoria = " ".join(cat_palabras).strip().capitalize()

    return {"tipo": tipo, "monto": round(abs(monto), 2), "moneda": moneda, "categoria": categoria}

def _wa_enviar_mensaje(telefono, texto):
    token = os.environ.get("WHATSAPP_TOKEN", "")
    phone_id = os.environ.get("WHATSAPP_PHONE_ID", "")
    if not token or not phone_id:
        print("[whatsapp] falta WHATSAPP_TOKEN o WHATSAPP_PHONE_ID en el entorno")
        return
    try:
        r = req.post(
            f"https://graph.facebook.com/v20.0/{phone_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "messaging_product": "whatsapp",
                "to": telefono,
                "type": "text",
                "text": {"body": texto},
            },
            timeout=10,
        )
        if not r.ok:
            print(f"[whatsapp] error al enviar ({r.status_code}): {r.text}")
    except Exception as e:
        print(f"[whatsapp] excepcion al enviar: {e}")

def _procesar_mensaje_whatsapp(msg):
    wamid = msg.get("id")
    if not wamid or wamid in _wa_procesados:
        return
    _wa_procesados.add(wamid)
    if len(_wa_procesados) > 2000:
        _wa_procesados.clear()

    telefono = msg.get("from", "")
    texto = ((msg.get("text") or {}).get("body") or "").strip()
    print(f"[whatsapp] mensaje recibido de '{telefono}': {texto!r}")
    if not telefono or not texto:
        return

    m = re.match(r"(?i)^vincular\s+(\d{6})$", texto.strip())
    if m:
        codigo = m.group(1)
        entrada = _wa_codigos.get(codigo)
        if not entrada or entrada[1] < time.time():
            _wa_enviar_mensaje(telefono, "❌ Código inválido o vencido. Generá uno nuevo desde la app.")
            return
        db.table("whatsapp_users").upsert({"telefono": telefono, "user_id": entrada[0]}, on_conflict="telefono").execute()
        _wa_codigos.pop(codigo, None)
        _wa_enviar_mensaje(telefono, "✅ ¡Listo! Tu WhatsApp quedó vinculado a tu cuenta de Finanzas.")
        return

    vinculo = db.table("whatsapp_users").select("user_id").eq("telefono", telefono).execute()
    if not vinculo.data:
        _wa_enviar_mensaje(
            telefono,
            "No reconozco este número. Vinculalo primero desde la app: Finanzas → sección WhatsApp → Vincular.",
        )
        return
    user_id = vinculo.data[0]["user_id"]

    parseado = _parse_mensaje_whatsapp(texto)
    if not parseado:
        _wa_enviar_mensaje(telefono, "No entendí 🤔. Probá algo como: *gasté 500 en supermercado* o *ingreso 300000 sueldo*.")
        return

    hoy = (datetime.now(timezone.utc) - timedelta(hours=3)).date().isoformat()
    ok, resultado = _insertar_transaccion(
        user_id, parseado["tipo"], parseado["monto"], hoy,
        categoria=parseado["categoria"], descripcion="", moneda=parseado["moneda"],
    )
    if not ok:
        _wa_enviar_mensaje(
            telefono,
            "⛔ Llegaste al límite de 50 transacciones gratis este mes. Entrá a la app para hacerte Pro y seguir cargando.",
        )
        return

    simbolo = {"ARS": "$", "USD": "USD ", "EUR": "€"}.get(parseado["moneda"], "$")
    emoji = "🔴" if parseado["tipo"] == "Gasto" else "🟢"
    cat_txt = f" ({parseado['categoria']})" if parseado["categoria"] else ""
    _wa_enviar_mensaje(telefono, f"{emoji} {parseado['tipo']} de {simbolo}{parseado['monto']:,.2f}{cat_txt} registrado ✓")

@app.route("/api/finanzas/whatsapp/codigo", methods=["POST"])
@login_required
def whatsapp_codigo():
    codigo = f"{random.randint(0, 999999):06d}"
    _wa_codigos[codigo] = (session["user_id"], time.time() + 900)
    numero = re.sub(r"[^0-9]", "", os.environ.get("WHATSAPP_DISPLAY_NUMBER", ""))
    wa_link = f"https://wa.me/{numero}?text={quote(f'VINCULAR {codigo}')}"
    return jsonify({"ok": True, "codigo": codigo, "wa_link": wa_link})

@app.route("/api/finanzas/whatsapp/estado")
@login_required
def whatsapp_estado():
    res = db.table("whatsapp_users").select("telefono").eq("user_id", session["user_id"]).execute()
    if res.data:
        tel = res.data[0]["telefono"]
        return jsonify({"vinculado": True, "telefono_oculto": "•••• " + tel[-4:]})
    return jsonify({"vinculado": False})

@app.route("/api/finanzas/whatsapp/desvincular", methods=["DELETE"])
@login_required
def whatsapp_desvincular():
    db.table("whatsapp_users").delete().eq("user_id", session["user_id"]).execute()
    return jsonify({"ok": True})

@app.route("/api/finanzas/whatsapp/webhook", methods=["GET"])
def whatsapp_webhook_verificar():
    modo = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge", "")
    if modo == "subscribe" and token and token == os.environ.get("WHATSAPP_VERIFY_TOKEN"):
        return challenge, 200
    return "Forbidden", 403

@app.route("/api/finanzas/whatsapp/webhook", methods=["POST"])
def whatsapp_webhook_recibir():
    app_secret = os.environ.get("WHATSAPP_APP_SECRET", "")
    if app_secret:
        firma = request.headers.get("X-Hub-Signature-256", "")
        esperado = "sha256=" + hmac.new(app_secret.encode(), request.get_data(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(firma, esperado):
            return jsonify({"error": "firma invalida"}), 403

    data = request.get_json(silent=True) or {}
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                for msg in (change.get("value") or {}).get("messages", []):
                    _procesar_mensaje_whatsapp(msg)
    except Exception:
        pass
    return jsonify({"ok": True})

@app.route("/api/finanzas/inflacion")
@login_required
def inflacion():
    global _inflacion_cache
    if time.time() - _inflacion_cache["ts"] < 86400 and _inflacion_cache["data"] is not None:
        return jsonify(_inflacion_cache["data"])
    try:
        r = req.get(
            "https://apis.datos.gob.ar/series/api/series/",
            params={"ids": "148.3_INIVELNAL_DICI_M_26", "limit": 25, "format": "json"},
            timeout=6,
        )
        series = r.json().get("data", [])
        result = [{"mes": row[0][:7], "ipc": row[1]} for row in series if row[1] is not None]
        _inflacion_cache = {"data": result, "ts": time.time()}
        return jsonify(result)
    except Exception:
        return jsonify(_inflacion_cache["data"] or []), 200

@app.route("/api/finanzas/stats")
@login_required
def stats():
    if not _es_pro(session["user_id"]):
        return jsonify({"error": "pro_requerido"}), 403
    from collections import defaultdict
    def _norm(s):
        s = (s or "otros").strip().lower()
        return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    hoy_ar = (datetime.now(timezone.utc) - timedelta(hours=3)).date()
    mes  = request.args.get("mes",  type=int, default=hoy_ar.month)
    anio = request.args.get("anio", type=int, default=hoy_ar.year)
    mes  = max(1, min(12, mes))
    inicio_mes = date(anio, mes, 1).isoformat()
    inicio_mes_ant = date(anio if mes > 1 else anio - 1, mes - 1 if mes > 1 else 12, 1).isoformat()
    fin_mes = date(anio if mes < 12 else anio + 1, mes + 1 if mes < 12 else 1, 1).isoformat()
    res_act = db.table("transacciones").select("tipo,monto,categoria").eq("user_id", session["user_id"]).gte("fecha", inicio_mes).lt("fecha", fin_mes).execute()
    res_ant = db.table("transacciones").select("tipo,monto").eq("user_id", session["user_id"]).gte("fecha", inicio_mes_ant).lt("fecha", inicio_mes).execute()
    cats_total = defaultdict(float)
    cats_label = {}
    gas_act = ing_act = 0.0
    for t in res_act.data:
        m = float(t["monto"])
        if t["tipo"] == "Gasto":
            key = _norm(t.get("categoria"))
            cats_total[key] += m
            if key not in cats_label:
                cats_label[key] = (t.get("categoria") or "Otros").strip().capitalize()
            gas_act += m
        else:
            ing_act += m
    gas_ant = sum(float(t["monto"]) for t in res_ant.data if t["tipo"] == "Gasto")
    ing_ant  = sum(float(t["monto"]) for t in res_ant.data if t["tipo"] == "Ingreso")
    meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    return jsonify({
        "categorias": [{"nombre": cats_label[k], "total": v} for k, v in sorted(cats_total.items(), key=lambda x: -x[1])],
        "resumen": {
            "gastos_actual": gas_act, "ingresos_actual": ing_act,
            "gastos_anterior": gas_ant, "ingresos_anterior": ing_ant,
            "mes_actual": meses[mes - 1], "mes_anterior": meses[(mes - 2) % 12],
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
