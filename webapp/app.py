from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, render_template, request

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from paperbot.data import fetch_latest_price, fetch_ohlcv  # noqa: E402
from paperbot.dca import DcaConfig, run_dca_backtest  # noqa: E402
from paperbot.risk import (  # noqa: E402
    classify_risk,
    positive_window_pct,
    price_max_drawdown_pct,
    price_volatility_pct,
)

app = Flask(__name__)

EXCHANGE = "binance"
DEFAULT_TICKER_SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT"]


@app.route("/")
def index():
    tickers = []
    for symbol in DEFAULT_TICKER_SYMBOLS:
        try:
            price = fetch_latest_price(EXCHANGE, symbol)
            tickers.append({"symbol": symbol, "price": price, "error": None})
        except Exception as exc:  # exchange indisponivel, rede em baixo, etc.
            tickers.append({"symbol": symbol, "price": None, "error": str(exc)})
    return render_template("index.html", tickers=tickers, exchange=EXCHANGE)


@app.route("/dca")
def dca():
    symbols_param = request.args.get("symbols", "BTC/USDT,ETH/USDT,SOL/USDT")
    days = int(request.args.get("days", 180))
    installments = int(request.args.get("installments", 12))
    cash = float(request.args.get("cash", 10_000))

    symbols = [s.strip() for s in symbols_param.split(",") if s.strip()]
    rows = []
    chart_data = None

    for symbol in symbols:
        try:
            ohlcv = fetch_ohlcv(EXCHANGE, symbol, "1d", days)
            if len(ohlcv) < installments:
                rows.append({"symbol": symbol, "error": "Dados insuficientes para este periodo."})
                continue

            config = DcaConfig(total_capital=cash, num_installments=installments)
            result = run_dca_backtest(ohlcv, config)
            rows.append(
                {
                    "symbol": symbol,
                    "dca_return_pct": result.total_return_pct,
                    "lump_sum_return_pct": result.lump_sum_return_pct,
                    "beats_lump_sum": result.beats_lump_sum,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "error": None,
                }
            )

            if chart_data is None:
                chart_data = {
                    "symbol": symbol,
                    "labels": [ts.strftime("%Y-%m-%d") for ts in result.equity_curve.index],
                    "dca_values": [round(v, 2) for v in result.equity_curve.tolist()],
                    "lump_sum_values": [round(v, 2) for v in result.lump_sum_equity_curve.tolist()],
                }
        except Exception as exc:
            rows.append({"symbol": symbol, "error": str(exc)})

    return render_template(
        "dca.html",
        rows=rows,
        chart_data=chart_data,
        symbols_param=symbols_param,
        days=days,
        installments=installments,
        cash=cash,
    )


@app.route("/risk")
def risk():
    symbols_param = request.args.get("symbols", "BTC/USDT,ETH/USDT,SOL/USDT,BNB/USDT")
    days = int(request.args.get("days", 365))
    window = int(request.args.get("window", 7))

    symbols = [s.strip() for s in symbols_param.split(",") if s.strip()]
    rows = []

    for symbol in symbols:
        try:
            ohlcv = fetch_ohlcv(EXCHANGE, symbol, "1d", days)
            if len(ohlcv) < 2:
                rows.append({"symbol": symbol, "error": "Dados insuficientes para este periodo."})
                continue
            volatility_pct = price_volatility_pct(ohlcv, "1d")
            max_drawdown_pct = price_max_drawdown_pct(ohlcv)
            rows.append(
                {
                    "symbol": symbol,
                    "volatility_pct": volatility_pct,
                    "max_drawdown_pct": max_drawdown_pct,
                    "positive_window_pct": positive_window_pct(ohlcv, window=window),
                    "risk_level": classify_risk(volatility_pct, max_drawdown_pct),
                    "error": None,
                }
            )
        except Exception as exc:
            rows.append({"symbol": symbol, "error": str(exc)})

    return render_template(
        "risk.html",
        rows=rows,
        symbols_param=symbols_param,
        days=days,
        window=window,
    )


def main() -> None:
    # debug=False: isto corre sem consola em segundo plano via Task Scheduler
    # (ver scripts/setup_windows.ps1); usa --debug para o modo de desenvolvimento.
    debug = "--debug" in sys.argv
    app.run(host="127.0.0.1", port=5000, debug=debug)


if __name__ == "__main__":
    main()
