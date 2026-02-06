# ==============================================================================
# LICITACIONES EUSKADI - V53 (SCROLL FIX & DATE SCRAPING IMPROVED)
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
import urllib3

# Desactivar advertencias SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURACIÓN DE URLS ---
RSS_OBRAS_ACTIVO = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=3&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_CERRADO = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=4&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_REDACCION = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=12&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_OBRAS_SUSPENDIDO = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=10&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"

RSS_SERV_ACTIVO = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=3&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_SERV_CERRADO = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=4&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_SERV_REDACCION = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=12&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
RSS_SERV_SUSPENDIDO = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=10&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"

SOURCES = [
    {"type": "obras", "status": "activo", "url": RSS_OBRAS_ACTIVO},
    {"type": "obras", "status": "cerrado", "url": RSS_OBRAS_CERRADO},
    {"type": "obras", "status": "redaccion", "url": RSS_OBRAS_REDACCION},
    {"type": "obras", "status": "suspendido", "url": RSS_OBRAS_SUSPENDIDO},
    {"type": "servicios", "status": "activo", "url": RSS_SERV_ACTIVO},
    {"type": "servicios", "status": "cerrado", "url": RSS_SERV_CERRADO},
    {"type": "servicios", "status": "redaccion", "url": RSS_SERV_REDACCION},
    {"type": "servicios", "status": "suspendido", "url": RSS_SERV_SUSPENDIDO}
]

KEYWORDS_ING = ["redacción", "proyecto", "dirección de obra", "asistencia técnica", "ingeniería", "consultoría", "estudio", "control de calidad", "geotécnico", "coordinación", "redaccion"]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

LIMIT_PER_SOURCE = 60 

# --- FUNCIONES ---
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

def calcular_dias_restantes(fecha_limite_str, status):
    if status in ["cerrado", "suspendido"]: return -1
    if not fecha_limite_str or fecha_limite_str == "Consultar": return 999
    try:
        fmt = "%d/%m/%Y" 
        if " " in fecha_limite_str: fecha_limite_str = fecha_limite_str.split(" ")[0]
        limite = datetime.strptime(fecha_limite_str, fmt)
        hoy = datetime.now()
        delta = (limite - hoy).days
        return delta
    except: return 999

def es_ingenieria(titulo):
    t = titulo.lower()
    return any(k in t for k in KEYWORDS_ING)

# --- SCRAPING ---
datos_finales = []
fecha_actual_str = datetime.now().strftime("%d/%m/%Y %H:%M")

print(f"🚀 INICIANDO V53 ({fecha_actual_str})")

for source in SOURCES:
    tipo_origen = source["type"]
    estado_rss = source["status"]
    
    try:
        response = requests.get(source["url"], headers=HEADERS, timeout=45, verify=False)
        if response.status_code != 200: continue
        
        soup_rss = BeautifulSoup(response.content, 'xml')
        items = soup_rss.find_all('item')[:LIMIT_PER_SOURCE]
        
        for i, item in enumerate(items):
            link = item.link.text
            titulo = item.title.text
            
            # Categoría
            categoria = tipo_origen
            if tipo_origen == "servicios" and es_ingenieria(titulo): categoria = "ingenieria"

            # Fecha RSS (Suele ser la última actualización o cierre)
            try:
                pub_dt = parsedate_to_datetime(item.pubDate.text)
                f_rss_iso = pub_dt.strftime("%Y-%m-%d")
                f_rss_fmt = pub_dt.strftime("%d/%m/%Y")
            except:
                f_rss_iso = datetime.now().strftime("%Y-%m-%d")
                f_rss_fmt = datetime.now().strftime("%d/%m/%Y")

            entidad = "Consultar detalle"
            presupuesto = 0.0
            fecha_limite = None
            expediente = "---"
            logo_url = "https://cdn-icons-png.flaticon.com/512/4300/4300058.png"
            
            # Por defecto usamos la RSS, pero si encontramos una en HTML, la sobreescribimos
            f_primera_iso = f_rss_iso
            f_primera_fmt = f_rss_fmt
            found_html_date = False

            try:
                r_det = requests.get(link, headers=HEADERS, timeout=15, verify=False)
                if r_det.status_code == 200:
                    s_det = BeautifulSoup(r_det.content, 'html.parser')
                    
                    # LOGO
                    div_titulo = s_det.find('div', class_='barraTitulo')
                    if div_titulo:
                        img = div_titulo.find('img')
                        if img and img.get('src'):
                            src = img.get('src')
                            logo_url = "https://www.contratacion.euskadi.eus" + src if src.startswith('/') else src

                    # DATOS BÁSICOS
                    target_fecha = s_det.find(string=re.compile(r"Fecha l.mite de presentaci.n", re.IGNORECASE))
                    if target_fecha:
                        next_el = target_fecha.parent.find_next_sibling('div') or target_fecha.parent.find_next_sibling('dd')
                        if next_el: fecha_limite = next_el.text.strip().split(' ')[0]

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

                    # MEJORA: BÚSQUEDA AGRESIVA DE FECHA PRIMERA PUBLICACIÓN
                    # Buscamos varias etiquetas posibles
                    patterns_fecha = [
                        r"Fecha de publicaci.n del anuncio",
                        r"Fecha de env.o del anuncio",
                        r"Fecha de primera publicaci.n"
                    ]
                    
                    for pat in patterns_fecha:
                        if found_html_date: break
                        target_fpub = s_det.find(string=re.compile(pat, re.IGNORECASE))
                        if target_fpub:
                             next_el = target_fpub.parent.find_next_sibling('div') or target_fpub.parent.find_next_sibling('dd')
                             if next_el:
                                 raw_date = next_el.text.strip().split(' ')[0]
                                 try:
                                     dt_p = datetime.strptime(raw_date, "%d/%m/%Y")
                                     f_primera_iso = dt_p.strftime("%Y-%m-%d")
                                     f_primera_fmt = dt_p.strftime("%d/%m/%Y")
                                     found_html_date = True
                                 except: pass

            except: pass

            if entidad == "Consultar detalle" and " - " in titulo:
                entidad = titulo.split(" - ")[0]

            zona = detectar_zona(entidad)
            dias = calcular_dias_restantes(fecha_limite, estado_rss)
            
            if fecha_limite:
                try: limite_iso = datetime.strptime(fecha_limite, "%d/%m/%Y").strftime("%Y-%m-%d")
                except: limite_iso = "2999-12-31"
            else:
                fecha_limite = "---"; limite_iso = "2999-12-31"

            presu_txt = "{:,.2f} €".format(presupuesto).replace(",", "X").replace(".", ",").replace("X", ".")

            datos_finales.append({
                "id": len(datos_finales),
                "categoria": categoria,
                "estado": estado_rss,
                "entidad": entidad,
                "objeto": titulo.replace('"', "'"),
                "presupuesto_num": presupuesto,
                "presupuesto_txt": presu_txt,
                "limite": limite_iso,
                "limite_fmt": fecha_limite,
                "publicado": f_rss_iso,
                "publicado_fmt": f_rss_fmt,
                "primera_pub": f_primera_iso,
                "primera_pub_fmt": f_primera_fmt,
                "dias_restantes": dias,
                "expediente": expediente,
                "grupo_fav": zona,
                "logo": logo_url,
                "link": link
            })
    except: pass

datos_json = json.dumps(datos_finales)

# --- HTML TEMPLATE V53 (SCROLL FIX & FILTER FIX) ---
html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LICITACIONES V53</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{ --primary: #2563eb; --bg: #f8fafc; --text-main: #0f172a; --grid-layout: 1fr 90px 90px 90px 130px 110px 50px; }}
        * {{ box-sizing: border-box; }}
        html, body {{ height: 100%; width: 100%; overflow: hidden; margin: 0; padding: 0; }}
        body {{ background-color: var(--bg); font-family: 'Inter', sans-serif; color: var(--text-main); display: flex; flex-direction: column; }}
        
        /* HEADER (Fila Única) */
        .app-header {{ height: 60px; flex-shrink: 0; background: white; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; padding: 0 15px; z-index: 100; gap: 10px; }}
        .app-brand {{ font-weight: 800; font-size: 1rem; color: #1e293b; display: flex; align-items: center; gap: 6px; white-space: nowrap; }}
        
        .nav-pills {{ display: flex; gap: 4px; background: #f1f5f9; padding: 3px; border-radius: 6px; }}
        .nav-item {{ padding: 5px 10px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; cursor: pointer; color: #64748b; transition: 0.2s; white-space: nowrap; }}
        .nav-item.active {{ background: white; color: var(--primary); box-shadow: 0 1px 2px rgba(0,0,0,0.1); }}
        .nav-item.dashboard-tab {{ color: #7c3aed; }}
        .nav-item.dashboard-tab.active {{ background: #7c3aed; color: white; }}

        .filters-container {{ display: flex; align-items: center; gap: 5px; border-left: 1px solid #e2e8f0; padding-left: 10px; }}
        .tiny-chip {{ padding: 4px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 0.65rem; font-weight: 800; cursor: pointer; background: white; color: #64748b; }}
        .tiny-chip.active {{ background: #eff6ff; border-color: var(--primary); color: var(--primary); }}
        .tc-red.active {{ background: #fef2f2; border-color: #ef4444; color: #ef4444; }}
        .tc-org.active {{ background: #fff7ed; border-color: #f97316; color: #f97316; }}
        .tc-gry.active {{ background: #f1f5f9; border-color: #64748b; color: #334155; }}

        .date-switch {{ display: flex; background: #f1f5f9; border-radius: 4px; padding: 2px; border: 1px solid #e2e8f0; }}
        .ds-opt {{ padding: 2px 6px; font-size: 0.6rem; font-weight: 800; color: #64748b; cursor: pointer; border-radius: 2px; }}
        .ds-opt.active {{ background: white; color: #0f172a; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }}

        .search-container {{ flex: 1; min-width: 150px; max-width: 300px; position: relative; }}
        .header-search {{ width: 100%; padding: 6px 10px 6px 30px; border-radius: 6px; border: 1px solid #e2e8f0; font-size: 0.8rem; outline: none; background: #f8fafc; }}
        .search-icon {{ position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: #94a3b8; font-size: 0.8rem; }}

        .update-time {{ font-size: 0.65rem; color: #94a3b8; font-weight: 700; white-space: nowrap; margin-left: auto; padding-left: 10px; }}

        .header-utils {{ display: flex; gap: 5px; }}
        .util-btn {{ width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; color: #64748b; background: white; }}
        .btn-pdf {{ background: #1e293b; color: white; border: none; }}

        /* MAIN LAYOUT (Scroll Fix) */
        .app-container {{ display: flex; flex: 1; height: calc(100vh - 60px); width: 100vw; overflow: hidden; }}
        
        .sidebar {{ width: 260px; background: white; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; overflow: hidden; flex-shrink: 0; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; background: #f1f5f9; position: relative; overflow: hidden; }}
        
        .filter-list {{ flex:1; overflow-y: auto; padding: 15px; }}
        .sb-title {{ font-size: 0.65rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin: 15px 0 8px 5px; }}
        .ent-card {{ display: flex; align-items: center; gap: 10px; padding: 6px 8px; border-radius: 6px; cursor: pointer; margin-bottom: 2px; }}
        .ent-card.active {{ background: #eff6ff; color: var(--primary); font-weight: 700; }}
        .ent-img {{ width: 18px; height: 18px; object-fit: contain; mix-blend-mode: multiply; }}
        .ent-name {{ font-size: 0.75rem; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        .ent-badge {{ background: #e2e8f0; color: #475569; font-size: 0.65rem; font-weight: 800; padding: 2px 5px; border-radius: 4px; }}
        .range-card {{ background: white; border: 1px solid #e2e8f0; border-left: 4px solid #ccc; border-radius: 6px; padding: 10px; margin-bottom: 6px; cursor: pointer; font-size: 0.75rem; font-weight: 700; display: flex; justify-content: space-between; }}
        .range-card.active {{ background: #f8fafc; }}

        /* TABLE WRAPPER & SCROLLING */
        #table-wrapper {{ display: flex; flex-direction: column; height: 100%; overflow: hidden; }}
        
        .top-deck {{ background: white; padding: 12px 20px; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; }}
        .kpi-row {{ display: flex; gap: 10px; }}
        .kpi-box {{ flex: 1; padding: 10px; border-radius: 8px; background: #f8fafc; border: 1px solid transparent; cursor: pointer; }}
        .kpi-box.active {{ background: white; border-color: #dbeafe; }}
        .kpi-val {{ font-size: 1.2rem; font-weight: 800; }}
        .kpi-lbl {{ font-size: 0.6rem; font-weight: 800; text-transform: uppercase; color: #64748b; }}
        
        .grid-header {{ display: grid; grid-template-columns: var(--grid-layout); gap: 10px; padding: 10px 20px; background: #e2e8f0; font-size: 0.65rem; font-weight: 800; color: #475569; flex-shrink: 0; }}
        
        /* THIS IS THE KEY FIX FOR SCROLLING */
        .list-container {{ flex: 1; overflow-y: auto; padding: 15px 20px; min-height: 0; }}
        
        .entity-group {{ background: white; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 12px; overflow: hidden; }}
        .eg-title-row {{ background: #f8fafc; padding: 8px 15px; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; cursor: pointer; }}
        .row-item {{ display: grid; grid-template-columns: var(--grid-layout); gap: 10px; padding: 10px 15px; border-bottom: 1px solid #f1f5f9; font-size: 0.8rem; align-items: start; }}
        .ri-title {{ font-weight: 600; color: #1e293b; line-height: 1.2; }}
        .st-badge {{ font-size: 0.6rem; font-weight: 800; padding: 2px 4px; border-radius: 3px; text-transform: uppercase; }}
        .st-activo {{ background:#dbeafe; color:#1e40af; }}
        .st-cerrado {{ background:#fee2e2; color:#991b1b; }}
        .st-redaccion {{ background:#ffedd5; color:#9a3412; }}
        .st-suspendido {{ background:#f1f5f9; color:#475569; }}

        /* DASHBOARD */
        #dashboard-view {{ display: none; height: 100%; padding: 20px; overflow-y: auto; background: #f1f5f9; }}
        .dash-grid {{ display: grid; grid-template-columns: 1fr 1fr 300px; grid-template-rows: auto 300px 300px; gap: 20px; }}
        .d-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-direction: column; }}
        .top-item {{ display: flex; gap: 10px; align-items: center; padding: 8px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.8rem; }}

        @media (max-width: 1000px) {{
            .app-header {{ height: auto; flex-wrap: wrap; padding: 10px; }}
            .search-container {{ order: 10; max-width: none; min-width: 100%; }}
            .app-container {{ height: auto; flex-direction: column; display: block; overflow: visible; }}
            .sidebar {{ display: none; }}
            .grid-header {{ display: none; }}
            .row-item {{ display: flex; flex-direction: column; }}
            .list-container {{ overflow: visible; height: auto; }}
        }}
    </style>
</head>
<body>
<div class="app-header">
    <div class="app-brand"><i class="fa-solid fa-layer-group"></i> <span>LICITACIONES</span></div>
    
    <div class="nav-pills">
        <div class="nav-item active" onclick="switchDataset('obras', this)">OBRAS</div>
        <div class="nav-item" onclick="switchDataset('servicios', this)">SERV</div>
        <div class="nav-item" onclick="switchDataset('ingenieria', this)">ING</div>
        <div class="nav-item dashboard-tab" onclick="toggleDashboard(this)"><i class="fa-solid fa-chart-pie"></i></div>
    </div>

    <div class="filters-container">
        <div class="tiny-chip active" id="f-st-act" onclick="toggleStatus('activo')">ACT</div>
        <div class="tiny-chip tc-red" id="f-st-cer" onclick="toggleStatus('cerrado')">CER</div>
        <div class="tiny-chip tc-org" id="f-st-red" onclick="toggleStatus('redaccion')">RED</div>
        <div class="tiny-chip tc-gry" id="f-st-sus" onclick="toggleStatus('suspendido')">SUS</div>
        
        <div class="date-switch">
            <div class="ds-opt active" id="ts-pub" onclick="setDateRef('primera')">1ª</div>
            <div class="ds-opt" id="ts-upd" onclick="setDateRef('ultima')">ÚLT</div>
        </div>
        
        <div class="tiny-chip" id="btn-24h" onclick="toggleTimeFilter('24h')">24H</div>
        <div class="tiny-chip" id="btn-week" onclick="toggleTimeFilter('week')">SEM</div>
    </div>

    <div class="search-container">
        <i class="fa-solid fa-magnifying-glass search-icon"></i>
        <input type="text" class="header-search" id="search" placeholder="Buscar..." onkeyup="renderTable()">
    </div>

    <div class="update-time">{fecha_actual_str}</div>

    <div class="header-utils">
        <div class="util-btn" onclick="location.reload()"><i class="fa-solid fa-rotate"></i></div>
        <div class="util-btn btn-pdf" onclick="window.print()"><i class="fa-solid fa-file-pdf"></i></div>
    </div>
</div>

<div class="app-container">
    <div class="sidebar">
        <div id="sidebar-content" class="filter-list"></div>
    </div>
    <div class="main-content">
        <div id="table-wrapper">
            <div class="top-deck">
                <div class="kpi-row">
                    <div class="kpi-box k-blue active" onclick="setMode('ads', this)">
                        <div class="kpi-val" id="k-count">0</div>
                        <div class="kpi-lbl">Anuncios</div>
                    </div>
                    <div class="kpi-box" onclick="setMode('entities', this)">
                        <div class="kpi-val" id="k-ent">0</div>
                        <div class="kpi-lbl">Entidades</div>
                    </div>
                    <div class="kpi-box" onclick="setMode('money', this)">
                        <div class="kpi-val" id="k-money">0 €</div>
                        <div class="kpi-lbl">Importe Total</div>
                    </div>
                </div>
            </div>
            <div class="grid-header">
                <div>DESCRIPCIÓN</div>
                <div>1ª PUB</div>
                <div>ÚLTIMA</div>
                <div>LÍMITE</div>
                <div style="text-align:right">IMPORTE</div>
                <div style="text-align:center">ESTADO</div>
                <div style="text-align:center">LINK</div>
            </div>
            <div id="list-view" class="list-container">
                <div id="list-inner"></div>
            </div>
        </div>

        <div id="dashboard-view">
            <div class="dash-grid">
                <div class="d-card" style="grid-column: span 3; flex-direction:row; gap:40px; justify-content:center;">
                    <div style="text-align:center"><div class="kpi-val" id="dm-vol" style="font-size:2.5rem">0</div><div class="kpi-lbl">Volumen Total</div></div>
                    <div style="text-align:center"><div class="kpi-val" id="dm-num" style="font-size:2.5rem">0</div><div class="kpi-lbl">Expedientes</div></div>
                </div>
                <div class="d-card"><h3>Zonas</h3><div style="height:200px"><canvas id="chartZone"></canvas></div></div>
                <div class="d-card"><h3>Top Entidades</h3><div style="height:200px"><canvas id="chartEnt"></canvas></div></div>
                <div class="d-card" style="grid-row: span 2;"><h3>Top Importes</h3><div id="top-opps-list"></div></div>
                <div class="d-card" style="grid-column: span 2;"><h3>Rangos Presupuesto</h3><div style="height:200px"><canvas id="chartRanges"></canvas></div></div>
            </div>
        </div>
    </div>
</div>

<script>
    const allData = {datos_json};
    let currentCategory = 'obras', activeStatuses = ['activo'], dateRef = 'primera', timeFilter = null;
    let sidebarMode = 'ads', activeFilter = {{ type: 'none', value: null }}, sortField = 'publicado', sortDir = 'desc', chartInstances = [];

    function getData() {{
        let d = allData.filter(x => x.categoria === currentCategory && activeStatuses.includes(x.estado));
        if (timeFilter) {{
            let limit = new Date();
            limit.setDate(limit.getDate() - (timeFilter === '24h' ? 1 : 7));
            d = d.filter(x => new Date(dateRef === 'primera' ? x.primera_pub : x.publicado) >= limit);
        }}
        return d;
    }}

    function switchDataset(cat, el) {{ 
        currentCategory = cat; 
        document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active')); 
        el.classList.add('active'); 
        resetView(); 
    }}

    function toggleStatus(st) {{
        const btn = document.getElementById('f-st-'+st.substring(0,3));
        if(activeStatuses.includes(st)) {{ if(activeStatuses.length > 1) {{ activeStatuses = activeStatuses.filter(x => x !== st); btn.classList.remove('active'); }} }}
        else {{ activeStatuses.push(st); btn.classList.add('active'); }}
        refresh();
    }}

    function setDateRef(ref) {{
        dateRef = ref;
        document.getElementById('ts-pub').classList.toggle('active', ref === 'primera');
        document.getElementById('ts-upd').classList.toggle('active', ref === 'ultima');
        refresh();
    }}

    function toggleTimeFilter(tf) {{
        timeFilter = (timeFilter === tf) ? null : tf;
        document.getElementById('btn-24h').classList.toggle('active', timeFilter === '24h');
        document.getElementById('btn-week').classList.toggle('active', timeFilter === 'week');
        refresh();
    }}

    function setMode(m, el) {{ sidebarMode = m; document.querySelectorAll('.kpi-box').forEach(x => x.classList.remove('active')); el.classList.add('active'); refresh(); }}

    function resetView() {{ document.getElementById('dashboard-view').style.display = 'none'; document.getElementById('table-wrapper').style.display = 'flex'; refresh(); }}

    function toggleDashboard(el) {{
        document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active')); el.classList.add('active');
        document.getElementById('table-wrapper').style.display = 'none'; document.getElementById('dashboard-view').style.display = 'block';
        renderDashboard();
    }}

    function refresh() {{ updateKPIs(); renderSidebar(); renderTable(); }}

    function updateKPIs() {{
        const d = getData();
        document.getElementById('k-count').innerText = d.length;
        document.getElementById('k-ent').innerText = [...new Set(d.map(x=>x.entidad))].length;
        document.getElementById('k-money').innerText = new Intl.NumberFormat('de-DE').format(d.reduce((a,b)=>a+b.presupuesto_num,0)) + ' €';
    }}

    function renderSidebar() {{
        const sb = document.getElementById('sidebar-content'); sb.innerHTML = ''; const d = getData();
        if(sidebarMode === 'entities') {{
            let ents = {{}}; d.forEach(x => {{ ents[x.entidad] = (ents[x.entidad]||0)+1; }});
            Object.entries(ents).sort((a,b)=>b[1]-a[1]).forEach(([name, count]) => {{
                sb.innerHTML += `<div class="ent-card" onclick="applyFilter('entity', '${{name}}')"><div class="ent-name">${{name}}</div><div class="ent-badge">${{count}}</div></div>`;
            }});
        }} else if(sidebarMode === 'money') {{
            [ ['< 100k', 'u100'], ['100k-500k', 'u500'], ['> 500k', 'o500'] ].forEach(r => {{
                sb.innerHTML += `<div class="range-card" onclick="applyFilter('price', '${{r[1]}}')">${{r[0]}}</div>`;
            }});
        }} else {{ sb.innerHTML = '<div class="sb-title">Filtros activos</div><div class="ent-card active" onclick="applyFilter(null, null)">Todos los anuncios</div>'; }}
    }}

    function applyFilter(t, v) {{ activeFilter = {{type:t, value:v}}; renderTable(); }}

    function renderTable() {{
        const container = document.getElementById('list-inner'); 
        container.innerHTML = ""; // Limpieza crítica
        const search = document.getElementById('search').value.toLowerCase();
        
        let data = getData().filter(x => x.objeto.toLowerCase().includes(search) || x.entidad.toLowerCase().includes(search));
        
        if(activeFilter.type === 'entity') data = data.filter(x => x.entidad === activeFilter.value);
        if(activeFilter.type === 'price') {{
             if(activeFilter.value==='u100') data = data.filter(x=>x.presupuesto_num < 100000);
             else if(activeFilter.value==='u500') data = data.filter(x=>x.presupuesto_num >= 100000 && x.presupuesto_num < 500000);
             else if(activeFilter.value==='o500') data = data.filter(x=>x.presupuesto_num >= 500000);
        }}
        
        let grouped = {{}}; data.forEach(x => {{ if(!grouped[x.entidad]) grouped[x.entidad]=[]; grouped[x.entidad].push(x); }});
        
        if(Object.keys(grouped).length === 0) {{
            container.innerHTML = '<div style="text-align:center; padding:20px; color:#94a3b8">No hay resultados</div>';
            return;
        }}

        Object.entries(grouped).forEach(([ent, rows]) => {{
            let html = `<div class="entity-group"><div class="eg-title-row" onclick="let gr=this.nextElementSibling; gr.style.display=gr.style.display==='none'?'block':'none'"><strong>${{ent}}</strong> <span>${{rows.length}} licit.</span></div><div style="display:block">`;
            rows.forEach(r => {{
                let stCls = 'st-activo';
                if(r.estado === 'cerrado') stCls = 'st-cerrado';
                else if(r.estado === 'redaccion') stCls = 'st-redaccion';
                else if(r.estado === 'suspendido') stCls = 'st-suspendido';

                html += `<div class="row-item">
                    <div><div style="margin-bottom:4px"><span class="st-badge ${{stCls}}">${{r.estado}}</span> <small style="color:#94a3b8">${{r.expediente}}</small></div><div class="ri-title">${{r.objeto}}</div></div>
                    <div>${{r.primera_pub_fmt}}</div><div>${{r.publicado_fmt}}</div><div>${{r.limite_fmt}}</div>
                    <div style="text-align:right; font-weight:700">${{r.presupuesto_txt}}</div>
                    <div style="text-align:center">${{r.dias_restantes > -1 ? r.dias_restantes + ' d' : '-'}}</div>
                    <div style="text-align:center"><a href="${{r.link}}" target="_blank"><i class="fa-solid fa-eye"></i></a></div>
                </div>`;
            }});
            html += '</div></div>'; container.innerHTML += html;
        }});
    }}

    function renderDashboard() {{
        chartInstances.forEach(c => c.destroy()); chartInstances = []; const d = getData();
        document.getElementById('dm-vol').innerText = new Intl.NumberFormat('de-DE').format(d.reduce((a,b)=>a+b.presupuesto_num,0)) + ' €';
        document.getElementById('dm-num').innerText = d.length;
        
        const zoneD = {{}}; d.forEach(x => zoneD[x.grupo_fav] = (zoneD[x.grupo_fav]||0)+1);
        chartInstances.push(new Chart(document.getElementById('chartZone'), {{ type:'doughnut', data:{{ labels:Object.keys(zoneD), datasets:[{{data:Object.values(zoneD), backgroundColor:['#3b82f6','#10b981','#f59e0b','#ef4444']}}] }} }}));
        
        const entD = {{}}; d.forEach(x => entD[x.entidad] = (entD[x.entidad]||0)+x.presupuesto_num);
        const topEnts = Object.entries(entD).sort((a,b)=>b[1]-a[1]).slice(0,5);
        chartInstances.push(new Chart(document.getElementById('chartEnt'), {{ type:'bar', data:{{ labels:topEnts.map(x=>x[0].substring(0,10)), datasets:[{{label:'€', data:topEnts.map(x=>x[1]), backgroundColor:'#3b82f6'}}] }}, options:{{indexAxis:'y'}} }}));

        const list = document.getElementById('top-opps-list'); list.innerHTML = '';
        [...d].sort((a,b)=>b.presupuesto_num-a.presupuesto_num).slice(0,5).forEach(x=> {{
            list.innerHTML += `<div class="top-item"><div><strong>${{x.entidad}}</strong><br><small>${{x.objeto.substring(0,40)}}...</small></div><div style="margin-left:auto">${{x.presupuesto_txt}}</div></div>`;
        }});
    }}

    refresh();
</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
print("✅ Generado V53 con corrección de scroll, fechas y filtros.")
