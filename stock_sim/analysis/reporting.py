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
    
    # Delete old reports for this ticker
    for old_report in os.listdir(output_dir):
        if old_report.startswith(f"{ticker}_report_") and old_report.endswith(".html"):
            try:
                os.remove(os.path.join(output_dir, old_report))
                print(f"Deleted old report: {old_report}")
            except Exception as e:
                print(f"Warning: Could not delete old report {old_report}: {e}")
    
    # Extract data from result
    if not result or 'statistics' not in result:
        print(f"Error: Invalid result data for {ticker}")
        return None
    
    stats = result['statistics']
    
    # Get actual number of paths from the paths matrix if available
    paths_matrix = result.get('paths_matrix', None)
    if paths_matrix is not None:
        num_paths = paths_matrix.shape[0]
    elif 'simulation_config' in result:
        num_paths = result['simulation_config'].get('paths', 1000)
    else:
        num_paths = stats.get('num_paths', 1000)
    
    # Ensure num_paths is set in stats
    stats['num_paths'] = num_paths
    
    # Format paths for HTML
    graphs = result.get('graphs', {})
    paths_graph = f"../graphs/{ticker}_price_paths.png"
    distribution_graph = f"../graphs/{ticker}_price_histogram.png"
    return_histogram_graph = f"../graphs/{ticker}_return_histogram.png"
    qq_plot_graph = f"../graphs/{ticker}_qq_plot.png"
    returns_boxplot_graph = f"../graphs/{ticker}_returns_boxplot.png"
    risk_reward_graph = f"../graphs/{ticker}_risk_reward.png"
    yearly_returns_graph = f"../graphs/{ticker}_yearly_returns.png"
    
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
    
    # HTML Template with improved styling and interactivity
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
            max-width: 1200px;
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
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .metric-box {{
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            position: relative;
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
            grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
            gap: 20px;
        }}
        .image-container {{
            text-align: center;
            margin-bottom: 30px;
            cursor: pointer;
            transition: transform 0.3s ease;
        }}
        .image-container:hover {{
            transform: scale(1.02);
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
            width: 300px;
            background-color: #2c3e50;
            color: #fff;
            text-align: left;
            border-radius: 6px;
            padding: 10px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -150px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 14px;
            line-height: 1.4;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .tooltip:hover .tooltip-text {{
            visibility: visible;
            opacity: 1;
        }}
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.9);
        }}
        .modal-content {{
            margin: auto;
            display: block;
            width: 90%;
            max-width: 1200px;
            max-height: 90vh;
            object-fit: contain;
        }}
        .close {{
            position: absolute;
            right: 35px;
            top: 15px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }}
        .simulation-params {{
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .param-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 15px;
        }}
        .param-item {{
            padding: 10px;
            background-color: white;
            border-radius: 4px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .market-interpretation {{
            background-color: #e8f4f8;
            padding: 15px;
            border-radius: 6px;
            margin-top: 10px;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{ticker} Stock Price Simulation</h1>
            <p>Generated on: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        </div>
        
        <div class="simulation-params">
            <h2>Simulation Parameters</h2>
            <div class="param-grid">
                <div class="param-item tooltip">
                    <strong>Model Type:</strong> {result.get('model_type', 'combined').upper()}
                    <span class="tooltip-text">The type of stochastic model used for price simulation</span>
                </div>
                <div class="param-item tooltip">
                    <strong>Number of Paths:</strong> {num_paths:,}
                    <span class="tooltip-text">Number of simulated price paths used in Monte Carlo simulation</span>
                </div>
                <div class="param-item tooltip">
                    <strong>Time Steps:</strong> {stats.get('num_steps', 21)}
                    <span class="tooltip-text">Number of discrete time points in the simulation</span>
                </div>
                <div class="param-item tooltip">
                    <strong>Time Horizon:</strong> {stats.get('num_steps', 21)} trading days
                    <span class="tooltip-text">Length of the forecast period in trading days</span>
                </div>
                <div class="param-item tooltip">
                    <strong>Annual Drift (μ):</strong> {stats.get('mu', 0)*100:.2f}%
                    <span class="tooltip-text">Expected annual return based on historical data</span>
                </div>
                <div class="param-item tooltip">
                    <strong>Annual Volatility (σ):</strong> {stats.get('sigma', 0)*100:.2f}%
                    <span class="tooltip-text">Annual volatility of returns based on historical data</span>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Summary Statistics</h2>
            <div class="metrics">
                <div class="metric-box tooltip">
                    <h3>Initial Price</h3>
                    <p>${initial_price:.2f}</p>
                    <span class="tooltip-text">Current market price used as starting point for simulation</span>
                    <div class="market-interpretation">
                        Base price for calculating potential returns
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Expected Final Price</h3>
                    <p>${mean_final_price:.2f}</p>
                    <span class="tooltip-text">Average predicted price across all simulation paths</span>
                    <div class="market-interpretation">
                        The model's central price forecast
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Expected Return</h3>
                    <p class="{('positive' if pct_return >= 0 else 'negative')}">{pct_return:.2f}%</p>
                    <span class="tooltip-text">Average predicted return over the simulation period</span>
                    <div class="market-interpretation">
                        {
                            "Strong Buy Signal" if pct_return > 15 else
                            "Buy Signal" if pct_return > 5 else
                            "Hold Signal" if pct_return > -5 else
                            "Sell Signal" if pct_return > -15 else
                            "Strong Sell Signal"
                        }
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Return Volatility</h3>
                    <p>{stats.get('return_volatility', 0):.2f}%</p>
                    <span class="tooltip-text">Standard deviation of returns, measuring price uncertainty</span>
                    <div class="market-interpretation">
                        {
                            "Very High Risk" if stats.get('return_volatility', 0) > 30 else
                            "High Risk" if stats.get('return_volatility', 0) > 20 else
                            "Moderate Risk" if stats.get('return_volatility', 0) > 10 else
                            "Low Risk"
                        }
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Sharpe Ratio</h3>
                    <p class="{('positive' if stats.get('sharpe_ratio', 0) > 0.5 else 'negative')}">{stats.get('sharpe_ratio', 0):.2f}</p>
                    <span class="tooltip-text">Risk-adjusted return measure (higher is better)</span>
                    <div class="market-interpretation">
                        {
                            "Excellent Risk-Adjusted Returns" if stats.get('sharpe_ratio', 0) > 1.5 else
                            "Good Risk-Adjusted Returns" if stats.get('sharpe_ratio', 0) > 1 else
                            "Fair Risk-Adjusted Returns" if stats.get('sharpe_ratio', 0) > 0.5 else
                            "Poor Risk-Adjusted Returns"
                        }
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Sortino Ratio</h3>
                    <p class="{('positive' if stats.get('sortino_ratio', 0) > 0.5 else 'negative')}">{stats.get('sortino_ratio', 0):.2f}</p>
                    <span class="tooltip-text">Risk-adjusted return focusing on downside volatility</span>
                    <div class="market-interpretation">
                        {
                            "Excellent Downside Protection" if stats.get('sortino_ratio', 0) > 2 else
                            "Good Downside Protection" if stats.get('sortino_ratio', 0) > 1 else
                            "Fair Downside Protection" if stats.get('sortino_ratio', 0) > 0.5 else
                            "Poor Downside Protection"
                        }
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Risk Metrics</h2>
            <div class="metrics">
                <div class="metric-box tooltip">
                    <h3>Value at Risk (95%)</h3>
                    <p>{stats.get('var_95', 0):.2f}%</p>
                    <span class="tooltip-text">Maximum expected loss at 95% confidence level</span>
                    <div class="market-interpretation">
                        {
                            "Very High Risk" if stats.get('var_95', 0) > 20 else
                            "High Risk" if stats.get('var_95', 0) > 15 else
                            "Moderate Risk" if stats.get('var_95', 0) > 10 else
                            "Low Risk"
                        }
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Conditional VaR (95%)</h3>
                    <p>{stats.get('cvar_95', 0):.2f}%</p>
                    <span class="tooltip-text">Average loss when losses exceed VaR</span>
                    <div class="market-interpretation">
                        Expected loss in worst-case scenarios
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Maximum Drawdown</h3>
                    <p>{stats.get('max_drawdown', 0)*100:.2f}%</p>
                    <span class="tooltip-text">Largest peak-to-trough decline</span>
                    <div class="market-interpretation">
                        {
                            "Extreme Risk" if stats.get('max_drawdown', 0)*100 > 30 else
                            "High Risk" if stats.get('max_drawdown', 0)*100 > 20 else
                            "Moderate Risk" if stats.get('max_drawdown', 0)*100 > 10 else
                            "Low Risk"
                        }
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Skewness</h3>
                    <p>{stats.get('skewness', 0):.2f}</p>
                    <span class="tooltip-text">Measure of return distribution asymmetry</span>
                    <div class="market-interpretation">
                        {
                            "Strong Positive Skew (Upside Potential)" if stats.get('skewness', 0) > 0.5 else
                            "Slight Positive Skew" if stats.get('skewness', 0) > 0.1 else
                            "Symmetric" if abs(stats.get('skewness', 0)) <= 0.1 else
                            "Slight Negative Skew" if stats.get('skewness', 0) > -0.5 else
                            "Strong Negative Skew (Downside Risk)"
                        }
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Kurtosis</h3>
                    <p>{stats.get('kurtosis', 0):.2f}</p>
                    <span class="tooltip-text">Measure of extreme return frequency</span>
                    <div class="market-interpretation">
                        {
                            "Very High Tail Risk" if stats.get('kurtosis', 0) > 5 else
                            "High Tail Risk" if stats.get('kurtosis', 0) > 3 else
                            "Normal Tail Risk" if stats.get('kurtosis', 0) > 2 else
                            "Low Tail Risk"
                        }
                    </div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>Advanced Risk Analytics</h2>
            <div class="metrics">
                <div class="metric-box tooltip">
                    <h3>Treynor Ratio</h3>
                    <p>{stats.get('treynor_ratio', 0):.4f}</p>
                    <span class="tooltip-text">Risk-adjusted performance relative to systematic risk (β). Higher values indicate better risk-adjusted returns.</span>
                    <div class="market-interpretation">
                        {
                            "Excellent" if stats.get('treynor_ratio', 0) > 0.15 else
                            "Good" if stats.get('treynor_ratio', 0) > 0.10 else
                            "Fair" if stats.get('treynor_ratio', 0) > 0.05 else
                            "Poor"
                        }
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Information Ratio</h3>
                    <p>{stats.get('information_ratio', 0):.4f}</p>
                    <span class="tooltip-text">Measures risk-adjusted excess returns relative to benchmark. Higher values indicate better active management.</span>
                    <div class="market-interpretation">
                        {
                            "Superior" if stats.get('information_ratio', 0) > 1.0 else
                            "Good" if stats.get('information_ratio', 0) > 0.5 else
                            "Average" if stats.get('information_ratio', 0) > 0 else
                            "Underperforming"
                        }
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Calmar Ratio</h3>
                    <p>{stats.get('calmar_ratio', 0):.4f}</p>
                    <span class="tooltip-text">Ratio of average annual compounded return to maximum drawdown risk. Higher values indicate better risk-adjusted performance.</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Omega Ratio</h3>
                    <p>{stats.get('omega_ratio', 0):.4f}</p>
                    <span class="tooltip-text">Probability-weighted ratio of gains versus losses relative to a threshold. Values > 1 indicate positive risk-adjusted performance.</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Tail Risk (CVaR 99%)</h3>
                    <p>{stats.get('cvar_99', 0):.2f}%</p>
                    <span class="tooltip-text">Expected loss in the worst 1% of scenarios. More conservative risk measure than VaR.</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Beta (β)</h3>
                    <p>{stats.get('beta', 0):.4f}</p>
                    <span class="tooltip-text">Measure of systematic risk relative to market. β>1 indicates higher volatility than market.</span>
                    <div class="market-interpretation">
                        {
                            "Highly Aggressive" if stats.get('beta', 0) > 1.5 else
                            "Aggressive" if stats.get('beta', 0) > 1.2 else
                            "Moderate" if stats.get('beta', 0) > 0.8 else
                            "Defensive" if stats.get('beta', 0) > 0.5 else
                            "Very Defensive"
                        }
                    </div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Technical Indicators</h2>
            <div class="metrics">
                <div class="metric-box tooltip">
                    <h3>RSI (14-day)</h3>
                    <p>{stats.get('rsi_14', 0):.2f}</p>
                    <span class="tooltip-text">Relative Strength Index. Measures momentum. Values >70 indicate overbought, <30 oversold.</span>
                    <div class="market-interpretation">
                        {
                            "Strongly Overbought" if stats.get('rsi_14', 0) > 80 else
                            "Overbought" if stats.get('rsi_14', 0) > 70 else
                            "Neutral" if stats.get('rsi_14', 0) > 30 else
                            "Oversold" if stats.get('rsi_14', 0) > 20 else
                            "Strongly Oversold"
                        }
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Bollinger Band Width</h3>
                    <p>{stats.get('bb_width', 0):.4f}</p>
                    <span class="tooltip-text">Measures price volatility. Higher values indicate higher volatility.</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>MACD Signal</h3>
                    <p>{stats.get('macd_signal', 'Neutral')}</p>
                    <span class="tooltip-text">Moving Average Convergence/Divergence trend indicator.</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Statistical Analysis</h2>
            <div class="metrics">
                <div class="metric-box tooltip">
                    <h3>Hurst Exponent</h3>
                    <p>{stats.get('hurst_exponent', 0):.4f}</p>
                    <span class="tooltip-text">Measures long-term memory of time series. H>0.5 indicates trend-following, H<0.5 indicates mean-reversion.</span>
                    <div class="market-interpretation">
                        {
                            "Strong Trend-Following" if stats.get('hurst_exponent', 0) > 0.65 else
                            "Weak Trend-Following" if stats.get('hurst_exponent', 0) > 0.55 else
                            "Random Walk" if stats.get('hurst_exponent', 0) > 0.45 else
                            "Weak Mean-Reversion" if stats.get('hurst_exponent', 0) > 0.35 else
                            "Strong Mean-Reversion"
                        }
                    </div>
                </div>
                <div class="metric-box tooltip">
                    <h3>Ljung-Box Test (p-value)</h3>
                    <p>{stats.get('ljung_box_p', 0):.4f}</p>
                    <span class="tooltip-text">Tests for presence of autocorrelation. Low p-values indicate significant autocorrelation.</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Jarque-Bera Test (p-value)</h3>
                    <p>{stats.get('jarque_bera_p', 0):.4f}</p>
                    <span class="tooltip-text">Tests for normality of returns. Low p-values indicate non-normal distribution.</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Advanced Probability Analysis</h2>
            <div class="metrics">
                <div class="metric-box tooltip">
                    <h3>Probability of New High</h3>
                    <p>{stats.get('prob_new_high', 0):.2f}%</p>
                    <span class="tooltip-text">Probability of reaching a new high within simulation period.</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Probability of 30%+ Gain</h3>
                    <p>{stats.get('prob_up_30percent', 0):.2f}%</p>
                    <span class="tooltip-text">Chance of at least 30% return</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Probability of 30%+ Loss</h3>
                    <p>{stats.get('prob_down_30percent', 0):.2f}%</p>
                    <span class="tooltip-text">Risk of at least 30% loss</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Expected Shortfall (2.5%)</h3>
                    <p>{stats.get('expected_shortfall_97_5', 0):.2f}%</p>
                    <span class="tooltip-text">Average loss in worst 2.5% of scenarios</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Gain/Loss Ratio</h3>
                    <p>{stats.get('gain_loss_ratio', 0):.4f}</p>
                    <span class="tooltip-text">Ratio of average gain to average loss. Higher values indicate better risk/reward.</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Win Rate</h3>
                    <p>{stats.get('win_rate', 0):.2f}%</p>
                    <span class="tooltip-text">Percentage of simulations resulting in profit</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Regime Analysis</h2>
            <div class="metrics">
                <div class="metric-box tooltip">
                    <h3>Current Regime</h3>
                    <p>{stats.get('current_regime', 'Unknown')}</p>
                    <span class="tooltip-text">Current market regime based on volatility and returns</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Regime Transition Probability</h3>
                    <p>{stats.get('regime_transition_prob', 0):.2f}%</p>
                    <span class="tooltip-text">Probability of regime change within simulation period</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Regime-Adjusted VaR</h3>
                    <p>{stats.get('regime_adjusted_var', 0):.2f}%</p>
                    <span class="tooltip-text">Value at Risk adjusted for current market regime</span>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>Jump Analysis</h2>
            <div class="metrics">
                <div class="metric-box tooltip">
                    <h3>Jump Intensity (λ)</h3>
                    <p>{stats.get('jump_intensity', 0):.2f} per year</p>
                    <span class="tooltip-text">Expected number of jumps per year</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Mean Jump Size</h3>
                    <p>{stats.get('jump_mean', 0)*100:.2f}%</p>
                    <span class="tooltip-text">Average size of price jumps</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Jump Volatility</h3>
                    <p>{stats.get('jump_sigma', 0)*100:.2f}%</p>
                    <span class="tooltip-text">Volatility of jump sizes</span>
                </div>
                <div class="metric-box tooltip">
                    <h3>Probability of Jump</h3>
                    <p>{stats.get('prob_jump', 0):.2f}%</p>
                    <span class="tooltip-text">Probability of at least one jump in simulation period</span>
                </div>
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
                        <th>Interpretation</th>
                    </tr>
                    <tr>
                        <td>5%</td>
                        <td>${stats.get('percentiles', {}).get('5%', 0):.2f}</td>
                        <td class="{('positive' if (stats.get('percentiles', {}).get('5%', 0)/initial_price - 1)*100 >= 0 else 'negative')}">{((stats.get('percentiles', {}).get('5%', 0)/initial_price - 1)*100):.2f}%</td>
                        <td>Worst-case scenario (95% confidence)</td>
                    </tr>
                    <tr>
                        <td>25%</td>
                        <td>${stats.get('percentiles', {}).get('25%', 0):.2f}</td>
                        <td class="{('positive' if (stats.get('percentiles', {}).get('25%', 0)/initial_price - 1)*100 >= 0 else 'negative')}">{((stats.get('percentiles', {}).get('25%', 0)/initial_price - 1)*100):.2f}%</td>
                        <td>Lower quartile</td>
                    </tr>
                    <tr>
                        <td>50% (Median)</td>
                        <td>${stats.get('percentiles', {}).get('50%', 0):.2f}</td>
                        <td class="{('positive' if (stats.get('percentiles', {}).get('50%', 0)/initial_price - 1)*100 >= 0 else 'negative')}">{((stats.get('percentiles', {}).get('50%', 0)/initial_price - 1)*100):.2f}%</td>
                        <td>Most likely scenario</td>
                    </tr>
                    <tr>
                        <td>75%</td>
                        <td>${stats.get('percentiles', {}).get('75%', 0):.2f}</td>
                        <td class="{('positive' if (stats.get('percentiles', {}).get('75%', 0)/initial_price - 1)*100 >= 0 else 'negative')}">{((stats.get('percentiles', {}).get('75%', 0)/initial_price - 1)*100):.2f}%</td>
                        <td>Upper quartile</td>
                    </tr>
                    <tr>
                        <td>95%</td>
                        <td>${stats.get('percentiles', {}).get('95%', 0):.2f}</td>
                        <td class="{('positive' if (stats.get('percentiles', {}).get('95%', 0)/initial_price - 1)*100 >= 0 else 'negative')}">{((stats.get('percentiles', {}).get('95%', 0)/initial_price - 1)*100):.2f}%</td>
                        <td>Best-case scenario (95% confidence)</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="image-section">
            <h2>Visualizations</h2>
            <p>Click on any graph to enlarge</p>
            <div class="image-grid">
                <div class="image-container">
                    <h3>Simulation Paths</h3>
                    <img src="{paths_graph}" alt="Price Simulation Paths" onclick="openModal(this.src)">
                </div>
                <div class="image-container">
                    <h3>Final Price Distribution</h3>
                    <img src="{distribution_graph}" alt="Final Price Distribution" onclick="openModal(this.src)">
                </div>
                <div class="image-container">
                    <h3>Returns Histogram</h3>
                    <img src="{return_histogram_graph}" alt="Returns Histogram" onclick="openModal(this.src)">
                </div>
                <div class="image-container">
                    <h3>QQ Plot</h3>
                    <img src="{qq_plot_graph}" alt="QQ Plot" onclick="openModal(this.src)">
                </div>
                <div class="image-container">
                    <h3>Returns Boxplot</h3>
                    <img src="{returns_boxplot_graph}" alt="Returns Boxplot" onclick="openModal(this.src)">
                </div>
                <div class="image-container">
                    <h3>Risk-Reward Analysis</h3>
                    <img src="{risk_reward_graph}" alt="Risk-Reward Analysis" onclick="openModal(this.src)">
                </div>
                <div class="image-container">
                    <h3>Historical Returns by Year</h3>
                    <img src="{yearly_returns_graph}" alt="Historical Returns by Year" onclick="openModal(this.src)">
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>This report was generated using advanced Monte Carlo simulation techniques.</p>
            <p>The analysis is based on {num_paths:,} simulated price paths over {stats.get('num_steps', 21)} trading days.</p>
            <p>Past performance does not guarantee future results. This report is for educational purposes only.</p>
            <a href="consolidated_report.html" class="back-link">← Back to All Stocks</a>
        </div>
    </div>
    
    <!-- Modal for enlarged images -->
    <div id="imageModal" class="modal">
        <span class="close" onclick="closeModal()">&times;</span>
        <img class="modal-content" id="modalImg">
    </div>
    
    <script>
        // Image modal functionality
        function openModal(src) {{
            var modal = document.getElementById("imageModal");
            var modalImg = document.getElementById("modalImg");
            modal.style.display = "block";
            modalImg.src = src;
        }}
        
        function closeModal() {{
            var modal = document.getElementById("imageModal");
            modal.style.display = "none";
        }}
        
        // Close modal when clicking outside the image
        window.onclick = function(event) {{
            var modal = document.getElementById("imageModal");
            if (event.target == modal) {{
                modal.style.display = "none";
            }}
        }}
        
        // Enable tooltips
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
    
    # Get the most recent ticker and its result
    most_recent_ticker = list(results.keys())[-1] if results else None
    most_recent_result = results.get(most_recent_ticker) if most_recent_ticker else None
    
    # Only process the most recent simulation
    summary_data = []
    stock_details = []
    
    if most_recent_result and 'statistics' not in most_recent_result:
        print(f"Error: Invalid result data for {most_recent_ticker}")
        return None
        
    if most_recent_result:
        stats = most_recent_result['statistics']
        model_params = most_recent_result.get('model_params', {})
        paths_matrix = most_recent_result.get('paths_matrix', None)
        
        # Get actual number of paths from the paths matrix if available
        actual_num_paths = paths_matrix.shape[0] if paths_matrix is not None else stats.get('num_paths', 1000)
        
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
            'Ticker': most_recent_ticker,
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
        ticker_paths_graph = f"/graphs/{most_recent_ticker}_paths.png"
        ticker_dist_graph = f"/graphs/{most_recent_ticker}_distribution.png"
        
        # Calculate percentages for downside risk and upside potential
        downside_risk = (percentile_5 / initial_price - 1) * 100 if initial_price > 0 else 0
        upside_potential = (percentile_95 / initial_price - 1) * 100 if initial_price > 0 else 0
        
        # Create detailed section for the most recent stock
        stock_detail = f"""
        <div class='stock-section'>
            <h2>{most_recent_ticker} Detailed Analysis</h2>
            <div class='statistics'>
                <div class='stat-item'><strong>Initial Price:</strong> ${initial_price:.2f}</div>
                <div class='stat-item'><strong>Annual Drift:</strong> {model_params.get('mu', 0)*100:.2f}%</div>
                <div class='stat-item'><strong>Annual Volatility:</strong> {model_params.get('sigma', 0)*100:.2f}%</div>
                <div class='stat-item'><strong>Expected Return:</strong> {stats.get('expected_return', 0):.2f}%</div>
                <div class='stat-item'><strong>Downside Risk (5%):</strong> {downside_risk:.2f}%</div>
                <div class='stat-item'><strong>Upside Potential (95%):</strong> {upside_potential:.2f}%</div>
            </div>
            
            <h3>Price Distribution</h3>
            <p>The simulation shows the potential price range for {most_recent_ticker} after running {actual_num_paths:,} simulation paths with {stats.get('num_steps', 21)} time steps:</p>
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
            <img src='{ticker_paths_graph}' alt='{most_recent_ticker} Simulation Paths'><img src='{ticker_dist_graph}' alt='{most_recent_ticker} Price Distribution'></div>"""
        
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
            <p>This report summarizes the Monte Carlo simulation results using a regime-switching, jump-diffusion model with earnings shocks.</p>
        </div>
        
        <h2>Most Recent Simulation Results</h2>
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