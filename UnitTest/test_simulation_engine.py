#!/usr/bin/env python3

"""
Test Simulation Engine
--------------------
Unit tests for the SimulationEngine class.
"""

from UnitTest.test_base import BaseTestCase
import os
import numpy as np
from stock_sim.simulation_engine import SimulationEngine
from unittest.mock import patch, MagicMock


class TestSimulationEngine(BaseTestCase):
    """Test cases for the SimulationEngine class."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        # Create a simulation engine with temporary output directory
        self.engine = SimulationEngine(output_base_dir=self.get_output_dir())
    
    def test_init_creates_output_structure(self):
        """Test that initialization creates the output directory structure."""
        # Check that the output directories were created
        self.assertTrue(os.path.exists(self.engine._output_base_dir))
        self.assertTrue(os.path.exists(self.engine._reports_dir))
        self.assertTrue(os.path.exists(self.engine._graphs_dir))
        self.assertTrue(os.path.exists(self.engine._data_dir))
    
    @patch('stock_sim.models.ModelFactory.create_model')
    def test_run_simulation_basic(self, mock_create_model):
        """Test that run_simulation calls the model factory and returns a result."""
        # Set up mock model
        mock_model = MagicMock()
        mock_model.initial_price = self.test_initial_price
        mock_model.mu = 0.08
        mock_model.sigma = 0.2
        
        # Set up mock paths_matrix
        paths_matrix = np.ones((self.test_paths, self.test_steps + 1)) * self.test_initial_price
        mock_model.simulate.return_value = paths_matrix
        
        # Set up mock calculate_statistics
        with patch('stock_sim.analysis.calculate_statistics') as mock_stats:
            mock_stats.return_value = {'mean_return': 0.1, 'std_return': 0.2}
            
            # Set up mock save_simulation_data
            with patch('stock_sim.analysis.save_simulation_data') as mock_save:
                mock_save.return_value = os.path.join(self.engine._data_dir, 'test_data.json')
                
                # Set up mock generate_plots
                with patch('stock_sim.visualization.generate_plots') as mock_plots:
                    mock_plots.return_value = {'main': 'plot1.png', 'histogram': 'plot2.png'}
                    
                    # Mock the model creation
                    mock_create_model.return_value = mock_model
                    
                    # Run simulation
                    result = self.engine.run_simulation(
                        self.test_ticker,
                        model_type='gbm',
                        paths=self.test_paths,
                        steps=self.test_steps,
                        dt=self.test_dt,
                        calibrate=False
                    )
                    
                    # Verify model creation was called
                    mock_create_model.assert_called_once()
                    
                    # Verify model.simulate was called with correct parameters
                    mock_model.simulate.assert_called_once_with(
                        paths=self.test_paths, 
                        steps=self.test_steps, 
                        dt=self.test_dt
                    )
                    
                    # Check that result contains expected keys
                    self.assertIn('ticker', result)
                    self.assertIn('model_type', result)
                    self.assertIn('paths_matrix', result)
                    self.assertIn('statistics', result)
                    self.assertIn('initial_price', result)
                    self.assertIn('model_params', result)
                    self.assertIn('data_path', result)
                    self.assertIn('plot_paths', result)
                    
                    # Check ticker and model_type values
                    self.assertEqual(result['ticker'], self.test_ticker)
                    self.assertEqual(result['model_type'], 'gbm')
    
    def test_request_stop(self):
        """Test that request_stop sets the stop flag for a simulation."""
        # Request stop for a simulation
        sim_id = "test_sim_1"
        result = self.engine.request_stop(sim_id)
        
        # Check that stop was registered
        self.assertTrue(result)
        self.assertTrue(self.engine.is_stop_requested(sim_id))
        
        # Check that None ID returns False
        self.assertFalse(self.engine.request_stop(None))
    
    def test_is_stop_requested(self):
        """Test is_stop_requested returns correct value."""
        # Request stop for a simulation
        sim_id = "test_sim_2"
        self.engine.request_stop(sim_id)
        
        # Check that stop is requested for the simulation
        self.assertTrue(self.engine.is_stop_requested(sim_id))
        
        # Check that stop is not requested for other simulations
        self.assertFalse(self.engine.is_stop_requested("other_sim"))
        self.assertFalse(self.engine.is_stop_requested(None))
    
    @patch('stock_sim.models.ModelFactory.create_model')
    def test_batch_simulate(self, mock_create_model):
        """Test batch_simulate runs simulations for multiple tickers."""
        # Set up mock model
        mock_model = MagicMock()
        mock_model.initial_price = self.test_initial_price
        mock_model.mu = 0.08
        mock_model.sigma = 0.2
        
        # Set up mock paths_matrix
        paths_matrix = np.ones((self.test_paths, self.test_steps + 1)) * self.test_initial_price
        mock_model.simulate.return_value = paths_matrix
        
        # Mock the model creation
        mock_create_model.return_value = mock_model
        
        # Mock the other functions
        with patch('stock_sim.analysis.calculate_statistics') as mock_stats:
            mock_stats.return_value = {'mean_return': 0.1, 'std_return': 0.2}
            
            with patch('stock_sim.analysis.save_simulation_data') as mock_save:
                mock_save.return_value = os.path.join(self.engine._data_dir, 'test_data.json')
                
                with patch('stock_sim.visualization.generate_plots') as mock_plots:
                    mock_plots.return_value = {'main': 'plot1.png', 'histogram': 'plot2.png'}
                    
                    # Run batch simulation
                    tickers = ['AAPL', 'MSFT', 'GOOG']
                    results = self.engine.batch_simulate(
                        tickers,
                        model_type='gbm',
                        paths=self.test_paths,
                        steps=self.test_steps,
                        dt=self.test_dt,
                        calibrate=False
                    )
                    
                    # Check that results contains correct keys
                    self.assertEqual(len(results), len(tickers))
                    for ticker in tickers:
                        self.assertIn(ticker, results)
                        self.assertIn('model_type', results[ticker])
                        self.assertIn('paths_matrix', results[ticker])
                        self.assertIn('statistics', results[ticker])
                        self.assertIn('model_params', results[ticker])


if __name__ == "__main__":
    unittest.main() 