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
HTML_FILE = "monitor_licitaciones.html"
DB_FILE = "base_datos.json" # Archivo donde se guardará el historial

# --- PLANTILLA HTML (INTERACCIÓN AVANZADA v3.1) ---
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
        
        .kpi-card { 
            background: white; border: none; border-radius: var(--card-radius); padding: 15px 20px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); height: 100%; position: relative; overflow: hidden; 
            cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; border: 1px solid transparent;
        }
        .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); border-color: #bfdbfe; }
        .kpi-card.active-kpi { border-color: #0d6efd; background-color: #eff6ff; }
        
        .kpi-value { font-size: 1.6rem; font-weight: 800; color: #1e293b; margin-bottom: 0; line-height: 1.2; }
        .kpi-label { font-size: 0.7rem; text-transform: uppercase; color: #64748b; font-weight: 700; letter-spacing: 0.5px; }
        .kpi-icon { position: absolute; right: -5px; top: -5px; font-size: 4rem; opacity: 0.05; transform: rotate(10deg); color: #000; }

        .filters-bar { background: white; padding: 15px; border-radius: var(--card-radius); margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); display: flex; flex-wrap: wrap; gap: 10px; align-items: center; justify-content: space-between; }
        .btn-filter { font-weight: 600; font-size: 0.85rem; border-radius: 20px; padding: 6px 16px; border: 1px solid #e2e8f0; color: #64748b; background: white; transition: all 0.2s; }
        .btn-filter.active, .btn-filter:hover { background-color: #eff6ff; color: #2563eb; border-color: #bfdbfe; }
        
        .date-input { border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 12px; font-size: 0.85rem; width: 110px; }
        .date-select { border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px 25px 6px 10px; font-size: 0.85rem; background-color: #fff; cursor: pointer; }

        .dashboard-card { background: white; border-radius: var(--card-radius); box-shadow: 0 2px 4px rgba(0,0,0,0.05); padding: 20px; margin-bottom: 20px; }
        
        table.dataTable thead th { background-color: #f8fafc; color: #475569; font-weight: 700; text-transform: uppercase; font-size: 0.7rem; border-bottom: 2px solid #e2e8f0 !important; vertical-align: middle; }
        table.dataTable tbody td { vertical-align: middle; color: #334155; padding: 8px 10px; }
        
        .badge-baja { font-weight: 700; padding: 3px 8px; border-radius: 6px; min-width: 45px; display: inline-block; text-align: center; }
        .baja-alta { background-color: #dcfce7; color: #166534; }
        .baja-media { background-color: #fef9c3; color: #854d0e; }
        .baja-baja { background-color: #fee2e2; color: #991b1b; }
        .badge-tipo { font-size: 0.65rem; padding: 3px 6px; border-radius: 4px; border: 1px solid #e2e8f0; background: #f8fafc; color: #475569; text-transform: uppercase; }
        .badge-estado { font-size: 0.65rem; padding: 3px 6px; border-radius: 4px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

        .sidebar-option { display: block; width: 100%; text-align: left; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 8px; margin-bottom: 8px; background: white; color: #475569; transition: all 0.2s; font-size: 0.9rem; }
        .sidebar-option:hover { background: #f8fafc; border-color: #cbd5e1; color: #0f172a; }
        .sidebar-option.active { background: #eff6ff; border-color: #3b82f6; color: #1d4ed8; font-weight: 600; }
        .sidebar-count { float: right; background: #e2e8f0; color: #475569; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; }
        
        .winner-link { cursor: pointer; color: #0f172a; font-weight: 700; text-decoration: none; transition: color 0.2s; }
        .winner-link:hover { color: #2563eb; text-decoration: underline; }
        .filter-active-info { display: none; background: #eff6ff; border: 1px solid #bfdbfe; color: #1e40af; padding: 8px 15px; border-radius: 8px; margin-bottom: 15px; font-size: 0.9rem; align-items: center; justify-content: space-between; }
    </style>
</head>
<body>
    <div class="offcanvas offcanvas-start" tabindex="-1" id="offcanvasFiltros">
        <div class="offcanvas-header bg-light">
            <h5 class="offcanvas-title fw-bold text-primary" id="sidebarTitle">Filtros</h5>
            <button type="button" class="btn-close" data-bs-dismiss="offcanvas"></button>
        </div>
        <div class="offcanvas-body">
            <p class="small text-muted mb-3" id="sidebarDesc">Seleccione una opción para filtrar:</p>
            <div id="sidebarContent"></div>
            <div class="mt-4 pt-3 border-top">
                <button class="btn btn-outline-danger btn-sm w-100" onclick="resetSidebarFilter()">Quitar este filtro</button>
            </div>
        </div>
    </div>

    <div class="container-fluid px-4 py-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <div>
                <h3 class="fw-bold text-dark mb-0"><i class="bi bi-layers-half text-primary me-2"></i>Monitor Licitaciones</h3>
                <p class="text-muted mb-0 small">Gipuzkoa | Total Registros: <span id="totalRecords">0</span> | Actualizado: <span id="lastUpdate">__FECHA__</span></p>
            </div>
        </div>

        <div class="filters-bar">
            <div class="d-flex gap-2">
                <button class="btn-filter active" onclick="setGlobalFilter('tipo', 'all', this)">Todos</button>
                <button class="btn-filter" onclick="setGlobalFilter('tipo', 'OBRA', this)">Obras</button>
                <button class="btn-filter" onclick="setGlobalFilter('tipo', 'SERV', this)">Servicios</button>
                <button class="btn-filter" onclick="setGlobalFilter('tipo', 'ING', this)">Ingeniería</button>
            </div>
            <div class="d-flex gap-2 align-items-center bg-light p-2 rounded border">
                <i class="bi bi-calendar3 text-muted"></i>
                <select id="filterYear" class="form-select form-select-sm date-select" style="width:80px;" onchange="table.draw()"><option value="">Año</option></select>
                <select id="filterMonth" class="form-select form-select-sm date-select" style="width:100px;" onchange="table.draw()">
                    <option value="">Mes</option>
                    <option value="01">Ene</option><option value="02">Feb</option><option value="03">Mar</option>
                    <option value="04">Abr</option><option value="05">May</option><option value="06">Jun</option>
                    <option value="07">Jul</option><option value="08">Ago</option><option value="09">Sep</option>
                    <option value="10">Oct</option><option value="11">Nov</option><option value="12">Dic</option>
                </select>
                <span class="text-muted small mx-1">|</span>
                <input type="text" class="date-input flatpickr" id="dateFrom" placeholder="Desde...">
                <input type="text" class="date-input flatpickr" id="dateTo" placeholder="Hasta...">
            </div>
        </div>

        <div id="activeFilterAlert" class="filter-active-info">
            <span><i class="bi bi-funnel-fill me-2"></i>Filtro activo: <strong id="filterName">...</strong></span>
            <button class="btn btn-sm btn-close" onclick="limpiarTodo()"></button>
        </div>

        <div class="row g-3 mb-4">
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar('volumen', this)"><i class="bi bi-cash-coin kpi-icon"></i><div class="kpi-label">Volumen Total</div><div class="kpi-value" id="kpi-volumen">0 €</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar('baja', this)"><i class="bi bi-graph-down-arrow kpi-icon"></i><div class="kpi-label">Baja Media</div><div class="kpi-value text-primary" id="kpi-baja">0%</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar('licitadores', this)"><i class="bi bi-people kpi-icon"></i><div class="kpi-label">Media Lic.</div><div class="kpi-value" id="kpi-licitadores">0</div></div></div>
            <div class="col-xl-3 col-md-6"><div class="kpi-card" onclick="openSidebar('contratistas', this)"><i class="bi bi-briefcase kpi-icon"></i><div class="kpi-label">Contratistas</div><div class="kpi-value" id="kpi-contratistas">0</div></div></div>
        </div>

        <div class="dashboard-card">
            <table id="tablaContratos" class="table table-hover w-100">
                <thead>
                    <tr>
                        <th width="8%">Fecha Adj.</th>
                        <th width="8%">Estado</th>
                        <th width="8%">Tipo</th>
                        <th width="20%">Entidad / Objeto</th>
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
        let currentFilters = { tipo: 'all', sidebarCategory: null, sidebarValue: null };

        $(document).ready(function() {
            $('#totalRecords').text(datos.length);
            initDateControls();
            initTable();
            updateKPIs(datos);
        });

        function initDateControls() {
            flatpickr(".date-input", { dateFormat: "d/m/Y", locale: "es", onChange: function() { table.draw(); } });
            const years = [...new Set(datos.map(d => d.fecha_adjudicacion.split('/')[2]))].sort().reverse();
            years.forEach(y => $('#filterYear').append(`<option value="${y}">${y}</option>`));
        }

        function initTable() {
            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                const rowData = datos[dataIndex];
                
                // 1. Tipo
                if (currentFilters.tipo !== 'all' && rowData.tipo_licitacion !== currentFilters.tipo) return false;

                // 2. Fechas
                const dateParts = rowData.fecha_adjudicacion.split('/');
                const dateObj = new Date(dateParts[2], dateParts[1]-1, dateParts[0]);
                
                const selYear = $('#filterYear').val();
                const selMonth = $('#filterMonth').val();
                if (selYear && dateParts[2] !== selYear) return false;
                if (selMonth && dateParts[1] !== selMonth) return false;

                const min = $('#dateFrom').val() ? parseDate($('#dateFrom').val()) : null;
                const max = $('#dateTo').val() ? parseDate($('#dateTo').val()) : null;
                if (min && dateObj < min) return false;
                if (max && dateObj > max) return false;

                // 3. Sidebar
                if (currentFilters.sidebarCategory) {
                    const val = currentFilters.sidebarValue;
                    const imp = rowData.importe_adjudicacion;
                    const baja = rowData.baja_pct;
                    const lic = rowData.num_licitadores;
                    const gan = rowData.ganador;

                    if (currentFilters.sidebarCategory === 'volumen') {
                        if (val === '<50k' && imp >= 50000) return false;
                        if (val === '<100k' && imp >= 100000) return false;
                        if (val === '<200k' && imp >= 200000) return false;
                        if (val === '<500k' && imp >= 500000) return false;
                        if (val === '<800k' && imp >= 800000) return false;
                        if (val === '<1M' && imp >= 1000000) return false;
                        if (val === '<2M' && imp >= 2000000) return false;
                        if (val === '<5M' && imp >= 5000000) return false;
                        if (val === '>5M' && imp < 5000000) return false;
                    }
                    else if (currentFilters.sidebarCategory === 'baja') {
                        if (val === '<3' && baja >= 3) return false;
                        if (val === '<5' && baja >= 5) return false;
                        if (val === '<10' && baja >= 10) return false;
                        if (val === '<15' && baja >= 15) return false;
                        if (val === '>15' && baja <= 15) return false;
                    }
                    else if (currentFilters.sidebarCategory === 'licitadores') {
                        if (val === '>5') { if(lic <= 5) return false; }
                        else { if (lic != val) return false; }
                    }
                    else if (currentFilters.sidebarCategory === 'contratistas') {
                        if (gan !== val) return false;
                    }
                }
                return true;
            });

            table = $('#tablaContratos').DataTable({
                data: datos,
                language: { url: "//cdn.datatables.net/plug-ins/1.13.7/i18n/es-ES.json" },
                paging: false,
                order: [[ 0, "desc" ]],
                columns: [
                    { data: 'fecha_adjudicacion', render: (d) => { const p=d.split('/'); return `<span class="d-none">${p[2]}${p[1]}${p[0]}</span><span class="small fw-bold">${d}</span>`; }},
                    { data: 'estado_fase', className: 'text-center', render: d => {
                        let color = d.includes('ADJ') ? 'bg-primary' : (d.includes('FORM') ? 'bg-success' : 'bg-secondary');
                        return `<span class="badge text-white ${color} badge-estado">${d.substring(0,10)}</span>`;
                    }},
                    { data: 'tipo_licitacion', className: 'text-center', render: d => {
                        let c = d==='ING'?'#8b5cf6':(d==='OBRA'?'#ef4444':'#3b82f6');
                        return `<span class="badge-tipo" style="color:${c};border-color:${c}40;background:${c}10">${d}</span>`;
                    }},
                    { data: null, render: d => `<div style="line-height:1.2"><span class="d-block text-truncate small fw-bold text-dark" style="max-width:280px" title="${d.entidad}">${d.entidad}</span><span class="d-block text-muted text-truncate small" style="max-width:280px" title="${d.objeto}">${d.objeto}</span></div>` },
                    { data: 'ganador', render: d => `<span class="text-truncate d-block small" style="max-width:180px" title="${d}">${d}</span>` },
                    { data: 'presupuesto_base', className: 'text-end', render: d => `<span class="text-secondary small text-nowrap">${eur.format(d)}</span>` },
                    { data: 'importe_adjudicacion', className: 'text-end', render: d => `<span class="fw-bold small text-dark text-nowrap">${eur.format(d)}</span>` },
                    { data: 'baja_pct', className: 'text-center', render: d => {
                        let cls = d >= 20 ? 'baja-alta' : d >= 10 ? 'baja-media' : d > 0 ? 'baja-baja' : 'bg-light text-muted';
                        return `<span class="badge-baja ${cls}">${d}%</span>`;
                    }},
                    { data: 'num_licitadores', className: 'text-center', render: d => `<span class="badge bg-white border text-dark shadow-sm">${d}</span>` },
                    { data: null, orderable: false, className: 'text-end', render: (d,t,r,m) => `<button class="btn btn-sm btn-light border" onclick='verDetalle(${m.row})'><i class="bi bi-eye"></i></button>` }
                ]
            });

            table.on('draw', function() {
                const filteredData = table.rows({ filter: 'applied' }).data().toArray();
                updateKPIs(filteredData);
            });
        }

        function openSidebar(category, el) {
            $('.kpi-card').removeClass('active-kpi');
            $(el).addClass('active-kpi');
            let html = ''; let title = '';
            const currentData = table.rows({ filter: 'applied' }).data().toArray();

            if (category === 'volumen') {
                title = 'Filtrar por Importe';
                const ranges = [
                    {k: '<50k', l: 'Menor de 50.000 €'}, {k: '<100k', l: '< 100.000 €'}, 
                    {k: '<200k', l: '< 200.000 €'}, {k: '<500k', l: '< 500.000 €'},
                    {k: '<800k', l: '< 800.000 €'}, {k: '<1M', l: '< 1.000.000 €'},
                    {k: '<2M', l: '< 2.000.000 €'}, {k: '<5M', l: '< 5.000.000 €'}, {k: '>5M', l: '> 5.000.000 €'}
                ];
                ranges.forEach(r => html += `<button class="sidebar-option" onclick="applySidebar('${category}', '${r.k}')">${r.l}</button>`);
            } 
            else if (category === 'baja') {
                title = 'Filtrar por Baja';
                const ranges = [{k: '<3', l: '< 3%'}, {k: '<5', l: '< 5%'}, {k: '<10', l: '< 10%'}, {k: '<15', l: '< 15%'}, {k: '>15', l: '> 15%'}];
                ranges.forEach(r => html += `<button class="sidebar-option" onclick="applySidebar('${category}', '${r.k}')">${r.l}</button>`);
            }
            else if (category === 'licitadores') {
                title = 'Filtrar por Competencia';
                [1,2,3,4,5].forEach(n => html += `<button class="sidebar-option" onclick="applySidebar('${category}', ${n})">${n} Licitador(es)</button>`);
                html += `<button class="sidebar-option" onclick="applySidebar('${category}', '>5')">Más de 5</button>`;
            }
            else if (category === 'contratistas') {
                title = 'Contratistas (En vista actual)';
                const counts = {};
                currentData.forEach(d => { if(d.ganador !== 'Desconocido') counts[d.ganador] = (counts[d.ganador] || 0) + 1; });
                const sorted = Object.entries(counts).sort((a,b) => b[1] - a[1]);
                if (sorted.length === 0) html = '<p class="text-muted text-center">No hay datos</p>';
                else sorted.forEach(([n, c]) => html += `<button class="sidebar-option" onclick="applySidebar('${category}', '${n.replace(/'/g, "\\'")}')"><span class="text-truncate d-inline-block" style="max-width:220px;">${n}</span><span class="sidebar-count">${c}</span></button>`);
            }
            $('#sidebarTitle').text(title); $('#sidebarContent').html(html);
            new bootstrap.Offcanvas('#offcanvasFiltros').show();
        }

        function applySidebar(cat, val) {
            currentFilters.sidebarCategory = cat; currentFilters.sidebarValue = val;
            let label = val; 
            if(cat==='licitadores') label = val + ' licitadores';
            $('#filterName').text(label); $('#activeFilterAlert').css('display', 'flex');
            bootstrap.Offcanvas.getInstance('#offcanvasFiltros').hide(); table.draw();
        }

        function resetSidebarFilter() {
            currentFilters.sidebarCategory = null; currentFilters.sidebarValue = null;
            $('#activeFilterAlert').hide(); $('.kpi-card').removeClass('active-kpi');
            bootstrap.Offcanvas.getInstance('#offcanvasFiltros').hide(); table.draw();
        }

        function setGlobalFilter(key, val, btn) {
            if(key === 'tipo') { $('.btn-filter').removeClass('active'); $(btn).addClass('active'); currentFilters.tipo = val; }
            table.draw();
        }
        function limpiarTodo() { resetSidebarFilter(); }
        function updateKPIs(data) {
            let vol = 0, sumBaja = 0, countBaja = 0, sumLic = 0; const contratistasUnicos = new Set();
            data.forEach(d => {
                vol += d.importe_adjudicacion;
                if(d.baja_pct > 0) { sumBaja += d.baja_pct; countBaja++; }
                sumLic += d.num_licitadores;
                if(d.ganador !== "Desconocido") contratistasUnicos.add(d.ganador);
            });
            $('#kpi-volumen').text(eur.format(vol));
            $('#kpi-baja').text((countBaja ? (sumBaja / countBaja) : 0).toFixed(2) + '%');
            $('#kpi-licitadores').text((data.length ? (sumLic / data.length) : 0).toFixed(1));
            $('#kpi-contratistas').text(contratistasUnicos.size);
        }
        function parseDate(d) { if(!d) return null; const p = d.split('/'); return new Date(p[2], p[1]-1, p[0]); }
        window.verDetalle = function(idx) {
            const d = table.row(idx).data();
            $('#modalTipo').text(d.tipo_licitacion); $('#modalObjeto').text(d.objeto);
            $('#modalEntidad').text(d.entidad); $('#modalExp').text(d.expediente);
            $('#modalBase').text(eur.format(d.presupuesto_base)); $('#modalAdj').text(eur.format(d.importe_adjudicacion));
            $('#modalNumLic').text(d.num_licitadores); $('#linkFicha').attr('href', d.url_ficha);
            let htmlRiv = ''; d.rivales.forEach(r => { const isWin = r === d.ganador; htmlRiv += `<div class="p-2 border rounded mb-1 d-flex justify-content-between align-items-center ${isWin?'bg-success bg-opacity-10 border-success':''}"><span class="small ${isWin?'fw-bold text-success':''}">${r}</span>${isWin?'<i class="bi bi-trophy-fill text-success"></i>':''}</div>`; });
            $('#modalRivales').html(htmlRiv || '<span class="text-muted fst-italic">Sin datos</span>');
            let htmlDocs = ''; d.documentos.forEach(doc => htmlDocs += `<a href="${doc.url}" target="_blank" class="btn btn-outline-secondary btn-sm text-start text-truncate"><i class="bi bi-file-earmark-pdf text-danger me-2"></i>${doc.nombre}</a>`);
            $('#modalDocs').html(htmlDocs);
            new bootstrap.Modal('#modalDetalle').show();
        };
    </script>
</body>
</html>
"""

# --- MOTOR DE EXTRACCIÓN CON PERSISTENCIA ---
class MonitorEngine:
    def __init__(self):
        # 1. FUENTES RSS (URLs Largas Correctas)
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
        
        # 2. CARGAR BASE DE DATOS EXISTENTE
        self.db = []
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    self.db = json.load(f)
                    self.processed_ids = {d['id'] for d in self.db}
                print(f"📂 Base de datos cargada: {len(self.db)} registros previos.")
            except:
                print("⚠️ Error leyendo base de datos, iniciando nueva.")

    def clean_money(self, txt):
        if not txt: return 0.0
        try: return float(txt.replace('.', '').replace(',', '.'))
        except: return 0.0

    def get_tab_value(self, soup, tab_id, label):
        tab = soup.find('div', id=tab_id)
        if not tab: return None
        for row in tab.find_all('div', class_='row'):
            cols = row.find_all('div', recursive=False)
            if len(cols) >= 2:
                if label.lower() in cols[0].get_text(strip=True).lower():
                    return cols[1].get_text(strip=True)
        return None

    def process_url(self, url, tipo, estado):
        print(f"      Procesando: {url}")
        try:
            r = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(r.content, 'html.parser')
            
            data = {'id': hashlib.md5(url.encode()).hexdigest(), 'url_ficha': url, 'tipo_licitacion': tipo, 'estado_fase': estado}

            head = soup.find('div', class_='cabeceraDetalle')
            data['objeto'] = head.find('dd').get_text(strip=True) if head and head.find('dd') else "Sin descripción"

            keywords_ing = ['redacción', 'proyecto', 'dirección de obra', 'asistencia técnica', 'consultoría', 'estudio', 'coordinación', 'ingeniería', 'arquitectura']
            if tipo == "SERV":
                obj_lower = data['objeto'].lower()
                for kw in keywords_ing:
                    if kw in obj_lower:
                        data['tipo_licitacion'] = "ING"
                        break

            fecha_adj = self.get_tab_value(soup, 'tabs-9', 'Fecha adjudicación')
            if not fecha_adj:
                dt_headers = soup.find_all('dt')
                for dt in dt_headers:
                    if "última publicación" in dt.get_text():
                        dd = dt.find_next_sibling('dd')
                        if dd: fecha_adj = dd.get_text(strip=True).split(' ')[0]
                        break
            data['fecha_adjudicacion'] = fecha_adj or "Pendiente"
            
            data['entidad'] = self.get_tab_value(soup, 'tabs-2', 'Poder adjudicador') or "Desconocido"
            data['expediente'] = self.get_tab_value(soup, 'tabs-1', 'Expediente') or "N/A"

            base_str = self.get_tab_value(soup, 'tabs-4', 'Presupuesto del contrato sin IVA') or self.get_tab_value(soup, 'tabs-4', 'Valor estimado')
            adj_str = self.get_tab_value(soup, 'tabs-9', 'Precio sin IVA')
            data['presupuesto_base'] = self.clean_money(base_str)
            data['importe_adjudicacion'] = self.clean_money(adj_str)
            data['ganador'] = self.get_tab_value(soup, 'tabs-9', 'Razón social') or "Desconocido"

            if data['presupuesto_base'] > 0 and data['importe_adjudicacion'] > 0:
                ahorro = data['presupuesto_base'] - data['importe_adjudicacion']
                data['baja_pct'] = round((ahorro / data['presupuesto_base']) * 100, 2)
            else:
                data['baja_pct'] = 0.0

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

        except Exception as e:
            print(f"      Error: {e}")
            return None

    def run(self):
        print("🚀 INICIANDO MONITOR 3.1 (SIN LÍMITES + BASE DE DATOS)...")
        new_items_count = 0
        
        for s in self.sources:
            try:
                r = requests.get(s['url'], headers=self.headers, timeout=20)
                if r.status_code != 200: continue
                root = ET.fromstring(r.content)
                items = root.findall('.//item')
                print(f"📡 {s['tipo']} ({s['estado']}): {len(items)} items encontrados.")
                
                # --- CAMBIO CLAVE: Quitamos el [:15] para leer todo el RSS ---
                for item in items: 
                    link = item.find('link').text
                    if link not in self.processed_ids:
                        data = self.process_url(link, s['tipo'], s['estado'])
                        if data:
                            self.processed_ids.add(link) # Añadir ID al set de control
                            self.db.append(data)         # Añadir a la base de datos
                            new_items_count += 1
                            time.sleep(0.1)
            except Exception as e:
                print(f"   Error RSS: {e}")
        
        # Guardar Base de Datos actualizada
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.db, f, ensure_ascii=False, indent=2)
            
        print(f"💾 Base de datos guardada con {new_items_count} nuevos registros.")
        return self.db

if __name__ == "__main__":
    engine = MonitorEngine()
    data = engine.run()
    
    tz = timezone(timedelta(hours=1))
    now_str = datetime.now(tz).strftime("%d/%m/%Y %H:%M")
    
    json_str = json.dumps(data, ensure_ascii=False)
    final_html = HTML_TEMPLATE.replace('__DATOS_JSON__', json_str).replace('__FECHA__', now_str)
    
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(final_html)
        
    print(f"\n✅ REPORTE GENERADO: {HTML_FILE} con {len(data)} licitaciones totales.")
