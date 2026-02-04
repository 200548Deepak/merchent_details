import sqlite3

# Database file
DB_FILE = "binance_ads.db"

# Connect to SQLite
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# Fetch all rows from the table
cursor.execute("SELECT * FROM ads")
rows = cursor.fetchall()

# Print table headers
print(f"{'advNo':<25} {'userNo':<40} {'fetched_at'}")
print("-" * 80)

# Print all rows
for adv_no, user_no, fetched_at in rows:
    print(f"{adv_no:<25} {user_no:<40} {fetched_at}")

# Close connection
conn.close()

print(f"\nTotal rows: {len(rows)}")
