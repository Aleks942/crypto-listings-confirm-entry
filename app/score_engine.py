from dataclasses import dataclass
from typing import List


# =========================
# Result container
# =========================
@dataclass
class CheckResult:
    ok: bool
    points: int
    note: str


# =========================
# Helpers
# =========================
def _avg(vals: List[float]) -> float:
    return sum(vals) / max(1, len(vals))


def _body(c):
    return abs(c.c - c.o)


def _range(c):
    return max(1e-9, c.h - c.l)


# =========================
# 1️⃣ LIQUIDITY + SPREAD
# =========================
def score_liquidity(candles) -> CheckResult:
    vols = [c.v for c in candles[-20:]]
    bodies = [_body(c) for c in candles[-20:]]
    ranges = [_range(c) for c in candles[-20:]]

    avg_vol = _avg(vols)
    avg_body = _avg(bodies)
    avg_range = _avg(ranges)

    # мёртвый рынок
    if avg_vol <= 0:
        return CheckResult(False, 0, "no volume")

    # тонкий рынок / большой спред
    if avg_body / avg_range < 0.15:
        return CheckResult(False, 0, "thin market / wide spread")

    pts = 2 if avg_vol > _avg(vols[:-5]) else 1
    return CheckResult(True, pts, "liquidity ok")


# =========================
# 2️⃣ STRUCTURE (NO FAKE MOVE)
# =========================
def score_structure(candles) -> CheckResult:
    last = candles[-1]
    prev = candles[-5:]

    impulse = max(c.h for c in prev) - min(c.l for c in prev)
    body = _body(last)

    # импульс без тела = манипуляция
    if body / max(1e-9, impulse) < 0.25:
        return CheckResult(False, 0, "fake impulse")

    # нет отката
    pullbacks = [c.l for c in prev]
    if min(pullbacks) >= last.l:
        return CheckResult(False, 0, "no pullback")

    return CheckResult(True, 2, "structure ok")


# =========================
# 3️⃣ TIMING + FOLLOW-THROUGH
# =========================
def score_timing(candles) -> CheckResult:
    recent = candles[-10:]
    vols = [c.v for c in recent]

    # объём всплеск был, но продолжения нет
    if max(vols[:-1]) > vols[-1] * 2:
        return CheckResult(False, 0, "no follow-through")

    # слишком поздно
    closes = [c.c for c in recent]
    if closes[-1] == max(closes):
        return CheckResult(False, 0, "late entry")

    return CheckResult(True, 2, "timing ok")
