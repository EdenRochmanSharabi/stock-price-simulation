"""
Stock Price Simulation package.
"""
from src.data_retrieval import fetch_stock_data, get_market_parameters
from src.regime_switching import RegimeSwitchingModel
from src.jump_diffusion import JumpDiffusionModel
from src.earnings_shocks import EarningsShockModel
from src.simulation import run_simulation

__version__ = '0.1.0' 