import os

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    flash,
    redirect,
    url_for,
    request,
    jsonify,
    current_app,
    session
)

from flask_login import current_user, login_required

from sqlalchemy import or_, func

from ..auth_utils import require_role

from ..services.chatbot import chatbot

from app.extensions import limiter

from ..data import (
    sa_db,
    Oposicion,
    User,
    Visita,
    VisitaGlobal,
    Favorita,
    AuditLog
)

from ..scraping.boe_scraper import (
    scrape_boe_ultimos_dias,
    sync_boe_hasta_hoy,
)

main_bp = Blueprint("main", __name__)


# =====================================================
# CHATBOT API
# =====================================================

@main_bp.route("/api/chatbot", methods=["POST"])
@limiter.limit("20 per minute")
def chatbot_api():

    payload = request.get_json(silent=True) or {}

    user_message = (payload.get("message") or "").strip()

    if not user_message:

        return jsonify({
            "ok": False,
            "error": "Mensaje vacío."
        }), 400

    if len(user_message) > 1200:

        return jsonify({
            "ok": False,
            "error": "Mensaje demasiado largo."
        }), 400

    try:

        answer = chatbot(user_message)

        return jsonify({
            "ok": True,
            "answer": answer
        })

    except ValueError as exc:

        current_app.logger.exception(
            "Error en /api/chatbot: %s",
            exc
        )

        return jsonify({
            "ok": False,
            "error": str(exc)
        }), 500

    except Exception as exc:

        current_app.logger.exception(
            "Error en /api/chatbot: %s",
            exc
        )

        return jsonify({
            "ok": False,
            "error": "No se pudo generar respuesta."
        }), 500


# =====================================================
# INDEX
# =====================================================

@main_bp.route("/")
def index():

    try:

        sync_boe_hasta_hoy(
            max_dias_inicial=30,
            max_dias_guardados=30
        )

    except Exception as e:

        current_app.logger.error(
            f"Error al actualizar datos: {e}"
        )

    hoy = datetime.today().strftime("%Y%m%d")

    fecha_mostrar = datetime.today().strftime("%d/%m/%Y")

    opos = Oposicion.query.filter_by(
        fecha=hoy
    ).order_by(
        Oposicion.fecha.desc()
    ).limit(4).all()

    provincias_rows = sa_db.session.query(
        Oposicion.provincia
    ).distinct().filter(
        Oposicion.provincia.isnot(None)
    ).order_by(
        Oposicion.provincia
    ).all()

    provincias = [p[0] for p in provincias_rows]

    return render_template(
        "index.html",
        oposiciones=opos,
        fecha_hoy=fecha_mostrar,
        provincias=provincias
    )


# =====================================================
# RESULTADOS
# =====================================================

@main_bp.route("/resultados")
def resultados():

    busqueda = request.args.get("busqueda", "")

    provincia = request.args.get("provincia", "")

    orden = request.args.get("orden", "fecha_desc")

    page = int(request.args.get("page", 1))

    por_pagina = 10

    query = Oposicion.query

    if busqueda:

        like_str = f"%{busqueda}%"

        query = query.filter(or_(
            Oposicion.titulo.like(like_str),
            Oposicion.identificador.like(like_str),
            Oposicion.control.like(like_str),
            Oposicion.departamento.like(like_str)
        ))

    if provincia:

        query = query.filter(
            Oposicion.provincia == provincia
        )

    if orden == "fecha_asc":

        query = query.order_by(
            Oposicion.fecha.asc()
        )

    else:

        query = query.order_by(
            Oposicion.fecha.desc()
        )

    pagination = query.paginate(
        page=page,
        per_page=por_pagina,
        error_out=False
    )

    rows = pagination.items

    total = pagination.total

    provincias = [
        p[0]
        for p in sa_db.session.query(
            Oposicion.provincia
        ).distinct().filter(
            Oposicion.provincia.isnot(None)
        ).all()
    ]

    visitadas_ids = []

    favoritas_ids = []

    if current_user.is_authenticated:

        visitadas_ids = [
            v.oposicion_id
            for v in current_user.visitas
        ]

        favoritas_ids = [
            f.oposicion_id
            for f in current_user.favoritas
        ]

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


# =====================================================
# ADMIN SCRAPING
# =====================================================

@main_bp.route("/admin/scrape_ultimos_30")
@require_role('admin')
def admin_scrape_ultimos_30():

    nuevas = scrape_boe_ultimos_dias(30)

    flash(
        f"Se han insertado {len(nuevas)} oposiciones nuevas.",
        "success"
    )

    return redirect(
        url_for("user.oposiciones_vigentes")
    )


# =====================================================
# ESTADÍSTICAS
# =====================================================

@main_bp.route("/estadisticas")
def estadisticas():

    visitas_autenticadas = sa_db.session.query(
        Oposicion.departamento,
        func.count(Visita.id).label('total_visitas')
    ).join(
        Visita,
        Visita.oposicion_id == Oposicion.id
    ).group_by(
        Oposicion.departamento
    ).order_by(
        sa_db.desc('total_visitas')
    ).all()

    visitas_anonimas = sa_db.session.query(
        Oposicion.departamento,
        func.sum(VisitaGlobal.total_visitas).label('total_visitas')
    ).join(
        VisitaGlobal,
        VisitaGlobal.oposicion_id == Oposicion.id
    ).group_by(
        Oposicion.departamento
    ).all()

    total_autenticadas = sum(
        (fila.total_visitas or 0)
        for fila in visitas_autenticadas
    )

    total_anonimas = sum(
        (fila.total_visitas or 0)
        for fila in visitas_anonimas
    )

    acumulado_por_departamento = {}

    for fila in visitas_autenticadas:

        if not fila.departamento:
            continue

        acumulado_por_departamento[fila.departamento] = (
            acumulado_por_departamento.get(
                fila.departamento,
                0
            ) + (fila.total_visitas or 0)
        )

    for fila in visitas_anonimas:

        if not fila.departamento:
            continue

        acumulado_por_departamento[fila.departamento] = (
            acumulado_por_departamento.get(
                fila.departamento,
                0
            ) + (fila.total_visitas or 0)
        )

    stats = [
        {
            "departamento": dep,
            "total_visitas": total
        }
        for dep, total in sorted(
            acumulado_por_departamento.items(),
            key=lambda item: item[1],
            reverse=True
        )
    ]

    labels = [
        fila["departamento"]
        for fila in stats
    ]

    values = [
        fila["total_visitas"]
        for fila in stats
    ]

    # 🔥 NUEVO: AUDITORÍA
    logs = AuditLog.query.order_by(
        AuditLog.timestamp.desc()
    ).limit(100).all()

    return render_template(
        "estadisticas.html",
        stats=stats,
        labels=labels,
        values=values,
        total_autenticadas=total_autenticadas,
        total_anonimas=total_anonimas,
        logs=logs
    )


# =====================================================
# PÁGINAS LEGALES
# =====================================================

@main_bp.route("/politica-cookies")
def politica_cookies():

    return render_template("politica_cookies.html")


@main_bp.route("/politica-privacidad")
def politica_privacidad():

    return render_template("politica_privacidad.html")


@main_bp.route("/aviso-legal")
def aviso_legal():

    return render_template("aviso_legal.html")


# =====================================================
# ADMIN SYNC
# =====================================================

@main_bp.route("/admin/sync_boe")
@require_role('admin')
def admin_sync_boe():

    nuevas = sync_boe_hasta_hoy()

    flash(
        f"Sincronización completada. Insertadas {len(nuevas)} oposiciones nuevas.",
        "success",
    )

    return redirect(
        url_for("user.oposiciones_vigentes")
    )


# =====================================================
# THEME
# =====================================================

@main_bp.route('/toggle-theme')
def toggle_theme():

    current_theme = session.get('theme', 'dark')

    session['theme'] = (
        'light'
        if current_theme == 'dark'
        else 'dark'
    )

    session.modified = True

    return redirect(
        request.referrer or url_for('main.index')
    )