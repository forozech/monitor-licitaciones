# ==============================================================================
# MONITOR DE CONTRATACIÓN EUSKADI - V49 VITAMINADA (TABLA + BAJAS + ADJUDICATARIOS)
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
import urllib3

# Evitar errores de certificados en webs antiguas
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. CONFIGURACIÓN COMPLETA DE FUENTES ---
# Incluye Obras (p01=1) y Servicios (p01=2)
# Incluye Adjudicado (p02=5), Formalizado (p02=8) y Finalizado/Cerrado (p02=14)
SOURCES = [
    # OBRAS
    {"tipo": "OBRA", "estado": "ADJUDICADO",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=5&idioma=es"},
    {"tipo": "OBRA", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=8&p11=01/01/2025&idioma=es"},
    {"tipo": "OBRA", "estado": "CERRADO",     "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=14&p11=01/01/2025&idioma=es"},
    
    # SERVICIOS
    {"tipo": "SERV", "estado": "ADJUDICADO",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=5&idioma=es"},
    {"tipo": "SERV", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=8&p11=01/01/2025&idioma=es"},
    {"tipo": "SERV", "estado": "CERRADO",     "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=14&p11=01/01/2025&idioma=es"}
]

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def limpiar_precio(texto):
    """Convierte texto sucio '1.500,00 €' a float 1500.00"""
    if not texto: return 0.0
    try:
        clean = re.sub(r'[^\d,]', '', texto) # Quitar letras y símbolos
        return float(clean.replace(',', '.')) if clean else 0.0
    except: return 0.0

def extraer_datos_contrato(url):
    """Entra en la ficha y saca la información financiera y el ganador"""
    res = {
        "entidad": "Desconocido",
        "ganador": "---",
        "base": 0.0,
        "final": 0.0
    }
    try:
        r = requests.get(url, headers=HEADERS, verify=False, timeout=10)
        r.encoding = r.apparent_encoding # Forzar UTF-8 real
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Estrategia de búsqueda en filas de tabla (tr -> th/td)
        for row in soup.find_all('tr'):
            th = row.find('th')
            td = row.find('td')
            if th and td:
                lab = th.get_text().lower().strip()
                val = td.get_text().strip()
                
                # 1. ENTIDAD (Poder adjudicador)
                if "poder adjudicador" in lab:
                    res["entidad"] = val

                # 2. GANADOR (Adjudicatario / Contratista)
                # Buscamos varias palabras clave porque la web cambia según el estado
                if any(x in lab for x in ["adjudicatario", "contratista", "empresa adjudicataria", "identidad"]):
                    limpio = val.split('\n')[0].strip() # Quitamos el CIF si sale debajo
                    if len(limpio) > 2: res["ganador"] = limpio

                # 3. PRESUPUESTO BASE (Licitación sin IVA)
                if "presupuesto base de licitaci" in lab and "sin iva" in lab:
                    res["base"] = limpiar_precio(val)

                # 4. PRECIO FINAL (Adjudicación / Formalización / Liquidación)
                # Buscamos el precio real por el que se ha cerrado
                if any(x in lab for x in ["importe de adjudicaci", "importe de formalizaci", "importe de liquidaci"]):
                    if "sin iva" in lab:
                        res["final"] = limpiar_precio(val)
        
        return res
    except: return res

# --- PROCESAMIENTO ---
resultados = []
links_procesados = set()

print(f"🚀 INICIANDO ANÁLISIS V49 (COMPLETO) - {datetime.now().strftime('%H:%M:%S')}")

for src in SOURCES:
    try:
        r = requests.get(src['url'], headers=HEADERS, verify=False, timeout=15)
        soup = BeautifulSoup(r.content, 'xml')
        items = soup.find_all('item')[:15] # 15 últimos de cada tipo

        for item in items:
            link = item.link.text
            if link in links_procesados: continue
            links_procesados.add(link)
            
            titulo = item.title.text
            
            # ESCANEO PROFUNDO
            data = extraer_datos_contrato(link)
            time.sleep(0.2) # Pausa técnica

            # CÁLCULO DE BAJA (%)
            baja = 0.0
            if data["base"] > 0 and data["final"] > 0:
                baja = ((data["base"] - data["final"]) / data["base"]) * 100
            
            # Limpieza visual
            ganador_display = data["ganador"]
            if len(ganador_display) < 3 or "---" in ganador_display:
                ganador_display = "Ver detalle"

            resultados.append({
                "tipo": src['tipo'],
                "estado": src['estado'],
                "entidad": data["entidad"],
                "objeto": titulo,
                "ganador": ganador_display,
                "base": data["base"],
                "final": data["final"],
                "baja": round(baja, 2),
                "link": link
            })
            
    except Exception as e:
        print(f"❌ Error leyendo RSS {src['estado']}: {e}")

# --- GENERACIÓN DEL HTML (PLANTILLA V49) ---
html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor de Licitaciones Euskadi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; font-size: 0.9rem; background: #f8f9fa; }}
        .container-fluid {{ padding: 25px; }}
        
        /* ESTILOS TABLA */
        .table {{ background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        thead {{ background: #2c3e50; color: white; }}
        th {{ font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; vertical-align: middle; }}
        td {{ vertical-align: middle; padding: 12px 10px; }}
        
        /* BADGES */
        .badge-baja {{ font-size: 0.85rem; padding: 5px 8px; width: 60px; display: inline-block; }}
        .baja-alta {{ background-color: #d63384; color: white; }} /* > 20% */
        .baja-media {{ background-color: #20c997; color: white; }} /* > 10% */
        .baja-baja {{ background-color: #e9ecef; color: #495057; }} /* < 10% */
        
        .est-adjudicado {{ color: #fd7e14; font-weight: 800; font-size: 0.8rem; }}
        .est-formalizado {{ color: #0d6efd; font-weight: 800; font-size: 0.8rem; }}
        .est-cerrado {{ color: #198754; font-weight: 800; font-size: 0.8rem; }}
        
        .ganador {{ font-weight: 600; color: #2c3e50; }}
        .entidad {{ font-size: 0.85rem; color: #6c757d; font-weight: 500; }}
        .objeto-link {{ text-decoration: none; color: #212529; font-weight: 600; display: block; }}
        .objeto-link:hover {{ color: #0d6efd; }}
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2 class="mb-0">📊 Monitor de Contratación Pública</h2>
            <div class="text-end">
                <span class="badge bg-secondary">Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}</span>
                <span class="badge bg-dark ms-2">{len(resultados)} Registros</span>
            </div>
        </div>

        <div class="table-responsive">
            <table class="table table-hover align-middle">
                <thead>
                    <tr>
                        <th width="5%">Tipo</th>
                        <th width="8%">Estado</th>
                        <th width="15%">Entidad</th>
                        <th width="30%">Objeto del Contrato</th>
                        <th width="18%">Adjudicatario (Ganador)</th>
                        <th width="8%" class="text-end">P. Base</th>
                        <th width="8%" class="text-end">P. Adj.</th>
                        <th width="8%" class="text-center">Baja</th>
                    </tr>
                </thead>
                <tbody>
"""

for r in resultados:
    # Formateo de moneda (1.000 €)
    base_str = "{:,.0f} €".format(r['base']).replace(",", ".")
    final_str = "{:,.0f} €".format(r['final']).replace(",", ".") if r['final'] > 0 else "-"
    
    # Lógica de colores para Baja
    clase_baja = "baja-baja"
    if r['baja'] > 10: clase_baja = "baja-media"
    if r['baja'] > 20: clase_baja = "baja-alta"
    
    # Badge Tipo
    badge_tipo = "bg-warning text-dark" if r['tipo'] == "OBRA" else "bg-info text-white"
    
    # Clase Estado
    clase_estado = "est-adjudicado"
    if r['estado'] == "FORMALIZADO": clase_estado = "est-formalizado"
    if r['estado'] == "CERRADO": clase_estado = "est-cerrado"

    html += f"""
                    <tr>
                        <td class="text-center"><span class="badge {badge_tipo}">{r['tipo']}</span></td>
                        <td class="{clase_estado}">{r['estado']}</td>
                        <td class="entidad">{r['entidad'][:40]}</td>
                        <td><a href="{r['link']}" target="_blank" class="objeto-link">{r['objeto']}</a></td>
                        <td class="ganador text-truncate" style="max-width: 200px;" title="{r['ganador']}">{r['ganador']}</td>
                        <td class="text-end text-muted small">{base_str}</td>
                        <td class="text-end fw-bold">{final_str}</td>
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

# Guardar
with open("analisis.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ ANÁLISIS COMPLETADO. Archivo 'analisis.html' generado correctamente.")
