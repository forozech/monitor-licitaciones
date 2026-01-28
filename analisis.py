import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import json
import time
import hashlib
import os
from datetime import datetime, timedelta, timezone

# --- CONFIGURACIÓN ---
OUTPUT_FILE = "analisis.html"

# --- PLANTILLA HTML (DASHBOARD PROFESIONAL) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor de Licitaciones | Euskadi</title>
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <style>
        :root {
            --bs-primary-rgb: 13, 110, 253;
            --bg-color: #f8f9fa;
            --card-shadow: 0 2px 12px rgba(0,0,0,0.04);
        }
        body { background-color: var(--bg-color); font-family: 'Segoe UI', system-ui, sans-serif; }
        
        /* KPIs */
        .kpi-card {
            background: white; border: none; border-radius: 12px;
            padding: 20px; box-shadow: var(--card-shadow);
            position: relative; overflow: hidden; height: 100%;
        }
        .kpi-icon {
            position: absolute; right: -10px; top: -10px;
            font-size: 4rem; opacity: 0.05; color: #0d6efd;
        }
        .kpi-value { font-size: 1.8rem; font-weight: 700; color: #2c3e50; margin-bottom: 0;}
        .kpi-label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: #6c757d; font-weight: 600; }

        /* Contenedores */
        .table-card { background: white; border-radius: 12px; box-shadow: var(--card-shadow); padding: 20px; border: none; margin-bottom: 20px; }
        
        /* Tabla */
        table.dataTable thead th { background-color: #f8f9fa; border-bottom: 2px solid #e9ecef !important; font-size: 0.85rem; text-transform: uppercase; color: #495057; }
        table.dataTable tbody td { vertical-align: middle; font-size: 0.9rem; }
        
        /* Badges de Baja */
        .badge-baja { font-weight: 700; padding: 5px 8px; border-radius: 6px; min-width: 55px; display: inline-block; text-align: center; font-size: 0.8rem;}
        .baja-alta { background-color: #d1fae5; color: #065f46; } /* > 15% */
        .baja-media { background-color: #fef3c7; color: #92400e; } /* 5-15% */
        .baja-baja { background-color: #fee2e2; color: #991b1b; } /* < 5% */
        .baja-negativa { background-color: #f3f4f6; color: #374151; } /* 0% */

        /* Etiquetas */
        .badge-tipo { font-size: 0.7rem; padding: 4px 6px; border-radius: 4px; border: 1px solid transparent; }
        .badge-obra { background-color: #e0f2fe; color: #0369a1; border-color: #bae6fd; }
        .badge-serv { background-color: #f3e8ff; color: #7e22ce; border-color: #e9d5ff; }

        /* Modal */
        .modal-content { border-radius: 16px; border: none; box-shadow: 0 10px 40px rgba(0,0,0,0.1); }
        .modal-header { background: #f8f9fa; border-radius: 16px 16px 0 0; border-bottom: 1px solid #eee; }
        .rival-list { max-height: 300px; overflow-y: auto; }
        .rival-item { padding: 10px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: center; font-size: 0.9rem;}
        .rival-item:last-child { border-bottom: none; }
        .rival-winner { background-color: #ecfdf5; font-weight: 600; color: #065f46; border-radius: 6px; }
    </style>
</head>
<body>
    <div class="container-fluid px-4 py-4">
        <div class="d-flex justify-content-between align-items-end mb-4">
            <div>
                <h2 class="fw-bold text-dark mb-0">Monitor de Licitaciones</h2>
                <p class="text-muted mb-0 small">Gipuzkoa | Adjudicaciones y Formalizaciones 2025</p>
            </div>
            <div class="text-end">
                <span class="badge bg-light text-secondary border">Actualizado: <span id="lastUpdate">__FECHA__</span></span>
            </div>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-lg-3 col-md-6"><div class="kpi-card"><i class="bi bi-cash-coin kpi-icon"></i><div class="kpi-label">Volumen Total</div><div class="kpi-value" id="kpi-volumen">0 €</div></div></div>
            <div class="col-lg-3 col-md-6"><div class="kpi-card"><i class="bi bi-graph-down-arrow kpi-icon"></i><div class="kpi-label">Baja Media</div><div class="kpi-value text-primary" id="kpi-baja">0%</div></div></div>
            <div class="col-lg-3 col-md-6"><div class="kpi-card"><i class="bi bi-people kpi-icon"></i><div class="kpi-label">Competencia Media</div><div class="kpi-value" id="kpi-licitadores">0</div><div class="small text-muted">Empresas / Licitación</div></div></div>
            <div class="col-lg-3 col-md-6"><div class="kpi-card"><i class="bi bi-file-earmark-text kpi-icon"></i><div class="kpi-label">Contratos Analizados</div><div class="kpi-value" id="kpi-contratos">0</div></div></div>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-md-8">
                <div class="table-card h-100">
                    <h6 class="fw-bold text-secondary text-uppercase small mb-3">Distribución de Bajas (%)</h6>
                    <div style="height: 200px;"><canvas id="chartBajas"></canvas></div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="table-card h-100">
                    <h6 class="fw-bold text-secondary text-uppercase small mb-3">Top Adjudicatarios</h6>
                    <div style="height: 200px; position: relative;"><canvas id="chartWinners"></canvas></div>
                </div>
            </div>
        </div>

        <div class="table-card">
            <table id="tablaContratos" class="table table-hover w-100">
                <thead>
                    <tr>
                        <th width="10%">Exp.</th>
                        <th width="35%">Objeto / Ganador</th>
                        <th width="12%" class="text-end">Presupuesto</th>
                        <th width="12%" class="text-end">Adjudicación</th>
                        <th width="8%" class="text-center">Baja</th>
                        <th width="5%" class="text-center">Lic.</th>
                        <th width="10%" class="text-center">Estado</th>
                        <th width="8%"></th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <div class="modal fade" id="modalDetalle" tabindex="-1">
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title fw-bold">Detalle del Expediente</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-light border mb-4">
                        <small class="text-uppercase text-muted fw-bold" style="font-size: 0.7rem;">Objeto del contrato</small>
                        <p class="mb-0 fw-bold text-dark" id="modalObjeto" style="line-height: 1.4;">...</p>
                    </div>

                    <div class="row mb-4">
                        <div class="col-6">
                            <div class="p-3 bg-light rounded border">
                                <span class="d-block text-muted small text-uppercase fw-bold">Presupuesto Base</span>
                                <span class="h5 fw-bold text-dark mb-0" id="modalBase">0 €</span>
                            </div>
                        </div>
                        <div class="col-6">
                            <div class="p-3 bg-white rounded border border-success">
                                <span class="d-block text-success small text-uppercase fw-bold">Importe Adjudicación</span>
                                <span class="h5 fw-bold text-success mb-0" id="modalAdj">0 €</span>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-7 border-end">
                            <h6 class="fw-bold mb-3 small text-uppercase">Empresas Presentadas (<span id="modalNumLic">0</span>)</h6>
                            <div id="modalRivales" class="rival-list"></div>
                        </div>
                        <div class="col-md-5 ps-md-4">
                            <h6 class="fw-bold mb-3 small text-uppercase">Documentación</h6>
                            <div id="modalDocs" class="d-grid gap-2"></div>
                            <div class="mt-3 pt-3 border-top text-center">
                                <a id="linkFicha" href="#" target="_blank" class="btn btn-sm btn-outline-primary">Ver Ficha Original <i class="bi bi-box-arrow-up-right ms-1"></i></a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>

    <script>
        // DATOS INYECTADOS
        const datos = __DATOS_JSON__;
        
        // Configuración Moneda
        const eur = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });

        $(document).ready(function() {
            renderDashboard(datos);
        });

        function renderDashboard(data) {
            // 1. Calcular KPIs
            let vol = 0, sumBaja = 0, sumLic = 0, winners = {};
            data.forEach(d => {
                vol += d.importe_adjudicacion;
                sumBaja += d.baja_pct;
                sumLic += d.num_licitadores;
                let w = d.ganador.length > 20 ? d.ganador.substring(0, 20) + '...' : d.ganador;
                if(d.ganador !== "Desconocido") winners[w] = (winners[w] || 0) + 1;
            });

            $('#kpi-volumen').text(eur.format(vol));
            $('#kpi-baja').text((data.length ? (sumBaja / data.length) : 0).toFixed(2) + '%');
            $('#kpi-licitadores').text((data.length ? (sumLic / data.length) : 0).toFixed(1));
            $('#kpi-contratos').text(data.length);

            // 2. Gráficos
            renderCharts(data, winners);

            // 3. Tabla
            $('#tablaContratos').DataTable({
                data: data,
                language: { url: "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json" },
                pageLength: 25,
                order: [[ 4, "desc" ]], // Ordenar por % Baja descendente
                columns: [
                    { data: 'expediente', render: d => `<span class="fw-bold text-dark small">${d}</span>` },
                    { data: null, render: d => `
                        <div style="line-height:1.2">
                            <span class="d-block fw-bold text-primary" style="font-size:0.85rem">${d.ganador}</span>
                            <span class="d-block text-muted text-truncate small" style="max-width: 250px;" title="${d.objeto}">${d.objeto}</span>
                        </div>` 
                    },
                    { data: 'presupuesto_base', className: 'text-end', render: d => `<span class="text-secondary small">${eur.format(d)}</span>` },
                    { data: 'importe_adjudicacion', className: 'text-end', render: d => `<span class="fw-bold text-dark small">${eur.format(d)}</span>` },
                    { data: 'baja_pct', className: 'text-center', render: d => {
                        let cls = 'baja-negativa';
                        if(d >= 15) cls = 'baja-alta';
                        else if(d >= 5) cls = 'baja-media';
                        else if(d > 0) cls = 'baja-baja';
                        return `<span class="badge-baja ${cls}">${d}%</span>`;
                    }},
                    { data: 'num_licitadores', className: 'text-center', render: d => `<span class="badge bg-light text-dark border">${d}</span>` },
                    { data: null, className: 'text-center', render: d => {
                        let cls = d.tipo_licitacion === 'OBRA' ? 'badge-obra' : 'badge-serv';
                        return `<span class="badge-tipo ${cls} me-1">${d.tipo_licitacion}</span><span class="badge-tipo bg-white border text-secondary">${d.estado_fase.substring(0,3)}</span>`;
                    }},
                    { data: null, orderable: false, render: (d, type, row, meta) => `
                        <button class="btn btn-sm btn-outline-secondary border-0" onclick='verDetalle(${meta.row})'><i class="bi bi-eye-fill"></i></button>` 
                    }
                ]
            });
        }

        function renderCharts(data, winners) {
            // Chart Bajas
            const ranges = [0, 0, 0, 0];
            data.forEach(d => {
                if(d.baja_pct < 5) ranges[0]++;
                else if(d.baja_pct < 10) ranges[1]++;
                else if(d.baja_pct < 20) ranges[2]++;
                else ranges[3]++;
            });

            new Chart(document.getElementById('chartBajas'), {
                type: 'bar',
                data: {
                    labels: ['< 5%', '5-10%', '10-20%', '> 20%'],
                    datasets: [{ data: ranges, backgroundColor: ['#fee2e2', '#fef3c7', '#d1fae5', '#059669'], borderRadius: 4 }]
                },
                options: { 
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } }, 
                    scales: { y: { display: false }, x: { grid: { display: false } } } 
                }
            });

            // Chart Winners
            const sorted = Object.entries(winners).sort((a,b) => b[1]-a[1]).slice(0, 5);
            new Chart(document.getElementById('chartWinners'), {
                type: 'doughnut',
                data: {
                    labels: sorted.map(x => x[0]),
                    datasets: [{ data: sorted.map(x => x[1]), backgroundColor: ['#3b82f6', '#6366f1', '#8b5cf6', '#a855f7', '#d946ef'], borderWidth: 0 }]
                },
                options: { 
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { position: 'right', labels: { boxWidth: 10, font: { size: 10 } } } },
                    cutout: '70%'
                }
            });
        }

        window.verDetalle = function(idx) {
            const d = datos[idx];
            $('#modalObjeto').text(d.objeto);
            $('#modalBase').text(eur.format(d.presupuesto_base));
            $('#modalAdj').text(eur.format(d.importe_adjudicacion));
            $('#modalNumLic').text(d.num_licitadores);
            $('#linkFicha').attr('href', d.url_ficha);

            let htmlRivales = '';
            d.rivales.forEach(r => {
                const isWinner = r === d.ganador;
                htmlRivales += `<div class="rival-item ${isWinner ? 'rival-winner' : ''}">
                    <span>${r}</span>
                    ${isWinner ? '<i class="bi bi-trophy-fill text-success"></i>' : ''}
                </div>`;
            });
            $('#modalRivales').html(htmlRivales || '<div class="text-center text-muted py-3 small">No hay información de competencia</div>');

            let htmlDocs = '';
            d.documentos.forEach(doc => {
                htmlDocs += `<a href="${doc.url}" target="_blank" class="btn btn-outline-secondary btn-sm text-start text-truncate mb-1">
                    <i class="bi bi-file-earmark-pdf text-danger me-2"></i>${doc.nombre}
                </a>`;
            });
            $('#modalDocs').html(htmlDocs || '<div class="text-center text-muted py-3 small">Sin documentos públicos</div>');

            new bootstrap.Modal('#modalDetalle').show();
        };
    </script>
</body>
</html>
"""

# --- MOTOR DE INTELIGENCIA (EXTRACTOR) ---
class MonitorEngine:
    def __init__(self):
        # RSS CORREGIDOS Y COMPLETOS
        self.sources = [
            # OBRAS
            {"tipo": "OBRA", "estado": "ADJUDICADO",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=5&p11=01/01/2025&p26=ES212&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "OBRA", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=8&p11=01/01/2025&p26=ES212&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "OBRA", "estado": "CERRADO",     "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=14&p11=01/01/2025&p26=ES212&p45=1&idioma=es&R01HNoPortal=true"},
            # SERVICIOS (URL FORMALIZADO ARREGLADA)
            {"tipo": "SERV", "estado": "ADJUDICADO",  "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=5&p11=01/01/2025&p26=ES212&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=8&p11=01/01/2025&p26=ES212&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "CERRADO",     "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=14&p11=01/01/2025&p26=ES212&p45=1&idioma=es&R01HNoPortal=true"}
        ]
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        self.processed_ids = set()

    def clean_money(self, txt):
        """Convierte texto de moneda español a float"""
        if not txt: return 0.0
        try: return float(txt.replace('.', '').replace(',', '.'))
        except: return 0.0

    def get_tab_value(self, soup, tab_id, label):
        """Busca valor en una fila de bootstrap dentro de una pestaña específica"""
        tab = soup.find('div', id=tab_id)
        if not tab: return None
        # Buscar en todas las filas de la pestaña
        for row in tab.find_all('div', class_='row'):
            text_row = row.get_text(" ", strip=True).lower()
            if label.lower() in text_row:
                # El valor suele estar en la columna col-*-8
                val_div = row.find('div', class_=re.compile(r'col-.*-8'))
                return val_div.get_text(strip=True) if val_div else None
        return None

    def process_url(self, url, tipo, estado):
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            r.encoding = 'utf-8' # Asegurar codificación
            soup = BeautifulSoup(r.text, 'html.parser')
            
            data = {
                'id': hashlib.md5(url.encode()).hexdigest(),
                'url_ficha': url,
                'tipo_licitacion': tipo,
                'estado_fase': estado
            }

            # 1. Objeto (Header)
            head = soup.find('div', class_='cabeceraDetalle')
            data['objeto'] = head.find('dd').get_text(strip=True) if head and head.find('dd') else "Sin descripción"

            # 2. Datos Generales (Tab 1)
            data['expediente'] = self.get_tab_value(soup, 'tabs-1', 'Expediente')
            
            # 3. Económicos (Tab 4 & Tab 9)
            base_str = self.get_tab_value(soup, 'tabs-4', 'Presupuesto del contrato sin IVA')
            adj_str = self.get_tab_value(soup, 'tabs-9', 'Precio sin IVA')
            
            data['presupuesto_base'] = self.clean_money(base_str)
            data['importe_adjudicacion'] = self.clean_money(adj_str)
            data['ganador'] = self.get_tab_value(soup, 'tabs-9', 'Razón social') or "Desconocido"

            # 4. Cálculo de Baja
            if data['presupuesto_base'] > 0 and data['importe_adjudicacion'] > 0:
                ahorro = data['presupuesto_base'] - data['importe_adjudicacion']
                data['baja_pct'] = round((ahorro / data['presupuesto_base']) * 100, 2)
            else:
                data['baja_pct'] = 0.0

            # 5. Competencia (Tab 8)
            rivales = []
            tab8 = soup.find('div', id='tabs-8')
            if tab8:
                for row in tab8.find_all('div', class_='row'):
                    if "Razón Social" in row.get_text():
                        v = row.find('div', class_=re.compile(r'col-.*-8'))
                        if v: rivales.append(v.get_text(strip=True))
            data['rivales'] = list(set(rivales)) # Eliminar duplicados
            data['num_licitadores'] = len(data['rivales'])

            # 6. Documentos (Tab 5 - Decodificar onclick)
            docs = []
            links = soup.find_all('a', onclick=re.compile(r"descargarFichero"))
            for l in links:
                fid = re.search(r"\(+'(\d+)'", l.get('onclick'))
                if fid:
                    fid_num = fid.group(1)
                    # Determinar endpoint según si es contrato o doc normal
                    endpoint = "descargaFicheroContratoPorIdFichero" if "Contrato" in l.get('onclick') else "descargaFicheroPorIdFichero"
                    url_doc = f"https://www.contratacion.euskadi.eus/ac70cPublicidadWar/downloadDokusiREST/{endpoint}?idFichero={fid_num}&R01HNoPortal=true"
                    docs.append({'nombre': l.get_text(strip=True), 'url': url_doc})
            data['documentos'] = docs

            return data

        except Exception as e:
            print(f"Error procesando {url}: {e}")
            return None

    def run(self):
        print("🚀 INICIANDO MONITOR DE LICITACIONES...")
        results = []
        
        for s in self.sources:
            print(f"📡 Verificando Feed: {s['tipo']} - {s['estado']}")
            try:
                r = requests.get(s['url'], headers=self.headers, timeout=20)
                # Parseo XML manual para evitar fallos de librerías estrictas
                root = ET.fromstring(r.content)
                
                # Procesar últimos 15 items por feed para no saturar
                items = root.findall('.//item')[:15]
                print(f"   -> Encontrados {len(items)} contratos.")
                
                for item in items:
                    link = item.find('link').text
                    if link not in self.processed_ids:
                        data = self.process_url(link, s['tipo'], s['estado'])
                        if data:
                            self.processed_ids.add(link)
                            results.append(data)
                            # Pequeña pausa para no ser baneados
                            time.sleep(0.2)
            except Exception as e:
                print(f"⚠️ Error en Feed {s['url']}: {e}")
        
        return results

# --- EJECUCIÓN PRINCIPAL ---
if __name__ == "__main__":
    engine = MonitorEngine()
    data = engine.run()
    
    # Obtener fecha hora España
    tz = timezone(timedelta(hours=1))
    now_str = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
    
    # Inyectar JSON en la plantilla HTML
    json_str = json.dumps(data, ensure_ascii=False)
    final_html = HTML_TEMPLATE.replace('__DATOS_JSON__', json_str)
    final_html = final_html.replace('__FECHA__', now_str)
    
    # Guardar archivo
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"\n✅ GENERACIÓN COMPLETADA. {len(data)} contratos procesados en {OUTPUT_FILE}")
