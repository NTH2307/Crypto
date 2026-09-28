from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Trade:
    timestamp: datetime
    side: str
    price: float
    amount: float
    fee: float
    cash_after: float


@dataclass
class PaperPortfolio:
    """Carteira virtual: nunca envia ordens a uma exchange real."""

    cash: float
    fee_rate: float = 0.001
    position_amount: float = 0.0
    entry_price: Optional[float] = None
    trades: List[Trade] = field(default_factory=list)

    @property
    def in_position(self) -> bool:
        return self.position_amount > 0

    def equity(self, current_price: float) -> float:
        return self.cash + self.position_amount * current_price

    def buy(self, timestamp, price: float, fraction: float = 0.95) -> None:
        if self.in_position or price <= 0:
            return
        spend = self.cash * fraction
        fee = spend * self.fee_rate
        amount = (spend - fee) / price
        if amount <= 0:
            return
        self.cash -= spend
        self.position_amount = amount
        self.entry_price = price
        self.trades.append(Trade(timestamp, "buy", price, amount, fee, self.cash))

    def sell(self, timestamp, price: float) -> None:
        if not self.in_position or price <= 0:
            return
        proceeds = self.position_amount * price
        fee = proceeds * self.fee_rate
        self.cash += proceeds - fee
        self.trades.append(Trade(timestamp, "sell", price, self.position_amount, fee, self.cash))
        self.position_amount = 0.0
        self.entry_price = None
