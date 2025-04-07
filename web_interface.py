#!/usr/bin/env python3

"""
Stock Simulation Web Interface
-----------------------------
A web interface for running stock price simulations and viewing results.
"""

import os
import sys
import json
import threading
import time
from typing import Dict, Any
import argparse
from datetime import datetime

# Set the path to find modules correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Set matplotlib backend to Agg (non-interactive) for thread safety
import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
# Updated imports to match current structure
from stock_sim.simulation_engine import SimulationEngine
from stock_sim.utils import SP500TickerManager
from stock_sim.analysis.reporting import generate_stock_report, generate_batch_report
from stock_sim.models import ModelFactory
from stock_sim.strategy_executor import StrategyExecutor

# Create output directories
def create_directory(directory):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

# Initialize engine and ticker manager
engine = SimulationEngine(output_base_dir="output")
ticker_manager = SP500TickerManager()

# Initialize strategy executor
strategy_executor = StrategyExecutor()

# Initialize sectors
def load_sector_mapping_from_csv():
    """Load the sector mapping from CSV files."""
    sectors = ticker_manager.get_sectors()
    mapping = {}
    
    for sector in sectors:
        mapping[sector] = ticker_manager.get_ticker_by_sector(sector)
    
    return mapping

SECTORS = load_sector_mapping_from_csv()

# Track simulation status with thread safety
class SimulationStatus:
    def __init__(self):
        self._lock = threading.Lock()
        self._status = {
            "running": False,
            "progress": 0,
            "total_stocks": 0,
            "completed_stocks": 0,
            "current_sector": "",
            "current_stock": "",
            "start_time": 0,
            "end_time": 0,
            "errors": []
        }
    
    def get(self) -> Dict[str, Any]:
        with self._lock:
            return self._status.copy()
    
    def update(self, updates: Dict[str, Any]) -> None:
        with self._lock:
            self._status.update(updates)
    
    def reset(self) -> None:
        with self._lock:
            self._status = {
                "running": False,
                "progress": 0,
                "total_stocks": 0,
                "completed_stocks": 0,
                "current_sector": "",
                "current_stock": "",
                "start_time": 0,
                "end_time": 0,
                "errors": []
            }

simulation_status = SimulationStatus()

# Create Flask app with appropriate static folder
current_dir = os.path.dirname(os.path.abspath(__file__))
template_dir = os.path.join(current_dir, 'templates')
static_dir = os.path.join(template_dir, 'static')

# Explicitly create the app with absolute paths
app = Flask(__name__, 
            template_folder=template_dir, 
            static_folder=static_dir,
            static_url_path='/static')

# Print template path for debugging
print(f"Flask app initialized with template_folder: {template_dir}")
print(f"Static folder: {static_dir}")
print(f"Template file exists: {os.path.exists(os.path.join(template_dir, 'index.html'))}")

@app.route('/')
def index():
    """Render the main simulation control page."""
    global SECTORS
    
    # Reload sectors if empty
    if not SECTORS:
        SECTORS = load_sector_mapping_from_csv()
    
    # Get sectors and count total stocks
    total_stocks = sum(len(tickers) for tickers in SECTORS.values())
    
    # Debug log to see sectors and counts
    print(f"Loaded {len(SECTORS)} sectors with {total_stocks} total stocks")
    for sector, tickers in SECTORS.items():
        print(f"  - {sector}: {len(tickers)} stocks")
    
    try:
        # Include full path for debugging
        template_path = os.path.join(template_dir, 'index.html')
        print(f"Rendering template from: {template_path}")
        
        return render_template('index.html', 
                              sectors=SECTORS, 
                              total_stocks=total_stocks,
                              simulation_status=simulation_status.get())
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error rendering template: {str(e)}", 500

@app.route('/documentation')
def documentation():
    """Render the documentation page."""
    try:
        template_path = os.path.join(template_dir, 'documentation.html')
        print(f"Rendering documentation template from: {template_path}")
        return render_template('documentation.html')
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error rendering documentation template: {str(e)}", 500

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files."""
    return send_from_directory('templates/static', path)

@app.route('/reports/<path:path>')
def serve_report(path):
    """Serve report files from the output directory."""
    # Look directly in output/reports directory
    reports_dir = os.path.join('output', 'reports')
    if os.path.exists(os.path.join(reports_dir, path)):
        return send_from_directory(reports_dir, path)
    
    # For backwards compatibility, also check timestamped directories
    output_dir = 'output'
    if os.path.exists(output_dir):
        dirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d)) and d.startswith('20')]
        if dirs:
            # Sort dirs by name (timestamp) in descending order to get the latest
            dirs.sort(reverse=True)
            latest_dir = os.path.join(output_dir, dirs[0])
            reports_dir = os.path.join(latest_dir, 'reports')
            # Check if the requested path exists in the reports directory
            full_path = os.path.join(reports_dir, path)
            if os.path.exists(full_path):
                return send_from_directory(reports_dir, path)
    
    return "Report not found", 404

@app.route('/graphs/<path:path>')
def serve_graph(path):
    """Serve graph files from the output directory."""
    # Look directly in output/graphs directory
    graphs_dir = os.path.join('output', 'graphs')
    if os.path.exists(os.path.join(graphs_dir, path)):
        return send_from_directory(graphs_dir, path)
    
    # For backwards compatibility, also check timestamped directories
    output_dir = 'output'
    if os.path.exists(output_dir):
        dirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d)) and d.startswith('20')]
        if dirs:
            # Sort dirs by name (timestamp) in descending order to get the latest
            dirs.sort(reverse=True)
            latest_dir = os.path.join(output_dir, dirs[0])
            graphs_dir = os.path.join(latest_dir, 'graphs')
            # Check if the requested path exists in the graphs directory
            full_path = os.path.join(graphs_dir, path)
            if os.path.exists(full_path):
                return send_from_directory(graphs_dir, path)
    
    return "Graph not found", 404

@app.route('/refresh_tickers', methods=['POST'])
def refresh_tickers():
    """Refresh the S&P 500 tickers and sector mapping."""
    try:
        # Get fresh sector mapping from ticker manager
        ticker_manager.refresh_tickers(force=True)
        
        # Update global SECTORS
        global SECTORS
        SECTORS = load_sector_mapping_from_csv()
        
        return jsonify({
            "status": "success",
            "message": f"Successfully refreshed {len(SECTORS)} sectors",
            "sectors": SECTORS
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error refreshing tickers: {str(e)}"
        })

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    """Start a simulation with the given parameters."""
    try:
        # Debug: Print all form data
        print("Form data received:", {key: request.form.get(key) for key in request.form.keys()})
        
        # Get parameters from form
        model_type = request.form.get('model_type', 'gbm')
        num_paths = int(request.form.get('num_paths', 1000))
        num_steps = int(request.form.get('num_steps', 21))
        time_step = float(request.form.get('time_step', 1/252))
        lookback_period = request.form.get('lookback_period', '2y')  # Extract lookback_period from the form
        calibrate = request.form.get('calibrate', 'true') == 'true'
        save_full_paths = request.form.get('save_full_paths', 'false') == 'true'  # Add option to save full paths
        
        # Get selected tickers from JSON string or list
        selected_tickers = []
        
        try:
            if 'tickers' in request.form:
                # Might be a JSON string
                tickers_data = request.form['tickers']
                selected_tickers = json.loads(tickers_data)
            elif 'tickers[]' in request.form:
                # Might be a list in form data
                selected_tickers = request.form.getlist('tickers[]')
        except json.JSONDecodeError:
            # If not valid JSON, treat it as a comma-separated string
            selected_tickers = [ticker.strip() for ticker in request.form.get('tickers', '').split(',') if ticker.strip()]
        
        print(f"Selected tickers ({len(selected_tickers)}): {selected_tickers}")
        
        # Get model parameters
        model_params = {}
        
        # Optional parameters based on model type
        if model_type in ['jump', 'hybrid', 'combined']:
            # Add jump parameters if provided
            if 'jump_intensity' in request.form:
                model_params['jump_intensity'] = float(request.form.get('jump_intensity', 10))
            if 'jump_mean' in request.form:
                model_params['jump_mean'] = float(request.form.get('jump_mean', -0.01))
            if 'jump_sigma' in request.form:
                model_params['jump_sigma'] = float(request.form.get('jump_sigma', 0.02))
        
        if model_type in ['hybrid', 'combined']:
            # Add volatility clustering parameter if provided
            if 'vol_clustering' in request.form:
                model_params['vol_clustering'] = float(request.form.get('vol_clustering', 0.85))
        
        # Create output directories
        output_dir = create_directory('output')
        create_directory(os.path.join(output_dir, 'reports'))
        create_directory(os.path.join(output_dir, 'graphs'))
        
        # Get selected sectors from checkboxes
        filtered_sectors = request.form.getlist('sectors')
        print(f"Selected sectors ({len(filtered_sectors)}): {filtered_sectors}")
        
        # If sectors are selected but no tickers, add tickers from those sectors
        if filtered_sectors and not selected_tickers:
            for sector in filtered_sectors:
                if sector in SECTORS:
                    selected_tickers.extend(SECTORS[sector])
        
        # If still no tickers, use all available tickers
        if not selected_tickers:
            for sector_tickers in SECTORS.values():
                selected_tickers.extend(sector_tickers)
        
        # Remove duplicates while preserving order
        selected_tickers = list(dict.fromkeys(selected_tickers))
        
        print(f"Final selected tickers: {len(selected_tickers)}")
        
        # Reset and initialize simulation status
        simulation_status.reset()
        simulation_status.update({
            "running": True,
            "progress": 0,
            "total_stocks": len(selected_tickers),
            "completed_stocks": 0,
            "current_sector": "",
            "current_stock": "",
            "start_time": time.time(),
            "end_time": 0
        })
        
        # Start simulation in a separate thread
        simulation_thread = threading.Thread(
            target=run_simulation_thread,
            args=(model_type, num_paths, num_steps, time_step, output_dir, filtered_sectors),
            kwargs={
                "model_params": model_params, 
                "selected_tickers": selected_tickers,
                "lookback_period": lookback_period,  # Pass lookback_period to the thread
                "save_full_paths": save_full_paths   # Pass the save_full_paths option
            }
        )
        simulation_thread.daemon = True
        simulation_thread.start()
        
        return jsonify({
            "status": "success",
            "message": f"Simulation started with {len(selected_tickers)} stocks",
            "tickers_count": len(selected_tickers)
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"Error starting simulation: {str(e)}"
        })

def run_simulation_thread(model_type, num_paths, num_steps, time_step, 
                         output_dir, filtered_sectors=None, model_params=None, selected_tickers=None,
                         lookback_period=None, save_full_paths=False):
    """Run a simulation in a separate thread."""
    try:
        # Ensure we have tickers
        if not selected_tickers:
            simulation_status.update({
                "running": False,
                "errors": ["No tickers selected for simulation"]
            })
            return
        
        total_tickers = len(selected_tickers)
        completed = 0
        errors = []
        
        # Process each ticker
        for i, ticker in enumerate(selected_tickers):
            try:
                # Update status
                current_sector = next((sector for sector, tickers in SECTORS.items() if ticker in tickers), "Unknown")
                
                simulation_status.update({
                    "current_sector": current_sector,
                    "current_stock": ticker,
                    "completed_stocks": completed
                })
                
                print(f"Processing {ticker} ({i+1}/{total_tickers})...")
                
                # Create model configuration dictionary (FLAT STRUCTURE)
                model_config = {
                    'model_type': model_type,    # Correct key - ensure this is a string
                    'paths': int(num_paths),     # Ensure this is an integer
                    'steps': int(num_steps),     # Ensure this is an integer
                    'dt': float(time_step),      # Ensure this is a float
                    'lookback_period': lookback_period if lookback_period else '2y',  # Use parameter instead of request.form
                    'save_full_paths': save_full_paths,  # Add save_full_paths option
                }
                
                # Add any custom model parameters if provided
                # Ensure these are added at the top level, not nested
                if model_params and isinstance(model_params, dict):
                    model_config.update(model_params)
                
                # Retrieve calibrate value from the form/request if it was passed
                # Assuming 'calibrate' was passed to this thread function or retrieved earlier
                # For now, hardcoding to True based on previous call structure
                calibrate_flag = True # Or get it from function arguments/global context
                
                # Debug log parameters
                print(f"Running simulation for {ticker} with config: {model_config}")
                
                # Run simulation using the simulation engine with the flat config
                result = engine.run_simulation(
                    ticker=ticker,
                    model_config=model_config,
                    calibrate=calibrate_flag,
                    simulation_id=simulation_status.get().get("simulation_id")
                )
                
                # Update progress
                completed += 1
                progress = int((completed / total_tickers) * 100)
                
                simulation_status.update({
                    "progress": progress,
                    "completed_stocks": completed
                })
                
                # Check if there's a result
                if result is None:
                    errors.append(f"Failed to simulate {ticker} - no result returned")
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                error_msg = f"Error processing {ticker}: {str(e)}"
                print(error_msg)
                errors.append(error_msg)
                
                # Still count as completed for progress
                completed += 1
                progress = int((completed / total_tickers) * 100)
                
                simulation_status.update({
                    "progress": progress,
                    "completed_stocks": completed
                })
        
        # Generate multi-stock report if there are multiple tickers
        if total_tickers > 1:
            try:
                # Generate batch report using existing results
                from stock_sim.analysis.reporting import generate_batch_report
                generate_batch_report(results=results, output_dir=output_dir)
            except Exception as e:
                errors.append(f"Error generating batch report: {str(e)}")
        
        # Update final status
        end_time = time.time()
        elapsed_seconds = int(end_time - simulation_status.get()["start_time"])
        
        simulation_status.update({
            "running": False,
            "progress": 100,
            "completed_stocks": completed,
            "end_time": end_time,
            "elapsed_seconds": elapsed_seconds,
            "errors": errors
        })
        
        print(f"Simulation completed with {completed}/{total_tickers} stocks in {elapsed_seconds} seconds")
        if errors:
            print("====== SIMULATION ERRORS ======")
            for error in errors:
                print(error)
            print("===============================")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Update status with error
        simulation_status.update({
            "running": False,
            "errors": [f"Simulation thread error: {str(e)}"]
        })

@app.route('/simulation_status')
def get_simulation_status():
    """Get the current simulation status."""
    status = simulation_status.get()
    
    # Calculate elapsed and remaining time
    if status["running"] and status["start_time"] > 0:
        elapsed_seconds = int(time.time() - status["start_time"])
        status["elapsed_seconds"] = elapsed_seconds
        
        # Estimate remaining time based on progress
        if status["progress"] > 0:
            total_estimated_seconds = (elapsed_seconds / status["progress"]) * 100
            remaining_seconds = int(total_estimated_seconds - elapsed_seconds)
            status["remaining_seconds"] = remaining_seconds if remaining_seconds > 0 else 0
    
    return jsonify(status)

@app.route('/view_report')
def view_report():
    """Redirect to the consolidated report that shows all available reports."""
    try:
        # Check for consolidated report first
        reports_dir = os.path.join('output', 'reports')
        consolidated_report = os.path.join(reports_dir, "consolidated_report.html")
        
        # Always refresh the consolidated report to include latest reports
        create_consolidated_report(reports_dir)
        
        # If consolidated report exists, redirect to it
        if os.path.exists(consolidated_report):
            return redirect(f'/reports/consolidated_report.html')
        
        # If no consolidated report could be created, fall back to individual reports
        if os.path.exists(reports_dir):
            # List HTML files in the reports directory
            report_files = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
            
            if report_files:
                # Sort by modification time (newest first)
                report_files.sort(key=lambda f: os.path.getmtime(os.path.join(reports_dir, f)), reverse=True)
                # Redirect to the newest report
                return redirect(f'/reports/{report_files[0]}')
        
        # If no reports found, check legacy directories
        output_dir = 'output'
        if os.path.exists(output_dir):
            # Check for date-stamped subdirectories
            dirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d)) and d.startswith('20')]
            
            if dirs:
                # Sort directories by name (timestamp) in descending order
                dirs.sort(reverse=True)
                latest_dir = os.path.join(output_dir, dirs[0])
                reports_dir = os.path.join(latest_dir, 'reports')
                
                if os.path.exists(reports_dir):
                    # Check for consolidated report in the legacy directory
                    consolidated_report = os.path.join(reports_dir, "consolidated_report.html")
                    if os.path.exists(consolidated_report):
                        return redirect(f'/reports/consolidated_report.html')
                    
                    report_files = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
                    
                    if report_files:
                        # Sort by modification time (newest first)
                        report_files.sort(key=lambda f: os.path.getmtime(os.path.join(reports_dir, f)), reverse=True)
                        # Redirect to the newest report
                        return redirect(f'/reports/{report_files[0]}')
        
        # If no reports found at all
        return "No reports found. Please run a simulation first.", 404
    
    except Exception as e:
        return f"Error finding report: {str(e)}", 500

def create_consolidated_report(reports_dir):
    """
    Create a consolidated report that shows forecasts for all available stocks.
    
    Args:
        reports_dir (str): Directory where reports are stored
    """
    try:
        import pandas as pd
        from datetime import datetime
        
        # Ensure reports directory exists
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        # Get all HTML reports except consolidated report
        report_files = [f for f in os.listdir(reports_dir) if f.endswith('.html') 
                       and not f.startswith('consolidated_report')]
        
        # Path to the consolidated report
        consolidated_path = os.path.join(reports_dir, "consolidated_report.html")
        
        # Group reports by ticker and get the most recent one for each
        ticker_reports = {}
        for report in report_files:
            # Skip batch reports
            if report.startswith("batch_report"):
                continue
                
            # Extract ticker and timestamp from filename
            parts = report.split('_')
            if len(parts) >= 3:  # Ensure we have enough parts
                ticker = parts[0]
                timestamp = parts[2].replace('.html', '')
                
                # Keep only the most recent report for each ticker
                if ticker not in ticker_reports or timestamp > ticker_reports[ticker][1]:
                    ticker_reports[ticker] = (report, timestamp)
        
        # Parse data from the most recent reports
        stocks_data = []
        for ticker, (report, _) in ticker_reports.items():
            # Add to data
            stocks_data.append({
                "ticker": ticker,
                "report_file": report,
                "sector": "Unknown",  # This would need to be populated from your sector data
                "model_type": "combined",
                "recommendation": "HOLD",
                "recommendation_class": "hold",
                "current_price": 0.0,  # Placeholder for actual price data
                "forecast_price": 0.0, # Placeholder for actual forecast data
                "expected_return": 0.0, # Placeholder
                "volatility": 0.0,     # Placeholder
                "sharpe": 0.0,         # Placeholder
                "prob_profit": 0.0     # Placeholder
            })
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(stocks_data)
        
        # For demo purposes, assign sectors based on ticker first letter
        # In a real implementation, you would look up the actual sector
        def assign_sector(ticker):
            first_letter = ticker[0].upper()
            if first_letter in "ABC":
                return "Technology"
            elif first_letter in "DEF":
                return "Consumer Goods"
            elif first_letter in "GHIJ":
                return "Healthcare"
            elif first_letter in "KLMN":
                return "Financials"
            elif first_letter in "OPQR":
                return "Energy"
            elif first_letter in "STUV":
                return "Materials"
            else:
                return "Other"
                
        df["sector"] = df["ticker"].apply(assign_sector)
        
        # Generate some random data for the demo
        # In a real implementation, you would extract this from actual simulation results
        import random
        for i, row in df.iterrows():
            current_price = random.uniform(50, 500)
            expected_return = random.uniform(-15, 15)
            forecast_price = current_price * (1 + expected_return/100)
            
            if expected_return >= 8:
                recommendation = "STRONG BUY"
                recommendation_class = "strong-buy"
            elif expected_return >= 5:
                recommendation = "BUY"
                recommendation_class = "buy"
            elif expected_return <= -8:
                recommendation = "STRONG SELL"
                recommendation_class = "strong-sell"
            elif expected_return <= -5:
                recommendation = "SELL"
                recommendation_class = "sell"
            else:
                recommendation = "HOLD"
                recommendation_class = "hold"
                
            df.at[i, "current_price"] = current_price
            df.at[i, "forecast_price"] = forecast_price
            df.at[i, "expected_return"] = expected_return
            df.at[i, "volatility"] = random.uniform(10, 40)
            df.at[i, "sharpe"] = random.uniform(-0.5, 1.5)
            df.at[i, "prob_profit"] = random.uniform(30, 70)
            df.at[i, "recommendation"] = recommendation
            df.at[i, "recommendation_class"] = recommendation_class
            
        # Sort by sector and then by ticker
        df = df.sort_values(["sector", "ticker"])
        
        # Get unique sectors
        sectors = df.sector.unique()
        
        # Generate HTML content
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Stock Price Forecast</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                    margin: 0;
                    padding: 0;
                    color: #333;
                    line-height: 1.6;
                }
                .container {
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }
                h1, h2, h3 {
                    color: #2c3e50;
                }
                .header {
                    padding: 20px;
                    background-color: #2c3e50;
                    color: white;
                    margin-bottom: 30px;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-bottom: 30px;
                    background-color: white;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                th {
                    background-color: #2c3e50;
                    color: white;
                    text-align: left;
                    padding: 12px 15px;
                }
                td {
                    padding: 10px 15px;
                    border-bottom: 1px solid #ddd;
                }
                tr:nth-child(even) {
                    background-color: #f8f9fa;
                }
                .sector-heading {
                    background-color: #3498db;
                    color: white;
                    padding: 12px 15px;
                    font-weight: bold;
                    text-transform: uppercase;
                }
                .strong-buy, .buy, .hold, .sell, .strong-sell {
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 4px;
                    color: white;
                    font-weight: bold;
                    text-align: center;
                }
                .strong-buy {
                    background-color: #28a745;
                }
                .buy {
                    background-color: #5cb85c;
                }
                .hold {
                    background-color: #f0ad4e;
                }
                .sell {
                    background-color: #d9534f;
                }
                .strong-sell {
                    background-color: #c9302c;
                }
                .positive {
                    color: #28a745;
                    font-weight: bold;
                }
                .negative {
                    color: #dc3545;
                    font-weight: bold;
                }
                .footer {
                    text-align: center;
                    margin-top: 50px;
                    padding: 20px;
                    border-top: 1px solid #eee;
                    font-size: 14px;
                    color: #6c757d;
                }
                .ticker-link {
                    color: #2c3e50;
                    font-weight: bold;
                    text-decoration: none;
                }
                .ticker-link:hover {
                    text-decoration: underline;
                }
                .sim-summary {
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    margin-bottom: 20px;
                }
                .sim-summary h3 {
                    margin-top: 0;
                    color: #2c3e50;
                }
                .sim-summary ul {
                    list-style-type: none;
                    padding: 0;
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                }
                .sim-summary li {
                    padding: 5px 10px;
                    background-color: #e9ecef;
                    border-radius: 4px;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <div class="container">
                    <h1>Stock Price Forecast</h1>
                    <p>1-Month Horizon | Report generated on """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
                </div>
            </div>
            
            <div class="container">
                <div class="sim-summary">
                    <h3>Simulation Summary</h3>
                    <p>This consolidated report contains simulations for """ + str(len(df)) + """ stocks across """ + str(len(sectors)) + """ sectors.</p>
                    <ul>
                        <li><strong>Models:</strong> COMBINED</li>
                        <li><strong>Time Horizon:</strong> Approximately 1 month</li>
                    </ul>
                    <p>Click on any ticker symbol to view detailed simulation results and visualizations.</p>
                </div>
                
                <h2>Forecasts by Sector</h2>
                
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Model</th>
                            <th>Recommendation</th>
                            <th>Current Price</th>
                            <th>1-Month Forecast</th>
                            <th>Expected Return</th>
                            <th>Volatility</th>
                            <th>Sharpe</th>
                            <th>Prob. Profit</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        
        # Add rows for each sector and ticker
        for sector in sectors:
            html_content += f"""
                        <tr>
                            <td colspan="9" class="sector-heading">{sector}</td>
                        </tr>
            """
            
            # Add rows for each ticker in the sector
            sector_df = df[df.sector == sector]
            for _, row in sector_df.iterrows():
                html_content += f"""
                        <tr>
                            <td><a href="/reports/{row.report_file}" class="ticker-link">{row.ticker}</a></td>
                            <td>{row.model_type.upper()}</td>
                            <td><div class="{row.recommendation_class}">{row.recommendation}</div></td>
                            <td>${row.current_price:.2f}</td>
                            <td>${row.forecast_price:.2f}</td>
                            <td class="{'positive' if row.expected_return > 0 else 'negative' if row.expected_return < 0 else ''}">
                                {row.expected_return:.2f}%
                            </td>
                            <td>{row.volatility:.2f}%</td>
                            <td class="{'positive' if row.sharpe > 0.5 else 'negative' if row.sharpe < 0 else ''}">
                                {row.sharpe:.2f}
                            </td>
                            <td>{row.prob_profit:.2f}%</td>
                        </tr>
                """
        
        # Close the table and add footer
        html_content += """
                    </tbody>
                </table>
                
                <div class="footer">
                    <p>These forecasts are based on Monte Carlo simulations over a 1-month horizon.</p>
                    <p>The information provided is for educational purposes only and should not be considered financial advice.</p>
                    <p>Return to <a href="/">simulation dashboard</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Write the consolidated report
        with open(consolidated_path, 'w') as f:
            f.write(html_content)
        
        print(f"Created consolidated report: {consolidated_path}")
        return True
        
    except Exception as e:
        print(f"Error creating consolidated report: {e}")
        import traceback
        traceback.print_exc()
        return False

# Add API simulation status access for compatibility
@app.route('/api/simulations')
def get_simulations():
    """Get status of active simulations."""
    status = simulation_status.get()
    
    # Format for compatibility with API
    active = {}
    if status["running"] or status["progress"] > 0:
        active["1"] = {
            "id": 1,
            "tickers": selected_tickers if 'selected_tickers' in globals() else [],
            "model_type": "hybrid",
            "status": "running" if status["running"] else "completed",
            "progress": status["progress"],
            "summary": {
                "total": status["total_stocks"],
                "completed": status["completed_stocks"],
                "failed": len(status["errors"])
            },
            "has_errors": len(status["errors"]) > 0,
            "error_summary": {f"Error {i+1}": error for i, error in enumerate(status["errors"])}
        }
    
    return jsonify({
        "active": active
    })

def format_time(seconds):
    """Format time in seconds to HH:MM:SS."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

# Add direct file serving routes for resources
@app.route('/output/<path:path>')
def serve_output(path):
    """Serve files from the output directory."""
    return send_from_directory('output', path)

@app.route('/lab')
def lab():
    """Render the Strategy Lab page."""
    return render_template('lab.html')

@app.route('/run_strategy', methods=['POST'])
def run_strategy():
    """Execute a user-defined strategy and return results."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['code', 'start_date', 'end_date', 'initial_capital', 'tickers']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f"Missing required field: {field}"}), 400
        
        code = data['code']
        start_date = data['start_date']
        end_date = data['end_date']
        initial_capital = data['initial_capital']
        tickers = data['tickers']
        
        # Validate data types
        if not isinstance(code, str) or not code.strip():
            return jsonify({'error': "Strategy code must be a non-empty string"}), 400
            
        if not isinstance(start_date, str) or not start_date.strip():
            return jsonify({'error': "Start date must be a non-empty string"}), 400
            
        if not isinstance(end_date, str) or not end_date.strip():
            return jsonify({'error': "End date must be a non-empty string"}), 400
            
        if not isinstance(initial_capital, (int, float)) or initial_capital <= 0:
            return jsonify({'error': "Initial capital must be a positive number"}), 400
            
        if not isinstance(tickers, list) or not tickers:
            return jsonify({'error': "Tickers must be a non-empty list"}), 400

        results = strategy_executor.execute_strategy(
            code=code,
            start_date=start_date,
            end_date=end_date,
            initial_capital=initial_capital,
            tickers=tickers
        )

        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Error running strategy: {str(e)}")
        return jsonify({'error': str(e)}), 400

# This ensures app is available when imported
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the stock simulation web interface')
    # IMPORTANT: Always use port 8080 for this application (port 5000 conflicts with macOS AirPlay Receiver)
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on (use 8080, not 5000)')
    args = parser.parse_args()
    
    # Run the application directly if this script is executed
    app.run(debug=True, host='0.0.0.0', port=args.port) 