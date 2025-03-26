"""
Module for implementing regime switching model for stock price simulation.
"""
import numpy as np
from numba import jit

# Define market regimes
BEAR_MARKET = 0
BULL_MARKET = 1

class RegimeSwitchingModel:
    """
    A model for switching between different market regimes (bull/bear).
    
    Uses a Markov chain to transition between regimes.
    """
    
    def __init__(self, transition_matrix=None, initial_regime=None):
        """
        Initialize the regime switching model.
        
        Parameters:
        -----------
        transition_matrix : numpy.ndarray, optional
            2x2 transition probability matrix where:
            - transition_matrix[0,0] = P(bear->bear)
            - transition_matrix[0,1] = P(bear->bull)
            - transition_matrix[1,0] = P(bull->bear)
            - transition_matrix[1,1] = P(bull->bull)
            If None, a default matrix is used.
        initial_regime : int, optional
            Initial regime (0 for bear, 1 for bull).
            If None, it's randomly chosen.
        """
        if transition_matrix is None:
            # Default transition matrix with historically reasonable values
            # Bear market has higher probability to continue in bear state
            # Bull market has higher probability to continue in bull state
            self.transition_matrix = np.array([
                [0.90, 0.10],  # Bear: 90% stay, 10% switch to bull
                [0.05, 0.95]   # Bull: 5% switch to bear, 95% stay
            ])
        else:
            # Validate transition matrix
            if transition_matrix.shape != (2, 2):
                raise ValueError("Transition matrix must be 2x2")
            
            # Ensure rows sum to 1
            if not np.allclose(transition_matrix.sum(axis=1), np.ones(2)):
                raise ValueError("Rows of transition matrix must sum to 1")
                
            self.transition_matrix = transition_matrix
            
        # Set initial regime
        if initial_regime is None:
            # Randomly choose initial regime based on steady-state probabilities
            steady_state = self._calculate_steady_state()
            self.current_regime = np.random.choice([BEAR_MARKET, BULL_MARKET], p=steady_state)
        else:
            if initial_regime not in [BEAR_MARKET, BULL_MARKET]:
                raise ValueError("Initial regime must be 0 (bear) or 1 (bull)")
            self.current_regime = initial_regime
        
        # Initialize regime history
        self.regime_history = [self.current_regime]
        
    def _calculate_steady_state(self):
        """
        Calculate the steady-state probabilities of the Markov chain.
        
        Returns:
        --------
        numpy.ndarray
            Steady-state probability vector [P(bear), P(bull)]
        """
        # For a 2-state Markov chain, steady state can be calculated as:
        # P(bear) = P(bull->bear) / (P(bear->bull) + P(bull->bear))
        # P(bull) = P(bear->bull) / (P(bear->bull) + P(bull->bear))
        p_bull_to_bear = self.transition_matrix[1, 0]
        p_bear_to_bull = self.transition_matrix[0, 1]
        
        p_bear = p_bull_to_bear / (p_bear_to_bull + p_bull_to_bear)
        p_bull = p_bear_to_bull / (p_bear_to_bull + p_bull_to_bear)
        
        return np.array([p_bear, p_bull])
        
    def next_regime(self):
        """
        Transition to the next regime based on transition probabilities.
        
        Returns:
        --------
        int
            New regime (0 for bear, 1 for bull)
        """
        # Get transition probabilities for current regime
        transition_probs = self.transition_matrix[self.current_regime]
        
        # Sample next regime
        self.current_regime = np.random.choice([BEAR_MARKET, BULL_MARKET], p=transition_probs)
        
        # Update regime history
        self.regime_history.append(self.current_regime)
        
        return self.current_regime
    
    def get_regime_parameters(self, base_drift, base_volatility):
        """
        Get drift and volatility parameters based on current regime.
        
        Parameters:
        -----------
        base_drift : float
            Base drift (annualized)
        base_volatility : float
            Base volatility (annualized)
            
        Returns:
        --------
        tuple
            (drift, volatility) for current regime
        """
        if self.current_regime == BEAR_MARKET:
            # Bear market: negative drift, higher volatility
            drift = -0.1  # Fixed negative drift for bear market
            volatility = base_volatility * 1.5  # 50% higher volatility
        else:  # BULL_MARKET
            # Bull market: positive drift, normal volatility
            drift = 0.15  # Fixed positive drift for bull market
            volatility = base_volatility
            
        return drift, volatility
    
    def reset(self, initial_regime=None):
        """
        Reset the model to initial state.
        
        Parameters:
        -----------
        initial_regime : int, optional
            Initial regime (0 for bear, 1 for bull)
            If None, it's randomly chosen.
        """
        if initial_regime is None:
            # Randomly choose initial regime based on steady-state probabilities
            steady_state = self._calculate_steady_state()
            self.current_regime = np.random.choice([BEAR_MARKET, BULL_MARKET], p=steady_state)
        else:
            if initial_regime not in [BEAR_MARKET, BULL_MARKET]:
                raise ValueError("Initial regime must be 0 (bear) or 1 (bull)")
            self.current_regime = initial_regime
            
        # Reset regime history
        self.regime_history = [self.current_regime]

@jit(nopython=True)
def generate_regime_path(transition_matrix, initial_regime, n_steps):
    """
    Generate a regime path using Numba for performance.
    
    Parameters:
    -----------
    transition_matrix : numpy.ndarray
        2x2 transition probability matrix
    initial_regime : int
        Initial regime (0 for bear, 1 for bull)
    n_steps : int
        Number of steps to simulate
        
    Returns:
    --------
    numpy.ndarray
        Array of regime indices (0 for bear, 1 for bull)
    """
    # Initialize regime path
    regime_path = np.zeros(n_steps, dtype=np.int32)
    regime_path[0] = initial_regime
    
    # Generate regime path
    for i in range(1, n_steps):
        # Get transition probabilities for current regime
        current_regime = regime_path[i-1]
        p_stay = transition_matrix[current_regime, current_regime]
        
        # Transition to next regime
        if np.random.random() > p_stay:
            # Switch regime (XOR with 1 flips 0->1 and 1->0)
            regime_path[i] = current_regime ^ 1
        else:
            # Stay in same regime
            regime_path[i] = current_regime
            
    return regime_path

@jit(nopython=True)
def get_regime_parameters_jit(regime, base_drift, base_volatility):
    """
    Get regime-specific parameters using Numba for performance.
    
    Parameters:
    -----------
    regime : int
        Regime (0 for bear, 1 for bull)
    base_drift : float
        Base drift parameter
    base_volatility : float
        Base volatility parameter
        
    Returns:
    --------
    tuple
        (drift, volatility) for the regime
    """
    if regime == 0:  # BEAR_MARKET
        drift = -0.1  # Fixed negative drift for bear market
        volatility = base_volatility * 1.5  # 50% higher volatility
    else:  # BULL_MARKET
        drift = 0.15  # Fixed positive drift for bull market
        volatility = base_volatility
        
    return drift, volatility 