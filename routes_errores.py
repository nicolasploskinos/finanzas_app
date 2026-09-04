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
