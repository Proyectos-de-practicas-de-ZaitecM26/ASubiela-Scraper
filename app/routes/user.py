import os
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from app.email_utils import send_new_oposiciones_email
from datetime import datetime, timedelta

from ..data import (
    sa_db,
    Visita,
    VisitaGlobal,
    Favorita,
    Oposicion,
    Suscripcion,
    AuditLog
)

from flask_login import login_required, current_user

from ..audit_utils import log_audit

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
)

user_bp = Blueprint("user", __name__)


# =====================================================
# FUNCIONES AUXILIARES
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

        print(f"Error al registrar visita global: {e}")


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

        else:

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

        print(f"Error al gestionar favorito: {e}")

        return False


# =====================================================
# RUTAS
# =====================================================

@user_bp.route("/user", methods=["GET", "POST"])
@login_required
def user_home():

    return render_template("user.html")


# =====================================================
# TRACKING VISITAS + AUDITORÍA
# =====================================================

@user_bp.route("/marcar_visitada/<int:oposicion_id>", methods=["POST"])
def marcar_visitada(oposicion_id):

    oposicion = Oposicion.query.get(oposicion_id)

    if current_user.is_authenticated:

        registrar_visita(current_user.id, oposicion_id)

        log_audit(
            user_id=current_user.id,
            action="CLICK_OPOSICION",
            audit_metadata={
                "oposicion_id": oposicion_id,
                "titulo": oposicion.titulo if oposicion else "Desconocido"
            }
        )

    else:

        registrar_visita_global(oposicion_id)

        log_audit(
            user_id=None,
            action="CLICK_OPOSICION_ANONIMO",
            audit_metadata={
                "oposicion_id": oposicion_id,
                "titulo": oposicion.titulo if oposicion else "Desconocido"
            }
        )

    return jsonify({"ok": True})