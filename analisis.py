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
HTML_FILE = "monitor_licitaciones.html"
DB_FILE = "licitaciones_db.json"
BACKUP_DIR = "backups"

# --- PLANTILLA HTML (v6.0 - BI & SECURITY EDITION) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor Licitaciones Euskadi | 2025</title>
    
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <link href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/rowgroup/1.4.1/css/rowGroup.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/buttons/2.4.2/css/buttons.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/plug-ins/1.13.7/features/searchHighlight/dataTables.searchHighlight.css" rel="stylesheet">
    
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
    
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
    <script src="https://npmcdn.com/flatpickr/dist/l10n/es.js"></script>

    <style>
        :root { 
            --primary: #0f172a; --accent: #2563eb; --bg-body: #f8fafc; --card-bg: #ffffff;
            --border-color: #e2e8f0; --text-main: #334155; --text-light: #64748b;
        }
        body { background-color: var(--bg-body); font-family: 'Inter', sans-serif; font-size: 0.875rem; color: var(--text-main); }
        
        /* UI General */
        .main-header { padding-bottom: 1rem; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: end; margin-bottom: 2rem; }
        .kpi-card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 20px; height: 100%; position: relative; overflow: hidden; cursor: pointer; transition: all 0.3s ease; box-shadow: 0 1px 3px rgba(0,0,0,0.02); }
        .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05); border-color: var(--accent); }
        .kpi-card.active-kpi { border-color: var(--accent); background-color: #eff6ff; }
        .kpi-value { font-size: 1.75rem; font-weight: 700; color: var(--primary); margin-bottom: 4px; }
        .kpi-label { font-size: 0.75rem; text-transform: uppercase; color: var(--text-light); font-weight: 600; letter-spacing: 0.05em; }
        .kpi-icon { position: absolute; right: -10px; top: -10px; font-size: 5rem; opacity: 0.03; color: var(--primary); transform: rotate(15deg); }

        /* Filtros y Botones */
        .filters-container { background: var(--card-bg); padding: 1rem 1.5rem; border-radius: 12px; border: 1px solid var(--border-color); margin-bottom: 1.5rem; display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; justify-content: space-between; }
        .btn-filter { background: transparent; border: 1px solid var(--border-color); color: var(--text-light); font-weight: 500; padding: 0.4rem 1rem; border-radius: 99px; font-size: 0.85rem; transition: all 0.2s ease; }
        .btn-filter:hover { background: #f1f5f9; color: var(--primary); }
        .btn-filter.active { background: var(--primary); color: white; border-color: var(--primary); }
        
        .group-controls { background: #f1f5f9; padding: 4px; border-radius: 8px; display: flex; gap: 4px; }
        .btn-group-mode { border: none; background: transparent; color: var(--text-light); font-size: 0.85rem; padding: 4px 12px; border-radius: 6px; font-weight: 500; }
        .btn-group-mode.active { background: white; color: var(--primary); box-shadow: 0 1px 2px rgba(0,0,0,0.1); font-weight: 600; }

        /* Personalización Botones Exportar DataTables */
        div.dt-buttons { display: flex; gap: 8px; }
        button.dt-button { 
            background: white !important; border: 1px solid var(--border-color) !important; 
            border-radius: 6px !important; color: var(--text-main) !important; font-size: 0.8rem !important;
            padding: 4px 12px !important; box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
            transition: all 0.2s !important;
        }
        button.dt-button:hover { background: #f8fafc !important; border-color: var(--accent) !important; color: var(--accent) !important; }
        
        /* Tabla */
        .table-card { background: var(--card-bg); border-radius: 12px; border: 1px solid var(--border-color); overflow: hidden; padding: 0; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.02); }
        table.dataTable thead th { background-color: #f8fafc; color: #475569; font-weight: 600; text-transform: uppercase; font-size: 0.7rem; border-bottom: 1px solid var(--border-color) !important; padding: 1rem !important; }
        
        tr.dtrg-group { cursor: pointer; background-color: #f8fafc !important; }
        tr.dtrg-group:hover { background-color: #e2e8f0 !important; }
        tr.dtrg-group td { padding: 12px 16px !important; border-bottom: 1px solid #cbd5e1; }
        .group-header-content { display: flex; align-items: center; justify-content: space-between; width: 100%; }
        .group-title { font-weight: 700; color: var(--primary); font-size: 0.95rem; display: flex; align-items: center; gap: 10px; }
        .group-sum { font-weight: 700; color: var(--primary); font-family: monospace; font-size: 1rem; background: #dbeafe; padding: 2px 8px; border-radius: 4px; color: #1e40af; }
        .group-chevron { transition: transform 0.2s; }
        tr.dtrg-group.expanded .group-chevron { transform: rotate(90deg); }

        /* Etiquetas Avanzadas */
        .badge-status { padding: 4px 8px; border-radius: 6px; font-weight: 600; font-size: 0.7rem; text-transform: uppercase; }
        .status-adj { background-color: #dbeafe; color: #1e40af; }
        .status-form { background-color: #dcfce7; color: #166534; }
        .status-cerr { background-color: #f1f5f9; color: #64748b; }
        
        .badge-baja { font-weight: 700; padding: 4px 8px; border-radius: 6px; min-width: 55px; text-align: center; font-size: 0.8rem; }
        .baja-high { background: #fee2e2; color: #b91c1c; position: relative; } /* Rojo Alerta */
        .baja-mid { background: #fef9c3; color: #a16207; }
        .baja-low { background: #f1f5f9; color: #64748b; }
        
        .badge-ute { background: #6366f1; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 700; margin-left: 6px; vertical-align: middle; }
        .warning-icon { color: #dc2626; margin-left: 4px; font-size: 0.9rem; cursor: help; }
        
        /* Highlighting */
        span.searchHighlight { background-color: #fef08a; font-weight: bold; padding: 0 2px; border-radius: 2px; }

        .winner-link { color: var(--primary); font-weight: 600; text-decoration: none; }
        .winner-link:hover { color: var(--accent); text-decoration: underline; }
        .sidebar-option { width: 100%; text-align: left; padding: 10px 14px; border: 1px solid var(--border-color); border-radius: 8px; margin-bottom: 8px; background: white; color: var(--text-main); display: flex; justify-content: space-between; align-items: center; transition: all 0.2s; }
        .sidebar-option:hover { border-color: var(--accent); color: var(--accent); background: #eff6ff; }
        .filter-alert { display: none; background: var(--primary); color: white; padding: 10px 20px; border-radius: 8px; margin-bottom: 20px; align-items: center; justify-content: space-between; }
    </style>
</head>
<body>
    <div class="offcanvas offcanvas-end" tabindex="-1" id="offcanvasFiltros">
        <div class="offcanvas-header border-bottom"><h5 class="offcanvas-title fw-bold">Filtros</h5><button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button></div>
        <div class="offcanvas-body bg-light"><div id="sidebarContent"></div><div class="mt-4 pt-3 border-top"><button class="btn btn-outline-danger w-100" onclick="resetSidebarFilter()">Eliminar Filtro</button></div></div>
    </div>

    <div class="container-fluid px-5 py-4">
        <header class="main-header">
            <div><h2 class="fw-bold mb-1 text-dark">Monitor de Licitaciones</h2><p class="text-muted mb-0 small">Base de Datos Gipuzkoa | Total: <strong id="totalRecords">0</strong> | Act: <span id="lastUpdate">__FECHA__</span></p></div>
            <div><span class="badge bg-light text-dark border">v6.0 B.I. Edition</span></div>
        </header>

        <div class="filters-container">
            <div class="d-flex gap-2">
                <button class="btn-filter active" onclick="setGlobalFilter('tipo', 'all', this)">Todos</button>
                <button class="btn-filter" onclick="setGlobalFilter('tipo', 'OBRA', this)">Obras</button>
                <button class="btn-filter" onclick="setGlobalFilter('tipo', 'SERV', this)">Servicios</button>
                <button class="btn-filter" onclick="setGlobalFilter('tipo', 'ING', this)">Ingeniería</button>
            </div>
            
            <div class="group-controls">
                <button class="btn-group-mode active" onclick="changeGrouping('none', this)" title="Ver listado"><i class="bi bi-list-ul me-1"></i>Detalle</button>
                <button class="btn-group-mode" onclick="changeGrouping('entidad', this)" title="Por Organismo"><i class="bi bi-building me-1"></i>Entidad</button>
                <button class="btn-group-mode" onclick="changeGrouping('ganador', this)" title="Por Contratista"><i class="bi bi-briefcase me-1"></i>Contratista</button>
            </div>

            <div class="d-flex align-items-center gap-2 bg-light p-1 rounded border">
                <select id="filterYear" class="form-select form-select-sm border-0 bg-transparent" style="width:70px;" onchange="table.draw()"><option value="">Año</option></select>
                <select id="filterMonth" class="form-select form-select-sm border-0 bg-transparent" style="width:80px;" onchange="table.draw()">
                    <option value="">Mes</option><option value="01">Ene</option><option value="02">Feb</option><option value="03">Mar</option><option value="04">Abr</option><option value="05">May</option><option value="06">Jun</option><option value="07">Jul</option><option value="08">Ago</option><option value="09">Sep</option><option value="10">Oct</option><option value="11">Nov</option><option value="12">Dic</option>
                </select>
                <input type="text" class="form-control form-control-sm border-0 bg-transparent text-center" style="width:85px;" id="dateFrom" placeholder="Desde">
                <input type="text" class="form-control form-control-sm border-0 bg-transparent text-center" style="width:85px;" id="dateTo" placeholder="Hasta">
            </div>
        </div>

        <div id="activeFilterAlert" class="filter-alert"><span><i class="bi bi-funnel-fill me-2"></i>Filtro: <strong id="filterName">...</strong></span><button class="btn btn-sm text-white" onclick="limpiarTodo()"><i class="bi bi-x-lg"></i></button></div>

        <div class="row g-3 mb-4">
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar('volumen', this)"><i class="bi bi-wallet2 kpi-icon"></i><div class="kpi-label">Volumen Acumulado</div><div class="kpi-value" id="kpi-volumen">0 €</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar('baja', this)"><i class="bi bi-graph-down-arrow kpi-icon"></i><div class="kpi-label">Baja Media</div><div class="kpi-value text-primary" id="kpi-baja">0%</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar('licitadores', this)"><i class="bi bi-people kpi-icon"></i><div class="kpi-label">Media Lic.</div><div class="kpi-value" id="kpi-licitadores">0</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar('contratistas', this)"><i class="bi bi-building kpi-icon"></i><div class="kpi-label">Contratistas Únicos</div><div class="kpi-value" id="kpi-contratistas">0</div></div></div>
        </div>

        <div class="table-card p-0">
            <table id="tablaContratos" class="table w-100 mb-0">
                <thead>
                    <tr>
                        <th width="8%">Fecha</th>
                        <th width="8%" class="text-center">Estado</th>
                        <th width="5%" class="text-center">Tipo</th>
                        <th width="25%">Entidad / Objeto</th>
                        <th width="18%">Adjudicatario</th>
                        <th width="10%" class="text-end">Base</th>
                        <th width="10%" class="text-end">Adjudicación</th>
                        <th width="6%" class="text-center">Baja</th>
                        <th width="5%" class="text-center">Lic.</th>
                        <th width="5%"></th>
                    </tr>
                </thead>
                <tbody></tbody>
            </table>
        </div>
    </div>

    <div class="modal fade" id="modalDetalle" tabindex="-1"><div class="modal-dialog modal-lg modal-dialog-centered"><div class="modal-content border-0 shadow-lg"><div class="modal-header border-bottom"><h5 class="modal-title fw-bold">Detalle</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body p-4">
        <div class="mb-4"><span class="badge bg-dark mb-2" id="modalTipo">Tipo</span><h5 class="fw-bold text-dark mb-1" id="modalObjeto">...</h5><p class="text-muted small"><i class="bi bi-bank me-1"></i><span id="modalEntidad">Entidad</span> &bull; Exp: <span id="modalExp"></span></p></div>
        <div class="row g-3 mb-4"><div class="col-6"><div class="p-3 bg-light rounded border"><div class="text-uppercase text-muted small fw-bold mb-1">Base</div><div class="fs-5 fw-bold" id="modalBase">0 €</div></div></div><div class="col-6"><div class="p-3 bg-success bg-opacity-10 rounded border border-success"><div class="text-uppercase text-success small fw-bold mb-1">Adjudicación</div><div class="fs-5 fw-bold text-success" id="modalAdj">0 €</div></div></div></div>
        <div class="row"><div class="col-md-7 border-end"><h6 class="fw-bold small text-uppercase mb-3">Rivales (<span id="modalNumLic">0</span>)</h6><div id="modalRivales" class="d-flex flex-column gap-2" style="max-height:200px; overflow-y:auto;"></div></div><div class="col-md-5 ps-4"><h6 class="fw-bold small text-uppercase mb-3">Acciones</h6><div id="modalDocs" class="d-grid gap-2 mb-3"></div><a id="linkFicha" href="#" target="_blank" class="btn btn-primary w-100">Ver Ficha Oficial</a></div></div>
    </div></div></div></div>

    <script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.min.js"></script>
    <script src="https://cdn.datatables.net/1.13.7/js/dataTables.bootstrap5.min.js"></script>
    <script src="https://cdn.datatables.net/rowgroup/1.4.1/js/dataTables.rowGroup.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/dataTables.buttons.min.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/buttons.bootstrap5.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.53/pdfmake.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdfmake/0.1.53/vfs_fonts.js"></script>
    <script src="https://cdn.datatables.net/buttons/2.4.2/js/buttons.html5.min.js"></script>
    <script src="https://cdn.datatables.net/plug-ins/1.13.7/features/searchHighlight/dataTables.searchHighlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/mark.js/8.11.1/jquery.mark.min.js"></script>
    
    <script>
        const datos = __DATOS_JSON__;
        const eur = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
        let table;
        let currentFilters = { tipo: 'all', sidebarCategory: null, sidebarValue: null };

        $(document).ready(function() {
            $('#totalRecords').text(datos.length);
            initDateControls();
            initTable();
            updateKPIs(datos);
        });

        function initDateControls() {
            flatpickr("#dateFrom", { dateFormat: "d/m/Y", locale: "es", onChange: function() { table.draw(); } });
            flatpickr("#dateTo", { dateFormat: "d/m/Y", locale: "es", onChange: function() { table.draw(); } });
            const years = [...new Set(datos.map(d => d.fecha_adjudicacion.split('/')[2]))].sort().reverse();
            years.forEach(y => $('#filterYear').append(`<option value="${y}">${y}</option>`));
        }

        function initTable() {
            // Filtro Personalizado
            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                const rowData = datos[dataIndex];
                if (currentFilters.tipo !== 'all' && rowData.tipo_licitacion !== currentFilters.tipo) return false;
                
                const dateParts = rowData.fecha_adjudicacion.split('/');
                const dateObj = new Date(dateParts[2], dateParts[1]-1, dateParts[0]);
                const selYear = $('#filterYear').val();
                const selMonth = $('#filterMonth').val();
                const min = $('#dateFrom').val() ? parseDate($('#dateFrom').val()) : null;
                const max = $('#dateTo').val() ? parseDate($('#dateTo').val()) : null;

                if (selYear && dateParts[2] !== selYear) return false;
                if (selMonth && dateParts[1] !== selMonth) return false;
                if (min && dateObj < min) return false;
                if (max && dateObj > max) return false;

                if (currentFilters.sidebarCategory) {
                    const val = currentFilters.sidebarValue;
                    const imp = rowData.importe_adjudicacion;
                    const baja = rowData.baja_pct;
                    const gan = rowData.ganador;
                    if (currentFilters.sidebarCategory === 'volumen') {
                        if (val === '<50k' && imp >= 50000) return false;
                        if (val === '<100k' && imp >= 100000) return false;
                        if (val === '<500k' && imp >= 500000) return false;
                        if (val === '<1M' && imp >= 1000000) return false;
                        if (val === '>1M' && imp < 1000000) return false;
                    }
                    if (currentFilters.sidebarCategory === 'baja' && val === '<10' && baja >= 10) return false;
                    if (currentFilters.sidebarCategory === 'baja' && val === '>10' && baja < 10) return false;
                    if (currentFilters.sidebarCategory === 'contratistas' && gan !== val) return false;
                }
                return true;
            });

            table = $('#tablaContratos').DataTable({
                data: datos,
                paging: false,
                info: false,
                order: [[ 0, "desc" ]],
                searchHighlight: true, // Activamos el resaltado
                dom: 'Bfrtip', // Activamos botones
                buttons: [
                    { extend: 'excel', text: '<i class="bi bi-file-earmark-excel me-1"></i>Excel', className: 'btn btn-sm btn-light' },
                    { extend: 'pdf', text: '<i class="bi bi-file-earmark-pdf me-1"></i>PDF', className: 'btn btn-sm btn-light' },
                    { extend: 'copy', text: '<i class="bi bi-clipboard me-1"></i>Copiar', className: 'btn btn-sm btn-light' }
                ],
                rowGroup: {
                    enable: false, 
                    startRender: function ( rows, group ) {
                        const total = rows.data().pluck('importe_adjudicacion').reduce((a, b) => a + b, 0);
                        const count = rows.count();
                        return $('<tr class="dtrg-group"></tr>')
                            .append(`<td colspan="10"><div class="group-header-content"><div class="group-title"><i class="bi bi-chevron-right group-chevron"></i>${group}</div><div class="group-stats"><span class="badge bg-white text-dark border">${count} exp.</span><span class="group-sum">${eur.format(total)}</span></div></div></td>`)
                            .on('click', function() {
                                const isExpanded = $(this).hasClass('expanded');
                                const nextRows = $(this).nextUntil('.dtrg-group');
                                if(isExpanded) { nextRows.hide(); $(this).removeClass('expanded'); } else { nextRows.show(); $(this).addClass('expanded'); }
                            });
                    }
                },
                columns: [
                    { data: 'fecha_adjudicacion', render: (d) => `<span class="fw-medium text-dark text-nowrap">${d}</span>` },
                    { data: 'estado_fase', className: 'text-center', render: d => {
                        let cls = d.includes('ADJ') ? 'status-adj' : (d.includes('FORM') ? 'status-form' : 'status-cerr');
                        return `<span class="badge-status ${cls}">${d.substring(0,10)}</span>`;
                    }},
                    { data: 'tipo_licitacion', className: 'text-center', render: d => {
                         let c = d==='ING'?'#8b5cf6':(d==='OBRA'?'#ef4444':'#3b82f6');
                         return `<span class="badge-status" style="color:${c}; background:${c}15; border:1px solid ${c}30">${d}</span>`;
                    }},
                    { data: 'entidad', render: (d,t,r) => `<div style="line-height:1.2"><div class="fw-bold text-dark text-truncate" style="max-width:280px" title="${d}">${d}</div><div class="text-muted text-truncate small" style="max-width:280px" title="${r.objeto}">${r.objeto}</div></div>` },
                    { data: 'ganador', render: (d,t,r) => {
                        let uteBadge = r.es_ute ? '<span class="badge-ute">UTE</span>' : '';
                        return `<a onclick="applySidebar('contratistas', '${d.replace(/'/g, "\\'")}')" class="winner-link text-truncate d-block small" style="max-width:200px" title="${d}">${d}${uteBadge}</a>`;
                    }},
                    { data: 'presupuesto_base', className: 'text-end', render: d => `<span class="text-secondary small font-monospace">${eur.format(d)}</span>` },
                    { data: 'importe_adjudicacion', className: 'text-end', render: d => `<span class="fw-bold text-dark small font-monospace">${eur.format(d)}</span>` },
                    { data: 'baja_pct', className: 'text-center', render: d => {
                        let cls = d >= 20 ? 'baja-high' : (d >= 10 ? 'baja-mid' : 'baja-low');
                        let icon = d >= 20 ? '<i class="bi bi-exclamation-triangle-fill warning-icon" title="Posible baja temeraria"></i>' : '';
                        return `<span class="badge-baja ${cls}">${d}%</span>${icon}`;
                    }},
                    { data: 'num_licitadores', className: 'text-center', render: d => d },
                    { data: null, orderable: false, className: 'text-end', render: (d,t,r,m) => `<button class="btn btn-sm btn-outline-secondary border-0" onclick='verDetalle(${m.row})'><i class="bi bi-eye"></i></button>` }
                ]
            });

            table.on('draw', function() {
                updateKPIs(table.rows({ filter: 'applied' }).data().toArray());
                if (table.rowGroup().enabled()) $('#tablaContratos tbody tr:not(.dtrg-group)').hide();
            });
        }

        function changeGrouping(mode, btn) {
            $('.btn-group-mode').removeClass('active'); $(btn).addClass('active');
            if (mode === 'none') { table.rowGroup().enable(false); table.order([[0, 'desc']]).draw(); $('#tablaContratos tbody tr').show(); } 
            else { const colIdx = (mode === 'entidad') ? 3 : 4; table.rowGroup().dataSrc(mode); table.rowGroup().enable(true); table.order([[colIdx, 'asc'], [0, 'desc']]).draw(); }
        }

        function setGlobalFilter(key, val, btn) { if(key === 'tipo') { $('.btn-filter').removeClass('active'); $(btn).addClass('active'); currentFilters.tipo = val; } table.draw(); }
        function openSidebar(cat, el) { /* Mismo código anterior */ } 
        function applySidebar(cat, val) { currentFilters.sidebarCategory = cat; currentFilters.sidebarValue = val; $('#activeFilterAlert').css('display', 'flex'); $('#filterName').text(val); table.draw(); }
        function resetSidebarFilter() { currentFilters.sidebarCategory = null; $('#activeFilterAlert').hide(); table.draw(); }
        function limpiarTodo() { resetSidebarFilter(); }
        function parseDate(d) { if(!d) return null; const p = d.split('/'); return new Date(p[2], p[1]-1, p[0]); }
        function updateKPIs(data) {
            let vol = 0, sumBaja = 0, countBaja = 0, sumLic = 0; const contratistasUnicos = new Set();
            data.forEach(d => {
                vol += d.importe_adjudicacion; if(d.baja_pct > 0) { sumBaja += d.baja_pct; countBaja++; } sumLic += d.num_licitadores;
                if(d.ganador !== "Desconocido") contratistasUnicos.add(d.ganador);
            });
            $('#kpi-volumen').text(new Intl.NumberFormat('es-ES', { maximumFractionDigits: 0 }).format(vol) + ' €');
            $('#kpi-baja').text((countBaja ? (sumBaja / countBaja) : 0).toFixed(2) + '%');
            $('#kpi-licitadores').text((data.length ? (sumLic / data.length) : 0).toFixed(1));
            $('#kpi-contratistas').text(contratistasUnicos.size);
        }
        
        window.verDetalle = function(idx) {
            const d = table.row(idx).data();
            $('#modalTipo').text(d.tipo_licitacion); $('#modalObjeto').text(d.objeto);
            $('#modalEntidad').text(d.entidad); $('#modalExp').text(d.expediente);
            $('#modalBase').text(eur.format(d.presupuesto_base)); $('#modalAdj').text(eur.format(d.importe_adjudicacion));
            let htmlRiv = ''; d.rivales.forEach(r => { const isWin = r === d.ganador; htmlRiv += `<div class="p-2 border rounded mb-1 d-flex justify-content-between align-items-center ${isWin?'bg-success bg-opacity-10 border-success':''}"><span class="small ${isWin?'fw-bold text-success':''}">${r}</span>${isWin?'<i class="bi bi-trophy-fill text-success"></i>':''}</div>`; });
            $('#modalRivales').html(htmlRiv); let htmlDocs = ''; d.documentos.forEach(doc => htmlDocs += `<a href="${doc.url}" target="_blank" class="btn btn-outline-secondary btn-sm text-start text-truncate"><i class="bi bi-file-earmark-pdf me-2"></i>${doc.nombre}</a>`);
            $('#modalDocs').html(htmlDocs); $('#linkFicha').attr('href', d.url_ficha);
            new bootstrap.Modal('#modalDetalle').show();
        };
    </script>
</body>
</html>
"""

# --- MOTOR DE EXTRACCIÓN (PERSISTENTE + BACKUPS + UTE DETECTION) ---
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

            # UTE DETECTION
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
        print("🚀 MONITOR v6.0 INICIANDO...")
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
