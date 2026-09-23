import os
import threading
import time
import requests
from bs4 import BeautifulSoup
from flask import Flask

# Заглушка для Render, чтобы он думал, что это сайт
app = Flask(__name__)


@app.route("/")
def home():
  return "Parser is running!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


TG_TOKEN = "8953539218:AAHIkMDMaforSQkBelAN9CZObc-X1rAKIgw"
TG_CHAT_ID = "943352873"

OLX_URLS = [
    "https://www.olx.ua/d/uk/elektronika/telefony-i-aksessuary/smartfony/q-iphone-13-pro/?search%5Bfilter_float_price%3Afrom%5D=5000&search%5Bfilter_float_price%3Ato%5D=14000",
    "https://www.olx.ua/d/uk/elektronika/telefony-i-aksessuary/smartfony/q-iphone-14-pro/?search%5Bfilter_float_price%3Afrom%5D=5000&search%5Bfilter_float_price%3Ato%5D=18000",
    "https://www.olx.ua/d/uk/elektronika/telefony-i-aksessuary/smartfony/q-iphone-15-pro/?search%5Bfilter_float_price%3Afrom%5D=5000&search%5Bfilter_float_price%3Ato%5D=20000",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

seen_ads = set()


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
    print(f"Ошибка ТГ: {e}")


def check_olx():
  for url in OLX_URLS:
    try:
      response = requests.get(url, headers=HEADERS, timeout=15)
      if response.status_code != 200:
        continue

      soup = BeautifulSoup(response.text, "html.parser")
      cards = soup.find_all("div", {"data-cy": "l-card"})

      for card in cards:
        link_tag = card.find("a")
        if not link_tag:
          continue

        raw_link = link_tag.get("href")
        clean_link = (
            "https://www.olx.ua" + raw_link.split("#")[0]
            if raw_link.startswith("/")
            else raw_link.split("#")[0]
        )

        if clean_link in seen_ads:
          continue

        title_elem = card.find("h6")
        title = title_elem.text.strip() if title_elem else "iPhone"

        price_elem = card.find("p", {"data-testid": "ad-price"})
        price = price_elem.text.strip() if price_elem else "Договорная"

        if len(seen_ads) > 0:
          msg = f"🔥 <b>Новый лот на OLX!</b>\n\n📱 <b>{title}</b>\n💰 <b>Цена:</b> {price}\n\n🔗 <a href='{clean_link}'>Открыть объявление</a>"
          send_telegram(msg)

        seen_ads.add(clean_link)

      time.sleep(3)
    except Exception as e:
      print(f"Ошибка парсинга: {e}")


def main_loop():
  send_telegram(
      "🚀 Парсер запущен на Render и отслеживает 13 Pro, 14 Pro и 15 Pro!"
  )
  while True:
    check_olx()
    time.sleep(90)

send_telegram("🔔 Тестовое сообщение! Бот работает и связь с ТГ есть.")
if __name__ == "__main__":
  # Запускаем сайт в отдельном потоке
  threading.Thread(target=run_flask, daemon=True).start()
  # Запускаем парсер
  main_loop()
