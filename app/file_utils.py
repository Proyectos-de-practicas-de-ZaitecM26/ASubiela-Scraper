import os
from flask import current_app
from werkzeug.utils import secure_filename
from datetime import datetime

def upload_profile_photo (request, user):
    if "foto_perfil" in request.files:
        file = request.files["foto_perfil"]
        if file and file.filename:
            allowed_extensions = {"png", "jpg", "jpeg", "gif", "webp"}
            filename_orig = file.filename.lower()
            if "." in filename_orig and filename_orig.rsplit(".", 1)[1] in allowed_extensions:

                extension = filename_orig.rsplit(".", 1)[1]
                filename = secure_filename(f"user_{user.id}_{int(datetime.now().timestamp())}.{extension}")

                upload_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "profiles")
                os.makedirs(upload_folder, exist_ok=True)

                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)

                return f"/static/uploads/profiles/{filename}"