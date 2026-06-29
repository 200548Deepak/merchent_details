import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

SOURCE_DB_PATH = Path(r"merch_details.db")
TARGET_DB_PATH = Path(r"compare.db")
SOURCE_TABLE = "user_info"
TARGET_TABLE = "compare"

COMPARE_COLUMNS = [
    "completedOrderNum",
    "completedBuyOrderNum",
    "completedSellOrderNum",
]


@dataclass
class ColumnMeta:
    name: str
    type_name: str
    is_pk: bool


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def get_table_columns(conn: sqlite3.Connection, db_alias: str, table_name: str) -> List[ColumnMeta]:
    rows = conn.execute(
        f"PRAGMA {quote_ident(db_alias)}.table_info({quote_ident(table_name)})"
    ).fetchall()
    return [ColumnMeta(name=row[1], type_name=(row[2] or ""), is_pk=bool(row[5])) for row in rows]


def detect_date_column(columns: Sequence[ColumnMeta]) -> str:
    names = {c.name for c in columns}
    if "date" in names:
        return "date"
    if "created_at" in names:
        return "created_at"
    raise ValueError("user_info has no date or created_at column")


def detect_partition_columns(columns: Sequence[ColumnMeta], date_col: str) -> List[str]:
    if any(c.name == "userNo" for c in columns):
        return ["userNo"]

    pk_cols = [c.name for c in columns if c.is_pk and c.name != date_col]
    if pk_cols:
        return pk_cols

    raise ValueError("No partition column available to compare current day with previous day")


def validate_compare_columns(columns: Sequence[ColumnMeta]) -> None:
    names = {c.name for c in columns}
    missing = [c for c in COMPARE_COLUMNS if c not in names]
    if missing:
        raise ValueError(f"Missing required compare columns in user_info: {', '.join(missing)}")


def create_compare_table(conn: sqlite3.Connection) -> int:
    columns = get_table_columns(conn, "src", SOURCE_TABLE)
    validate_compare_columns(columns)

    date_col = detect_date_column(columns)
    partition_cols = detect_partition_columns(columns, date_col)

    base_defs = [
        f"{quote_ident(c.name)} {(c.type_name or 'TEXT')}"
        for c in columns
    ]
    diff_defs = [f"{quote_ident(f'{name}_diff')} INTEGER" for name in COMPARE_COLUMNS]

    conn.execute(f"DROP TABLE IF EXISTS {quote_ident(TARGET_TABLE)}")
    conn.execute(
        f"CREATE TABLE {quote_ident(TARGET_TABLE)} (\n    "
        + ",\n    ".join(base_defs + diff_defs)
        + "\n)"
    )

    partition_expr = ", ".join(f"u.{quote_ident(c)}" for c in partition_cols)
    order_expr = f"date(u.{quote_ident(date_col)})"

    select_exprs = [f"u.{quote_ident(c.name)}" for c in columns]
    for name in COMPARE_COLUMNS:
        q_name = quote_ident(name)
        q_diff = quote_ident(f"{name}_diff")
        select_exprs.append(
            "CASE "
            f"WHEN u.{q_name} IS NULL OR LAG(u.{q_name}) OVER (PARTITION BY {partition_expr} ORDER BY {order_expr}) IS NULL THEN NULL "
            f"ELSE CAST(u.{q_name} AS INTEGER) - CAST(LAG(u.{q_name}) OVER (PARTITION BY {partition_expr} ORDER BY {order_expr}) AS INTEGER) "
            f"END AS {q_diff}"
        )

    insert_sql = (
        f"INSERT INTO {quote_ident(TARGET_TABLE)}\n"
        "SELECT\n    "
        + ",\n    ".join(select_exprs)
        + f"\nFROM {quote_ident('src')}.{quote_ident(SOURCE_TABLE)} u"
    )

    cur = conn.execute(insert_sql)
    return cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0


def rebuild_compare_db() -> int:
    TARGET_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(TARGET_DB_PATH) as conn:
        conn.execute(f"ATTACH DATABASE {str(SOURCE_DB_PATH)!r} AS {quote_ident('src')}")
        inserted_rows = create_compare_table(conn)
        conn.commit()
        conn.execute(f"DETACH DATABASE {quote_ident('src')}")
    return inserted_rows


def main() -> None:
    inserted_rows = rebuild_compare_db()
    print("Created compare table in compare.db from user_info.")
    print("Added diff columns: completedOrderNum_diff, completedBuyOrderNum_diff, completedSellOrderNum_diff")
    print(f"Inserted {inserted_rows} rows")


if __name__ == "__main__":
    main()
