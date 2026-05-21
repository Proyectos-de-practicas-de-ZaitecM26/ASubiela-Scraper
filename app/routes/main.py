from datetime import datetime

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from flask_login import current_user

from sqlalchemy import func, or_

from ..auth_utils import require_role

from ..data import (
    AuditLog,
    Favorita,
    Oposicion,
    User,
    Visita,
    VisitaGlobal,
    sa_db
)

from ..scraping.boe_scraper import (
    scrape_boe_ultimos_dias,
    sync_boe_hasta_hoy,
)



main_bp = Blueprint("main", __name__)


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

    today = datetime.today()

    hoy = today.strftime("%Y%m%d")

    fecha_mostrar = today.strftime("%d/%m/%Y")

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

    orden = request.args.get(
        "orden",
        "fecha_desc"
    )

    page = int(
        request.args.get("page", 1)
    )

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

    query = query.order_by(
        Oposicion.fecha.asc()
        if orden == "fecha_asc"
        else Oposicion.fecha.desc()
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

#@main_bp.route("/admin/scrape_ultimos_30")
#@require_role("admin")
#def admin_scrape_ultimos_30():

    nuevas = scrape_boe_ultimos_dias(30)

    flash(
        f"Se han insertado {len(nuevas)} oposiciones nuevas.",
        "success"
    )

    return redirect(
        url_for("user.oposiciones_vigentes")
    )

# =====================================================
# ADMIN SYNC
# =====================================================

#@main_bp.route("/admin/sync_boe")
#@require_role("admin")
#def admin_sync_boe():

    nuevas = sync_boe_hasta_hoy()

    flash(
        f"Sincronización completada. "
        f"Insertadas {len(nuevas)} oposiciones nuevas.",
        "success",
    )

    return redirect(
        url_for("user.oposiciones_vigentes")
    )
