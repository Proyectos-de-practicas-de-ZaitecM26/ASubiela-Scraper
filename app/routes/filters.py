import re
from flask import Blueprint, session, request, redirect, url_for
from flask_login import current_user
from datetime import datetime, date


filters_bp = Blueprint("filters", __name__)

PALABRAS_CLAVE = [
    r"convocatoria", r"oposiciones?", r"plazas?",
    r"acceso", r"proceso selectivo", r"funcionarios?",
    r"cuerpo", r"escala", r"grupo [A-C][12]?",
    r"turnos?", r"libre", r"promoci[oó]n interna",
    r"discapacidad", r"reserva", r"nombramientos?",
    r"ceses?", r"ampliac[ió]n", r"modificac[ió]n",
    r"anulaci[oó]n", r"correcc[ió]n", r"presentac[ió]n",
    r"admisi[oó]n", r"exclusi[oó]n", r"lista[s]?",
    r"solicitantes?", r"admitidos?", r"excluidos?",
    r"tribunal", r"calificac[ió]n", r"pruebas?",
    r"ejercicio[s]?", r"examen", r"resultados?",
    r"puntuac[ió]n", r"adjudicac[ió]n", r"destinos?",
    r"traslados?", r"ayuntamiento?"
]

PALABRAS_CLAVE_REGEX = rf"\b({'|'.join(PALABRAS_CLAVE)})\b"
PATRON_RESALTADO = re.compile(PALABRAS_CLAVE_REGEX, flags=re.IGNORECASE)

@filters_bp.before_app_request
def ensure_theme():
    if "theme" not in session:
        session["theme"] = "light"

@filters_bp.app_context_processor
def inject_theme():
    return {"theme": session.get("theme", "light")}

@filters_bp.app_context_processor
def inject_user():
    return {"user": current_user}

@filters_bp.app_template_filter("format_date")
def format_date_filter(date_str):
    if not date_str or len(date_str) != 8 or not date_str.isdigit():
        return date_str
    try:
        return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
    except Exception:
        return date_str

@filters_bp.app_template_filter("es_reciente")
def es_reciente(fecha_str, dias=0):
    try:
        f = datetime.strptime(fecha_str, "%Y%m%d").date()
        return (date.today() - f).days <= dias
    except Exception:
        return False

@filters_bp.app_template_filter("resaltar_titulo")
def resaltar_titulo(titulo):
    if not titulo:
        return titulo

    return PATRON_RESALTADO.sub(r"<strong>\1</strong>", titulo)
