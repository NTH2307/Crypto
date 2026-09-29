from __future__ import annotations

import pandas as pd

from .validation import _timeframe_to_minutes


def price_volatility_pct(ohlcv: pd.DataFrame, timeframe: str) -> float:
    """Volatilidade anualizada do preço (desvio padrao dos retornos, %)."""
    if len(ohlcv) < 2:
        return 0.0
    returns = ohlcv["close"].astype(float).pct_change().dropna()
    if returns.empty or returns.std() == 0:
        return 0.0
    periods_per_year = (60 * 24 * 365) / _timeframe_to_minutes(timeframe)
    return float(returns.std() * (periods_per_year ** 0.5) * 100)


def price_max_drawdown_pct(ohlcv: pd.DataFrame) -> float:
    """Pior queda historica do preco, do pico ao fundo seguinte, no periodo dado."""
    if len(ohlcv) < 2:
        return 0.0
    close = ohlcv["close"].astype(float)
    running_max = close.cummax()
    drawdown = (close - running_max) / running_max
    return float(drawdown.min() * 100)


def positive_window_pct(ohlcv: pd.DataFrame, window: int = 7) -> float:
    """Percentagem de janelas nao sobrepostas de `window` candles com retorno positivo.

    E uma medida de consistencia da tendencia no periodo testado -- nao uma
    previsao de quantas janelas futuras serao positivas.
    """
    close = ohlcv["close"].astype(float).reset_index(drop=True)
    if len(close) < window + 1:
        return 0.0

    positive = 0
    total = 0
    for start in range(0, len(close) - window, window):
        window_start = close.iloc[start]
        window_end = close.iloc[start + window]
        if window_start == 0:
            continue
        total += 1
        if window_end > window_start:
            positive += 1

    if total == 0:
        return 0.0
    return positive / total * 100
