"""Suscripción Pro vía MercadoPago."""
import os
from flask import Blueprint, jsonify, redirect, request, session

import montor_server as core

bp = Blueprint("pagos", __name__)


def _cancelar_preapproval(preapproval_id):
    """Cancela una preaprobación existente en MercadoPago. Se usa antes de
    crear una nueva (ej: el usuario cambia de método de pago desde su
    perfil) para no dejarlo con dos suscripciones activas en paralelo."""
    if not preapproval_id:
        return
    mp_token = os.environ.get("MP_ACCESS_TOKEN", "")
    try:
        core.req.put(
            f"https://api.mercadopago.com/preapproval/{preapproval_id}",
            headers={"Authorization": f"Bearer {mp_token}"},
            json={"status": "cancelled"},
        )
    except Exception:
        pass


@bp.route("/api/montor/suscribir")
@core.login_required
def suscribir():
    mp_token = os.environ.get("MP_ACCESS_TOKEN", "")
    base_url = os.environ.get("BASE_URL") or request.host_url.rstrip("/")
    ciclo = request.args.get("ciclo") if request.args.get("ciclo") in core._PLANES_PRO else "mensual"
    plan = core._PLANES_PRO[ciclo]

    # Si ya tenía una suscripción (ej: está cambiando el método de pago), se
    # cancela la vieja antes de armar la nueva para no cobrarle dos veces.
    res = core.db.table("usuarios").select("mp_preapproval_id").eq("id", session["user_id"]).execute()
    if res.data:
        _cancelar_preapproval(res.data[0].get("mp_preapproval_id"))

    r = core.req.post(
        "https://api.mercadopago.com/preapproval",
        headers={"Authorization": f"Bearer {mp_token}"},
        json={
            "reason": plan["etiqueta"],
            "external_reference": session["user_id"],
            "payer_email": f"{session['username']}@montor.local",
            "auto_recurring": {
                "frequency": plan["frequency"],
                "frequency_type": "months",
                "transaction_amount": plan["monto"],
                "currency_id": "ARS",
            },
            "back_url": f"{base_url}/montor",
            "notification_url": f"{base_url}/api/montor/webhook/mercadopago",
        }
    )
    data = r.json()
    init_point = data.get("init_point")
    if not init_point:
        return jsonify({"error": "No se pudo crear la suscripción", "detalle": data}), 500

    if data.get("id"):
        core.db.table("usuarios").update({
            "mp_preapproval_id": data["id"],
            "plan_ciclo": ciclo,
        }).eq("id", session["user_id"]).execute()

    return redirect(init_point)


@bp.route("/api/montor/webhook/mercadopago", methods=["POST"])
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
        user_id = preapproval.get("external_reference")
        estado = preapproval.get("status")

        if estado == "authorized" and user_id:
            proximo_pago = preapproval.get("next_payment_date") or preapproval.get("auto_recurring", {}).get("next_payment_date")
            actualizacion = {"plan": "pro"}
            if proximo_pago:
                actualizacion["mp_proximo_pago"] = proximo_pago
            core.db.table("usuarios").update(actualizacion).eq("id", user_id).execute()
        elif estado in ("cancelled", "paused") and user_id:
            # La preaprobación puede cancelarse desde afuera de la app (el
            # propio panel de MercadoPago, una tarjeta rechazada, etc.) — si
            # coincide con la que tenemos guardada, se refleja acá. Si el
            # usuario ya armó una preaprobación nueva (cambio de método de
            # pago) esto no la pisa, porque compara el id.
            res = core.db.table("usuarios").select("mp_preapproval_id").eq("id", user_id).execute()
            if res.data and res.data[0].get("mp_preapproval_id") == resource_id:
                core.db.table("usuarios").update({"plan": "free"}).eq("id", user_id).execute()

    return jsonify({"ok": True})
