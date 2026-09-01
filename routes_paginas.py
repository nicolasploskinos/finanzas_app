"""Páginas HTML (no-API): landing, dashboard, login, PWA."""
from datetime import datetime, timezone
from flask import Blueprint, render_template, session, redirect, send_from_directory

import montor_server as core

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


@bp.route("/montor")
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
    return render_template("montor.html", username=session["username"], is_pro=is_pro, is_trial=is_trial,
                            trial_dias=trial_dias, whatsapp_habilitado=whatsapp_habilitado)


@bp.route("/montor/viajes")
@core.login_required
def viajes_page():
    return render_template("viajes.html", username=session["username"], is_pro=core._es_pro(session["user_id"]))


@bp.route("/montor/analisis")
@core.login_required
def analisis_page():
    return render_template("analisis.html", username=session["username"], is_pro=core._es_pro(session["user_id"]))


@bp.route("/montor/login")
def login_page():
    if "user_id" in session:
        return redirect("/montor")
    return render_template("auth.html")


@bp.route("/montor/logout")
def logout():
    session.clear()
    return redirect("/montor/login")


@bp.route("/montor/manifest.json")
def manifest():
    return send_from_directory("static", "montor_manifest.json", mimetype="application/manifest+json")


@bp.route("/montor/sw.js")
def sw():
    return send_from_directory("static", "montor_sw.js", mimetype="application/javascript")
