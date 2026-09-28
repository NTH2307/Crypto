import pandas as pd
import pytest

from paperbot.dca import DcaConfig, run_dca_backtest


def _make_ohlcv(closes):
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=len(closes), freq="D"),
            "close": closes,
        }
    )


def test_dca_invests_full_capital_no_fees():
    ohlcv = _make_ohlcv([100.0] * 12)
    config = DcaConfig(total_capital=1200.0, num_installments=12, fee_rate=0.0)
    result = run_dca_backtest(ohlcv, config)
    assert result.total_invested == pytest.approx(1200.0)
    assert result.total_units == pytest.approx(12.0)
    assert result.final_equity == pytest.approx(1200.0)
    assert result.total_return_pct == pytest.approx(0.0)


def test_dca_beats_lump_sum_in_a_falling_then_rising_market():
    # Preco cai a meio e recupera no fim: DCA compra mais barato a meio do caminho.
    closes = [100, 90, 80, 70, 60, 50, 60, 70, 80, 90, 100, 100]
    ohlcv = _make_ohlcv(closes)
    config = DcaConfig(total_capital=1200.0, num_installments=12, fee_rate=0.0)
    result = run_dca_backtest(ohlcv, config)
    assert result.beats_lump_sum


def test_dca_loses_to_lump_sum_in_a_steadily_rising_market():
    closes = [float(100 + i * 10) for i in range(12)]
    ohlcv = _make_ohlcv(closes)
    config = DcaConfig(total_capital=1200.0, num_installments=12, fee_rate=0.0)
    result = run_dca_backtest(ohlcv, config)
    assert not result.beats_lump_sum


def test_dca_applies_fees():
    ohlcv = _make_ohlcv([100.0] * 12)
    config = DcaConfig(total_capital=1200.0, num_installments=12, fee_rate=0.01)
    result = run_dca_backtest(ohlcv, config)
    assert result.total_return_pct < 0


def test_dca_max_drawdown_is_negative_when_price_dips_between_buys():
    # So ha compras no inicio e no fim; entre elas o preco sobe e depois cai,
    # criando um drawdown na posicao ja aberta.
    closes = [100.0, 100.0, 200.0, 100.0, 100.0]
    ohlcv = _make_ohlcv(closes)
    config = DcaConfig(total_capital=1200.0, num_installments=2, fee_rate=0.0)
    result = run_dca_backtest(ohlcv, config)
    assert result.max_drawdown_pct == pytest.approx(-50.0)


def test_dca_raises_when_not_enough_candles():
    ohlcv = _make_ohlcv([100.0] * 3)
    config = DcaConfig(total_capital=1200.0, num_installments=12, fee_rate=0.0)
    with pytest.raises(ValueError):
        run_dca_backtest(ohlcv, config)
