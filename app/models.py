from dataclasses import dataclass
from typing import Optional, Literal


# режим логики
Mode = Literal["FIRST_MOVE", "CONFIRM_LIGHT"]

# оценка силы
ScoreLetter = Literal["A", "B", "C"]


@dataclass
class Candle:
    o: float
    h: float
    l: float
    c: float
    v: float


@dataclass
class SignalInput:
    symbol: str
    exchange: str
    tf: str                    # "5m" или "15m"
    candles: list[Candle]
    mode_hint: Optional[Mode] = None
