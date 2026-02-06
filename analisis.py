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

# --- PLANTILLA HTML (v9.33 - Diseño Intacto) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Monitor Licitaciones Euskadi | 2025</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/1.13.7/css/dataTables.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/rowgroup/1.4.1/css/rowGroup.bootstrap5.min.css" rel="stylesheet">
    <link href="https://cdn.datatables.net/buttons/2.4.2/css/buttons.bootstrap5.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/flatpickr/dist/flatpickr.min.css">
    <script src="https://cdn.jsdelivr.net/npm/flatpickr"></script>
    <script src="https://npmcdn.com/flatpickr/dist/l10n/es.js"></script>
    <style>
        :root { --primary: #0f172a; --accent: #2563eb; --bg-body: #f8fafc; --card-bg: #ffffff; --border-color: #cbd5e1; --text-main: #334155; --text-light: #64748b; --group-bg: #f8fafc; --group-hover: #f1f5f9; --rival-color: #7c3aed; }
        body { background-color: var(--bg-body); font-family: 'Inter', sans-serif; font-size: 0.85rem; color: var(--text-main); }
        .top-bar { background: var(--card-bg); padding: 0.5rem 1rem; border-bottom: 1px solid var(--border-color); display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 0.5rem; position: sticky; top: 0; z-index: 1000; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .app-title { font-size: 1.1rem; font-weight: 700; color: var(--primary); display: flex; align-items: center; gap: 10px; margin: 0; }
        .stats-badge { background: #f1f5f9; padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; color: var(--text-light); border: 1px solid var(--border-color); display: flex; align-items: center; gap: 8px; }
        .btn-home { background: var(--primary); color: white; border: none; border-radius: 4px; padding: 2px 8px; font-size: 0.8rem; cursor: pointer; transition: all 0.2s; }
        .btn-home:hover { background: var(--accent); transform: scale(1.05); }
        .kpi-row { display: flex; gap: 10px; flex-wrap: wrap; }
        .kpi-col { flex: 1 1 0; min-width: 140px; }
        .kpi-card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 10px; padding: 12px 14px; height: 100%; position: relative; overflow: hidden; cursor: pointer; transition: all 0.2s ease; display:flex; flex-direction:column; justify-content:space-between; }
        .kpi-card:hover { border-color: var(--accent); transform: translateY(-2px); box-shadow: 0 6px 12px -2px rgba(0,0,0,0.08); }
        .kpi-card.active-filter { border-color: var(--rival-color); background: #fcfaff; box-shadow: inset 0 0 0 1px var(--rival-color); }
        .kpi-value { font-size: 1.25rem; font-weight: 700; color: var(--primary); line-height: 1.1; margin-bottom: 2px; }
        .kpi-label { font-size: 0.65rem; text-transform: uppercase; color: var(--text-light); font-weight: 600; letter-spacing: 0.05em; }
        .kpi-footer { display: flex; align-items: center; justify-content: space-between; margin-top: 6px; padding-top: 6px; border-top: 1px solid #f1f5f9; }
        .kpi-tag { font-size: 0.65rem; font-weight: 600; padding: 2px 6px; border-radius: 4px; background: #f1f5f9; color: #64748b; display: inline-flex; align-items: center; gap: 4px; }
        .tag-green { background: #dcfce7; color: #166534; }
        .kpi-icon { position: absolute; right: -5px; top: -5px; font-size: 3.5rem; opacity: 0.04; color: var(--primary); transform: rotate(10deg); }
        .data-pill { display: flex; flex-direction: column; }
        .pill-label { font-size: 0.55rem; color: #94a3b8; text-transform: uppercase; }
        .pill-val { font-size: 0.75rem; font-weight: 700; color: #475569; }
        .btn-filter { background: transparent; border: 1px solid var(--border-color); color: var(--text-light); font-weight: 500; padding: 0.3rem 0.8rem; border-radius: 99px; font-size: 0.8rem; transition: all 0.2s ease; }
        .btn-filter:hover { background: #f8fafc; color: var(--primary); border-color: var(--text-light); }
        .btn-filter.active { background: var(--primary); color: white; border-color: var(--primary); }
        .btn-date-mode.active { background: #475569; border-color: #475569; }
        .btn-action { border: 1px solid var(--border-color); background: white; color: var(--text-main); border-radius: 6px; padding: 4px 10px; font-size: 0.9rem; transition: all 0.2s; }
        .btn-action:hover { border-color: var(--accent); color: var(--accent); background: #f8fafc; }
        div.dt-buttons { display: none !important; }
        .table-card { background: var(--card-bg); border-radius: 8px; border: 1px solid var(--border-color); overflow: hidden; padding: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.02); min-height: 400px; }
        table.dataTable { width: 100% !important; margin: 0 !important; border-collapse: separate; border-spacing: 0; }
        table.dataTable thead th { background-color: #f8fafc; color: #475569; font-weight: 700; text-transform: uppercase; font-size: 0.75rem; border-bottom: 2px solid #e2e8f0 !important; padding: 12px 10px !important; vertical-align: middle; white-space: nowrap; cursor: pointer; }
        table.dataTable tbody td { padding: 10px 12px; vertical-align: middle; border-bottom: 1px solid #f1f5f9; font-size: 0.85rem; }
        .dataTables_filter { padding: 8px 15px; background: white; border-bottom: 1px solid #f1f5f9; }
        .dataTables_filter label { font-size: 0.85rem; color: #64748b; font-weight: 500; display: flex; align-items: center; gap: 8px; }
        .dataTables_filter input { border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px 10px; font-size: 0.85rem; outline: none; transition: border 0.2s; }
        .dataTables_filter input:focus { border-color: var(--accent); box-shadow: 0 0 0 2px rgba(37,99,235,0.1); }
        tr.dtrg-group td { background-color: var(--group-bg) !important; border-top: 2px solid #cbd5e1; border-bottom: 1px solid #e2e8f0; cursor: pointer; padding: 10px 15px; }
        tr.dtrg-group:hover td { background-color: var(--group-hover) !important; }
        .group-header-container { display: flex; align-items: center; justify-content: space-between; width: 100%; }
        .group-left { display: flex; align-items: center; gap: 12px; overflow: hidden; }
        .group-right { display: flex; align-items: center; gap: 25px; flex-shrink: 0; }
        .group-expander { color: #64748b; font-size: 1rem; transition: transform 0.2s; }
        tr.dtrg-group.expanded .group-expander { transform: rotate(90deg); color: var(--accent); }
        .group-name { font-weight: 700; font-size: 0.95rem; color: var(--primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 400px; }
        .group-rank-badge { background: #334155; color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; font-weight: 700; }
        .group-insight { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: #64748b; margin-left: 10px; border-left: 1px solid #cbd5e1; padding-left: 10px; }
        .metric-box { display: flex; flex-direction: column; align-items: flex-end; line-height: 1; }
        .metric-val { font-weight: 700; color: var(--primary); font-size: 0.95rem; }
        .metric-lbl { font-size: 0.6rem; color: #64748b; text-transform: uppercase; margin-top: 2px; }
        .winner-link { color: var(--text-main); font-weight: 600; text-decoration: none; cursor: pointer; transition: color 0.15s; }
        .winner-link:hover { color: var(--accent); text-decoration: underline; }
        .dt-center { text-align: center !important; } .dt-right { text-align: right !important; }
        .badge-status { padding: 3px 6px; border-radius: 4px; font-weight: 600; font-size: 0.65rem; text-transform: uppercase; }
        .status-adj { background-color: #dbeafe; color: #1e40af; } .status-form { background-color: #dcfce7; color: #166534; } .status-cerr { background-color: #f1f5f9; color: #64748b; }
        .badge-baja { font-weight: 700; padding: 2px 6px; border-radius: 4px; font-size: 0.75rem; }
        .baja-high { background: #fee2e2; color: #b91c1c; border: 1px solid #fecaca; }
        .baja-mid { background: #fef9c3; color: #a16207; border: 1px solid #fde047; }
        .baja-low { background: #f1f5f9; color: #64748b; border: 1px solid #e2e8f0; }
        .badge-ute { background: #6366f1; color: white; padding: 1px 4px; border-radius: 3px; font-size: 0.6rem; font-weight: 700; margin-left: 4px; }
        #viewAnalysis { display: none; padding: 0; }
        .analysis-header { padding: 12px 15px; background: linear-gradient(to right, #eff6ff, #ffffff); border-bottom: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }
        #analysisSearchInput { border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px 12px; width: 250px; font-size: 0.85rem; outline: none; }
        #analysisSearchInput:focus { border-color: var(--accent); }
        .filter-alert { display: none; background: var(--primary); color: white; padding: 8px 16px; border-radius: 6px; margin-bottom: 16px; align-items: center; justify-content: space-between; font-size: 0.85rem; }
        .chart-row { display: flex; align-items: center; margin-bottom: 8px; }
        .chart-label { width: 40px; font-size: 0.8rem; text-align: center; color: #64748b; font-weight: 700; margin-right: 10px; }
        .chart-bar-container { flex-grow: 1; height: 32px; background: #f1f5f9; border-radius: 6px; overflow: hidden; position: relative; display: flex; align-items: center; }
        .chart-bar { height: 100%; background: var(--accent); border-radius: 4px; transition: width 0.5s ease; }
        .chart-value { position: absolute; left: 10px; font-size: 0.75rem; font-weight: 700; color: #334155; z-index: 2; display: flex; align-items: center; gap: 8px; width: 100%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .chart-context { font-weight: 400; color: #64748b; font-size: 0.7rem; margin-left: auto; margin-right: 10px; }
        .date-filter-container { display: flex; align-items: center; gap: 2px; background: white; padding: 2px 4px; border-radius: 6px; border: 1px solid #e2e8f0; }
        .date-filter-input { width: 55px; font-size: 0.75rem; border: none; background: transparent; text-align: center; }
        .date-filter-select { width: 60px; font-size: 0.75rem; border: none; background: transparent; padding-left: 4px; }
        .modal-xl-custom { max-width: 1000px; }
        .modal-content { border-radius: 16px; border: none; }
        .modal-header { padding: 20px 24px; border-bottom: 1px solid #f1f5f9; position: sticky; top: 0; background: white; z-index: 10; }
        .info-card { background: white; border-radius: 12px; padding: 16px 20px; border: 1px solid #e2e8f0; height: 100%; display: flex; flex-direction: column; justify-content: space-between; }
        .info-card-value { font-size: 1.25rem; font-weight: 700; color: #0f172a; }
        .step-wizard { display: flex; justify-content: space-between; position: relative; margin-bottom: 24px; padding: 0 10px; }
        .step-wizard::before { content: ''; position: absolute; top: 12px; left: 20px; right: 20px; height: 2px; background: #e2e8f0; z-index: 0; }
        .step-item { position: relative; z-index: 1; text-align: center; width: 33%; }
        .step-circle { width: 26px; height: 26px; border-radius: 50%; background: #e2e8f0; border: 2px solid #fff; margin: 0 auto 8px; display: flex; align-items: center; justify-content: center; transition: all 0.3s; }
        .step-item.active .step-circle { background: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.2); }
        .step-item.completed .step-circle { background: #16a34a; }
        .rival-row { display: flex; align-items: center; padding: 8px 12px; background: white; border: 1px solid #e2e8f0; margin-bottom: 6px; border-radius: 6px; }
        .avatar-circle { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 0.75rem; margin-right: 10px; background: #64748b; }
    </style>
</head>
<body>
    <div class="top-bar">
        <div class="d-flex align-items-center gap-3">
            <h1 class="app-title"><i class="bi bi-activity"></i> Licitaciones</h1>
            <div class="stats-badge"><span id="totalRecords" class="fw-bold text-dark">0</span> exps. <span class="text-muted mx-1">|</span> <span id="lastUpdate">__FECHA__</span><button class="btn-home" onclick="resetHome()" title="Volver al Inicio"><i class="bi bi-house-door-fill"></i></button></div>
        </div>
        <div class="d-flex align-items-center gap-2">
            <div class="d-flex gap-1 border-end pe-2 me-1">
                <button class="btn-action" onclick="triggerExport('excel')"><i class="bi bi-file-earmark-excel"></i></button>
                <button class="btn-action" onclick="triggerExport('pdf')"><i class="bi bi-file-earmark-pdf"></i></button>
                <button class="btn-action" onclick="triggerExport('copy')"><i class="bi bi-clipboard"></i></button>
            </div>
            <div class="d-flex gap-1 border-end pe-2 me-1">
                <button class="btn-action" id="btnViewMode" onclick="toggleViewMode()"><i class="bi bi-layers"></i> Agrupar</button>
                <button class="btn-action" id="btnExpandAll" onclick="toggleExpandAll()" style="display:none;"><i class="bi bi-arrows-expand"></i></button>
            </div>
            <div class="d-flex gap-1 border-end pe-2 me-1">
                <button class="btn-filter active" onclick="setGlobalFilter('tipo', 'all', this)">Todos</button>
                <button class="btn-filter" onclick="setGlobalFilter('tipo', 'OBRA', this)">Obras</button>
                <button class="btn-filter" onclick="setGlobalFilter('tipo', 'SERV', this)">Servicios</button>
                <button class="btn-filter" onclick="setGlobalFilter('tipo', 'ING', this)">Ingeniería</button>
            </div>
            <div class="d-flex gap-1 border-end pe-2 me-1">
                <button class="btn-filter btn-date-mode" onclick="setDateMode('PUB', this)">PUB</button>
                <button class="btn-filter btn-date-mode active" onclick="setDateMode('ADJ', this)">ADJ</button>
            </div>
            <div class="date-filter-container">
                <select id="filterYear" class="date-filter-select" onchange="runFilter()"><option value="">Año</option></select>
                <span class="text-muted opacity-25">|</span>
                <select id="filterMonth" class="date-filter-select" onchange="runFilter()"><option value="">Mes</option><option value="01">Ene</option><option value="02">Feb</option><option value="03">Mar</option><option value="04">Abr</option><option value="05">May</option><option value="06">Jun</option><option value="07">Jul</option><option value="08">Ago</option><option value="09">Sep</option><option value="10">Oct</option><option value="11">Nov</option><option value="12">Dic</option></select>
                <span class="text-muted opacity-25">|</span>
                <input type="text" class="date-filter-input" id="dateFrom" placeholder="Desde"><span class="text-muted opacity-25">-</span><input type="text" class="date-filter-input" id="dateTo" placeholder="Hasta">
            </div>
        </div>
    </div>

    <div class="container-fluid px-4 py-4" id="mainContainer">
        <div id="activeFilterAlert" class="filter-alert"><span><i class="bi bi-funnel-fill me-2"></i>Filtro: <strong id="filterName">...</strong></span><button class="btn btn-sm text-white p-0" onclick="limpiarTodo()"><i class="bi bi-x-lg"></i></button></div>
        
        <div class="kpi-row mb-4">
            <div class="kpi-col"><div class="kpi-card" onclick="autoGroup('entidad', 'base')"><i class="bi bi-coin kpi-icon"></i><div class="kpi-label">Volumen Base</div><div class="kpi-value text-secondary" id="kpi-volumen-base">0 €</div><div class="kpi-footer"><span class="kpi-tag">OFICIAL</span></div></div></div>
            <div class="kpi-col"><div class="kpi-card" onclick="autoGroup('entidad', 'adj')"><i class="bi bi-wallet2 kpi-icon"></i><div class="kpi-label">Volumen ADJ.</div><div class="kpi-value text-success" id="kpi-volumen-adj">0 €</div><div class="kpi-footer"><span class="kpi-tag tag-green">REAL</span></div></div></div>
            <div class="kpi-col"><div class="kpi-card" onclick="loadAnalysisTable('baja')"><i class="bi bi-graph-down-arrow kpi-icon"></i><div class="kpi-label">Baja Media</div><div class="kpi-value" id="kpi-baja">0,00%</div><div class="kpi-footer"><div class="data-pill"><span class="pill-label">Ahorro Total</span><span class="pill-val text-success" id="kpi-ahorro-total">0 €</span></div></div></div></div>
            <div class="kpi-col"><div class="kpi-card" onclick="loadAnalysisTable('licitadores')"><i class="bi bi-people kpi-icon"></i><div class="kpi-label">Media Lic.</div><div class="kpi-value" id="kpi-licitadores">0,00</div><div class="kpi-footer"><div class="data-pill"><span class="pill-label">Máx. Exp.</span><span class="pill-val" id="kpi-lic-max">0</span></div><div class="data-pill text-end"><span class="pill-label">1 Lic.</span><span class="pill-val text-danger" id="kpi-lic-unique">0%</span></div></div></div></div>
            <div class="kpi-col"><div class="kpi-card" onclick="autoGroup('contratista', 'adj')"><i class="bi bi-building kpi-icon"></i><div class="kpi-label">Contratistas</div><div class="kpi-value" id="kpi-contratistas">0</div><div class="kpi-footer"><span class="kpi-tag">EMPRESAS ÚNICAS</span></div></div></div>
            <div class="kpi-col"><div class="kpi-card" id="cardRivales" onclick="toggleRivalsFilter()" style="border-color: #7c3aed; background: #f5f3ff;"><i class="bi bi-stars kpi-icon" style="color:#7c3aed;"></i><div class="kpi-label" style="color:#7c3aed;">Filtro Estratégico</div><div class="kpi-value" id="kpiRivalesText" style="color:#7c3aed; font-size:1rem;">Empresas Clave</div></div></div>
            <div class="kpi-col"><div class="kpi-card" onclick="openEvolutionModal()" style="border-color: #3b82f6; background: #eff6ff;"><i class="bi bi-bar-chart-line-fill kpi-icon" style="color:#3b82f6;"></i><div class="kpi-label text-primary">Análisis Temporal</div><div class="kpi-value text-primary" style="font-size:1rem;">Evolución</div></div></div>
        </div>
        
        <div class="table-card">
            <div id="viewMain">
                <table id="tablaContratos" class="table table-hover w-100 mb-0">
                    <thead><tr><th width="6%">1ª Pub.</th><th width="6%">Adj.</th><th width="8%" class="text-center">Estado</th><th width="5%" class="text-center">Tipo</th><th width="23%">Entidad / Objeto</th><th width="18%">Adjudicatario</th><th width="10%" class="text-end">Base</th><th width="10%" class="text-end">Adjudicación</th><th width="6%" class="text-center">Baja</th><th width="5%" class="text-center">Lic.</th><th width="1%"></th></tr></thead><tbody></tbody>
                </table>
            </div>
            <div id="viewAnalysis">
                <div class="analysis-header"><div class="analysis-title-block"><i class="bi bi-bar-chart-fill"></i> <span id="analysisTitle">ANÁLISIS DE DATOS</span></div><input type="text" id="analysisSearchInput" placeholder="Escribe para buscar..."></div>
                <table id="tablaAnalisis" class="table table-hover w-100 mb-0"><thead></thead><tbody></tbody></table>
            </div>
        </div>
    </div>

    <div class="modal fade" id="modalDetalle" tabindex="-1"><div class="modal-dialog modal-xl modal-xl-custom modal-dialog-centered"><div class="modal-content border-0 shadow-lg">
        <div class="modal-header"><div class="w-100"><div class="d-flex justify-content-between align-items-start mb-2"><div class="d-flex gap-2"><span class="badge bg-dark" id="modalTipo">TIPO</span><span class="badge bg-secondary bg-opacity-75" id="modalEstado">ESTADO</span></div><div><a id="btnLinkOriginal" href="#" target="_blank" class="btn btn-sm btn-primary me-2"><i class="bi bi-box-arrow-up-right me-1"></i> Ver Anuncio Original</a><button class="btn btn-sm btn-outline-secondary" onclick="copiarExp()"><i class="bi bi-copy me-1"></i><span id="modalExp"></span></button></div></div><h5 class="fw-bold text-dark mb-1" id="modalObjeto">Título</h5><div class="text-muted small fw-medium"><i class="bi bi-building me-1"></i> <span id="modalEntidad">Entidad</span></div></div><button type="button" class="btn-close ms-3" data-bs-dismiss="modal"></button></div>
        <div class="modal-body">
            <div class="row g-3 mb-4"><div class="col-lg-3 col-6"><div class="info-card"><div class="info-card-label">Presupuesto Base</div><div class="info-card-value text-secondary" id="modalBase">0 €</div></div></div><div class="col-lg-3 col-6"><div class="info-card" style="background:#f0fdf4; border-color:#bbf7d0;"><div class="info-card-label text-success">Adjudicación</div><div class="info-card-value text-success" id="modalAdj">0 €</div></div></div><div class="col-lg-3 col-6"><div class="info-card"><div class="info-card-label">Baja / Ahorro</div><div class="info-card-value" id="modalBajaPct">0%</div><div class="progress-slim"><div class="progress-bar-custom" id="barraBaja" style="width:0%"></div></div></div></div><div class="col-lg-3 col-6"><div class="info-card text-center"><div class="text-muted small fw-bold text-uppercase">Duración</div><div class="fs-2 fw-bold text-dark" id="modalDiasTrans">0</div><div class="text-muted small">Días</div></div></div></div>
            <div class="row g-4"><div class="col-lg-7"><h6 class="fw-bold text-uppercase small text-muted mb-2">Licitadores (<span id="modalNumLic">0</span>)</h6><div class="insight-strip" id="smartInsight"><i class="bi bi-lightbulb-fill insight-icon"></i><div id="insightText">...</div></div><div id="modalRivales" class="scroll-box"></div></div><div class="col-lg-5"><div class="bg-white p-3 rounded border mb-3"><h6 class="fw-bold text-uppercase small text-muted mb-3">Cronograma</h6><div class="step-wizard"><div class="step-item completed"><div class="step-circle"><i class="bi bi-check text-white"></i></div><div class="step-label">Publicado</div><div class="step-date" id="modalFechaPub"></div></div><div class="step-item active"><div class="step-circle"></div><div class="step-label">En Proceso</div></div><div class="step-item" id="stepAdj"><div class="step-circle"></div><div class="step-label">Adjudicado</div><div class="step-date" id="modalFechaAdj"></div></div></div></div><div class="bg-white p-3 rounded border"><h6 class="fw-bold text-uppercase small text-muted mb-3">Documentación</h6><div id="modalDocs" class="d-grid gap-2 mb-3" style="max-height:200px; overflow-y:auto;"></div></div></div></div>
        </div>
    </div></div></div>

    <div class="modal fade" id="modalEvolucion" tabindex="-1"><div class="modal-dialog modal-xl modal-dialog-centered"><div class="modal-content"><div class="modal-header"><div><h5 class="modal-title fw-bold text-primary"><i class="bi bi-calendar-week me-2"></i>Evolución Mensual y Reparto</h5><div class="small text-muted" id="chartSubtitle">Mostrando datos según filtros actuales</div></div><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body bg-light"><div class="bg-white p-4 rounded border shadow-sm"><div id="chartContainer"></div></div></div></div></div></div>

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
        const eur = new Intl.NumberFormat('es-ES', { style: 'decimal', minimumFractionDigits: 0, maximumFractionDigits: 0, useGrouping: true });
        const eurDec = new Intl.NumberFormat('es-ES', { style: 'decimal', minimumFractionDigits: 2, maximumFractionDigits: 2, useGrouping: true });
        
        let table, analysisTable;
        let currentFilters = { tipo: 'all', analysisCategory: null, analysisValue: null };
        let viewMode = 'detail', dateMode = 'ADJ';
        let currentGroupStats = {}, allGroupsExpanded = false, currentAnalysisMode = null;
        let rivalsFilterActive = false;
        let groupingFocus = 'entidad'; 
        const STRATEGIC_RIVALS = ["MOYUA", "AMENABAR", "CAMPEZO", "URDINBERRI", "OTEGUI", "ORSA", "ASFALTIA", "GEOTUNEL", "URBYCOLAN", "LANDA IMAZ", "MARIEZCURRENA", "ZUBIEDER", "SASOI", "ASFALTOS DEBA"];

        $(document).ready(function() {
            const ingKeywords = ['redacción', 'proyecto', 'dirección de obra', 'asistencia técnica', 'consultoría', 'estudio', 'coordinación', 'ingeniería', 'arquitectura'];
            datos.forEach(d => {
                d.groupSort = 0; 
                if (d.tipo_licitacion === 'SERV') {
                    const obj = (d.objeto || '').toLowerCase();
                    if (ingKeywords.some(k => obj.includes(k))) { d.tipo_licitacion = 'ING'; }
                }
            });

            $('#totalRecords').text(datos.length);
            initDateControls();
            initTable();
            
            $('#tablaContratos tbody').on('click', 'tr.dtrg-group', function () {
                var nextRows = $(this).nextUntil('.dtrg-group');
                if (nextRows.is(':visible')) { nextRows.hide(); $(this).removeClass('expanded'); } else { nextRows.show(); $(this).addClass('expanded'); }
            });

            // --- SEARCH DEBOUNCE FIX (v9.31) ---
            let searchTimeout = null;
            $('#analysisSearchInput').on('keyup', function() {
                clearTimeout(searchTimeout);
                let val = this.value;
                searchTimeout = setTimeout(() => {
                    if(analysisTable) analysisTable.search(val).draw();
                }, 350); 
            });
        });

        function getRowDate(row) { return (dateMode === 'PUB') ? (row.fecha_pub_iso || '') : (row.fecha_iso || ''); }
        function initDateControls() {
            flatpickr("#dateFrom", { dateFormat: "d/m/Y", locale: "es", onChange: function() { runFilter(); } });
            flatpickr("#dateTo", { dateFormat: "d/m/Y", locale: "es", onChange: function() { runFilter(); } });
            const years = [...new Set(datos.map(d => d.fecha_iso ? d.fecha_iso.slice(0,4) : null))].filter(Boolean).sort().reverse();
            years.forEach(y => $('#filterYear').append(`<option value="${y}">${y}</option>`));
        }

        function runFilter() { table.draw(); }

        function resetHome() { 
            $('#activeFilterAlert').fadeOut(100); 
            $('#viewAnalysis').hide(); $('#viewMain').show();
            $('#cardRivales').removeClass('active-filter'); $('#kpiRivalesText').text('Empresas Clave');
            $('#analysisSearchInput').val('');
            currentFilters.analysisCategory = null; currentFilters.analysisValue = null; 
            rivalsFilterActive = false; groupingFocus = 'entidad'; viewMode = 'detail'; 
            $('#btnViewMode').removeClass('active').html('<i class="bi bi-layers"></i> Agrupar');
            $('#btnExpandAll').hide();
            if(analysisTable) { analysisTable.search('').draw(); }
            table.search('').rowGroup().enable(false).order([[2, "desc"]]).draw(); 
        }
        
        function limpiarTodo() { resetHome(); }
        
        function toggleRivalsFilter() {
            rivalsFilterActive = !rivalsFilterActive;
            const btn = $('#cardRivales'); const txt = $('#kpiRivalesText');
            if(rivalsFilterActive) { btn.addClass('active-filter'); txt.text('Activado'); } else { btn.removeClass('active-filter'); txt.text('Empresas Clave'); }
            table.draw();
        }

        function autoGroup(focus, sortMode) {
            groupingFocus = focus; viewMode = 'grouped';
            $('#btnViewMode').addClass('active').html('<i class="bi bi-layers-fill"></i> Desagrupar');
            $('#btnExpandAll').show();
            updateGroupingLogic(); 
            $('#viewAnalysis').hide(); $('#viewMain').show(); 
        }

        function openEvolutionModal() { renderEvolutionChart(); new bootstrap.Modal('#modalEvolucion').show(); }
        
        function renderEvolutionChart() {
            let filteredData = table.rows({ filter: 'applied' }).data().toArray();
            let monthStats = {}; const monthNames = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
            let mode = (currentFilters.analysisCategory === 'contratistas') ? 'contractor_view' : ((currentFilters.analysisCategory === 'entidad') ? 'entity_view' : 'general');
            let subtitle = (mode === 'contractor_view') ? `Analizando clientes de: <strong>${currentFilters.analysisValue}</strong>` : ((mode === 'entity_view') ? `Analizando adjudicatarios de: <strong>${currentFilters.analysisValue}</strong>` : "Visión General del Mercado");
            $('#chartSubtitle').html(subtitle);
            for(let i=0; i<12; i++) monthStats[i] = { vol: 0, count: 0, topKey: {}, maxKeyVal: 0, maxKeyName: "" };
            let maxVol = 0;
            filteredData.forEach(d => {
                let dateStr = getRowDate(d); 
                if(dateStr && dateStr.length >= 7) {
                    let m = parseInt(dateStr.substring(5,7)) - 1; 
                    if(m >= 0 && m <= 11) {
                        monthStats[m].vol += d.importe_adjudicacion; monthStats[m].count++;
                        let key = (mode === 'contractor_view') ? d.entidad : ((mode === 'entity_view') ? d.ganador : d.ganador);
                        if(key && key !== "Desconocido") monthStats[m].topKey[key] = (monthStats[m].topKey[key] || 0) + d.importe_adjudicacion;
                    }
                }
            });
            for(let i=0; i<12; i++) {
                if(monthStats[i].vol > maxVol) maxVol = monthStats[i].vol;
                let bestK = "", bestV = 0;
                for (const [k, v] of Object.entries(monthStats[i].topKey)) { if (v > bestV) { bestV = v; bestK = k; } }
                monthStats[i].maxKeyName = bestK; monthStats[i].maxKeyVal = bestV;
            }
            let html = '';
            for(let i=0; i<12; i++) {
                let s = monthStats[i]; let width = maxVol > 0 ? (s.vol / maxVol * 100) : 0;
                let displayVal = s.vol > 0 ? eurDec.format(s.vol) + ' €' : '-';
                let contextInfo = "";
                if (s.maxKeyName) {
                    let prefix = (mode === 'contractor_view') ? "Cliente principal: " : "Top Adj: ";
                    let pct = (s.vol > 0) ? Math.round(s.maxKeyVal / s.vol * 100) : 0;
                    contextInfo = `<span class="chart-context">${prefix} <strong>${s.maxKeyName}</strong> (${pct}%)</span>`;
                }
                html += `<div class="chart-row"><div class="chart-label">${monthNames[i]}</div><div class="chart-bar-container"><div class="chart-bar" style="width: ${width}%"></div><div class="chart-value ps-2">${displayVal} ${s.count > 0 ? `<span class="badge bg-white text-dark ms-2 border" style="font-size:0.65rem">${s.count} exp</span>` : ''}</div>${contextInfo}</div></div>`;
            }
            $('#chartContainer').html(html);
        }

        function initTable() {
            $.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
                if (settings.nTable.id !== 'tablaContratos') return true;
                try {
                    const row = datos[dataIndex]; if (!row) return false;
                    if (currentFilters.tipo !== 'all' && row.tipo_licitacion !== currentFilters.tipo) return false;
                    const dateTarget = getRowDate(row);
                    const selYear = $('#filterYear').val(); const selMonth = $('#filterMonth').val();
                    const min = $('#dateFrom').val() ? parseDate($('#dateFrom').val()) : null; const max = $('#dateTo').val() ? parseDate($('#dateTo').val()) : null;
                    if (selYear && dateTarget.slice(0,4) !== selYear) return false;
                    if (selMonth && dateTarget.slice(5,7) !== selMonth) return false;
                    if (min && toDateFromISO(dateTarget) < min) return false;
                    if (max && toDateFromISO(dateTarget) > max) return false;
                    if (currentFilters.analysisCategory) {
                        const val = currentFilters.analysisValue;
                        if (currentFilters.analysisCategory === 'contratistas' && row.ganador !== val) return false;
                        if (currentFilters.analysisCategory === 'entidad' && row.entidad !== val) return false;
                    }
                    if (rivalsFilterActive) {
                        let winnerUpper = (row.ganador || "").toUpperCase();
                        if (!STRATEGIC_RIVALS.some(rival => winnerUpper.includes(rival))) return false;
                    }
                    return true;
                } catch(e) { return false; }
            });

            table = $('#tablaContratos').DataTable({
                data: datos, paging: false, info: false, order: [[ 2, "desc" ]], searchHighlight: true, dom: 'Bfrtip',
                deferRender: true, searchDelay: 350, // --- PERFORMANCE FIXES ---
                buttons: [ { extend: 'excel', className: 'buttons-excel' }, { extend: 'pdf', className: 'buttons-pdf' }, { extend: 'copy', className: 'buttons-copy' } ],
                drawCallback: function() { 
                    let d = this.api().rows({ filter: 'applied' }).data().toArray();
                    updateKPIs(d); 
                    if ($('#viewAnalysis').is(':visible') && currentAnalysisMode) loadAnalysisTable(currentAnalysisMode);
                },
                rowGroup: {
                    enable: false,
                    startRender: function ( rows, group ) {
                        const count = rows.count();
                        const stats = currentGroupStats[group] || { total: 0, rank: 0, pct: 0 };
                        let partnerTotals = {};
                        rows.every(function() {
                            let d = this.data();
                            let partner = (groupingFocus === 'entidad') ? d.ganador : d.entidad;
                            if(partner && partner !== 'Desconocido') partnerTotals[partner] = (partnerTotals[partner] || 0) + d.importe_adjudicacion;
                        });
                        let sortedPartners = Object.keys(partnerTotals).sort((a,b) => partnerTotals[b] - partnerTotals[a]).slice(0, 2);
                        let insightHTML = "";
                        if(sortedPartners.length > 0) {
                            let label = (groupingFocus === 'entidad') ? "Top:" : "Cli:";
                            let partnersStr = sortedPartners.map(p => `<span>${p.substring(0,15)}..</span>`).join('<span class="text-muted mx-1">,</span>');
                            insightHTML = `<div class="group-insight"><span class="fw-bold">${label}</span>${partnersStr}</div>`;
                        }
                        let icon = (groupingFocus === 'entidad') ? '<i class="bi bi-bank2 text-secondary"></i>' : '<i class="bi bi-cone-striped text-secondary"></i>';
                        return $('<tr class="dtrg-group">').append(`<td colspan="11"><div class="group-header-container"><div class="group-left"><i class="bi bi-chevron-right group-expander"></i><div class="group-rank-badge">#${stats.rank}</div>${icon}<div class="group-name" title="${group}">${group}</div>${insightHTML}</div><div class="group-right"><div class="metric-box"><span class="metric-val">${eur.format(stats.total)} €</span><span class="metric-lbl">VOLUMEN</span></div><div class="metric-box"><span class="metric-val text-muted">${stats.pct.toFixed(1)}%</span><span class="metric-lbl">CUOTA</span></div><span class="badge bg-white text-dark border ms-2">${count}</span></div></div></td>`);
                    }
                },
                columns: [
                    { data: 'fecha_publicacion', render: (d,t,r) => (t==='sort'||t==='type')?r.fecha_pub_iso||'':`<span class="text-secondary small text-nowrap">${d||'-'}</span>` },
                    { data: 'fecha_adjudicacion', render: (d,t,r) => (t==='sort'||t==='type')?r.fecha_iso||'':`<span class="fw-medium text-dark text-nowrap">${d}</span>` },
                    { data: 'estado_fase', className: 'text-center', render: d => `<span class="badge-status ${d.includes('ADJ')?'status-adj':(d.includes('FORM')?'status-form':'status-cerr')}">${d.substring(0,10)}</span>` },
                    { data: 'tipo_licitacion', className: 'text-center', render: d => `<span class="badge-status" style="color:${d==='OBRA'?'#ef4444':'#3b82f6'}; border:1px solid currentColor">${d}</span>` },
                    { data: 'entidad', render: (d,t,r) => `<div style="line-height:1.2"><div class="fw-bold text-truncate" style="max-width:280px"><a onclick="applyAnalysisFilter('entidad', '${d.replace(/'/g, "\\'")}')" class="winner-link">${d}</a></div><div class="text-muted text-truncate small" style="max-width:280px">${r.objeto}</div></div>` },
                    { data: 'ganador', render: (d,t,r) => `<div class="d-flex align-items-center"><a onclick="applyAnalysisFilter('contratistas', '${d.replace(/'/g, "\\'")}')" class="winner-link text-truncate d-block small" style="max-width:200px">${d}${r.es_ute ? '<span class="badge-ute">UTE</span>' : ''}</a></div>` },
                    { data: 'presupuesto_base', className: 'text-end', render: (d,t) => t==='display'?`<span class="text-secondary small">${eurDec.format(d)} €</span>`:d },
                    { data: 'importe_adjudicacion', className: 'text-end', render: (d,t) => t==='display'?`<span class="fw-bold text-dark small">${eurDec.format(d)} €</span>`:d },
                    { data: 'baja_pct', className: 'text-center', render: d => `<span class="badge-baja ${d>=20?'baja-high':(d>=10?'baja-mid':'baja-low')}">${d.toFixed(2).replace('.', ',')}%</span>` },
                    { data: 'num_licitadores', className: 'text-center', render: d => d },
                    { data: null, orderable: false, className: 'text-end', render: (d,t,r,m) => `<button class="btn btn-sm btn-outline-secondary border-0" onclick='verDetalle(${m.row})'><i class="bi bi-eye"></i></button>` },
                    { data: 'groupSort', visible: false, type: 'num' }
                ]
            });
        }

        function setGlobalFilter(key, val, btn) { 
            if(key === 'tipo') { $('.btn-filter').removeClass('active'); $(btn).addClass('active'); currentFilters.tipo = val; } 
            if (viewMode === 'grouped') { updateGroupingLogic(); } else { table.draw(); }
        }
        function triggerExport(t) { let at = $('#viewAnalysis').is(':visible') ? analysisTable : table; if(at && t==='excel') at.button('.buttons-excel').trigger(); if(at && t==='copy') at.button('.buttons-copy').trigger(); }
        function toDateFromISO(iso) { if(!iso || iso.length < 10) return null; return new Date(parseInt(iso.slice(0,4)), parseInt(iso.slice(5,7))-1, parseInt(iso.slice(8,10))); }
        function parseDate(d) { if(!d) return null; const p = d.split('/'); return new Date(parseInt(p[2],10), parseInt(p[1],10)-1, parseInt(p[0],10)); }
        
        function updateKPIs(data) {
            let volBase = 0, volAdj = 0, sumBaja = 0, sumLic = 0; 
            let maxLic = 0, singleLicCount = 0;
            const contratistasUnicos = new Set();
            data.forEach(d => {
                volBase += d.presupuesto_base; volAdj += d.importe_adjudicacion; 
                sumBaja += d.baja_pct; sumLic += d.num_licitadores;
                if(d.num_licitadores > maxLic) maxLic = d.num_licitadores;
                if(d.num_licitadores === 1) singleLicCount++;
                if(d.ganador !== "Desconocido") contratistasUnicos.add(d.ganador);
            });
            $('#kpi-volumen-base').text(eur.format(volBase) + ' €');
            $('#kpi-volumen-adj').text(eur.format(volAdj) + ' €');
            let avgBaja = data.length > 0 ? (sumBaja / data.length) : 0;
            let colorBaja = avgBaja > 15 ? '#16a34a' : (avgBaja > 5 ? '#2563eb' : '#64748b');
            $('#kpi-baja').text(avgBaja.toFixed(2).replace('.', ',') + '%').css('color', colorBaja);
            let ahorroTotal = Math.max(0, volBase - volAdj);
            $('#kpi-ahorro-total').text(eur.format(ahorroTotal) + ' €');
            let avgLic = data.length > 0 ? (sumLic / data.length) : 0;
            $('#kpi-licitadores').text(avgLic.toFixed(2).replace('.', ','));
            $('#kpi-lic-max').text(maxLic);
            let singleLicPct = data.length > 0 ? ((singleLicCount / data.length) * 100) : 0;
            $('#kpi-lic-unique').text(singleLicPct.toFixed(0) + '%');
            $('#kpi-contratistas').text(contratistasUnicos.size);
        }

        function toggleViewMode() {
            const btn = $('#btnViewMode');
            if(viewMode === 'detail') { 
                viewMode = 'grouped'; btn.addClass('active').html('<i class="bi bi-layers-fill"></i> Desagrupar'); $('#btnExpandAll').show(); 
            } else { 
                viewMode = 'detail'; btn.removeClass('active').html('<i class="bi bi-layers"></i> Agrupar'); $('#btnExpandAll').hide(); 
                table.rowGroup().enable(false); table.order.fixed(null); 
            }
            updateGroupingLogic();
        }

        function toggleExpandAll() {
            if (viewMode !== 'grouped') return;
            const btn = $('#btnExpandAll');
            const rows = $('#tablaContratos tbody tr:not(.dtrg-group)'), groups = $('.dtrg-group');
            if (!allGroupsExpanded) { rows.show(); groups.addClass('expanded'); allGroupsExpanded = true; btn.html('<i class="bi bi-arrows-collapse"></i>'); } 
            else { rows.hide(); groups.removeClass('expanded'); allGroupsExpanded = false; btn.html('<i class="bi bi-arrows-expand"></i>'); }
        }
        
        function updateGroupingLogic() {
            if (viewMode === 'detail') { table.order([[2, 'desc']]).draw(); return; }
            let groupColName = (groupingFocus === 'entidad') ? 'entidad' : 'ganador';
            let groupTotals = {}, globalTotal = 0;
            table.rows({ search: 'applied' }).data().toArray().forEach(row => { 
                let k = row[groupColName]; if(!groupTotals[k]) groupTotals[k]=0; groupTotals[k]+=row.importe_adjudicacion; globalTotal+=row.importe_adjudicacion; 
            });
            table.rows().every(function() { let d=this.data(); d.groupSort=groupTotals[d[groupColName]]||0; this.invalidate(); });
            let sortedKeys = Object.keys(groupTotals).sort((a,b) => groupTotals[b]-groupTotals[a]);
            currentGroupStats = {}; sortedKeys.forEach((k,i) => { currentGroupStats[k] = { total: groupTotals[k], rank: i+1, pct: globalTotal>0?(groupTotals[k]/globalTotal*100):0 }; });
            table.rowGroup().dataSrc(groupColName).enable(true); 
            table.order.fixed( { pre: [ 11, 'desc' ] } );
            table.order([ 7, 'desc' ]).draw();
            $('.dtrg-group').nextUntil('.dtrg-group').hide();
        }

        function setDateMode(mode, btn) { 
            dateMode = mode; $('.btn-date-mode').removeClass('active'); $(btn).addClass('active'); table.draw(); 
        }
        
        function loadAnalysisTable(mode) {
            currentAnalysisMode = mode; 
            let d = table.rows({ search: 'applied' }).data().toArray();
            let stats = {}, cat = (mode==='contratistas')?'contratistas':'entidad';
            d.forEach(row => {
                let k = (cat==='entidad')?row.entidad:row.ganador; if(!k || k==='Desconocido') return;
                if(!stats[k]) stats[k] = { count:0, vol:0, baja:0, lic:0 };
                stats[k].count++; stats[k].vol+=row.importe_adjudicacion; stats[k].baja+=row.baja_pct; stats[k].lic+=row.num_licitadores;
            });
            let aData = Object.keys(stats).map(k => ({ name:k, count:stats[k].count, vol:stats[k].vol, avgBaja:stats[k].count?(stats[k].baja/stats[k].count):0, avgLic:stats[k].count?(stats[k].lic/stats[k].count):0, category:cat }));
            let cols = [
                { title:"#", data:null, render:(d,t,r,m)=>m.row+1, className:"dt-center", width:"5%" },
                { title:"Nombre", data:"name", width:"40%" },
                { title:"Exps", data:"count", className:"dt-center", width:"10%" },
                { title:"Volumen", data:"vol", className:"dt-right", render:function(d,t){ return t==='display'?eurDec.format(d)+' €':d; }, width:"20%" },
                { title:"Baja Med", data:"avgBaja", className:"dt-center", render:function(d,t){ return t==='display'?d.toFixed(2)+'%':d; }, width:"10%" }
            ];
            if($.fn.DataTable.isDataTable('#tablaAnalisis')) $('#tablaAnalisis').DataTable().destroy(); $('#tablaAnalisis').empty();
            let defaultSort = [3, 'desc']; if(mode === 'baja') defaultSort = [4, 'desc']; if(mode === 'licitadores') defaultSort = [2, 'desc'];
            analysisTable = $('#tablaAnalisis').DataTable({ 
                data:aData, columns:cols, order:[defaultSort], paging:false, dom:'t', 
                buttons:[{extend:'excel',className:'buttons-excel'}] 
            });
            $('#tablaAnalisis tbody').off('click','tr').on('click','tr',function(){ let dt = analysisTable.row(this).data(); if(dt) applyAnalysisFilter(dt.category, dt.name); });
            $('#viewMain').hide(); $('#viewAnalysis').fadeIn(200);
        }
        
        function applyAnalysisFilter(cat, val) { 
            currentFilters.analysisCategory = cat; currentFilters.analysisValue = val; 
            $('#filterName').text(val); $('#activeFilterAlert').css('display','flex'); 
            $('#viewAnalysis').hide(); $('#viewMain').fadeIn(200); 
            table.draw();
        }
        
        function parseSpanishDate(str) { if(!str || str.length < 10) return null; const p = str.split('/'); if(p.length !== 3) return null; return new Date(p[2], p[1]-1, p[0]); }
        function copiarExp() { navigator.clipboard.writeText($('#modalExp').text()).then(() => alert('Copiado!')); }
        window.verDetalle = function(idx) {
            const d = table.row(idx).data();
            $('#modalTipo').text(d.tipo_licitacion); $('#modalEstado').text(d.estado_fase); $('#modalObjeto').text(d.objeto);
            $('#modalEntidad').text(d.entidad); $('#modalExp').text(d.expediente); $('#btnLinkOriginal').attr('href', d.url_ficha);
            let pct = d.baja_pct; let lic = d.num_licitadores;
            let insight = (pct>20)?"<strong>Temeraria</strong> (>20%)":(pct<2?"<strong>Ajustada</strong> (<2%)":(lic>10?"<strong>Alta Competencia</strong>":"Estándar"));
            $('#insightText').html(insight);
            $('#modalBase').text(eurDec.format(d.presupuesto_base)+' €'); $('#modalAdj').text(eurDec.format(d.importe_adjudicacion)+' €');
            $('#modalBajaPct').text(d.baja_pct.toFixed(2).replace('.',',')+'%');
            $('#barraBaja').css('width', Math.min(d.baja_pct,100)+'%').css('background-color', (d.baja_pct>25?'#ef4444':(d.baja_pct>15?'#f59e0b':'#22c55e')));
            $('#modalFechaPub').text(d.fecha_publicacion||'--'); $('#modalFechaAdj').text(d.fecha_adjudicacion||'--');
            if(d.fecha_adjudicacion && d.fecha_adjudicacion!=="Pendiente") $('#stepAdj').addClass('completed').find('.step-circle').html('<i class="bi bi-check text-white"></i>').css('background','#16a34a');
            else $('#stepAdj').removeClass('completed').find('.step-circle').html('').css('background','#e2e8f0');
            let f1 = (d.fecha_pub_iso && d.fecha_pub_iso.length>5)?new Date(d.fecha_pub_iso):parseSpanishDate(d.fecha_publicacion);
            let f2 = (d.fecha_iso && d.fecha_iso.length>5)?new Date(d.fecha_iso):parseSpanishDate(d.fecha_adjudicacion);
            $('#modalDiasTrans').text((f1&&f2&&!isNaN(f1)&&!isNaN(f2)) ? Math.ceil(Math.abs(f2-f1)/(1000*60*60*24)) : "En curso");
            let htmlRiv = '';
            if(d.ganador && d.ganador !== 'Desconocido') htmlRiv += `<div class="rival-row" style="background:#f0fdf4; border-color:#bbf7d0"><div class="avatar-circle" style="background:linear-gradient(135deg, #3b82f6, #2563eb)">${d.ganador.substring(0,2)}</div><div style="flex-grow:1"><div class="fw-bold text-dark">${d.ganador}</div><div class="text-success small fw-bold">GANADOR</div></div><a href="https://www.google.com/search?q=${d.ganador}" target="_blank" class="search-icon"><i class="bi bi-search"></i></a></div>`;
            if(d.rivales) d.rivales.forEach(r => { if(r!==d.ganador) htmlRiv+=`<div class="rival-row"><div class="avatar-circle">${r.substring(0,2)}</div><div style="flex-grow:1; color:#64748b; font-weight:600; font-size:0.9rem;">${r}</div><a href="https://www.google.com/search?q=${r}" target="_blank" class="search-icon"><i class="bi bi-search"></i></a></div>`; });
            $('#modalNumLic').text(d.num_licitadores); $('#modalRivales').html(htmlRiv || '<div class="text-muted small p-3">Sin datos</div>');
            let htmlDocs = '';
            if(d.documentos) d.documentos.forEach(doc => htmlDocs+=`<a href="${doc.url}" target="_blank" class="btn btn-outline-secondary btn-sm text-start text-truncate"><i class="bi bi-file-earmark-pdf me-2 text-danger"></i>${doc.nombre}</a>`);
            $('#modalDocs').html(htmlDocs || '<div class="text-muted small">No hay documentos.</div>');
            new bootstrap.Modal('#modalDetalle').show();
        };
    </script>
</body>
</html>
"""

def normalize_fecha_es(fecha_txt: str):
    if not fecha_txt: return "Pendiente", ""
    s = fecha_txt.strip()
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", s)
    if m: return f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{int(m.group(3))}", f"{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", s)
    if m: return f"{int(m.group(3)):02d}/{int(m.group(2)):02d}/{int(m.group(1))}", f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    m = re.match(r"^(\d{1,2})-(\d{1,2})-(\d{4})$", s)
    if m: return f"{int(m.group(1)):02d}/{int(m.group(2)):02d}/{int(m.group(3))}", f"{int(m.group(3)):04d}-{int(m.group(2)):02d}-{int(m.group(1)):02d}"
    return "Pendiente", ""

class MonitorEngine:
    def __init__(self):
        # NOTA: Las fechas en las URLs (p11=01/01/2025) se sobreescribirán en runtime
        # si ya existen datos en la DB.
        self.base_sources = [
            {"tipo": "OBRA", "estado": "ADJUDICADO", "base_url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=5&p11={}&p26=ES212&idioma=es&R01HNoPortal=true"},
            {"tipo": "OBRA", "estado": "FORMALIZADO", "base_url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=8&p11={}&p26=ES212&idioma=es&R01HNoPortal=true"},
            {"tipo": "OBRA", "estado": "CERRADO", "base_url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=1&p02=14&p11={}&p26=ES212&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "ADJUDICADO", "base_url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=5&p11={}&p26=ES212&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "FORMALIZADO", "base_url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=8&p11={}&p26=ES212&idioma=es&R01HNoPortal=true"},
            {"tipo": "SERV", "estado": "CERRADO", "base_url": "https://www.contratacion.euskadi.eus/ac70cPublicidadWar/suscribirAnuncio/suscripcionRss?p01=2&p02=14&p11={}&p26=ES212&idioma=es&R01HNoPortal=true"}
        ]
        self.session = requests.Session()
        self.headers = {'User-Agent': 'Mozilla/5.0'}
        self.processed_ids = set()
        self.db = []
        self.latest_date = None

        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, 'r', encoding='utf-8') as f:
                    self.db = json.load(f)
                
                # Encontrar la fecha más reciente para optimizar la carga
                dates = []
                for d in self.db:
                    # Normalizar fechas antiguas si es necesario
                    if 'fecha_iso' not in d:
                        disp, iso = normalize_fecha_es(d.get('fecha_adjudicacion', ''))
                        d['fecha_adjudicacion'] = disp; d['fecha_iso'] = iso
                    
                    if d.get('fecha_pub_iso') and len(d['fecha_pub_iso']) == 10:
                        dates.append(d['fecha_pub_iso'])

                if dates:
                    dates.sort()
                    self.latest_date = dates[-1] # La fecha más reciente (YYYY-MM-DD)
                
                unique_dict = {d['url_ficha']: d for d in self.db}
                self.db = list(unique_dict.values())
                self.processed_ids = {d.get('id') for d in self.db if d.get('id')}
                print(f"✅ DB cargada: {len(self.db)} registros. Última fecha conocida: {self.latest_date or 'N/A'}")
            except Exception: pass

    def backup_db(self):
        if not os.path.exists(BACKUP_DIR): os.makedirs(BACKUP_DIR)
        if os.path.exists(DB_FILE):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            shutil.copy2(DB_FILE, f"{BACKUP_DIR}/db_backup_{timestamp}.json")
            print(f"🛡️ Backup creado: db_backup_{timestamp}.json")

    def clean_money(self, txt):
        if not txt: return 0.0
        try: return float(txt.replace('.', '').replace(',', '.'))
        except Exception: return 0.0

    def clean_text(self, txt):
        if not txt: return "Desconocido"
        return " ".join(txt.split()).title()

    def get_tab_value(self, soup, tab_id, label):
        tab = soup.find('div', id=tab_id)
        if not tab: return None
        for row in tab.find_all('div', class_='row'):
            cols = row.find_all('div', recursive=False)
            if len(cols) >= 2 and label.lower() in cols[0].get_text(strip=True).lower():
                return cols[1].get_text(strip=True)
        return None
        
    def sanitize_data(self, data):
        """ Corrige errores conocidos en los datos (ej: Donostiako Etxegintza) """
        try:
            entidad_upper = (data.get('entidad') or "").upper()
            ganador_upper = (data.get('ganador') or "").upper()
            
            # --- FIX: Donostiako Etxegintza / Urdinberri ---
            if "ETXEGINTZA" in entidad_upper and ("URDINBERRI" in ganador_upper or "URDIBERRI" in ganador_upper):
                base = data.get('presupuesto_base', 0)
                adj = data.get('importe_adjudicacion', 0)
                
                # Si la adjudicación es disparatada (ej: > 2 veces el base), probablemente faltan decimales o sobran ceros
                if base > 0 and adj > (base * 1.5):
                    # Intentar corregir dividiendo por 100 (error céntimos común) o ajustando al base
                    # Asumimos error de céntimos (leer 100000 cents como 100000 euros)
                    data['importe_adjudicacion'] = adj / 100.0
                    # Recalcular baja
                    if data['presupuesto_base'] > 0:
                        data['baja_pct'] = round(((data['presupuesto_base'] - data['importe_adjudicacion']) / data['presupuesto_base']) * 100, 2)
                    print(f"🔧 CORRECCIÓN APLICADA: Urdinberri/Etxegintza ajustado de {adj}€ a {data['importe_adjudicacion']}€")

        except Exception as e:
            print(f"⚠️ Error sanitizando datos: {e}")
        return data

    def process_url(self, url, tipo, estado):
        try:
            r = self.session.get(url, headers=self.headers, timeout=20)
            if r.status_code != 200: return None
            soup = BeautifulSoup(r.content, 'html.parser')
            data = {'id': hashlib.md5(url.encode()).hexdigest(), 'url_ficha': url, 'tipo_licitacion': tipo, 'estado_fase': estado}
            head = soup.find('div', class_='cabeceraDetalle')
            data['objeto'] = "Sin descripción"
            fecha_pub_text = None
            if head:
                dt_obj = head.find('dt', string=lambda text: text and "Objeto" in text)
                if dt_obj:
                    dd_obj = dt_obj.find_next_sibling('dd')
                    if dd_obj: data['objeto'] = dd_obj.get_text(strip=True)
                else:
                    dd_first = head.find('dd')
                    if dd_first: data['objeto'] = dd_first.get_text(strip=True)
                for dt in head.find_all('dt'):
                    if "primera publicación" in dt.get_text(strip=True).lower():
                        dd = dt.find_next_sibling('dd')
                        if dd: fecha_pub_text = dd.get_text(strip=True).split(' ')[0]
                        break
            if not fecha_pub_text: fecha_pub_text = self.get_tab_value(soup, 'tabs-1', 'Fecha de publicación')
            pub_disp, pub_iso = normalize_fecha_es(fecha_pub_text or "")
            data['fecha_publicacion'] = pub_disp; data['fecha_pub_iso'] = pub_iso
            fecha_adj = self.get_tab_value(soup, 'tabs-9', 'Fecha adjudicación')
            if not fecha_adj:
                for dt in soup.find_all('dt'):
                    if "última publicación" in dt.get_text(strip=True).lower():
                        dd = dt.find_next_sibling('dd')
                        if dd: fecha_adj = dd.get_text(strip=True).split(' ')[0]
                        break
            fecha_display, fecha_iso = normalize_fecha_es(fecha_adj or "")
            data['fecha_adjudicacion'] = fecha_display; data['fecha_iso'] = fecha_iso
            raw_entidad = self.get_tab_value(soup, 'tabs-2', 'Poder adjudicador')
            data['entidad'] = self.clean_text(raw_entidad)
            data['expediente'] = self.get_tab_value(soup, 'tabs-1', 'Expediente') or "N/A"
            base = self.get_tab_value(soup, 'tabs-4', 'Presupuesto del contrato sin IVA') or self.get_tab_value(soup, 'tabs-4', 'Valor estimado')
            adj = self.get_tab_value(soup, 'tabs-9', 'Precio sin IVA')
            data['presupuesto_base'] = self.clean_money(base)
            data['importe_adjudicacion'] = self.clean_money(adj)
            raw_ganador = self.get_tab_value(soup, 'tabs-9', 'Razón social')
            data['ganador'] = self.clean_text(raw_ganador)
            ganador_upper = (data['ganador'] or "").upper()
            data['es_ute'] = any(x in ganador_upper for x in ['UTE', 'UNION TEMPORAL', 'UNIÓN TEMPORAL', 'ALDI BATERAKO'])
            if data['presupuesto_base'] > 0 and data['importe_adjudicacion'] > 0:
                data['baja_pct'] = round(((data['presupuesto_base'] - data['importe_adjudicacion']) / data['presupuesto_base']) * 100, 2)
            else: data['baja_pct'] = 0.0
            rivales = []
            tab8 = soup.find('div', id='tabs-8')
            if tab8:
                for row in tab8.find_all('div', class_='row'):
                    cols = row.find_all('div', recursive=False)
                    if len(cols) >= 2 and "razón social" in cols[0].get_text(strip=True).lower():
                        rivales.append(self.clean_text(cols[1].get_text(strip=True)))
            data['rivales'] = sorted(set(rivales))
            data['num_licitadores'] = len(data['rivales'])
            docs = []
            for a in soup.find_all('a', onclick=True):
                onclick = a.get('onclick') or ""
                if "descargarFichero" in onclick:
                    fid = re.search(r"'(\d+)'", onclick)
                    if fid:
                        ep = "descargaFicheroContratoPorIdFichero" if "Contrato" in onclick else "descargaFicheroPorIdFichero"
                        docs.append({'nombre': a.get_text(strip=True) or "Documento", 'url': f"https://www.contratacion.euskadi.eus/ac70cPublicidadWar/downloadDokusiREST/{ep}?idFichero={fid.group(1)}&R01HNoPortal=true"})
            data['documentos'] = docs
            
            # --- APLICAR CORRECCIONES DE DATOS ---
            data = self.sanitize_data(data)
            
            return data
        except Exception: return None

    def repair_db(self):
        """ Revisa la DB local en busca de datos faltantes y los repara """
        print("🔧 Revisando registros antiguos incompletos...")
        repaired_count = 0
        for i, item in enumerate(self.db):
            # Condición de "roto": No tiene fecha de publicación o es Pendiente
            needs_repair = False
            if not item.get('fecha_pub_iso') or item.get('fecha_publicacion') == 'Pendiente':
                needs_repair = True
            
            # También reaplicar sanitización si se nos pasó
            if needs_repair:
                print(f"   Reparando: {item.get('objeto')[:40]}...")
                try:
                    new_data = self.process_url(item['url_ficha'], item['tipo_licitacion'], item['estado_fase'])
                    if new_data:
                        self.db[i] = new_data # Actualizar en sitio
                        repaired_count += 1
                        time.sleep(0.5) # Pausa para no saturar
                except Exception as e:
                    print(f"   Error reparando: {e}")

        if repaired_count > 0:
            print(f"✅ Reparados {repaired_count} registros antiguos.")
            # Guardar cambios intermedios
            unique_dict = {d['url_ficha']: d for d in self.db}
            self.db = list(unique_dict.values())
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.db, f, ensure_ascii=False, indent=2)

    def run(self, force_scrape=True):
        if force_scrape:
            print("🚀 MONITOR v9.33 INICIANDO...")
            self.backup_db()
            
            # --- PASO 1: REPARAR DATOS ANTIGUOS ---
            self.repair_db()

            # --- PASO 2: CARGA INCREMENTAL (NUEVOS) ---
            new_items = 0
            start_date_str = "01/01/2025" # Default
            if self.latest_date:
                try:
                    last_dt = datetime.strptime(self.latest_date, "%Y-%m-%d")
                    safe_start = last_dt - timedelta(days=5)
                    start_date_str = safe_start.strftime("%d/%m/%Y")
                    print(f"📅 Optimización activada: Buscando solo desde {start_date_str}")
                except: pass
            
            active_sources = []
            for bs in self.base_sources:
                url_final = bs['base_url'].format(start_date_str)
                active_sources.append({**bs, 'url': url_final})

            for s in active_sources:
                try:
                    r = self.session.get(s['url'], headers=self.headers, timeout=25)
                    if r.status_code != 200: continue
                    root = ET.fromstring(r.content)
                    for item in root.findall('.//item'):
                        link_el = item.find('link')
                        if link_el is None or not link_el.text: continue
                        link = link_el.text.strip()
                        item_id = hashlib.md5(link.encode()).hexdigest()
                        if item_id not in self.processed_ids:
                            print(f" + Nuevo: {link[-20:]}")
                            data = self.process_url(link, s['tipo'], s['estado'])
                            if data:
                                self.processed_ids.add(item_id)
                                self.db.append(data)
                                new_items += 1
                                time.sleep(0.1)
                except Exception as e: print(f"Error RSS: {e}")
            
            if new_items > 0:
                unique_dict = {d['url_ficha']: d for d in self.db}
                self.db = list(unique_dict.values())
                with open(DB_FILE, 'w', encoding='utf-8') as f:
                    json.dump(self.db, f, ensure_ascii=False, indent=2)
                print(f"💾 Guardados {new_items} nuevos expedientes.")
            else: print("💤 Sin novedades.")
        return self.db

def get_now_str(tz_key="Europe/Madrid"):
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo(tz_key)).strftime("%d/%m/%Y %H:%M")
    except Exception: return datetime.now().strftime("%d/%m/%Y %H:%M")

if __name__ == "__main__":
    SCRAPE_ACTIVO = True 
    engine = MonitorEngine()
    data = None
    if not SCRAPE_ACTIVO:
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f: 
                raw_data = json.load(f)
                unique_d = {d['url_ficha']: d for d in raw_data}
                data = list(unique_d.values())
            print(f"📦 MODO LOCAL: cargados {len(data)} registros únicos.")
        else:
            print("⚠️ No hay DB local. Activando escaneo forzoso...")
            data = engine.run(force_scrape=True)
    else:
        data = engine.run(force_scrape=True)

    now_str = get_now_str("Europe/Madrid")
    html = HTML_TEMPLATE.replace('__DATOS_JSON__', json.dumps(data, ensure_ascii=False)).replace('__FECHA__', now_str)
    with open(HTML_FILE, "w", encoding="utf-8") as f: f.write(html)
    print(f"✅ Dashboard generado: {HTML_FILE}")
