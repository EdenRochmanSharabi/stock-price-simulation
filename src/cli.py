#!/usr/bin/env python
"""
Command-line interface for stock price simulation.
"""
import argparse
import sys
from datetime import datetime

from src.simulation import run_simulation

def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
    --------
    argparse.Namespace
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description='Simulate stock price with regime switching and jump diffusion'
    )
    
    parser.add_argument('ticker', type=str, help='Stock ticker symbol')
    
    parser.add_argument('--paths', type=int, default=1000,
                       help='Number of simulation paths (default: 1000)')
    
    parser.add_argument('--steps', type=int, default=252,
                       help='Number of time steps (default: 252)')
    
    parser.add_argument('--dt', type=float, default=1/252,
                       help='Time step size in years (default: 1/252)')
    
    parser.add_argument('--start-date', type=str, default=None,
                       help='Start date for simulation (default: today)')
    
    parser.add_argument('--no-calibration', action='store_false', dest='use_calibration',
                       help='Disable parameter calibration from historical data')
    
    parser.add_argument('--no-save', action='store_false', dest='save_results',
                       help='Disable saving simulation results')
    
    parser.add_argument('--no-plots', action='store_false', dest='show_plots',
                       help='Disable showing plots')
    
    return parser.parse_args()

def main():
    """
    Main entry point for the CLI.
    """
    args = parse_args()
    
    # Print simulation parameters
    print(f"Simulation Parameters:")
    print(f"=====================")
    print(f"Ticker: {args.ticker}")
    print(f"Number of paths: {args.paths}")
    print(f"Number of steps: {args.steps}")
    print(f"Time step size: {args.dt}")
    print(f"Start date: {args.start_date or 'Today'}")
    print(f"Use calibration: {args.use_calibration}")
    print(f"Save results: {args.save_results}")
    print(f"Show plots: {args.show_plots}")
    print()
    
    # Run simulation
    try:
        results = run_simulation(
            ticker=args.ticker,
            n_paths=args.paths,
            n_steps=args.steps,
            dt=args.dt,
            start_date=args.start_date,
            use_calibration=args.use_calibration,
            save_results=args.save_results,
            show_plots=args.show_plots
        )
        
        return 0
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main()) 