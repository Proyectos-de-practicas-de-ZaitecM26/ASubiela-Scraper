from datetime import datetime
import os

from flask import (
    Blueprint,
    app,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    current_app,
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from ..data import sa_db, User
from ..email_utils import (
    send_password_reset_email,
    generate_reset_token,
    verify_reset_token,
)

auth_bp = Blueprint("auth", __name__)


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
        titulacion=titulacion
    )

    try:
        sa_db.session.add(nuevo_usuario)
        sa_db.session.commit()
        
        return nuevo_usuario # Devolvemos el objeto por si necesitas su ID inmediatamente

    except Exception as e:
        sa_db.session.rollback()
        print(f"Error al crear usuario: {e}")
        raise e # Re-lanzamos para manejar el error (ej. email duplicado) en la ruta

def find_user_by_email(email):
    user = User.query.filter_by(email=email.lower()).first()
    return user


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        user = find_user_by_email(email)
        if not user or not check_password_hash(user.password_hash, password):
            flash("Credenciales inválidas.", "danger")
            return redirect(url_for("auth.login"))
        login_user(user)
        flash("Sesión iniciada.", "success")
        next_url = request.args.get("next") or url_for("main.index")
        return redirect(next_url)
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("main.index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        name = (request.form.get("nombre") or "").strip()
        apellidos = (request.form.get("apellidos") or "").strip()
        age = request.form.get("edad") or ""
        nivel_estudios = (request.form.get("nivel_estudios") or "").strip()
        telefono = (request.form.get("telefono") or "").strip() or None
        titulacion = (request.form.get("titulacion") or "").strip() or None

        if not all(
            [
                email,
                password,
                name,
                apellidos,
                age,
                nivel_estudios,
            ]
        ):
            flash("¡Rellena todos los campos obligatorios!", "danger")
            return render_template("register.html", user=current_user)

        if find_user_by_email(email):
            flash("Ese email ya está registrado.", "warning")
            return render_template("register.html", user=current_user)

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

        foto_perfil = None
        if "foto_perfil" in request.files:
            file = request.files["foto_perfil"]
            if file and file.filename:
                allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
                filename = file.filename.lower()
                if "." in filename and filename.rsplit(".", 1)[1] in allowed_extensions:
                    filename = secure_filename(
                        f"user_{user['id']}_{int(datetime.now().timestamp())}."
                        f"{filename.rsplit('.', 1)[1]}"
                    )
                    upload_folder = current_app.config["UPLOAD_FOLDER"]
                    filepath = os.path.join(upload_folder, filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    file.save(filepath)
                    foto_perfil = f"/static/uploads/profiles/{filename}"

                    user.foto_perfil = foto_perfil
                    try:
                        sa_db.session.commit()
                    except Exception as e:
                        sa_db.session.rollback()
                        print(f"Error al actualizar la foto de perfil: {e}")

        user = find_user_by_email(email)
        login_user(user)
        flash("Registro correcto. Sesión iniciada.", "success")
        return redirect(url_for("main.index"))
    return render_template("register.html")


@auth_bp.route("/change_password", methods=["POST"])
@login_required
def change_password():
    current_password = request.form.get("current_password")
    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not current_password or not new_password or not confirm_password:
        flash("Por favor, rellena todos los campos.", "danger")
        return redirect(url_for("user.configuracion_cuenta"))

    if new_password != confirm_password:
        flash("Las nuevas contraseñas no coinciden.", "danger")
        return redirect(url_for("user.configuracion_cuenta"))

    if not check_password_hash(current_user.password_hash, current_password):
        flash("La contraseña actual es incorrecta.", "danger")
        return redirect(url_for("user.configuracion_cuenta"))

    try:
        current_user.password_hash = generate_password_hash(new_password)
        sa_db.session.commit()
        
        flash("¡Contraseña actualizada correctamente!", "success")
    except Exception as e:
        sa_db.session.rollback()
        flash("Ocurrió un error al actualizar la contraseña.", "danger")
        print(f"Error: {e}")

    return redirect(url_for("user.configuracion_cuenta"))


@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    """Solicitud de recuperación de contraseña"""
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()

        if not email:
            flash("Por favor, introduce tu correo electrónico.", "danger")
            return redirect(url_for("auth.forgot_password"))

        user = find_user_by_email(email)

        if user:
            token = generate_reset_token(email)
            try:
                send_password_reset_email(email, token)
                flash(
                    "Se ha enviado un correo con instrucciones para restablecer tu contraseña.",
                    "success",
                )
            except Exception as e:
                flash(
                    "Error al enviar el correo. Por favor, inténtalo más tarde.",
                    "danger",
                )
        else:
            # Por seguridad, mostramos el mismo mensaje aunque el email no exista
            flash(
                "Se ha enviado un correo con instrucciones para restablecer tu contraseña.",
                "success",
            )

        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Formulario para establecer nueva contraseña usando el token"""
    email = verify_reset_token(token)

    if not email:
        flash("El enlace de recuperación es inválido o ha expirado.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if not new_password or not confirm_password:
            flash("Por favor, rellena todos los campos.", "danger")
            return redirect(url_for("auth.reset_password", token=token))

        if len(new_password) < 6:
            flash("La contraseña debe tener al menos 6 caracteres.", "danger")
            return redirect(url_for("auth.reset_password", token=token))

        if new_password != confirm_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for("auth.reset_password", token=token))

        user = find_user_by_email(email)

        if user:
            try:
                user.password_hash = generate_password_hash(new_password)
                sa_db.session.commit()

                flash(
                    "¡Contraseña restablecida correctamente! Ahora puedes iniciar sesión.",
                    "success",
                )
                return redirect(url_for("auth.login"))
            except Exception as e:
                sa_db.session.rollback()
                flash("Error al procesar la solicitud. Inténtalo de nuevo.", "danger")
                print(f"Error en reset_password: {e}")
        else:
            flash("No se encontró ningún usuario con ese correo electrónico.", "danger")
            return redirect(url_for("auth.forgot_password"))

    return render_template("reset_password.html", token=token, email=email)
