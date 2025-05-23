#!/usr/bin/env python3

"""
Test script for stock price simulation models.
"""

import sys
import os
import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
import time

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stock_sim.models.gbm_model import GBMModel
from stock_sim.models.jump_diffusion_model import JumpDiffusionModel
from stock_sim.models.hybrid_model import HybridModel


class TestSimulationModels(unittest.TestCase):
    """Test cases for simulation models."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.ticker = "AAPL"  # Use a reliable ticker for testing
        self.paths = 100
        self.steps = 50
        self.dt = 1/252
        
        # Model parameters
        self.initial_price = 150.0
        self.mu = 0.08
        self.sigma = 0.2
        
        # Jump diffusion parameters
        self.jump_intensity = 10.0
        self.jump_mean = -0.01
        self.jump_sigma = 0.02
        
        # Volatility clustering parameter
        self.vol_clustering = 0.85
        
        # Create a mock historical data
        self.mock_data = self._create_mock_stock_data()
    
    def _create_mock_stock_data(self):
        """Create mock stock data for testing."""
        # Create a simple price series with upward trend
        dates = pd.date_range(start='2020-01-01', periods=252, freq='B')
        prices = np.array([self.initial_price * (1 + 0.0002 * i) for i in range(252)])
        
        # Create a DataFrame with Close column
        data = pd.DataFrame({
            'Close': prices,
            'Open': prices * 0.99,
            'High': prices * 1.01,
            'Low': prices * 0.98,
            'Volume': np.random.randint(1000000, 5000000, 252)
        }, index=dates)
        
        return data
    
    @patch('yfinance.download')
    def test_gbm_simulation(self, mock_yf_download):
        """Test GBM simulation produces expected output shape."""
        # Mock the yfinance download to return test data
        mock_yf_download.return_value = self.mock_data
        
        # Create GBM model
        model = GBMModel(self.ticker, calibrate=False, mu=self.mu, sigma=self.sigma)
        
        # Run simulation
        paths = model.simulate(paths=self.paths, steps=self.steps, dt=self.dt)
        
        # Check output shape
        self.assertEqual(paths.shape, (self.paths, self.steps + 1))
        
        # Check initial price
        self.assertTrue(np.all(paths[:, 0] == model.initial_price))
        
        # Check all prices are positive
        self.assertTrue(np.all(paths > 0))
    
    @patch('yfinance.download')
    def test_jump_simulation(self, mock_yf_download):
        """Test jump diffusion simulation produces expected output shape."""
        # Mock the yfinance download to return test data
        mock_yf_download.return_value = self.mock_data
        
        # Create Jump Diffusion model
        model = JumpDiffusionModel(
            self.ticker, 
            calibrate=False,
            mu=self.mu, 
            sigma=self.sigma,
            jump_intensity=self.jump_intensity,
            jump_mean=self.jump_mean,
            jump_sigma=self.jump_sigma
        )
        
        # Run simulation
        paths = model.simulate(paths=self.paths, steps=self.steps, dt=self.dt)
        
        # Check output shape
        self.assertEqual(paths.shape, (self.paths, self.steps + 1))
        
        # Check initial price
        self.assertTrue(np.all(paths[:, 0] == model.initial_price))
        
        # Check all prices are positive
        self.assertTrue(np.all(paths > 0))
    
    @patch('yfinance.download')
    def test_hybrid_simulation(self, mock_yf_download):
        """Test hybrid model (regime switching + jump diffusion) produces expected output shape."""
        # Mock the yfinance download to return test data
        mock_yf_download.return_value = self.mock_data
        
        # Create Hybrid model
        model = HybridModel(
            self.ticker,
            calibrate=False,
            mu=self.mu,
            sigma=self.sigma,
            vol_clustering=self.vol_clustering,
            jump_intensity=self.jump_intensity,
            jump_mean=self.jump_mean,
            jump_sigma=self.jump_sigma
        )
        
        # Run simulation
        paths = model.simulate(paths=self.paths, steps=self.steps, dt=self.dt)
        
        # Check output shape
        self.assertEqual(paths.shape, (self.paths, self.steps + 1))
        
        # Check initial price
        self.assertTrue(np.all(paths[:, 0] == model.initial_price))
        
        # Check all prices are positive
        self.assertTrue(np.all(paths > 0))


class TableTestResult(unittest.TestResult):
    """Custom TestResult class that collects test results for table display."""
    
    def __init__(self):
        super().__init__()
        self.test_results = []
        self.start_times = {}
    
    def startTest(self, test):
        super().startTest(test)
        test_name = self._get_test_name(test)
        self.start_times[test_name] = time.time()
    
    def addSuccess(self, test):
        super().addSuccess(test)
        test_name = self._get_test_name(test)
        duration = time.time() - self.start_times[test_name]
        self.test_results.append({
            'name': test_name,
            'status': 'PASS',
            'time': duration
        })
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        test_name = self._get_test_name(test)
        duration = time.time() - self.start_times[test_name]
        self.test_results.append({
            'name': test_name,
            'status': 'FAIL',
            'time': duration,
            'error': err
        })
    
    def addError(self, test, err):
        super().addError(test, err)
        test_name = self._get_test_name(test)
        duration = time.time() - self.start_times.get(test_name, time.time())
        self.test_results.append({
            'name': test_name,
            'status': 'ERROR',
            'time': duration,
            'error': err
        })
    
    def _get_test_name(self, test):
        """Extract test name from test object."""
        return test.id().split('.')[-1]


def print_test_results_table(result):
    """Print test results in a nice table format."""
    if not result.test_results:
        print("No tests were run.")
        return
    
    # Print header
    print("\n" + "="*80)
    print("{:<40} {:<10} {:<15}".format("Test Name", "Status", "Time (s)"))
    print("-"*80)
    
    # Print each test result
    for test_result in result.test_results:
        status = test_result['status']
        status_formatted = f"\033[92m{status}\033[0m" if status == 'PASS' else f"\033[91m{status}\033[0m"
        print("{:<40} {:<25} {:.6f}".format(
            test_result['name'],
            status_formatted,
            test_result['time']
        ))
    
    # Print summary
    total = len(result.test_results)
    passed = sum(1 for r in result.test_results if r['status'] == 'PASS')
    failed = sum(1 for r in result.test_results if r['status'] in ('FAIL', 'ERROR'))
    
    print("-"*80)
    print(f"Total: {total} | Passed: {passed} | Failed: {failed}")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Create a test suite with all tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSimulationModels)
    
    # Run the tests and collect results
    result = TableTestResult()
    suite.run(result)
    
    # Print the results table
    print_test_results_table(result) 