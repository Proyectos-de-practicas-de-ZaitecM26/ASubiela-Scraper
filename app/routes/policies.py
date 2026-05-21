from flask import Blueprint, render_template


policies_bp = Blueprint("policies", __name__)

@policies_bp.route("/politica-cookies")
def politica_cookies():

    return render_template(
        "politica_cookies.html"
    )


@policies_bp.route("/politica-privacidad")
def politica_privacidad():

    return render_template(
        "politica_privacidad.html"
    )


@policies_bp.route("/aviso-legal")
def aviso_legal():

    return render_template(
        "aviso_legal.html"
    )