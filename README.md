# 📊 Orderbook Delta Momentum Strategy
**Test assignment for trading based on orderbook delta (Level 2) from Bybit exchange.**
This strategy identifies trade entry and exit points based on volume shifts in bid/ask sides. The project implements a full pipeline: data collection → signal generation → backtest → final report.

## 🚀 Quick Start

### 🔧 Install Dependencies

```bash
pip install \
  aiohttp>=3.8.0 \
  numpy>=1.24.0 \
  websockets>=11.0.3 \
  pandas>=2.0.0 \
  pyarrow>=12.0.0 \
  matplotlib>=3.7.0 \
  python-dateutil>=2.8.2
```

### ⚙️ Configuration (`config.py`)

```python
# Trading Parameters
SYMBOL = "ETHUSDT"       # Trading pair
TESTNET = True           # Use Bybit testnet
DELTA_THRESHOLD = 0.1    # Delta sensitivity

# Backtest Settings
INITIAL_BALANCE = 10000  # Starting capital (USD)
TRADE_QUANTITY = 0.1     # Trade volume (ETH)
MAX_ITERATIONS = 100     # Number of ticks to simulate
```

## 🔁 Workflow

```bash
python main.py
```

**Steps:**
1. Connect to Bybit Testnet
2. Fetch orderbook snapshots via REST API
3. Calculate delta between snapshots
4. Generate signals (BUY / SELL / HOLD)
5. Execute virtual trades
6. Print final strategy performance report

## ⚙️ Components

### Data Collection

* `bybit_client.py`, `bybit_adapter.py` — REST integration with Bybit
* Level 2 snapshot fetching: bids / asks
* Delta calculation engine

### Signal Generation

* `DeltaStrategy` — basic logic: if delta > threshold → BUY/SELL
* Threshold is configured in `config.py`

### Backtest

* `Backtester` — trade simulator using generated signals
* No slippage or fees assumed (simplified simulation)

### Reporting

* `ReportGenerator` — builds final performance report & metrics

## 📁 Project Structure

| File/Folder         | Purpose                             |
| ------------------- | ----------------------------------- |
| `main.py`           | Entry point, simulation loop        |
| `data_service.py`   | Orderbook fetching & delta logic    |
| `strategy_service.py`| Delta-based signal generation       |
| `backtest_service.py`| Trade execution simulator           |
| `handlers.py`       | Command handlers (CQRS)             |
| `contracts.py`      | Basic CQRS pattern implementation   |
| `bybit_*.py`        | REST adapters for Bybit API         |
| `report.py`         | Performance metrics and charts      |
| `config.py`         | Backtest and trade parameters       |

## 📊 Example Report

```
==================== RESEARCH REPORT ====================
Strategy: Orderbook Delta Momentum
Symbol: ETHUSDT
Timeframe: N/A
Total Iterations: 100
---------------------------------------------------------
Performance Metrics:
Initial Balance: $10000.00
Final Balance:   $10250.00
Position:        0.350000 ETH
Position Value:  $1050.00
Total Value:     $11300.00
PNL:             $1300.00
Total Trades:    15
---------------------------------------------------------
Conclusion: This research demonstrates a basic strategy
based on orderbook delta momentum. The strategy showed
a profit of $1300.00 over 100 iterations.
=========================================================
```

## 📉 Trade Visualization

Each trade is visualized on a bar chart:

![Trade Prices](./python/trade_prices.png)

* 🟩 Green bars — profitable trades
* 🟥 Red bars — losing trades
* X-axis — trade index
* Y-axis — entry price

You can quickly evaluate:
- Trade frequency and timing
- Profit/loss distribution
- Strategy consistency

### 📄 `trades_report.csv` — Raw Log of All Trades

Each row represents a trade event. Typical columns include:

| Column     | Description                            |
| ---------- | --------------------------------------- |
| timestamp  | Timestamp of the trade (or tick)       |
| signal     | BUY / SELL signal                      |
| price      | Entry price                            |
| position   | Direction: long / short (1 / -1)       |
| pnl        | Profit or loss                         |
| delta      | Delta value that triggered the signal  |

Optionally: `trade_id`, `position_size`, `exit_price`, `duration`, etc.

**Usage:**
- Enables charting (e.g. `trade_prices.png`)
- Useful for calculating metrics like winrate, average PnL, drawdown, etc.
- Easily importable into `pandas` or Excel

## 🧰 Dependencies

- Python 3.8+
- `aiohttp`, `websockets` — async network I/O
- `numpy`, `pandas`, `pyarrow` — data processing
- `matplotlib`, `python-dateutil` — charting and time parsing
