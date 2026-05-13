import os

RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "cambia-esto-en-produccion")
    # Configuracion SQLAlchemy    
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///boe_scraper.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "static/uploads/")

    # Flask-Mail (idealmente todo por variables de entorno)
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.getenv(
        "MAIL_USERNAME", "notificaciones.scraper@gmail.com")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "sqoj zfue ovcf dlhz")
    MAIL_DEFAULT_SENDER = MAIL_USERNAME