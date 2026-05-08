from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_admin.contrib.sqla.view import tools, sql_cast, Unicode, or_
from flask_admin.actions import action
from flask import redirect, url_for, abort, flash, request
from flask_login import current_user
from sqlalchemy import func
import unicodedata
from datetime import datetime
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

    column_list = ['id', 'email', 'role', 'name', 'apellidos', 'is_active']

    column_labels = {
        'id': 'ID',
        'email': 'Correo',
        'role': 'Rol',
        'name': 'Nombre',
        'apellidos': 'Apellidos',
        'is_active': 'Usuario Activo'
    }
    
    column_formatters = {
        'is_active': lambda v, c, m, p: 'Sí' if m.is_active else 'No'
    }

    form_columns = ['email', 'role', 'name', 'apellidos', 'telefono', 'nivel_estudios', 'titulacion']

    column_searchable_list = ['email', 'name', 'apellidos']

    column_filters = ['role']

    column_default_sort = ('id', True)

    column_exclude_list = ['password_hash']
    
    column_extra_row_actions = [
        LinkRowAction('fa fa-lock', '/admin/admin_users/block/?id={row_id}', 'Bloquear/Desbloquear')
    ]
    
    @expose('/block/')
    def action_toggle_active(self):
        user_id = request.args.get('id')
        if user_id:
            # Buscamos el objeto en la DB
            user = sa_db.session.query(User).get(user_id)
            
            if user:
                # Cambiamos el atributo 'is_active' (el interruptor)
                # Si es True pasa a False, si es False pasa a True
                user.is_active = not user.is_active
                
                # GUARDAR CAMBIOS: Importante para que no se pierdan
                sa_db.session.commit()
                
                # Feedback visual
                estado = "activado" if user.is_active else "bloqueado"
                flash(f"Usuario {user.email} ha sido {estado}.", "success")
            else:
                flash("Usuario no encontrado.", "error")
        
        # REDIRECCIÓN: Esto evita que te quedes en la URL /block/
        # .index_view es el nombre interno de la lista de Flask-Admin
        return redirect(url_for('.index_view'))

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


# =========================
# 📄 OPOSICIONES ADMIN
# =========================

class OposicionModelView(SecureModelView):
    list_template = 'admin/oposiciones_list.html'

    # Mostrar 10 resultados por página por defecto
    page_size = 10
    can_set_page_size = False
    page_size_options = [10, 25, 50]

    column_list = ['id', 'fecha', 'departamento', 'provincia', 'identificador', 'titulo']

    column_labels = {
        'id': 'ID',
        'fecha': 'Fecha',
        'departamento': 'Departamento',
        'provincia': 'Provincia',
        'identificador': 'Identificador',
        'titulo': 'Título',
    }

    column_filters = []
    column_searchable_list = ['titulo', 'identificador', 'departamento', 'provincia']
    column_default_sort = ('fecha', True)
    action_disallowed_list = ['delete', 'eliminar_seleccionados']

    @staticmethod
    def _normalize_text(value):
        if not value:
            return ""
        normalized = unicodedata.normalize("NFD", value)
        without_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return without_accents.lower().strip()

    @staticmethod
    def _normalize_sql_expr(column):
        expr = func.lower(sql_cast(column, Unicode))
        for src, dst in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ü", "u"), ("ñ", "n")):
            expr = func.replace(expr, src, dst)
        return expr

    def _apply_search(self, query, count_query, joins, count_joins, search):
        terms = search.split(" ")

        for term in terms:
            normalized_term = self._normalize_text(term)
            if not normalized_term:
                continue

            stmt = tools.parse_like_term(normalized_term)

            filter_stmt = []
            count_filter_stmt = []

            for field, path in self._search_fields:
                query, joins, alias = self._apply_path_joins(query, joins, path, inner_join=False)

                count_alias = None
                if count_query is not None:
                    count_query, count_joins, count_alias = self._apply_path_joins(
                        count_query, count_joins, path, inner_join=False
                    )

                column = field if alias is None else getattr(alias, field.key)
                normalized_column = self._normalize_sql_expr(column)
                filter_stmt.append(normalized_column.ilike(stmt))

                if count_query is not None:
                    column = field if count_alias is None else getattr(count_alias, field.key)
                    normalized_count_column = self._normalize_sql_expr(column)
                    count_filter_stmt.append(normalized_count_column.ilike(stmt))

            query = query.filter(or_(*filter_stmt))

            if count_query is not None:
                count_query = count_query.filter(or_(*count_filter_stmt))

        return query, count_query, joins, count_joins

    @expose('/guardar_favorita/<int:oposicion_id>', methods=('POST',))
    def guardar_favorita(self, oposicion_id):
        if not self.is_accessible():
            return self.inaccessible_callback('guardar_favorita')

        existente = Favorita.query.filter_by(
            user_id=current_user.id,
            oposicion_id=oposicion_id,
        ).first()

        if existente:
            flash('La oposición ya estaba en favoritos.', 'info')
            return redirect(request.referrer or self.get_url('.index_view'))

        favorita = Favorita(
            user_id=current_user.id,
            oposicion_id=oposicion_id,
            fecha_favorito=datetime.now().isoformat(),
        )
        sa_db.session.add(favorita)
        sa_db.session.commit()
        flash('Oposición guardada en favoritos.', 'success')

        return redirect(request.referrer or self.get_url('.index_view'))


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
        OposicionModelView(
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
