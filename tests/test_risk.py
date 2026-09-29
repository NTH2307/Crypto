import pandas as pd
import pytest

from paperbot.risk import positive_window_pct, price_max_drawdown_pct, price_volatility_pct


def _make_ohlcv(closes):
    return pd.DataFrame({"close": closes})


def test_price_volatility_zero_for_flat_price():
    ohlcv = _make_ohlcv([100.0] * 10)
    assert price_volatility_pct(ohlcv, "1d") == 0.0


def test_price_volatility_positive_for_moving_price():
    ohlcv = _make_ohlcv([100.0, 105.0, 98.0, 110.0, 90.0, 115.0])
    assert price_volatility_pct(ohlcv, "1d") > 0


def test_price_max_drawdown_zero_for_monotonically_rising_price():
    ohlcv = _make_ohlcv([100.0, 110.0, 120.0, 130.0])
    assert price_max_drawdown_pct(ohlcv) == 0.0


def test_price_max_drawdown_captures_peak_to_trough():
    ohlcv = _make_ohlcv([100.0, 200.0, 100.0, 150.0])
    # Pico 200, minimo seguinte 100 -> queda de 50%.
    assert price_max_drawdown_pct(ohlcv) == pytest.approx(-50.0)


def test_positive_window_pct_all_positive():
    # 3 janelas de 2 candles, todas a subir.
    ohlcv = _make_ohlcv([100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0])
    assert positive_window_pct(ohlcv, window=2) == pytest.approx(100.0)


def test_positive_window_pct_mixed():
    # janela 1: 100 -> 90 (negativa), janela 2: 90 -> 120 (positiva)
    ohlcv = _make_ohlcv([100.0, 95.0, 90.0, 105.0, 120.0])
    assert positive_window_pct(ohlcv, window=2) == pytest.approx(50.0)


def test_positive_window_pct_not_enough_data():
    ohlcv = _make_ohlcv([100.0, 105.0])
    assert positive_window_pct(ohlcv, window=7) == 0.0
