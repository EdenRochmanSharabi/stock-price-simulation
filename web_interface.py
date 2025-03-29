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
import pandas as pd
import numpy as np
from jinja2 import Environment, BaseLoader

# Set the path to find modules correctly
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Set matplotlib backend to Agg (non-interactive) for thread safety
import matplotlib
matplotlib.use('Agg')

from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from stock_sim.simulation_engine import SimulationEngine
from stock_sim.utils.sp500 import SP500TickerManager
from stock_sim.analysis.reporting import generate_stock_report, generate_batch_report

# Create the output directory if it doesn't exist
def create_directory(directory):
    """Create a directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

# SP500 utility functions to bridge between old and new interfaces
def get_sector_mapping():
    """Get a mapping of sectors to tickers."""
    manager = SP500TickerManager()
    manager.refresh_tickers(force=True)
    
    sectors = manager.get_sectors()
    mapping = {}
    
    for sector in sectors:
        mapping[sector] = manager.get_ticker_by_sector(sector)
    
    return mapping

def save_sector_mapping_to_csv(mapping):
    """Save the sector mapping to CSV files."""
    manager = SP500TickerManager()
    # The manager saves the data automatically when refreshed
    manager._sectors = {}
    for sector, tickers in mapping.items():
        for ticker in tickers:
            manager._sectors[ticker] = sector
    manager._tickers = list(manager._sectors.keys())
    manager._save_data()
    return True

def load_sector_mapping_from_csv():
    """Load the sector mapping from CSV files."""
    manager = SP500TickerManager()
    sectors = manager.get_sectors()
    mapping = {}
    
    for sector in sectors:
        mapping[sector] = manager.get_ticker_by_sector(sector)
    
    return mapping

# Bridge for the generate_report function
def generate_report(result, ticker, output_dir, is_multi_stock=False):
    """
    Bridge function to generate reports using the new structure.
    
    Args:
        result: Simulation result(s)
        ticker: Ticker symbol or "multi_stock" for batch reports
        output_dir: Directory to save the report
        is_multi_stock: Whether it's a multi-stock report
    """
    if is_multi_stock or ticker == "multi_stock":
        return generate_batch_report(result, output_dir)
    else:
        # Pass the entire result object, not just the statistics
        return generate_stock_report(ticker, result, output_dir)

def generate_stock_report(ticker, result, output_dir):
    """
    Generate an HTML report for a single stock.
    
    Args:
        ticker (str): Stock ticker symbol
        result (dict): Simulation result including statistics
        output_dir (str): Output directory for reports
    
    Returns:
        str: Path to the generated report
    """
    # Check if result is valid
    if not result or 'statistics' not in result:
        print(f"Error: Invalid result data for {ticker}")
        return None
        
    # Extract statistics from result
    statistics = result['statistics']
    
    # Determine reports directory
    if os.path.basename(output_dir) == "reports":
        reports_dir = output_dir
    else:
        # Create reports subdirectory
        reports_dir = os.path.join(output_dir, "reports")
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
            '1%': 0.0,
            '5%': 0.0,
            '10%': 0.0,
            '25%': 0.0,
            '50%': 0.0,
            '75%': 0.0,
            '90%': 0.0,
            '95%': 0.0,
            '99%': 0.0
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
    
    # Add model information if available
    model_info = {
        'model_type': result.get('model_type', 'combined'),
        'num_paths': 1000,
        'num_steps': 21,
        'dt': 1/252,
        'mu': statistics.get('mu', 0.0),
        'sigma': statistics.get('sigma', 0.0),
        'jump_intensity': result.get('jump_intensity', 10),
        'jump_mean': result.get('jump_mean', 0),
        'jump_sigma': result.get('jump_sigma', 0),
        'vol_clustering': result.get('vol_clustering', 0.85)
    }
    
    # Try to extract paths matrix info
    if 'paths_matrix' in result:
        try:
            model_info['num_paths'] = result['paths_matrix'].shape[0]
            model_info['num_steps'] = result['paths_matrix'].shape[1] - 1
        except (AttributeError, IndexError):
            pass
            
    # Determine if scipy is available for advanced stats
    try:
        import scipy
        has_scipy = True
    except ImportError:
        has_scipy = False
    
    # Add timestamp to filename to avoid overwriting
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"{ticker}_report_{timestamp}.html"
    report_path = os.path.join(reports_dir, report_filename)
    
    # Template for stock report
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
            .stats-table {
                margin-bottom: 20px;
                width: 100%;
            }
            .stats-table table {
                width: 100%;
                border-collapse: collapse;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            }
            .stats-table th {
                background-color: #f2f2f2;
                color: #333;
                font-weight: bold;
            }
            .stats-table tr:nth-child(even) {
                background-color: #f8f9fa;
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
            /* Modal for enlarged images */
            .modal {
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                overflow: auto;
                background-color: rgba(0,0,0,0.85);
                transition: opacity 0.3s ease;
            }
            .modal-content {
                display: block;
                max-width: 90%;
                max-height: 90%;
                margin: auto;
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                box-shadow: 0 4px 8px rgba(0,0,0,0.2);
                cursor: zoom-out;
            }
            .close {
                position: absolute;
                top: 15px;
                right: 25px;
                color: white;
                font-size: 35px;
                font-weight: bold;
                cursor: pointer;
            }
            .close:hover {
                color: #999;
            }
            .clickable-image {
                cursor: zoom-in;
                transition: transform 0.2s;
            }
            .clickable-image:hover {
                transform: scale(1.02);
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
                        <p>{{ num_paths }}</p>
                    </div>
                    <div>
                        <h3>Time Steps</h3>
                        <p>{{ num_steps }}</p>
                    </div>
                    <div>
                        <h3>Time Step Size</h3>
                        <p>{{ '%.4f' % dt }} years ({{ (dt * 252) | round(1) }} days)</p>
                    </div>
                    <div>
                        <h3>Drift (μ)</h3>
                        <p>{{ mu | round(4) }} (annualized)</p>
                    </div>
                    <div>
                        <h3>Volatility (σ)</h3>
                        <p>{{ sigma | round(4) }} (annualized)</p>
                    </div>
                    {% if model_type == 'jump' or model_type == 'combined' %}
                    <div>
                        <h3>Jump Intensity</h3>
                        <p>{{ jump_intensity | round(2) }} jumps/year</p>
                    </div>
                    <div>
                        <h3>Jump Mean</h3>
                        <p>{{ jump_mean | round(4) }}</p>
                    </div>
                    <div>
                        <h3>Jump Volatility</h3>
                        <p>{{ jump_sigma | round(4) }}</p>
                    </div>
                    {% endif %}
                    {% if model_type == 'combined' %}
                    <div>
                        <h3>Volatility Clustering</h3>
                        <p>{{ vol_clustering | round(2) }}</p>
                    </div>
                    {% endif %}
                </div>
            </div>
            
            <div class="section">
                <h2>Key Metrics</h2>
                <div class="metrics">
                    <div class="metric-box">
                        <h3>Current Price</h3>
                        <p>${{ initial_price | round(2) }}</p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Forecast Price (1m)</h3>
                        <p>${{ mean_final_price | round(2) }}</p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Expected Return</h3>
                        <p class="{% if expected_return > 0 %}positive{% elif expected_return < 0 %}negative{% else %}neutral{% endif %}">
                            {{ expected_return | round(2) }}%
                        </p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Volatility</h3>
                        <p>{{ return_volatility | round(2) }}%</p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Probability of Profit</h3>
                        <p class="{% if prob_profit > 50 %}positive{% elif prob_profit < 50 %}negative{% else %}neutral{% endif %}">
                            {{ prob_profit | round(2) }}%
                        </p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Upside Potential</h3>
                        <p class="positive">{{ prob_up_20percent | round(2) }}%</p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Downside Risk</h3>
                        <p class="negative">{{ prob_down_20percent | round(2) }}%</p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>Value at Risk (95%)</h3>
                        <p class="negative">${{ var_95 | round(2) }}</p>
                    </div>
                    
                    {% if has_scipy %}
                    <div class="metric-box">
                        <h3>
                            <span class="tooltip">Sharpe Ratio
                                <span class="tooltiptext">Risk-adjusted return measure. Higher is better.</span>
                            </span>
                        </h3>
                        <p class="{% if sharpe_ratio > 1 %}positive{% elif sharpe_ratio < 0 %}negative{% else %}neutral{% endif %}">
                            {{ sharpe_ratio | round(2) }}
                        </p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>
                            <span class="tooltip">Sortino Ratio
                                <span class="tooltiptext">Measures return against downside risk. Higher is better.</span>
                            </span>
                        </h3>
                        <p class="{% if sortino_ratio > 1 %}positive{% elif sortino_ratio < 0 %}negative{% else %}neutral{% endif %}">
                            {{ sortino_ratio | round(2) }}
                        </p>
                    </div>
                    
                    <div class="metric-box">
                        <h3>
                            <span class="tooltip">Max Drawdown
                                <span class="tooltiptext">Maximum observed price decline. Lower is better.</span>
                            </span>
                        </h3>
                        <p class="negative">{{ (max_drawdown * 100) | round(2) }}%</p>
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
                            <th>Stock Market Interpretation</th>
                        </tr>
                        <tr>
                            <td>1% (Worst Case)</td>
                            <td>${{ percentiles['1%'] | round(2) }}</td>
                            <td class="negative">{{ ((percentiles['1%'] / initial_price - 1) * 100) | round(2) }}%</td>
                            <td>Maximum loss threshold (99% confidence). Consider this your stop-loss level for risk management.</td>
                        </tr>
                        <tr>
                            <td>5% </td>
                            <td>${{ percentiles['5%'] | round(2) }}</td>
                            <td class="negative">{{ ((percentiles['5%'] / initial_price - 1) * 100) | round(2) }}%</td>
                            <td>Value-at-Risk (VaR) threshold. Useful for setting protective stops and sizing positions.</td>
                        </tr>
                        <tr>
                            <td>25%</td>
                            <td>${{ percentiles['25%'] | round(2) }}</td>
                            <td class="{% if (percentiles['25%'] / initial_price - 1) * 100 > 0 %}positive{% else %}negative{% endif %}">
                                {{ ((percentiles['25%'] / initial_price - 1) * 100) | round(2) }}%
                            </td>
                            <td>Lower quartile price - significant downside potential if reached, consider reevaluating position.</td>
                        </tr>
                        <tr>
                            <td>50% (Median)</td>
                            <td>${{ percentiles['50%'] | round(2) }}</td>
                            <td class="{% if (percentiles['50%'] / initial_price - 1) * 100 > 0 %}positive{% else %}negative{% endif %}">
                                {{ ((percentiles['50%'] / initial_price - 1) * 100) | round(2) }}%
                            </td>
                            <td>Most likely price outcome. Use as central forecast for investment decisions.</td>
                        </tr>
                        <tr>
                            <td>75%</td>
                            <td>${{ percentiles['75%'] | round(2) }}</td>
                            <td class="positive">{{ ((percentiles['75%'] / initial_price - 1) * 100) | round(2) }}%</td>
                            <td>Upper quartile price - possible target for taking partial profits in bullish scenarios.</td>
                        </tr>
                        <tr>
                            <td>95%</td>
                            <td>${{ percentiles['95%'] | round(2) }}</td>
                            <td class="positive">{{ ((percentiles['95%'] / initial_price - 1) * 100) | round(2) }}%</td>
                            <td>Optimistic but realistic price target. Consider for profit-taking strategies.</td>
                        </tr>
                        <tr>
                            <td>99% (Best Case)</td>
                            <td>${{ percentiles['99%'] | round(2) }}</td>
                            <td class="positive">{{ ((percentiles['99%'] / initial_price - 1) * 100) | round(2) }}%</td>
                            <td>Maximum realistic upside (99% confidence). Useful for setting aggressive price targets.</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <div class="section">
                <h2>Advanced Statistics</h2>
                <div class="stats-table">
                    <table>
                        <tr>
                            <th>Statistic</th>
                            <th>Value</th>
                            <th>Stock Market Interpretation</th>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">Skewness
                                    <span class="tooltiptext">Measures asymmetry of return distribution. Positive values indicate right skew, negative values indicate left skew.</span>
                                </span>
                            </td>
                            <td>{{ skewness | round(2) }}</td>
                            <td>{% if skewness > 0.5 %}Positive skew indicates higher chance of large gains than losses. Favorable for long positions.{% elif skewness < -0.5 %}Negative skew suggests higher risk of sudden large drops. Consider hedging or smaller position sizes.{% else %}Balanced upside/downside risk profile. Typical market behavior.{% endif %}</td>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">Kurtosis
                                    <span class="tooltiptext">Measures "tailedness" of distribution. Higher values indicate more outliers and fat tails.</span>
                                </span>
                            </td>
                            <td>{{ kurtosis | round(2) }}</td>
                            <td>{% if kurtosis > 1 %}Higher likelihood of extreme price movements (crashes or rallies). Consider using options for protection or reduced position sizing.{% elif kurtosis < -1 %}Returns likely to be more consistent and predictable. Suitable for steady strategies.{% else %}Normal market volatility expected. Standard risk management appropriate.{% endif %}</td>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">t-statistic
                                    <span class="tooltiptext">Tests if returns are statistically different from zero. Larger absolute values indicate greater significance.</span>
                                </span>
                            </td>
                            <td>{{ t_stat | round(2) }}</td>
                            <td>{% if t_stat > 0 %}Positive trend in returns{% else %}Negative trend in returns{% endif %}. {% if t_stat|abs > 1.96 %}Strong evidence of non-random price movement.{% else %}Trend may be due to random variation.{% endif %}</td>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">t-test p-value
                                    <span class="tooltiptext">Probability that observed returns could happen by chance. Lower values indicate stronger statistical significance.</span>
                                </span>
                            </td>
                            <td>{{ p_value | round(2) }}</td>
                            <td class="{% if p_value < 0.05 %}positive{% else %}neutral{% endif %}">{% if p_value < 0.05 %}Statistically significant (p < 0.05). {% if t_stat > 0 %}Strong bullish signal.{% else %}Strong bearish signal.{% endif %}{% else %}Not statistically significant. Trend may be random noise.{% endif %}</td>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">95% Confidence Interval
                                    <span class="tooltiptext">Range within which the true return is likely to fall with 95% probability.</span>
                                </span>
                            </td>
                            <td>{{ return_ci_lower | round(2) }}% to {{ return_ci_upper | round(2) }}%</td>
                            <td>{% if return_ci_lower > 0 %}High confidence in positive returns. Strong buy signal with clearly defined upside.{% elif return_ci_upper < 0 %}High confidence in negative returns. Consider avoiding or shorting if appropriate.{% else %}Uncertain direction with both positive and negative scenarios possible. Consider neutral strategies or waiting for clearer signals.{% endif %}</td>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">Normality Test Statistic
                                    <span class="tooltiptext">Tests if returns follow a normal distribution. Used to validate risk models.</span>
                                </span>
                            </td>
                            <td>{{ normality_stat | round(2) }}</td>
                            <td>Measure of how closely returns follow a bell curve distribution. {% if normality_p > 0.05 %}Returns appear to follow normal distribution.{% else %}Returns show deviation from normal distribution.{% endif %}</td>
                        </tr>
                        <tr>
                            <td>
                                <span class="tooltip">Normality Test p-value
                                    <span class="tooltiptext">Probability value for normality test. Values above 0.05 suggest normal distribution.</span>
                                </span>
                            </td>
                            <td>{{ normality_p | round(2) }}</td>
                            <td class="{% if normality_p > 0.05 %}positive{% else %}negative{% endif %}">{% if normality_p > 0.05 %}Returns follow normal distribution (p > 0.05). Standard risk models like VaR and options pricing are reliable.{% else %}Returns deviate from normal distribution (p < 0.05). Standard risk models may underestimate extreme events - consider extra hedging.{% endif %}</td>
                        </tr>
                    </table>
                </div>
            </div>
            
            <div class="image-section">
                <h2>Simulation Visualizations</h2>
                
                <div class="image-grid">
                    <div class="image-container">
                        <h3>Simulated Price Paths</h3>
                        <img src="../graphs/{{ ticker }}_paths.png" alt="Price Paths" class="clickable-image" onclick="openModal(this.src)">
                    </div>
                    
                    <div class="image-container">
                        <h3>Price Distribution</h3>
                        <img src="../graphs/{{ ticker }}_distribution.png" alt="Price Distribution" class="clickable-image" onclick="openModal(this.src)">
                    </div>
                    
                    <div class="image-container">
                        <h3>Return Distribution</h3>
                        <img src="../graphs/{{ ticker }}_return_histogram.png" alt="Return Distribution" class="clickable-image" onclick="openModal(this.src)">
                    </div>
                    
                    <div class="image-container">
                        <h3>QQ Plot</h3>
                        <img src="../graphs/{{ ticker }}_qq_plot.png" alt="QQ Plot" class="clickable-image" onclick="openModal(this.src)">
                    </div>
                    
                    <div class="image-container">
                        <h3>Daily Returns</h3>
                        <img src="../graphs/{{ ticker }}_returns_boxplot.png" alt="Returns Box Plot" class="clickable-image" onclick="openModal(this.src)">
                    </div>
                    
                    <div class="image-container">
                        <h3>Risk-Reward Analysis</h3>
                        <img src="../graphs/{{ ticker }}_risk_reward.png" alt="Risk-Reward Analysis" class="clickable-image" onclick="openModal(this.src)">
                    </div>
                </div>
            </div>
            
            <!-- Modal for enlarged images -->
            <div id="imageModal" class="modal">
                <span class="close" onclick="closeModal()">&times;</span>
                <img id="modalImage" class="modal-content">
            </div>
            
            <div class="footer">
                <p>Generated on {{ today_date }} using Monte Carlo simulation with 
                   {{ num_paths }} paths over {{ num_steps }} trading days.</p>
                <p>This report is for educational purposes only and should not be considered investment advice.</p>
            </div>
        </div>
        
        <script>
            // Image modal functionality
            const modal = document.getElementById("imageModal");
            const modalImg = document.getElementById("modalImage");
            
            function openModal(imageSrc) {
                modal.style.display = "block";
                modalImg.src = imageSrc;
            }
            
            function closeModal() {
                modal.style.display = "none";
            }
            
            // Close modal when clicking outside the image
            modal.addEventListener('click', function(event) {
                if (event.target === modal) {
                    closeModal();
                }
            });
            
            // Close modal with escape key
            document.addEventListener('keydown', function(event) {
                if (event.key === "Escape") {
                    closeModal();
                }
            });
        </script>
    </body>
    </html>
    """
    
    # Prepare context for template
    context = {
        'ticker': ticker,
        'today_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'has_scipy': has_scipy
    }
    
    # Add all statistics to context
    context.update(statistics)
    
    # Add model parameters
    context.update(model_info)
    
    # Create Jinja2 environment
    env = Environment(loader=BaseLoader())
    
    # Add custom filters
    env.filters['round'] = lambda value, precision=2: round(float(value), precision)
    
    # Load template from string
    template = env.from_string(template_str)
    
    # Render HTML
    html_content = template.render(**context)
    
    # Write to file
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    print(f"Generated report for {ticker}: {report_path}")
    return report_path

# Create Flask app with appropriate static folder
app = Flask(__name__, static_folder='templates/static')

# Initialize simulation engine
simulation_engine = SimulationEngine(output_base_dir="output")

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

# Add utility functions for formatting in the report template
def format_price(value):
    """Format a price value for display."""
    return f"${float(value):.2f}"

def format_percent(value):
    """Format a percentage value for display."""
    return f"{float(value):.2f}%"

def format_num(value):
    """Format a number value for display."""
    return f"{float(value):.4f}"

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
        # Create directories for output
        data_dir = os.path.join(output_dir, 'data')
        reports_dir = os.path.join(output_dir, 'reports')
        graphs_dir = os.path.join(output_dir, 'graphs')
        
        create_directory(data_dir)
        create_directory(reports_dir)
        create_directory(graphs_dir)
        
        # Process with specific tickers if provided
        tickers_to_simulate = []
        if selected_tickers:
            tickers_to_simulate = selected_tickers
        # Fall back to sectors if no tickers specified
        elif filtered_sectors:
            for sector in filtered_sectors:
                if sector in SECTORS:
                    tickers_to_simulate.extend(SECTORS[sector])
            
        # Limit to a reasonable number
        if len(tickers_to_simulate) > 50:
            tickers_to_simulate = tickers_to_simulate[:50]
            simulation_status.update({
                "errors": simulation_status.get()["errors"] + ["Limited to 50 stocks maximum."]
            })
        
        simulation_status.update({
            "total_stocks": len(tickers_to_simulate)
        })
        
        # Store all simulation results
        all_results = {}
        
        # Run simulations for each ticker
        for i, ticker in enumerate(tickers_to_simulate):
            try:
                # Update status
                simulation_status.update({
                    "current_stock": ticker,
                    "completed_stocks": i,
                    "progress": (i / len(tickers_to_simulate)) * 100 if tickers_to_simulate else 0
                })
                
                print(f"Starting simulation for {ticker}...")
                
                # Get sector for this ticker
                sector = None
                for sec, tickers in SECTORS.items():
                    if ticker in tickers:
                        sector = sec
                        break
                
                # Run simulation with parameters
                params = {
                    "ticker": ticker,
                    "model_type": model_type,
                    "paths": num_paths,
                    "steps": num_steps,
                    "dt": time_step,
                    "calibrate": True if not model_params else False,
                }
                
                # Add manual parameters if calibration is disabled
                if model_params:
                    params.update(model_params)
                
                print(f"Running simulation for {ticker} with parameters: {params}")
                
                # Run simulation
                result = simulation_engine.run_simulation(**params)
                
                # Add sector information
                if sector:
                    result['sector'] = sector
                
                # Store result
                all_results[ticker] = result
                
                # Generate individual stock report
                generate_report(result, ticker, output_dir)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error processing {ticker}: {str(e)}")
                simulation_status.update({
                    "errors": simulation_status.get()["errors"] + [f"Error processing {ticker}: {str(e)}"]
                })
        
        # Generate consolidated report for all stocks
        if len(all_results) > 1:
            try:
                # Use our custom consolidated report generator
                consolidated_report_path = generate_consolidated_report(all_results, reports_dir)
                print(f"Created consolidated report: {consolidated_report_path}")
            except Exception as e:
                import traceback
                traceback.print_exc()
                print(f"Error generating consolidated report: {str(e)}")
                simulation_status.update({
                    "errors": simulation_status.get()["errors"] + [f"Error generating consolidated report: {str(e)}"]
                })
        
        # Complete status
        simulation_status.update({
            "running": False,
            "progress": 100,
            "completed_stocks": len(tickers_to_simulate),
            "end_time": time.time()
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error in simulation thread: {str(e)}")
        simulation_status.update({
            "running": False,
            "errors": simulation_status.get()["errors"] + [f"Error in simulation thread: {str(e)}"],
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
        # Always try to use consolidated_report.html first
        reports_dir = os.path.join('output', 'reports')
        consolidated_report = os.path.join(reports_dir, "consolidated_report.html")
        
        # If consolidated report exists, use it
        if os.path.exists(consolidated_report):
            return redirect(url_for('serve_report', path="consolidated_report.html"))
        
        # Standard fallback if nothing else works
        main_report_names = ["simulation_report.html", "report.html", "index.html"]
        
        # Check in standard reports directory
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
        reports_dir = os.path.join('output', 'reports')
        if os.path.exists(reports_dir):
            # Look for reports with timestamp in filename
            ticker_reports = [f for f in os.listdir(reports_dir) if f.startswith(f"{ticker}_report_") and f.endswith('.html')]
            if ticker_reports:
                # Sort by name (which includes timestamp) in descending order
                ticker_reports.sort(reverse=True)
                return redirect(url_for('serve_report', path=ticker_reports[0]))
        
        # Fall back to standard report name
        report_filename = f"{ticker}_report.html"
        
        # Check in standard reports directory
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