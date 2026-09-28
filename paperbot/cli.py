from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from .config import StrategyConfig
from .data import fetch_ohlcv
from .engine import run_backtest
from .portfolio import PaperPortfolio
from .strategy import SmaCrossRsiStrategy
from .validation import buy_and_hold_return_pct, profit_factor, sharpe_ratio


def _build_strategy(args: argparse.Namespace) -> SmaCrossRsiStrategy:
    config = StrategyConfig(
        fast_period=args.fast,
        slow_period=args.slow,
        rsi_period=args.rsi_period,
        rsi_overbought=args.rsi_overbought,
        stop_loss_pct=args.stop_loss,
    )
    return SmaCrossRsiStrategy(config)


def cmd_backtest(args: argparse.Namespace) -> None:
    ohlcv = fetch_ohlcv(args.exchange, args.symbol, args.timeframe, args.days)
    if ohlcv.empty:
        print("Sem dados de mercado devolvidos pela exchange.")
        return

    strategy = _build_strategy(args)
    result = run_backtest(ohlcv, strategy, initial_cash=args.cash, fee_rate=args.fee)

    print(f"Par: {args.symbol}  Timeframe: {args.timeframe}  Periodo: {args.days} dias")
    print(f"Capital inicial:  {args.cash:.2f}")
    print(f"Capital final:    {result.final_equity:.2f}")
    print(f"Retorno total:    {result.total_return_pct:.2f}%")
    print(f"Max drawdown:     {result.max_drawdown_pct:.2f}%")
    print(f"Numero de trades: {result.num_trades}")
    print(f"Win rate:         {result.win_rate_pct:.2f}%")


def cmd_validate(args: argparse.Namespace) -> None:
    symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    days_list = [int(d.strip()) for d in args.days_list.split(",") if d.strip()]
    strategy = _build_strategy(args)

    rows = []
    for symbol in symbols:
        for days in days_list:
            ohlcv = fetch_ohlcv(args.exchange, symbol, args.timeframe, days)
            if len(ohlcv) < 2:
                print(f"Sem dados suficientes para {symbol} / {days}d, a saltar.")
                continue

            result = run_backtest(ohlcv, strategy, initial_cash=args.cash, fee_rate=args.fee)
            bh_return = buy_and_hold_return_pct(ohlcv)
            rows.append(
                {
                    "symbol": symbol,
                    "days": days,
                    "strategy_return_pct": result.total_return_pct,
                    "buy_hold_return_pct": bh_return,
                    "beats_buy_hold": result.total_return_pct > bh_return,
                    "max_drawdown_pct": result.max_drawdown_pct,
                    "sharpe": sharpe_ratio(result.equity_curve, args.timeframe),
                    "profit_factor": profit_factor(result.trades),
                    "num_trades": result.num_trades,
                    "win_rate_pct": result.win_rate_pct,
                }
            )

    if not rows:
        print("Nenhum resultado obtido -- verifica os simbolos e o timeframe.")
        return

    header = (
        f"{'Par':<10}{'Dias':>6}{'Estrategia':>12}{'BuyHold':>10}"
        f"{'BateB&H':>9}{'MaxDD':>9}{'Sharpe':>8}{'ProfFac':>9}{'Trades':>8}{'WinRate':>9}"
    )
    print(header)
    print("-" * len(header))

    wins = 0
    for r in rows:
        beats = "SIM" if r["beats_buy_hold"] else "nao"
        wins += 1 if r["beats_buy_hold"] else 0
        pf_display = "inf" if r["profit_factor"] == float("inf") else f"{r['profit_factor']:.2f}"
        print(
            f"{r['symbol']:<10}{r['days']:>6}{r['strategy_return_pct']:>11.2f}%"
            f"{r['buy_hold_return_pct']:>9.2f}%{beats:>9}{r['max_drawdown_pct']:>8.2f}%"
            f"{r['sharpe']:>8.2f}{pf_display:>9}{r['num_trades']:>8}{r['win_rate_pct']:>8.2f}%"
        )

    print("-" * len(header))
    print(f"Bateu buy-and-hold em {wins}/{len(rows)} testes ({wins / len(rows) * 100:.1f}%).")
    print(
        "Aviso: bater buy-and-hold nalguns testes nao prova lucro futuro. "
        "Olha para a consistencia entre pares/periodos, nao para um unico resultado bom, "
        "e nunca uses isto como garantia antes de arriscar dinheiro real."
    )


def cmd_live(args: argparse.Namespace) -> None:
    print("MODO SIMULACAO (paper trading) -- nenhuma ordem real e enviada a exchange.")
    state_path = Path(args.state_file)

    if state_path.exists():
        state = json.loads(state_path.read_text())
        portfolio = PaperPortfolio(cash=state["cash"], fee_rate=args.fee)
        portfolio.position_amount = state["position_amount"]
        portfolio.entry_price = state["entry_price"]
        print(f"Estado restaurado de {state_path}")
    else:
        portfolio = PaperPortfolio(cash=args.cash, fee_rate=args.fee)

    strategy = _build_strategy(args)

    try:
        while True:
            ohlcv = fetch_ohlcv(args.exchange, args.symbol, args.timeframe, args.warmup_days)
            df = strategy.compute_indicators(ohlcv).reset_index(drop=True)

            if len(df) < 2:
                time.sleep(args.interval)
                continue

            i = len(df) - 1
            signal = strategy.generate_signal(df, i, portfolio.in_position, portfolio.entry_price)
            price = float(df.iloc[i]["close"])
            timestamp = df.iloc[i]["timestamp"]

            if signal == "buy":
                portfolio.buy(timestamp, price)
                print(f"[{timestamp}] COMPRA simulada a {price:.2f}")
            elif signal == "sell":
                portfolio.sell(timestamp, price)
                print(f"[{timestamp}] VENDA simulada a {price:.2f}")

            equity = portfolio.equity(price)
            print(
                f"[{timestamp}] preco={price:.2f} equity={equity:.2f} "
                f"cash={portfolio.cash:.2f} posicao={portfolio.position_amount:.6f}"
            )

            state_path.write_text(
                json.dumps(
                    {
                        "cash": portfolio.cash,
                        "position_amount": portfolio.position_amount,
                        "entry_price": portfolio.entry_price,
                    }
                )
            )

            time.sleep(args.interval)
    except KeyboardInterrupt:
        print(f"Paragem manual. Estado guardado em {state_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paperbot",
        description="Bot de paper trading de criptomoedas (simulacao, sem dinheiro real).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--exchange", default="binance")
    common.add_argument("--symbol", default="BTC/USDT")
    common.add_argument("--timeframe", default="1h")
    common.add_argument("--fast", type=int, default=20)
    common.add_argument("--slow", type=int, default=50)
    common.add_argument("--rsi-period", type=int, default=14)
    common.add_argument("--rsi-overbought", type=float, default=70.0)
    common.add_argument("--stop-loss", type=float, default=0.05)
    common.add_argument("--cash", type=float, default=10_000.0)
    common.add_argument("--fee", type=float, default=0.001)

    backtest_parser = sub.add_parser("backtest", parents=[common], help="Corre um backtest historico.")
    backtest_parser.add_argument("--days", type=int, default=180)
    backtest_parser.set_defaults(func=cmd_backtest)

    validate_parser = sub.add_parser(
        "validate",
        parents=[common],
        help="Compara a estrategia com buy-and-hold em varios pares/periodos, para testar robustez.",
    )
    validate_parser.add_argument(
        "--symbols", default="BTC/USDT,ETH/USDT", help="Lista de pares separados por virgula."
    )
    validate_parser.add_argument(
        "--days-list", default="90,180,365", help="Lista de periodos (dias) separados por virgula."
    )
    validate_parser.set_defaults(func=cmd_validate)

    live_parser = sub.add_parser(
        "live", parents=[common], help="Corre em loop, simulando trades em tempo real (sem dinheiro real)."
    )
    live_parser.add_argument("--interval", type=int, default=300, help="Segundos entre iteracoes.")
    live_parser.add_argument(
        "--warmup-days", type=int, default=30, help="Dias de historico pedidos em cada iteracao."
    )
    live_parser.add_argument("--state-file", default="paperbot_state.json")
    live_parser.set_defaults(func=cmd_live)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
