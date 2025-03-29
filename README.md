# Stock Price Simulation with Regime Switching and Jump Diffusion

A Monte Carlo simulation tool for stock price modeling that incorporates regime switching and jump diffusion processes. The tool provides a web interface for running simulations and generating reports.

## Features

- Multiple simulation models:
  - Geometric Brownian Motion (GBM)
  - Jump Diffusion
  - Combined (GBM + Jump Diffusion)
- Regime switching capabilities
- Automatic model calibration using historical data
- Web interface for easy control and monitoring
- Sector-based analysis
- Support for S&P 500 stocks with automatic ticker updates
- Detailed reporting and visualization

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd stock-simulation
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the web interface:
```bash
python run_web_ui.py
```

2. Open your web browser and navigate to `http://localhost:5000`

3. Configure simulation parameters:
   - Select simulation model
   - Set number of paths and steps
   - Choose sectors and number of companies per sector
   - Configure model parameters (automatic or manual)

4. Click "Start Simulation" to begin

5. Monitor progress in real-time through the web interface

6. View the generated report when complete

## S&P 500 Tickers

The application includes built-in support for S&P 500 stocks with the following features:

- Automatic retrieval of current S&P 500 constituents from Wikipedia
- Sector-based organization of stocks
- Ability to refresh ticker data at any time
- Individual sector refresh capability
- Persistent storage of ticker data in CSV format

### Ticker Data Management

- Ticker data is stored in two CSV files:
  - `sp500_tickers.csv`: List of all S&P 500 tickers
  - `sp500_sectors.csv`: Sector mapping for all tickers

- The data can be refreshed in two ways:
  1. Global refresh: Updates all S&P 500 tickers and sector mappings
  2. Sector refresh: Updates tickers for a specific sector

## Simulation Models

### 1. Geometric Brownian Motion (GBM)

The basic GBM model assumes stock prices follow a log-normal distribution with constant drift and volatility:

\[ dS_t = \mu S_t dt + \sigma S_t dW_t \]

### 2. Jump Diffusion

Incorporates sudden price jumps to model market shocks:

\[ dS_t = \mu S_t dt + \sigma S_t dW_t + J_t dN_t \]

Where:
- \( J_t \) is the jump size
- \( N_t \) is a Poisson process

### 3. Combined Model

A hybrid model that combines GBM with jump diffusion and regime switching:

\[ dS_t = \mu_i S_t dt + \sigma_i S_t dW_t + J_t dN_t \]

Where \( i \) represents the current market regime.

## Output

The simulation generates:

1. Price paths for each stock
2. Statistical analysis including:
   - Mean and standard deviation
   - Value at Risk (VaR)
   - Expected Shortfall
   - Regime probabilities
3. Visualizations:
   - Price path plots
   - Distribution plots
   - Regime transition diagrams
4. HTML reports with interactive elements

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 