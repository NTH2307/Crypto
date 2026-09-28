from __future__ import annotations

import pandas as pd


def fetch_ohlcv(
    exchange_id: str,
    symbol: str,
    timeframe: str,
    since_days: int,
    limit_per_call: int = 1000,
) -> pd.DataFrame:
    """Descarrega candles OHLCV públicos (sem chaves de API) via ccxt."""
    import ccxt

    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({"enableRateLimit": True})

    since = exchange.milliseconds() - since_days * 24 * 60 * 60 * 1000
    all_candles: list = []

    while True:
        candles = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since, limit=limit_per_call)
        if not candles:
            break
        all_candles.extend(candles)
        last_ts = candles[-1][0]
        if last_ts <= since:
            break
        since = last_ts + 1
        if len(candles) < limit_per_call:
            break

    df = pd.DataFrame(all_candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
        df = df.drop_duplicates(subset="timestamp").sort_values("timestamp").reset_index(drop=True)
    return df


def fetch_latest_price(exchange_id: str, symbol: str) -> float:
    import ccxt

    exchange_class = getattr(ccxt, exchange_id)
    exchange = exchange_class({"enableRateLimit": True})
    ticker = exchange.fetch_ticker(symbol)
    return float(ticker["last"])
