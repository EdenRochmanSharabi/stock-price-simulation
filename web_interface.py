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
from stock_simulation_engine.modules.engine import run_simulation, create_directory
from stock_simulation_engine.sp500_tickers import (
    get_sector_mapping, 
    save_sector_mapping_to_csv, 
    load_sector_mapping_from_csv
)
from stock_simulation_engine.reporting import generate_report

# Create Flask app with appropriate static folder
app = Flask(__name__, static_folder='templates/static')

# Initialize sectors
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
    
    return render_template('index.html', 
                          sectors=SECTORS, 
                          total_stocks=total_stocks,
                          simulation_status=simulation_status.get())

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
        # Get fresh sector mapping
        sector_mapping = get_sector_mapping()
        if sector_mapping:
            # Save to CSV
            save_sector_mapping_to_csv(sector_mapping)
            # Update global SECTORS
            global SECTORS
            SECTORS = sector_mapping
            return jsonify({
                "status": "success",
                "message": f"Successfully refreshed {len(sector_mapping)} sectors",
                "sectors": sector_mapping
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Failed to retrieve sector mapping"
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
        model_type = request.form.get('model_type', 'combined')
        num_paths = int(request.form.get('num_paths', 1000))
        num_steps = int(request.form.get('num_steps', 21))
        time_step = float(request.form.get('time_step', 1/252))
        calibrate = request.form.get('calibrate', 'true') == 'true'
        
        # Get selected tickers from JSON string or list
        selected_tickers = []
        if 'tickers' in request.form:
            try:
                # Try to parse JSON string format
                tickers_data = request.form.get('tickers')
                print(f"Raw tickers data: {tickers_data}")
                
                # Handle square brackets in string format (common issue)
                if tickers_data.startswith('[') and tickers_data.endswith(']'):
                    # Remove outer brackets and split by comma
                    tickers_data = tickers_data.strip('[]')
                    if tickers_data:  # Only process if not empty
                        # Handle quoted strings in the list
                        if '"' in tickers_data or "'" in tickers_data:
                            # Try JSON parsing again
                            try:
                                selected_tickers = json.loads(f"[{tickers_data}]")
                            except json.JSONDecodeError:
                                # Fall back to simple parsing
                                selected_tickers = [t.strip().strip('"\'') for t in tickers_data.split(',')]
                        else:
                            selected_tickers = [t.strip() for t in tickers_data.split(',')]
                else:
                    # Standard JSON parsing
                    selected_tickers = json.loads(tickers_data)
                
                print(f"Processed tickers: {selected_tickers}")
            except Exception as e:
                # If parsing fails, treat as single ticker or fallback
                print(f"Error parsing tickers: {str(e)}")
                ticker_value = request.form.get('tickers')
                if ticker_value and ticker_value != '[]':
                    selected_tickers = [ticker_value]
        else:
            # Legacy format
            selected_tickers = request.form.getlist('tickers[]')
            print(f"Retrieved tickers from list format: {selected_tickers}")
        
        # If no tickers selected directly, check if sectors were selected
        if not selected_tickers:
            selected_sectors = request.form.getlist('sectors')
            if selected_sectors:
                # Get tickers from selected sectors - DO NOT LIMIT to 3 tickers
                selected_tickers = []
                for sector in selected_sectors:
                    if sector in SECTORS:
                        # Include ALL tickers in the sector
                        selected_tickers.extend(SECTORS[sector])
            else:
                # If still no tickers, use EXPE as default
                selected_tickers = ['EXPE']
                print("No tickers selected, using default ticker: EXPE")
        
        print(f"Selected tickers: {selected_tickers}")
        
        # Get manual parameters if calibration is disabled
        model_params = {}
        if not calibrate:
            model_params = {
                'mu': float(request.form.get('mu', 0.1)),
                'sigma': float(request.form.get('sigma', 0.2)),
                'lambda': float(request.form.get('lambda', 0.1)),
                'mu_j': float(request.form.get('mu_j', 0.0)),
                'sigma_j': float(request.form.get('sigma_j', 0.1))
            }
        
        # Use the simple directory structure
        base_output_dir = 'output'
        
        # Create organized subdirectories
        data_dir = os.path.join(base_output_dir, 'data')
        reports_dir = os.path.join(base_output_dir, 'reports')
        graphs_dir = os.path.join(base_output_dir, 'graphs')
        
        os.makedirs(data_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)
        os.makedirs(graphs_dir, exist_ok=True)
        
        # Update simulation status
        simulation_status.update({
            "running": True,
            "progress": 0,
            "current_stock": "",
            "completed_stocks": 0,
            "total_stocks": len(selected_tickers),
            "start_time": time.time(),
            "errors": []
        })
        
        # Start simulation in a separate thread
        thread = threading.Thread(
            target=run_simulation_thread,
            args=(model_type, num_paths, num_steps, time_step, base_output_dir, None, model_params, selected_tickers)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "success",
            "message": "Simulation started successfully"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

def run_simulation_thread(model_type, num_paths, num_steps, time_step, 
                         output_dir, filtered_sectors=None, model_params=None, selected_tickers=None):
    """
    Run simulation in a separate thread and update status.
    
    Args:
        model_type: Type of simulation model
        num_paths: Number of simulation paths
        num_steps: Number of time steps
        time_step: Size of time step in years
        output_dir: Directory to save results
        filtered_sectors: List of sectors to analyze (or None for all)
        model_params: Manual parameters for simulation (or None for calibration)
        selected_tickers: List of specific tickers to simulate
    """
    try:
        # Process with specific tickers if provided
        if selected_tickers:
            total_stocks = len(selected_tickers)
            simulation_status.update({
                "total_stocks": total_stocks
            })
            
            # Create a dictionary to store simulation results
            simulation_results = {}
            
            # Run simulations for each selected ticker
            for i, ticker in enumerate(selected_tickers):
                try:
                    # Update status
                    simulation_status.update({
                        "current_stock": ticker,
                        "current_sector": "",
                        "completed_stocks": i,
                        "progress": (i / total_stocks) * 100 if total_stocks > 0 else 0
                    })
                    
                    # Run simulation for this ticker
                    result = run_simulation(
                        ticker=ticker,
                        model_type=model_type,
                        paths=num_paths,
                        steps=num_steps,
                        dt=time_step,
                        output_dir=output_dir,
                        calibrate=True if not model_params else False,
                        mu=model_params.get('mu') if model_params else None,
                        sigma=model_params.get('sigma') if model_params else None,
                        jump_intensity=model_params.get('lambda', 10) if model_params else 10,
                        jump_mean=model_params.get('mu_j', -0.01) if model_params else -0.01,
                        jump_sigma=model_params.get('sigma_j', 0.02) if model_params else 0.02
                    )
                    
                    # Store the result
                    if result:
                        simulation_results[ticker] = result
                    
                except Exception as e:
                    # Log the error
                    with open('app.log', 'a') as f:
                        f.write(f"Error processing {ticker}: {str(e)}\n")
                    
                    # Update status with error
                    simulation_status.update({
                        "errors": simulation_status.get()["errors"] + [f"Error processing {ticker}: {str(e)}"]
                    })
            
            # Generate report
            generate_report(
                results=simulation_results,
                output_dir=output_dir
            )
        
        # Mark as complete
        simulation_status.update({
            "running": False,
            "completed_stocks": total_stocks if selected_tickers else 0,
            "progress": 100,
            "end_time": time.time()
        })
        
    except Exception as e:
        # Log the error
        with open('app.log', 'a') as f:
            f.write(f"Error in simulation thread: {str(e)}\n")
        
        # Update status with error
        simulation_status.update({
            "running": False,
            "errors": simulation_status.get()["errors"] + [f"Error in simulation: {str(e)}"],
            "end_time": time.time()
        })

@app.route('/simulation_status')
def get_simulation_status():
    """Get the current simulation status."""
    status = simulation_status.get()
    
    # Calculate elapsed time and estimated time remaining
    if status["running"] and status["start_time"] > 0:
        elapsed = time.time() - status["start_time"]
        progress = status["progress"]
        
        # Calculate time remaining if progress is non-zero
        if progress > 0:
            total_estimated = elapsed * 100 / progress
            remaining = total_estimated - elapsed
        else:
            remaining = 0
            
        # Format times
        status["elapsed_time"] = format_time(elapsed)
        status["remaining_time"] = format_time(remaining)
    
    return jsonify(status)

@app.route('/api/simulations')
def get_simulations():
    """Get active simulations status (API compatibility endpoint)."""
    # Return empty response for API compatibility
    return jsonify({
        "active": {},
        "completed": []
    })

def format_time(seconds):
    """Format time in seconds to HH:MM:SS"""
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

@app.route('/view_report')
def view_report():
    """View the simulation report."""
    ticker = request.args.get('ticker', '')
    
    # Find the main consolidated report first if no ticker specified
    if not ticker:
        # Look for main simulation report in standard location
        main_report_names = ["consolidated_report.html", "simulation_report.html", "report.html", "index.html"]
        
        # Check in standard reports directory
        reports_dir = os.path.join('output', 'reports')
        if os.path.exists(reports_dir):
            for report_name in main_report_names:
                if os.path.exists(os.path.join(reports_dir, report_name)):
                    return redirect(url_for('serve_report', path=report_name))
        
        # Check in timestamped directories
        output_dir = 'output'
        if os.path.exists(output_dir):
            dirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d)) and d.startswith('20')]
            if dirs:
                dirs.sort(reverse=True)
                latest_dir = os.path.join(output_dir, dirs[0])
                reports_dir = os.path.join(latest_dir, 'reports')
                if os.path.exists(reports_dir):
                    for report_name in main_report_names:
                        if os.path.exists(os.path.join(reports_dir, report_name)):
                            return redirect(url_for('serve_report', path=report_name))
                            
        # If we can't find a main report, try to find any HTML file in reports directory
        if os.path.exists(reports_dir):
            html_files = [f for f in os.listdir(reports_dir) if f.endswith('.html')]
            if html_files:
                return redirect(url_for('serve_report', path=html_files[0]))
                
        # Return a helpful message if no reports found
        return "No simulation reports found. Please run a simulation first.", 404
    
    # Handle ticker-specific report
    if ticker:
        # Look for stock-specific report
        report_filename = f"{ticker}_report.html"
        
        # Check in standard reports directory
        reports_dir = os.path.join('output', 'reports')
        if os.path.exists(os.path.join(reports_dir, report_filename)):
            return redirect(url_for('serve_report', path=report_filename))
        
        # Check in timestamped directories
        output_dir = 'output'
        if os.path.exists(output_dir):
            dirs = [d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d)) and d.startswith('20')]
            if dirs:
                dirs.sort(reverse=True)
                latest_dir = os.path.join(output_dir, dirs[0])
                reports_dir = os.path.join(latest_dir, 'reports')
                report_path = os.path.join(reports_dir, report_filename)
                if os.path.exists(report_path):
                    return redirect(url_for('serve_report', path=report_filename))
        
        return f"Stock report not found for {ticker}", 404

# This ensures app is available when imported
if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run the stock simulation web interface')
    # IMPORTANT: Always use port 8080 for this application (port 5000 conflicts with macOS AirPlay Receiver)
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on (use 8080, not 5000)')
    args = parser.parse_args()
    
    # Run the application directly if this script is executed
    app.run(debug=True, host='0.0.0.0', port=args.port) 