import requests
import datetime
import os

NOTION_API_KEYS = os.getenv("NOTION_API_KEYS").split(",")
DATABASE_IDS = os.getenv("DATABASE_IDS").split(",")
WEBHOOK_URLS = os.getenv("WEBHOOK_URLS").split(",")

def check_and_notify(api_key, database_id, webhook_url):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    response = requests.post(url, headers=headers)
    results = response.json().get("results", [])

    now = datetime.datetime.now(datetime.timezone.utc)
    overdue_items = []

    for item in results:
        date_field = item.get("properties", {}).get("日付", {}).get("date", {}).get("start")
        if date_field:
            date = datetime.datetime.fromisoformat(date_field)
            if date < now:
                overdue_items.append(item["properties"]["Name"]["title"][0]["text"]["content"])

    if overdue_items:
        message = {"text": f"Overdue items: {', '.join(overdue_items)}"}
        response = requests.post(webhook_url, json=message)
        print("Notification sent:", response.status_code, response.text)  # 確認用
    else:
        print("No overdue items found.")  # 過期の項目がない場合のログ

if __name__ == "__main__":
    for api_key, database_id, webhook_url in zip(NOTION_API_KEYS, DATABASE_IDS, WEBHOOK_URLS):
        check_and_notify(api_key, database_id, webhook_url)
