"""Páginas HTML (no-API): landing, dashboard, login, PWA."""
import os
from flask import Blueprint, render_template, session, redirect, send_from_directory

import montor_server as core

bp = Blueprint("paginas", __name__)


def _spa_version():
    """mtime del bundle, para invalidar la cache del navegador en cada deploy.
    El build se commitea (PythonAnywhere no corre Node), así que el archivo
    siempre está en disco; si falta, devolvemos algo que no cachee."""
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "app", "montor.js")
    try:
        return str(int(os.path.getmtime(ruta)))
    except OSError:
        return "dev"


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
    plan = core._estado_plan(session["user_id"])
    is_pro, is_trial, trial_dias = plan["is_pro"], plan["is_trial"], plan["trial_dias"]
    whatsapp_habilitado = session["user_id"] == core._WHATSAPP_USER_ID
    return render_template("montor.html", username=session["username"], is_pro=is_pro, is_trial=is_trial,
                            trial_dias=trial_dias, whatsapp_habilitado=whatsapp_habilitado)


@bp.route("/montor/viajes")
@core.login_required
def viajes_page():
    # Migrada a React (ver templates/spa.html y frontend/).
    return render_template("spa.html", titulo="Viajes", v=_spa_version())


@bp.route("/montor/analisis")
@core.login_required
def analisis_page():
    # Migrada a React. El resto de las páginas sigue en Jinja; los datos
    # (usuario, plan, transacciones) los pide el propio frontend por la API.
    return render_template("spa.html", titulo="Análisis", v=_spa_version())


@bp.route("/montor/login")
def login_page():
    if "user_id" in session:
        return redirect("/montor")
    # Migrada a React (ver templates/spa.html y frontend/).
    return render_template("spa.html", titulo="Ingresar", v=_spa_version())


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
