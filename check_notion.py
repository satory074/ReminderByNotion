import requests
import datetime
import os

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

    now = datetime.datetime.now(datetime.timezone.utc)
    overdue_items = []

    for item in results:
        # "日付"フィールドを取得
        date_field = item.get("properties", {}).get("日付", {}).get("date", {}).get("start")
        if date_field:
            # ISO形式の日時をdatetimeオブジェクトに変換
            date = datetime.datetime.fromisoformat(date_field)
            # タイムゾーン情報を付与
            if date.tzinfo is None:
                date = date.replace(tzinfo=datetime.timezone.utc)
            # 現在時刻（UTC）と比較
            if date < now:
                overdue_items.append(item["properties"]["タイトル"]["title"][0]["text"]["content"])

    if overdue_items:
        message = {"text": f"Overdue items: {', '.join(overdue_items)}"}
        response = requests.post(WEBHOOK_URL, json=message)
        print("Notification sent:", response.status_code, response.text)
    else:
        print("No overdue items found.")

if __name__ == "__main__":
    check_and_notify()
