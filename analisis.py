import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import json
import time
import hashlib
import os
import shutil
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN ---
HTML_FILE = "analisis.html" 
DB_FILE = "licitaciones_db.json"
BACKUP_DIR = "backups"

# --- PLANTILLA HTML (v8.0 - MARKET INTELLIGENCE EDITION) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Intelligence Hub | Licitaciones Euskadi</title>
    
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/buttons/2.4.2/css/buttons.bootstrap5.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">

    <style>
        :root { --primary: #0f172a; --accent: #2563eb; --bg: #f1f5f9; }
        body { background-color: var(--bg); font-family: 'Inter', sans-serif; font-size: 0.85rem; color: #1e293b; }
        
        /* Header & Dashboard */
        .glass-header { background: var(--primary); color: white; padding: 2rem 0; margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        .stat-card { background: white; border-radius: 12px; padding: 1.5rem; border: 1px solid #e2e8f0; height: 100%; transition: transform 0.2s; }
        .stat-card:hover { transform: translateY(-5px); }
        .stat-val { font-size: 1.8rem; font-weight: 800; color: var(--primary); }
        .stat-label { font-size: 0.7rem; text-transform: uppercase; font-weight: 700; color: #64748b; letter-spacing: 0.05em; }

        /* Filtros Pro */
        .filter-zone { background: white; border-radius: 12px; padding: 1.5rem; margin-bottom: 1.5rem; border: 1px solid #e2e8f0; }
        .btn-check:checked + .btn-outline-primary { background-color: var(--accent); border-color: var(--accent); color: white; }
        
        /* Tabla Estilo Excel Pro */
        .table-container { background: white; border-radius: 12px; border: 1px solid #e2e8f0; padding: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
        table.dataTable { border-collapse: collapse !important; }
        table.dataTable thead th { background: #f8fafc; color: #475569; font-weight: 700; text-transform: uppercase; font-size: 0.65rem; border-bottom: 2px solid #e2e8f0 !important; }
        .clickable-cell { color: var(--accent); cursor: pointer; font-weight: 600; }
        .clickable-cell:hover { text-decoration: underline; }

        /* Ranking Panel */
        .ranking-item { display: flex; align-items: center; padding: 0.75rem; border-bottom: 1px solid #f1f5f9; }
        .ranking-rank { width: 30px; font-weight: 800; color: #cbd5e1; }
        .ranking-name { flex: 1; font-weight: 600; font-size: 0.8rem; }
        .ranking-val { font-family: 'monospace'; font-weight: 700; color: var(--primary); }

        /* PDF & Print Optimization */
        @media print {
            .no-print, .dt-buttons, .dataTables_filter, .dataTables_length { display: none !important; }
            body { background: white; padding: 0; }
            .container-fluid { width: 100%; padding: 0; }
            .table-container { border: none; box-shadow: none; }
            table { font-size: 7pt !important; width: 100% !important; }
            .stat-card { border: 1px solid #eee; break-inside: avoid; }
            @page { size: landscape; margin: 0.5cm; }
        }
    </style>
</head>
<body>

<div class="glass-header no-print">
    <div class="container-fluid px-4">
        <div class="row align-items-center">
            <div class="col-md-6">
                <h3 class="fw-800 mb-1"><i class="bi bi-briefcase-fill me-2"></i>Market Intelligence Hub</h3>
                <p class="opacity-75 mb-0">Análisis Competitivo de Adjudicaciones Gipuzkoa</p>
            </div>
            <div class="col-md-6 text-md-end">
                <button class="btn btn-light btn-sm fw-700" onclick="window.print()"><i class="bi bi-file-earmark-pdf-fill me-1"></i>Exportar Informe PDF</button>
            </div>
        </div>
    </div>
</div>

<div class="container-fluid px-4">
    <div class="row g-3 mb-4 no-print">
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-label">Volumen Total Adjudicado</div>
                <div class="stat-val" id="stat-total">0 €</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-label">Baja Media del Mercado</div>
                <div class="stat-val text-success" id="stat-baja">0%</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-label">Competencia (Media Licitadores)</div>
                <div class="stat-val text-primary" id="stat-comp">0</div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="stat-card">
                <div class="stat-label">Empresas Adjudicatarias</div>
                <div class="stat-val" id="stat-empresas">0</div>
            </div>
        </div>
    </div>

    <div class="row g-4">
        <div class="col-xl-3 no-print">
            <div class="filter-zone mb-4">
                <h6 class="fw-800 mb-3"><i class="bi bi-funnel me-2"></i>Filtros Temporales</h6>
                <div class="d-grid gap-2">
                    <input type="radio" class="btn-check" name="timeFilter" id="t-all" checked onchange="filterTime('all')">
                    <label class="btn btn-outline-primary btn-sm text-start" for="t-all">Histórico Completo</label>
                    
                    <input type="radio" class="btn-check" name="timeFilter" id="t-24h" onchange="filterTime(1)">
                    <label class="btn btn-outline-primary btn-sm text-start" for="t-24h">Últimas 24 Horas</label>
                    
                    <input type="radio" class="btn-check" name="timeFilter" id="t-week" onchange="filterTime(7)">
                    <label class="btn btn-outline-primary btn-sm text-start" for="t-week">Última Semana</label>
                    
                    <input type="radio" class="btn-check" name="timeFilter" id="t-month" onchange="filterTime(30)">
                    <label class="btn btn-outline-primary btn-sm text-start" for="t-month">Último Mes</label>
                </div>

                <h6 class="fw-800 mt-4 mb-3"><i class="bi bi-check-circle me-2"></i>Estado del Contrato</h6>
                <div class="btn-group w-100" role="group">
                    <button type="button" class="btn btn-outline-secondary btn-sm" onclick="filterStatus('ADJUDICADO')">Adj.</button>
                    <button type="button" class="btn btn-outline-secondary btn-sm" onclick="filterStatus('FORMALIZADO')">Form.</button>
                    <button type="button" class="btn btn-outline-secondary btn-sm" onclick="filterStatus('')">Todos</button>
                </div>
            </div>

            <div class="filter-zone">
                <h6 class="fw-800 mb-3"><i class="bi bi-trophy me-2"></i>Top Licitadores (Cuota)</h6>
                <div id="ranking-list">
                    </div>
            </div>
        </div>

        <div class="col-xl-9">
            <div class="table-container">
                <table id="mainTable" class="table table-hover w-100">
                    <thead>
                        <tr>
                            <th>Fecha</th>
                            <th>Entidad Cliente</th>
                            <th>Objeto del Contrato</th>
                            <th>Adjudicatario</th>
                            <th>Importe (€)</th>
                            <th>Baja %</th>
                            <th>Lic.</th>
                            <th>Estado</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>
<script src="https://cdn.datatables.net/buttons/2.4.2/js/dataTables.buttons.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
<script src="https://cdn.datatables.net/buttons/2.4.2/js/buttons.html5.min.js"></script>

<script>
    const data = __DATOS_JSON__;
    const eur = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
    let table;

    $(document).ready(function() {
        initTable();
        updateDashboard(data);
        renderRanking(data);
    });

    function initTable() {
        table = $('#mainTable').DataTable({
            data: data,
            pageLength: 25,
            order: [[0, 'desc']],
            dom: 'Bfrtip',
            buttons: ['copy', 'excel'],
            columns: [
                { data: 'fecha_adjudicacion' },
                { data: 'entidad', className: 'clickable-cell', render: d => `<span onclick="filterByValue('${d}')">${d}</span>` },
                { data: 'objeto', render: d => `<div class="text-truncate" style="max-width:300px" title="${d}">${d}</div>` },
                { data: 'ganador', className: 'clickable-cell', render: (d,t,r) => `<span onclick="filterByValue('${d}')">${d}</span> ${r.es_ute ? '<small class="badge bg-indigo text-white">UTE</small>' : ''}` },
                { data: 'importe_adjudicacion', className: 'fw-bold text-end', render: d => eur.format(d) },
                { data: 'baja_pct', className: 'text-center', render: d => `<span class="badge ${d > 20 ? 'bg-danger' : 'bg-light text-dark'}">${d}%</span>` },
                { data: 'num_licitadores', className: 'text-center' },
                { data: 'estado_fase', render: d => `<span class="small fw-bold">${d.includes('ADJ') ? 'ADJ' : 'FORM'}</span>` }
            ],
            language: { url: '//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json' },
            drawCallback: function() {
                const api = this.api();
                updateDashboard(api.rows({filter:'applied'}).data().toArray());
            }
        });
    }

    function updateDashboard(filteredData) {
        let total = 0, bajas = 0, licitadores = 0, empresas = new Set();
        filteredData.forEach(r => {
            total += r.importe_adjudicacion;
            bajas += r.baja_pct;
            licitadores += r.num_licitadores;
            if(r.ganador !== 'Desconocido') empresas.add(r.ganador);
        });
        
        const count = filteredData.length || 1;
        $('#stat-total').text(eur.format(total));
        $('#stat-baja').text((bajas / count).toFixed(1) + '%');
        $('#stat-comp').text((licitadores / count).toFixed(1));
        $('#stat-empresas').text(empresas.size);
    }

    function renderRanking(currentData) {
        const stats = {};
        currentData.forEach(r => {
            if(r.ganador === 'Desconocido') return;
            if(!stats[r.ganador]) stats[r.ganador] = { sum: 0, count: 0 };
            stats[r.ganador].sum += r.importe_adjudicacion;
            stats[r.ganador].count++;
        });

        const sorted = Object.entries(stats).sort((a,b) => b[1].sum - a[1].sum).slice(0, 10);
        let html = '';
        sorted.forEach(([name, val], i) => {
            html += `
            <div class="ranking-item">
                <div class="ranking-rank">${i+1}</div>
                <div class="ranking-name text-truncate" onclick="filterByValue('${name}')" style="cursor:pointer">${name}</div>
                <div class="ranking-val">${(val.sum/1000000).toFixed(1)}M</div>
            </div>`;
        });
        $('#ranking-list').html(html);
    }

    function filterByValue(val) {
        table.search(val).draw();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function filterStatus(status) {
        table.column(7).search(status).draw();
    }

    function filterTime(days) {
        $.fn.dataTable.ext.search.pop();
        if(days !== 'all') {
            const cutoff = new Date();
            cutoff.setDate(cutoff.getDate() - days);
            
            $.fn.dataTable.ext.search.push((settings, data, index) => {
                const parts = data[0].split('/');
                const date = new Date(parts[2], parts[1]-1, parts[0]);
                return date >= cutoff;
            });
        }
        table.draw();
    }
</script>
</body>
</html>
"""

# --- MOTOR DE EXTRACCIÓN (PERSISTENTE CON NUEVA URL DE SERVICIOS) ---
class MonitorEngine:
    def __init__(self):
        self.sources = [
            {"tipo": "OBRA", "estado": "ADJUDICADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=5&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "OBRA", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=8&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "OBRA", "estado": "CERRADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=14&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "ADJUDICADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=5&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=8&p03=&p04=&p05=&p06=FALSE&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=10000.0&p14=2.0E7&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=01/01/2025&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "CERRADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=14&p03=&p04=&p05=&p06=FALSE&p07=&p08=&p09=&p10=&p11=&p12=01/01/2025&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"}
        ]
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.processed_ids = set()
        self.db = []
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    self.db = json.load(f)
                    self.processed_ids = {d['id'] for d in self.db}
                print(f"✅ DB cargada: {len(self.db)} registros.")
            except: pass

    def backup_db(self):
        if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
        if os.path.exists(DB_FILE):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(DB_FILE, f"{BACKUP_DIR}/db_backup_{timestamp}.json")
            print(f"🛡️ Backup creado: db_backup_{timestamp}.json")

    def clean_money(self, txt):
        if not txt: return 0.0
        try: return float(txt.replace('.', '').replace(',', '.'))
        except: return 0.0

    def get_tab_value(self, soup, tab_id, label):
        tab = soup.find('div', id=tab_id)
        if not tab: return None
        for row in tab.find_all('div', class_='row'):
            cols = row.find_all('div', recursive=False)
            if len(cols) >= 2 and label.lower() in cols[0].get_text(strip=True).lower():
                return cols[1].get_text(strip=True)
        return None

    def process_url(self, url, tipo, estado):
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(r.content, 'html.parser')
            data = {'id': hashlib.md5(url.encode()).hexdigest(), 'url_ficha': url, 'tipo_licitacion': tipo, 'estado_fase': estado}
            
            head = soup.find('div', class_='cabeceraDetalle')
            data['objeto'] = head.find('dd').get_text(strip=True) if head and head.find('dd') else "Sin descripción"

            if tipo == "SERV" and any(k in data['objeto'].lower() for k in ['redacción', 'proyecto', 'dirección de obra', 'asistencia técnica', 'consultoría', 'estudio', 'coordinación', 'ingeniería', 'arquitectura']):
                data['tipo_licitacion'] = "ING"

            fecha_adj = self.get_tab_value(soup, 'tabs-9', 'Fecha adjudicación')
            if not fecha_adj:
                for dt in soup.find_all('dt'):
                    if "última publicación" in dt.get_text():
                        dd = dt.find_next_sibling('dd')
                        if dd: fecha_adj = dd.get_text(strip=True).split(' ')[0]
                        break
            data['fecha_adjudicacion'] = fecha_adj or "Pendiente"
            data['entidad'] = self.get_tab_value(soup, 'tabs-2', 'Poder adjudicador') or "Desconocido"
            data['expediente'] = self.get_tab_value(soup, 'tabs-1', 'Expediente') or "N/A"

            base = self.get_tab_value(soup, 'tabs-4', 'Presupuesto del contrato sin IVA') or self.get_tab_value(soup, 'tabs-4', 'Valor estimado')
            adj = self.get_tab_value(soup, 'tabs-9', 'Precio sin IVA')
            data['presupuesto_base'] = self.clean_money(base)
            data['importe_adjudicacion'] = self.clean_money(adj)
            data['ganador'] = self.get_tab_value(soup, 'tabs-9', 'Razón social') or "Desconocido"

            ganador_upper = data['ganador'].upper()
            data['es_ute'] = any(x in ganador_upper for x in ['UTE', 'UNION TEMPORAL', 'UNIÓN TEMPORAL', 'ALDI BATERAKO'])

            if data['presupuesto_base'] > 0 and data['importe_adjudicacion'] > 0:
                data['baja_pct'] = round(((data['presupuesto_base'] - data['importe_adjudicacion']) / data['presupuesto_base']) * 100, 2)
            else: data['baja_pct'] = 0.0

            rivales = []
            tab8 = soup.find('div', id='tabs-8')
            if tab8:
                for row in tab8.find_all('div', class_='row'):
                    cols = row.find_all('div', recursive=False)
                    if len(cols) >= 2 and "Razón Social" in cols[0].get_text(strip=True):
                        rivales.append(cols[1].get_text(strip=True))
            data['rivales'] = list(set(rivales))
            data['num_licitadores'] = len(data['rivales'])

            docs = []
            for l in soup.find_all('a', onclick=re.compile(r"descargarFichero")):
                fid = re.search(r"\(+'(\d+)'", l.get('onclick'))
                if fid:
                    ep = "descargaFicheroContratoPorIdFichero" if "Contrato" in l.get('onclick') else "descargaFicheroPorIdFichero"
                    docs.append({'nombre': l.get_text(strip=True), 'url': f"https://www.contratacion.euskadi.eus/ac70cPublicidadWar/downloadDokusiREST/{ep}?idFichero={fid.group(1)}&R01HNoPortal=true"})
            data['documentos'] = docs
            return data
        except: return None

    def run(self):
        print("🚀 MONITOR v8.0 INICIANDO...")
        self.backup_db()
        new_items = 0
        for s in self.sources:
            try:
                r = requests.get(s['url'], headers=self.headers, timeout=20)
                if r.status_code != 200: continue
                root = ET.fromstring(r.content)
                for item in root.findall('.//item'):
                    link = item.find('link').text
                    if link not in self.processed_ids:
                        print(f" + Procesando: {link[-20:]}")
                        data = self.process_url(link, s['tipo'], s['estado'])
                        if data:
                            self.processed_ids.add(link)
                            self.db.append(data)
                            new_items += 1
                            time.sleep(0.1)
            except Exception as e: print(f"Error RSS: {e}")
        
        if new_items > 0:
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, ensure_ascii=False, indent=2)
            print(f"💾 Guardados {new_items} nuevos expedientes.")
        else: print("💤 Sin novedades.")
        return self.db

if __name__ == "__main__":
    engine = MonitorEngine()
    data = engine.run()
    now_str = datetime.now(timezone(timedelta(hours=1))).strftime("%d/%m/%Y %H:%M")
    html = HTML_TEMPLATE.replace('__DATOS_JSON__', json.dumps(data, ensure_ascii=False)).replace('__FECHA__', now_str)
    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(html)
    print(f"✅ Dashboard generado: {HTML_FILE}")
