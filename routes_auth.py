"""Login y registro."""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

import montor_server as core

bp = Blueprint("auth", __name__)


def sembrar_ejemplos(user_id):
    """Le deja a la cuenta nueva tres movimientos de ejemplo.

    Sin esto, lo primero que ve alguien que se acaba de registrar es una
    pantalla vacía que dice "Sin movimientos" — justo en el momento en que
    decide si la app le sirve o no. Con datos adentro se entiende de un
    vistazo qué hace: el consolidado, una categoría, y sobre todo el gasto en
    dólares, que es el diferencial del producto.

    Van marcados con es_ejemplo para poder ofrecerle borrarlos todos juntos
    (ver DELETE /api/montor/ejemplos) y para que no le consuman el cupo del
    plan gratis. Falla en silencio a propósito: que no se pueda sembrar el
    ejemplo no es motivo para tirarle abajo el registro a un usuario nuevo.
    """
    hoy = core._hoy_ar()
    cotiz = core._obtener_cotizaciones()
    ejemplos = [
        {"tipo": "Ingreso", "monto": 950000.0, "categoria": "Sueldo",
         "moneda": "ARS", "fecha": hoy.replace(day=1).isoformat()},
        {"tipo": "Gasto", "monto": 45800.0, "categoria": "Supermercado",
         "moneda": "ARS", "fecha": hoy.isoformat()},
        {"tipo": "Gasto", "monto": 12.0, "categoria": "Suscripciones",
         "moneda": "USD", "fecha": hoy.isoformat()},
    ]
    filas = [{
        **e,
        "descripcion": "Ejemplo — borralo cuando quieras",
        "user_id": user_id,
        "viaje_id": None,
        "es_ejemplo": True,
        "cotizacion_usd": cotiz.get("USD"),
        "cotizacion_eur": cotiz.get("EUR"),
    } for e in ejemplos]

    try:
        core.db.table("transacciones").insert(filas).execute()
    except Exception as e:
        core.app.logger.warning("no se pudieron sembrar los ejemplos de %s: %s", user_id, e)


@bp.route("/api/montor/login", methods=["POST"])
def login():
    data     = request.get_json()
    username = (data.get("username") or "").strip()
    password =  data.get("password") or ""

    if core._login_bloqueado(username):
        return jsonify({"ok": False, "error": "too_many_attempts"}), 429

    res = core.db.table("usuarios").select("*").eq("username", username).execute()
    if not res.data or not check_password_hash(res.data[0]["password_hash"], password):
        core._registrar_intento_fallido(username)
        return jsonify({"ok": False, "error": "invalid_credentials"}), 401

    user = res.data[0]
    session.permanent = True
    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    core._login_intentos.pop(username, None)
    return jsonify({"ok": True})


@bp.route("/api/montor/register", methods=["POST"])
def register():
    data     = request.get_json()
    username = (data.get("username") or "").strip()
    password =  data.get("password") or ""

    if not username or not password:
        return jsonify({"ok": False, "error": "missing_fields"}), 400

    if len(password) < 8:
        return jsonify({"ok": False, "error": "weak_password"}), 400

    if core.db.table("usuarios").select("id").eq("username", username).execute().data:
        return jsonify({"ok": False, "error": "username_taken"}), 400

    res = core.db.table("usuarios").insert({
        "username":      username,
        "password_hash": generate_password_hash(password),
        "verificado":    True,
        "plan":          "trial",
        "trial_expira":  (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
    }).execute()

    user = res.data[0]
    sembrar_ejemplos(user["id"])

    session.permanent = True
    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    return jsonify({"ok": True}), 201
