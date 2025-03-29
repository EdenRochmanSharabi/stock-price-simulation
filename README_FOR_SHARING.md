# Stock Price Simulation Web Application

This package contains a stock price simulation tool with a web interface for easy configuration and visualization.

## Contents

- Web interface for running simulations
- Monte Carlo simulation engine with GBM, Jump Diffusion, and Combined models
- Real-time simulation progress tracking
- Interactive HTML reports with visualizations
- S&P 500 sector analysis

## Installation Instructions

1. Make sure Python 3.8+ is installed on your computer
2. Extract all files to a folder of your choice
3. Open a terminal/command prompt and navigate to the extracted folder
4. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. From the main folder, run:
   ```
   python run_web_ui.py
   ```
2. A browser window should automatically open to the web interface (http://localhost:5001)
3. If the browser doesn't open automatically, manually navigate to http://localhost:5001

## Using the Web Interface

1. **Configure Simulation Parameters**:
   - Select model type (Combined, GBM, or Jump Diffusion)
   - Set number of simulation paths (more paths = higher accuracy but slower)
   - Set time horizon (number of steps/trading days)
   - Choose how many companies to simulate per sector

2. **Select Market Sectors**:
   - Choose which S&P 500 sectors to include in the simulation

3. **Run Simulation**:
   - Click "Start Simulation" to begin
   - Monitor progress in real-time
   - When complete, view the consolidated report

4. **View Reports**:
   - The consolidated report shows statistics for all simulated stocks
   - Click on individual ticker symbols to see detailed reports with visualizations
   - All reports are saved in the output/reports directory

## Troubleshooting

- **Port in Use Error**: If port 5001 is already in use, edit run_web_ui.py and change the port number
- **Missing Graphs**: If reports show missing graphs, run a simulation first to generate them
- **Long Running Time**: Reduce the number of paths or number of companies per sector for faster results

## Technical Notes

- The simulation uses Monte Carlo methods with regime-switching and jump diffusion
- Historical data is used to calibrate model parameters
- All simulation data is stored locally in the output directory 