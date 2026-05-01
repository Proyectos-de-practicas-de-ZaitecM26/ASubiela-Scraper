from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, abort
from flask_login import current_user

from ..data import sa_db, User


class SecureAdminIndexView(AdminIndexView):
    """Protect the admin index page"""
    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, 'role', None) == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        abort(403)


class SecureModelView(ModelView):
    """Protect individual model views"""
    def is_accessible(self):
        return current_user.is_authenticated and getattr(current_user, 'role', None) == 'admin'

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        abort(403)


def init_admin(app):
    admin = Admin(app, name='Admin', template_mode='bootstrap4', index_view=SecureAdminIndexView())
    admin.add_view(SecureModelView(User, sa_db.session, name='Usuarios', endpoint='admin_users'))
    return admin
