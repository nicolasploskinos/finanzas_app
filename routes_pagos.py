"""Suscripción Pro vía MercadoPago."""
import os
from flask import Blueprint, jsonify, redirect, request, session

import finanzas_server as core

bp = Blueprint("pagos", __name__)


@bp.route("/api/finanzas/suscribir")
@core.login_required
def suscribir():
    mp_token = os.environ.get("MP_ACCESS_TOKEN", "")
    base_url = os.environ.get("BASE_URL") or request.host_url.rstrip("/")
    plan = core._PLANES_PRO.get(request.args.get("ciclo"), core._PLANES_PRO["mensual"])
    r = core.req.post(
        "https://api.mercadopago.com/preapproval",
        headers={"Authorization": f"Bearer {mp_token}"},
        json={
            "reason": plan["etiqueta"],
            "external_reference": session["user_id"],
            "payer_email": f"{session['username']}@finanzas.local",
            "auto_recurring": {
                "frequency": plan["frequency"],
                "frequency_type": "months",
                "transaction_amount": plan["monto"],
                "currency_id": "ARS",
            },
            "back_url": f"{base_url}/finanzas",
            "notification_url": f"{base_url}/api/finanzas/webhook/mercadopago",
        }
    )
    data = r.json()
    init_point = data.get("init_point")
    if not init_point:
        return jsonify({"error": "No se pudo crear la suscripción", "detalle": data}), 500
    return redirect(init_point)


@bp.route("/api/finanzas/webhook/mercadopago", methods=["POST"])
def webhook_mp():
    data = request.get_json(silent=True) or {}
    topic = data.get("type") or request.args.get("topic", "")
    resource_id = data.get("data", {}).get("id") or request.args.get("id", "")

    if topic in ("subscription_preapproval", "preapproval") and resource_id:
        mp_token = os.environ.get("MP_ACCESS_TOKEN", "")
        r = core.req.get(
            f"https://api.mercadopago.com/preapproval/{resource_id}",
            headers={"Authorization": f"Bearer {mp_token}"}
        )
        preapproval = r.json()
        if preapproval.get("status") == "authorized":
            user_id = preapproval.get("external_reference")
            if user_id:
                core.db.table("usuarios").update({"plan": "pro"}).eq("id", user_id).execute()

    return jsonify({"ok": True})
