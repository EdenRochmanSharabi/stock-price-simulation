#!/usr/bin/env python3

"""
Stock Price Simulation
------------------------------
Main entry point for running stock price simulations.
This is a modular implementation of stock price simulation models.
"""

from modules.base import StockModel, calculate_returns
from modules.models import GBMModel, JumpDiffusionModel, HybridModel
from modules.analytics import calculate_statistics, save_simulation_data, generate_plots
from modules.engine import run_simulation, create_directory


if __name__ == "__main__":
    # Simple test if run directly
    ticker = "AAPL"
    result = run_simulation(ticker, model_type='combined', paths=500, steps=21)
    if result:
        print(f"Simulation completed successfully for {ticker}")
        print(f"Expected return: {result['statistics']['expected_return']:.2f}%")
        print(f"Probability of profit: {result['statistics']['prob_profit']:.2f}%") 