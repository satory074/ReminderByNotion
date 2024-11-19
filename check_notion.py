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
        date_property = item.get("properties", {}).get("日付", {})
        date_value = date_property.get("date")
        if date_value and date_value.get("start"):
            date_field = date_value.get("start")
            try:
                # ISO形式の日時をdatetimeオブジェクトに変換
                date = datetime.datetime.fromisoformat(date_field)
                # タイムゾーン情報を付与
                if date.tzinfo is None:
                    date = date.replace(tzinfo=datetime.timezone.utc)
                # 現在時刻（UTC）と比較
                if date < now:
                    # "タイトル"フィールドを取得
                    title_property = item.get("properties", {}).get("タイトル", {})
                    title_list = title_property.get("title", [])
                    if title_list:
                        title_text = title_list[0].get("text", {}).get("content", "No Title")
                    else:
                        title_text = "No Title"
                    overdue_items.append(title_text)
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
        message = {"content": f"Overdue items: {', '.join(overdue_items)}"}
        response = requests.post(WEBHOOK_URL, json=message)
        print("Notification sent:", response.status_code, response.text)
    else:
        print("No overdue items found.")

if __name__ == "__main__":
    check_and_notify()
