import requests

def Anomaly_points(user_name):
    points = 0
    API_URL = f"https://c2c.binance.com/bapi/c2c/v2/friendly/c2c/user/profile-and-ads-list?userNo={user_name}"
    
    try:
        response = requests.get(API_URL, timeout=10)
        data = response.json()
        user_stats = data["data"]["userDetailVo"].get("userStatsRet", {})
        print(f"Fetched stats for {user_name}: {user_stats}")
    except Exception as e:
        print(f"Error fetching {user_name}: {e}")
        return False
    
Anomaly_points("s5f8776c7001b3c4e9300023ccfb838f5")