from flask import Blueprint, redirect, request, session, url_for


theme_bp = Blueprint("theme", __name__)

@theme_bp.route("/toggle-theme")
def toggle_theme():
    current = session.get("theme", "light")
    session["theme"] = "dark" if current == "light" else "light"
    return redirect(request.referrer or url_for("main.index"))