import os


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Missing environment variable: {name}")
    return value


# Telegram
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = env("TELEGRAM_CHAT_ID")

# анти-спам (сек)
DEDUP_SECONDS = int(os.getenv("DEDUP_SECONDS", "900"))

# путь к файлу состояния
STATE_PATH = os.getenv("STATE_PATH", "state.json")

# риск (% от депозита)
RISK_FIRST_MOVE = float(os.getenv("RISK_FIRST_MOVE", "0.25"))
RISK_CONFIRM = float(os.getenv("RISK_CONFIRM", "0.5"))
