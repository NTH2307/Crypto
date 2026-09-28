from __future__ import annotations

from typing import Optional

import pandas as pd

from .config import StrategyConfig
from .indicators import rsi, sma


class SmaCrossRsiStrategy:
    """Cruzamento de SMA rápida/lenta, filtrado por RSI, com stop-loss."""

    def __init__(self, config: Optional[StrategyConfig] = None):
        self.config = config or StrategyConfig()

    def compute_indicators(self, ohlcv: pd.DataFrame) -> pd.DataFrame:
        df = ohlcv.copy()
        df["sma_fast"] = sma(df["close"], self.config.fast_period)
        df["sma_slow"] = sma(df["close"], self.config.slow_period)
        df["rsi"] = rsi(df["close"], self.config.rsi_period)
        return df

    def generate_signal(
        self,
        df: pd.DataFrame,
        i: int,
        in_position: bool,
        entry_price: Optional[float],
    ) -> str:
        """Devolve 'buy', 'sell' ou 'hold' para a candle no índice i."""
        if i < 1:
            return "hold"

        row = df.iloc[i]
        prev = df.iloc[i - 1]

        if pd.isna(row["sma_fast"]) or pd.isna(row["sma_slow"]) or pd.isna(row["rsi"]):
            return "hold"

        crossed_up = prev["sma_fast"] <= prev["sma_slow"] and row["sma_fast"] > row["sma_slow"]
        crossed_down = prev["sma_fast"] >= prev["sma_slow"] and row["sma_fast"] < row["sma_slow"]

        if in_position:
            if entry_price is not None:
                stop_price = entry_price * (1 - self.config.stop_loss_pct)
                if row["close"] <= stop_price:
                    return "sell"
            if crossed_down:
                return "sell"
            return "hold"

        if crossed_up and row["rsi"] < self.config.rsi_overbought:
            return "buy"
        return "hold"
