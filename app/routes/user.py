import os
from sqlalchemy import or_
from werkzeug.utils import secure_filename
from app.email_utils import send_new_oposiciones_email
from datetime import datetime, timedelta
from ..data import sa_db, Visita, Favorita, Oposicion, Suscripcion
from flask_login import login_required, current_user
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
)

user_bp = Blueprint("user", __name__)


# --- FUNCIONES AUXILIARES ---
def registrar_visita(user_id, oposicion_id):
    """
    Registra una visita o actualiza la fecha si ya existe (equivalente a INSERT OR REPLACE).
    """
    visita = Visita.query.filter_by(user_id=user_id, oposicion_id=oposicion_id).first()
    
    fecha_actual = datetime.utcnow().isoformat()

    if visita:
        visita.fecha_visita = fecha_actual
    else:
        visita = Visita(
            user_id=user_id, 
            oposicion_id=oposicion_id, 
            fecha_visita=fecha_actual
        )
        sa_db.session.add(visita)

    try:
        sa_db.session.commit()
    except Exception as e:
        sa_db.session.rollback()
        print(f"Error al registrar visita: {e}")


def toggle_favorito(user_id, oposicion_id):
    """
    Alterna el estado de favorito: si existe lo borra, si no existe lo crea.
    Retorna True si se añadió a favoritos, False si se eliminó.
    """
    favorito = Favorita.query.filter_by(user_id=user_id, oposicion_id=oposicion_id).first()

    try:
        if favorito:
            sa_db.session.delete(favorito)
            sa_db.session.commit()
            return False  
        else:
            nuevo_favorito = Favorita(
                user_id=user_id,
                oposicion_id=oposicion_id,
                fecha_favorito=datetime.utcnow().isoformat()
            )
            sa_db.session.add(nuevo_favorito)
            sa_db.session.commit()
            return True  
            
    except Exception as e:
        sa_db.session.rollback()
        print(f"Error al gestionar favorito: {e}")
        return False
    
    
# --- RUTAS ---
@user_bp.route("/user", methods=["GET", "POST"])
@login_required
def user_home():
    return render_template("user.html")


@user_bp.route("/user_oposiciones")
@login_required
def oposiciones_vigentes():
    user = current_user
    desde = (datetime.today() - timedelta(days=30)).strftime("%Y%m%d")
    page = request.args.get("page", 1, type=int)
    por_pagina = 10
    raw_departamentos = request.args.getlist("departamentos")
    selected_departamentos = [d for d in raw_departamentos if d.strip()]
    busqueda = request.args.get("busqueda", "")
    provincia = request.args.get("provincia", "")
    fecha_desde = request.args.get("fecha_desde", "")
    fecha_hasta = request.args.get("fecha_hasta", "")
    orden = request.args.get("orden", "fecha_desc")

    query = Oposicion.query.filter(Oposicion.fecha >= desde)

    if selected_departamentos:
        query = query.filter(Oposicion.departamento.in_(selected_departamentos))

    if busqueda:
        like_filter = f"%{busqueda}%"
        query = query.filter(or_(
            Oposicion.titulo.like(like_filter),
            Oposicion.identificador.like(like_filter),
            Oposicion.control.like(like_filter)
        ))

    if provincia:
        query = query.filter(Oposicion.provincia == provincia)

    if fecha_desde:
        query = query.filter(Oposicion.fecha >= fecha_desde.replace("-", ""))

    if fecha_hasta:
        query = query.filter(Oposicion.fecha <= fecha_hasta.replace("-", ""))

    if orden == "fecha_asc":
        query = query.order_by(Oposicion.fecha.asc())
    else:
        query = query.order_by(Oposicion.fecha.desc())

    pagination = query.paginate(page=page, per_page=por_pagina, error_out=False)
    oposiciones = pagination.items
    total = pagination.total
    total_pages = pagination.pages
    departamentos_query = sa_db.session.query(Oposicion.departamento).distinct().filter(
        Oposicion.fecha >= desde, 
        Oposicion.departamento.isnot(None)
    ).order_by(Oposicion.departamento).all()
    departamentos = [d[0] for d in departamentos_query]

    provincias_query = sa_db.session.query(Oposicion.provincia).distinct().filter(
        Oposicion.provincia.isnot(None)
    ).order_by(Oposicion.provincia).all()
    provincias = [p[0] for p in provincias_query]

    visitadas = [v.oposicion_id for v in user.visitas]
    favoritas = [f.oposicion_id for f in user.favoritas]

    return render_template(
        "user_oposiciones.html",
        departamentos=departamentos,
        selected_departamentos=selected_departamentos,
        oposiciones=oposiciones,
        provincias=provincias,
        busqueda=busqueda,
        provincia_filtro=provincia,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        orden=orden,
        page=page,
        total_pages=total_pages,
        visitadas=visitadas,
        favoritas=favoritas,
        hoy=datetime.today().strftime("%Y%m%d"),
        titulo_pagina=f"📢 Oposiciones Vigentes de {user.name} {user.apellidos}",
        total=total
    )

@user_bp.route("/user_alertas", methods=["GET", "POST"])
@login_required
def newsletter_prefs():
    if request.method == "POST":
        alerta_diaria = 1 if request.form.get("alerta_diaria") else 0
        seleccionados = request.form.getlist("departamentos")
        
        if "Todos" in seleccionados or not seleccionados:
            dept_string = "Todos"
        else:
            dept_string = ",".join(seleccionados)

        prefs = current_user.suscripcion
        
        if prefs:
            prefs.alerta_diaria = alerta_diaria
            prefs.departamento_filtro = dept_string
        else:
            nueva_sub = Suscripcion(
                user_id=current_user.id,
                alerta_diaria=alerta_diaria,
                departamento_filtro=dept_string
            )
            sa_db.session.add(nueva_sub)

        try:
            sa_db.session.commit()
            flash("¡Preferencias de alertas actualizadas!", "success")
        except Exception as e:
            sa_db.session.rollback()
            flash("Error al guardar las preferencias.", "danger")
            print(f"Error: {e}")
            
        return redirect(url_for("user.newsletter_prefs"))

    prefs = current_user.suscripcion
    if not prefs:
        prefs = {
            "alerta_diaria": 0,
            "departamento_filtro": "Todos",
        }

    dept_query = sa_db.session.query(Oposicion.departamento).distinct().filter(
        Oposicion.departamento.isnot(None)
    ).order_by(Oposicion.departamento).all()
    
    departamentos = [d[0] for d in dept_query]

    return render_template(
        "user_newsletter.html",
        user=current_user,
        prefs=prefs,
        departamentos=departamentos,
    )


@user_bp.route("/user_configuracion")
@login_required
def configuracion_cuenta():
    return render_template("user_configuracion.html")


@user_bp.route("/update_profile", methods=["POST"])
@login_required
def update_profile():
    user = current_user
    user.name = request.form.get("name", "").strip()
    user.apellidos = request.form.get("apellidos", "").strip()
    user.telefono = request.form.get("telefono", "").strip()
    
    genero = request.form.get("genero", "").strip()
    if genero == "Otro":
        otro_genero = request.form.get("otro_genero", "").strip()
        user.genero = otro_genero if otro_genero else genero
    else:
        user.genero = genero
    user.dni = request.form.get("dni", "").strip()
    user.fecha_nacimiento = request.form.get("fecha_nacimiento", "").strip()
    user.nacionalidad = request.form.get("nacionalidad", "").strip()
    user.direccion = request.form.get("direccion", "").strip()
    user.codigo_postal = request.form.get("codigo_postal", "").strip()
    user.ciudad = request.form.get("ciudad", "").strip()
    user.provincia = request.form.get("provincia", "").strip()
    user.nivel_estudios = request.form.get("nivel_estudios", "").strip()
    user.titulacion = request.form.get("titulacion", "").strip()
    user.situacion_laboral = request.form.get("situacion_laboral", "").strip()
    
    idiomas_seleccionados = request.form.getlist("idiomas")
    otros_idiomas = request.form.get("otros_idiomas", "").strip()
    if otros_idiomas:
        idiomas_seleccionados.append(otros_idiomas)
    user.idiomas = ", ".join(idiomas_seleccionados) if idiomas_seleccionados else ""

    user.discapacidad = 1 if request.form.get("discapacidad") == "si" else 0
    user.porcentaje_discapacidad = int(request.form.get("porcentaje_discapacidad", 0) or 0)

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
                
                user.foto_perfil = f"/static/uploads/profiles/{filename}"

    try:
        sa_db.session.commit()
        flash("Perfil actualizado correctamente", "success")
    except Exception as e:
        sa_db.session.rollback()
        current_app.logger.error(f"Error al actualizar perfil: {e}")
        flash("Hubo un error al guardar los cambios.", "danger")

    return redirect(url_for("user.configuracion_cuenta"))


@user_bp.route("/marcar_visitada/<int:oposicion_id>", methods=["POST"])
@login_required
def marcar_visitada(oposicion_id):
    user_id = current_user.id
    registrar_visita(user_id, oposicion_id)
    return jsonify({"ok": True})


@user_bp.route("/toggle_favorito/<int:oposicion_id>", methods=["POST"])
@login_required
def toggle_favorito_route(oposicion_id):
    user = current_user
    is_favorite = toggle_favorito(user.id, oposicion_id)
    return jsonify({"ok": True, "is_favorite": is_favorite})


@user_bp.route("/user_favoritas")
@login_required
def oposiciones_favoritas():
    user = current_user
    desde = (datetime.today() - timedelta(days=30)).strftime("%Y%m%d")

    depts_query = sa_db.session.query(Oposicion.departamento).distinct().filter(
        Oposicion.fecha >= desde, 
        Oposicion.departamento.isnot(None)
    ).order_by(Oposicion.departamento).all()
    departamentos = [d[0] for d in depts_query]

    prov_query = sa_db.session.query(Oposicion.provincia).distinct().filter(
        Oposicion.provincia.isnot(None)
    ).order_by(Oposicion.provincia).all()
    provincias = [p[0] for p in prov_query]
    
    query_favoritas = sa_db.session.query(Oposicion).join(
        Favorita, Oposicion.id == Favorita.oposicion_id
    ).filter(
        Favorita.user_id == user.id
    ).order_by(
        Favorita.fecha_favorito.desc()
    )

    oposiciones_ordenadas = query_favoritas.all()
    visitadas_ids = [v.oposicion_id for v in user.visitas]
    favoritas_ids = [f.oposicion_id for f in user.favoritas]

    return render_template(
        "user_oposiciones.html",
        oposiciones=oposiciones_ordenadas,
        departamentos=departamentos,
        selected_departamentos=[],
        provincias=provincias,
        busqueda="",
        provincia_filtro="",
        fecha_desde="",
        fecha_hasta="",
        visitadas=visitadas_ids,
        favoritas=favoritas_ids,
        hoy=datetime.now().strftime("%Y%m%d"),
        total=len(oposiciones_ordenadas),
        page=1,
        total_pages=1,
        orden="desc",
        titulo_pagina=f"⭐ Oposiciones Favoritas de {user.name} {user.apellidos}",
    )


@user_bp.route("/enviar_resumen_ahora", methods=["POST"])
@login_required
def enviar_resumen_ahora():
    user = current_user
    prefs = user.suscripcion
    dept_filter_str = prefs.departamento_filtro if prefs else "Todos"

    fecha_busqueda = datetime.now().strftime("%Y%m%d")
    
    query = Oposicion.query.filter(Oposicion.fecha >= fecha_busqueda)

    if dept_filter_str and dept_filter_str != "Todos":
        clean_str = dept_filter_str.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
        lista_depts = [d.strip() for d in clean_str.split(',') if d.strip()]
        
        if lista_depts:
            query = query.filter(Oposicion.departamento.in_(lista_depts))

    opos_objects = query.order_by(Oposicion.fecha.desc()).limit(200).all()

    oposiciones = [
        {
            "identificador": o.identificador,
            "control": o.control,
            "titulo": o.titulo,
            "url_html": o.url_html,
            "url_pdf": o.url_pdf,
            "departamento": o.departamento,
            "fecha": o.fecha,
            "provincia": o.provincia
        } for o in opos_objects
    ]

    if oposiciones:
        try:
            send_new_oposiciones_email([user.email], oposiciones)
            flash(
                f"✅ Email enviado correctamente a {user.email} con {len(oposiciones)} oposiciones recientes.",
                "success",
            )
        except Exception as e:
            current_app.logger.error(f"Error al enviar email: {e}")
            flash(f"❌ Error al enviar email: {e}", "danger")
    else:
        flash(f"⚠️ No se encontraron oposiciones publicadas hoy para: {dept_filter_str}", "warning")

    return redirect(url_for("user.newsletter_prefs"))