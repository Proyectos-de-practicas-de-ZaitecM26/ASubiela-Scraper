from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, abort
from flask_login import current_user

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


class SecureModelView(ModelView):

    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, "role", None) == "admin"

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        abort(403)


# =========================
# 👤 USERS ADMIN
# =========================

class UserModelView(SecureModelView):

    column_list = ['id', 'email', 'role', 'name', 'apellidos']

    column_labels = {
        'id': 'ID',
        'email': 'Correo',
        'role': 'Rol',
        'name': 'Nombre',
        'apellidos': 'Apellidos'
    }

    form_columns = ['email', 'role', 'name', 'apellidos', 'telefono', 'nivel_estudios', 'titulacion']

    column_searchable_list = ['email', 'name', 'apellidos']

    column_filters = ['role']

    column_default_sort = ('id', True)

    column_exclude_list = ['password_hash']

    def on_model_change(self, form, model, is_created):
        if model.role not in User.ROLES:
            raise ValueError("Rol inválido")


# =========================
# ⚙️ INIT ADMIN
# =========================

def init_admin(app):
    admin = Admin(
        app,
        name="Panel Admin",
        index_view=SecureAdminIndexView()
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