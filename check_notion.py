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

    jst = pytz.timezone('Asia/Tokyo')
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    now_jst = now_utc.astimezone(jst)
    today_jst = now_jst.date()
    overdue_items = []
    due_today_items = []

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
                due_date = date_jst.date()
                # "タイトル"フィールドを取得
                title_property = item.get("properties", {}).get("タイトル", {})
                title_list = title_property.get("title", [])
                if title_list:
                    title_text = title_list[0].get("text", {}).get("content", "No Title")
                else:
                    title_text = "No Title"
                # 日付を簡潔な形式にフォーマット
                date_str = date_jst.strftime('%Y-%m-%d %H:%M')
                task_info = {'title': title_text, 'date': date_jst, 'date_str': date_str}

                # タスクを分類
                if due_date < today_jst:
                    overdue_items.append(task_info)
                elif due_date == today_jst:
                    due_today_items.append(task_info)
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

    if overdue_items or due_today_items:
        embeds = []

        if overdue_items:
            # 日付で昇順にソート
            overdue_items.sort(key=lambda x: x['date'])
            # Overdueタスクの埋め込みメッセージを作成
            embed_fields = []
            for item in overdue_items:
                embed_fields.append({
                    "name": item['title'],
                    "value": f"期限日: {item['date_str']}",
                    "inline": False
                })
            embed = {
                "title": "【リマインダー】期限が切れたタスクがあります",
                "color": 15158332,  # 赤色
                "fields": embed_fields,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            embeds.append(embed)

        if due_today_items:
            # 日付で昇順にソート
            due_today_items.sort(key=lambda x: x['date'])
            # 今日が期限のタスクの埋め込みメッセージを作成
            embed_fields = []
            for item in due_today_items:
                embed_fields.append({
                    "name": item['title'],
                    "value": f"期限日: {item['date_str']}",
                    "inline": False
                })
            embed = {
                "title": "【リマインダー】今日が期限のタスクがあります",
                "color": 3066993,  # 緑色
                "fields": embed_fields,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            embeds.append(embed)

        data = {
            "embeds": embeds
        }

        response = requests.post(WEBHOOK_URL, json=data)
        print("Notification sent:", response.status_code, response.text)
    else:
        print("No overdue or due today items found.")

if __name__ == "__main__":
    check_and_notify()
