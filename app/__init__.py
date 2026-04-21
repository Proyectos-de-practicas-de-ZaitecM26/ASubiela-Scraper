import os
from flask import Flask, session, request, redirect, url_for
from flask_login import current_user

from .config import Config
from .db import init_boe_db, init_users_db, migrate_users_db, teardown_appcontext

from datetime import timedelta
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

from app.models import User


def create_app():
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )

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
        return User.get(user_id)

    # Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(chat_bp)

    # DB init
    with app.app_context():
        init_boe_db()
        init_users_db()
        migrate_users_db()

    app.teardown_appcontext(teardown_appcontext)

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

    return app