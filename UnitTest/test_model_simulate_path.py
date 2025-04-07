#!/usr/bin/env python3

"""
Test Model Simulate Path Method
----------------------------
Unit tests for the simulate_path method across all stock models.
"""

import unittest
import numpy as np
from unittest.mock import patch, MagicMock
import pandas as pd
import sys
import os
import time

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stock_sim.models.gbm_model import GBMModel
from stock_sim.models.jump_diffusion_model import JumpDiffusionModel
from stock_sim.models.hybrid_model import HybridModel


class TestModelSimulatePath(unittest.TestCase):
    """Test cases for the simulate_path method in all model classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Test parameters
        self.test_ticker = "AAPL"
        self.test_initial_price = 150.0
        self.custom_initial_price = 200.0
        self.test_steps = 50
        self.test_dt = 1/252
        
        # Model parameters
        self.mu = 0.05  # Annual drift (return)
        self.sigma = 0.2  # Annual volatility
        
        # Jump diffusion parameters
        self.jump_intensity = 10  # Expected number of jumps per year
        self.jump_mean = -0.01  # Expected jump size
        self.jump_sigma = 0.02  # Jump size volatility
        
        # Volatility clustering parameter
        self.vol_clustering = 0.85
    
    @patch('yfinance.download')
    def test_gbm_model_simulate_path(self, mock_yf_download):
        """Test the simulate_path method in GBMModel."""
        # Mock the yfinance download to return test data
        mock_yf_download.return_value = self._create_mock_stock_data()
        
        # Create a GBM model
        model = GBMModel(self.test_ticker, calibrate=False, mu=self.mu, sigma=self.sigma)
        original_price = model.initial_price
        
        # Generate a single path with the default initial price
        path = model.simulate_path(self.test_initial_price, self.test_steps, self.test_dt)
        
        # Check that path is a numpy array with appropriate size
        self.assertIsInstance(path, np.ndarray)
        self.assertEqual(len(path), self.test_steps)
        
        # Check that no prices are negative
        self.assertTrue(np.all(path >= 0))
        
        # Generate another path with custom initial price
        path2 = model.simulate_path(self.custom_initial_price, self.test_steps, self.test_dt)
        
        # Check that the model's initial price wasn't permanently changed
        self.assertEqual(model.initial_price, original_price)
    
    @patch('yfinance.download')
    def test_jump_diffusion_model_simulate_path(self, mock_yf_download):
        """Test the simulate_path method in JumpDiffusionModel."""
        # Mock the yfinance download to return test data
        mock_yf_download.return_value = self._create_mock_stock_data()
        
        # Create a Jump Diffusion model
        model = JumpDiffusionModel(
            self.test_ticker, 
            calibrate=False,
            mu=self.mu, 
            sigma=self.sigma,
            jump_intensity=self.jump_intensity,
            jump_mean=self.jump_mean,
            jump_sigma=self.jump_sigma
        )
        original_price = model.initial_price
        
        # Generate a single path with the default initial price
        path = model.simulate_path(self.test_initial_price, self.test_steps, self.test_dt)
        
        # Check that path is a numpy array with appropriate size
        self.assertIsInstance(path, np.ndarray)
        self.assertEqual(len(path), self.test_steps)
        
        # Check that no prices are negative
        self.assertTrue(np.all(path >= 0))
        
        # Generate another path with custom initial price
        path2 = model.simulate_path(self.custom_initial_price, self.test_steps, self.test_dt)
        
        # Check that the model's initial price wasn't permanently changed
        self.assertEqual(model.initial_price, original_price)
    
    @patch('yfinance.download')
    def test_hybrid_model_simulate_path(self, mock_yf_download):
        """Test the simulate_path method in HybridModel."""
        # Mock the yfinance download to return test data
        mock_yf_download.return_value = self._create_mock_stock_data()
        
        # Create a Hybrid model
        model = HybridModel(
            self.test_ticker,
            calibrate=False,
            mu=self.mu,
            sigma=self.sigma,
            vol_clustering=self.vol_clustering,
            jump_intensity=self.jump_intensity,
            jump_mean=self.jump_mean,
            jump_sigma=self.jump_sigma
        )
        original_price = model.initial_price
        
        # Generate a single path with the default initial price
        path = model.simulate_path(self.test_initial_price, self.test_steps, self.test_dt)
        
        # Check that path is a numpy array with appropriate size
        self.assertIsInstance(path, np.ndarray)
        self.assertEqual(len(path), self.test_steps)
        
        # Check that no prices are negative
        self.assertTrue(np.all(path >= 0))
        
        # Generate another path with custom initial price
        path2 = model.simulate_path(self.custom_initial_price, self.test_steps, self.test_dt)
        
        # Check that the model's initial price wasn't permanently changed
        self.assertEqual(model.initial_price, original_price)
    
    @patch('yfinance.download')
    def test_simulate_path_with_error_handling(self, mock_yf_download):
        """Test the error handling in simulate_path method."""
        # Mock the yfinance download to return test data
        mock_yf_download.return_value = self._create_mock_stock_data()
        
        # Create a model
        model = GBMModel(self.test_ticker, calibrate=False, mu=self.mu, sigma=self.sigma)
        
        # Mock the simulate method to raise an exception
        with patch.object(GBMModel, 'simulate', side_effect=Exception("Test exception")):
            # This should not raise an exception but use the fallback
            path = model.simulate_path(self.test_initial_price, self.test_steps)
            
            # Check that the fallback generated a proper path
            self.assertIsInstance(path, np.ndarray)
            self.assertEqual(len(path), self.test_steps)
            self.assertTrue(np.all(path >= 0))
    
    def _create_mock_stock_data(self):
        """Create mock stock data for testing."""
        # Create a simple price series with upward trend
        dates = pd.date_range(start='2020-01-01', periods=252, freq='B')
        prices = np.array([self.test_initial_price * (1 + 0.0002 * i) for i in range(252)])
        
        # Create a DataFrame with Close column
        data = pd.DataFrame({
            'Close': prices,
            'Open': prices * 0.99,
            'High': prices * 1.01,
            'Low': prices * 0.98,
            'Volume': np.random.randint(1000000, 5000000, 252)
        }, index=dates)
        
        return data


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
    suite = unittest.TestLoader().loadTestsFromTestCase(TestModelSimulatePath)
    
    # Run the tests and collect results
    result = TableTestResult()
    suite.run(result)
    
    # Print the results table
    print_test_results_table(result) 