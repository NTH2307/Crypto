import pandas as pd

from paperbot.indicators import rsi, sma


def test_sma_basic():
    s = pd.Series([1, 2, 3, 4, 5])
    result = sma(s, 2)
    assert pd.isna(result.iloc[0])
    assert result.iloc[1] == 1.5
    assert result.iloc[-1] == 4.5


def test_rsi_all_gains_is_100():
    s = pd.Series(range(1, 30))
    result = rsi(s, period=14)
    assert result.iloc[-1] == 100.0


def test_rsi_all_losses_is_0():
    s = pd.Series(range(30, 1, -1))
    result = rsi(s, period=14)
    assert result.iloc[-1] == 0.0
