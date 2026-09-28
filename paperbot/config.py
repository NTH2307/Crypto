from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StrategyConfig:
    """Parâmetros da estratégia de cruzamento de médias móveis + RSI."""

    fast_period: int = 20
    slow_period: int = 50
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    stop_loss_pct: float = 0.05
