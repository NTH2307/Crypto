# crypto-paper-trader

Bot de **paper trading** (simulação) de criptomoedas. Lê dados de mercado
reais através da [ccxt](https://github.com/ccxt/ccxt) (por omissão, Binance,
via endpoints públicos, sem necessidade de chaves de API), aplica uma
estratégia técnica e simula compras/vendas contra uma carteira virtual.

> ⚠️ **Isto NÃO executa ordens reais em nenhuma exchange e NÃO é
> aconselhamento financeiro.** É uma ferramenta de simulação e
> aprendizagem. O desempenho passado (num backtest ou em paper trading) não
> garante qualquer resultado futuro. Trading de criptomoedas com dinheiro
> real implica risco de perda total do capital. Usa isto por tua conta e
> risco.

## O que faz

- **Backtest**: descarrega histórico de candles (OHLCV) e simula a
  estratégia sobre esse período, devolvendo retorno total, drawdown máximo,
  número de trades e win rate.
- **Live (simulado)**: corre em ciclo contínuo, busca o preço mais recente,
  aplica a mesma estratégia, e regista compras/vendas *simuladas* numa
  carteira virtual persistida em disco (`paperbot_state.json`). Nunca envia
  ordens à exchange.

## Estratégia por omissão

Cruzamento de médias móveis simples (SMA rápida vs. SMA lenta) filtrado por
RSI, com stop-loss percentual:

- **Compra**: a SMA rápida cruza para cima da SMA lenta, e o RSI está abaixo
  do limiar de sobrecompra (por omissão 70).
- **Venda**: a SMA rápida cruza para baixo da SMA lenta, **ou** o preço cai
  abaixo do stop-loss definido a partir do preço de entrada (por omissão
  5%).

Todos estes parâmetros são configuráveis por linha de comandos.

## Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Uso

### Backtest

```bash
python -m paperbot backtest --symbol BTC/USDT --timeframe 1h --days 180 \
    --fast 20 --slow 50 --rsi-period 14 --cash 10000
```

Exemplo de saída:

```
Par: BTC/USDT  Timeframe: 1h  Periodo: 180 dias
Capital inicial: 10000.00
Capital final:   11342.18
Retorno total:   13.42%
Max drawdown:    -8.71%
Numero de trades: 14
Win rate:        57.14%
```

### Validação (comparação com buy-and-hold em vários pares/períodos)

Um único backtest não prova que a estratégia é boa — pode ter sido sorte do
período. O comando `validate` corre a mesma estratégia sobre vários pares e
vários períodos, e compara sempre com "buy and hold" (comprar no início e
segurar até ao fim), que é a referência mínima que uma estratégia ativa tem
de bater para justificar a complexidade extra.

```bash
python -m paperbot validate \
    --symbols BTC/USDT,ETH/USDT,SOL/USDT \
    --days-list 90,180,365 \
    --timeframe 1h
```

Para cada combinação par/período mostra o retorno da estratégia, o retorno
de buy-and-hold, se bateu ou não, drawdown máximo, Sharpe ratio anualizado,
profit factor, número de trades e win rate, terminando com um resumo de em
quantos testes a estratégia bateu buy-and-hold.

Isto ainda **não é prova de lucro futuro** — é só um filtro melhor do que
olhar para um único número. Uma estratégia que só bate buy-and-hold num
período específico, mas não nos outros, está provavelmente sobreajustada
(overfitted) a esse período.

### Live (simulado, sem dinheiro real)

```bash
python -m paperbot live --symbol BTC/USDT --timeframe 5m --interval 300
```

Corre indefinidamente (`Ctrl+C` para parar), imprime o preço e o estado da
carteira virtual a cada iteração, e guarda o estado em
`paperbot_state.json` para poder retomar depois.

## Testes

```bash
pytest
```

Os testes cobrem os indicadores técnicos, a contabilidade da carteira
virtual e a lógica de geração de sinais — não fazem chamadas de rede.

## Estrutura

```
paperbot/
  config.py      # parâmetros da estratégia
  data.py        # obtenção de OHLCV via ccxt (dados públicos)
  indicators.py  # SMA, EMA, RSI
  strategy.py    # lógica de sinais (compra/venda/hold)
  portfolio.py   # carteira virtual (cash, posição, trades)
  engine.py      # motor de backtest
  cli.py         # interface de linha de comandos
tests/
```

## Ir além disto (aviso)

Este projeto foi deliberadamente construído **só em modo simulação**. Ligar
isto a uma exchange real com chaves de API e dinheiro verdadeiro é uma
decisão à parte, com risco financeiro direto — não faças essa alteração sem
teres validado a estratégia extensivamente em backtest e em paper trading, e
sem perceberes bem os riscos (falhas de rede, slippage, bugs no código a
executarem ordens reais, etc.).
