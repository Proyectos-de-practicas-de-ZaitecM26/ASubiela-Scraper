# app/scraping/boe.py

import requests
from datetime import datetime, date, timedelta
from bs4 import BeautifulSoup
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from ..data import sa_db, Oposicion


def extraer_provincia(texto):
    if not texto:
        return None
    import re as _re

    texto = _re.sub(r"\s+", " ", texto).strip()

    provincias = [
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
    for p in provincias:
        if _re.search(rf"\b{_re.escape(p)}\b", texto, _re.IGNORECASE):
            return p

    caps = _re.findall(r"\b[A-ZÑ]{4,15}\b", texto)
    if caps:
        return caps[0].capitalize()
    return None


BOE_SUMARIO_URL = "https://www.boe.es/datosabiertos/api/boe/sumario/{fecha}"


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
        return []

    try:
        soup = BeautifulSoup(r.content, "lxml-xml")
    except Exception:
        soup = BeautifulSoup(r.content, "xml")

    seccion = soup.find("seccion", {"codigo": "2B"})
    if not seccion:
        return []

    items = seccion.find_all("item")
    newly_inserted = []

    for item in items:
        identificador_tag = item.find("identificador")
        control_tag = item.find("control")
        titulo_tag = item.find("titulo")
        url_html_tag = item.find("url_html")
        url_pdf_tag = item.find("url_pdf")

        identificador = identificador_tag.text.strip() if identificador_tag else None
        control = control_tag.text.strip() if control_tag else None
        titulo = titulo_tag.text.strip() if titulo_tag else None
        url_html = url_html_tag.text.strip() if url_html_tag else None
        url_pdf = url_pdf_tag.text.strip() if url_pdf_tag else None

        dept_parent = item.find_parent("departamento")
        departamento = (
            dept_parent.get("nombre")
            if dept_parent and dept_parent.has_attr("nombre")
            else None
        )

        provincia = extraer_provincia(titulo) or extraer_provincia(control)

        try:
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
            
            sa_db.session.add(nueva_opo)
            # Hacemos commit individual para replicar el comportamiento de tu script original
            sa_db.session.commit()

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

        except IntegrityError:
            # Si el registro ya existe (url_html UNIQUE), limpiamos la sesión y saltamos
            sa_db.session.rollback()
            continue
        except Exception:
            # Para cualquier otro error, revertimos para no dejar la sesión bloqueada
            sa_db.session.rollback()
            continue

    return newly_inserted

def scrape_boe_ultimos_dias(dias: int = 30):
    """
    Hace scraping del BOE para los últimos `dias` días (incluyendo hoy)
    usando SQLAlchemy.
    """
    hoy = date.today()
    todas_nuevas = []

    for i in range(dias):
        fecha_obj = hoy - timedelta(days=i)
        nuevas = scrape_boe_dia(fecha_obj)
        if nuevas:
            print(f"[BOE] {fecha_obj} -> {len(nuevas)} oposiciones nuevas")
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
        print("[BOE] BBDD ya está sincronizada hasta hoy")
        return []

    todas_nuevas = []
    current = start_date

    while current <= hoy:
        nuevas = scrape_boe_dia(current)
        if nuevas:
            print(f"[BOE] {current} -> {len(nuevas)} oposiciones nuevas")
            todas_nuevas.extend(nuevas)
        else:
            print(f"[BOE] {current} -> sin oposiciones nuevas o sin sección 2B")
        current += timedelta(days=1)

    # --- Eliminar registros antiguos (Limpieza con SQLAlchemy) ---
    try:
        if max_dias_guardados and max_dias_guardados > 0:
            cutoff = hoy - timedelta(days=(max_dias_guardados - 1))
            cutoff_str = cutoff.strftime("%Y%m%d")
            
            num_borrados = sa_db.session.query(Oposicion).filter(Oposicion.fecha < cutoff_str).delete()
            sa_db.session.commit()
            
            print(f"[BOE] Eliminados {num_borrados} registros anteriores a {cutoff_str}")
    except Exception as e:
        sa_db.session.rollback()
        print(f"[BOE] Error al eliminar registros antiguos: {e}")

    return todas_nuevas