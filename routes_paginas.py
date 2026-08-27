"""Páginas HTML (no-API): landing, dashboard, login, PWA."""
from datetime import datetime, timezone
from flask import Blueprint, render_template, session, redirect, send_from_directory

import finanzas_server as core

bp = Blueprint("paginas", __name__)


@bp.route("/")
def landing():
    return render_template("landing.html")


@bp.route("/privacidad")
def privacidad():
    return render_template("privacidad.html")


@bp.route("/terminos")
def terminos():
    return render_template("terminos.html")


@bp.route("/finanzas")
@core.login_required
def index():
    user = core.db.table("usuarios").select("plan,trial_expira").eq("id", session["user_id"]).execute().data
    is_pro = False
    is_trial = False
    trial_dias = 0
    if user:
        plan = user[0].get("plan")
        trial_expira = user[0].get("trial_expira")
        if plan == "pro":
            is_pro = True
        elif plan == "trial" and trial_expira:
            expira = datetime.fromisoformat(trial_expira.replace("Z", "+00:00"))
            if expira > datetime.now(timezone.utc):
                is_pro = True
                is_trial = True
                trial_dias = max(1, (expira - datetime.now(timezone.utc)).days + 1)
    whatsapp_habilitado = session["user_id"] == core._WHATSAPP_USER_ID
    return render_template("finanzas.html", username=session["username"], is_pro=is_pro, is_trial=is_trial,
                            trial_dias=trial_dias, whatsapp_habilitado=whatsapp_habilitado)


@bp.route("/finanzas/viajes")
@core.login_required
def viajes_page():
    return render_template("viajes.html", username=session["username"], is_pro=core._es_pro(session["user_id"]))


@bp.route("/finanzas/login")
def login_page():
    if "user_id" in session:
        return redirect("/finanzas")
    return render_template("auth.html")


@bp.route("/finanzas/logout")
def logout():
    session.clear()
    return redirect("/finanzas/login")


@bp.route("/finanzas/manifest.json")
def manifest():
    return send_from_directory("static", "finanzas_manifest.json", mimetype="application/manifest+json")


@bp.route("/finanzas/sw.js")
def sw():
    return send_from_directory("static", "finanzas_sw.js", mimetype="application/javascript")
