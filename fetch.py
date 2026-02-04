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
POLL_INTERVAL = 2  # seconds between polls

# Filters
ASSET = "USDT"
FIAT = "INR"
TRADE_TYPE = "BUY"
PUBLISHER_TYPE = "merchant"
CLASSIFIES = ["mass", "profession", "fiat_trade"]
PAY_TYPES = ["UPI", "IMPS", "BankIndia", "Paytm", "GPay", "PhonePe", "BANK"]

DB_FILE = "binance_users.db"

# ----------------------------
# Setup SQLite (UNIQUE userNo)
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

# ----------------------------
# Polling loop
# ----------------------------
page = 1

print("🚀 Starting live polling (unique userNo only)... Press Ctrl+C to stop")

try:
    while True:
        payload = {
            "fiat": FIAT,
            "page": page,
            "rows": ROWS_PER_PAGE,
            "tradeType": TRADE_TYPE,
            "asset": ASSET,
            "countries": [],
            "proMerchantAds": False,
            "shieldMerchantAds": False,
            "filterType": "tradable",
            "periods": [15],
            "additionalKycVerifyFilter": 1,
            "publisherType": PUBLISHER_TYPE,
            "payTypes": PAY_TYPES,
            "classifies": CLASSIFIES,
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
            time.sleep(POLL_INTERVAL)
            continue

        if not data:
            print("🛑 No ads found.")
        else:
            new_users = 0

            for item in data:
                user_no = item.get("advertiser", {}).get("userNo")

                if user_no:
                    try:
                        cursor.execute(
                            "INSERT OR IGNORE INTO users (userNo) VALUES (?)",
                            (user_no,)
                        )
                        if cursor.rowcount == 1:
                            new_users += 1
                    except sqlite3.Error as e:
                        print(f"DB error for userNo {user_no}: {e}")

            conn.commit()
            print(f"Page {page}: {len(data)} ads scanned, {new_users} new users stored")

        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:
    print("\n🛑 Polling stopped by user.")

finally:
    conn.close()
    print("✅ Database closed")
