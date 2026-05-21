# app/scraping/boe.py
from dotenv.main import logger
import requests
import re as _re
import logging
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from ..data import sa_db, Oposicion




logging.basicConfig(level=logging.INFO)

BOE_SUMARIO_URL = "https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"

PROVINCIAS_LIST = [ 
        "Álava", "Albacete", "Alicante", "Almería", "Asturias",
        "Ávila", "Badajoz", "Barcelona", "Bizkaia", "Burgos",
        "Cáceres", "Cádiz", "Cantabria", "Castellón", "Ciudad Real",
        "Córdoba", "A Coruña", "Cuenca", "Gipuzkoa", "Girona",
        "Granada", "Guadalajara", "Huelva", "Huesca", "Illes Balears",
        "Jaén", "León", "Lleida", "Lugo", "Madrid",
        "Málaga", "Murcia", "Navarra", "Ourense", "Palencia",
        "Las Palmas", "Pontevedra", "La Rioja", "Salamanca",
        "Santa Cruz de Tenerife", "Segovia", "Sevilla", "Soria",
        "Tarragona", "Teruel", "Toledo", "Valencia", "Valladolid",
        "Zamora", "Zaragoza", "Ceuta", "Melilla"
    ]

PROVINCIAS_MAP = {p.lower(): p for p in PROVINCIAS_LIST}
REGEX_PROVINCIAS = rf"\b({'|'.join(_re.escape(p) for p in PROVINCIAS_LIST)})\b"
PATRON_PROVINCIAS = _re.compile(REGEX_PROVINCIAS, flags=_re.IGNORECASE)
PATRON_MAYUSCULAS = _re.compile(r"\b[A-ZÑ]{4,15}\b")



def extraer_provincia(texto):
    if not texto:
        return None
    
    texto_limpio = _re.sub(r"\s+", " ", texto).strip()
    
    match = PATRON_PROVINCIAS.search(texto_limpio)
    if match:
        # Recuperamos el nombre original mapeando la minúscula
        provincia_encontrada = match.group(1).lower()
        return PROVINCIAS_MAP.get(provincia_encontrada)

    caps = PATRON_MAYUSCULAS.findall(texto_limpio)
    if caps:
        return caps[0].capitalize()
        
    return None
    

def scrape_boe_dia(fecha: date):
    """
    Descarga y guarda en la BBDD las oposiciones del BOE (sección 2B)
    para un día concreto (objeto date).
    Devuelve la lista de oposiciones nuevas insertadas.
    """
    fecha_str = fecha.strftime("%Y%m%d")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; scraping_boe/1.0)",
        "Accept": "application/xml, text/xml, */*; q=0.01",
    }

    url = BOE_SUMARIO_URL.format(fecha=fecha_str)
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200 or not r.content:
            return []
    except requests.RequestException:
        logger.error(f"[BOE] Error de red al consultar {fecha_str}: {e}")
        return []

    try:
        soup = BeautifulSoup(r.content, "lxml-xml")
    except Exception:
        soup = BeautifulSoup(r.content, "xml")

    seccion = soup.find("seccion", {"codigo": "2B"})
    if not seccion:
        return []

    items = seccion.find_all("item")
    existentes = sa_db.session.query(Oposicion.identificador).filter_by(fecha=fecha_str).all()
    set_existentes = {e[0] for e in existentes}
    nuevas_oposiciones_db = []
    newly_inserted_dicts = []

    for item in items:
        identificador_tag = item.find("identificador")
        identificador = identificador_tag.text.strip() if identificador_tag else None
        if not identificador or identificador in set_existentes:
            continue
        
        control_tag = item.find("control")
        titulo_tag = item.find("titulo")
        url_html_tag = item.find("url_html")
        url_pdf_tag = item.find("url_pdf")
        dept_parent = item.find_parent("departamento")
        
        control = control_tag.text.strip() if control_tag else None
        titulo = titulo_tag.text.strip() if titulo_tag else None
        url_html = url_html_tag.text.strip() if url_html_tag else None
        url_pdf = url_pdf_tag.text.strip() if url_pdf_tag else None
        departamento = dept_parent.get("nombre") if dept_parent and dept_parent.has_attr("nombre") else None


        provincia = extraer_provincia(titulo) or extraer_provincia(control)
        
        nueva_opo = Oposicion(
                identificador=identificador,
                control=control,
                titulo=titulo,
                url_html=url_html,
                url_pdf=url_pdf,
                departamento=departamento,
                fecha=fecha_str,
                provincia=provincia
            )
        nuevas_oposiciones_db.append(nueva_opo)
        newly_inserted.append({
                "identificador": identificador,
                "control": control,
                "titulo": titulo,
                "url_html": url_html,
                "url_pdf": url_pdf,
                "departamento": departamento,
                "fecha": fecha_str,
                "provincia": provincia,
            })

    if nuevas_oposiciones_db:
        try:
            sa_db.session.add_all(nuevas_oposiciones_db)
            sa_db.session.commit()
        except Exception as e:
            sa_db.session.rollback()
            logger.error(f"[BOE] Error masivo al guardar oposiciones el {fecha_str}: {e}")
            return []

    return newly_inserted_dicts


def scrape_boe_ultimos_dias(dias: int = 30):
    """
    Hace scraping del BOE para los últimos días (incluyendo hoy)
    usando SQLAlchemy.
    """
    hoy = date.today()
    todas_nuevas = []

    for i in range(dias):
        fecha_obj = hoy - timedelta(days=i)
        nuevas = scrape_boe_dia(fecha_obj)
        if nuevas:
            logger.info(f"[BOE] {fecha_obj} -> {len(nuevas)} oposiciones nuevas")
            todas_nuevas.extend(nuevas)

    return todas_nuevas


def get_last_boe_date() -> date | None:
    """
    Devuelve la última fecha (tipo date) que hay en la tabla oposiciones.
    Utiliza func.max de SQLAlchemy.
    """
    max_fecha = sa_db.session.query(func.max(Oposicion.fecha)).scalar()

    if not max_fecha:
        return None

    try:
        return datetime.strptime(max_fecha, "%Y%m%d").date()
    except ValueError:
        return None


def sync_boe_hasta_hoy(max_dias_inicial: int = 30,
    max_dias_guardados: int = 30):
    """
    Sincroniza la BBDD del BOE usando SQLAlchemy.
    Mantiene la lógica de inicio desde la última fecha y limpieza de antiguos.
    """
    hoy = date.today()
    last_date = get_last_boe_date()

    if last_date is None:
        start_date = hoy - timedelta(days=max_dias_inicial - 1)
    else:
        start_date = last_date + timedelta(days=1)
        
    if start_date > hoy:
        logger.info("[BOE] BBDD ya está sincronizada hasta hoy")
        return []

    todas_nuevas = []
    current = start_date

    while current <= hoy:
        nuevas = scrape_boe_dia(current)
        if nuevas:
            logger.info(f"[BOE] {current} -> {len(nuevas)} oposiciones nuevas")
            todas_nuevas.extend(nuevas)
        else:
           logger.info(f"[BOE] {current} -> sin oposiciones nuevas o sin sección 2B")
        current += timedelta(days=1)


    try:
        if max_dias_guardados and max_dias_guardados > 0:
            cutoff = hoy - timedelta(days=(max_dias_guardados - 1))
            cutoff_str = cutoff.strftime("%Y%m%d")
            
            num_borrados = sa_db.session.query(Oposicion).filter(Oposicion.fecha < cutoff_str).delete()
            sa_db.session.commit()
            
        logger.info(f"[BOE] Eliminados {num_borrados} registros anteriores a {cutoff_str}")
    except Exception as e:
        sa_db.session.rollback()
        logger.error(f"[BOE] Error al eliminar registros antiguos: {e}")

    return todas_nuevas