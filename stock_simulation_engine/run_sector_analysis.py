#!/usr/bin/env python3

"""
Run Sector Analysis
--------------------------
Main script to run simulations for multiple stocks across market sectors
and generate consolidated reports.
"""

import os
import pandas as pd
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from modules.engine import run_simulation, create_directory
from reporting import generate_report
from sp500_tickers import load_sector_mapping_from_csv, get_sector_mapping, save_sector_mapping_to_csv

# Load S&P 500 sectors and tickers
def load_sectors():
    """Load sector mapping from CSV or retrieve fresh data."""
    sector_mapping = load_sector_mapping_from_csv()
    if not sector_mapping:
        print("No sector mapping found, retrieving fresh data...")
        sector_mapping = get_sector_mapping()
        save_sector_mapping_to_csv(sector_mapping)
    return sector_mapping

# Initialize sectors
SECTORS = load_sectors()

def run_sector_simulation(sector, tickers, model_type, paths, steps, output_dir):
    """
    Run simulations for all tickers in a sector.
    
    Args:
        sector (str): Sector name
        tickers (list): List of ticker symbols
        model_type (str): Simulation model type
        paths (int): Number of simulation paths
        steps (int): Number of time steps
        output_dir (str): Base output directory
    
    Returns:
        dict: Dictionary of simulation results by ticker
    """
    print(f"\n--- Processing {sector} Sector ---")
    
    # Run simulations for each ticker
    results = {}
    
    for ticker in tickers:
        try:
            # Run the simulation
            result = run_simulation(
                ticker, 
                model_type=model_type, 
                paths=paths, 
                steps=steps, 
                output_dir=output_dir,
                reports_dir=os.path.join(output_dir, "reports"),
                graphs_dir=os.path.join(output_dir, "graphs")
            )
            
            # Store results
            if result:
                results[ticker] = result
                print(f"Simulation for {ticker} completed successfully.")
            else:
                print(f"Warning: Simulation for {ticker} returned None, skipping.")
        except Exception as e:
            print(f"Error processing {ticker}: {str(e)}")
    
    return results


def run_all_simulations(model_type, paths, steps, companies_per_sector, output_dir):
    """
    Run simulations for all sectors and generate reports.
    
    Args:
        model_type (str): Simulation model type
        paths (int): Number of simulation paths
        steps (int): Number of time steps
        companies_per_sector (int): Number of companies to simulate per sector
        output_dir (str): Output directory
    """
    # Create output directories - simplified to just 3 folders
    for subdir in ["data", "reports", "graphs"]:
        create_directory(os.path.join(output_dir, subdir))
    
    # Select tickers to simulate
    all_tickers = []
    selected_tickers = {}
    
    for sector, tickers in SECTORS.items():
        # Take the specified number of companies per sector
        sector_tickers = tickers[:companies_per_sector]
        selected_tickers[sector] = sector_tickers
        all_tickers.extend(sector_tickers)
    
    print(f"Selected {len(all_tickers)} tickers across {len(SECTORS)} sectors")
    
    # Process each sector
    all_results = {}
    
    # Option to use parallel processing
    use_parallel = False
    
    if use_parallel:
        # Parallel execution
        with ProcessPoolExecutor() as executor:
            futures = {
                executor.submit(
                    run_sector_simulation, 
                    sector, 
                    tickers, 
                    model_type, 
                    paths, 
                    steps, 
                    output_dir
                ): sector 
                for sector, tickers in selected_tickers.items()
            }
            
            for future in as_completed(futures):
                sector = futures[future]
                try:
                    sector_results = future.result()
                    all_results.update(sector_results)
                except Exception as e:
                    print(f"Error processing sector {sector}: {str(e)}")
    else:
        # Sequential execution
        for sector, tickers in selected_tickers.items():
            sector_results = run_sector_simulation(
                sector, 
                tickers, 
                model_type, 
                paths, 
                steps, 
                output_dir
            )
            all_results.update(sector_results)
    
    # Generate consolidated report
    print(f"Processed {len(all_results)} tickers across {len(SECTORS)} sectors.")
    if all_results:
        # Add sector information to each result
        for ticker, result in all_results.items():
            for sector, tickers in selected_tickers.items():
                if ticker in tickers:
                    result['sector'] = sector
                    break
        
        # Generate report
        generate_report(all_results, output_dir)
    else:
        print("No simulation results to generate report from.")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Run stock price simulations for multiple companies across sectors',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--model', type=str, default='combined',
                      choices=['gbm', 'jump', 'combined'],
                      help='Simulation model type')
    parser.add_argument('--paths', type=int, default=1000,
                      help='Number of simulation paths')
    parser.add_argument('--steps', type=int, default=21,
                      help='Number of time steps (trading days)')
    parser.add_argument('--companies', type=int, default=3,
                      help='Number of companies per sector')
    parser.add_argument('--output-dir', type=str, default='output',
                      help='Output directory')
    parser.add_argument('--high-precision', action='store_true',
                      help='Use high-precision simulation (more paths)')
    
    return parser.parse_args()


def main():
    """Main execution function."""
    # Parse arguments
    args = parse_arguments()
    
    # Set paths to higher value if high precision is requested
    if args.high_precision:
        args.paths = 10000
        print(f"High precision mode enabled: using {args.paths:,} simulation paths")
    
    print(f"Stock Price Simulation with {args.model.upper()} model")
    print(f"Paths: {args.paths}, Steps: {args.steps}, Companies per sector: {args.companies}")
    print(f"Output directory: {args.output_dir}")
    
    # Run simulations
    run_all_simulations(
        args.model, 
        args.paths, 
        args.steps, 
        args.companies, 
        args.output_dir
    )


if __name__ == "__main__":
    main() 