# ==============================================================================
# MONITOR DE ADJUDICACIONES EUSKADI - V8 (FINALIZADOS + ADJUDICATARIOS)
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
import urllib3

# Evitar errores de certificado en webs antiguas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. CONFIGURACIÓN DE FUENTES (OBRAS Y SERVICIOS) ---
# Hemos recuperado los FINALIZADOS (p02=14)
SOURCES = [
    # OBRAS (p01=1)
    {"tipo": "OBRA", "estado": "ADJUDICADO",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=5&idioma=es"},
    {"tipo": "OBRA", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=8&p11=01/01/2025&idioma=es"},
    {"tipo": "OBRA", "estado": "FINALIZADO",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=14&p11=01/01/2025&idioma=es"},
    
    # SERVICIOS (p01=2)
    {"tipo": "SERV", "estado": "ADJUDICADO",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=5&idioma=es"},
    {"tipo": "SERV", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=8&p11=01/01/2025&idioma=es"},
    {"tipo": "SERV", "estado": "FINALIZADO",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=14&p11=01/01/2025&idioma=es"}
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def limpiar_precio(texto):
    """Convierte '1.200,50 €' a float 1200.50"""
    if not texto: return 0.0
    try:
        clean = re.sub(r'[^\d,]', '', texto) # Quitar todo menos números y comas
        return float(clean.replace(',', '.')) if clean else 0.0
    except: return 0.0

def extraer_datos_financieros(url):
    """Entra en la ficha y saca: Ganador, Presupuesto Base y Precio Adjudicado"""
    res = {
        "entidad": "Desconocido",
        "ganador": "---",
        "base": 0.0,
        "adjudicado": 0.0
    }
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=10)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Recorremos la tabla de datos
        for row in soup.find_all('tr'):
            th = row.find('th')
            td = row.find('td')
            if th and td:
                lab = th.get_text().lower().strip()
                val = td.get_text().strip()
                
                # 1. ENTIDAD
                if "poder adjudicador" in lab:
                    res["entidad"] = val

                # 2. GANADOR (Adjudicatario / Contratista / Empresa)
                # Buscamos variantes para asegurar que lo pilla
                if any(x in lab for x in ["adjudicatario", "contratista", "empresa adjudicataria", "identidad"]):
                    # Cogemos solo la primera línea (el nombre) y quitamos el CIF si sale debajo
                    if len(val) > 2: res["ganador"] = val.split('\n')[0]

                # 3. PRESUPUESTO BASE (Sin IVA)
                if "presupuesto base de licitaci" in lab and "sin iva" in lab:
                    res["base"] = limpiar_precio(val)

                # 4. PRECIO FINAL (Adjudicación o Liquidación)
                # En finalizados a veces se llama "Importe de liquidación"
                if any(x in lab for x in ["importe de adjudicaci", "importe de formalizaci", "importe de liquidaci"]):
                    if "sin iva" in lab:
                        res["adjudicado"] = limpiar_precio(val)
        
        return res
    except: return res

# --- PROCESAMIENTO ---
resultados = []
links_vistos = set()

print("🔄 ESCANEANDO TODO EL CICLO (ADJUDICADO -> FORMALIZADO -> FINALIZADO)...")

for src in SOURCES:
    try:
        r = requests.get(src['url'], headers=HEADERS, verify=False, timeout=20)
        soup = BeautifulSoup(r.content, 'xml')
        items = soup.find_all('item')[:15] # 15 de cada tipo

        for item in items:
            link = item.link.text
            if link in links_vistos: continue
            links_vistos.add(link)
            
            titulo = item.title.text
            
            # Extraemos los datos duros
            data = extraer_datos_financieros(link)
            time.sleep(0.2) # Pausa cortés

            # Cálculo de la BAJA (%)
            baja = 0.0
            if data["base"] > 0 and data["adjudicado"] > 0:
                baja = ((data["base"] - data["adjudicado"]) / data["base"]) * 100
            
            # Filtro visual para ganadores vacíos
            ganador_final = data["ganador"] if len(data["ganador"]) > 3 else "Consultar Ficha"

            resultados.append({
                "tipo": src['tipo'],
                "estado": src['estado'],
                "entidad": data["entidad"],
                "objeto": titulo,
                "ganador": ganador_final,
                "base": data["base"],
                "adjudicado": data["adjudicado"],
                "baja": round(baja, 2),
                "link": link
            })
            
    except Exception as e:
        print(f"Error en {src['url']}: {e}")

# --- GENERACIÓN DEL HTML (TABLA V4) ---
html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor de Contratación Euskadi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; font-size: 0.85rem; background: #f4f6f9; }}
        .container-fluid {{ padding: 20px; }}
        h1 {{ color: #2c3e50; font-weight: 700; }}
        .table {{ background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        thead {{ background: #343a40; color: white; }}
        th {{ font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; }}
        td {{ vertical-align: middle; }}
        
        .badge-baja {{ font-size: 0.85rem; padding: 5px 8px; }}
        .baja-alta {{ background-color: #d63384; color: white; }} /* > 20% */
        .baja-media {{ background-color: #20c997; color: white; }} /* > 10% */
        .baja-baja {{ background-color: #6c757d; color: white; }} /* < 10% */
        
        /* Colores de Estado */
        .est-adjudicado {{ color: #fd7e14; font-weight: bold; }}
        .est-formalizado {{ color: #0d6efd; font-weight: bold; }}
        .est-finalizado {{ color: #198754; font-weight: bold; }}

        .entidad {{ font-weight: bold; color: #495057; }}
        .ganador {{ color: #0d6efd; font-weight: 600; }}
        tr:hover {{ background-color: #f1f3f5; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h1>📊 Monitor de Bajas y Adjudicatarios</h1>
            <span class="text-muted">Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
        </div>

        <div class="table-responsive">
            <table class="table table-hover table-striped">
                <thead>
                    <tr>
                        <th width="5%">Tipo</th>
                        <th width="8%">Estado</th>
                        <th width="15%">Entidad</th>
                        <th width="30%">Objeto</th>
                        <th width="20%">Ganador (Adjudicatario)</th>
                        <th width="8%" class="text-end">P. Base</th>
                        <th width="8%" class="text-end">P. Final</th>
                        <th width="6%" class="text-center">Baja</th>
                    </tr>
                </thead>
                <tbody>
"""

for r in resultados:
    # Formato de moneda
    base_str = "{:,.0f} €".format(r['base']).replace(",", ".")
    adj_str = "{:,.0f} €".format(r['adjudicado']).replace(",", ".") if r['adjudicado'] > 0 else "---"
    
    # Color de la baja
    clase_baja = "baja-baja"
    if r['baja'] > 10: clase_baja = "baja-media"
    if r['baja'] > 20: clase_baja = "baja-alta"
    
    # Color tipo y estado
    badge_tipo = "bg-warning text-dark" if r['tipo'] == "OBRA" else "bg-info text-white"
    
    clase_estado = "est-adjudicado"
    if r['estado'] == "FORMALIZADO": clase_estado = "est-formalizado"
    if r['estado'] == "FINALIZADO": clase_estado = "est-finalizado"

    html += f"""
                    <tr>
                        <td><span class="badge {badge_tipo}">{r['tipo']}</span></td>
                        <td class="{clase_estado}">{r['estado']}</td>
                        <td class="entidad">{r['entidad'][:40]}...</td>
                        <td><a href="{r['link']}" target="_blank" class="text-decoration-none text-dark fw-bold">{r['objeto'][:90]}...</a></td>
                        <td class="ganador">{r['ganador']}</td>
                        <td class="text-end text-muted">{base_str}</td>
                        <td class="text-end fw-bold">{adj_str}</td>
                        <td class="text-center">
                            <span class="badge badge-baja {clase_baja}">{r['baja']}%</span>
                        </td>
                    </tr>
    """

html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

with open("analisis.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Completado. Se han procesado {len(resultados)} registros en 'analisis.html'.")
