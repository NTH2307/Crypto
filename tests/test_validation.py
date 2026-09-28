from datetime import datetime

import pandas as pd
import pytest

from paperbot.portfolio import Trade
from paperbot.validation import (
    _timeframe_to_minutes,
    buy_and_hold_return_pct,
    profit_factor,
    sharpe_ratio,
)


def test_timeframe_to_minutes():
    assert _timeframe_to_minutes("5m") == 5
    assert _timeframe_to_minutes("1h") == 60
    assert _timeframe_to_minutes("4h") == 240
    assert _timeframe_to_minutes("1d") == 60 * 24
    assert _timeframe_to_minutes("1w") == 60 * 24 * 7


def test_timeframe_to_minutes_invalid_unit():
    with pytest.raises(ValueError):
        _timeframe_to_minutes("1x")


def test_buy_and_hold_return_pct():
    ohlcv = pd.DataFrame({"close": [100.0, 110.0, 121.0]})
    assert buy_and_hold_return_pct(ohlcv) == pytest.approx(21.0)


def test_buy_and_hold_return_pct_needs_two_rows():
    ohlcv = pd.DataFrame({"close": [100.0]})
    assert buy_and_hold_return_pct(ohlcv) == 0.0


def test_sharpe_ratio_zero_for_flat_equity():
    equity = pd.Series([100.0, 100.0, 100.0])
    assert sharpe_ratio(equity, "1h") == 0.0


def test_sharpe_ratio_positive_for_steady_gains():
    equity = pd.Series([100.0, 101.0, 102.01, 103.03])
    assert sharpe_ratio(equity, "1h") > 0


def test_profit_factor_no_trades_is_zero():
    assert profit_factor([]) == 0.0


def test_profit_factor_only_winning_trades_is_infinite():
    trades = [
        Trade(datetime(2024, 1, 1), "buy", 100.0, 1.0, 0.0, 0.0),
        Trade(datetime(2024, 1, 2), "sell", 110.0, 1.0, 0.0, 110.0),
    ]
    assert profit_factor(trades) == float("inf")


def test_profit_factor_mixed_trades():
    trades = [
        Trade(datetime(2024, 1, 1), "buy", 100.0, 1.0, 0.0, 0.0),
        Trade(datetime(2024, 1, 2), "sell", 120.0, 1.0, 0.0, 120.0),
        Trade(datetime(2024, 1, 3), "buy", 120.0, 1.0, 0.0, 0.0),
        Trade(datetime(2024, 1, 4), "sell", 110.0, 1.0, 0.0, 110.0),
    ]
    # Ganho de 20 no primeiro par, perda de 10 no segundo par.
    assert profit_factor(trades) == pytest.approx(2.0)
