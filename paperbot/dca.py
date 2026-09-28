from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class DcaConfig:
    """DCA: investe um capital total em parcelas iguais, espaçadas ao longo do período."""

    total_capital: float = 10_000.0
    num_installments: int = 12
    fee_rate: float = 0.001


@dataclass
class DcaResult:
    equity_curve: pd.Series
    lump_sum_equity_curve: pd.Series
    total_invested: float
    total_units: float
    final_equity: float
    total_return_pct: float
    max_drawdown_pct: float
    average_cost_basis: float
    lump_sum_final_equity: float
    lump_sum_return_pct: float
    beats_lump_sum: bool


def run_dca_backtest(ohlcv: pd.DataFrame, config: DcaConfig) -> DcaResult:
    if config.num_installments < 1:
        raise ValueError("num_installments tem de ser >= 1")
    if len(ohlcv) < config.num_installments:
        raise ValueError("Nao ha candles suficientes para o numero de parcelas pedido.")

    df = ohlcv.reset_index(drop=True)
    n = len(df)
    contribution = config.total_capital / config.num_installments

    if config.num_installments > 1:
        buy_indices = [round(i * (n - 1) / (config.num_installments - 1)) for i in range(config.num_installments)]
    else:
        buy_indices = [0]

    total_units = 0.0
    total_invested = 0.0
    equity_curve = []
    buy_pointer = 0

    for i in range(n):
        price = float(df.iloc[i]["close"])
        while buy_pointer < len(buy_indices) and buy_indices[buy_pointer] == i:
            fee = contribution * config.fee_rate
            total_units += (contribution - fee) / price
            total_invested += contribution
            buy_pointer += 1
        equity_curve.append(total_units * price)

    equity_series = pd.Series(equity_curve, index=df["timestamp"])
    final_equity = float(equity_series.iloc[-1])
    total_return_pct = (final_equity / total_invested - 1) * 100 if total_invested else 0.0
    average_cost_basis = (total_invested / total_units) if total_units else 0.0

    running_max = equity_series.cummax()
    running_max_safe = running_max.replace(0, float("nan"))
    drawdown = (equity_series - running_max) / running_max_safe
    max_drawdown_pct = float(drawdown.min() * 100) if not drawdown.dropna().empty else 0.0

    first_price = float(df.iloc[0]["close"])
    last_price = float(df.iloc[-1]["close"])
    lump_sum_fee = config.total_capital * config.fee_rate
    lump_sum_units = (config.total_capital - lump_sum_fee) / first_price
    lump_sum_final_equity = lump_sum_units * last_price
    lump_sum_return_pct = (lump_sum_final_equity / config.total_capital - 1) * 100
    lump_sum_equity_series = df["close"].astype(float) * lump_sum_units
    lump_sum_equity_series.index = df["timestamp"]

    return DcaResult(
        equity_curve=equity_series,
        lump_sum_equity_curve=lump_sum_equity_series,
        total_invested=total_invested,
        total_units=total_units,
        final_equity=final_equity,
        total_return_pct=total_return_pct,
        max_drawdown_pct=max_drawdown_pct,
        average_cost_basis=average_cost_basis,
        lump_sum_final_equity=lump_sum_final_equity,
        lump_sum_return_pct=lump_sum_return_pct,
        beats_lump_sum=total_return_pct > lump_sum_return_pct,
    )
