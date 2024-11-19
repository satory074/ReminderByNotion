import requests
import datetime
import os
import pytz

NOTION_API_KEY = os.getenv("NOTION_API_KEYS")
DATABASE_ID = os.getenv("DATABASE_IDS")
WEBHOOK_URL = os.getenv("WEBHOOK_URLS")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def check_and_notify():
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    response = requests.post(url, headers=headers)
    print("Notion API Response:", response.json()) 
    results = response.json().get("results", [])

    now_utc = datetime.datetime.now(datetime.timezone.utc)
    jst = pytz.timezone('Asia/Tokyo')
    now_jst = now_utc.astimezone(jst)
    overdue_items = []

    for item in results:
        # "日付"フィールドを取得
        date_property = item.get("properties", {}).get("日付", {})
        date_value = date_property.get("date")
        if date_value and date_value.get("start"):
            date_field = date_value.get("start")
            try:
                # ISO形式の日時をdatetimeオブジェクトに変換
                date_utc = datetime.datetime.fromisoformat(date_field)
                # タイムゾーン情報がない場合はUTCを設定
                if date_utc.tzinfo is None:
                    date_utc = date_utc.replace(tzinfo=datetime.timezone.utc)
                # JSTに変換
                date_jst = date_utc.astimezone(jst)
                # 現在時刻（JST）と比較
                if date_jst < now_jst:
                    # "タイトル"フィールドを取得
                    title_property = item.get("properties", {}).get("タイトル", {})
                    title_list = title_property.get("title", [])
                    if title_list:
                        title_text = title_list[0].get("text", {}).get("content", "No Title")
                    else:
                        title_text = "No Title"
                    # 期限切れのアイテムをリストに追加
                    overdue_items.append({'title': title_text, 'date': date_jst})
            except ValueError as e:
                print(f"Invalid date format for item: {item['id']}")
                continue
        else:
            # "日付"フィールドがない、または無効な場合はスキップ
            title_property = item.get("properties", {}).get("タイトル", {})
            title_list = title_property.get("title", [])
            if title_list:
                title_text = title_list[0].get("text", {}).get("content", "No Title")
            else:
                title_text = "No Title"
            print(f"Skipping item with missing or invalid date: {title_text}")

    if overdue_items:
        # 日付で昇順にソート
        overdue_items.sort(key=lambda x: x['date'])

        # Discordの埋め込みメッセージを作成
        embed_fields = []
        for item in overdue_items:
            date_str = item['date'].strftime('%Y-%m-%d %H:%M')
            embed_fields.append({
                "name": item['title'],
                "value": f"期限日: {date_str}",
                "inline": False
            })

        embed = {
            "title": "【リマインダー】期限切れのアイテムがあります",
            "color": 15158332,  # 赤色
            "fields": embed_fields,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

        data = {
            "embeds": [embed]
        }

        response = requests.post(WEBHOOK_URL, json=data)
        print("Notification sent:", response.status_code, response.text)
    else:
        print("No overdue items found.")

if __name__ == "__main__":
    check_and_notify()
