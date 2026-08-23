"""Vinculación y webhook del bot de WhatsApp."""
import hashlib
import hmac
import os
import random
import re
import time
from urllib.parse import quote
from flask import Blueprint, jsonify, request, session

import finanzas_server as core

bp = Blueprint("whatsapp", __name__)


@bp.route("/api/finanzas/whatsapp/codigo", methods=["POST"])
@core.login_required
def whatsapp_codigo():
    if session["user_id"] != core._WHATSAPP_USER_ID:
        return jsonify({"ok": False, "error": "whatsapp_no_disponible"}), 403
    codigo = f"{random.randint(0, 999999):06d}"
    core._wa_codigos[codigo] = (session["user_id"], time.time() + 900)
    numero = re.sub(r"[^0-9]", "", os.environ.get("WHATSAPP_DISPLAY_NUMBER", ""))
    wa_link = f"https://wa.me/{numero}?text={quote(f'VINCULAR {codigo}')}"
    return jsonify({"ok": True, "codigo": codigo, "wa_link": wa_link})


@bp.route("/api/finanzas/whatsapp/estado")
@core.login_required
def whatsapp_estado():
    res = core.db.table("whatsapp_users").select("telefono").eq("user_id", session["user_id"]).execute()
    if res.data:
        tel = res.data[0]["telefono"]
        return jsonify({"vinculado": True, "telefono_oculto": "•••• " + tel[-4:]})
    return jsonify({"vinculado": False})


@bp.route("/api/finanzas/whatsapp/desvincular", methods=["DELETE"])
@core.login_required
def whatsapp_desvincular():
    core.db.table("whatsapp_users").delete().eq("user_id", session["user_id"]).execute()
    return jsonify({"ok": True})


@bp.route("/api/finanzas/whatsapp/webhook", methods=["GET"])
def whatsapp_webhook_verificar():
    modo = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge", "")
    if modo == "subscribe" and token and token == os.environ.get("WHATSAPP_VERIFY_TOKEN"):
        return challenge, 200
    return "Forbidden", 403


@bp.route("/api/finanzas/whatsapp/webhook", methods=["POST"])
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
                    core._procesar_mensaje_whatsapp(msg)
    except Exception:
        pass
    return jsonify({"ok": True})
