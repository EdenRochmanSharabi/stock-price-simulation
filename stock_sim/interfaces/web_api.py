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
    <html>
    <head>
        <title>Stock Price Simulation API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
            h1, h2 { color: #2c3e50; }
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
        </style>
        <script>
            // Simple JavaScript for interactive features
            document.addEventListener('DOMContentLoaded', function() {
                // Check active simulations on page load
                fetchActiveSimulations();
                
                // Set up periodic refresh of active simulations
                setInterval(fetchActiveSimulations, 5000);
            });
            
            function fetchActiveSimulations() {
                fetch('/api/simulations')
                    .then(response => response.json())
                    .then(data => {
                        const activeSimsDiv = document.getElementById('active-simulations');
                        activeSimsDiv.innerHTML = '';
                        
                        if (Object.keys(data.active).length === 0) {
                            activeSimsDiv.innerHTML = '<p>No active simulations</p>';
                            return;
                        }
                        
                        // Create elements for each active simulation
                        for (const [id, sim] of Object.entries(data.active)) {
                            const simDiv = document.createElement('div');
                            simDiv.className = 'status running';
                            simDiv.innerHTML = `
                                <h3>Simulation #${id}</h3>
                                <p>Ticker(s): ${sim.tickers.join(', ')}</p>
                                <p>Model: ${sim.model_type}</p>
                                <p>Status: ${sim.status}</p>
                                <button class="button stop" onclick="stopSimulation(${id})">Stop Simulation</button>
                            `;
                            activeSimsDiv.appendChild(simDiv);
                        }
                    })
                    .catch(error => console.error('Error fetching simulations:', error));
            }
            
            function stopSimulation(id) {
                fetch(`/api/simulations/${id}/stop`, { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                        fetchActiveSimulations();
                    })
                    .catch(error => console.error('Error stopping simulation:', error));
            }
        </script>
    </head>
    <body>
        <h1>Stock Price Simulation API</h1>
        <p>Welcome to the Stock Price Simulation API. Use the following endpoints to run simulations:</p>
        
        <h2>Active Simulations</h2>
        <div id="active-simulations">
            <p>Loading...</p>
        </div>
        
        <div class="endpoint">
            <h2>GET /api/tickers</h2>
            <p>Get a list of available tickers.</p>
            <pre>curl -X GET http://localhost:8080/api/tickers</pre>
        </div>
        
        <div class="endpoint">
            <h2>GET /api/sectors</h2>
            <p>Get a list of available sectors.</p>
            <pre>curl -X GET http://localhost:8080/api/sectors</pre>
        </div>
        
        <div class="endpoint">
            <h2>GET /api/tickers/{sector}</h2>
            <p>Get tickers for a specific sector.</p>
            <pre>curl -X GET http://localhost:8080/api/tickers/Technology</pre>
        </div>
        
        <div class="endpoint">
            <h2>POST /api/simulate</h2>
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
            <h2>POST /api/batch</h2>
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
            <h2>GET /api/simulations</h2>
            <p>Get status of active simulations.</p>
            <pre>curl -X GET http://localhost:8080/api/simulations</pre>
        </div>
        
        <div class="endpoint">
            <h2>POST /api/simulations/{id}/stop</h2>
            <p>Stop a running simulation.</p>
            <pre>curl -X POST http://localhost:8080/api/simulations/1/stop</pre>
        </div>
        
        <div class="endpoint">
            <h2>GET /output/{path}</h2>
            <p>Access output files (reports, graphs, etc.)</p>
            <pre>curl -X GET http://localhost:8080/output/reports/AAPL_report_20210101_123456.html</pre>
        </div>
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
        
        # Run the batch simulation, passing the simulation_id
        results = engine.batch_simulate(
            tickers=tickers,
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
                simulations['active'][sim_id]['results'] = results
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
                
            # Add results for completed simulations
            if sim_info.get('status') == 'Completed':
                if 'result' in sim_info:  # Single simulation
                    # Just provide a reference to the report or summary
                    result = sim_info['result']
                    if 'report_path' in result:
                        active_sims[sim_id]['report_path'] = result['report_path']
                elif 'results' in sim_info:  # Batch simulation
                    # Just count successful vs failed
                    successful = sum(1 for r in sim_info['results'].values() if r is not None)
                    failed = len(sim_info['results']) - successful
                    active_sims[sim_id]['summary'] = {
                        'successful': successful,
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
        
        # Add results or error info if available
        if sim_info.get('status') == 'Completed':
            if 'result' in sim_info:  # Single simulation
                response['result'] = sim_info['result']
            elif 'results' in sim_info:  # Batch simulation
                response['results'] = sim_info['results']
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