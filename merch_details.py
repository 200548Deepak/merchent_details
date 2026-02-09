import requests
import json
import sqlite3
from datetime import datetime, timezone, timedelta

# Define IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))

def merch_detail(user_name):
    API_URL = f"https://c2c.binance.com/bapi/c2c/v2/friendly/c2c/user/profile-and-ads-list?userNo={user_name}"
    
    try:
        response = requests.get(API_URL, timeout=10)
        data = response.json()
        
        # Extract user details
        user_detail = data["data"]["userDetailVo"]
        user_stats = user_detail.get("userStatsRet", {})
        
        # Extract user info fields
        user_info = {
            "userNo": user_detail.get("userNo"),
            "registerDays": user_stats.get("registerDays"),
            "firstOrderDays": user_stats.get("firstOrderDays"),
            "avgReleaseTimeOfLatest30day": user_stats.get("avgReleaseTimeOfLatest30day"),
            "avgPayTimeOfLatest30day": user_stats.get("avgPayTimeOfLatest30day"),
            "finishRateLatest30day": user_stats.get("finishRateLatest30day"),
            "completedOrderNumOfLatest30day": user_stats.get("completedOrderNumOfLatest30day"),
            "completedBuyOrderNumOfLatest30day": user_stats.get("completedBuyOrderNumOfLatest30day"),
            "completedSellOrderNumOfLatest30day": user_stats.get("completedSellOrderNumOfLatest30day"),
            "completedOrderNum": user_stats.get("completedOrderNum"),
            "completedBuyOrderNum": user_stats.get("completedBuyOrderNum"),
            "completedSellOrderNum": user_stats.get("completedSellOrderNum"),
            "counterpartyCount": user_stats.get("counterpartyCount"),
            "userIdentity": user_detail.get("userIdentity"),
            "badges": user_detail.get("badges"),
            "vipLevel": user_detail.get("vipLevel"),
            "lastActiveTime": user_detail.get("lastActiveTime"),
            "isCompanyAccount": user_detail.get("isCompanyAccount"),
        }
        
        # Extract sell list
        sell_list = data["data"].get("sellList", [])
        sell_data = []
        for ad in sell_list:
            sell_data.append({
                "advNo": ad.get("advNo"),
                "tradeType": ad.get("tradeType"),
                "priceFloatingRatio": ad.get("priceFloatingRatio"),
                "rateFloatingRatio": ad.get("rateFloatingRatio"),
                "price": ad.get("price"),
                "initAmount": ad.get("initAmount"),
                "surplusAmount": ad.get("surplusAmount"),
                "tradableQuantity": ad.get("tradableQuantity"),
                "amountAfterEditing": ad.get("amountAfterEditing"),
                "maxSingleTransAmount": ad.get("maxSingleTransAmount"),
                "minSingleTransAmount": ad.get("minSingleTransAmount"),
            })
        
        # Extract buy list
        buy_list = data["data"].get("buyList", [])
        buy_data = []
        for ad in buy_list:
            buy_data.append({
                "advNo": ad.get("advNo"),
                "tradeType": ad.get("tradeType"),
                "priceFloatingRatio": ad.get("priceFloatingRatio"),
                "rateFloatingRatio": ad.get("rateFloatingRatio"),
                "price": ad.get("price"),
                "initAmount": ad.get("initAmount"),
                "surplusAmount": ad.get("surplusAmount"),
                "tradableQuantity": ad.get("tradableQuantity"),
                "amountAfterEditing": ad.get("amountAfterEditing"),
                "maxSingleTransAmount": ad.get("maxSingleTransAmount"),
                "minSingleTransAmount": ad.get("minSingleTransAmount"),
            })
        
        # Display results
        print("\n" + "="*60)
        print("USER INFORMATION")
        print("="*60)
        for key, value in user_info.items():
            print(f"{key}: {value}")
        
        print("\n" + "="*60)
        print(f"SELL ADS ({len(sell_data)} ads)")
        print("="*60)
        if sell_data:
            print(json.dumps(sell_data, indent=2))
        else:
            print("No sell ads found")
        
        print("\n" + "="*60)
        print(f"BUY ADS ({len(buy_data)} ads)")
        print("="*60)
        if buy_data:
            print(json.dumps(buy_data, indent=2))
        else:
            print("No buy ads found")
        
        # Save to SQLite database
        save_to_sqlite(user_info, sell_data, buy_data)
        
        return user_info, sell_data, buy_data
        
    except Exception as e:
        print(f"Error fetching {user_name}: {e}")
        return None, None, None

def save_to_sqlite(user_info, sell_data, buy_data):
    """Save extracted data to SQLite3 database"""
    try:
        # Connect to database
        conn = sqlite3.connect("merch_details.db")
        cursor = conn.cursor()
        
        # Create user info table with composite primary key (userNo, date)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_info (
                id INTEGER,
                userNo TEXT,
                registerDays INTEGER,
                firstOrderDays INTEGER,
                avgReleaseTimeOfLatest30day REAL,
                avgPayTimeOfLatest30day REAL,
                finishRateLatest30day REAL,
                completedOrderNumOfLatest30day INTEGER,
                completedBuyOrderNumOfLatest30day INTEGER,
                completedSellOrderNumOfLatest30day INTEGER,
                completedOrderNum INTEGER,
                completedBuyOrderNum INTEGER,
                completedSellOrderNum INTEGER,
                counterpartyCount INTEGER,
                userIdentity TEXT,
                badges TEXT,
                vipLevel INTEGER,
                lastActiveTime INTEGER,
                isCompanyAccount BOOLEAN,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date DATE DEFAULT (date('now')),
                PRIMARY KEY (userNo, date)
            )
        """)
        
        # Create sell ads table with composite primary key (userNo, advNo, date)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sell_ads (
                id INTEGER,
                userNo TEXT,
                advNo TEXT,
                tradeType TEXT,
                priceFloatingRatio TEXT,
                rateFloatingRatio TEXT,
                price TEXT,
                initAmount TEXT,
                surplusAmount TEXT,
                tradableQuantity TEXT,
                amountAfterEditing TEXT,
                maxSingleTransAmount TEXT,
                minSingleTransAmount TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date DATE DEFAULT (date('now')),
                PRIMARY KEY (userNo, advNo, date),
                FOREIGN KEY (userNo) REFERENCES user_info(userNo)
            )
        """)
        
        # Create buy ads table with composite primary key (userNo, advNo, date)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buy_ads (
                id INTEGER,
                userNo TEXT,
                advNo TEXT,
                tradeType TEXT,
                priceFloatingRatio TEXT,
                rateFloatingRatio TEXT,
                price TEXT,
                initAmount TEXT,
                surplusAmount TEXT,
                tradableQuantity TEXT,
                amountAfterEditing TEXT,
                maxSingleTransAmount TEXT,
                minSingleTransAmount TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                date DATE DEFAULT (date('now')),
                PRIMARY KEY (userNo, advNo, date),
                FOREIGN KEY (userNo) REFERENCES user_info(userNo)
            )
        """)
        
        # Insert user info with today's date
        current_date = datetime.now(IST).strftime('%Y-%m-%d')
        try:
            cursor.execute("""
                INSERT INTO user_info 
                (userNo, registerDays, firstOrderDays, avgReleaseTimeOfLatest30day, avgPayTimeOfLatest30day, 
                 finishRateLatest30day, completedOrderNumOfLatest30day, completedBuyOrderNumOfLatest30day, 
                 completedSellOrderNumOfLatest30day, completedOrderNum, completedBuyOrderNum, 
                 completedSellOrderNum, counterpartyCount, userIdentity, badges, vipLevel, 
                 lastActiveTime, isCompanyAccount, date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_info["userNo"],
                user_info["registerDays"],
                user_info["firstOrderDays"],
                user_info["avgReleaseTimeOfLatest30day"],
                user_info["avgPayTimeOfLatest30day"],
                user_info["finishRateLatest30day"],
                user_info["completedOrderNumOfLatest30day"],
                user_info["completedBuyOrderNumOfLatest30day"],
                user_info["completedSellOrderNumOfLatest30day"],
                user_info["completedOrderNum"],
                user_info["completedBuyOrderNum"],
                user_info["completedSellOrderNum"],
                user_info["counterpartyCount"],
                user_info["userIdentity"],
                json.dumps(user_info["badges"]),
                user_info["vipLevel"],
                user_info["lastActiveTime"],
                user_info["isCompanyAccount"],
                current_date
            ))
            print(f"Inserted user info for {current_date} into database")
        except sqlite3.IntegrityError:
            print(f"User data for {current_date} already exists in database, updating...")
            cursor.execute("""
                UPDATE user_info SET 
                registerDays=?, firstOrderDays=?, avgReleaseTimeOfLatest30day=?, avgPayTimeOfLatest30day=?,
                finishRateLatest30day=?, completedOrderNumOfLatest30day=?, completedBuyOrderNumOfLatest30day=?,
                completedSellOrderNumOfLatest30day=?, completedOrderNum=?, completedBuyOrderNum=?,
                completedSellOrderNum=?, counterpartyCount=?, userIdentity=?, badges=?, vipLevel=?,
                lastActiveTime=?, isCompanyAccount=?
                WHERE userNo=? AND date=?
            """, (
                user_info["registerDays"],
                user_info["firstOrderDays"],
                user_info["avgReleaseTimeOfLatest30day"],
                user_info["avgPayTimeOfLatest30day"],
                user_info["finishRateLatest30day"],
                user_info["completedOrderNumOfLatest30day"],
                user_info["completedBuyOrderNumOfLatest30day"],
                user_info["completedSellOrderNumOfLatest30day"],
                user_info["completedOrderNum"],
                user_info["completedBuyOrderNum"],
                user_info["completedSellOrderNum"],
                user_info["counterpartyCount"],
                user_info["userIdentity"],
                json.dumps(user_info["badges"]),
                user_info["vipLevel"],
                user_info["lastActiveTime"],
                user_info["isCompanyAccount"],
                user_info["userNo"],
                current_date
            ))
            print(f"Updated user info for {current_date} in database")
        
        # Insert sell ads with today's date
        for ad in sell_data:
            try:
                cursor.execute("""
                    INSERT INTO sell_ads 
                    (userNo, advNo, tradeType, priceFloatingRatio, rateFloatingRatio, price, 
                     initAmount, surplusAmount, tradableQuantity, amountAfterEditing, 
                     maxSingleTransAmount, minSingleTransAmount, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_info["userNo"],
                    ad["advNo"],
                    ad["tradeType"],
                    ad["priceFloatingRatio"],
                    ad["rateFloatingRatio"],
                    ad["price"],
                    ad["initAmount"],
                    ad["surplusAmount"],
                    ad["tradableQuantity"],
                    ad["amountAfterEditing"],
                    ad["maxSingleTransAmount"],
                    ad["minSingleTransAmount"],
                    current_date
                ))
            except sqlite3.IntegrityError:
                # Update if exists
                cursor.execute("""
                    UPDATE sell_ads SET
                    tradeType=?, priceFloatingRatio=?, rateFloatingRatio=?, price=?,
                    initAmount=?, surplusAmount=?, tradableQuantity=?, amountAfterEditing=?,
                    maxSingleTransAmount=?, minSingleTransAmount=?
                    WHERE userNo=? AND advNo=? AND date=?
                """, (
                    ad["tradeType"],
                    ad["priceFloatingRatio"],
                    ad["rateFloatingRatio"],
                    ad["price"],
                    ad["initAmount"],
                    ad["surplusAmount"],
                    ad["tradableQuantity"],
                    ad["amountAfterEditing"],
                    ad["maxSingleTransAmount"],
                    ad["minSingleTransAmount"],
                    user_info["userNo"],
                    ad["advNo"],
                    current_date
                ))
        
        if sell_data:
            print(f"Inserted/Updated {len(sell_data)} sell ads for {current_date}")
        
        # Insert buy ads with today's date
        for ad in buy_data:
            try:
                cursor.execute("""
                    INSERT INTO buy_ads 
                    (userNo, advNo, tradeType, priceFloatingRatio, rateFloatingRatio, price, 
                     initAmount, surplusAmount, tradableQuantity, amountAfterEditing, 
                     maxSingleTransAmount, minSingleTransAmount, date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_info["userNo"],
                    ad["advNo"],
                    ad["tradeType"],
                    ad["priceFloatingRatio"],
                    ad["rateFloatingRatio"],
                    ad["price"],
                    ad["initAmount"],
                    ad["surplusAmount"],
                    ad["tradableQuantity"],
                    ad["amountAfterEditing"],
                    ad["maxSingleTransAmount"],
                    ad["minSingleTransAmount"],
                    current_date
                ))
            except sqlite3.IntegrityError:
                # Update if exists
                cursor.execute("""
                    UPDATE buy_ads SET
                    tradeType=?, priceFloatingRatio=?, rateFloatingRatio=?, price=?,
                    initAmount=?, surplusAmount=?, tradableQuantity=?, amountAfterEditing=?,
                    maxSingleTransAmount=?, minSingleTransAmount=?
                    WHERE userNo=? AND advNo=? AND date=?
                """, (
                    ad["tradeType"],
                    ad["priceFloatingRatio"],
                    ad["rateFloatingRatio"],
                    ad["price"],
                    ad["initAmount"],
                    ad["surplusAmount"],
                    ad["tradableQuantity"],
                    ad["amountAfterEditing"],
                    ad["maxSingleTransAmount"],
                    ad["minSingleTransAmount"],
                    user_info["userNo"],
                    ad["advNo"],
                    current_date
                ))
        
        if buy_data:
            print(f"Inserted/Updated {len(buy_data)} buy ads for {current_date}")
        
        # Commit changes
        conn.commit()
        print("Saved data to: merch_details.db")
        
        conn.close()
        
    except Exception as e:
        print(f"Error saving to SQLite: {e}")

def fetch_all_users():
    """Fetch details for all users from the users table"""
    try:
        # Connect to binance_merch database to get user numbers
        conn_source = sqlite3.connect("binance_merch.db")
        cursor_source = conn_source.cursor()
        
        # Get all user numbers
        cursor_source.execute("SELECT userNo FROM users")
        users = cursor_source.fetchall()
        conn_source.close()
        
        total_users = len(users)
        print(f"\nFetching details for {total_users} users...")
        print("="*60)
        
        successful = 0
        failed = 0
        
        for index, (user_no,) in enumerate(users, 1):
            try:
                print(f"[{index}/{total_users}] Fetching details for: {user_no}")
                result = merch_detail(user_no)
                if result[0] is not None:
                    successful += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"  Error: {e}")
                failed += 1
        
        print("\n" + "="*60)
        print(f"Fetch Complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total: {total_users}")
        print("="*60)
        
    except Exception as e:
        print(f"Error fetching all users: {e}")

# Run for all users
fetch_all_users()

# Or run for a single user
# merch_detail("s5f8776c7001b3c4e9300023ccfb838f5")