# ==============================================================================
# MONITOR DE ADJUDICACIONES EUSKADI - V2 (INTERFAZ COMPLETA + BOTÓN WIN)
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURACIÓN DE URLS (Tus nuevos links de adjudicaciones) ---
SOURCES = [
    {"type": "obras", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=5&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
    {"type": "servicios", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=5&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"}
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def limpiar_precio(texto):
    if not texto: return 0.0
    try:
        clean = re.sub(r'[^\d,]', '', texto)
        return float(clean.replace(',', '.'))
    except: return 0.0

datos_analisis = []
print(f"🚀 INICIANDO ANÁLISIS V2...")

for src in SOURCES:
    print(f"   > Escaneando {src['type']}...")
    try:
        res = requests.get(src['url'], headers=HEADERS, verify=False, timeout=30)
        soup_rss = BeautifulSoup(res.content, 'xml')
        items = soup_rss.find_all('item')[:30] 

        for item in items:
            link = item.link.text
            titulo = item.title.text
            ganador = "Desconocido"
            p_base = 0.0
            p_adju = 0.0
            entidad = "Gobierno Vasco" # Valor por defecto
            logo_url = "https://cdn-icons-png.flaticon.com/512/4300/4300058.png"

            try:
                r_det = requests.get(link, headers=HEADERS, verify=False, timeout=15)
                s_det = BeautifulSoup(r_det.content, 'html.parser')
                
                # Buscar en tablas de datos
                for row in s_det.find_all('tr'):
                    header = row.find('th')
                    value = row.find('td')
                    if header and value:
                        txt = header.get_text().lower()
                        val_txt = value.get_text().strip()
                        if "adjudicatario" in txt: ganador = val_txt
                        if "importe de adjudicaci" in txt: p_adju = limpiar_precio(val_txt)
                        if "presupuesto del contrato sin iva" in txt: p_base = limpiar_precio(val_txt)
                        if "poder adjudicador" in txt: entidad = val_txt
                
                # Logo
                img = s_det.find('img', src=re.compile(r"logo"))
                if img: logo_url = "https://www.contratacion.euskadi.eus" + img['src'] if img['src'].startswith('/') else img['src']
            except: pass

            baja = 0.0
            if p_base > 0 and p_adju > 0:
                baja = ((p_base - p_adju) / p_base) * 100

            datos_analisis.append({
                "categoria": src['type'],
                "entidad": entidad,
                "objeto": titulo,
                "ganador": ganador.split('(')[0].strip(), # Limpiar nombres largos
                "presupuesto_num": p_base,
                "adjudicado_num": p_adju,
                "baja": round(baja, 2),
                "logo": logo_url,
                "link": link
            })
            time.sleep(0.5)
    except: pass

datos_json = json.dumps(datos_analisis)

# --- HTML TEMPLATE (Heredando el diseño V49) ---
html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ANÁLISIS DE ADJUDICACIONES</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{ --primary: #2563eb; --bg: #f8fafc; --text-main: #0f172a; --grid-layout: 1fr 140px 140px 100px 60px; }}
        * {{ box-sizing: border-box; }}
        body {{ background-color: var(--bg); font-family: 'Inter', sans-serif; margin: 0; padding: 0; color: var(--text-main); overflow: hidden; }}
        
        .app-header {{ height: 60px; background: white; border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; padding: 0 20px; z-index: 50; position:relative; }}
        .app-brand {{ font-weight: 800; font-size: 1.2rem; color: #1e293b; display: flex; align-items: center; gap: 10px; }}
        .nav-pills {{ display: flex; gap: 5px; background: #f1f5f9; padding: 4px; border-radius: 8px; }}
        .nav-item {{ padding: 6px 15px; border-radius: 6px; font-size: 0.85rem; font-weight: 600; cursor: pointer; color: #64748b; transition: all 0.2s; }}
        .nav-item.active {{ background: white; color: var(--primary); box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        
        .app-container {{ display: flex; height: calc(100vh - 60px); width: 100vw; }}
        .sidebar {{ width: 280px; background: #ffffff; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; padding: 20px 0; overflow-y: auto; }}
        .main-content {{ flex: 1; display: flex; flex-direction: column; background: #f1f5f9; overflow: hidden; }}
        
        .sb-title {{ font-size: 0.7rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin: 15px 25px 8px; }}
        .filter-row {{ display: flex; justify-content: space-between; padding: 10px 25px; font-size: 0.85rem; cursor: pointer; font-weight: 500; }}
        .filter-row.active {{ background: #eff6ff; color: var(--primary); border-left: 3px solid var(--primary); }}
        
        .top-deck {{ background: white; padding: 15px 30px; border-bottom: 1px solid #e2e8f0; }}
        .kpi-row {{ display: flex; gap: 15px; margin-bottom: 15px; }}
        .kpi-box {{ flex: 1; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }}
        .k-blue {{ background: #eff6ff; color: #1e40af; border-color: #dbeafe; }}
        .k-green {{ background: #ecfdf5; color: #065f46; border-color: #d1fae5; }}
        .kpi-val {{ font-size: 1.5rem; font-weight: 800; }}
        
        .grid-header {{ display: grid; grid-template-columns: var(--grid-layout); gap: 10px; padding: 10px 30px; background: #e2e8f0; font-size: 0.7rem; font-weight: 800; color: #475569; }}
        .list-container {{ flex: 1; overflow-y: auto; padding: 20px 30px; }}
        .row-item {{ display: grid; grid-template-columns: var(--grid-layout); gap: 10px; padding: 15px 20px; background: white; border-bottom: 1px solid #f1f5f9; font-size: 0.85rem; align-items: center; }}
        .ri-win {{ font-weight: 700; color: var(--primary); }}
        .baja-pill {{ padding: 4px 8px; border-radius: 6px; font-weight: 800; text-align: center; }}
        .b-verde {{ background: #dcfce7; color: #166534; }}
        .b-naranja {{ background: #ffedd5; color: #9a3412; }}
        .b-roja {{ background: #fee2e2; color: #991b1b; }}
    </style>
</head>
<body>
<div class="app-header">
    <div class="app-brand"><i class="fa-solid fa-trophy"></i> ANÁLISIS</div>
    <div class="nav-pills">
        <div class="nav-item active" onclick="switchCat('obras', this)">OBRAS</div>
        <div class="nav-item" onclick="switchCat('servicios', this)">SERVICIOS</div>
    </div>
    <div class="header-actions">
        <a href="index.html" class="nav-item" style="text-decoration:none">← LICITACIONES</a>
    </div>
</div>
<div class="app-container">
    <div class="sidebar">
        <div class="sb-title">VISTA DE DATOS</div>
        <div class="filter-row active" onclick="setMode('entities', this)"><i class="fa-solid fa-building"></i> ENTIDADES</div>
        <div class="filter-row" onclick="setMode('winners', this)"><i class="fa-solid fa-crown"></i> WIN (GANADORES)</div>
        <div id="sidebar-items"></div>
    </div>
    <div class="main-content">
        <div class="top-deck">
            <div class="kpi-row">
                <div class="kpi-box k-blue">
                    <div class="kpi-val" id="k-total">0 €</div>
                    <div style="font-size:0.7rem; font-weight:700">VOLUMEN TOTAL</div>
                </div>
                <div class="kpi-box k-green">
                    <div class="kpi-val" id="k-baja">0 %</div>
                    <div style="font-size:0.7rem; font-weight:700">BAJA MEDIA</div>
                </div>
            </div>
            <input type="text" id="search" placeholder="Buscar por ganador u objeto..." style="width:100%; padding:10px; border-radius:8px; border:1px solid #cbd5e1;" onkeyup="render()">
        </div>
        <div class="grid-header">
            <div>DESCRIPCIÓN / GANADOR</div>
            <div>P. BASE</div>
            <div>P. ADJUDICADO</div>
            <div style="text-align:center">BAJA %</div>
            <div style="text-align:center">LINK</div>
        </div>
        <div class="list-container" id="list"></div>
    </div>
</div>
<script>
    const data = {datos_json};
    let currentCat = 'obras'; let sidebarMode = 'entities'; let activeFilter = null;

    function switchCat(cat, el) {{
        currentCat = cat;
        document.querySelectorAll('.nav-pills .nav-item').forEach(x => x.classList.remove('active'));
        el.classList.add('active');
        activeFilter = null;
        renderSidebar(); render();
    }}

    function setMode(mode, el) {{
        sidebarMode = mode;
        document.querySelectorAll('.filter-row').forEach(x => x.classList.remove('active'));
        el.classList.add('active');
        activeFilter = null;
        renderSidebar(); render();
    }}

    function renderSidebar() {{
        const container = document.getElementById('sidebar-items');
        container.innerHTML = '';
        const filtered = data.filter(d => d.categoria === currentCat);
        const counts = {{}};
        const field = sidebarMode === 'entities' ? 'entidad' : 'ganador';
        
        filtered.forEach(d => {{ counts[d[field]] = (counts[d[field]] || 0) + 1; }});
        
        Object.entries(counts).sort((a,b)=>b[1]-a[1]).forEach(([name, count]) => {{
            const div = document.createElement('div');
            div.className = 'filter-row' + (activeFilter === name ? ' active' : '');
            div.innerHTML = `<span>${{name.substring(0,25)}}...</span><strong>${{count}}</strong>`;
            div.onclick = () => {{ activeFilter = name; renderSidebar(); render(); }};
            container.appendChild(div);
        }});
    }}

    function render() {{
        const list = document.getElementById('list');
        const search = document.getElementById('search').value.toLowerCase();
        let filtered = data.filter(d => d.categoria === currentCat);
        
        if(activeFilter) filtered = filtered.filter(d => (sidebarMode === 'entities' ? d.entidad : d.ganador) === activeFilter);
        if(search) filtered = filtered.filter(d => d.objeto.toLowerCase().includes(search) || d.ganador.toLowerCase().includes(search));

        list.innerHTML = '';
        let total = 0; let totalBaja = 0;

        filtered.forEach(d => {{
            total += d.adjudicado_num;
            totalBaja += d.baja;
            const bCls = d.baja > 15 ? 'b-roja' : (d.baja > 5 ? 'b-naranja' : 'b-verde');
            list.innerHTML += `
                <div class="row-item">
                    <div>
                        <div style="font-size:0.7rem; color:#64748b">${{d.entidad}}</div>
                        <div style="font-weight:600; margin-bottom:4px">${{d.objeto}}</div>
                        <div class="ri-win"><i class="fa-solid fa-crown"></i> ${{d.ganador}}</div>
                    </div>
                    <div style="font-weight:600">${{d.presupuesto_num.toLocaleString()}}€</div>
                    <div style="font-weight:800; color:var(--primary)">${{d.adjudicado_num.toLocaleString()}}€</div>
                    <div style="display:flex; justify-content:center"><span class="baja-pill ${{bCls}}">${{d.baja}}%</span></div>
                    <div style="text-align:center"><a href="${{d.link}}" target="_blank" style="color:var(--primary)"><i class="fa-solid fa-arrow-up-right-from-square"></i></a></div>
                </div>`;
        }});

        document.getElementById('k-total').innerText = total.toLocaleString() + ' €';
        document.getElementById('k-baja').innerText = (filtered.length ? (totalBaja/filtered.length).toFixed(2) : 0) + ' %';
    }}

    renderSidebar(); render();
</script>
</body>
</html>
"""

with open("analisis.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("✅ analisis.html V2 generado con éxito.")
