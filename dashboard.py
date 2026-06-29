import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from flask import Flask, render_template_string, request
from compare import rebuild_compare_db

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "merch_details.db"
COMPARE_DB_PATH = BASE_DIR / "compare.db"
ALLOWED_TABLES = ["user_info", "sell_ads", "buy_ads"]

app = Flask(__name__)
IST_TZ = timezone(timedelta(hours=5, minutes=30))

TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Merchant Details Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-space: #070913;
      --bg-panel: rgba(16, 22, 40, 0.75);
      --bg-panel-solid: #0f1524;
      --border-glow: rgba(99, 102, 241, 0.15);
      --border-muted: rgba(255, 255, 255, 0.08);
      --color-primary: #6366f1;
      --color-secondary: #06b6d4;
      --color-success: #10b981;
      --color-danger: #f43f5e;
      --color-warning: #f59e0b;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-dark: #64748b;
      --accent-gradient: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--bg-space);
      background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.08) 0px, transparent 50%);
      background-attachment: fixed;
      color: var(--text-main);
      line-height: 1.5;
      padding-bottom: 40px;
    }

    /* Navbar / Header */
    .app-header {
      background: rgba(15, 21, 36, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-muted);
      padding: 14px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
    }

    .brand-logo {
      background: var(--accent-gradient);
      width: 38px;
      height: 38px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }

    .brand-title {
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.5px;
      background: var(--accent-gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .nav-menu {
      display: flex;
      gap: 6px;
      background: rgba(255, 255, 255, 0.03);
      padding: 4px;
      border-radius: 10px;
      border: 1px solid var(--border-muted);
    }

    .nav-btn {
      padding: 8px 18px;
      border-radius: 8px;
      color: var(--text-muted);
      font-size: 14px;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s ease;
    }

    .nav-btn:hover {
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.05);
    }

    .nav-btn.active {
      color: #fff;
      background: var(--color-primary);
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
    }

    /* Container layout */
    .container {
      max-width: 1440px;
      margin: 24px auto;
      padding: 0 24px;
    }

    .page-title-section {
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .page-title {
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.5px;
    }

    .page-subtitle {
      font-size: 14px;
      color: var(--text-muted);
      margin-top: 4px;
    }

    /* Card styling */
    .glass-card {
      background: var(--bg-panel);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border-muted);
      border-radius: 14px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    .card-title {
      font-size: 15px;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text-main);
      border-bottom: 1px solid var(--border-muted);
      padding-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    /* Filter Form & Grid */
    .filters-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .filter-grid-primary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
    }

    .filter-grid-secondary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      border-top: 1px solid var(--border-muted);
      padding-top: 16px;
      margin-top: 8px;
    }

    .input-wrapper {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    label {
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    input, select {
      background: rgba(15, 22, 40, 0.6);
      border: 1px solid var(--border-muted);
      border-radius: 8px;
      color: var(--text-main);
      padding: 10px 14px;
      font-size: 13px;
      font-family: inherit;
      width: 100%;
      outline: none;
      transition: all 0.2s ease;
    }

    input:focus, select:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
      background: rgba(15, 22, 40, 0.85);
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 20px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s ease;
      font-family: inherit;
    }

    .btn-primary {
      background: var(--accent-gradient);
      color: #fff;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
    }

    .btn-primary:hover {
      opacity: 0.95;
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.05);
      color: var(--text-main);
      border: 1px solid var(--border-muted);
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: var(--text-muted);
    }

    .btn:active {
      transform: translateY(0);
    }

    .btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none !important;
    }

    /* Stats Grid */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }

    .stat-card {
      background: var(--bg-panel);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border-muted);
      border-radius: 14px;
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
      position: relative;
      overflow: hidden;
    }

    .stat-card::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: var(--accent-gradient);
    }

    .stat-icon {
      font-size: 22px;
      width: 46px;
      height: 46px;
      background: rgba(99, 102, 241, 0.1);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--color-primary);
    }

    .stat-content {
      display: flex;
      flex-direction: column;
    }

    .stat-label {
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .stat-value {
      font-size: 22px;
      font-weight: 700;
      color: #fff;
      margin-top: 2px;
    }

    /* Table styling */
    .table-container {
      border: 1px solid var(--border-muted);
      border-radius: 10px;
      overflow: hidden;
      background: rgba(10, 15, 30, 0.4);
      margin-top: 12px;
    }

    .table-responsive {
      max-height: 65vh;
      overflow-y: auto;
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 13px;
      text-align: left;
    }

    th {
      background: var(--bg-panel-solid);
      color: var(--text-muted);
      font-weight: 600;
      padding: 14px 16px;
      border-bottom: 1px solid var(--border-muted);
      position: sticky;
      top: 0;
      z-index: 10;
      white-space: nowrap;
    }

    td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-muted);
      color: var(--text-main);
      white-space: nowrap;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tbody tr {
      transition: background-color 0.15s ease;
    }

    tbody tr:hover {
      background-color: rgba(255, 255, 255, 0.02);
    }

    tbody tr:nth-child(even) {
      background-color: rgba(255, 255, 255, 0.005);
    }

    /* Scrollbars */
    .table-responsive::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }

    .table-responsive::-webkit-scrollbar-track {
      background: transparent;
    }

    .table-responsive::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.15);
      border-radius: 10px;
    }

    .table-responsive::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.3);
    }

    /* Badges */
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
      line-height: 1;
    }

    .badge-success {
      background: rgba(16, 185, 129, 0.12);
      color: var(--color-success);
      border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .badge-danger {
      background: rgba(244, 63, 94, 0.12);
      color: var(--color-danger);
      border: 1px solid rgba(244, 63, 94, 0.2);
    }

    .badge-neutral {
      background: rgba(148, 163, 184, 0.1);
      color: var(--text-muted);
      border: 1px solid rgba(148, 163, 184, 0.15);
    }

    .empty-cell {
      color: var(--text-dark);
      font-weight: 300;
    }

    /* SQL Debug Terminal */
    .sql-terminal {
      background: #05070f;
      border: 1px solid #1e293b;
      border-radius: 10px;
      padding: 16px;
      font-family: "Courier New", Courier, monospace;
      color: #38bdf8;
      font-size: 12px;
      overflow-x: auto;
      margin-top: 12px;
      box-shadow: inset 0 2px 8px rgba(0,0,0,0.8);
    }

    .sql-terminal-header {
      display: flex;
      justify-content: space-between;
      color: var(--text-dark);
      font-size: 11px;
      margin-bottom: 8px;
      font-weight: bold;
      text-transform: uppercase;
    }

    .collapsible-debug {
      cursor: pointer;
      user-select: none;
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 12px;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border-muted);
      font-size: 13px;
      font-weight: 600;
    }

    .collapsible-debug:hover {
      background: rgba(255, 255, 255, 0.04);
    }

    .debug-content {
      display: none;
      margin-top: 12px;
    }

    .debug-content.open {
      display: block;
    }

    /* Error alert */
    .error-card {
      background: rgba(244, 63, 94, 0.1);
      border: 1px solid rgba(244, 63, 94, 0.25);
      border-radius: 10px;
      padding: 16px;
      color: var(--color-danger);
      font-weight: 600;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      gap: 12px;
    }

    /* Toast styles */
    #toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .toast {
      background: #131b2e;
      border-radius: 8px;
      border: 1px solid var(--border-muted);
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
      padding: 12px 18px;
      font-size: 13px;
      font-weight: 500;
      min-width: 280px;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      opacity: 0;
      transform: translateY(20px);
    }
    .toast-success {
      border-left: 4px solid var(--color-success);
    }
    .toast-error {
      border-left: 4px solid var(--color-danger);
    }
  </style>
</head>
<body>
  <header class="app-header">
    <a href="/" class="brand">
      <div class="brand-logo">📈</div>
      <span class="brand-title">Merchant Analytics Hub</span>
    </a>
    <div style="display: flex; align-items: center; gap: 16px;">
      <button type="button" class="btn btn-secondary" id="syncBtn" onclick="syncCompareDb()">
        <span class="btn-text">Sync Compare DB</span>
        <span class="spinner" style="display:none; margin-left: 5px;">⏳</span>
      </button>
      <nav class="nav-menu">
        <a href="/" class="nav-btn" id="nav-btn-home">Merchants</a>
        <a href="/compare" class="nav-btn" id="nav-btn-compare">Comparison</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <div class="page-title-section">
      <div>
        <h2 class="page-title">Merchant Database Explorer</h2>
        <div class="page-subtitle">View and filter P2P advertiser and merchant telemetry data.</div>
      </div>
    </div>

    {% if error %}
      <div class="error-card">
        <span>⚠️</span>
        <div><strong>Query Error:</strong> {{ error }}</div>
      </div>
    {% endif %}

    <div class="glass-card">
      <div class="card-title">🔍 Filters & Settings</div>
      <form method="get" class="filters-form">
        <div class="filter-grid-primary">
          <div class="input-wrapper">
            <label for="table">Source Table</label>
            <select id="table" name="table" onchange="this.form.submit()">
              {% for t in allowed_tables %}
                <option value="{{ t }}" {% if t == filters.table %}selected{% endif %}>{{ t }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="input-wrapper">
            <label for="user_no">User ID</label>
            <input id="user_no" name="user_no" value="{{ filters.user_no }}" placeholder="Filter userNo" />
          </div>

          <div class="input-wrapper">
            <label for="date_from">From Date</label>
            <input id="date_from" type="date" name="date_from" value="{{ filters.date_from }}" />
          </div>

          <div class="input-wrapper">
            <label for="date_to">To Date</label>
            <input id="date_to" type="date" name="date_to" value="{{ filters.date_to }}" />
          </div>
        </div>

        <div class="filter-grid-secondary">
          <div class="input-wrapper">
            <label for="last_active_from">Last Active From (IST)</label>
            <input id="last_active_from" type="datetime-local" name="last_active_from" value="{{ filters.last_active_from }}" />
          </div>

          <div class="input-wrapper">
            <label for="last_active_to">Last Active To (IST)</label>
            <input id="last_active_to" type="datetime-local" name="last_active_to" value="{{ filters.last_active_to }}" />
          </div>

          <div class="input-wrapper">
            <label for="limit">Row Limit</label>
            <input id="limit" type="number" min="1" max="1000" name="limit" value="{{ filters.limit }}" />
          </div>
        </div>

        <div class="filter-grid-secondary" style="border-top: 1px dashed var(--border-muted); margin-top: 4px;">
          <div class="input-wrapper">
            <label for="col_name">Column filter</label>
            <select id="col_name" name="col_name">
              <option value="">-- Choose Column --</option>
              {% for col in all_columns %}
                <option value="{{ col }}" {% if col == filters.col_name %}selected{% endif %}>{{ col }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="input-wrapper">
            <label for="col_op">Operator</label>
            <select id="col_op" name="col_op">
              <option value="=" {% if filters.col_op == "=" %}selected{% endif %}>=</option>
              <option value="LIKE" {% if filters.col_op == "LIKE" %}selected{% endif %}>Contains</option>
              <option value=">" {% if filters.col_op == ">" %}selected{% endif %}>&gt;</option>
              <option value="<" {% if filters.col_op == "<" %}selected{% endif %}>&lt;</option>
              <option value=">=" {% if filters.col_op == ">=" %}selected{% endif %}>&gt;=</option>
              <option value="<=" {% if filters.col_op == "<=" %}selected{% endif %}>&lt;=</option>
            </select>
          </div>

          <div class="input-wrapper">
            <label for="col_val">Filter Value</label>
            <input id="col_val" name="col_val" value="{{ filters.col_val }}" placeholder="e.g. Ordinary or 100" />
          </div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 12px; margin-top: 8px;">
          <button type="button" class="btn btn-secondary" onclick="window.location.href='/'">Reset</button>
          <button type="submit" class="btn btn-primary">Apply Queries</button>
        </div>
      </form>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <span class="stat-label">Rows Loaded</span>
          <span class="stat-value">{{ row_count }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🗄️</div>
        <div class="stat-content">
          <span class="stat-label">Total in Table</span>
          <span class="stat-value">{{ total_rows }}</span>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">👥</div>
        <div class="stat-content">
          <span class="stat-label">Unique Merchants</span>
          <span class="stat-value">
            {% if distinct_users > 0 %}
              {{ distinct_users }}
            {% else %}
              —
            {% endif %}
          </span>
        </div>
      </div>
    </div>

    {% if not error %}
      <div class="glass-card" style="padding: 16px;">
        <div class="card-title" style="margin-bottom: 12px; border-bottom: none; padding-bottom: 0;">📋 Query Results</div>
        
        {% if rows %}
          <div class="table-container">
            <div class="table-responsive">
              <table>
                <thead>
                  <tr>
                    {% for col in columns %}
                      <th>{{ col }}</th>
                    {% endfor %}
                  </tr>
                </thead>
                <tbody>
                  {% for row in rows %}
                    <tr>
                      {% for value in row %}
                        <td>{{ value }}</td>
                      {% endfor %}
                    </tr>
                  {% endfor %}
                </tbody>
              </table>
            </div>
          </div>
        {% else %}
          <div style="text-align: center; padding: 48px 24px; color: var(--text-muted);">
            <div style="font-size: 36px; margin-bottom: 12px;">🔍</div>
            <h4>No matching merchant records found</h4>
            <p style="font-size: 13px; margin-top: 6px;">Try adjusting your search filters or check your source table selection.</p>
          </div>
        {% endif %}
      </div>
    {% endif %}

    {% if query_executed %}
      <div class="glass-card" style="padding: 16px;">
        <div class="collapsible-debug" onclick="toggleDebugPanel()">
          <span>🛠️ SQL Inspector (Developer Tool)</span>
          <span id="debugPanelIcon">▶</span>
        </div>
        <div id="debugPanelContent" class="debug-content">
          <div class="sql-terminal-header">
            <span>Executed Query Details</span>
          </div>
          <div class="sql-terminal">
            {{ query_executed }}
          </div>
          <div style="font-size: 12px; color: var(--text-muted); margin-top: 10px;">
            <strong>Bindings:</strong> <code>{{ query_params }}</code>
          </div>
        </div>
      </div>
    {% endif %}
  </main>

  <script>
    const COLUMN_MAPPING = {
      "userNo": "Merchant ID",
      "userName": "Username",
      "nickName": "Nickname",
      "completedOrderNum": "Total Orders",
      "completedOrderNum_diff": "Orders Delta",
      "completedBuyOrderNum": "Buy Orders",
      "completedBuyOrderNum_diff": "Buy Orders Delta",
      "completedSellOrderNum": "Sell Orders",
      "completedSellOrderNum_diff": "Sell Orders Delta",
      "avgReleaseTimeOfLatest30day": "Avg Release Time (30d)",
      "avgPayTimeOfLatest30day": "Avg Pay Time (30d)",
      "completedOrderNumOfLatest30day": "Orders (30d)",
      "date": "Data Date",
      "created_at": "Collected At",
      "lastactivetime": "Last Active",
      "adcreatedtime": "Ad Created",
      "adupdatedtime": "Ad Updated",
      "badges": "Verification Status",
      "userType": "Merchant Type",
      "tradeType": "Trade Type",
      "asset": "Crypto Asset",
      "fiat": "Fiat Currency",
      "price": "Market Price",
      "surplusAmount": "Available Quantity",
      "minSingleTransAmount": "Min Trade Limit",
      "maxSingleTransAmount": "Max Trade Limit"
    };

    function getHumanLabel(col) {
      if (COLUMN_MAPPING[col]) return COLUMN_MAPPING[col];
      let label = col.replace(/_diff$/, ' Delta');
      label = label.replace(/([A-Z])/g, ' $1');
      label = label.replace(/_/g, ' ');
      label = label.trim();
      return label.charAt(0).toUpperCase() + label.slice(1);
    }

    document.addEventListener("DOMContentLoaded", () => {
      // Determine active nav tab
      const path = window.location.pathname;
      const navBtnHome = document.getElementById('nav-btn-home');
      const navBtnCompare = document.getElementById('nav-btn-compare');
      if (path === '/compare') {
        if (navBtnCompare) navBtnCompare.classList.add('active');
      } else {
        if (navBtnHome) navBtnHome.classList.add('active');
      }

      // Format table headers
      const headers = document.querySelectorAll("thead th");
      headers.forEach(th => {
        const colName = th.textContent.trim();
        const human = getHumanLabel(colName);
        th.innerHTML = `${human} <span class="empty-cell" style="font-size:10px; display:block; font-weight:normal; opacity:0.5; margin-top:2px;">${colName}</span>`;
      });

      // Format cells
      const headerNames = Array.from(document.querySelectorAll("thead th")).map(th => {
        const span = th.querySelector("span");
        return span ? span.textContent.trim() : th.textContent.trim();
      });

      const rows = document.querySelectorAll("tbody tr");
      rows.forEach(row => {
        const cells = row.querySelectorAll("td");
        cells.forEach((td, idx) => {
          const header = headerNames[idx];
          const val = td.textContent.trim();

          // Format None / Empty
          if (val === "None" || val === "" || val === "null") {
            td.innerHTML = `<span class="empty-cell">—</span>`;
            return;
          }

          // Format diff delta badges
          if (header && (header.endsWith("_diff") || header.includes("diff") || header.endsWith("Delta"))) {
            const num = parseFloat(val);
            if (!isNaN(num)) {
              if (num > 0) {
                td.innerHTML = `<span class="badge badge-success">+${num}</span>`;
              } else if (num < 0) {
                td.innerHTML = `<span class="badge badge-danger">${num}</span>`;
              } else {
                td.innerHTML = `<span class="badge badge-neutral">0</span>`;
              }
            }
            return;
          }

          // Format float rounding
          const floatVal = parseFloat(val);
          if (!isNaN(floatVal) && val.includes('.') && val.split('.')[1].length > 2) {
            if (header.toLowerCase().includes("time") || header.toLowerCase().includes("rate") || header.toLowerCase().includes("avg")) {
              td.textContent = floatVal.toFixed(2);
            }
          }
        });
      });
    });

    function toggleDebugPanel() {
      const content = document.getElementById('debugPanelContent');
      const icon = document.getElementById('debugPanelIcon');
      if (content) {
        content.classList.toggle('open');
        if (content.classList.contains('open')) {
          if (icon) icon.textContent = '▼';
        } else {
          if (icon) icon.textContent = '▶';
        }
      }
    }

    async function syncCompareDb() {
      const btn = document.getElementById('syncBtn');
      if (!btn) return;
      const btnText = btn.querySelector('.btn-text');
      const spinner = btn.querySelector('.spinner');
      
      btn.disabled = true;
      if (btnText) btnText.textContent = "Syncing...";
      if (spinner) spinner.style.display = "inline-block";
      
      try {
        const response = await fetch('/api/rebuild-compare', { method: 'POST' });
        const data = await response.json();
        if (data.success) {
          showToast('success', `Comparison database rebuilt! ${data.inserted_rows} rows updated.`);
          setTimeout(() => {
            if (window.location.pathname === '/compare') {
              window.location.reload();
            }
          }, 1200);
        } else {
          showToast('error', `Sync failed: ${data.error}`);
        }
      } catch (err) {
        showToast('error', `Network error: ${err.message}`);
      } finally {
        btn.disabled = false;
        if (btnText) btnText.textContent = "Sync Compare DB";
        if (spinner) spinner.style.display = "none";
      }
    }

    function showToast(type, message) {
      let container = document.getElementById('toast-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
      }
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.innerHTML = `
        <span>${type === 'success' ? '✅' : '❌'}</span>
        <div>${message}</div>
      `;
      container.appendChild(toast);
      
      setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
      }, 10);
      
      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => toast.remove(), 300);
      }, 4000);
    }
  </script>
</body>
</html>
"""


COMPARE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Compare Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-space: #070913;
      --bg-panel: rgba(16, 22, 40, 0.75);
      --bg-panel-solid: #0f1524;
      --border-glow: rgba(99, 102, 241, 0.15);
      --border-muted: rgba(255, 255, 255, 0.08);
      --color-primary: #6366f1;
      --color-secondary: #06b6d4;
      --color-success: #10b981;
      --color-danger: #f43f5e;
      --color-warning: #f59e0b;
      --text-main: #f1f5f9;
      --text-muted: #94a3b8;
      --text-dark: #64748b;
      --accent-gradient: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background-color: var(--bg-space);
      background-image: 
        radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
        radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.08) 0px, transparent 50%);
      background-attachment: fixed;
      color: var(--text-main);
      line-height: 1.5;
      padding-bottom: 40px;
    }

    /* Navbar / Header */
    .app-header {
      background: rgba(15, 21, 36, 0.85);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border-muted);
      padding: 14px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    }

    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
    }

    .brand-logo {
      background: var(--accent-gradient);
      width: 38px;
      height: 38px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 20px;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }

    .brand-title {
      font-size: 18px;
      font-weight: 700;
      letter-spacing: -0.5px;
      background: var(--accent-gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .nav-menu {
      display: flex;
      gap: 6px;
      background: rgba(255, 255, 255, 0.03);
      padding: 4px;
      border-radius: 10px;
      border: 1px solid var(--border-muted);
    }

    .nav-btn {
      padding: 8px 18px;
      border-radius: 8px;
      color: var(--text-muted);
      font-size: 14px;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s ease;
    }

    .nav-btn:hover {
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.05);
    }

    .nav-btn.active {
      color: #fff;
      background: var(--color-primary);
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
    }

    /* Container layout */
    .container {
      max-width: 1440px;
      margin: 24px auto;
      padding: 0 24px;
    }

    .page-title-section {
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .page-title {
      font-size: 24px;
      font-weight: 700;
      letter-spacing: -0.5px;
    }

    .page-subtitle {
      font-size: 14px;
      color: var(--text-muted);
      margin-top: 4px;
    }

    /* Card styling */
    .glass-card {
      background: var(--bg-panel);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border-muted);
      border-radius: 14px;
      padding: 24px;
      margin-bottom: 24px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    .card-title {
      font-size: 15px;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text-main);
      border-bottom: 1px solid var(--border-muted);
      padding-bottom: 12px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    /* Filter Form & Grid */
    .filters-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .filter-grid-primary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 16px;
    }

    .filter-grid-secondary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 16px;
      border-top: 1px solid var(--border-muted);
      padding-top: 16px;
      margin-top: 8px;
    }

    .input-wrapper {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    label {
      font-size: 11px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    input, select {
      background: rgba(15, 22, 40, 0.6);
      border: 1px solid var(--border-muted);
      border-radius: 8px;
      color: var(--text-main);
      padding: 10px 14px;
      font-size: 13px;
      font-family: inherit;
      width: 100%;
      outline: none;
      transition: all 0.2s ease;
    }

    input:focus, select:focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
      background: rgba(15, 22, 40, 0.85);
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 20px;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border: none;
      transition: all 0.2s ease;
      font-family: inherit;
    }

    .btn-primary {
      background: var(--accent-gradient);
      color: #fff;
      box-shadow: 0 4px 12px rgba(99, 102, 241, 0.25);
    }

    .btn-primary:hover {
      opacity: 0.95;
      transform: translateY(-1px);
      box-shadow: 0 6px 16px rgba(99, 102, 241, 0.35);
    }

    .btn-secondary {
      background: rgba(255, 255, 255, 0.05);
      color: var(--text-main);
      border: 1px solid var(--border-muted);
    }

    .btn-secondary:hover {
      background: rgba(255, 255, 255, 0.08);
      border-color: var(--text-muted);
    }

    .btn:active {
      transform: translateY(0);
    }

    .btn:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      transform: none !important;
    }

    /* Table styling */
    .table-container {
      border: 1px solid var(--border-muted);
      border-radius: 10px;
      overflow: hidden;
      background: rgba(10, 15, 30, 0.4);
      margin-top: 12px;
    }

    .table-responsive {
      max-height: 55vh;
      overflow-y: auto;
      overflow-x: auto;
    }

    table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      font-size: 13px;
      text-align: left;
    }

    th {
      background: var(--bg-panel-solid);
      color: var(--text-muted);
      font-weight: 600;
      padding: 14px 16px;
      border-bottom: 1px solid var(--border-muted);
      position: sticky;
      top: 0;
      z-index: 10;
      white-space: nowrap;
    }

    td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-muted);
      color: var(--text-main);
      white-space: nowrap;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tbody tr {
      transition: background-color 0.15s ease;
    }

    tbody tr:hover {
      background-color: rgba(255, 255, 255, 0.02);
    }

    /* Scrollbars */
    .table-responsive::-webkit-scrollbar,
    .column-panel::-webkit-scrollbar,
    .leaderboard-table-container::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }

    .table-responsive::-webkit-scrollbar-track,
    .column-panel::-webkit-scrollbar-track,
    .leaderboard-table-container::-webkit-scrollbar-track {
      background: transparent;
    }

    .table-responsive::-webkit-scrollbar-thumb,
    .column-panel::-webkit-scrollbar-thumb,
    .leaderboard-table-container::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.15);
      border-radius: 10px;
    }

    .table-responsive::-webkit-scrollbar-thumb:hover,
    .column-panel::-webkit-scrollbar-thumb:hover,
    .leaderboard-table-container::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.3);
    }

    /* Badges */
    .badge {
      display: inline-flex;
      align-items: center;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 700;
      line-height: 1;
    }

    .badge-success {
      background: rgba(16, 185, 129, 0.12);
      color: var(--color-success);
      border: 1px solid rgba(16, 185, 129, 0.2);
    }

    .badge-danger {
      background: rgba(244, 63, 94, 0.12);
      color: var(--color-danger);
      border: 1px solid rgba(244, 63, 94, 0.2);
    }

    .badge-neutral {
      background: rgba(148, 163, 184, 0.1);
      color: var(--text-muted);
      border: 1px solid rgba(148, 163, 184, 0.15);
    }

    .empty-cell {
      color: var(--text-dark);
      font-weight: 300;
    }

    /* Column Panel modal-like */
    .column-panel {
      margin-top: 16px;
      padding: 16px;
      border: 1px solid var(--border-muted);
      border-radius: 10px;
      background: rgba(15, 22, 40, 0.95);
      display: none;
      max-height: 320px;
      overflow-y: auto;
    }

    .column-panel.open {
      display: block;
      animation: slideDown 0.2s ease-out;
    }

    .checkbox-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 10px 16px;
      margin-top: 12px;
    }

    .checkbox-item {
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 13px;
      color: var(--text-main);
      cursor: pointer;
      user-select: none;
      padding: 8px;
      border-radius: 6px;
      transition: background 0.15s ease;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .checkbox-item:hover {
      background: rgba(255, 255, 255, 0.04);
    }

    .checkbox-item input[type="checkbox"] {
      width: 16px;
      height: 16px;
      accent-color: var(--color-primary);
      cursor: pointer;
      flex-shrink: 0;
    }

    /* Split layout */
    .dashboard-layout {
      display: grid;
      grid-template-columns: 1fr;
      gap: 24px;
    }

    @media (min-width: 1100px) {
      .dashboard-layout {
        grid-template-columns: minmax(0, 1fr) 420px;
        align-items: start;
      }
    }

    .left-column {
      display: flex;
      flex-direction: column;
      gap: 24px;
    }

    .right-column {
      position: sticky;
      top: 80px;
    }

    .leaderboard-table-container {
      overflow-x: hidden !important;
    }

    .leaderboard-table-container th,
    .leaderboard-table-container td {
      padding: 10px 8px !important;
      font-size: 12px;
    }

    .leaderboard-table-container table {
      width: 100%;
      table-layout: fixed;
    }

    .leaderboard-table-container th:nth-child(1),
    .leaderboard-table-container td:nth-child(1) {
      width: 45px;
      text-align: center;
    }

    .leaderboard-table-container th:nth-child(2),
    .leaderboard-table-container td:nth-child(2) {
      width: auto;
    }

    .leaderboard-table-container th:nth-child(3),
    .leaderboard-table-container td:nth-child(3) {
      width: 90px;
      text-align: right;
    }

    .leaderboard-table-container th:nth-child(4),
    .leaderboard-table-container td:nth-child(4) {
      width: 95px;
      text-align: right;
    }

    .rank-cell {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      font-weight: 700;
      font-size: 11px;
    }

    .rank-1 { background: linear-gradient(135deg, #fbbf24 0%, #d97706 100%); color: #fff; box-shadow: 0 2px 8px rgba(251, 191, 36, 0.4); }
    .rank-2 { background: linear-gradient(135deg, #cbd5e1 0%, #64748b 100%); color: #fff; box-shadow: 0 2px 8px rgba(203, 213, 225, 0.4); }
    .rank-3 { background: linear-gradient(135deg, #b45309 0%, #78350f 100%); color: #fff; box-shadow: 0 2px 8px rgba(180, 83, 9, 0.4); }
    .rank-other { background: rgba(255, 255, 255, 0.05); color: var(--text-muted); border: 1px solid var(--border-muted); }

    /* Stats Grid */
    .stats-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
    }

    .stat-card {
      background: var(--bg-panel);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border-muted);
      border-radius: 14px;
      padding: 20px;
      display: flex;
      align-items: center;
      gap: 16px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
      position: relative;
      overflow: hidden;
    }

    .stat-card::after {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: var(--accent-gradient);
    }

    .stat-icon {
      font-size: 22px;
      width: 46px;
      height: 46px;
      background: rgba(99, 102, 241, 0.1);
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--color-primary);
    }

    .stat-content {
      display: flex;
      flex-direction: column;
    }

    .stat-label {
      font-size: 11px;
      color: var(--text-muted);
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .stat-value {
      font-size: 22px;
      font-weight: 700;
      color: #fff;
      margin-top: 2px;
    }

    /* Make right section longer */
    .leaderboard-table-container {
      max-height: 80vh;
      overflow-y: auto;
    }

    /* Error alert */
    .error-card {
      background: rgba(244, 63, 94, 0.1);
      border: 1px solid rgba(244, 63, 94, 0.25);
      border-radius: 10px;
      padding: 16px;
      color: var(--color-danger);
      font-weight: 600;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      gap: 12px;
    }

    /* Toast styles */
    #toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .toast {
      background: #131b2e;
      border-radius: 8px;
      border: 1px solid var(--border-muted);
      box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
      padding: 12px 18px;
      font-size: 13px;
      font-weight: 500;
      min-width: 280px;
      display: flex;
      align-items: center;
      gap: 10px;
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      opacity: 0;
      transform: translateY(20px);
    }
    .toast-success {
      border-left: 4px solid var(--color-success);
    }
    .toast-error {
      border-left: 4px solid var(--color-danger);
    }
  </style>
</head>
<body>
  <header class="app-header">
    <a href="/" class="brand">
      <div class="brand-logo">📈</div>
      <span class="brand-title">Merchant Analytics Hub</span>
    </a>
    <div style="display: flex; align-items: center; gap: 16px;">
      <button type="button" class="btn btn-secondary" id="syncBtn" onclick="syncCompareDb()">
        <span class="btn-text">Sync Compare DB</span>
        <span class="spinner" style="display:none; margin-left: 5px;">⏳</span>
      </button>
      <nav class="nav-menu">
        <a href="/" class="nav-btn" id="nav-btn-home">Merchants</a>
        <a href="/compare" class="nav-btn" id="nav-btn-compare">Comparison</a>
      </nav>
    </div>
  </header>

  <main class="container">
    <div class="page-title-section">
      <div>
        <h2 class="page-title">Comparison Analytics</h2>
        <div class="page-subtitle">Inspect differences between snapshot runs and track merchant order velocity.</div>
      </div>
    </div>

    {% if error %}
      <div class="error-card">
        <span>⚠️</span>
        <div><strong>Comparison Error:</strong> {{ error }}</div>
      </div>
    {% endif %}

    {% if not error %}
      <div class="dashboard-layout">
        <!-- LEFT COLUMN: TOP LEFT & BOTTOM LEFT -->
        <div class="left-column">
          <!-- TOP LEFT: ACTIVE / TOTAL USERS & SELL VOLUME -->
          <div class="stats-row">
            <div class="stat-card">
              <div class="stat-icon">👥</div>
              <div class="stat-content">
                <span class="stat-label">Active / Total Users</span>
                <span class="stat-value">{{ active_users }} / {{ total_users }}</span>
                <span style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                  Active = ≥1 trade in last 24h
                </span>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">📈</div>
              <div class="stat-content">
                <span class="stat-label">Sell Volume (Daily)</span>
                <span class="stat-value" style="color: var(--color-success);">{{ "%.4f"|format(sell_volume_daily_cr) }} Cr</span>
                <span style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                  Value on {{ target_date }} (x1250)
                </span>
              </div>
            </div>

            <div class="stat-card">
              <div class="stat-icon">🗄️</div>
              <div class="stat-content">
                <span class="stat-label">Sell Volume (Cumulative)</span>
                <span class="stat-value" style="color: var(--color-primary);">{{ "%.2f"|format(sell_volume_cum_cr) }} Cr</span>
                <span style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
                  Cumulative value (x1250)
                </span>
              </div>
            </div>
          </div>

          <!-- BOTTOM LEFT: FILTERS -->
          <div class="glass-card" style="margin-bottom: 0;">
            <div class="card-title">🔍 Comparison Filters</div>
            <form method="get" class="filters-form">
              <div class="filter-grid-primary">
                <div class="input-wrapper">
                  <label for="user_no">User ID</label>
                  <input id="user_no" name="user_no" value="{{ filters.user_no }}" placeholder="Filter userNo" />
                </div>

                <div class="input-wrapper">
                  <label for="limit">Preview Limit</label>
                  <input id="limit" type="number" min="1" max="1000" name="limit" value="{{ filters.limit }}" />
                </div>

                <div class="input-wrapper">
                  <label for="leaderboard_limit">Leaderboard Limit</label>
                  <input id="leaderboard_limit" type="number" min="1" max="100" name="leaderboard_limit" value="{{ filters.leaderboard_limit }}" />
                </div>
              </div>

              <div class="filter-grid-secondary">
                <div class="input-wrapper">
                  <label for="col_name">Column filter</label>
                  <select id="col_name" name="col_name">
                    <option value="">-- Choose Column --</option>
                    {% for col in all_columns %}
                      <option value="{{ col }}" {% if col == filters.col_name %}selected{% endif %}>{{ col }}</option>
                    {% endfor %}
                  </select>
                </div>

                <div class="input-wrapper">
                  <label for="col_op">Operator</label>
                  <select id="col_op" name="col_op">
                    <option value="=" {% if filters.col_op == "=" %}selected{% endif %}>=</option>
                    <option value="LIKE" {% if filters.col_op == "LIKE" %}selected{% endif %}>Contains</option>
                    <option value=">" {% if filters.col_op == ">" %}selected{% endif %}>&gt;</option>
                    <option value="<" {% if filters.col_op == "<" %}selected{% endif %}>&lt;</option>
                    <option value=">=" {% if filters.col_op == ">=" %}selected{% endif %}>&gt;=</option>
                    <option value="<=" {% if filters.col_op == "<=" %}selected{% endif %}>&lt;=</option>
                  </select>
                </div>

                <div class="input-wrapper">
                  <label for="col_val">Filter Value</label>
                  <input id="col_val" name="col_val" value="{{ filters.col_val }}" placeholder="e.g. 10 or Active" />
                </div>
              </div>

              <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 12px; border-top: 1px dashed var(--border-muted); padding-top: 16px;">
                <button type="button" class="btn btn-secondary" onclick="toggleColumnPanel()">Configure Table Columns</button>
                <div style="display: flex; gap: 12px;">
                  <button type="button" class="btn btn-secondary" onclick="window.location.href='/compare'">Reset</button>
                  <button type="submit" class="btn btn-primary">Apply Queries</button>
                </div>
              </div>

              <div id="columnPanel" class="column-panel {% if column_panel_open %}open{% endif %}">
                <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border-muted); padding-bottom: 10px; margin-bottom: 10px;">
                  <div>
                    <strong style="font-size: 13px;">Visible Output Columns</strong>
                    <div style="font-size:11px; color: var(--text-muted); margin-top: 2px;">Deselected fields will be hidden in the Comparison preview table below.</div>
                  </div>
                  <button type="submit" class="btn btn-primary" style="padding: 6px 14px; font-size: 12px;">Apply Selected Columns</button>
                </div>
                <div class="checkbox-grid">
                  {% for col in all_columns %}
                    <label class="checkbox-item" title="{{ col }}">
                      <input type="checkbox" name="visible_columns" value="{{ col }}" {% if col in selected_columns %}checked{% endif %} />
                      <span>{{ col }}</span>
                    </label>
                  {% endfor %}
                </div>
              </div>
            </form>
          </div>

          <!-- BOTTOM LEFT NEXT LINE: COMPARISON PREVIEW -->
          <div class="glass-card" style="padding: 16px; margin-bottom: 0;">
            <div class="card-title" style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
              <span>📋 Comparison Preview</span>
              <span style="font-size:12px; color: var(--text-muted); font-weight: normal; text-transform: none;">Rows shown: {{ row_count }}</span>
            </div>
            
            {% if rows %}
              <div class="table-container" style="margin-top: 0;">
                <div class="table-responsive">
                  <table>
                    <thead>
                      <tr>
                        {% for col in columns %}
                          <th>{{ col }}</th>
                        {% endfor %}
                      </tr>
                    </thead>
                    <tbody>
                      {% for row in rows %}
                        <tr>
                          {% for value in row %}
                            <td>{{ value|safe }}</td>
                          {% endfor %}
                        </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </div>
              </div>
            {% else %}
              <div style="text-align: center; padding: 48px 24px; color: var(--text-muted);">
                <div style="font-size: 36px; margin-bottom: 12px;">🔍</div>
                <h4>No comparison matches found</h4>
                <p style="font-size: 13px; margin-top: 6px;">Try adjusting filters or sync/rebuild database if it's currently empty.</p>
              </div>
            {% endif %}
          </div>
        </div>

        <!-- RIGHT COLUMN: LEADERBOARD -->
        <div class="right-column">
          <div class="glass-card" style="padding: 16px; margin-bottom: 0;">
            <div class="card-title" style="margin-bottom: 12px;">🏆 Leaderboard</div>
            <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 16px;">
              Rankings based on order velocity (diff) for target date <strong>{{ target_date }}</strong>.
            </div>
            {% if leaderboard_rows %}
              <div class="table-container" style="margin-top: 0;">
                <div class="table-responsive leaderboard-table-container">
                  <table>
                    <thead>
                      <tr>
                        <th style="width: 50px; text-align: center;">Rank</th>
                        <th>Username</th>
                        <th style="text-align: right;">Delta Orders</th>
                        <th style="text-align: right;">Rank Change</th>
                      </tr>
                    </thead>
                    <tbody>
                      {% for row in leaderboard_rows %}
                        <tr>
                          <td style="text-align: center;">
                            <div class="rank-cell {% if row.rank == 1 %}rank-1{% elif row.rank == 2 %}rank-2{% elif row.rank == 3 %}rank-3{% else %}rank-other{% endif %}">
                              {{ row.rank }}
                            </div>
                          </td>
                          <td>
                            <div style="font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{{ row.username }}">{{ row.username }}</div>
                            <div style="font-size: 10px; color: var(--text-muted); margin-top: 2px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="ID: {{ row.userNo }}">ID: {{ row.userNo }}</div>
                          </td>
                          <td style="text-align: right; font-weight: 700;">
                            {% if row.deltaOrders > 0 %}
                              <span class="badge badge-success">+{{ row.deltaOrders|round(0)|int }}</span>
                            {% elif row.deltaOrders < 0 %}
                              <span class="badge badge-danger">{{ row.deltaOrders|round(0)|int }}</span>
                            {% else %}
                              <span class="badge badge-neutral">0</span>
                            {% endif %}
                          </td>
                          <td style="text-align: right;">
                            {% if row.rank_change_pct is not none %}
                              {% if row.rank_change_pct > 0 %}
                                <span class="badge badge-success" style="font-size: 11px;">▲ {{ row.rank_change_pct|round(1) }}%</span>
                              {% elif row.rank_change_pct < 0 %}
                                <span class="badge badge-danger" style="font-size: 11px;">▼ {{ row.rank_change_pct|abs|round(1) }}%</span>
                              {% else %}
                                <span class="badge badge-neutral" style="font-size: 11px;">0.0%</span>
                              {% endif %}
                            {% else %}
                              <span class="badge badge-neutral" style="font-size: 11px; background: rgba(99, 102, 241, 0.1); color: var(--color-primary); border-color: rgba(99, 102, 241, 0.2);">New</span>
                            {% endif %}
                          </td>
                        </tr>
                      {% endfor %}
                    </tbody>
                  </table>
                </div>
              </div>
            {% else %}
              <div style="text-align: center; padding: 24px; color: var(--text-muted);">
                No leaderboard data available.
              </div>
            {% endif %}
          </div>
        </div>
      </div>
    {% endif %}
  </main>

  <script>
    const COLUMN_MAPPING = {
      "userNo": "Merchant ID",
      "userName": "Username",
      "nickName": "Username(nickname)",
      "completedOrderNum": "tot orders",
      "completedOrderNum_diff": "delta orders",
      "completedBuyOrderNum": "buy",
      "completedBuyOrderNum_diff": "Buy Orders Delta",
      "completedSellOrderNum": "sell",
      "completedSellOrderNum_diff": "Sell Orders Delta",
      "avgReleaseTimeOfLatest30day": "avg release time",
      "avgPayTimeOfLatest30day": "avg paytime",
      "completedOrderNumOfLatest30day": "Orders (30d)",
      "date": "date",
      "created_at": "Collected At",
      "lastactivetime": "Last Active",
      "adcreatedtime": "Ad Created",
      "adupdatedtime": "Ad Updated",
      "badges": "Verification Status",
      "userType": "Merchant Type",
      "tradeType": "Trade Type",
      "asset": "Crypto Asset",
      "fiat": "Fiat Currency",
      "price": "Market Price",
      "surplusAmount": "Available Quantity",
      "minSingleTransAmount": "Min Trade Limit",
      "maxSingleTransAmount": "Max Trade Limit",
      "registerDays": "reg days",
      "rank": "rank",
      "finishRateLatest30day": "finishrate"
    };

    function getHumanLabel(col) {
      if (COLUMN_MAPPING[col]) return COLUMN_MAPPING[col];
      let label = col.replace(/_diff$/, ' Delta');
      label = label.replace(/([A-Z])/g, ' $1');
      label = label.replace(/_/g, ' ');
      label = label.trim();
      return label.charAt(0).toUpperCase() + label.slice(1);
    }

    document.addEventListener("DOMContentLoaded", () => {
      // Determine active nav tab
      const path = window.location.pathname;
      const navBtnHome = document.getElementById('nav-btn-home');
      const navBtnCompare = document.getElementById('nav-btn-compare');
      if (path === '/compare') {
        if (navBtnCompare) navBtnCompare.classList.add('active');
      } else {
        if (navBtnHome) navBtnHome.classList.add('active');
      }

      // Format table headers
      const headers = document.querySelectorAll("thead th");
      headers.forEach(th => {
        const colName = th.textContent.trim();
        if (colName === "Rank" || colName === "Merchant" || colName === "Diff" || colName === "Username" || colName === "Delta Orders" || colName === "Rank Change") return;
        const human = getHumanLabel(colName);
        th.innerHTML = `${human} <span class="empty-cell" style="font-size:10px; display:block; font-weight:normal; opacity:0.5; margin-top:2px;">${colName}</span>`;
      });

      // Format checkboxes in Config Columns
      const checkLabels = document.querySelectorAll(".checkbox-item span");
      checkLabels.forEach(span => {
        const colName = span.textContent.trim();
        const human = getHumanLabel(colName);
        span.innerHTML = `<strong>${human}</strong> <span style="font-size:11px; opacity:0.5; margin-left:4px;">(${colName})</span>`;
      });

      // Format cells
      const headerNames = Array.from(document.querySelectorAll("thead th")).map(th => {
        const span = th.querySelector("span");
        return span ? span.textContent.trim() : th.textContent.trim();
      });

      const rows = document.querySelectorAll("tbody tr");
      rows.forEach(row => {
        const cells = row.querySelectorAll("td");
        cells.forEach((td, idx) => {
          const header = headerNames[idx];
          if (header === "Rank" || header === "Merchant" || header === "Diff" || header === "Username" || header === "Delta Orders" || header === "Rank Change" || header === "buy" || header === "sell" || header === "tot orders") return;
          const val = td.textContent.trim();

          // Format None / Empty
          if (val === "None" || val === "" || val === "null") {
            td.innerHTML = `<span class="empty-cell">—</span>`;
            return;
          }

          // Format diff delta badges
          if (header && (header.endsWith("_diff") || header.includes("diff") || header.endsWith("Delta"))) {
            const num = parseFloat(val);
            if (!isNaN(num)) {
              if (num > 0) {
                td.innerHTML = `<span class="badge badge-success">+${num}</span>`;
              } else if (num < 0) {
                td.innerHTML = `<span class="badge badge-danger">${num}</span>`;
              } else {
                td.innerHTML = `<span class="badge badge-neutral">0</span>`;
              }
            }
            return;
          }

          // Format float rounding
          const floatVal = parseFloat(val);
          if (!isNaN(floatVal) && val.includes('.') && val.split('.')[1].length > 2) {
            if (header.toLowerCase().includes("time") || header.toLowerCase().includes("rate") || header.toLowerCase().includes("avg")) {
              td.textContent = floatVal.toFixed(2);
            }
          }
        });
      });
    });

    function toggleColumnPanel() {
      const panel = document.getElementById('columnPanel');
      if (panel) {
        panel.classList.toggle('open');
      }
    }

    async function syncCompareDb() {
      const btn = document.getElementById('syncBtn');
      if (!btn) return;
      const btnText = btn.querySelector('.btn-text');
      const spinner = btn.querySelector('.spinner');
      
      btn.disabled = true;
      if (btnText) btnText.textContent = "Syncing...";
      if (spinner) spinner.style.display = "inline-block";
      
      try {
        const response = await fetch('/api/rebuild-compare', { method: 'POST' });
        const data = await response.json();
        if (data.success) {
          showToast('success', `Comparison database rebuilt! ${data.inserted_rows} rows updated.`);
          setTimeout(() => {
            if (window.location.pathname === '/compare') {
              window.location.reload();
            }
          }, 1200);
        } else {
          showToast('error', `Sync failed: ${data.error}`);
        }
      } catch (err) {
        showToast('error', `Network error: ${err.message}`);
      } finally {
        btn.disabled = false;
        if (btnText) btnText.textContent = "Sync Compare DB";
        if (spinner) spinner.style.display = "none";
      }
    }

    function showToast(type, message) {
      let container = document.getElementById('toast-container');
      if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
      }
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      toast.innerHTML = `
        <span>${type === 'success' ? '✅' : '❌'}</span>
        <div>${message}</div>
      `;
      container.appendChild(toast);
      
      setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateY(0)';
      }, 10);
      
      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(-20px)';
        setTimeout(() => toast.remove(), 300);
      }, 4000);
    }
  </script>
</body>
</html>
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [r[1] for r in rows]


def sanitize_filters(args: Dict[str, str]) -> Dict[str, str]:
    table_name = args.get("table", "user_info")
    if table_name not in ALLOWED_TABLES:
        table_name = "user_info"

    limit_str = args.get("limit", "100").strip()
    try:
        limit = str(max(1, min(int(limit_str), 1000)))
    except ValueError:
        limit = "100"

    col_op = args.get("col_op", "=").strip()
    if col_op not in ["=", "LIKE", ">", "<", ">=", "<="]:
        col_op = "="

    return {
        "table": table_name,
        "user_no": args.get("user_no", "").strip(),
        "date_from": args.get("date_from", "").strip(),
        "date_to": args.get("date_to", "").strip(),
        "last_active_from": args.get("last_active_from", "").strip(),
        "last_active_to": args.get("last_active_to", "").strip(),
        "limit": limit,
        "col_name": args.get("col_name", "").strip(),
        "col_op": col_op,
        "col_val": args.get("col_val", "").strip(),
    }


def sanitize_compare_filters(args: Dict[str, str]) -> Dict[str, str]:
    limit_str = args.get("limit", "100").strip()
    leaderboard_limit_str = args.get("leaderboard_limit", "30").strip()

    try:
        limit = str(max(1, min(int(limit_str), 1000)))
    except ValueError:
        limit = "100"

    try:
        leaderboard_limit = str(max(1, min(int(leaderboard_limit_str), 100)))
    except ValueError:
        leaderboard_limit = "30"

    col_op = args.get("col_op", "=").strip()
    if col_op not in ["=", "LIKE", ">", "<", ">=", "<="]:
        col_op = "="

    return {
        "user_no": args.get("user_no", "").strip(),
        "date_from": args.get("date_from", "").strip(),
        "date_to": args.get("date_to", "").strip(),
        "limit": limit,
        "leaderboard_limit": leaderboard_limit,
        "col_name": args.get("col_name", "").strip(),
        "col_op": col_op,
        "col_val": args.get("col_val", "").strip(),
    }


def select_visible_columns(all_columns: List[str], requested_columns: List[str]) -> List[str]:
    requested_set = {column for column in requested_columns if column in all_columns}
    if not requested_set:
        return list(all_columns)

    return [column for column in all_columns if column in requested_set]


def parse_ist_datetime_to_epoch_ms(value: str, end_of_range: bool = False) -> Optional[int]:
    if not value:
        return None

    parsed_dt = None
    matched_format = ""
    for dt_format in ("%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            parsed_dt = datetime.strptime(value, dt_format)
            matched_format = dt_format
            break
        except ValueError:
            continue

    if parsed_dt is None:
        return None

    if matched_format == "%Y-%m-%d":
        if end_of_range:
            parsed_dt = parsed_dt.replace(hour=23, minute=59, second=59, microsecond=999000)
        else:
            parsed_dt = parsed_dt.replace(hour=0, minute=0, second=0, microsecond=0)

    parsed_dt = parsed_dt.replace(tzinfo=IST_TZ)
    return int(parsed_dt.timestamp() * 1000)


def build_query(table_name: str, columns: List[str], filters: Dict[str, str]) -> Tuple[str, List[object]]:
    where_clauses = []
    params: List[object] = []

    if "userNo" in columns and filters["user_no"]:
        where_clauses.append("userNo LIKE ?")
        params.append(f"%{filters['user_no']}%")

    if "date" in columns and filters["date_from"]:
        where_clauses.append("date(date) >= date(?)")
        params.append(filters["date_from"])

    if "date" in columns and filters["date_to"]:
        where_clauses.append("date(date) <= date(?)")
        params.append(filters["date_to"])

    last_active_column = next((col for col in columns if col.lower() == "lastactivetime"), None)
    if last_active_column and filters["last_active_from"]:
        from_ms = parse_ist_datetime_to_epoch_ms(filters["last_active_from"], end_of_range=False)
        if from_ms is not None:
            where_clauses.append(f"CAST({last_active_column} AS INTEGER) >= ?")
            params.append(from_ms)

    if last_active_column and filters["last_active_to"]:
        to_ms = parse_ist_datetime_to_epoch_ms(filters["last_active_to"], end_of_range=True)
        if to_ms is not None:
            where_clauses.append(f"CAST({last_active_column} AS INTEGER) <= ?")
            params.append(to_ms)

    # Column-level filter
    if filters["col_name"] and filters["col_val"]:
        col_name = filters["col_name"]
        if col_name in columns:
            operator = filters["col_op"]
            col_val = filters["col_val"]
            
            # For non-numeric operators, always use LIKE to handle JSON and text
            if operator in ["=", "LIKE"]:
                where_clauses.append(f"{col_name} LIKE ?")
                params.append(f"%{col_val}%")
            else:
                # For numeric comparisons, cast to REAL
                where_clauses.append(f"CAST({col_name} AS REAL) {operator} ?")
                try:
                    params.append(float(col_val))
                except ValueError:
                    # If value is not numeric, skip this filter
                    pass

    sql = f"SELECT * FROM {table_name}"
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    if "date" in columns:
        sql += " ORDER BY date DESC"
    elif "created_at" in columns:
        sql += " ORDER BY created_at DESC"
    else:
        sql += " ORDER BY rowid DESC"

    sql += " LIMIT ?"
    params.append(filters["limit"])
    return sql, params


def build_compare_query(columns: List[str], filters: Dict[str, str]) -> Tuple[str, List[object]]:
    table_name = "compare"
    where_clauses = []
    params: List[object] = []

    if "userNo" in columns and filters["user_no"]:
        where_clauses.append("userNo LIKE ?")
        params.append(f"%{filters['user_no']}%")

    if "date" in columns and filters["date_from"]:
        where_clauses.append("date(date) >= date(?)")
        params.append(filters["date_from"])

    if "date" in columns and filters["date_to"]:
        where_clauses.append("date(date) <= date(?)")
        params.append(filters["date_to"])

    if filters["col_name"] and filters["col_val"]:
        col_name = filters["col_name"]
        if col_name in columns:
            operator = filters["col_op"]
            col_val = filters["col_val"]

            if operator in ["=", "LIKE"]:
                where_clauses.append(f"{col_name} LIKE ?")
                params.append(f"%{col_val}%")
            else:
                try:
                    numeric_val = float(col_val)
                except ValueError:
                    numeric_val = None

                if numeric_val is not None:
                    where_clauses.append(f"CAST({col_name} AS REAL) {operator} ?")
                    params.append(numeric_val)

    inner_sql = "SELECT *, ROW_NUMBER() OVER (PARTITION BY date ORDER BY COALESCE(completedOrderNum_diff, 0) DESC, userNo ASC) AS rank FROM compare"
    sql = f"SELECT * FROM ({inner_sql})"
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    if "date" in columns:
        sql += " ORDER BY date DESC, rank ASC"
    else:
        sql += " ORDER BY rowid DESC"

    sql += " LIMIT ?"
    params.append(filters["limit"])
    return sql, params


def fetch_compare_leaderboard(
  conn: sqlite3.Connection,
  columns: List[str],
  leaderboard_limit: int,
) -> List[Tuple]:
  if "userNo" not in columns:
    return []

  if "completedOrderNum_diff" not in columns:
    return []

  nickname_select = "MAX(COALESCE(c.nickName, '')) AS nickname" if "nickName" in columns else "'' AS nickname"

  query = f"""
    WITH latest_day AS (
      SELECT MAX(date(date)) AS day
      FROM compare
      WHERE date IS NOT NULL
    )
    SELECT
      c.userNo,
      {nickname_select},
      ROUND(SUM(COALESCE(CAST(c.completedOrderNum_diff AS REAL), 0)), 2) AS total_completedordernum_diff
    FROM compare c
    JOIN latest_day ld ON date(c.date) = ld.day
    WHERE c.userNo IS NOT NULL
      AND TRIM(c.userNo) <> ''
    GROUP BY c.userNo
    ORDER BY total_completedordernum_diff DESC
    LIMIT ?
  """
  return conn.execute(query, (leaderboard_limit,)).fetchall()


def format_epoch_ms_time_columns(columns: List[str], rows: List[Tuple]) -> List[Tuple]:
    # Fields stored as epoch milliseconds that should be displayed in IST.
    epoch_ms_fields = {"lastactivetime", "adcreatedtime", "adupdatedtime"}
    index_to_col = {
        idx: col_name
        for idx, col_name in enumerate(columns)
        if col_name.lower() in epoch_ms_fields
    }

    if not index_to_col:
        return rows

    formatted_rows: List[Tuple] = []
    for row in rows:
        row_values = list(row)

        for idx in index_to_col:
            raw_value = row_values[idx]
            if raw_value is None or str(raw_value).strip() == "":
                continue

            try:
                epoch_ms = int(float(raw_value))
                dt_ist = datetime.fromtimestamp(epoch_ms / 1000, tz=IST_TZ)
                row_values[idx] = dt_ist.strftime("%Y-%m-%d %H:%M:%S IST")
            except (ValueError, OSError, OverflowError):
                continue

        formatted_rows.append(tuple(row_values))

    return formatted_rows


def format_compare_deltas(columns: List[str], rows: List[Tuple]) -> List[Tuple]:
    try:
        buy_idx = columns.index("completedBuyOrderNum")
        buy_diff_idx = columns.index("completedBuyOrderNum_diff")
    except ValueError:
        buy_idx = buy_diff_idx = None

    try:
        sell_idx = columns.index("completedSellOrderNum")
        sell_diff_idx = columns.index("completedSellOrderNum_diff")
    except ValueError:
        sell_idx = sell_diff_idx = None

    try:
        tot_idx = columns.index("completedOrderNum")
        tot_diff_idx = columns.index("completedOrderNum_diff")
    except ValueError:
        tot_idx = tot_diff_idx = None

    if buy_idx is None and sell_idx is None and tot_idx is None:
        return rows

    formatted_rows: List[Tuple] = []
    for row in rows:
        row_list = list(row)
        
        # Format Buy
        if buy_idx is not None and buy_diff_idx is not None:
            buy_val = row_list[buy_idx]
            buy_diff = row_list[buy_diff_idx]
            if buy_val is not None:
                if buy_diff is not None:
                    try:
                        diff_val = int(buy_diff)
                        if diff_val > 0:
                            row_list[buy_idx] = f"{buy_val} <span style='color: var(--color-success); font-weight: 600;'>(+{diff_val})</span>"
                        elif diff_val < 0:
                            row_list[buy_idx] = f"{buy_val} <span style='color: var(--color-danger); font-weight: 600;'>({diff_val})</span>"
                        else:
                            row_list[buy_idx] = f"{buy_val} <span style='color: var(--text-muted); font-weight: 600;'>(0)</span>"
                    except ValueError:
                        pass

        # Format Sell
        if sell_idx is not None and sell_diff_idx is not None:
            sell_val = row_list[sell_idx]
            sell_diff = row_list[sell_diff_idx]
            if sell_val is not None:
                if sell_diff is not None:
                    try:
                        diff_val = int(sell_diff)
                        if diff_val > 0:
                            row_list[sell_idx] = f"{sell_val} <span style='color: var(--color-success); font-weight: 600;'>(+{diff_val})</span>"
                        elif diff_val < 0:
                            row_list[sell_idx] = f"{sell_val} <span style='color: var(--color-danger); font-weight: 600;'>({diff_val})</span>"
                        else:
                            row_list[sell_idx] = f"{sell_val} <span style='color: var(--text-muted); font-weight: 600;'>(0)</span>"
                    except ValueError:
                        pass

        # Format Tot Orders
        if tot_idx is not None and tot_diff_idx is not None:
            tot_val = row_list[tot_idx]
            tot_diff = row_list[tot_diff_idx]
            if tot_val is not None:
                if tot_diff is not None:
                    try:
                        diff_val = int(tot_diff)
                        if diff_val > 0:
                            row_list[tot_idx] = f"{tot_val} <span style='color: var(--color-success); font-weight: 600;'>(+{diff_val})</span>"
                        elif diff_val < 0:
                            row_list[tot_idx] = f"{tot_val} <span style='color: var(--color-danger); font-weight: 600;'>({diff_val})</span>"
                        else:
                            row_list[tot_idx] = f"{tot_val} <span style='color: var(--text-muted); font-weight: 600;'>(0)</span>"
                    except ValueError:
                        pass
                        
        formatted_rows.append(tuple(row_list))
    return formatted_rows


def project_rows(columns: List[str], rows: List[Tuple], visible_columns: List[str]) -> List[Tuple]:
    if visible_columns == columns:
        return rows

    column_indexes = [columns.index(column) for column in visible_columns if column in columns]
    if not column_indexes:
        return rows

    return [tuple(row[index] for index in column_indexes) for row in rows]


@app.route("/")
def dashboard():
    filters = sanitize_filters(request.args)

    if not DB_PATH.exists():
        return f"Database not found: {DB_PATH}", 404

    error = ""
    columns: List[str] = []
    all_columns: List[str] = []
    rows: List[Tuple] = []
    row_count = 0
    total_rows = 0
    distinct_users = 0
    query_executed = ""
    query_params = []

    try:
        with get_connection() as conn:
            columns = get_table_columns(conn, filters["table"])
            all_columns = columns
            if not columns:
                raise ValueError(f"Table '{filters['table']}' not found")

            query, params = build_query(filters["table"], columns, filters)
            query_executed = query
            query_params = params[:-1]  # Exclude LIMIT param for clarity
            
            result = conn.execute(query, params).fetchall()
            rows = [tuple(r) for r in result]
            rows = format_epoch_ms_time_columns(columns, rows)
            row_count = len(rows)

            total_rows = conn.execute(f"SELECT COUNT(*) FROM {filters['table']}").fetchone()[0]
            if "userNo" in columns:
                distinct_users = conn.execute(
                    f"SELECT COUNT(DISTINCT userNo) FROM {filters['table']}"
                ).fetchone()[0]

    except Exception as exc:
        error = str(exc)

    return render_template_string(
        TEMPLATE,
        allowed_tables=ALLOWED_TABLES,
        filters=filters,
        columns=columns,
        all_columns=all_columns,
        rows=rows,
        row_count=row_count,
        total_rows=total_rows,
        distinct_users=distinct_users,
        error=error,
        query_executed=query_executed,
        query_params=query_params,
    )


@app.route("/compare")
def compare_dashboard():
    filters = sanitize_compare_filters(request.args)

    if not COMPARE_DB_PATH.exists():
        return f"Database not found: {COMPARE_DB_PATH}", 404

    error = ""
    columns: List[str] = []
    all_columns: List[str] = []
    selected_columns: List[str] = []
    rows: List[Tuple] = []
    row_count = 0
    leaderboard_rows: List[Dict] = []
    
    total_users = 0
    active_users = 0
    sell_volume_cum_cr = 0.0
    sell_volume_daily_cr = 0.0
    target_date = ""

    try:
        with sqlite3.connect(COMPARE_DB_PATH) as conn:
            columns = get_table_columns(conn, "compare")
            if not columns:
                raise ValueError("Table 'compare' not found in compare.db")

            columns.append("rank")

            DEFAULT_COMPARE_COLUMNS = [
                "nickName",
                "date",
                "completedBuyOrderNum",
                "completedSellOrderNum",
                "completedOrderNum",
                "rank",
                "registerDays",
                "avgPayTimeOfLatest30day",
                "avgReleaseTimeOfLatest30day",
                "finishRateLatest30day"
            ]

            ordered_all = [col for col in DEFAULT_COMPARE_COLUMNS if col in columns]
            remaining_cols = [col for col in columns if col not in ordered_all]
            all_columns = ordered_all + remaining_cols

            requested_visible = request.args.getlist("visible_columns")
            if not requested_visible:
                selected_columns = list(ordered_all)
            else:
                selected_columns = [col for col in requested_visible if col in columns]

            # Determine target_date
            date_to_val = filters.get("date_to")
            if date_to_val:
                cur = conn.execute("SELECT MAX(date) FROM compare WHERE date <= ?", (date_to_val,))
            else:
                cur = conn.execute("SELECT MAX(date) FROM compare")
            target_date_row = cur.fetchone()
            target_date = target_date_row[0] if target_date_row and target_date_row[0] else None

            if not target_date:
                cur = conn.execute("SELECT MAX(date) FROM compare")
                target_date_row = cur.fetchone()
                target_date = target_date_row[0] if target_date_row and target_date_row[0] else None

            # Get the date prior to target_date
            prev_date = None
            if target_date:
                cur = conn.execute("SELECT DISTINCT date FROM compare WHERE date < ? ORDER BY date DESC LIMIT 1", (target_date,))
                prev_date_row = cur.fetchone()
                prev_date = prev_date_row[0] if prev_date_row and prev_date_row[0] else None

            # Query stats for target_date
            if target_date:
                # Total users
                total_users = conn.execute("SELECT COUNT(1) FROM compare WHERE date = ?", (target_date,)).fetchone()[0]
                # Active users (done at least one trade in last 24hrs)
                active_users = conn.execute("SELECT COUNT(1) FROM compare WHERE date = ? AND completedOrderNum_diff >= 1", (target_date,)).fetchone()[0]
                # Cumulative sell orders sum
                sum_sell_orders = conn.execute("SELECT SUM(COALESCE(completedSellOrderNum, 0)) FROM compare WHERE date = ?", (target_date,)).fetchone()[0] or 0
                # Daily sell orders sum
                sum_sell_orders_diff = conn.execute("SELECT SUM(COALESCE(completedSellOrderNum_diff, 0)) FROM compare WHERE date = ?", (target_date,)).fetchone()[0] or 0
                
                sell_volume_cum_cr = (sum_sell_orders * 1250) / 10000000.0
                sell_volume_daily_cr = (sum_sell_orders_diff * 1250) / 10000000.0

            query, params = build_compare_query(columns, filters)
            result = conn.execute(query, params).fetchall()
            rows = [tuple(r) for r in result]
            rows = format_epoch_ms_time_columns(columns, rows)
            rows = format_compare_deltas(columns, rows)
            rows = project_rows(columns, rows, selected_columns)
            row_count = len(rows)

            # Query leaderboard
            leaderboard_limit = int(filters["leaderboard_limit"])
            if target_date:
                leaderboard_query = """
                WITH latest_dates AS (
                    SELECT ? as date_today, ? as date_yesterday
                ),
                today_ranks AS (
                    SELECT userNo, nickName, completedOrderNum_diff,
                           ROW_NUMBER() OVER (ORDER BY COALESCE(completedOrderNum_diff, 0) DESC, userNo ASC) as rank_today
                    FROM compare
                    WHERE date = (SELECT date_today FROM latest_dates)
                ),
                yesterday_ranks AS (
                    SELECT userNo,
                           ROW_NUMBER() OVER (ORDER BY COALESCE(completedOrderNum_diff, 0) DESC, userNo ASC) as rank_yesterday
                    FROM compare
                    WHERE date = (SELECT date_yesterday FROM latest_dates)
                )
                SELECT 
                    t.rank_today,
                    t.userNo,
                    t.nickName,
                    t.completedOrderNum_diff,
                    y.rank_yesterday
                FROM today_ranks t
                LEFT JOIN yesterday_ranks y ON t.userNo = y.userNo
                ORDER BY t.rank_today ASC
                LIMIT ?
                """
                leaderboard_results = conn.execute(leaderboard_query, (target_date, prev_date, leaderboard_limit)).fetchall()
                for r in leaderboard_results:
                    rank_today, user_no, nick_name, delta_orders, rank_yesterday = r
                    rank_change_pct = None
                    if rank_yesterday:
                        diff = rank_yesterday - rank_today
                        rank_change_pct = (diff / rank_yesterday) * 100.0
                    
                    leaderboard_rows.append({
                        "rank": rank_today,
                        "userNo": user_no,
                        "username": nick_name or "—",
                        "deltaOrders": delta_orders or 0,
                        "rank_change_pct": rank_change_pct
                    })

    except Exception as exc:
        error = str(exc)

    return render_template_string(
        COMPARE_TEMPLATE,
        filters=filters,
        columns=selected_columns,
        all_columns=all_columns,
        selected_columns=selected_columns,
        rows=rows,
        row_count=row_count,
        leaderboard_rows=leaderboard_rows,
        total_users=total_users,
        active_users=active_users,
        sell_volume_cum_cr=sell_volume_cum_cr,
        sell_volume_daily_cr=sell_volume_daily_cr,
        target_date=target_date,
        error=error,
        column_panel_open=bool(request.args.getlist("visible_columns")),
    )


@app.route("/api/rebuild-compare", methods=["POST"])
def api_rebuild_compare():
    try:
        inserted_rows = rebuild_compare_db()
        return {"success": True, "inserted_rows": inserted_rows}
    except Exception as e:
        return {"success": False, "error": str(e)}, 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
