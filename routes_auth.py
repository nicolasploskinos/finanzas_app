"""Login y registro."""
from datetime import datetime, timedelta, timezone
from flask import Blueprint, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

import montor_server as core

bp = Blueprint("auth", __name__)


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

    session.permanent = True
    session["user_id"]  = user["id"]
    session["username"] = user["username"]
    return jsonify({"ok": True}), 201
