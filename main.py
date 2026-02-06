# ==============================================================================
# LICITACIONES EUSKADI - V54 (CLEAN UI & ROBUST LOGIC REWRITE)
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
from email.utils import parsedate_to_datetime
import urllib3

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

print(f"🚀 INICIANDO V54 ({fecha_actual_str})")

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

            # Fecha RSS
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
            
            f_primera_iso = f_rss_iso
            f_primera_fmt = f_rss_fmt
            found_html_date = False

            try:
                r_det = requests.get(link, headers=HEADERS, timeout=15, verify=False)
                if r_det.status_code == 200:
                    s_det = BeautifulSoup(r_det.content, 'html.parser')
                    
                    div_titulo = s_det.find('div', class_='barraTitulo')
                    if div_titulo:
                        img = div_titulo.find('img')
                        if img and img.get('src'):
                            src = img.get('src')
                            logo_url = "https://www.contratacion.euskadi.eus" + src if src.startswith('/') else src

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

                    # Búsqueda agresiva fecha
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

# --- HTML TEMPLATE V54 (CLEAN LAYOUT) ---
html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LICITACIONES V54</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{ 
            --primary: #3b82f6; 
            --bg: #f3f4f6; 
            --text: #111827; 
            --border: #e5e7eb;
            --header-h: 55px;
            --toolbar-h: 45px;
            --total-top: 100px;
            --grid-cols: 1fr 90px 90px 90px 120px 100px 50px;
        }}
        * {{ box-sizing: border-box; }}
        html, body {{ height: 100%; width: 100%; margin: 0; padding: 0; overflow: hidden; font-family: 'Inter', sans-serif; color: var(--text); background: var(--bg); }}
        
        /* 1. TOP HEADER */
        .app-header {{ height: var(--header-h); background: white; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; padding: 0 20px; z-index: 50; }}
        .brand {{ font-weight: 800; font-size: 1.1rem; color: #1e293b; display: flex; align-items: center; gap: 8px; }}
        .brand i {{ color: var(--primary); }}
        
        .main-nav {{ display: flex; gap: 10px; background: #f9fafb; padding: 4px; border-radius: 8px; border: 1px solid var(--border); }}
        .nav-btn {{ padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: 600; cursor: pointer; color: #6b7280; transition: 0.2s; }}
        .nav-btn:hover {{ color: #111827; background: #e5e7eb; }}
        .nav-btn.active {{ background: white; color: var(--primary); box-shadow: 0 1px 2px rgba(0,0,0,0.05); border: 1px solid #f3f4f6; }}
        .nav-btn.dash-btn.active {{ color: #7c3aed; }}
        
        .search-wrap {{ position: relative; width: 300px; }}
        .search-inp {{ width: 100%; padding: 8px 10px 8px 32px; border: 1px solid var(--border); border-radius: 6px; font-size: 0.85rem; outline: none; background: #f9fafb; }}
        .search-inp:focus {{ border-color: var(--primary); background: white; }}
        .search-icon {{ position: absolute; left: 10px; top: 50%; transform: translateY(-50%); color: #9ca3af; font-size: 0.85rem; }}

        /* 2. TOOLBAR (Second Row) */
        .toolbar {{ height: var(--toolbar-h); background: white; border-bottom: 1px solid var(--border); display: flex; align-items: center; padding: 0 20px; gap: 15px; justify-content: space-between; }}
        .filter-group {{ display: flex; align-items: center; gap: 8px; }}
        .fg-label {{ font-size: 0.7rem; font-weight: 800; color: #9ca3af; text-transform: uppercase; margin-right: 4px; }}
        
        .chip {{ padding: 4px 10px; border: 1px solid var(--border); border-radius: 20px; font-size: 0.75rem; font-weight: 600; color: #4b5563; background: white; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 4px; }}
        .chip:hover {{ border-color: #d1d5db; color: #111827; }}
        .chip.active {{ background: #eff6ff; border-color: var(--primary); color: var(--primary); font-weight: 700; }}
        /* Colores Específicos */
        .chip.c-red.active {{ background: #fef2f2; border-color: #ef4444; color: #ef4444; }}
        .chip.c-org.active {{ background: #fff7ed; border-color: #f97316; color: #f97316; }}
        .chip.c-gry.active {{ background: #f3f4f6; border-color: #6b7280; color: #374151; }}
        
        .switch-wrap {{ display: flex; background: #f3f4f6; border-radius: 4px; padding: 2px; border: 1px solid var(--border); }}
        .sw-opt {{ padding: 3px 8px; font-size: 0.7rem; font-weight: 700; color: #6b7280; cursor: pointer; border-radius: 3px; }}
        .sw-opt.active {{ background: white; color: #111827; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }}

        .meta-info {{ font-size: 0.7rem; color: #9ca3af; font-weight: 600; margin-left: auto; }}
        .action-icon {{ width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 4px; cursor: pointer; color: #4b5563; border: 1px solid transparent; }}
        .action-icon:hover {{ background: #f3f4f6; border-color: var(--border); }}

        /* 3. MAIN LAYOUT */
        .app-body {{ display: flex; height: calc(100vh - var(--total-top)); }}
        .sidebar {{ width: 260px; background: white; border-right: 1px solid var(--border); display: flex; flex-direction: column; overflow: hidden; }}
        .content {{ flex: 1; display: flex; flex-direction: column; background: #f9fafb; position: relative; overflow: hidden; }}

        /* Sidebar Content */
        .sb-scroll {{ flex: 1; overflow-y: auto; padding: 10px; }}
        .sb-head {{ padding: 15px 10px 5px 10px; font-size: 0.7rem; font-weight: 800; color: #9ca3af; text-transform: uppercase; }}
        .sb-item {{ display: flex; align-items: center; justify-content: space-between; padding: 8px 10px; border-radius: 6px; cursor: pointer; font-size: 0.8rem; margin-bottom: 2px; color: #374151; }}
        .sb-item:hover {{ background: #f3f4f6; }}
        .sb-item.active {{ background: #eff6ff; color: var(--primary); font-weight: 600; }}
        .sb-badge {{ background: #e5e7eb; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; color: #4b5563; }}
        .sb-item.active .sb-badge {{ background: #dbeafe; color: var(--primary); }}

        /* Table Area */
        .table-stats {{ padding: 10px 20px; display: flex; gap: 15px; background: white; border-bottom: 1px solid var(--border); }}
        .stat-card {{ flex: 1; padding: 10px; border: 1px solid var(--border); border-radius: 8px; background: #f9fafb; cursor: pointer; }}
        .stat-card.active {{ background: #eff6ff; border-color: #bfdbfe; }}
        .stat-val {{ font-size: 1.2rem; font-weight: 800; color: #1f2937; }}
        .stat-lbl {{ font-size: 0.7rem; font-weight: 700; text-transform: uppercase; color: #6b7280; }}

        /* IMPORTANT: SCROLL FIX */
        .table-container {{ flex: 1; overflow-y: auto; position: relative; }}
        .grid-head {{ display: grid; grid-template-columns: var(--grid-cols); gap: 15px; padding: 10px 20px; background: #f3f4f6; border-bottom: 1px solid var(--border); font-size: 0.7rem; font-weight: 700; color: #6b7280; position: sticky; top: 0; z-index: 10; }}
        .grid-row {{ display: grid; grid-template-columns: var(--grid-cols); gap: 15px; padding: 12px 20px; border-bottom: 1px solid var(--border); background: white; align-items: start; font-size: 0.85rem; }}
        .grid-row:hover {{ background: #f9fafb; }}
        
        .row-main {{ display: flex; flex-direction: column; gap: 4px; }}
        .row-meta {{ font-size: 0.75rem; color: #6b7280; display: flex; align-items: center; gap: 6px; }}
        .badge {{ padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }}
        .bd-act {{ background: #dbeafe; color: #1e40af; }}
        .bd-cer {{ background: #fee2e2; color: #991b1b; }}
        .bd-red {{ background: #ffedd5; color: #9a3412; }}
        .bd-sus {{ background: #f3f4f6; color: #374151; }}

        .row-title {{ font-weight: 600; color: #111827; line-height: 1.4; }}
        .row-date {{ font-size: 0.8rem; color: #4b5563; }}
        .row-money {{ font-weight: 700; text-align: right; color: #1f2937; }}
        .action-link {{ color: var(--primary); display: flex; justify-content: center; font-size: 1rem; }}

        /* Group Headers */
        .group-header {{ background: #e5e7eb; padding: 8px 20px; font-size: 0.85rem; font-weight: 700; color: #374151; cursor: pointer; display: flex; justify-content: space-between; position: sticky; top: 38px; z-index: 9; border-bottom: 1px solid #d1d5db; }}
        
        /* Dashboard */
        #dashboard-view {{ display: none; padding: 20px; overflow-y: auto; height: 100%; }}
        .dash-grid {{ display: grid; grid-template-columns: 1fr 1fr 300px; gap: 20px; }}
        .d-card {{ background: white; padding: 20px; border-radius: 12px; border: 1px solid var(--border); box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}

        @media (max-width: 1000px) {{
            .app-header {{ height: auto; flex-direction: column; padding: 10px; align-items: stretch; gap: 10px; }}
            .search-wrap {{ width: 100%; }}
            .toolbar {{ height: auto; flex-wrap: wrap; padding: 10px; }}
            .app-body {{ height: auto; display: block; overflow: visible; }}
            .sidebar {{ display: none; }}
            .table-container {{ height: auto; overflow: visible; }}
            .grid-head {{ display: none; }}
            .grid-row {{ display: flex; flex-direction: column; gap: 8px; }}
            .group-header {{ top: 0; }}
        }}
    </style>
</head>
<body>

<div class="app-header">
    <div class="brand"><i class="fa-solid fa-layer-group"></i> LICITACIONES EUSKADI</div>
    
    <div class="search-wrap">
        <i class="fa-solid fa-magnifying-glass search-icon"></i>
        <input type="text" class="search-inp" id="search" placeholder="Buscar expediente, objeto..." onkeyup="renderTable()">
    </div>

    <div class="main-nav">
        <div class="nav-btn active" onclick="setCat('obras', this)">OBRAS</div>
        <div class="nav-btn" onclick="setCat('servicios', this)">SERVICIOS</div>
        <div class="nav-btn" onclick="setCat('ingenieria', this)">INGENIERÍA</div>
        <div class="nav-btn dash-btn" onclick="toggleDash(this)"><i class="fa-solid fa-chart-pie"></i></div>
    </div>
</div>

<div class="toolbar">
    <div style="display:flex; gap:15px; flex-wrap:wrap">
        <div class="filter-group">
            <div class="fg-label">Estado:</div>
            <div class="chip active" id="st-act" onclick="toggleSt('activo')">ACTIVOS</div>
            <div class="chip c-red" id="st-cer" onclick="toggleSt('cerrado')">CERRADOS</div>
            <div class="chip c-org" id="st-red" onclick="toggleSt('redaccion')">REDACCIÓN</div>
            <div class="chip c-gry" id="st-sus" onclick="toggleSt('suspendido')">SUSP.</div>
        </div>
        
        <div class="filter-group">
            <div class="fg-label">Ref. Fecha:</div>
            <div class="switch-wrap">
                <div class="sw-opt active" id="d-prim" onclick="setDateRef('primera')">1ª PUB</div>
                <div class="sw-opt" id="d-ult" onclick="setDateRef('ultima')">ÚLTIMA</div>
            </div>
        </div>

        <div class="filter-group">
            <div class="fg-label">Tiempo:</div>
            <div class="chip" id="t-24h" onclick="toggleTime('24h')">24H</div>
            <div class="chip" id="t-week" onclick="toggleTime('week')">SEMANA</div>
        </div>
    </div>

    <div style="display:flex; align-items:center; gap:10px">
        <div class="meta-info">Act: {fecha_actual_str}</div>
        <div class="action-icon" onclick="location.reload()"><i class="fa-solid fa-rotate"></i></div>
        <div class="action-icon" onclick="window.print()"><i class="fa-solid fa-print"></i></div>
    </div>
</div>

<div class="app-body">
    <div class="sidebar">
        <div class="sb-head">Filtros Rápidos</div>
        <div class="sb-scroll" id="sb-content"></div>
    </div>

    <div class="content">
        <div id="table-wrapper" style="display:flex; flex-direction:column; height:100%">
            <div class="table-stats">
                <div class="stat-card active" onclick="setSbMode('ads')">
                    <div class="stat-val" id="k-cnt">0</div>
                    <div class="stat-lbl">Licitaciones</div>
                </div>
                <div class="stat-card" onclick="setSbMode('ent')">
                    <div class="stat-val" id="k-ent">0</div>
                    <div class="stat-lbl">Entidades</div>
                </div>
                <div class="stat-card" onclick="setSbMode('money')">
                    <div class="stat-val" id="k-eur">0 €</div>
                    <div class="stat-lbl">Importe Total</div>
                </div>
            </div>

            <div class="table-container">
                <div class="grid-head">
                    <div>DESCRIPCIÓN / EXPEDIENTE</div>
                    <div>1ª PUBLICACIÓN</div>
                    <div>ÚLT. ACTUALIZACIÓN</div>
                    <div>FECHA LÍMITE</div>
                    <div style="text-align:right">IMPORTE (S/IVA)</div>
                    <div style="text-align:center">DÍAS</div>
                    <div style="text-align:center">LINK</div>
                </div>
                <div id="list-target"></div>
            </div>
        </div>

        <div id="dashboard-view">
            <div class="dash-grid">
                <div class="d-card" style="grid-column: span 2">
                    <h3>Volumen por Entidad</h3>
                    <div style="height:250px"><canvas id="c-ent"></canvas></div>
                </div>
                <div class="d-card">
                    <h3>Por Zonas</h3>
                    <div style="height:250px"><canvas id="c-zone"></canvas></div>
                </div>
                <div class="d-card" style="grid-column: span 3">
                    <h3>Rangos de Presupuesto</h3>
                    <div style="height:200px"><canvas id="c-range"></canvas></div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    const RAW_DATA = {datos_json};
    
    // STATE
    let state = {{
        cat: 'obras',
        statuses: ['activo'],
        dateRef: 'primera', // 'primera' | 'ultima'
        timeFilter: null,   // '24h' | 'week' | null
        sbMode: 'ads',      // 'ads' | 'ent' | 'money'
        activeFilter: null  // {{type: 'entity'|'price', value: ...}}
    }};

    // --- CORE LOGIC ---
    function getFilteredData() {{
        // 1. Cat & Status
        let d = RAW_DATA.filter(x => x.categoria === state.cat && state.statuses.includes(x.estado));
        
        // 2. Time Filter
        if(state.timeFilter) {{
            let cutoff = new Date();
            cutoff.setDate(cutoff.getDate() - (state.timeFilter === '24h' ? 1 : 7));
            d = d.filter(x => {{
                let targetDate = state.dateRef === 'primera' ? x.primera_pub : x.publicado;
                return new Date(targetDate) >= cutoff;
            }});
        }}

        // 3. Search
        let q = document.getElementById('search').value.toLowerCase();
        if(q) d = d.filter(x => x.objeto.toLowerCase().includes(q) || x.entidad.toLowerCase().includes(q) || x.expediente.toLowerCase().includes(q));

        // 4. Sidebar Filter
        if(state.activeFilter) {{
            if(state.activeFilter.type === 'entity') d = d.filter(x => x.entidad === state.activeFilter.value);
            if(state.activeFilter.type === 'price') {{
                let p = x => x.presupuesto_num;
                let v = state.activeFilter.value;
                if(v === 'u100') d = d.filter(x => p(x) < 100000);
                if(v === 'u500') d = d.filter(x => p(x) >= 100000 && p(x) < 500000);
                if(v === 'o500') d = d.filter(x => p(x) >= 500000);
            }}
        }}

        return d;
    }}

    // --- UI ACTIONS ---
    function setCat(c, el) {{
        state.cat = c;
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        el.classList.add('active');
        setView('table');
        refresh();
    }}

    function toggleSt(st) {{
        let idx = state.statuses.indexOf(st);
        let btn = document.getElementById('st-'+st.substring(0,3));
        
        if(idx > -1) {{
            if(state.statuses.length > 1) {{ state.statuses.splice(idx, 1); btn.classList.remove('active'); }}
        }} else {{
            state.statuses.push(st); btn.classList.add('active');
        }}
        refresh();
    }}

    function setDateRef(ref) {{
        state.dateRef = ref;
        document.getElementById('d-prim').className = ref==='primera' ? 'sw-opt active' : 'sw-opt';
        document.getElementById('d-ult').className = ref==='ultima' ? 'sw-opt active' : 'sw-opt';
        refresh();
    }}

    function toggleTime(tf) {{
        state.timeFilter = (state.timeFilter === tf) ? null : tf;
        document.getElementById('t-24h').className = state.timeFilter==='24h' ? 'chip active' : 'chip';
        document.getElementById('t-week').className = state.timeFilter==='week' ? 'chip active' : 'chip';
        refresh();
    }}

    function setSbMode(m) {{ state.sbMode = m; state.activeFilter = null; renderSidebar(); }}
    
    function applyFilter(t, v) {{ state.activeFilter = {{type:t, value:v}}; refresh(); }}

    function toggleDash(el) {{
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        el.classList.add('active');
        setView('dash');
    }}

    function setView(v) {{
        document.getElementById('table-wrapper').style.display = v==='table' ? 'flex' : 'none';
        document.getElementById('dashboard-view').style.display = v==='dash' ? 'block' : 'none';
        if(v === 'dash') renderCharts();
    }}

    // --- RENDERERS ---
    function refresh() {{
        let data = getFilteredData();
        
        // KPIs
        document.getElementById('k-cnt').innerText = data.length;
        document.getElementById('k-ent').innerText = [...new Set(data.map(x=>x.entidad))].length;
        document.getElementById('k-eur').innerText = new Intl.NumberFormat('de-DE', {{ maximumFractionDigits: 0 }}).format(data.reduce((a,b)=>a+b.presupuesto_num,0)) + ' €';

        renderSidebar();
        renderTable(data);
    }}

    function renderSidebar() {{
        let sb = document.getElementById('sb-content'); sb.innerHTML = '';
        let data = getFilteredData(); // Use filtered data context? Or global? usually filtered context is better
        
        if(state.sbMode === 'ads') {{
            sb.innerHTML = `<div class="sb-item active" onclick="applyFilter(null,null)"><div>Todos los anuncios</div><div class="sb-badge">${{data.length}}</div></div>`;
        }}
        else if(state.sbMode === 'ent') {{
            let c = {{}}; data.forEach(x => c[x.entidad] = (c[x.entidad]||0)+1);
            Object.entries(c).sort((a,b)=>b[1]-a[1]).forEach(([k,v]) => {{
                let cls = state.activeFilter?.value === k ? 'active' : '';
                sb.innerHTML += `<div class="sb-item ${{cls}}" onclick="applyFilter('entity','${{k}}')"><div>${{k}}</div><div class="sb-badge">${{v}}</div></div>`;
            }});
        }}
        else if(state.sbMode === 'money') {{
            sb.innerHTML += `<div class="sb-item" onclick="applyFilter('price','u100')"><div>< 100k €</div></div>`;
            sb.innerHTML += `<div class="sb-item" onclick="applyFilter('price','u500')"><div>100k - 500k €</div></div>`;
            sb.innerHTML += `<div class="sb-item" onclick="applyFilter('price','o500')"><div>> 500k €</div></div>`;
        }}
    }}

    function renderTable(data) {{
        let tgt = document.getElementById('list-target'); tgt.innerHTML = '';
        if(data.length === 0) {{ tgt.innerHTML = '<div style="padding:40px; text-align:center; color:#9ca3af">No hay resultados</div>'; return; }}

        // Group by Entity
        let grp = {{}}; data.forEach(x => {{ if(!grp[x.entidad]) grp[x.entidad]=[]; grp[x.entidad].push(x); }});
        
        // Sort Groups by total amount
        let sortedEnts = Object.keys(grp).sort((a,b) => {{
            let sumA = grp[a].reduce((s,x)=>s+x.presupuesto_num,0);
            let sumB = grp[b].reduce((s,x)=>s+x.presupuesto_num,0);
            return sumB - sumA;
        }});

        sortedEnts.forEach(ent => {{
            let rows = grp[ent];
            let total = rows.reduce((s,x)=>s+x.presupuesto_num,0);
            
            let html = `<div class="group-header" onclick="this.nextElementSibling.hidden = !this.nextElementSibling.hidden">
                <span>${{ent}}</span> <span>${{rows.length}} exp | ${{new Intl.NumberFormat('de-DE').format(total)}} €</span>
            </div><div class="group-body">`;
            
            rows.forEach(r => {{
                let badge = 'bd-act';
                if(r.estado==='cerrado') badge='bd-cer';
                if(r.estado==='redaccion') badge='bd-red';
                if(r.estado==='suspendido') badge='bd-sus';

                html += `<div class="grid-row">
                    <div class="row-main">
                        <div class="row-meta"><span class="badge ${{badge}}">${{r.estado}}</span> ${{(r.expediente||'--')}}</div>
                        <div class="row-title">${{r.objeto}}</div>
                    </div>
                    <div class="row-date">${{r.primera_pub_fmt}}</div>
                    <div class="row-date">${{r.publicado_fmt}}</div>
                    <div class="row-date" style="font-weight:600">${{r.limite_fmt}}</div>
                    <div class="row-money">${{r.presupuesto_txt}}</div>
                    <div style="text-align:center; font-weight:700">${{r.dias_restantes > -1 ? r.dias_restantes : '-'}}</div>
                    <div class="action-link"><a href="${{r.link}}" target="_blank"><i class="fa-solid fa-eye"></i></a></div>
                </div>`;
            }});
            html += `</div>`;
            tgt.innerHTML += html;
        }});
    }}

    let charts = [];
    function renderCharts() {{
        charts.forEach(c => c.destroy()); charts = [];
        let data = getFilteredData();
        
        // Entidades
        let ec = {{}}; data.forEach(x => ec[x.entidad] = (ec[x.entidad]||0)+x.presupuesto_num);
        let sorted = Object.entries(ec).sort((a,b)=>b[1]-a[1]).slice(0,10);
        
        charts.push(new Chart(document.getElementById('c-ent'), {{
            type: 'bar',
            data: {{ labels: sorted.map(x=>x[0].substring(0,15)+'...'), datasets: [{{ label:'Volumen (€)', data: sorted.map(x=>x[1]), backgroundColor:'#3b82f6' }}] }},
            options: {{ indexAxis: 'y', maintainAspectRatio: false }}
        }}));

        // Zonas
        let zc = {{}}; data.forEach(x => zc[x.grupo_fav] = (zc[x.grupo_fav]||0)+1);
        charts.push(new Chart(document.getElementById('c-zone'), {{
            type: 'doughnut',
            data: {{ labels: Object.keys(zc), datasets: [{{ data: Object.values(zc), backgroundColor: ['#3b82f6','#10b981','#f59e0b','#ef4444','#6b7280'] }}] }},
            options: {{ maintainAspectRatio: false }}
        }}));
        
        // Rangos
        let ranges = {{'<100k':0, '100k-1M':0, '>1M':0}};
        data.forEach(x => {{
            if(x.presupuesto_num < 100000) ranges['<100k']++;
            else if(x.presupuesto_num < 1000000) ranges['100k-1M']++;
            else ranges['>1M']++;
        }});
        charts.push(new Chart(document.getElementById('c-range'), {{
            type: 'bar',
            data: {{ labels: Object.keys(ranges), datasets: [{{ label:'Expedientes', data: Object.values(ranges), backgroundColor:'#8b5cf6' }}] }},
            options: {{ maintainAspectRatio: false }}
        }}));
    }}

    // Init
    refresh();
</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f: f.write(html_content)
print("✅ V54 Generada: Interfaz limpia y lógica robusta.")
