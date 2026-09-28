from datetime import datetime

import pytest

from paperbot.portfolio import PaperPortfolio


def test_buy_reduces_cash_and_opens_position():
    p = PaperPortfolio(cash=1000.0, fee_rate=0.0)
    p.buy(datetime(2024, 1, 1), price=100.0, fraction=1.0)
    assert p.in_position
    assert p.position_amount == 10.0
    assert p.cash == 0.0


def test_buy_applies_fee():
    p = PaperPortfolio(cash=1000.0, fee_rate=0.01)
    p.buy(datetime(2024, 1, 1), price=100.0, fraction=1.0)
    assert p.position_amount == pytest.approx(9.9)


def test_sell_closes_position_and_returns_cash():
    p = PaperPortfolio(cash=1000.0, fee_rate=0.0)
    p.buy(datetime(2024, 1, 1), price=100.0, fraction=1.0)
    p.sell(datetime(2024, 1, 2), price=110.0)
    assert not p.in_position
    assert p.cash == pytest.approx(1100.0)


def test_second_buy_while_in_position_is_ignored():
    p = PaperPortfolio(cash=1000.0, fee_rate=0.0)
    p.buy(datetime(2024, 1, 1), price=100.0, fraction=1.0)
    p.buy(datetime(2024, 1, 2), price=50.0, fraction=1.0)
    assert p.entry_price == 100.0


def test_sell_without_position_is_noop():
    p = PaperPortfolio(cash=1000.0, fee_rate=0.0)
    p.sell(datetime(2024, 1, 1), price=100.0)
    assert p.cash == 1000.0
    assert not p.in_position
