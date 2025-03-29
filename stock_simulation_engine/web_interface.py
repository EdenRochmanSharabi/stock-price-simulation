#!/usr/bin/env python3

"""
Stock Simulation Web Interface
-----------------------------
A web interface for running stock price simulations and viewing results.
"""

import os
import json
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from modules.engine import run_simulation, create_directory
from run_sector_analysis import run_all_simulations, SECTORS
import threading
import time
import multiprocessing
import atexit
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

app = Flask(__name__, static_folder='templates/static')

# Track simulation status
simulation_status = {
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

# Register cleanup function
def cleanup_multiprocessing():
    """Clean up any remaining multiprocessing resources."""
    for process in multiprocessing.active_children():
        process.terminate()
        process.join()
    multiprocessing.set_start_method('spawn', force=True)

atexit.register(cleanup_multiprocessing)

@app.route('/')
def index():
    """Render the main simulation control page."""
    # Get sectors and count total stocks
    total_stocks = sum(len(tickers) for tickers in SECTORS.values())
    
    return render_template('index.html', 
                          sectors=SECTORS, 
                          total_stocks=total_stocks,
                          simulation_status=simulation_status)

@app.route('/static/<path:path>')
def send_static(path):
    """Serve static files."""
    return send_from_directory('templates/static', path)

@app.route('/reports/<path:path>')
def serve_report(path):
    """Serve report files from the output directory."""
    return send_from_directory('output/reports', path)

@app.route('/graphs/<path:path>')
def serve_graph(path):
    """Serve graph files from the output directory."""
    return send_from_directory('output/graphs', path)

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    """Start a simulation with the given parameters."""
    global simulation_status
    
    # Don't start if already running
    if simulation_status["running"]:
        return jsonify({"status": "error", "message": "Simulation already running"})
    
    # Get parameters from form
    model_type = request.form.get('model_type', 'combined')
    num_paths = int(request.form.get('num_paths', 1000))
    num_steps = int(request.form.get('num_steps', 21))
    time_step = float(request.form.get('time_step', 1/252))
    companies_per_sector = int(request.form.get('companies_per_sector', 3))
    output_dir = request.form.get('output_dir', 'output')  # Always use the clean output structure
    selected_sectors = request.form.getlist('sectors')
    
    # Model calibration parameters
    calibrate = request.form.get('calibrate', 'true') == 'true'
    lookback_period = request.form.get('lookback_period', '2y')
    
    # Manual model parameters (used if calibrate is False)
    mu = float(request.form.get('mu', 0.08))
    sigma = float(request.form.get('sigma', 0.2))
    jump_intensity = float(request.form.get('jump_intensity', 10))
    jump_mean = float(request.form.get('jump_mean', -0.01))
    jump_sigma = float(request.form.get('jump_sigma', 0.02))
    vol_clustering = float(request.form.get('vol_clustering', 0.85))
    
    # Gather the parameters in a dictionary
    model_params = {
        'calibrate': calibrate,
        'lookback_period': lookback_period,
        'mu': mu,
        'sigma': sigma,
        'jump_intensity': jump_intensity,
        'jump_mean': jump_mean,
        'jump_sigma': jump_sigma,
        'vol_clustering': vol_clustering
    }
    
    # Calculate total stocks
    total_stocks = 0
    filtered_sectors = {}
    
    # If sectors were selected, filter the SECTORS dictionary
    if selected_sectors:
        for sector_name in selected_sectors:
            if sector_name in SECTORS:
                filtered_sectors[sector_name] = SECTORS[sector_name][:companies_per_sector]
                total_stocks += len(filtered_sectors[sector_name])
    else:
        # If no sectors were explicitly selected, use all sectors
        for sector_name, tickers in SECTORS.items():
            filtered_sectors[sector_name] = tickers[:companies_per_sector]
            total_stocks += len(filtered_sectors[sector_name])
    
    # Reset simulation status
    simulation_status = {
        "running": True,
        "progress": 0,
        "total_stocks": total_stocks,
        "completed_stocks": 0,
        "current_sector": "",
        "current_stock": "",
        "start_time": time.time(),
        "end_time": 0,
        "errors": []
    }
    
    # Start simulation in a separate thread
    thread = threading.Thread(target=run_simulation_thread, 
                            args=(model_type, num_paths, num_steps, time_step,
                                  companies_per_sector, output_dir, filtered_sectors, model_params))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "success", "message": "Simulation started"})

def run_simulation_thread(model_type, num_paths, num_steps, time_step, companies_per_sector, 
                          output_dir, filtered_sectors=None, model_params=None):
    """Run the simulation in a separate thread and update the status."""
    global simulation_status
    
    try:
        # Create output directories - simplified to just 3 folders
        for subdir in ["data", "reports", "graphs"]:
            create_directory(os.path.join(output_dir, subdir))
        
        # If filtered_sectors is provided, use it instead of all SECTORS
        sectors_to_use = filtered_sectors if filtered_sectors else SECTORS
        
        # Process each sector
        all_results = {}
        completed_stocks = 0
        
        for sector, tickers in sectors_to_use.items():
            # Update current sector in status
            simulation_status["current_sector"] = sector
            
            # Use only the specified number of companies per sector
            sector_tickers = tickers[:companies_per_sector]
            
            # Run simulations for each ticker in this sector
            for ticker in sector_tickers:
                # Update current stock in status
                simulation_status["current_stock"] = ticker
                
                try:
                    # Run the simulation with all parameters
                    result = run_simulation(
                        ticker, 
                        model_type=model_type, 
                        paths=num_paths, 
                        steps=num_steps,
                        dt=time_step,
                        output_dir=output_dir,
                        reports_dir=os.path.join(output_dir, "reports"),
                        graphs_dir=os.path.join(output_dir, "graphs"),
                        **model_params
                    )
                    
                    # Store results
                    if result:
                        result['sector'] = sector
                        all_results[ticker] = result
                    else:
                        simulation_status["errors"].append(f"Simulation for {ticker} returned None")
                
                except Exception as e:
                    simulation_status["errors"].append(f"Error processing {ticker}: {str(e)}")
                
                # Update progress
                completed_stocks += 1
                simulation_status["completed_stocks"] = completed_stocks
                simulation_status["progress"] = int((completed_stocks / simulation_status["total_stocks"]) * 100)
        
        # Generate reports
        from reporting import generate_report
        if all_results:
            generate_report(all_results, output_dir)
        
        # Update status to complete
        simulation_status["running"] = False
        simulation_status["progress"] = 100
        simulation_status["end_time"] = time.time()
        
    except Exception as e:
        simulation_status["errors"].append(f"Error in simulation thread: {str(e)}")
        simulation_status["running"] = False
        simulation_status["end_time"] = time.time()
    finally:
        # Clean up multiprocessing resources
        cleanup_multiprocessing()

@app.route('/simulation_status')
def get_simulation_status():
    """Return the current simulation status as JSON."""
    global simulation_status
    
    # Calculate elapsed time if simulation is running
    if simulation_status["running"] and simulation_status["start_time"] > 0:
        elapsed = time.time() - simulation_status["start_time"]
        
        # Estimate remaining time based on progress
        if simulation_status["progress"] > 0:
            estimated_total = elapsed / (simulation_status["progress"] / 100)
            remaining = estimated_total - elapsed
        else:
            remaining = 0
        
        # Add these to the status
        status_with_times = simulation_status.copy()
        status_with_times["elapsed_seconds"] = int(elapsed)
        status_with_times["remaining_seconds"] = int(remaining)
        
        return jsonify(status_with_times)
    
    # If simulation is complete, calculate total run time
    if not simulation_status["running"] and simulation_status["end_time"] > 0:
        total_time = simulation_status["end_time"] - simulation_status["start_time"]
        
        status_with_times = simulation_status.copy()
        status_with_times["elapsed_seconds"] = int(total_time)
        status_with_times["remaining_seconds"] = 0
        
        return jsonify(status_with_times)
    
    # Otherwise just return the status as is
    return jsonify(simulation_status)

@app.route('/view_report')
def view_report():
    """Redirect to the consolidated report."""
    return redirect('/reports/consolidated_report.html')

if __name__ == '__main__':
    # Make sure template directories exist
    os.makedirs('templates/static', exist_ok=True)
    
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=9999) 