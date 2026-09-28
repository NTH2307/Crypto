from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd

from .portfolio import PaperPortfolio, Trade
from .strategy import SmaCrossRsiStrategy


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    trades: List[Trade]
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    num_trades: int
    win_rate_pct: float


def run_backtest(
    ohlcv: pd.DataFrame,
    strategy: SmaCrossRsiStrategy,
    initial_cash: float = 10_000.0,
    fee_rate: float = 0.001,
) -> BacktestResult:
    df = strategy.compute_indicators(ohlcv).reset_index(drop=True)
    portfolio = PaperPortfolio(cash=initial_cash, fee_rate=fee_rate)
    equity_curve = []

    for i in range(len(df)):
        row = df.iloc[i]
        signal = strategy.generate_signal(df, i, portfolio.in_position, portfolio.entry_price)
        if signal == "buy":
            portfolio.buy(row["timestamp"], row["close"])
        elif signal == "sell":
            portfolio.sell(row["timestamp"], row["close"])
        equity_curve.append(portfolio.equity(row["close"]))

    equity_series = pd.Series(equity_curve, index=df["timestamp"] if len(df) else None)
    final_equity = equity_series.iloc[-1] if len(equity_series) else initial_cash
    total_return_pct = (final_equity / initial_cash - 1) * 100 if initial_cash else 0.0

    if len(equity_series):
        running_max = equity_series.cummax()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown_pct = drawdown.min() * 100
    else:
        max_drawdown_pct = 0.0

    sell_trades = [t for t in portfolio.trades if t.side == "sell"]
    buy_trades = [t for t in portfolio.trades if t.side == "buy"]
    wins = sum(1 for buy, sell in zip(buy_trades, sell_trades) if sell.price > buy.price)
    win_rate_pct = (wins / len(sell_trades) * 100) if sell_trades else 0.0

    return BacktestResult(
        equity_curve=equity_series,
        trades=portfolio.trades,
        final_equity=final_equity,
        total_return_pct=total_return_pct,
        max_drawdown_pct=max_drawdown_pct,
        num_trades=len(portfolio.trades),
        win_rate_pct=win_rate_pct,
    )
