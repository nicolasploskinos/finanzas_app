"""Páginas HTML (no-API): landing, dashboard, login, PWA."""
import json
import os
from flask import Blueprint, render_template, request, session, redirect, send_from_directory

import montor_server as core

bp = Blueprint("paginas", __name__)

_APP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "app")
_MANIFEST = os.path.join(_APP_DIR, ".vite", "manifest.json")
_assets_cache = {"mtime": None, "valor": None}

_OG_IMAGEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "og-montor.png")


def _og_image_url():
    """URL absoluta de la imagen de preview al compartir el link.

    Tiene que ser absoluta y https: los crawlers (WhatsApp, Twitter) no
    resuelven rutas relativas, y detrás del proxy de PythonAnywhere
    `request.host_url` llega como http:// aunque el sitio se sirva por
    https — sin forzarlo, la imagen quedaría detrás de un redirect que
    varios crawlers no siguen.

    El `?v=` con el mtime es para poder refrescarla: WhatsApp y Facebook
    cachean el preview de una URL casi indefinidamente, así que cambiar el
    archivo sin cambiar la URL no se vería nunca.
    """
    base = (os.environ.get("BASE_URL") or request.host_url).rstrip("/")
    if base.startswith("http://") and not ("localhost" in base or "127.0.0.1" in base):
        base = "https://" + base[len("http://"):]
    try:
        version = int(os.path.getmtime(_OG_IMAGEN))
    except OSError:
        return None
    return f"{base}/static/og-montor.png?v={version}"


def _spa_assets():
    """Nombres de los archivos del build (con hash), leídos del manifest de
    Vite. El hash va en el nombre y no en un `?v=`: con code splitting, la
    plantilla cargaba `montor.js?v=...` mientras los chunks importaban
    `./montor.js` a secas, y el navegador —que identifica los módulos por
    URL— evaluaba el entry dos veces, quedando con dos copias de React.

    El build se commitea (PythonAnywhere no corre Node), así que el manifest
    siempre está en disco; se cachea por mtime para no leerlo en cada request.
    """
    try:
        mtime = os.path.getmtime(_MANIFEST)
    except OSError:
        return {"js": "montor.js", "css": "montor.css"}

    if _assets_cache["mtime"] != mtime:
        with open(_MANIFEST, encoding="utf-8") as f:
            manifest = json.load(f)
        entrada = next((v for v in manifest.values() if v.get("isEntry")), {})
        # Con cssCodeSplit apagado el CSS no cuelga de la entrada, sino que
        # queda como un asset suelto bajo la clave "style.css".
        css = (entrada.get("css") or [manifest.get("style.css", {}).get("file", "montor.css")])[0]
        _assets_cache.update(
            mtime=mtime, valor={"js": entrada.get("file", "montor.js"), "css": css}
        )
    return _assets_cache["valor"]


@bp.route("/")
def landing():
    # Migrada a React (ver templates/spa.html y frontend/). titulo_completo
    # + los meta/og se pasan explícitos porque esta es la única página
    # pública que de verdad le importa a SEO/compartir en redes.
    return render_template(
        "spa.html",
        titulo_completo="Montor — Control de gastos en ARS, USD y EUR",
        meta_description="Controlá tus gastos e ingresos en pesos, dólares y euros. Cotización oficial BNA automática. Gratis.",
        og_title="Montor — Control de gastos en ARS, USD y EUR",
        og_description="La app que entiende la economía argentina. Manejá pesos y dólares en un solo lugar, con cotización oficial actualizada.",
        og_image=_og_image_url(),
        assets=_spa_assets(),
    )


@bp.route("/privacidad")
def privacidad():
    # Migrada a React (ver templates/spa.html y frontend/).
    return render_template("spa.html", titulo="Política de Privacidad", assets=_spa_assets())


@bp.route("/terminos")
def terminos():
    # Migrada a React (ver templates/spa.html y frontend/).
    return render_template("spa.html", titulo="Términos de Servicio", assets=_spa_assets())


@bp.route("/montor")
@core.login_required
def index():
    # Migrada a React (ver templates/spa.html y frontend/). El usuario, el
    # plan y todo lo demás los pide el propio frontend por /api/montor/me.
    return render_template("spa.html", titulo_completo="Montor", pwa=True, assets=_spa_assets())


@bp.route("/montor/viajes")
@core.login_required
def viajes_page():
    # Migrada a React (ver templates/spa.html y frontend/).
    return render_template("spa.html", titulo="Viajes", assets=_spa_assets())


@bp.route("/montor/analisis")
@core.login_required
def analisis_page():
    # Migrada a React. El resto de las páginas sigue en Jinja; los datos
    # (usuario, plan, transacciones) los pide el propio frontend por la API.
    return render_template("spa.html", titulo="Análisis", assets=_spa_assets())


@bp.route("/montor/login")
def login_page():
    if "user_id" in session:
        return redirect("/montor")
    # Migrada a React (ver templates/spa.html y frontend/).
    return render_template("spa.html", titulo="Ingresar", assets=_spa_assets())


@bp.route("/montor/logout")
def logout():
    session.clear()
    return redirect("/montor/login")


@bp.route("/montor/manifest.json")
def manifest():
    return send_from_directory("static", "montor_manifest.json", mimetype="application/manifest+json")


@bp.route("/montor/sw.js")
def sw():
    return send_from_directory("static", "montor_sw.js", mimetype="application/javascript")
