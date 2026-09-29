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
- **Validate**: compara a estratégia técnica com "buy and hold" em vários
  pares e períodos, para detetar se o resultado é consistente ou só sorte de
  um período específico.
- **DCA**: simula investir um capital dividido em parcelas iguais ao longo
  do tempo, e compara com "lump sum" (investir tudo de uma vez).
- **Dashboard web** (`webapp/`): página local com preços ao vivo e um gráfico
  comparando DCA vs lump sum — ver secção própria abaixo.
- **Live (simulado)**: corre em ciclo contínuo, busca o preço mais recente,
  aplica a estratégia técnica, e regista compras/vendas *simuladas* numa
  carteira virtual persistida em disco (`paperbot_state.json`). Nunca envia
  ordens à exchange.

## Sobre a estratégia técnica vs. DCA

A estratégia técnica (cruzamento de médias + RSI, abaixo) foi validada com o
comando `validate` contra vários pares/períodos e **perdeu consistentemente**
para "buy and hold" (só bateu em 2 de 9 testes, e mesmo nesses só porque
perdeu menos numa queda de mercado, não por lucro real). Isto está de acordo
com o que a literatura financeira mostra em geral: estratégias técnicas
simples raramente batem buy-and-hold depois de fees, sobretudo em mercados
com tendências fortes.

Por isso, para quem quer algo mais simples e com melhor histórico de
resultados, o comando `dca` (Dollar Cost Averaging — investir um valor fixo
a intervalos regulares, sem tentar cronometrar o mercado) é a abordagem
recomendada neste projeto. Não bate sempre "lump sum" (investir tudo já),
mas reduz o risco de entrares com tudo mesmo antes de uma queda — é uma
ferramenta de gestão de risco, não de tentar bater o mercado.

## Estratégia técnica por omissão

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

### Risco (indicadores históricos, não previsões)

```bash
python -m paperbot risk --symbols BTC/USDT,ETH/USDT,SOL/USDT --days 365
```

Mostra, por par: volatilidade anualizada, pior queda histórica (peak-to-
trough) e percentagem de janelas de N candles com retorno positivo, todos
calculados sobre o período pedido. Servem para avaliares o risco que
estarias a assumir — não para prever se vai subir ou descer a seguir.

### DCA (recomendado)

```bash
python -m paperbot dca --symbol BTC/USDT --timeframe 1d --days 365 \
    --cash 10000 --installments 12
```

Divide os 10000 em 12 parcelas espaçadas ao longo dos últimos 365 dias,
compra a cada parcela ao preço de fecho desse dia, e compara o resultado
final com teres investido os 10000 de uma vez só no primeiro dia (lump
sum).

Exemplo de saída:

```
Par: BTC/USDT  Timeframe: 1d  Periodo: 365 dias
Capital total:           10000.00
Parcelas:                12
Custo medio por unidade: 61234.5678
Valor final (DCA):       11820.44
Retorno DCA:             18.20%
Valor final (lump sum):  13500.12
Retorno lump sum:        35.00%
DCA bateu lump sum:      nao
```

Não é garantido que o DCA bata lump sum (normalmente não bate em mercados a
subir de forma constante) — a vantagem do DCA é reduzir o risco de entrares
com tudo mesmo antes de uma queda grande, não maximizar o retorno esperado.

### DCA — validação em vários pares/períodos

Tal como a estratégia técnica, um único teste de DCA não prova nada. Usa
`dca-validate` para ver a consistência em vários pares e períodos:

```bash
python -m paperbot dca-validate \
    --symbols BTC/USDT,ETH/USDT,SOL/USDT \
    --days-list 90,180,365 \
    --installments 12
```

Mostra, para cada combinação, o retorno do DCA vs. lump sum, se bateu ou
não, e o drawdown máximo — o que importa aqui não é "ganhar" em todos os
testes, mas ver se o drawdown é consistentemente mais controlado.

### DCA — modo live (simulado, sem dinheiro real)

Compra uma parcela fixa a cada N dias, indefinidamente, e guarda o estado
em disco:

```bash
python -m paperbot dca-live --symbol BTC/USDT --contribution 100 \
    --interval-days 7 --check-interval 3600
```

Isto verifica a cada hora (`--check-interval` em segundos) se já passaram
`--interval-days` desde a última compra simulada; se sim, "compra" ao preço
atual. Nunca envia ordens reais. O estado fica em `dca_state.json` (podes
mudar com `--state-file`), por isso podes parar (`Ctrl+C`) e retomar depois
sem perder o histórico.

### Backtest (estratégia técnica)

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

## Dashboard web

Uma página local (não publicada online) com três vistas:

- **Preços** (`/`) — preços ao vivo de alguns pares (BTC, ETH, SOL, BNB),
  dados públicos via ccxt.
- **Risco** (`/risk`) — volatilidade anualizada, pior queda histórica e
  consistência de tendência por par, no período escolhido. São factos sobre
  o passado, não previsões — a página explica isso de forma explícita.
- **DCA vs Lump Sum** (`/dca`) — tabela comparando DCA com lump sum em vários
  pares, mais um gráfico da evolução do valor investido ao longo do tempo.

Em todas, os parâmetros (pares, dias, etc.) são ajustáveis no formulário da
própria página.

Corre manualmente com:

```bash
python webapp/app.py
```

Depois abre `http://127.0.0.1:5000` no browser. Corre só na tua máquina —
não é um serviço público nem guarda nada permanentemente. Os dados são
sempre em tempo real: cada vez que abres uma página, ela vai buscar os
preços e recalcula os indicadores nesse momento — não há um "refresh diário"
à espera, nem é preciso.

### Arranque automático no Windows (atalhos no ambiente de trabalho)

Para não teres de abrir o PowerShell todas as vezes:

```powershell
.\scripts\setup_windows.ps1
```

Isto:
- Cria um atalho na pasta de Arranque do Windows (`shell:startup`) que
  arranca o dashboard sozinho sempre que inicias sessão (sem janela de
  consola visível, e sem precisar de privilégios de Administrador).
- Arranca o dashboard imediatamente, sem esperares pelo próximo login.
- Cria 3 atalhos no ambiente de trabalho: **Crypto - Preços**, **Crypto -
  Risco**, **Crypto - DCA vs Lump Sum**.

Para desfazer tudo isto (remover o arranque automático e os atalhos):

```powershell
.\scripts\remove_windows_setup.ps1
```

> Esta página **mostra dados de simulações e histórico de mercado**. Não
> gera recomendações de "onde investir" nem qualquer tipo de sinal de
> compra/venda automático — é uma visualização dos resultados que já
> obténs pela linha de comandos, nada mais.

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
  dca.py         # simulação de DCA vs lump sum
  validation.py  # buy-and-hold, Sharpe, profit factor
  risk.py        # volatilidade, pior queda, consistência (históricos)
  cli.py         # interface de linha de comandos
webapp/
  app.py         # dashboard Flask local
  templates/
  static/
scripts/
  setup_windows.ps1         # arranque automático + atalhos no ambiente de trabalho
  remove_windows_setup.ps1  # desfaz o setup_windows.ps1
tests/
```

## Ir além disto (aviso)

Este projeto foi deliberadamente construído **só em modo simulação**. Ligar
isto a uma exchange real com chaves de API e dinheiro verdadeiro é uma
decisão à parte, com risco financeiro direto — não faças essa alteração sem
teres validado a estratégia extensivamente em backtest e em paper trading, e
sem perceberes bem os riscos (falhas de rede, slippage, bugs no código a
executarem ordens reais, etc.).
