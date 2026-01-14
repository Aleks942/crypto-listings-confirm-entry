import requests
from .config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True
        # parse_mode УБРАН — ЭТО КЛЮЧЕВО
    }
    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
