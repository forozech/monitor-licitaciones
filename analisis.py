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

# --- PLANTILLA HTML (LIGERA, SIN GRÁFICOS, CON FILTRO INGENIERÍA) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es" data-bs-theme="light">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor Licitaciones | Euskadi 2025</title>
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
    
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
    <script src="https://npmcdn.com/flatpickr/dist/l10n/es.js"></script>

    <style>
        :root { --bs-primary-rgb: 13, 110, 253; --bg-color: #f0f2f5; --card-radius: 12px; }
        body { background-color: var(--bg-color); font-family: 'Segoe UI', system-ui, sans-serif; font-size: 0.85rem; }
        
        /* KPIs Compactos */
        .kpi-card { 
            background: white; border: none; border-radius: var(--card-radius); padding: 15px 20px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: 100%; position: relative; overflow: hidden; 
            cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;
        }
        .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-left: 4px solid #0d6efd; }
        .kpi-value { font-size: 1.6rem; font-weight: 800; color: #1e293b; margin-bottom: 0; line-height: 1.2; }
        .kpi-label { font-size: 0.7rem; text-transform: uppercase; color: #64748b; font-weight: 700; letter-spacing: 0.5px; }
        .kpi-icon { position: absolute; right: -5px; top: -5px; font-size: 4rem; opacity: 0.05; transform: rotate(10deg); color: #000; }

        /* Filtros Superiores */
        .filters-bar { background: white; padding: 15px; border-radius: var(--card-radius); margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-wrap: wrap; gap: 15px; align-items: center; justify-content: space-between; }
        .btn-filter { font-weight: 600; font-size: 0.85rem; border-radius: 20px; padding: 6px 16px; border: 1px solid #e2e8f0; color: #64748b; background: white; transition: all 0.2s; }
        .btn-filter.active, .btn-filter:hover { background-color: #eff6ff; color: #2563eb; border-color: #bfdbfe; }
        .date-input { border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 12px; font-size: 0.85rem; width: 130px; }

        /* Tabla */
        .dashboard-card { background: white; border-radius: var(--card-radius); box-shadow: 0 2px 4px rgba(0,0,0,0.05); padding: 20px; margin-bottom: 20px; }
        
        table.dataTable thead th { background-color: #f8fafc; color: #475569; font-weight: 700; text-transform: uppercase; font-size: 0.7rem; border-bottom: 2px solid #e2e8f0 !important; vertical-align: middle; }
        table.dataTable tbody td { vertical-align: middle; color: #334155; padding: 8px 10px; }
        
        /* Badges */
        .badge-baja { font-weight: 700; padding: 3px 8px; border-radius: 6px; min-width: 45px; display: inline-block; text-align: center; }
        .baja-alta { background-color: #dcfce7; color: #166534; }
        .baja-media { background-color: #fef9c3; color: #854d0e; }
        .baja-baja { background-color: #fee2e2; color: #991b1b; }
        .badge-tipo { font-size: 0.65rem; padding: 3px 6px; border-radius: 4px; border: 1px solid #e2e8f0; background: #f8fafc; color: #475569; text-transform: uppercase; }
        
        /* Interacción Ganador */
        .winner-link { cursor: pointer; color: #0f172a; font-weight: 700; text-decoration: none; transition: color 0.2s; }
        .winner-link:hover { color: #2563eb; text-decoration: underline; }
        .filter-active-info { display: none; background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; padding: 8px 15px; border-radius: 8px; margin-bottom: 15px; font-size: 0.9rem; align-items: center; justify-content: space-between; }
    </style>
</head>
<body>
    <div class="offcanvas offcanvas-start" tabindex="-1" id="offcanvasFiltros">
        <div class="offcanvas-header bg-light">
            <h5 class="offcanvas-title fw-bold text-primary"><i class="bi bi-sliders me-2"></i>Filtros Avanzados</h5>
            <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
        </div>
        <div class="offcanvas-body">
            <p class="small text-muted mb-4">Segmentar datos de la tabla.</p>
            <div class="mb-4">
                <label class="form-label fw-bold small text-uppercase text-secondary">Estado</label>
                <select class="form-select form-select-sm" id="filtroEstado">
                    <option value="">Todos</option>
                    <option value="ADJUDICADO">Adjudicados</option>
                    <option value="FORMALIZADO">Formalizados</option>
                    <option value="CERRADO">Cerrados</option>
                </select>
            </div>
            <div class="mb-4">
                <label class="form-label fw-bold small text-uppercase text-secondary">Baja (%)</label>
                <div class="input-group input-group-sm">
                    <input type="number" class="form-control" placeholder="Min" id="bajaMin">
                    <span class="input-group-text">-</span>
                    <input type="number" class="form-control" placeholder="Max" id="bajaMax">
                </div>
            </div>
            <div class="d-grid">
                <button class="btn btn-primary btn-sm" onclick="aplicarFiltrosSidebar()">Aplicar</button>
                <button class="btn btn-link btn-sm text-muted mt-2" onclick="limpiarFiltros()">Limpiar</button>
            </div>
        </div>
    </div>

    <div class="container-fluid px-4 py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h3 class="fw-bold text-dark mb-0"><i class="bi bi-layers-half text-primary me-2"></i>Monitor Licitaciones</h3>
                <p class="text-muted mb-0 small">Gipuzkoa | Actualizado: <span id="lastUpdate">__FECHA__</span></p>
            </div>
        </div>

        <div class="filters-bar">
            <div class="d-flex gap-2">
                <button class="btn-filter active" onclick="filterType('all', this)">Todos</button>
                <button class="btn-filter" onclick="filterType('OBRA', this)">Obras</button>
                <button class="btn-filter" onclick="filterType('SERV', this)">Servicios</button>
                <button class="btn-filter" onclick="filterType('ING', this)">Ingeniería</button>
            </div>
            <div class="d-flex gap-2 align-items-center">
                <span class="small fw-bold text-muted text-uppercase me-2"><i class="bi bi-calendar-event me-1"></i>Fecha Adj:</span>
                <input type="text" class="date-input flatpickr" id="dateFrom" placeholder="Desde...">
                <input type="text" class="date-input flatpickr" id="dateTo" placeholder="Hasta...">
            </div>
        </div>

        <div id="activeFilterAlert" class="filter-active-info">
            <span><i class="bi bi-funnel-fill me-2"></i>Empresa: <strong id="filterName">...</strong></span>
            <button class="btn btn-sm btn-close" onclick="limpiarBusqueda()"></button>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar()"><i class="bi bi-cash-coin kpi-icon"></i><div class="kpi-label">Volumen Total</div><div class="kpi-value" id="kpi-volumen">0 €</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar()"><i class="bi bi-graph-down-arrow kpi-icon"></i><div class="kpi-label">Baja Media</div><div class="kpi-value text-primary" id="kpi-baja">0%</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar()"><i class="bi bi-people kpi-icon"></i><div class="kpi-label">Media Lic.</div><div class="kpi-value" id="kpi-licitadores">0</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar()"><i class="bi bi-files kpi-icon"></i><div class="kpi-label">Contratos</div><div class="kpi-value" id="kpi-contratos">0</div></div></div>
        </div>

        <div class="dashboard-card">
            <table id="tablaContratos" class="table table-hover w-100">
                <thead>
                    <tr>
                        <th width="8%">Fecha Adj.</th>
                        <th width="8%">Tipo</th>
                        <th width="22%">Entidad / Objeto</th>
                        <th width="15%">Ganador</th>
                        <th width="10%" class="text-end">Presupuesto</th>
                        <th width="10%" class="text-end">Adjudicación</th>
                        <th width="5%" class="text-center">Baja</th>
                        <th width="5%" class="text-center">Lic.</th>
                        <th width="5%" class="text-center"></th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <div class="modal fade" id="modalDetalle" tabindex="-1"><div class="modal-dialog modal-lg modal-dialog-centered"><div class="modal-content"><div class="modal-header bg-light"><h5 class="modal-title fw-bold">Detalle del Expediente</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body">
        <div class="mb-3"><span class="badge bg-primary mb-2" id="modalTipo">Tipo</span><h5 class="fw-bold" id="modalObjeto">...</h5><p class="text-muted small mb-0"><i class="bi bi-building me-1"></i><span id="modalEntidad">Entidad</span> | Exp: <span id="modalExp"></span></p></div>
        <div class="row mb-4"><div class="col-md-6"><div class="p-3 border rounded bg-light"><small class="text-uppercase fw-bold text-muted">Presupuesto Base</small><div class="fs-5 fw-bold text-dark" id="modalBase">0 €</div></div></div><div class="col-md-6"><div class="p-3 border rounded border-success bg-opacity-10"><small class="text-uppercase fw-bold text-success">Importe Adjudicación</small><div class="fs-5 fw-bold text-success" id="modalAdj">0 €</div></div></div></div>
        <div class="row"><div class="col-md-7 border-end"><h6 class="fw-bold small text-uppercase mb-3">Empresas Participantes (<span id="modalNumLic">0</span>)</h6><div id="modalRivales" class="v-stack gap-2" style="max-height:250px; overflow-y:auto;"></div></div><div class="col-md-5 ps-3"><h6 class="fw-bold small text-uppercase mb-3">Documentación</h6><div id="modalDocs" class="d-grid gap-2"></div><div class="mt-4"><a id="linkFicha" href="#" target="_blank" class="btn btn-outline-primary w-100 btn-sm"><i class="bi bi-box-arrow-up-right me-2"></i>Ver en Euskadi.eus</a></div></div></div>
    </div></div></div></div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>
    
    <script>
        const datos = __DATOS_JSON__;
        const eur = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
        let table;

        $(document).ready(function() {
            initDatePickers();
            initTable();
            updateKPIs(datos);
        });

        function initDatePickers() {
            flatpickr(".date-input", { dateFormat: "d/m/Y", locale: "es", onChange: function() { table.draw(); } });
        }

        function initTable() {
            // Filtro Fecha
            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                const min = $('#dateFrom').val() ? parseDate($('#dateFrom').val()) : null;
                const max = $('#dateTo').val() ? parseDate($('#dateTo').val()) : null;
                const dateData = parseDate(data[0]); 
                if ( (min === null && max === null) || (min === null && dateData <= max) || (min <= dateData && max === null) || (min <= dateData && dateData <= max) ) return true;
                return false;
            });
            
            // Filtros Sidebar
            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
               const estadoFilter = $('#filtroEstado').val();
               const minBaja = parseFloat($('#bajaMin').val());
               const maxBaja = parseFloat($('#bajaMax').val());
               const estado = data[9]; // Columna oculta estado
               const baja = parseFloat(data[6].replace('%','').replace(',','.'));
               
               if(estadoFilter && !estado.includes(estadoFilter)) return false;
               if(!isNaN(minBaja) && baja < minBaja) return false;
               if(!isNaN(maxBaja) && baja > maxBaja) return false;
               return true;
            });

            table = $('#tablaContratos').DataTable({
                data: datos,
                language: { url: "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json" },
                pageLength: 20,
                order: [[ 0, "desc" ]],
                columns: [
                    { data: 'fecha_adjudicacion', render: (d,t,r) => {
                        const parts = d.split('/');
                        const sortVal = parts.length===3 ? parts[2]+parts[1]+parts[0] : 0;
                        return `<span class="d-none">${sortVal}</span><span class="small fw-bold text-nowrap">${d}</span>`;
                    }},
                    { data: 'tipo_licitacion', className: 'text-center', render: d => {
                        let color = d==='ING' ? '#8b5cf6' : (d==='OBRA' ? '#ef4444' : '#3b82f6');
                        return `<span class="badge-tipo" style="color:${color};border-color:${color}40;background:${color}10">${d}</span>`;
                    }},
                    { data: null, render: d => `<div style="line-height:1.2"><span class="d-block text-truncate small fw-bold text-dark" style="max-width:280px" title="${d.entidad}">${d.entidad}</span><span class="d-block text-muted text-truncate small" style="max-width:280px" title="${d.objeto}">${d.objeto}</span></div>` },
                    { data: 'ganador', render: d => `<a onclick="filtrarPorGanador('${d}')" class="winner-link text-truncate d-block small" style="max-width:180px" title="Ver todo de ${d}">${d}</a>` },
                    { data: 'presupuesto_base', className: 'text-end', render: d => `<span class="text-secondary small text-nowrap">${eur.format(d)}</span>` },
                    { data: 'importe_adjudicacion', className: 'text-end', render: d => `<span class="fw-bold small text-dark text-nowrap">${eur.format(d)}</span>` },
                    { data: 'baja_pct', className: 'text-center', render: d => {
                        let cls = d >= 20 ? 'baja-alta' : d >= 10 ? 'baja-media' : d > 0 ? 'baja-baja' : 'bg-light text-muted';
                        return `<span class="badge-baja ${cls}">${d}%</span>`;
                    }},
                    { data: 'num_licitadores', className: 'text-center', render: d => `<span class="badge bg-white border text-dark shadow-sm">${d}</span>` },
                    { data: null, orderable: false, className: 'text-end', render: (d,t,r,m) => `<button class="btn btn-sm btn-light border" onclick='verDetalle(${m.row})'><i class="bi bi-eye"></i></button>` },
                    { data: 'estado_fase', visible: false }
                ]
            });

            table.on('draw', function() {
                const filteredData = table.rows({ filter: 'applied' }).data().toArray();
                updateKPIs(filteredData);
            });
        }

        function updateKPIs(data) {
            let vol = 0, sumBaja = 0, countBaja = 0, sumLic = 0;
            data.forEach(d => {
                vol += d.importe_adjudicacion;
                if(d.baja_pct > 0) { sumBaja += d.baja_pct; countBaja++; }
                sumLic += d.num_licitadores;
            });
            $('#kpi-volumen').text(eur.format(vol));
            $('#kpi-baja').text((countBaja ? (sumBaja / countBaja) : 0).toFixed(2) + '%');
            $('#kpi-licitadores').text((data.length ? (sumLic / data.length) : 0).toFixed(1));
            $('#kpi-contratos').text(data.length);
        }

        function filterType(type, btn) {
            $('.btn-filter').removeClass('active');
            $(btn).addClass('active');
            if(type === 'all') table.column(1).search('').draw();
            else table.column(1).search(type).draw();
        }

        function filtrarPorGanador(nombre) {
            table.search(nombre).draw();
            $('#filterName').text(nombre);
            $('#activeFilterAlert').css('display', 'flex');
        }

        function limpiarBusqueda() {
            table.search('').draw();
            $('#activeFilterAlert').hide();
        }
        
        function aplicarFiltrosSidebar() { table.draw(); bootstrap.Offcanvas.getInstance('#offcanvasFiltros').hide(); }
        function limpiarFiltros() { $('#filtroEstado').val(''); $('#bajaMin').val(''); $('#bajaMax').val(''); table.draw(); }
        function openSidebar() { new bootstrap.Offcanvas('#offcanvasFiltros').show(); }
        function parseDate(d) { if(!d) return null; const p = d.split('/'); return new Date(p[2], p[1]-1, p[0]); }
        
        window.verDetalle = function(idx) {
            const d = table.row(idx).data();
            $('#modalTipo').text(d.tipo_licitacion);
            $('#modalObjeto').text(d.objeto);
            $('#modalEntidad').text(d.entidad);
            $('#modalExp').text(d.expediente);
            $('#modalBase').text(eur.format(d.presupuesto_base));
            $('#modalAdj').text(eur.format(d.importe_adjudicacion));
            $('#modalNumLic').text(d.num_licitadores);
            $('#linkFicha').attr('href', d.url_ficha);
            let htmlRiv = '';
            d.rivales.forEach(r => {
               const isWin = r === d.ganador;
               htmlRiv += `<div class="p-2 border rounded mb-1 d-flex justify-content-between align-items-center ${isWin?'bg-success bg-opacity-10 border-success':''}">
                   <span class="small ${isWin?'fw-bold text-success':''}">${r}</span>${isWin?'<i class="bi bi-trophy-fill text-success"></i>':''}</div>`; 
            });
            $('#modalRivales').html(htmlRiv || '<span class="text-muted fst-italic">Sin datos</span>');
            let htmlDocs = '';
            d.documentos.forEach(doc => {
                htmlDocs += `<a href="${doc.url}" target="_blank" class="btn btn-outline-secondary btn-sm text-start text-truncate"><i class="bi bi-file-earmark-pdf text-danger me-2"></i>${doc.nombre}</a>`;
            });
            $('#modalDocs').html(htmlDocs);
            new bootstrap.Modal('#modalDetalle').show();
        };
    </script>
</body>
</html>
"""

# --- MOTOR DE EXTRACCIÓN (PYTHON) ---
class MonitorEngine:
    def __init__(self):
        # FUENTES RSS: URLs largas intactas
        self.sources = [
            {"tipo": "OBRA", "estado": "ADJUDICADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=5&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "OBRA", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=8&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "OBRA", "estado": "CERRADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=14&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            
            {"tipo": "SERV", "estado": "ADJUDICADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=5&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "FORMALIZADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=8&p03=&p04=&p05=&p06=&p07=&p08=&p09=&p10=&p11=01/01/2025&p12=&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "CERRADO", "url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=14&p03=&p04=&p05=&p06=FALSE&p07=&p08=&p09=&p10=&p11=&p12=01/01/2025&p13=&p14=&p15=&p16=&p17=FALSE&p18=&p19=&p20=&p21=&p22=&p23=&p24=&p25=FALSE&p26=ES212&p27=&p28=&p29=&p30=&p31=&p32=&p33=&p34=&p35=&p36=&p37=&p38=&p39=&p40=&p41=&p42=&p43=false&p44=FALSE&p45=1&idioma=es&R01HNoPortal=true"}
        ]
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.processed_ids = set()

    def clean_money(self, txt):
        if not txt: return 0.0
        try: return float(txt.replace('.', '').replace(',', '.'))
        except: return 0.0

    def get_tab_value(self, soup, tab_id, label):
        tab = soup.find('div
