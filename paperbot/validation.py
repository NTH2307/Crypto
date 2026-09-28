from __future__ import annotations

from typing import List

import pandas as pd

from .portfolio import Trade

_TIMEFRAME_UNIT_MINUTES = {"m": 1, "h": 60, "d": 60 * 24, "w": 60 * 24 * 7}


def _timeframe_to_minutes(timeframe: str) -> float:
    unit = timeframe[-1]
    if unit not in _TIMEFRAME_UNIT_MINUTES:
        raise ValueError(f"Timeframe nao suportado: {timeframe!r}")
    value = float(timeframe[:-1])
    return value * _TIMEFRAME_UNIT_MINUTES[unit]


def buy_and_hold_return_pct(ohlcv: pd.DataFrame) -> float:
    """Retorno de comprar no primeiro candle e vender no ultimo (referencia)."""
    if len(ohlcv) < 2:
        return 0.0
    first_close = float(ohlcv.iloc[0]["close"])
    last_close = float(ohlcv.iloc[-1]["close"])
    if first_close == 0:
        return 0.0
    return (last_close / first_close - 1) * 100


def sharpe_ratio(equity_curve: pd.Series, timeframe: str) -> float:
    """Sharpe anualizado (assume taxa livre de risco = 0)."""
    if len(equity_curve) < 2:
        return 0.0
    returns = equity_curve.pct_change().dropna()
    if returns.empty or returns.std() == 0:
        return 0.0
    periods_per_year = (60 * 24 * 365) / _timeframe_to_minutes(timeframe)
    return float(returns.mean() / returns.std() * (periods_per_year ** 0.5))


def profit_factor(trades: List[Trade]) -> float:
    """Soma de ganhos / soma de perdas (em valor absoluto) por trade fechado."""
    buys = [t for t in trades if t.side == "buy"]
    sells = [t for t in trades if t.side == "sell"]

    gains = 0.0
    losses = 0.0
    for buy, sell in zip(buys, sells):
        pnl = sell.amount * (sell.price - buy.price) - buy.fee - sell.fee
        if pnl >= 0:
            gains += pnl
        else:
            losses += -pnl

    if losses == 0:
        return float("inf") if gains > 0 else 0.0
    return gains / losses
