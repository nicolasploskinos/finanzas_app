"""
Ingreso con Google (OAuth 2.0, flujo de authorization code).

Por qué importa más de lo que parece: hasta ahora una cuenta era usuario +
contraseña y nada más — sin email, no hay forma de recuperar el acceso. Si
alguien que paga olvida su contraseña, pierde la cuenta y todo su historial,
para siempre. Entrar con Google resuelve eso de raíz: el email llega ya
verificado por Google y la recuperación es "volvé a entrar con Google", sin
tener que montar envío de mails ni un flujo de reseteo.

Queda apagado si no están configuradas GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET;
el frontend pregunta por /api/montor/auth/config y no muestra el botón.

Sobre verificar el id_token: no se chequea la firma a propósito. El token no
viene del navegador sino de un POST nuestro a la URL de Google, sobre TLS y
autenticado con el client_secret; en el flujo de authorization code eso es
justamente lo que lo hace confiable (es lo que la propia documentación de
Google admite para este caso). Si el token llegara por el lado del cliente,
verificar la firma sí sería obligatorio.
"""
import base64
import json
import os
import re
import secrets
import unicodedata
from urllib.parse import urlencode

from flask import Blueprint, jsonify, redirect, request, session

import montor_server as core
import routes_auth

bp = Blueprint("google", __name__)

_AUTORIZAR = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN = "https://oauth2.googleapis.com/token"


def _configurado():
    return bool(os.environ.get("GOOGLE_CLIENT_ID") and os.environ.get("GOOGLE_CLIENT_SECRET"))


def _redirect_uri():
    """Tiene que coincidir EXACTO con la que se cargó en Google Cloud Console.

    Se fuerza https por lo mismo que la imagen de Open Graph: detrás del proxy
    de PythonAnywhere request.host_url llega como http, y Google rechaza el
    intercambio si la redirect_uri no es idéntica a la registrada.
    """
    base = (os.environ.get("BASE_URL") or request.host_url).rstrip("/")
    if base.startswith("http://") and not ("localhost" in base or "127.0.0.1" in base):
        base = "https://" + base[len("http://"):]
    return base + "/api/montor/auth/google/callback"


def _decodificar_id_token(id_token):
    """Payload del JWT, sin verificar firma (ver nota del encabezado)."""
    payload = id_token.split(".")[1]
    payload += "=" * (-len(payload) % 4)  # el base64url de JWT viene sin padding
    return json.loads(base64.urlsafe_b64decode(payload))


def _username_libre(email):
    """Un usuario legible a partir del email, que no choque con uno existente.

    El username sigue siendo la identidad visible de la cuenta (aparece en el
    saludo del panel), así que conviene que se parezca a la persona y no a un
    identificador de Google.
    """
    base = unicodedata.normalize("NFD", email.split("@")[0])
    base = "".join(c for c in base if unicodedata.category(c) != "Mn")
    base = re.sub(r"[^a-zA-Z0-9._-]", "", base).strip("._-").lower()[:20] or "usuario"

    candidato = base
    for intento in range(2, 60):
        existe = core.db.table("usuarios").select("id").eq("username", candidato).execute().data
        if not existe:
            return candidato
        candidato = f"{base}{intento}"
    return f"{base}{secrets.token_hex(3)}"


@bp.route("/api/montor/auth/config")
def config():
    """Le dice al frontend si mostrar el botón de Google."""
    return jsonify({"google": _configurado()})


@bp.route("/api/montor/auth/google")
def iniciar():
    if not _configurado():
        return redirect("/montor/login?error=google_no_configurado")

    # state: defensa contra CSRF. Se guarda en la sesión y se compara a la
    # vuelta; sin esto, un tercero podría inducir el callback con su propio
    # código y dejar al visitante logueado en una cuenta ajena.
    estado = secrets.token_urlsafe(24)
    session["google_state"] = estado

    return redirect(_AUTORIZAR + "?" + urlencode({
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": estado,
        # Fuerza el selector de cuenta: en una compu compartida, saltar
        # directo a la última cuenta usada es una forma fácil de entrar sin
        # querer con la cuenta de otro.
        "prompt": "select_account",
    }))


@bp.route("/api/montor/auth/google/callback")
def callback():
    if not _configurado():
        return redirect("/montor/login?error=google_no_configurado")

    esperado = session.pop("google_state", None)
    if not esperado or request.args.get("state") != esperado:
        return redirect("/montor/login?error=google_state")

    if request.args.get("error") or not request.args.get("code"):
        # El caso normal acá es que la persona haya cancelado en la pantalla
        # de Google: se la devuelve al login sin ruido.
        return redirect("/montor/login")

    try:
        resp = core.req.post(_TOKEN, data={
            "code": request.args["code"],
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "redirect_uri": _redirect_uri(),
            "grant_type": "authorization_code",
        }, timeout=15)
        resp.raise_for_status()
        datos = _decodificar_id_token(resp.json()["id_token"])
    except Exception as e:
        core.app.logger.error("fallo el intercambio de token con Google: %s", e)
        return redirect("/montor/login?error=google")

    email = (datos.get("email") or "").strip().lower()
    google_id = datos.get("sub")
    if not email or not google_id or not datos.get("email_verified"):
        return redirect("/montor/login?error=google_email")

    usuario = _buscar_o_crear(email, google_id)
    if not usuario:
        return redirect("/montor/login?error=google")

    session.permanent = True
    session["user_id"] = usuario["id"]
    session["username"] = usuario["username"]
    return redirect("/montor")


def _buscar_o_crear(email, google_id):
    """Devuelve la cuenta que corresponde a esa identidad de Google.

    Tres casos, en orden:
      1. Ya entró con Google antes -> se la reconoce por google_id.
      2. Existe una cuenta con ese email -> se vincula. Esto es lo que permite
         que alguien que se registró con usuario y contraseña pase a entrar
         con Google sin perder sus datos.
      3. No existe -> cuenta nueva, sin contraseña (la identidad la respalda
         Google), con la misma prueba de 7 días y los mismos movimientos de
         ejemplo que el registro normal.
    """
    por_google = core.db.table("usuarios").select("*").eq("google_id", google_id).execute().data
    if por_google:
        return por_google[0]

    por_email = core.db.table("usuarios").select("*").eq("email", email).execute().data
    if por_email:
        core.db.table("usuarios").update({"google_id": google_id}).eq("id", por_email[0]["id"]).execute()
        return por_email[0]

    from datetime import datetime, timedelta, timezone

    res = core.db.table("usuarios").insert({
        "username": _username_libre(email),
        "email": email,
        "google_id": google_id,
        "password_hash": None,  # la identidad la respalda Google
        "verificado": True,
        "plan": "trial",
        "trial_expira": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    }).execute()
    if not res.data:
        return None

    nuevo = res.data[0]
    routes_auth.sembrar_ejemplos(nuevo["id"])
    return nuevo
