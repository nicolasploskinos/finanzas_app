"""Perfil de usuario: cambiar nombre y contraseña, ver el estado de la
suscripción Pro (ciclo, próximo pago) y cancelarla."""
import os
from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

import montor_server as core

bp = Blueprint("cuenta", __name__)


@bp.route("/api/montor/cuenta", methods=["GET"])
@core.login_required
def cuenta():
    user_id = session["user_id"]
    res = core.db.table("usuarios").select(
        "username,plan,trial_expira,plan_ciclo,mp_preapproval_id,mp_proximo_pago"
    ).eq("id", user_id).execute()
    if not res.data:
        return jsonify({"error": "not_found"}), 404

    u = res.data[0]
    estado = core._estado_plan(user_id)

    suscripcion = None
    if u.get("plan") == "pro" and u.get("mp_preapproval_id"):
        suscripcion = {
            "ciclo": u.get("plan_ciclo"),
            "proximo_pago": u.get("mp_proximo_pago"),
        }

    return jsonify({
        "username": u["username"],
        "is_pro": estado["is_pro"],
        "is_trial": estado["is_trial"],
        "trial_dias": estado["trial_dias"],
        "trial_expira": u.get("trial_expira"),
        "suscripcion": suscripcion,
    })


@bp.route("/api/montor/cuenta/nombre", methods=["PUT"])
@core.login_required
def cambiar_nombre():
    data = request.get_json(silent=True) or {}
    nuevo = (data.get("username") or "").strip()
    if len(nuevo) < 3:
        return jsonify({"ok": False, "error": "too_short"}), 400

    user_id = session["user_id"]
    existe = core.db.table("usuarios").select("id").eq("username", nuevo).execute().data
    if any(fila["id"] != user_id for fila in existe):
        return jsonify({"ok": False, "error": "username_taken"}), 400

    core.db.table("usuarios").update({"username": nuevo}).eq("id", user_id).execute()
    session["username"] = nuevo
    return jsonify({"ok": True, "username": nuevo})


@bp.route("/api/montor/cuenta/password", methods=["PUT"])
@core.login_required
def cambiar_password():
    data = request.get_json(silent=True) or {}
    actual = data.get("actual") or ""
    nueva = data.get("nueva") or ""
    if len(nueva) < 8:
        return jsonify({"ok": False, "error": "weak_password"}), 400

    user_id = session["user_id"]
    res = core.db.table("usuarios").select("password_hash").eq("id", user_id).execute()
    if not res.data or not check_password_hash(res.data[0]["password_hash"], actual):
        return jsonify({"ok": False, "error": "wrong_password"}), 400

    core.db.table("usuarios").update({"password_hash": generate_password_hash(nueva)}).eq("id", user_id).execute()
    return jsonify({"ok": True})


@bp.route("/api/montor/cuenta/cancelar-suscripcion", methods=["POST"])
@core.login_required
def cancelar_suscripcion():
    user_id = session["user_id"]
    res = core.db.table("usuarios").select("mp_preapproval_id").eq("id", user_id).execute()
    preapproval_id = res.data[0].get("mp_preapproval_id") if res.data else None

    if preapproval_id:
        mp_token = os.environ.get("MP_ACCESS_TOKEN", "")
        try:
            core.req.put(
                f"https://api.mercadopago.com/preapproval/{preapproval_id}",
                headers={"Authorization": f"Bearer {mp_token}"},
                json={"status": "cancelled"},
            )
        except Exception:
            pass

    core.db.table("usuarios").update({"plan": "free", "mp_preapproval_id": None}).eq("id", user_id).execute()
    return jsonify({"ok": True})
