from flask import Flask, render_template, request, flash
import requests

app = Flask(__name__)
app.secret_key = "supersecret"

# -------------------------
# Columns to display
# -------------------------
# Priority columns (display at top)
PRIORITY_COLUMNS = [
    "registerDays", "firstOrderDays","completedSellOrderNum","completedBuyOrderNum", "completedSellOrderNumOfLatest30day",
    "completedBuyOrderNumOfLatest30day", "counterpartyCount",
    "avgReleaseTimeOfLatest30day",  "avgPayTimeOfLatest30day"  
]

# Full columns list (all stats)
USER_STATS_COLUMNS = [
    "registerDays", "firstOrderDays", "avgReleaseTimeOfLatest30day",
    "avgPayTimeOfLatest30day", "finishRateLatest30day", "completedOrderNumOfLatest30day",
    "completedBuyOrderNumOfLatest30day", "completedSellOrderNumOfLatest30day",
    "completedOrderTotalBtcAmountOfLatest30day", "completedOrderNum",
    "completedBuyOrderNum", "completedSellOrderNum", "completedBuyOrderTotalBtcAmount",
    "completedSellOrderTotalBtcAmount", "completedOrderTotalBtcAmount", "counterpartyCount"
]

# -------------------------
# Anomaly logic with column flags
# -------------------------
def anomaly_points(user_stats):
    points = 0
    column_flags = {col: False for col in USER_STATS_COLUMNS}

    # 1. Buy / Sell imbalance
    if user_stats['completedSellOrderNum'] == 0:
        points += 10
        column_flags['completedSellOrderNum'] = True
    else:
        ratio = user_stats['completedBuyOrderNum'] / user_stats['completedSellOrderNum']
        if ratio >= 8:
            points += 10
            column_flags['completedBuyOrderNum'] = True
            column_flags['completedSellOrderNum'] = True

    # 2. Orders per day since registration
    if user_stats['registerDays'] == 0:
        day_avg = 0
    else:
        day_avg = user_stats['completedBuyOrderNum'] / user_stats['registerDays']
        if 2 < day_avg < 3:
            points += 20
            column_flags['completedBuyOrderNum'] = True
            column_flags['registerDays'] = True
        elif day_avg >= 3:
            points += 30
            column_flags['completedBuyOrderNum'] = True
            column_flags['registerDays'] = True

    # 3. Last 30 days activity
    buy_30 = user_stats['completedBuyOrderNumOfLatest30day']
    if 60 <= buy_30 < 90:
        points += 30
        column_flags['completedBuyOrderNumOfLatest30day'] = True
    elif buy_30 >= 90:
        points += 40
        column_flags['completedBuyOrderNumOfLatest30day'] = True

    # 4. Counterparty concentration
    if user_stats['counterpartyCount'] == 0:
        avg = 0
    else:
        avg = user_stats['completedOrderNum'] / user_stats['counterpartyCount']

    if 2 < avg < 2.5:
        points += 10
        column_flags['completedOrderNum'] = True
        column_flags['counterpartyCount'] = True
    elif 2.5 < avg < 3:
        points += 15
        column_flags['completedOrderNum'] = True
        column_flags['counterpartyCount'] = True
    elif 3 <= avg < 4:
        points += 25
        column_flags['completedOrderNum'] = True
        column_flags['counterpartyCount'] = True
    elif avg >= 4:
        points += 40
        column_flags['completedOrderNum'] = True
        column_flags['counterpartyCount'] = True

    return points, points >= 30, column_flags

# -------------------------
# Fetch user data from Binance API
# -------------------------
def fetch_user(userNo):
    API_URL = f"https://c2c.binance.com/bapi/c2c/v2/friendly/c2c/user/profile-and-ads-list?userNo={userNo}"
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        user_stats = data["data"]["userDetailVo"].get("userStatsRet", {})
        if user_stats:
            user_stats['userNo'] = userNo
            return user_stats
    except Exception as e:
        print(f"Error fetching {userNo}: {e}")
    return None

# -------------------------
# Web page route
# -------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    user_data = None
    column_flags = {}
    if request.method == "POST":
        userNo = request.form.get("userNo", "").strip()
        if userNo:
            stats = fetch_user(userNo)
            if stats:
                points, is_anomaly, column_flags = anomaly_points(stats)
                stats["points"] = points
                stats["status"] = "ANOMALY" if is_anomaly else "NORMAL"
                user_data = stats
            else:
                flash("User not found or failed to fetch data", "danger")
        else:
            flash("Enter a userNo", "warning")

    # Prepare other columns (all except priority)
    other_columns = [c for c in USER_STATS_COLUMNS if c not in PRIORITY_COLUMNS]
    return render_template("index.html", user=user_data,
                           priority_columns=PRIORITY_COLUMNS,
                           other_columns=other_columns,
                           flags=column_flags)

# -------------------------
# Run the app
# -------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
