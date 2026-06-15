import os
import stripe
from flask import Flask
from datetime import timedelta
from .config import Config
from .data import sa_db, User
from .extensions import mail, login_manager, limiter
from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.user import user_bp
from app.routes.chat import chat_bp
from app.routes.payments import payments_bp
from app.routes.stripe_pay import stripe_pay_bp
from app.routes.filters import filters_bp
from app.routes.policies import policies_bp
from app.routes.theme import theme_bp
from app.routes.admin import init_admin_dashboard
from app.routes.user import user_bp, register_login_handlers
from .audit_utils import register_audit_signals
from werkzeug.security import generate_password_hash

def create_default_admin(app):
    app.logger.info("Verificando existencia de admin por defecto...")
    email = app.config.get("DEFAULT_ADMIN_EMAIL")
    password = app.config.get("DEFAULT_ADMIN_PASSWORD")

    if not email or not password:
        raise ValueError("No se han definido las variables de entorno para el admin por defecto (DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD)")
    
    name = app.config.get("DEFAULT_ADMIN_NAME", email.split("@")[0])
    email = email.lower().strip()
    user = User.query.filter_by(email=email).first()
    if not user:
        app.logger.info(f"Creando default admin: {email}")
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            name=name,
            role='admin',
            is_verified=True
        )
        sa_db.session.add(user)
        sa_db.session.commit()
        app.logger.info("Admin por defecto creado exitosamente")
    else:
        app.logger.info("Admin por defecto ya existe")
    app.logger.info("Verificacion de admin por defecto completada")
    

def create_app(config_overrides=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
    )
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
    
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(filters_bp)
    app.register_blueprint(policies_bp)
    app.register_blueprint(theme_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(stripe_pay_bp)

    with app.app_context():
        create_default_admin(app)

    
    init_admin_dashboard(app)

    return app