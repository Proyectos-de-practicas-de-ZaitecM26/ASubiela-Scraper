import os
import sqlite3
from flask import current_app
from .models import sa_db, User, Oposicion, Visita, Favorita, Suscripcion
from ..config import Config

def inicializar_y_migrar():
    """Crea la DB y migra datos si es la primera vez que se ejecuta."""
    if not os.path.exists('instance/boe_scraper.db'): # Flask-SQLAlchemy suele crearla en /instance
        sa_db.create_all()
        
        # Verificamos si existen los archivos antiguos para migrar
        if os.path.exists('usuarios.db') and os.path.exists('oposiciones.db'):
            current_app.logger.info("⚠️ Detectadas bases de datos antiguas. Iniciando migración automática...")
            
            # Reutilizamos la lógica del script anterior (simplificada)
            conn_u = sqlite3.connect('usuarios.db')
            conn_o = sqlite3.connect('oposiciones.db')
            
            # Migrar Oposiciones
            opos = conn_o.execute("SELECT * FROM oposiciones").fetchall()
            for r in opos:
                sa_db.session.add(Oposicion(id=r[0], identificador=r[1], control=r[2], 
                                        titulo=r[3], url_html=r[4], url_pdf=r[5], 
                                        departamento=r[6], fecha=r[7], provincia=r[8]))
            
            # Migrar Usuarios
            users = conn_u.execute("SELECT * FROM users").fetchall()
            for r in users:
                sa_db.session.add(User(id=r[0], email=r[1], password_hash=r[2], name=r[3], 
                                    apellidos=r[4], age=r[5], telefono=r[6], 
                                    foto_perfil=r[7], nivel_estudios=r[8], titulacion=r[9]))
            
            sa_db.session.commit() # Commit intermedio para FKs

            # Migrar tablas relacionales
            visitas = conn_u.execute("SELECT * FROM visitas").fetchall()
            for r in visitas:
                sa_db.session.add(Visita(id=r[0], user_id=r[1], oposicion_id=r[2], fecha_visita=r[3]))
            
            favs = conn_u.execute("SELECT * FROM favoritas").fetchall()
            for r in favs:
                sa_db.session.add(Favorita(id=r[0], user_id=r[1], oposicion_id=r[2], fecha_favorito=r[3]))

            susc = conn_u.execute("SELECT * FROM suscripciones").fetchall()
            for r in susc:
                sa_db.session.add(Suscripcion(user_id=r[0], alerta_diaria=r[1], 
                                            alerta_favoritos=r[2], departamento_filtro=r[3]))
            
            sa_db.session.commit()
            conn_u.close()
            conn_o.close()
            current_app.logger.info("✅ Migración finalizada. Ya puedes borrar los archivos .db antiguos.")
    else:
        # Garantizar que la columna 'role' exista y hacer backfill si falta.
        try:
            db_path = 'instance/boe_scraper.db'
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cur = conn.cursor()
                # Comprobar columnas existentes en users
                cur.execute("PRAGMA table_info('users')")
                cols = [r[1] for r in cur.fetchall()]
                if 'role' not in cols:
                    current_app.logger.info("⚠️ Columna 'role' ausente en users. Añadiendo columna por defecto='viewer'...")
                    try:
                        cur.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'viewer'")
                        conn.commit()
                        # Asegurar valores no nulos
                        cur.execute("UPDATE users SET role='viewer' WHERE role IS NULL")
                        conn.commit()
                        current_app.logger.info("✅ Columna 'role' añadida y valores por defecto aplicados.")
                    except Exception as e:
                        current_app.logger.exception(f"Error al añadir columna 'role': {e}")
                conn.close()
        except Exception:
            current_app.logger.exception("Error comprobando/migrando la columna 'role' en la base de datos existente.")

        current_app.logger.info("✅ No es necesario ejecutar la migración, ya estamos usando SqlAlchemy")
