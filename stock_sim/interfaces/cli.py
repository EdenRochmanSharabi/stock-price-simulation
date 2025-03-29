#!/usr/bin/env python3

"""
Command Line Interface
--------------------
Command-line interface for running stock simulations.
"""

import argparse
import sys
import os
import time
from ..simulation_engine import SimulationEngine
from ..utils import SP500TickerManager


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Stock Price Simulation with Regime Switching and Jump Diffusion",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add main arguments
    parser.add_argument('tickers', nargs='*', help='Ticker symbols to simulate')
    
    # Add simulation options
    sim_group = parser.add_argument_group('Simulation Options')
    sim_group.add_argument('-m', '--model', type=str, default='hybrid',
                         choices=['gbm', 'jump', 'hybrid'],
                         help='Simulation model type')
    sim_group.add_argument('-p', '--paths', type=int, default=1000,
                         help='Number of simulation paths')
    sim_group.add_argument('-s', '--steps', type=int, default=21,
                         help='Number of time steps')
    sim_group.add_argument('-c', '--calibrate', action='store_true',
                         help='Calibrate model from historical data')
    sim_group.add_argument('-l', '--lookback', type=str, default='2y',
                         help='Lookback period for historical data')
    
    # Add advanced model parameters
    adv_group = parser.add_argument_group('Advanced Model Parameters')
    adv_group.add_argument('--mu', type=float, help='Drift parameter (annualized)')
    adv_group.add_argument('--sigma', type=float, help='Volatility parameter (annualized)')
    adv_group.add_argument('--jump-intensity', type=float, help='Jump intensity (jumps per year)')
    adv_group.add_argument('--jump-mean', type=float, help='Jump mean size')
    adv_group.add_argument('--jump-sigma', type=float, help='Jump size volatility')
    adv_group.add_argument('--vol-clustering', type=float, help='Volatility clustering parameter')
    
    # Add ticker selection options
    ticker_group = parser.add_argument_group('Ticker Selection')
    ticker_group.add_argument('--sector', type=str, help='Run simulation for a specific sector')
    ticker_group.add_argument('--sector-limit', type=int, default=5,
                            help='Limit of tickers per sector')
    ticker_group.add_argument('--random', type=int, help='Use random tickers (specify count)')
    ticker_group.add_argument('--refresh-tickers', action='store_true',
                            help='Refresh S&P 500 ticker list')
    
    # Add output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('-o', '--output-dir', type=str, default='output',
                            help='Output directory')
    
    return parser.parse_args()


def get_tickers(args):
    """
    Get the list of tickers to simulate based on command-line arguments.
    
    Args:
        args: Command-line arguments
        
    Returns:
        list: List of ticker symbols
    """
    ticker_manager = SP500TickerManager()
    
    # Refresh tickers if requested
    if args.refresh_tickers:
        ticker_manager.refresh_tickers(force=True)
    
    # If explicit tickers are provided, use them
    if args.tickers:
        return args.tickers
    
    # If sector is specified, get tickers for that sector
    if args.sector:
        tickers = ticker_manager.get_ticker_by_sector(args.sector, limit=args.sector_limit)
        if not tickers:
            print(f"No tickers found for sector: {args.sector}")
            print("Available sectors:", ", ".join(ticker_manager.get_sectors()))
            return []
        return tickers
    
    # If random tickers are requested
    if args.random:
        return ticker_manager.get_random_tickers(count=args.random)
    
    # Default to a single well-known ticker if nothing else is specified
    print("No tickers specified, using default: AAPL")
    return ["AAPL"]


def build_model_params(args):
    """Build model parameters from command-line arguments."""
    params = {}
    
    # Add advanced parameters if provided
    if args.mu is not None:
        params['mu'] = args.mu
    if args.sigma is not None:
        params['sigma'] = args.sigma
    if args.jump_intensity is not None:
        params['jump_intensity'] = args.jump_intensity
    if args.jump_mean is not None:
        params['jump_mean'] = args.jump_mean
    if args.jump_sigma is not None:
        params['jump_sigma'] = args.jump_sigma
    if args.vol_clustering is not None:
        params['vol_clustering'] = args.vol_clustering
    
    return params


def main():
    """Main entry point for the command-line interface."""
    # Parse command-line arguments
    args = parse_args()
    
    # Get tickers to simulate
    tickers = get_tickers(args)
    if not tickers:
        print("No tickers to simulate. Exiting.")
        sys.exit(1)
    
    print(f"Running {args.model.upper()} simulation for {len(tickers)} tickers:")
    print(", ".join(tickers))
    
    # Create simulation engine
    engine = SimulationEngine(output_base_dir=args.output_dir)
    
    # Build model parameters
    model_params = build_model_params(args)
    
    # Run simulations
    start_time = time.time()
    results = engine.batch_simulate(
        tickers=tickers,
        model_type=args.model,
        paths=args.paths,
        steps=args.steps,
        calibrate=args.calibrate,
        lookback_period=args.lookback,
        **model_params
    )
    end_time = time.time()
    
    # Print summary
    print("\nSimulation completed in {:.2f} seconds".format(end_time - start_time))
    print(f"Results saved to {os.path.abspath(args.output_dir)}")
    
    # Print brief summary of results
    successful = [t for t, r in results.items() if r is not None]
    failed = [t for t, r in results.items() if r is None]
    
    print(f"Successful simulations: {len(successful)}/{len(tickers)}")
    if failed:
        print(f"Failed simulations: {len(failed)}/{len(tickers)}")
        print("Failed tickers:", ", ".join(failed))
    
    # Return success status
    return 0 if len(successful) > 0 else 1


if __name__ == "__main__":
    sys.exit(main()) 