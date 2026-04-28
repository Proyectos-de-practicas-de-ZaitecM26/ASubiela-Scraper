from datetime import datetime
from app import create_app
from app.data import Oposicion, Suscripcion 
from app.email_utils import send_new_oposiciones_email
from app.scraping.boe_scraper import sync_boe_hasta_hoy

app = create_app()

# Buscamos oposiciones con la fecha de "HOY"
FECHA_BUSQUEDA = datetime.now().strftime("%Y%m%d") 

def job_diario():
    print(f"⏰ [ {datetime.now()} ] Iniciando tarea diaria...")
    
    with app.app_context():
        # Mantenemos el test_request_context para que url_for y render_template funcionen en los mails
        with app.test_request_context():
            
            # 1. DESCARGA AUTOMÁTICA (Ya usa SQLAlchemy internamente)
            print("🔄 Conectando con el BOE para descargar novedades...")
            try:
                nuevas = sync_boe_hasta_hoy()
                print(f"   ✅ Datos actualizados. {len(nuevas)} oposiciones nuevas encontradas.")
            except Exception as e:
                print(f"   ⚠️ Error al conectar con el BOE: {e}")

            # 2. GESTIÓN DE ENVÍO DE EMAILS
            # Obtenemos suscripciones activas
            suscripciones = Suscripcion.query.filter_by(alerta_diaria=1).all()
            
            if not suscripciones:
                print("📭 Nadie tiene activadas las alertas diarias hoy.")
                return

            print(f"👥 Procesando {len(suscripciones)} usuarios suscritos...")

            for sub in suscripciones:
                # Gracias a backref='user' en el modelo Suscripcion, accedemos directo al User
                user = sub.user 
                if not user or not user.email:
                    continue
                
                email = user.email
                filtros_str = sub.departamento_filtro
                
                # Construimos la query base
                query = Oposicion.query.filter_by(fecha=FECHA_BUSQUEDA)

                # Aplicamos filtros de departamento si existen
                if filtros_str and filtros_str != "Todos":
                    # Limpiamos el string por si viene con formato de lista de texto
                    clean_str = filtros_str.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
                    lista_depts = [d.strip() for d in clean_str.split(',') if d.strip()]
                    
                    if lista_depts:
                        query = query.filter(Oposicion.departamento.in_(lista_depts))
                
                # Ejecutamos la consulta
                opos_objects = query.all()

                if opos_objects:
                    # Convertimos objetos SQLAlchemy a diccionarios para mantener compatibilidad con send_new_oposiciones_email
                    # (Si tu función de email acepta objetos, podrías pasar opos_objects directamente)
                    opos_dicts = [
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

                    print(f"   ✅ Enviando {len(opos_dicts)} oposiciones a {email} (Filtros: {filtros_str})")
                    try:
                        send_new_oposiciones_email([email], opos_dicts)
                    except Exception as e:
                        print(f"   ❌ Error enviando a {email}: {e}")
                else:
                    print(f"   ℹ️ {email}: No hay novedades hoy para sus filtros.")

            print("🏁 Tarea finalizada con éxito.")

if __name__ == "__main__":
    job_diario()