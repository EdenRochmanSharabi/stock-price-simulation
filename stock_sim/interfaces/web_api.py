#!/usr/bin/env python3

"""
Web API Interface
---------------
A RESTful API for running stock price simulations.
"""

import os
import json
import threading
import time
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from ..simulation_engine import SimulationEngine
from ..utils import SP500TickerManager
from ..models import ModelFactory

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable Cross-Origin Resource Sharing

# Create simulation engine
engine = SimulationEngine(output_base_dir="output")

# Create ticker manager
ticker_manager = SP500TickerManager()

# Global state for tracking running simulations
simulations = {
    'active': {},  # Will store simulation_id -> thread info
    'next_id': 1,  # Counter for creating unique simulation IDs
    'lock': threading.Lock()  # Ensure thread-safe updates to the simulations dict
}


@app.route('/')
def index():
    """Render the main page."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Stock Price Simulation API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
            h1, h2, h3 { color: #2c3e50; }
            pre { background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; }
            .endpoint { margin-bottom: 20px; border-left: 4px solid #3498db; padding-left: 15px; }
            code { background-color: #f8f8f8; padding: 2px 4px; border-radius: 3px; }
            .button { 
                display: inline-block; 
                background-color: #3498db; 
                color: white; 
                padding: 10px 15px; 
                border-radius: 5px; 
                text-decoration: none; 
                margin-top: 10px;
                cursor: pointer;
            }
            .button.stop { background-color: #e74c3c; }
            .status { margin-top: 20px; padding: 10px; border-radius: 5px; }
            .status.running { background-color: #f1c40f; color: #000; }
            .status.stopped { background-color: #e74c3c; color: #fff; }
            .status.success { background-color: #2ecc71; color: #fff; }
            .error-section { 
                background-color: #ffdddd; 
                color: #900; 
                padding: 10px; 
                border-radius: 5px; 
                margin-top: 10px;
                border-left: 5px solid #e74c3c;
            }
            .error-list {
                margin-top: 10px;
                max-height: 200px;
                overflow-y: auto;
                font-family: monospace;
            }
            .error-ticker {
                font-weight: bold;
                margin-right: 10px;
            }
            .summary-section {
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                margin-top: 10px;
            }
            .summary-value {
                font-weight: bold;
                color: #2c3e50;
            }
            .tabs {
                display: flex;
                margin-bottom: 10px;
            }
            .tab {
                padding: 10px 15px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                cursor: pointer;
                margin-right: 5px;
            }
            .tab.active {
                background-color: #3498db;
                color: white;
                border-color: #3498db;
            }
            .tab-content {
                display: none;
            }
            .tab-content.active {
                display: block;
            }
        </style>
        <script>
            // Simple JavaScript for interactive features
            document.addEventListener('DOMContentLoaded', function() {
                console.log('DOM fully loaded - initializing UI');
                
                // Initialize tabs
                const tabs = document.querySelectorAll('.tab');
                if (tabs.length === 0) {
                    console.error('No tab elements found');
                }
                
                // Set default active tab if none is set
                const activeTab = document.querySelector('.tab.active');
                if (!activeTab && tabs.length > 0) {
                    tabs[0].classList.add('active');
                    const tabId = tabs[0].getAttribute('data-tab');
                    if (tabId) {
                        const tabContent = document.getElementById(tabId);
                        if (tabContent) {
                            tabContent.classList.add('active');
                        }
                    }
                }
                
                // Check active simulations on page load
                fetchActiveSimulations();
                
                // Set up periodic refresh of active simulations
                setInterval(fetchActiveSimulations, 5000);
                
                // Set up tab navigation
                tabs.forEach(tab => {
                    tab.addEventListener('click', function() {
                        const tabId = this.getAttribute('data-tab');
                        if (tabId) {
                            showTab(tabId);
                        }
                    });
                });
            });
            
            function showTab(tabId) {
                console.log('Showing tab:', tabId);
                // Hide all tabs and remove active class
                document.querySelectorAll('.tab-content').forEach(content => {
                    content.classList.remove('active');
                });
                document.querySelectorAll('.tab').forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Show selected tab and add active class
                const tabContent = document.getElementById(tabId);
                const tabButton = document.querySelector(`.tab[data-tab="${tabId}"]`);
                
                if (!tabContent) {
                    console.error(`Tab content with id ${tabId} not found`);
                    return;
                }
                
                if (!tabButton) {
                    console.error(`Tab button for ${tabId} not found`);
                    return;
                }
                
                tabContent.classList.add('active');
                tabButton.classList.add('active');
            }
            
            function fetchActiveSimulations() {
                console.log('Fetching active simulations...');
                
                fetch('/api/simulations')
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        const activeSimsDiv = document.getElementById('active-simulations');
                        if (!activeSimsDiv) {
                            console.error('Could not find active-simulations element');
                            return;
                        }
                        
                        activeSimsDiv.innerHTML = '';
                        
                        if (!data.active || Object.keys(data.active).length === 0) {
                            activeSimsDiv.innerHTML = '<p>No active simulations</p>';
                            return;
                        }
                        
                        // Create elements for each active simulation
                        for (const [id, sim] of Object.entries(data.active)) {
                            const simDiv = document.createElement('div');
                            simDiv.className = 'status running';
                            
                            let summaryHtml = '';
                            if (sim.summary) {
                                summaryHtml = `
                                    <div class="summary-section">
                                        <h4>Summary</h4>
                                        <p>Total tickers: <span class="summary-value">${sim.summary.total || '?'}</span></p>
                                        <p>Completed: <span class="summary-value">${sim.summary.completed || 0}</span></p>
                                        <p>Failed: <span class="summary-value">${sim.summary.failed || 0}</span></p>
                                    </div>
                                `;
                            }
                            
                            let errorHtml = '';
                            if (sim.has_errors) {
                                errorHtml = `
                                    <div class="error-section">
                                        <h4>Errors</h4>
                                        <div class="error-list">
                                `;
                                
                                if (sim.error_summary) {
                                    for (const [ticker, error] of Object.entries(sim.error_summary)) {
                                        errorHtml += `<p><span class="error-ticker">${ticker}:</span> ${error}</p>`;
                                    }
                                }
                                
                                errorHtml += `
                                        </div>
                                        <button class="button" onclick="viewSimulationDetails(${id})">View All Errors</button>
                                    </div>
                                `;
                            }
                            
                            simDiv.innerHTML = `
                                <h3>Simulation #${id}</h3>
                                <p>Ticker(s): ${sim.tickers ? sim.tickers.join(', ') : 'Unknown'}</p>
                                <p>Model: ${sim.model_type || 'Unknown'}</p>
                                <p>Status: ${sim.status || 'Unknown'}</p>
                                <button class="button stop" onclick="stopSimulation(${id})">Stop Simulation</button>
                                ${summaryHtml}
                                ${errorHtml}
                            `;
                            activeSimsDiv.appendChild(simDiv);
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching simulations:', error);
                        const activeSimsDiv = document.getElementById('active-simulations');
                        if (activeSimsDiv) {
                            activeSimsDiv.innerHTML = '<p>Error loading simulations. Please refresh the page.</p>';
                        }
                    });
            }
            
            function stopSimulation(id) {
                console.log(`Attempting to stop simulation ${id}...`);
                const button = event.target;
                button.disabled = true;
                button.textContent = 'Stopping...';
                
                fetch(`/api/simulations/${id}/stop`, { method: 'POST' })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        console.log(`Successfully stopped simulation ${id}`);
                        alert(data.message || 'Simulation stopped');
                        fetchActiveSimulations();
                    })
                    .catch(error => {
                        console.error('Error stopping simulation:', error);
                        alert(`Error stopping simulation: ${error.message}`);
                        button.disabled = false;
                        button.textContent = 'Stop Simulation';
                    });
            }
            
            function viewSimulationDetails(id) {
                fetch(`/api/simulations/${id}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP error ${response.status}`);
                        }
                        return response.json();
                    })
                    .then(data => {
                        // Create a modal even if there are no errors, to show simulation details
                        const errorModal = document.createElement('div');
                        errorModal.style.position = 'fixed';
                        errorModal.style.top = '50px';
                        errorModal.style.left = '50%';
                        errorModal.style.transform = 'translateX(-50%)';
                        errorModal.style.width = '80%';
                        errorModal.style.maxHeight = '80vh';
                        errorModal.style.overflow = 'auto';
                        errorModal.style.backgroundColor = 'white';
                        errorModal.style.padding = '20px';
                        errorModal.style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';
                        errorModal.style.zIndex = '1000';
                        errorModal.style.borderRadius = '5px';
                        
                        let modalHtml = `
                            <h3>Details for Simulation #${id}</h3>
                            <p>Status: ${data.status || 'Unknown'}</p>
                        `;
                        
                        if (data.errors && Object.keys(data.errors).length > 0) {
                            modalHtml += `
                                <p>Total errors: ${data.error_count || Object.keys(data.errors).length}</p>
                                <div class="error-list" style="max-height: 60vh;">
                            `;
                            
                            for (const [ticker, error] of Object.entries(data.errors)) {
                                modalHtml += `<p><span class="error-ticker">${ticker}:</span> ${error}</p>`;
                            }
                            
                            modalHtml += `</div>`;
                        } else {
                            modalHtml += `<p>No errors reported for this simulation.</p>`;
                        }
                        
                        modalHtml += `
                            <button class="button" style="margin-top: 20px;" onclick="document.body.removeChild(this.parentNode)">Close</button>
                        `;
                        
                        errorModal.innerHTML = modalHtml;
                        document.body.appendChild(errorModal);
                    })
                    .catch(error => {
                        console.error('Error fetching simulation details:', error);
                        alert(`Error fetching details for simulation #${id}: ${error.message}`);
                    });
            }
        </script>
    </head>
    <body>
        <h1>Stock Price Simulation API</h1>
        <p>Welcome to the Stock Price Simulation API. Use the following endpoints to run simulations:</p>
        
        <div class="tabs" id="main-tabs">
            <div class="tab active" data-tab="active-tab">Active Simulations</div>
            <div class="tab" data-tab="endpoints-tab">API Endpoints</div>
        </div>
        
        <div id="active-tab" class="tab-content active">
            <h2>Active Simulations</h2>
            <div id="active-simulations">
                <p>Loading simulations...</p>
            </div>
            
            <div class="form-group" style="margin-top: 20px;">
                <h3>Run New Simulation</h3>
                <p>Use the API endpoints below to start a new simulation.</p>
                <button class="button" onclick="window.location.reload()">Refresh Page</button>
            </div>
        </div>
        
        <div id="endpoints-tab" class="tab-content">
            <h2>API Endpoints</h2>
            
            <div class="endpoint">
                <h3>GET /api/tickers</h3>
                <p>Get a list of available tickers.</p>
                <pre>curl -X GET http://localhost:8080/api/tickers</pre>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/sectors</h3>
                <p>Get a list of available sectors.</p>
                <pre>curl -X GET http://localhost:8080/api/sectors</pre>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/tickers/{sector}</h3>
                <p>Get tickers for a specific sector.</p>
                <pre>curl -X GET http://localhost:8080/api/tickers/Technology</pre>
            </div>
            
            <div class="endpoint">
                <h3>POST /api/simulate</h3>
                <p>Run a simulation with the provided parameters.</p>
                <pre>
curl -X POST http://localhost:8080/api/simulate \\
     -H "Content-Type: application/json" \\
     -d '{
       "ticker": "AAPL",
       "model_type": "hybrid",
       "paths": 1000,
       "steps": 21,
       "calibrate": true
     }'
                </pre>
            </div>
            
            <div class="endpoint">
                <h3>POST /api/batch</h3>
                <p>Run simulations for multiple tickers.</p>
                <pre>
curl -X POST http://localhost:8080/api/batch \\
     -H "Content-Type: application/json" \\
     -d '{
       "tickers": ["AAPL", "MSFT", "GOOGL"],
       "model_type": "gbm",
       "paths": 1000,
       "steps": 21
     }'
                </pre>
            </div>
            
            <div class="endpoint">
                <h3>GET /api/simulations</h3>
                <p>Get status of active simulations.</p>
                <pre>curl -X GET http://localhost:8080/api/simulations</pre>
            </div>
            
            <div class="endpoint">
                <h3>POST /api/simulations/{id}/stop</h3>
                <p>Stop a running simulation.</p>
                <pre>curl -X POST http://localhost:8080/api/simulations/1/stop</pre>
            </div>
            
            <div class="endpoint">
                <h3>GET /output/{path}</h3>
                <p>Access output files (reports, graphs, etc.)</p>
                <pre>curl -X GET http://localhost:8080/output/reports/AAPL_report_20210101_123456.html</pre>
            </div>
        </div>
        
        <script>
            // Check if UI is working properly
            console.log('Bottom of page script loaded');
            
            // Add a fallback in case the DOMContentLoaded event already fired
            if (document.readyState === 'complete' || document.readyState === 'interactive') {
                console.log('Document already loaded, initializing UI directly');
                setTimeout(function() {
                    // Initialize main UI elements
                    const tabs = document.querySelectorAll('.tab');
                    tabs.forEach(tab => {
                        tab.addEventListener('click', function() {
                            const tabId = this.getAttribute('data-tab');
                            if (tabId) {
                                showTab(tabId);
                            }
                        });
                    });
                    
                    // Make sure active tab is shown
                    const activeTab = document.querySelector('.tab.active');
                    if (activeTab) {
                        const tabId = activeTab.getAttribute('data-tab');
                        if (tabId) {
                            showTab(tabId);
                        }
                    }
                    
                    // Fetch active simulations
                    fetchActiveSimulations();
                }, 100);
            }
        </script>
    </body>
    </html>
    """


@app.route('/api/tickers')
def get_tickers():
    """Get a list of available tickers."""
    # Refresh tickers if they're not loaded
    if not ticker_manager.get_tickers():
        ticker_manager.refresh_tickers()
    
    return jsonify({
        'tickers': ticker_manager.get_tickers()
    })


@app.route('/api/sectors')
def get_sectors():
    """Get a list of available sectors."""
    # Refresh tickers if they're not loaded
    if not ticker_manager.get_tickers():
        ticker_manager.refresh_tickers()
    
    return jsonify({
        'sectors': ticker_manager.get_sectors()
    })


@app.route('/api/tickers/<sector>')
def get_tickers_by_sector(sector):
    """Get tickers for a specific sector."""
    # Refresh tickers if they're not loaded
    if not ticker_manager.get_tickers():
        ticker_manager.refresh_tickers()
    
    limit = request.args.get('limit', default=None, type=int)
    tickers = ticker_manager.get_ticker_by_sector(sector, limit=limit)
    
    return jsonify({
        'sector': sector,
        'tickers': tickers
    })


def run_simulation_thread(sim_id, ticker, model_type, paths, steps, calibrate, lookback_period, advanced_params):
    """Run a simulation in a separate thread."""
    try:
        # Update simulation status
        with simulations['lock']:
            if sim_id in simulations['active']:
                simulations['active'][sim_id]['status'] = 'Running'
        
        # Run the simulation, passing the simulation_id
        result = engine.run_simulation(
            ticker=ticker,
            model_type=model_type,
            paths=paths,
            steps=steps,
            calibrate=calibrate,
            lookback_period=lookback_period,
            simulation_id=sim_id,  # Pass sim_id for stop handling
            **advanced_params
        )
        
        # Update the results
        with simulations['lock']:
            if sim_id in simulations['active']:  # Check if sim was canceled
                simulations['active'][sim_id]['status'] = 'Completed'
                simulations['active'][sim_id]['result'] = result
                # Keep completed simulation in the list for a while
                threading.Timer(300, lambda: remove_simulation(sim_id)).start()
    
    except InterruptedError as e:
        # Simulation was stopped by user
        with simulations['lock']:
            if sim_id in simulations['active']:
                simulations['active'][sim_id]['status'] = 'Stopped'
                simulations['active'][sim_id]['error'] = str(e)
    
    except Exception as e:
        import traceback
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        
        # Update the error info
        with simulations['lock']:
            if sim_id in simulations['active']:
                simulations['active'][sim_id]['status'] = 'Failed'
                simulations['active'][sim_id]['error'] = error_info
                # Keep failed simulation in the list for a while
                threading.Timer(300, lambda: remove_simulation(sim_id)).start()


def run_batch_simulation_thread(sim_id, tickers, model_type, paths, steps, calibrate, lookback_period, advanced_params):
    """Run batch simulations in a separate thread."""
    try:
        # Update simulation status
        with simulations['lock']:
            if sim_id in simulations['active']:
                simulations['active'][sim_id]['status'] = 'Running'
                # Initialize errors dict
                simulations['active'][sim_id]['errors'] = {}
        
        # Run the batch simulation, passing the simulation_id
        batch_results = engine.batch_simulate(
            tickers=tickers,
            model_type=model_type,
            paths=paths,
            steps=steps,
            calibrate=calibrate,
            lookback_period=lookback_period,
            simulation_id=sim_id,  # Pass sim_id for stop handling
            **advanced_params
        )
        
        # Extract results and errors
        results = batch_results.get('results', {})
        errors = batch_results.get('errors', {})
        summary = batch_results.get('summary', {})
        
        # Update the results
        with simulations['lock']:
            if sim_id in simulations['active']:  # Check if sim was canceled
                simulations['active'][sim_id]['status'] = 'Completed'
                simulations['active'][sim_id]['results'] = results
                simulations['active'][sim_id]['errors'] = errors
                simulations['active'][sim_id]['summary'] = summary
                
                # Print out errors to terminal for visibility
                if errors:
                    print("\n====== SIMULATION ERRORS ======")
                    for ticker, error in errors.items():
                        print(f"Error with {ticker}: {error}")
                    print("===============================\n")
                    
                # Keep completed simulation in the list for a while
                threading.Timer(300, lambda: remove_simulation(sim_id)).start()
    
    except InterruptedError as e:
        # Simulation was stopped by user
        with simulations['lock']:
            if sim_id in simulations['active']:
                simulations['active'][sim_id]['status'] = 'Stopped'
                simulations['active'][sim_id]['error'] = str(e)
    
    except Exception as e:
        import traceback
        error_info = {
            'error': str(e),
            'traceback': traceback.format_exc()
        }
        
        # Update the error info
        with simulations['lock']:
            if sim_id in simulations['active']:
                simulations['active'][sim_id]['status'] = 'Failed'
                simulations['active'][sim_id]['error'] = error_info
                # Keep failed simulation in the list for a while
                threading.Timer(300, lambda: remove_simulation(sim_id)).start()


def remove_simulation(sim_id):
    """Remove a simulation from the active list."""
    with simulations['lock']:
        if sim_id in simulations['active']:
            del simulations['active'][sim_id]


@app.route('/api/simulate', methods=['POST'])
def simulate():
    """Run a simulation with the provided parameters."""
    try:
        # Parse JSON data from the request
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract parameters
        ticker = data.get('ticker')
        if not ticker:
            return jsonify({'error': 'No ticker provided'}), 400
        
        model_type = data.get('model_type', 'hybrid')
        paths = int(data.get('paths', 1000))
        steps = int(data.get('steps', 21))
        calibrate = bool(data.get('calibrate', True))
        lookback_period = data.get('lookback_period', '2y')
        
        # Extract advanced parameters
        advanced_params = {}
        for param in ['mu', 'sigma', 'jump_intensity', 'jump_mean', 'jump_sigma', 'vol_clustering']:
            if param in data:
                advanced_params[param] = float(data[param])
        
        # Create a new simulation ID
        with simulations['lock']:
            sim_id = simulations['next_id']
            simulations['next_id'] += 1
            
            # Store simulation info
            simulations['active'][sim_id] = {
                'type': 'single',
                'tickers': [ticker],
                'model_type': model_type,
                'paths': paths,
                'steps': steps,
                'calibrate': calibrate,
                'status': 'Starting',
                'start_time': time.time()
            }
        
        # Start the simulation in a separate thread
        thread = threading.Thread(
            target=run_simulation_thread,
            args=(sim_id, ticker, model_type, paths, steps, calibrate, lookback_period, advanced_params)
        )
        thread.daemon = True
        thread.start()
        
        # Return the simulation ID
        return jsonify({
            'message': f'Simulation started for {ticker}',
            'simulation_id': sim_id
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/batch', methods=['POST'])
def batch_simulate():
    """Run simulations for multiple tickers."""
    try:
        # Parse JSON data from the request
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract parameters
        tickers = data.get('tickers')
        if not tickers:
            return jsonify({'error': 'No tickers provided'}), 400
        
        model_type = data.get('model_type', 'hybrid')
        paths = int(data.get('paths', 1000))
        steps = int(data.get('steps', 21))
        calibrate = bool(data.get('calibrate', True))
        lookback_period = data.get('lookback_period', '2y')
        
        # Extract advanced parameters
        advanced_params = {}
        for param in ['mu', 'sigma', 'jump_intensity', 'jump_mean', 'jump_sigma', 'vol_clustering']:
            if param in data:
                advanced_params[param] = float(data[param])
        
        # Create a new simulation ID
        with simulations['lock']:
            sim_id = simulations['next_id']
            simulations['next_id'] += 1
            
            # Store simulation info
            simulations['active'][sim_id] = {
                'type': 'batch',
                'tickers': tickers,
                'model_type': model_type,
                'paths': paths,
                'steps': steps,
                'calibrate': calibrate,
                'status': 'Starting',
                'start_time': time.time()
            }
        
        # Start the simulation in a separate thread
        thread = threading.Thread(
            target=run_batch_simulation_thread,
            args=(sim_id, tickers, model_type, paths, steps, calibrate, lookback_period, advanced_params)
        )
        thread.daemon = True
        thread.start()
        
        # Return the simulation ID
        return jsonify({
            'message': f'Batch simulation started for {len(tickers)} tickers',
            'simulation_id': sim_id,
            'tickers': tickers
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500


@app.route('/api/simulations')
def get_simulations():
    """Get the status of all active simulations."""
    with simulations['lock']:
        # Create a safe copy without thread objects and other non-serializable items
        active_sims = {}
        for sim_id, sim_info in simulations['active'].items():
            # Create a new dict with only serializable info
            active_sims[sim_id] = {
                'type': sim_info.get('type'),
                'tickers': sim_info.get('tickers', []),
                'model_type': sim_info.get('model_type'),
                'status': sim_info.get('status'),
                'start_time': sim_info.get('start_time')
            }
            
            # Add elapsed time
            if 'start_time' in sim_info:
                elapsed = time.time() - sim_info['start_time']
                active_sims[sim_id]['elapsed_seconds'] = elapsed
            
            # Add errors if they exist
            if 'errors' in sim_info and sim_info['errors']:
                active_sims[sim_id]['has_errors'] = True
                # Include up to 10 errors in the response
                error_items = list(sim_info['errors'].items())[:10]
                error_summary = {ticker: error for ticker, error in error_items}
                active_sims[sim_id]['error_summary'] = error_summary
                if len(sim_info['errors']) > 10:
                    active_sims[sim_id]['error_summary']['more'] = f"...and {len(sim_info['errors']) - 10} more errors"
            
            # Add results for completed simulations
            if sim_info.get('status') == 'Completed':
                if 'result' in sim_info:  # Single simulation
                    # Just provide a reference to the report or summary
                    result = sim_info['result']
                    if 'report_path' in result:
                        active_sims[sim_id]['report_path'] = result['report_path']
                elif 'results' in sim_info:  # Batch simulation
                    # Include the summary if available
                    if 'summary' in sim_info:
                        active_sims[sim_id]['summary'] = sim_info['summary']
                    else:
                        # Calculate summary if not already present
                        successful = sum(1 for r in sim_info['results'].values() if r is not None)
                        failed = len(sim_info['results']) - successful
                        active_sims[sim_id]['summary'] = {
                            'total': len(sim_info['results']),
                            'completed': successful,
                            'failed': failed
                        }
    
    return jsonify({
        'active': active_sims
    })


@app.route('/api/simulations/<int:sim_id>')
def get_simulation(sim_id):
    """Get the status of a specific simulation."""
    with simulations['lock']:
        if sim_id not in simulations['active']:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim_info = simulations['active'][sim_id]
        
        # Create a response with basic info
        response = {
            'id': sim_id,
            'type': sim_info.get('type'),
            'tickers': sim_info.get('tickers', []),
            'model_type': sim_info.get('model_type'),
            'status': sim_info.get('status')
        }
        
        # Add elapsed time
        if 'start_time' in sim_info:
            elapsed = time.time() - sim_info['start_time']
            response['elapsed_seconds'] = elapsed
        
        # Add errors if present
        if 'errors' in sim_info and sim_info['errors']:
            response['errors'] = sim_info['errors']
            response['has_errors'] = True
            response['error_count'] = len(sim_info['errors'])
        
        # Add summary if available for batch simulations
        if 'summary' in sim_info:
            response['summary'] = sim_info['summary']
        
        # Add results or error info if available
        if sim_info.get('status') == 'Completed':
            if 'result' in sim_info:  # Single simulation
                response['result'] = sim_info['result']
            elif 'results' in sim_info:  # Batch simulation
                # Don't include the full results as it can be large
                # Instead, return ticker names that succeeded
                successful_tickers = [
                    ticker for ticker, result in sim_info['results'].items() 
                    if result is not None
                ]
                response['successful_tickers'] = successful_tickers
                
                # Add the first result for reference if available
                if successful_tickers:
                    first_ticker = successful_tickers[0]
                    first_result = sim_info['results'][first_ticker]
                    if 'report_path' in first_result:
                        response['sample_report_path'] = first_result['report_path']
        
        elif sim_info.get('status') == 'Failed':
            if 'error' in sim_info:
                response['error'] = sim_info['error']
    
    return jsonify(response)


@app.route('/api/simulations/<int:sim_id>/stop', methods=['POST'])
def stop_simulation(sim_id):
    """Stop a running simulation."""
    with simulations['lock']:
        if sim_id not in simulations['active']:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim_info = simulations['active'][sim_id]
        
        # Set the status to stopped
        sim_info['status'] = 'Stopping'
        
        # Request stop in the simulation engine
        engine.request_stop(sim_id)
        
        # Update status
        sim_info['status'] = 'Stopped'
        
        # Schedule removal after a while
        threading.Timer(60, lambda: remove_simulation(sim_id)).start()
    
    return jsonify({
        'message': f'Simulation {sim_id} has been stopped',
        'id': sim_id
    })


@app.route('/output/<path:filename>')
def serve_output(filename):
    """Serve output files."""
    # Ensure the output directory exists
    output_dir = os.path.abspath("output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Serve the requested file
    return send_from_directory(output_dir, filename)


def main(port=8080):
    """Run the web server."""
    # Ensure the output directory exists
    output_dir = os.path.abspath("output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)


if __name__ == '__main__':
    main() 