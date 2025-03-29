# Refactored Stock Price Simulation

This directory contains a refactored version of the stock price simulation code. The original monolithic implementation has been reorganized into a modular structure for better maintainability and extensibility.

## Directory Structure

```
stock_simulation_engine/
├── modules/               # Core simulation modules
│   ├── __init__.py       # Package initialization
│   ├── base_models.py    # Base simulation classes and utilities
│   ├── simulation_models.py # Specific model implementations (GBM, Jump, Combined)
│   ├── stats_viz.py      # Statistics calculation and visualization
│   └── runner.py         # Main simulation runner
├── stock_simulation_engine_simulation.py # Main entry point for single-stock simulation
├── run_simulations.py    # Multi-stock simulation across sectors
├── reporting.py          # Report generation functionality
└── README_REFACTORED.md  # This file
```

## Modules

### base_models.py
- Contains the `StockModel` base class
- Provides core functionality like data loading and calibration
- Defines utility functions like `calculate_returns`

### simulation_models.py
- Implements concrete simulation models:
  - `GeometricBrownianMotion`: Standard GBM model
  - `JumpDiffusionModel`: GBM with jump processes
  - `CombinedModel`: Advanced model with GBM, jumps, and volatility clustering

### stats_viz.py
- Contains functions for statistical analysis of simulation results
- Implements visualization functions for generating plots

### runner.py
- Provides the main `run_simulation` function
- Handles model selection, simulation execution, and results processing

## Usage

### Running a Single Stock Simulation

```python
from modules.engine import run_simulation

result = run_simulation(
    ticker="AAPL",
    model_type="combined",  # Options: "gbm", "jump", "combined"
    paths=1000,
    steps=21,
    output_dir="output"
)
```

### Running Sector Simulations

```bash
python run_simulations.py --model combined --paths 1000 --steps 21 --companies 3
```

## Improvements from Refactoring

1. **Modularity**: Code is now organized into logical components
2. **Maintainability**: Easier to update individual components without breaking others
3. **Extensibility**: New models or features can be added with minimal changes
4. **Code Reuse**: Common functionality is centralized and shared
5. **Testing**: Components can be tested in isolation

## Deleted Files

During refactoring, the following files were consolidated or made redundant:

- `stock_simulation.py`: Refactored into the modules directory
- Original `models.py` and `runner.py` in the `src/simulation` directory (if they existed) 