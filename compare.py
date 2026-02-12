import sqlite3
from typing import List, Optional, Tuple

DB_PATH = r"E:\Deepak\Work\merchent_details\merch_details.db"


def detect_date_column(conn: sqlite3.Connection) -> str:
	columns = [row[1] for row in conn.execute("PRAGMA table_info(user_info)")]
	if "date" in columns:
		return "date"
	if "created_at" in columns:
		return "created_at"
	raise ValueError("user_info does not contain a date column")


def fetch_daily_diffs(
	conn: sqlite3.Connection,
	date_col: str,
) -> List[Tuple[str, str, int, int, int]]:
	query = f"""
	WITH daily AS (
		SELECT
			userNo,
			date({date_col}) AS day,
			MAX(completedOrderNumOfLatest30day) AS value
		FROM user_info
		WHERE completedOrderNumOfLatest30day IS NOT NULL
		GROUP BY userNo, day
	),
	diffs AS (
		SELECT
			d.userNo,
			d.day AS day,
			d.value AS value,
			p.value AS prev_value,
			d.value - p.value AS diff
		FROM daily d
		JOIN daily p
			ON d.userNo = p.userNo
			AND p.day = date(d.day, '-1 day')
	)
	SELECT day, userNo, value, prev_value, diff
	FROM diffs
	ORDER BY day, userNo;
	"""
	return conn.execute(query).fetchall()


def fetch_avg_diff_overall(
	conn: sqlite3.Connection,
	date_col: str,
) -> Optional[float]:
	query = f"""
	WITH daily AS (
		SELECT
			userNo,
			date({date_col}) AS day,
			MAX(completedOrderNumOfLatest30day) AS value
		FROM user_info
		WHERE completedOrderNumOfLatest30day IS NOT NULL
		GROUP BY userNo, day
	),
	diffs AS (
		SELECT
			d.userNo,
			d.day AS day,
			d.value - p.value AS diff
		FROM daily d
		JOIN daily p
			ON d.userNo = p.userNo
			AND p.day = date(d.day, '-1 day')
	)
	SELECT AVG(diff) FROM diffs;
	"""
	row = conn.execute(query).fetchone()
	return row[0] if row else None


def fetch_avg_diff_by_day(
	conn: sqlite3.Connection,
	date_col: str,
) -> List[Tuple[str, float, int]]:
	query = f"""
	WITH daily AS (
		SELECT
			userNo,
			date({date_col}) AS day,
			MAX(completedOrderNumOfLatest30day) AS value
		FROM user_info
		WHERE completedOrderNumOfLatest30day IS NOT NULL
		GROUP BY userNo, day
	),
	diffs AS (
		SELECT
			d.userNo,
			d.day AS day,
			d.value - p.value AS diff
		FROM daily d
		JOIN daily p
			ON d.userNo = p.userNo
			AND p.day = date(d.day, '-1 day')
	)
	SELECT day, AVG(diff) AS avg_diff, COUNT(*) AS sample_count
	FROM diffs
	GROUP BY day
	ORDER BY day;
	"""
	return conn.execute(query).fetchall()


def store_daily_diffs(
	conn: sqlite3.Connection,
	date_col: str,
) -> int:
	conn.execute("""
	CREATE TABLE IF NOT EXISTS user_info_diffs (
		userNo TEXT,
		day DATE,
		value INTEGER,
		prev_value INTEGER,
		diff INTEGER,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		PRIMARY KEY (userNo, day)
	)
	""")

	query = f"""
	WITH daily AS (
		SELECT
			userNo,
			date({date_col}) AS day,
			MAX(completedOrderNumOfLatest30day) AS value
		FROM user_info
		WHERE completedOrderNumOfLatest30day IS NOT NULL
		GROUP BY userNo, day
	),
	diffs AS (
		SELECT
			d.userNo,
			d.day AS day,
			d.value AS value,
			p.value AS prev_value,
			d.value - p.value AS diff
		FROM daily d
		JOIN daily p
			ON d.userNo = p.userNo
			AND p.day = date(d.day, '-1 day')
	)
	INSERT OR REPLACE INTO user_info_diffs (userNo, day, value, prev_value, diff)
	SELECT userNo, day, value, prev_value, diff
	FROM diffs;
	"""

	cur = conn.execute(query)
	conn.commit()
	return cur.rowcount


def main() -> None:
	with sqlite3.connect(DB_PATH) as conn:
		date_col = detect_date_column(conn)
		stored = store_daily_diffs(conn, date_col)

		overall_avg = fetch_avg_diff_overall(conn, date_col)
		daily_avgs = fetch_avg_diff_by_day(conn, date_col)

	if overall_avg is None:
		print("No day-over-day comparisons available.")
		return

	print("Average day-over-day change (completedOrderNumOfLatest30day):")
	print(f"Overall average: {overall_avg:.2f}")
	print("\nDaily averages:")
	for day, avg_diff, sample_count in daily_avgs:
		print(f"{day}: avg_diff={avg_diff:.2f} (n={sample_count})")

	print(f"\nStored diffs in user_info_diffs: {stored}")


if __name__ == "__main__":
	main()
