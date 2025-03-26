# Stock Price Simulation with Regime Switching and Jump Diffusion

This project simulates stock price movements over a one-year period using Monte Carlo methods. The simulation incorporates advanced features such as:

- **Regime switching**: Modeling different market conditions (bull/bear markets)
- **Jump diffusion**: Capturing sudden price jumps and drops
- **Earnings event shocks**: Modeling the impact of scheduled earnings announcements

## Requirements

- Python 3.8 or later
- Dependencies listed in `requirements.txt`

## Installation

```bash
# Clone the repository
git clone [repository-url]
cd stock-price-simulation

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

- `src/`: Source code
  - `data_retrieval.py`: Functions to fetch historical stock data
  - `regime_switching.py`: Implementation of regime switching model
  - `jump_diffusion.py`: Implementation of jump diffusion component
  - `earnings_shocks.py`: Logic for modeling earnings announcement impacts
  - `simulation.py`: Main simulation engine
  - `utils.py`: Utility functions
- `tests/`: Unit tests
- `data/`: Directory for storing data
- `notebooks/`: Jupyter notebooks for analysis and visualization

## Usage

```python
from src.simulation import run_simulation

# Run a simulation for a specific ticker
results = run_simulation(ticker="AAPL", num_simulations=1000)
```

## Features

- **Data Retrieval**: Uses yfinance to fetch historical stock data for calibration
- **Regime Switching**: Models bull and bear market conditions with transitions governed by a Markov chain
- **Jump Diffusion**: Incorporates sudden price jumps using a Poisson process
- **Earnings Shocks**: Models the impact of earnings announcements on stock prices
- **Performance Optimization**: Uses Numba for faster simulation execution 