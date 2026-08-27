import os
import re
import sys
import json
import time
import unicodedata
import calendar
import requests as req
from google import genai
from google.genai import types as genai_types
from flask import Flask, session, redirect, request, jsonify
from flask_cors import CORS
from supabase import create_client
from functools import wraps
from datetime import date, timedelta, datetime, timezone
from dotenv import load_dotenv

load_dotenv()

# Cuando este archivo se ejecuta directamente ("python finanzas_server.py"),
# Python lo registra en sys.modules como "__main__", no como "finanzas_server".
# Los routes_*.py hacen "import finanzas_server as core": sin esta línea, ese
# import no encuentra el módulo ya cargado y re-ejecuta este archivo entero
# desde cero como una instancia separada, chocando más abajo al registrar los
# blueprints sobre el módulo equivocado.
sys.modules.setdefault("finanzas_server", sys.modules[__name__])

_inflacion_cache = {"data": None, "ts": 0}
_cotiz_cache = {"data": None, "ts": 0}
_evolucion_usd_cache = {"data": None, "ts": 0}
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

def _pagina_error(titulo, mensaje):
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo} — Finanzas</title>
<style>
  body {{ font-family: -apple-system, "Segoe UI", sans-serif; background:#0f0f1a; color:#e2e8f0;
         display:flex; align-items:center; justify-content:center; min-height:100vh; margin:0; text-align:center; }}
  div {{ padding: 24px; }}
  h1 {{ font-size: 22px; margin: 0 0 8px; }}
  p {{ color:#94a3b8; margin: 0 0 20px; }}
  a {{ color:#60a5fa; text-decoration:none; }}
</style></head>
<body><div><h1>{titulo}</h1><p>{mensaje}</p><a href="/finanzas">Volver a Finanzas</a></div></body></html>"""


@app.errorhandler(404)
def _error_404(e):
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "not_found"}), 404
    return _pagina_error("Página no encontrada", "La página que buscás no existe o cambió de lugar."), 404


@app.errorhandler(500)
def _error_500(e):
    print(f"[error 500] {request.method} {request.path}: {e}")
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "server_error"}), 500
    return _pagina_error("Algo salió mal", "Tuvimos un error inesperado. Ya estamos al tanto, probá de nuevo en un rato."), 500

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

def _evolucion_usd():
    """Serie histórica día -> cotización oficial del dólar (bluelytics tiene
    esto desde 2011). Se cachea una hora: es un archivo grande y el histórico
    no cambia, solo se le agrega el día de hoy."""
    if _evolucion_usd_cache["data"] and time.time() - _evolucion_usd_cache["ts"] < 3600:
        return _evolucion_usd_cache["data"]
    try:
        r = req.get("https://api.bluelytics.com.ar/v2/evolution.json", timeout=8)
        serie = {d["date"]: round(d["value_sell"], 2) for d in r.json() if d.get("source") == "Oficial"}
    except Exception:
        serie = {}
    _evolucion_usd_cache["data"] = serie
    _evolucion_usd_cache["ts"] = time.time()
    return serie

def _cotizacion_para_fecha(fecha_str):
    """Cotización a guardar en una transacción con fecha "fecha_str" (para
    carga tardía con fecha pasada, no para el día de hoy). El dólar histórico
    sale de _evolucion_usd(); como bluelytics no publica fin de semana ni
    feriados, se busca hacia atrás hasta la fecha publicada más cercana. El
    euro no tiene serie histórica pública en esta API: se aproxima aplicando
    a ese dólar histórico la relación EUR/USD de la cotización en vivo de
    hoy - es una aproximación razonable para cargas recientes, no un valor
    exacto de esa fecha."""
    hoy = _hoy_ar()
    try:
        fecha = date.fromisoformat(fecha_str)
    except (TypeError, ValueError):
        fecha = hoy
    if fecha >= hoy:
        return _obtener_cotizaciones()

    serie = _evolucion_usd()
    usd_hist = None
    for atras in range(10):
        candidata = (fecha - timedelta(days=atras)).isoformat()
        if candidata in serie:
            usd_hist = serie[candidata]
            break
    if usd_hist is None:
        return _obtener_cotizaciones()

    cotiz_live = _obtener_cotizaciones()
    eur_hist = None
    if cotiz_live.get("USD") and cotiz_live.get("EUR"):
        eur_hist = round(usd_hist * (cotiz_live["EUR"] / cotiz_live["USD"]), 2)
    return {"USD": usd_hist, "EUR": eur_hist}

def _convertir_moneda(monto, origen, destino, cotiz):
    if origen == destino:
        return monto
    ars = monto if origen == "ARS" else (monto * cotiz[origen] if cotiz.get(origen) else None)
    if ars is None:
        return None
    if destino == "ARS":
        return ars
    return ars / cotiz[destino] if cotiz.get(destino) else None

def _cotiz_de_tx(t, cotiz_fallback):
    """Cada transacción guarda la cotización del día en que se cargó (ver
    _insertar_transaccion). Para calcular totales usamos esa foto histórica en
    vez de la cotización de hoy, así los montos ya cargados no se revalúan
    solos con el paso del tiempo. cotiz_fallback cubre las filas viejas,
    cargadas antes de que existiera esta columna."""
    return {
        "USD": t.get("cotizacion_usd") or cotiz_fallback.get("USD"),
        "EUR": t.get("cotizacion_eur") or cotiz_fallback.get("EUR"),
    }

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
    if not pendientes:
        return
    for r in pendientes:
        prox = r["proxima_fecha"]
        while prox <= hoy:
            # Si el backfill genera una fila con fecha pasada (ej: la app no
            # se abrió en varios meses), usa la cotización histórica de esa
            # fecha en vez de la de hoy.
            cotiz = _cotizacion_para_fecha(prox)
            db.table("transacciones").insert({
                "tipo": r["tipo"], "monto": r["monto"], "fecha": prox,
                "categoria": r["categoria"], "descripcion": r["descripcion"],
                "moneda": r["moneda"], "user_id": user_id,
                "cotizacion_usd": cotiz.get("USD"), "cotizacion_eur": cotiz.get("EUR"),
            }).execute()
            prox = _siguiente_fecha(prox, r["frecuencia"])
        db.table("recurrentes").update({"proxima_fecha": prox}).eq("id", r["id"]).execute()

def _insertar_transaccion(user_id, tipo, monto, fecha, categoria="", descripcion="", moneda="ARS", viaje_id=None):
    if not _es_pro(user_id):
        inicio_mes = _hoy_ar().replace(day=1).isoformat()
        count = len(db.table("transacciones").select("id").eq("user_id", user_id).gte("fecha", inicio_mes).execute().data)
        if count >= 50:
            return False, "limite_pro"
    # Se guarda la cotización del día de la transacción (la de hoy si es de
    # hoy, la histórica de esa fecha si es una carga tardía con fecha
    # pasada), para que los totales no se revalúen solos con el tiempo.
    cotiz = _cotizacion_para_fecha(fecha)
    payload = {
        "tipo": tipo, "monto": float(monto), "fecha": fecha,
        "categoria": categoria or "", "descripcion": descripcion or "",
        "moneda": moneda or "ARS", "user_id": user_id, "viaje_id": viaje_id,
        "cotizacion_usd": cotiz.get("USD"), "cotizacion_eur": cotiz.get("EUR"),
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
    # español
    "ingreso", "ingrese", "ingresaron",
    "cobre", "cobro",
    "deposito", "depositaron",
    "recibi",
    "gane",
    "sueldo",
    # inglés
    "income", "received", "earned", "deposited", "salary", "paycheck",
}
_WA_PALABRAS_DESCARTE = {
    # español
    "gaste", "gasto", "pague",
    "cobre", "cobro", "ingreso", "ingrese", "ingresaron", "deposito", "depositaron", "recibi", "gane",
    "en", "de", "del", "la", "el", "los", "las", "me",
    "usd", "dolar", "dolares", "eur", "euro", "euros",
    # inglés
    "spent", "paid", "income", "received", "earned", "deposited", "salary", "paycheck", "got", "bought",
    "on", "for", "the", "a", "an", "of", "my", "i",
    "dollar", "dollars", "bucks", "pound", "pounds",
}

# Palabras inequívocamente de un idioma u otro, para poder responder en el
# mismo idioma incluso cuando la IA no está disponible y se usa el regex.
_WA_MARCADORES_ES = {
    "gaste", "gasto", "pague", "cobre", "cobro", "ingreso", "recibi", "gane", "sueldo",
    "en", "de", "del", "la", "el", "los", "las", "eso", "esto", "ultimo", "ultima", "borra", "borrar", "elimina",
}
_WA_MARCADORES_EN = {
    "spent", "paid", "income", "received", "earned", "deposited", "salary", "paycheck", "got", "bought",
    "on", "for", "the", "a", "an", "my", "that", "this", "last", "one", "undo", "delete", "remove", "please",
}

def _wa_detectar_idioma_regex(texto):
    palabras = re.findall(r"[a-z]+", _norm_header(texto))
    hits_en = sum(1 for p in palabras if p in _WA_MARCADORES_EN)
    hits_es = sum(1 for p in palabras if p in _WA_MARCADORES_ES)
    return "en" if hits_en > hits_es else "es"

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
    if any(p in palabras for p in ("usd", "dolar", "dolares", "u$s", "dollar", "dollars", "bucks")):
        moneda = "USD"
    elif any(p in palabras for p in ("eur", "euro", "euros")):
        moneda = "EUR"

    resto = limpio[:match.start()] + limpio[match.end():]
    cat_palabras = [w for w in re.findall(r"[a-z]+", resto) if w not in _WA_PALABRAS_DESCARTE]
    categoria = " ".join(cat_palabras).strip().capitalize()

    return {"tipo": tipo, "monto": round(abs(monto), 2), "moneda": moneda, "categoria": categoria, "descripcion": descripcion}

_WA_SCHEMA_INTERPRETACION = {
    "type": "object",
    "properties": {
        "idioma": {"type": "string", "enum": ["es", "en"]},
        "intencion": {"type": "string", "enum": ["carga", "borrar_ultimo", "otro"]},
        "tipo": {"type": "string", "enum": ["Gasto", "Ingreso"]},
        "monto": {"type": "number"},
        "moneda": {"type": "string", "enum": ["ARS", "USD", "EUR"]},
        "categoria": {"type": "string"},
        "descripcion": {"type": "string"},
    },
    "required": ["idioma", "intencion"],
}

def _wa_interpretar_mensaje_ia(texto):
    """Intenta interpretar el mensaje con Gemini, más tolerante que las reglas
    fijas de respaldo (jerga, montos aproximados, frases sueltas, español o
    inglés, y cada quien lo escribe o lo dice a su manera). Devuelve
    (disponible, accion, idioma, datos):
    - (False, None, "es", None): la IA no está disponible (sin key, error,
      timeout) — el llamador debe usar las reglas de respaldo (regex).
    - (True, None, idioma, None): la IA entendió que no es ni una carga ni
      un pedido de borrar — probablemente una pregunta o charla.
    - (True, "borrar_ultimo", idioma, None): quiere deshacer lo último que cargó.
    - (True, "carga", idioma, dict): la IA extrajo una transacción.
    idioma es "es" o "en", detectado a partir del mensaje."""
    if not os.environ.get("GEMINI_API_KEY"):
        return False, None, "es", None

    # Convención de siempre: lo que va entre paréntesis es la descripción,
    # tal cual, sin que la IA lo reinterprete. Se lo sacamos del texto antes
    # de mandarlo, así la categoría se infiere solo del resto del mensaje —
    # mismo comportamiento que el parser regex de respaldo.
    desc_match = re.search(r"\(([^)]+)\)", texto)
    descripcion_forzada = desc_match.group(1).strip() if desc_match else None
    texto_ia = (texto[:desc_match.start()] + texto[desc_match.end():]) if desc_match else texto

    prompt = (
        "Interpretá este mensaje de WhatsApp de alguien llevando sus finanzas personales. Puede estar en "
        "español rioplatense informal (jerga como 'lucas' o 'palos' para miles/millones, montos aproximados, "
        "abreviaturas, faltas de ortografía) o en inglés — cada persona escribe o habla distinto, así que "
        "interpretá la intención, no una frase exacta.\n\n"
        f'Mensaje: "{texto_ia}"\n\n'
        "Primero detectá el idioma del mensaje (idioma: 'es' o 'en').\n\n"
        "Después elegí la intención (intencion):\n"
        "- 'carga': describe un gasto o ingreso concreto, con un monto (ej: 'gasté 500 en el super', "
        "'me cayeron 300 lucas de sueldo', 'spent 50 bucks on groceries'). Completá también: tipo (Gasto o "
        "Ingreso; asumí Gasto si no queda claro), monto (número, convertí jerga como 'lucas'=miles, "
        "'palos'=millones, o abreviaturas tipo '5k'=5000 a su valor real, sin separadores), moneda (ARS por "
        "defecto, USD o EUR solo si se menciona explícitamente), categoria (una palabra corta, en el mismo "
        "idioma del mensaje, ej: comida/food, transporte/transport, sueldo/salary — vacío si no hay ninguna "
        "pista), descripcion (detalle breve opcional, vacío si no aporta nada nuevo).\n"
        "- 'borrar_ultimo': quiere deshacer o borrar lo último que cargó por este chat, de cualquier forma en "
        "que lo pida, en cualquier idioma (ej: 'borrá lo último', 'sacá el último gasto', 'epa me equivoqué, "
        "borralo', 'undo that', 'delete the last one', 'oops, remove it'). No hace falta que use palabras "
        "exactas.\n"
        "- 'otro': cualquier otra cosa (pregunta, saludo, charla, o un gasto/ingreso sin monto claro). No "
        "completes los demás campos en este caso."
    )
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                               http_options=genai_types.HttpOptions(timeout=25000))
        resp = client.models.generate_content(
            model="gemini-3.5-flash-lite", contents=prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=_WA_SCHEMA_INTERPRETACION,
            ),
        )
        data = json.loads(resp.text)
    except Exception:
        return False, None, "es", None

    idioma = data.get("idioma") if data.get("idioma") in ("es", "en") else "es"
    intencion = data.get("intencion")
    if intencion == "borrar_ultimo":
        return True, "borrar_ultimo", idioma, None
    if intencion != "carga":
        return True, None, idioma, None

    try:
        monto = float(data.get("monto") or 0)
    except (TypeError, ValueError):
        monto = 0
    if monto <= 0:
        return True, None, idioma, None

    tipo = data.get("tipo") if data.get("tipo") in ("Gasto", "Ingreso") else "Gasto"
    moneda = data.get("moneda") if data.get("moneda") in ("ARS", "USD", "EUR") else "ARS"
    descripcion = descripcion_forzada if descripcion_forzada is not None else (data.get("descripcion") or "").strip()
    return True, "carga", idioma, {
        "tipo": tipo,
        "monto": round(monto, 2),
        "moneda": moneda,
        "categoria": (data.get("categoria") or "").strip().capitalize(),
        "descripcion": descripcion,
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
        "La pregunta puede estar en español o en inglés — respondé siempre en el mismo idioma en el que está "
        "escrita la pregunta. Respondé corto y directo (máximo 3-4 líneas), como si fueras un amigo que te "
        "cuenta cómo vienen tus cuentas — nada de tono de sistema, atención al cliente, ni listas. "
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

def _wa_descargar_media(media_id):
    """Los medios de WhatsApp no vienen en el webhook: hay que pedirle a Meta
    la URL temporal del archivo y después descargarlo aparte."""
    token = os.environ.get("WHATSAPP_TOKEN", "")
    if not token or not media_id:
        return None, None
    try:
        meta = req.get(
            f"https://graph.facebook.com/v20.0/{media_id}",
            headers={"Authorization": f"Bearer {token}"}, timeout=10,
        ).json()
        url = meta.get("url")
        if not url:
            return None, None
        r = req.get(url, headers={"Authorization": f"Bearer {token}"}, timeout=20)
        if not r.ok:
            return None, None
        return r.content, meta.get("mime_type", "audio/ogg")
    except Exception:
        return None, None

def _wa_transcribir_audio(audio_bytes, mime_type):
    if not os.environ.get("GEMINI_API_KEY"):
        return None
    try:
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"],
                               http_options=genai_types.HttpOptions(timeout=20000))
        parte_audio = genai_types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        prompt = (
            "Transcribí exactamente lo que se dice en este audio de WhatsApp, en el mismo idioma en el que "
            "habla la persona (español o inglés), tal cual se dijo (incluyendo jerga o números tal como se "
            "pronuncian). Devolvé solo la transcripción en texto corrido, sin comillas ni comentarios adicionales."
        )
        resp = client.models.generate_content(model="gemini-3.5-flash-lite", contents=[parte_audio, prompt])
        return (resp.text or "").strip() or None
    except Exception:
        return None

_WA_TEXTOS = {
    "audio_no_entendido": {
        "es": "No llegué a entender bien el audio 😅 ¿Me lo repetís o me lo escribís posta?",
        "en": "I couldn't quite make out that audio 😅 Can you say it again, or just type it?",
    },
    "vincular_vencido": {
        "es": "Ese código ya no sirve, está vencido o mal escrito 🤔 Generá uno nuevo desde la app y probamos de nuevo.",
        "en": "That code doesn't work anymore, it's expired or mistyped 🤔 Generate a new one from the app and let's try again.",
    },
    "vincular_ok": {
        "es": "¡Listo! Ya te tengo agendado 🙌 De ahora en más contame tus gastos e ingresos como si me estuvieras escribiendo a un amigo.",
        "en": "Done! You're all set 🙌 From now on just tell me your expenses and income like you'd text a friend.",
    },
    "no_vinculado": {
        "es": "Todavía no te conozco 👋 Vinculá este WhatsApp desde la app (Finanzas → sección WhatsApp → Vincular) y arrancamos.",
        "en": "I don't know you yet 👋 Link this WhatsApp from the app (Finanzas → WhatsApp section → Link) and we'll get started.",
    },
    "borrar_nada": {
        "es": "No tengo ninguna carga reciente por acá para borrar 🤔 ¿Seguro que cargaste algo hace poco?",
        "en": "I don't have anything recent here to delete 🤔 Are you sure you logged something recently?",
    },
    "borrado_generico": {
        "es": "Listo, ya lo borré 🗑️",
        "en": "Done, deleted it 🗑️",
    },
    "no_entendi": {
        "es": "No te entendí bien 😅 Contame algo como *gasté 500 en el super* o *cobré 300000 de sueldo*, "
              "o preguntame algo tipo *cuánto gasté en comida este mes*.",
        "en": "I didn't quite get that 😅 Try something like *spent 500 on groceries* or *got paid 300000*, "
              "or ask me something like *how much did I spend on food this month*.",
    },
    "limite": {
        "es": "Che, llegaste al límite de *50* cargas gratis este mes ⛔ Si querés seguir sin cortarte, pasate a Pro desde la app.",
        "en": "Hey, you hit the *50* free entries limit this month ⛔ Upgrade to Pro from the app if you want to keep going.",
    },
}

def _wa_texto(codigo, idioma):
    return _WA_TEXTOS[codigo].get(idioma if idioma in ("es", "en") else "es") or _WA_TEXTOS[codigo]["es"]

def _wa_borrar_ultima_transaccion(telefono, user_id, tx_id, idioma="es"):
    if not tx_id:
        _wa_enviar_mensaje(telefono, _wa_texto("borrar_nada", idioma))
        return
    borrado = db.table("transacciones").select("tipo,monto,moneda,categoria").eq("id", tx_id).eq("user_id", user_id).execute().data
    db.table("transacciones").delete().eq("id", tx_id).eq("user_id", user_id).execute()
    db.table("whatsapp_users").update({"ultima_transaccion_id": None}).eq("telefono", telefono).execute()
    if borrado:
        t = borrado[0]
        simbolo = {"ARS": "$", "USD": "USD ", "EUR": "€"}.get(t.get("moneda") or "ARS", "$")
        cat_txt = f" · {t['categoria']}" if t.get("categoria") else ""
        if idioma == "en":
            articulo = "the expense" if t["tipo"] == "Gasto" else "the income"
            _wa_enviar_mensaje(telefono, f"Done, deleted {articulo} of *{simbolo}{float(t['monto']):,.2f}*{cat_txt} 🗑️")
        else:
            articulo = "el gasto" if t["tipo"] == "Gasto" else "el ingreso"
            _wa_enviar_mensaje(telefono, f"Listo, borré {articulo} de *{simbolo}{float(t['monto']):,.2f}*{cat_txt} 🗑️")
    else:
        _wa_enviar_mensaje(telefono, _wa_texto("borrado_generico", idioma))

def _procesar_mensaje_whatsapp(msg):
    wamid = msg.get("id")
    if not wamid or wamid in _wa_procesados:
        return
    _wa_procesados.add(wamid)
    if len(_wa_procesados) > 2000:
        _wa_procesados.clear()

    telefono = msg.get("from", "")
    if not telefono:
        return

    if msg.get("type") == "audio":
        audio_bytes, mime_type = _wa_descargar_media((msg.get("audio") or {}).get("id"))
        texto = _wa_transcribir_audio(audio_bytes, mime_type) if audio_bytes else None
        print(f"[whatsapp] audio recibido de '{telefono}', transcripción: {texto!r}")
        if not texto:
            _wa_enviar_mensaje(telefono, _wa_texto("audio_no_entendido", "es"))
            return
    else:
        texto = ((msg.get("text") or {}).get("body") or "").strip()
        print(f"[whatsapp] mensaje recibido de '{telefono}': {texto!r}")
        if not texto:
            return

    m = re.match(r"(?i)^vincular\s+(\d{6})$", texto.strip())
    if m:
        codigo = m.group(1)
        entrada = _wa_codigos.get(codigo)
        if not entrada or entrada[1] < time.time():
            _wa_enviar_mensaje(telefono, _wa_texto("vincular_vencido", "es"))
            return
        db.table("whatsapp_users").upsert({"telefono": telefono, "user_id": entrada[0]}, on_conflict="telefono").execute()
        _wa_codigos.pop(codigo, None)
        _wa_enviar_mensaje(telefono, _wa_texto("vincular_ok", "es"))
        return

    vinculo = db.table("whatsapp_users").select("user_id,ultima_transaccion_id").eq("telefono", telefono).execute()
    if not vinculo.data:
        _wa_enviar_mensaje(telefono, _wa_texto("no_vinculado", "es"))
        return
    user_id = vinculo.data[0]["user_id"]
    if user_id != _WHATSAPP_USER_ID:
        return

    ia_disponible, accion, idioma, datos = _wa_interpretar_mensaje_ia(texto)
    if not ia_disponible:
        # Sin IA disponible: reglas fijas de respaldo, más rígidas que el
        # entendimiento libre de la IA pero que nunca dejan a la carga sin
        # funcionar del todo (incluyen tanto español como inglés).
        idioma = _wa_detectar_idioma_regex(texto)
        if re.match(r"(?i)^(borrar|eliminar)\s+(el\s+|la\s+)?(ultimo|último|ultima|última)(\s+(gasto|ingreso))?$", texto.strip()) or \
           re.match(r"(?i)^(undo|delete|remove)\b", texto.strip()):
            accion, datos = "borrar_ultimo", None
        else:
            parseado_regex = _parse_mensaje_whatsapp(texto)
            accion, datos = ("carga", parseado_regex) if parseado_regex else (None, None)

    if accion == "borrar_ultimo":
        _wa_borrar_ultima_transaccion(telefono, user_id, vinculo.data[0].get("ultima_transaccion_id"), idioma)
        return

    if accion != "carga" or not datos:
        respuesta = _wa_responder_pregunta(user_id, texto)
        _wa_enviar_mensaje(telefono, respuesta or _wa_texto("no_entendi", idioma))
        return

    parseado = datos
    hoy = _hoy_ar().isoformat()
    ok, resultado = _insertar_transaccion(
        user_id, parseado["tipo"], parseado["monto"], hoy,
        categoria=parseado["categoria"], descripcion=parseado["descripcion"], moneda=parseado["moneda"],
    )
    if not ok:
        _wa_enviar_mensaje(telefono, _wa_texto("limite", idioma))
        return

    db.table("whatsapp_users").update({"ultima_transaccion_id": resultado["id"]}).eq("telefono", telefono).execute()

    simbolo = {"ARS": "$", "USD": "USD ", "EUR": "€"}.get(parseado["moneda"], "$")
    emoji = "🔴" if parseado["tipo"] == "Gasto" else "🟢"
    cat_txt = f" · {parseado['categoria']}" if parseado["categoria"] else ""
    desc_txt = f" · {parseado['descripcion']}" if parseado["descripcion"] else ""
    if idioma == "en":
        tipo_txt = "expense" if parseado["tipo"] == "Gasto" else "income"
        _wa_enviar_mensaje(telefono, f"{emoji} Logged your {tipo_txt} of *{simbolo}{parseado['monto']:,.2f}*{cat_txt}{desc_txt} ✓")
    else:
        tipo_txt = "gasto" if parseado["tipo"] == "Gasto" else "ingreso"
        _wa_enviar_mensaje(telefono, f"{emoji} Anoté tu {tipo_txt} de *{simbolo}{parseado['monto']:,.2f}*{cat_txt}{desc_txt} ✓")

# ── Stats ──────────────────────────────────────────────────────────────────────

def _stats_mes(user_id, mes, anio):
    from collections import defaultdict
    def _norm(s):
        s = (s or "otros").strip().lower()
        return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    inicio_mes = date(anio, mes, 1).isoformat()
    inicio_mes_ant = date(anio if mes > 1 else anio - 1, mes - 1 if mes > 1 else 12, 1).isoformat()
    fin_mes = date(anio if mes < 12 else anio + 1, mes + 1 if mes < 12 else 1, 1).isoformat()
    res_act = db.table("transacciones").select("tipo,monto,moneda,categoria,cotizacion_usd,cotizacion_eur").eq("user_id", user_id).gte("fecha", inicio_mes).lt("fecha", fin_mes).execute()
    res_ant = db.table("transacciones").select("tipo,monto,moneda,cotizacion_usd,cotizacion_eur").eq("user_id", user_id).gte("fecha", inicio_mes_ant).lt("fecha", inicio_mes).execute()
    cotiz_live = _obtener_cotizaciones()
    def _ars(t):
        conv = _convertir_moneda(float(t["monto"]), t.get("moneda") or "ARS", "ARS", _cotiz_de_tx(t, cotiz_live))
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
