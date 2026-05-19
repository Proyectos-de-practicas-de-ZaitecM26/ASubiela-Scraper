import os
from flask import Flask, session, request, redirect, url_for
from flask_login import current_user, user_logged_in, user_logged_out
from datetime import datetime, date, timedelta
from .config import Config
from .data import sa_db, User, inicializar_y_migrar
from .extensions import mail, login_manager, limiter
from .audit_utils import log_audit
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.chat import chat_bp
from app.routes.admin import init_admin


def create_app(config_overrides=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite3"
    app.config.from_object(Config)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    )

    if config_overrides:
        app.config.update(config_overrides)

    mail.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    login_manager.login_view = "auth.login"

    sa_db.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


    @user_logged_in.connect_via(app)
    def log_login(sender, user, **extra):
        log_audit(
            user_id=user.id,
            action='login',
            audit_metadata={'email': user.email}
        )

    @user_logged_out.connect_via(app)
    def log_logout(sender, user, **extra):
        log_audit(
            user_id=user.id,
            action='logout',
            audit_metadata={'email': user.email}
        )

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(chat_bp)

    with app.app_context():
        inicializar_y_migrar()

    # Admin
    init_admin(app)
    print(app.url_map)

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
            return f"{date_str[6:8]}/{date_str[4:6]}/{date_str[0:4]}"
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
        import re

        if not titulo:
            return titulo

        palabras_clave = [
            r"\bconvocatoria\b", r"\boposiciones?\b", r"\bplazas?\b",
            r"\bacceso\b", r"\bproceso selectivo\b", r"\bfuncionarios?\b",
            r"\bcuerpo\b", r"\bescala\b", r"\bgrupo [A-C][12]?\b",
            r"\bturnos?\b", r"\blibre\b", r"\bpromoci[oó]n interna\b",
            r"\bdiscapacidad\b", r"\breserva\b", r"\bnombramientos?\b",
            r"\bceses?\b", r"\bampliac[ió]n\b", r"\bmodificac[ió]n\b",
            r"\banulaci[oó]n\b", r"\bcorrecc[ió]n\b", r"\bpresentac[ió]n\b",
            r"\badmisi[oó]n\b", r"\bexclusi[oó]n\b", r"\blista[s]?\b",
            r"\bsolicitantes?\b", r"\badmitidos?\b", r"\bexcluidos?\b",
            r"\btribunal\b", r"\bcalificac[ió]n\b", r"\bpruebas?\b",
            r"\bejercicio[s]?\b", r"\bexamen\b", r"\bresultados?\b",
            r"\bpuntuac[ió]n\b", r"\badjudicac[ió]n\b", r"\bdestinos?\b",
            r"\btraslados?\b", r"\bayuntamiento?\b"
        ]

        resultado = titulo
        for patron in palabras_clave:
            resultado = re.sub(
                patron,
                lambda m: f"<strong>{m.group()}</strong>",
                resultado,
                flags=re.IGNORECASE,
            )

        return resultado

    return app