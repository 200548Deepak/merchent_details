import requests
import json
import time
import sqlite3

# ----------------------------
# Settings
# ----------------------------
API_URL = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://p2p.binance.com",
    "Referer": "https://p2p.binance.com"
}

ROWS_PER_PAGE = 10
PAGE_SLEEP = 1
CYCLE_SLEEP = 10

DB_FILE = "binance_merch.db"

# ----------------------------
# Setup SQLite (UNIQUE users)
# ----------------------------
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    userNo TEXT PRIMARY KEY,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()

print("🚀 Fetching ALL pages — saving UNIQUE userNo only")

try:
    while True:
        page = 1
        total_new = 0

        while True:
            payload = {
                "fiat": "INR",
                "page": page,
                "rows": 10,
                "tradeType": "BUY",
                "asset": "USDT",
                "countries": [],
                "proMerchantAds": False,
                "shieldMerchantAds": False,
                "filterType": "tradable",
                "periods": [],
                "additionalKycVerifyFilter": 0,
                "publisherType": "merchant",
                "payTypes": [],
                "classifies": ["mass", "profession", "fiat_trade"],
                "tradedWith": False,
                "followed": False
            }

            try:
                response = requests.post(
                    API_URL,
                    headers=HEADERS,
                    data=json.dumps(payload),
                    timeout=10
                )
                data = response.json().get("data", [])
            except Exception as e:
                print(f"❌ Error fetching page {page}: {e}")
                break

            if not data:
                print(f"🛑 Reached last page ({page - 1})")
                break

            new_users = 0
            for item in data:
                user_no = item.get("advertiser", {}).get("userNo")

                if user_no:
                    cursor.execute(
                        "INSERT OR IGNORE INTO users (userNo) VALUES (?)",
                        (user_no,)
                    )
                    if cursor.rowcount == 1:
                        new_users += 1

            conn.commit()
            total_new += new_users

            print(f"Page {page}: {len(data)} ads scanned, {new_users} new users")

            page += 1
            time.sleep(PAGE_SLEEP)

        print(f"✅ Cycle complete. Total NEW users added: {total_new}")
        print(f"⏳ Sleeping {CYCLE_SLEEP}s before next cycle...\n")
        time.sleep(CYCLE_SLEEP)

except KeyboardInterrupt:
    print("\n🛑 Stopped by user")

finally:
    conn.close()
    print("✅ Database closed")
