from __future__ import annotations
from dataclasses import dataclass
from .models import SignalInput, Candle, ScoreLetter, Mode
from .config import RISK_FIRST_MOVE, RISK_CONFIRM


@dataclass
class Score:
    letter: ScoreLetter
    points: int  # 0..4


@dataclass
class Decision:
    mode: Mode
    score: Score
    entry_open: bool
    entry_type: str
    risk_pct: float
    telegram_text: str


def _avg(values: list[float]) -> float:
    return sum(values) / max(1, len(values))


def _impulse_metrics(candles: list[Candle]):
    highs = [c.h for c in candles]
    lows = [c.l for c in candles]
    closes = [c.c for c in candles]
    return max(highs), min(lows), closes[-1]


def score_market(candles: list[Candle]) -> Score:
    if len(candles) < 14:
        base = candles[:-3] if len(candles) > 3 else candles
        last3 = candles[-3:]
    else:
        base = candles[-13:-3]
        last3 = candles[-3:]

    base_vol = _avg([c.v for c in base]) if base else 0
    last_vol = _avg([c.v for c in last3])

    vol_ok = base_vol > 0 and last_vol >= 1.5 * base_vol

    max_h, min_l, last_c = _impulse_metrics(candles)
    impulse = (max_h - min_l) / min_l if min_l > 0 else 0
    impulse_ok = impulse >= 0.15

    mid = min_l + 0.5 * (max_h - min_l)
    hold_ok = last_c > mid

    hl_ok = len(candles) >= 3 and candles[-1].l > candles[-2].l

    def rng(c: Candle):
        return c.h - c.l

    narrow_ok = False
    if len(candles) >= 6:
        prev = _avg([rng(c) for c in candles[-6:-3]])
        last = _avg([rng(c) for c in candles[-3:]])
        narrow_ok = last < prev

    structure_ok = hl_ok or narrow_ok

    points = sum([impulse_ok, vol_ok, hold_ok, structure_ok])

    if points == 4:
        letter: ScoreLetter = "A"
    elif points == 3:
        letter = "B"
    else:
        letter = "C"

    return Score(letter=letter, points=points)


def pick_mode(inp: SignalInput) -> Mode:
    if inp.mode_hint in ("FIRST_MOVE", "CONFIRM_LIGHT"):
        return inp.mode_hint
    return "FIRST_MOVE" if inp.tf == "5m" else "CONFIRM_LIGHT"


def entry_first_move(candles: list[Candle], score: Score):
    if score.points < 3:
        return False, "SCORE ниже B"
    if len(candles) < 4:
        return False, "Недостаточно свечей"

    last = candles[-1]
    prev = candles[-2]
    prev2 = candles[-3]

    def rng(c: Candle):
        return c.h - c.l

    pause_ok = rng(last) <= 0.8 * rng(prev) or rng(prev) <= 0.8 * rng(prev2)
    mid = last.l + 0.5 * (last.h - last.l)
    close_ok = last.c > mid

    if pause_ok and close_ok:
        return True, "Пауза и сильное закрытие"

    return False, "Нет паузы или слабое закрытие"


def entry_confirm(candles: list[Candle], score: Score):
    if score.letter != "A":
        return False, "Нужен SCORE A"
    if len(candles) < 14:
        return False, "Недостаточно истории"

    max_h, min_l, last_c = _impulse_metrics(candles)
    move = max_h - min_l
    if move <= 0:
        return False, "Нет импульса"

    retr = (max_h - last_c) / move
    retr_ok = 0.20 <= retr <= 0.40

    mid = min_l + 0.5 * move
    hold_ok = last_c > mid

    last3 = candles[-3:]
    prev3 = candles[-6:-3]
    vol_ok = _avg([c.v for c in last3]) >= 1.1 * _avg([c.v for c in prev3])

    if retr_ok and hold_ok and vol_ok:
        return True, "Коррекция и подтверждение"

    return False, "Нет подтверждения"


def build_decision(inp: SignalInput) -> Decision:
    mode = pick_mode(inp)
    score = score_market(inp.candles)

    if mode == "FIRST_MOVE":
        entry, reason = entry_first_move(inp.candles, score)
        risk = RISK_FIRST_MOVE
        entry_type = "FIRST MOVE"
        emoji = "🟢"
        tp = "TP1 +1R → 50%, стоп BE"
    else:
        entry, reason = entry_confirm(inp.candles, score)
        risk = RISK_CONFIRM
        entry_type = "CONFIRM-LIGHT"
        emoji = "🟡"
        tp = "TP1 +1R → 30%, стоп BE"

    status = "ENTRY OPEN" if entry else "NO ENTRY"

    text = (
        f"{emoji} {entry_type} — {status}\n\n"
        f"{inp.symbol} ({inp.exchange}) TF {inp.tf}\n"
        f"SCORE: {score.letter} ({score.points}/4)\n"
        f"Риск: {risk:.2f}%\n\n"
        f"Причина:\n- {reason}\n\n"
        f"Exit:\n- {tp}"
    )

    return Decision(
        mode=mode,
        score=score,
        entry_open=entry,
        entry_type=entry_type,
        risk_pct=risk,
        telegram_text=text,
    )
