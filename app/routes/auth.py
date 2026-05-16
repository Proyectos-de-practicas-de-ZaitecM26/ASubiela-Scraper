from datetime import datetime
import os
import requests

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user,
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash,
)

from werkzeug.utils import secure_filename

from ..data import sa_db, User

from ..email_utils import (
    send_password_reset_email,
    generate_reset_token,
    verify_reset_token,
    send_verification_email,
    verify_email_token
)

auth_bp = Blueprint("auth", __name__)


# =====================================================
# HELPERS
# =====================================================

def create_user(
    email,
    password,
    name,
    apellidos,
    age,
    telefono=None,
    nivel_estudios=None,
    titulacion=None,
):

    password_hash = generate_password_hash(password)

    email_clean = email.lower().strip()

    nuevo_usuario = User(
        email=email_clean,
        password_hash=password_hash,
        name=name,
        apellidos=apellidos,
        age=age,
        telefono=telefono,
        nivel_estudios=nivel_estudios,
        titulacion=titulacion,
        role='viewer',
        is_verified=False
    )

    try:

        sa_db.session.add(nuevo_usuario)

        sa_db.session.commit()

        return nuevo_usuario

    except Exception as e:

        sa_db.session.rollback()

        print(f"Error al crear usuario: {e}")

        raise e


def find_user_by_email(email):

    user = User.query.filter_by(email=email.lower()).first()

    return user


# =====================================================
# LOGIN
# =====================================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        # =========================
        # RECAPTCHA
        # =========================

        recaptcha_response = request.form.get(
            "g-recaptcha-response"
        )

        data = {
            "secret": current_app.config[
                "RECAPTCHA_SECRET_KEY"
            ],
            "response": recaptcha_response,
            "remoteip": request.remote_addr
        }

        google_response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data
        )

        result = google_response.json()

        if not result.get("success"):

            flash(
                "Debes completar el reCAPTCHA.",
                "danger"
            )

            return redirect(url_for("auth.login"))

        # =========================
        # LOGIN NORMAL
        # =========================

        email = (
            request.form.get("email") or ""
        ).strip()

        password = (
            request.form.get("password") or ""
        )

        user = find_user_by_email(email)

        if not user or not check_password_hash(
            user.password_hash,
            password
        ):

            flash(
                "Credenciales inválidas.",
                "danger"
            )

            return redirect(url_for("auth.login"))

        # =========================
        # EMAIL VERIFICADO
        # =========================

        if not user.is_verified:

            flash(
                "Debes verificar tu correo "
                "electrónico antes de iniciar sesión.",
                "warning"
            )

            return redirect(url_for("auth.login"))

        login_user(user)

        flash(
            "Sesión iniciada.",
            "success"
        )

        next_url = request.args.get(
            "next"
        ) or url_for("main.index")

        return redirect(next_url)

    return render_template(
        "login.html",
        site_key=current_app.config[
            "RECAPTCHA_SITE_KEY"
        ]
    )

# =====================================================
# LOGOUT
# =====================================================

@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Sesión cerrada.", "info")

    return redirect(url_for("main.index"))


# =====================================================
# REGISTER
# =====================================================

@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        email = (request.form.get("email") or "").strip()

        password = request.form.get("password") or ""

        name = (request.form.get("nombre") or "").strip()

        apellidos = (request.form.get("apellidos") or "").strip()

        age = request.form.get("edad") or ""

        nivel_estudios = (
            request.form.get("nivel_estudios") or ""
        ).strip()

        telefono = (
            request.form.get("telefono") or ""
        ).strip() or None

        titulacion = (
            request.form.get("titulacion") or ""
        ).strip() or None

        if not all([
            email,
            password,
            name,
            apellidos,
            age,
            nivel_estudios,
        ]):

            flash(
                "¡Rellena todos los campos obligatorios!",
                "danger"
            )

            return render_template(
                "register.html",
                user=current_user
            )

        if find_user_by_email(email):

            flash(
                "Ese email ya está registrado.",
                "warning"
            )

            return render_template(
                "register.html",
                user=current_user
            )

        create_user(
            email,
            password,
            name,
            apellidos,
            age,
            telefono,
            nivel_estudios,
            titulacion,
        )

        user = find_user_by_email(email)

        # =====================================================
        # FOTO PERFIL
        # =====================================================

        foto_perfil = None

        if "foto_perfil" in request.files:

            file = request.files["foto_perfil"]

            if file and file.filename:

                allowed_extensions = {
                    "png",
                    "jpg",
                    "jpeg",
                    "gif",
                    "webp"
                }

                filename = file.filename.lower()

                if "." in filename and \
                   filename.rsplit(".", 1)[1] in allowed_extensions:

                    filename = secure_filename(
                        f"user_{user.id}_{int(datetime.now().timestamp())}."
                        f"{filename.rsplit('.', 1)[1]}"
                    )

                    upload_folder = current_app.config["UPLOAD_FOLDER"]

                    filepath = os.path.join(
                        upload_folder,
                        filename
                    )

                    os.makedirs(
                        os.path.dirname(filepath),
                        exist_ok=True
                    )

                    file.save(filepath)

                    foto_perfil = (
                        f"/static/uploads/profiles/{filename}"
                    )

                    user.foto_perfil = foto_perfil

                    try:

                        sa_db.session.commit()

                    except Exception as e:

                        sa_db.session.rollback()

                        print(
                            f"Error al actualizar foto: {e}"
                        )

        # =====================================================
        # EMAIL VERIFICACIÓN
        # =====================================================

        try:

            send_verification_email(user.email)

            flash(
                "Registro completado. "
                "Revisa tu correo para verificar tu cuenta.",
                "success"
            )

        except Exception as e:

            print(f"Error enviando email: {e}")

            flash(
                "Cuenta creada, pero no se pudo enviar "
                "el email de verificación.",
                "warning"
            )

        return redirect(url_for("auth.login"))

    return render_template("register.html")


# =====================================================
# VERIFY EMAIL
# =====================================================

@auth_bp.route("/verify_email/<token>")
def verify_email(token):

    email = verify_email_token(token)

    if not email:

        flash(
            "El enlace de verificación es inválido "
            "o ha expirado.",
            "danger"
        )

        return redirect(url_for("auth.login"))

    user = find_user_by_email(email)

    if not user:

        flash(
            "Usuario no encontrado.",
            "danger"
        )

        return redirect(url_for("auth.login"))

    if user.is_verified:

        flash(
            "Tu cuenta ya estaba verificada.",
            "info"
        )

        return redirect(url_for("auth.login"))

    try:

        user.is_verified = True

        sa_db.session.commit()

        flash(
            "Cuenta verificada correctamente. "
            "Ya puedes iniciar sesión.",
            "success"
        )

    except Exception as e:

        sa_db.session.rollback()

        print(f"Error verificando usuario: {e}")

        flash(
            "Error al verificar la cuenta.",
            "danger"
        )

    return redirect(url_for("auth.login"))


# =====================================================
# CHANGE PASSWORD
# =====================================================

@auth_bp.route("/change_password", methods=["POST"])
@login_required
def change_password():

    current_password = request.form.get("current_password")

    new_password = request.form.get("new_password")

    confirm_password = request.form.get("confirm_password")

    if not current_password \
       or not new_password \
       or not confirm_password:

        flash(
            "Por favor, rellena todos los campos.",
            "danger"
        )

        return redirect(
            url_for("user.configuracion_cuenta")
        )

    if new_password != confirm_password:

        flash(
            "Las nuevas contraseñas no coinciden.",
            "danger"
        )

        return redirect(
            url_for("user.configuracion_cuenta")
        )

    if not check_password_hash(
        current_user.password_hash,
        current_password
    ):

        flash(
            "La contraseña actual es incorrecta.",
            "danger"
        )

        return redirect(
            url_for("user.configuracion_cuenta")
        )

    try:

        current_user.password_hash = generate_password_hash(
            new_password
        )

        sa_db.session.commit()

        flash(
            "¡Contraseña actualizada correctamente!",
            "success"
        )

    except Exception as e:

        sa_db.session.rollback()

        flash(
            "Ocurrió un error al actualizar la contraseña.",
            "danger"
        )

        print(f"Error: {e}")

    return redirect(
        url_for("user.configuracion_cuenta")
    )


# =====================================================
# FORGOT PASSWORD
# =====================================================

@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = (
            request.form.get("email") or ""
        ).strip().lower()

        if not email:

            flash(
                "Por favor, introduce tu correo electrónico.",
                "danger"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        user = find_user_by_email(email)

        if user:

            token = generate_reset_token(email)

            try:

                send_password_reset_email(email, token)

                flash(
                    "Se ha enviado un correo "
                    "para restablecer tu contraseña.",
                    "success",
                )

            except Exception:

                flash(
                    "Error al enviar el correo.",
                    "danger",
                )

        else:

            flash(
                "Se ha enviado un correo "
                "para restablecer tu contraseña.",
                "success",
            )

        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")


# =====================================================
# RESET PASSWORD
# =====================================================

@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):

    email = verify_reset_token(token)

    if not email:

        flash(
            "El enlace de recuperación "
            "es inválido o ha expirado.",
            "danger"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "POST":

        new_password = request.form.get("new_password")

        confirm_password = request.form.get(
            "confirm_password"
        )

        if not new_password or not confirm_password:

            flash(
                "Por favor, rellena todos los campos.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        if len(new_password) < 6:

            flash(
                "La contraseña debe tener "
                "al menos 6 caracteres.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        if new_password != confirm_password:

            flash(
                "Las contraseñas no coinciden.",
                "danger"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        user = find_user_by_email(email)

        if user:

            try:

                user.password_hash = generate_password_hash(
                    new_password
                )

                sa_db.session.commit()

                flash(
                    "¡Contraseña restablecida correctamente!",
                    "success",
                )

                return redirect(url_for("auth.login"))

            except Exception as e:

                sa_db.session.rollback()

                print(f"Error reset_password: {e}")

                flash(
                    "Error al procesar la solicitud.",
                    "danger"
                )

        else:

            flash(
                "No existe ningún usuario "
                "con ese correo.",
                "danger"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

    return render_template(
        "reset_password.html",
        token=token,
        email=email
    )