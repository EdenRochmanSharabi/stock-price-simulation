#!/usr/bin/env python3

"""
Reporting Module
--------------
Generate HTML reports for simulation results.
"""

import os
import json
import datetime
import pandas as pd


def generate_stock_report(ticker, statistics, output_dir):
    """
    Generate an HTML report for a single stock simulation.
    
    Args:
        ticker (str): Stock ticker symbol
        statistics (dict): Simulation statistics
        output_dir (str): Directory to save report
        
    Returns:
        str: Path to the generated report
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate report filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{ticker}_report_{timestamp}.html"
    report_path = os.path.join(output_dir, report_filename)
    
    # Build a simple HTML report
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Simulation Report: {ticker}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #2c3e50; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        th, td {{ text-align: left; padding: 8px; }}
        th {{ background-color: #3498db; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .stats-container {{ display: flex; flex-wrap: wrap; }}
        .stats-box {{ flex: 1; min-width: 300px; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>Stock Price Simulation Report</h1>
    <div class="stats-box">
        <h2>{ticker} - Overview</h2>
        <table>
            <tr><th>Parameter</th><th>Value</th></tr>
            <tr><td>Model Type</td><td>{statistics.get('model_type', 'N/A')}</td></tr>
            <tr><td>Initial Price</td><td>${statistics.get('initial_price', 0):.2f}</td></tr>
            <tr><td>Number of Paths</td><td>{statistics.get('num_paths', 0)}</td></tr>
            <tr><td>Number of Steps</td><td>{statistics.get('num_steps', 0)}</td></tr>
            <tr><td>Time Horizon</td><td>{statistics.get('num_steps', 0)} trading days</td></tr>
            <tr><td>Expected Final Price</td><td>${statistics.get('mean_final_price', 0):.2f}</td></tr>
            <tr><td>Expected Return</td><td>{statistics.get('expected_return', 0):.2f}%</td></tr>
            <tr><td>Return Volatility</td><td>{statistics.get('return_volatility', 0):.2f}%</td></tr>
        </table>
    </div>
    
    <div class="stats-container">
        <div class="stats-box">
            <h2>Risk Metrics</h2>
            <table>
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>95% Value at Risk</td><td>${statistics.get('var_95', 0):.2f}</td></tr>
                <tr><td>99% Value at Risk</td><td>${statistics.get('var_99', 0):.2f}</td></tr>
                <tr><td>Maximum Drawdown</td><td>{statistics.get('max_drawdown', 0)*100:.2f}%</td></tr>
                <tr><td>Sharpe Ratio</td><td>{statistics.get('sharpe_ratio', 0):.2f}</td></tr>
                <tr><td>Sortino Ratio</td><td>{statistics.get('sortino_ratio', 0):.2f}</td></tr>
                <tr><td>Skewness</td><td>{statistics.get('skewness', 0):.2f}</td></tr>
                <tr><td>Kurtosis</td><td>{statistics.get('kurtosis', 0):.2f}</td></tr>
            </table>
        </div>
        
        <div class="stats-box">
            <h2>Probabilities</h2>
            <table>
                <tr><th>Event</th><th>Probability</th></tr>
                <tr><td>Profit</td><td>{statistics.get('prob_profit', 0):.2f}%</td></tr>
                <tr><td>Loss</td><td>{statistics.get('prob_loss', 0):.2f}%</td></tr>
                <tr><td>Up 10%+</td><td>{statistics.get('prob_up_10percent', 0):.2f}%</td></tr>
                <tr><td>Up 20%+</td><td>{statistics.get('prob_up_20percent', 0):.2f}%</td></tr>
                <tr><td>Down 10%+</td><td>{statistics.get('prob_down_10percent', 0):.2f}%</td></tr>
                <tr><td>Down 20%+</td><td>{statistics.get('prob_down_20percent', 0):.2f}%</td></tr>
            </table>
        </div>
    </div>
    
    <div class="stats-box">
        <h2>Price Distribution</h2>
        <table>
            <tr><th>Percentile</th><th>Price</th></tr>
    """
    
    # Add percentiles to the report
    if 'percentiles' in statistics:
        for percentile, value in statistics['percentiles'].items():
            html_content += f"<tr><td>{percentile}</td><td>${float(value):.2f}</td></tr>\n"
    
    html_content += """
        </table>
    </div>
    
    <div class="stats-box">
        <h2>Model Parameters</h2>
        <table>
            <tr><th>Parameter</th><th>Value</th></tr>
    """
    
    # Add model parameters
    model_params = [
        ('mu', 'Drift (μ)'),
        ('sigma', 'Volatility (σ)'),
        ('jump_intensity', 'Jump Intensity (λ)'),
        ('jump_mean', 'Jump Mean'),
        ('jump_sigma', 'Jump Volatility'),
        ('vol_clustering', 'Volatility Clustering')
    ]
    
    for param_key, param_name in model_params:
        if param_key in statistics:
            value = statistics[param_key]
            html_content += f"<tr><td>{param_name}</td><td>{value:.4f}</td></tr>\n"
    
    html_content += """
        </table>
    </div>
    
    <div class="stats-box">
        <h2>Simulation Information</h2>
        <p>This report was generated on: """ + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        <p>The simulation used a """ + statistics.get('model_type', 'unknown').upper() + """ model to generate """ + str(statistics.get('num_paths', 0)) + """ price paths over """ + str(statistics.get('num_steps', 0)) + """ trading days.</p>
    </div>
</body>
</html>
"""
    
    # Write the HTML to file
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    print(f"Generated report for {ticker}: {report_path}")
    return report_path


def generate_batch_report(results, output_dir):
    """
    Generate a batch report for multiple stock simulations.
    
    Args:
        results (dict): Dictionary of simulation results keyed by ticker
        output_dir (str): Directory to save report
        
    Returns:
        str: Path to the generated report
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate report filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"batch_report_{timestamp}.html"
    report_path = os.path.join(output_dir, report_filename)
    
    # Extract summary data for each ticker
    summary_data = []
    
    for ticker, result in results.items():
        if result is None or 'statistics' not in result:
            continue
            
        stats = result['statistics']
        summary_data.append({
            'Ticker': ticker,
            'Initial Price': f"${stats.get('initial_price', 0):.2f}",
            'Expected Return': f"{stats.get('expected_return', 0):.2f}%",
            'Return Volatility': f"{stats.get('return_volatility', 0):.2f}%",
            'Sharpe Ratio': f"{stats.get('sharpe_ratio', 0):.2f}",
            'Prob Profit': f"{stats.get('prob_profit', 0):.2f}%",
            'VaR 95%': f"${stats.get('var_95', 0):.2f}",
            'Max Drawdown': f"{stats.get('max_drawdown', 0)*100:.2f}%"
        })
    
    # Convert to DataFrame for easier HTML generation
    if summary_data:
        df = pd.DataFrame(summary_data)
        summary_table = df.to_html(index=False, classes="dataframe")
    else:
        summary_table = "<p>No valid simulation results to display.</p>"
    
    # Build the HTML report
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Batch Simulation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2 {{ color: #2c3e50; }}
        table.dataframe {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
        table.dataframe th, table.dataframe td {{ text-align: left; padding: 8px; }}
        table.dataframe th {{ background-color: #3498db; color: white; }}
        table.dataframe tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .container {{ margin: 20px; }}
    </style>
</head>
<body>
    <h1>Batch Simulation Report</h1>
    <div class="container">
        <h2>Summary Statistics</h2>
        {summary_table}
    </div>
    
    <div class="container">
        <h2>Simulation Information</h2>
        <p>This report was generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        <p>Number of tickers simulated: {len(results)}</p>
        <p>Number of successful simulations: {len(summary_data)}</p>
    </div>
</body>
</html>
"""
    
    # Write the HTML to file
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    print(f"Generated batch report: {report_path}")
    return report_path 