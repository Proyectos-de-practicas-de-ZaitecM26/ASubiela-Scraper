import os
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import current_user, login_required
from ..db import get_boe_db, get_users_db
from ..services.chatbot import chatbot
from .. import limiter
from ..data import sa_db, Oposicion, User, Visita, Favorita
from sqlalchemy import or_, func
from ..scraping.boe_scraper import (
    scrape_boe_ultimos_dias,
    sync_boe_hasta_hoy,
)

main_bp = Blueprint("main", __name__)


@main_bp.route("/api/chatbot", methods=["POST"])
@limiter.limit("20 per minute")
def chatbot_api():
    """Endpoint de chat que usa Groq en backend para no exponer la API key en cliente."""
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get("message") or "").strip()

    if not user_message:
        return jsonify({"ok": False, "error": "Mensaje vacío."}), 400

    if len(user_message) > 1200:
        return jsonify({"ok": False, "error": "Mensaje demasiado largo (máx. 1200 caracteres)."}), 400

    try:
        answer = chatbot(user_message)
        return jsonify({"ok": True, "answer": answer})
    except ValueError as exc:
        current_app.logger.exception("Error en /api/chatbot: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500
    except Exception as exc:
        current_app.logger.exception("Error en /api/chatbot: %s", exc)
        return jsonify({"ok": False, "error": "No se pudo generar respuesta en este momento."}), 500


@main_bp.route("/")
def index():
    try:
        # Sincronizar la BBDD con los días faltantes hasta hoy.
        # Si la tabla está vacía, `sync_boe_hasta_hoy` bajará hasta 30 días atrás.
        sync_boe_hasta_hoy(max_dias_inicial=30, max_dias_guardados=30)
    except Exception as e:
        current_app.logger.error(f"Error al actualizar datos: {e}")
    
    hoy = datetime.today().strftime("%Y%m%d")
    fecha_mostrar = datetime.today().strftime("%d/%m/%Y")
   
    opos = Oposicion.query.filter_by(fecha=hoy)\
        .order_by(Oposicion.fecha.desc())\
        .limit(4).all()
    
    provincias_rows = sa_db.session.query(Oposicion.provincia).distinct()\
        .filter(Oposicion.provincia.isnot(None))\
        .order_by(Oposicion.provincia).all()
 
    provincias = [p[0] for p in provincias_rows]
    
    return render_template(
        "index.html", 
        oposiciones=opos, 
        fecha_hoy=fecha_mostrar, 
        provincias=provincias
    )

@main_bp.route("/resultados")
def resultados():

    busqueda = request.args.get("busqueda", "")
    provincia = request.args.get("provincia", "")
    orden = request.args.get("orden", "fecha_desc")
    page = int(request.args.get("page", 1))
    por_pagina = 10
    
    query = Oposicion.query
    
    # Filtro de búsqueda (opcional)
    if busqueda:
        like_str = f"%{busqueda}%"
        query = query.filter(or_(
            Oposicion.titulo.like(like_str),
            Oposicion.identificador.like(like_str),
            Oposicion.control.like(like_str),
            Oposicion.departamento.like(like_str)
        ))

    # Filtro por provincia (opcional)
    if provincia:
        query = query.filter(Oposicion.provincia == provincia)
        
    # Orden + paginación
    if orden == "fecha_asc":
        query = query.order_by(Oposicion.fecha.asc())
    else:
        query = query.order_by(Oposicion.fecha.desc())
    
    pagination = query.paginate(page=page, per_page=por_pagina, error_out=False)
    rows = pagination.items
    total = pagination.total

    # Provincias disponibles
    provincias = [p[0] 
        for p in sa_db.session.query(Oposicion.provincia).distinct().filter(Oposicion.provincia.isnot(None)).all()]

    # Visitadas / Favoritas
    visitadas_ids = []
    favoritas_ids = []

    if current_user.is_authenticated:
        # Gracias a backref='user', podemos acceder directo:
        visitadas_ids = [v.oposicion_id for v in current_user.visitas]
        favoritas_ids = [f.oposicion_id for f in current_user.favoritas]

    return render_template(
        "resultados.html",
        rows=rows,
        page=page,
        total_pages=pagination.pages,
        provincias=provincias,
        busqueda=busqueda,
        provincia_filtro=provincia,
        orden=orden,
        visitadas=visitadas_ids,
        favoritas=favoritas_ids,
        total=total
    )


@main_bp.route("/admin/scrape_ultimos_30")
@login_required
def admin_scrape_ultimos_30():
    nuevas = scrape_boe_ultimos_dias(30)
    flash(
        f"Se han insertado {len(nuevas)} oposiciones nuevas de los últimos 30 días.", "success")
    return redirect(url_for("user.oposiciones_vigentes"))



@main_bp.route("/estadisticas")
def estadisticas():
    # Hacemos un JOIN entre Visitas y Oposiciones y agrupamos por departamento
    stats_query = sa_db.session.query(
        Oposicion.departamento,
        func.count(Visita.id).label('total_visitas')
    ).join(Visita, Visita.oposicion_id == Oposicion.id)\
     .group_by(Oposicion.departamento)\
     .order_by(sa_db.desc('total_visitas')).all()

    if not stats_query:
        return render_template("estadisticas.html", stats=[], labels=[], values=[])

    labels = [s.departamento for s in stats_query]
    values = [s.total_visitas for s in stats_query]
    
    # Convertimos a diccionario para mantener compatibilidad con tu template
    stats = [{"departamento": s.departamento, "total_visitas": s.total_visitas} for s in stats_query]

    return render_template("estadisticas.html", stats=stats, labels=labels, values=values)


@main_bp.route("/politica-cookies")
def politica_cookies():
    return render_template("politica_cookies.html")


@main_bp.route("/politica-privacidad")
def politica_privacidad():
    return render_template("politica_privacidad.html")


@main_bp.route("/aviso-legal")
def aviso_legal():
    return render_template("aviso_legal.html")


@main_bp.route("/admin/sync_boe")
@login_required
def admin_sync_boe():
    """
    Sincroniza la BBDD del BOE SOLO con los días que falten hasta hoy.
    Usa sync_boe_hasta_hoy y luego redirige a las oposiciones vigentes.
    """
    nuevas = sync_boe_hasta_hoy()  # por defecto, si está vacía baja hasta 30 días atrás
    flash(
        f"Sincronización completada. Insertadas {len(nuevas)} oposiciones nuevas.",
        "success",
    )
    return redirect(url_for("user.oposiciones_vigentes"))
