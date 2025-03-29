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


def generate_stock_report(ticker, result, output_dir):
    """
    Generate an HTML report for a single stock simulation.
    
    Args:
        ticker (str): Stock ticker symbol
        result (dict): Simulation result dictionary
        output_dir (str): Directory to save report
        
    Returns:
        str: Path to the generated report
    """
    # Ensure output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Extract data from result
    if not result or 'statistics' not in result or 'paths' not in result or 'graphs' not in result:
        print(f"Error: Invalid result data for {ticker}")
        return None
    
    stats = result['statistics']
    graphs = result['graphs']
    
    # Format paths for HTML
    paths_graph = f"../{os.path.relpath(graphs['paths'], output_dir)}"
    distribution_graph = f"../{os.path.relpath(graphs['distribution'], output_dir)}"
    return_histogram_graph = f"../{os.path.relpath(graphs['return_histogram'], output_dir)}"
    qq_plot_graph = f"../{os.path.relpath(graphs['qq_plot'], output_dir)}"
    returns_boxplot_graph = f"../{os.path.relpath(graphs['returns_boxplot'], output_dir)}"
    risk_reward_graph = f"../{os.path.relpath(graphs['risk_reward'], output_dir)}"
    
    # Generate report filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{ticker}_report_{timestamp}.html"
    report_path = os.path.join(output_dir, report_filename)
    
    # Helper function to format values with colors based on positive/negative
    def color_format(value, is_percent=False, reverse=False):
        """Format values with color coding"""
        if not isinstance(value, (int, float)):
            return value
        
        # Determine if positive or negative (or zero)
        if value > 0:
            color_class = "negative" if reverse else "positive"
        elif value < 0:
            color_class = "positive" if reverse else "negative"
        else:
            color_class = "neutral"
        
        # Format the value
        if is_percent:
            formatted = f"{value:.2f}%"
        else:
            formatted = f"{value:.2f}"
        
        return f"<span class='{color_class}'>{formatted}</span>"
    
    # Get summary statistics
    initial_price = stats.get('initial_price', 0)
    mean_final_price = stats.get('mean_final_price', 0)
    pct_return = ((mean_final_price / initial_price) - 1) * 100 if initial_price > 0 else 0
    
    # HTML Template with improved styling and structure
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{ticker} Stock Price Simulation</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 20px;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-radius: 8px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid #eee;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .metric-box {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .metric-box h3 {{
            margin-top: 0;
            margin-bottom: 10px;
            font-size: 16px;
            color: #2c3e50;
        }}
        .metric-box p {{
            margin: 0;
            font-size: 18px;
            font-weight: bold;
        }}
        .positive {{
            color: #28a745;
        }}
        .negative {{
            color: #dc3545;
        }}
        .neutral {{
            color: #6c757d;
        }}
        .percentiles {{
            margin-bottom: 20px;
        }}
        .percentiles table, .stats-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .percentiles th, .percentiles td, .stats-table th, .stats-table td {{
            text-align: left;
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }}
        .percentiles th, .stats-table th {{
            background-color: #f2f2f2;
        }}
        .image-section {{
            margin-top: 40px;
        }}
        .image-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
            gap: 20px;
        }}
        .image-container {{
            text-align: center;
            margin-bottom: 30px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-radius: 4px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            font-size: 14px;
            color: #6c757d;
        }}
        .tooltip {{
            position: relative;
            display: inline-block;
            cursor: help;
        }}
        .tooltip .tooltip-text {{
            visibility: hidden;
            width: 200px;
            background-color: #555;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -100px;
            opacity: 0;
            transition: opacity 0.3s;
        }}
        .tooltip:hover .tooltip-text {{
            visibility: visible;
            opacity: 1;
        }}
        .back-link {{
            color: #3498db;
            text-decoration: none;
            display: inline-block;
            margin-bottom: 20px;
            font-weight: 500;
        }}
        .back-link:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{ticker} Stock Price Simulation</h1>
            <p>Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="section">
            <h2>Summary</h2>
            <div class="metrics">
                <div class="metric-box">
                    <h3>Initial Price</h3>
                    <p>${initial_price:.2f}</p>
                </div>
                <div class="metric-box">
                    <h3>Expected Final Price</h3>
                    <p>${mean_final_price:.2f}</p>
                </div>
                <div class="metric-box">
                    <h3>Expected Return</h3>
                    <p class="{('positive' if pct_return >= 0 else 'negative')}">{pct_return:.2f}%</p>
                </div>
                <div class="metric-box">
                    <h3>Volatility</h3>
                    <p>{stats.get('return_volatility', 0):.2f}%</p>
                </div>
                <div class="metric-box">
                    <h3>Probability of Profit</h3>
                    <p>{stats.get('prob_profit', 0):.2f}%</p>
                </div>
                <div class="metric-box">
                    <h3>Sharpe Ratio</h3>
                    <p>{stats.get('sharpe_ratio', 0):.2f}</p>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Price Percentiles</h2>
            <div class="percentiles">
                <table>
                    <tr>
                        <th>Percentile</th>
                        <th>Price</th>
                        <th>Return</th>
                    </tr>
                    <tr>
                        <td>5%</td>
                        <td>${stats.get('percentiles', {}).get('5%', 0):.2f}</td>
                        <td class="{('positive' if (stats.get('percentiles', {}).get('5%', 0)/initial_price - 1)*100 >= 0 else 'negative')}">{((stats.get('percentiles', {}).get('5%', 0)/initial_price - 1)*100):.2f}%</td>
                    </tr>
                    <tr>
                        <td>25%</td>
                        <td>${stats.get('percentiles', {}).get('25%', 0):.2f}</td>
                        <td class="{('positive' if (stats.get('percentiles', {}).get('25%', 0)/initial_price - 1)*100 >= 0 else 'negative')}">{((stats.get('percentiles', {}).get('25%', 0)/initial_price - 1)*100):.2f}%</td>
                    </tr>
                    <tr>
                        <td>50% (Median)</td>
                        <td>${stats.get('percentiles', {}).get('50%', 0):.2f}</td>
                        <td class="{('positive' if (stats.get('percentiles', {}).get('50%', 0)/initial_price - 1)*100 >= 0 else 'negative')}">{((stats.get('percentiles', {}).get('50%', 0)/initial_price - 1)*100):.2f}%</td>
                    </tr>
                    <tr>
                        <td>75%</td>
                        <td>${stats.get('percentiles', {}).get('75%', 0):.2f}</td>
                        <td class="{('positive' if (stats.get('percentiles', {}).get('75%', 0)/initial_price - 1)*100 >= 0 else 'negative')}">{((stats.get('percentiles', {}).get('75%', 0)/initial_price - 1)*100):.2f}%</td>
                    </tr>
                    <tr>
                        <td>95%</td>
                        <td>${stats.get('percentiles', {}).get('95%', 0):.2f}</td>
                        <td class="{('positive' if (stats.get('percentiles', {}).get('95%', 0)/initial_price - 1)*100 >= 0 else 'negative')}">{((stats.get('percentiles', {}).get('95%', 0)/initial_price - 1)*100):.2f}%</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="section">
            <h2>Risk Metrics</h2>
            <div class="metrics">
                <div class="metric-box tooltip">
                    <h3>Value at Risk (95%)</h3>
                    <p>{stats.get('var_95', 0):.2f}%</p>
                    <span class="tooltip-text">Maximum expected loss at 95% confidence level</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Conditional VaR (95%)</h3>
                    <p>{stats.get('cvar_95', 0):.2f}%</p>
                    <span class="tooltip-text">Expected loss given the loss exceeds the 95% VaR</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Max Drawdown</h3>
                    <p>{stats.get('max_drawdown', 0):.2f}%</p>
                    <span class="tooltip-text">Largest percentage drop from peak to trough</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Sortino Ratio</h3>
                    <p>{stats.get('sortino_ratio', 0):.2f}</p>
                    <span class="tooltip-text">Risk-adjusted return focusing on downside volatility</span>
                </div>
            </div>
        </div>
        
        <div class="image-section">
            <h2>Visualizations</h2>
            <div class="image-grid">
                <div class="image-container">
                    <h3>Simulation Paths</h3>
                    <img src="{paths_graph}" alt="Price Simulation Paths">
                </div>
                <div class="image-container">
                    <h3>Final Price Distribution</h3>
                    <img src="{distribution_graph}" alt="Final Price Distribution">
                </div>
                <div class="image-container">
                    <h3>Returns Histogram</h3>
                    <img src="{return_histogram_graph}" alt="Returns Histogram">
                </div>
                <div class="image-container">
                    <h3>QQ Plot</h3>
                    <img src="{qq_plot_graph}" alt="QQ Plot">
                </div>
                <div class="image-container">
                    <h3>Returns Boxplot</h3>
                    <img src="{returns_boxplot_graph}" alt="Returns Boxplot">
                </div>
                <div class="image-container">
                    <h3>Risk-Reward Analysis</h3>
                    <img src="{risk_reward_graph}" alt="Risk-Reward Analysis">
                </div>
            </div>
        </div>
        
        <div class="header">
            <a href="consolidated_report.html" class="back-link">← Back to All Stocks</a>
        </div>
    </div>
    
    <script>
        // Enable tooltips via JavaScript for dynamic content
        document.addEventListener('mouseover', function(e) {{
            if (e.target.classList.contains('tooltip')) {{
                const tooltip = e.target.querySelector('.tooltip-text');
                if (tooltip) {{
                    tooltip.style.visibility = 'visible';
                    tooltip.style.opacity = '1';
                }}
            }}
        }});
        
        document.addEventListener('mouseout', function(e) {{
            if (e.target.classList.contains('tooltip')) {{
                const tooltip = e.target.querySelector('.tooltip-text');
                if (tooltip) {{
                    tooltip.style.visibility = 'hidden';
                    tooltip.style.opacity = '0';
                }}
            }}
        }});
    </script>
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
    
    # Create a consolidated report file that will always be at the same location
    consolidated_report_path = os.path.join(output_dir, "consolidated_report.html")
    
    # Extract summary data for each ticker
    summary_data = []
    stock_details = []
    
    for ticker, result in results.items():
        if result is None or 'statistics' not in result:
            continue
            
        stats = result['statistics']
        model_params = result.get('model_params', {})
        
        # Get required statistics
        initial_price = stats.get('initial_price', 0)
        mean_final_price = stats.get('mean_final_price', 0)
        median_final_price = stats.get('percentiles', {}).get('50%', 0)
        min_price = stats.get('min_price', 0)
        max_price = stats.get('max_price', 0)
        std_dev = stats.get('std_final_price', 0)
        percentile_5 = stats.get('percentiles', {}).get('5%', 0)
        percentile_95 = stats.get('percentiles', {}).get('95%', 0)
        
        # Add to summary table
        summary_data.append({
            'Ticker': ticker,
            'Initial Price': f"${initial_price:.2f}",
            'Mean Final Price': f"${mean_final_price:.2f}",
            'Median Final Price': f"${median_final_price:.2f}",
            'Min Price': f"${min_price:.2f}",
            'Max Price': f"${max_price:.2f}",
            'Std Dev': f"${std_dev:.2f}",
            '5% Percentile': f"${percentile_5:.2f}",
            '95% Percentile': f"${percentile_95:.2f}"
        })
        
        # Get paths to graphs (relative to HTML file)
        ticker_paths_graph = f"/graphs/{ticker}_paths.png"
        ticker_dist_graph = f"/graphs/{ticker}_distribution.png"
        
        # Calculate percentages for downside risk and upside potential
        downside_risk = (percentile_5 / initial_price - 1) * 100 if initial_price > 0 else 0
        upside_potential = (percentile_95 / initial_price - 1) * 100 if initial_price > 0 else 0
        
        # Create detailed section for each stock
        stock_detail = f"""
        <div class='stock-section'>
            <h2>{ticker} Detailed Analysis</h2>
            <div class='statistics'>
                <div class='stat-item'><strong>Initial Price:</strong> ${initial_price:.2f}</div>
                <div class='stat-item'><strong>Annual Drift:</strong> {model_params.get('mu', 0)*100:.2f}%</div>
                <div class='stat-item'><strong>Annual Volatility:</strong> {model_params.get('sigma', 0)*100:.2f}%</div>
                <div class='stat-item'><strong>Expected Return:</strong> {stats.get('expected_return', 0):.2f}%</div>
                <div class='stat-item'><strong>Downside Risk (5%):</strong> {downside_risk:.2f}%</div>
                <div class='stat-item'><strong>Upside Potential (95%):</strong> {upside_potential:.2f}%</div>
            </div>
            
            <h3>Price Distribution</h3>
            <p>The simulation shows the potential price range for {ticker} after running {stats.get('num_paths', 1000)} simulation paths with {stats.get('num_steps', 21)} time steps:</p>
            <ul>
                <li><strong>Mean Final Price:</strong> ${mean_final_price:.2f}</li>
                <li><strong>Median Final Price:</strong> ${median_final_price:.2f}</li>
                <li><strong>Standard Deviation:</strong> ${std_dev:.2f}</li>
                <li><strong>Minimum Final Price:</strong> ${min_price:.2f}</li>
                <li><strong>Maximum Final Price:</strong> ${max_price:.2f}</li>
            </ul>
            
            <h3>Percentiles</h3>
            <ul>
                <li><strong>5th Percentile:</strong> ${percentile_5:.2f}</li>
                <li><strong>25th Percentile:</strong> ${stats.get('percentiles', {}).get('25%', 0):.2f}</li>
                <li><strong>50th Percentile (Median):</strong> ${median_final_price:.2f}</li>
                <li><strong>75th Percentile:</strong> ${stats.get('percentiles', {}).get('75%', 0):.2f}</li>
                <li><strong>95th Percentile:</strong> ${percentile_95:.2f}</li>
            </ul>
            
            <h3>Simulation Visualizations</h3>
        <img src='{ticker_paths_graph}' alt='{ticker} Simulation Paths'><img src='{ticker_dist_graph}' alt='{ticker} Price Distribution'></div>"""
        
        stock_details.append(stock_detail)
    
    # Create the summary table HTML
    if summary_data:
        # Generate table HTML manually to match the old format exactly
        table_rows = []
        table_rows.append("<tr><th>Ticker</th><th>Initial Price</th><th>Mean Final Price</th><th>Median Final Price</th><th>Min Price</th><th>Max Price</th><th>Std Dev</th><th>5% Percentile</th><th>95% Percentile</th></tr>")
        
        for row in summary_data:
            table_rows.append(f"""
        <tr>
            <td>{row['Ticker']}</td>
            <td>{row['Initial Price']}</td>
            <td>{row['Mean Final Price']}</td>
            <td>{row['Median Final Price']}</td>
            <td>{row['Min Price']}</td>
            <td>{row['Max Price']}</td>
            <td>{row['Std Dev']}</td>
            <td>{row['5% Percentile']}</td>
            <td>{row['95% Percentile']}</td>
        </tr>
        """)
        
        summary_table = "<table>" + "".join(table_rows) + "</table>"
    else:
        summary_table = "<p>No valid simulation results to display.</p>"
    
    # Create the complete HTML content
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Price Forecast</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            margin: 0;
            padding: 0;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .header {{
            padding: 20px;
            background-color: #2c3e50;
            color: white;
            margin-bottom: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #2c3e50;
            color: white;
            text-align: left;
            padding: 12px 15px;
        }}
        td {{
            padding: 10px 15px;
            border-bottom: 1px solid #ddd;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        .stock-section {{
            margin-bottom: 40px;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .statistics {{
            display: flex;
            flex-wrap: wrap;
        }}
        .stat-item {{
            width: 33%;
            margin-bottom: 10px;
        }}
        img {{
            max-width: 100%;
            height: auto;
            margin-top: 15px;
            border: 1px solid #ddd;
        }}
        .positive {{
            color: #28a745;
            font-weight: bold;
        }}
        .negative {{
            color: #dc3545;
            font-weight: bold;
        }}
        .neutral {{
            color: #6c757d;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Stock Price Simulation Summary Report</h1>
            <p>Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p>This report summarizes the Monte Carlo simulation results for multiple stocks using a regime-switching, jump-diffusion model with earnings shocks.</p>
        </div>
        
        <h2>Simulation Results Summary</h2>
        {summary_table}
        
        {''.join(stock_details)}
        
        <div class="footer">
            <p>Simulation powered by advanced stochastic modeling techniques. The results presented are for educational purposes only and should not be considered financial advice.</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write the HTML to file
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    # Also write to the consolidated report file
    with open(consolidated_report_path, 'w') as f:
        f.write(html_content)
    
    print(f"Generated batch report: {report_path}")
    print(f"Created consolidated report: {consolidated_report_path}")
    return report_path 