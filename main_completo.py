# ==============================================================================
# LICITACIONES EUSKADI - V65 (DISEÑO MÓVIL OPTIMIZADO + TURBO)
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import json
import re
import time
import concurrent.futures
from datetime import datetime
from email.utils import parsedate_to_datetime
import urllib3

# Desactivar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 🟢 CONFIGURACIÓN 🟢 ---
MODO_DISENO = False  # False para descargas reales
MAX_WORKERS = 20     # Hilos simultáneos

# --- URLS ---
RSS_OBRAS_PLAZO = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=3&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_SERV_PLAZO  = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=3&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"

RSS_OBRAS_ALERTA      = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=2&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_ANULADO     = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=13&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_DESIERTO    = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=9&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_DESIST      = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=6&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_REDACCION   = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=12&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_PREVIO      = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=1&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_FINALIZADO  = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=14&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_HISTORICO   = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=7&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_MODIF       = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=11&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_CERRADO     = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=4&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_SUSPENSION  = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=10&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/06/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"

RSS_SERV_ALERTA      = RSS_OBRAS_ALERTA.replace("p01=1", "p01=2")
RSS_SERV_ANULADO     = RSS_OBRAS_ANULADO.replace("p01=1", "p01=2")
RSS_SERV_DESIERTO    = RSS_OBRAS_DESIERTO.replace("p01=1", "p01=2")
RSS_SERV_DESIST      = RSS_OBRAS_DESIST.replace("p01=1", "p01=2")
RSS_SERV_REDACCION   = RSS_OBRAS_REDACCION.replace("p01=1", "p01=2")
RSS_SERV_PREVIO      = RSS_OBRAS_PREVIO.replace("p01=1", "p01=2")
RSS_SERV_FINALIZADO  = RSS_OBRAS_FINALIZADO.replace("p01=1", "p01=2")
RSS_SERV_HISTORICO   = RSS_OBRAS_HISTORICO.replace("p01=1", "p01=2")
RSS_SERV_MODIF       = RSS_OBRAS_MODIF.replace("p01=1", "p01=2")
RSS_SERV_CERRADO     = RSS_OBRAS_CERRADO.replace("p01=1", "p01=2")
RSS_SERV_SUSPENSION  = RSS_OBRAS_SUSPENSION.replace("p01=1", "p01=2")

SOURCES = [
    {"type": "obras", "tag": "", "url": RSS_OBRAS_PLAZO},
    {"type": "obras", "tag": "ALERTA", "url": RSS_OBRAS_ALERTA},
    {"type": "obras", "tag": "ANULADO", "url": RSS_OBRAS_ANULADO},
    {"type": "obras", "tag": "DESIERTO", "url": RSS_OBRAS_DESIERTO},
    {"type": "obras", "tag": "DESISTIMIENTO", "url": RSS_OBRAS_DESIST},
    {"type": "obras", "tag": "REDACCION", "url": RSS_OBRAS_REDACCION},
    {"type": "obras", "tag": "PREVIO", "url": RSS_OBRAS_PREVIO},
    {"type": "obras", "tag": "FINALIZADO", "url": RSS_OBRAS_FINALIZADO},
    {"type": "obras", "tag": "HISTORICO", "url": RSS_OBRAS_HISTORICO},
    {"type": "obras", "tag": "MODIF", "url": RSS_OBRAS_MODIF},
    {"type": "obras", "tag": "PLAZO CERRADO", "url": RSS_OBRAS_CERRADO},
    {"type": "obras", "tag": "SUSPENDIDO", "url": RSS_OBRAS_SUSPENSION},
    
    {"type": "servicios", "tag": "", "url": RSS_SERV_PLAZO},
    {"type": "servicios", "tag": "ALERTA", "url": RSS_SERV_ALERTA},
    {"type": "servicios", "tag": "ANULADO", "url": RSS_SERV_ANULADO},
    {"type": "servicios", "tag": "DESIERTO", "url": RSS_SERV_DESIERTO},
    {"type": "servicios", "tag": "DESISTIMIENTO", "url": RSS_SERV_DESIST},
    {"type": "servicios", "tag": "REDACCION", "url": RSS_SERV_REDACCION},
    {"type": "servicios", "tag": "PREVIO", "url": RSS_SERV_PREVIO},
    {"type": "servicios", "tag": "FINALIZADO", "url": RSS_SERV_FINALIZADO},
    {"type": "servicios", "tag": "HISTORICO", "url": RSS_SERV_HISTORICO},
    {"type": "servicios", "tag": "MODIF", "url": RSS_SERV_MODIF},
    {"type": "servicios", "tag": "PLAZO CERRADO", "url": RSS_SERV_CERRADO},
    {"type": "servicios", "tag": "SUSPENDIDO", "url": RSS_SERV_SUSPENSION}
]

KEYWORDS_ING = ["redacción", "proyecto", "dirección de obra", "asistencia técnica", "ingeniería", "consultoría", "estudio", "control de calidad", "geotécnico", "coordinación", "redaccion"]

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def detectar_zona(texto):
    if not texto: return "Otros"
    texto = texto.lower()
    if any(x in texto for x in ["añarbe", "aguas del añarbe"]): return "Añarbe"
    if any(x in texto for x in ["txingudi", "irun", "hondarribia"]): return "Txingudi"
    if any(x in texto for x in ["donostia", "san sebastián", "errenteria", "pasaia", "hernani", "lasarte", "andoain", "oiartzun", "astigarraga", "urnieta", "lezo", "usurbil"]): return "Donostialdea"
    if any(x in texto for x in ["diputación", "foru aldundia", "bidegi"]): return "Diputación"
    return "Otros"

def limpiar_precio(texto):
    if not texto: return 0.0
    try:
        clean = re.sub(r'[^\d,]', '', texto)
        return float(clean.replace(',', '.'))
    except: return 0.0

def calcular_dias_restantes(fecha_limite_str):
    if not fecha_limite_str or fecha_limite_str == "Consultar": return 999
    try:
        fmt = "%d/%m/%Y" 
        if " " in fecha_limite_str: fecha_limite_str = fecha_limite_str.split(" ")[0]
        limite = datetime.strptime(fecha_limite_str, fmt)
        return (limite - datetime.now()).days
    except: return 999

def es_ingenieria(titulo):
    return any(k in titulo.lower() for k in KEYWORDS_ING)

def procesar_licitacion(args):
    item, tipo_origen, tag_estado = args
    link = item.link.text
    titulo = item.title.text
    categoria = tipo_origen
    if tipo_origen == "servicios" and es_ingenieria(titulo): categoria = "ingenieria"
    estado_label = tag_estado if tag_estado else "EN PLAZO"

    try:
        pub_dt = parsedate_to_datetime(item.pubDate.text)
        fecha_pub = pub_dt.strftime("%d/%m/%Y")
        fecha_pub_iso = pub_dt.strftime("%Y-%m-%d")
    except:
        fecha_pub = datetime.now().strftime("%d/%m/%Y")
        fecha_pub_iso = datetime.now().strftime("%Y-%m-%d")

    entidad = "Consultar detalle"
    presupuesto = 0.0
    fecha_limite = None
    primera_pub = "---"
    primera_pub_iso = fecha_pub_iso
    expediente = "---"
    logo_url = "https://cdn-icons-png.flaticon.com/512/4300/4300058.png"

    try:
        r_det = requests.get(link, headers=HEADERS, timeout=20, verify=False)
        if r_det.status_code == 200:
            s_det = BeautifulSoup(r_det.content, 'html.parser')
            div_titulo = s_det.find('div', class_='barraTitulo')
            if div_titulo:
                img = div_titulo.find('img')
                if img and img.get('src'):
                    logo_url = "https://www.contratacion.euskadi.eus" + img.get('src') if img.get('src').startswith('/') else img.get('src')

            target_fecha = s_det.find(string=re.compile(r"Fecha l.mite de presentaci.n", re.IGNORECASE))
            if target_fecha:
                next_el = target_fecha.parent.find_next_sibling('div') or target_fecha.parent.find_next_sibling('dd')
                if next_el: fecha_limite = next_el.text.strip().split(' ')[0]
            
            target_ppub = s_det.find(string=re.compile(r"Fecha de la primera publicaci.n", re.IGNORECASE))
            if target_ppub:
                next_el = target_ppub.parent.find_next_sibling('dd')
                if next_el: primera_pub = next_el.text.strip().split(' ')[0]
            else:
                target_ppub_gen = s_det.find(string=re.compile(r"^Fecha de publicaci.n", re.IGNORECASE))
                if target_ppub_gen:
                    next_el = target_ppub_gen.parent.find_next_sibling('dd')
                    if next_el: primera_pub = next_el.text.strip().split(' ')[0]

            target_presu = s_det.find(string=re.compile(r"Presupuesto del contrato sin IVA", re.IGNORECASE))
            if target_presu:
                next_el = target_presu.parent.find_next_sibling('div') or target_presu.parent.find_next_sibling('dd')
                if next_el: presupuesto = limpiar_precio(next_el.text)

            target_entidad = s_det.find(string=re.compile(r"Poder adjudicador", re.IGNORECASE))
            if target_entidad:
                next_el = target_entidad.parent.find_next_sibling('div') or target_entidad.parent.find_next_sibling('dd')
                if next_el: entidad = next_el.text.strip()
                
            target_exp = s_det.find(string=re.compile(r"Expediente", re.IGNORECASE))
            if target_exp:
                next_el = target_exp.parent.find_next_sibling('div') or target_exp.parent.find_next_sibling('dd')
                if next_el: expediente = next_el.text.strip()
    except: pass

    if entidad == "Consultar detalle" and " - " in titulo: entidad = titulo.split(" - ")[0]
    if primera_pub == "---": primera_pub = fecha_pub
    
    try: primera_pub_iso = datetime.strptime(primera_pub, "%d/%m/%Y").strftime("%Y-%m-%d")
    except: primera_pub_iso = fecha_pub_iso

    zona = detectar_zona(entidad)
    if fecha_limite:
        dias = calcular_dias_restantes(fecha_limite)
        try: limite_iso = datetime.strptime(fecha_limite, "%d/%m/%Y").strftime("%Y-%m-%d")
        except: limite_iso = "2999-12-31"; dias=999
    else: fecha_limite = "Consultar"; limite_iso = "2999-12-31"; dias = 999

    presu_txt = "{:,.2f} €".format(presupuesto).replace(",", "X").replace(".", ",").replace("X", ".")

    return {
        "id": 0, "categoria": categoria, "entidad": entidad, "objeto": titulo.replace('"', "'"),
        "estado": estado_label, "presupuesto_num": presupuesto, "presupuesto_txt": presu_txt,
        "limite": limite_iso, "limite_fmt": fecha_limite, "publicado": fecha_pub_iso,
        "publicado_fmt": fecha_pub, "primera_pub": primera_pub, "primera_pub_iso": primera_pub_iso,
        "dias_restantes": dias, "expediente": expediente, "grupo_fav": zona, "logo": logo_url, "link": link
    }

# --- LÓGICA PRINCIPAL ---
datos_finales = []
fecha_actual_str = datetime.now().strftime("%d/%m %H:%M")

if MODO_DISENO:
    print(f"🎨 MODO DISEÑO ACTIVADO...")
    datos_finales = [ { "id": 1, "categoria": "obras", "entidad": "Aguas del Añarbe", "objeto": "Renovación tubería", "estado": "EN PLAZO", "presupuesto_num": 150000.00, "presupuesto_txt": "150.000 €", "limite": "2025-06-01", "limite_fmt": "01/06/2025", "publicado": "2024-02-18", "publicado_fmt": "18/02/2024", "primera_pub": "10/01/2024", "primera_pub_iso": "2024-01-10", "dias_restantes": 120, "expediente": "OB-001", "grupo_fav": "Añarbe", "logo": "https://www.contratacion.euskadi.eus/images/webkpe00-euskadieus-logotipoa.gif", "link": "#" } ]
else:
    print(f"🚀 INICIANDO TURBO-SCRAPING ({MAX_WORKERS} hilos)...")
    work_queue = []
    for source in SOURCES:
        try:
            resp = requests.get(source["url"], headers=HEADERS, timeout=30, verify=False)
            soup = BeautifulSoup(resp.content, 'xml')
            items = soup.find_all('item')
            for item in items: work_queue.append((item, source["type"], source.get("tag", "")))
        except: pass
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(procesar_licitacion, work_queue))
        for i, res in enumerate(results):
            if res: res["id"] = i; datos_finales.append(res)
    print(f"🎉 FINALIZADO: {len(datos_finales)} items.")

datos_json = json.dumps(datos_finales)

# --- HTML TEMPLATE (V65 - MOBILE OPTIMIZED) ---
html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LICITACIONES EUSKADI - V65</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{ --primary: #2563eb; --bg: #f8fafc; --text-main: #0f172a; --grid-layout: 90px 1fr 100px 100px 100px 120px 80px 50px; }}
        * {{ box-sizing: border-box; }}
        body {{ background-color: var(--bg); font-family: 'Inter', sans-serif; margin: 0; padding: 0; color: var(--text-main); overflow: hidden; }}
        
        /* HEADER (DESKTOP) */
        .app-header {{ height: 70px; background: white; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; padding: 0 20px; z-index: 50; gap: 20px; }}
        .header-left {{ display: flex; align-items: center; gap: 15px; flex-shrink: 0; }}
        .app-brand {{ font-weight: 800; font-size: 1.2rem; color: #1e293b; display: flex; align-items: center; gap: 10px; white-space: nowrap; }}
        .mobile-toggle {{ display: none; font-size: 1.2rem; color: #64748b; cursor: pointer; padding: 5px; }}

        .header-center {{ flex: 1; display: flex; align-items: center; gap: 15px; background: #f1f5f9; padding: 5px 10px; border-radius: 8px; overflow-x: auto; }}
        .control-cluster {{ display: flex; align-items: center; gap: 5px; border-right: 1px solid #cbd5e1; padding-right: 10px; }}
        .search-input {{ background: transparent; border: none; outline: none; font-size: 0.85rem; width: 180px; font-weight: 500; color: #334155; }}
        .search-input::placeholder {{ color: #94a3b8; }}
        .icon-btn {{ color: #64748b; cursor: pointer; padding: 4px; border-radius: 4px; transition: 0.2s; font-size: 0.85rem; }}
        .icon-btn:hover {{ background: #e2e8f0; color: var(--primary); }}
        .active-filters {{ display: flex; gap: 5px; align-items: center; }}
        .af-tag {{ background: white; color: var(--primary); padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 700; display: flex; align-items: center; gap: 5px; cursor: pointer; border: 1px solid #bfdbfe; white-space: nowrap; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
        .update-time {{ font-size: 0.7rem; color: #94a3b8; font-weight: 600; white-space: nowrap; margin-left: auto; }}

        .header-right {{ display: flex; align-items: center; gap: 15px; flex-shrink: 0; }}
        .action-group {{ display: flex; gap: 5px; align-items: center; }}
        .date-selector {{ display: flex; background: #f1f5f9; border-radius: 6px; padding: 2px; border: 1px solid #e2e8f0; margin-right: 5px; }}
        .ds-opt {{ font-size: 0.7rem; font-weight: 700; padding: 4px 8px; cursor: pointer; border-radius: 4px; color: #64748b; transition: 0.2s; }}
        .ds-opt.active {{ background: white; color: var(--primary); box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
        .action-btn {{ padding: 6px 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 0.75rem; font-weight: 700; cursor: pointer; background: white; color: #475569; transition: 0.2s; }}
        .action-btn.active {{ background: #eff6ff; border-color: var(--primary); color: var(--primary); }}
        .nav-pills {{ display: flex; gap: 3px; background: #f1f5f9; padding: 3px; border-radius: 8px; }}
        .nav-item {{ padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; cursor: pointer; color: #64748b; transition: all 0.2s; white-space: nowrap; }}
        .nav-item.active {{ background: white; color: var(--primary); box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}
        .nav-item.dashboard-tab {{ color: #7c3aed; }}
        .nav-item.dashboard-tab.active {{ background: #7c3aed; color: white; }}

        /* LAYOUT PRINCIPAL */
        .app-container {{ display: flex; height: calc(100vh - 70px); width: 100vw; }}
        .sidebar {{ width: 280px; background: #ffffff; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; padding: 20px 0; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; background: #f1f5f9; position: relative; overflow: hidden; }}
        .filter-list {{ flex:1; overflow-y: auto; padding: 0 15px; }}
        .sb-title {{ font-size: 0.7rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin: 15px 0 8px 10px; }}
        .ent-card {{ display: flex; align-items: center; gap: 10px; padding: 6px 10px; border-radius: 6px; cursor: pointer; margin-bottom: 2px; border: 1px solid transparent; }}
        .ent-card.active {{ background: #eff6ff; border-color: #bfdbfe; }}
        .ent-img {{ width: 20px; height: 20px; object-fit: contain; mix-blend-mode: multiply; opacity: 0.8; }}
        .ent-name {{ font-size: 0.8rem; font-weight: 500; color: #334155; flex: 1; overflow: hidden; text-overflow: ellipsis; }}
        .ent-badge {{ background: #e2e8f0; color: #475569; font-size: 0.7rem; font-weight: 700; padding: 2px 6px; border-radius: 4px; }}
        .ent-card.active .ent-name {{ color: var(--primary); font-weight: 700; }}
        .ent-card.active .ent-badge {{ background: #dbeafe; color: var(--primary); }}
        .range-card {{ background: white; border: 1px solid #e2e8f0; border-left-width: 4px; border-radius: 8px; padding: 12px 15px; margin-bottom: 8px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; font-weight: 700; color: #334155; }}
        .range-card.active {{ background: #f8fafc; border-color: currentColor; color: #1e293b; }}
        .rc-green {{ border-left-color: #10b981; }} .rc-blue {{ border-left-color: #3b82f6; }} .rc-orange {{ border-left-color: #f59e0b; }} .rc-purple {{ border-left-color: #7c3aed; }}
        .filter-row {{ display: flex; justify-content: space-between; align-items: center; padding: 7px 12px; font-size: 0.85rem; color: #475569; font-weight: 500; cursor: pointer; border-radius: 6px; border-left: 3px solid transparent; }}
        .filter-row.active {{ background: #eff6ff; color: var(--primary); font-weight: 600; border-left-color: var(--primary); }}
        
        .top-deck {{ background: white; padding: 15px 30px; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; display: flex; flex-direction: column; gap: 15px; }}
        .kpi-row {{ display: flex; gap: 15px; }}
        .kpi-box {{ flex: 1; padding: 15px; border-radius: 10px; background: #f8fafc; border: 1px solid transparent; cursor: pointer; }}
        .kpi-box.active {{ background: white; border-color: currentColor; }}
        .k-blue {{ color: #1e40af; border-color: #dbeafe; background: #eff6ff; }}
        .k-green {{ color: #065f46; border-color: #d1fae5; background: #ecfdf5; }}
        .k-red {{ color: #991b1b; border-color: #fecaca; background: #fef2f2; }}
        .kpi-val {{ font-size: 1.5rem; font-weight: 800; }}
        .kpi-lbl {{ font-size: 0.7rem; font-weight: 700; text-transform: uppercase; opacity: 0.8; }}
        
        #table-wrapper {{ display: flex; flex-direction: column; height: 100%; overflow: hidden; }}
        .grid-header {{ display: grid; grid-template-columns: var(--grid-layout); gap: 10px; padding: 10px 30px; background: #e2e8f0; font-size: 0.7rem; font-weight: 800; color: #475569; user-select: none; flex-shrink: 0; }}
        .gh-cell {{ cursor: pointer; display: flex; align-items: center; gap: 5px; }}
        .gh-cell.active {{ color: var(--primary); }}
        .gh-center {{ justify-content: center; text-align: center; }}
        .gh-right {{ justify-content: flex-end; text-align: right; }}
        
        .list-container {{ flex: 1; overflow-y: auto; padding: 0; }}
        .list-inner {{ padding: 20px 30px; }}
        
        /* CABECERA DE GRUPO */
        .entity-group {{ margin-bottom: 15px; background: white; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
        .eg-title-row {{ 
            display: grid; 
            grid-template-columns: var(--grid-layout); 
            gap: 10px; 
            background: #f8fafc; 
            padding: 8px 20px; 
            border-bottom: 1px solid #e2e8f0; 
            align-items: center; 
            cursor: pointer; 
        }}
        .eg-name-part {{ grid-column: 1 / span 5; display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 0.95rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .eg-total {{ grid-column: 6; text-align: right; font-weight: 800; color: #334155; font-size: 0.85rem; }}
        .eg-count {{ grid-column: 7; text-align: center; font-size: 0.75rem; color: #64748b; font-weight: 600; }}
        .eg-logo {{ height: 30px; width: 30px; object-fit: contain; mix-blend-mode: multiply; }}
        .eg-chevron {{ transition: transform 0.3s; color: #94a3b8; flex-shrink: 0; }}
        .entity-group.collapsed .eg-chevron {{ transform: rotate(-90deg); }}
        .entity-group.collapsed .group-rows {{ display: none; }}
        
        .row-item {{ display: grid; grid-template-columns: var(--grid-layout); gap: 10px; align-items: flex-start; padding: 12px 20px; border-bottom: 1px solid #f1f5f9; font-size: 0.85rem; }}
        .ri-title {{ font-weight: 600; color: #1e293b; }}
        .ri-exp {{ font-size: 0.7rem; color: #64748b; margin-bottom: 3px; }}
        .badge {{ text-align: center; font-size: 0.7rem; font-weight: 700; padding: 3px 6px; border-radius: 4px; }}
        .b-red {{ background: #fee2e2; color: #991b1b; }}
        .b-orange {{ background: #ffedd5; color: #9a3412; }}
        .b-green {{ background: #dcfce7; color: #166534; }}
        .status-pill {{ font-size: 0.7rem; font-weight: 800; padding: 4px 8px; border-radius: 6px; text-align: center; cursor: pointer; display: inline-block; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: all 0.2s; border: 1px solid transparent; }}
        .status-pill:hover {{ transform: scale(1.02); filter: brightness(0.95); }}
        .st-active {{ background: #dbeafe; color: #1e40af; border-color: #bfdbfe; }} 
        .st-danger {{ background: #fee2e2; color: #991b1b; border-color: #fecaca; }} 
        .st-success {{ background: #dcfce7; color: #166534; border-color: #bbf7d0; }} 
        .st-warn {{ background: #ffedd5; color: #9a3412; border-color: #fed7aa; }} 
        .st-gray {{ background: #f1f5f9; color: #64748b; border-color: #e2e8f0; }} 
        .st-purple {{ background: #f3e8ff; color: #6b21a8; border-color: #e9d5ff; }} 
        
        #dashboard-view {{ display: none; height: 100%; padding: 20px; overflow: hidden; background: #f1f5f9; }}
        .dashboard-container {{ display: grid; grid-template-rows: auto 1fr; gap: 20px; height: 100%; }}
        .dash-kpis {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }}
        .kpi-modern {{ background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); display: flex; flex-direction: column; justify-content: center; border: 1px solid #f8fafc; position: relative; overflow: hidden; }}
        .kpi-modern::before {{ content: ''; position: absolute; top:0; left:0; width: 4px; height: 100%; }}
        .km-1::before {{ background: #3b82f6; }} .km-2::before {{ background: #10b981; }} .km-3::before {{ background: #8b5cf6; }}
        .kpi-m-label {{ font-size: 0.85rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; }}
        .kpi-m-val {{ font-size: 2rem; font-weight: 800; color: #1e293b; margin-top: 5px; }}
        .kpi-m-sub {{ font-size: 0.75rem; color: #94a3b8; margin-top: 5px; }}
        .dash-content {{ display: grid; grid-template-columns: 1fr 1fr 320px; grid-template-rows: 1fr 1fr; gap: 20px; min-height: 0; }}
        .d-card {{ background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); display: flex; flex-direction: column; position: relative; }}
        .dc-title {{ font-size: 0.95rem; font-weight: 700; color: #334155; margin-bottom: 15px; display: flex; justify-content: space-between; }}
        .chart-box {{ position: relative; flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; }}
        .c-span-v {{ grid-row: span 2; }}
        .top-list-container {{ overflow-y: auto; padding-right: 5px; }}
        .top-item {{ display: flex; gap: 10px; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.85rem; }}
        .top-item:last-child {{ border: none; }}
        .ti-idx {{ background: #f1f5f9; color: #64748b; font-weight: 700; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; }}
        .ti-info {{ flex: 1; overflow: hidden; }}
        .ti-ent {{ font-weight: 700; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .ti-val {{ font-weight: 600; color: var(--primary); text-align: right; white-space: nowrap; }}
        .ti-desc {{ font-size: 0.75rem; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

        /* --- 📱 MOBILE OPTIMIZATION (V65) --- */
        @media (max-width: 900px) {{
            /* Header */
            .app-header {{ height: auto; flex-wrap: wrap; padding: 10px; gap: 10px; align-items: stretch; }}
            .header-left {{ width: 100%; justify-content: space-between; margin-bottom: 5px; }}
            .mobile-toggle {{ display: block; }}
            
            /* Center: Filters & Search */
            .header-center {{ order: 3; width: 100%; flex-direction: column; align-items: flex-start; overflow-x: visible; }}
            .control-cluster {{ width: 100%; border-right: none; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; margin-bottom: 5px; }}
            .search-input {{ width: 100%; }}
            .active-filters {{ flex-wrap: wrap; }}

            /* Right: Actions & Nav */
            .header-right {{ order: 2; width: 100%; justify-content: space-between; overflow-x: auto; padding-bottom: 5px; }}
            .action-group {{ flex-shrink: 0; }}
            .nav-pills {{ flex-shrink: 0; }}

            /* Layout */
            .app-container {{ height: auto; flex-direction: column; }}
            .sidebar {{ display: none; width: 100%; border-right: none; position: fixed; top: 0; left: 0; height: 100vh; z-index: 100; box-shadow: 2px 0 10px rgba(0,0,0,0.1); padding-top: 60px; }}
            .sidebar.active {{ display: flex; }}
            .filter-list {{ padding-bottom: 100px; }} /* Space for close button if needed */
            
            /* Add close button to sidebar on mobile */
            .sidebar::before {{ content: '✕ Cerrar Menú'; position: absolute; top: 15px; right: 20px; font-weight: 800; color: #64748b; cursor: pointer; }}
            .sidebar:active::before {{ color: var(--primary); }}
            /* Hack to close sidebar: clicking top area */
            
            .top-deck {{ padding: 15px; }}
            .kpi-row {{ flex-wrap: wrap; }}
            .grid-header {{ display: none; }}
            
            /* --- CARD STYLE FOR ROWS (V65) --- */
            .row-item {{ 
                display: flex; 
                flex-direction: column; 
                position: relative; 
                padding: 15px; 
                gap: 5px;
                border-bottom: 4px solid #f1f5f9; /* Separator */
            }}
            /* Status Badge: Top Left */
            .row-item > div:nth-child(1) {{ order: 1; justify-content: flex-start !important; width: auto; margin-bottom: 5px; }}
            .status-pill {{ width: auto; font-size: 0.65rem; }}
            
            /* Title & Exp: Order 2 */
            .row-item > div:nth-child(2) {{ order: 2; width: 100%; padding-right: 0; }}
            .ri-title {{ font-size: 1rem; line-height: 1.4; }}
            
            /* Price: Order 3 (Big) */
            .row-item > div:nth-child(6) {{ order: 3; text-align: left !important; font-size: 1.1rem; color: var(--primary); font-weight: 800; margin-top: 5px; }}
            
            /* Limit Date & Days: Order 4 (Row) */
            .row-item > div:nth-child(5) {{ order: 4; text-align: left !important; font-size: 0.8rem; color: #64748b; display: inline-block; margin-right: 10px; }}
            .row-item > div:nth-child(5)::before {{ content: 'Límite: '; }}
            
            .row-item > div:nth-child(7) {{ order: 4; display: inline-block; justify-content: flex-start !important; }}
            
            /* Hide unused columns */
            .m-hide {{ display: none; }}
            .row-item > div:last-child {{ position: absolute; top: 15px; right: 15px; }} /* Link arrow top right */

            /* Group Header Mobile */
            .eg-title-row {{ display: flex; justify-content: space-between; padding: 10px 15px; }}
            .eg-name-part {{ width: 65%; font-size: 0.9rem; }}
            .eg-total {{ width: 35%; text-align: right; font-size: 0.8rem; }}
            .eg-count {{ display: none; }}
            
            /* Dashboard Mobile */
            .dash-kpis {{ grid-template-columns: 1fr; }}
            .dash-content {{ display: flex; flex-direction: column; }}
            .d-card {{ min-height: 300px; }}
            .chart-box {{ height: 250px; }}
        }}
    </style>
</head>
<body>
<div class="app-header">
    <div class="header-left">
        <div class="mobile-toggle" onclick="toggleSidebar()"><i class="fa-solid fa-bars"></i></div>
        <div class="app-brand"><i class="fa-solid fa-layer-group"></i> LICITACIONES</div>
    </div>
    <div class="header-center">
        <div class="control-cluster">
            <i class="fa-solid fa-magnifying-glass" style="color:#94a3b8; font-size:0.8rem"></i>
            <input type="text" class="search-input" id="search" placeholder="Buscar expediente..." onkeyup="renderTable()">
            <div class="icon-btn" onclick="toggleAll(false)" title="Contraer todo"><i class="fa-solid fa-angles-up"></i></div>
            <div class="icon-btn" onclick="toggleAll(true)" title="Expandir todo"><i class="fa-solid fa-angles-down"></i></div>
        </div>
        <div class="active-filters" id="active-filters-container"></div>
        <div class="update-time"><i class="fa-regular fa-clock"></i> {fecha_actual_str}</div>
    </div>
    <div class="header-right">
        <div class="action-group">
            <div class="date-selector">
                <div class="ds-opt" id="dm-first" onclick="setDateMode('first')">1ª Pub</div>
                <div class="ds-opt active" id="dm-last" onclick="setDateMode('last')">Notif.</div>
            </div>
            <div class="action-btn" id="btn-reload" onclick="reloadData()" title="Recargar"><i class="fa-solid fa-rotate"></i></div>
            <div class="action-btn" id="btn-24h" onclick="toggle24hFilter()">24h</div>
            <div class="action-btn" id="btn-week" onclick="toggleWeekFilter()">Sem.</div>
            <div class="action-btn" onclick="window.print()"><i class="fa-solid fa-file-pdf"></i></div>
        </div>
        <div class="nav-pills">
            <div class="nav-item active" onclick="switchDataset('obras', this)">OBRAS</div>
            <div class="nav-item" onclick="switchDataset('servicios', this)">SERV.</div>
            <div class="nav-item" onclick="switchDataset('ingenieria', this)">ING.</div>
            <div class="nav-item dashboard-tab" onclick="toggleDashboard(this)"><i class="fa-solid fa-chart-pie"></i></div>
        </div>
    </div>
</div>

<div class="app-container">
    <div class="sidebar" id="main-sidebar" onclick="if(event.target === this) toggleSidebar()">
        <div id="sidebar-content" class="filter-list"></div>
    </div>
    <div class="main-content">
        <div id="table-wrapper">
            <div class="top-deck">
                <div class="kpi-row">
                    <div class="kpi-box k-blue active" onclick="setMode('ads', this)">
                        <div class="kpi-val" id="k-count">0</div>
                        <div class="kpi-lbl">Activos</div>
                    </div>
                    <div class="kpi-box k-green" onclick="setMode('entities', this)">
                        <div class="kpi-val" id="k-ent">0</div>
                        <div class="kpi-lbl">Entidades</div>
                    </div>
                    <div class="kpi-box k-red" onclick="setMode('status', this)">
                        <div class="kpi-val" id="k-status">0</div>
                        <div class="kpi-lbl">Estados</div>
                    </div>
                    <div class="kpi-box" style="background:#f3f4f6; color:#4b5563" onclick="setMode('money', this)">
                        <div class="kpi-val" id="k-money">0 €</div>
                        <div class="kpi-lbl">Total</div>
                    </div>
                </div>
            </div>
            
            <div class="grid-header">
                <div class="gh-cell gh-center" onclick="setSort('estado')">ESTADO <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell" onclick="setSort('objeto')">DESCRIPCIÓN / EXPEDIENTE <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell gh-center" onclick="setSort('primera_pub')">1ª PUB <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell gh-center" onclick="setSort('publicado')">NOTIF. <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell gh-center" onclick="setSort('limite')">LÍMITE <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell gh-right" onclick="setSort('presupuesto_num')">IMPORTE <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell gh-center" onclick="setSort('dias_restantes')">DIAS <i class="fa-solid fa-sort"></i></div>
                <div style="text-align:center">LINK</div>
            </div>
            <div id="list-view" class="list-container">
                <div id="list-inner" class="list-inner"></div>
            </div>
        </div>
        <div id="dashboard-view">
            <div class="dashboard-container">
                <div class="dash-kpis">
                    <div class="kpi-modern km-1"><span class="kpi-m-label">Volumen Total</span><div class="kpi-m-val" id="dm-vol">0 €</div><span class="kpi-m-sub">Licitado en el periodo</span></div>
                    <div class="kpi-modern km-2"><span class="kpi-m-label">Nº Licitaciones</span><div class="kpi-m-val" id="dm-num">0</div><span class="kpi-m-sub">Expedientes activos</span></div>
                    <div class="kpi-modern km-3"><span class="kpi-m-label">Presupuesto Medio</span><div class="kpi-m-val" id="dm-avg">0 €</div><span class="kpi-m-sub">Por contrato</span></div>
                </div>
                <div class="dash-content">
                    <div class="d-card"><div class="dc-title">Distribución por Zonas</div><div class="chart-box"><canvas id="chartZone"></canvas></div></div>
                    <div class="d-card"><div class="dc-title">Entidades (Top 5 Volumen)</div><div class="chart-box"><canvas id="chartEnt"></canvas></div></div>
                    <div class="d-card c-span-v"><div class="dc-title">Top Oportunidades</div><div class="top-list-container" id="top-opps-list"></div></div>
                    <div class="d-card" style="grid-column: span 2"><div class="dc-title">Rangos de Presupuesto</div><div class="chart-box"><canvas id="chartRanges" style="max-height:100%"></canvas></div></div>
                </div>
            </div>
        </div>
    </div>
</div>
<script>
    const allData = {datos_json};
    let currentCategory = 'obras'; let filterWeek = false; let filter24h = false; let sidebarMode = 'ads'; 
    let currentFilters = {{ entity: null, status: null, price: null }};
    let sortField = 'publicado'; let sortDir = 'desc'; let chartInstances = [];
    let dateFilterMode = 'last'; 

    function setDateMode(mode) {{
        dateFilterMode = mode;
        document.getElementById('dm-first').classList.remove('active');
        document.getElementById('dm-last').classList.remove('active');
        document.getElementById('dm-' + mode).classList.add('active');
        if(filter24h || filterWeek) {{ renderSidebar(); renderTable(); updateKPIs(); }}
    }}

    function getStatusClass(status) {{
        s = status.toUpperCase();
        if(s.includes('ANULADO') || s.includes('DESIERTO') || s.includes('DESIST')) return 'st-danger';
        if(s.includes('PLAZO')) return 'st-active';
        if(s.includes('FORMALIZADO') || s.includes('FINALIZADO')) return 'st-success';
        if(s.includes('ALERTA') || s.includes('SUSPEN')) return 'st-warn';
        if(s.includes('REDACCION') || s.includes('MODIF')) return 'st-purple';
        return 'st-gray';
    }}

    function getData() {{
        let d = allData.filter(x => x.categoria === currentCategory);
        let now = new Date(); let limitDate = null;
        if (filter24h) {{ limitDate = new Date(); limitDate.setDate(now.getDate() - 1); }} 
        else if (filterWeek) {{ limitDate = new Date(); limitDate.setDate(now.getDate() - 7); }}
        if(limitDate) {{ d = d.filter(x => {{ let dateStr = (dateFilterMode === 'first') ? x.primera_pub_iso : x.publicado; if(!dateStr) return false; return new Date(dateStr) >= limitDate; }}); }}
        return d;
    }}

    function switchDataset(cat, el) {{ 
        currentCategory = cat; 
        document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active')); 
        if(el) el.classList.add('active'); 
        document.getElementById('dashboard-view').style.display = 'none'; 
        document.getElementById('table-wrapper').style.display = 'flex'; 
        if(window.innerWidth > 900) document.querySelector('.sidebar').style.display = 'flex'; 
        resetFilters(); updateKPIs(); setMode('ads', document.querySelector('.k-blue')); 
    }}
    function toggleDashboard(el) {{ 
        document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active')); 
        el.classList.add('active'); 
        document.getElementById('table-wrapper').style.display = 'none'; 
        document.querySelector('.sidebar').style.display = 'none'; 
        document.getElementById('dashboard-view').style.display = 'block'; 
        setTimeout(() => renderDashboard(), 50);
    }}
    function reloadData() {{ const btn = document.getElementById('btn-reload'); btn.querySelector('i').classList.add('fa-spin'); setTimeout(() => {{ window.location.href = window.location.href; }}, 500); }}
    function toggle24hFilter() {{ filter24h = !filter24h; if(filter24h) filterWeek = false; updateButtons(); updateKPIs(); renderSidebar(); renderTable(); }}
    function toggleWeekFilter() {{ filterWeek = !filterWeek; if(filterWeek) filter24h = false; updateButtons(); updateKPIs(); renderSidebar(); renderTable(); }}
    function updateButtons() {{ const btn24 = document.getElementById('btn-24h'); const btnWeek = document.getElementById('btn-week'); filter24h ? btn24.classList.add('active') : btn24.classList.remove('active'); filterWeek ? btnWeek.classList.add('active') : btnWeek.classList.remove('active'); }}
    function resetFilters() {{ currentFilters = {{ entity: null, status: null, price: null }}; renderSidebar(); renderTable(); }}
    function setMode(mode, el) {{ sidebarMode = mode; document.querySelectorAll('.kpi-box').forEach(x => x.classList.remove('active')); if(el) el.classList.add('active'); renderSidebar(); }}
    function setSort(field) {{ if(sortField === field) sortDir = sortDir === 'asc' ? 'desc' : 'asc'; else {{ sortField = field; sortDir = 'desc'; }} renderTable(); }}
    function toggleGroup(header) {{ header.parentElement.classList.toggle('collapsed'); }}
    function toggleAll(expand) {{ document.querySelectorAll('.entity-group').forEach(el => {{ expand ? el.classList.remove('collapsed') : el.classList.add('collapsed'); }}); }}
    function toggleSidebar() {{ document.getElementById('main-sidebar').classList.toggle('active'); }}
    
    function updateKPIs() {{ 
        const data = getData(); 
        document.getElementById('k-count').innerText = data.length; 
        document.getElementById('k-ent').innerText = [...new Set(data.map(d=>d.entidad))].length; 
        document.getElementById('k-status').innerText = [...new Set(data.map(d=>d.estado))].length;
        const total = data.reduce((a,b)=>a+b.presupuesto_num,0); 
        document.getElementById('k-money').innerText = formatMoney(total); 
    }}
    function formatMoney(amount) {{ return new Intl.NumberFormat('de-DE', {{ style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }}).format(amount); }}
    
    function applyFilter(type, val) {{
        if (currentFilters[type] === val) currentFilters[type] = null;
        else currentFilters[type] = val;
        renderSidebar(); renderTable(); 
        if(window.innerWidth <= 900) toggleSidebar(); 
    }}

    function renderActiveFilters() {{
        const c = document.getElementById('active-filters-container'); c.innerHTML = '';
        if(currentFilters.entity) c.innerHTML += `<div class="af-tag" onclick="applyFilter('entity', '${{currentFilters.entity}}')">Entidad: ${{currentFilters.entity.substring(0,15)}}... <i class="fa-solid fa-xmark"></i></div>`;
        if(currentFilters.status) c.innerHTML += `<div class="af-tag" onclick="applyFilter('status', '${{currentFilters.status}}')">Estado: ${{currentFilters.status}} <i class="fa-solid fa-xmark"></i></div>`;
        if(currentFilters.price) c.innerHTML += `<div class="af-tag" onclick="applyFilter('price', '${{currentFilters.price}}')">Presupuesto <i class="fa-solid fa-xmark"></i></div>`;
        if(currentFilters.entity || currentFilters.status || currentFilters.price) {{
             c.innerHTML += `<div class="af-tag" style="background:#fee2e2; color:#991b1b; border-color:#fecaca" onclick="resetFilters()">Borrar</div>`;
        }}
    }}

    function renderSidebar() {{
        const sb = document.getElementById('sidebar-content'); sb.innerHTML = ''; const data = getData();
        if (sidebarMode === 'ads') {{ sb.innerHTML = `<div class="sb-title">VISTA GENERAL</div><div class="filter-row active"><span>Todos los Anuncios</span></div>`; }} 
        else if (sidebarMode === 'entities') {{
            sb.innerHTML = `<div class="sb-title">ENTIDADES</div>`;
            let uniqueEnts = {{}}; data.forEach(d => {{ if(!uniqueEnts[d.entidad]) uniqueEnts[d.entidad] = {{count:0, logo: d.logo, zone: d.grupo_fav}}; uniqueEnts[d.entidad].count++; }});
            let zonesList = {{}}; for(let ent in uniqueEnts) {{ let z = uniqueEnts[ent].zone; if(!zonesList[z]) zonesList[z] = []; zonesList[z].push({{name: ent, ...uniqueEnts[ent]}}); }}
            const priority = ["Añarbe", "Txingudi", "Diputación", "Donostialdea", "Otros"]; let sortedZones = Object.keys(zonesList).sort((a, b) => {{ let ia = priority.indexOf(a); let ib = priority.indexOf(b); if (ia === -1) ia = 99; if (ib === -1) ib = 99; return ia - ib; }});
            sortedZones.forEach(z => {{ sb.innerHTML += `<div style="padding:5px 10px; font-weight:800; color:#cbd5e1; font-size:0.7rem; margin-top:15px; text-transform:uppercase">${{z}}</div>`; zonesList[z].sort((a,b) => b.count - a.count); zonesList[z].forEach(obj => {{ let active = (currentFilters.entity === obj.name) ? 'active' : ''; let nameClean = obj.name.replace('Ayuntamiento', 'Ayto'); sb.innerHTML += `<div class="ent-card ${{active}}" onclick="applyFilter('entity', '${{obj.name}}')"><img src="${{obj.logo}}" class="ent-img"><div class="ent-name">${{nameClean}}</div><div class="ent-badge">${{obj.count}}</div></div>`; }}); }});
        }} else if (sidebarMode === 'status') {{
            sb.innerHTML = `<div class="sb-title">ESTADO DEL EXPEDIENTE</div>`;
            let counts = {{}}; data.forEach(d => {{ counts[d.estado] = (counts[d.estado]||0)+1; }});
            let sorted = Object.keys(counts).sort();
            sorted.forEach(s => {{ let active = (currentFilters.status === s) ? 'active' : ''; let stClass = getStatusClass(s); sb.innerHTML += `<div class="ent-card ${{active}}" onclick="applyFilter('status', '${{s}}')" style="padding:10px"><div style="width:12px; height:12px; border-radius:50%; margin-right:8px;" class="${{stClass}}"></div><div class="ent-name">${{s}}</div><div class="ent-badge">${{counts[s]}}</div></div>`; }});
        }} else if (sidebarMode === 'money') {{
             sb.innerHTML = `<div class="sb-title">RANGO DE PRESUPUESTO</div>`;
             let ranges = [ {{l:'< 50.000 €', v:'u50', style:'rc-green'}}, {{l:'< 100.000 €', v:'u100', style:'rc-green'}}, {{l:'< 200.000 €', v:'u200', style:'rc-green'}}, {{l:'< 400.000 €', v:'u400', style:'rc-blue'}}, {{l:'< 600.000 €', v:'u600', style:'rc-blue'}}, {{l:'< 1.000.000 €', v:'u1m', style:'rc-orange'}}, {{l:'< 2.000.000 €', v:'u2m', style:'rc-orange'}}, {{l:'> 2.000.000 €', v:'o2m', style:'rc-purple'}} ];
             ranges.forEach(r => {{ let active = (currentFilters.price === r.v) ? 'active' : ''; sb.innerHTML += `<div class="range-card ${{r.style}} ${{active}}" onclick="applyFilter('price', '${{r.v}}')"><span>${{r.l}}</span><i class="fa-solid fa-chevron-right range-icon"></i></div>`; }});
        }}
    }}

    function renderTable() {{
        renderActiveFilters();
        const container = document.getElementById('list-inner'); container.innerHTML = ""; const search = document.getElementById('search').value.toLowerCase();
        
        let data = getData().filter(d => {{ 
            let matchText = d.objeto.toLowerCase().includes(search); 
            let matchEntity = currentFilters.entity ? (d.entidad === currentFilters.entity) : true;
            let matchStatus = currentFilters.status ? (d.estado === currentFilters.status) : true;
            let matchPrice = true;
            if (currentFilters.price) {{
                 let v = currentFilters.price;
                 if(v === 'u50') matchPrice = d.presupuesto_num < 50000; 
                 else if(v === 'u100') matchPrice = d.presupuesto_num < 100000; 
                 else if(v === 'u200') matchPrice = d.presupuesto_num < 200000; 
                 else if(v === 'u400') matchPrice = d.presupuesto_num < 400000; 
                 else if(v === 'u600') matchPrice = d.presupuesto_num < 600000; 
                 else if(v === 'u1m') matchPrice = d.presupuesto_num < 1000000; 
                 else if(v === 'u2m') matchPrice = d.presupuesto_num < 2000000; 
                 else if(v === 'o2m') matchPrice = d.presupuesto_num >= 2000000; 
            }}
            return matchText && matchEntity && matchStatus && matchPrice; 
        }});

        if(data.length === 0) {{ container.innerHTML = "<div style='text-align:center; padding:40px; color:#94a3b8'>No hay datos con estos filtros</div>"; return; }}
        
        let grouped = {{}}; data.forEach(d => {{ if(!grouped[d.entidad]) grouped[d.entidad]=[]; grouped[d.entidad].push(d); }});
        let ents = Object.keys(grouped).sort((a, b) => {{
            let rowsA = grouped[a], rowsB = grouped[b]; let valA, valB;
            if (sortField === 'presupuesto_num') {{ valA = rowsA.reduce((s, x) => s + x.presupuesto_num, 0); valB = rowsB.reduce((s, x) => s + x.presupuesto_num, 0); }} 
            else if (sortField === 'publicado') {{ valA = rowsA.reduce((m, x) => x.publicado > m ? x.publicado : m, ''); valB = rowsB.reduce((m, x) => x.publicado > m ? x.publicado : m, ''); }}
            else if (sortField === 'primera_pub') {{ valA = rowsA.reduce((m, x) => x.primera_pub > m ? x.primera_pub : m, ''); valB = rowsB.reduce((m, x) => x.primera_pub > m ? x.primera_pub : m, ''); }}
            else if (sortField === 'limite') {{ valA = rowsA.reduce((m, x) => x.limite < m ? x.limite : m, '9999-12-31'); valB = rowsB.reduce((m, x) => x.limite < m ? x.limite : m, '9999-12-31'); }}
            else if (sortField === 'dias_restantes') {{ valA = Math.min(...rowsA.map(x => x.dias_restantes)); valB = Math.min(...rowsB.map(x => x.dias_restantes)); }}
            else {{ valA = a.toLowerCase(); valB = b.toLowerCase(); }}
            if (typeof valA === 'string') {{ if (valA < valB) return sortDir === 'asc' ? -1 : 1; if (valA > valB) return sortDir === 'asc' ? 1 : -1; return 0; }}
            return sortDir === 'asc' ? valA - valB : valB - valA;
        }});
        
        ents.forEach(ent => {{
            let rows = grouped[ent]; rows.sort((a,b) => {{ let va = a[sortField], vb = b[sortField]; if (typeof va === 'string') {{ if(va < vb) return sortDir === 'asc' ? -1 : 1; if(va > vb) return sortDir === 'asc' ? 1 : -1; return 0; }} return sortDir === 'asc' ? va - vb : vb - va; }});
            let total = rows.reduce((s,x)=>s+x.presupuesto_num,0); let totalTxt = formatMoney(total); let logo = rows[0].logo;
            let entClean = ent.replace('Ayuntamiento', 'Ayto');
            
            let html = `<div class="entity-group">
                <div class="eg-title-row" onclick="toggleGroup(this)">
                    <div class="eg-name-part">
                        <i class="fa-solid fa-chevron-down eg-chevron"></i>
                        <img src="${{logo}}" class="eg-logo"> 
                        ${{entClean}}
                    </div>
                    <div class="eg-total">${{totalTxt}}</div>
                    <div class="eg-count">${{rows.length}} licit.</div>
                </div>
                <div class="group-rows">`;

            rows.forEach(r => {{ let bg = r.dias_restantes < 7 ? 'b-red' : (r.dias_restantes < 15 ? 'b-orange' : 'b-green'); let stClass = getStatusClass(r.estado); 
                html += `<div class="row-item">
                            <div style="display:flex; justify-content:center"><span class="status-pill ${{stClass}}" onclick="applyFilter('status', '${{r.estado}}')">${{r.estado}}</span></div>
                            <div><div class="ri-exp">${{r.expediente}}</div><div class="ri-title">${{r.objeto}}</div></div>
                            <div class="m-hide" style="font-weight:600; text-align:center">${{r.primera_pub}}</div>
                            <div class="m-hide" style="text-align:center">${{r.publicado_fmt}}</div>
                            <div style="font-weight:600; color:${{r.dias_restantes<7?'#ef4444':'#334155'}}; text-align:center">${{r.limite_fmt}}</div>
                            <div style="text-align:right; font-weight:700">${{r.presupuesto_txt}}</div>
                            <div style="display:flex; justify-content:center"><span class="badge ${{bg}}">${{r.dias_restantes}} días</span></div>
                            <div style="text-align:center"><a href="${{r.link}}" target="_blank" style="color:var(--primary)"><i class="fa-solid fa-arrow-right"></i></a></div>
                        </div>`; 
            }});
            html += `</div></div>`; container.innerHTML += html;
        }});
    }}
    
    function renderDashboard() {{
        chartInstances.forEach(c => c.destroy()); chartInstances = []; const data = getData();
        const totalVol = data.reduce((s,x)=>s+x.presupuesto_num, 0); const count = data.length; const avg = count > 0 ? totalVol / count : 0;
        document.getElementById('dm-vol').innerText = formatMoney(totalVol); document.getElementById('dm-num').innerText = count; document.getElementById('dm-avg').innerText = formatMoney(avg);
        const zoneCounts = {{}}; data.forEach(d => {{ zoneCounts[d.grupo_fav] = (zoneCounts[d.grupo_fav]||0) + d.presupuesto_num }});
        chartInstances.push(new Chart(document.getElementById('chartZone'), {{ type: 'doughnut', data: {{ labels: Object.keys(zoneCounts), datasets: [{{ data: Object.values(zoneCounts), backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#64748b'], borderWidth: 0 }}] }}, options: {{ maintainAspectRatio: false, plugins: {{ legend: {{ position: window.innerWidth<768?'bottom':'right', labels: {{ boxWidth: 12, font: {{ size: 10 }} }} }} }} }} }}));
        const entCounts = {{}}; data.forEach(d => {{ entCounts[d.entidad] = (entCounts[d.entidad]||0) + d.presupuesto_num }});
        const sortedEnts = Object.entries(entCounts).sort((a,b)=>b[1]-a[1]).slice(0,5);
        chartInstances.push(new Chart(document.getElementById('chartEnt'), {{ type: 'bar', data: {{ labels: sortedEnts.map(x=>x[0].replace('Ayuntamiento', 'Ayto').substring(0,18)+'...'), datasets: [{{ label: 'Volumen (€)', data: sortedEnts.map(x=>x[1]), backgroundColor: '#3b82f6', borderRadius: 4, barThickness: 20 }}] }}, options: {{ indexAxis: 'y', maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ display: false }} }} }} }} }}));
        let ranges = {{ '< 100k':0, '100k-500k':0, '500k-1M':0, '> 1M':0 }}; data.forEach(d => {{ let p = d.presupuesto_num; if(p < 100000) ranges['< 100k']++; else if(p < 500000) ranges['100k-500k']++; else if(p < 1000000) ranges['500k-1M']++; else ranges['> 1M']++; }});
        chartInstances.push(new Chart(document.getElementById('chartRanges'), {{ type: 'bar', data: {{ labels: Object.keys(ranges), datasets: [{{ label: 'Cantidad', data: Object.values(ranges), backgroundColor: ['#94a3b8', '#60a5fa', '#3b82f6', '#1e40af'], borderRadius: 6, barThickness: 30 }}] }}, options: {{ maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#f1f5f9' }} }}, x: {{ grid: {{ display: false }} }} }} }} }}));
        const topList = document.getElementById('top-opps-list'); topList.innerHTML = ''; let sortedAds = [...data].sort((a,b) => b.presupuesto_num - a.presupuesto_num).slice(0, 10);
        sortedAds.forEach((item, idx) => {{ topList.innerHTML += `<div class="top-item"><div class="ti-idx">${{idx+1}}</div><div class="ti-info"><div class="ti-ent">${{item.entidad.replace('Ayuntamiento', 'Ayto')}}</div><div class="ti-desc">${{item.objeto}}</div></div><div class="ti-val">${{item.presupuesto_txt}}</div></div>`; }});
    }}
    updateKPIs(); setMode('ads', document.querySelector('.k-blue')); renderTable();
</script>
</body>
</html>
"""

with open("index_completo.html", "w", encoding="utf-8") as file:
    file.write(html_content)

print("✅ Archivo 'index_completo.html' generado con éxito (V65 - Mobile + Turbo).")
