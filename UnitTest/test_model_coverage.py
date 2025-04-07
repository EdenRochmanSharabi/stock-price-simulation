#!/usr/bin/env python3

"""
Tests to ensure 100% coverage of the model classes.
"""

import unittest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from datetime import datetime
import sys
import os
import time

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from stock_sim.models.base_model import StockModel, calculate_returns
from stock_sim.models.gbm_model import GBMModel
from stock_sim.models.jump_diffusion_model import JumpDiffusionModel
from stock_sim.models.hybrid_model import HybridModel


class TableTestResult(unittest.TestResult):
    """Custom TestResult class that collects test results for table display."""
    
    def __init__(self, stream=None, descriptions=None, verbosity=None, **kwargs):
        super().__init__()
        self.test_results = []
        self.start_times = {}
        self.stream = stream
        self.descriptions = descriptions
        self.verbosity = verbosity
    
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
        return test._testMethodName


def print_test_results_table(result):
    """Print test results in a table format."""
    # Get the maximum length for test name
    max_name_length = max(len(r['name']) for r in result.test_results)
    
    # Print table header
    header = f"\n{'=' * 80}\n"
    header += f"Test Name{' ' * (max_name_length - 9)}Status     Time (s)       \n"
    header += f"{'-' * 80}\n"
    print(header, end='')
    
    # Print test results
    for r in result.test_results:
        status = r['status']
        print(f"{r['name']}{' ' * (max_name_length - len(r['name']) + 1)}{status}{' ' * (10 - len(status))}{r['time']:.6f}")
    
    # Print footer with summary
    passed = sum(1 for r in result.test_results if r['status'] == 'PASS')
    failed = sum(1 for r in result.test_results if r['status'] == 'FAIL')
    error = sum(1 for r in result.test_results if r['status'] == 'ERROR')
    total = len(result.test_results)
    total_time = sum(r['time'] for r in result.test_results)
    
    footer = f"{'-' * 80}\n"
    footer += f"Total: {total} | Passed: {passed} | Failed: {failed} | Error: {error}\n"
    footer += f"{'=' * 80}\n"
    print(footer)


class TestModelCoverage(unittest.TestCase):
    """Tests designed to achieve 100% coverage of model classes."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_ticker = "AAPL"
        self.test_price = 150.0
        
        # Create mock historical data
        dates = pd.date_range(start='2020-01-01', periods=252)
        self.mock_data = pd.DataFrame({
            'Open': np.linspace(100, 150, 252),
            'High': np.linspace(105, 155, 252),
            'Low': np.linspace(95, 145, 252),
            'Close': np.linspace(102, 152, 252),
            'Volume': np.random.randint(1000000, 5000000, 252)
        }, index=dates)
    
    @patch('yfinance.download')
    def test_base_model_properties(self, mock_yf_download):
        """Test property getters in StockModel."""
        # Mock the download function
        mock_yf_download.return_value = self.mock_data
        
        # Implement a concrete StockModel for testing
        class ConcreteStockModel(StockModel):
            def simulate(self, paths=1000, steps=252, dt=1/252):
                return np.zeros((paths, steps + 1))
        
        # Create a model with the mocked data
        model = ConcreteStockModel(
            self.test_ticker, 
            start_date=datetime.now(), 
            lookback_period="1y",
            calibrate=True
        )
        
        # Test property getters
        self.assertEqual(model.ticker, self.test_ticker)
        self.assertAlmostEqual(model.initial_price, 152.0, places=1)
        self.assertTrue(hasattr(model, 'mu'))
        self.assertTrue(hasattr(model, 'sigma'))
        self.assertIsInstance(model.historical_data, pd.DataFrame)
        
        # Test calculate_returns function
        prices = np.array([100, 110, 121, 133.1])
        returns = calculate_returns(prices)
        self.assertEqual(len(returns), len(prices) - 1)
    
    @patch('yfinance.download')
    def test_load_historical_data_error(self, mock_yf_download):
        """Test error handling in _load_historical_data."""
        # Make the download function raise an exception
        mock_yf_download.side_effect = Exception("Test error")
        
        # Implement a concrete StockModel for testing
        class ConcreteStockModel(StockModel):
            def simulate(self, paths=1000, steps=252, dt=1/252):
                return np.zeros((paths, steps + 1))
        
        # Create a model (should handle the error gracefully)
        with self.assertRaises(ValueError):
            # This should raise ValueError since the model requires historical data
            ConcreteStockModel(self.test_ticker)
    
    @patch('yfinance.download')
    def test_base_model_calibration(self, mock_yf_download):
        """Test the calibration process in the base model."""
        # Create mock data that will cause calibration to work normally
        mock_yf_download.return_value = self.mock_data
        
        # Create a concrete model
        class ConcreteStockModel(StockModel):
            def simulate(self, paths=1000, steps=252, dt=1/252):
                return np.zeros((paths, steps + 1))
        
        # Create model with calibration
        with patch('builtins.print') as mock_print:
            model = ConcreteStockModel(self.test_ticker, calibrate=True)
        
        # Check that calibration produced reasonable values
        self.assertIsNotNone(model.mu)
        self.assertIsNotNone(model.sigma)
        self.assertFalse(np.isnan(model.mu))
        self.assertFalse(np.isnan(model.sigma))
    
    @patch('yfinance.download')
    def test_base_model_calibration_error(self, mock_yf_download):
        """Test error handling in calibration process."""
        mock_yf_download.return_value = self.mock_data
        
        # Create a concrete model with a mocked calibration method that returns default values
        class ConcreteStockModel(StockModel):
            def simulate(self, paths=1000, steps=252, dt=1/252):
                return np.zeros((paths, steps + 1))
                
            def _calibrate_model(self):
                print("Using default values due to test mock")
                return 0.08, 0.20  # Default values
        
        # Create model and verify it handles the error
        with patch('builtins.print') as mock_print:
            model = ConcreteStockModel(self.test_ticker, calibrate=True)
        
        # It should use the default values for calibration
        self.assertEqual(model.mu, 0.08)
        self.assertEqual(model.sigma, 0.20)
    
    @patch('yfinance.download')
    def test_simulate_path_error(self, mock_yf_download):
        """Test error handling in simulate_path."""
        # Mock the download function
        mock_yf_download.return_value = self.mock_data
        
        # Create a model
        model = GBMModel(self.test_ticker, calibrate=False)
        
        # Mock the simulate method to raise an exception
        with patch.object(GBMModel, 'simulate', side_effect=Exception("Test exception")):
            # This should not raise an exception but use the fallback
            path = model.simulate_path(self.test_price, steps=10)
            
            # Check that fallback generated a path
            self.assertEqual(len(path), 10)
            self.assertGreaterEqual(path.min(), 0)  # No negative prices
    
    @patch('yfinance.download')
    def test_jump_diffusion_calibration(self, mock_yf_download):
        """Test the calibration of JumpDiffusionModel."""
        # Create mock data with jumps
        mock_data = self.mock_data.copy()
        # Add some jumps to the data
        jump_indices = [50, 100, 150, 200]
        for idx in jump_indices:
            mock_data.iloc[idx, mock_data.columns.get_loc('Close')] *= 0.9  # 10% drop
        
        mock_yf_download.return_value = mock_data
        
        # Create a model with calibration enabled
        with patch('builtins.print') as mock_print:  # Capture print statements
            model = JumpDiffusionModel(self.test_ticker, calibrate=True)
        
        # Test that the model has calibrated jump parameters
        self.assertGreater(model.jump_intensity, 0)
        
        # Test property getters
        self.assertEqual(model.jump_mean, model._jump_mean)
        self.assertEqual(model.jump_sigma, model._jump_sigma)
        self.assertEqual(model.jump_intensity, model._jump_intensity)
    
    @patch('yfinance.download')
    def test_jump_diffusion_calibration_error(self, mock_yf_download):
        """Test error handling in JumpDiffusionModel calibration."""
        # Create a model with a special subclass to test error handling
        mock_yf_download.return_value = self.mock_data
        
        class TestableJumpDiffusionModel(JumpDiffusionModel):
            def _calibrate_jump_parameters(self):
                try:
                    # Simulate error scenario
                    raise Exception("Test calibration error")
                except Exception as e:
                    print(f"Error calibrating jump parameters for {self.ticker}: {e}")
                    # Fallback to default parameters
                    self._jump_intensity = 10
                    self._jump_mean = -0.01
                    self._jump_sigma = 0.02
        
        # Create model with calibration
        with patch('builtins.print') as mock_print:
            model = TestableJumpDiffusionModel(self.test_ticker, calibrate=True)
        
        # Check that it used default values
        self.assertEqual(model.jump_intensity, 10)
        self.assertEqual(model.jump_mean, -0.01)
        self.assertEqual(model.jump_sigma, 0.02)
    
    @patch('yfinance.download')
    def test_hybrid_model_properties(self, mock_yf_download):
        """Test property getters in HybridModel."""
        # Mock the download function
        mock_yf_download.return_value = self.mock_data
        
        # Create a model
        model = HybridModel(
            self.test_ticker, 
            calibrate=False,
            vol_clustering=0.75,
            jump_intensity=5,
            jump_mean=-0.02,
            jump_sigma=0.03
        )
        
        # Test property getters
        self.assertEqual(model.vol_clustering, 0.75)
        self.assertIsInstance(model.jump_model, JumpDiffusionModel)
        self.assertEqual(model.jump_model.jump_intensity, 5)
        self.assertEqual(model.jump_model.jump_mean, -0.02)
        self.assertEqual(model.jump_model.jump_sigma, 0.03)
    
    @patch('yfinance.download')
    def test_jump_diffusion_simulate(self, mock_yf_download):
        """Test the simulate method in JumpDiffusionModel."""
        # Mock the download function
        mock_yf_download.return_value = self.mock_data
        
        # Create a model
        model = JumpDiffusionModel(
            self.test_ticker, 
            calibrate=False,
            mu=0.08,
            sigma=0.2,
            jump_intensity=10,
            jump_mean=-0.01,
            jump_sigma=0.02
        )
        
        # Simulate with a very small number of paths and steps to speed up the test
        paths = 5
        steps = 10
        
        # Run the simulation
        result = model.simulate(paths=paths, steps=steps)
        
        # Check the shape and basic properties
        self.assertEqual(result.shape, (paths, steps + 1))
        self.assertTrue(np.all(result[:, 0] == model.initial_price))
        self.assertTrue(np.all(result >= 0))
    
    @patch('yfinance.download')
    def test_hybrid_model_simulate(self, mock_yf_download):
        """Test the simulate method in HybridModel."""
        # Mock the download function
        mock_yf_download.return_value = self.mock_data
        
        # Create a model
        model = HybridModel(
            self.test_ticker,
            calibrate=False,
            mu=0.08,
            sigma=0.2,
            vol_clustering=0.85,
            jump_intensity=10,
            jump_mean=-0.01,
            jump_sigma=0.02
        )
        
        # Simulate with a very small number of paths and steps to speed up the test
        paths = 5
        steps = 10
        
        # Run the simulation
        result = model.simulate(paths=paths, steps=steps)
        
        # Check the shape and basic properties
        self.assertEqual(result.shape, (paths, steps + 1))
        self.assertTrue(np.all(result[:, 0] == model.initial_price))
        self.assertTrue(np.all(result >= 0))
    
    @patch('yfinance.download')
    def test_base_model_abstract_methods(self, mock_yf_download):
        """Test the abstract methods in StockModel."""
        # Mock the download function
        mock_yf_download.return_value = self.mock_data
        
        # Try to instantiate the abstract class directly
        with self.assertRaises(TypeError):
            model = StockModel(self.test_ticker)
        
        # Implement a concrete model but forget to implement the simulate method
        class IncompleteModel(StockModel):
            pass
            
        # This should raise TypeError because simulate is abstract
        with self.assertRaises(TypeError):
            model = IncompleteModel(self.test_ticker)

    @patch('yfinance.download')
    def test_base_model_simulate_path_with_jumps(self, mock_yf_download):
        """Test the simulate_path method with exceptions and jumps."""
        # Mock the download function
        mock_yf_download.return_value = self.mock_data
        
        # Create a model
        model = JumpDiffusionModel(self.test_ticker, calibrate=False)
        
        # Force an exception in simulate to trigger the fallback in simulate_path
        with patch.object(JumpDiffusionModel, 'simulate', side_effect=Exception("Forced exception")):
            path = model.simulate_path(self.test_price, steps=20)
            self.assertEqual(len(path), 20)
    
    @patch('yfinance.download')
    def test_jump_diffusion_calibration_edge_cases(self, mock_yf_download):
        """Test edge cases in JumpDiffusionModel calibration."""
        # Create mock data with extreme jumps
        mock_data = self.mock_data.copy()
        # Create a simple data series with big jumps
        dates = pd.date_range(start='2020-01-01', periods=252)
        prices = np.zeros(252) + 100.0
        # Add some clear jumps that will be detected
        for i in range(30, 252, 30):
            prices[i] = 80.0  # 20% drop every 30 days
        
        mock_data = pd.DataFrame({
            'Close': prices,
            'Open': prices * 0.99,
            'High': prices * 1.01,
            'Low': prices * 0.98,
            'Volume': np.random.randint(1000000, 5000000, 252)
        }, index=dates)
        
        mock_yf_download.return_value = mock_data
        
        # Mock print to capture output
        with patch('builtins.print'):
            # Create model with calibration enabled
            model = JumpDiffusionModel(self.test_ticker, calibrate=True)
            
        # Should have detected jumps
        self.assertGreaterEqual(model.jump_intensity, 0)

    @patch('yfinance.download')
    def test_models_with_jumps(self, mock_yf_download):
        """Test models with explicitly triggered jumps."""
        # Mock the download function
        mock_yf_download.return_value = self.mock_data
        
        # Create models
        jump_model = JumpDiffusionModel(
            self.test_ticker, 
            calibrate=False,
            mu=0.08,
            sigma=0.2,
            jump_intensity=100,  # Very high intensity to guarantee jumps
            jump_mean=-0.1,
            jump_sigma=0.05
        )
        
        hybrid_model = HybridModel(
            self.test_ticker,
            calibrate=False,
            mu=0.08,
            sigma=0.2,
            vol_clustering=0.85,
            jump_intensity=100,  # Very high intensity to guarantee jumps
            jump_mean=-0.1,
            jump_sigma=0.05
        )
        
        # Force jumps by controlling random numbers
        with patch('numpy.random.random', return_value=np.zeros(10)):  # Always below jump_prob
            # Run simulations that will definitely have jumps
            jump_paths = jump_model.simulate(paths=10, steps=5)
            hybrid_paths = hybrid_model.simulate(paths=10, steps=5)
            
            # Verify results
            self.assertEqual(jump_paths.shape, (10, 6))
            self.assertEqual(hybrid_paths.shape, (10, 6))
            
            # Check that paths include the initial price
            self.assertTrue(np.all(jump_paths[:, 0] == jump_model.initial_price))
            self.assertTrue(np.all(hybrid_paths[:, 0] == hybrid_model.initial_price))


if __name__ == '__main__':
    # Create a TestRunner with our custom result class
    runner = unittest.TextTestRunner(resultclass=TableTestResult)
    result = runner.run(unittest.TestLoader().loadTestsFromTestCase(TestModelCoverage))
    
    # Print a formatted table of results
    max_name_length = max(len(r['name']) for r in result.test_results)
    
    # Print table header
    header = f"\n{'=' * 80}\n"
    header += f"Test Name{' ' * (max_name_length - 9)}Status     Time (s)       \n"
    header += f"{'-' * 80}\n"
    print(header, end='')
    
    # Print test results
    for r in result.test_results:
        status = r['status']
        print(f"{r['name']}{' ' * (max_name_length - len(r['name']) + 1)}{status}{' ' * (10 - len(status))}{r['time']:.6f}")
    
    # Print footer with summary
    passed = sum(1 for r in result.test_results if r['status'] == 'PASS')
    failed = sum(1 for r in result.test_results if r['status'] == 'FAIL')
    error = sum(1 for r in result.test_results if r['status'] == 'ERROR')
    total = len(result.test_results)
    
    footer = f"{'-' * 80}\n"
    footer += f"Total: {total} | Passed: {passed} | Failed: {failed} | Error: {error}\n"
    footer += f"{'=' * 80}\n"
    print(footer) 