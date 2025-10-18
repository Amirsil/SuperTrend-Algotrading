# 🚀 Project: Supertrend Alpaca Trading Bot

## 🧩 Goal
Create a full Python trading bot project that replicates the following TradingView Supertrend strategy, connects to Alpaca for live/paper trading, includes a pandas-based backtester, and compares results to buy-and-hold performance.

---

## 📜 Original TradingView Supertrend Strategy
```pine
//@version=4
strategy("Supertrend Strategy", overlay=true, format=format.price, precision=2, initial_capital=10000, default_qty_type=strategy.percent_of_equity, default_qty_value=10)

Periods = input(title="ATR Period", type=input.integer, defval=10)
src = input(hl2, title="Source")
Multiplier = input(title="ATR Multiplier", type=input.float, step=0.1, defval=3.0)
changeATR = input(title="Change ATR Calculation Method ?", type=input.bool, defval=true)

atr2 = sma(tr, Periods)
atr = changeATR ? atr(Periods) : atr2

up = src - (Multiplier * atr)
up1 = nz(up[1], up)
up := close[1] > up1 ? max(up, up1) : up

dn = src + (Multiplier * atr)
dn1 = nz(dn[1], dn)
dn := close[1] < dn1 ? min(dn, dn1) : dn

trend = 1
trend := nz(trend[1], trend)
trend := trend == -1 and close > dn1 ? 1 : trend == 1 and close < up1 ? -1 : trend

// Signals
buySignal = trend == 1 and trend[1] == -1
sellSignal = trend == -1 and trend[1] == 1

// Plotting
upPlot = plot(trend == 1 ? up : na, title="Up Trend", style=plot.style_linebr, linewidth=2, color=color.green)
dnPlot = plot(trend == -1 ? dn : na, title="Down Trend", style=plot.style_linebr, linewidth=2, color=color.red)

// Strategy entries and exits
if (buySignal)
    strategy.entry("Long", strategy.long)

if (sellSignal)
    strategy.close("Long")
    strategy.entry("Short", strategy.short)

if (buySignal)
    strategy.close("Short")

// Optional: signals on chart
showsignals = input(title="Show Buy/Sell Signals ?", type=input.bool, defval=true)
plotshape(buySignal and showsignals ? up : na, title="Buy", text="Buy", location=location.absolute, style=shape.labelup, size=size.tiny, color=color.green, textcolor=color.white)
plotshape(sellSignal and showsignals ? dn : na, title="Sell", text="Sell", location=location.absolute, style=shape.labeldown, size=size.tiny, color=color.red, textcolor=color.white)
```

## 🏗️ Folder Structure


supertrend-alpaca-bot/
│
├── main.py
├── config.json
├── requirements.txt
├── Makefile
│
├── core/
│   ├── supertrend.py
│   ├── strategy.py
│   ├── alpaca_trader.py
│   ├── backtest.py
│   └── compare.py
│
└── tests/
    ├── test_supertrend.py
    ├── test_strategy.py
    └── test_backtest.py
⚙️ Implementation Details
1️⃣ core/supertrend.py
Implement a vectorized Supertrend calculator using pandas (inputs: dataframe with columns ['high', 'low', 'close'], period, multiplier).
Output: dataframe with columns ['supertrend', 'trend', 'buy_signal', 'sell_signal'].

2️⃣ core/strategy.py
Generate trade signals from Supertrend output:

Return list of (timestamp, signal, price)

Optionally integrate stop-loss or take-profit later

3️⃣ core/backtest.py
Implement a backtester:

Inputs: OHLCV DataFrame, signals, initial capital

Simulate buy/sell trades

Calculate metrics:

Total Return

Max Drawdown

Win Rate

Sharpe Ratio

Number of trades

Plot equity curve vs buy-and-hold

4️⃣ core/compare.py
Run both:

Supertrend backtest

Buy-and-hold benchmark
Print summary + plot side-by-side performance.

5️⃣ core/alpaca_trader.py
Connect to Alpaca API using alpaca-trade-api

Support:

Paper trading (via paper API keys)

Live trading (via live keys)

Periodically check latest candle and update position according to signals.

6️⃣ main.py
Add a CLI interface:

bash
Copy code
python main.py --backtest SYMBOL START_DATE END_DATE
python main.py --compare SYMBOL
python main.py --paper SYMBOL
python main.py --live SYMBOL
7️⃣ config.json
Basic configuration:

json
Copy code
{
  "alpaca_api_key": "YOUR_KEY",
  "alpaca_secret_key": "YOUR_SECRET",
  "base_url": "https://paper-api.alpaca.markets",
  "initial_capital": 10000,
  "atr_period": 10,
  "atr_multiplier": 3.0,
  "symbol": "AAPL"
}
8️⃣ requirements.txt
nginx
Copy code
pandas
numpy
matplotlib
yfinance
alpaca-trade-api
pytest
9️⃣ Makefile
yaml
Copy code
install:
	pip install -r requirements.txt

test:
	pytest tests/

backtest:
	python main.py --backtest AAPL 2022-01-01 2024-01-01

compare:
	python main.py --compare AAPL
🔟 tests/
Use pytest to test:

ATR correctness

Signal generation

Backtest output reproducibility

📊 Backtest Report Example
Print metrics:

yaml
Copy code
Strategy Return: 48.3%
Buy & Hold Return: 31.7%
Sharpe Ratio: 1.12
Max Drawdown: -12.5%
Win Rate: 57%
Number of Trades: 26
Plot:

Candles + Supertrend lines

Buy/Sell markers

Equity curve vs buy-and-hold

🧪 Expected Usage
bash
Copy code
make install
python main.py --backtest AAPL 2022-01-01 2024-01-01
python main.py --compare AAPL
pytest tests/
🧠 Bonus (optional)
If possible, allow a flag --engine backtrader to run using the backtrader library for advanced metrics.


also for alpaca trading - 

API_KEY = "PK9YD1BMM2113S9R3COI"
API_SECRET = "t5ijHKJ12eiSDKkuzj6DjjrfXAIcVhGNbCrnu5V2"
BASE_URL = "https://paper-api.alpaca.markets"


