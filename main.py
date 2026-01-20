# ==============================================================================
# GENERADOR DASHBOARD 10.0 - ULTIMATE UI (PUSH SIDEBAR + COMPACT HEADER)
# ==============================================================================

!pip install requests beautifulsoup4 pandas

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import json
from datetime import datetime
from google.colab import files
import sys

# --- 1. CONFIGURACIÓN ---
RSS_URL = "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=3&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124 Safari/537.36'}

KEYWORDS_FAVORITOS = {
    "Donostialdea": ["Donostia", "San Sebastián", "Donostiako", "Errenteria", "Rentería", "Pasaia", "Pasajes", "Hernani", "Lasarte", "Andoain", "Oiartzun", "Astigarraga", "Urnieta", "Lezo", "Usurbil"],
    "Diputación": ["Foru Aldundia", "Diputación", "Gipuzkoako Foru"],
    "Txingudi": ["Txingudi", "Servicios de Txingudi"],
    "Añarbe": ["Añarbe", "Aguas del Añarbe"]
}

# --- 2. FUNCIONES DE EXTRACCIÓN ---
def limpiar_presupuesto(texto):
    if not texto: return 0.0
    try: return float(texto.lower().replace('€','').replace('.','').replace(',','.').strip())
    except: return 0.0

def calcular_dias_restantes(fecha_str):
    if not fecha_str or "Consultar" in fecha_str: return 999
    formatos = ["%d/%m/%Y %H:%M", "%d/%m/%Y"]
    for fmt in formatos:
        try: return (datetime.strptime(fecha_str, fmt) - datetime.now()).days + 1
        except ValueError: continue
    return 999

def detectar_grupo(entidad):
    for grupo, keywords in KEYWORDS_FAVORITOS.items():
        for k in keywords:
            if k.lower() in entidad.lower(): return True, grupo
    return False, "Otros"

print("🚀 INICIANDO GENERACIÓN UI 10.0...")
print("---------------------------------------")

try:
    resp = requests.get(RSS_URL, headers=HEADERS)
    soup_rss = BeautifulSoup(resp.content, 'xml')
    items = soup_rss.find_all('item')
except:
    print("Error conectando con el servidor.")
    sys.exit()

datos = []
total_items = len(items)

for i, item in enumerate(items):
    print(f"[{i+1}/{total_items}] Leyendo: {item.title.text[:40]}...", end="\r")
    link = item.link.text
    try:
        r = requests.get(link, headers=HEADERS, timeout=5)
        soup_det = BeautifulSoup(r.content, 'html.parser')
        info = {}
        for row in soup_det.find_all('div', class_='row'):
            cols = row.find_all('div', recursive=False)
            if len(cols) >= 2: info[" ".join(cols[0].text.split())] = " ".join(cols[1].text.split())
        for dt in soup_det.find_all('dt'):
            dd = dt.find_next_sibling('dd')
            if dd: info[" ".join(dt.text.split())] = " ".join(dd.text.split())

        presu_txt = info.get("Presupuesto del contrato sin IVA", "0")
        entidad = info.get("Poder adjudicador", info.get("Entidad impulsora", "Desconocido"))
        fecha_limite = info.get("Fecha límite de presentación de ofertas o solicitudes de participación", "Consultar")
        es_fav, grupo = detectar_grupo(entidad)
        
        datos.append({
            "entidad": entidad,
            "objeto": info.get("Objeto del contrato", item.title.text),
            "presupuesto_txt": presu_txt,
            "presupuesto_num": limpiar_presupuesto(presu_txt),
            "limite": fecha_limite,
            "dias_restantes": calcular_dias_restantes(fecha_limite),
            "expediente": info.get("Expediente", "---"),
            "link": link,
            "es_fav": es_fav,
            "grupo_fav": grupo
        })
        time.sleep(0.05)
    except: continue

print(f"\n✅ Datos listos. Construyendo Interfaz...")

df = pd.DataFrame(datos)

# --- PREPARAR DATOS JS ---
summary_df = df.groupby('entidad')['presupuesto_num'].sum().reset_index()
summary_df.columns = ['name', 'total']
counts = df['entidad'].value_counts().reset_index()
counts.columns = ['name', 'count']
summary_df = summary_df.merge(counts, on='name')
entities_json = summary_df.to_json(orient='records')

stats_total_anuncios = len(df)
stats_total_entidades = df['entidad'].nunique()
stats_total_dinero = df['presupuesto_num'].sum()
stats_dinero_fmt = "{:,.2f} €".format(stats_total_dinero).replace(",", "X").replace(".", ",").replace("X", ".")

# --- GENERAR HTML ---
grupos = df.groupby('entidad')
html_cards = ""

for entidad, grupo in grupos:
    es_fav = grupo.iloc[0]['es_fav']
    grupo_fav_nombre = grupo.iloc[0]['grupo_fav']
    total_entidad_num = grupo['presupuesto_num'].sum()
    total_entidad_fmt = "{:,.2f} €".format(total_entidad_num).replace(",", "X").replace(".", ",").replace("X", ".")
    min_dias = grupo['dias_restantes'].min()
    
    css_class = "tender-card fav" if es_fav else "tender-card"
    icon = "⭐" if es_fav else "🏛️"

    html_cards += f"""
    <div class="{css_class}" 
         data-entidad="{entidad.replace('"', '&quot;')}" 
         data-fav="{str(es_fav).lower()}" 
         data-grupo="{grupo_fav_nombre}" 
         data-total="{total_entidad_num}"
         data-min-dias="{min_dias}">
        <div class="card-header">
            <div class="header-left"><span style="font-size:1.1rem;">{icon}</span><span class="entity-name">{entidad}</span></div>
            <div class="entity-total">{total_entidad_fmt}</div>
        </div>
        <div class="items-container">
    """
    
    for _, row in grupo.iterrows():
        dias = row['dias_restantes']
        if dias < 5: badge_class, texto_dias = "badge-urgent", f"🔥 {dias} días"
        elif dias < 15: badge_class, texto_dias = "badge-warning", f"⚠️ {dias} días"
        elif dias == 999: badge_class, texto_dias = "badge-info", "Consultar"
        else: badge_class, texto_dias = "badge-ok", f"✅ {dias} días"

        html_cards += f"""
        <div class="tender-item" data-presu="{row['presupuesto_num']}" data-dias="{dias}" data-texto="{row['objeto'].lower()} {row['expediente'].lower()}">
            <div class="tender-title">{row['objeto']}</div>
            <div class="meta-row">
                <span class="chip chip-exp">📂 {row['expediente']}</span>
                <span class="chip chip-price">{row['presupuesto_txt']}</span>
                <div style="display:flex; align-items:center; gap:5px;">
                    <span class="chip chip-date">📅 {row['limite']}</span>
                    <span class="chip-days {badge_class}">{texto_dias}</span>
                </div>
                <div style="flex-grow:1;"></div>
                <a href="{row['link']}" target="_blank" class="action-btn">Ver Ficha ↗</a>
            </div>
        </div>
        """
    html_cards += "</div></div>"

# --- PLANTILLA HTML (ESTILOS MEJORADOS) ---
html_final = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor Licitaciones Euskadi</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{ 
            --primary: #3b82f6; 
            --bg: #f8fafc; 
            --text: #1e293b;
            --sidebar-width: 320px;
        }}
        body {{ background-color: var(--bg); font-family: 'Inter', sans-serif; margin: 0; padding: 20px; overflow-x: hidden; }}
        
        /* LAYOUT PRINCIPAL CON TRANSICIÓN DE EMPUJE */
        #main-wrapper {{
            max-width: 1200px; margin: 0 auto; 
            transition: margin-left 0.3s ease-in-out;
        }}
        
        /* 1. HERO STATS - MODERN COLORS */
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        
        .stat-box {{
            padding: 15px 20px;
            border-radius: 12px;
            cursor: pointer; transition: all 0.2s; position: relative; overflow: hidden;
            display: flex; flex-direction: column; justify-content: center;
            border: 1px solid rgba(0,0,0,0.05);
        }}
        
        /* COLOR: ANUNCIOS (AZUL) */
        .stat-blue {{ background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); }}
        .stat-blue .stat-val {{ color: #1e40af; }}
        .stat-blue .stat-lbl {{ color: #3b82f6; }}
        
        /* COLOR: ENTIDADES (ESMERALDA) */
        .stat-green {{ background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%); }}
        .stat-green .stat-val {{ color: #065f46; }}
        .stat-green .stat-lbl {{ color: #10b981; }}
        
        /* COLOR: DINERO (VIOLETA) */
        .stat-purple {{ background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%); }}
        .stat-purple .stat-val {{ color: #5b21b6; }}
        .stat-purple .stat-lbl {{ color: #8b5cf6; }}

        .stat-box:hover {{ transform: translateY(-2px); box-shadow: 0 8px 15px -3px rgba(0, 0, 0, 0.05); filter: brightness(0.98); }}
        
        .stat-val {{ font-size: 1.6rem; font-weight: 800; line-height: 1; }}
        .stat-lbl {{ font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 6px; }}

        /* 2. BARRA DE CONTROL COMPACTA Y ALINEADA */
        .top-bar {{ 
            background: white; 
            padding: 10px 20px; /* Menos altura */
            border-radius: 10px; 
            box-shadow: 0 1px 3px rgba(0,0,0,0.05); 
            margin-bottom: 20px; 
            display: flex; 
            flex-wrap: wrap; 
            align-items: center; /* Alineación vertical perfecta */
            justify-content: space-between;
            gap: 15px;
            border: 1px solid #e2e8f0;
        }}
        
        .title-box {{ display: flex; align-items: baseline; gap: 10px; }}
        .title-box h1 {{ margin: 0; color: #0f172a; font-size: 1.1rem; font-weight: 800; }}
        .title-box span {{ color: #94a3b8; font-size: 0.8rem; font-weight: 500; }}
        
        .filters {{ display: flex; gap: 10px; align-items: center; }}
        
        select, input {{ 
            padding: 6px 12px; /* Inputs más compactos */
            border: 1px solid #cbd5e1; border-radius: 6px; 
            font-family: inherit; background: #fff; font-size: 0.85rem;
            outline: none; color: #334155; font-weight: 500;
        }}
        input {{ width: 200px; }}
        input:focus, select:focus {{ border-color: var(--primary); }}

        /* SIDEBAR (PUSH MODE) */
        .sidebar {{
            height: 100%; width: 0; position: fixed; z-index: 1000; top: 0; left: 0;
            background-color: #ffffff; overflow-x: hidden; transition: 0.3s ease-in-out;
            border-right: 1px solid #e2e8f0;
            display: flex; flex-direction: column;
            box-shadow: 5px 0 15px rgba(0,0,0,0.03);
        }}
        .sidebar-header {{ 
            padding: 15px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; 
            display: flex; justify-content: space-between; align-items: center; 
        }}
        .sidebar-title {{ font-weight: 700; font-size: 1rem; color: #1e293b; }}
        .closebtn {{ font-size: 1.2rem; cursor: pointer; color: #64748b; padding: 5px; }}
        
        .sidebar-content {{ flex-grow: 1; overflow-y: auto; padding: 10px; }}
        
        .entity-row {{
            padding: 10px 12px; border-bottom: 1px solid #f1f5f9; cursor: pointer;
            display: flex; justify-content: space-between; align-items: center; border-radius: 6px; margin-bottom: 2px;
        }}
        .entity-row:hover {{ background-color: #eff6ff; }}
        .e-name {{ font-weight: 500; color: #334155; font-size: 0.85rem; }}
        .e-val {{ font-weight: 700; color: var(--primary); font-size: 0.8rem; background: #dbeafe; padding: 2px 8px; border-radius: 8px; }}

        /* TARJETAS DE RESULTADOS */
        .tender-card {{ background: white; border-radius: 10px; margin-bottom: 15px; border: 1px solid #e2e8f0; overflow: hidden; }}
        .tender-card.fav {{ border: 2px solid #f59e0b; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1); }}
        
        .card-header {{ background: #fcfcfc; padding: 12px 18px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #f1f5f9; }}
        .entity-name {{ font-weight: 700; color: #0f172a; margin-left: 8px; font-size: 0.95rem; }}
        .entity-total {{ background: #f1f5f9; padding: 4px 10px; border-radius: 15px; font-size: 0.8rem; font-weight: 700; color: #475569; }}
        
        .tender-item {{ padding: 15px 18px; border-bottom: 1px solid #f8fafc; }}
        .tender-item:hover {{ background-color: #fafafa; }}
        .tender-title {{ font-weight: 600; color: #334155; margin-bottom: 6px; font-size: 0.9rem; line-height: 1.4; }}
        
        /* CHIPS */
        .meta-row {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 6px; }}
        .chip {{ padding: 3px 8px; border-radius: 5px; font-size: 0.75rem; font-weight: 700; }}
        .chip-exp {{ background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; }}
        .chip-price {{ background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }}
        .chip-date {{ background: #fff; color: #475569; border: 1px solid #cbd5e1; }}
        .chip-days {{ padding: 3px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold; color: white; }}
        .badge-urgent {{ background-color: #ef4444; }}
        .badge-warning {{ background-color: #f97316; }}
        .badge-info {{ background-color: #94a3b8; }}
        .badge-ok {{ background-color: #3b82f6; }}
        
        .action-btn {{ text-decoration: none; background: #2563eb; color: white; padding: 5px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; margin-left: auto; }}
        .hidden {{ display: none !important; }}
    </style>
</head>
<body>

    <div id="mySidebar" class="sidebar">
        <div class="sidebar-header">
            <span id="sidebarTitle" class="sidebar-title">Lista Entidades</span>
            <span class="closebtn" onclick="closeSidebar()">&times;</span>
        </div>
        <div id="sidebarContent" class="sidebar-content"></div>
    </div>

    <div id="main-wrapper">
        
        <div class="stats-grid">
            <div class="stat-box stat-blue" onclick="resetView()">
                <span class="stat-val">{stats_total_anuncios}</span>
                <span class="stat-lbl">Anuncios Activos</span>
            </div>
            <div class="stat-box stat-green" onclick="openSidebar('entidades')">
                <span class="stat-val">{stats_total_entidades}</span>
                <span class="stat-lbl">Entidades (Ver A-Z)</span>
            </div>
            <div class="stat-box stat-purple" onclick="openSidebar('importe')">
                <span class="stat-val">{stats_dinero_fmt}</span>
                <span class="stat-lbl">Importe Total</span>
            </div>
        </div>

        <div class="top-bar">
            <div class="title-box">
                <h1>MONITOR LICITACIONES</h1>
                <span>| {time.strftime("%d/%m/%Y")}</span>
            </div>
            
            <div class="filters">
                <input type="text" id="searchInput" placeholder="🔎 Buscar..." onkeyup="aplicarFiltros()">
                
                <select id="zonaFilter" onchange="aplicarFiltros()">
                    <option value="Todas">Todas las zonas</option>
                    <option value="fav">⭐ Favoritos</option>
                    <option value="Donostialdea">Donostialdea</option>
                    <option value="Diputación">Diputación</option>
                    <option value="Txingudi">Txingudi</option>
                    <option value="Añarbe">Añarbe</option>
                </select>

                <select id="precioFilter" onchange="aplicarFiltros()">
                    <option value="all">Cualquier precio</option>
                    <option value="200000"> < 200k</option>
                    <option value="400000"> < 400k</option>
                    <option value="1000000"> < 1M</option>
                    <option value="more1000000"> > 1M</option>
                </select>

                <select id="ordenFilter" onchange="ordenarTarjetas()">
                    <option value="urgencia">⏳ Urgencia</option>
                    <option value="presupuesto">💰 Presupuesto</option>
                    <option value="az">🔤 Nombre A-Z</option>
                </select>
            </div>
        </div>

        <div id="cardsList">
            {html_cards}
        </div>
    </div>

    <script>
        const entitiesData = {entities_json};

        document.addEventListener('DOMContentLoaded', () => {{ ordenarTarjetas(); }});

        // --- LÓGICA SIDEBAR PUSH ---
        function openSidebar(mode) {{
            const sidebar = document.getElementById("mySidebar");
            const wrapper = document.getElementById("main-wrapper");
            const content = document.getElementById("sidebarContent");
            const title = document.getElementById("sidebarTitle");

            // Abrir y Empujar
            sidebar.style.width = "320px";
            if(window.innerWidth > 768) {{ // Solo empujar en escritorio
                wrapper.style.marginLeft = "340px";
            }}
            
            content.innerHTML = "";
            let sortedData = [];

            if (mode === 'entidades') {{
                title.innerText = "Entidades (A-Z)";
                sortedData = entitiesData.sort((a, b) => a.name.localeCompare(b.name));
            }} else {{
                title.innerText = "Ranking Importe";
                sortedData = entitiesData.sort((a, b) => b.total - a.total);
            }}

            sortedData.forEach(item => {{
                let valStr = "";
                if (mode === 'importe') valStr = new Intl.NumberFormat('de-DE', {{ style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }}).format(item.total);
                else valStr = item.count;

                const div = document.createElement("div");
                div.className = "entity-row";
                div.innerHTML = `<span class="e-name">${{item.name}}</span><span class="e-val">${{valStr}}</span>`;
                div.onclick = () => {{
                    filtrarPorEntidadEspecifica(item.name);
                    // En móvil cerramos, en escritorio podemos dejarlo abierto o cerrar a gusto del usuario
                    if(window.innerWidth <= 768) closeSidebar();
                }};
                content.appendChild(div);
            }});
        }}

        function closeSidebar() {{
            document.getElementById("mySidebar").style.width = "0";
            document.getElementById("main-wrapper").style.marginLeft = "auto"; // Reset margin
        }}

        function filtrarPorEntidadEspecifica(nombre) {{
            document.getElementById('searchInput').value = nombre; 
            document.getElementById('zonaFilter').value = "Todas"; 
            aplicarFiltros();
        }}

        function resetView() {{
            document.getElementById('searchInput').value = "";
            document.getElementById('zonaFilter').value = "Todas";
            document.getElementById('precioFilter').value = "all";
            aplicarFiltros();
            closeSidebar();
        }}

        // --- FILTROS Y ORDENACIÓN ---
        function aplicarFiltros() {{
            let search = document.getElementById('searchInput').value.toLowerCase();
            let zona = document.getElementById('zonaFilter').value;
            let precio = document.getElementById('precioFilter').value;
            
            let cards = document.getElementsByClassName('tender-card');
            
            for (let card of cards) {{
                let mostrarCard = true;
                let esFav = card.getAttribute('data-fav') === "true";
                let grupo = card.getAttribute('data-grupo');
                let entidadNombre = card.getAttribute('data-entidad').toLowerCase();
                
                if (zona === 'fav' && !esFav) mostrarCard = false;
                else if (zona !== 'Todas' && zona !== 'fav' && grupo !== zona) mostrarCard = false;
                
                if (mostrarCard) {{
                    let items = card.getElementsByClassName('tender-item');
                    let visiblesEnCard = 0;
                    for (let item of items) {{
                        let itemVisible = true;
                        let texto = item.getAttribute('data-texto');
                        let presu = parseFloat(item.getAttribute('data-presu'));
                        
                        if (search && !texto.includes(search) && !entidadNombre.includes(search)) itemVisible = false;
                        if (precio !== 'all') {{
                            if (precio === 'more1000000') {{ if (presu < 1000000) itemVisible = false; }}
                            else {{ if (presu >= parseFloat(precio)) itemVisible = false; }}
                        }}
                        if (itemVisible) {{ item.classList.remove('hidden'); visiblesEnCard++; }}
                        else {{ item.classList.add('hidden'); }}
                    }}
                    if (visiblesEnCard === 0) mostrarCard = false;
                }}
                if (mostrarCard) card.classList.remove('hidden'); else card.classList.add('hidden');
            }}
            ordenarTarjetas();
        }}

        function ordenarTarjetas() {{
            let criterio = document.getElementById('ordenFilter').value;
            let container = document.getElementById('cardsList');
            let cards = Array.from(container.getElementsByClassName('tender-card'));
            
            cards.sort((a, b) => {{
                if (a.classList.contains('hidden') && !b.classList.contains('hidden')) return 1;
                if (!a.classList.contains('hidden') && b.classList.contains('hidden')) return -1;

                let favA = a.getAttribute('data-fav') === 'true' ? 1 : 0;
                let favB = b.getAttribute('data-fav') === 'true' ? 1 : 0;

                if (criterio === 'urgencia') {{
                    if (favB !== favA) return favB - favA; 
                    return parseFloat(a.getAttribute('data-min-dias')) - parseFloat(b.getAttribute('data-min-dias'));
                }} 
                else if (criterio === 'presupuesto') {{
                    return parseFloat(b.getAttribute('data-total')) - parseFloat(a.getAttribute('data-total'));
                }}
                else if (criterio === 'az') {{
                    if (favB !== favA) return favB - favA; 
                    return a.getAttribute('data-entidad').localeCompare(b.getAttribute('data-entidad'));
                }}
            }});
            
            cards.forEach(card => {{
                container.appendChild(card);
                let itemsContainer = card.querySelector('.items-container');
                let items = Array.from(itemsContainer.getElementsByClassName('tender-item'));
                items.sort((ia, ib) => {{
                    if (criterio === 'presupuesto') return parseFloat(ib.getAttribute('data-presu')) - parseFloat(ia.getAttribute('data-presu'));
                    else return parseFloat(ia.getAttribute('data-dias')) - parseFloat(ib.getAttribute('data-dias'));
                }});
                items.forEach(item => itemsContainer.appendChild(item));
            }});
        }}
    </script>
</body>
</html>
"""

# --- GUARDAR COMO INDEX.HTML PARA LA WEB ---
nombre_archivo = "index.html"
with open(nombre_archivo, "w", encoding="utf-8") as f:
    f.write(html_final)

print(f"✅ Archivo {nombre_archivo} generado correctamente.")
# Eliminamos la línea de files.download porque en el servidor automático daría error