#!/usr/bin/env python3

"""
Report Generation Module
-----------------------
Generates HTML reports for simulation results.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import matplotlib.gridspec as gridspec
from matplotlib.ticker import PercentFormatter
import glob
from typing import Dict, List, Any, Tuple, Union, Optional
import textwrap
from jinja2 import Template, Environment, BaseLoader
from stock_simulation_engine.modules.engine import create_directory


# Define custom filters for Jinja2
def format_price(value):
    """Format a number as a price with 2 decimal places."""
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "0.00"  # Return default if conversion fails

def format_percent(value):
    """Format a number as a percentage with 2 decimal places."""
    try:
        return f"{float(value):.2f}"
    except (ValueError, TypeError):
        return "0.00"  # Return default if conversion fails

def format_num(value):
    """Format a number with thousand separators."""
    try:
        return f"{int(value):,}"
    except (ValueError, TypeError):
        return "0"  # Return default if conversion fails


def generate_stock_report(ticker, statistics, output_dir):
    """
    Generate an HTML report for a single stock.
    
    Args:
        ticker (str): Stock ticker symbol
        statistics (dict): Statistics dictionary from simulation
        output_dir (str): Output directory for reports
    
    Returns:
        str: Path to the generated report
    """
    # Determine reports directory
    if os.path.basename(output_dir) == "reports":
        reports_dir = output_dir
    else:
        # Create reports subdirectory
        reports_dir = os.path.join('output', "reports")
        create_directory(reports_dir)
    
    # Ensure all required statistics are present with defaults
    required_stats = {
        'sharpe_ratio': 0.0,
        'sortino_ratio': 0.0,
        'max_drawdown': 0.0,
        'return_volatility': 0.0,
        'skewness': 0.0,
        'kurtosis': 0.0,
        't_stat': 0.0,
        'p_value': 0.0,
        'return_ci_lower': 0.0,
        'return_ci_upper': 0.0,
        'shapiro_stat': 0.0,
        'shapiro_p': 0.0,
        'mean_return': 0.0,
        'std_return': 0.0,
        'var_95': 0.0,
        'cvar_95': 0.0,
        'var_99': 0.0,
        'cvar_99': 0.0,
        'percentiles': {
            '1': 0.0,
            '5': 0.0,
            '10': 0.0,
            '25': 0.0,
            '50': 0.0,
            '75': 0.0,
            '90': 0.0,
            '95': 0.0,
            '99': 0.0
        }
    }
    
    # Update statistics with defaults for missing values
    for key, default_value in required_stats.items():
        if key not in statistics:
            statistics[key] = default_value
        elif isinstance(default_value, dict) and isinstance(statistics.get(key), dict):
            for subkey, subdefault in default_value.items():
                if subkey not in statistics[key]:
                    statistics[key][subkey] = subdefault
    
    # Basic template for stock report
    template_str = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ ticker }} Stock Price Simulation</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                margin: 0;
                padding: 20px;
                color: #333;
                line-height: 1.6;
            }
            .container {
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background-color: white;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-radius: 8px;
            }
            h1, h2, h3 {
                color: #2c3e50;
            }
            .header {
                text-align: center;
                margin-bottom: 20px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            .section {
                margin-bottom: 30px;
            }
            .metrics {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                gap: 15px;
                margin-bottom: 30px;
            }
            .metric-box {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .metric-box h3 {
                margin-top: 0;
                margin-bottom: 10px;
                font-size: 16px;
                color: #2c3e50;
            }
            .metric-box p {
                margin: 0;
                font-size: 18px;
                font-weight: bold;
            }
            .positive {
                color: #28a745;
            }
            .negative {
                color: #dc3545;
            }
            .neutral {
                color: #6c757d;
            }
            .percentiles {
                margin-bottom: 20px;
            }
            .percentiles table, .stats-table {
                width: 100%;
                border-collapse: collapse;
            }
            .percentiles th, .percentiles td, .stats-table th, .stats-table td {
                text-align: left;
                padding: 8px;
                border-bottom: 1px solid #ddd;
            }
            .percentiles th, .stats-table th {
                background-color: #f2f2f2;
            }
            .recommendation {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 4px;
                color: white;
                font-weight: bold;
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
            .image-section {
                margin-top: 40px;
            }
            .image-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
                gap: 20px;
            }
            .image-container {
                text-align: center;
                margin-bottom: 30px;
            }
            img {
                max-width: 100%;
                height: auto;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                border-radius: 4px;
            }
            .footer {
                text-align: center;
                margin-top: 40px;
                font-size: 14px;
                color: #6c757d;
            }
            .tooltip {
                position: relative;
                display: inline-block;
                cursor: help;
            }
            .tooltip .tooltiptext {
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
            }
            .tooltip:hover .tooltiptext {
                visibility: visible;
                opacity: 1;
            }
            .sim-params {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 6px;
                margin-bottom: 20px;
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
            }
            .sim-params div {
                margin-bottom: 10px;
            }
            .sim-params h3 {
                margin-top: 0;
                margin-bottom: 5px;
                font-size: 14px;
                color: #6c757d;
            }
            .sim-params p {
                margin: 0;
                font-weight: bold;
            }
            .back-link {
                display: inline-block;
                margin-bottom: 20px;
                padding: 5px 10px;
                background-color: #f8f9fa;
                color: #2c3e50;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
            }
            .back-link:hover {
                background-color: #e9ecef;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="consolidated_report.html" class="back-link">← Back to All Stocks</a>
            
            <div class="header">
                <h1>{{ ticker }} Stock Price Simulation</h1>
                <p>1-Month Price Forecast | {{ today_date }}</p>
                
                {% if expected_return >= 8 and prob_up_20percent >= 30 %}
                    <div class="recommendation strong-buy">STRONG BUY</div>
                {% elif expected_return >= 5 %}
                    <div class="recommendation buy">BUY</div>
                {% elif expected_return <= -8 and prob_down_20percent >= 30 %}
                    <div class="recommendation strong-sell">STRONG SELL</div>
                {% elif expected_return <= -5 %}
                    <div class="recommendation sell">SELL</div>
                {% else %}
                    <div class="recommendation hold">HOLD</div>
                {% endif %}
            </div>
            
            <div class="section">
                <h2>Simulation Parameters</h2>
                <div class="sim-params">
                    <div>
                        <h3>Model Type</h3>
                        <p>{{ model_type | upper }}</p>
                    </div>
                    <div>
                        <h3>Number of Paths</h3>
                        <p>{{ num_paths | format_num }}</p>
                    </div>
                    <div>
                        <h3>Time Steps</h3>
                        <p>{{ num_steps }}</p>
                    </div>
                    <div>
                        <h3>Time Step Size</h3>
                        <p>{{ '%.4f' % dt|float }} years ({{ (dt|float) * 252 | format_price }} days)</p>
                    </div>
                    <div>
                        <h3>Drift (μ)</h3>
                        <p>{{ mu|float|format_price }} (annualized)</p>
                    </div>
                    <div>
                        <h3>Volatility (σ)</h3>
                        <p>{{ sigma|float|format_price }} (annualized)</p>
                    </div>
                    {% if model_type == 'jump' or model_type == 'combined' %}
                    <div>
                        <h3>Jump Intensity</h3>
                        <p>{{ jump_intensity|float|format_price }} jumps/year</p>
                    </div>
                    <div>
                        <h3>Jump Mean</h3>
                        <p>{{ jump_mean|float|format_price }}</p>
                    </div>
                    <div>
                        <h3>Jump Volatility</h3>
                        <p>{{ jump_sigma|float|format_price }}</p>
                    </div>
                    {% endif %}
                    {% if model_type == 'combined' %}
                    <div>
                        <h3>Volatility Clustering</h3>
                        <p>{{ vol_clustering|float|format_price }}</p>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <div class="section">
                <h2>Key Metrics</h2>
                <div class="metrics">
                    <div class="metric-box">
                        <h3>Current Price</h3>
                        <p>${{ initial_price|format_price }}</p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Forecast Price (1m)</h3>
                        <p>${{ mean_final_price|format_price }}</p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Expected Return</h3>
                        <p class="{% if expected_return > 0 %}positive{% elif expected_return < 0 %}negative{% else %}neutral{% endif %}">
                            {{ expected_return|format_percent }}%
                        </p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Volatility</h3>
                        <p>{{ return_volatility|format_percent }}%</p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Probability of Profit</h3>
                        <p class="{% if prob_profit > 50 %}positive{% elif prob_profit < 50 %}negative{% else %}neutral{% endif %}">
                            {{ prob_profit|format_percent }}%
                        </p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Upside Potential</h3>
                        <p class="positive">{{ prob_up_20percent|format_percent }}%</p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Downside Risk</h3>
                        <p class="negative">{{ prob_down_20percent|format_percent }}%</p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Value at Risk (95%)</h3>
                        <p class="negative">${{ var_95|format_price }}</p>
                    </div>
                    
                    {% if has_scipy %}
                    <div class="metric-box">
                        <h3>
                            <span class="tooltip">Sharpe Ratio
                                <span class="tooltiptext">Risk-adjusted return measure. Higher is better.</span>
                            </span>
                        </h3>
                        <p class="{% if sharpe_ratio > 1 %}positive{% elif sharpe_ratio < 0 %}negative{% else %}neutral{% endif %}">
                            {{ sharpe_ratio|format_price }}
                        </p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>
                            <span class="tooltip">Sortino Ratio
                                <span class="tooltiptext">Measures return against downside risk. Higher is better.</span>
                            </span>
                        </h3>
                        <p class="{% if sortino_ratio > 1 %}positive{% elif sortino_ratio < 0 %}negative{% else %}neutral{% endif %}">
                            {{ sortino_ratio|format_price }}
                        </p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>
                            <span class="tooltip">Max Drawdown
                                <span class="tooltiptext">Maximum observed price decline. Lower is better.</span>
                            </span>
                        </h3>
                        <p class="negative">{{ (max_drawdown|float * 100)|format_percent }}%</p>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <div class="section">
                <h2>Price Distribution</h2>
                <div class="percentiles">
                    <table>
                        <tr>
                            <th>Percentile</th>
                            <th>Price</th>
                            <th>Return</th>
                        </tr>
                        <tr>
                            <td>1% (Worst Case)</td>
                            <td>${{ percentiles['1%']|format_price }}</td>
                            <td class="negative">{{ ((percentiles['1%']|float / initial_price|float - 1) * 100)|format_percent }}%</td>
                        </tr>
                        <tr>
                            <td>5% </td>
                            <td>${{ percentiles['5%']|format_price }}</td>
                            <td class="negative">{{ ((percentiles['5%']|float / initial_price|float - 1) * 100)|format_percent }}%</td>
                        </tr>
                        <tr>
                            <td>25%</td>
                            <td>${{ percentiles['25%']|format_price }}</td>
                            <td class="{% if (percentiles['25%']|float / initial_price|float - 1) * 100 > 0 %}positive{% else %}negative{% endif %}">
                                {{ ((percentiles['25%']|float / initial_price|float - 1) * 100)|format_percent }}%
                            </td>
                        </tr>
                        <tr>
                            <td>50% (Median)</td>
                            <td>${{ percentiles['50%']|format_price }}</td>
                            <td class="{% if (percentiles['50%']|float / initial_price|float - 1) * 100 > 0 %}positive{% else %}negative{% endif %}">
                                {{ ((percentiles['50%']|float / initial_price|float - 1) * 100)|format_percent }}%
                            </td>
                        </tr>
                        <tr>
                            <td>75%</td>
                            <td>${{ percentiles['75%']|format_price }}</td>
                            <td class="positive">{{ ((percentiles['75%']|float / initial_price|float - 1) * 100)|format_percent }}%</td>
                        </tr>
                        <tr>
                            <td>95%</td>
                            <td>${{ percentiles['95%']|format_price }}</td>
                            <td class="positive">{{ ((percentiles['95%']|float / initial_price|float - 1) * 100)|format_percent }}%</td>
                        </tr>
                        <tr>
                            <td>99% (Best Case)</td>
                            <td>${{ percentiles['99%']|format_price }}</td>
                            <td class="positive">{{ ((percentiles['99%']|float / initial_price|float - 1) * 100)|format_percent }}%</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            {% if has_scipy %}
            <div class="section">
                <h2>Advanced Statistics</h2>
                <div class="advanced-stats">
                    <table class="stats-table">
                        <tr>
                            <th>Statistic</th>
                            <th>Value</th>
                            <th>Interpretation</th>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">Skewness
                                    <span class="tooltiptext">Measures the asymmetry of return distribution</span>
                                </span>
                            </td>
                            <td>{{ skewness|format_price }}</td>
                            <td>
                                {% if skewness > 0.5 %}
                                    Right-skewed distribution (more upside potential)
                                {% elif skewness < -0.5 %}
                                    Left-skewed distribution (more downside risk)
                                {% else %}
                                    Roughly symmetric distribution
                                {% endif %}
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">Kurtosis
                                    <span class="tooltiptext">Measures the "tailedness" of distribution</span>
                                </span>
                            </td>
                            <td>{{ kurtosis|format_price }}</td>
                            <td>
                                {% if kurtosis > 2 %}
                                    Heavy-tailed (more extreme outcomes)
                                {% elif kurtosis < -0.5 %}
                                    Light-tailed (fewer extreme outcomes)
                                {% else %}
                                    Close to normal distribution
                                {% endif %}
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">t-statistic
                                    <span class="tooltiptext">Tests if return is significantly different from zero</span>
                                </span>
                            </td>
                            <td>{{ t_stat|format_price }}</td>
                            <td>
                                {% if p_value < 0.05 %}
                                    <span class="{% if t_stat > 0 %}positive{% else %}negative{% endif %}">
                                        Statistically significant (p = {{ p_value|format_price }})
                                    </span>
                                {% else %}
                                    <span class="neutral">
                                        Not statistically significant (p = {{ p_value|format_price }})
                                    </span>
                                {% endif %}
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">95% Confidence Interval
                                    <span class="tooltiptext">Range of likely outcomes with 95% confidence</span>
                                </span>
                            </td>
                            <td colspan="2">
                                {{ return_ci_lower|format_price }}% to {{ return_ci_upper|format_price }}%
                            </td>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">Normality Test
                                    <span class="tooltiptext">{{ normality_test }} test for normal distribution</span>
                                </span>
                            </td>
                            <td>{{ normality_stat|format_price }}</td>
                            <td>
                                {% if normality_p > 0.05 %}
                                    <span class="positive">
                                        Returns follow normal distribution (p = {{ normality_p|format_price }})
                                    </span>
                                {% else %}
                                    <span class="neutral">
                                        Returns do not follow normal distribution (p = {{ normality_p|format_price }})
                                    </span>
                                {% endif %}
                            </td>
                        </tr>
                    </table>
                </div>
            </div>
            {% endif %}
            
            <div class="image-section">
                <h2>Simulation Visualizations</h2>
                
                <div class="image-grid">
                    <div class="image-container">
                        <h3>Simulated Price Paths</h3>
                        <img src="../graphs/{{ ticker }}_price_paths.png" alt="Price Paths">
                    </div>
                    
                    <div class="image-container">
                        <h3>Final Price Distribution</h3>
                        <img src="../graphs/{{ ticker }}_price_histogram.png" alt="Price Distribution">
                    </div>
                    
                    <div class="image-container">
                        <h3>Return Distribution</h3>
                        <img src="../graphs/{{ ticker }}_return_histogram.png" alt="Return Distribution">
                    </div>
                    
                    {% if has_scipy %}
                    <div class="image-container">
                        <h3>Return QQ Plot</h3>
                        <img src="../graphs/{{ ticker }}_qq_plot.png" alt="Return QQ Plot">
                    </div>
                    
                    <div class="image-container">
                        <h3>Daily Returns Box Plot</h3>
                        <img src="../graphs/{{ ticker }}_returns_boxplot.png" alt="Returns Box Plot">
                    </div>
                    
                    <div class="image-container">
                        <h3>Risk-Reward Analysis</h3>
                        <img src="../graphs/{{ ticker }}_risk_reward.png" alt="Risk-Reward Analysis">
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <div class="footer">
                <p>Generated on {{ today_date }} using Monte Carlo simulation with 
                   {{ num_paths }} paths over {{ num_steps }} trading days.</p>
                <p>This report is for educational purposes only and should not be considered investment advice.</p>
                <p><a href="consolidated_report.html">Back to All Stocks</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create a Jinja2 environment with our custom filters
    env = Environment(loader=BaseLoader())
    env.filters['format_price'] = format_price
    env.filters['format_percent'] = format_percent
    env.filters['format_num'] = format_num
    env.filters['round'] = lambda x, y: round(float(x), y)
    env.filters['int'] = lambda x: int(x)
    env.filters['join'] = lambda x, y: y.join(x) if isinstance(x, (list, tuple)) else str(x)
    env.filters['upper'] = lambda x: x.upper() if isinstance(x, str) else str(x)
    
    # Add a safe multiplication filter
    def safe_multiply(value, factor):
        try:
            return float(value) * float(factor)
        except (TypeError, ValueError):
            return 0.0
    
    env.filters['safe_multiply'] = safe_multiply
    
    # Modify template to avoid multiplication issues
    modified_template = template_str
    # Fix Max Drawdown line
    modified_template = modified_template.replace('{{ (max_drawdown|float * 100)|format_percent }}%', 
                                                 '{{ max_drawdown|float|safe_multiply(100)|format_percent }}%')
    
    # Fix dt calculation
    modified_template = modified_template.replace('{{ (dt|float) * 252 | format_price }}', 
                                                '{{ dt|float|safe_multiply(252)|format_price }}')
    
    # Fix percentile calculations
    percentiles = ["1%", "5%", "25%", "50%", "75%", "95%", "99%"]
    for p in percentiles:
        # Example expression: {{ ((percentiles['1%']|float / initial_price|float - 1) * 100)|format_percent }}
        old_expr = f"{{ ((percentiles['{p}']|float / initial_price|float - 1) * 100)|format_percent }}"
        new_expr = f"{{ ((percentiles['{p}']|float / initial_price|float - 1)|safe_multiply(100))|format_percent }}"
        modified_template = modified_template.replace(old_expr, new_expr)
    
    # Create the template from the modified string
    template = env.from_string(modified_template)
    
    # Convert a copy of statistics to avoid modifying the original
    render_data = statistics.copy()
    
    # Add additional template variables
    render_data.update({
        'today_date': datetime.now().strftime("%Y-%m-%d"),
        'num_paths': statistics.get('num_paths', 1000),
        'num_steps': statistics.get('num_steps', 21),
    })
    
    # Ensure all numeric values are floats to avoid type errors in the template
    for key, value in render_data.items():
        if isinstance(value, (int, float)) and key != 'num_paths' and key != 'num_steps':
            render_data[key] = float(value)
    
    # Special handling for percentiles dictionary
    if 'percentiles' in render_data and isinstance(render_data['percentiles'], dict):
        for key, value in render_data['percentiles'].items():
            if isinstance(value, (int, float)):
                render_data['percentiles'][key] = float(value)
    
    # Render template
    try:
        html_content = template.render(**render_data)
        
        # Save report
        report_path = os.path.join(reports_dir, f"{ticker}_report.html")
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        return report_path
    except Exception as e:
        print(f"Error rendering template for {ticker}: {str(e)}")
        raise


def generate_consolidated_report(results, output_dir):
    """
    Generate a consolidated report of all stock simulations.
    
    Args:
        results (dict): Dictionary of simulation results by ticker
        output_dir (str): Output directory for reports
    
    Returns:
        str: Path to the consolidated report
    """
    # Determine if output_dir is already a reports directory
    if os.path.basename(output_dir) == "reports":
        reports_dir = output_dir
    else:
        # Create reports subdirectory
        reports_dir = os.path.join(output_dir, "reports")
        create_directory(reports_dir)
    
    # Create a dataframe to store all stock data
    stocks_data = []
    
    for ticker, result in results.items():
        statistics = result['statistics']
        sector = result.get('sector', 'Unknown')
        model_type = result.get('model_type', 'combined')
        
        # Extract simulation parameters
        sim_params = {
            'model_type': model_type,
            'num_paths': result.get('paths_matrix', {}).shape[0] if 'paths_matrix' in result else 1000,
            'num_steps': result.get('paths_matrix', {}).shape[1] - 1 if 'paths_matrix' in result else 21,
        }
        
        # Determine recommendation
        expected_return = statistics['expected_return']
        prob_up_20 = statistics['prob_up_20percent']
        prob_down_20 = statistics['prob_down_20percent']
        
        if expected_return >= 8 and prob_up_20 >= 30:
            recommendation = "STRONG BUY"
            recommendation_class = "strong-buy"
        elif expected_return >= 5:
            recommendation = "BUY"
            recommendation_class = "buy"
        elif expected_return <= -8 and prob_down_20 >= 30:
            recommendation = "STRONG SELL"
            recommendation_class = "strong-sell"
        elif expected_return <= -5:
            recommendation = "SELL"
            recommendation_class = "sell"
        else:
            recommendation = "HOLD"
            recommendation_class = "hold"
        
        # Add to dataframe
        stocks_data.append({
            "ticker": ticker,
            "sector": sector,
            "model_type": model_type,
            "num_paths": sim_params['num_paths'],
            "num_steps": sim_params['num_steps'],
            "recommendation": recommendation,
            "recommendation_class": recommendation_class,
            "current_price": statistics['initial_price'],
            "forecast_price": statistics['mean_final_price'],
            "expected_return": statistics['expected_return'],
            "volatility": statistics.get('return_volatility', 0),
            "sharpe": statistics.get('sharpe_ratio', 0),
            "prob_profit": statistics['prob_profit'],
            "upside": statistics['prob_up_20percent'],
            "downside": statistics['prob_down_20percent']
        })
    
    # Return early if no data
    if not stocks_data:
        print("No data available for consolidated report")
        return None
    
    # Convert to dataframe
    df = pd.DataFrame(stocks_data)
    
    # Add sorting value for recommendations
    rec_order = {
        "STRONG BUY": 1,
        "BUY": 2,
        "HOLD": 3,
        "SELL": 4,
        "STRONG SELL": 5
    }
    df["rec_order"] = df["recommendation"].map(rec_order)
    
    # Sort by sector and recommendation
    df = df.sort_values(["sector", "rec_order"])
    
    # Group by sector
    sectors = df.sector.unique()
    
    # Template for consolidated report
    template_str = """
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
                <p>1-Month Horizon | Report generated on {{ report_date }}</p>
            </div>
        </div>
        
        <div class="container">
            <div class="sim-summary">
                <h3>Simulation Summary</h3>
                <p>This consolidated report contains simulations for {{ num_stocks }} stocks across {{ num_sectors }} sectors.</p>
                <ul>
                    <li><strong>Models:</strong> {{ df.model_type.unique() | join(', ') | upper }}</li>
                    <li><strong>Paths:</strong> {{ df.num_paths.mean() | int }} (average)</li>
                    <li><strong>Steps:</strong> {{ df.num_steps.mean() | int }} (average)</li>
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
                    {% for sector in sectors %}
                    <tr>
                        <td colspan="9" class="sector-heading">{{ sector }}</td>
                    </tr>
                    {% for _, row in df[df.sector == sector].iterrows() %}
                    <tr>
                        <td><a href="/view_report?type=stock&ticker={{ row.ticker }}" class="ticker-link">{{ row.ticker }}</a></td>
                        <td>{{ row.model_type | upper }}</td>
                        <td><div class="{{ row.recommendation_class }}">{{ row.recommendation }}</div></td>
                        <td>${{ row.current_price|round(2) }}</td>
                        <td>${{ row.forecast_price|round(2) }}</td>
                        <td class="{% if row.expected_return > 0 %}positive{% elif row.expected_return < 0 %}negative{% endif %}">
                            {{ row.expected_return|round(2) }}%
                        </td>
                        <td>{{ row.volatility|round(2) }}%</td>
                        <td class="{% if row.sharpe > 0.5 %}positive{% elif row.sharpe < 0 %}negative{% endif %}">
                            {{ row.sharpe|round(2) }}
                        </td>
                        <td>{{ row.prob_profit|round(2) }}%</td>
                    </tr>
                    {% endfor %}
                    {% endfor %}
                </tbody>
            </table>
            
            <div class="footer">
                <p>These forecasts are based on Monte Carlo simulations over a 1-month horizon.</p>
                <p>The information provided is for educational purposes only and should not be considered financial advice.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create a Jinja2 environment with our custom filters
    env = Environment(loader=BaseLoader())
    env.filters['format_price'] = format_price
    env.filters['format_percent'] = format_percent
    env.filters['format_num'] = format_num
    env.filters['round'] = lambda x, y: round(float(x), y)
    env.filters['int'] = lambda x: int(x)
    env.filters['join'] = lambda x, y: y.join(x)
    env.filters['upper'] = lambda x: x.upper() if isinstance(x, str) else x
    
    # Create the template from the string and environment
    template = env.from_string(template_str)
    
    # Render template
    html_content = template.render(
        report_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        num_stocks=len(df),
        num_sectors=len(sectors),
        sectors=sectors,
        df=df
    )
    
    # Save as HTML
    report_path = os.path.join(reports_dir, "consolidated_report.html")
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    print(f"Consolidated report saved to: {report_path}")
    return report_path


def generate_report(results, output_dir):
    """
    Generate comprehensive HTML reports for all simulation results.
    
    Args:
        results (dict): Dictionary of simulation results
        output_dir (str): Base output directory
    """
    print("\nGenerating simulation reports...")
    
    # Always use standard directories regardless of what's passed in
    # If output_dir is something like 'output/20250328_123456', we still
    # want to save to 'output/reports' for consistency
    base_output_dir = 'output'
    if output_dir != base_output_dir:
        if os.path.dirname(output_dir) == base_output_dir:
            # If it's like 'output/something', use the base
            output_dir = base_output_dir
    
    # Use simplified directory structure
    reports_dir = os.path.join(base_output_dir, "reports")
    graphs_dir = os.path.join(base_output_dir, "graphs")
    
    # Create reports directory if it doesn't exist
    create_directory(reports_dir)
    create_directory(graphs_dir)
    
    # Ensure we have results
    if not results:
        print("No results to generate reports for.")
        return
    
    # Generate individual stock reports
    for ticker, result in results.items():
        try:
            # Add simulation parameters to statistics
            result_stats = result['statistics'].copy()
            
            # Add model parameters
            result_stats.update({
                'model_type': result.get('model_type', 'combined'),
                'num_paths': result.get('paths_matrix', {}).shape[0] if 'paths_matrix' in result else 1000,
                'num_steps': result.get('paths_matrix', {}).shape[1] - 1 if 'paths_matrix' in result else 21,
                'dt': 1/252,  # Default time step
                'mu': result_stats.get('mu', result_stats.get('expected_return', 0)/100),
                'sigma': result_stats.get('sigma', result_stats.get('return_volatility', 0)/100),
                'jump_intensity': result.get('jump_intensity', 10),
                'jump_mean': result.get('jump_mean', -0.01),
                'jump_sigma': result.get('jump_sigma', 0.02),
                'vol_clustering': result.get('vol_clustering', 0.85)
            })
            
            # Ensure normality test values are properly mapped for the report template
            if 'normality_stat' in result_stats:
                result_stats['shapiro_stat'] = result_stats['normality_stat']
            if 'normality_p' in result_stats:
                result_stats['shapiro_p'] = result_stats['normality_p']
            if 'normality_test' not in result_stats:
                result_stats['normality_test'] = 'Shapiro-Wilk'  # Default test name if missing
            
            # Generate individual report directly in the reports directory
            report_path = os.path.join(reports_dir, f"{ticker}_report.html")
            generate_stock_report(ticker, result_stats, reports_dir)
            
            print(f"Generated report for {ticker}")
        except Exception as e:
            print(f"Error generating report for {ticker}: {str(e)}")
    
    # Generate consolidated report
    try:
        consolidated_path = generate_consolidated_report(results, reports_dir)
        if consolidated_path:
            print(f"Consolidated report saved to: {consolidated_path}")
    except Exception as e:
        print(f"Error generating consolidated report: {str(e)}")
    
    print(f"Reports generated successfully in {reports_dir}")


if __name__ == "__main__":
    # Test with dummy data if run directly
    test_stats = {
        "ticker": "TEST",
        "initial_price": 100.0,
        "mean_final_price": 105.0,
        "median_final_price": 104.0,
        "std_final_price": 10.0,
        "min_final_price": 80.0,
        "max_final_price": 130.0,
        "percentiles": {
            "1%": 85.0,
            "5%": 90.0,
            "10%": 93.0,
            "25%": 98.0,
            "50%": 104.0,
            "75%": 110.0,
            "90%": 118.0,
            "95%": 122.0,
            "99%": 128.0
        },
        "expected_return": 5.0,
        "median_return": 4.0,
        "var_95": 10.0,
        "var_99": 15.0,
        "prob_profit": 60.0,
        "prob_loss": 40.0,
        "prob_up_10percent": 30.0,
        "prob_up_20percent": 15.0,
        "prob_down_10percent": 20.0,
        "prob_down_20percent": 10.0
    }
    
    generate_stock_report("TEST", test_stats, "output") 