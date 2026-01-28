import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import json
import time
import hashlib
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN ---
OUTPUT_FILE = "analisis.html"

# --- PLANTILLA HTML (DASHBOARD) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor Licitaciones | Gipuzkoa 2025</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root { --bs-primary-rgb: 13, 110, 253; --bg-color: #f4f6f8; }
        body { background-color: var(--bg-color); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 0.9rem; }
        .kpi-card { background: white; border: none; border-radius: 12px; padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); height: 100%; position: relative; overflow: hidden; }
        .kpi-value { font-size: 1.8rem; font-weight: 800; color: #1e293b; margin-bottom: 0; }
        .kpi-label { font-size: 0.75rem; text-transform: uppercase; color: #64748b; font-weight: 600; }
        .kpi-icon { position: absolute; right: -10px; top: -10px; font-size: 5rem; opacity: 0.05; transform: rotate(15deg); }
        .dashboard-card { background: white; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); padding: 20px; margin-bottom: 20px; }
        .badge-baja { font-weight: 700; padding: 4px 8px; border-radius: 6px; min-width: 50px; display: inline-block; text-align: center; }
        .baja-alta { background-color: #dcfce7; color: #166534; }
        .baja-media { background-color: #fef9c3; color: #854d0e; }
        .baja-baja { background-color: #fee2e2; color: #991b1b; }
        .badge-estado { font-size: 0.7rem; padding: 3px 8px; border-radius: 12px; font-weight: 600; border: 1px solid #e5e7eb; }
    </style>
</head>
<body>
    <div class="container-fluid px-4 py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div><h2 class="fw-bold text-dark mb-0">Monitor de Licitaciones</h2><p class="text-muted mb-0 small">Gipuzkoa | Obras y Servicios 2025</p></div>
            <div class="text-end"><span class="badge bg-white text-secondary border shadow-sm py-2 px-3">Actualizado: <span id="lastUpdate">__FECHA__</span></span></div>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-xl-3 col-md-6"><div class="kpi-card"><i class="bi bi-cash-stack kpi-icon"></i><div class="kpi-label">Volumen Total</div><div class="kpi-value" id="kpi-volumen">0 €</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card"><i class="bi bi-percent kpi-icon"></i><div class="kpi-label">Baja Media</div><div class="kpi-value text-primary" id="kpi-baja">0%</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card"><i class="bi bi-people-fill kpi-icon"></i><div class="kpi-label">Competencia Media</div><div class="kpi-value" id="kpi-licitadores">0</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card"><i class="bi bi-file-earmark-check kpi-icon"></i><div class="kpi-label">Contratos</div><div class="kpi-value" id="kpi-contratos">0</div></div></div>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-md-8"><div class="dashboard-card h-100"><h6 class="fw-bold text-secondary small mb-3">DISTRIBUCIÓN DE BAJAS</h6><div style="height: 200px;"><canvas id="chartBajas"></canvas></div></div></div>
            <div class="col-md-4"><div class="dashboard-card h-100"><h6 class="fw-bold text-secondary small mb-3">TOP ADJUDICATARIOS</h6><div style="height: 200px; position: relative;"><canvas id="chartWinners"></canvas></div></div></div>
        </div>

        <div class="dashboard-card">
            <table id="tablaContratos" class="table table-hover w-100">
                <thead><tr><th>Exp.</th><th>Objeto / Ganador</th><th class="text-end">Presupuesto</th><th class="text-end">Adjudicación</th><th class="text-center">Baja</th><th class="text-center">Lic.</th><th class="text-center">Estado</th><th></th></tr></thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <div class="modal fade" id="modalDetalle" tabindex="-1"><div class="modal-dialog modal-lg modal-dialog-centered"><div class="modal-content"><div class="modal-header"><h5 class="modal-title fw-bold">Detalle Expediente</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body">
        <div class="alert alert-light border mb-4"><small class="text-uppercase text-muted fw-bold" style="font-size:0.7rem;">Objeto</small><p class="mb-0 fw-bold text-dark" id="modalObjeto">...</p></div>
        <div class="row mb-4"><div class="col-6"><div class="p-3 bg-light rounded border"><span class="d-block text-muted small fw-bold">PRESUPUESTO</span><span class="h5 fw-bold text-dark mb-0" id="modalBase">0 €</span></div></div><div class="col-6"><div class="p-3 bg-white rounded border border-success"><span class="d-block text-success small fw-bold">ADJUDICACIÓN</span><span class="h5 fw-bold text-success mb-0" id="modalAdj">0 €</span></div></div></div>
        <div class="row"><div class="col-md-7 border-end"><h6 class="fw-bold mb-3 small text-muted">LICITADORES (<span id="modalNumLic">0</span>)</h6><div id="modalRivales" style="max-height:300px;overflow-y:auto;"></div></div><div class="col-md-5 ps-md-4"><h6 class="fw-bold mb-3 small text-muted">ENLACES</h6><div id="modalDocs" class="d-grid gap-2"></div><div class="mt-4 text-center"><a id="linkFicha" href="#" target="_blank" class="btn btn-sm btn-outline-primary w-100">Ver Ficha Original</a></div></div></div>
    </div></div></div></div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>
    <script>
        const datos = __DATOS_JSON__;
        const eur = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });

        $(document).ready(function() {
            // KPIs
            let vol = 0, sumBaja = 0, countBaja = 0, sumLic = 0, winners = {};
            datos.forEach(d => {
                vol += d.importe_adjudicacion;
                if(d.baja_pct > 0) { sumBaja += d.baja_pct; countBaja++; }
                sumLic += d.num_licitadores;
                if(d.ganador !== "Desconocido") winners[d.ganador] = (winners[d.ganador] || 0) + 1;
            });

            $('#kpi-volumen').text(eur.format(vol));
            $('#kpi-baja').text((countBaja ? (sumBaja / countBaja) : 0).toFixed(2) + '%');
            $('#kpi-licitadores').text((datos.length ? (sumLic / datos.length) : 0).toFixed(1));
            $('#kpi-contratos').text(datos.length);

            // Gráficos
            const ranges = [0, 0, 0, 0];
            datos.forEach(d => {
                if(d.baja_pct <= 0.5) ranges[0]++;
                else if(d.baja_pct < 10) ranges[1]++;
                else if(d.baja_pct < 20) ranges[2]++;
                else ranges[3]++;
            });
            new Chart(document.getElementById('chartBajas'), { type: 'bar', data: { labels: ['Sin Baja', '< 10%', '10-20%', '> 20%'], datasets: [{ data: ranges, backgroundColor: ['#e2e8f0', '#fde047', '#86efac', '#22c55e'] }] }, options: { plugins:{legend:{display:false}}, scales:{y:{display:false},x:{grid:{display:false}}} } });

            const sortedW = Object.entries(winners).sort((a,b)=>b[1]-a[1]).slice(0,5);
            new Chart(document.getElementById('chartWinners'), { type: 'doughnut', data: { labels: sortedW.map(x=>x[0]), datasets: [{ data: sortedW.map(x=>x[1]), backgroundColor: ['#3b82f6','#6366f1','#8b5cf6','#a855f7','#d946ef'] }] }, options: { plugins:{legend:{position:'right',labels:{boxWidth:10}}}, cutout:'70%' } });

            // Tabla
            $('#tablaContratos').DataTable({
                data: datos,
                language: { url: "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json" },
                pageLength: 25,
                order: [[ 4, "desc" ]],
                columns: [
                    { data: 'expediente', render: d => `<span class="fw-bold small">${d}</span>` },
                    { data: null, render: d => `<div style="line-height:1.2"><span class="d-block fw-bold text-primary small">${d.ganador}</span><span class="d-block text-muted text-truncate small" style="max-width:250px" title="${d.objeto}">${d.objeto}</span></div>` },
                    { data: 'presupuesto_base', className: 'text-end', render: d => `<span class="text-secondary small">${eur.format(d)}</span>` },
                    { data: 'importe_adjudicacion', className: 'text-end', render: d => `<span class="fw-bold small">${eur.format(d)}</span>` },
                    { data: 'baja_pct', className: 'text-center', render: d => {
                        let cls = d >= 15 ? 'baja-alta' : d >= 5 ? 'baja-media' : d > 0 ? 'baja-baja' : 'bg-light text-muted';
                        return `<span class="badge-baja ${cls}">${d}%</span>`;
                    }},
                    { data: 'num_licitadores', className: 'text-center', render: d => `<span class="badge bg-white border text-dark">${d}</span>` },
                    { data: 'estado_fase', className: 'text-center', render: d => `<span class="badge-estado bg-white text-secondary">${d.substring(0,3)}</span>` },
                    { data: null, orderable: false, render: (d,t,r,m) => `<button class="btn btn-sm btn-outline-secondary border-0" onclick='verDetalle(${m.row})'><i class="bi bi-eye-fill"></i></button>` }
                ]
            });
        });

        window.verDetalle = function(idx) {
            const d = datos[idx];
            $('#modalObjeto').text(d.objeto);
            $('#modalBase').text(eur.format(d.presupuesto_base));
            $('#modalAdj').text(eur.format(d.importe_adjudicacion));
            $('#modalNumLic').text(d.num_licitadores);
            $('#linkFicha').attr('href', d.url_ficha);
            
            let htmlRiv = '';
            d.rivales.forEach(r => htmlRiv += `<div class="p-2 border-bottom small d-flex justify-content-between"><span>${r}</span>${r===d.ganador?'<i class="bi bi-trophy-fill text-success"></i>':''}</div>`);
            $('#modalRivales').html(htmlRiv || '<div class="text-center text-muted py-2 small">Sin datos detallados</div>');

            let htmlDoc = '';
            d.documentos.forEach(doc => htmlDoc += `<a href="${doc.url}" target="_blank" class="btn btn-outline-secondary btn-sm text-start text-truncate mb-1"><i class="bi bi-file-pdf me-2"></i>${doc.nombre}</a>`);
            $('#modalDocs').html(htmlDoc);
            
            new bootstrap.Modal('#modalDetalle').show();
        };
    </script>
</body>
</html>
"""

# --- MOTOR DE EXTRACCIÓN (FIXED) ---
class MonitorEngine:
    def __init__(self):
        # FUENTES RSS EXACTAS SEGÚN INSTRUCCIONES DEL USUARIO
        # URL Servicios-Formalizado reconstruida con la lógica de las demás
        self.sources = [
            # OBRAS
            {"tipo": "OBRA", "estado": "ADJUDICADO",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=5&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "OBRA", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=8&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "OBRA", "estado": "CERRADO",     "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=14&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            
            # SERVICIOS
            {"tipo": "SERV", "estado": "ADJUDICADO",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=5&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            # RECONSTRUIDO: p01=2 (Servicios), p02=8 (Formalizado) + resto de parámetros idénticos
            {"tipo": "SERV", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=8&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "CERRADO",     "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=14&p03=&p04=&p05=&p06=FALSE&p07=&p08=&p09=&p10=&p11=&p12=01/01/2025&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"}
        ]
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.processed_ids = set()

    def clean_money(self, txt):
        if not txt: return 0.0
        try: return float(txt.replace('.', '').replace(',', '.'))
        except: return 0.0

    # Lógica mejorada basada en tu HTML: busca texto en columna 1, devuelve columna 2
    def get_tab_value(self, soup, tab_id, label):
        tab = soup.find('div', id=tab_id)
        if not tab: return None
        
        # Buscar en filas Bootstrap (row)
        # En tu HTML: <div class="row"><div class="col...4">Label</div><div class="col...8">Value</div></div>
        for row in tab.find_all('div', class_='row'):
            cols = row.find_all('div', recursive=False) # Solo hijos directos
            if len(cols) >= 2:
                label_text = cols[0].get_text(strip=True)
                if label.lower() in label_text.lower():
                    return cols[1].get_text(strip=True)
        return None

    def process_url(self, url, tipo, estado):
        print(f"      Procesando: {url}")
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(r.content, 'html.parser')
            
            data = {
                'id': hashlib.md5(url.encode()).hexdigest(),
                'url_ficha': url,
                'tipo_licitacion': tipo,
                'estado_fase': estado
            }

            # 1. HEADER (Objeto)
            # En tu HTML: <div class="cabeceraDetalle">...<dd><p>Texto</p></dd>
            head = soup.find('div', class_='cabeceraDetalle')
            if head and head.find('dd'):
                data['objeto'] = head.find('dd').get_text(strip=True)
            else:
                data['objeto'] = "Sin descripción"

            # 2. DATOS GENERALES (Tabs-1)
            data['expediente'] = self.get_tab_value(soup, 'tabs-1', 'Expediente') or "N/A"

            # 3. ECONÓMICOS (Tabs-4 y Tabs-9)
            base_str = self.get_tab_value(soup, 'tabs-4', 'Presupuesto del contrato sin IVA')
            if not base_str: base_str = self.get_tab_value(soup, 'tabs-4', 'Valor estimado') # Fallback

            adj_str = self.get_tab_value(soup, 'tabs-9', 'Precio sin IVA')
            
            data['presupuesto_base'] = self.clean_money(base_str)
            data['importe_adjudicacion'] = self.clean_money(adj_str)
            data['ganador'] = self.get_tab_value(soup, 'tabs-9', 'Razón social') or "Desconocido"

            # 4. CALCULO BAJA
            if data['presupuesto_base'] > 0 and data['importe_adjudicacion'] > 0:
                ahorro = data['presupuesto_base'] - data['importe_adjudicacion']
                data['baja_pct'] = round((ahorro / data['presupuesto_base']) * 100, 2)
            else:
                data['baja_pct'] = 0.0

            # 5. RIVALES (Tabs-8)
            # En tu HTML aparece bajo "Empresas Licitadoras".
            # Buscamos todas las filas donde la col-1 sea "Razón Social" y cogemos la col-2
            rivales = []
            tab8 = soup.find('div', id='tabs-8')
            if tab8:
                for row in tab8.find_all('div', class_='row'):
                    cols = row.find_all('div', recursive=False)
                    if len(cols) >= 2:
                        lbl = cols[0].get_text(strip=True)
                        if "Razón Social" in lbl:
                            val = cols[1].get_text(strip=True)
                            if val: rivales.append(val)
            
            data['rivales'] = list(set(rivales))
            data['num_licitadores'] = len(data['rivales'])

            # 6. DOCUMENTOS
            docs = []
            for l in soup.find_all('a', onclick=re.compile(r"descargarFichero")):
                fid = re.search(r"\(+'(\d+)'", l.get('onclick'))
                if fid:
                    ep = "descargaFicheroContratoPorIdFichero" if "Contrato" in l.get('onclick') else "descargaFicheroPorIdFichero"
                    docs.append({'nombre': l.get_text(strip=True), 'url': f"https://www.contratacion.euskadi.eus/ac70cPublicidadWar/downloadDokusiREST/{ep}?idFichero={fid.group(1)}&R01HNoPortal=true"})
            data['documentos'] = docs

            return data

        except Exception as e:
            print(f"      Error: {e}")
            return None

    def run(self):
        print("🚀 INICIANDO MONITOR CON URLs CORREGIDAS...")
        results = []
        
        for s in self.sources:
            print(f"📡 RSS: {s['tipo']} - {s['estado']}")
            try:
                r = requests.get(s['url'], headers=self.headers, timeout=20)
                if r.status_code != 200: 
                    print(f"   Error HTTP {r.status_code}")
                    continue
                
                # Parsear XML
                root = ET.fromstring(r.content)
                items = root.findall('.//item')
                print(f"   -> Encontrados {len(items)} items.")
                
                for item in items[:12]: # Límite de seguridad
                    link = item.find('link').text
                    if link not in self.processed_ids:
                        data = self.process_url(link, s['tipo'], s['estado'])
                        if data:
                            self.processed_ids.add(link)
                            results.append(data)
                            time.sleep(0.2)
            except Exception as e:
                print(f"   Error leyendo RSS: {e}")
        
        return results

if __name__ == "__main__":
    engine = MonitorEngine()
    data = engine.run()
    
    # Hora Madrid
    tz = timezone(timedelta(hours=1))
    now_str = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
    
    json_str = json.dumps(data, ensure_ascii=False)
    final_html = HTML_TEMPLATE.replace('__DATOS_JSON__', json_str).replace('__FECHA__', now_str)
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"\n✅ REPORTE GENERADO: {OUTPUT_FILE} con {len(data)} licitaciones.")
