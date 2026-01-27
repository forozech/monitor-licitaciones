# ==============================================================================
# MONITOR DE LICITACIONES EUSKADI - V6 (OBRAS + SERVICIOS + FONDOS UE)
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import json
import re
import time
from datetime import datetime
import urllib3
import os

# Desactivar advertencias de certificados SSL (comÃºn en webs gubernamentales antiguas)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURACIÃ“N DE FUENTES (OBRAS Y SERVICIOS) ---
# p01=1 (Obras), p01=2 (Servicios)
# p02=5 (AdjudicaciÃ³n), p02=8 (Formalizado), p02=14 (Finalizado)
SOURCES = [
    # --- OBRAS ---
    {"tipo": "OBRA", "estado": "ADJUDICADO",  "color": "orange", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=5&idioma=es"},
    {"tipo": "OBRA", "estado": "FORMALIZADO", "color": "blue",   "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=8&p11=01/01/2025&idioma=es"},
    {"tipo": "OBRA", "estado": "FINALIZADO",  "color": "green",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=14&p11=01/01/2025&idioma=es"},
    
    # --- SERVICIOS ---
    {"tipo": "SERVICIO", "estado": "ADJUDICADO",  "color": "orange", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=5&idioma=es"},
    {"tipo": "SERVICIO", "estado": "FORMALIZADO", "color": "blue",   "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=8&p11=01/01/2025&idioma=es"},
    {"tipo": "SERVICIO", "estado": "FINALIZADO",  "color": "green",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=14&p11=01/01/2025&idioma=es"}
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def limpiar_precio(texto):
    if not texto: return 0.0
    try:
        clean = re.sub(r'[^\d,]', '', texto)
        return float(clean.replace(',', '.')) if clean else 0.0
    except: return 0.0

def extraer_detalles(url):
    """Extrae ganador, importe final, plazos y si tiene fondos europeos"""
    res = {
        "ganador": "---", 
        "importe": 0.0, 
        "entidad": "Desconocido", 
        "plazo": "",
        "europeo": False
    }
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        texto_pag = soup.get_text().upper()

        # DetecciÃ³n de Fondos Europeos
        if any(x in texto_pag for x in ["NEXTGENERATION", "PRTR", "FONDO EUROPEO", "FINANCIADO POR LA UN"]):
            res["europeo"] = True

        for row in soup.find_all('tr'):
            th = row.find('th')
            td = row.find('td')
            if th and td:
                lab = th.get_text().lower()
                val = td.get_text().strip()
                
                # Entidad
                if "poder adjudicador" in lab: res["entidad"] = val
                # Ganador
                if any(x in lab for x in ["adjudicatario", "contratista", "empresa"]): 
                    res["ganador"] = val.split('\n')[0]
                # Importe (prioriza el de adjudicaciÃ³n/formalizaciÃ³n sin IVA)
                if any(x in lab for x in ["importe de adjudicaci", "importe de formalizaci", "precio de adjudicaci"]):
                    if "sin iva" in lab and res["importe"] == 0.0:
                        res["importe"] = limpiar_precio(val)
                # Plazo
                if "plazo de ejecuci" in lab: res["plazo"] = val

        return res
    except: return res

# --- PROCESO PRINCIPAL ---
resultados = []
links_procesados = set()

print("ðŸš€ INICIANDO ESCANEO DE EUSKADI...")

for src in SOURCES:
    try:
        print(f"ðŸ”Ž Leyendo: {src['tipo']} - {src['estado']}...")
        r = requests.get(src['url'], headers=HEADERS, verify=False, timeout=20)
        soup = BeautifulSoup(r.content, 'xml')
        items = soup.find_all('item')[:15] # Leemos los 15 mÃ¡s recientes de cada tipo

        for item in items:
            link = item.link.text
            if link in links_procesados: continue
            links_procesados.add(link)

            titulo = item.title.text
            data = extraer_detalles(link)
            
            # PequeÃ±a pausa para no saturar el servidor
            time.sleep(0.3)

            resultados.append({
                "tipo": src['tipo'],
                "estado": src['estado'],
                "color_estado": src['color'],
                "titulo": titulo,
                "entidad": data["entidad"],
                "ganador": data["ganador"],
                "importe": data["importe"],
                "europeo": data["europeo"],
                "link": link
            })
    except Exception as e:
        print(f"Error en fuente: {e}")

# --- GENERACIÃ“N DEL HTML ---
html_content = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor de Licitaciones Euskadi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f8f9fa; font-family: 'Segoe UI', sans-serif; }}
        .badge-obra {{ background-color: #6f42c1; color: white; }}
        .badge-servicio {{ background-color: #0d6efd; color: white; }}
        .badge-eu {{ background-color: #ffc107; color: black; font-weight: bold; }}
        .card {{ margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: none; }}
        .price {{ font-size: 1.2em; font-weight: bold; color: #2c3e50; }}
        .ganador {{ color: #198754; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="container py-4">
        <h1 class="mb-4 text-center">ðŸ“Š Radar de ContrataciÃ³n PÃºblica Euskadi</h1>
        <p class="text-center text-muted">Ãšltima actualizaciÃ³n: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        
        <div class="row">
"""

for item in resultados:
    # Formateo de moneda
    importe_str = "{:,.2f} â‚¬".format(item['importe']).replace(",", "X").replace(".", ",").replace("X", ".")
    
    badge_tipo = "badge-obra" if item['tipo'] == "OBRA" else "badge-servicio"
    badge_ue = '<span class="badge badge-eu">ðŸ‡ªðŸ‡º FONDOS UE</span>' if item['europeo'] else ""
    
    # Colores para el estado
    bg_header = "#6c757d" # Gris por defecto
    if item['estado'] == "ADJUDICADO": bg_header = "#fd7e14" # Naranja
    if item['estado'] == "FORMALIZADO": bg_header = "#0d6efd" # Azul
    if item['estado'] == "FINALIZADO": bg_header = "#198754" # Verde

    html_content += f"""
    <div class="col-md-6 col-lg-4">
        <div class="card h-100">
            <div class="card-header text-white d-flex justify-content-between align-items-center" style="background-color: {bg_header}">
                <span class="badge {badge_tipo}">{item['tipo']}</span>
                <span class="small fw-bold">{item['estado']}</span>
            </div>
            <div class="card-body">
                <h6 class="card-subtitle mb-2 text-muted">{item['entidad']}</h6>
                <h5 class="card-title"><a href="{item['link']}" target="_blank" class="text-decoration-none text-dark">{item['titulo'][:100]}...</a></h5>
                <hr>
                <p class="card-text">
                    <strong>Ganador:</strong> <span class="ganador">{item['ganador']}</span><br>
                    <strong>Importe:</strong> <span class="price">{importe_str}</span>
                </p>
                {badge_ue}
            </div>
        </div>
    </div>
    """

html_content += """
        </div>
    </div>
</body>
</html>
"""

# Guardar archivo
with open("analisis.html", "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"âœ… Hecho. {len(resultados)} licitaciones procesadas en 'analisis.html'.")
