from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ScoreResult:
    grade: str          # A / B / C
    points: int         # 0–5
    reasons: List[str]  # объяснение
    send: bool          # слать в Telegram или молчать


def score_entry(
    candles_5m: List[Dict],
    candles_15m: List[Dict] | None = None,
) -> ScoreResult:
    """
    Prop-style scoring engine.
    Работает строго, без эмоций.
    """

    points = 0
    reasons = []

    # ===============================
    # 1. Импульс 5m
    # ===============================
    if len(candles_5m) >= 3:
        last = candles_5m[-1]
        prev = candles_5m[-2]

        body = abs(last["c"] - last["o"])
        prev_body = abs(prev["c"] - prev["o"])

        if body > prev_body * 1.3:
            points += 1
            reasons.append("Импульсная свеча 5m")

        if last["v"] > sum(c["v"] for c in candles_5m[-6:-1]) / 5:
            points += 1
            reasons.append("Объём выше среднего")

    # ===============================
    # 2. Структура (нет рванья)
    # ===============================
    closes = [c["c"] for c in candles_5m[-5:]]
    if max(closes) - min(closes) < min(closes) * 0.06:
        points += 1
        reasons.append("Контролируемая структура")

    # ===============================
    # 3. Подтверждение 15m
    # ===============================
    if candles_15m and len(candles_15m) >= 2:
        last15 = candles_15m[-1]
        prev15 = candles_15m[-2]

        if last15["c"] > prev15["c"]:
            points += 1
            reasons.append("Подтверждение таймфрейма 15m")

    # ===============================
    # 4. Грейд
    # ===============================
    if points >= 4:
        grade = "A"
        send = True
    elif points == 3:
        grade = "B"
        send = True
    elif points == 2:
        grade = "C"
        send = True
    else:
        grade = "NO_TRADE"
        send = False

    return ScoreResult(
        grade=grade,
        points=points,
        reasons=reasons,
        send=send,
    )
