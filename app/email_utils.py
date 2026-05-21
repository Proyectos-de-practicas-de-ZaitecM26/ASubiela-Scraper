from flask_mail import Message
from flask import url_for, render_template
from app.extensions import mail
from .data import sa_db, User
from itsdangerous import URLSafeTimedSerializer
import os


serializer = URLSafeTimedSerializer(
    os.environ.get('SECRET_KEY', 'dev-secret-key')
)




def generate_reset_token(email):
    """Genera token seguro para resetear contraseña"""
    return serializer.dumps(email, salt='password-reset-salt')


def verify_reset_token(token, expiration=3600):
    """Verifica token de reset"""
    try:
        email = serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=expiration
        )
        return email
    except:
        return None


def send_password_reset_email(email, token):

    reset_url = url_for(
        'auth.reset_password',
        token=token,
        _external=True
    )

    html = f"""
    <div style="font-family: Arial; max-width: 600px; margin:auto;">

        <h2 style="color:#0d6efd;">
            Recuperación de contraseña
        </h2>

        <p>Hola,</p>

        <p>
            Has solicitado restablecer tu contraseña.
        </p>

        <div style="margin:30px 0; text-align:center;">
            <a href="{reset_url}"
               style="
                    background:#0d6efd;
                    color:white;
                    padding:12px 24px;
                    text-decoration:none;
                    border-radius:5px;
               ">
                Restablecer contraseña
            </a>
        </div>

        <p>
            Este enlace expirará en 1 hora.
        </p>

    </div>
    """

    msg = Message(
        subject="Recuperación de contraseña - Oposiciones BOE",
        recipients=[email],
        html=html
    )

    mail.send(msg)






def generate_verification_token(email):
    """Genera token de verificación"""
    return serializer.dumps(email, salt='email-verification-salt')


def verify_email_token(token, expiration=86400):
    """
    Verifica token email
    86400 = 24h
    """
    try:
        email = serializer.loads(
            token,
            salt='email-verification-salt',
            max_age=expiration
        )
        return email
    except:
        return None


def send_verification_email(email):

    token = generate_verification_token(email)

    verify_url = url_for(
        'auth.verify_email',
        token=token,
        _external=True
    )

    html = f"""
    <div style="font-family: Arial; max-width: 600px; margin:auto;">

        <h2 style="color:#198754;">
            Verifica tu cuenta
        </h2>

        <p>
            Gracias por registrarte en Oposiciones BOE.
        </p>

        <p>
            Pulsa el siguiente botón para activar tu cuenta:
        </p>

        <div style="margin:30px 0; text-align:center;">
            <a href="{verify_url}"
               style="
                    background:#198754;
                    color:white;
                    padding:12px 24px;
                    text-decoration:none;
                    border-radius:5px;
               ">
                Verificar cuenta
            </a>
        </div>

        <p>
            O copia este enlace:
        </p>

        <p style="word-break: break-all;">
            {verify_url}
        </p>

        <p style="font-size:12px; color:#777;">
            Este enlace expirará en 24 horas.
        </p>

    </div>
    """

    msg = Message(
        subject="Verifica tu cuenta - Oposiciones BOE",
        recipients=[email],
        html=html
    )

    mail.send(msg)


# =====================================================
# NEWSLETTER OPOSICIONES
# =====================================================

def send_new_oposiciones_email(recipients, oposiciones):

    if not recipients or not oposiciones:
        return

    html_content = render_template(
        'emails/nuevas_oposiciones.html',
        oposiciones=oposiciones
    )

    subject = f"📢 {len(oposiciones)} nuevas oposiciones encontradas"

    msg = Message(
        subject=subject,
        recipients=recipients,
        html=html_content,
        charset='utf-8'
    )

    mail.send(msg)





def all_user_emails():

    results = sa_db.session.query(User.email).all()

    return [r[0] for r in results]