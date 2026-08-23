import os
import re
import json
import time
import unicodedata
import calendar
import requests as req
from google import genai
from google.genai import types as genai_types
from flask import Flask, session, redirect
from flask_cors import CORS
from supabase import create_client
from functools import wraps
from datetime import date, timedelta, datetime, timezone
from dotenv import load_dotenv

load_dotenv()

_inflacion_cache = {"data": None, "ts": 0}
_cotiz_cache = {"data": None, "ts": 0}
_wa_codigos = {}       # codigo de vinculación -> (user_id, expira_ts)
_wa_procesados = set() # wamids ya procesados, para ignorar reintentos de Meta

# La app de Meta está en modo desarrollo (sin Business Verification), así que
# el bot de WhatsApp solo le puede responder a números que agreguemos a mano
# a la lista de destinatarios permitidos. Hasta que se verifique el negocio,
# el bot queda restringido a esta única cuenta.
_WHATSAPP_USER_ID = "39d80812-6467-4e6e-b557-34e64a135608"  # Nicolas

def _hoy_ar():
    # El servidor corre en UTC; Buenos Aires es UTC-3 todo el año (sin horario de verano).
    return (datetime.now(timezone.utc) - timedelta(hours=3)).date()

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ["SECRET_KEY"]
app.permanent_session_lifetime = timedelta(days=30)
app.config["SESSION_COOKIE_SECURE"]   = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # tope global de subida (el import de CSV ya recorta a 2MB aparte)

db = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_KEY"])

_login_intentos = {}           # username -> [timestamps de intentos fallidos]
_LOGIN_MAX_INTENTOS = 5
_LOGIN_VENTANA_SEGUNDOS = 15 * 60

def _login_bloqueado(username):
    ahora = time.time()
    intentos = [ts for ts in _login_intentos.get(username, []) if ahora - ts < _LOGIN_VENTANA_SEGUNDOS]
    _login_intentos[username] = intentos
    return len(intentos) >= _LOGIN_MAX_INTENTOS

def _registrar_intento_fallido(username):
    _login_intentos.setdefault(username, []).append(time.time())

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect("/finanzas/login")
        return f(*args, **kwargs)
    return decorated

@app.after_request
def _no_cache_html(resp):
    if resp.mimetype == "text/html":
        resp.headers["Cache-Control"] = "no-store"
    return resp

# ── Cotizaciones ──────────────────────────────────────────────────────────────

def _obtener_cotizaciones():
    if _cotiz_cache["data"] and time.time() - _cotiz_cache["ts"] < 600:
        return _cotiz_cache["data"]
    try:
        r = req.get("https://api.bluelytics.com.ar/v2/latest", timeout=5)
        data = r.json()
        cotiz = {
            "USD": round(data["oficial"]["value_sell"], 2),
            "EUR": round(data["oficial_euro"]["value_sell"], 2),
        }
    except Exception:
        cotiz = {"USD": None, "EUR": None}
    _cotiz_cache["data"] = cotiz
    _cotiz_cache["ts"] = time.time()
    return cotiz

def _convertir_moneda(monto, origen, destino, cotiz):
    if origen == destino:
        return monto
    ars = monto if origen == "ARS" else (monto * cotiz[origen] if cotiz.get(origen) else None)
    if ars is None:
        return None
    if destino == "ARS":
        return ars
    return ars / cotiz[destino] if cotiz.get(destino) else None

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
    hoy = _hoy_ar().isoformat()
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

def _insertar_transaccion(user_id, tipo, monto, fecha, categoria="", descripcion="", moneda="ARS", viaje_id=None):
    if not _es_pro(user_id):
        inicio_mes = _hoy_ar().replace(day=1).isoformat()
        count = len(db.table("transacciones").select("id").eq("user_id", user_id).gte("fecha", inicio_mes).execute().data)
        if count >= 50:
            return False, "limite_pro"
    payload = {
        "tipo": tipo, "monto": float(monto), "fecha": fecha,
        "categoria": categoria or "", "descripcion": descripcion or "",
        "moneda": moneda or "ARS", "user_id": user_id, "viaje_id": viaje_id,
    }
    res = db.table("transacciones").insert(payload).execute()
    return True, res.data[0]

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

# ── Bot de WhatsApp ────────────────────────────────────────────────────────────

_WA_PALABRAS_INGRESO = {
    "ingreso", "ingrese", "ingresaron",
    "cobre", "cobro",
    "deposito", "depositaron",
    "recibi",
    "gane",
    "sueldo",
}
_WA_PALABRAS_DESCARTE = {
    "gaste", "gasto", "pague",
    "cobre", "cobro", "ingreso", "ingrese", "ingresaron", "deposito", "depositaron", "recibi", "gane",
    "en", "de", "del", "la", "el", "los", "las", "me",
    "usd", "dolar", "dolares", "eur", "euro", "euros",
}

def _parse_mensaje_whatsapp(texto):
    desc_match = re.search(r"\(([^)]+)\)", texto)
    descripcion = desc_match.group(1).strip() if desc_match else ""
    if desc_match:
        texto = texto[:desc_match.start()] + texto[desc_match.end():]

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

    return {"tipo": tipo, "monto": round(abs(monto), 2), "moneda": moneda, "categoria": categoria, "descripcion": descripcion}

_WA_SCHEMA_TRANSACCION = {
    "type": "object",
    "properties": {
        "es_transaccion": {"type": "boolean"},
        "tipo": {"type": "string", "enum": ["Gasto", "Ingreso"]},
        "monto": {"type": "number"},
        "moneda": {"type": "string", "enum": ["ARS", "USD", "EUR"]},
        "categoria": {"type": "string"},
        "descripcion": {"type": "string"},
    },
    "required": ["es_transaccion"],
}

def _wa_interpretar_mensaje_ia(texto):
    """Intenta interpretar el mensaje con Gemini, más tolerante que el regex
    (jerga, montos aproximados, frases sueltas). Devuelve (disponible, dato):
    - (False, None): la IA no está disponible (sin key, error, timeout) —
      el llamador debe usar el parser regex como respaldo.
    - (True, None): la IA respondió pero decidió que no es una carga.
    - (True, dict): la IA extrajo una transacción."""
    if not os.environ.get("GEMINI_API_KEY"):
        return False, None
    prompt = (
        "Interpretá este mensaje de WhatsApp de alguien registrando un gasto o ingreso personal, en español "
        "rioplatense informal: puede usar jerga ('lucas' o 'palos' para miles/millones), montos aproximados, "
        "abreviaturas, faltas de ortografía, o frases sueltas sin estructura fija.\n\n"
        f'Mensaje: "{texto}"\n\n'
        "Si el mensaje NO describe un gasto o ingreso con un monto concreto (por ejemplo es una pregunta, un "
        "saludo, o no incluye plata), respondé es_transaccion=false y nada más.\n"
        "Si SÍ es una carga, completá además: tipo (Gasto o Ingreso; asumí Gasto si no queda claro), monto "
        "(número, convertí jerga como 'lucas'=miles, 'palos'=millones, o abreviaturas tipo '5k'=5000 y "
        "'37k'=37000 a su valor real, sin separadores), "
        "moneda (ARS por defecto, USD o EUR solo si se menciona explícitamente), categoria (una palabra corta "
        "en español, ej: comida, transporte, sueldo — vacío si no hay ninguna pista), descripcion (detalle breve "
        "opcional, vacío si no aporta nada nuevo)."
    )
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                               http_options=genai_types.HttpOptions(timeout=20000))
        resp = client.models.generate_content(
            model="gemini-3.5-flash-lite", contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=_WA_SCHEMA_TRANSACCION,
            ),
        )
        data = json.loads(resp.text)
    except Exception:
        return False, None

    if not data.get("es_transaccion"):
        return True, None
    try:
        monto = float(data.get("monto") or 0)
    except (TypeError, ValueError):
        monto = 0
    if monto <= 0:
        return True, None

    tipo = data.get("tipo") if data.get("tipo") in ("Gasto", "Ingreso") else "Gasto"
    moneda = data.get("moneda") if data.get("moneda") in ("ARS", "USD", "EUR") else "ARS"
    return True, {
        "tipo": tipo,
        "monto": round(monto, 2),
        "moneda": moneda,
        "categoria": (data.get("categoria") or "").strip().capitalize(),
        "descripcion": (data.get("descripcion") or "").strip(),
    }

def _wa_responder_pregunta(user_id, pregunta):
    if not os.environ.get("GEMINI_API_KEY"):
        return None
    hoy_ar = _hoy_ar()
    desde = (hoy_ar - timedelta(days=180)).isoformat()
    res = (db.table("transacciones").select("tipo,monto,moneda,categoria,descripcion,fecha")
           .eq("user_id", user_id).gte("fecha", desde).order("fecha", desc=True).limit(300).execute())
    if not res.data:
        return "Todavía no tenés movimientos cargados para que te pueda contar algo 🤔"

    lineas = "\n".join(
        f"{t['fecha']} | {t['tipo']} | {t['monto']} {t.get('moneda') or 'ARS'} | "
        f"{t.get('categoria') or 'sin categoría'} | {t.get('descripcion') or ''}"
        for t in res.data
    )
    dias = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    hoy_txt = f"{dias[hoy_ar.weekday()]} {hoy_ar.isoformat()}"
    prompt = (
        "Sos un asistente financiero respondiendo por WhatsApp. "
        f"Hoy es {hoy_txt} (formato fecha: AAAA-MM-DD). Estos son los movimientos del usuario de los "
        f"últimos 6 meses (fecha | tipo | monto | moneda | categoría | descripción):\n\n{lineas}\n\n"
        f'El usuario pregunta: "{pregunta}"\n\n'
        "Si la pregunta menciona una fecha relativa (ej. 'el viernes pasado', 'ayer', 'la semana pasada'), "
        "calculá la fecha real tomando como referencia la fecha de hoy de arriba, y usá solo los movimientos "
        "de esa fecha o rango exacto.\n"
        "Respondé en español rioplatense, corto y directo (máximo 3-4 líneas, como un mensaje real de WhatsApp). "
        "Usá solo estos datos, no inventes cifras que no estén ahí. Si no podés responder con esta información, decilo. "
        "Envolvé entre asteriscos simples (*así*) cualquier número o monto que menciones en la respuesta, para que "
        "WhatsApp lo muestre en negrita — es la única marca que podés usar, no uses ningún otro markdown ni bullets."
    )
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                               http_options=genai_types.HttpOptions(timeout=15000))
        resp = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
        return (resp.text or "").strip() or None
    except Exception:
        return None

def _wa_a_formato_envio(telefono):
    # Los mensajes ENTRANTES de números argentinos llegan como 549+área+número
    # (formato moderno). El endpoint de ENVÍO de Meta, para Argentina, a veces
    # solo reconoce el formato local viejo 54+área+15+número. Asume área de 2
    # dígitos (CABA/GBA, el único caso de uso real de esta app por ahora).
    if telefono.startswith("549") and len(telefono) == 13:
        return "54" + telefono[3:5] + "15" + telefono[5:]
    return telefono

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
                "to": _wa_a_formato_envio(telefono),
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
    if user_id != _WHATSAPP_USER_ID:
        return

    ia_disponible, parseado = _wa_interpretar_mensaje_ia(texto)
    if not ia_disponible:
        parseado = _parse_mensaje_whatsapp(texto)
    if not parseado:
        respuesta = _wa_responder_pregunta(user_id, texto)
        _wa_enviar_mensaje(telefono, respuesta or (
            "No entendí 🤔. Probá algo como: *gasté 500 en supermercado* o *ingreso 300000 sueldo*, "
            "o preguntame algo como *cuánto gasté en comida este mes*."
        ))
        return

    hoy = _hoy_ar().isoformat()
    ok, resultado = _insertar_transaccion(
        user_id, parseado["tipo"], parseado["monto"], hoy,
        categoria=parseado["categoria"], descripcion=parseado["descripcion"], moneda=parseado["moneda"],
    )
    if not ok:
        _wa_enviar_mensaje(
            telefono,
            "⛔ Llegaste al límite de *50* transacciones gratis este mes. Entrá a la app para hacerte Pro y seguir cargando.",
        )
        return

    simbolo = {"ARS": "$", "USD": "USD ", "EUR": "€"}.get(parseado["moneda"], "$")
    emoji = "🔴" if parseado["tipo"] == "Gasto" else "🟢"
    cat_txt = f" · {parseado['categoria']}" if parseado["categoria"] else ""
    desc_txt = f" · {parseado['descripcion']}" if parseado["descripcion"] else ""
    _wa_enviar_mensaje(telefono, f"{emoji} {parseado['tipo']} de *{simbolo}{parseado['monto']:,.2f}*{cat_txt}{desc_txt} registrado ✓")

# ── Stats ──────────────────────────────────────────────────────────────────────

def _stats_mes(user_id, mes, anio):
    from collections import defaultdict
    def _norm(s):
        s = (s or "otros").strip().lower()
        return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    inicio_mes = date(anio, mes, 1).isoformat()
    inicio_mes_ant = date(anio if mes > 1 else anio - 1, mes - 1 if mes > 1 else 12, 1).isoformat()
    fin_mes = date(anio if mes < 12 else anio + 1, mes + 1 if mes < 12 else 1, 1).isoformat()
    res_act = db.table("transacciones").select("tipo,monto,moneda,categoria").eq("user_id", user_id).gte("fecha", inicio_mes).lt("fecha", fin_mes).execute()
    res_ant = db.table("transacciones").select("tipo,monto,moneda").eq("user_id", user_id).gte("fecha", inicio_mes_ant).lt("fecha", inicio_mes).execute()
    cotiz = _obtener_cotizaciones()
    def _ars(t):
        conv = _convertir_moneda(float(t["monto"]), t.get("moneda") or "ARS", "ARS", cotiz)
        return conv if conv is not None else 0.0
    cats_total = defaultdict(float)
    cats_label = {}
    gas_act = ing_act = 0.0
    for t in res_act.data:
        m = _ars(t)
        if t["tipo"] == "Gasto":
            key = _norm(t.get("categoria"))
            cats_total[key] += m
            if key not in cats_label:
                cats_label[key] = (t.get("categoria") or "Otros").strip().capitalize()
            gas_act += m
        else:
            ing_act += m
    gas_ant = sum(_ars(t) for t in res_ant.data if t["tipo"] == "Gasto")
    ing_ant  = sum(_ars(t) for t in res_ant.data if t["tipo"] == "Ingreso")
    meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    return {
        "categorias": [{"nombre": cats_label[k], "total": v} for k, v in sorted(cats_total.items(), key=lambda x: -x[1])],
        "resumen": {
            "gastos_actual": gas_act, "ingresos_actual": ing_act,
            "gastos_anterior": gas_ant, "ingresos_anterior": ing_ant,
            "mes_actual": meses[mes - 1], "mes_anterior": meses[(mes - 2) % 12],
        },
        "count_mes": len(res_act.data),
    }

_resumen_ia_cache = {}  # (user_id, mes, anio) -> texto ya generado (solo meses cerrados)

# ── Viajes ──────────────────────────────────────────────────────────────────

def _payload_viaje(d):
    return {
        "nombre":       (d.get("nombre") or "").strip(),
        "fecha_inicio": d.get("fecha_inicio"),
        "fecha_fin":    d.get("fecha_fin"),
    }

# ── Pagos ─────────────────────────────────────────────────────────────────────

_PLANES_PRO = {
    "mensual": {"frequency": 1,  "monto": 6000,  "etiqueta": "Finanzas Pro (mensual)"},
    "anual":   {"frequency": 12, "monto": 60000, "etiqueta": "Finanzas Pro (anual)"},
}

# ── Registro de rutas (ver routes_*.py) ────────────────────────────────────────
# Cada archivo routes_*.py agrupa los endpoints de un area de la app (paginas,
# auth, finanzas/stats, viajes, whatsapp, pagos) y accede a todo lo de arriba
# (db, genai, helpers, caches) via "import finanzas_server as core", nunca con
# "from finanzas_server import x" -- eso rompería el mockeo en los tests, que
# reemplazan atributos de este modulo (core.db, core.genai, etc).

import routes_paginas  # noqa: E402
import routes_auth  # noqa: E402
import routes_finanzas  # noqa: E402
import routes_viajes  # noqa: E402
import routes_whatsapp  # noqa: E402
import routes_pagos  # noqa: E402

app.register_blueprint(routes_paginas.bp)
app.register_blueprint(routes_auth.bp)
app.register_blueprint(routes_finanzas.bp)
app.register_blueprint(routes_viajes.bp)
app.register_blueprint(routes_whatsapp.bp)
app.register_blueprint(routes_pagos.bp)

if __name__ == "__main__":
    import socket
    port = int(os.environ.get("PORT", 5001))
    ip = socket.gethostbyname(socket.gethostname())
    print(f"\n  Local:  http://localhost:{port}/finanzas\n")
    app.run(host="0.0.0.0", port=port, debug=False)
