import os
import threading
import time
import requests
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Parser is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

TG_TOKEN = "8953539218:AAHIkMDMaforSQkBelAN9CZObc-X1rAKIgw"
TG_CHAT_ID = "943352873"

# Запросы напрямую к API OLX
API_URLS = [
    ("iPhone 13 Pro", "https://www.olx.ua/api/v1/offers/?offset=0&limit=40&query=iphone%2013%20pro&filter_float_price:from=5000&filter_float_price:to=14000"),
    ("iPhone 14 Pro", "https://www.olx.ua/api/v1/offers/?offset=0&limit=40&query=iphone%2014%20pro&filter_float_price:from=5000&filter_float_price:to=18000"),
    ("iPhone 15 Pro", "https://www.olx.ua/api/v1/offers/?offset=0&limit=40&query=iphone%2015%20pro&filter_float_price:from=5000&filter_float_price:to=20000"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Version": "2.0"
}

seen_ads = set()
is_first_run = True

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка ТГ: {e}", flush=True)

def check_olx():
    global is_first_run
    print("🔍 Начинаю сканирование API OLX...", flush=True)
    
    for model_name, url in API_URLS:
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                print(f"⚠️ Ошибка API ({model_name}): Статус {response.status_code}", flush=True)
                continue

            data = response.json()
            offers = data.get("data", [])
            print(f"Найдено объявлений ({model_name}): {len(offers)}", flush=True)

            for item in offers:
                ad_id = item.get("id")
                clean_link = item.get("url")
                title = item.get("title", "iPhone")
                
                # Достаем цену
                params = item.get("params", [])
                price = "Договорная"
                for p in params:
                    if p.get("key") == "price":
                        price = p.get("value", {}).get("label", "Договорная")
                        break

                if str(ad_id) in seen_ads or clean_link in seen_ads:
                    continue

                if not is_first_run:
                    print(f"🔥 НАЙДЕНО НОВОЕ ОБЪЯВЛЕНИЕ: {title} - {price}", flush=True)
                    msg = f"🔥 <b>Новый лот на OLX!</b>\n\n📱 <b>{title}</b>\n💰 <b>Цена:</b> {price}\n\n🔗 <a href='{clean_link}'>Открыть объявление</a>"
                    send_telegram(msg)

                seen_ads.add(str(ad_id))
                if clean_link:
                    seen_ads.add(clean_link)

            time.sleep(2)
        except Exception as e:
            print(f"Ошибка парсинга API ({model_name}): {e}", flush=True)

    if is_first_run:
        print(f"✅ Первый круг завершен. В базе {len(seen_ads)} старых объявлений.", flush=True)
        is_first_run = False

def main_loop():
    send_telegram("🚀 Парсер переведен на чистый API OLX! Блокировки пройдены.")
    while True:
        check_olx()
        time.sleep(60)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    main_loop()
