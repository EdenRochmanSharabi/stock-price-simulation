# Stock Price Simulation with Regime Switching and Jump Diffusion

A Monte Carlo simulation tool for stock price modeling that incorporates regime switching and jump diffusion processes. The tool provides an object-oriented implementation following SOLID principles with proper encapsulation, abstraction, inheritance, and polymorphism.

## Features

- **Multiple Simulation Models**:
  - **Geometric Brownian Motion (GBM)**: Standard model for stock price movements
  - **Jump Diffusion**: Extends GBM with jumps to model market shocks
  - **Hybrid Model**: Combines GBM, jumps, and volatility regime switching

- **Object-Oriented Design**:
  - Encapsulation of model parameters and data
  - Abstraction through clear interfaces
  - Inheritance for model specialization
  - Polymorphism via the model interface
  - Design patterns (Factory, Strategy)

- **Comprehensive Analysis**:
  - Statistical metrics (mean, variance, VaR, etc.)
  - Risk measures (Sharpe ratio, Sortino ratio)
  - Probability distributions
  - Drawdown analysis

- **Visualization**:
  - Price path plots
  - Probability distribution histograms
  - Interactive HTML reports

- **SP500 Integration**:
  - Automatic retrieval of SP500 constituents
  - Sector-based analysis
  - Batch simulation capabilities

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd stock-simulation
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Command Line Interface

Run simulations directly from the command line:

```bash
# Basic usage with default parameters (simulates AAPL)
python run_simulation.py

# Specify ticker symbols
python run_simulation.py MSFT AAPL GOOGL

# Specify model type and parameters
python run_simulation.py TSLA -m jump -p 5000 -s 63

# Run simulation for a specific sector
python run_simulation.py --sector "Information Technology" --sector-limit 5

# Use random tickers
python run_simulation.py --random 3

# Advanced parameters
python run_simulation.py AMZN -m hybrid --mu 0.1 --sigma 0.3 --jump-intensity 15
```

### Web API

Run the simulation via a web API:

```bash
# Start the web server on port 8080
python run_web_server.py
```

Once the server is running, you can:

- Access the API documentation: http://localhost:8080/
- Run simulations via HTTP requests:

```bash
# Run a simulation for AAPL
curl -X POST http://localhost:8080/api/simulate \
     -H "Content-Type: application/json" \
     -d '{"ticker": "AAPL", "model_type": "hybrid", "paths": 1000, "steps": 21}'

# Get available sectors
curl -X GET http://localhost:8080/api/sectors

# Get tickers in a specific sector
curl -X GET http://localhost:8080/api/tickers/Technology

# Run batch simulation
curl -X POST http://localhost:8080/api/batch \
     -H "Content-Type: application/json" \
     -d '{"tickers": ["MSFT", "AAPL", "GOOGL"], "model_type": "gbm"}'
```

### Using the Python API

You can also use the library in your own Python code:

```python
from stock_sim.models import ModelFactory
from stock_sim.simulation_engine import SimulationEngine

# Create a simulation engine
engine = SimulationEngine(output_base_dir="results")

# Run a simulation
result = engine.run_simulation(
    ticker="AAPL",
    model_type="hybrid",
    paths=1000,
    steps=21,
    calibrate=True,
    lookback_period="2y"
)

# Access the results
statistics = result['statistics']
print(f"Expected return: {statistics['expected_return']:.2f}%")
print(f"Probability of profit: {statistics['prob_profit']:.2f}%")
```

## Project Structure

The project follows a modular, object-oriented structure:

```
stock_sim/
├── models/                  # Simulation models
│   ├── base_model.py        # Abstract base class
│   ├── gbm_model.py         # Geometric Brownian Motion
│   ├── jump_diffusion_model.py  # Jump Diffusion
│   ├── hybrid_model.py      # Combined model
│   └── factory.py           # Model factory
├── analysis/                # Statistical analysis
│   ├── statistics.py        # Statistical calculations
│   ├── data_storage.py      # Data persistence
│   └── reporting.py         # Report generation
├── visualization/           # Data visualization
│   └── plots.py             # Plotting functions
├── utils/                   # Utilities
│   └── sp500.py             # S&P 500 data manager
├── interfaces/              # User interfaces
│   └── cli.py               # Command-line interface
└── simulation_engine.py     # Main simulation engine
```

## OOP Design Principles

The implementation follows object-oriented design principles:

1. **Encapsulation**:
   - Private attributes with getter methods
   - Clear separation of concerns

2. **Abstraction**:
   - Abstract base class for models
   - Consistent interfaces

3. **Inheritance**:
   - Model hierarchy with specialized implementations
   - Code reuse through inheritance

4. **Polymorphism**:
   - Model-agnostic simulation engine
   - Factory pattern for model creation

## License

This project is licensed under the MIT License - see the LICENSE file for details. 