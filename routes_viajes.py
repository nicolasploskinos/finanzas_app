"""Viajes: seguimiento de gastos por viaje, convertidos a ARS/USD/EUR."""
from flask import Blueprint, jsonify, request, session

import finanzas_server as core

bp = Blueprint("viajes", __name__)


@bp.route("/api/finanzas/viajes", methods=["GET"])
@core.login_required
def listar_viajes():
    if not core._es_pro(session["user_id"]):
        return jsonify({"error": "pro_requerido"}), 403
    viajes = (
        core.db.table("viajes").select("*").eq("user_id", session["user_id"])
        .order("fecha_inicio", desc=True).execute().data
    )
    ids = [v["id"] for v in viajes]
    gastos = {}
    if ids:
        cotiz = core._obtener_cotizaciones()
        txs = (
            core.db.table("transacciones").select("viaje_id,tipo,monto,moneda")
            .eq("user_id", session["user_id"]).in_("viaje_id", ids).execute().data
        )
        for t in txs:
            if t["tipo"] != "Gasto":
                continue
            vid = t["viaje_id"]
            origen = t.get("moneda") or "ARS"
            monto = float(t["monto"])
            gastos.setdefault(vid, {"ARS": 0.0, "USD": 0.0, "EUR": 0.0})
            for destino in ("ARS", "USD", "EUR"):
                conv = core._convertir_moneda(monto, origen, destino, cotiz)
                if conv is not None:
                    gastos[vid][destino] += conv
    for v in viajes:
        v["gastado"] = gastos.get(v["id"], {"ARS": 0.0, "USD": 0.0, "EUR": 0.0})
    return jsonify(viajes)


@bp.route("/api/finanzas/viajes", methods=["POST"])
@core.login_required
def crear_viaje():
    if not core._es_pro(session["user_id"]):
        return jsonify({"ok": False, "error": "pro_requerido"}), 403
    d = request.get_json()
    payload = core._payload_viaje(d)
    if not payload["nombre"] or not payload["fecha_inicio"] or not payload["fecha_fin"]:
        return jsonify({"ok": False, "error": "missing_trip_fields"}), 400
    payload["user_id"] = session["user_id"]
    res = core.db.table("viajes").insert(payload).execute()
    return jsonify(res.data[0]), 201


@bp.route("/api/finanzas/viajes/<int:vid>", methods=["PUT"])
@core.login_required
def editar_viaje(vid):
    if not core._es_pro(session["user_id"]):
        return jsonify({"ok": False, "error": "pro_requerido"}), 403
    d = request.get_json()
    payload = core._payload_viaje(d)
    if not payload["nombre"] or not payload["fecha_inicio"] or not payload["fecha_fin"]:
        return jsonify({"ok": False, "error": "missing_trip_fields"}), 400
    res = core.db.table("viajes").update(payload).eq("id", vid).eq("user_id", session["user_id"]).execute()
    if not res.data:
        return jsonify({"ok": False, "error": "no encontrado"}), 404
    return jsonify(res.data[0])


@bp.route("/api/finanzas/viajes/<int:vid>", methods=["DELETE"])
@core.login_required
def eliminar_viaje(vid):
    core.db.table("viajes").delete().eq("id", vid).eq("user_id", session["user_id"]).execute()
    return jsonify({"ok": True})


@bp.route("/api/finanzas/viajes/<int:vid>", methods=["GET"])
@core.login_required
def detalle_viaje(vid):
    if not core._es_pro(session["user_id"]):
        return jsonify({"error": "pro_requerido"}), 403
    viaje = core.db.table("viajes").select("*").eq("id", vid).eq("user_id", session["user_id"]).execute().data
    if not viaje:
        return jsonify({"error": "no encontrado"}), 404
    viaje = viaje[0]

    txs = (
        core.db.table("transacciones").select("*")
        .eq("user_id", session["user_id"]).eq("viaje_id", vid)
        .order("fecha").execute().data
    )

    cotiz = core._obtener_cotizaciones()
    totales = {"ARS": 0.0, "USD": 0.0, "EUR": 0.0}
    por_cat = {"ARS": {}, "USD": {}, "EUR": {}}
    for t in txs:
        origen = t.get("moneda") or "ARS"
        monto = float(t["monto"])
        t["monto_usd"] = core._convertir_moneda(monto, origen, "USD", cotiz)
        if t["tipo"] != "Gasto":
            continue
        cat = (t.get("categoria") or "").strip() or "Sin categoría"
        for destino in ("ARS", "USD", "EUR"):
            conv = core._convertir_moneda(monto, origen, destino, cotiz)
            if conv is None:
                continue
            totales[destino] += conv
            por_cat[destino][cat] = por_cat[destino].get(cat, 0.0) + conv

    por_cat_lista = {
        m: sorted([{"nombre": c, "total": v} for c, v in cats.items()], key=lambda x: -x["total"])
        for m, cats in por_cat.items()
    }

    return jsonify({
        "viaje": viaje, "transacciones": txs, "totales": totales,
        "por_categoria": por_cat_lista,
    })
