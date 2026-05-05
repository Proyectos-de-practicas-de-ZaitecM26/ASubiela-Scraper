import os
from flask import Flask, session, request, redirect, url_for
from flask_login import current_user
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView


from .config import Config
from .data import sa_db, User
from .data import inicializar_y_migrar

from datetime import datetime, date, timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .extensions import mail, login_manager

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
)

from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.chat import chat_bp

def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"

    # Config
    app.config.from_object(Config)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True, 
        SESSION_COOKIE_SAMESITE='Lax',
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30)
    )

    # Extensiones
    mail.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    login_manager.login_view = "auth.login"

    # 🔥 FIX IMPORTANTE: user_loader de Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(chat_bp)
    
    # Initialize the db extension
    sa_db.init_app(app)

    # DB init
    with app.app_context():
        inicializar_y_migrar()

    #admin
    admin = Admin(name="Admin") 
    admin.init_app(app)
    admin.add_view(ModelView(User, sa_db.session, name="Usuarios", endpoint="admin_users"))
    print(app.url_map)

    # =========================
    # THEME
    # =========================
    @app.before_request
    def ensure_theme():
        if "theme" not in session:
            session["theme"] = "light"

    @app.route("/toggle_theme")
    def toggle_theme():
        current = session.get("theme", "light")
        session["theme"] = "dark" if current == "light" else "light"
        return redirect(request.referrer or url_for("main.index"))

    @app.context_processor
    def inject_theme():
        return {"theme": session.get("theme", "light")}

    @app.context_processor
    def inject_user():
        return {"user": current_user}
    
    # ==== Filtros Jinja ====

    @app.template_filter("format_date")
    def format_date_filter(date_str):
        if not date_str or len(date_str) != 8 or not date_str.isdigit():
            return date_str
        try:
            year = date_str[0:4]
            month = date_str[4:6]
            day = date_str[6:8]
            return f"{day}/{month}/{year}"
        except Exception:
            return date_str

    @app.template_filter("es_reciente")
    def es_reciente(fecha_str, dias=0):
        try:
            f = datetime.strptime(fecha_str, "%Y%m%d").date()
            return (date.today() - f).days <= dias
        except Exception:
            return False

    @app.template_filter("resaltar_titulo")
    def resaltar_titulo(titulo):
        """Resalta palabras clave importantes en el título de las oposiciones"""
        import re

        if not titulo:
            return titulo

        # Palabras clave a resaltar
        palabras_clave = [
            r"\bconvocatoria\b",
            r"\boposiciones?\b",
            r"\bplazas?\b",
            r"\bacceso\b",
            r"\bproceso selectivo\b",
            r"\bfuncionarios?\b",
            r"\bcuerpo\b",
            r"\bescala\b",
            r"\bgrupo [A-C][12]?\b",
            r"\bturnos?\b",
            r"\blibre\b",
            r"\bpromoci[oó]n interna\b",
            r"\bdiscapacidad\b",
            r"\breserva\b",
            r"\bnombramientos?\b",
            r"\bceses?\b",
            r"\bampliac[ió]n\b",
            r"\bmodificac[ió]n\b",
            r"\banulaci[oó]n\b",
            r"\bcorrecc[ió]n\b",
            r"\bpresentac[ió]n\b",
            r"\badmisi[oó]n\b",
            r"\bexclusi[oó]n\b",
            r"\blista[s]?\b",
            r"\bsolicitantes?\b",
            r"\badmitidos?\b",
            r"\bexcluidos?\b",
            r"\btribunal\b",
            r"\bcalificac[ió]n\b",
            r"\bpruebas?\b",
            r"\bejercicio[s]?\b",
            r"\bexamen\b",
            r"\bresultados?\b",
            r"\bpuntuac[ió]n\b",
            r"\badjudicac[ió]n\b",
            r"\bdestinos?\b",
            r"\btraslados?\b",
            r"\bayuntamiento?\b"
        ]

        # Reemplazar cada palabra clave con versión en negrita
        resultado = titulo
        for patron in palabras_clave:
            resultado = re.sub(
                patron,
                lambda m: f'<strong>{m.group()}</strong>',
                resultado,
                flags=re.IGNORECASE,
            )

        return resultado


    return app