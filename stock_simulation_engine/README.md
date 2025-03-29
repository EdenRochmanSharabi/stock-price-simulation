# Stock Price Simulation with Regime Switching and Jump Diffusion

A comprehensive Monte Carlo simulation engine for stock price modeling with multiple simulation approaches, including Geometric Brownian Motion (GBM), Jump Diffusion, and a Hybrid model that combines GBM with regime switching and jumps.

## Table of Contents
- [Overview](#overview)
- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Usage](#usage)
  - [Single Stock Simulation](#single-stock-simulation)
  - [Multiple Stock Simulation](#multiple-stock-simulation)
  - [Web Interface](#web-interface)
- [Simulation Models](#simulation-models)
  - [Geometric Brownian Motion (GBM)](#geometric-brownian-motion-gbm)
  - [Jump Diffusion Model](#jump-diffusion-model)
  - [Hybrid Model](#hybrid-model)
- [Parameters](#parameters)
- [Outputs](#outputs)
  - [Data Files](#data-files)
  - [Visualizations](#visualizations)
  - [Reports](#reports)
- [Statistics & Analysis](#statistics--analysis)
- [Dependencies](#dependencies)

## Overview

This simulation engine allows you to model stock price movements using various stochastic processes. It can be used for risk assessment, option pricing, portfolio optimization, and scenario analysis.

## Directory Structure

```
stock_simulation_engine/
├── modules/                   # Core simulation modules
│   ├── __init__.py           # Package initialization
│   ├── base.py               # Base classes and utilities
│   ├── models.py             # Model implementations (GBM, Jump, Hybrid)
│   ├── analytics.py          # Statistics and visualization functions
│   └── engine.py             # Main simulation engine
├── templates/                 # HTML templates for reports
│   ├── static/               # Static assets for templates
│   └── index.html            # Main template for report generation
├── output/                    # Default output directory
│   ├── data/                 # Simulation data files
│   ├── graphs/               # Generated visualizations
│   └── reports/              # HTML reports
├── stock_simulation_main.py  # Simple entry point for single-stock simulation
├── web_interface.py          # Flask-based web interface
├── reporting.py              # Report generation functionality
├── sp500_tickers.py          # S&P 500 tickers and sector information
├── requirements.txt          # Project dependencies
└── README.md                 # This file
```

## Installation

1. Clone the repository
2. Install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Single Stock Simulation

To run a simulation for a single stock:

```python
from modules.engine import run_simulation

result = run_simulation(
    ticker="AAPL",
    model_type="combined",  # Options: "gbm", "jump", "combined"
    paths=1000,             # Number of simulation paths
    steps=21,               # Number of time steps (trading days)
    output_dir="output"     # Output directory
)
```

You can also run a simple simulation via command line:

```bash
python stock_simulation_main.py
```

### Multiple Stock Simulation

For simulating multiple stocks:

```python
from stock_simulation_engine.reporting import generate_multi_stock_report
from modules.engine import run_simulation
import os

tickers = ["AAPL", "MSFT", "AMZN"]
results = {}

for ticker in tickers:
    result = run_simulation(ticker, model_type="combined", paths=1000, steps=21)
    results[ticker] = result

# Generate a consolidated report
report_path = generate_multi_stock_report(results, "output/reports")
print(f"Generated multi-stock report: {report_path}")
```

### Web Interface

The package includes a web interface for easy interaction:

```bash
python web_interface.py
```

Navigate to http://localhost:5000 in your browser to access the web interface.

## Simulation Models

### Geometric Brownian Motion (GBM)

The standard model for stock price movements with constant drift and volatility.

### Jump Diffusion Model

Extends GBM by adding random jumps to model market shocks.

### Hybrid Model

Combines GBM, jump diffusion, and volatility clustering to create a more realistic model of stock price behavior.

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ticker` | str | - | Stock ticker symbol |
| `model_type` | str | "gbm" | Simulation model type ("gbm", "jump", or "combined") |
| `paths` | int | 1000 | Number of simulation paths |
| `steps` | int | 21 | Number of time steps (typically trading days) |
| `dt` | float | 1/252 | Time increment in years (default: one trading day) |
| `output_dir` | str | "output" | Base directory for output files |
| `reports_dir` | str | "{output_dir}/reports" | Directory for HTML reports |
| `graphs_dir` | str | "{output_dir}/graphs" | Directory for visualization files |
| `calibrate` | bool | True | Whether to calibrate model params from historical data |
| `lookback_period` | str | "2y" | Period for historical data (e.g., "1y", "2y", "5y") |
| `mu` | float | None | Drift parameter (annualized, calibrated if None) |
| `sigma` | float | None | Volatility parameter (annualized, calibrated if None) |
| `jump_intensity` | float | 10 | Average number of jumps per year |
| `jump_mean` | float | -0.01 | Mean jump size (proportional) |
| `jump_sigma` | float | 0.02 | Standard deviation of jump size |
| `vol_clustering` | float | 0.85 | Volatility regime clustering parameter |

## Outputs

### Data Files

Simulation data is saved in the `output/data/` directory:
- `{ticker}_simulation_data.json`: JSON file with simulation statistics
- `{ticker}_paths.csv`: CSV file with simulated price paths

### Visualizations

Charts are saved in the `output/graphs/` directory:
- Price paths chart
- Price distribution histogram
- Returns distribution histogram
- Probability cone chart
- Value at Risk (VaR) visualization

### Reports

HTML reports are generated in the `output/reports/` directory:
- Individual stock reports: `{ticker}_report.html`
- Multi-stock consolidated reports: `multi_stock_report_{timestamp}.html`

## Statistics & Analysis

The simulation calculates and provides the following statistics:

- **Price Statistics**: Mean, median, standard deviation, min/max, percentiles
- **Return Statistics**: Expected return, median return, return volatility
- **Risk Measures**: VaR (95% and 99%), maximum drawdown
- **Probability Metrics**: Profit/loss probability, probability of specific price movements
- **Statistical Measures**: Skewness, kurtosis, normality tests
- **Risk-Adjusted Metrics**: Sharpe ratio, Sortino ratio, confidence intervals

## Dependencies

- numpy: Numerical computations
- pandas: Data handling
- matplotlib: Basic plotting functionality
- seaborn: Enhanced visualizations
- yfinance: Historical stock data retrieval
- jinja2: HTML template rendering
- tqdm: Progress bars
- flask: Web interface 