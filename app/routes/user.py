from datetime import datetime, timedelta

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import (
    current_user,
    login_required
)

from sqlalchemy import or_

from app.email_utils import (
    send_new_oposiciones_email
)

from app.file_utils import (
    upload_profile_photo
)

from ..audit_utils import log_audit

from ..data import (
    AuditLog,
    Favorita,
    Oposicion,
    Suscripcion,
    User,
    Visita,
    VisitaGlobal,
    sa_db
)

from ..extensions import login_manager


user_bp = Blueprint("user", __name__)


# =====================================================
# LOGIN MANAGER
# =====================================================

def register_login_handlers():

    @login_manager.user_loader
    def load_user(user_id):

        return sa_db.session.get(
            User,
            int(user_id)
        )


# =====================================================
# VISITAS
# =====================================================

def registrar_visita(user_id, oposicion_id):

    visita = Visita.query.filter_by(
        user_id=user_id,
        oposicion_id=oposicion_id
    ).first()

    fecha_actual = datetime.utcnow().isoformat()

    if visita:

        visita.fecha_visita = fecha_actual

    else:

        visita = Visita(
            user_id=user_id,
            oposicion_id=oposicion_id,
            fecha_visita=fecha_actual
        )

        sa_db.session.add(visita)

    try:

        sa_db.session.commit()

    except Exception as e:

        sa_db.session.rollback()

        print(f"Error al registrar visita: {e}")


def registrar_visita_global(oposicion_id):

    fecha = datetime.utcnow().isoformat()

    try:

        visita = VisitaGlobal.query.filter_by(
            oposicion_id=oposicion_id
        ).first()

        if visita:

            visita.total_visitas += 1

            visita.fecha_ultima_visita = fecha

        else:

            sa_db.session.add(
                VisitaGlobal(
                    oposicion_id=oposicion_id,
                    total_visitas=1,
                    fecha_ultima_visita=fecha,
                )
            )

        sa_db.session.commit()

    except Exception as e:

        sa_db.session.rollback()

        print(
            f"Error al registrar visita global: {e}"
        )


# =====================================================
# FAVORITOS
# =====================================================

def toggle_favorito(user_id, oposicion_id):

    favorito = Favorita.query.filter_by(
        user_id=user_id,
        oposicion_id=oposicion_id
    ).first()

    try:

        if favorito:

            sa_db.session.delete(favorito)

            sa_db.session.commit()

            return False

        nuevo_favorito = Favorita(
            user_id=user_id,
            oposicion_id=oposicion_id,
            fecha_favorito=datetime.utcnow().isoformat()
        )

        sa_db.session.add(nuevo_favorito)

        sa_db.session.commit()

        return True

    except Exception as e:

        sa_db.session.rollback()

        print(
            f"Error al gestionar favorito: {e}"
        )

        return False


# =====================================================
# USER HOME
# =====================================================

@user_bp.route("/user", methods=["GET", "POST"])
@login_required
def user_home():

    return render_template("user.html")


# =====================================================
# OPOSICIONES VIGENTES
# =====================================================

@user_bp.route("/user_oposiciones")
@login_required
def oposiciones_vigentes():

    user = current_user

    today = datetime.today()

    desde = (
        today - timedelta(days=30)
    ).strftime("%Y%m%d")

    page = request.args.get(
        "page",
        1,
        type=int
    )

    por_pagina = 10

    raw_departamentos = request.args.getlist(
        "departamentos"
    )

    selected_departamentos = [
        d for d in raw_departamentos
        if d.strip()
    ]

    busqueda = request.args.get(
        "busqueda",
        ""
    )

    provincia = request.args.get(
        "provincia",
        ""
    )

    fecha_desde = request.args.get(
        "fecha_desde",
        ""
    )

    fecha_hasta = request.args.get(
        "fecha_hasta",
        ""
    )

    orden = request.args.get(
        "orden",
        "fecha_desc"
    )

    query = Oposicion.query.filter(
        Oposicion.fecha >= desde
    )

    if selected_departamentos:

        query = query.filter(
            Oposicion.departamento.in_(
                selected_departamentos
            )
        )

    if busqueda:

        like_filter = f"%{busqueda}%"

        query = query.filter(or_(
            Oposicion.titulo.like(like_filter),
            Oposicion.identificador.like(like_filter),
            Oposicion.control.like(like_filter)
        ))

    if provincia:

        query = query.filter(
            Oposicion.provincia == provincia
        )

    if fecha_desde:

        query = query.filter(
            Oposicion.fecha >= fecha_desde.replace("-", "")
        )

    if fecha_hasta:

        query = query.filter(
            Oposicion.fecha <= fecha_hasta.replace("-", "")
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

    oposiciones = pagination.items

    total = pagination.total

    total_pages = pagination.pages

    departamentos_query = sa_db.session.query(
        Oposicion.departamento
    ).distinct().filter(
        Oposicion.fecha >= desde,
        Oposicion.departamento.isnot(None)
    ).order_by(
        Oposicion.departamento
    ).all()

    departamentos = [
        d[0]
        for d in departamentos_query
    ]

    provincias_query = sa_db.session.query(
        Oposicion.provincia
    ).distinct().filter(
        Oposicion.provincia.isnot(None)
    ).order_by(
        Oposicion.provincia
    ).all()

    provincias = [
        p[0]
        for p in provincias_query
    ]

    visitadas = [
        v.oposicion_id
        for v in user.visitas
    ]

    favoritas = [
        f.oposicion_id
        for f in user.favoritas
    ]

    return render_template(
        "user_oposiciones.html",
        departamentos=departamentos,
        selected_departamentos=selected_departamentos,
        oposiciones=oposiciones,
        provincias=provincias,
        busqueda=busqueda,
        provincia_filtro=provincia,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        orden=orden,
        page=page,
        total_pages=total_pages,
        visitadas=visitadas,
        favoritas=favoritas,
        hoy=today.strftime("%Y%m%d"),
        titulo_pagina=(
            f"📢 Oposiciones Vigentes "
            f"de {user.name} {user.apellidos}"
        ),
        total=total
    )