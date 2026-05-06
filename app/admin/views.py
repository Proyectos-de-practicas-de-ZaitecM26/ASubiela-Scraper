from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.actions import action
from flask import redirect, url_for, abort, flash, request
from flask_login import current_user
from sqlalchemy import func
from markupsafe import Markup

from ..data import sa_db, User, Oposicion, Favorita, Visita, Suscripcion


# =========================
# 🔐 SEGURIDAD ADMIN
# =========================

class SecureAdminIndexView(AdminIndexView):

    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, "role", None) == "admin"

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        abort(403)

    @expose('/')
    def index(self):
        stats = {
            'usuarios':      sa_db.session.query(User).count(),
            'oposiciones':   sa_db.session.query(Oposicion).count(),
            'favoritas':     sa_db.session.query(Favorita).count(),
            'visitas':       sa_db.session.query(Visita).count(),
            'suscripciones': sa_db.session.query(Suscripcion).count(),
        }

        ultimos_usuarios = (
            sa_db.session.query(User)
            .order_by(User.id.desc())
            .limit(5)
            .all()
        )

        ultimas_oposiciones = (
            sa_db.session.query(Oposicion)
            .order_by(Oposicion.id.desc())
            .limit(5)
            .all()
        )

        return self.render(
            'admin/index.html',
            stats=stats,
            ultimos_usuarios=ultimos_usuarios,
            ultimas_oposiciones=ultimas_oposiciones,
        )


# =========================
# 📦 BASE SEGURA CON CSV
# =========================

class SecureModelView(ModelView):
    """
    ModelView base con:
    - Control de acceso por rol admin
    - Exportación a CSV habilitada
    - Acción masiva de eliminación con confirmación
    """

    # ── Exportación CSV ────────────────────────────────────────────────
    can_export = True   
    export_types = ['csv']     

    def __init__(self, model, session, **kwargs):
        super().__init__(model, session, **kwargs)
        # Flask-Admin 2.x requires explicit initialization for bulk actions
        self.init_actions()

    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, "role", None) == "admin"

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        abort(403)

    # ── Acción masiva: eliminar seleccionados ──────────────────────────
    @action(
        'eliminar_seleccionados',
        'Eliminar seleccionados',
        '¿Seguro que quieres eliminar los registros seleccionados? Esta acción no se puede deshacer.'
    )
    def action_eliminar_seleccionados(self, ids):
        try:
            count = 0
            for record_id in ids:
                obj = self.model.query.get(record_id)
                if obj:
                    sa_db.session.delete(obj)
                    count += 1
            sa_db.session.commit()
            flash(f'{count} registro(s) eliminado(s) correctamente.', 'success')
        except Exception as e:
            sa_db.session.rollback()
            flash(f'Error al eliminar: {str(e)}', 'error')


# =========================
# 👤 USERS ADMIN
# =========================

class UserModelView(SecureModelView):

    # `foto_perfil` se renderiza como botón (sin "-") al final
    column_list = ['id', 'email', 'role', 'name', 'apellidos', 'foto_perfil']

    column_labels = {
        'id': 'ID',
        'email': 'Correo',
        'role': 'Rol',
        'name': 'Nombre',
        'apellidos': 'Apellidos',
        'foto_perfil': 'Imagen de perfil',
    }

    form_columns = ['email', 'role', 'name', 'apellidos', 'telefono', 'nivel_estudios', 'titulacion', 'foto_perfil']

    column_searchable_list = ['email', 'name', 'apellidos']

    column_filters = ['role']

    column_default_sort = ('id', True)

    column_exclude_list = ['password_hash']

    def _foto_perfil_button(self, context, model, name):
        src = getattr(model, "foto_perfil", None)
        if not src:
            return Markup("Sin imagen")

        modal_id = f"fotoPerfilModal_{getattr(model, 'id', '')}"
        remove_url = self.get_url(".remove_profile_image")
        return_url = request.url
        return Markup(
            f'<div style="display:flex;align-items:center;gap:12px;">'
            f'  <img src="{src}" alt="foto_perfil" '
            f'       style="width:64px;height:64px;object-fit:cover;border-radius:10px;" />'
            f'  <div style="display:flex;flex-direction:column;gap:8px;">'
            f'    <button type="button" class="btn btn-sm btn-primary" '
            f'            data-bs-toggle="modal" data-bs-target="#{modal_id}">'
            f'      Moderar Imagen de perfil'
            f'    </button>'
            f'    <form method="post" action="{remove_url}" style="margin:0;">'
            f'      <input type="hidden" name="id" value="{getattr(model, "id", "")}" />'
            f'      <input type="hidden" name="url" value="{return_url}" />'
            f'      <button type="submit" class="btn btn-sm btn-danger">Eliminar imagen</button>'
            f'    </form>'
            f'  </div>'
            f'</div>'
            f'<div class="modal fade" id="{modal_id}" tabindex="-1" aria-hidden="true">'
            f'  <div class="modal-dialog modal-dialog-centered">'
            f'    <div class="modal-content">'
            f'      <div class="modal-header">'
            f'        <h5 class="modal-title">Imagen de perfil</h5>'
            f'        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>'
            f'      </div>'
            f'      <div class="modal-body" style="text-align:center;">'
            f'        <img src="{src}" alt="foto_perfil" style="max-width:100%;height:auto;border-radius:10px;" />'
            f'      </div>'
            f'    </div>'
            f'  </div>'
            f'</div>'
        )

    column_formatters = {
        "foto_perfil": _foto_perfil_button,
    }

    @expose("/remove_profile_image", methods=("POST",))
    def remove_profile_image(self):
        user_id = request.form.get("id")
        return_url = request.form.get("url") or self.get_url(".index_view")

        try:
            user = User.query.get(user_id)
            if not user:
                flash("Usuario no encontrado.", "error")
                return redirect(return_url)

            user.foto_perfil = None

            if hasattr(user, "admin_notes"):
                note = "Imagen eliminada por el admin por contenido ofensivo."
                existing = getattr(user, "admin_notes", "") or ""
                user.admin_notes = existing + (("\n" if existing else "") + note)

            sa_db.session.commit()
            flash("Imagen eliminada correctamente.", "success")
        except Exception as e:
            sa_db.session.rollback()
            flash(f"Error al eliminar la imagen: {str(e)}", "error")

        return redirect(return_url)

    @action(
        "moderar_imagen",
        "Moderar Imagen",
        "¿Seguro que quieres eliminar la imagen de perfil de los usuarios seleccionados?",
    )
    def action_moderar_imagen(self, ids):
        try:
            count = 0
            for record_id in ids:
                user = User.query.get(record_id)
                if not user:
                    continue

                user.foto_perfil = None

                # Optional: only applies if you later add this column to the model
                if hasattr(user, "admin_notes"):
                    note = "Imagen eliminada por el admin por contenido ofensivo."
                    existing = getattr(user, "admin_notes", "") or ""
                    user.admin_notes = existing + (("\n" if existing else "") + note)

                count += 1

            sa_db.session.commit()
            flash(f"Imagen eliminada correctamente en {count} usuario(s).", "success")
        except Exception as e:
            sa_db.session.rollback()
            flash(f"Error al moderar imágenes: {str(e)}", "error")

    # Acción masiva adicional específica para usuarios: cambiar rol a viewer
    @action(
        'degradar_a_viewer',
        'Cambiar rol a Viewer',
        '¿Seguro que quieres cambiar el rol de los usuarios seleccionados a "viewer"?'
    )
    def action_degradar_a_viewer(self, ids):
        try:
            count = 0
            for record_id in ids:
                user = User.query.get(record_id)
                if user and user.role != 'admin':
                    user.role = 'viewer'
                    count += 1
            sa_db.session.commit()
            flash(f'Rol actualizado a "viewer" en {count} usuario(s).', 'success')
        except Exception as e:
            sa_db.session.rollback()
            flash(f'Error al actualizar roles: {str(e)}', 'error')

    def on_model_change(self, form, model, is_created):
        if model.role not in User.ROLES:
            raise ValueError("Rol inválido")

    def scaffold_form(self):
        form_class = super().scaffold_form()
        if hasattr(self.model, "admin_notes") and "admin_notes" not in self.form_columns:
            self.form_columns = list(self.form_columns) + ["admin_notes"]
        return form_class


# =========================
# 📊 ANALYTICS
# =========================

class AnalyticsView(BaseView):

    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, "role", None) == "admin"

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        abort(403)

    @expose('/')
    def index(self):
        dept_stats = sa_db.session.query(
            Oposicion.departamento,
            func.count(Oposicion.id)
        ).group_by(Oposicion.departamento).order_by(func.count(Oposicion.id).desc()).limit(7).all()

        estudios_stats = sa_db.session.query(
            User.nivel_estudios,
            func.count(User.id)
        ).filter(User.nivel_estudios.isnot(None)).group_by(User.nivel_estudios).all()

        top_visitadas = sa_db.session.query(
            Oposicion.titulo,
            func.count(Visita.id).label('total')
        ).join(Visita).group_by(Oposicion.id).order_by(func.count(Visita.id).desc()).limit(5).all()

        return self.render(
            'admin/analytics.html',
            dept_stats=dept_stats,
            estudios_stats=estudios_stats,
            top_visitadas=top_visitadas
        )


# =========================
# ⚙️ INIT ADMIN
# =========================

def init_admin(app):
    admin = Admin(
        app,
        name="Panel Admin",
        index_view=SecureAdminIndexView()
    )

    # 📊 Analíticas
    admin.add_view(
        AnalyticsView(
            name="Analíticas",
            endpoint="analytics",
        )
    )

    # 👤 Usuarios
    admin.add_view(
        UserModelView(
            User,
            sa_db.session,
            name="Usuarios",
            endpoint="admin_users"
        )
    )

    # 📄 Oposiciones
    admin.add_view(
        SecureModelView(
            Oposicion,
            sa_db.session,
            name="Oposiciones",
            endpoint="admin_oposiciones"
        )
    )

    # ⭐ Favoritas
    admin.add_view(
        SecureModelView(
            Favorita,
            sa_db.session,
            name="Favoritas",
            endpoint="admin_favoritas"
        )
    )

    # 👀 Visitas
    admin.add_view(
        SecureModelView(
            Visita,
            sa_db.session,
            name="Visitas",
            endpoint="admin_visitas"
        )
    )

    # 🔔 Suscripciones
    admin.add_view(
        SecureModelView(
            Suscripcion,
            sa_db.session,
            name="Suscripciones",
            endpoint="admin_suscripciones"
        )
    )

    return admin