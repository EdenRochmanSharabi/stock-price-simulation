#!/usr/bin/env python3

"""
Test Analysis and Reporting
-------------------------
Unit tests for the analysis and reporting components with strict verification.
"""

from test_base import BaseTestCase
import os
import json
import numpy as np
from unittest.mock import patch, MagicMock
import matplotlib.pyplot as plt
from stock_sim.analysis import calculate_statistics, save_simulation_data
from stock_sim.analysis.reporting import generate_stock_report, generate_batch_report
from stock_sim.analysis.statistics import calculate_max_drawdown, calculate_max_drawdown_across_paths


class TestAnalysis(BaseTestCase):
    """Test cases for the analysis and reporting components with strict verification."""
    
    def setUp(self):
        """Set up test fixtures."""
        super().setUp()
        
        # Create a sample paths matrix for testing
        self.paths_matrix = np.ones((self.test_paths, self.test_steps + 1)) * self.test_initial_price
        
        # Create a deterministic test path matrix for strict verification
        self.deterministic_paths = np.array([
            [100, 110, 90, 95, 105],  # Path 1: Known drawdown
            [100, 105, 115, 110, 120],  # Path 2: Upward trend
            [100, 95, 90, 85, 80],   # Path 3: Downward trend
            [100, 100, 100, 100, 100],  # Path 4: Flat
            [100, 110, 120, 90, 110]   # Path 5: Volatile
        ])
        
        # Add a simple increasing trend with controlled volatility
        for i in range(1, self.test_steps + 1):
            self.paths_matrix[:, i] = self.paths_matrix[:, i-1] * (1 + 0.01 * np.random.randn(self.test_paths))
    
    def test_calculate_statistics_exact_values(self):
        """Test statistics calculation with known exact values."""
        # Use deterministic paths for exact calculations
        stats = calculate_statistics(self.test_ticker, self.deterministic_paths, 100.0)
        
        # Test exact values for basic statistics
        self.assertEqual(stats['initial_price'], 100.0)
        self.assertAlmostEqual(stats['mean_final_price'], 103.0)  # Average of [105, 120, 80, 100, 110]
        self.assertAlmostEqual(stats['median_final_price'], 105.0)
        self.assertAlmostEqual(stats['min_final_price'], 80.0)
        self.assertAlmostEqual(stats['max_final_price'], 120.0)
        
        # Test exact percentiles
        self.assertAlmostEqual(stats['percentiles']['50%'], 105.0)
        
        # Test exact returns
        expected_return = (103.0 / 100.0 - 1) * 100  # 3%
        self.assertAlmostEqual(stats['expected_return'], expected_return)
        
        # Test exact probabilities
        self.assertAlmostEqual(stats['prob_profit'], 60.0)  # 3 out of 5 paths end higher
        self.assertAlmostEqual(stats['prob_loss'], 40.0)   # 2 out of 5 paths end lower
        
        # Test exact risk metrics
        self.assertAlmostEqual(stats['max_drawdown'], 0.25)  # Maximum 25% drawdown in path 5
    
    def test_calculate_statistics_edge_cases(self):
        """Test statistics calculation with edge cases."""
        # Test case 1: All constant values
        constant_paths = np.full((5, 5), 100.0)
        stats_constant = calculate_statistics(self.test_ticker, constant_paths, 100.0)
        
        self.assertAlmostEqual(stats_constant['return_volatility'], 0.0)
        self.assertAlmostEqual(stats_constant['max_drawdown'], 0.0)
        self.assertAlmostEqual(stats_constant['expected_return'], 0.0)
        self.assertAlmostEqual(stats_constant['var_95'], 0.0)
        self.assertAlmostEqual(stats_constant['var_99'], 0.0)
        
        # Test case 2: Extreme values
        extreme_paths = np.array([
            [100, 1000, 10000, 100000, 1000000],  # Extreme growth
            [100, 10, 1, 0.1, 0.01],              # Extreme decline
            [100, 100, 100, 100, 100],            # No change
            [100, -100, 100, -100, 100],          # Alternating
            [100, np.inf, np.inf, np.inf, np.inf] # Infinity
        ])
        
        stats_extreme = calculate_statistics(self.test_ticker, extreme_paths, 100.0)
        self.assertTrue(np.isfinite(stats_extreme['return_volatility']))
        self.assertTrue(np.isfinite(stats_extreme['max_drawdown']))
        self.assertTrue(np.isfinite(stats_extreme['expected_return']))
        
        # Test case 3: Single path
        single_path = np.array([[100, 110, 90, 95, 105]])
        stats_single = calculate_statistics(self.test_ticker, single_path, 100.0)
        
        self.assertAlmostEqual(stats_single['mean_final_price'], 105.0)
        self.assertAlmostEqual(stats_single['median_final_price'], 105.0)
        
        # Test case 4: NaN values
        nan_paths = np.array([
            [100, 110, np.nan, 95, 105],
            [100, 105, 115, np.nan, 120]
        ])
        
        stats_nan = calculate_statistics(self.test_ticker, nan_paths, 100.0)
        self.assertTrue(np.isfinite(stats_nan['expected_return']))
        self.assertTrue(np.isfinite(stats_nan['return_volatility']))
    
    def test_calculate_max_drawdown_strict(self):
        """Test maximum drawdown calculation with strict verification."""
        # Test case 1: Known drawdown pattern
        test_paths = np.array([
            [100, 110, 90, 95, 105],    # Max drawdown: (110-90)/110 = 0.1818
            [100, 120, 60, 80, 100],    # Max drawdown: (120-60)/120 = 0.5000
            [100, 100, 100, 100, 100],  # Max drawdown: 0
            [100, 90, 80, 70, 60],      # Max drawdown: 0.4000
            [100, 110, 120, 130, 140]   # Max drawdown: 0
        ])
        
        max_dd = calculate_max_drawdown(test_paths)
        expected_max_dd = (0.1818 + 0.5000 + 0.0 + 0.4000 + 0.0) / 5
        self.assertAlmostEqual(max_dd, expected_max_dd, places=4)
        
        # Test case 2: No drawdown
        no_drawdown_paths = np.array([
            [100, 110, 120, 130, 140],
            [100, 100, 100, 100, 100]
        ])
        self.assertAlmostEqual(calculate_max_drawdown(no_drawdown_paths), 0.0)
        
        # Test case 3: Complete loss
        complete_loss_paths = np.array([
            [100, 50, 0, 0, 0],
            [100, 75, 50, 25, 0]
        ])
        self.assertAlmostEqual(calculate_max_drawdown(complete_loss_paths), 1.0)
        
        # Test case 4: Maximum drawdown across paths
        max_dd_across = calculate_max_drawdown_across_paths(test_paths)
        self.assertAlmostEqual(max_dd_across, 0.5, places=4)  # Maximum drawdown is 50% in path 2
    
    def test_calculate_statistics_consistency(self):
        """Test internal consistency of statistical calculations."""
        stats = calculate_statistics(self.test_ticker, self.deterministic_paths, 100.0)
        
        # Test probability consistency
        self.assertAlmostEqual(stats['prob_profit'] + stats['prob_loss'], 100.0)
        
        # Test percentile consistency
        self.assertGreaterEqual(stats['percentiles']['99%'], stats['percentiles']['95%'])
        self.assertGreaterEqual(stats['percentiles']['95%'], stats['percentiles']['90%'])
        self.assertGreaterEqual(stats['percentiles']['90%'], stats['percentiles']['75%'])
        self.assertGreaterEqual(stats['percentiles']['75%'], stats['percentiles']['50%'])
        self.assertGreaterEqual(stats['percentiles']['50%'], stats['percentiles']['25%'])
        self.assertGreaterEqual(stats['percentiles']['25%'], stats['percentiles']['10%'])
        self.assertGreaterEqual(stats['percentiles']['10%'], stats['percentiles']['5%'])
        self.assertGreaterEqual(stats['percentiles']['5%'], stats['percentiles']['1%'])
        
        # Test VaR consistency
        self.assertGreaterEqual(stats['var_99'], stats['var_95'])
        
        # Test return consistency
        if stats['return_volatility'] > 0:
            self.assertTrue(np.isfinite(stats['sharpe_ratio']))
            self.assertTrue(np.isfinite(stats['sortino_ratio']))
        
        # Test confidence interval consistency
        self.assertLess(stats['return_ci_lower'], stats['expected_return'])
        self.assertGreater(stats['return_ci_upper'], stats['expected_return'])
    
    def test_calculate_statistics_numerical_stability(self):
        """Test numerical stability with extreme values."""
        # Create paths with very large and very small values
        extreme_paths = np.array([
            [1e-10, 1e-9, 1e-8, 1e-7, 1e-6],
            [1e6, 1e7, 1e8, 1e9, 1e10],
            [1.0, 1.1, 1.2, 1.3, 1.4],
            [-1e6, -1e7, -1e8, -1e9, -1e10],
            [0.0, 0.0, 0.0, 0.0, 0.0]
        ])
        
        stats = calculate_statistics(self.test_ticker, extreme_paths, 1.0)
        
        # Check that all statistics are finite
        for key, value in stats.items():
            if isinstance(value, (float, np.ndarray)):
                self.assertTrue(np.all(np.isfinite(value)), f"Non-finite value in {key}")
            elif isinstance(value, dict):
                for subkey, subvalue in value.items():
                    if isinstance(subvalue, (float, np.ndarray)):
                        self.assertTrue(np.all(np.isfinite(subvalue)), 
                                     f"Non-finite value in {key}.{subkey}")

    def test_calculate_statistics_basic(self):
        """Test basic statistics calculation."""
        stats = calculate_statistics(self.test_ticker, self.paths_matrix, self.test_initial_price)
        
        # Check basic statistics
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats['ticker'], self.test_ticker)
        self.assertEqual(stats['initial_price'], self.test_initial_price)
        self.assertGreater(stats['mean_final_price'], 0)
        self.assertGreater(stats['median_final_price'], 0)
        self.assertGreaterEqual(stats['max_final_price'], stats['min_final_price'])
    
    def test_calculate_statistics_percentiles(self):
        """Test percentile calculations."""
        stats = calculate_statistics(self.test_ticker, self.paths_matrix, self.test_initial_price)
        
        # Check percentiles
        percentiles = stats['percentiles']
        required_percentiles = ['1%', '5%', '10%', '25%', '50%', '75%', '90%', '95%', '99%']
        
        for p in required_percentiles:
            self.assertIn(p, percentiles)
            self.assertIsInstance(percentiles[p], float)
        
        # Check percentile ordering
        self.assertLess(percentiles['1%'], percentiles['50%'])
        self.assertLess(percentiles['50%'], percentiles['99%'])
    
    def test_calculate_statistics_returns(self):
        """Test return calculations."""
        stats = calculate_statistics(self.test_ticker, self.paths_matrix, self.test_initial_price)
        
        # Check return metrics
        self.assertIsInstance(stats['expected_return'], float)
        self.assertIsInstance(stats['median_return'], float)
        self.assertIsInstance(stats['return_volatility'], float)
        self.assertGreaterEqual(stats['return_volatility'], 0)
    
    def test_calculate_statistics_risk_metrics(self):
        """Test risk metric calculations."""
        stats = calculate_statistics(self.test_ticker, self.paths_matrix, self.test_initial_price)
        
        # Check risk metrics
        self.assertIsInstance(stats['var_95'], float)
        self.assertIsInstance(stats['var_99'], float)
        self.assertIsInstance(stats['max_drawdown'], float)
        self.assertGreaterEqual(stats['var_99'], stats['var_95'])  # 99% VaR should be greater than 95% VaR
        self.assertGreaterEqual(stats['max_drawdown'], 0)  # Max drawdown should be non-negative
        self.assertLessEqual(stats['max_drawdown'], 1)  # Max drawdown should be less than or equal to 1
    
    def test_calculate_statistics_probabilities(self):
        """Test probability calculations."""
        stats = calculate_statistics(self.test_ticker, self.paths_matrix, self.test_initial_price)
        
        # Check probability metrics
        self.assertIsInstance(stats['prob_profit'], float)
        self.assertIsInstance(stats['prob_loss'], float)
        self.assertIsInstance(stats['prob_up_10percent'], float)
        self.assertIsInstance(stats['prob_up_20percent'], float)
        self.assertIsInstance(stats['prob_down_10percent'], float)
        self.assertIsInstance(stats['prob_down_20percent'], float)
        
        # Check probability ranges
        for prob in [stats['prob_profit'], stats['prob_loss'], 
                    stats['prob_up_10percent'], stats['prob_up_20percent'],
                    stats['prob_down_10percent'], stats['prob_down_20percent']]:
            self.assertGreaterEqual(prob, 0)
            self.assertLessEqual(prob, 100)
    
    def test_calculate_statistics_advanced(self):
        """Test advanced statistical calculations."""
        stats = calculate_statistics(self.test_ticker, self.paths_matrix, self.test_initial_price)
        
        # Check advanced statistics
        self.assertIsInstance(stats['skewness'], (float, type(None)))
        self.assertIsInstance(stats['kurtosis'], (float, type(None)))
        self.assertIsInstance(stats['t_stat'], (float, type(None)))
        self.assertIsInstance(stats['p_value'], (float, type(None)))
        self.assertIsInstance(stats['normality_stat'], (float, type(None)))
        self.assertIsInstance(stats['normality_p'], (float, type(None)))
        self.assertIsInstance(stats['normality_test'], (str, type(None)))
    
    def test_calculate_statistics_risk_adjusted_returns(self):
        """Test risk-adjusted return calculations."""
        stats = calculate_statistics(self.test_ticker, self.paths_matrix, self.test_initial_price)
        
        # Check risk-adjusted return metrics
        self.assertIsInstance(stats['sharpe_ratio'], float)
        self.assertIsInstance(stats['sortino_ratio'], float)
        self.assertIsInstance(stats['return_ci_lower'], float)
        self.assertIsInstance(stats['return_ci_upper'], float)
        
        # Check confidence interval ordering
        self.assertLess(stats['return_ci_lower'], stats['return_ci_upper'])
    
    @patch('stock_sim.analysis.data_storage.os.path.exists')
    @patch('stock_sim.analysis.data_storage.os.makedirs')
    @patch('stock_sim.analysis.data_storage.open', new_callable=MagicMock)
    @patch('pandas.DataFrame.to_csv')
    @patch('numpy.savetxt')
    @patch('json.dump')
    def test_save_simulation_data(self, mock_json_dump, mock_savetxt, mock_to_csv, mock_open, mock_makedirs, mock_exists):
        """Test the save_simulation_data function."""
        # Mock file operations
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value = MagicMock()
        
        # Create output directory
        output_dir = self.get_output_dir()
        
        # Calculate statistics using deterministic paths for verification
        stats = calculate_statistics(self.test_ticker, self.deterministic_paths, 100.0)
        
        # Save the data
        save_simulation_data(self.test_ticker, self.deterministic_paths, stats, output_dir)
        
        # Verify mock functions were called with correct data
        self.assertTrue(mock_exists.called or mock_makedirs.called)
        self.assertTrue(mock_to_csv.called or mock_savetxt.called or mock_json_dump.called)
        
        # Verify the saved statistics match the calculated ones
        mock_json_dump.assert_called()
        saved_stats = mock_json_dump.call_args[0][0]
        self.assertEqual(saved_stats['initial_price'], 100.0)
        self.assertAlmostEqual(saved_stats['mean_final_price'], 103.0)
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('os.path.exists')
    @patch('stock_sim.analysis.reporting.open', new_callable=MagicMock)
    def test_generate_stock_report(self, mock_open, mock_exists, mock_figure, mock_savefig):
        """Test the generate_stock_report function."""
        # Mock file operations
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "{{ticker}} {{model_type}}"
        mock_open.return_value.__enter__.return_value.write = MagicMock()
        
        # Create output directory
        output_dir = self.get_output_dir()
        os.makedirs(output_dir, exist_ok=True)  # Ensure directory exists
        
        # Calculate statistics
        stats = calculate_statistics(self.test_ticker, self.paths_matrix, self.test_initial_price)
        
        # Create a result dictionary
        result = {
            'ticker': self.test_ticker,
            'model_type': 'gbm',
            'paths_matrix': self.paths_matrix,
            'statistics': stats,
            'initial_price': self.test_initial_price,
            'model_params': {'mu': 0.05, 'sigma': 0.2},
            'plot_paths': {'main': 'plot1.png', 'histogram': 'plot2.png'}
        }
        
        # Mock matplotlib
        mock_fig = MagicMock()
        mock_figure.return_value = mock_fig
        mock_savefig.return_value = None
        
        # Generate the report
        with patch('stock_sim.visualization.generate_plots') as mock_plots:
            mock_plots.return_value = {'main': 'plot1.png', 'histogram': 'plot2.png'}
            generate_stock_report(self.test_ticker, result, output_dir)
            self.assertTrue(mock_open.called)
    
    @patch('matplotlib.pyplot.savefig')
    @patch('matplotlib.pyplot.figure')
    @patch('os.path.exists')
    @patch('stock_sim.analysis.reporting.open', new_callable=MagicMock)
    def test_generate_batch_report(self, mock_open, mock_exists, mock_figure, mock_savefig):
        """Test the generate_batch_report function."""
        # Mock file operations
        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "{{tickers|join(',')}} {{model_type}}"
        mock_open.return_value.__enter__.return_value.write = MagicMock()
        
        # Create output directory
        output_dir = self.get_output_dir()
        
        # Calculate statistics for multiple tickers
        stats1 = calculate_statistics('AAPL', self.paths_matrix, self.test_initial_price)
        stats2 = calculate_statistics('MSFT', self.paths_matrix * 1.2, self.test_initial_price * 1.2)
        
        # Create batch results
        batch_results = {
            'AAPL': {
                'ticker': 'AAPL',
                'model_type': 'gbm',
                'paths_matrix': self.paths_matrix,
                'statistics': stats1,
                'initial_price': self.test_initial_price,
                'model_params': {'mu': 0.05, 'sigma': 0.2},
                'plot_paths': {'main': 'plot1.png', 'histogram': 'plot2.png'}
            },
            'MSFT': {
                'ticker': 'MSFT',
                'model_type': 'jump',
                'paths_matrix': self.paths_matrix * 1.2,
                'statistics': stats2,
                'initial_price': self.test_initial_price * 1.2,
                'model_params': {'mu': 0.06, 'sigma': 0.15},
                'plot_paths': {'main': 'plot3.png', 'histogram': 'plot4.png'}
            }
        }
        
        # Mock matplotlib
        mock_fig = MagicMock()
        mock_figure.return_value = mock_fig
        mock_savefig.return_value = None
        
        # Generate the report
        with patch('stock_sim.visualization.generate_plots') as mock_plots:
            mock_plots.return_value = {'main': 'plot1.png', 'histogram': 'plot2.png'}
            generate_batch_report(batch_results, output_dir)
            self.assertTrue(mock_open.called)


if __name__ == "__main__":
    unittest.main() 