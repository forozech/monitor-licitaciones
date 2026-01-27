# ==============================================================================
# MONITOR DE ADJUDICACIONES EUSKADI - V1 (ANÁLISIS DE BAJAS Y GANADORES)
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

# --- ENLACES RSS DE ADJUDICACIÓN / FORMALIZACIÓN ---
SOURCES = [
    {"type": "obras", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=5&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
    {"type": "servicios", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=5&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"}
]

HEADERS = {'User-Agent': 'Mozilla/5.0'}

def limpiar_precio(texto):
    if not texto: return 0.0
    try:
        clean = re.sub(r'[^\d,]', '', texto)
        return float(clean.replace(',', '.'))
    except: return 0.0

# --- SCRAPING DE ADJUDICACIONES ---
adjudicaciones = []
print(f"🚀 INICIANDO ANÁLISIS DE ADJUDICACIONES...")

for src in SOURCES:
    print(f"   > Consultando {src['type']}...")
    try:
        res = requests.get(src['url'], headers=HEADERS, verify=False, timeout=30)
        soup_rss = BeautifulSoup(res.content, 'xml')
        items = soup_rss.find_all('item')[:40] # Analizamos las 40 más recientes por lote

        for item in items:
            link = item.link.text
            titulo = item.title.text
            
            # Entramos al detalle para sacar Ganador y Precio Final
            ganador = "Desconocido"
            p_base = 0.0
            p_adju = 0.0
            entidad = "Consultar"

            try:
                r_det = requests.get(link, headers=HEADERS, verify=False, timeout=15)
                s_det = BeautifulSoup(r_det.content, 'html.parser')
                
                # Extraer Empresa Ganadora
                t_ganador = s_det.find(string=re.compile(r"Adjudicatario", re.IGNORECASE))
                if t_ganador:
                    ganador = t_ganador.parent.find_next_sibling().text.strip()

                # Extraer Presupuesto Base (Sin IVA)
                t_base = s_det.find(string=re.compile(r"Presupuesto del contrato sin IVA", re.IGNORECASE))
                if t_base:
                    p_base = limpiar_precio(t_base.parent.find_next_sibling().text)

                # Extraer Importe Adjudicación (Sin IVA)
                t_adju = s_det.find(string=re.compile(r"Importe de adjudicaci.n sin IVA", re.IGNORECASE))
                if t_adju:
                    p_adju = limpiar_precio(t_adju.parent.find_next_sibling().text)

                # Entidad
                t_ent = s_det.find(string=re.compile(r"Poder adjudicador", re.IGNORECASE))
                if t_ent:
                    entidad = t_ent.parent.find_next_sibling().text.strip()
            except: pass

            # Calcular Baja %
            baja = 0.0
            if p_base > 0 and p_adju > 0:
                baja = ((p_base - p_adju) / p_base) * 100

            adjudicaciones.append({
                "tipo": src['type'],
                "entidad": entidad,
                "objeto": titulo,
                "ganador": ganador,
                "base": p_base,
                "adjudicado": p_adju,
                "baja": round(baja, 2),
                "fecha": datetime.now().strftime("%Y-%m-%d"), # Fecha captura
                "link": link
            })
            time.sleep(1) # Pausa ética

    except Exception as e:
        print(f"Error: {e}")

# --- GENERACIÓN DE analisis.html ---
# (Usa la misma estética V49 pero con las columnas de análisis)
html_analisis = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ANÁLISIS ADJUDICACIONES</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{ --primary: #2563eb; --bg: #f8fafc; }}
        body {{ font-family: 'Inter', sans-serif; background: var(--bg); margin: 0; padding: 20px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        .card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th {{ text-align: left; padding: 12px; border-bottom: 2px solid #f1f5f9; color: #64748b; font-size: 0.8rem; text-transform: uppercase; }}
        td {{ padding: 12px; border-bottom: 1px solid #f1f5f9; font-size: 0.9rem; }}
        .baja-pill {{ padding: 4px 8px; border-radius: 6px; font-weight: 700; font-size: 0.8rem; }}
        .b-verde {{ background: #dcfce7; color: #166534; }}
        .b-naranja {{ background: #ffedd5; color: #9a3412; }}
        .b-roja {{ background: #fee2e2; color: #991b1b; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 Monitor de Adjudicaciones</h1>
        <a href="index.html" style="text-decoration:none; color:var(--primary); font-weight:700;">← Volver a Licitaciones</a>
    </div>
    
    <div class="card">
        <table>
            <thead>
                <tr>
                    <th>Entidad</th>
                    <th>Objeto</th>
                    <th>Ganador (WIN)</th>
                    <th>P. Base</th>
                    <th>P. Adjudicado</th>
                    <th>Baja %</th>
                </tr>
            </thead>
            <tbody>
                {"".join([f'''
                <tr>
                    <td>{a['entidad'][:40]}...</td>
                    <td><a href="{a['link']}" target="_blank" style="color:#0f172a; text-decoration:none;">{a['objeto'][:60]}...</a></td>
                    <td style="font-weight:700; color:var(--primary);">{a['ganador']}</td>
                    <td>{a['base']:,.0f}€</td>
                    <td>{a['adjudicado']:,.0f}€</td>
                    <td><span class="baja-pill {'b-roja' if a['baja'] > 15 else ('b-naranja' if a['baja'] > 5 else 'b-verde')}">{a['baja']}%</span></td>
                </tr>
                ''' for a in adjudicaciones])}
            </tbody>
        </table>
    </div>
</body>
</html>
"""

with open("analisis.html", "w", encoding="utf-8") as f:
    f.write(html_analisis)
print("✅ analisis.html generado.")
