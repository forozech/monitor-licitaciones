# ==============================================================================
# LICITACIONES EUSKADI - V51 (COMPACT HEADER + FULL DASHBOARD RESTORED)
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

# --- CONFIGURACIÓN DE URLS (MISMAS QUE V50) ---
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

print(f"🚀 INICIANDO V51 ({fecha_actual_str})")

for source in SOURCES:
    tipo_origen = source["type"]
    estado_rss = source["status"]
    print(f"   > Procesando {tipo_origen.upper()} [{estado_rss.upper()}]...")
    
    try:
        response = requests.get(source["url"], headers=HEADERS, timeout=45, verify=False)
        
        if response.status_code != 200:
            print(f"    ⚠️ Error HTTP {response.status_code}")
            continue

        soup_rss = BeautifulSoup(response.content, 'xml')
        items = soup_rss.find_all('item')[:LIMIT_PER_SOURCE]
        print(f"      ✅ {len(items)} items encontrados.")

        for i, item in enumerate(items):
            link = item.link.text
            titulo = item.title.text
            
            # Categoría
            categoria = tipo_origen
            if tipo_origen == "servicios" and es_ingenieria(titulo):
                categoria = "ingenieria"

            try:
                pub_dt = parsedate_to_datetime(item.pubDate.text)
                fecha_rss = pub_dt.strftime("%d/%m/%Y")
                fecha_rss_iso = pub_dt.strftime("%Y-%m-%d")
            except:
                fecha_rss = datetime.now().strftime("%d/%m/%Y")
                fecha_rss_iso = datetime.now().strftime("%Y-%m-%d")

            entidad = "Consultar detalle"
            presupuesto = 0.0
            fecha_limite = None
            expediente = "---"
            logo_url = "https://cdn-icons-png.flaticon.com/512/4300/4300058.png"
            
            fecha_primera_pub = fecha_rss
            fecha_primera_pub_iso = fecha_rss_iso

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
                        parent = target_fecha.parent
                        next_el = parent.find_next_sibling('div') or parent.find_next_sibling('dd')
                        if next_el: fecha_limite = next_el.text.strip().split(' ')[0]

                    target_presu = s_det.find(string=re.compile(r"Presupuesto del contrato sin IVA", re.IGNORECASE))
                    if target_presu:
                        parent = target_presu.parent
                        next_el = parent.find_next_sibling('div') or parent.find_next_sibling('dd')
                        if next_el: presupuesto = limpiar_precio(next_el.text)

                    target_entidad = s_det.find(string=re.compile(r"Poder adjudicador", re.IGNORECASE))
                    if target_entidad:
                        parent = target_entidad.parent
                        next_el = parent.find_next_sibling('div') or parent.find_next_sibling('dd')
                        if next_el: entidad = next_el.text.strip()
                        
                    target_exp = s_det.find(string=re.compile(r"Expediente", re.IGNORECASE))
                    if target_exp:
                        parent = target_exp.parent
                        next_el = parent.find_next_sibling('div') or parent.find_next_sibling('dd')
                        if next_el: expediente = next_el.text.strip()

                    target_fpub = s_det.find(string=re.compile(r"Fecha de publicaci.n del anuncio", re.IGNORECASE))
                    if target_fpub:
                         parent = target_fpub.parent
                         next_el = parent.find_next_sibling('div') or parent.find_next_sibling('dd')
                         if next_el:
                             raw_date = next_el.text.strip().split(' ')[0]
                             try:
                                 dt_prim = datetime.strptime(raw_date, "%d/%m/%Y")
                                 fecha_primera_pub = dt_prim.strftime("%d/%m/%Y")
                                 fecha_primera_pub_iso = dt_prim.strftime("%Y-%m-%d")
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

            obj = {
                "id": len(datos_finales),
                "categoria": categoria,
                "estado": estado_rss,
                "entidad": entidad,
                "objeto": titulo.replace('"', "'"),
                "presupuesto_num": presupuesto,
                "presupuesto_txt": presu_txt,
                "limite": limite_iso,
                "limite_fmt": fecha_limite,
                "publicado": fecha_rss_iso,
                "publicado_fmt": fecha_rss,
                "primera_pub": fecha_primera_pub_iso,
                "primera_pub_fmt": fecha_primera_pub,
                "dias_restantes": dias,
                "expediente": expediente,
                "grupo_fav": zona,
                "logo": logo_url,
                "link": link
            }
            datos_finales.append(obj)

    except Exception as e:
        print(f"❌ Error en {tipo_origen}: {e}")

datos_json = json.dumps(datos_finales)

# --- HTML TEMPLATE (V51 - COMPACT HEADER + RESTORED DASHBOARD) ---
html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LICITACIONES V51</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{ --primary: #2563eb; --bg: #f8fafc; --text-main: #0f172a; --grid-layout: 1fr 90px 90px 90px 130px 110px 50px; }}
        * {{ box-sizing: border-box; }}
        body {{ background-color: var(--bg); font-family: 'Inter', sans-serif; margin: 0; padding: 0; color: var(--text-main); overflow: hidden; }}
        
        /* HEADER ULTRA-COMPACTO */
        .app-header {{ height: 60px; background: white; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; padding: 0 15px; z-index: 50; }}
        .header-left {{ display: flex; align-items: center; gap: 15px; }}
        .header-right {{ display: flex; align-items: center; gap: 10px; }}
        
        .app-brand {{ font-weight: 800; font-size: 1.1rem; color: #1e293b; display: flex; align-items: center; gap: 8px; white-space: nowrap; margin-right: 10px; }}
        
        /* NAVIGATION */
        .nav-pills {{ display: flex; gap: 4px; background: #f1f5f9; padding: 3px; border-radius: 6px; margin-right: 10px; }}
        .nav-item {{ padding: 5px 10px; border-radius: 5px; font-size: 0.8rem; font-weight: 600; cursor: pointer; color: #64748b; transition: all 0.2s; white-space: nowrap; }}
        .nav-item:hover {{ color: #0f172a; background: rgba(255,255,255,0.5); }}
        .nav-item.active {{ background: white; color: var(--primary); box-shadow: 0 1px 2px rgba(0,0,0,0.1); }}
        .nav-item.dashboard-tab {{ color: #7c3aed; }}
        .nav-item.dashboard-tab.active {{ background: #7c3aed; color: white; }}

        /* COMPACT FILTERS */
        .filters-container {{ display: flex; align-items: center; gap: 8px; border-left: 1px solid #e2e8f0; padding-left: 15px; height: 36px; }}
        .f-divider {{ width: 1px; height: 20px; background: #e2e8f0; margin: 0 2px; }}

        .tiny-chip {{ padding: 3px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-size: 0.7rem; font-weight: 700; cursor: pointer; background: white; color: #64748b; transition: 0.2s; white-space: nowrap; }}
        .tiny-chip:hover {{ border-color: #cbd5e1; color: #0f172a; }}
        .tiny-chip.active {{ background: #eff6ff; border-color: var(--primary); color: var(--primary); }}
        
        /* Colores Específicos Chips */
        .tc-red.active {{ background: #fef2f2; border-color: #ef4444; color: #ef4444; }}
        .tc-org.active {{ background: #fff7ed; border-color: #f97316; color: #f97316; }}
        .tc-gry.active {{ background: #f1f5f9; border-color: #64748b; color: #334155; }}

        /* Switch Fechas */
        .date-switch {{ display: flex; background: #e2e8f0; border-radius: 4px; padding: 2px; }}
        .ds-opt {{ padding: 2px 6px; font-size: 0.65rem; font-weight: 700; color: #64748b; cursor: pointer; border-radius: 3px; }}
        .ds-opt.active {{ background: white; color: #0f172a; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }}

        /* Utility Buttons */
        .util-btn {{ width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border: 1px solid #e2e8f0; border-radius: 6px; cursor: pointer; color: #475569; background: white; font-size: 0.9rem; }}
        .util-btn:hover {{ color: #0f172a; border-color: #cbd5e1; }}
        .btn-pdf {{ background: #1e293b; color: white; border: none; }}
        .btn-pdf:hover {{ background: #334155; }}

        /* LAYOUT GENERAL */
        .app-container {{ display: flex; height: calc(100vh - 60px); width: 100vw; }}
        .sidebar {{ width: 280px; background: #ffffff; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; padding: 20px 0; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; background: #f1f5f9; position: relative; overflow: hidden; }}
        .mobile-toggle {{ display: none; font-size: 1.2rem; color: #64748b; cursor: pointer; padding: 5px; }}

        /* SIDEBAR (Igual V50) */
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
        .ver-todo {{ background: #eff6ff; color: var(--primary); border: 1px solid #dbeafe; border-radius: 6px; padding: 10px; margin-bottom: 15px; text-align: center; font-weight: 700; cursor: pointer; }}
        .filter-row {{ display: flex; justify-content: space-between; align-items: center; padding: 7px 12px; font-size: 0.85rem; color: #475569; font-weight: 500; cursor: pointer; border-radius: 6px; border-left: 3px solid transparent; }}
        .filter-row.active {{ background: #eff6ff; color: var(--primary); font-weight: 600; border-left-color: var(--primary); }}

        /* LIST & TABLE */
        .top-deck {{ background: white; padding: 15px 30px; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; }}
        .kpi-row {{ display: flex; gap: 15px; margin-bottom: 15px; }}
        .kpi-box {{ flex: 1; padding: 15px; border-radius: 10px; background: #f8fafc; border: 1px solid transparent; cursor: pointer; }}
        .kpi-box.active {{ background: white; border-color: currentColor; }}
        .k-blue {{ color: #1e40af; border-color: #dbeafe; background: #eff6ff; }}
        .k-green {{ color: #065f46; border-color: #d1fae5; background: #ecfdf5; }}
        .kpi-val {{ font-size: 1.5rem; font-weight: 800; }}
        .kpi-lbl {{ font-size: 0.7rem; font-weight: 700; text-transform: uppercase; opacity: 0.8; }}
        .toolbar {{ display: flex; gap: 20px; align-items: center; justify-content: space-between; }}
        .search-box {{ flex: 1; max-width: 400px; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 6px; outline: none; }}
        
        #table-wrapper {{ display: flex; flex-direction: column; height: 100%; overflow: hidden; }}
        .grid-header {{ display: grid; grid-template-columns: var(--grid-layout); gap: 10px; padding: 10px 30px; background: #e2e8f0; font-size: 0.7rem; font-weight: 800; color: #475569; user-select: none; flex-shrink: 0; }}
        .gh-cell {{ cursor: pointer; display: flex; align-items: center; gap: 5px; }}
        .list-container {{ flex: 1; overflow-y: auto; padding: 0; }}
        .list-inner {{ padding: 20px 30px; }}
        
        .entity-group {{ margin-bottom: 15px; background: white; border-radius: 8px; border: 1px solid #e2e8f0; overflow: hidden; }}
        .eg-title-row {{ background: #f8fafc; padding: 8px 20px; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; cursor: pointer; }}
        .eg-info {{ display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 0.95rem; }}
        .eg-logo {{ height: 30px; width: 30px; object-fit: contain; mix-blend-mode: multiply; }}
        .eg-chevron {{ transition: transform 0.3s; color: #94a3b8; }}
        .entity-group.collapsed .eg-chevron {{ transform: rotate(-90deg); }}
        .entity-group.collapsed .group-rows {{ display: none; }}
        
        .row-item {{ display: grid; grid-template-columns: var(--grid-layout); gap: 10px; align-items: flex-start; padding: 12px 20px; border-bottom: 1px solid #f1f5f9; font-size: 0.85rem; }}
        .ri-title {{ font-weight: 600; color: #1e293b; }}
        .ri-exp {{ font-size: 0.7rem; color: #64748b; margin-bottom: 3px; display:flex; gap:10px; align-items:center; }}
        
        .st-badge {{ font-size: 0.65rem; font-weight:800; padding:2px 5px; border-radius:3px; text-transform:uppercase; }}
        .st-activo {{ background:#dbeafe; color:#1e40af; }}
        .st-cerrado {{ background:#fee2e2; color:#991b1b; }}
        .st-redaccion {{ background:#ffedd5; color:#9a3412; }}
        .st-suspendido {{ background:#f1f5f9; color:#475569; }}

        .badge {{ text-align: center; font-size: 0.7rem; font-weight: 700; padding: 3px 6px; border-radius: 4px; }}
        .b-red {{ background: #fee2e2; color: #991b1b; }}
        .b-orange {{ background: #ffedd5; color: #9a3412; }}
        .b-green {{ background: #dcfce7; color: #166534; }}
        .b-gray {{ background: #e2e8f0; color: #64748b; }}

        /* DASHBOARD RESTAURADO (Full Layout V49) */
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
        .d-card {{ background: white; border-radius: 16px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); display: flex; flex-direction: column; position: relative; min-height: 0; }}
        .dc-title {{ font-size: 0.95rem; font-weight: 700; color: #334155; margin-bottom: 15px; }}
        .chart-box {{ flex: 1; min-height: 0; position:relative; display: flex; align-items: center; justify-content: center; }}
        .c-span-v {{ grid-row: span 2; }}
        .top-list-container {{ overflow-y: auto; padding-right: 5px; }}
        .top-item {{ display: flex; gap: 10px; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9; font-size: 0.85rem; }}
        .top-item:last-child {{ border: none; }}
        .ti-idx {{ background: #f1f5f9; color: #64748b; font-weight: 700; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; }}
        .ti-info {{ flex: 1; overflow: hidden; }}
        .ti-ent {{ font-weight: 700; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .ti-val {{ font-weight: 600; color: var(--primary); text-align: right; white-space: nowrap; }}
        .ti-desc {{ font-size: 0.75rem; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}

        @media (max-width: 1100px) {{
            .app-container {{ flex-direction: column; height: auto; }}
            .app-header {{ height: auto; flex-direction: column; align-items: flex-start; padding: 10px; gap: 10px; }}
            .header-left {{ width: 100%; justify-content: space-between; }}
            .header-right {{ width: 100%; justify-content: space-between; flex-wrap: wrap; }}
            .filters-container {{ border-left: none; padding-left: 0; overflow-x: auto; width: 100%; padding-bottom: 5px; }}
            
            .sidebar {{ display: none; width: 100%; height: auto; max-height: 400px; }}
            .sidebar.active {{ display: flex; }}
            .mobile-toggle {{ display: block; }}
            .grid-header {{ display: none; }}
            .row-item {{ display: flex; flex-direction: column; gap: 5px; padding: 15px; position: relative; }}
            .row-item > div:last-child {{ position: absolute; top: 15px; right: 15px; }}
            
            .dash-content {{ display: flex; flex-direction: column; }}
            .d-card {{ min-height: 300px; }}
        }}
    </style>
</head>
<body>
<div class="app-header">
    <div class="header-left">
        <div style="display:flex; align-items:center; gap:10px">
            <div class="mobile-toggle" onclick="toggleSidebar()"><i class="fa-solid fa-bars"></i></div>
            <div class="app-brand"><i class="fa-solid fa-layer-group"></i> LICITACIONES</div>
        </div>
        <div class="nav-pills">
            <div class="nav-item active" onclick="switchDataset('obras', this)">OBRAS</div>
            <div class="nav-item" onclick="switchDataset('servicios', this)">SERV.</div>
            <div class="nav-item" onclick="switchDataset('ingenieria', this)">ING.</div>
            <div class="nav-item dashboard-tab" onclick="toggleDashboard(this)"><i class="fa-solid fa-chart-pie"></i></div>
        </div>
    </div>
    
    <div class="header-right">
        <div class="filters-container">
            <div class="tiny-chip active" id="f-st-act" onclick="toggleStatus('activo')">ACT</div>
            <div class="tiny-chip tc-red" id="f-st-cer" onclick="toggleStatus('cerrado')">CER</div>
            <div class="tiny-chip tc-org" id="f-st-red" onclick="toggleStatus('redaccion')">RED</div>
            <div class="tiny-chip tc-gry" id="f-st-sus" onclick="toggleStatus('suspendido')">SUS</div>
            
            <div class="f-divider"></div>
            
            <div class="date-switch">
                <div class="ds-opt active" id="ts-pub" onclick="setDateRef('primera')">1ª PUB</div>
                <div class="ds-opt" id="ts-upd" onclick="setDateRef('ultima')">ÚLT</div>
            </div>
            
            <div class="tiny-chip" id="btn-24h" onclick="toggleTimeFilter('24h')">24H</div>
            <div class="tiny-chip" id="btn-week" onclick="toggleTimeFilter('week')">SEM</div>
        </div>
        
        <div style="display:flex; gap:5px; margin-left:5px">
             <div class="util-btn" id="btn-reload" onclick="reloadData()"><i class="fa-solid fa-rotate"></i></div>
             <button class="util-btn btn-pdf" onclick="window.print()"><i class="fa-solid fa-file-pdf"></i></button>
        </div>
    </div>
</div>

<div class="app-container">
    <div class="sidebar" id="main-sidebar">
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
                    <div class="kpi-box k-green" onclick="setMode('entities', this)">
                        <div class="kpi-val" id="k-ent">0</div>
                        <div class="kpi-lbl">Entidades</div>
                    </div>
                    <div class="kpi-box" style="background:#f3f4f6; color:#4b5563" onclick="setMode('money', this)">
                        <div class="kpi-val" id="k-money">0 €</div>
                        <div class="kpi-lbl">Total</div>
                    </div>
                </div>
                <div class="toolbar">
                    <input type="text" class="search-box" id="search" placeholder="Buscar expediente, objeto..." onkeyup="renderTable()">
                    <div style="font-size:0.75rem; color:#94a3b8; font-weight:600">{fecha_actual_str}</div>
                </div>
            </div>
            <div class="grid-header">
                <div class="gh-cell" onclick="setSort('objeto')">DESCRIPCIÓN <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell" onclick="setSort('primera_pub')">1ª PUB <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell" onclick="setSort('publicado')">ÚLTIMA <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell" onclick="setSort('limite')">LÍMITE <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell" style="justify-content:flex-end" onclick="setSort('presupuesto_num')">IMPORTE <i class="fa-solid fa-sort"></i></div>
                <div class="gh-cell" style="justify-content:center" onclick="setSort('dias_restantes')">ESTADO <i class="fa-solid fa-sort"></i></div>
                <div style="text-align:center">VER</div>
            </div>
            <div id="list-view" class="list-container">
                <div id="list-inner" class="list-inner"></div>
            </div>
        </div>
        
        <div id="dashboard-view">
            <div class="dashboard-container">
                <div class="dash-kpis">
                    <div class="kpi-modern km-1"><span class="kpi-m-label">Volumen Visible</span><div class="kpi-m-val" id="dm-vol">0 €</div></div>
                    <div class="kpi-modern km-2"><span class="kpi-m-label">Expedientes</span><div class="kpi-m-val" id="dm-num">0</div></div>
                    <div class="kpi-modern km-3"><span class="kpi-m-label">Presupuesto Medio</span><div class="kpi-m-val" id="dm-avg">0 €</div></div>
                </div>
                <div class="dash-content">
                    <div class="d-card"><div class="dc-title">Por Zona</div><div class="chart-box"><canvas id="chartZone"></canvas></div></div>
                    <div class="d-card"><div class="dc-title">Top Entidades</div><div class="chart-box"><canvas id="chartEnt"></canvas></div></div>
                    <div class="d-card c-span-v"><div class="dc-title">Top Oportunidades</div><div class="top-list-container" id="top-opps-list"></div></div>
                    <div class="d-card" style="grid-column: span 2"><div class="dc-title">Rangos de Presupuesto</div><div class="chart-box"><canvas id="chartRanges" style="max-height:100%"></canvas></div></div>
                </div>
            </div>
        </div>
    </div>
</div>

<script>
    const allData = {datos_json};
    
    // ESTADO DE LA APP
    let currentCategory = 'obras';
    let activeStatuses = ['activo']; 
    let dateRef = 'primera'; 
    let timeFilter = null; 
    
    let sidebarMode = 'ads'; 
    let activeFilter = {{ type: 'none', value: null }}; 
    let sortField = 'publicado'; 
    let sortDir = 'desc'; 
    let chartInstances = [];
    
    // --- LÓGICA DE DATOS ---
    function getData() {{
        let d = allData.filter(x => x.categoria === currentCategory);
        d = d.filter(x => activeStatuses.includes(x.estado));
        
        if (timeFilter) {{
            let now = new Date();
            let limit = new Date();
            if (timeFilter === '24h') limit.setDate(now.getDate() - 1);
            if (timeFilter === 'week') limit.setDate(now.getDate() - 7);
            
            d = d.filter(x => {{
                let dateStr = dateRef === 'primera' ? x.primera_pub : x.publicado;
                let itemDate = new Date(dateStr);
                return itemDate >= limit;
            }});
        }}
        return d;
    }}

    // --- INTERFAZ & ACCIONES ---
    function switchDataset(cat, el) {{ 
        currentCategory = cat; 
        document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active')); 
        if(el) el.classList.add('active'); 
        resetView();
    }}
    
    function toggleStatus(st) {{
        const btn = document.getElementById('f-st-'+st.substring(0,3));
        if(activeStatuses.includes(st)) {{
            if(activeStatuses.length > 1) {{
                activeStatuses = activeStatuses.filter(x => x !== st);
                btn.classList.remove('active');
            }}
        }} else {{
            activeStatuses.push(st);
            btn.classList.add('active');
        }}
        updateKPIs(); renderSidebar(); renderTable();
    }}
    
    function setDateRef(ref) {{
        dateRef = ref;
        document.getElementById('ts-pub').classList.toggle('active', ref === 'primera');
        document.getElementById('ts-upd').classList.toggle('active', ref === 'ultima');
        if(timeFilter) {{ updateKPIs(); renderSidebar(); renderTable(); }}
    }}
    
    function toggleTimeFilter(tf) {{
        if(timeFilter === tf) timeFilter = null; 
        else timeFilter = tf;
        
        document.getElementById('btn-24h').classList.toggle('active', timeFilter === '24h');
        document.getElementById('btn-week').classList.toggle('active', timeFilter === 'week');
        updateKPIs(); renderSidebar(); renderTable();
    }}
    
    function reloadData() {{
        const btn = document.getElementById('btn-reload'); btn.querySelector('i').classList.add('fa-spin');
        setTimeout(() => {{ window.location.href = window.location.href; }}, 500);
    }}

    function resetView() {{
        document.getElementById('dashboard-view').style.display = 'none'; 
        document.getElementById('table-wrapper').style.display = 'flex';
        activeFilter = {{ type: 'none', value: null }};
        updateKPIs(); renderSidebar(); renderTable();
    }}

    function toggleDashboard(el) {{
        document.querySelectorAll('.nav-item').forEach(x => x.classList.remove('active'));
        el.classList.add('active');
        document.getElementById('table-wrapper').style.display = 'none';
        document.getElementById('dashboard-view').style.display = 'block';
        if(window.innerWidth <= 1100) document.querySelector('.sidebar').style.display = 'none';
        renderDashboard();
    }}
    
    function setMode(mode, el) {{ 
        sidebarMode = mode; 
        document.querySelectorAll('.kpi-box').forEach(x => x.classList.remove('active')); 
        if(el) el.classList.add('active'); 
        activeFilter = {{ type: 'none', value: null }}; 
        renderSidebar(); renderTable(); 
    }}
    
    function applyFilter(type, val) {{ activeFilter = {{ type: type, value: val }}; renderSidebar(); renderTable(); if(window.innerWidth <= 1100) toggleSidebar(); }}
    function toggleSidebar() {{ document.getElementById('main-sidebar').classList.toggle('active'); }}
    function setSort(field) {{ if(sortField === field) sortDir = sortDir === 'asc' ? 'desc' : 'asc'; else {{ sortField = field; sortDir = 'desc'; }} renderTable(); }}
    function toggleGroup(header) {{ header.parentElement.classList.toggle('collapsed'); }}

    // --- RENDERIZADO ---
    function updateKPIs() {{ 
        const data = getData(); 
        document.getElementById('k-count').innerText = data.length; 
        document.getElementById('k-ent').innerText = [...new Set(data.map(d=>d.entidad))].length; 
        const total = data.reduce((a,b)=>a+b.presupuesto_num,0); 
        document.getElementById('k-money').innerText = formatMoney(total); 
    }}
    
    function formatMoney(amount) {{ return new Intl.NumberFormat('de-DE', {{ style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }}).format(amount); }}

    function renderSidebar() {{
        const sb = document.getElementById('sidebar-content'); sb.innerHTML = ''; const data = getData();
        if (sidebarMode === 'ads') {{ sb.innerHTML = `<div class="sb-title">VISTA GENERAL</div><div class="filter-row active"><span>Todos los Registros</span></div>`; }} 
        else if (sidebarMode === 'entities') {{
            sb.innerHTML = `<div class="sb-title">ENTIDADES</div>`;
            let uniqueEnts = {{}}; data.forEach(d => {{ if(!uniqueEnts[d.entidad]) uniqueEnts[d.entidad] = {{count:0, logo: d.logo, zone: d.grupo_fav}}; uniqueEnts[d.entidad].count++; }});
            let zonesList = {{}}; for(let ent in uniqueEnts) {{ let z = uniqueEnts[ent].zone; if(!zonesList[z]) zonesList[z] = []; zonesList[z].push({{name: ent, ...uniqueEnts[ent]}}); }}
            const priority = ["Añarbe", "Txingudi", "Diputación", "Donostialdea", "Otros"]; let sortedZones = Object.keys(zonesList).sort((a, b) => {{ let ia = priority.indexOf(a); let ib = priority.indexOf(b); if (ia === -1) ia = 99; if (ib === -1) ib = 99; return ia - ib; }});
            sortedZones.forEach(z => {{ sb.innerHTML += `<div style="padding:5px 10px; font-weight:800; color:#cbd5e1; font-size:0.7rem; margin-top:15px; text-transform:uppercase">${{z}}</div>`; zonesList[z].sort((a,b) => b.count - a.count); zonesList[z].forEach(obj => {{ let active = (activeFilter.type === 'entity' && activeFilter.value === obj.name) ? 'active' : ''; let nameClean = obj.name.replace('Ayuntamiento', 'Ayto'); sb.innerHTML += `<div class="ent-card ${{active}}" onclick="applyFilter('entity', '${{obj.name}}')"><img src="${{obj.logo}}" class="ent-img"><div class="ent-name">${{nameClean}}</div><div class="ent-badge">${{obj.count}}</div></div>`; }}); }});
        }} else if (sidebarMode === 'money') {{
             sb.innerHTML = `<div class="sb-title">RANGO DE PRESUPUESTO</div><div class="ver-todo" onclick="setMode('ads');"><i class="fa-regular fa-circle-check"></i> Ver Todo</div>`;
             let ranges = [ {{l:'< 50.000 €', v:'u50', style:'rc-green'}}, {{l:'< 100k €', v:'u100', style:'rc-green'}}, {{l:'< 400k €', v:'u400', style:'rc-blue'}}, {{l:'< 1M €', v:'u1m', style:'rc-orange'}}, {{l:'> 1M €', v:'o2m', style:'rc-purple'}} ];
             ranges.forEach(r => {{ let active = (activeFilter.type === 'price' && activeFilter.value === r.v) ? 'active' : ''; sb.innerHTML += `<div class="range-card ${{r.style}} ${{active}}" onclick="applyFilter('price', '${{r.v}}')"><span>${{r.l}}</span><i class="fa-solid fa-chevron-right"></i></div>`; }});
        }}
    }}

    function renderTable() {{
        const container = document.getElementById('list-inner'); container.innerHTML = ""; const search = document.getElementById('search').value.toLowerCase();
        let data = getData().filter(d => {{ 
            let matchText = d.objeto.toLowerCase().includes(search) || d.expediente.toLowerCase().includes(search); 
            let matchFilter = true; 
            if (activeFilter.type === 'entity') matchFilter = d.entidad === activeFilter.value; 
            if (activeFilter.type === 'price') {{ 
                if(activeFilter.value === 'u50') matchFilter = d.presupuesto_num < 50000; 
                else if(activeFilter.value === 'u100') matchFilter = d.presupuesto_num < 100000; 
                else if(activeFilter.value === 'u400') matchFilter = d.presupuesto_num < 400000; 
                else if(activeFilter.value === 'u1m') matchFilter = d.presupuesto_num < 1000000; 
                else if(activeFilter.value === 'o2m') matchFilter = d.presupuesto_num >= 1000000; 
            }} 
            return matchText && matchFilter; 
        }});
        
        if(data.length === 0) {{ container.innerHTML = "<div style='text-align:center; padding:40px; color:#94a3b8'>No hay datos con los filtros actuales</div>"; return; }}
        
        let grouped = {{}}; data.forEach(d => {{ if(!grouped[d.entidad]) grouped[d.entidad]=[]; grouped[d.entidad].push(d); }});
        let ents = Object.keys(grouped).sort((a, b) => {{
            let rowsA = grouped[a], rowsB = grouped[b]; 
            let valA, valB;
            if (sortField === 'presupuesto_num') {{ valA = rowsA.reduce((s, x) => s + x.presupuesto_num, 0); valB = rowsB.reduce((s, x) => s + x.presupuesto_num, 0); }} 
            else {{ valA = a.toLowerCase(); valB = b.toLowerCase(); }} 
            
            if(sortField === 'publicado' || sortField === 'primera_pub') return 0; 
            if (typeof valA === 'string') {{ if (valA < valB) return sortDir === 'asc' ? -1 : 1; if (valA > valB) return sortDir === 'asc' ? 1 : -1; return 0; }}
            return sortDir === 'asc' ? valA - valB : valB - valA;
        }});

        ents.forEach(ent => {{
            let rows = grouped[ent]; 
            rows.sort((a,b) => {{ 
                let va = a[sortField], vb = b[sortField]; 
                if (typeof va === 'string') {{ if(va < vb) return sortDir === 'asc' ? -1 : 1; if(va > vb) return sortDir === 'asc' ? 1 : -1; return 0; }} 
                return sortDir === 'asc' ? va - vb : vb - va; 
            }});
            
            let total = rows.reduce((s,x)=>s+x.presupuesto_num,0); let logo = rows[0].logo;
            let html = `<div class="entity-group"><div class="eg-title-row" onclick="toggleGroup(this)"><div class="eg-info"><i class="fa-solid fa-chevron-down eg-chevron"></i><img src="${{logo}}" class="eg-logo"> ${{ent.replace('Ayuntamiento', 'Ayto')}}</div><div style="font-size:0.8rem; font-weight:700; color:#64748b">${{rows.length}} exp. | ${{formatMoney(total)}}</div></div><div class="group-rows">`;
            
            rows.forEach(r => {{
                let badgeClass = 'st-activo';
                if(r.estado === 'cerrado') badgeClass = 'st-cerrado';
                else if(r.estado === 'redaccion') badgeClass = 'st-redaccion';
                else if(r.estado === 'suspendido') badgeClass = 'st-suspendido';
                
                let diasBadge = '';
                if(r.dias_restantes > -1) {{
                    let bg = r.dias_restantes < 7 ? 'b-red' : (r.dias_restantes < 15 ? 'b-orange' : 'b-green');
                    diasBadge = `<span class="badge ${{bg}}">${{r.dias_restantes}} días</span>`;
                }} else {{
                    diasBadge = `<span class="badge b-gray">-</span>`;
                }}

                html += `<div class="row-item">
                    <div>
                        <div class="ri-exp"><span class="st-badge ${{badgeClass}}">${{r.estado}}</span> ${{r.expediente}}</div>
                        <div class="ri-title">${{r.objeto}}</div>
                    </div>
                    <div style="font-size:0.8rem">${{r.primera_pub_fmt}}</div>
                    <div style="font-size:0.8rem">${{r.publicado_fmt}}</div>
                    <div style="font-weight:600; color:#334155">${{r.limite_fmt}}</div>
                    <div style="text-align:right; font-weight:700">${{r.presupuesto_txt}}</div>
                    <div style="display:flex; justify-content:center">${{diasBadge}}</div>
                    <div style="text-align:center"><a href="${{r.link}}" target="_blank" style="color:var(--primary); font-size:1.1rem" title="Ver detalle"><i class="fa-solid fa-eye"></i></a></div>
                </div>`; 
            }});
            html += `</div></div>`; container.innerHTML += html;
        }});
    }}
    
    function renderDashboard() {{
        chartInstances.forEach(c => c.destroy()); chartInstances = []; const data = getData();
        const totalVol = data.reduce((s,x)=>s+x.presupuesto_num, 0); const count = data.length; const avg = count > 0 ? totalVol / count : 0;
        document.getElementById('dm-vol').innerText = formatMoney(totalVol); document.getElementById('dm-num').innerText = count; document.getElementById('dm-avg').innerText = formatMoney(avg);
        
        const zoneCounts = {{}}; data.forEach(d => {{ zoneCounts[d.grupo_fav] = (zoneCounts[d.grupo_fav]||0) + 1 }});
        chartInstances.push(new Chart(document.getElementById('chartZone'), {{ type: 'doughnut', data: {{ labels: Object.keys(zoneCounts), datasets: [{{ data: Object.values(zoneCounts), backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#64748b'], borderWidth: 0 }}] }}, options: {{ maintainAspectRatio: false, plugins: {{ legend: {{ position: 'right' }} }} }} }}));
        
        const entCounts = {{}}; data.forEach(d => {{ entCounts[d.entidad] = (entCounts[d.entidad]||0) + d.presupuesto_num }});
        const sortedEnts = Object.entries(entCounts).sort((a,b)=>b[1]-a[1]).slice(0,5);
        chartInstances.push(new Chart(document.getElementById('chartEnt'), {{ type: 'bar', data: {{ labels: sortedEnts.map(x=>x[0].replace('Ayuntamiento', 'Ayto').substring(0,15)+'...'), datasets: [{{ label: 'Volumen (€)', data: sortedEnts.map(x=>x[1]), backgroundColor: '#3b82f6', borderRadius: 4, barThickness: 20 }}] }}, options: {{ indexAxis: 'y', maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ x: {{ grid: {{ display: false }} }}, y: {{ grid: {{ display: false }} }} }} }} }}));
        
        let ranges = {{ '< 100k':0, '100k-500k':0, '500k-1M':0, '> 1M':0 }}; data.forEach(d => {{ let p = d.presupuesto_num; if(p < 100000) ranges['< 100k']++; else if(p < 500000) ranges['100k-500k']++; else if(p < 1000000) ranges['500k-1M']++; else ranges['> 1M']++; }});
        chartInstances.push(new Chart(document.getElementById('chartRanges'), {{ type: 'bar', data: {{ labels: Object.keys(ranges), datasets: [{{ label: 'Cantidad', data: Object.values(ranges), backgroundColor: ['#94a3b8', '#60a5fa', '#3b82f6', '#1e40af'], borderRadius: 6, barThickness: 30 }}] }}, options: {{ maintainAspectRatio: false, plugins: {{ legend: {{ display: false }} }}, scales: {{ y: {{ beginAtZero: true, grid: {{ color: '#f1f5f9' }} }}, x: {{ grid: {{ display: false }} }} }} }} }}));

        const topList = document.getElementById('top-opps-list'); topList.innerHTML = ''; let sortedAds = [...data].sort((a,b) => b.presupuesto_num - a.presupuesto_num).slice(0, 10);
        sortedAds.forEach((item, idx) => {{ topList.innerHTML += `<div class="top-item"><div class="ti-idx">${{idx+1}}</div><div class="ti-info"><div class="ti-ent">${{item.entidad.replace('Ayuntamiento', 'Ayto')}}</div><div class="ti-desc">${{item.objeto}}</div></div><div class="ti-val">${{item.presupuesto_txt}}</div></div>`; }});
    }}
    
    updateKPIs(); renderSidebar(); renderTable();
</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as file:
    file.write(html_content)

print("✅ Archivo 'index.html' generado con éxito (V51 - Compact Header + Full Dashboard).")
