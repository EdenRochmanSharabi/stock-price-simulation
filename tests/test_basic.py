"""
Basic tests for stock price simulation modules.
"""
import sys
import os
import unittest
import numpy as np
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_retrieval import fetch_stock_data
from src.regime_switching import RegimeSwitchingModel, generate_regime_path
from src.jump_diffusion import JumpDiffusionModel, generate_jump_diffusion_path
from src.earnings_shocks import EarningsShockModel
from src.utils import generate_dates

class TestDataRetrieval(unittest.TestCase):
    """Test the data retrieval module."""
    
    def test_fetch_stock_data(self):
        """Test fetching stock data."""
        # This test requires internet connection
        ticker = "AAPL"
        stock_data = fetch_stock_data(ticker, period="1mo", save_to_file=False)
        
        # Check if data is not None and has expected columns
        self.assertIsNotNone(stock_data)
        self.assertIn('Adj Close', stock_data.columns)
        self.assertIn('Volume', stock_data.columns)
        
        # Check if data has some rows
        self.assertGreater(len(stock_data), 0)

class TestRegimeSwitching(unittest.TestCase):
    """Test the regime switching module."""
    
    def test_regime_model_initialization(self):
        """Test regime switching model initialization."""
        model = RegimeSwitchingModel()
        
        # Check if transition matrix is valid
        self.assertEqual(model.transition_matrix.shape, (2, 2))
        self.assertTrue(np.allclose(model.transition_matrix.sum(axis=1), np.ones(2)))
        
        # Check if current regime and history are initialized
        self.assertIn(model.current_regime, [0, 1])
        self.assertEqual(len(model.regime_history), 1)
    
    def test_regime_transitions(self):
        """Test regime transitions."""
        model = RegimeSwitchingModel()
        
        # Generate transitions
        initial_regime = model.current_regime
        transitions = []
        
        for _ in range(100):
            regime = model.next_regime()
            transitions.append(regime)
        
        # Check if transitions include both regimes
        self.assertTrue(0 in transitions or 1 in transitions)
        
        # Check if regime history is updated correctly
        self.assertEqual(len(model.regime_history), 101)  # Initial + 100 transitions
    
    def test_generate_regime_path(self):
        """Test generating a regime path with Numba."""
        n_steps = 252
        transition_matrix = np.array([
            [0.90, 0.10],
            [0.05, 0.95]
        ])
        initial_regime = 1
        
        path = generate_regime_path(transition_matrix, initial_regime, n_steps)
        
        # Check path length and values
        self.assertEqual(len(path), n_steps)
        self.assertTrue(all(regime in [0, 1] for regime in path))
        self.assertEqual(path[0], initial_regime)

class TestJumpDiffusion(unittest.TestCase):
    """Test the jump diffusion module."""
    
    def test_jump_model_initialization(self):
        """Test jump diffusion model initialization."""
        model = JumpDiffusionModel()
        
        # Check default parameters
        self.assertEqual(model.lambda_, 0.1)
        self.assertEqual(model.mu_j, -0.05)
        self.assertEqual(model.sigma_j, 0.1)
        
        # Check empty history
        self.assertEqual(len(model.jump_times), 0)
        self.assertEqual(len(model.jump_sizes), 0)
    
    def test_generate_jump(self):
        """Test jump generation."""
        model = JumpDiffusionModel(lambda_=10)  # High intensity for testing
        dt = 1/252
        
        # Generate jumps multiple times
        jump_results = []
        for _ in range(100):
            jump_occurs, jump_size = model.generate_jump(dt)
            jump_results.append(jump_occurs)
        
        # Check if at least some jumps occurred
        self.assertTrue(any(jump_results))
        
        # Check jump history
        self.assertGreater(len(model.jump_times), 0)
        self.assertGreater(len(model.jump_sizes), 0)
        self.assertEqual(len(model.jump_times), len(model.jump_sizes))
    
    def test_generate_jump_diffusion_path(self):
        """Test generating a jump diffusion path with Numba."""
        n_steps = 252
        dt = 1/252
        lambda_ = 0.5
        mu_j = -0.05
        sigma_j = 0.1
        
        jump_indicators, jump_sizes = generate_jump_diffusion_path(
            n_steps, dt, lambda_, mu_j, sigma_j
        )
        
        # Check arrays dimensions
        self.assertEqual(len(jump_indicators), n_steps)
        self.assertEqual(len(jump_sizes), n_steps)
        
        # Check if some jumps occurred
        self.assertTrue(any(jump_indicators))
        
        # Check if jump sizes are non-zero only where indicators are True
        for i in range(n_steps):
            if jump_indicators[i]:
                self.assertNotEqual(jump_sizes[i], 0.0)
            else:
                self.assertEqual(jump_sizes[i], 0.0)

class TestEarningsShocks(unittest.TestCase):
    """Test the earnings shocks module."""
    
    def test_earnings_model_initialization(self):
        """Test earnings shock model initialization."""
        # Create some test earnings dates
        earnings_dates = [
            datetime.now(),
            datetime.now().replace(month=(datetime.now().month % 12) + 1)
        ]
        
        model = EarningsShockModel(earnings_dates=earnings_dates)
        
        # Check parameters
        self.assertEqual(model.shock_mean, 0.0)
        self.assertEqual(model.shock_std, 0.05)
        self.assertEqual(model.pre_earnings_drift, 0.01)
        self.assertEqual(len(model.earnings_dates), 2)
        
        # Check empty history
        self.assertEqual(len(model.shock_history), 0)
    
    def test_is_earnings_day(self):
        """Test checking if a date is an earnings date."""
        # Create earnings dates
        today = datetime.now()
        earnings_dates = [today]
        
        model = EarningsShockModel(earnings_dates=earnings_dates)
        
        # Check same day
        self.assertTrue(model.is_earnings_day(today))
        
        # Check day within tolerance
        next_day = today.replace(day=(today.day % 28) + 1)
        self.assertTrue(model.is_earnings_day(next_day))
        
        # Check day outside tolerance
        far_day = today.replace(month=(today.month % 12) + 1)
        self.assertFalse(model.is_earnings_day(far_day))

class TestUtils(unittest.TestCase):
    """Test utility functions."""
    
    def test_generate_dates(self):
        """Test date generation."""
        n_steps = 252
        dates = generate_dates(n_steps=n_steps)
        
        # Check correct length
        self.assertEqual(len(dates), n_steps)
        
        # Check it's a DatetimeIndex
        self.assertIsInstance(dates, pd.DatetimeIndex)
        
        # Check business day frequency
        for i in range(1, len(dates)):
            days_diff = (dates[i] - dates[i-1]).days
            self.assertLessEqual(days_diff, 3)  # Max 3 days between business days (weekend + holiday)

if __name__ == '__main__':
    unittest.main() 