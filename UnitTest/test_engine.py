#!/usr/bin/env python3

"""
Test Simulation Engine
----------------------
Unit tests for the simulation engine module.
"""

from UnitTest.test_base import BaseTestCase
from unittest.mock import patch, MagicMock
import numpy as np
import pandas as pd
from stock_sim.engine import StockSimulationEngine
from stock_sim.models.gbm_model import GBMModel
from stock_sim.models.hybrid_model import HybridModel
from stock_sim.models.jump_diffusion_model import JumpDiffusionModel


class TestSimulationEngine(BaseTestCase):
    """Test cases for the StockSimulationEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a StockSimulationEngine instance for testing
        self.engine = StockSimulationEngine()
        
        # Create a mock stock data for testing
        self.mock_stock_data = pd.DataFrame({
            'Close': [100.0 * (1 + 0.001 * i) for i in range(252)],
            'Date': pd.date_range(start='2020-01-01', periods=252, freq='B')
        })
        self.mock_stock_data.set_index('Date', inplace=True)
    
    @patch('stock_sim.data.fetch_historical_data')
    def test_simulate_single_stock_gbm(self, mock_fetch_data):
        """Test the simulate_single_stock method with GBM model."""
        # Mock the fetch_historical_data to return our mock data
        mock_fetch_data.return_value = self.mock_stock_data
        
        # Simulate a single stock with GBM model
        result = self.engine.simulate_single_stock(
            ticker=self.test_ticker,
            model_type='gbm',
            days=self.test_days,
            paths=self.test_paths,
            volatility_lookback=30
        )
        
        # Validate the result structure
        self._validate_simulation_result(result, 'gbm')
    
    @patch('stock_sim.data.fetch_historical_data')
    def test_simulate_single_stock_jump(self, mock_fetch_data):
        """Test the simulate_single_stock method with Jump Diffusion model."""
        # Mock the fetch_historical_data to return our mock data
        mock_fetch_data.return_value = self.mock_stock_data
        
        # Simulate a single stock with Jump Diffusion model
        result = self.engine.simulate_single_stock(
            ticker=self.test_ticker,
            model_type='jump',
            days=self.test_days,
            paths=self.test_paths,
            volatility_lookback=30,
            jump_params={'lambda': 5, 'mu_j': -0.01, 'sigma_j': 0.02}
        )
        
        # Validate the result structure
        self._validate_simulation_result(result, 'jump')
    
    @patch('stock_sim.data.fetch_historical_data')
    def test_simulate_single_stock_hybrid(self, mock_fetch_data):
        """Test the simulate_single_stock method with Hybrid model."""
        # Mock the fetch_historical_data to return our mock data
        mock_fetch_data.return_value = self.mock_stock_data
        
        # Simulate a single stock with Hybrid model
        result = self.engine.simulate_single_stock(
            ticker=self.test_ticker,
            model_type='hybrid',
            days=self.test_days,
            paths=self.test_paths,
            volatility_lookback=30,
            hybrid_params={
                'jump_params': {'lambda': 5, 'mu_j': -0.01, 'sigma_j': 0.02},
                'regime_params': {'num_regimes': 2, 'transition_matrix': [[0.95, 0.05], [0.05, 0.95]]}
            }
        )
        
        # Validate the result structure
        self._validate_simulation_result(result, 'hybrid')
    
    def test_create_model(self):
        """Test the _create_model method."""
        # Test GBM model creation
        gbm_model = self.engine._create_model(
            'gbm', 
            initial_price=100.0, 
            mu=0.05, 
            sigma=0.2
        )
        self.assertIsInstance(gbm_model, GBMModel)
        
        # Test Jump Diffusion model creation
        jump_params = {'lambda': 5, 'mu_j': -0.01, 'sigma_j': 0.02}
        jump_model = self.engine._create_model(
            'jump', 
            initial_price=100.0, 
            mu=0.05, 
            sigma=0.2, 
            jump_params=jump_params
        )
        self.assertIsInstance(jump_model, JumpDiffusionModel)
        
        # Test Hybrid model creation
        hybrid_params = {
            'jump_params': {'lambda': 5, 'mu_j': -0.01, 'sigma_j': 0.02},
            'regime_params': {'num_regimes': 2, 'transition_matrix': [[0.95, 0.05], [0.05, 0.95]]}
        }
        hybrid_model = self.engine._create_model(
            'hybrid', 
            initial_price=100.0, 
            mu=0.05, 
            sigma=0.2, 
            hybrid_params=hybrid_params
        )
        self.assertIsInstance(hybrid_model, HybridModel)
        
        # Test invalid model type
        with self.assertRaises(ValueError):
            self.engine._create_model('invalid_model', initial_price=100.0, mu=0.05, sigma=0.2)
    
    @patch('stock_sim.engine.multiprocessing.Pool')
    @patch('stock_sim.data.fetch_historical_data')
    def test_simulate_batch(self, mock_fetch_data, mock_pool):
        """Test the simulate_batch method."""
        # Mock the fetch_historical_data to return our mock data
        mock_fetch_data.return_value = self.mock_stock_data
        
        # Mock the pool's map method to simulate parallel processing
        mock_process = MagicMock()
        mock_process.get.return_value = {
            'ticker': self.test_ticker,
            'model_type': 'gbm',
            'paths_matrix': np.ones((self.test_paths, self.test_steps + 1)) * 100.0,
            'statistics': {'expected_return': 0.05, 'return_volatility': 0.2}
        }
        mock_pool.return_value.apply_async.return_value = mock_process
        mock_pool.return_value.__enter__.return_value = mock_pool.return_value
        
        # Simulate a batch of stocks
        tickers = ['AAPL', 'MSFT', 'GOOG']
        result = self.engine.simulate_batch(
            tickers=tickers,
            model_type='gbm',
            days=self.test_days,
            paths=self.test_paths
        )
        
        # Check that the result is a dictionary with the correct tickers
        self.assertIsInstance(result, dict)
        
        # Note: Due to mocking, we won't have all tickers in the result
        # but we should have at least one entry from our mock
        self.assertTrue(any(ticker in result for ticker in tickers))
    
    def _validate_simulation_result(self, result, expected_model_type):
        """Helper method to validate simulation result structure."""
        # Check that result is a dictionary with expected keys
        self.assertIsInstance(result, dict)
        
        required_keys = [
            'ticker', 'model_type', 'paths_matrix', 
            'statistics', 'initial_price', 'model_params'
        ]
        
        for key in required_keys:
            self.assertIn(key, result, f"Missing key in result: {key}")
        
        # Check that model_type matches expected
        self.assertEqual(result['model_type'], expected_model_type)
        
        # Check that paths_matrix has correct shape
        self.assertEqual(
            result['paths_matrix'].shape, 
            (self.test_paths, self.test_steps + 1)
        )
        
        # Check statistics
        self.assertIn('expected_return', result['statistics'])
        self.assertIn('return_volatility', result['statistics'])


if __name__ == "__main__":
    unittest.main() 