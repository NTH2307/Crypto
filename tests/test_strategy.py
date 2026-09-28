import pandas as pd

from paperbot.config import StrategyConfig
from paperbot.strategy import SmaCrossRsiStrategy


def _make_df():
    return pd.DataFrame(
        {
            "close": [10.0, 10.0, 10.0, 10.0],
            "sma_fast": [5.0, 4.0, 6.0, 7.0],
            "sma_slow": [5.0, 5.0, 5.0, 5.0],
            "rsi": [50.0, 50.0, 50.0, 50.0],
        }
    )


def test_cross_up_triggers_buy():
    strategy = SmaCrossRsiStrategy(StrategyConfig())
    df = _make_df()
    signal = strategy.generate_signal(df, i=2, in_position=False, entry_price=None)
    assert signal == "buy"


def test_cross_up_blocked_by_overbought_rsi():
    strategy = SmaCrossRsiStrategy(StrategyConfig(rsi_overbought=70.0))
    df = _make_df()
    df.loc[2, "rsi"] = 90.0
    signal = strategy.generate_signal(df, i=2, in_position=False, entry_price=None)
    assert signal == "hold"


def test_cross_down_triggers_sell_when_in_position():
    strategy = SmaCrossRsiStrategy(StrategyConfig())
    df = _make_df()
    df["sma_fast"] = [7.0, 6.0, 4.0, 3.0]
    signal = strategy.generate_signal(df, i=2, in_position=True, entry_price=10.0)
    assert signal == "sell"


def test_stop_loss_triggers_sell():
    strategy = SmaCrossRsiStrategy(StrategyConfig(stop_loss_pct=0.05))
    df = _make_df()
    df.loc[2, "close"] = 9.0
    signal = strategy.generate_signal(df, i=2, in_position=True, entry_price=10.0)
    assert signal == "sell"


def test_hold_without_signal():
    strategy = SmaCrossRsiStrategy(StrategyConfig())
    df = _make_df()
    df["sma_fast"] = [5.0, 5.0, 5.0, 5.0]
    signal = strategy.generate_signal(df, i=2, in_position=False, entry_price=None)
    assert signal == "hold"
