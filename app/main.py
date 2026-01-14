from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal

from .models import Candle, SignalInput
from .logic import build_decision
from .telegram import send_telegram
from .storage import dedup_ok

app = FastAPI(title="Crypto Listings Confirm / Entry Engine")

Mode = Literal["FIRST_MOVE", "CONFIRM_LIGHT"]


class CandleIn(BaseModel):
    o: float
    h: float
    l: float
    c: float
    v: float


class WebhookIn(BaseModel):
    symbol: str = Field(..., examples=["ESIM"])
    exchange: str = Field(..., examples=["BYBIT"])
    tf: str = Field(..., examples=["5m", "15m"])
    candles: List[CandleIn]
    mode_hint: Optional[Mode] = None


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/webhook/listing")
def webhook_listing(payload: WebhookIn):
    if payload.tf not in ("5m", "15m"):
        raise HTTPException(status_code=400, detail="tf must be 5m or 15m")

    candles = [Candle(**c.model_dump()) for c in payload.candles]

    inp = SignalInput(
        symbol=payload.symbol,
        exchange=payload.exchange,
        tf=payload.tf,
        candles=candles,
        mode_hint=payload.mode_hint,
    )

    decision = build_decision(inp)

    dedup_key = (
        f"{payload.symbol}:"
        f"{decision.mode}:"
        f"{decision.score.letter}:"
        f"{decision.score.points}:"
        f"{decision.entry_open}"
    )

    if not dedup_ok(dedup_key):
        return {"sent": False, "reason": "dedup"}

    send_telegram(decision.telegram_text)

    return {
        "sent": True,
        "mode": decision.mode,
        "score": f"{decision.score.letter}({decision.score.points}/4)",
        "entry_open": decision.entry_open,
    }
