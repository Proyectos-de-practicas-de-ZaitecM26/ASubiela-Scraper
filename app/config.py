import os


class Config:
    # =====================================================
    # DEFAULT ADMIN USER
    # =====================================================
    
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD")
    DEFAULT_ADMIN_NAME = os.getenv("DEFAULT_ADMIN_NAME")
    
    # =====================================================
    # AI PROVIDERS
    # =====================================================
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    DEFAULT_AI_PROVIDER = os.getenv(
        "DEFAULT_AI_PROVIDER", 
        "groq"
    )
    
    
     # =====================================================
    # STRIPE
    # =====================================================
    
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

    # =====================================================
    # EMAIL 
    # =====================================================
    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "cambia-esto-en-produccion"
    )

    # =====================================================
    # SQLALCHEMY
    # =====================================================

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "SQLALCHEMY_DATABASE_URI",
        "sqlite:///boe_scraper.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # =====================================================
    # UPLOADS
    # =====================================================

    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER",
        "static/uploads/"
    )

    # =====================================================
    # RECAPTCHA
    # =====================================================
    
    RECAPTCHA_ENABLED = os.getenv(
        "RECAPTCHA_ENABLED",
        "True"
    )
    
    RECAPTCHA_SITE_KEY = os.getenv(
        "RECAPTCHA_SITE_KEY"
    )

    RECAPTCHA_SECRET_KEY = os.getenv(
        "RECAPTCHA_SECRET_KEY"
    )

    # =====================================================
    # FLASK MAIL
    # =====================================================

    MAIL_SERVER = "smtp.gmail.com"

    MAIL_PORT = 587

    MAIL_USE_TLS = True

    MAIL_USE_SSL = False

    MAIL_USERNAME = os.getenv("MAIL_USERNAME")

    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    MAIL_DEFAULT_SENDER = MAIL_USERNAME