import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from flask import Flask, render_template_string, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "merch_details.db"
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
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background: #f8fafc; color: #0f172a; }
    h1 { margin: 0 0 16px; }
    .card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
    .row { display: flex; gap: 12px; flex-wrap: wrap; align-items: end; }
    .field { display: flex; flex-direction: column; min-width: 140px; }
    label { font-size: 12px; color: #475569; margin-bottom: 4px; font-weight: 600; }
    input, select, button { padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; }
    button { cursor: pointer; background: #2563eb; color: white; border: none; }
    button:hover { background: #1d4ed8; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { border: 1px solid #e2e8f0; padding: 6px 8px; text-align: left; }
    th { background: #f1f5f9; position: sticky; top: 0; }
    .table-wrap { max-height: 70vh; overflow: auto; }
    .muted { color: #64748b; font-size: 12px; }
    .stats { display: flex; gap: 18px; flex-wrap: wrap; }
    .error { color: #b91c1c; font-weight: 600; }
    .filter-section { border-top: 1px solid #e2e8f0; padding-top: 12px; margin-top: 12px; }
  </style>
</head>
<body>
  <h1>Merchant Details Dashboard</h1>

  <div class="card">
    <form method="get">
      <div class="row">
        <div class="field">
          <label for="table">Table</label>
          <select id="table" name="table" onchange="this.form.submit()">
            {% for t in allowed_tables %}
              <option value="{{ t }}" {% if t == filters.table %}selected{% endif %}>{{ t }}</option>
            {% endfor %}
          </select>
        </div>

        <div class="field">
          <label for="user_no">User No</label>
          <input id="user_no" name="user_no" value="{{ filters.user_no }}" placeholder="Search userNo" />
        </div>

        <div class="field">
          <label for="date_from">From Date</label>
          <input id="date_from" type="date" name="date_from" value="{{ filters.date_from }}" />
        </div>

        <div class="field">
          <label for="date_to">To Date</label>
          <input id="date_to" type="date" name="date_to" value="{{ filters.date_to }}" />
        </div>

        <div class="field">
          <label for="last_active_from">Last Active From (IST)</label>
          <input id="last_active_from" type="datetime-local" name="last_active_from" value="{{ filters.last_active_from }}" />
        </div>

        <div class="field">
          <label for="last_active_to">Last Active To (IST)</label>
          <input id="last_active_to" type="datetime-local" name="last_active_to" value="{{ filters.last_active_to }}" />
        </div>

        <div class="field">
          <label for="limit">Limit</label>
          <input id="limit" type="number" min="1" max="1000" name="limit" value="{{ filters.limit }}" />
        </div>

        <div class="field">
          <button type="submit">Apply Filters</button>
        </div>
      </div>

      <div class="filter-section">
        <div class="row">
          <div class="field">
            <label for="col_name">Column Filter</label>
            <select id="col_name" name="col_name">
              <option value="">-- Select Column --</option>
              {% for col in all_columns %}
                <option value="{{ col }}" {% if col == filters.col_name %}selected{% endif %}>{{ col }}</option>
              {% endfor %}
            </select>
          </div>

          <div class="field">
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

          <div class="field">
            <label for="col_val">Value</label>
            <input id="col_val" name="col_val" value="{{ filters.col_val }}" placeholder="Filter value" />
          </div>
        </div>
        <p class="muted">Add column-level filters, e.g., badges = "Ordinary" or completedOrderNum > 100</p>
      </div>
    </form>
  </div>

  <div class="card stats">
    <div><b>Rows shown:</b> {{ row_count }}</div>
    <div><b>Total in table:</b> {{ total_rows }}</div>
    <div><b>Distinct users in table:</b> {{ distinct_users }}</div>
  </div>

  {% if error %}
    <div class="card error">{{ error }}</div>
  {% else %}
    {% if query_executed %}
      <div class="card muted">
        <b>Debug - SQL Query:</b><br>
        <code>{{ query_executed }}</code><br>
        <b>Parameters:</b> {{ query_params }}
      </div>
    {% endif %}
    <div class="card table-wrap">
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
  {% endif %}
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


def format_last_active_time(columns: List[str], rows: List[Tuple]) -> List[Tuple]:
    try:
        last_active_idx = next(i for i, col in enumerate(columns) if col.lower() == "lastactivetime")
    except StopIteration:
        return rows

    formatted_rows: List[Tuple] = []
    for row in rows:
        row_values = list(row)
        raw_value = row_values[last_active_idx]

        if raw_value is not None and str(raw_value).strip() != "":
            try:
                epoch_ms = int(float(raw_value))
                dt_ist = datetime.fromtimestamp(epoch_ms / 1000, tz=IST_TZ)
                row_values[last_active_idx] = dt_ist.strftime("%Y-%m-%d %H:%M:%S IST")
            except (ValueError, OSError, OverflowError):
                pass

        formatted_rows.append(tuple(row_values))

    return formatted_rows


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
            rows = format_last_active_time(columns, rows)
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


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
