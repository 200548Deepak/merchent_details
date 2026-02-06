import sqlite3
from datetime import datetime, timedelta

DB_PATH = r"E:\Deepak\Work\merchent_details\merch_details.db"
DATE_COL = "date"  # change to "created_at" if needed

today = datetime.now().date()
yesterday = today - timedelta(days=1)

query = f"""
WITH daily AS (
    SELECT
        userNo,
        date({DATE_COL}) AS day,
        MAX(completedOrderNumOfLatest30day) AS value
    FROM user_info
    WHERE date({DATE_COL}) IN (?, ?)
    GROUP BY userNo, day
),
diffs AS (
    SELECT
        COALESCE(t.userNo, y.userNo) AS userNo,
        COALESCE(t.value, 0) - COALESCE(y.value, 0) AS diff
    FROM (SELECT userNo, value FROM daily WHERE day = ?) t
    FULL OUTER JOIN (SELECT userNo, value FROM daily WHERE day = ?) y
        ON t.userNo = y.userNo
)
SELECT userNo, diff
FROM diffs
WHERE diff > 1000
ORDER BY diff DESC;
"""

# SQLite doesn't support FULL OUTER JOIN directly; emulate with UNION.
query = f"""
WITH daily AS (
    SELECT
        userNo,
        date({DATE_COL}) AS day,
        MAX(completedOrderNumOfLatest30day) AS value
    FROM user_info
    WHERE date({DATE_COL}) IN (?, ?)
    GROUP BY userNo, day
),
t AS (SELECT userNo, value FROM daily WHERE day = ?),
y AS (SELECT userNo, value FROM daily WHERE day = ?),
diffs AS (
    SELECT t.userNo, t.value - COALESCE(y.value, 0) AS diff
    FROM t LEFT JOIN y ON t.userNo = y.userNo
    UNION ALL
    SELECT y.userNo, 0 - y.value AS diff
    FROM y LEFT JOIN t ON y.userNo = t.userNo
    WHERE t.userNo IS NULL
)
SELECT userNo, diff
FROM diffs
WHERE diff > 2000
ORDER BY diff DESC;
"""

with sqlite3.connect(DB_PATH) as conn:
    rows = conn.execute(
        query,
        (today.isoformat(), yesterday.isoformat(),
         today.isoformat(), yesterday.isoformat())
    ).fetchall()
a=0
for user_no, diff in rows:
    a+=1
    print(str(a) + " " + str(user_no), diff)
