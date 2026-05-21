import os
from flask import Flask
from datetime import timedelta
from .config import Config
from .data import sa_db, inicializar_y_migrar
from .extensions import mail, login_manager, limiter
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.chat import chat_bp
from app.routes.filters import filters_bp
from app.routes.policies import policies_bp
from app.routes.admin import init_admin
from app.routes.user import user_bp, register_login_handlers
from .audit_utils import register_audit_signals

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
    limiter.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)
    sa_db.init_app(app)
    
    register_login_handlers()
    register_audit_signals(app)
    

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(filters_bp)
    app.register_blueprint(policies_bp)

    with app.app_context():
        inicializar_y_migrar()

    
    init_admin(app)

    return app