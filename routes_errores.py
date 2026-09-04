"""
Registro de errores, del backend y del frontend.

Sin esto, la única forma de enterarse de que a alguien se le rompió una
pantalla es que se tome el trabajo de avisar — y la mayoría no avisa, se va.
La página de error del server ya le promete al usuario "ya estamos al tanto";
esto es lo que hace que sea cierto.

Dos reglas que valen para todo el módulo:

1. Registrar un error NUNCA puede romper el pedido que lo estaba atendiendo.
   Si Supabase está caído justo cuando queremos anotar la falla, el usuario
   no tiene que enterarse por partida doble: se cae a `app.logger` y sigue.
2. El texto viene de afuera (el navegador del visitante), así que se recorta
   y se trata como dato, nunca como algo confiable.
"""
import time

from flask import Blueprint, jsonify, request, session

import montor_server as core

bp = Blueprint("errores", __name__)

# Recortes: un stack de React puede venir enorme, y no aporta nada guardar
# 200 kB por fila. Con el principio del stack alcanza para ubicar la falla.
_MAX_MENSAJE = 2_000
_MAX_STACK = 8_000
_MAX_RUTA = 500
_MAX_USER_AGENT = 400

# Tope por IP: si una pantalla entra en loop de render, el navegador puede
# disparar cientos de reportes por minuto. Interesa el primero, no la
# avalancha — y menos llenar la tabla.
_MAX_REPORTES = 20
_VENTANA_SEGUNDOS = 5 * 60
_reportes = {}  # ip -> [timestamps]


def _recortar(valor, tope):
    if valor is None:
        return None
    texto = str(valor).strip()
    if not texto:
        return None
    return texto[:tope]


# ── Aviso por WhatsApp ────────────────────────────────────────────────────
# Una tabla que nadie abre no sirve de nada: el punto de todo esto es
# enterarse sin que el usuario tenga que avisar. Se reusa el WhatsApp que ya
# está integrado para el bot.
#
# Dos topes, porque una pantalla en loop puede generar cientos de errores y
# no queremos que el teléfono explote:
#   - el mismo mensaje no se avisa dos veces en varias horas,
#   - y hay un máximo de avisos por hora, sea cual sea el error.
_AVISO_MISMO_ERROR_SEG = 6 * 60 * 60
_AVISO_MAX_POR_HORA = 4
_avisados = {}       # mensaje -> timestamp del último aviso
_avisos_recientes = []  # timestamps, para el tope por hora


def _corresponde_avisar(mensaje):
    ahora = time.time()
    if ahora - _avisados.get(mensaje, 0) < _AVISO_MISMO_ERROR_SEG:
        return False
    del _avisos_recientes[: len(_avisos_recientes) - _AVISO_MAX_POR_HORA * 4]
    recientes = [t for t in _avisos_recientes if ahora - t < 3600]
    _avisos_recientes[:] = recientes
    if len(recientes) >= _AVISO_MAX_POR_HORA:
        return False
    _avisados[mensaje] = ahora
    _avisos_recientes.append(ahora)
    return True


def _avisar(origen, mensaje, ruta):
    """Manda el error por WhatsApp. Nunca propaga: avisar de una falla no
    puede ser, a su vez, una falla.

    Ojo con una limitación de la API de Meta: fuera de las 24 h desde el
    último mensaje del usuario al bot, sólo se pueden mandar plantillas
    aprobadas, no texto libre. Si pasa eso el envío falla y queda registrado
    en el log — el error igual quedó guardado en la tabla.
    """
    try:
        if not _corresponde_avisar(mensaje):
            return
        res = (
            core.db.table("whatsapp_users")
            .select("telefono")
            .eq("user_id", core._WHATSAPP_USER_ID)
            .execute()
        )
        if not res.data:
            return
        partes = [f"⚠️ Montor: error en el {origen}", "", mensaje[:300]]
        if ruta:
            partes += ["", f"En: {ruta}"]
        core._wa_enviar_mensaje(res.data[0]["telefono"], "\n".join(partes))
    except Exception as e:
        core.app.logger.error("no se pudo avisar del error por WhatsApp: %s", e)


def registrar(origen, mensaje, stack=None, ruta=None, user_id=None, user_agent=None):
    """Guarda un error. Devuelve True si quedó anotado en la base.

    Pensada para llamarse desde un `except`: se traga cualquier problema
    propio antes que propagarlo hacia arriba.
    """
    mensaje = _recortar(mensaje, _MAX_MENSAJE)
    if not mensaje:
        return False

    fila = {
        "origen": origen,
        "mensaje": mensaje,
        "stack": _recortar(stack, _MAX_STACK),
        "ruta": _recortar(ruta, _MAX_RUTA),
        "user_id": user_id,
        "user_agent": _recortar(user_agent, _MAX_USER_AGENT),
    }
    try:
        core.db.table("errores").insert(fila).execute()
        _avisar(origen, mensaje, fila["ruta"])
        return True
    except Exception as e:
        # Último recurso: al log del server, que en PythonAnywhere sí se puede
        # leer. Nunca relanzar desde acá.
        core.app.logger.error("no se pudo registrar el error (%s): %s | original: %s", origen, e, mensaje)
        return False


def _demasiados_reportes(ip):
    ahora = time.time()
    recientes = [ts for ts in _reportes.get(ip, []) if ahora - ts < _VENTANA_SEGUNDOS]
    _reportes[ip] = recientes
    if len(recientes) >= _MAX_REPORTES:
        return True
    recientes.append(ahora)
    return False


@bp.route("/api/montor/errores", methods=["POST"])
def reportar():
    """Lo llama el frontend cuando una pantalla se rompe.

    Deliberadamente sin login_required: los errores que más importan son los
    de alguien que todavía no entró (landing, registro, login). El user_id se
    toma de la sesión si existe, nunca del cuerpo del pedido — si no,
    cualquiera podría atribuirle errores a otra cuenta.
    """
    if _demasiados_reportes(request.remote_addr or "?"):
        # 202: para el frontend es un caso normal, no algo que reintentar.
        return jsonify({"ok": True, "guardado": False}), 202

    datos = request.get_json(silent=True) or {}
    guardado = registrar(
        origen="frontend",
        mensaje=datos.get("mensaje"),
        stack=datos.get("stack"),
        ruta=datos.get("ruta"),
        user_id=session.get("user_id"),
        user_agent=request.headers.get("User-Agent"),
    )
    return jsonify({"ok": True, "guardado": guardado}), 202
