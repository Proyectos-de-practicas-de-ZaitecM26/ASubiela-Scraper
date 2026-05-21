from datetime import datetime
from app import create_app
from app.data import Oposicion, Suscripcion 
from app.email_utils import send_new_oposiciones_email
from app.scraping.boe_scraper import sync_boe_hasta_hoy

app = create_app()


FECHA_BUSQUEDA = datetime.now().strftime("%Y%m%d") 

def job_diario():
    print(f"[ {datetime.now()} ] Iniciando tarea diaria...")
    
    with app.app_context():
        with app.test_request_context():
           
            print("Conectando con el BOE para descargar novedades...")
            try:
                nuevas = sync_boe_hasta_hoy()
                print(f"Datos actualizados. {len(nuevas)} oposiciones nuevas encontradas.")
            except Exception as e:
                print(f"Error al conectar con el BOE: {e}")

            suscripciones = Suscripcion.query.filter_by(alerta_diaria=1).all()
            
            if not suscripciones:
                print("Nadie tiene activadas las alertas diarias hoy.")
                return

            print(f"Procesando {len(suscripciones)} usuarios suscritos...")

            for sub in suscripciones:
                user = sub.user 
                if not user or not user.email:
                    continue
                
                email = user.email
                filtros_str = sub.departamento_filtro
       
                query = Oposicion.query.filter_by(fecha=FECHA_BUSQUEDA)

                if filtros_str and filtros_str != "Todos":
                    clean_str = filtros_str.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
                    lista_depts = [d.strip() for d in clean_str.split(',') if d.strip()]
                    
                    if lista_depts:
                        query = query.filter(Oposicion.departamento.in_(lista_depts))
                
                opos_objects = query.all()

                if opos_objects:
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

                    print(f" Enviando {len(opos_dicts)} oposiciones a {email} (Filtros: {filtros_str})")
                    try:
                        send_new_oposiciones_email([email], opos_dicts)
                    except Exception as e:
                        print(f" Error enviando a {email}: {e}")
                else:
                    print(f" {email}: No hay novedades hoy para sus filtros.")

            print(" Tarea finalizada con éxito.")

if __name__ == "__main__":
    job_diario()